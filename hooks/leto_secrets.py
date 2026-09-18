#!/usr/bin/env python3
"""Leto secret resolution + live validation.

ONE env file holds every Leto credential: ~/.config/leto/leto.env (mode 600).
Kept outside any git work tree on purpose — EOD is an autonomous agent with git
access in ~/Projects/Leto, and .gitignore is one `git add -f` away from useless.

Resolution order for every key (no flag day — legacy files keep working):
  1. already-set environment variable
  2. ~/.config/leto/leto.env
  3. legacy single-value file (~/.config/leto/<name>)
  4. None

Usage:
    python3 leto_secrets.py --check          # live-probe every secret, JSON to stdout
    python3 leto_secrets.py --check --quiet  # exit 1 if any secret is auth-failed
    python3 leto_secrets.py --names          # list configured key names (never values)

As a library:
    from leto_secrets import get, load_env
    load_env()                 # populate os.environ from leto.env (env var wins)
    key = get("LINEAR_API_KEY")

WHY --check EXISTS: preflight only ever live-probed the Linear key. The three
Slack tokens were checked for FILE EXISTENCE only — the exact failure preflight's
own comment warns about ("the key FILE existing is not enough"). The Linear key
then died on 2026-08-24 and stayed dead 23 days. Every secret gets a real probe
now, and each failure is a named blocker cause the escalation ladder can track.

Tokens are sent with urllib, not `curl -H`, so they never appear in process argv.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CFG = Path.home() / ".config" / "leto"
ENV_FILE = CFG / "leto.env"

# key -> legacy single-value file under ~/.config/leto/
LEGACY_FILES = {
    "LINEAR_API_KEY": "linear-api-key",
    "SLACK_BOT_TOKEN": "slack-bot-token",
    "SLACK_APP_TOKEN": "slack-app-token",
    "SLACK_USER_TOKEN": "slack-user-token",
}

# Every key Leto knows about. YouTrack's two came from a second .env under
# ~/.claude/scheduled-tasks/youtrack-daily-digest/ — folded in here.
ALL_KEYS = list(LEGACY_FILES) + ["YOUTRACK_BASE_URL", "YOUTRACK_TOKEN"]

PROBE_TIMEOUT = 5  # seconds per probe; all probes run in parallel


# ── Resolution ───────────────────────────────────────────────────────────────

def parse_env_file(path: Path = ENV_FILE) -> dict[str, str]:
    """Parse `export KEY=value` / `KEY=value`. Matches the youtrack .env format."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            out[key] = val
    return out


def get(name: str) -> str | None:
    """Resolve one secret. Env var → leto.env → legacy file → None."""
    if os.environ.get(name):
        return os.environ[name]
    val = parse_env_file().get(name)
    if val:
        return val
    legacy = LEGACY_FILES.get(name)
    if legacy:
        p = CFG / legacy
        if p.exists():
            return p.read_text().strip()
    return None


# Keys this module injected into os.environ itself, so source_of() can still
# tell a caller-supplied env var apart from one we loaded out of leto.env.
_INJECTED: set[str] = set()


def load_env() -> list[str]:
    """Populate os.environ from leto.env + legacy files. An already-set env var
    always wins. Returns the key names loaded (never values)."""
    loaded = []
    for key in ALL_KEYS:
        if os.environ.get(key):
            continue
        val = get(key)
        if val:
            os.environ[key] = val
            _INJECTED.add(key)
            loaded.append(key)
    return loaded


def source_of(name: str) -> str:
    """Where a key is coming from — for diagnostics. Never returns a value.

    Must mirror get()'s precedence exactly: a caller-supplied env var wins over
    leto.env, so it has to be tested first. Keys we injected ourselves are not
    "env" — they are reported as whatever file they actually came from.
    """
    if os.environ.get(name) and name not in _INJECTED:
        return "env"
    if name in parse_env_file():
        return "leto.env"
    legacy = LEGACY_FILES.get(name)
    if legacy and (CFG / legacy).exists():
        return f"legacy:{legacy}"
    return "unset"


# ── Probes ───────────────────────────────────────────────────────────────────
# Each returns (status, detail). status: ok | auth-failed | bad-shape | network

_HTTP_SENTINEL = "__leto_http__"


def _request(url: str, headers: dict, data: bytes | None = None) -> tuple[int, str]:
    """HTTP via curl.

    Not urllib: this host's python3 loads no system CA bundle, so every https
    request raises CERTIFICATE_VERIFY_FAILED (listener.py:19-26 patches around
    the same thing with certifi, and preflight.py shells out to curl for it).
    certifi happens to be installed today and would work — curl is chosen
    anyway because it has no Python dependency to lose. A validator whose job
    is catching silent breakage should not itself break on a Python upgrade.

    Secret headers go in on STDIN as a curl config file, so tokens never appear
    in argv (i.e. never in `ps`). The URL and request body are not secret and
    stay in argv.

    Raises OSError on transport failure so callers can tell a network blip from
    an auth rejection — curl exits non-zero only for the former.
    """
    argv = ["curl", "-sS", "--max-time", str(PROBE_TIMEOUT),
            "--config", "-", "-w", f"\n{_HTTP_SENTINEL}%{{http_code}}"]
    if data is not None:
        argv += ["-X", "POST", "--data-binary", data.decode()]
    argv.append(url)

    config = "".join(
        'header = "{}: {}"\n'.format(k, v.replace("\\", "\\\\").replace('"', '\\"'))
        for k, v in headers.items()
    )

    proc = subprocess.run(argv, input=config, capture_output=True,
                          text=True, timeout=PROBE_TIMEOUT + 4)
    if proc.returncode != 0:
        raise OSError(f"curl exit {proc.returncode}: {proc.stderr.strip()[:120]}")

    body, _, code = proc.stdout.rpartition(_HTTP_SENTINEL)
    try:
        return int(code.strip()), body.rstrip("\n")
    except ValueError:
        raise OSError("could not parse curl status")


def probe_linear(token: str) -> tuple[str, str]:
    body = json.dumps({"query": "query { viewer { id } }"}).encode()
    code, text = _request(
        "https://api.linear.app/graphql",
        {"Content-Type": "application/json", "Authorization": token},
        body,
    )
    if code == 200 and '"errors"' not in text:
        return "ok", "viewer query succeeded"
    if code == 401 or "AUTHENTICATION_ERROR" in text:
        return "auth-failed", "401 — rotate at Linear → Settings → Security & access"
    return "auth-failed", f"HTTP {code}"


def _probe_slack(token: str, kind: str) -> tuple[str, str]:
    if not token.startswith(kind):
        return "bad-shape", f"expected a token starting with '{kind}'"
    code, text = _request("https://slack.com/api/auth.test",
                          {"Authorization": f"Bearer {token}"}, b"")
    try:
        payload = json.loads(text)
    except ValueError:
        return "auth-failed", f"unparseable response (HTTP {code})"
    if payload.get("ok"):
        return "ok", f"{payload.get('user', '?')} @ {payload.get('team', '?')}"
    return "auth-failed", payload.get("error", "ok:false")


def probe_slack_bot(token: str) -> tuple[str, str]:
    return _probe_slack(token, "xoxb-")


def probe_slack_user(token: str) -> tuple[str, str]:
    return _probe_slack(token, "xoxp-")


def probe_slack_app(token: str) -> tuple[str, str]:
    """Shape only. Socket Mode app tokens cannot be validated without opening a
    websocket, which would fight the running listener for the connection."""
    if token.startswith("xapp-"):
        return "ok", "shape ok (xapp-); Socket Mode not probed by design"
    return "bad-shape", "expected a token starting with 'xapp-'"


def probe_youtrack(token: str) -> tuple[str, str]:
    base = (get("YOUTRACK_BASE_URL") or "").rstrip("/")
    if not base:
        return "bad-shape", "YOUTRACK_BASE_URL not set"
    code, text = _request(f"{base}/api/users/me?fields=login",
                          {"Authorization": f"Bearer {token}",
                           "Accept": "application/json"})
    if code == 200:
        try:
            return "ok", f"login {json.loads(text).get('login', '?')}"
        except ValueError:
            return "ok", "200"
    if code in (401, 403):
        return "auth-failed", f"HTTP {code} — token rejected"
    return "auth-failed", f"HTTP {code}"


# secret key -> (probe fn, blocker cause for the escalation ladder, required?)
PROBES = {
    "LINEAR_API_KEY":   (probe_linear,     "linear-key-401",            True),
    "SLACK_BOT_TOKEN":  (probe_slack_bot,  "slack-bot-token-invalid",   True),
    "SLACK_APP_TOKEN":  (probe_slack_app,  "slack-app-token-invalid",   False),
    "SLACK_USER_TOKEN": (probe_slack_user, "slack-user-token-invalid",  False),
    "YOUTRACK_TOKEN":   (probe_youtrack,   "youtrack-token-invalid",    False),
}


def check_one(key: str) -> dict:
    probe, cause, required = PROBES[key]
    entry = {"key": key, "cause": cause, "required": required,
             "source": source_of(key)}
    token = get(key)
    if not token:
        entry.update(status="missing",
                     detail=f"not set in {ENV_FILE} or environment")
        return entry
    try:
        status, detail = probe(token)
    except (OSError, subprocess.TimeoutExpired) as e:
        # Network failure is NOT an auth failure — same rule preflight already
        # applies. A flaky wifi moment must never escalate as a dead credential.
        status, detail = "network", f"probe unreachable ({type(e).__name__})"
    entry.update(status=status, detail=detail)
    return entry


def check_all() -> dict:
    with ThreadPoolExecutor(max_workers=len(PROBES)) as pool:
        results = list(pool.map(check_one, PROBES))

    failed = [r for r in results if r["status"] in ("auth-failed", "bad-shape")]
    missing_required = [r for r in results
                        if r["status"] == "missing" and r["required"]]
    return {
        "env_file": str(ENV_FILE),
        "env_file_exists": ENV_FILE.exists(),
        "status": "fail" if (failed or missing_required) else "ok",
        # Named causes the escalation ladder tracks per-day. Network blips and
        # optional-missing keys deliberately do not produce a blocker.
        "blockers": [r["cause"] for r in failed + missing_required],
        "secrets": results,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Leto secret resolution + validation")
    ap.add_argument("--check", action="store_true",
                    help="live-probe every secret; JSON to stdout")
    ap.add_argument("--names", action="store_true",
                    help="list configured key names and their source (never values)")
    ap.add_argument("--quiet", action="store_true",
                    help="with --check: print nothing, just set the exit code")
    args = ap.parse_args()

    if args.names:
        for key in ALL_KEYS:
            print(f"{key:20s} {source_of(key)}")
        return

    if args.check:
        out = check_all()
        if not args.quiet:
            print(json.dumps(out, indent=2))
        sys.exit(1 if out["status"] == "fail" else 0)

    ap.print_help()


if __name__ == "__main__":
    main()
