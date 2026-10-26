# schedulers/

One file per scheduled routine. Each uses the **pointer pattern**: the task registered in `mcp__scheduled-tasks` is a thin prompt that reads its doc here at run time. Edits apply on the next run with no re-registration.

| Doc | Task | Status |
|---|---|---|
| `granola-intake.md` | `leto-granola-intake`, 17:15 Mon–Fri | live |
| `daily-brief.md` | Cloud routine `trig_01RdFbMkCQgSw1fQ8eVA2L6Y` "Leto daily brief", weekdays 10:15 Madrid. Runs with the laptop closed and reads this file from `main` | live |
| `politics-weekly.md` | Weekly politics brief | Phase 3 |

v2 rules for every routine (from `CLAUDE.md`):
- It produces its artifact from existing data and never waits on a reply.
- A failed source is one line in the same output, never a separate alert.
- Runs are logged as one JSONL line in `.local-data/`, not as vault session logs.

v1 docs (morning brief v3, EOD, weekly review, collector, monthly sweep, …) are in `archive/v1/schedulers/`.
