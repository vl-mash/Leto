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

import argparse
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


# ── Escalation ladder ────────────────────────────────────────────────────────
# A routine blocked on a cause it cannot fix itself must CHANGE ITS BEHAVIOUR,
# not repeat itself. The Linear key died 2026-08-24 and the portfolio sent ~34
# near-identical DMs over 17 weekdays (EOD abort + sa_ping, daily). Nothing was
# wrong with the alerting — it worked perfectly and became wallpaper.
#
# So the ladder escalates by SUBTRACTION: the one-liner goes out once, then the
# brief itself degrades — first a line, then taking the ONE-thing slot, finally
# stripping to four lines. What changes is the shape of the thing Vladimir
# already reads every morning, so it cannot be tuned out; the wallpaper is what
# gets removed.
#
# Tier 4 stands a routine down DYNAMICALLY — re-evaluated against the live probe
# every run, self-healing the moment the cause clears. Deliberately NOT a
# written disable flag: that needs a human to remember to undo it, which is the
# same dead-man's-switch-plus-manual-reset pattern that just failed with SA-002.

BLOCKER_STATE = LETO / ".local-data" / "blocker-state.json"

# cause -> tasks for which this cause makes the run pointless. A cause absent
# here degrades its routines but never stands one down. Critically,
# leto-daily-brief is NOT listed under linear-key-401: without Linear it still
# delivers calendar, Granola actions and Slack, and it is also the escalation
# channel itself. Standing it down would remove the only routine still earning
# its keep and blind the very surface reporting the outage.
FATAL_FOR = {
    "linear-key-401": ["leto-personal-backlog-eod"],
    "slack-bot-token-invalid": ["leto-personal-backlog-eod", "leto-daily-brief",
                                "leto-weekly-review"],
}


def _tier(days: int) -> int:
    if days >= 10:
        return 4
    if days >= 5:
        return 3
    if days >= 2:
        return 2
    return 1


def track_blockers(causes: list, issues: list, task: str | None) -> dict:
    """Count consecutive days per cause, assign a tier, persist, return verdicts.

    `days` advances only when last_seen != today, so all six routines can call
    preflight on the same day without inflating the count.
    """
    try:
        state = json.loads(BLOCKER_STATE.read_text()) if BLOCKER_STATE.exists() else {}
    except (OSError, ValueError):
        state = {}

    active, recovered = [], []

    # Causes that have cleared since the last run — good news, reported once for
    # the day, then dropped. A new occurrence later starts again at tier 1,
    # because a new failure is new news.
    for cause in list(state):
        if cause in causes:
            continue
        prior = state.pop(cause)
        if prior.get("last_seen") != TODAY:
            recovered.append({"cause": cause, "was_days": prior.get("days", 0),
                              "first_seen": prior.get("first_seen")})

    for cause in causes:
        entry = state.get(cause)
        if entry is None:
            entry = {"first_seen": TODAY, "last_seen": TODAY, "days": 1,
                     "notified": False}
        elif entry.get("last_seen") != TODAY:
            entry["days"] = entry.get("days", 0) + 1
            entry["last_seen"] = TODAY
        entry["tier"] = _tier(entry["days"])
        state[cause] = entry

        # The one-liner goes out once per cause, and keeps being offered until a
        # send actually succeeds (the caller flips `notified` via --mark-notified).
        verdict = {
            "cause": cause,
            "days": entry["days"],
            "first_seen": entry["first_seen"],
            "tier": entry["tier"],
            "dm": not entry.get("notified", False),
            "fatal_for": FATAL_FOR.get(cause, []),
            "stand_down": bool(task and entry["tier"] >= 4
                               and task in FATAL_FOR.get(cause, [])),
        }
        active.append(verdict)

        if entry["days"] >= 2:
            issue(issues, "warn", f"{cause}-streak",
                  f"blocked {entry['days']} consecutive run-days since "
                  f"{entry['first_seen']} (tier {entry['tier']})")

    try:
        BLOCKER_STATE.parent.mkdir(parents=True, exist_ok=True)
        BLOCKER_STATE.write_text(json.dumps(state, indent=2) + "\n")
    except OSError as e:
        issue(issues, "warn", "blocker-state", f"could not persist: {e}")

    return {
        "active": sorted(active, key=lambda v: -v["tier"]),
        "recovered": recovered,
        # Highest tier across all active causes — what the brief keys its shape off.
        "max_tier": max((v["tier"] for v in active), default=0),
        "stand_down": any(v["stand_down"] for v in active),
    }


def mark_notified(causes: list) -> None:
    """Record that the one-liner for these causes actually landed, so it is not
    repeated. Called by a scheduler AFTER a successful send."""
    try:
        state = json.loads(BLOCKER_STATE.read_text()) if BLOCKER_STATE.exists() else {}
    except (OSError, ValueError):
        return
    for cause in causes:
        if cause in state:
            state[cause]["notified"] = True
    try:
        BLOCKER_STATE.write_text(json.dumps(state, indent=2) + "\n")
    except OSError:
        pass


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
    ap = argparse.ArgumentParser(description="Leto scheduled-task preflight")
    ap.add_argument("--task", metavar="TASK_ID", default=None,
                    help="calling task id (e.g. leto-personal-backlog-eod) — adds the "
                         "per-task stand_down verdict from the escalation ladder")
    ap.add_argument("--mark-notified", metavar="CAUSE", nargs="+", default=None,
                    help="record that a blocker one-liner was successfully sent, so it "
                         "is not repeated; call AFTER the send succeeds, then exit")
    args = ap.parse_args()

    if args.mark_notified:
        mark_notified(args.mark_notified)
        print(json.dumps({"marked_notified": args.mark_notified}))
        sys.exit(0)

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
    out["blockers"] = track_blockers(blocker_causes, issues, args.task)
    print(json.dumps(out, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
