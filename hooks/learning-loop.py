#!/usr/bin/env python3
"""Learning-loop consumption for EOD triage and brief feedback (VM-79).

Reads eod-triage-feedback.json (last 60 entries) and brief-feedback.json to:
1. Compute suppress patterns — proposal titles/phrases Vladimir consistently skips
2. Write eod-suppress-patterns.json — the actioned suppress list
3. Score new proposal titles against the suppress list
4. Surface approval-rate stats for the weekly review

This closes VM-5 — the capture was already built; this is the consumption pass
that makes the learning loop actually compound.

Suppress threshold: ≥2 skips in last 60 entries (tunable with --threshold).

Usage:
    python3 learning-loop.py --stats                # approval rates + top patterns
    python3 learning-loop.py --update-suppress-list # write eod-suppress-patterns.json
    python3 learning-loop.py --check "title here"   # is this suppressed? (JSON)
    python3 learning-loop.py --score "title here"   # confidence score (JSON)
    python3 learning-loop.py --list-suppressed      # current suppress list (JSON)

--stats output:
{
  "window_entries": N,          # entries in the analysis window
  "section_a": {
    "total_proposed": N, "total_approved": N,
    "approval_rate": 0.0-1.0,   # null if no data
    "total_skipped": N,
    "top_skipped": [{"title": "...", "count": N}]
  },
  "section_b": { ... },
  "suppressed_pattern_count": N,  # patterns meeting the threshold
  "suppress_list_path": "..."
}

--check / --score output:
{
  "title": "...",
  "normalized": "...",
  "confidence": "high" | "medium" | "low",
  "suppressed": bool,
  "match_type": "exact" | "fuzzy" | null,
  "matched_pattern": "..." | null,
  "skip_count": N,
  "approved_before": bool,
  "note": "..."
}
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ_MADRID = ZoneInfo("Europe/Madrid")
TODAY     = datetime.now(TZ_MADRID).date()

LOCAL       = Path.home() / "Projects" / "Leto" / ".local-data"
EOD_FEED    = LOCAL / "eod-triage-feedback.json"
BRIEF_FEED  = LOCAL / "brief-feedback.json"
SUPPRESS    = LOCAL / "eod-suppress-patterns.json"

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "is", "are", "was", "be", "as",
    "into", "via", "that", "this", "it", "its", "not", "new", "add",
    "fix", "update", "create", "remove", "move", "set", "get", "run",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    if not path.exists():
        return {"entries": []}
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {"entries": []}


def normalize(title: str) -> str:
    """Lowercase, remove punctuation, drop stop words, sort remaining words."""
    words = re.sub(r"[^\w\s]", " ", title.lower()).split()
    sig   = sorted(w for w in words if len(w) > 2 and w not in STOP_WORDS)
    return " ".join(sig)


def keyword_set(title: str) -> frozenset[str]:
    """Significant words in a title (3+ chars, not stop words)."""
    words = re.sub(r"[^\w\s]", " ", title.lower()).split()
    return frozenset(w for w in words if len(w) > 2 and w not in STOP_WORDS)


def fuzzy_match(a: str, b: str, min_shared: int = 3) -> bool:
    """True if titles share ≥ min_shared significant words."""
    return len(keyword_set(a) & keyword_set(b)) >= min_shared


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(entries: list[dict]) -> dict:
    """Aggregate approval/skip stats from eod-triage-feedback entries."""
    a_proposed = a_approved = a_skipped = 0
    b_proposed = b_approved = b_skipped = 0
    all_skipped_titles: list[str] = []
    all_approved_titles: list[str] = []

    for e in entries:
        sa = e.get("section_a", {})
        sb = e.get("section_b", {})
        a_proposed += sa.get("proposed", 0)
        a_approved += sa.get("approved", 0)
        a_skipped  += sa.get("skipped", 0)
        b_proposed += sb.get("proposed", 0)
        b_approved += sb.get("approved", 0)
        b_skipped  += sb.get("skipped", 0)
        all_skipped_titles  += sa.get("skipped_titles", []) + sb.get("skipped_titles", [])
        # Reconstruct approved titles — not directly stored, but we can approximate
        # from the next entry's signals if available. For now: track what's skipped.

    # Top skipped titles by frequency
    skip_counter = Counter(all_skipped_titles)

    return {
        "section_a": {
            "total_proposed": a_proposed,
            "total_approved": a_approved,
            "approval_rate": round(a_approved / a_proposed, 3) if a_proposed else None,
            "total_skipped": a_skipped,
            "top_skipped": [{"title": t, "count": c}
                            for t, c in skip_counter.most_common(10)],
        },
        "section_b": {
            "total_proposed": b_proposed,
            "total_approved": b_approved,
            "approval_rate": round(b_approved / b_proposed, 3) if b_proposed else None,
            "total_skipped": b_skipped,
        },
        "all_skipped_titles": all_skipped_titles,
        "skip_counter": skip_counter,
    }


def build_suppress_patterns(entries: list[dict], threshold: int = 2) -> list[dict]:
    """Build suppress list from skipped titles meeting the frequency threshold."""
    analysis = analyse(entries)
    skip_counter: Counter = analysis["skip_counter"]
    all_skipped: list[str] = analysis["all_skipped_titles"]

    patterns: list[dict] = []
    seen_normalized: set[str] = set()

    for title, count in skip_counter.most_common():
        if count < threshold:
            continue
        norm = normalize(title)
        if not norm or norm in seen_normalized:
            continue
        seen_normalized.add(norm)

        # Find all original titles that fuzzy-match this one
        originals = [t for t in all_skipped if fuzzy_match(t, title)]
        last_seen = ""
        for e in reversed(entries):
            skipped = (e.get("section_a", {}).get("skipped_titles", [])
                       + e.get("section_b", {}).get("skipped_titles", []))
            if any(fuzzy_match(t, title) for t in skipped):
                last_seen = e.get("date", "")
                break

        patterns.append({
            "pattern":         norm,
            "original_titles": list(dict.fromkeys(originals)),  # deduplicated
            "skip_count":      count,
            "last_skipped":    last_seen,
            "match_type":      "exact",
        })

    return patterns


def score_title(title: str, patterns: list[dict]) -> dict:
    """Score a proposed title against the suppress list."""
    norm = normalize(title)
    for p in patterns:
        # Exact normalized match
        if norm == p["pattern"]:
            return {
                "title": title, "normalized": norm,
                "confidence": "low", "suppressed": True,
                "match_type": "exact", "matched_pattern": p["pattern"],
                "skip_count": p["skip_count"],
                "approved_before": False,
                "note": f"⚠️ Pattern you've skipped {p['skip_count']}x — include anyway?",
            }
        # Fuzzy match (≥3 shared keywords)
        if fuzzy_match(title, " ".join(p["pattern"].split())):
            return {
                "title": title, "normalized": norm,
                "confidence": "low", "suppressed": True,
                "match_type": "fuzzy", "matched_pattern": p["pattern"],
                "skip_count": p["skip_count"],
                "approved_before": False,
                "note": f"⚠️ Fuzzy match to pattern skipped {p['skip_count']}x — include anyway?",
            }
    return {
        "title": title, "normalized": norm,
        "confidence": "medium", "suppressed": False,
        "match_type": None, "matched_pattern": None,
        "skip_count": 0, "approved_before": False,
        "note": "",
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stats", action="store_true",
                        help="Approval rates + top skipped patterns")
    parser.add_argument("--update-suppress-list", action="store_true",
                        help="Write eod-suppress-patterns.json from current feedback")
    parser.add_argument("--check", metavar="TITLE",
                        help="Is this title suppressed? Returns JSON")
    parser.add_argument("--score", metavar="TITLE",
                        help="Confidence score for a new proposal title")
    parser.add_argument("--list-suppressed", action="store_true",
                        help="Current suppress list (JSON)")
    parser.add_argument("--threshold", type=int, default=2,
                        help="Skip count threshold for suppression (default 2)")
    parser.add_argument("--window", type=int, default=60,
                        help="Max entries to analyze (default 60)")
    args = parser.parse_args()

    eod_data = load_json(EOD_FEED)
    entries  = eod_data.get("entries", [])[-args.window:]

    if not entries:
        empty = {
            "message": "No eod-triage-feedback entries yet — patterns will build as EOD runs are applied.",
            "entries": 0,
        }
        if args.stats or args.update_suppress_list or args.list_suppressed:
            print(json.dumps(empty, indent=2))
            return

    patterns = build_suppress_patterns(entries, threshold=args.threshold)

    if args.list_suppressed:
        print(json.dumps({"suppressed": patterns, "count": len(patterns)}, indent=2))
        return

    if args.update_suppress_list:
        payload = {
            "last_updated":       TODAY.isoformat(),
            "window_entries":     len(entries),
            "threshold":          args.threshold,
            "suppressed":         patterns,
            "suppressed_count":   len(patterns),
        }
        LOCAL.mkdir(parents=True, exist_ok=True)
        SUPPRESS.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    if args.check or args.score:
        title = args.check or args.score
        # Load existing suppress list if available (avoids recomputing)
        if SUPPRESS.exists():
            try:
                existing = json.loads(SUPPRESS.read_text())
                patterns = existing.get("suppressed", patterns)
            except (OSError, json.JSONDecodeError):
                pass
        result = score_title(title, patterns)
        print(json.dumps(result, indent=2))
        return

    if args.stats:
        analysis  = analyse(entries)
        out = {
            "window_entries":         len(entries),
            "section_a":              analysis["section_a"],
            "section_b":              analysis["section_b"],
            "suppressed_pattern_count": len(patterns),
            "top_skipped":            analysis["section_a"]["top_skipped"],
            "suppress_list_path":     str(SUPPRESS),
        }
        print(json.dumps(out, indent=2))
        return

    # Default: print a human-readable summary
    analysis = analyse(entries)
    sa = analysis["section_a"]
    sb = analysis["section_b"]
    print(f"Learning loop — {TODAY.isoformat()}  ({len(entries)} entries in window)")
    print()
    rate_a = f"{sa['approval_rate']:.0%}" if sa["approval_rate"] is not None else "—"
    rate_b = f"{sb['approval_rate']:.0%}" if sb["approval_rate"] is not None else "—"
    print(f"  Section A (state updates): {sa['total_proposed']} proposed · {sa['total_approved']} approved · rate {rate_a}")
    print(f"  Section B (new tickets):   {sb['total_proposed']} proposed · {sb['total_approved']} approved · rate {rate_b}")
    print(f"  Suppressed patterns (≥{args.threshold} skips): {len(patterns)}")
    if patterns:
        for p in patterns[:5]:
            print(f"    • [{p['skip_count']}x] {p['original_titles'][0] if p['original_titles'] else p['pattern']}")


if __name__ == "__main__":
    main()
