# Persona shim — the 3-line skill wrapper template

Vladimir's persona skills (`/pm`, `/cto`, `/designer`, `/engineer`, `/qa`, `/security`, `/growth`, `/analytics`, `/blake`, `/product-ops`) are role-shaped but identity-blind by default. The shim adds **Vladimir-shaping** on top of role-shaping without touching the persona files themselves.

## The pattern

```markdown
---
name: <persona>
description: <unchanged from original>
user_invocable: true
---

Load context in this order — do not skip steps:

1. Read `~/Obsidian Vault/Vladimir's Vault/80 System/reader-context.md` first. Treat its directives as binding (voice, hard don'ts, language preferences, what Vladimir wants from this persona).
2. Read and fully embody the persona at `~/Projects/Agents/personas/<persona-file>.md`. Apply its frameworks, heuristics, and anti-patterns.
3. Then process the user's question.

If reader-context.md does not yet exist, proceed with persona-only and note at the end of your response: "reader-context.md not found — Leto bootstrap pending."
```

## Why this order

Cache-friendly per BEST_PRACTICES Law 6: static identity (reader-context.md, ~60 lines, rarely changes) → static role (persona file, never changes) → dynamic user request (changes every turn). Anthropic prompt cache stays hot across the first two blocks; only the tail busts.

## Why a graceful fallback

The shim must work even before the bootstrap interview has run. Phase 1 step 1–7 ships infrastructure; step 8 is the interview that generates reader-context.md. Persona shims updated in step 10 must not break the persona skills in the gap.

## Persona file mapping (verified 2026-04-30)

9 skills are thin wrappers that load a separate persona file:

| Skill | Persona file |
|---|---|
| `pm` | `~/Projects/Agents/personas/pm-shreyas.md` |
| `cto` | `~/Projects/Agents/personas/cto-martin.md` |
| `designer` | `~/Projects/Agents/personas/designer-julie.md` |
| `engineer` | `~/Projects/Agents/personas/engineer-carmack.md` |
| `qa` | `~/Projects/Agents/personas/qa-elisabeth.md` |
| `security` | `~/Projects/Agents/personas/security-troy.md` |
| `growth` | `~/Projects/Agents/personas/growth-andrew.md` |
| `analytics` | `~/Projects/Agents/personas/analytics-cassie.md` |
| `product-ops` | `~/Projects/Agents/personas/product-ops.md` |

**`/blake` is a special case** — its SKILL.md contains the full ~227-line persona inline rather than wrapping a separate file. For `/blake`, the shim is prepended at the top of the body content (after `# Head of Product Operations / Chief of Staff`) instead of replacing a thin-wrapper line. Future cleanup: extract Blake's persona to `~/Projects/Agents/personas/blake-samic.md` so all 10 follow the thin-wrapper pattern.

## The thin-wrapper shim (for the 9)

Replace the existing single line with this 3-step block:

```markdown
Load context in this order — do not skip steps:

1. Read `~/Obsidian Vault/Vladimir's Vault/80 System/reader-context.md` first. Treat its directives as binding (voice, hard don'ts, language preferences, what Vladimir wants from this persona).
2. Load and fully embody the persona at `~/Projects/Agents/personas/<persona-file>.md`. Read the entire file and act as that <role-label> for the rest of this session. Apply its frameworks, heuristics, and anti-patterns.
3. Then process the user's question.

If `reader-context.md` does not exist, proceed with persona-only and note at the end of your response: "reader-context.md not found — Leto bootstrap pending."
```

## The /blake shim (prepended)

For `/blake`, prepend this immediately after `# Head of Product Operations / Chief of Staff` and before `You are Blake Samic`:

```markdown
**Vladimir-shaping (read first):** Before applying the Blake Samic persona below, read `~/Obsidian Vault/Vladimir's Vault/80 System/reader-context.md` and treat its directives as binding (voice, hard don'ts, language preferences, what Vladimir wants from this persona). If the file is missing, proceed with persona-only and note at the end: "reader-context.md not found — Leto bootstrap pending."
```

## What this does NOT do

- It does not modify the persona files themselves. Other users / other environments running these personas get unmodified Shreyas / Carmack / etc.
- It does not load Me.md (too long for every invocation; reader-context.md is the distilled operational form).
- It does not load MEMORY.md (working patterns; loaded by `/leto`, not by personas).
