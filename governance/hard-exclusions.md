# Hard Exclusions — Tier 3 / Tier 4

These exclusions apply **regardless of tier or standing approval**. No SA can override them.

## 1. HR-shaped recipients

Always require per-action explicit approval. No standing approval, no automation.

| Person | Role | Why |
|--------|------|-----|
| Teo Georgoulis | Manager (Head R&D Ops) | Direct reporting line — political weight |
| Dima Kushnikov | CTO/CPO (skip-level) | Apex decision-maker — irreversible signals |
| Ingrid Bernaudin | CPTO (EPD apex) | Senior stakeholder |
| Nastya | VP Engineering | Senior stakeholder |
| Lu Borko | Senior business stakeholder | Political map |
| Sophia Tessum | People Partner | HR function |
| Kate Silaeva | VP Talent Acquisition | HR function |
| Irina Burykina | HR | HR function |

**Rule:** Any action where a HR-shaped person is the recipient, subject, or context
→ per-action approval required, even if a standing approval exists for that action type.

Checked by: `standing-approvals.py --hr-check "Name"`

## 2. Financial commitments

Never auto-commit to spend, contracts, or purchase approvals. Always per-action.

Examples: vendor approvals, budget sign-offs, contract acknowledgements, payments.

## 3. Irreversible deletions

Never auto-delete files, vault content, Linear issues, or Slack messages without confirmation.
Archive = OK. Delete = always per-action.

## 4. Outbound to external parties

Any message, email, or Slack DM to someone outside Manychat requires per-action approval.
Standing approvals only cover internal + DM-to-self actions.

## 5. Scope escalation

Standing approvals are scoped to the exact action-type and conditions registered.
They do NOT generalize. An SA for `eod-auto-apply Section B high-confidence` does NOT cover:
- Section A state updates
- Medium/low confidence items
- Items involving HR-shaped context
- Any action type not explicitly listed

## Enforcement

`standing-approvals.py --check "action-type" --recipient "Name"` enforces these rules
programmatically. Any scheduler or skill calling this should treat `approved: false` as a
hard stop and fall through to the normal per-action approval flow.

## Changes

These exclusions can only be changed by explicit session with Vladimir — not by Leto
autonomously. Changes must be documented in `references/CHANGELOG.md`.
