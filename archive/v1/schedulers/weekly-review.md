---
type: scheduler
task-id: leto-weekly-review
cron: 30 16 * * 5
timezone: Europe/Madrid (host local)
status: active
phase: v4
pairs-with: none — v4 is one-way; the collector (leto-weekly-collect) is retired
purpose: Friday one-way week wrap to Slack DM + the weekly note written from real data. No questions, no nudge, no waiting on a reply. First Friday of the month also carries the portfolio governance summary.
---

# Weekly review v4 (one-way) — `leto-weekly-review`

Fires Friday 16:30 Madrid. Sends ONE week-wrap DM and writes the weekly note itself. It asks
nothing and waits for nothing.

## Why v4 retired the interview (2026-09-18)

The ritual has now failed the same way twice, in two different shapes:

- **v2** put an auto-briefing in the vault with empty Wins / Challenges / Surprises /
  Reflection sections → *zero* filled sections, zero reactions.
- **v3** moved it to Slack as a thread of 3 interview questions with a Monday nudge and a
  collector → *zero* answers across W36 and W37, streak `0/0`, **never once completed**.

Two consecutive redesigns, identical outcome. The common factor is not the surface (vault
then Slack) — it is that both designs made the artifact depend on Vladimir replying.
`feedback_scheduled_output_shape.md` records this as a standing rule: *never design around
reaction/approval loops*, already at three occurrences before this one. A third reshape of
the same dependency would be the fourth.

So v4 inverts it: the routine produces the whole artifact from data that already exists
(Linear, EOD ledgers, Granola, Slack, session logs). Vladimir's reflection is welcome as an
edit to the note, never as a precondition for it. Silence now costs nothing, so there is
nothing left to fail.

W36/W37 were also confounded — both overlapped his 2026-09-01..09-11 OOO — but the v2
result was not, and one mechanism failing twice on the same axis is enough.

## How to update

**Pointer pattern:** the registered task runs STEP 0 (preflight + sa_ping) then reads THIS
file's "Prompt" section as source-of-truth on every run.

## Prompt (executed by the scheduled task)

```
Leto weekly wrap v4 — Tier 2 scheduled, Friday 16:30 Madrid. Today is the system date.
Vladimir's Slack user ID: U06A5QCK073. "This week" = Mon–today.

STEP 1 — CONTEXT:
1. ~/Obsidian Vault/Vladimir's Vault/40 System/reader-context.md
2. ~/.claude/projects/-Users-vladimir-mashkovtsev-Projects-Leto/memory/MEMORY.md (open
   project_career_repositioning.md for the receipts ladder)
3. IDEMPOTENCY: if 40 System/Journal/Weekly/<YYYY-Www>.md already exists AND a
   <today>-leto-weekly-review.md session log exists → exit ("wrap already ran").
4. BLOCKER LADDER: read `blockers` from STEP 0's preflight. If any active cause lists
   leto-weekly-review in its `fatal_for` at tier >= 4, skip the Linear queries in 2a and say
   so in the wrap in one line — never omit a section silently because its source is dead.

STEP 2 — GATHER THE WEEK (all local/API, parallel where possible):
a. Linear VM+RND via linear-graphql.sh: issues completed this week (state.type=completed,
   completedAt in week) · still In Progress · due next week · stale 14d+.
b. EOD health: ledgers in ~/Projects/Leto/.local-data/eod-ledgers/ for Mon–Fri.
   JSON-parse every line; never string-match (two serialization styles exist in that
   directory and a grep silently under-matches — it already caused a real miss on
   2026-09-11).
   Run-rate counts ONLY ledgers whose terminal event is {"e":"done"} with note "ok" or
   "recovered". Count {"e":"blocked"} ledgers separately and report them explicitly —
   `EOD 0/5 (5 blocked: linear-key-401)` — and treat a ledger with neither terminal event
   as incomplete, not as a run. Ledgers written before 2026-09-18 with `done` + a note
   starting `aborted-` count as blocked.
   Also: total auto-transitions/creations, and list every auto-Done this week (identifier +
   title) — that recap is the safety net for wrong auto-closes.
   Until 2026-09-18 this counted any "done" event, and aborted runs wrote `done` with
   note "aborted-<reason>" — so it reported `EOD 5/5 runs` for weeks in which nothing ran.
   A health metric that cannot go down is not a health metric.
c. Granola extracts this week (00 Inbox/Sources/granola/): meeting count, key decisions,
   political-map moments (verbatim, unfiltered).
d. Slack this week: from:me highlights — decisions made, commitments given (compressed).
e. Morning-brief health: count this week's <date>-leto-daily-brief.md session logs vs
   weekdays.

STEP 3 — COMPOSE + SEND THE WRAP (one screen, Slack mrkdwn, ≤20 lines):

📅 *Week wrap — W<NN>*
*Shipped:* <top 3-5 completed VM/RND items with links; "+N more" if over>
*Receipts ladder:* <1-2 lines — career-relevant receipts that landed (cite), or "quiet week">
*Meetings:* <N processed; 1-2 key decisions>
*Leto ops:* brief <N>/5 · EOD <N>/5<, blocked: <cause> ><, ⚠️ auto-Done recap: VM-x "title",
VM-y "title" — undo if wrong>
*Next week seeds:* <due-next-week + stale items, 1-2 lines>
_Week note: <obsidian link or path>_

Send via `~/Projects/Leto/integrations/slack/leto-bot-post.sh U06A5QCK073 -`.

NO THREAD. NO QUESTIONS. NO NUDGE. Do not ask Vladimir to reply, rate, react to, or confirm
anything — that dependency is exactly what v2 and v3 died of. This is a report, not a form.

STEP 4 — WRITE THE WEEKLY NOTE (the artifact, from data — not a skeleton to fill in):
Path: ~/Obsidian Vault/Vladimir's Vault/40 System/Journal/Weekly/<YYYY-Www>.md
Frontmatter per conventions/frontmatter.md (type: weekly-note, origin: claude,
session-skill: leto-weekly-review, created: <actual `date -Iseconds`>, week: <YYYY-Www>).

Sections, all populated from STEP 2 — every claim carries its receipt (link, path, or
identifier). Write plain declarative prose; no empty headings, no prompts, no placeholders:
  ## Shipped              — completed items with links, grouped by project
  ## In flight            — still In Progress, with age
  ## Decisions            — from Granola extracts + Slack from:me, each with its source
  ## Meetings             — count + the ones that mattered and why
  ## Leto ops             — brief/EOD run-rate, blocked causes, auto-Done recap
  ## Next week            — due-next-week + stale 14d+, as candidates not commitments
  ## Vladimir's notes     — a single line: "_(add anything here — nothing waits on it)_"

That last section is an open door, not a question. If he writes in it, good; if he never
does, the note is already complete without him. Never pre-fill it, and never treat its
emptiness as a failure, a missed streak, or something to follow up on.

Task state stays in Linear (ADR-002) — this note records what happened, never a checkbox,
register entry or TODO.

STEP 5 — FIRST FRIDAY OF THE MONTH ONLY: append a governance block to the wrap message
(not a thread reply — v4 has no thread). This is the portfolio's own health surface, and the
one that should have caught the 2026-08-24 Linear outage 23 days earlier:
  - SA status: `standing-approvals.py --status` → one line per SA (expiry, review age)
  - Credentials: `python3 ~/Projects/Leto/hooks/leto_secrets.py --check` → name any secret
    not "ok" (the Linear key returned 401 for 23 days while its file sat happily in place)
  - Blocker ladder: any cause in .local-data/blocker-state.json at tier >= 3, with its
    day count and first_seen — a routine standing itself down must never be quiet news
  - Routine health: missed brief/EOD runs this month (session logs + ledgers)
  - Pointer integrity: registered SKILL.md for daily-brief / eod / weekly still reference
    their repo docs (grep) — flag any that don't
  - Cost: `scheduled-cost.py --json --days 7` → today / 7d / 30d / % of monthly credit

STEP 6 — LOG:
Session log 40 System/Sessions/<year>/<today>-leto-weekly-review.md: wrap summary line,
message permalink, the weekly-note path, counts. `created:` MUST be the actual
`date -Iseconds` value, never the nominal 16:30.

No state files. v3's weekly-thread.json and weekly-streak.json are retired — a streak that
counts answers is meaningless once nothing asks a question, and the weekly note's existence
plus the session log already provide idempotency.

GUARDRAILS: hard don'ts from reader-context.md. No Linear/Notion mutations. One DM to
U06A5QCK073 only (SA-001). English narration; RU verbatim where Vladimir wrote RU.
```

## Rollback

`update_scheduled_task(taskId="leto-weekly-review", enabled=false)`.

v3 (poster + interview thread + `leto-weekly-collect` collector) and v2 (vault skeleton) are
both in this file's git history. Restoring either means restoring a reply dependency that has
now failed twice — see "Why v4 retired the interview" before doing it.
