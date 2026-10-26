# Tier 1 — Surfaced reminders

Leto holds state about overdue items but Vladimir must invoke `/leto` to see it. No push, no automation — just better visibility when Vladimir does engage.

## What works at Tier 1

- `_claude/TODO.md` lives in the vault with `since:` markers on every entry (see `conventions/since-markers.md`).
- The 7/14/21 escalation ladder applies: soft mention at week 1, direct question at week 2, disposition proposal at week 3+.
- `/leto` brief surfaces: today's date, last session, stale TODOs (with ladder treatment), the "haven't contacted in 30 days" people query (Dataview already exists in vault), exercise streak counter (if vault Home dashboard exposes it).

## Triggers

- Vladimir invokes `/leto`, `/leto today`, or any persona skill.
- Vladimir manually adds entries to `_claude/TODO.md`.
- Leto adds entries to `_claude/TODO.md` at session-end when commitments emerge from the conversation (with `since:` set to today).

## Promotion criteria to Tier 2

Before enabling scheduled briefs (Tier 2):

1. Vladimir has used Tier 1 for at least 2 weeks.
2. The 7/14/21 ladder has surfaced at least 3 stale items and Vladimir has resolved them (parked, scheduled, dropped) — proving the convention is useful, not noise.
3. Vladimir explicitly requests Tier 2 promotion. No automatic graduation.

## What Tier 1 still does NOT do

- No proactive notification when something becomes stale.
- No scheduled briefs.
- No drafting outbound messages.

The state is **available**, not **announced**.
