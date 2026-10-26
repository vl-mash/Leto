# Tier 3 — Approval-gated drafts (Phase 3 — ACTIVE as of 2026-05-15)

Slack-on-behalf, end-to-end. Leto detects inbound DMs and @mentions, drafts a response, surfaces for approval, sends on confirmation. Vladimir approves or rejects in the same Slack DM-to-self thread he already uses for briefs.

## Locked decisions (2026-05-15)

| Decision | Choice | Rationale |
|---|---|---|
| Approval surface | **Slack DM-to-self only** | Vladimir lives in Slack; vault is audit trail only. Dual surface adds friction without benefit at V1. |
| Channel allow-list | **DMs only (V1)** | Safest scope. Channel context adds noise and threading complexity. Expand at V2. |
| Persona routing | **Route by content** | `/product-ops` default; `/cto` for engineering questions; `/pm` for product decisions; `/blake` for ops/political; `/engineer` for code. Detection step classifies. |
| Detection cadence | **30-min unified poll** | Single scheduler covers all DMs. Outside 10–12 peak window to avoid interrupting focus time. |

## Active flow

1. **Detection** — `leto-slack-intake` scheduler polls every 30 min (except 10:00–12:00 Madrid peak). Reads unread DMs and @mentions. Creates a source file per thread: `00 Inbox/Sources/slack/<YYYY-MM-DD>-<sender>-<slug>.source.md`.

2. **Context gather** — For each new source: reads thread history + sender profile (Slack) + most recent Granola extract involving sender + any open Linear/Notion items linked to sender or topic.

3. **Drafting** — Persona classified by content type (see routing table above). `vladimir-tov` skill + `Voice Signature.md` applied for voice calibration. Confidence check: if audience confidence is "Low" or "Uncalibrated", surfaces "no draft — please handle directly" instead.

4. **Surfacing** — Leto bot posts to Vladimir's DM-to-self:
   ```
   ✉️ *Draft — <sender> · <topic slug>*
   <draft text>
   ──────────────
   👍 send · ✏️ edit · ❌ reject
   Source: <slack thread link>
   ```
   Vault audit doc at `00 Inbox/Drafts/slack/<YYYY-MM-DD>-<sender>-<slug>/decision.md`.

5. **Send** — On 👍: `slack_schedule_message` 30s in the future (recall window). On ✏️: Vladimir replies with edit instructions; Leto regenerates + re-surfaces. On ❌: logged, no send.

6. **Audit** — Weekly aggregate appended to Friday review: drafts surfaced / sent / edited / rejected / unanswered.

## Hard exclusions (never drafted, even at Tier 3)

- **HR-shaped recipients** (Manager / VP / Director / People Partner / COO / CPTO): drafts ARE generated and surfaced for review, but **never auto-sent** — require explicit per-action 👍 approval each time. No standing approval covers this audience.
- **Irreversible actions**: calendar deletes, Linear issue closes, Notion page deletes, external email to non-Manychat domains.
- **Financial**: vendor commitments, expense approvals, billing.
- **Low/uncalibrated voice confidence**: surfaces "no draft — please handle directly" with context. Voice confidence map in `Voice Signature.md` is authoritative.

When an exclusion fires: source still captured to `00 Inbox/Sources/`; Slack DM-to-self posts "⚠️ no draft — [reason]. Source captured."

**On politics:** not excluded. Drafts on political topics allowed, treated like any other domain.

## Ticket graph (M5)

| VM | Title | Dependency |
|---|---|---|
| VM-36 | Phase 3 entry — lock decisions + finalize spec | — (this file) |
| VM-37 | Slack intake scheduler (`leto-slack-intake`) | — |
| VM-38 | Drafting skill — persona routing + voice guard | VM-37 |
| VM-39 | Surfacing flow — Slack DM-to-self + reaction handling | VM-38 |
| VM-40 | Send mechanism — `slack_schedule_message` + recall | VM-39 |
| VM-41 | Audit aggregate — Friday review addition | VM-40 |

## Promotion criteria to Tier 4

- 4 weeks of clean operation.
- Edit rate < 30% (drafts sent without significant edits).
- Vladimir explicitly requests Tier 4 promotion.

## V2 scope (deferred)

- Channel allow-list expansion (DMs + named ops channels)
- Linear intake scheduler (`leto-linear-intake`)
- Thread-reply edit syntax (instead of "reply with instructions → regenerate")
- Auto-send for low-stakes, high-confidence, non-HR-shaped drafts (standing approval)
