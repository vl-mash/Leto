#!/usr/bin/env python3
"""Check reader-context.md staleness and count pending fact-patch proposals.

Runs as part of the daily-brief PART A to pre-load context for the
"stale facts" section in PART C. No LLM calls — pure file inspection.

Exit codes: always 0 (informational only; surfacing is up to the caller).

Output JSON:
{
  "reader_context": {
    "path": "...",
    "last_updated": "YYYY-MM-DD",      # from frontmatter `updated:` field
    "days_old": N,
    "stale": bool                       # true if > 7 days old
  },
  "patches_pending": N,                 # count of unresolved fact-patch proposals
  "patch_paths": ["..."],               # paths of pending patches (newest first)
  "should_surface": bool                # true if anything needs attention
}

Usage:
    python3 ~/Projects/Leto/hooks/fact-freshen.py
    python3 ~/Projects/Leto/hooks/fact-freshen.py --json      (default, always JSON)
    python3 ~/Projects/Leto/hooks/fact-freshen.py --human     (human-readable summary)
    python3 ~/Projects/Leto/hooks/fact-freshen.py --staleness-days 7  (configure threshold)
"""

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ_MADRID = ZoneInfo("Europe/Madrid")
TODAY = datetime.now(TZ_MADRID).date()

HOME  = Path.home()
VAULT = HOME / "Obsidian Vault" / "Vladimir's Vault"
READER_CONTEXT = VAULT / "40 System" / "reader-context.md"
PATCHES_DIR    = VAULT / "00 Inbox" / "Drafts" / "fact-patches"


def parse_frontmatter_date(path: Path, field: str) -> str | None:
    """Extract a YYYY-MM-DD value from YAML frontmatter in a markdown file."""
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        # Grab everything between the first two `---` lines
        if not text.startswith("---"):
            return None
        end = text.find("---", 3)
        if end < 0:
            return None
        fm = text[3:end]
        m = re.search(rf"^{re.escape(field)}\s*:\s*(.+)$", fm, re.MULTILINE)
        if not m:
            return None
        val = m.group(1).strip().strip("'\"")
        # Accept "YYYY-MM-DD" or "YYYY-MM-DDT..."
        return val[:10] if re.match(r"\d{4}-\d{2}-\d{2}", val) else None
    except OSError:
        return None


def check_reader_context(staleness_days: int) -> dict:
    if not READER_CONTEXT.exists():
        return {
            "path": str(READER_CONTEXT),
            "last_updated": None,
            "days_old": None,
            "stale": True,          # missing = definitely stale
        }
    last_updated_str = parse_frontmatter_date(READER_CONTEXT, "updated")
    if last_updated_str:
        try:
            last_updated = date.fromisoformat(last_updated_str)
            days_old = (TODAY - last_updated).days
        except ValueError:
            last_updated_str = None
            days_old = None
    else:
        days_old = None

    return {
        "path": str(READER_CONTEXT),
        "last_updated": last_updated_str,
        "days_old": days_old,
        "stale": (days_old is None) or (days_old > staleness_days),
    }


def check_pending_patches() -> tuple[int, list[str]]:
    """Return (count, sorted_paths) of pending fact-patch proposals."""
    if not PATCHES_DIR.is_dir():
        return 0, []

    pending = []
    for f in PATCHES_DIR.glob("*.md"):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
            # Check frontmatter status field
            if not text.startswith("---"):
                # No frontmatter — treat as pending
                pending.append(f)
                continue
            end = text.find("---", 3)
            fm = text[3:end] if end > 3 else ""
            m = re.search(r"^status\s*:\s*(.+)$", fm, re.MULTILINE)
            status = m.group(1).strip().strip("'\"").lower() if m else "pending"
            if status == "pending":
                pending.append(f)
        except OSError:
            pass

    # Sort newest first (by filename date prefix YYYY-MM-DD)
    pending.sort(key=lambda p: p.name, reverse=True)
    return len(pending), [str(p) for p in pending]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", default=True,
                        help="Output JSON (default)")
    parser.add_argument("--human", action="store_true",
                        help="Human-readable summary instead of JSON")
    parser.add_argument("--staleness-days", type=int, default=7,
                        help="Days before reader-context.md is considered stale (default 7)")
    args = parser.parse_args()

    rc = check_reader_context(args.staleness_days)
    patch_count, patch_paths = check_pending_patches()
    should_surface = rc["stale"] or patch_count > 0

    out = {
        "reader_context": rc,
        "patches_pending": patch_count,
        "patch_paths": patch_paths,
        "should_surface": should_surface,
    }

    if args.human:
        rc_age = f"{rc['days_old']}d old" if rc['days_old'] is not None else "unknown age"
        stale_marker = " ⚠️ STALE" if rc["stale"] else " ✓"
        print(f"reader-context.md: last updated {rc['last_updated'] or '?'} ({rc_age}){stale_marker}")
        print(f"Pending fact-patches: {patch_count}")
        if patch_paths:
            for p in patch_paths[:5]:
                print(f"  • {Path(p).name}")
        print(f"Should surface: {'yes' if should_surface else 'no'}")
    else:
        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
