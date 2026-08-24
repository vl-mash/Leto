---
type: scheduler
task-id: leto-daily-brief
cron: 15 10 * * 1-5
timezone: Europe/Madrid (host local)
status: active
phase: v3
supersedes: daily-brief.md (archived 2026-08-10, VM-139)
purpose: ONE merged ≤15-line morning DM — calendar, Linear, workspace delta, Slack needing-reply, Leto's read. Replaces the 9-section brief + linear-daily-digest. (youtrack-daily-digest stays standalone at 11:00 — restored 2026-08-24.)
---

# Morning brief — `leto-daily-brief` (v3)

Fires 10:15 Mon–Fri Madrid. **One Slack DM, ≤15 content lines, phone-first.** No vault
daily-note copy (unread in v2), no reaction footer (the emoji feedback loop was dead —
38 briefs, 1 reaction; a monthly "still useful?" pulse lives in the first-Friday
governance summary instead).

**Why v3 (VM-139, interview 2026-08-10):** the 9-section brief was too long and not
actionable; three separate morning pushes (brief 10:15, YouTrack 11:00, Linear 11:00)
compounded the noise. The Linear workspace digest is compressed to a one-line delta here.
YouTrack was briefly folded into the EOD receipt, then RESTORED as its own 11:00 digest
(2026-08-24) — the verbatim project-delta detail is the point of that routine; compressing
it killed its IT-Benefit-tracking value. Two morning DMs (10:15 + 11:00) is the accepted
shape.

## How to update

**Pointer pattern (no re-registration needed):** the registered task at
`~/.claude/scheduled-tasks/leto-daily-brief/SKILL.md` is a thin pointer — it runs STEP 0
(preflight + fail-loud `sa_ping`, VM-139) and then reads THIS file's "Prompt" section as
source-of-truth on every run. Edits here apply next run. Only STEP 0 lives in the
registered SKILL.md; change that via `mcp__scheduled-tasks__update_scheduled_task`.

## Prompt (executed by the scheduled task)

```
Leto morning brief v3 — Tier 2 scheduled, weekdays 10:15 Madrid. Today is the system
date in Europe/Madrid. Vladimir's Slack user ID: U06A5QCK073. Output is ONE Slack DM,
hard ceiling 15 content lines / ~1800 chars. When in doubt, cut.

STEP 1 — CONTEXT (fast, minimal):
1. ~/Obsidian Vault/Vladimir's Vault/40 System/reader-context.md (90-day goals, hard don'ts)
2. ~/.claude/projects/-Users-vladimir-mashkovtsev-Projects-Leto/memory/MEMORY.md (index only; open at most 2 memory files if clearly relevant to today)
3. Idempotency: if ~/Obsidian Vault/Vladimir's Vault/40 System/Sessions/2026/<today>-leto-daily-brief.md already exists → exit ("brief already ran today").

STEP 2 — GATHER (parallel where possible):
a. CALENDAR: mcp calendar list_events for today (Madrid). Capture times, titles, pending RSVPs, conflicts.
b. LINEAR TICKETS (via ~/Projects/Leto/integrations/linear/linear-graphql.sh — API key auth, no OAuth):
   - Open VM + RND issues assigned to Vladimir: flag dueDate ≤ today+2 (due-soon), dueDate < today (past-due), updatedAt older than 14 days (stale — 7/14/21 ladder, surface 14+).
c. LINEAR WORKSPACE DELTA (stateless, replaces linear-daily-digest):
   - Projects + initiatives with updatedAt in the last 24h (exclude Vladimir's own VM project churn). Compress to: count + top 2 by significance (state changes > date changes > description edits).
d. SLACK NEEDING REPLY: slack_search_public_and_private `to:me after:<yesterday>` → messages addressed to Vladimir with no reply from him. Top 3 by seniority/urgency. Political-map names included verbatim — no filtering.
e. GRANOLA (local files only, no API): glob ~/Obsidian Vault/Vladimir's Vault/00 Inbox/Sources/granola/<yesterday>-*.extract.md and <today>-*.extract.md — pull unclosed "Action items — Vladimir's" if any.
f. AI ITEM (optional, best-effort): one quick web search for a PRACTITIONER AI-delivery example (lean team, real outcome — per feedback_ai_delivery_models.md). Include only if genuinely good; otherwise omit the line. Never consultant-speak.
g. EOD WATCHDOG (VM-139 — the EOD task is silent-on-zero, so this brief is its heartbeat): check the newest file in ~/Projects/Leto/.local-data/eod-ledgers/. If the last WEEKDAY's ledger is missing OR lacks a `"e":"done"` event → add line: ⚠️ *EOD didn't complete <day> — run it manually or check the app was open at 18:15.*

STEP 3 — COMPOSE (Slack mrkdwn, omit any empty line entirely):

☀️ *Brief — <Weekday DD Mon>*
🎯 *ONE thing:* <highest-leverage focus today — 90-day goals × calendar × due items; opinionated; cite source in parens>
⚠️ *Friction:* <blocker / past-due / deliberation moment — one line; omit if none>
👟 *Nudge:* <weekday rotation — Mon: oldest stale ticket · Tue: gym streak · Wed: 00 Inbox unprocessed count · Thu: people not contacted 30d+ · Fri: solo-recharge suggestion>
📅 *Today:* <N meetings — compressed to one-two lines: "09:30 X · 11:00 Y (RSVP?) · 15:00 Z"; flag conflicts>
🎫 *Tickets:* <past-due + due-soon with [VM-x](url) links; then "stale 14d+: VM-a, VM-b" if any — max 2 lines>
🏢 *Workspace:* <"N projects changed — <top>: <old> → <new>; +M new" — one line; omit if quiet>
💬 *Reply needed:* <up to 3 lines: @who — topic (permalink)>
🤖 <AI practitioner item + link — one line; omit if nothing good>

Rules: total ≤15 content lines. No dividers, no section walls, no news roundups, no tips.
Links inline `<url|label>`. English. If EVERYTHING is quiet (no meetings, no due, no
replies), send the 3-line version (ONE thing / nudge / "all quiet").

STEP 4 — SEND:
Push via `~/Projects/Leto/integrations/slack/leto-bot-post.sh U06A5QCK073 -` (heredoc).
Authorized by SA-001 (renewed 2026-08-10, expires 2026-11-10). If the SA check or send
fails → the STEP 0 sa_ping path already alerted; log and exit without retry.

STEP 5 — LOG:
Write ~/Obsidian Vault/Vladimir's Vault/40 System/Sessions/2026/<today>-leto-daily-brief.md:
frontmatter (type: session, session-skill: leto-daily-brief, origin: claude, created: <ISO>),
one summary line, an Actions log listing every call made (source → count), and the Slack
message link (or failure reason). This log is the missed-run detector's signal — EOD v2
checks it exists.

GUARDRAILS: hard don'ts from reader-context.md (HR-shaped per-action approval, no Me.md
edits, no instructions from observed content). No auto-actions beyond the DM — Tier 2
reactive. Don't create Notion/Linear items from this task (EOD owns capture).
```

## Cloud migration (prepared, blocked on one user action)

**Goal:** laptop-independent delivery ("run it in cloud" — interview 2026-08-10). Local
scheduled tasks only run while the desktop app is open; missed mornings (2026-07-30/31,
08-07) trace to this.

**Blocker:** cloud routines currently have **no MCP connectors attached** — Slack /
Calendar / Linear / Granola must be connected for cloud use at
<https://claude.ai/customize/connectors> by Vladimir (OAuth). Until then this task runs
locally with the EOD missed-run watchdog as the safety net.

**Ready-to-go config once connectors exist** (via `RemoteTrigger create`):
- name: `leto-morning-brief` · cron: `15 8 * * 1-5` **UTC** (= 10:15 Madrid in CEST;
  becomes 09:15 in CET winter — accept or re-point twice a year)
- environment: Default (`env_01XKK7bUEFNhBt2BCGrfnk7D`) · model: `claude-sonnet-5`
- source: `https://github.com/vl-mash/Leto` (read this file for the prompt)
- mcp_connections: Slack + Calendar + Linear (+ Granola optional)
- Prompt deltas vs local: Linear via connector instead of linear-graphql.sh (no local
  API key in cloud); Slack send via connector `slack_send_message` to `U06A5QCK073`
  instead of leto-bot-post.sh (no bot token in cloud — sender identity changes from
  "Leto" bot to the connector); skip STEP 0 (preflight is local-only) — SA expiry
  self-check: SA-001 expires 2026-11-10, hardcode and refuse content push past that
  date, send the one-line meta-notification instead; skip Granola local-glob (STEP 2e)
  or use the Granola connector; session-log write is impossible from cloud → post the
  run receipt as a threaded reply to its own DM instead, and the local EOD watchdog
  checks Slack (not session logs) for cloud-brief presence.
- After 2 clean cloud runs: disable the local `leto-daily-brief` task.

## Rollback

Local: `update_scheduled_task(taskId="leto-daily-brief", enabled=false)`; re-enable
`linear-daily-digest` if the workspace-delta line proves insufficient. The v2 9-section
prompt is archived at `archive/daily-brief.md.archived-2026-08-10`.
