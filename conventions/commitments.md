# Commitments convention (VM-76)

The **commitment register** tracks interpersonal commitments — things Vladimir promised to
someone, or things others promised to Vladimir. It is distinct from `TODO.md` (personal tasks)
because every entry requires a named counterparty (`to:` or `from:`).

**Location:** `~/Obsidian Vault/Vladimir's Vault/40 System/Claude/Commitments.md`  
**Parser:** `~/Projects/Leto/hooks/commitments.py`  
**ADR:** `~/Projects/Leto/references/adr-001-commitment-store.md`

---

## Entry format

Every commitment is a single markdown list item with an HTML comment holding structured metadata:

```markdown
- [ ] <description> <!-- id: C-NNN | since: YYYY-MM-DD | due: YYYY-MM-DD | to/from: Name | source: <path or system> -->
```

Fields:
- `id` — sequential `C-NNN`, assigned at creation, never reused
- `since` — date the commitment was recorded (not a deadline; used for 7/14/21 ladder)
- `due` — explicit deadline if stated ("by Friday", "before Dima returns"); **if present, escalation fires at the due date, not just at 14 days**
- `to` — (outbound) person Vladimir committed to
- `from` — (inbound) person who committed to Vladimir
- `team` — Linear routing: `VM` (private, default) or `RND` (shared R&D Ops team)
- `linear-id` — VM-NNN or RND-NNN backlink; populated after ticket creation
- `ticket` — `none` for inbound monitoring items that should NOT graduate to Linear
- `source` — citation: granola extract slug, Slack permalink, or "TODO.md" for migrated items

Closed commitments use `- [x]` and get moved to `## Closed` at end of month.

---

## Register structure

```markdown
---
type: commitment-register
updated: YYYY-MM-DD
---

# Commitment Register

## Outbound — Vladimir's commitments

- [ ] description <!-- id: C-001 | since: 2026-06-01 | due: 2026-06-10 | to: Teo Georgoulis | source: granola/2026-06-01-day-1-week-kick-off.extract.md -->

## Inbound — commitments to Vladimir

- [ ] description <!-- id: C-002 | since: 2026-06-02 | due: 2026-06-07 | from: Daria Senina | source: granola/2026-05-21-ta-presentation.extract.md -->

## Closed

- [x] description <!-- id: C-000 | closed: YYYY-MM-DD -->
```

---

## Team routing (VM vs RND)

Every outbound commitment gets a Linear ticket. Routing:

| Condition | Team |
|-----------|------|
| Personal interaction (career, private conversation, personal follow-up) | `VM` |
| HR-shaped counterparty (Teo, Dima, Sophia, etc.) | `VM` always |
| Team deliverable, Teo/Anna comfortable seeing it tracked | `RND` |
| Project not yet formally approved as R&D Ops work | `VM` until approved |

Inbound commitments (others → Vladimir): register for monitoring only. `ticket: none` unless Vladimir needs to track an explicit follow-up action of his own. **Never create tickets on others' behalf.**

## What counts as a commitment (vs a personal task in TODO.md)

**Include in Commitments.md:**
- Vladimir said "I'll send / I'll do / I'll get back to you" to a named person
- A named person said they'd do something for Vladimir (deliverable, not just FYI)
- A meeting action item explicitly assigned to Vladimir or to a named other person

**Keep in TODO.md:**
- Tasks without a counterparty ("clean up vault", "run bootstrap")
- Personal errands ("book gym")
- Leto-project work → Linear

**Boundary case:** "Review Linear pilot end date" — if it came from a discussion with Teo, it's a commitment (to: Teo); if Vladimir just wants to do it himself, it's a TODO.

---

## Extraction sources

### Granola-intake (automated)
After writing each extract.md, the scheduler reads:
- `## Action items — Vladimir's` → each item becomes an outbound commitment IF it names a person
  (heuristic: contains a capitalized name or references a person just discussed)
- `## Action items — others` → `**Name**: task` lines → inbound commitment from that person

Threshold: only extract items that are explicit commitments (not status updates or observations).
Skip items that are purely informational ("Continue watching Biz Ops situation").

### Slack from:me (EOD, planned VM-77)
Commitment-language phrases in Slack messages:
- "I'll send / I'll do / I'll set up / I'll get back" + named recipient → outbound
- Currently EOD matches these to Linear tickets; after VM-77, also appends to Commitments.md

### Manual (/leto session)
Vladimir can say "add to commitment register: [description]" in any session.

---

## Status model (VM-77)

Status is stored in the `status:` metadata field:

| Status | Meaning | Escalation |
|--------|---------|------------|
| *(none)* / `open` | Active, tracking normally | Deadline-aware ladder |
| `on-hold` | Deliberately parked — waiting for info/capacity/input | Suppressed. Resurfaces after `hold-since` > 14d ("hold still valid?") |
| `blocked` | External dependency — someone else must act first | FYI only, not urgent |
| `done` | Completed | Moves to `[x]` and suppressed |
| `dropped` | Cancelled, won't do | Moves to `[x]` and suppressed |

`hold-reason` and `hold-since` fields only apply to `on-hold` / `blocked`.

**The stale-data problem:** Some status changes happen in Vladimir's head, not in Granola or Slack. The correction path is designed to be low-friction:
- In any `/leto` session: "mark C-005 on-hold: waiting for capacity data" → Leto calls `commitments.py --update`
- Slack reply on the daily-brief NUDGE thread (see below)
- Direct edit of Commitments.md (last resort)

## Slack reply correction (VM-77)

When the daily-brief NUDGE posts a commitments table to Slack, Vladimir can reply in that same thread with shorthand commands. The next day's brief (PART A step 8) reads those replies and applies them:

```
done C-001
on-hold C-005 C-006: waiting for capacity + Daria inputs
blocked C-007: waiting for Teo to debrief Nadia first
redate C-003 2026-07-31
open C-005         ← clears on-hold
drop C-NNN
extend C-005       ← reset hold-since to today (buy 14 more days of suppression)
```

Multiple commands per reply are fine (one per line). The brief applies each with `commitments.py --update`, then logs what it changed in the session log.

**Hold-stale resurface**: when `hold-since > 14 days`, the NUDGE sends: "C-005/C-006 have been on hold for N days — still waiting? Reply `extend C-NNN` / `unblock C-NNN: outcome` / `drop C-NNN`"

## Escalation (VM-77 — deadline-aware, builds on this register)

The `commitments.py --list` output feeds VM-77's daily-brief NUDGE:
- **due date present + past due**: escalate immediately (same day, every day until closed)
- **due date present + due soon (≤ 2 days)**: surface day-before reminder
- **no due date + since > 14 days**: direct question ("still active?")
- **no due date + since > 21 days**: propose disposition (close / park / graduate to Linear)

---

## ID assignment

The parser auto-assigns the next available `C-NNN` when given `--next-id`. IDs are sequential
across both Outbound and Inbound sections. Never reuse a closed ID.
