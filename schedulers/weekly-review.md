---
type: scheduler
task-id: leto-weekly-review
cron: 30 16 * * 5
timezone: Europe/Madrid (host local)
status: active
phase: v3
pairs-with: weekly-collect.md (leto-weekly-collect, Mon+Tue 09:00)
purpose: Friday POSTER of the weekly ritual — one-screen week wrap to Slack DM + a thread with 3 interview questions Vladimir answers async. The Monday collector turns answers into the weekly note + next-week plan. No empty journaling skeleton.
---

# Weekly review v3 (poster) — `leto-weekly-review`

Fires Friday 16:30 Madrid. **The ritual now lives in Slack** (interview 2026-08-10:
*"it doesn't work now, but I really want to start using it"* + guided-conversation +
nudge-until-done + all-in-Slack). v2's approach — an auto-briefing in the vault with empty
Wins/Challenges/Surprises/Reflection sections — produced zero filled sections and zero
reactions; the skeleton is retired.

**Two halves:** this poster (Friday) sends the wrap + 3 questions as a Slack thread.
`leto-weekly-collect` (Mon 09:00, retry Tue) reads the replies, writes the weekly note,
posts the next-week plan, nudges once if silent, and keeps the streak.

## How to update

**Pointer pattern:** the registered task runs STEP 0 (preflight + sa_ping) then reads THIS
file's "Prompt" section as source-of-truth on every run.

## Prompt (executed by the scheduled task)

```
Leto weekly poster v3 — Tier 2 scheduled, Friday 16:30 Madrid. Today is the system date.
Vladimir's Slack user ID: U06A5QCK073. "This week" = Mon–today.

STEP 1 — CONTEXT:
1. ~/Obsidian Vault/Vladimir's Vault/40 System/reader-context.md
2. ~/.claude/projects/-Users-vladimir-mashkovtsev-Projects-Leto/memory/MEMORY.md (open
   project_career_repositioning.md for the receipts ladder)
3. ~/Projects/Leto/.local-data/weekly-streak.json (streak count; absent = streak 0)
4. Idempotency: if ~/Projects/Leto/.local-data/weekly-thread.json already has this ISO week
   → exit ("poster already ran").

STEP 2 — GATHER THE WEEK (all local/API, parallel where possible):
a. Linear VM+RND via linear-graphql.sh: issues completed this week (state.type=completed,
   completedAt in week) · still In Progress · due next week · stale 14d+.
b. EOD health: ledgers in ~/Projects/Leto/.local-data/eod-ledgers/ for Mon–Fri.
   Run-rate counts ONLY ledgers whose terminal event is {"e":"done"} with note "ok" or
   "recovered". Count {"e":"blocked"} ledgers separately and report them explicitly —
   `EOD 0/5 (5 blocked: linear-key-401)` — and treat a ledger with neither terminal event
   as incomplete, not as a run.
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

📅 *Week wrap — W<NN>*  _(streak: <N> weeks)_
*Shipped:* <top 3-5 completed VM/RND items with links; "+N more" if over>
*Receipts ladder:* <1-2 lines — career-relevant receipts that landed (cite), or "quiet week">
*Meetings:* <N processed; 1-2 key decisions>
*Leto ops:* brief <N>/5 · EOD <N>/5 runs · auto: <T> transitions, <C> created<, ⚠️ auto-Done
recap: VM-x "title", VM-y "title" — undo if wrong>
*Next week seeds:* <due-next-week + stale items, 1-2 lines>

Send via `~/Projects/Leto/integrations/slack/leto-bot-post.sh U06A5QCK073 -`. Capture
`channel` and `ts` from the JSON response.

STEP 4 — THE INTERVIEW THREAD (each question its own threaded reply, parent ts from STEP 3):
Q1: "1️⃣ *Wins* — what actually landed this week? 1-3 bullets, RU/EN, any length."
Q2: "2️⃣ *Friction* — what dragged, blocked, or surprised you?"
Q3: "3️⃣ *Next week* — your top 3. Skip this and Monday's plan is my guess, not your call."
FIRST FRIDAY OF MONTH ONLY, Q4 + governance block as a 4th reply:
   "4️⃣ *Pulse* — are the brief / EOD receipts / this ritual still earning their place?
   Одного слова хватит."
   Then append the governance summary to the same reply:
   - SA status: `standing-approvals.py --status` → one line per SA (expiry, review age)
   - Routine health: missed brief/EOD runs this month (session logs + ledgers)
   - Pointer integrity: registered SKILL.md for daily-brief / eod / weekly / collect still
     reference their repo docs (grep) — flag any that don't
   - Cost note if ~/.config/leto/cost-cap.json pause flag exists or spend is notable

Closing threaded reply:
"Reply to any of these whenever — I collect Monday 09:00 and turn it into the week plan.
Silence = plan is my best guess + streak resets."

STEP 5 — STATE + LOG:
a. Write ~/Projects/Leto/.local-data/weekly-thread.json:
   {"week":"<YYYY-Www>","channel":"<channel>","thread_ts":"<ts>","posted_at":"<ISO>",
    "questions":3|4,"collected":false,"nudged":false}
b. Session log 40 System/Sessions/<year>/<today>-leto-weekly-review.md: wrap summary line,
   thread permalink, counts. Include slack-thread-channel/-ts in frontmatter (audit).

GUARDRAILS: hard don'ts from reader-context.md. No Linear/Notion mutations. One DM thread to
U06A5QCK073 only (SA-001). Don't pre-fill Vladimir's answers — the keystone is HIS review.
English narration; RU verbatim where he wrote RU.
```

## Rollback

`update_scheduled_task(taskId="leto-weekly-review", enabled=false)` (+ same for
`leto-weekly-collect`). v2's single-task briefing prompt: git history of this file.
