#!/usr/bin/env python3
"""Summarize doubt-stop hook spend.

Reads ~/.claude/logs/doubt-stop/summary.csv. Prints rollups for today,
this week, last 30 days. Lists top sessions. Optional --threshold X exits
non-zero if today's spend exceeds $X — wire into a shell prompt or cron
for alerting.

Usage:
    python3 usage.py
    python3 usage.py --threshold 5.00
    python3 usage.py --json
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

SUMMARY_CSV = Path.home() / ".claude" / "logs" / "doubt-stop" / "summary.csv"
ERROR_LOG = Path.home() / ".claude" / "logs" / "doubt-stop" / "errors.log"


def load_rows():
    if not SUMMARY_CSV.exists():
        return []
    with open(SUMMARY_CSV, newline="") as fh:
        return list(csv.DictReader(fh))


def parse_date(ts: str) -> date | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts).date()
    except ValueError:
        return None


def summarize(rows, since: date) -> dict:
    """Aggregate stats for rows on/after `since`."""
    total_cost = 0.0
    invocations = 0
    ok = miss = unv = 0
    for row in rows:
        d = parse_date(row.get("timestamp", ""))
        if not d or d < since:
            continue
        invocations += 1
        try:
            total_cost += float(row.get("cost_usd") or 0.0)
        except ValueError:
            pass
        try:
            ok += int(row.get("ok") or 0)
            miss += int(row.get("miss") or 0)
            unv += int(row.get("unverifiable") or 0)
        except ValueError:
            pass
    return {
        "cost_usd": round(total_cost, 4),
        "invocations": invocations,
        "ok": ok,
        "miss": miss,
        "unverifiable": unv,
    }


def top_sessions(rows, since: date, n: int = 5):
    bucket = defaultdict(lambda: {"cost": 0.0, "ok": 0, "miss": 0, "unv": 0, "n": 0})
    for row in rows:
        d = parse_date(row.get("timestamp", ""))
        if not d or d < since:
            continue
        sid = row.get("session_id", "?")
        b = bucket[sid]
        b["n"] += 1
        try:
            b["cost"] += float(row.get("cost_usd") or 0.0)
            b["ok"] += int(row.get("ok") or 0)
            b["miss"] += int(row.get("miss") or 0)
            b["unv"] += int(row.get("unverifiable") or 0)
        except ValueError:
            pass
    return sorted(bucket.items(), key=lambda kv: kv[1]["cost"], reverse=True)[:n]


def count_errors_since(since: date) -> int:
    if not ERROR_LOG.exists():
        return 0
    count = 0
    with open(ERROR_LOG) as fh:
        for line in fh:
            d = parse_date(line.split()[0] if line.split() else "")
            if d and d >= since:
                count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--threshold", type=float, default=None,
                        help="Exit non-zero if today's spend exceeds this amount (USD)")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    rows = load_rows()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    last_30 = today - timedelta(days=30)

    today_stats = summarize(rows, today)
    week_stats = summarize(rows, week_start)
    month_stats = summarize(rows, last_30)
    errors_today = count_errors_since(today)
    errors_week = count_errors_since(week_start)
    top = top_sessions(rows, today, n=5)

    if args.json:
        out = {
            "today": today_stats,
            "week": week_stats,
            "last_30_days": month_stats,
            "errors_today": errors_today,
            "errors_this_week": errors_week,
            "top_sessions_today": [
                {"session_id": sid, **{k: round(v, 4) if k == "cost" else v for k, v in b.items()}}
                for sid, b in top
            ],
        }
        print(json.dumps(out, indent=2))
    else:
        print(f"Doubt-stop usage — {today.isoformat()}")
        print()
        print(f"  Today        ${today_stats['cost_usd']:>7.4f}   ({today_stats['invocations']:>3} invocations · "
              f"OK={today_stats['ok']} MISS={today_stats['miss']} UNV={today_stats['unverifiable']} · errors={errors_today})")
        print(f"  This week    ${week_stats['cost_usd']:>7.4f}   ({week_stats['invocations']:>3} invocations · errors={errors_week})")
        print(f"  Last 30d     ${month_stats['cost_usd']:>7.4f}   ({month_stats['invocations']:>3} invocations)")
        if args.threshold is not None:
            print(f"  Threshold    ${args.threshold:>7.2f}   (alert if today exceeds)")
        if top:
            print()
            print("  Top sessions today:")
            for sid, b in top:
                print(f"    {sid[:32]:<32}  ${b['cost']:>7.4f}  OK={b['ok']} MISS={b['miss']} UNV={b['unv']} ({b['n']} calls)")
        if not rows:
            print("\n  (no data — hook hasn't fired yet or summary.csv missing)")

    if args.threshold is not None and today_stats["cost_usd"] > args.threshold:
        sys.exit(1)


if __name__ == "__main__":
    main()
