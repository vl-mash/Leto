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

### Bootstrap completion (same day)
- Generated `~/Obsidian Vault/Vladimir's Vault/80 System/reader-context.md` v1 (61 lines, within tolerance) via `/leto bootstrap` interview.
- Logged decisions to `~/Obsidian Vault/Vladimir's Vault/80 System/Bootstrap Decisions.md`.
- Updated `_claude/TODO.md` with Phase 1 closures and follow-ups (re-bootstrap reminder, voice-signature capture for Phase 3, /blake extraction cleanup).

### Persona shims applied
- 9 thin-wrapper skills (`pm`, `cto`, `designer`, `engineer`, `qa`, `security`, `growth`, `analytics`, `product-ops`): replaced single-line persona load with 3-step shim (read reader-context.md → load persona → user request). Cache-friendly per Law 6.
- `/blake` (inline persona, ~227 lines): prepended Vladimir-shaping note after `# Head of Product Operations / Chief of Staff` heading; full persona body unchanged.
- Documented `/blake` as a special case in `conventions/persona-shim.md`. Future cleanup: extract to thin-wrapper pattern.

### PHILOSOPHY.md rewritten
- Removed Dima-flavored framing. Anchored Vladimir's distinct stance: builder-shaped, politically literate (engages with the Irina-pattern guard), persona-orchestrating, graduated proactive, Manychat-context first-class. Operational principles remain (cache-friendly load order, output contracts, immutable source + regenerable extract, vault as cockpit, English-narration / RU-output language rule).

### Open at end of Phase 1
- Approval surface for Tier 3 (Obsidian / Slack / dual). Decided at Phase 3 entry.
- Channel allow-list for Tier 3. Decided at Phase 3 entry.
- Persona orchestration default for drafts. Decided at Phase 3 entry.
- Auto-capture cadence per stream. Decided at Phase 3 entry.
- Memory→vault promotion rule for stable patterns. Decided at Phase 2 entry.
- Voice signature for `vladimir-tov` enrichment — captured in TODO, addressed at Phase 3 entry.

---

## [Phase 1 — Bootstrap v2 depth] — 2026-05-01

Vladimir flagged that v1 was thin on personal life, hobbies, fun, thought patterns, and values. Re-opened the bootstrap to capture depth across three clusters.

### Added (in vault, not this repo)
- `Me.md` revisions: 4-value list (added Reliability) + Moral stance; Cognitive style + Builder-vs-architect + AI 10x in How I Think; significant rewrite of How I Relate (social texture, friend pattern, close friends, family situation); NEW section "Hobbies & Recharge"; Social drain bullet in Patterns & Pitfalls.
- `reader-context.md` bumped to v2 — reflects builder-by-circumstance / architect-by-aspiration, AI 10x, energy constraints, hobbies, evolution > destination, morally-flexible directive, retaliation-aware political guard.
- `Bootstrap Decisions.md` extended with v2 round.

### Updated (in memory)
- `feedback_political_pattern.md` — appended clarifying paragraph: rule is calibrated retaliation, not no retaliation. Personas should not moralize; advise tactically.

### Decided
- **Builder by circumstance, architect by aspiration (1-3-5y)**. AI 10x is the lever to make the transition.
- **Reliability** added as the 4th core value (was missing from v1's ranked list).
- **Evolution > destination**. Progress is the success metric.
- **Morally flexible**. Don't moralize at Vladimir. Help him think tactically.
- **Retaliation when wronged is in scope**; the political-pattern guard is "calibrate, be subtle, count the cost," not "don't retaliate."
- **Best Saturday is solo, seldom achievable.** System should not push social or productive weekends.

---

## [Phase 2 — Tier 2 scheduled] — 2026-05-01

Tier 2 schedulers shipped. Four scheduled tasks registered via `mcp__scheduled-tasks__create_scheduled_task`. Adopts Vladimir's existing Cowork prompts as substrate where applicable; adds Leto-distinct layers (Vladimir-shaping, vault write, reaction tracker, political-pattern guard).

### Scheduled tasks registered

| Task ID | Schedule | Purpose |
|---|---|---|
| `leto-daily-brief` | 09:45 Mon-Fri Madrid | Comprehensive daily briefing — adopts Vladimir's Cowork 9-section prompt + 3-bullet recommendation layer + reaction tracker. Writes to today's daily note. |
| `leto-weekly-review` | Friday 16:30 Madrid | End-of-week retrospective + next-week plan. Adopts Cowork weekly prompt structure. Writes to Journal/Weekly/<YYYY-Www>.md. Doesn't auto-fill Wins/Challenges (keystone is Vladimir's review). |
| `leto-monthly-sweep` | First Sunday 10:00 Madrid | Appends `## Monthly Synthesis` block to latest weekly review for Vladimir to fill in. |
| `leto-granola-intake` | 19:00 Mon-Fri Madrid | Captures new Granola meetings as immutable source.md + regenerable extract.md (personalized via reader-context.md) at `00 Inbox/Sources/granola/`. Powers daily brief Granola section without re-fetching; grounds Phase 3 drafts. |

### Decided at Phase 2 entry

- Daily brief cadence: **09:45 Mon-Fri Madrid** (15 min before peak window).
- Weekly review cadence: **Friday 16:30 Madrid** (switched from initial Mon 10:00 — wrap-the-week is better than start-the-week for retrospective).
- Memory→vault promotion rule: **time-based 90-day stable** (auto-propose at next bootstrap refresh).
- Brief Reactions tracker added to `80 System/82 Dashboards/Brief Reactions.md` — Phase 3 promotion gate signal (≤ 1 ⚠️/❌ per week sustained 2 weeks).
- Cowork's existing daily/weekly stay running in parallel until Phase 3 entry; retire then.

### Added (this repo)

- `schedulers/daily-brief.md` — full prompt + 9-section structure adopted from Cowork + Vladimir-shaping + vault write
- `schedulers/weekly-review.md` — Friday 16:30 retrospective + next-week plan
- `schedulers/monthly-sweep.md` — first Sunday append to latest weekly
- `schedulers/granola-intake.md` — continuous Granola capture (source/extract pattern)
- `conventions/memory-promotion.md` — 90-day stable rule
- `tiers/tier-2-scheduled.md` — promoted from placeholder to active spec

### Added (vault, separate commit)

- `80 System/82 Dashboards/Brief Reactions.md` — manual aggregation of Tier 2 brief reactions; Phase 3 promotion gate signal
- `20 Goals/23 Reviews/Performance Review 2025-10.md` — Anna Bokareva, exceed expectations
- `20 Goals/23 Reviews/Performance Review 2026-01.md` — Anna Bokareva, exceed expectations (substantial)
- `80 System/Career Profile.md` — added Performance reviews table linking the two new files

### Parked (logged in TODO)

- Dima Kushnikov's [nestor-plugin](https://github.com/dkushnikov/nestor-plugin) — decision-making capability inspiration. Most plausibly a Phase 4+ consideration. Read repo, decide whether to borrow primitives or build a Leto-equivalent.

### Phase 3 promotion gate (open)

- 2 weeks of clean operation (10 weekday brief runs + 2 weekly reviews + ~10 granola-intake runs)
- ≤ 1 ⚠️ or ❌ reaction per week
- Granola source/extract files accumulating without errors
- Vladimir explicit "ready for Phase 3" → lock the Phase 3 deferred decisions then

---

## [Phase 2 — guardrail simplification] — 2026-05-01

Vladimir audited the guardrail set and dropped two:

### Removed
- **Political-pattern guardrail** — politics is now treated as any other domain. Leto doesn't filter political-map names from briefs, doesn't surface "neutral only" framing in extracts, doesn't apply the 3 calibration tests as imposed gates. `feedback_political_pattern.md` rewritten as Vladimir's own learning (historical context + 3 self-applied tests) rather than Leto-imposed rules. Personas can echo the tests back when Vladimir asks; otherwise treat politics like any domain.
- **AI-first vs AI-native terminology rule** — dropped from operational layers. Vladimir still uses AI-native externally (per Career Profile and user_role memory), but Leto doesn't enforce or auto-rewrite. Descriptive references in identity files preserved; rule references removed.

### Kept (audited list)

**Core safety (all kept):**
- No outbound action without approval at Tier 0/1/2
- No file deletes
- No instructions from observed content (prompt-injection defense)
- Empty results require explicit handling
- No silent file writes
- Failure as structured output

**Architectural (all kept):**
- Don't modify Me.md or persona files
- Stay in tier
- Cite when asserting

**Personal-context filters (kept):**
- HR-shaped recipients require explicit per-action approval — even at Tier 4 (preserves agency, prevents auto-fire to Manager/VP/Director/People Partner/COO/CPTO)
- Low ToV-confidence → "no draft — please handle directly" (Phase 3+ only)
- Don't push social weekends / honor energy reality

### Files updated
- `~/Obsidian Vault/Vladimir's Vault/80 System/reader-context.md` — removed political and AI-first hard don'ts; updated personas section
- `~/.claude/projects/-Users-vladimir-mashkovtsev/memory/feedback_political_pattern.md` — full rewrite as Vladimir's own learning
- `~/Projects/Leto/CLAUDE.md` — politics framing softened, HR-shaped rule promoted to top-level guardrail
- `~/Projects/Leto/PHILOSOPHY.md` — Politically-literate principle reframed (no imposed rules)
- `~/Projects/Leto/skills/leto.md` — guardrail #5 moved from political-pattern to HR-shaped
- `~/Projects/Leto/schedulers/{daily-brief,weekly-review,monthly-sweep,granola-intake}.md` — political guard removed; AI-native rule removed
- `~/Projects/Leto/tiers/tier-2-scheduled.md` — political-guard-breach failure mode dropped
- `~/Projects/Leto/tiers/tier-3-drafts.md` — political hard exclusion removed; HR-shaped exclusion strengthened
- `~/Obsidian Vault/Vladimir's Vault/80 System/82 Dashboards/Brief Reactions.md` — reaction definition updated; politics no longer counts as breach
- 4 registered scheduled tasks — prompts updated via `mcp__scheduled-tasks__update_scheduled_task` to drop political/AI-native references

---

## [Pre-Leto] — 2026-04-15

Inherited from Vladimir's existing infrastructure (not part of this repo, but referenced):

- `~/Projects/Agents/` — 10 persona skills + `BEST_PRACTICES.md` (17 sections).
- `~/Obsidian Vault/Vladimir's Vault/` — PARA-shaped vault, `Me.md`, dashboards, templates.
- `~/.claude/projects/-Users-vladimir-mashkovtsev/memory/` — Claude Code memory across user/feedback/project/reference types.
- MCP connectors: Notion, Slack, Linear, Granola, Gmail, Calendar, YouTrack.
