# Tier 2 — Scheduled prompts (Phase 2 — ACTIVE as of 2026-05-01)

Adds harness wiring without adding outbound action. Builds trust that Leto has correct context before drafting on Vladimir's behalf in Phase 3.

## Active components

### Daily brief — `leto-daily-brief`
- **Cadence:** 09:45 Mon–Fri Europe/Madrid (15 min before peak window 10–12).
- **Substrate:** Vladimir's existing Cowork daily briefing prompt (9 sections: Calendar / Slack / Granola / Backlog / News / AI / Ideas / Tip / Focus). Adopted as the proven structure.
- **Leto-distinct layers:** opening 3-bullet recommendation (today's ONE thing / friction / nudge); voice rules from reader-context.md; political-pattern guard; vault write to today's daily note as `## Brief (auto)`; reaction tracker.
- **Spec:** `~/Projects/Leto/schedulers/daily-brief.md`

### Weekly review — `leto-weekly-review`
- **Cadence:** Friday 16:30 Europe/Madrid (wrap-the-week while context is freshest; switched from Monday 10:00 per Vladimir 2026-05-01).
- **Substrate:** Vladimir's existing Cowork weekly briefing prompt (Past Week + Next Week structure).
- **Leto-distinct layers:** vault write to `Journal/Weekly/<YYYY-Www>.md`; political guard; doesn't auto-fill Wins/Challenges/Surprises (keystone is Vladimir's review); receipts-ladder section foreground.
- **Spec:** `~/Projects/Leto/schedulers/weekly-review.md`

### Monthly sweep — `leto-monthly-sweep`
- **Cadence:** First Sunday of each month at 10:00 Madrid (cron `0 10 1-7 * 0`).
- **Output:** appends `## Monthly Synthesis` block to the latest weekly review note.
- **Spec:** `~/Projects/Leto/schedulers/monthly-sweep.md`

### Granola intake — `leto-granola-intake`
- **Cadence:** 19:00 Mon–Fri Europe/Madrid (end of work day).
- **Output:** captures every new Granola meeting since last run as immutable `source.md` + regenerable `extract.md` (personalized via reader-context.md) at `00 Inbox/Sources/granola/`.
- **Purpose:** (1) feed daily brief's Granola section without re-fetching; (2) ground Phase 3 drafts in actual meeting content; (3) accumulate voice signals for vladimir-tov calibration.
- **Spec:** `~/Projects/Leto/schedulers/granola-intake.md`

## Trigger mechanism

`mcp__scheduled-tasks__create_scheduled_task` registered each task. Tasks store as skill files under `~/.claude/scheduled-tasks/<task-id>/SKILL.md`. Source-of-truth for prompt content lives in the Leto repo (`schedulers/*.md`); updates apply via `mcp__scheduled-tasks__update_scheduled_task`.

To pause any task: `mcp__scheduled-tasks__update_scheduled_task(taskId=..., enabled=false)`.

## Cowork coexistence + retirement

Vladimir's existing Claude Cowork daily and weekly briefings continue to fire alongside Leto's tasks during the Phase 2 → Phase 3 promotion period (≥ 2 weeks). After Leto's tasks are dialed in (≤ 1 ⚠️/❌ reaction per week sustained 2 weeks), retire Cowork's daily and weekly. One source-of-truth principle.

## Failure modes

- **Wrong-context brief surfacing inappropriate items** → kill switch is `enabled=false`. Diagnose via session log.
- **Brief becomes nagging on famine days** → weekday-only enforcement already in place.
- **Daily note already has `## Brief (auto)` from earlier run** → prompt exits early.
- **Granola MCP unavailable** → graceful degradation: daily brief falls back to direct Granola fetch; granola-intake logs error and exits.
- **Slack/Calendar/Linear/Notion MCP unavailable** → daily brief structurally degrades and writes available sections only with "live data unavailable" markers.
- **HR-shaped recipient appears in a nudge that looks like an auto-action recommendation** → counts as a ❌ reaction; the rule is per-action approval, not exclusion from awareness, so awareness-only is fine.

## Phase boundary review

**Phase 2 → Phase 3 promotion criteria:**

- 2 weeks of clean operation (10 weekday brief runs + 2 weekly reviews + ~10 granola-intake runs)
- ≤ 1 ⚠️ or ❌ reaction per week (tracked in `80 System/82 Dashboards/Brief Reactions.md`)
- Granola source/extract files accumulating without errors
- Vladimir explicit "ready for Phase 3" → at that point we lock the Phase 3 deferred decisions

## Locked Phase 2 decisions (from 2026-05-01 entry)

- Daily brief cadence: 09:45 Mon–Fri Madrid
- Weekly review cadence: Friday 16:30 Madrid
- Monthly sweep cadence: First Sunday 10:00 Madrid
- Granola intake cadence: 19:00 Mon–Fri Madrid
- Memory→vault promotion rule: time-based 90-day stable (see `~/Projects/Leto/conventions/memory-promotion.md`)
- Cowork's existing daily/weekly stay running in parallel until Phase 3 entry; retire then.

## Open at Phase 2 close (deferred to Phase 3 entry)

- Approval surface for Tier 3 (Obsidian-only / Slack-only / dual)
- Channel allow-list for Tier 3
- Persona orchestration default for drafts
- Auto-capture cadence per stream beyond Granola (Slack threads, Linear comments, Gmail) — likely add slack-intake and linear-intake at Phase 3
