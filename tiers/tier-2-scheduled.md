# Tier 2 — Scheduled prompts (Phase 2 scope)

> **Status: roadmap.** Detailed at Phase 2 entry. This file is a placeholder summarizing the intent.

## Intent

Adds harness wiring without adding outbound action. Builds trust that Leto has correct context before it ever drafts on Vladimir's behalf.

## Planned components

- **Daily brief** at 09:45 weekday Europe/Madrid — appends `## Brief (auto)` to today's daily note. Three bullets max: today's "ONE thing," friction points, one nudge (stale relationship / exercise streak / unprocessed inbox). Honors low-energy template — never displaces Vladimir's manual lines.
- **Friday weekly review prompt** at 16:30 — push notification + Slack DM-to-self ("weekly review ready"). Auto-fills Wins/Challenges/Surprises as drafts Vladimir edits.
- **First-Sunday monthly sweep** — appends `## Monthly Synthesis` to latest weekly review note.

## Trigger mechanism

`mcp__scheduled-tasks__create_scheduled_task` definitions live in `~/Projects/Leto/schedulers/`. Each scheduler is one JSON config per cadence.

## Failure modes (anticipated)

- Wrong-context brief surfacing inappropriate items → kill switch is `mcp__scheduled-tasks__update_scheduled_task` with disabled flag.
- Brief becomes nagging on famine days → reduce to 2 bullets or weekday-only.
- Brief misses critical items (e.g. early-morning Slack DM) → log to a "missed" review during weekly review.

## Promotion criteria to Tier 3

- 2 weeks of clean operation.
- ≤ 1 wrong-context complaint per week.
- Vladimir explicitly requests Tier 3 promotion.

## Open decisions deferred to Phase 2 entry

- Brief time (07:30 / 09:45 / on-demand only)
- Push surface (Daily note only / Daily note + Slack DM-to-self)
- Memory→vault promotion rule for stable patterns
