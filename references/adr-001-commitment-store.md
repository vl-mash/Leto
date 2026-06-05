# ADR-001 — Commitment store: vault register + Linear graduation

**Status:** Accepted  
**Date:** 2026-06-05  
**Ticket:** [VM-76](https://linear.app/manychat/issue/VM-76)  
**Author:** Leto (Vladimir Mashkovtsev)

---

## Context

Commitments surface in three places today:

1. **Granola extracts** — `## Action items — Vladimir's` (outbound) and `## Action items — others` (inbound, `**Name**: task` format). Written at 17:15 Mon–Fri but never persisted in a unified register.
2. **Slack `from:me`** — commitment-language phrases ("I'll send", "I'll set up", "I'll get back"). The EOD scheduler already parses these but only uses them to propose Linear tickets — no persistent register.
3. **TODO.md** — personal backlog for tasks that don't belong in a project tracker. Currently holds both personal tasks AND interpersonal commitments mixed together.

The consequence: commitments age without tracking. The Daria Senina survey template was promised by June 3–5 (since: 2026-05-21, now 15 days old). Ashby access and sourcing-tool-name follow-ups are 8 days past their May 28 trigger. All three are in TODO.md, escalated by the 7/14/21 ladder — but the ladder treats them the same as vault-hygiene tasks. No distinction between "I owe someone something" and "I want to clean up the goals folder."

---

## Decision

**Hybrid: vault register as working surface, Linear for real project work.**

`~/Obsidian Vault/Vladimir's Vault/40 System/Claude/Commitments.md` is the canonical home for all interpersonal commitments. The EOD scheduler can propose graduation to Linear once a commitment ages beyond 7 days AND is clearly project-level work (not a quick send-a-link).

---

## Options considered

### A — Linear only (all commitments → VM issues)

- ✅ Integrated with backlog, queryable, visible in EOD
- ❌ Clogs the backlog. "I'll send you that link" shouldn't be a ticket.
- ❌ Too slow to create (EOD propose → Vladimir approve → apply round-trip)
- ❌ Linear issues have wrong granularity — interpersonal accountability vs project delivery

**Rejected.** The friction-to-value ratio is wrong for small commitments.

### B — Vault register only

- ✅ Low friction, fast to append, stays in vault with everything else
- ✅ Works with existing `since:` marker + 7/14/21 escalation convention
- ❌ Not surfaced in EOD or daily-brief without explicit wiring
- ❌ Doesn't distinguish commitment-age from task-age — escalation treats them the same

**Partially accepted.** The vault register IS the working surface. But escalation needs to be sharper than the TODO.md ladder (commitment to another person carries social cost that "clean the vault" does not).

### C — Hybrid (accepted)

Vault register as the default landing zone. Commitments stay there unless:
- They're > 7 days old AND clearly project-level work → propose Linear graduation in EOD
- They're explicitly linked to an existing Linear ticket → drop the vault entry, the ticket tracks it

The register is separated from TODO.md by scope: TODO.md holds personal tasks; Commitments.md holds interpersonal commitments only (requires a named counterparty in `to:` or `from:`).

---

## Consequences

### Positive
- Small commitments tracked without clogging Linear
- Clear escalation path: vault → Linear for real work, stay in vault for quick items
- Consistent `since:` + `due:` metadata enables VM-77 deadline-aware escalation
- Granola action items and Slack commitments have a single landing zone

### Negative / risks
- Two systems: Commitments.md + TODO.md. Overlap risk if items straddle the boundary.
  - Mitigation: after Commitments.md is running, migrate the 5 interpersonal items from TODO.md and leave TODO.md for personal/vault tasks only.
- Vault register doesn't send notifications — it relies on daily-brief surfacing.
  - Mitigation: VM-77 adds deadline-aware escalation that makes the NUDGE louder as commitments age past their due dates.

### Future graduation criteria (for EOD scheduler to propose Linear ticket)
- Commitment age > 7 days AND deliverable is substantial (not a "send a link")
- Commitment is explicitly linked to a project or recurring area of work
- Vladimir says "track this properly" in a session

---

## Schema

See `conventions/commitments.md` for the full entry format.  
Register path: `~/Obsidian Vault/Vladimir's Vault/40 System/Claude/Commitments.md`  
Parser: `~/Projects/Leto/hooks/commitments.py`
