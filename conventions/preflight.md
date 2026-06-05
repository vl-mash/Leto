# Preflight convention (VM-74)

Every Leto scheduled task MUST run preflight as its absolute first action — before loading
any vault files, memory, or context. A single fast Python call; typically < 1 second.

## Instruction block for SKILL.md files

Copy this verbatim as **PART A / STEP 1** (or STEP 0 if steps are 0-indexed):

```
STEP 0 — PREFLIGHT (run before anything else):
Run: `python3 ~/Projects/Leto/hooks/preflight.py`
Parse the JSON output:
- status "abort" → send ONE Slack DM to U06A5QCK073 via
  `~/Projects/Leto/integrations/slack/leto-bot-post.sh U06A5QCK073 -`:
  "⚠️ *Leto scheduler paused* (<task-name>) — <abort_reason>. Resume: `rm ~/.config/leto/schedulers-paused`"
  Then write a one-line session log (type=session, session-skill=<task-name>, note=aborted-preflight)
  and EXIT. Do not proceed with the task.
- status "warn" → log each issue in the session log under "preflight warnings"; continue.
- status "ok" → continue (say nothing if repaired=[] and issues=[]).
- If "repaired" is non-empty → note repaired items in session log.
```

## What preflight checks

| Check | Level | Action |
|-------|-------|--------|
| `~/.config/leto/schedulers-paused` exists | ABORT | Halt + Slack alert |
| `~/.config/leto/linear-api-key` missing | WARN | Log, continue |
| `~/.config/leto/slack-bot-token` missing | WARN | Log, continue |
| `~/.config/leto/cost-cap.json` missing | WARN | Log, continue |
| Vault root not accessible | WARN | Log, continue |
| `~/Projects/Leto/CLAUDE.md` missing | WARN | Log, continue |
| Granola processed registry missing | REPAIR | Create stub, log in `repaired` |
| Today's daily-journal stub missing | REPAIR | Create with frontmatter, log in `repaired` |
| Granola sources directory missing | REPAIR | `mkdir -p`, log in `repaired` |
| Current year's sessions directory missing | REPAIR | `mkdir -p`, log in `repaired` |

## Pause flag lifecycle

Written by `scheduled-cost.py --pause-if-over USD` (in `leto-weekly-review` Step 7b) when
today's programmatic spend exceeds the daily cap in `~/.config/leto/cost-cap.json`.

To resume: `rm ~/.config/leto/schedulers-paused`

The flag contains JSON `{paused_at, reason, daily_spend_usd, cap_usd}` for auditability.

## Script location

`~/Projects/Leto/hooks/preflight.py`

Exit codes: 0 = ok/warn (continue), 1 = abort (halt).

See `hooks/README.md` for the full docs.
