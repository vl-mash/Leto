# Leto — Bootstrap interview script

The one-time session that generates `~/Obsidian Vault/Vladimir's Vault/40 System/reader-context.md`. Invoked via `/leto bootstrap`.

**Time-box:** 45 minutes. Vladimir chose a single sitting over chunked. Respect it — if you're at minute 40 with three sections to go, ship a v1 and queue a "bootstrap-v2" TODO with a `since:` marker for the gaps.

**Style:** ground-truth-first, then targeted questions. Vladimir already has rich context (Me.md, memory files, vault structure). You are *reconciling* it, not extracting it from a blank slate. Lead with what you read; ask only when you genuinely don't know.

---

## Phase 1 — Read everything (5 min)

Before asking anything, read:

1. `~/Obsidian Vault/Vladimir's Vault/40 System/Me.md` — canonical narrative.
2. `~/Obsidian Vault/Vladimir's Vault/20 Work/Goals/Career/Career Profile.md` — career trajectory, scope, public positioning.
3. `~/Obsidian Vault/Vladimir's Vault/CLAUDE.md` — vault structure and conventions.
4. `~/.claude/projects/-Users-vo-Projects-Agents/memory/MEMORY.md` — index.
5. Every `~/.claude/projects/-Users-vo-Projects-Agents/memory/user_*.md` — who Vladimir is.
6. Every `~/.claude/projects/-Users-vo-Projects-Agents/memory/feedback_*.md` — what he's learned about himself and his environment.
7. Every `~/.claude/projects/-Users-vo-Projects-Agents/memory/project_*.md` — active projects.
8. `~/.claude/CLAUDE.md` — the skill stack and orchestration principles.
9. List the personas at `~/Projects/Leto/personas/` (ls — don't read full contents, just know what's available).

Do not ask questions during this phase. Just read.

---

## Phase 2 — Gap report (10 min)

Produce a structured report. Surface to Vladimir, do NOT auto-write anything yet.

Format:

```markdown
## What I learned about you

### Identity (from Me.md)
- [3-5 bullets summarizing values, decision style, energy pattern, peak hours, etc.]

### Career & role (from Career Profile.md + memory)
- [3-5 bullets — current role, trajectory, scope, key receipts, target direction]

### Patterns I should respect (from feedback_*.md)
- [bullets — comms style, political pattern, packaging triggers, etc.]

### Active projects (from project_*.md)
- [bulleted list with one-line status per project]

## Gaps I noticed

1. **[Gap or contradiction 1]** — [explain what's missing or conflicting]
2. **[Gap 2]** — ...
3. **[Gap 3]** — ...
[max 10 items]

## What I plan to ask

To generate reader-context.md, I need to know:
1. [Question 1 — pointed]
2. [Question 2 — pointed]
[max 10 questions]
```

Keep gaps to genuine ones. Do NOT ask Vladimir to re-confirm things Me.md already says. Do not ask about his energy pattern (Me.md is explicit). Do not ask about his values (Me.md is explicit).

**Genuine gaps that ARE worth asking** (these are illustrative, surface real ones from the read):

- Hard don'ts list: Me.md describes patterns but doesn't give a "Leto must never do X to me" list. Ask.
- Persona behavior preferences: when `/pm` engages, does Vladimir want it to push back hard, present options, or commit? Probably differs by persona.
- RU/EN switching: is there a rule (e.g. "RU for personal, EN for work") or feel-based?
- Domains of interest beyond work: Me.md mentions some, but the AI-extract perspective (mnemon's question "what do you want from extracts on these topics") may not be covered.
- Peak-window behavior: never interrupt 10–12 with anything? Or only auto-send during it? Or both?
- Goals horizon: 90-day vs 1-year vs 3-year — does reader-context.md surface near-term goals only?

---

## Phase 3 — Ask the questions (15 min)

Ask the questions you flagged in Phase 2. Use AskUserQuestion if 2–4 distinct choices each; use plain conversational asks for free-text answers.

**Cap:** 10 questions total. If you go over, you're either repeating Me.md or asking too much.

For each answer, restate briefly to confirm understanding before moving on. ("Got it — peak window 10–12 is sacred. I'll never schedule briefs or reminders during that window. Confirmed?")

---

## Phase 4 — Draft reader-context.md (10 min)

Generate `~/Obsidian Vault/Vladimir's Vault/40 System/reader-context.md` with this structure (≤ 60 lines total — strict):

```markdown
---
type: reader-context
created: <today>
updated: <today>
origin: claude
generated-from:
  - 80 System/Me.md
  - 20 Goals/Career/Career Profile.md
  - .claude/projects/-Users-vo-Projects-Agents/memory/MEMORY.md
  - bootstrap interview <today>
version: 1
---

# Reader Context — Vladimir Mashkovtsev

> Operational identity for AI loading. The narrative lives in `Me.md`; this file is the distilled, hot-path version loaded on every session and persona invocation.

## Who I Am

[2–3 sentences. Role, trajectory, what makes Vladimir Vladimir. Reference Me.md for depth.]

## Domains of Interest

- **Work:** [tag list — product ops, AI-native operations, Manychat, etc.]
- **Career:** [tag list]
- **Personal:** [tag list — health, learning, family, etc.]
- **Inner-work:** [tag list — values, decision style]

## Current Goals (90-day horizon)

[3–5 bulleted goals from his current Q-OKRs and career repositioning. Pull from project_career_repositioning.md and OKR data if surfaced.]

## What I Want From Personas

When you (a persona skill, or me as Leto) engage with Vladimir's request:

- [3–5 directives — e.g. "Lead with the recommendation, then receipts; don't open with caveats."]
- [Voice rules — direct, structured, no pre-addressing objections, casual-but-specific.]
- [Decision-style match — he tests and iterates, so propose experiments over architectures when appropriate.]
- [Energy-pattern awareness — feast-or-famine; on famine days, low-friction over thorough.]

## Hard Don'ts

Things to never do without explicit asking:

- Anything political — never coach on coalitions, upward reviews, skip-level grievances. Cardinal rule from `feedback_political_pattern.md`.
- Anything to/about Dima Kushnikov, Lu Borko, Anna Bokareva, Sophia Tessum, Nastya Shchogoleva — surface only, never draft.
- Don't pre-address objections in writing. Lead with the answer.
- Don't soften. Vladimir respects directness.
- Don't break the 10–12 peak window with reminders or notifications (Phase 2+).
- [Other hard don'ts surfaced in interview]

## Language

- Default: English.
- RU/EN code-switching allowed in conversation; if Vladimir writes RU, reply RU.
- Persona output: English unless context dictates.
```

Count lines. If over 60, compress. The goal is cache-friendly density.

---

## Phase 5 — Log decisions (5 min)

Write `~/Obsidian Vault/Vladimir's Vault/40 System/Bootstrap Decisions.md`:

```markdown
---
type: bootstrap-decisions
created: <today>
origin: claude
generated-from: leto bootstrap session <today>
---

# Bootstrap Decisions

## Questions asked and answers

1. **[Q1]** — [A1]
2. **[Q2]** — [A2]
...

## Gaps deferred

[Items from gap report that we did NOT cover this session, with `since:` markers and a TODO entry.]

## Reader Context v1

Generated at `80 System/reader-context.md` from this session.

## Next bootstrap

Bootstrap should be re-run when:
- Me.md is significantly updated.
- Career trajectory changes (new role, new company, new direction).
- Reader Context starts feeling stale (Vladimir flags drift).
- At least once per quarter for a refresh.
```

Then add a TODO to `_claude/TODO.md`:

```markdown
- [ ] Re-run /leto bootstrap to refresh reader-context.md <!-- since: <today + 90 days> -->
```

---

## Phase 6 — Confirm with Vladimir

Show Vladimir what you generated:

```
Bootstrap complete. I generated:

- ~/Obsidian Vault/Vladimir's Vault/40 System/reader-context.md (v1, 58 lines)
- ~/Obsidian Vault/Vladimir's Vault/40 System/Bootstrap Decisions.md
- 1 TODO added to _claude/TODO.md (re-bootstrap reminder for 90 days out)

Want me to walk through reader-context.md before we commit, or are we good?
```

Wait for his confirmation before exiting the session.

---

## Failure modes

- **Vladimir gets pulled away mid-interview**: write what you have so far to `Bootstrap Decisions.md` with status `incomplete`. Don't generate reader-context.md from a half-finished interview. Add a TODO to resume.
- **Gap report surfaces a contradiction in existing memory** (e.g. Me.md says one thing, `feedback_*.md` says another): surface to Vladimir explicitly. Don't reconcile silently.
- **Vladimir resists a question** ("don't want to think about that today"): skip and queue. Don't push.
- **Reader-context.md draft exceeds 60 lines**: compress. The cache-friendly contract is binding.
