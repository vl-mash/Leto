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
| **Every credential live-probed** (`leto_secrets.py --check`) | WARN | Log the failing key + its `cause`; continue |
| No `leto.env` and no legacy key files | WARN | Log, continue — run `scripts/migrate-secrets.sh` |
| `~/.config/leto/cost-cap.json` missing | WARN | Log, continue |
| Vault root not accessible | WARN | Log, continue |
| `~/Projects/Leto/CLAUDE.md` missing | WARN | Log, continue |
| Granola processed registry missing | REPAIR | Create stub, log in `repaired` |
| Today's daily-journal stub missing | REPAIR | Create with frontmatter, log in `repaired` |
| Granola sources directory missing | REPAIR | `mkdir -p`, log in `repaired` |
| Current year's sessions directory missing | REPAIR | `mkdir -p`, log in `repaired` |

## Credentials

All Leto secrets live in ONE file: `~/.config/leto/leto.env` (mode 600), outside every git
work tree. Template and per-key provenance: `~/Projects/Leto/.env.example`.

Resolution order per key — environment variable → `leto.env` → legacy
`~/.config/leto/<name>` single-value file. Legacy files keep working, so migration needs no
flag day.

```bash
bash scripts/migrate-secrets.sh          # consolidate legacy files -> leto.env
python3 hooks/leto_secrets.py --check    # live-probe every credential
python3 hooks/leto_secrets.py --names    # which key resolves from where (never values)
```

**Why probes, not file checks.** Preflight used to assert that credential *files existed*.
The Linear key file existed for 23 days (2026-08-24 → 09-16) while returning 401, and every
Linear-reading routine silently produced nothing. Existence proves nothing; only an
authenticated round-trip does. Each failing secret emits a named `cause`
(`linear-key-401`, `slack-bot-token-invalid`, …) in preflight's `blocker_causes`, which is
what the escalation ladder counts days against.

Network failure is **not** auth failure — a probe that cannot reach the host stays silent, so
a flaky connection never escalates as a dead credential.

## Pause flag lifecycle

Written by `scheduled-cost.py --pause-if-over USD` (in `leto-weekly-review` Step 7b) when
today's programmatic spend exceeds the daily cap in `~/.config/leto/cost-cap.json`.

To resume: `rm ~/.config/leto/schedulers-paused`

The flag contains JSON `{paused_at, reason, daily_spend_usd, cap_usd}` for auditability.

## Script location

`~/Projects/Leto/hooks/preflight.py`

Exit codes: 0 = ok/warn (continue), 1 = abort (halt).

See `hooks/README.md` for the full docs.
