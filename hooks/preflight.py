#!/usr/bin/env python3
"""Leto preflight check — run as the first step of every scheduled task.

Checks critical preconditions and repairs what can be fixed silently.

Exit codes:
  0 — ok or warn (scheduler should continue; check "issues" for warnings)
  1 — abort (scheduler must halt; read "abort_reason" and send Slack alert)

Output (always JSON to stdout):
{
  "status": "ok" | "warn" | "abort",
  "date": "YYYY-MM-DD",
  "abort_reason": "<string if abort, else empty>",
  "issues": [{"level": "abort"|"warn"|"info", "check": "<name>", "detail": "<msg>"}],
  "repaired": ["<item1>", ...]
}

Usage (from a SKILL.md PART A step 0):
  Run `python3 ~/Projects/Leto/hooks/preflight.py`
  - exit 1 (abort): halt task, send Slack DM, write minimal session log
  - exit 0 + status warn: log issues in session log, continue
  - exit 0 + status ok: continue normally
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ_MADRID = ZoneInfo("Europe/Madrid")
TODAY = datetime.now(TZ_MADRID).strftime("%Y-%m-%d")
YEAR = TODAY[:4]

# ── Paths ────────────────────────────────────────────────────────────────────

HOME = Path.home()
VAULT = HOME / "Obsidian Vault" / "Vladimir's Vault"
LETO  = HOME / "Projects" / "Leto"
CFG   = HOME / ".config" / "leto"
MEM   = HOME / ".claude" / "projects" / "-Users-vladimir-mashkovtsev-Projects-Leto" / "memory"

PAUSE_FLAG         = CFG / "schedulers-paused"
ENV_FILE           = CFG / "leto.env"      # consolidated secrets (see .env.example)
LINEAR_API_KEY     = CFG / "linear-api-key"   # legacy fallback only
SLACK_BOT_TOKEN    = CFG / "slack-bot-token"  # legacy fallback only
GRANOLA_REGISTRY   = MEM / "reference_granola_processed.md"
GRANOLA_SOURCES    = VAULT / "00 Inbox" / "Sources" / "granola"
SESSIONS_DIR       = VAULT / "40 System" / "Sessions" / YEAR
DAILY_NOTE         = VAULT / "40 System" / "Journal" / "Daily" / f"{TODAY}.md"
LETO_CLAUDE_MD     = LETO / "CLAUDE.md"
COST_CAP_FILE      = CFG / "cost-cap.json"


# ── Helpers ──────────────────────────────────────────────────────────────────

def issue(issues: list, level: str, check: str, detail: str) -> None:
    issues.append({"level": level, "check": check, "detail": detail})


def result(status: str, issues: list, repaired: list, abort_reason: str = "") -> dict:
    return {
        "status": status,
        "date": TODAY,
        "abort_reason": abort_reason,
        "issues": issues,
        "repaired": repaired,
    }


# ── Checks ───────────────────────────────────────────────────────────────────

def check_pause_flag(issues: list) -> bool:
    """Returns True → ABORT."""
    if PAUSE_FLAG.exists():
        try:
            data = json.loads(PAUSE_FLAG.read_text())
            reason = data.get("reason", "schedulers paused")
            issue(issues, "abort", "pause-flag", reason)
        except Exception:
            issue(issues, "abort", "pause-flag", "~/.config/leto/schedulers-paused exists")
        return True
    return False


def check_config_files(issues: list) -> None:
    """Non-secret config only.

    Credentials are deliberately NOT checked here any more. File-existence was
    the bug: the Linear key file existed for 23 days while returning 401. All
    credentials now go through check_secrets(), which resolves them (env →
    leto.env → legacy file) and live-probes each one. Checking the legacy paths
    here would also emit false warnings the moment those files are deleted.
    """
    if not COST_CAP_FILE.exists():
        issue(issues, "warn", "cost-cap.json", f"missing: {COST_CAP_FILE}")
    if not ENV_FILE.exists() and not LINEAR_API_KEY.exists():
        issue(issues, "warn", "leto.env",
              f"no consolidated secrets file at {ENV_FILE} and no legacy key files — "
              "run scripts/migrate-secrets.sh (see .env.example)")


def check_vault_root(issues: list) -> None:
    if not VAULT.is_dir():
        issue(issues, "warn", "vault-root", f"vault not accessible at {VAULT}")


def check_secrets(issues: list) -> list[str]:
    """Live-probe EVERY credential, not just Linear.

    Supersedes the old Linear-only probe. The original comment was right —
    "the key FILE existing is not enough" — but it only applied that lesson to
    one secret. The three Slack tokens were checked for file existence alone,
    so any of them could have died silently for a month exactly as the Linear
    key did (401 from 2026-08-24, unnoticed for 23 days).

    Advisory — never blocks. Network failure is not an auth failure, and
    leto_secrets keeps those verdicts distinct.

    Returns the list of named blocker causes for the escalation ladder.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from leto_secrets import check_all
        report = check_all()
    except Exception as e:  # advisory only — never break preflight
        issue(issues, "warn", "secrets-check-failed",
              f"could not validate credentials ({type(e).__name__}: {e})")
        return []

    for secret in report["secrets"]:
        status, key = secret["status"], secret["key"]
        if status == "ok" or status == "network":
            continue  # network blips stay silent by design
        if status == "missing" and not secret["required"]:
            continue  # optional credential, absent on purpose
        issue(issues, "warn", secret["cause"],
              f"{key} [{status}] — {secret['detail']} "
              f"(resolved from: {secret['source']})")

    return report["blockers"]


def check_leto_repo(issues: list) -> None:
    if not LETO_CLAUDE_MD.exists():
        issue(issues, "warn", "leto-repo", f"CLAUDE.md not found at {LETO_CLAUDE_MD}")


def check_standing_approvals(issues: list) -> None:
    """Warn if any SA is expired or past its 30d review window."""
    sa_script = LETO / "hooks" / "standing-approvals.py"
    if not sa_script.exists():
        return
    try:
        import subprocess
        result = subprocess.run(
            ["python3", str(sa_script), "--status"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return
        import json as _json
        data = _json.loads(result.stdout)
        if data.get("expired", 0) > 0:
            issue(issues, "warn", "sa-expired",
                  f"{data['expired']} standing approval(s) expired — update Standing Approvals.md")
        if data.get("review_needed", 0) > 0:
            issue(issues, "warn", "sa-review-needed",
                  f"{data['review_needed']} standing approval(s) past 30d review window")
    except Exception:
        pass  # SA check is advisory — never block the preflight


def get_sa_ping() -> dict:
    """Fail-loud SA expiry ping verdict (VM-139). Advisory — never blocks.

    Tasks act on this: if ping_needed, send `message` as a one-line DM
    (meta-notification — always allowed), then run standing-approvals.py --mark-pinged.
    """
    sa_script = LETO / "hooks" / "standing-approvals.py"
    if not sa_script.exists():
        return {"ping_needed": False, "message": ""}
    try:
        import subprocess
        r = subprocess.run(
            ["python3", str(sa_script), "--ping-check"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode != 0:
            return {"ping_needed": False, "message": ""}
        data = json.loads(r.stdout)
        return {"ping_needed": bool(data.get("ping_needed")), "message": data.get("message", "")}
    except Exception:
        return {"ping_needed": False, "message": ""}


# ── Repairs ──────────────────────────────────────────────────────────────────

def repair_granola_registry(repaired: list, issues: list) -> None:
    """Create the registry stub if missing. Idempotent."""
    if GRANOLA_REGISTRY.exists():
        return
    try:
        MEM.mkdir(parents=True, exist_ok=True)
        GRANOLA_REGISTRY.write_text(
            "---\n"
            "name: granola-processed-registry\n"
            "description: Registry of Granola meeting source-ids already processed by the"
            " leto-granola-intake scheduler. Prevents duplicate memory writes on re-runs.\n"
            "metadata:\n"
            "  node_type: memory\n"
            "  type: reference\n"
            f"  repaired_at: {datetime.now(TZ_MADRID).isoformat()}\n"
            "---\n\n"
            "Tracks which Granola meetings have been processed by `leto-granola-intake`.\n"
            "Check before writing memory updates. If a source-id appears here, skip\n"
            "the memory-update step for that meeting.\n\n"
            "## Processed\n\n"
            "_(empty — registry was missing and has been recreated)_\n"
        )
        repaired.append("granola-registry (created stub)")
    except OSError as e:
        issue(issues, "warn", "granola-registry-repair", f"could not create: {e}")


def repair_daily_journal(repaired: list, issues: list) -> None:
    """Create today's daily-note stub if missing. Idempotent."""
    if DAILY_NOTE.exists():
        return
    if not VAULT.is_dir():
        return  # vault not accessible — already warned above
    try:
        DAILY_NOTE.parent.mkdir(parents=True, exist_ok=True)
        DAILY_NOTE.write_text(
            "---\n"
            "type: daily-note\n"
            f"date: {TODAY}\n"
            "---\n\n"
            f"# {TODAY}\n\n"
            "_(auto-created by Leto preflight — fill in during the day)_\n"
        )
        repaired.append(f"daily-journal ({TODAY}) created stub")
    except OSError as e:
        issue(issues, "warn", "daily-journal-repair", f"could not create: {e}")


def repair_granola_sources_dir(repaired: list, issues: list) -> None:
    """Ensure the Granola sources directory exists."""
    if GRANOLA_SOURCES.is_dir():
        return
    if not VAULT.is_dir():
        return
    try:
        GRANOLA_SOURCES.mkdir(parents=True, exist_ok=True)
        repaired.append("granola-sources dir created")
    except OSError as e:
        issue(issues, "warn", "granola-sources-dir", f"could not create: {e}")


def repair_sessions_dir(repaired: list, issues: list) -> None:
    """Ensure the current year's sessions directory exists."""
    if SESSIONS_DIR.is_dir():
        return
    if not VAULT.is_dir():
        return
    try:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        repaired.append(f"sessions/{YEAR} dir created")
    except OSError as e:
        issue(issues, "warn", "sessions-dir", f"could not create: {e}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    issues: list = []
    repaired: list = []

    # 1. Pause flag — abort immediately if set
    if check_pause_flag(issues):
        abort_reason = issues[0]["detail"] if issues else "schedulers paused"
        print(json.dumps(result("abort", issues, repaired, abort_reason), indent=2))
        sys.exit(1)

    # 2. Config file checks (warn only)
    check_config_files(issues)

    # 3. Vault root + repo integrity + standing approvals + all credentials (warn only)
    check_vault_root(issues)
    check_leto_repo(issues)
    check_standing_approvals(issues)
    blocker_causes = check_secrets(issues)

    # 4. Repairs (silent — just log what changed)
    repair_granola_registry(repaired, issues)
    repair_daily_journal(repaired, issues)
    repair_granola_sources_dir(repaired, issues)
    repair_sessions_dir(repaired, issues)

    # 5. Determine overall status
    warn_count = sum(1 for i in issues if i["level"] == "warn")
    status = "warn" if warn_count > 0 else "ok"

    out = result(status, issues, repaired)
    out["sa_ping"] = get_sa_ping()  # fail-loud expiry ping verdict (VM-139)
    out["blocker_causes"] = blocker_causes
    print(json.dumps(out, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
