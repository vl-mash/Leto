# Doubt-driven Stop hook

Annotate-only Stop hook for Claude Code. Reviews each assistant turn for factual claims and logs verification findings. Does not block.

Ticket: [VM-44](https://linear.app/manychat/issue/VM-44).
Companion: [VM-43](https://linear.app/manychat/issue/VM-43) — the eval that measures whether this hook actually reduces hallucinations.

## How it works

1. Stop event fires after every assistant turn.
2. The hook reads the session transcript JSONL and extracts the last assistant text response.
3. **Pre-filter** — skips review entirely unless the response contains factuality signals (file paths, Linear IDs like `VM-42`, `.md`/`.py`/`.ts` filenames, `:42` line numbers, "exists at" / "located at" / "defined in", function signatures). Most chat-style turns trigger no review.
4. **Reviewer** — spawns `claude --print --model haiku` with a strict prompt: identify factual claims, attempt to verify, output one line per claim with `OK | MISS | UNVERIFIABLE`.
5. **Log** — appends findings to `~/.claude/logs/doubt-stop/<session_id>.md` and a one-line summary to `~/.claude/logs/doubt-stop/summary.csv`.
6. Always exits 0. Never blocks the user.

## Cost control

- **Pre-filter** skips most turns. Acknowledgments, brief clarifications, code without paths → no review fires.
- **Haiku** for the reviewer (5–10× cheaper than Sonnet for this kind of lookup work).
- **Budget cap** — `--max-budget-usd 0.30` per review invocation.
- **Response cap** — first 8000 chars only.
- **Timeout** — 90s, after which review aborts silently.

Initial smoke test at `$0.10` was too tight — Haiku exhausted budget mid-verification on a 3-claim response. `$0.30` gives headroom for a handful of tool roundtrips. Expected steady-state cost on a heavy day: $3–8. If too high, lower the budget or tighten the pre-filter.

## Recursion guard

The reviewer is itself a `claude` invocation, which would trigger the hook again — infinite recursion. The hook sets `LETO_DOUBT_DEPTH=1` in the spawned environment; the hook script checks this at entry and exits immediately if set.

## Install

```bash
bash install.sh
```

The installer:
- Verifies `jq` is present.
- Backs up `~/.claude/settings.json` to a timestamped `.bak` file.
- Inserts an entry into `hooks.Stop` pointing to the absolute path of `doubt-stop.py`.
- Idempotent — re-running replaces an existing entry that references this script.

Restart active Claude Code sessions for the hook to take effect.

## Uninstall

```bash
bash install.sh --uninstall
```

Removes the entry and prunes empty parent keys. The script also makes a timestamped backup before writing.

## Logs

```
~/.claude/logs/doubt-stop/
├── summary.csv              # one row per review: ts, session_id, response_chars, ok, miss, unverifiable
├── <session_id>.md          # per-session detail — each Stop event appended
└── errors.log               # transcript read errors, reviewer timeouts
```

Inspect with:

```bash
# Summary of the last 20 reviews
tail -20 ~/.claude/logs/doubt-stop/summary.csv | column -t -s,

# Hotspot: sessions with the most MISSes
awk -F, 'NR>1 {miss[$2]+=$5} END {for (s in miss) if (miss[s]>0) print miss[s], s}' \
  ~/.claude/logs/doubt-stop/summary.csv | sort -rn | head
```

## Phase plan (per VM-44)

- **v1 (this) — annotate-only.** Build signal. ~1 week of dogfooding.
- **v2 — promote to block for high-stakes ops.** After signal review, decide whether to block on `MISS` for: vault writes, Linear state transitions, Slack drafts. Annotate-only everywhere else.
- **Exit criterion.** Re-run `eval/run.py` after a week. If the `linear` category climbs from 2/6 baseline → 5+/6, the hook is working. If not, tune the reviewer prompt or remove.

## What it does NOT do (v1)

- Does not block any turn (annotate-only).
- Does not surface findings in-conversation — they live in log files. Future v2 could write to a tray/notification.
- Does not call MCP tools directly. The reviewer (Haiku via `claude --print`) inherits whatever tools the global Claude install has, but the hook itself doesn't orchestrate lookups.
- Does not interact with the eval. The eval (`eval/run.py`) tests the *delta* — running it before and after the hook is enabled is how we verify the hook works.
