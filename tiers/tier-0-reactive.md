# Tier 0 — Reactive (status quo)

Leto only acts when Vladimir explicitly invokes it. No scheduled tasks, no polling, no autonomous behavior.

## What works at Tier 0

- `/leto` opens a Leto session: reads CLAUDE.md → INDEX.md → MEMORY.md → Me.md → reader-context.md → recent session log; prints a brief and waits for Vladimir's request.
- `/leto bootstrap` runs the one-time interview that generates reader-context.md.
- `/leto today` produces an on-demand brief using current vault, calendar, Slack inbox state.
- `/leto capture <thing>` manually captures a source (URL, Slack thread, Linear issue) into `00 Inbox/Sources/`.
- All 10 persona skills (`/pm`, `/cto`, etc.) load reader-context.md as part of the persona shim, so every persona invocation is Vladimir-shaped.

## What Tier 0 explicitly does NOT do

- No auto-generated daily brief at a scheduled time.
- No polling Slack for new mentions.
- No drafting replies.
- No reminders, nudges, or alerts.

## Boundaries

The system is **reactive by design at Tier 0**. Per Dima's stance: "Claude is reactive, not proactive… will not notice you haven't journaled in three days and remind you." This is correct for the foundation phase — it builds trust that Leto has correct context before any automation is layered on.

## Promotion criteria to Tier 1

Tier 0 has no formal promotion criteria — it's the default. Tier 1 (surfaced reminders) is enabled the moment `_claude/TODO.md` exists with `since:` markers and `/leto` knows to apply the 7/14/21 ladder. This is part of Phase 1.

## Verification

- `/leto` cold (no session memory) loads context and produces a brief without errors.
- `/pm "test"` returns a response showing reader-context.md influence (uses Vladimir's voice, applies hard don'ts).
- No scheduled task appears in `mcp__scheduled-tasks__list_scheduled_tasks` for Leto.
