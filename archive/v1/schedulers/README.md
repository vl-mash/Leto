# Schedulers

Phase 2+ scheduled-task definitions. Each file is one cadence.

## Status: empty — schedulers ship in Phase 2.

When Phase 2 entry is approved, this directory will hold:

- `daily-brief.json` — 10:15 weekday Europe/Madrid; appends `## Brief (auto)` to today's daily note.
- `weekly-review.json` — Friday 16:30 Europe/Madrid; pushes notification + Slack DM-to-self.
- `monthly-sweep.json` — first Sunday of each month.
- `slack-poll.json` — Phase 3; 30-min poll for inbound messages outside peak window.

Each scheduler is consumed by `mcp__scheduled-tasks__create_scheduled_task` at install time.

## Format

```json
{
  "name": "leto-daily-brief",
  "schedule": "15 10 * * 1-5",
  "timezone": "Europe/Madrid",
  "enabled": false,
  "notes": "Fires inside Vladimir's peak window 10–12."
}
```

(Exact schema confirmed at Phase 2 entry against the MCP tool's contract.)
