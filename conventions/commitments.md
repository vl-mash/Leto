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
