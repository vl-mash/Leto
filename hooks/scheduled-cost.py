#!/usr/bin/env python3
"""Estimate scheduled-task API spend from Claude Code session JSONL files.

Reads all sdk-cli sessions across ~/.claude/projects/ and computes estimated
cost at full Anthropic API rates — the pricing that applies post-June-15-2026
when programmatic usage draws from the separate Agent-SDK credit pool.

Distinguishes:
  - "tasks"   sdk-cli sessions on non-haiku models (daily-brief, granola-intake, etc.)
  - "hooks"   sdk-cli sessions on haiku model (doubt-stop hook)
  - "total"   both combined — the full programmatic spend billed to the credit pool

Usage:
    python3 scheduled-cost.py
    python3 scheduled-cost.py --threshold 5.00   # exit 1 if today > $5
    python3 scheduled-cost.py --pause-if-over 10.00  # write pause flag if today > $10
    python3 scheduled-cost.py --days 7           # per-day breakdown for last N days
    python3 scheduled-cost.py --json             # machine-readable output

Pause flag: ~/.config/leto/schedulers-paused
  Written by --pause-if-over when today's spend exceeds the cap.
  Checked by each scheduler's preflight (VM-74 — self-healing preflight).
  Resume: rm ~/.config/leto/schedulers-paused
"""

import argparse
import glob
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECTS_DIR = Path.home() / ".claude" / "projects"
PAUSE_FLAG = Path.home() / ".config" / "leto" / "schedulers-paused"
COST_CAP_FILE = Path.home() / ".config" / "leto" / "cost-cap.json"

TZ_MADRID = ZoneInfo("Europe/Madrid")

# Full Anthropic API list prices (USD per million tokens, post-June-15 pool rates).
# Keyed by model-family prefix — matched with str.startswith().
MODEL_PRICES: list[tuple[str, dict]] = [
    ("claude-opus-4",    {"input": 15.00, "cache_write":  18.75, "cache_read": 1.50,  "output": 75.00}),
    ("claude-opus-3-7",  {"input": 15.00, "cache_write":  18.75, "cache_read": 1.50,  "output": 75.00}),
    ("claude-sonnet-4",  {"input":  3.00, "cache_write":   3.75, "cache_read": 0.30,  "output": 15.00}),
    ("claude-sonnet-3-7",{"input":  3.00, "cache_write":   3.75, "cache_read": 0.30,  "output": 15.00}),
    ("claude-haiku-4",   {"input":  0.80, "cache_write":   1.00, "cache_read": 0.08,  "output":  4.00}),
    ("claude-haiku-3",   {"input":  0.25, "cache_write":   0.30, "cache_read": 0.03,  "output":  1.25}),
]
DEFAULT_PRICE = {"input": 3.00, "cache_write": 3.75, "cache_read": 0.30, "output": 15.00}


def price_for(model: str | None) -> dict:
    if not model:
        return DEFAULT_PRICE
    for prefix, p in MODEL_PRICES:
        if model.startswith(prefix):
            return p
    return DEFAULT_PRICE


def is_haiku(model: str | None) -> bool:
    return bool(model and "haiku" in model.lower())


def est_cost(usage: dict, model: str | None) -> float:
    p = price_for(model)
    return (
        usage.get("input_tokens", 0)                    * p["input"]       / 1_000_000
        + usage.get("cache_creation_input_tokens", 0)   * p["cache_write"] / 1_000_000
        + usage.get("cache_read_input_tokens", 0)       * p["cache_read"]  / 1_000_000
        + usage.get("output_tokens", 0)                 * p["output"]      / 1_000_000
    )


def ts_to_date(ts: str) -> date | None:
    """Parse ISO timestamp → local Madrid date."""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone(TZ_MADRID).date()
    except (ValueError, TypeError):
        return None


def load_sessions() -> dict:
    """
    Returns sessions dict keyed by session_id.
    Each value: {model, cost_usd, input_tokens, cache_creation, cache_read, output_tokens,
                 rows, project, first_date, last_date, kind}
    kind = "task" | "hook"
    """
    sessions: dict = defaultdict(lambda: {
        "model": None, "cost_usd": 0.0,
        "input_tokens": 0, "cache_creation": 0, "cache_read": 0, "output_tokens": 0,
        "rows": 0, "project": None, "first_date": None, "last_date": None, "kind": "task",
    })

    for jsonl_path in glob.iglob(str(PROJECTS_DIR / "**" / "*.jsonl"), recursive=True):
        try:
            with open(jsonl_path) as fh:
                for raw in fh:
                    row = json.loads(raw)
                    if row.get("entrypoint") != "sdk-cli":
                        continue
                    sid = row.get("sessionId", "")
                    if not sid:
                        continue
                    msg = row.get("message", {})
                    if not isinstance(msg, dict):
                        continue
                    usage = msg.get("usage", {})
                    if not isinstance(usage, dict):
                        continue
                    model = msg.get("model") or sessions[sid]["model"]
                    cost = est_cost(usage, model)
                    d = ts_to_date(row.get("timestamp", ""))

                    s = sessions[sid]
                    if model:
                        s["model"] = model
                    s["cost_usd"] += cost
                    s["input_tokens"] += usage.get("input_tokens", 0)
                    s["cache_creation"] += usage.get("cache_creation_input_tokens", 0)
                    s["cache_read"] += usage.get("cache_read_input_tokens", 0)
                    s["output_tokens"] += usage.get("output_tokens", 0)
                    s["rows"] += 1
                    # project name = parent dir of the jsonl
                    p = Path(jsonl_path)
                    s["project"] = p.parent.name if "subagents" not in str(p) else p.parent.parent.name
                    if d:
                        if not s["first_date"] or d < s["first_date"]:
                            s["first_date"] = d
                        if not s["last_date"] or d > s["last_date"]:
                            s["last_date"] = d
                    s["kind"] = "hook" if is_haiku(s["model"]) else "task"
        except (OSError, json.JSONDecodeError):
            pass

    return dict(sessions)


def aggregate_by_date(sessions: dict, kind_filter: str | None = None) -> dict[date, float]:
    """Sum cost per day. kind_filter: None=all, 'task', 'hook'."""
    by_date: dict[date, float] = defaultdict(float)
    for s in sessions.values():
        if kind_filter and s["kind"] != kind_filter:
            continue
        d = s.get("last_date") or s.get("first_date")
        if d:
            by_date[d] += s["cost_usd"]
    return dict(by_date)


def rollup(by_date: dict[date, float], since: date) -> float:
    return round(sum(v for d, v in by_date.items() if d >= since), 4)


def load_cost_cap() -> dict:
    if COST_CAP_FILE.exists():
        try:
            with open(COST_CAP_FILE) as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            pass
    return {"daily_cap_usd": 10.00, "monthly_credit_usd": 100.00}


def write_pause_flag(daily_spend: float, cap: float) -> None:
    PAUSE_FLAG.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "paused_at": datetime.now(TZ_MADRID).isoformat(),
        "reason": f"daily spend ${daily_spend:.4f} exceeded cap ${cap:.2f}",
        "daily_spend_usd": round(daily_spend, 4),
        "cap_usd": cap,
        "cleared_at": None,
    }
    with open(PAUSE_FLAG, "w") as fh:
        json.dump(payload, fh, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--threshold", type=float, default=None,
                        help="Exit non-zero if today's total spend exceeds this (USD)")
    parser.add_argument("--pause-if-over", type=float, default=None, metavar="USD",
                        help="Write pause flag if today's spend exceeds this cap (USD)")
    parser.add_argument("--days", type=int, default=0,
                        help="Show per-day breakdown for last N days")
    parser.add_argument("--json", action="store_true",
                        help="Machine-readable JSON output")
    args = parser.parse_args()

    sessions = load_sessions()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())   # Monday
    last_30 = today - timedelta(days=30)

    cap_config = load_cost_cap()
    monthly_credit = cap_config.get("monthly_credit_usd", 100.0)
    daily_cap = args.pause_if_over or cap_config.get("daily_cap_usd", 10.0)

    all_by_date   = aggregate_by_date(sessions)
    task_by_date  = aggregate_by_date(sessions, "task")
    hook_by_date  = aggregate_by_date(sessions, "hook")

    today_total  = round(all_by_date.get(today, 0.0), 4)
    week_total   = rollup(all_by_date, week_start)
    month_total  = rollup(all_by_date, last_30)
    today_tasks  = round(task_by_date.get(today, 0.0), 4)
    today_hooks  = round(hook_by_date.get(today, 0.0), 4)

    paused = PAUSE_FLAG.exists()

    if args.json:
        out = {
            "today": {
                "total_usd": today_total,
                "tasks_usd": today_tasks,
                "hooks_usd": today_hooks,
            },
            "this_week_usd": week_total,
            "last_30_days_usd": month_total,
            "monthly_credit_usd": monthly_credit,
            "credit_remaining_estimate_usd": round(monthly_credit - month_total, 4),
            "pause_flag_active": paused,
            "session_count": len(sessions),
        }
        if args.days:
            d_start = today - timedelta(days=args.days - 1)
            out["daily_breakdown"] = {
                str(today - timedelta(days=i)):
                round(all_by_date.get(today - timedelta(days=i), 0.0), 4)
                for i in range(args.days - 1, -1, -1)
                if (today - timedelta(days=i)) >= d_start
            }
        print(json.dumps(out, indent=2))
    else:
        print(f"Scheduled-task spend — {today.isoformat()} (full API rates, post-June-15-2026)")
        print()
        print(f"  Today         ${today_total:>7.4f}   (tasks ${today_tasks:.4f} · hooks ${today_hooks:.4f})")
        print(f"  This week     ${week_total:>7.4f}")
        print(f"  Last 30 days  ${month_total:>7.4f}   / ${monthly_credit:.2f} monthly credit  "
              f"({100*month_total/monthly_credit:.1f}% used)")
        if paused:
            try:
                pdata = json.loads(PAUSE_FLAG.read_text())
                print(f"\n  ⚠️  PAUSE FLAG ACTIVE since {pdata.get('paused_at', '?')}: {pdata.get('reason', '?')}")
                print(f"     Clear with: rm {PAUSE_FLAG}")
            except Exception:
                print(f"\n  ⚠️  PAUSE FLAG ACTIVE at {PAUSE_FLAG}")
        if args.days:
            print(f"\n  Per-day breakdown (last {args.days} days):")
            for i in range(args.days - 1, -1, -1):
                d = today - timedelta(days=i)
                c = all_by_date.get(d, 0.0)
                bar = "█" * int(c * 20)   # scale: 1 block = $0.05
                print(f"    {d.isoformat()}  ${c:>6.4f}  {bar}")
        if args.threshold is not None:
            marker = "✓" if today_total <= args.threshold else "✗"
            print(f"\n  Threshold check: today ${today_total:.4f} vs ${args.threshold:.2f} — {marker}")
        print(f"\n  Sessions tracked: {len(sessions)} sdk-cli")

    # --- Side effects ---

    if args.pause_if_over is not None and today_total > args.pause_if_over:
        write_pause_flag(today_total, args.pause_if_over)
        if not args.json:
            print(f"\n  ⚠️  Cap breached: wrote pause flag to {PAUSE_FLAG}")

    if args.threshold is not None and today_total > args.threshold:
        sys.exit(1)


if __name__ == "__main__":
    main()
