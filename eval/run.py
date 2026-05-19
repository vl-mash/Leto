#!/usr/bin/env python3
"""Leto hallucination eval runner.

Loads JSON cases from cases/*.json, sends each question through
`claude --print` with a /leto preamble, scores by substring match,
writes per-run CSV to results/.

Usage:
    python3 run.py                    # full run
    python3 run.py --cases vault-001  # single case (for iteration)
    python3 run.py --runs 1           # one run per case (cheap smoke test)
"""

import argparse
import csv
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

EVAL_DIR = Path(__file__).parent
CASES_DIR = EVAL_DIR / "cases"
RESULTS_DIR = EVAL_DIR / "results"

MODEL = "sonnet"
TIMEOUT_S = 240
MAX_BUDGET_USD = 0.50
CWD_FOR_CLAUDE = Path.home() / "Projects" / "Leto"

PREAMBLE = "/leto\n\n"


def load_cases(filter_ids=None):
    cases = []
    for f in sorted(CASES_DIR.glob("*.json")):
        with open(f) as fh:
            cases.extend(json.load(fh))
    if filter_ids:
        cases = [c for c in cases if c["id"] in filter_ids]
    return cases


def invoke_claude(prompt: str) -> str:
    full = PREAMBLE + prompt
    try:
        result = subprocess.run(
            [
                "claude",
                "--print",
                "--model", MODEL,
                "--dangerously-skip-permissions",
                "--max-budget-usd", str(MAX_BUDGET_USD),
            ],
            input=full,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
            cwd=CWD_FOR_CLAUDE,
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return ""


def score(output: str, case: dict):
    lc = output.lower()
    missing = [s for s in case.get("expected_substrings", []) if s.lower() not in lc]
    forbidden_hit = [s for s in case.get("forbidden_substrings", []) if s.lower() in lc]
    return (not missing and not forbidden_hit), missing, forbidden_hit


def run_case(case: dict, runs: int) -> dict:
    outcomes = []
    for _ in range(runs):
        out = invoke_claude(case["question"])
        passed, missing, forbidden = score(out, case)
        outcomes.append({
            "passed": passed,
            "missing": missing,
            "forbidden": forbidden,
            "output_chars": len(out),
        })
    passes = sum(1 for o in outcomes if o["passed"])
    majority = passes >= (runs // 2 + 1)
    last_fail = next((o for o in outcomes if not o["passed"]), None)
    return {
        "case_id": case["id"],
        "category": case["category"],
        "passes": passes,
        "runs": runs,
        "majority": "PASS" if majority else "FAIL",
        "missing_expected": "|".join(last_fail["missing"]) if last_fail else "",
        "hit_forbidden": "|".join(last_fail["forbidden"]) if last_fail else "",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", nargs="*", help="Filter to specific case IDs")
    parser.add_argument("--runs", type=int, default=3, help="Runs per case (default 3)")
    parser.add_argument("--parallel", type=int, default=2, help="Max parallel invocations")
    args = parser.parse_args()

    cases = load_cases(filter_ids=args.cases)
    if not cases:
        print("No cases matched.", file=sys.stderr)
        sys.exit(1)

    RESULTS_DIR.mkdir(exist_ok=True)
    total_invocations = len(cases) * args.runs
    print(f"Running {len(cases)} cases × {args.runs} runs = {total_invocations} invocations")
    print(f"Model: {MODEL}, max budget per invocation: ${MAX_BUDGET_USD}")
    print(f"CWD for claude subprocess: {CWD_FOR_CLAUDE}\n")

    rows = []
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futures = {ex.submit(run_case, c, args.runs): c for c in cases}
        for i, future in enumerate(as_completed(futures), 1):
            row = future.result()
            print(f"[{i}/{len(cases)}] {row['case_id']:20s} {row['category']:10s} "
                  f"{row['passes']}/{row['runs']} {row['majority']}"
                  + (f"  missing: {row['missing_expected']}" if row['missing_expected'] else "")
                  + (f"  forbidden: {row['hit_forbidden']}" if row['hit_forbidden'] else ""))
            rows.append(row)

    rows.sort(key=lambda r: (r["category"], r["case_id"]))
    today = date.today().isoformat()
    csv_path = RESULTS_DIR / f"{today}.csv"
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by_cat = {}
    for r in rows:
        by_cat.setdefault(r["category"], []).append(r)
    overall_pass = sum(1 for r in rows if r["majority"] == "PASS")
    print(f"\nResults: {csv_path}")
    print(f"Overall: {overall_pass}/{len(rows)} cases pass ({100*overall_pass//len(rows)}%)")
    for cat in sorted(by_cat):
        cat_rows = by_cat[cat]
        p = sum(1 for r in cat_rows if r["majority"] == "PASS")
        print(f"  {cat:10s} {p}/{len(cat_rows)}")


if __name__ == "__main__":
    main()
