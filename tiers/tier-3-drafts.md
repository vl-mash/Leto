# Tier 3 — Approval-gated drafts (Phase 3 scope)

> **Status: roadmap.** Detailed at Phase 3 entry. This file is a placeholder summarizing the intent.

## Intent

Slack-on-behalf, end-to-end. Polling, dual approval surface, regenerable drafts, audit trail. Leto drafts; Vladimir approves; Leto sends.

## Planned flow

1. **Detection.** Scheduled task polls inbound channels every 30 min outside the 10–12 peak window. Reads unread @mentions and DMs.
2. **Context gather.** Thread + sender profile + relevant Granola/Linear/vault notes + memory political-map check.
3. **Drafting.** Persona-routed (`/product-ops` default, `/pm`/`/cto`/`/blake` by content) + `vladimir-tov` skill applied for voice.
4. **Surfacing.** Dual surface — `00 Inbox/Drafts/<system>/<slug>/{source.md, extract.md, decision.md}` in vault + Slack DM-to-self with reaction approvals (👍 send / ✏️ edit / ❌ reject).
5. **Send.** Via `slack_schedule_message` 30 seconds in the future — gives Vladimir a recall window if he reacts ⏪.
6. **Audit.** Weekly aggregate (sent / edited / rejected / unanswered) surfaces in Friday review.

## Hard exclusions (never drafted, even at Tier 3)

- **Anything to HR-shaped recipients** (Manager / VP / Director / People Partner / COO / CPTO): require explicit per-action approval at every tier. Drafts go to the approval surface; no auto-send even at Tier 4 standing approvals.
- **Anything irreversible**: calendar deletes, Linear issue closes, external email sends to non-Manychat domains, Notion page deletes.
- **Anything financial**: vendor commitments, expense approvals, billing-related.
- **Anything outside Vladimir's voice** when `vladimir-tov` confidence is low: surface "no draft — please handle directly" with the inbound context. **Voice calibration ground-truth**: `~/Obsidian Vault/Vladimir's Vault/80 System/Voice Signature.md` (13 principles + by-audience playbook + ~80 verbatim quotes). Load alongside `vladimir-tov` skill before drafting.

**On politics:** politically-charged topics are NOT excluded. Vladimir engages politics as strategic ground; drafts on political topics are allowed and treated like any other domain. The Irina-pattern guard from `feedback_political_pattern.md` is Vladimir's own learning, not a Leto exclusion — personas echo the 3 calibration tests back if Vladimir asks for them.

When an exclusion fires (HR-shaped, irreversible, financial, low ToV), Leto surfaces "no draft — please handle directly" with a one-line context summary. The inbound source is still captured to `00 Inbox/Sources/`.

## Promotion criteria to Tier 4

- 4 weeks of clean operation.
- Edit rate < 30% (drafts sent without significant edits).
- Vladimir explicitly requests Tier 4 promotion.

## Open decisions deferred to Phase 3 entry

- Approval surface (Obsidian-only / Slack-DM-only / **dual** recommended)
- Channel allow-list (DMs only / DMs + named / DMs + #*-ops + #*-pilot)
- Persona orchestration default (always `/product-ops` / **route by content** recommended)
- Auto-capture cadence per stream
