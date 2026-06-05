#!/usr/bin/env python3
"""Parse and query the Leto commitment register.

Reads ~/Obsidian Vault/.../40 System/Claude/Commitments.md and returns
structured data for use by other hooks (VM-77 escalation, daily-brief NUDGE).

Usage:
    python3 commitments.py                  # summary (human-readable)
    python3 commitments.py --json           # full list as JSON
    python3 commitments.py --summary        # counts + overdue (JSON)
    python3 commitments.py --past-due       # only overdue items (JSON)
    python3 commitments.py --next-id        # print next available C-NNN
    python3 commitments.py --section outbound   # filter by section
    python3 commitments.py --section inbound

JSON output for --json / --past-due (list of commitment objects):
[
  {
    "id": "C-001",
    "text": "Send Daria the survey template",
    "section": "outbound" | "inbound",
    "since": "2026-05-21",
    "since_days": 15,
    "due": "2026-06-05" | null,
    "past_due": true | false,
    "days_until_due": -1 | null,   # negative = past due
    "counterparty": "Daria Senina",
    "direction": "to" | "from",
    "source": "TODO.md",
    "closed": false
  },
  ...
]

JSON output for --summary:
{
  "total_open": N,
  "outbound_open": N,
  "inbound_open": N,
  "past_due": N,
  "due_today": N,
  "due_soon": N,        # due within 2 days
  "no_due_date_old": N  # open, no due date, since > 14 days
}
"""

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ_MADRID   = ZoneInfo("Europe/Madrid")
TODAY       = datetime.now(TZ_MADRID).date()
VAULT       = Path.home() / "Obsidian Vault" / "Vladimir's Vault"
REGISTER    = VAULT / "40 System" / "Claude" / "Commitments.md"

# Regex to find the <!-- ... --> comment block
COMMENT_RE = re.compile(r"<!--(.+?)-->")

SECTION_MAP = {
    "outbound": "outbound",
    "inbound":  "inbound",
    "closed":   "closed",
}


def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s.strip())
    except (ValueError, AttributeError):
        return None


def parse_register() -> list[dict]:
    if not REGISTER.exists():
        return []

    commitments = []
    current_section = None

    with open(REGISTER, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            stripped = line.strip()

            # Detect section headers
            low = stripped.lower()
            if "## outbound" in low:
                current_section = "outbound"
                continue
            elif "## inbound" in low:
                current_section = "inbound"
                continue
            elif "## closed" in low:
                current_section = "closed"
                continue

            # Parse list items
            if not (stripped.startswith("- [ ]") or stripped.startswith("- [x]")):
                continue
            if current_section is None:
                continue

            closed = stripped.startswith("- [x]")
            text_with_meta = stripped[5:].strip()

            # Extract text (before comment) and metadata
            m = COMMENT_RE.search(text_with_meta)
            if m:
                text = text_with_meta[:m.start()].strip()
                # Parse fields by splitting on | — robust against dashes in values
                meta: dict[str, str] = {}
                for part in m.group(1).split("|"):
                    part = part.strip()
                    if ":" in part:
                        key, _, val = part.partition(":")
                        meta[key.strip()] = val.strip()
                c_id         = meta.get("id", "")
                since_str    = meta.get("since")
                due_str      = meta.get("due")
                direction    = meta.get("to") and "to" or meta.get("from") and "from" or ""
                counterparty = meta.get("to") or meta.get("from") or ""
                source       = meta.get("source", "")
            else:
                text = text_with_meta
                c_id = since_str = due_str = ""
                direction = counterparty = source = ""

            since_date = parse_date(since_str)
            due_date   = parse_date(due_str)

            since_days     = (TODAY - since_date).days if since_date else None
            days_until_due = (due_date - TODAY).days   if due_date   else None
            past_due       = (days_until_due is not None and days_until_due < 0) and not closed

            commitments.append({
                "id":            c_id,
                "text":          text,
                "section":       current_section,
                "since":         since_str or None,
                "since_days":    since_days,
                "due":           due_str or None,
                "past_due":      past_due,
                "days_until_due": days_until_due,
                "counterparty":  counterparty or None,
                "direction":     direction or None,
                "source":        source or None,
                "closed":        closed,
            })

    return commitments


def summarize(items: list[dict]) -> dict:
    open_items = [c for c in items if not c["closed"]]
    return {
        "total_open":       len(open_items),
        "outbound_open":    sum(1 for c in open_items if c["section"] == "outbound"),
        "inbound_open":     sum(1 for c in open_items if c["section"] == "inbound"),
        "past_due":         sum(1 for c in open_items if c["past_due"]),
        "due_today":        sum(1 for c in open_items if c["days_until_due"] == 0),
        "due_soon":         sum(1 for c in open_items
                               if c["days_until_due"] is not None
                               and 0 < c["days_until_due"] <= 2),
        "no_due_date_old":  sum(1 for c in open_items
                               if c["due"] is None
                               and c["since_days"] is not None
                               and c["since_days"] > 14),
    }


def next_id(items: list[dict]) -> str:
    used = set()
    for c in items:
        m = re.match(r"C-(\d+)", c["id"])
        if m:
            used.add(int(m.group(1)))
    n = 1
    while n in used:
        n += 1
    return f"C-{n:03d}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json",     action="store_true", help="Full list as JSON")
    parser.add_argument("--summary",  action="store_true", help="Summary counts as JSON")
    parser.add_argument("--past-due", action="store_true", help="Only overdue items (JSON)")
    parser.add_argument("--next-id",  action="store_true", help="Print next available C-NNN")
    parser.add_argument("--section",  choices=["outbound", "inbound", "closed"],
                        help="Filter by section")
    args = parser.parse_args()

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

    if args.past_due:
        print(json.dumps([c for c in open_items if c["past_due"]], indent=2))
        return

    if args.json:
        print(json.dumps(open_items, indent=2))
        return

    # Human-readable default
    s = summarize(items)
    print(f"Commitment register — {TODAY.isoformat()}")
    print(f"  Open: {s['total_open']} ({s['outbound_open']} outbound · {s['inbound_open']} inbound)")
    if s["past_due"]:
        print(f"  ⚠️  Past due: {s['past_due']}")
    if s["due_today"]:
        print(f"  🔴 Due today: {s['due_today']}")
    if s["due_soon"]:
        print(f"  🟡 Due soon (≤2d): {s['due_soon']}")
    if s["no_due_date_old"]:
        print(f"  🔵 No due date, >14d old: {s['no_due_date_old']}")
    print()

    for section in ("outbound", "inbound"):
        section_items = [c for c in open_items if c["section"] == section]
        if not section_items:
            continue
        label = "Outbound" if section == "outbound" else "Inbound"
        print(f"  {label}:")
        for c in section_items:
            due_str = f" [DUE {c['due']}{'⚠️' if c['past_due'] else ''}]" if c["due"] else ""
            age_str = f" ({c['since_days']}d old)" if c["since_days"] is not None else ""
            party_str = f" {'to' if c['direction'] == 'to' else 'from'}: {c['counterparty']}" if c["counterparty"] else ""
            print(f"    {c['id']}: {c['text']}{due_str}{age_str}{party_str}")
        print()


if __name__ == "__main__":
    main()
