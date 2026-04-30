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

- Anything political (per `feedback_political_pattern.md`): coalition-building, upward review, skip-level grievance, anything to/about Dima Kushnikov, Lu Borko, Anna Bokareva, or Irina-adjacent topics.
- Anything irreversible: calendar deletes, Linear issue closes, external email sends, Notion deletes.
- Anything financial: vendor commitments, expense approvals, billing.
- Anything HR: messages to Manager / VP / Director / People Partner / COO / CPTO recipients.
- Anything outside Vladimir's voice when `vladimir-tov` confidence is low.

When any exclusion fires, Leto surfaces "no draft — please handle directly" with a one-line context summary. The inbound source is still captured to `00 Inbox/Sources/`.

## Promotion criteria to Tier 4

- 4 weeks of clean operation.
- No political-map breaches.
- Edit rate < 30% (drafts sent without significant edits).
- Vladimir explicitly requests Tier 4 promotion.

## Open decisions deferred to Phase 3 entry

- Approval surface (Obsidian-only / Slack-DM-only / **dual** recommended)
- Channel allow-list (DMs only / DMs + named / DMs + #*-ops + #*-pilot)
- Persona orchestration default (always `/product-ops` / **route by content** recommended)
- Auto-capture cadence per stream
