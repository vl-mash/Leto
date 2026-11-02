#!/usr/bin/env python3
"""Claude Code usage review: re-measure the 2026-10-30 baseline.

Reads ~/.claude/projects/*/*.jsonl transcripts and prints aggregate numbers only,
never prompt text (this repo is public). Baseline and what each number means:
memory `user_claude_code_usage.md`.

    python3 scripts/usage_review.py                      # everything
    python3 scripts/usage_review.py --until 2026-10-30   # reproduce the baseline
    python3 scripts/usage_review.py --since 2026-11-03   # after the fixes
"""

import argparse
import collections
import glob
import json
import os
import statistics as st
from datetime import datetime

ROOT = os.path.expanduser("~/.claude/projects")
HOOK_PREFIX = "You are reviewing a Claude Code assistant response"
SCHED_PREFIX = "<scheduled-task"


def text_of(content):
    if isinstance(content, str):
        return content
    return "\n".join(c.get("text", "") for c in content or [] if isinstance(c, dict) and c.get("type") == "text")


def parse(path):
    s = dict(start=None, end=None, first_prompt=None, first_reply="", modes=set(), branches=set(), models=collections.Counter(),
             turns=0, tokens=0, cache_read=0, compactions=0)
    for line in open(path, errors="replace"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        ts = d.get("timestamp")
        if ts:
            s["start"] = min(s["start"] or ts, ts)
            s["end"] = max(s["end"] or ts, ts)
        if d.get("isSidechain"):
            continue
        if d.get("subtype") == "compact_boundary" or d.get("isCompactSummary"):
            s["compactions"] += 1
        if d.get("gitBranch"):
            s["branches"].add(d["gitBranch"])
        msg = d.get("message") or {}
        if d.get("type") == "assistant":
            s["turns"] += 1
            if msg.get("model"):
                s["models"][msg["model"]] += 1
            if not s["first_reply"]:
                s["first_reply"] = text_of(msg.get("content"))[:80]
            u = msg.get("usage") or {}
            s["cache_read"] += u.get("cache_read_input_tokens", 0) or 0
            s["tokens"] += sum(u.get(k, 0) or 0 for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        elif d.get("type") == "user":
            if d.get("permissionMode"):
                s["modes"].add(d["permissionMode"])
            content = msg.get("content")
            if s["first_prompt"] is None and not d.get("isMeta") and not (
                isinstance(content, list) and any(isinstance(c, dict) and c.get("type") == "tool_result" for c in content)
            ):
                s["first_prompt"] = text_of(content).lstrip()[:80]
    return s


def kind(s):
    p = s["first_prompt"] or ""
    if not p:
        return "empty"
    if p.startswith(HOOK_PREFIX):
        return "hook"
    if p.startswith(SCHED_PREFIX):
        return "scheduled"
    return "human"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="YYYY-MM-DD, by session start")
    ap.add_argument("--until", help="YYYY-MM-DD inclusive, by session start")
    a = ap.parse_args()

    sessions = []
    for path in glob.glob(os.path.join(ROOT, "*", "*.jsonl")):
        s = parse(path)
        if not s["start"]:
            continue
        day = s["start"][:10]
        if (a.since and day < a.since) or (a.until and day > a.until):
            continue
        s["kind"] = kind(s)
        sessions.append(s)

    by_kind = collections.Counter(s["kind"] for s in sessions)
    print(f"sessions: {dict(by_kind)}")
    hooks = [s for s in sessions if s["kind"] == "hook"]
    if hooks:
        failed = sum(1 for s in hooks if s["first_reply"].startswith("Failed to authenticate"))
        print(f"reviewer-hook runs: {len(hooks)}, auth failures: {failed}")

    H = [s for s in sessions if s["kind"] == "human"]
    if not H:
        print("no hand-driven sessions in range")
        return
    dt = lambda x: datetime.fromisoformat(x.replace("Z", "+00:00"))
    total = sum(s["tokens"] for s in H) or 1
    long = [s for s in H if (dt(s["end"]) - dt(s["start"])).days >= 1]
    top15 = sum(s["tokens"] for s in sorted(H, key=lambda s: s["tokens"], reverse=True)[:15])
    ctx = st.median(s["cache_read"] / s["turns"] for s in H if s["turns"])
    models = collections.Counter()
    for s in H:
        models.update(s["models"])
    opus = sum(v for k, v in models.items() if "opus" in k) / (sum(models.values()) or 1)
    pct = lambda n: f"{n / len(H):.0%}"
    print(f"hand-driven sessions: {len(H)}")
    print(f"  longer than a day: {len(long)} ({pct(len(long))}), token share {sum(s['tokens'] for s in long) / total:.0%}")
    print(f"  top 15 sessions' token share: {top15 / total:.0%}")
    print(f"  median context per turn: {ctx / 1000:.0f}K tokens")
    print(f"  compacted sessions: {sum(1 for s in H if s['compactions'])}")
    print(f"  plan mode used: {pct(sum(1 for s in H if 'plan' in s['modes']))}")
    print(f"  on a feature branch: {pct(sum(1 for s in H if s['branches'] - {'main', 'HEAD'}))}")
    print(f"  Opus share of main-session turns: {opus:.0%}")


if __name__ == "__main__":
    main()
