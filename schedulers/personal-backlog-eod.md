---
type: scheduler
task-id: leto-personal-backlog-eod
cron: 15 18 * * 1-5
timezone: Europe/Madrid (host local)
status: active
phase: v3
adr: references/adr-003-eod-autonomous-receipts.md
standing-approval: SA-002 v2 (eod-auto-apply)
purpose: End-of-day reconciliation between the day's actual work and the Personal Backlog (Linear VM team). v3 applies changes autonomously (status transitions + new Triage tickets) and sends ONE receipts DM. No approval ceremony. Undo via any Leto session.
---

# Personal Backlog EOD v3 — `leto-personal-backlog-eod`

Fires **18:15 Mon–Fri** Madrid (widened from 17:30 to leave ≥60 min after `leto-granola-intake`
at 17:15 — heavy meeting days overran the old 15-min gap; Friday added so Thursday-evening and
Friday work stops falling into a reconciliation hole).

**v3 (VM-139, ADR-003):** the v2 approval ceremony (Slack thread reply-with-IDs +
`/leto post-personal-backlog-eod`) is retired — 8 of the last 10 proposals were never
reviewed and the apply flow was used about twice ever. v3 **applies directly** within hard
guardrails and sends receipts. Reversal of ADR-002's propose-only posture is deliberate and
documented in [ADR-003](../references/adr-003-eod-autonomous-receipts.md); authorized by
**SA-002 v2** in `40 System/Standing Approvals.md`. Two adversarial design reviews
(doubt-driven, 2026-08-11) shaped the mechanics; accepted trade-offs are in the ADR.

## How to update

**Pointer pattern (no re-registration needed):** the registered task at
`~/.claude/scheduled-tasks/leto-personal-backlog-eod/SKILL.md` is a thin pointer — it runs
STEP 0 (preflight + fail-loud `sa_ping`, VM-139) and then reads THIS file's "Prompt" section
as source-of-truth on every run. Edits here apply next run.

## Key reference data

| Property | Value |
|---|---|
| Team ID (VM) | `24cb3ebb-859c-4313-abee-bc4438dbf63b` |
| Integration script | `~/Projects/Leto/integrations/linear/linear-graphql.sh` (key at `~/.config/leto/linear-api-key`) |
| Run ledgers (append-only JSONL) | `~/Projects/Leto/.local-data/eod-ledgers/<YYYY-MM-DD>.jsonl` |
| Run lock | `~/Projects/Leto/.local-data/eod-ledgers/.lock/` (mkdir-atomic; stale after 3h) |
| Feedback JSON | `~/Projects/Leto/.local-data/eod-triage-feedback.json` |
| Sweep memory | `~/Projects/Leto/.local-data/eod-swept.json` |
| YouTrack digest | `bash ~/.claude/scheduled-tasks/youtrack-daily-digest/digest.sh` |

**VM team state IDs** (stable): Triage `ee755d0f-cd32-4736-96be-daf3f77545f8` · In Progress
`ef4fe66c-8a69-4fdb-82bf-46c6d65f3125` · In Review `e3992ec0-1834-413d-bbcc-a2323c9829df` ·
Done `8949d3c1-40ba-4f66-a289-e70385a02771` · Backlog `828ddd53-b645-4951-995a-a4549bce8820` ·
Canceled `581105c5-c469-4d66-89fa-c21f90d990c2` · Todo `06ff6bc9-c5d7-4211-94eb-3c22429fe162`

## Ledger format (append-only JSONL — one event per line, never rewritten)

```
{"e":"start","date":"<YYYY-MM-DD>","window_start":"<ISO>","at":"<ISO>"}
{"e":"signal","id":"<source-id>","disposition":"matched|created|noise|suppressed|hr|ambiguous|over-cap|drift-skip","at":"<ISO>"}
{"e":"intent","identifier":"VM-123","action":"transition|create","before_state":"Todo","target":"Done","source_id":"<id>","at":"<ISO>"}
{"e":"applied","identifier":"VM-123","after":"Done|<created VM-NNN + url>","at":"<ISO>"}
{"e":"receipt_text","text":"<full receipt DM body>","at":"<ISO>"}
{"e":"receipt_sent","at":"<ISO>"}
{"e":"undone","identifier":"VM-123","at":"<ISO>"}
{"e":"done","finished":"<ISO>","note":"ok|recovered|aborted-<reason>"}
```

A truncated trailing line (crash mid-write) is ignored on read. **`intent` is written BEFORE
the Linear call; `applied` immediately after it returns.** An `intent` with no `applied` means
the call's outcome is unknown → reconcile by fetching the issue: if its state equals the
intent's `target` (or the created ticket exists by title+timestamp), treat as applied.

## Prompt (executed by the scheduled task)

```
Leto Personal Backlog EOD v3 — Tier 4 scheduled (SA-002 v2), Mon–Fri 18:15 Madrid. Today is
the system date in Europe/Madrid. Vladimir's Slack user ID: U06A5QCK073. This task MUTATES
Linear (VM team only) within the gates below, then sends ONE receipts DM. It never messages
anyone but Vladimir. Ledger events per the "Ledger format" section of
~/Projects/Leto/schedulers/personal-backlog-eod.md.

================================================================
STEP 1 — GATES, IN THIS ORDER (all before any mutation):
================================================================
a. LOCK: mkdir ~/Projects/Leto/.local-data/eod-ledgers/.lock — if it already exists and is
   younger than 3h → exit silently ("another run in flight"). Older than 3h → remove it,
   proceed. Remove the lock at the very end of the run (and on every abort path).
b. SLACK GATE (receipt channel first — cheapest, and everything downstream needs it):
   `~/Projects/Leto/integrations/slack/leto-bot-post.sh --auth-check`. Fails → NO mutations,
   session log "aborted: no receipt channel", release lock, exit. The morning brief's
   watchdog surfaces the miss tomorrow.
c. RECOVERY SCAN: list ALL ledgers (not just today's) missing a "done" event, oldest first.
   For each incomplete ledger:
     - reconcile any intent-without-applied (fetch the issue; state == target → append the
       missing "applied" event; otherwise append {"e":"signal-requeue","id":<source_id>}).
     - if it has applied mutations and no "receipt_sent": re-send its stored "receipt_text"
       (prefix: "⚠️ recovered from an interrupted run — these DID apply:"). If no
       receipt_text stored, compose from its applied events. On send success append
       "receipt_sent"; on failure leave as-is (next run retries) and skip to exit.
     - append {"e":"done","note":"recovered"} ONLY after the receipt question is settled
       (sent, or nothing to send).
d. IDEMPOTENCY: if today's ledger now has a "done" event → release lock, exit.
e. SA GATE: `python3 ~/Projects/Leto/hooks/standing-approvals.py --check eod-auto-apply`.
   approved=false → PROPOSE-ONLY MODE: no mutations; compose the receipt as "would have
   applied" proposals; send it (channel already verified in 1b — on send failure, write the
   text to the session log); log, release lock, exit.
f. Load context: reader-context.md (hard don'ts) + this file.

================================================================
STEP 2 — SIGNAL WINDOW + COLLECTION:
================================================================
WINDOW: from the "window_start" of the OLDEST ledger recovered in 1c if any (so its
unprocessed signals re-enter), else from the newest done-ledger's "finished"; cap 72h back;
24h if no ledgers exist. Today's date labels the receipt; the WINDOW bounds the queries.

Collect (empty results fine):
A. Vault git commits:  git -C "<vault>" log --since "<window-start>" --no-merges
                       --author "vladimir" --pretty='%h|%s|%ai'  + touched paths per commit
B. Session logs created in window (40 System/Sessions/<year>/): skill, summary, decisions
C. Daily journal(s) in window: actuals, ONE-thing outcome, free-form notes
D. Granola extracts in window (00 Inbox/Sources/granola/*.extract.md): "Action items —
   Vladimir's", decisions. If today's granola session log is missing, add a receipt note
   ("granola hadn't run by EOD") — its signals land in tomorrow's window.
E. Slack from:me since window start: commitments ("I'll…"), work done ("shipped/done"),
   decisions. Skip acks. KEEP the permalink as the signal's source-id.
F. Leto repo commits in window (same git flags as A).

DEDUPE: drop any signal whose source-id appears as a "signal" event in the last 7 ledgers —
UNLESS its latest disposition there is "drift-skip" or it has a "signal-requeue" event
(those retry). Write a "signal" ledger event for EVERY signal the moment it is dispositioned.

================================================================
STEP 3 — MATCH against open VM issues:
================================================================
Fetch open VM issues (state.type not in completed/canceled) via linear-graphql.sh: id,
identifier, title, state{id,name}, dueDate, updatedAt, url.

Match heuristics per signal: exact title (case/whitespace-insensitive) · fuzzy ≥0.70 on the
keyword spine · path→project-prefix · shared keyword phrase.
- EXACTLY ONE issue matches → matched pair.
- >1 issue matches → NO action; disposition "ambiguous"; list in receipt with candidates.
- MATCH STRENGTH: "strong" = issue identifier cited in the signal (VM-123), exact title
  match, or path match; "weak" = fuzzy/keyword only.

================================================================
STEP 4 — HR GATE (applies to transitions AND creations):
================================================================
For every matched pair and creation candidate: run
`python3 ~/Projects/Leto/hooks/standing-approvals.py --hr-check "<issue title + signal text
+ extracted person names>"` (word-boundary matcher, RU/EN). hr_shaped=true → NO auto-action;
disposition "hr"; receipt "needs your call" list with the proposed action spelled out.
HR-shaped items are per-action approval, always.

================================================================
STEP 5 — APPLY (hard caps: ≤5 transitions + ≤5 creations; excess → disposition "over-cap"):
================================================================
Append the "start" event FIRST. If the ledger file cannot be written → abort (no ledger =
no mutations), session log, release lock, exit.

Per mutation, strictly: append "intent" event (with before_state) → make the Linear call →
append "applied" event. Never start a second call before the first's pair is complete.

5a. STATUS TRANSITIONS (matched, non-HR, single-candidate only):
  - DRIFT CHECK first: re-fetch current state. If it differs from STEP 3's fetch → skip,
    disposition "drift-skip" (retries tomorrow), note in receipt.
  - In Review: NEVER auto-transition (receipt mention only). Done/Canceled: never touch
    (undo excepted).
  - → Done: STRONG match AND completion language that is VLADIMIR'S OWN statement about HIS
    OWN work. Negations, others' completions, quotes, future tense NEVER count. Weak match +
    completion language → receipt suggestion only.
  - → In Progress: issue in Triage/Backlog/Todo + clear ongoing-work signal.
  - → Todo ("waiting"): explicit blocker language by Vladimir about his own item. Blocker
    context goes in the RECEIPT line — this task writes NO Linear comments.
  - Anything ambiguous (language OR match) → no change.
5b. NEW TICKETS (unmatched, non-HR, substantive — v1 noise rules stand: multi-file commits,
    real decisions, concrete Granola/Slack action items; never typo commits, acks, bot noise):
  - Score: `python3 ~/Projects/Leto/hooks/learning-loop.py --score "<title>" --source-type
    <granola-action|slack-commitment|session-log|git-commit>`.
  - Gate: confidence in {high, medium} AND suppressed=false → CREATE VM Triage ticket, title
    = short imperative, description = 1-2 lines + source citation + "_Auto-applied by Leto
    (SA-002 v2) — <ISO>_".
  - suppressed or low → disposition "suppressed"/"noise"; counted in receipt.
  - learning-loop.py failure → treat as medium, continue.

================================================================
STEP 6 — RECEIPT (compose → store → send):
================================================================
Compose the receipt body:

🌙 *EOD — <YYYY-MM-DD>*
✓ <VM-123|url> → Done  _(commit abc123)_          ← one line per transition
+ <VM-201|url> created  _(granola: <meeting>)_     ← one line per creation
⚠️ *Needs your call:* <item + proposed action (HR-shaped: <name>)>   ← if any
❓ *Ambiguous:* <signal> ↔ VM-a / VM-b             ← if any
⏸ *Over cap:* N more candidates held               ← if any
▫️ skipped: N (suppressed/noise) · drift-retry: N   ← if >0
📊 *YouTrack:* <delta, ≤3 lines>                   ← step 7 output
_undo: tell Leto "undo VM-123" in any session_

SEND RULE: send when (mutations > 0) OR (needs-your-call / ambiguous / over-cap > 0) OR
(warnings exist) OR (YouTrack has a delta). All zero → no DM (the morning brief flags a
missing/incomplete ledger next morning, so silence stays safe).

If sending: append "receipt_text" event (full body), send via
`~/Projects/Leto/integrations/slack/leto-bot-post.sh U06A5QCK073 -`, then append
"receipt_sent". Send failure → leave receipt_sent absent; the recovery scan re-sends the
stored text next run; mirror the body into the session log.

================================================================
STEP 7 — YOUTRACK DELTA (folded from the retired 11:00 digest; run BEFORE composing STEP 6):
================================================================
Run `bash ~/.claude/scheduled-tasks/youtrack-daily-digest/digest.sh`. Exit 0 → compress
stdout to ≤3 lines for the receipt. Exit 3 (no token) → omit silently. Exit 4 (API fail) →
one ⚠️ line. The script only advances its own state.json on success; if the receipt send
later fails, the delta is NOT lost — it lives in the stored "receipt_text" and is
re-delivered by the recovery scan.

================================================================
STEP 8 — CLOSE OUT:
================================================================
a. HAND-CANCEL SWEEP: for tickets auto-created in the last 7 ledgers, SKIP any identifier
   present in ~/Projects/Leto/.local-data/eod-swept.json OR having an "undone" event in
   those ledgers. Query the rest; any now Canceled → append the title to
   eod-triage-feedback.json → section_b.skipped_titles (suppress food) AND record the
   identifier in eod-swept.json (never double-counted).
b. Append eod-triage-feedback.json stats entry: {date, auto_transitions, auto_created,
   needs_call, skipped} (keep last 60).
c. Session log 40 System/Sessions/<year>/<today>-leto-personal-backlog-eod.md: window,
   signal counts, every mutation before→after, receipt status, errors.
d. Append {"e":"done","finished":<ISO>,"note":"ok"}. Release the lock.

================================================================
GUARDRAILS:
================================================================
- VM team ONLY. Never RND, never any other team. Never delete anything. NO Linear comments.
- Allowed auto-transitions: {In Progress, Done, Todo} on issues currently in
  Triage/Backlog/Todo/In Progress. In Review and Done/Canceled untouchable (undo excepted).
- Hard caps 5+5 per run. Signal floods (rebases, merges, bulk imports) land in "over-cap",
  never in Linear.
- HR-shaped → never auto, both directions. reader-context.md hard don'ts bind. Politics
  unfiltered in receipts — the gate is about ACTIONS, not visibility.
- Mutations without a verified receipt channel are forbidden (STEP 1b).
- English narration; preserve RU titles verbatim.
```

## Undo procedure (any Leto session: "undo VM-123")

0. Take the run lock (STEP 1a rules). If held by a live run → tell Vladimir "EOD run in
   flight — retry in a couple of minutes" and stop.
1. Find the LATEST non-undone mutation for that identifier across the last 7 ledgers. Older
   mutations of the same identifier are not auto-revertible (chain-undo is a manual call) —
   say so if the latest is already undone. Nothing found → report "outside the 7-day undo
   window or never auto-touched".
2. Fetch the issue's CURRENT state and `updatedAt`.
   - Transition undo: revert to `before_state` ONLY if current state == the mutation's
     target AND `updatedAt` is not meaningfully later than the mutation's `at` (≤ ~5 min
     drift). Otherwise → report "the issue moved since (state X, updated <ts>) — manual
     call", change nothing, write nothing.
   - Creation undo: if still open and `updatedAt` ≈ creation time → set Canceled. If it's
     been touched since → report and stop.
3. ONLY on a successful revert/cancel: append {"e":"undone"} to that ledger, append the
   title to eod-triage-feedback.json → section_b.skipped_titles (+increment skipped), and
   record the identifier in eod-swept.json (so the sweep never double-counts it).
4. Release the lock. Confirm in chat with the Linear link.

Known limitation (documented in ADR-003): equality-based undo can't distinguish "untouched"
from "a human independently set the same state within minutes" — the `updatedAt` guard
narrows this to a minutes-wide window; accepted.

## Relationship with other routines

| | this task (18:15 Mon–Fri) | morning brief (10:15) | weekly poster (Fri 16:30) |
|---|---|---|---|
| Writes Linear | YES (gated, capped, receipted) | no | no |
| Watches | morning brief ran today (session log; if absent, check Slack DM for a cloud-run brief before warning) | yesterday's EOD ledger has a "done" event? | EOD run-rate + auto-Done recap for the week |

## Rollback

`update_scheduled_task(taskId="leto-personal-backlog-eod", enabled=false)`. v2's propose-only
prompt: git history of this file (pre-VM-139). SA-002 v2 revocation: flip `active=false` in
Standing Approvals.md — STEP 1e then degrades the task to propose-only mode automatically.
