# Schedulers

Phase 2+ scheduled-task definitions. Each file is one cadence.

## Status: empty — schedulers ship in Phase 2.

When Phase 2 entry is approved, this directory will hold:

- `daily-brief.json` — 09:45 weekday Europe/Madrid; appends `## Brief (auto)` to today's daily note.
- `weekly-review.json` — Friday 16:30 Europe/Madrid; pushes notification + Slack DM-to-self.
- `monthly-sweep.json` — first Sunday of each month.
- `slack-poll.json` — Phase 3; 30-min poll for inbound messages outside peak window.

Each scheduler is consumed by `mcp__scheduled-tasks__create_scheduled_task` at install time.

## Format

```json
{
  "name": "leto-daily-brief",
  "schedule": "45 9 * * 1-5",
  "timezone": "Europe/Madrid",
  "enabled": false,
  "notes": "Honors Vladimir's peak window 10–12 by firing 15 min before."
}
```

(Exact schema confirmed at Phase 2 entry against the MCP tool's contract.)
