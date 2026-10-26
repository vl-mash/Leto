# Leto v2: PRD

Draft 2026-10-26 · Owner: Vladimir Mashkovtsev · Reviewer: Vladimir (personal project; no Linear home since the VM team was removed)

## TL;DR

Leto becomes a chief of staff and builder harness that works where Vladimir already works: RND Linear and his project folders.

- **Daily brief:** what matters today and why, plus what's new in AI he could use.
- **Weekly brief:** the org and its politics.
- **Capture:** turns his meeting commitments into RND Triage issues.
- **Every session:** knows his context, and makes starting a project and resuming one cheap.

It never asks him to react, approve or reply. The v1 push-and-approve machinery is archived.

## Problem & why now

Vladimir runs about eight R&D Ops projects at once and switches between them all day. Linear tells him what exists, but not what matters this week, what to prepare for, or what he promised in yesterday's meeting. Every new Claude session starts without his context unless the project copied it in.

Leto v1 tried to solve this by sending him things on a schedule and asking him to react. He stopped reading it. Five redesigns changed the format, and none changed the outcome. By October 2026 its routines were pointed at a Linear team that no longer exists. They ran a handful of times a month and mostly maintained their own alarms. Meanwhile the parts that do help (meeting intake, people memory, his writing voice) are spread across 16 project folders.

## Who it is for, and what they come to do

Vladimir only. He comes to:

- See, once a day, which three things matter and why, with prep for the meetings that count.
- Read once a week what moved in the org: who joined, moved or left, what leaders are pushing, what that means for him.
- Jump back into a project without re-reading everything.
- Start a new project with a PRD, a Linear project and a repo skeleton in one step.
- Write as himself, not as an AI.

## Outcome & success signal

- The daily brief arrives every weekday for two weeks running, from RND data, with every idea tied to a real RND project.
- At least 60% of the issues Leto captures into RND Triage are accepted.
- He invokes `/leto` modes at least 3 times a week by mid-November 2026.
- No routine depends on his reply, and no alert repeats.

## Solution

Ten components (A–J) in seven phases. Full design in `~/.claude/plans/hey-i-think-it-snoopy-stardust.md`.

| Phase | Ships |
|---|---|
| 0 | Archive v1 push and governance machinery; keep Granola intake; this PRD |
| 1 | One shared context file imported by every session; `/leto` returns Today's 3 on demand |
| 2 | Daily brief v4 (Today's 3, calendar prep, risk, AI news, implementation ideas); capture → RND Triage |
| 3 | `/leto resume`, `/leto week`, weekly politics brief |
| 4 | `/new-project` skill; Linear receipts convention |
| 5 | Voice v2, rebuilt from real messages |
| 6 | Obsidian set up for reading |

## Dependencies

- **Connectors:** Linear, Slack, Google Calendar, Granola, Humaans and web search, reachable from the scheduled runner. Cloud vs. local is decided by a spike in Phase 2.
- **Linear:** the RND team and Triage stay available for capture.
- **Q4 priorities:** the Q4 2026 KRs are the priority spine for ranking.

## Open questions

- Cloud routine or local scheduled task for the briefs? Owner: Claude (Phase 2 spike) · 2026-11-06
- Canonical source of the Q4 KRs: the Career file or Linear initiatives? Owner: Vladimir · 2026-10-30
- Monday 09:30 for the politics brief, or another slot? Owner: Vladimir · on first run
- Replace the claude.ai `vladimir-tov` with v2? Owner: Vladimir · after Phase 5
