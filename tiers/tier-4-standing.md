# Tier 4 — Standing approvals (Phase 4 scope)

> **Status: roadmap.** Detailed at Phase 4 entry. This file is a placeholder summarizing the intent.

## Intent

Pre-authorized narrow patterns that fire without per-message approval. The smallest possible expansion of autonomy, gated by hard exclusions.

## Examples (illustrative, not committed)

- Auto-decline meeting invites outside 10–18 Europe/Madrid working hours.
- Auto-thumbs-up to status pings in `#ops-team`.
- Auto-acknowledge Granola digest emails.

## Rule shape

Each rule lives in `~/Obsidian Vault/Vladimir's Vault/80 System/Standing Approvals.md` with frontmatter:

```yaml
---
rule-name: <slug>
trigger:
  system: slack | gmail | calendar
  match: <pattern>
action: <action description>
expires: YYYY-MM-DD                 # default 30 days
created: YYYY-MM-DD
last-fired: ""
fire-count: 0
---
```

## Hard exclusions (regardless of tier)

Same as Tier 3. Tier 4 does not relax any of them. Standing approvals only ever match patterns that are *outside* the exclusion zones.

## Governance

- Monthly review: open `Standing Approvals.md`, prune unused rules (fire-count = 0), re-affirm active rules.
- Every Tier-4 action also writes to `00 Inbox/Drafts/` for audit and surfaces in the next daily brief — Vladimir always sees what fired.
- Any exception to a rule (Vladimir manually overrides) bumps the rule into "review on next monthly" status.

## Promotion criteria

There is no Tier 5. Tier 4 is the ceiling. Beyond Tier 4, behavior changes require explicit per-rule approval, never blanket policy expansion.
