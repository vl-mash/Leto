#!/usr/bin/env python3
"""Check, list, and manage Leto standing approvals (Tier 4 — VM-81).

Standing Approvals.md is the source-of-truth (human-readable + machine-parseable).
Each SA entry has an inline comment marker:
  <!-- sa:id=SA-002|action-type=eod-auto-apply|expires=2026-09-05|active=true|reviewed=2026-06-05 -->

Hard exclusions (always denied, regardless of any standing approval):
- HR-shaped recipients: Manager / VP / Director / People Partner / COO / CPTO
  Known HR-shaped individuals at Manychat: Teo Georgoulis, Dima Kushnikov,
  Ingrid Bernaudin, Nastya, Lu Borko, Sophia Tessum, Kate Silaeva.
- Financial commitments or budget approvals
- Irreversible deletions
- Actions outside Tier 3/4 scope (never auto-publish externally, never auto-hire, etc.)

Usage:
    python3 standing-approvals.py --check eod-auto-apply
    python3 standing-approvals.py --check slack-dm-self --recipient "Vladimir Mashkovtsev"
    python3 standing-approvals.py --hr-check "Teo Georgoulis"
    python3 standing-approvals.py --status          # all SAs + health (JSON)
    python3 standing-approvals.py --list-expired     # expired SAs
    python3 standing-approvals.py --review-needed    # SAs with review overdue

--check output:
{
  "action_type": "...",
  "approved": true | false,
  "sa_id": "SA-002" | null,
  "reason": "...",
  "expires": "YYYY-MM-DD" | null,
  "days_until_expiry": N | null,
  "hr_exclusion_triggered": false
}

--hr-check output:
{
  "name": "...",
  "hr_shaped": true | false,
  "role": "..." | null,
  "rule": "per-action approval always required for HR-shaped recipients"
}
"""

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ_MADRID  = ZoneInfo("Europe/Madrid")
TODAY      = datetime.now(TZ_MADRID).date()

SA_FILE    = (Path.home() / "Obsidian Vault" / "Vladimir's Vault"
              / "40 System" / "Standing Approvals.md")

# ── HR-shaped recipients ──────────────────────────────────────────────────────
# These people ALWAYS require per-action approval, even at Tier 4.
# Source: reader-context.md "Hard Don'ts" + memory/user_*.md
HR_SHAPED: dict[str, str] = {
    # name (lowercase) → role description
    "teo georgoulis":      "Manager (Head R&D Ops)",
    "dima kushnikov":      "CTO/CPO (skip-level)",
    "ingrid bernaudin":    "CPTO (EPD apex)",
    "nastya":              "VP Engineering",
    "nastasya":            "VP Engineering",
    "lu borko":            "Senior stakeholder",
    "lu":                  "Senior stakeholder",
    "sophia tessum":       "People Partner",
    "kate silaeva":        "VP Talent Acquisition",
    "irina burykina":      "HR",
}


def is_hr_shaped(name: str) -> tuple[bool, str | None]:
    """Return (is_hr_shaped, role_description)."""
    low = name.strip().lower()
    # Exact match
    if low in HR_SHAPED:
        return True, HR_SHAPED[low]
    # Partial match (first or last name)
    for key, role in HR_SHAPED.items():
        if low in key or key in low:
            return True, role
    return False, None


# ── SA file parser ────────────────────────────────────────────────────────────

SA_COMMENT_RE = re.compile(
    r"<!--\s*sa:(.+?)-->"
)


def parse_sa_file() -> list[dict]:
    """Parse Standing Approvals.md for <!-- sa:... --> markers."""
    if not SA_FILE.exists():
        return []
    text = SA_FILE.read_text(encoding="utf-8", errors="replace")
    results = []
    for m in SA_COMMENT_RE.finditer(text):
        meta: dict[str, str] = {}
        for part in m.group(1).split("|"):
            part = part.strip()
            if "=" in part:
                key, _, val = part.partition("=")
                meta[key.strip()] = val.strip()
        if "id" in meta:
            expires_str = meta.get("expires", "")
            reviewed_str = meta.get("reviewed", "")
            expires_date   = _parse_date(expires_str)
            reviewed_date  = _parse_date(reviewed_str)
            days_until_exp = (expires_date - TODAY).days if expires_date else None
            days_since_rev = (TODAY - reviewed_date).days if reviewed_date else None

            results.append({
                "id":                meta.get("id", ""),
                "action_type":       meta.get("action-type", ""),
                "active":            meta.get("active", "true").lower() == "true",
                "expires":           expires_str or None,
                "days_until_expiry": days_until_exp,
                "expired":           (expires_date is not None and expires_date < TODAY),
                "reviewed":          reviewed_str or None,
                "days_since_review": days_since_rev,
                "review_needed":     (days_since_rev is not None and days_since_rev > 30),
            })
    return results


def _parse_date(s: str) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s.strip())
    except ValueError:
        return None


def find_sa(action_type: str, sas: list[dict]) -> dict | None:
    """Find the first active, non-expired SA for a given action type."""
    for sa in sas:
        if sa["action_type"] == action_type and sa["active"] and not sa["expired"]:
            return sa
    return None


# ── Check logic ───────────────────────────────────────────────────────────────

def check_action(action_type: str, recipient: str = "", sas: list[dict] | None = None) -> dict:
    if sas is None:
        sas = parse_sa_file()

    # 1. Hard exclusion: HR-shaped recipient
    if recipient:
        hr, role = is_hr_shaped(recipient)
        if hr:
            return {
                "action_type":           action_type,
                "approved":              False,
                "sa_id":                 None,
                "reason":                f"HR-shaped recipient '{recipient}' ({role}) — per-action approval always required",
                "expires":               None,
                "days_until_expiry":     None,
                "hr_exclusion_triggered":True,
            }

    # 2. Find matching SA
    sa = find_sa(action_type, sas)
    if sa is None:
        # Check if there's an expired one (gives a better error message)
        expired_sa = next((s for s in sas if s["action_type"] == action_type), None)
        if expired_sa and expired_sa.get("expired"):
            return {
                "action_type":           action_type,
                "approved":              False,
                "sa_id":                 expired_sa["id"],
                "reason":                f"{expired_sa['id']} expired on {expired_sa['expires']} — re-affirm in Standing Approvals.md",
                "expires":               expired_sa["expires"],
                "days_until_expiry":     expired_sa["days_until_expiry"],
                "hr_exclusion_triggered":False,
            }
        return {
            "action_type":           action_type,
            "approved":              False,
            "sa_id":                 None,
            "reason":                f"No active standing approval found for action-type '{action_type}'",
            "expires":               None,
            "days_until_expiry":     None,
            "hr_exclusion_triggered":False,
        }

    # 3. Warn if review overdue (but still approve — review is advisory)
    review_warning = ""
    if sa.get("review_needed"):
        review_warning = f" [review overdue — {sa['days_since_review']}d since last review]"

    return {
        "action_type":           action_type,
        "approved":              True,
        "sa_id":                 sa["id"],
        "reason":                f"{sa['id']} active until {sa['expires']}{review_warning}",
        "expires":               sa["expires"],
        "days_until_expiry":     sa["days_until_expiry"],
        "hr_exclusion_triggered":False,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", metavar="ACTION_TYPE",
                        help="Check if action-type is approved")
    parser.add_argument("--recipient", metavar="NAME", default="",
                        help="Recipient name for HR-shaped check (used with --check)")
    parser.add_argument("--hr-check", metavar="NAME",
                        help="Is this person HR-shaped?")
    parser.add_argument("--status", action="store_true",
                        help="All SAs + health (JSON)")
    parser.add_argument("--list-expired", action="store_true",
                        help="Expired SAs (JSON)")
    parser.add_argument("--review-needed", action="store_true",
                        help="SAs with review overdue (JSON)")
    args = parser.parse_args()

    sas = parse_sa_file()

    if args.hr_check:
        hr, role = is_hr_shaped(args.hr_check)
        print(json.dumps({
            "name":      args.hr_check,
            "hr_shaped": hr,
            "role":      role,
            "rule":      "per-action approval always required for HR-shaped recipients",
        }, indent=2))
        return

    if args.check:
        result = check_action(args.check, recipient=args.recipient, sas=sas)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["approved"] else 1)

    if args.list_expired:
        print(json.dumps([s for s in sas if s["expired"]], indent=2))
        return

    if args.review_needed:
        print(json.dumps([s for s in sas if s.get("review_needed")], indent=2))
        return

    if args.status:
        summary = {
            "checked_at":      TODAY.isoformat(),
            "total":           len(sas),
            "active":          sum(1 for s in sas if s["active"] and not s["expired"]),
            "expired":         sum(1 for s in sas if s["expired"]),
            "review_needed":   sum(1 for s in sas if s.get("review_needed")),
            "approvals":       sas,
        }
        print(json.dumps(summary, indent=2))
        return

    # Human-readable default
    if not sas:
        print(f"No standing approvals found in {SA_FILE}")
        return
    print(f"Standing approvals — {TODAY.isoformat()}")
    for sa in sas:
        status = "✓ active" if (sa["active"] and not sa["expired"]) else ("✗ expired" if sa["expired"] else "· inactive")
        exp_str = f"expires {sa['expires']} ({sa['days_until_expiry']}d)" if sa["expires"] else "no expiry"
        rev_warn = " ⚠️ review needed" if sa.get("review_needed") else ""
        print(f"  {sa['id']} [{status}] {sa['action_type']:<30} {exp_str}{rev_warn}")


if __name__ == "__main__":
    main()
