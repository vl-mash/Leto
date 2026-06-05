#!/usr/bin/env python3
"""Parse, query, and update the Leto commitment register.

Reads ~/Obsidian Vault/.../40 System/Claude/Commitments.md and returns
structured data for use by VM-77 escalation and the daily-brief NUDGE.

STATUS MODEL
  (none / open) — active, tracks on deadline-aware ladder
  on-hold       — deliberately parked; escalation suppressed; resurfaces after hold-since > 14d
  blocked       — external blocker (someone else must act first); surfaces as FYI not urgent
  done          — completed (use --update to mark; closes via --close-done)
  dropped       — cancelled (use --update to mark)

CORRECTION MECHANISM (VM-77)
  In-session: "mark C-005 on-hold: waiting for capacity data"
  Slack reply: daily-brief nudge thread accepts "on-hold C-005 C-006: reason"
  Python flag:  commitments.py --update C-005 on-hold "waiting for capacity data"

ESCALATION TIERS (deadline-aware, applied only to open/blocked items)
  1. past_due + open        → surface as ⚠️ every day
  2. due_today + open       → surface as 🔴
  3. due_soon (≤2d) + open  → surface as 🟡
  4. no due + since > 21d   → propose disposition (park/drop/redate)
  5. no due + since > 14d   → direct question ("still active?")
  6. no due + since 7-13d   → soft mention
  7. on-hold (any age)      → suppressed unless hold-since > 14d → "hold still valid?"
  8. blocked                → surface as FYI (no urgency) until unblocked

Usage:
    python3 commitments.py                         # human-readable summary
    python3 commitments.py --json                  # all open items as JSON
    python3 commitments.py --summary               # counts JSON
    python3 commitments.py --past-due              # overdue items only (JSON)
    python3 commitments.py --escalation-needed     # items requiring NUDGE action (JSON)
    python3 commitments.py --next-id               # print next C-NNN
    python3 commitments.py --section outbound|inbound
    python3 commitments.py --update C-005 on-hold "waiting for Daria inputs"
    python3 commitments.py --update C-001 done
    python3 commitments.py --update C-003 redate 2026-07-31
    python3 commitments.py --update C-004 open      # clear on-hold, reopen
"""

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ_MADRID = ZoneInfo("Europe/Madrid")
TODAY     = datetime.now(TZ_MADRID).date()
VAULT     = Path.home() / "Obsidian Vault" / "Vladimir's Vault"
REGISTER  = VAULT / "40 System" / "Claude" / "Commitments.md"

COMMENT_RE = re.compile(r"<!--(.+?)-->", re.DOTALL)
OPEN_STATUSES   = {"", "open", "blocked"}
CLOSED_STATUSES = {"done", "dropped"}


# ── Parsing ──────────────────────────────────────────────────────────────────

def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s.strip())
    except (ValueError, AttributeError):
        return None


def parse_meta(comment_text: str) -> dict[str, str]:
    """Split on | and partition on first : to get key→value dict."""
    result: dict[str, str] = {}
    for part in comment_text.split("|"):
        part = part.strip()
        if ":" in part:
            key, _, val = part.partition(":")
            result[key.strip()] = val.strip()
    return result


def parse_register() -> list[dict]:
    if not REGISTER.exists():
        return []

    items = []
    current_section = None

    with open(REGISTER, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            stripped = line.strip()
            low = stripped.lower()

            # Detect section headers
            if "## outbound" in low:
                current_section = "outbound"
                continue
            elif "## inbound" in low:
                current_section = "inbound"
                continue
            elif "## closed" in low:
                current_section = "closed"
                continue

            if not (stripped.startswith("- [ ]") or stripped.startswith("- [x]")):
                continue
            if current_section is None:
                continue

            closed_checkbox = stripped.startswith("- [x]")
            text_with_meta  = stripped[5:].strip()

            m = COMMENT_RE.search(text_with_meta)
            if m:
                text = text_with_meta[:m.start()].strip()
                meta = parse_meta(m.group(1))
            else:
                text = text_with_meta
                meta = {}

            c_id         = meta.get("id", "")
            since_str    = meta.get("since")
            due_str      = meta.get("due")
            direction    = "to" if "to" in meta else ("from" if "from" in meta else "")
            counterparty = meta.get("to") or meta.get("from") or ""
            source       = meta.get("source", "")
            status       = meta.get("status", "").lower()
            hold_reason  = meta.get("hold-reason", "")
            hold_since_str = meta.get("hold-since")
            team         = meta.get("team", "VM")
            linear_id    = meta.get("linear-id", "")
            ticket_field = meta.get("ticket", "")  # "none" = monitoring only, no ticket

            since_date     = parse_date(since_str)
            due_date       = parse_date(due_str)
            hold_since     = parse_date(hold_since_str)

            since_days     = (TODAY - since_date).days if since_date else None
            days_until_due = (due_date - TODAY).days   if due_date   else None
            hold_since_days= (TODAY - hold_since).days if hold_since else None

            # Effective closed: checkbox OR status in done/dropped
            closed = closed_checkbox or status in CLOSED_STATUSES

            past_due = (
                days_until_due is not None
                and days_until_due < 0
                and not closed
                and status not in ("on-hold", "blocked")
            )

            # Escalation tier (for open/blocked items only; on-hold suppressed)
            escalation = _escalation_tier(
                status=status,
                closed=closed,
                since_days=since_days,
                days_until_due=days_until_due,
                hold_since_days=hold_since_days,
            )

            items.append({
                "id":             c_id,
                "text":           text,
                "section":        current_section,
                "status":         status or "open",
                "since":          since_str,
                "since_days":     since_days,
                "due":            due_str,
                "past_due":       past_due,
                "days_until_due": days_until_due,
                "counterparty":   counterparty or None,
                "direction":      direction or None,
                "source":         source or None,
                "hold_reason":    hold_reason or None,
                "hold_since":     hold_since_str or None,
                "hold_since_days":hold_since_days,
                "escalation":     escalation,
                "closed":         closed,
                "team":           team,
                "linear_id":      linear_id or None,
                "ticket":         ticket_field or None,
                "monitoring_only": ticket_field == "none",
            })

    return items


def _escalation_tier(
    status: str,
    closed: bool,
    since_days: int | None,
    days_until_due: int | None,
    hold_since_days: int | None,
) -> str:
    """Return the escalation tier label for this commitment."""
    if closed:
        return "closed"
    if status == "on-hold":
        if hold_since_days is not None and hold_since_days > 14:
            return "hold-stale"      # hold may be outdated — resurface
        return "suppressed"
    if status == "blocked":
        return "blocked-fyi"         # surface as FYI, not urgent
    # Open / default
    if days_until_due is not None:
        if days_until_due < 0:
            return "past-due"        # ⚠️ overdue
        if days_until_due == 0:
            return "due-today"       # 🔴 due today
        if days_until_due <= 2:
            return "due-soon"        # 🟡 due in 1-2 days
    # No due date — use age ladder
    if since_days is None:
        return "open"
    if since_days >= 21:
        return "propose-disposition"
    if since_days >= 14:
        return "direct-question"
    if since_days >= 7:
        return "soft-mention"
    return "open"


# ── Summaries ─────────────────────────────────────────────────────────────────

def summarize(items: list[dict]) -> dict:
    open_items = [c for c in items if not c["closed"]]
    active     = [c for c in open_items if c["status"] not in ("on-hold",)]

    return {
        "total_open":        len(open_items),
        "outbound_open":     sum(1 for c in open_items if c["section"] == "outbound"),
        "inbound_open":      sum(1 for c in open_items if c["section"] == "inbound"),
        "on_hold":           sum(1 for c in open_items if c["status"] == "on-hold"),
        "blocked":           sum(1 for c in open_items if c["status"] == "blocked"),
        "past_due":          sum(1 for c in active if c["escalation"] == "past-due"),
        "due_today":         sum(1 for c in active if c["escalation"] == "due-today"),
        "due_soon":          sum(1 for c in active if c["escalation"] == "due-soon"),
        "hold_stale":        sum(1 for c in open_items if c["escalation"] == "hold-stale"),
        "no_due_date_old":   sum(1 for c in active
                                if c["due"] is None and c["since_days"] is not None
                                and c["since_days"] > 14),
    }


def escalation_needed(items: list[dict]) -> list[dict]:
    """Items the daily-brief NUDGE should act on, sorted by urgency."""
    priority = {
        "past-due": 0, "due-today": 1, "due-soon": 2,
        "hold-stale": 3,
        "propose-disposition": 4, "direct-question": 5, "soft-mention": 6,
        "blocked-fyi": 7,
    }
    actionable = [c for c in items
                  if not c["closed"] and c["escalation"] in priority]
    return sorted(actionable, key=lambda c: priority.get(c["escalation"], 99))


def next_id(items: list[dict]) -> str:
    used = set()
    for c in items:
        m = re.match(r"C-(\d+)", c.get("id") or "")
        if m:
            used.add(int(m.group(1)))
    n = 1
    while n in used:
        n += 1
    return f"C-{n:03d}"


# ── In-place update ───────────────────────────────────────────────────────────

def _serialize_meta(meta: dict[str, str]) -> str:
    """Serialize a metadata dict back to inline comment content.
    Order: id | since | due | to/from | status | hold-reason | hold-since | source
    """
    ORDER = ["id", "since", "due", "to", "from",
             "status", "hold-reason", "hold-since", "source"]
    parts = []
    for key in ORDER:
        if key in meta:
            parts.append(f"{key}: {meta[key]}")
    # Any keys not in ORDER
    for key, val in meta.items():
        if key not in ORDER:
            parts.append(f"{key}: {val}")
    return " | ".join(parts)


def set_linear_id(c_id: str, linear_id: str) -> bool:
    """Write a linear-id field into an existing commitment entry. Idempotent."""
    if not REGISTER.exists():
        return False
    lines = REGISTER.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        m = COMMENT_RE.search(line)
        if not m:
            continue
        meta = parse_meta(m.group(1))
        if meta.get("id", "").strip() != c_id:
            continue
        meta["linear-id"] = linear_id
        new_comment = f"<!-- {_serialize_meta(meta)} -->"
        lines[i] = line[:m.start()] + new_comment + line[m.end():]
        REGISTER.write_text("".join(lines), encoding="utf-8")
        return True
    return False


def update_commitment(c_id: str, new_status: str, reason: str = "", new_due: str = "") -> bool:
    """
    Update a commitment entry in-place.
    new_status: on-hold | blocked | open | done | dropped
    reason: optional hold-reason (used when status=on-hold or blocked)
    new_due: new due date string YYYY-MM-DD (used when action=redate)
    Returns True on success.
    """
    if not REGISTER.exists():
        print(f"ERROR: register not found at {REGISTER}", file=sys.stderr)
        return False

    lines = REGISTER.read_text(encoding="utf-8").splitlines(keepends=True)
    found = False

    for i, line in enumerate(lines):
        m = COMMENT_RE.search(line)
        if not m:
            continue
        meta = parse_meta(m.group(1))
        if meta.get("id", "").strip() != c_id:
            continue

        found = True
        # Apply the mutation
        if new_status == "redate":
            if new_due:
                meta["due"] = new_due
                # Don't change status
        elif new_status in ("done", "dropped"):
            meta["status"] = new_status
            # Will close via checkbox change below
            meta.pop("hold-reason", None)
            meta.pop("hold-since", None)
        elif new_status == "on-hold":
            meta["status"] = "on-hold"
            if reason:
                meta["hold-reason"] = reason
            meta["hold-since"] = TODAY.isoformat()
        elif new_status == "blocked":
            meta["status"] = "blocked"
            if reason:
                meta["hold-reason"] = reason
            meta["hold-since"] = TODAY.isoformat()
        elif new_status == "open":
            # Clear hold fields, reopen
            meta.pop("status", None)
            meta.pop("hold-reason", None)
            meta.pop("hold-since", None)

        # Rebuild the comment
        new_comment = f"<!-- {_serialize_meta(meta)} -->"
        # Replace old comment in the line
        new_line = line[:m.start()] + new_comment + line[m.end():]

        # Handle done/dropped: flip [ ] to [x]
        if new_status in ("done", "dropped"):
            new_line = re.sub(r"^(\s*)-\s*\[\s*\]", r"\1- [x]", new_line)

        lines[i] = new_line
        break

    if not found:
        print(f"ERROR: {c_id} not found in register", file=sys.stderr)
        return False

    REGISTER.write_text("".join(lines), encoding="utf-8")
    return True


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json",     action="store_true")
    parser.add_argument("--summary",  action="store_true")
    parser.add_argument("--past-due", action="store_true",
                        help="Only overdue items (JSON)")
    parser.add_argument("--escalation-needed", action="store_true",
                        help="Items needing NUDGE action, sorted by urgency (JSON)")
    parser.add_argument("--next-id",  action="store_true")
    parser.add_argument("--unlinked", action="store_true",
                        help="Open outbound entries missing linear-id (excluding monitoring-only). JSON.")
    parser.add_argument("--set-linear-id", nargs=2, metavar=("C_ID", "LINEAR_ID"),
                        help="Write linear-id to a commitment entry. E.g. --set-linear-id C-012 VM-91")
    parser.add_argument("--section",  choices=["outbound", "inbound", "closed"])
    parser.add_argument("--update", nargs="+", metavar=("ID", "STATUS"),
                        help=(
                            "Update a commitment: --update C-005 on-hold 'reason' "
                            "OR --update C-001 done OR --update C-003 redate YYYY-MM-DD"
                        ))
    args = parser.parse_args()

    # ── Set linear-id path ──
    if args.set_linear_id:
        c_id, linear_id = args.set_linear_id
        ok = set_linear_id(c_id, linear_id)
        if ok:
            items = parse_register()
            updated = next((c for c in items if c["id"] == c_id), None)
            print(json.dumps(updated or {"id": c_id, "linear_id": linear_id, "updated": True}, indent=2))
        else:
            print(json.dumps({"error": f"{c_id} not found"}, indent=2), file=sys.stderr)
        sys.exit(0 if ok else 1)

    # ── Update path ──
    if args.update:
        c_id = args.update[0]
        action = args.update[1] if len(args.update) > 1 else ""
        extra  = args.update[2] if len(args.update) > 2 else ""
        new_due = extra if action == "redate" else ""
        reason  = extra if action not in ("redate", "done", "dropped", "open") else ""
        ok = update_commitment(c_id, action, reason=reason, new_due=new_due)
        if ok:
            items = parse_register()
            updated = next((c for c in items if c["id"] == c_id), None)
            if updated:
                print(json.dumps(updated, indent=2))
            else:
                # Item was closed — confirm
                print(json.dumps({"id": c_id, "status": action, "updated": True}, indent=2))
        sys.exit(0 if ok else 1)

    # ── Query paths ──
    items = parse_register()

    if args.section:
        items = [c for c in items if c["section"] == args.section]

    if args.next_id:
        print(next_id(items))
        return

    if args.summary:
        print(json.dumps(summarize(items), indent=2))
        return

    open_items = [c for c in items if not c["closed"]]

    if getattr(args, "unlinked", False):
        # Open outbound commitments with no linear-id and not monitoring-only
        unlinked = [
            c for c in open_items
            if not c["linear_id"]
            and not c["monitoring_only"]
            and c["section"] != "closed"
        ]
        print(json.dumps(unlinked, indent=2))
        return

    if getattr(args, "past_due", False):
        print(json.dumps([c for c in open_items if c["past_due"]], indent=2))
        return

    if getattr(args, "escalation_needed", False):
        print(json.dumps(escalation_needed(items), indent=2))
        return

    if args.json:
        print(json.dumps(open_items, indent=2))
        return

    # ── Human-readable default ──
    s = summarize(items)
    print(f"Commitment register — {TODAY.isoformat()}")
    print(f"  Open: {s['total_open']} ({s['outbound_open']} out · {s['inbound_open']} in"
          + (f" · {s['on_hold']} on-hold" if s["on_hold"] else "")
          + (f" · {s['blocked']} blocked" if s["blocked"] else "") + ")")
    if s["past_due"]:
        print(f"  ⚠️  Past due: {s['past_due']}")
    if s["due_today"]:
        print(f"  🔴 Due today: {s['due_today']}")
    if s["due_soon"]:
        print(f"  🟡 Due soon (≤2d): {s['due_soon']}")
    if s["hold_stale"]:
        print(f"  🔵 Hold stale (>14d): {s['hold_stale']}")
    if s["no_due_date_old"]:
        print(f"  ❓ No due date, >14d old: {s['no_due_date_old']}")
    print()

    TIER_ICON = {
        "past-due": "⚠️", "due-today": "🔴", "due-soon": "🟡",
        "hold-stale": "🔵", "blocked-fyi": "ℹ️",
        "propose-disposition": "❓", "direct-question": "❓", "soft-mention": "·",
        "suppressed": "💤", "open": "·", "closed": "✓",
    }

    for section in ("outbound", "inbound"):
        section_items = [c for c in open_items if c["section"] == section]
        if not section_items:
            continue
        label = "Outbound" if section == "outbound" else "Inbound"
        print(f"  {label}:")
        for c in section_items:
            icon = TIER_ICON.get(c["escalation"], "·")
            due_str = f" [DUE {c['due']}]" if c["due"] else ""
            age_str = f" ({c['since_days']}d)" if c["since_days"] is not None else ""
            party   = f" {'→' if c['direction'] == 'to' else '←'} {c['counterparty']}" if c["counterparty"] else ""
            hold    = f" [hold: {c['hold_reason']}]" if c["status"] == "on-hold" and c.get("hold_reason") else (
                      " [on-hold]" if c["status"] == "on-hold" else "")
            print(f"  {icon} {c['id']}: {c['text'][:60]}{due_str}{hold}{age_str}{party}")
        print()


if __name__ == "__main__":
    main()
