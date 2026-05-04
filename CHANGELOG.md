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
- Brief Reactions tracker added to `80 System/Dashboards/Brief Reactions.md` — Phase 3 promotion gate signal (≤ 1 ⚠️/❌ per week sustained 2 weeks).
- Cowork's existing daily/weekly stay running in parallel until Phase 3 entry; retire then.

### Added (this repo)

- `schedulers/daily-brief.md` — full prompt + 9-section structure adopted from Cowork + Vladimir-shaping + vault write
- `schedulers/weekly-review.md` — Friday 16:30 retrospective + next-week plan
- `schedulers/monthly-sweep.md` — first Sunday append to latest weekly
- `schedulers/granola-intake.md` — continuous Granola capture (source/extract pattern)
- `conventions/memory-promotion.md` — 90-day stable rule
- `tiers/tier-2-scheduled.md` — promoted from placeholder to active spec

### Added (vault, separate commit)

- `80 System/Dashboards/Brief Reactions.md` — manual aggregation of Tier 2 brief reactions; Phase 3 promotion gate signal
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
- `~/Obsidian Vault/Vladimir's Vault/80 System/Dashboards/Brief Reactions.md` — reaction definition updated; politics no longer counts as breach
- 4 registered scheduled tasks — prompts updated via `mcp__scheduled-tasks__update_scheduled_task` to drop political/AI-native references

---

## [Phase 2 — Notion weekly alignment routine] — 2026-05-04

5th scheduled task added. Approval-gated Notion update routine — keeps Personal Backlog, Function Backlog, and Function OKRs aligned. Two-checkpoint design per Vladimir's "review every update before posting" requirement.

### Added
- `leto-notion-weekly-alignment` scheduled task — Monday 08:30 Madrid, read-only. Generates a proposal at `00 Inbox/Drafts/notion-alignment/<YYYY-MM-DD>.md` covering three sources (Personal Backlog `731433129a274838b4b6e426ff6f2f97`, Function Backlog `29db12e9aa1a8013942dc4e122b540b1`, Function OKRs page `2f0b12e9aa1a80798563f1524a8589af`).
- `~/Projects/Leto/schedulers/notion-alignment.md` — full spec including the Monday task prompt, the apply procedure for the manual command, and the proposal document schema.
- `/leto post-notion-updates <YYYY-MM-DD>` subcommand — added to `skills/leto.md` decision tree. Reads the proposal, parses `[x] Approve` checkboxes, pauses for explicit "yes" confirmation, then executes Notion writes for approved items only. Logs results back to the proposal's apply log.
- `00 Inbox/Drafts/notion-alignment/` directory in vault.
- `tiers/tier-2-scheduled.md` — added Notion alignment as 5th active component.

### Decided
- Cadence: Monday 08:30 Madrid (before peak window, before daily brief).
- Two control points: (1) read proposal, (2) trigger apply manually with explicit yes-confirmation. No automatic Notion writes anywhere in V1.
- Three proposal sections: A. Status updates (drift detection), B. New items (from Granola action items + Slack commitments), C. Alignment gaps (informational only — no apply action).
- This routine is a Phase-3-shaped capability shipped early, scoped narrowly to Notion alignment. Does NOT count toward Phase 2 → Phase 3 promotion gate (Slack-on-behalf still requires the broader Phase 3 entry decision).

### V2 deferred
- Auto-post for high-confidence trivial updates (after sustained clean operation).
- Two-way sync: every Granola meeting's action items auto-create Triage entries.
- OKR roll-up: when all linked Function items Done, propose KR status update.

---

## [Phase 2 — Slack DM-to-self push for daily/weekly] — 2026-05-04

Daily and weekly briefs now push highlights to Vladimir's Slack DM-to-self after vault write succeeds. Standing approval SA-001 documents the pattern.

### Added
- `~/Obsidian Vault/Vladimir's Vault/80 System/Standing Approvals.md` — new file. First entry SA-001 covers the DM-to-self pattern. 90-day expiry; re-affirm at next bootstrap refresh.
- STEP E (Slack push) added to daily-brief.md and weekly-review.md scheduler specs. Daily message ≤1500 chars (3-bullet recommendation + counts + vault link). Weekly message ≤3000 chars (highlights + receipts ladder + suggested priorities + vault link).
- Session logs now capture `Slack push: <success | failed>` line.
- Updated 2 registered scheduled tasks via `mcp__scheduled-tasks__update_scheduled_task` — prompts reference the standing approval.

### Decided
- DM-to-self is treated as a Tier-4-shaped standing approval, scoped narrowly to Leto's own auto-generated brief content. Recipient is Vladimir himself; reversible (can delete the message). Hard exclusions (HR-shaped recipients, irreversible, financial) still apply universally — SA-001 doesn't extend to other recipients or content.
- Failure mode: Slack push failure does NOT fail the task. Vault write is the source-of-truth; Slack is convenience surface. Logged but not retried.
- Granola intake and monthly sweep do NOT push to Slack (silent capture / quarterly cadence — no need).

### Pre-flight needed
- First daily brief run with Slack push enabled will pause on `slack_send_message` permission. Click "Run now" once on `leto-daily-brief` and `leto-weekly-review` to pre-approve.

### Pattern established
- The first standing approval. The Standing Approvals.md file is the registry; future SA-### entries follow the same shape (granted date, expiry, trigger, action, recipient, reversibility, format reference, failure handling).

---

## [Vault cleanup — aggressive restructure] — 2026-05-04

Vladimir audited the vault and approved aggressive cleanup. Resolved goal-scattering, 20-prefix collision, empty placeholder folders, and stale CLAUDE.md.

### Vault changes

**Deleted (6 empty placeholder folders):**
- `10 Work/12 Teams/`, `10 Work/13 Meetings/`, `10 Work/15 Decisions/`, `10 Work/16 Processes/`, `10 Work/17 Archive/` — all had only `.gitkeep`, no real content
- `80 System/83 Attachments/` — same

**Consolidated all goals into `20 Goals/`** (was scattered across 3 locations):
- `10 Work/18 Goals/Q1 2026 — *.md` (3 files) → `20 Goals/Quarterly/`
- `20 Personal/21 Goals/Quarterly/Q2 2026 — *.md` (3 files) → `20 Goals/Quarterly/`
- `20 Personal/21 Goals/Yearly/2026.md` → `20 Goals/Yearly/`
- `20 Personal/21 Goals/Vision.md` → `20 Goals/Vision.md`
- `20 Goals/22 Career/` → `20 Goals/Career/` (drop number)
- `20 Goals/23 Reviews/` → `20 Goals/Reviews/` (drop number)
- `80 System/Career Profile.md` → `20 Goals/Career/Career Profile.md` (co-locate with career)

**Resolved 20-prefix collision** (was `20 Goals/` AND `20 Personal/` at top level):
- `20 Personal/22 Health/` → `30 Personal/Health/`
- `20 Personal/` → `30 Personal/`

**Dropped redundant numeric prefixes inside subfolders:**
- `10 Work/11 Projects/` → `10 Work/Projects/`
- `10 Work/14 People/` → `10 Work/People/`
- `80 System/81 Templates/` → `80 System/Templates/`
- `80 System/82 Dashboards/` → `80 System/Dashboards/`
- `80 System/85 Sessions/` → `80 System/Sessions/`

**Grouped 3 setup guides under `80 System/Guides/`:**
- `Plugin Setup Guide.md`, `Git Sync Guide.md`, `Health Sync Setup.md` — moved from `80 System/` root into `80 System/Guides/`

**Rewrote vault `CLAUDE.md`** to reflect the new structure (the previous version was stale — referenced `20 Personal/21 Goals/`, `27 Learning/` (didn't exist), and obsolete number ranges).

### Leto repo updates (path references in tracked files)

Substituted via `sed -i`:
- `80 System/85 Sessions/` → `80 System/Sessions/` in 9 files: INDEX.md, CLAUDE.md, conventions/frontmatter.md, skills/leto.md, schedulers/{daily-brief,weekly-review,monthly-sweep,notion-alignment,granola-intake}.md
- `80 System/82 Dashboards/` → `80 System/Dashboards/` in 3 files: tiers/tier-2-scheduled.md, schedulers/daily-brief.md, CHANGELOG.md (current entry)
- `80 System/Career Profile.md` → `20 Goals/Career/Career Profile.md` in BOOTSTRAP.md, INDEX.md
- Cleaned stale "political-pattern guard" + "AI-native never AI-first" leftovers in scheduler-spec metadata

### Final vault structure

```
00 Inbox/{Drafts,Sources/granola/}
10 Work/{Projects, People}
20 Goals/{Vision.md, Yearly, Quarterly, Career, Reviews}
30 Personal/Health
80 System/{Templates, Dashboards, Sessions, Guides, Me.md, reader-context.md, Bootstrap Decisions.md, Standing Approvals.md}
Journal/{Daily, Weekly}
_claude/TODO.md
```

### What was deferred
- Templates pruning — kept all 13 templates as-is. Vladimir didn't flag specific ones as unused. Address separately if needed.
- Manual-daily-note habit — kept the folder + template; daily notes are now primarily Leto auto-output (Vladimir's own choice: "keep as-is").

### Risks accepted
- Wikilinks: Obsidian's wikilinks are by file basename, so most survive moves. Explicit Markdown links by path may break — none found in audit, but watch for issues when opening Obsidian next.
- Cowork's existing daily/weekly briefings reference paths in Vladimir's external Cowork prompts — not in the Leto repo. If those write to the old `80 System/82 Dashboards/` etc., they'll create the path back. Cowork retirement at Phase 3 entry resolves this.

---

## [Bootstrap voice round + cleanups] — 2026-05-04

Phase 3 prereq landed: voice calibration ground-truth. Plus two cleanups: `/blake` inline-to-thin-wrapper extraction and template prune.

### Voice round
- Subagent mined 23 Granola extracts + Slack `from:Vladimir` last 30 days → ~50 verbatim quotes, 10 voice patterns, 8 micro-signals.
- Vladimir corrected Pattern 3: "Russian for Russian-speakers" (recipient language), not "for peers" (relationship type).
- Second subagent filled 3 thin-corpus gaps (HR-shaped via Ana Pajuelo + Sophia Tessum + Anastasia Knyazeva; RU formal upward via DMs with Dima Kushnikov + `#rnd_ops` channel `C09KU6JSC22`; pushback via Kate Vekova + broader scan) → ~30 more verbatim quotes including the Valery Kashentsev calibrated-pushback masterclass and the 2025-01-29 Ira escalation.
- **Generated `~/Obsidian Vault/Vladimir's Vault/80 System/Voice Signature.md` v1** (~280 lines): 13 voice principles + by-audience playbook for 8 audience types + ~80 verbatim quotes + don't-say list + confidence map + calibration notes.
- `reader-context.md` references it ("Voice calibration for any drafting: load 80 System/Voice Signature.md").
- `tier-3-drafts.md` flags it as the calibration ground-truth (alongside `vladimir-tov` skill) before any Phase 3 draft.
- `Bootstrap Decisions.md` extended with voice round log.
- TODO closed: bootstrap voice round. New TODO: re-mine corpus in 90 days (~2026-08-04).

### /blake extraction
- `~/Projects/Agents/personas/blake-samic.md` created (verbatim copy of inline persona).
- `~/.claude/skills/blake/SKILL.md` rewritten as 3-step shim (matches the other 9).
- `conventions/persona-shim.md` updated — `/blake` no longer special-cased.
- All 10 persona skills now uniform.
- TODO closed: extract /blake inline.

### Template prune
- 13 → 8 templates in `80 System/Templates/`. Dropped: Health Log, Book, Decision, Meeting Note, Finance Review.
- Kept: Daily Note, Weekly Review, Project, Person, OKR, Morning Routine, One-on-One, Idea.

### Confidence map locked
- High: Russian peers, English peers/vendors, Russian formal upward (Dima), HR-shaped RU, Pushback (RU)
- Medium: HR-shaped EN (Sophia, mostly 2024 logistics)
- Low: Public/LinkedIn (1 sample), English pushback (sparse)
- Uncalibrated (flag any draft): Personal/family, Formal external email, Crisis comms

### Phase 3 readiness check
- ✅ Voice calibration ground-truth (Voice Signature.md)
- ✅ vladimir-tov skill (Anthropic-managed)
- ✅ Standing Approvals registry (SA-001 set the pattern)
- ✅ Reaction tracking infrastructure (Brief Reactions dashboard)
- ⏳ 2-week Tier 2 → Tier 3 gate (running through ~May 18)
- ⏳ Phase 3 deferred decisions (approval surface, channel allow-list, persona routing) — locked at Phase 3 entry

---

## [Pre-Leto] — 2026-04-15

Inherited from Vladimir's existing infrastructure (not part of this repo, but referenced):

- `~/Projects/Agents/` — 10 persona skills + `BEST_PRACTICES.md` (17 sections).
- `~/Obsidian Vault/Vladimir's Vault/` — PARA-shaped vault, `Me.md`, dashboards, templates.
- `~/.claude/projects/-Users-vladimir-mashkovtsev/memory/` — Claude Code memory across user/feedback/project/reference types.
- MCP connectors: Notion, Slack, Linear, Granola, Gmail, Calendar, YouTrack.
