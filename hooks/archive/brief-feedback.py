#!/usr/bin/env python3
"""Capture and query daily-brief reaction feedback.

Mirrors the pattern of eod-triage-feedback.json for the brief's own
quality loop. The brief writes one entry per run; VM-79 (learning-loop
consumption) reads the history to adapt format.

Store: ~/Projects/Leto/.local-data/brief-feedback.json

Entry schema:
{
  "date": "YYYY-MM-DD",
  "thread_ts": "...",      # Slack thread ts of the brief that day
  "thread_channel": "...", # Slack channel of that brief
  "reaction": "👍"|"⚠️"|"❌"|null,
  "reply_text": null|"...",
  "sections_flagged": [],   # e.g. ["AI NEWS", "INDUSTRY NEWS"] from reply parsing
  "read_attempts": 1|2,     # 2 if second read was needed (late-reaction fix)
  "silence": bool           # true if reaction is null
}

Usage:
    # Append result for a given date (called by daily-brief after reading thread)
    python3 brief-feedback.py --append 2026-06-05 "👍"
    python3 brief-feedback.py --append 2026-06-05 null "Nice brief"
    python3 brief-feedback.py --append 2026-06-05 "⚠️" "" --sections "AI NEWS,INDUSTRY NEWS"
    python3 brief-feedback.py --append 2026-06-05 null --thread-ts 1234.567 --thread-channel D0ABC

    # Query
    python3 brief-feedback.py --summary          # JSON summary
    python3 brief-feedback.py --streak           # just the int silence streak
    python3 brief-feedback.py --last N           # last N entries as JSON

--summary output:
{
  "total_entries": N,
  "with_reaction": N,
  "silence_streak": N,      # consecutive days ending today with no reaction
  "last_reaction": "👍"|"⚠️"|"❌"|null,
  "last_reaction_date": "YYYY-MM-DD"|null,
  "health": "healthy"|"check"|"silent",
  "nudge": "..."            # what the brief NUDGE should say (empty if healthy)
}

health thresholds:
  healthy  — streak < 3
  check    — streak 3–6  → soft nudge ("No reaction for N days — is the brief useful?")
  silent   — streak ≥ 7  → direct ask   ("7d without feedback — is this worth keeping?")
"""

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ_MADRID  = ZoneInfo("Europe/Madrid")
TODAY      = datetime.now(TZ_MADRID).date().isoformat()
STORE      = Path.home() / "Projects" / "Leto" / ".local-data" / "brief-feedback.json"
MAX_ENTRIES = 90   # keep ~3 months


def load() -> dict:
    if STORE.exists():
        try:
            return json.loads(STORE.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return {"entries": []}


def save(data: dict) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    # Trim to MAX_ENTRIES
    if len(data.get("entries", [])) > MAX_ENTRIES:
        data["entries"] = data["entries"][-MAX_ENTRIES:]
    STORE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def silence_streak(entries: list[dict]) -> int:
    """Count consecutive trailing days with reaction=null (silence=true)."""
    streak = 0
    for entry in reversed(entries):
        if entry.get("silence", True):
            streak += 1
        else:
            break
    return streak


def summarize(data: dict) -> dict:
    entries = data.get("entries", [])
    streak  = silence_streak(entries)
    reacted = [e for e in entries if not e.get("silence", True)]

    last_reaction      = reacted[-1].get("reaction") if reacted else None
    last_reaction_date = reacted[-1].get("date")     if reacted else None

    if streak < 3:
        health = "healthy"
        nudge  = ""
    elif streak < 7:
        health = "check"
        nudge  = f"No reaction for {streak} day{'s' if streak != 1 else ''} — is the brief format working? React 👍 good · ⚠️ off · ❌ wrong."
    else:
        health = "silent"
        nudge  = f"{streak} days without feedback. Is the brief still useful? Reply 'yes' to keep format, or 'restructure' to flag for a format review."

    return {
        "total_entries":     len(entries),
        "with_reaction":     len(reacted),
        "silence_streak":    streak,
        "last_reaction":     last_reaction,
        "last_reaction_date":last_reaction_date,
        "health":            health,
        "nudge":             nudge,
    }


def append_entry(
    entry_date: str,
    reaction: str | None,
    reply_text: str = "",
    sections_flagged: list[str] | None = None,
    thread_ts: str = "",
    thread_channel: str = "",
    read_attempts: int = 1,
) -> dict:
    data = load()
    # Overwrite if same date already exists (idempotent re-run)
    data["entries"] = [e for e in data["entries"] if e.get("date") != entry_date]
    data["entries"].append({
        "date":             entry_date,
        "thread_ts":        thread_ts,
        "thread_channel":   thread_channel,
        "reaction":         reaction,
        "reply_text":       reply_text or None,
        "sections_flagged": sections_flagged or [],
        "read_attempts":    read_attempts,
        "silence":          reaction is None,
    })
    save(data)
    return summarize(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])

    sub = parser.add_subparsers(dest="cmd")

    # --append
    app = sub.add_parser("--append", help="Append a feedback entry")

    parser.add_argument("--append", nargs="+", metavar=("DATE", "REACTION"),
                        help="DATE REACTION [reply_text] — REACTION is 👍/⚠️/❌ or null")
    parser.add_argument("--sections", default="",
                        help="Comma-separated section names flagged in reply")
    parser.add_argument("--thread-ts", default="")
    parser.add_argument("--thread-channel", default="")
    parser.add_argument("--read-attempts", type=int, default=1)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--streak", action="store_true")
    parser.add_argument("--last", type=int, default=0, metavar="N")

    args = parser.parse_args()

    if args.append:
        entry_date = args.append[0]
        raw_reaction = args.append[1] if len(args.append) > 1 else "null"
        reply_text   = args.append[2] if len(args.append) > 2 else ""
        reaction = None if raw_reaction.lower() in ("null", "none", "") else raw_reaction
        sections = [s.strip() for s in args.sections.split(",") if s.strip()] if args.sections else []
        result = append_entry(
            entry_date=entry_date,
            reaction=reaction,
            reply_text=reply_text,
            sections_flagged=sections,
            thread_ts=args.thread_ts,
            thread_channel=args.thread_channel,
            read_attempts=args.read_attempts,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    data = load()

    if args.streak:
        print(silence_streak(data.get("entries", [])))
        return

    if args.last:
        print(json.dumps(data.get("entries", [])[-args.last:], indent=2, ensure_ascii=False))
        return

    # Default: --summary
    print(json.dumps(summarize(data), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
