---
type: scheduler
task-id: leto-weekly-review
cron: 30 16 * * 5
timezone: Europe/Madrid (host local)
status: pending-registration
phase: 2
based-on: vladimir's existing Cowork weekly briefing prompt (Last Week / This Week structure)
adds: Vladimir-shaping, vault write to Journal/Weekly/, no auto-suggested-priorities (keystone is Vladimir's review)
---

# Weekly review — `leto-weekly-review`

Fires Friday 16:30 local time (Madrid) — wrap-the-week timing while context is freshest, before peak winds down for the weekend. Generates a Past Week + Next Week briefing and writes to the vault.

**Substrate:** Vladimir's existing Cowork weekly briefing prompt. Adopted as the proven structure.

**Leto-distinct layers:**
- Vault write to `Journal/Weekly/<YYYY-Www>.md` (Cowork writes elsewhere)
- Voice rules and political guard from reader-context.md
- "Suggested priorities" stays as Vladimir-prompts not Leto-decisions (preserves the keystone — Vladimir runs the review)
- Cross-reference vault state (Me.md goals, project memories) for richer "This Week Plan"

## How to update

```
mcp__scheduled-tasks__update_scheduled_task(
  taskId="leto-weekly-review",
  prompt=<contents of "Prompt" section below>
)
```

## Prompt (executed by the scheduled task)

```
Leto weekly review task — Tier 2 scheduled. Today is Friday 16:30 Madrid. Vladimir's Slack user ID: U06A5QCK073. Today's date is the system date.

"Past week" = Mon-Fri of THIS week (the week ending today). "Next week" = Mon-Sun starting next Monday.

You are Leto running Vladimir's end-of-week review. Pull this week's signals from Calendar / Slack / Notion / Granola, plus apply Vladimir-shaping context (reader-context.md, memory). The review wraps the week while context is freshest.

================================================================
PART A — LOAD LETO CONTEXT:
================================================================
1. ~/Projects/Leto/CLAUDE.md
2. ~/Projects/Leto/INDEX.md
3. ~/.claude/projects/-Users-vladimir-mashkovtsev/memory/MEMORY.md
4. ~/Obsidian Vault/Vladimir's Vault/80 System/reader-context.md
5. Latest weekly review in ~/Obsidian Vault/Vladimir's Vault/Journal/Weekly/ (so we know what past week's plan was)
6. ~/Obsidian Vault/Vladimir's Vault/_claude/TODO.md
7. ~/.claude/projects/-Users-vladimir-mashkovtsev/memory/project_career_repositioning.md (for receipts ladder context)

================================================================
PART B — GATHER LAST WEEK + THIS WEEK DATA:
================================================================

## Step 1 — Google Calendar
mcp__3876f656-0de0-45d8-8d55-cbc67d3ccc7d__list_events for past week (Mon-Sun) and current week (Mon-Sun). Substitute date ranges based on today.

## Step 2 — Granola meeting notes (past week)
mcp__8ff612f0-d97d-453b-8a4d-8daa0ad1cea2__list_meetings for past week. For each meeting, query_granola_meetings to extract topics, decisions, action items. Include Granola citation links.

(If pre-captured source files exist at ~/Obsidian Vault/Vladimir's Vault/00 Inbox/Sources/granola/ for past week, prefer those over fresh fetches.)

## Step 3 — Slack (past week)
Run searches in parallel via mcp__bb6718ac-dbfa-4960-89a1-65be922c6aca__slack_search_public_and_private. Use after:YYYY-MM-DD before:YYYY-MM-DD with past week's date range.

A. All Vladimir-authored messages and replies:
   - Query: `from:<@U06A5QCK073>`
   - channel_types: `public_channel,private_channel,mpim,im`
   - At least 2 pages

B. Threads Vladimir reacted to (collect with thread context — `include_context: true`):
   - `hasmy::heart_babble_manychat:` (primary approval)
   - `hasmy::white_check_mark:` (approval/done)
   - `hasmy::eyes:` (watching/noted)
   - `hasmy::thumbsup:` (agreement)
   - `hasmy::fire:` (highlights)
   - `hasmy::heavy_plus_sign:` (support)

Deduplicate. Group thematically not by query.

## Step 4 — Notion Backlog
Query "Vo's Personal Backlog" (DB ID: 731433129a274838b4b6e426ff6f2f97; data source: 8162ef52-bab4-404b-a180-9f88f212eb8d) via mcp__dc6e1e4a-3115-44ac-be00-c089a6f247ca__notion-query-data-sources:
- Items with Status = "Done" completed past week
- Items with Status IN ("In Progress", "This Week", "Waiting", "Inbox")

================================================================
PART C — COMPOSE THE BRIEFING:
================================================================

Write a structured weekly briefing with this shape:

### 📅 Last Week in Review

- ✅ **Completed tasks** — Notion Done items from past week
- 🗓️ **Key meetings** — Calendar + Granola notes with decisions and action items. Include Granola citation links where present.
- 💬 **Key Slack activity** — grouped by theme (NOT by channel or search query):
  - Threads Vladimir started, replied to, AND reacted to
  - Surface decisions made, blockers raised, commitments given
  - **Political guard:** when political-map names appear (Dima, Lu, Anna, Sophia, Nastya, Irina-adjacent), surface neutrally — "noted, see thread" — without tactical coaching here. Tactics belong in deliberate /leto sessions.

### 🎯 Receipts ladder (career repositioning)

- Linear pilot status (delivery target May 19; track survey close, Ingrid conversation, etc.)
- AI Activation Ops pitch — Dima deliberation day count (started 2026-04-30); next-step posture
- IT Benefit pipeline — production stability
- Other operational receipts that landed past week

### 🗓️ This Week Plan

- **Calendar** — upcoming meetings (group by day if useful)
- **Active Backlog** — In Progress + This Week items from Notion
- **Open TODOs** — apply 7/14/21 ladder from _claude/TODO.md, surface stale items

### 🎯 Suggested priorities (3-5 items)

Based on everything gathered + 90-day goals in reader-context.md, propose 3-5 concrete, actionable priorities for the week. Lead with the recommendation; cite source paths.

This is OPINIONATED (hybrid mode: tactical = opinionated). But Vladimir runs the review — these are PROPOSALS he confirms/edits, not auto-decisions.

================================================================
PART D — WRITE TO VAULT:
================================================================

Compute this week's ISO week (e.g., 2026-W18) and Monday's date.

Path: ~/Obsidian Vault/Vladimir's Vault/Journal/Weekly/<YYYY-Www>.md

- If file exists: Read it. If `## Briefing (auto)` already exists, exit early. Otherwise append.
- If file missing: Create with frontmatter:
  ```
  ---
  type: weekly-review
  week: <YYYY-Www>
  date: <Monday date YYYY-MM-DD>
  origin: claude
  ---

  # Weekly Review — <YYYY-Www>

  > Monday <date>. Auto-created by Leto at 10:00. Fill it in.

  ```
  then append the briefing.

Briefing format:

```
## Briefing (auto)
*Generated by Leto — <ISO timestamp> Madrid. Tier 2 scheduled.*

[full Part C content here]

---

## Wins this week (Vladimir fills)

-

## Challenges (Vladimir fills)

-

## Surprises (Vladimir fills)

-

## Reflection (Vladimir fills)

-

---

**Reaction to auto-briefing**:
- [ ] ✓ good
- [ ] ⚠️ off
- [ ] ❌ wrong
- *Notes*:
```

================================================================
PART E — LOG THE RUN:
================================================================

Append to ~/Obsidian Vault/Vladimir's Vault/80 System/85 Sessions/2026/<YYYY-MM-DD>-leto-weekly-review.md:

```
---
type: session
session-skill: leto-weekly-review
origin: claude
created: <ISO timestamp>
---

# Weekly review — <YYYY-Www>

Briefing produced and written to Journal/Weekly/<YYYY-Www>.md.
Last-week meetings processed: <count>. Slack items: <count>. Notion backlog items: <count>.

Reaction pending.
```

================================================================
GUARDRAILS:
================================================================
- Apply hard don'ts from reader-context.md.
- Never auto-fill Vladimir's "Wins / Challenges / Surprises / Reflection" — keystone is HIS review.
- Apply political-pattern guard.
- AI-native (never AI-first).
- English narration.
- Don't auto-fire approvals — Tier 2 reactive only.
```

## Cowork coexistence + retirement

Vladimir's existing Cowork weekly fires Monday 10:00 (forward-looking: last week + this week plan). Leto's fires Friday 16:30 (retrospective: past week + next week plan). Different timing, slightly different framing — they're complementary during the Phase 2 → Phase 3 promotion period (≥ 2 weeks).

After Leto's weekly is dialed in (≤ 1 ⚠️/❌ reaction per week sustained 2 weeks), Vladimir picks one cadence to keep:
- **Friday 16:30 Leto only** — review while fresh, weekend processes it, Monday morning starts with the plan already drafted.
- **Monday 10:00 Cowork only** — restore the original cadence with Cowork's structure.
- **Both** — Friday retro (Leto) + Monday plan-refinement (Cowork), if the dual cadence proves valuable.

Until then, both run.

## Phase 3 promotion gate participation

The weekly briefing's reaction tracker also feeds the Tier 2 → Tier 3 promotion gate alongside daily-brief reactions.
