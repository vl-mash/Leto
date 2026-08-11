---
type: scheduler
task-id: leto-weekly-collect
cron: 0 9 * * 1,2
timezone: Europe/Madrid (host local)
status: active
phase: v3
pairs-with: weekly-review.md (leto-weekly-review, Fri 16:30 poster)
purpose: Monday COLLECTOR of the weekly ritual — reads Vladimir's async replies to Friday's interview thread, writes the weekly note (auto wrap + his answers verbatim), posts the one-screen next-week plan, nudges ONCE if silent (Tuesday firing closes out regardless), keeps the streak.
---

# Weekly collect v3 (collector) — `leto-weekly-collect`

Fires **Monday and Tuesday 09:00** Madrid. Monday: collect-or-nudge. Tuesday: final collect —
close out with whatever exists. One nudge maximum (interview 2026-08-10: "nudge until done"
chosen alongside async — one ping, not a drip).

## How to update

**Pointer pattern:** the registered task runs STEP 0 (preflight + sa_ping) then reads THIS
file's "Prompt" section as source-of-truth on every run.

## Prompt (executed by the scheduled task)

```
Leto weekly collector v3 — Tier 2 scheduled, Mon+Tue 09:00 Madrid. Today is the system date.
Vladimir's Slack user ID: U06A5QCK073. The target week is LAST week (the one Friday's poster
wrapped).

STEP 1 — STATE:
Read ~/Projects/Leto/.local-data/weekly-thread.json.
- Missing, or "week" is not last week → session-log "no poster thread to collect" and exit
  (poster didn't run — the first-Friday governance block will surface the gap).
- "collected": true → exit ("already collected").

STEP 2 — READ THE THREAD:
`slack_read_thread` with the stored channel + thread_ts. (Reactions can lag on a first read —
if the thread looks empty, read it a second time before concluding silence:
feedback_slack_reaction_timing.) Extract every reply authored by Vladimir (U06A5QCK073),
mapped to the question each replies to (threading order; if he answered in one combined
message, split it sensibly).

STEP 3 — BRANCH:
A. HAS ANSWERS (≥1 substantive reply) → collect:
   1. Write ~/Obsidian Vault/Vladimir's Vault/40 System/Journal/Weekly/<YYYY-Www>.md
      (create or replace the auto sections; NEVER touch manual content if the file exists):
      ---
      type: weekly-review
      week: <YYYY-Www>
      date: <Monday-of-that-week YYYY-MM-DD>
      origin: claude
      ritual: slack-thread
      ---
      # Weekly Review — <YYYY-Www>

      ## Wrap (auto)
      <the poster's one-screen wrap, from its session log / thread parent>

      ## Vladimir's answers
      **Wins:** <verbatim, RU/EN as written>
      **Friction:** <verbatim>
      **Next week top-3:** <verbatim>
      <**Pulse:** verbatim, first-Friday weeks only>

      ## Next week plan (auto, from his top-3 + Linear)
      <3-5 concrete items: his top-3 first (cited as his), then due/stale VM+RND items>
   2. Update streak: ~/Projects/Leto/.local-data/weekly-streak.json →
      {"current": +1, "best": max, "last_completed": "<YYYY-Www>",
       "history": append {"week", "answers": N, "completed": true}} (keep last 26).
   3. Post the plan as a threaded reply to the poster thread:
      "✅ *Week <NN> plan* _(streak <N>)_
      1. <item> 2. <item> 3. <item>
      📓 Journal/Weekly/<YYYY-Www>.md"
   4. Mark weekly-thread.json "collected": true. Session log. Exit.

B. NO ANSWERS + today is MONDAY + "nudged": false → nudge (the ONE nudge):
   Threaded reply: "👋 2 minutes: three answers up-thread make Monday real. I collect again
   tomorrow 09:00 — after that the week closes without you."
   Set "nudged": true. Session log. Exit.

C. NO ANSWERS + today is TUESDAY (or nudged already) → close out:
   1. Write the weekly note as in A but "## Vladimir's answers" reads
      "_(no reflections this week — thread went unanswered)_" and the plan is built from
      Linear alone, labeled "_(my guess — you didn't call it)_".
   2. Streak: {"current": 0, history append {"week", "answers": 0, "completed": false}}.
   3. Threaded reply: "Week closed without your input — plan below is my guess.
      _(streak reset)_
      1. <item> 2. <item> 3. <item>"
   4. Mark "collected": true. Session log. Exit.

GUARDRAILS: hard don'ts from reader-context.md. No Linear/Notion mutations. One DM thread to
U06A5QCK073 only (SA-001). Vladimir's words land VERBATIM in the note — no paraphrasing, no
tone-softening. English narration around them.
```

## Rollback

`update_scheduled_task(taskId="leto-weekly-collect", enabled=false)`.
