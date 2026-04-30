# Changelog

Phase milestones and architectural decisions for Leto.

## [Phase 1 — Foundation] — 2026-04-30

### Added
- Repo scaffolding at `~/Projects/Leto/` (renamed from empty `~/Projects/Assistant/`).
- `CLAUDE.md` — the compass, loaded on every `/leto` invocation.
- `INDEX.md` — artifact map (single source for "where does X live").
- `BOOTSTRAP.md` — one-time interview script for generating reader-context.md.
- `PHILOSOPHY.md` — stance and principles (10 numbered).
- `tiers/tier-0-reactive.md` and `tiers/tier-1-surfaced.md` — Phase 1 active tiers.
- `tiers/tier-{2,3,4}-*.md` — roadmap placeholders for Phases 2–4.
- `skills/leto.md` — orchestrator definition (loaded by `/leto` skill wrapper).
- `conventions/persona-shim.md` — 3-line skill wrapper template for the 10 personas.
- `conventions/frontmatter.md` — typed YAML schemas for source / extract / draft / session log / reader-context.
- `conventions/since-markers.md` — 7/14/21-day escalation ladder, borrowed verbatim from Dima's obsidian-seed.
- `README.md` — entry point.

### Decided
- Project name: **Leto** (working name, rename anytime).
- Repo home: `~/Projects/Leto/` (renamed `~/Projects/Assistant/` in place — no migration).
- Federate identity: `Me.md` is canonical narrative, `reader-context.md` is the AI-facing operational distillation. They don't merge.
- Three-layer state: vault (persistent) / Claude Code memory (working patterns) / session logs (immutable).
- Reactive→proactive ladder, walked not jumped. Each tier requires ≥ 2 weeks of clean operation before promotion.
- All 10 personas get the reader-context.md shim (uniform; the file is bounded to ≤ 60 lines so cost is negligible).
- Bootstrap format: single 45-min session (Vladimir's choice over chunked).

### Borrowed from Dima Kushnikov
- Three-file continuity (`CLAUDE.md` + `MEMORY.md` + session log) — but Vladimir's MEMORY.md stays at the Claude Code path, not in the vault.
- `<!-- since: YYYY-MM-DD -->` TODO markers + 7/14/21 escalation ladder — verbatim.
- Reader Context as a personalization variable — adapted from mnemon's article-extract use case to Vladimir's persona-shaping use case.
- `origin: human | claude` frontmatter — applied to all Leto-generated artifacts.
- Stance: "Claude is reactive, not proactive. Value = context × request." — adopted as Tier 0 default; deliberate departure begins at Tier 2.

### Open at end of Phase 1
- Approval surface for Tier 3 (Obsidian / Slack / dual). Decided at Phase 3 entry.
- Channel allow-list for Tier 3. Decided at Phase 3 entry.
- Persona orchestration default for drafts. Decided at Phase 3 entry.
- Auto-capture cadence per stream. Decided at Phase 3 entry.
- Memory→vault promotion rule for stable patterns. Decided at Phase 2 entry.

---

## [Pre-Leto] — 2026-04-15

Inherited from Vladimir's existing infrastructure (not part of this repo, but referenced):

- `~/Projects/Agents/` — 10 persona skills + `BEST_PRACTICES.md` (17 sections).
- `~/Obsidian Vault/Vladimir's Vault/` — PARA-shaped vault, `Me.md`, dashboards, templates.
- `~/.claude/projects/-Users-vladimir-mashkovtsev/memory/` — Claude Code memory across user/feedback/project/reference types.
- MCP connectors: Notion, Slack, Linear, Granola, Gmail, Calendar, YouTrack.
