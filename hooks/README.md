# Hooks

## `scheduled-cost.py` — API spend tracker (VM-73)

Estimates programmatic (sdk-cli) API spend from Claude Code session JSONL files.
Reports today/week/30-day totals at full post-June-15-2026 rates, separated into
scheduled-task sessions (sonnet) vs hook sessions (haiku).

```bash
python3 hooks/scheduled-cost.py              # human-readable
python3 hooks/scheduled-cost.py --days 14   # per-day chart
python3 hooks/scheduled-cost.py --json       # machine-readable
python3 hooks/scheduled-cost.py --threshold 5.00   # exit 1 if today > $5
python3 hooks/scheduled-cost.py --pause-if-over 10.00  # write pause flag if over
```

Config: `~/.config/leto/cost-cap.json`
Pause flag: `~/.config/leto/schedulers-paused` (clear with `rm` to resume)

⚠️ **June 15 action:** Claim the Anthropic credit email at claude.ai/settings before
2026-06-15 (one-time opt-in). Then update `monthly_credit_usd` in `cost-cap.json`
to match your plan tier (Pro $20 / Max-5x $100 / Max-20x $200).

---

## `fact-freshen.py` — reader-context staleness + pending patch check (VM-75)

Checks `reader-context.md` frontmatter `updated:` date and counts pending
fact-patch proposals. No LLM calls. Runs as part of daily-brief PART A.

```bash
python3 hooks/fact-freshen.py              # JSON output (default)
python3 hooks/fact-freshen.py --human      # human-readable summary
python3 hooks/fact-freshen.py --staleness-days 14   # custom threshold
```

Patches dir: `~/Obsidian Vault/.../00 Inbox/Drafts/fact-patches/`
Convention: `conventions/fact-patches.md`

---

## `preflight.py` — scheduler precondition checks + self-repair (VM-74)

Runs as STEP 0 of every scheduled task. Fast (< 1s). Outputs JSON.

```bash
python3 hooks/preflight.py    # exit 0 = ok/warn, exit 1 = abort
```

Checks: pause flag (abort), config files (warn), vault root (warn), Leto repo (warn).
Repairs: granola registry, today's daily-journal stub, granola sources dir, sessions dir.

See `conventions/preflight.md` for the full spec and the SKILL.md instruction block.

---

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

Four layers, in order of effect:

1. **Pre-filter** skips most turns. Acknowledgments, brief clarifications, prose without paths → no review fires.
2. **Daily-cap auto-disable** — hook reads today's cumulative spend from `summary.csv` at entry; if it's already past `LETO_DOUBT_DAILY_CAP` (default $5.00), the hook exits 0 without spawning the reviewer and logs to `errors.log`.
3. **Haiku** for the reviewer (~5–10× cheaper than Sonnet for lookup work).
4. **Per-call budget cap** — `--max-budget-usd 0.30` per review invocation. Hard ceiling per turn.

Other caps: response truncated to first 8000 chars, 90s timeout, recursion guard via `LETO_DOUBT_DEPTH=1`.

Initial smoke test at `$0.10` per call was too tight — Haiku exhausted budget mid-verification on a 3-claim response. `$0.30` gives headroom for a handful of tool roundtrips.

### Check spend

```bash
python3 hooks/usage.py

# Doubt-stop usage — 2026-05-20
#
#   Today        $0.3421   (  4 invocations · OK=6 MISS=2 UNV=1 · errors=0)
#   This week    $1.2734   ( 12 invocations · errors=0)
#   Last 30d     $1.2734   ( 12 invocations)
#
#   Top sessions today:
#     a51b...  $0.1240  OK=3 MISS=1 UNV=0 (2 calls)
```

JSON output: `python3 hooks/usage.py --json`
Threshold alert (non-zero exit if today exceeds): `python3 hooks/usage.py --threshold 5.00`

### Tune the daily cap

```bash
# In your shell rc, or per-session:
export LETO_DOUBT_DAILY_CAP=10.00   # raise to $10/day
export LETO_DOUBT_DAILY_CAP=0.00    # effectively disable without uninstalling
```

The cap reads from `summary.csv`, so it survives restarts and applies across all sessions on this machine.

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
├── summary.csv              # one row per review: ts, session_id, response_chars, ok, miss, unverifiable, cost_usd
├── <session_id>.md          # per-session detail — each Stop event appended
└── errors.log               # transcript read errors, reviewer timeouts, daily-cap skips
```

Inspect with:

```bash
# Spend rollup — preferred
python3 hooks/usage.py

# Raw recent rows
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
