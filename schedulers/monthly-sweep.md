---
type: scheduler
task-id: leto-monthly-sweep
cron: 0 10-16 1-7 * 0
timezone: Europe/Madrid (host local)
status: registered
phase: 2
---

# Monthly sweep — `leto-monthly-sweep`

Fires the **first Sunday of each month at 10:00 Madrid**. Cron `0 10 1-7 * 0` means "10am, day-of-month 1-7, any month, only if Sunday" — which evaluates to the first Sunday of each month.

Appends a `## Monthly Synthesis` placeholder to the most recent weekly review note for Vladimir to fill in. Nothing auto-generated.

## How to update

```
mcp__scheduled-tasks__update_scheduled_task(
  taskId="leto-monthly-sweep",
  prompt=<contents of the "Prompt" section below>
)
```

## Prompt (executed by the scheduled task)

```
Leto monthly sweep prompt — Tier 2 scheduled. Today is the first Sunday of <Month YYYY> at 10:00 Madrid.

STEP 0 — IDLE-RECOVERY CHECK:
This task fires hourly within a recovery window (cron `0 10-16 1-7 * 0`) so a missed slot due to laptop sleep / Claude Code closure can still produce the sweep later. The first successful fire appends the Monthly Synthesis block; subsequent fires exit immediately.

Find the latest weekly review file in `~/Obsidian Vault/Vladimir's Vault/40 System/Journal/Weekly/`. If it already contains a `## Monthly Synthesis` heading, exit immediately with "Idle-recovery: monthly synthesis already present — skipping fire." Otherwise, proceed to STEP 1.

STEP 1 — LOAD CONTEXT:
1. ~/Projects/Leto/CLAUDE.md
2. ~/Projects/Leto/INDEX.md

STEP 2 — FIND LATEST WEEKLY REVIEW:
List ~/Obsidian Vault/Vladimir's Vault/40 System/Journal/Weekly/ and pick the most recently dated file (YYYY-Www.md, sort lexically descending).

STEP 3 — APPEND MONTHLY SYNTHESIS BLOCK:

If the latest weekly review file already contains a `## Monthly Synthesis` heading, exit early ("Already present").

Otherwise append:

```
## Monthly Synthesis — <Month YYYY>

*Auto-prompt by Leto on the first Sunday. Block 30 min, fill it in.*

### What worked this month

-

### What's drifting

-

### Receipts that landed

-

### Decisions for next month

-

### Reader-context drift check

Anything in `80 System/reader-context.md` feel stale? If yes, run `/leto bootstrap` to refresh.
```

STEP 4 — LOG THE RUN:

Append to ~/Obsidian Vault/Vladimir's Vault/40 System/Sessions/2026/<YYYY-MM-DD>-leto-monthly-sweep.md:

```
---
type: session
session-skill: leto-monthly-sweep
origin: claude
created: <ISO timestamp>
---

# Monthly sweep — <Month YYYY>

Appended Monthly Synthesis block to Journal/Weekly/<latest-week>.md.
```

GUARDRAILS:
- Never auto-fill the monthly synthesis content.
- If no weekly review file exists yet (edge case for first month), create one for the current week per the weekly-review.md convention, then append the monthly block.
- English narration.
```

## Note on cron expression

`0 10 1-7 * 0` is the standard cron pattern for "first Sunday at 10am":
- `0` minute
- `10` hour (10am local)
- `1-7` day-of-month range (covers the first 7 days)
- `*` any month
- `0` Sunday only

The intersection of "day-of-month 1-7" and "Sunday" yields the first Sunday of every month. Verified via crontab.guru.
