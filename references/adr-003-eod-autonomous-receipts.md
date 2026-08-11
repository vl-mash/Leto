# ADR-003 — EOD goes autonomous-with-receipts (scoped reversal of propose-only)

**Status:** Accepted
**Date:** 2026-08-11 (interview 2026-08-10)
**Ticket:** [VM-139](https://linear.app/manychat/issue/VM-139)
**Amends:** [ADR-002](adr-002-linear-only-commitments.md) ("capture is propose-only" — that clause only, for one workflow; everything else in ADR-002 stands)
**Author:** Leto (Vladimir Mashkovtsev)

---

## Context

ADR-002 (2026-08-03) made Linear the only task store and declared capture **propose-only**:
the EOD loop proposes, Vladimir approves via Slack thread reply + a slash command. Eight days
of evidence: **8 of the last 10 EOD proposals were never reviewed** (`status: pending-review`
forever), and the apply command was used roughly twice in the loop's lifetime (2026-06-18,
2026-07-31). The ceremony didn't gate the automation — it parked it.

Interviewed on 2026-08-10, Vladimir chose the opposite posture for this one workflow:
*"kill the approval ceremony — auto-apply status transitions and new tickets, send me a
message with updated/created tickets."* He selected auto transitions AND auto creation at
medium+high confidence explicitly.

The same interview killed the assumptions propose-only was built on: the reaction/approval
feedback loops were "friction by design" (38 briefs, 1 reaction; 34-day silence). A gate
nobody operates is not a gate — it's a queue where work goes to die. That was ADR-002's own
finding about the register; the approval thread turned out to be the same failure one layer
up.

Two adversarial review cycles (doubt-driven, 2026-08-11) ran before this ADR: cycle 1 (25
findings) on the design — HR-matcher substring bug, missing drift checks, caps, gate ordering;
cycle 2 (15 findings) on the crash-safety mechanics — which forced the append-only JSONL
ledger with intent-before-act event pairs, the mkdir run-lock, any-date recovery scan, and
stored-receipt re-delivery. Actionable findings are folded into the v3 design; accepted
trade-offs are recorded below. Stopped after two cycles (skill allows three): the remaining
findings class is implementation-level, and SA-002 v2's 30-day expiry + receipts + undo are
the runtime containment.

## Decision

**`leto-personal-backlog-eod` mutates Linear autonomously, within hard gates, and receipts
every mutation.** Scope — exactly and only:

| Allowed | Bounded by |
|---|---|
| Status transitions on existing **VM-team** issues: → In Progress, → Done, → Todo | Single-candidate match only; Done needs strong match + Vladimir's own completion statement; In Review and Done/Canceled untouchable; drift check before each write; ≤5/run |
| New **VM-team** Triage tickets from unmatched signals | `learning-loop.py` confidence ∈ {high, medium}, not suppressed; v1 noise rules; ≤5/run |
| ONE receipts DM to Vladimir per run | SA-001; Slack `auth.test` verified **before** the first mutation — no receipt channel, no mutations |

**Never:** other Linear teams, deletions, Linear comments, HR-shaped items (transitions OR
creations — those go to a "needs your call" receipt list, per-action approval always),
anything beyond the table above. The authorizing grant is **SA-002 v2** (Standing
Approvals.md); if it lapses, STEP 1b degrades the task to propose-only automatically —
expiry-as-dead-man's-switch, with the VM-139 fail-loud ping firing at T-7.

**Reversibility is load-bearing:** a per-run ledger (`.local-data/eod-ledgers/`) records
before→after for every mutation *as it happens* (crash-safe: an incomplete ledger blocks
reprocessing and re-delivers its receipt instead of double-applying). "undo VM-x" in any Leto
session reverts a transition (only if the state hasn't moved since) or cancels a created
ticket, and feeds the suppress list so repeat patterns stop being created. Tickets Vladimir
cancels by hand within 7 days feed the same list.

## Options considered

**A — Keep propose-only, lower the friction (one-tap "apply all").** Rejected: still a daily
tap Vladimir has demonstrated he won't take; the queue re-accumulates.

**B — Autonomous without receipts (trust + weekly recap).** Rejected: violates the audit
trail Leto is built on; a wrong auto-Done would be invisible for days.

**C — Autonomous with receipts + undo + caps (accepted).** Vladimir's explicit choice,
contained by the gates above.

## Consequences

### Positive
- Linear hygiene actually happens — the v2 evidence says proposals without automation equal
  no hygiene at all.
- The receipt DM is one glance; wrong actions cost one "undo VM-x", not a nightly ritual.
- The learning loop finally gets signal (undo + hand-cancel feed it); v2's approve/skip
  telemetry starved it (1 entry ever).

### Negative / accepted trade-offs (from the doubt review)
- **Medium confidence includes commit/session-log-derived tickets** — wider than SA-002 v1's
  high-only, per Vladimir's explicit pick. Contained by caps (≤5), noise rules, suppress
  learning, and the weekly auto-created recap. If junk exceeds tolerance, drop back to
  high-only by editing one gate line.
- **No shadow period.** Deliberate: a shadow week re-introduces the ceremony being killed.
  The first weeks' receipts + undo ARE the calibration channel.
- **A false auto-Done hides an issue from open-issue queries.** Mitigated (strong-match +
  own-statement rules, weekly auto-Done recap) but not eliminated. Accepted: the failure is
  visible in the receipt + weekly recap and one-tap reversible.
- **Suppress fuzzy-matching is weak on short titles** (stop-word stripping); exact-normalized
  match carries the load. Accepted for v1 of the loop.
- **Undo reverts only the latest mutation per issue** (chain-undo across days is a manual
  call), and equality-based undo can't distinguish "untouched" from "a human set the same
  state within minutes" — the `updatedAt` guard narrows the window to minutes. Accepted.
- **Linear notifications:** VM is a private team; mutations notify no one today. If a VM
  issue ever gains another subscriber, that issue becomes de-facto outbound — the HR gate
  plus VM-team-only scope is the containment. Revisit if VM stops being private.

### Reversal
Flip SA-002 `active=false` (task degrades to propose-only on its next run) or disable the
task. v2's propose-only prompt is in this file's git history (pre-VM-139). Ledgers make
every applied mutation individually revertible.

## Convention updates carried by this ADR
- `CLAUDE.md` (compass) + `conventions/linear-tracking.md`: "capture is propose-only" →
  "capture is autonomous-with-receipts for the EOD VM-team workflow (ADR-003); everything
  else propose-only".
- ADR-002's SA-002 review note ("flag for review at the next monthly governance pass") is
  discharged by this ADR: SA-002 v1 is superseded by v2, reviewed 2026-08-11.
