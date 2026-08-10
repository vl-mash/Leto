# ADR-002 — Linear is the only commitment store

**Status:** Accepted
**Date:** 2026-08-03
**Ticket:** [VM-138](https://linear.app/manychat/issue/VM-138)
**Supersedes:** [ADR-001](adr-001-commitment-store.md) (vault register + Linear graduation)
**Author:** Leto (Vladimir Mashkovtsev)

---

## Context

Vladimir named the problem directly: *"I have tasks in my team Linear (R&D Ops), my personal team in Linear (VM), and commitments you are creating and storing in Obsidian. I don't actually use commitments and mostly rely on Linear and… well… my memory. I want to reduce it to one source."*

ADR-001 chose a hybrid — the vault register as a low-friction landing zone, graduating to Linear when a commitment proved to be real project work. It rejected Linear-only on the grounds that *"'I'll send you that link' shouldn't be a ticket"* and that ticket creation was too slow.

**That rationale did not survive contact with the implementation.** VM-90 (2026-06-05) made every outbound commitment auto-create a Linear ticket on capture, and the routing table in `conventions/commitments.md` opens with "Every outbound commitment gets a Linear ticket." The register stopped being a filter in front of Linear and became a second copy of it — which then needed VM-91/VM-92 bidirectional sync to stay honest. Two stores, one of them unread.

The state at decision time (28 open entries):

| Signal | Count | Reading |
|---|---|---|
| Entries with a Linear ticket | 5 | The part that worked was the Linear part |
| Inbound ("others owe me"), untouched 45–62 days | 22 | Never used as task state |
| Past-due with no follow-up | 4 | Escalation fired into a surface nobody opened |
| Already flagged "propose disposition" (>21d) | 15 | The register knew it was dead |
| Entries recording work already finished | ≥1 (C-019) | Register didn't learn what memory already knew |

`TODO.md` told the same story: last edited 2026-06-02, 9 open items, 2 of them duplicates, 2 pointing at RND tickets that were already closed.

The failure wasn't the schema — `commitments.py` worked as specified. It was the assumption that a surface Vladimir doesn't open can hold state he depends on.

## Decision

**Linear is the only commitment store.** Two teams, one tool, split by audience:

| Team | Scope |
|---|---|
| **VM** | Personal + Leto-project + anything private (career, comp, HR-shaped counterparties). Default. |
| **RND** | R&D Ops function work that Teo / Anna / the team should see tracked. |

The Obsidian vault holds **knowledge only** — session logs, sources, extracts, journal, memory. Zero task state. `Commitments.md` and `TODO.md` are archived, not maintained.

### Capture is propose-only

No automation creates a task without Vladimir's tap. The `leto-personal-backlog-eod` loop is the single automated write path: it matches the day's signals (Granola extracts, Slack `from:me`, vault + repo commits, session logs) against open VM issues, proposes state changes and new tickets in a Slack DM thread, and applies what Vladimir approves with ✅/⏭️. In-session creation with an explicit yes stays available per `conventions/linear-tracking.md`.

Granola intake returns to pure knowledge capture: `source.md` + `extract.md` + memory updates. It no longer writes task state anywhere.

*(One exception survives from an earlier decision: SA-002 `eod-auto-apply` auto-creates Triage tickets for high-confidence, non-HR-shaped EOD items. Retiring it is a separate call — see Consequences.)*

### Inbound commitments are not task state

Things other people owe Vladimir are recorded as knowledge — in the meeting extract that captured them and in the relevant memory file — not as ageing checkboxes. This ratifies observed behavior: all 22 inbound entries were ignored for 45–62 days. Where an inbound promise actually blocks Vladimir's own work, it belongs as context on *his* issue.

### Escalation moves to Linear fields

The register's one genuinely useful feature was deadline-aware nudging. It is rebuilt on Linear's own fields in the daily brief's existing VM query:

- `dueDate` → past-due / due-today / due-soon tiers in the NUDGE slot
- `updatedAt` → the 7/14/21 staleness ladder that used to run on `TODO.md` `since:` markers

## Options considered

**A — Keep the hybrid, fix the sync.** Rejected: the sync wasn't broken; the surface was unused. More sync makes the duplicate more faithful, not more read.

**B — Vault-only, drop Linear for personal work.** Rejected: inverts observed behavior. Linear is where Vladimir actually works, and RND already requires it for team visibility.

**C — Linear-only (accepted).** One store, audience split by team. Costs the "append without a ticket" affordance — accepted, because the register proved that affordance was being used to *avoid* deciding, and undecided items simply aged.

## Consequences

### Positive
- One place to look. No reconciliation, no sync layer, no C-NNN ↔ VM-NNN mapping to keep straight.
- Escalation runs on fields Linear maintains itself, wherever Vladimir sets a due date — including from his phone.
- ~200 lines of parser plus three scheduler steps deleted rather than maintained.
- Capture is honest about cost: if something is worth a ticket it gets one; if it isn't, it was never going to get done from a checkbox either.

### Negative / risks
- **Small promises now need a ticket or nothing.** "Send Ilya the docs" becomes VM-136 or it lives in memory. Mitigation: the EOD loop proposes these from Slack/Granola signals, so the capture cost is a ✅ rather than a ticket-creation round-trip.
- **Inbound promises lose their nudge.** Nothing will remind Vladimir that Teo owes him something. Accepted deliberately (that nudge was ignored 22 times). Politically live inbound threads — the performance-rating and title-parity conversations — stay tracked in `project_career_repositioning.md`, where they were already better documented than in the register.
- **SA-002 remains an auto-write path**, which sits in tension with "propose-only." Left active because it was granted separately and expires 2026-09-05; flag for review at the next monthly governance pass.
- **Linear Triage becomes the place zombies accumulate.** The 7/14/21 staleness ladder in the brief is the countermeasure — it now runs against Linear instead of a file nobody opened.

### Reversal
Both repo and vault are git-tracked; archived files were moved, not deleted. Restoring means reverting the VM-138 commits, un-archiving `hooks/commitments.py` + the register, and re-activating SA-003.

## Migration record

Executed 2026-08-03 under VM-138. 28 register entries + 9 TODO items dispositioned: 5 already-linked left untouched, 1 new ticket created ([VM-137](https://linear.app/manychat/issue/VM-137), Arthur / Classic Linear migration), the rest dropped as stale, superseded, already-done, or inbound-not-tracked. Full per-item table in the archived register's tombstone header.

One open item surfaced by the migration: **VM-97** (C-017, R&D Ops governance doc for Teo) is archived in
Linear as of 2026-07-16 but still sits in "In Progress", so Linear's default issue query — and therefore
the daily brief — cannot see it. Left as-is pending Vladimir's call: un-archive to make it visible, or
cancel it deliberately. Flagged rather than silently changed, since archiving is usually intentional.
