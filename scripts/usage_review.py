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
import re
import statistics as st
from datetime import datetime

ROOT = os.path.expanduser("~/.claude/projects")
HOOK_PREFIX = "You are reviewing a Claude Code assistant response"
SCHED_PREFIX = "<scheduled-task"
# Oct 2026 list prices, $ per million tokens (input, output). Cache read = 0.1x input, cache write = 1.25x input.
PRICE = {"opus": (4, 20), "sonnet": (2, 10), "haiku": (0.10, 0.50), "fable": (10, 50)}
# Folder → Q4 2026 KR, from the project table in context/context.md. Update both together.
KR = {"Baguette": "KR 1.2 (owned)", "R-D-Tooling": "KR 2.1 (owned)", "R-DxCX": "KR 1.1 (Teo)",
      "workflows-rnd-ops-system-of-record": "Hub (run + KR 1.3)", "Leto": "Leto / personal", "Career": "Leto / personal"}
# Requests typed again and again; round 2 (2026-11-03) built commands for them.
ASKS = {"deploy": r"\b(merge and deploy|let'?s deploy|deploy it)\b",
        "try now": r"^(try (now|again))\b",
        "debrief": r"(process|check).{0,25}(call|meeting|transcript|message)|logged to linear|status updates in linear"}


def text_of(content):
    if isinstance(content, str):
        return content
    return "\n".join(c.get("text", "") for c in content or [] if isinstance(c, dict) and c.get("type") == "text")


def cost(u, model):
    fam = next((k for k in PRICE if k in (model or "")), None)
    if not fam:
        return {}
    i, o = PRICE[fam]
    return {"cache_read": (u.get("cache_read_input_tokens") or 0) * i * 0.1 / 1e6,
            "cache_write": (u.get("cache_creation_input_tokens") or 0) * i * 1.25 / 1e6,
            "input": (u.get("input_tokens") or 0) * i / 1e6,
            "output": (u.get("output_tokens") or 0) * o / 1e6}


def folder(path):
    name = os.path.basename(os.path.dirname(path)).replace("-Users-vladimir-mashkovtsev-", "").replace("Projects-", "")
    return name.split("--claude-worktrees")[0]


def parse(path):
    s = dict(start=None, end=None, first_prompt=None, first_reply="", modes=set(), branches=set(), models=collections.Counter(),
             turns=0, tokens=0, cache_read=0, compactions=0, first_ctx=None, cost=collections.Counter(), human=0,
             bash_errors=0, asks=collections.Counter(), folder=folder(path))
    tool_names = {}
    # One API response is written as several lines (one per content block), each repeating the same usage.
    # Count usage once per message id, or tokens and cost come out ~2.5x too high.
    usage = {}
    for n, line in enumerate(open(path, errors="replace")):
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
            if not s["first_reply"]:
                s["first_reply"] = text_of(msg.get("content"))[:80]
            if msg.get("usage"):
                usage[msg.get("id") or n] = (msg["usage"], msg.get("model"))
            for c in msg.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    tool_names[c.get("id")] = c.get("name")
        elif d.get("type") == "user":
            if d.get("permissionMode"):
                s["modes"].add(d["permissionMode"])
            content = msg.get("content")
            if isinstance(content, list) and any(isinstance(c, dict) and c.get("type") == "tool_result" for c in content):
                s["bash_errors"] += sum(1 for c in content if isinstance(c, dict) and c.get("type") == "tool_result"
                                        and c.get("is_error") and tool_names.get(c.get("tool_use_id")) == "Bash")
            elif not d.get("isMeta"):
                text = text_of(content).strip()
                if s["first_prompt"] is None:
                    s["first_prompt"] = text[:80]
                if text and not text.startswith(("<local-command", "Caveat:", "<system-reminder")):
                    s["human"] += 1
                    low = text.lower()
                    for name, rx in ASKS.items():
                        if re.search(rx, low) and (name == "debrief" or len(low) <= 60):
                            s["asks"][name] += 1
    for u, model in usage.values():  # insertion order = first-seen order; the last line per id has the final usage
        s["turns"] += 1
        if model:
            s["models"][model] += 1
        s["cache_read"] += u.get("cache_read_input_tokens", 0) or 0
        s["tokens"] += sum(u.get(k, 0) or 0 for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        if s["first_ctx"] is None:
            s["first_ctx"] = sum(u.get(k, 0) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        s["cost"].update(cost(u, model))
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

    # Round 2 (2026-11-03): fixed context, cache churn, tool friction, repeated asks, KR alignment.
    spend = sum((s["cost"] for s in H), collections.Counter())
    dollars = sum(spend.values()) or 1
    print(f"\nAPI-equivalent spend at list prices: ${dollars:,.0f}  "
          + "  ".join(f"{k} {v / dollars:.0%}" for k, v in spend.most_common()))
    print(f"  API calls per human message (median): {st.median(s['turns'] / s['human'] for s in H if s['human']):.1f}")
    print(f"  Bash errors per session: {sum(s['bash_errors'] for s in H) / len(H):.1f}")
    asks = sum((s["asks"] for s in H), collections.Counter())
    print(f"  repeated asks: " + ", ".join(f"{k} {asks[k]}" for k in ASKS))
    by_month = collections.defaultdict(list)
    for s in H:
        if s["first_ctx"]:
            by_month[s["start"][:7]].append(s["first_ctx"])
    print("  first-turn context by month (median): " + "  ".join(f"{m} {st.median(v) / 1000:.0f}K" for m, v in sorted(by_month.items())))
    by_kr = collections.defaultdict(list)
    for s in H:
        by_kr[KR.get(s["folder"], "run work, no KR")].append(s)
    print("  by KR (sessions, spend share):")
    for k, L in sorted(by_kr.items(), key=lambda kv: -sum(sum(s["cost"].values()) for s in kv[1])):
        print(f"    {k:22} {len(L):4}  {sum(sum(s['cost'].values()) for s in L) / dollars:4.0%}")


if __name__ == "__main__":
    main()
