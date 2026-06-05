#!/usr/bin/env python3
"""Tier 3 → 4 promotion-gate scorecard (VM-83).

Reads brief-feedback.json, eod-triage-feedback.json, and Slack draft
decision.md files to compute the Tier 3→4 promotion criteria. Makes
promotion data-backed rather than vibes-driven.

Gate criteria (all must pass for recommendation = "promote"):
  C1 — Brief quality:     ≤1 (⚠️+❌) per week × ≥2 consecutive clean weeks
  C2 — Draft discard:     discard rate < 30% over last 4 weeks
  C3 — Draft edit rate:   edit rate < 30% over last 4 weeks (sent unedited / sent total)
  C4 — Clean weeks:       ≥4 weeks of combined clean operation
  C5 — EOD loop health:   Section B approval rate ≥ 50% (advisory — no data = null, not blocking)

"Clean week" = C1 passing for that week AND no critical failures logged.

One non-automatable criterion remains: "Vladimir explicitly requests Tier 4 promotion."
The scorecard surfaces when the data criteria are met; the final call is Vladimir's.

Usage:
    python3 scorecard.py               # human-readable table
    python3 scorecard.py --json        # machine-readable
    python3 scorecard.py --weeks N     # analysis window (default 4)
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ_MADRID  = ZoneInfo("Europe/Madrid")
TODAY      = datetime.now(TZ_MADRID).date()

LOCAL      = Path.home() / "Projects" / "Leto" / ".local-data"
VAULT      = Path.home() / "Obsidian Vault" / "Vladimir's Vault"
BRIEF_FEED = LOCAL / "brief-feedback.json"
EOD_FEED   = LOCAL / "eod-triage-feedback.json"
DRAFTS_DIR = VAULT / "00 Inbox" / "Drafts" / "slack"


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    if not path.exists():
        return {"entries": []}
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {"entries": []}


def week_start(d: date) -> date:
    """Monday of the week containing d."""
    return d - timedelta(days=d.weekday())


def weeks_ago(n: int) -> date:
    return week_start(TODAY) - timedelta(weeks=n)


def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, AttributeError):
        return None


# ── C1: Brief quality ─────────────────────────────────────────────────────────

def brief_quality(weeks: int = 4) -> dict:
    """
    Returns:
      weekly_bad: dict[week_monday_str -> bad_count]
      clean_weeks: int (weeks where bad_count ≤ 1)
      consecutive_clean: int (consecutive clean weeks ending this week)
      passing: bool (consecutive_clean ≥ 2)
      no_data: bool
    """
    data = load_json(BRIEF_FEED)
    entries = data.get("entries", [])
    since = weeks_ago(weeks)

    weekly_reactions: dict[date, list] = defaultdict(list)
    for e in entries:
        d = parse_date(e.get("date"))
        if d and d >= since:
            r = e.get("reaction")
            weekly_reactions[week_start(d)].append(r)

    if not weekly_reactions:
        return {
            "weekly_bad": {},
            "clean_weeks": 0,
            "consecutive_clean": 0,
            "passing": None,  # null = no data
            "no_data": True,
        }

    weekly_bad: dict[str, int] = {}
    for wk, reactions in weekly_reactions.items():
        bad = sum(1 for r in reactions if r in ("⚠️", "❌"))
        weekly_bad[wk.isoformat()] = bad

    clean_count = sum(1 for bad in weekly_bad.values() if bad <= 1)

    # Consecutive clean weeks ending this week
    consecutive = 0
    check_wk = week_start(TODAY)
    for _ in range(weeks):
        wk_str = check_wk.isoformat()
        bad = weekly_bad.get(wk_str)
        if bad is None:
            # No data for this week — treat as clean if it's the current week (still ongoing)
            if check_wk == week_start(TODAY):
                check_wk -= timedelta(weeks=1)
                consecutive += 1
                continue
            break
        if bad <= 1:
            consecutive += 1
            check_wk -= timedelta(weeks=1)
        else:
            break

    return {
        "weekly_bad": weekly_bad,
        "clean_weeks": clean_count,
        "consecutive_clean": consecutive,
        "passing": consecutive >= 2,
        "no_data": False,
    }


# ── C2/C3: Draft quality ──────────────────────────────────────────────────────

def draft_quality(weeks: int = 4) -> dict:
    """
    Reads decision.md files from Drafts/slack/. Computes discard rate + edit rate.
    Returns: {total, sent, recalled, dropped, excluded, discard_rate, edit_rate, passing_discard, passing_edit, no_data}
    """
    since = TODAY - timedelta(weeks=weeks)

    sent = recalled = dropped = excluded = edited = 0
    total = 0

    if not DRAFTS_DIR.is_dir():
        return _draft_no_data()

    for decision_file in DRAFTS_DIR.glob("*/decision.md"):
        try:
            text = decision_file.read_text(encoding="utf-8", errors="replace")
            # Parse frontmatter
            if not text.startswith("---"):
                continue
            end = text.find("---", 3)
            if end < 0:
                continue
            fm_text = text[3:end]
            meta: dict[str, str] = {}
            for line in fm_text.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip()] = v.strip()

            created_d = parse_date(meta.get("created"))
            if not created_d or created_d < since:
                continue

            status = meta.get("status", "").lower()
            total += 1
            if status == "sent":
                sent += 1
            elif status == "recalled":
                recalled += 1
            elif status == "dropped":
                dropped += 1
            elif status == "excluded":
                excluded += 1
                total -= 1  # excluded doesn't count toward denominator

            # Edit rate: body contains "## Edit" section → was edited before send
            if status == "sent" and "## Edit" in text:
                edited += 1
        except OSError:
            pass

    if total == 0:
        return _draft_no_data()

    actionable = sent + recalled + dropped  # denominator for discard/edit
    discard_rate = (recalled + dropped) / actionable if actionable else None
    edit_rate    = edited / sent if sent else None

    return {
        "total":          total,
        "sent":           sent,
        "recalled":       recalled,
        "dropped":        dropped,
        "excluded":       excluded,
        "edited":         edited,
        "discard_rate":   round(discard_rate, 3) if discard_rate is not None else None,
        "edit_rate":      round(edit_rate, 3)    if edit_rate    is not None else None,
        "passing_discard":(discard_rate < 0.30)  if discard_rate is not None else None,
        "passing_edit":   (edit_rate    < 0.30)  if edit_rate    is not None else None,
        "no_data":        False,
    }


def _draft_no_data() -> dict:
    return {
        "total": 0, "sent": 0, "recalled": 0, "dropped": 0, "excluded": 0, "edited": 0,
        "discard_rate": None, "edit_rate": None,
        "passing_discard": None, "passing_edit": None,
        "no_data": True,
    }


# ── C5: EOD loop health (advisory) ───────────────────────────────────────────

def eod_health() -> dict:
    data = load_json(EOD_FEED)
    entries = data.get("entries", [])
    since = TODAY - timedelta(weeks=4)

    b_proposed = b_approved = 0
    for e in entries:
        d = parse_date(e.get("date"))
        if not d or d < since:
            continue
        sb = e.get("section_b", {})
        b_proposed += sb.get("proposed", 0)
        b_approved += sb.get("approved", 0) + sb.get("auto_applied", 0)

    if b_proposed == 0:
        return {"b_proposed": 0, "b_approved": 0, "approval_rate": None, "passing": None, "no_data": True}

    rate = b_approved / b_proposed
    return {
        "b_proposed": b_proposed,
        "b_approved": b_approved,
        "approval_rate": round(rate, 3),
        "passing": rate >= 0.50,
        "no_data": False,
    }


# ── Scorecard assembly ────────────────────────────────────────────────────────

def build_scorecard(weeks: int = 4) -> dict:
    bq  = brief_quality(weeks)
    dq  = draft_quality(weeks)
    eod = eod_health()

    # Determine per-criterion status
    c1 = _criterion("Brief quality ≤1 bad/week × ≥2 consecutive",
                     bq["passing"],
                     f"consecutive clean weeks: {bq['consecutive_clean']} "
                     f"(need 2){' — no data yet' if bq['no_data'] else ''}")

    c2 = _criterion("Draft discard rate < 30%",
                     dq["passing_discard"],
                     f"{dq['discard_rate']*100:.0f}%" if dq["discard_rate"] is not None
                     else "no drafts sent yet")

    c3 = _criterion("Draft edit rate < 30%",
                     dq["passing_edit"],
                     f"{dq['edit_rate']*100:.0f}%" if dq["edit_rate"] is not None
                     else "no drafts sent yet")

    # C4: clean weeks = weeks where brief quality was passing
    c4_val = bq["clean_weeks"]
    c4 = _criterion("≥4 weeks clean operation",
                     c4_val >= 4 if not bq["no_data"] else None,
                     f"{c4_val} clean week(s) in {weeks}w window"
                     + (" — no data yet" if bq["no_data"] else ""))

    c5 = _criterion("EOD Section B approval ≥50% (advisory)",
                     eod["passing"],  # null = advisory, doesn't block
                     f"{eod['approval_rate']*100:.0f}%" if eod["approval_rate"] is not None
                     else "no data yet")
    c5["advisory"] = True  # advisory = no data doesn't block recommendation

    # Overall: C1–C4 required (null = insufficient data, treat as not-yet-passing)
    required = [c1, c2, c3, c4]
    all_required_pass = all(c["passing"] is True for c in required)
    any_failing = any(c["passing"] is False for c in required)

    if all_required_pass:
        recommendation = "🟢 Gate passing — all criteria met. Vladimir's explicit request still needed to activate Tier 4."
    elif any_failing:
        failing = [c["name"] for c in required if c["passing"] is False]
        recommendation = f"🔴 Gate not passing — criteria failing: {', '.join(failing)}"
    else:
        pending = [c["name"] for c in required if c["passing"] is None]
        recommendation = f"🟡 Insufficient data for: {', '.join(pending)} — keep running, check next Friday"

    return {
        "checked_at": TODAY.isoformat(),
        "gate":       "tier3-to-tier4",
        "window_weeks": weeks,
        "criteria": [c1, c2, c3, c4, c5],
        "all_required_pass": all_required_pass,
        "recommendation": recommendation,
        "_raw": {"brief": bq, "drafts": dq, "eod": eod},
    }


def _criterion(name: str, passing, detail: str) -> dict:
    if passing is True:
        icon = "✅"
    elif passing is False:
        icon = "❌"
    else:
        icon = "⚪"  # no data
    return {"name": name, "passing": passing, "icon": icon, "detail": detail}


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json",  action="store_true")
    parser.add_argument("--weeks", type=int, default=4,
                        help="Analysis window in weeks (default 4)")
    args = parser.parse_args()

    sc = build_scorecard(args.weeks)

    if args.json:
        # Drop raw data from JSON output (keep it clean for weekly-review)
        out = {k: v for k, v in sc.items() if k != "_raw"}
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    # Human-readable
    print(f"Tier 3 → 4 Promotion Scorecard — {sc['checked_at']} ({sc['window_weeks']}w window)")
    print()
    for c in sc["criteria"]:
        adv = " (advisory)" if c.get("advisory") else ""
        print(f"  {c['icon']}  {c['name']}{adv}")
        print(f"       {c['detail']}")
    print()
    print(f"  {sc['recommendation']}")
    print()
    print("  Non-automatable: Vladimir explicitly requests Tier 4 activation.")


if __name__ == "__main__":
    main()
