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
LINEAR_API_KEY     = CFG / "linear-api-key"
SLACK_BOT_TOKEN    = CFG / "slack-bot-token"
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
    for name, path in [
        ("linear-api-key",  LINEAR_API_KEY),
        ("slack-bot-token", SLACK_BOT_TOKEN),
        ("cost-cap.json",   COST_CAP_FILE),
    ]:
        if not path.exists():
            issue(issues, "warn", name, f"missing: {path}")


def check_vault_root(issues: list) -> None:
    if not VAULT.is_dir():
        issue(issues, "warn", "vault-root", f"vault not accessible at {VAULT}")


def check_leto_repo(issues: list) -> None:
    if not LETO_CLAUDE_MD.exists():
        issue(issues, "warn", "leto-repo", f"CLAUDE.md not found at {LETO_CLAUDE_MD}")


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

    # 3. Vault root + repo integrity (warn only)
    check_vault_root(issues)
    check_leto_repo(issues)

    # 4. Repairs (silent — just log what changed)
    repair_granola_registry(repaired, issues)
    repair_daily_journal(repaired, issues)
    repair_granola_sources_dir(repaired, issues)
    repair_sessions_dir(repaired, issues)

    # 5. Determine overall status
    warn_count = sum(1 for i in issues if i["level"] == "warn")
    status = "warn" if warn_count > 0 else "ok"

    print(json.dumps(result(status, issues, repaired), indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
