#!/usr/bin/env python3
"""Doubt-driven Stop hook for Claude Code.

Fires on every Stop event. Reads the session transcript, extracts the last
assistant message, runs a fresh-context Claude review for factual claims,
and logs findings + cost to ~/.claude/logs/doubt-stop/.

Annotate-only — exits 0 regardless of findings. Never blocks.

Cost control:
- Pre-filter: skip review if response has no factuality signals.
- Reviewer uses Haiku (cheap lookup model).
- Per-call budget cap via --max-budget-usd.
- Daily-cap auto-disable: if today's spend >= LETO_DOUBT_DAILY_CAP, skip.
- Recursion guard via LETO_DOUBT_DEPTH env var.

Configure in ~/.claude/settings.json (see hooks/install.sh).
Inspect spend with hooks/usage.py.
"""

import csv
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

LOG_DIR = Path.home() / ".claude" / "logs" / "doubt-stop"
SUMMARY_CSV = LOG_DIR / "summary.csv"
ERROR_LOG = LOG_DIR / "errors.log"

REVIEWER_MODEL = "haiku"
TIMEOUT_S = 90
MAX_BUDGET_USD = 0.30
RESPONSE_CHAR_CAP = 8000

DEFAULT_DAILY_CAP_USD = 5.00
SUMMARY_COLUMNS = [
    "timestamp", "session_id", "response_chars",
    "ok", "miss", "unverifiable", "cost_usd",
]

# Heuristic pre-filter: response must contain at least one of these to trigger review.
FACTUALITY_PATTERNS = [
    re.compile(r"~/"),
    re.compile(r"\bVM-\d+\b"),
    re.compile(r"\b[A-Z]{2,5}-\d+\b"),
    re.compile(r"\b\w+\.md\b"),
    re.compile(r"\b\w+\.py\b"),
    re.compile(r"\b\w+\.ts\b"),
    re.compile(r":\d+\b"),
    re.compile(r"\bexists?\s+at\b", re.IGNORECASE),
    re.compile(r"\blocated\s+at\b", re.IGNORECASE),
    re.compile(r"\bdefined\s+in\b", re.IGNORECASE),
    re.compile(r"function\s+\w+\("),
]

REVIEW_PROMPT = """You are reviewing a Claude Code assistant response for factual claims that may be hallucinations.

For each concrete factual claim in the response, attempt to verify it. Concrete claims include:
- File paths (does the file exist?)
- Linear issue IDs with asserted state (VM-X is "Done" — is it?)
- Memory file content claims (does feedback_X.md actually say Y?)
- Function or symbol names with locations (foo() at bar.py:42 — does it exist there?)
- Persona file content (does engineer-carmack.md say Z?)

Output ONE LINE PER CLAIM in this exact format:
[OK|MISS|UNVERIFIABLE] | claim | evidence

- OK: verified true via tool lookup
- MISS: verified false (file doesn't exist, state differs, content differs)
- UNVERIFIABLE: opinion, judgment, recommendation, or has no checkable source within reach

Be strict but fair — paraphrased content that preserves meaning is OK.

Output ONLY the lines. No preamble, no summary, no markdown. If no factual claims are present, output exactly: NO_CLAIMS

ASSISTANT RESPONSE TO REVIEW:
---
{response}
---
"""


def log_error(msg: str) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().isoformat(timespec="seconds")
        with open(ERROR_LOG, "a") as fh:
            fh.write(f"{ts} {msg}\n")
    except OSError:
        pass


def read_hook_input() -> dict:
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def extract_last_assistant_text(transcript_path: str) -> str:
    if not transcript_path:
        return ""
    p = Path(transcript_path)
    if not p.exists():
        return ""
    last_text_blocks = []
    try:
        with open(p) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") != "assistant":
                    continue
                msg = entry.get("message", {})
                content = msg.get("content", [])
                if isinstance(content, str):
                    last_text_blocks = [content]
                elif isinstance(content, list):
                    last_text_blocks = [
                        b.get("text", "") for b in content
                        if isinstance(b, dict) and b.get("type") == "text"
                    ]
    except OSError as e:
        log_error(f"transcript read failed: {e}")
        return ""
    return "\n".join(t for t in last_text_blocks if t).strip()


def has_factuality_signal(text: str) -> bool:
    return any(p.search(text) for p in FACTUALITY_PATTERNS)


def run_reviewer(response: str) -> tuple[str, float]:
    """Spawn reviewer. Returns (findings_text, cost_usd)."""
    capped = response[:RESPONSE_CHAR_CAP]
    prompt = REVIEW_PROMPT.format(response=capped)
    env = os.environ.copy()
    env["LETO_DOUBT_DEPTH"] = "1"
    try:
        result = subprocess.run(
            [
                "claude",
                "--print",
                "--model", REVIEWER_MODEL,
                "--dangerously-skip-permissions",
                "--max-budget-usd", str(MAX_BUDGET_USD),
                "--output-format", "json",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
            env=env,
        )
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            log_error(f"reviewer non-JSON output: {result.stdout[:200]!r}")
            return "", 0.0
        text = (parsed.get("result") or "").strip()
        cost = float(parsed.get("total_cost_usd") or 0.0)
        if parsed.get("is_error"):
            log_error(f"reviewer is_error=true subtype={parsed.get('subtype')} result={text[:200]!r}")
        return text, cost
    except subprocess.TimeoutExpired:
        log_error("reviewer timeout")
        return "", 0.0
    except FileNotFoundError:
        log_error("claude CLI not found")
        return "", 0.0
    except Exception as e:
        log_error(f"reviewer failed: {e}")
        return "", 0.0


def today_spend() -> float:
    """Sum cost_usd from summary.csv for today's date. Returns 0.0 if no data."""
    if not SUMMARY_CSV.exists():
        return 0.0
    today = date.today().isoformat()
    total = 0.0
    try:
        with open(SUMMARY_CSV, newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                if row.get("timestamp", "").startswith(today):
                    try:
                        total += float(row.get("cost_usd") or 0.0)
                    except ValueError:
                        continue
    except OSError:
        return 0.0
    return total


def log_findings(session_id: str, findings: str, response_len: int, cost_usd: float) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{session_id}.md"
    ts = datetime.now().isoformat(timespec="seconds")
    with open(log_path, "a") as fh:
        fh.write(f"\n## {ts} (response: {response_len} chars, cost: ${cost_usd:.4f})\n\n{findings}\n")

    miss = sum(1 for l in findings.splitlines() if l.startswith("MISS"))
    ok = sum(1 for l in findings.splitlines() if l.startswith("OK"))
    unv = sum(1 for l in findings.splitlines() if l.startswith("UNVERIFIABLE"))

    write_header = not SUMMARY_CSV.exists()
    with open(SUMMARY_CSV, "a") as fh:
        if write_header:
            fh.write(",".join(SUMMARY_COLUMNS) + "\n")
        fh.write(f"{ts},{session_id},{response_len},{ok},{miss},{unv},{cost_usd:.4f}\n")


def main() -> int:
    if os.environ.get("LETO_DOUBT_DEPTH"):
        return 0

    data = read_hook_input()
    transcript_path = data.get("transcript_path", "")
    session_id = data.get("session_id", "unknown")

    response = extract_last_assistant_text(transcript_path)
    if not response:
        return 0

    if not has_factuality_signal(response):
        return 0

    daily_cap = float(os.environ.get("LETO_DOUBT_DAILY_CAP", DEFAULT_DAILY_CAP_USD))
    spent_today = today_spend()
    if spent_today >= daily_cap:
        log_error(f"daily cap reached: ${spent_today:.4f} >= ${daily_cap:.2f} — skipping review")
        return 0

    findings, cost = run_reviewer(response)
    if findings and findings != "NO_CLAIMS":
        log_findings(session_id, findings, len(response), cost)

    return 0


if __name__ == "__main__":
    sys.exit(main())
