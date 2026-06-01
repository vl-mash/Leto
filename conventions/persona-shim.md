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

1. Read `~/Obsidian Vault/Vladimir's Vault/40 System/reader-context.md` first. Treat its directives as binding (voice, hard don'ts, language preferences, what Vladimir wants from this persona).
2. Read and fully embody the persona at `~/Projects/Leto/personas/<persona-file>.md`. Apply its frameworks, heuristics, and anti-patterns.
3. Then process the user's question.

If reader-context.md does not yet exist, proceed with persona-only and note at the end of your response: "reader-context.md not found — Leto bootstrap pending."
```

## Why this order

Cache-friendly per BEST_PRACTICES Law 6: static identity (reader-context.md, ~60 lines, rarely changes) → static role (persona file, never changes) → dynamic user request (changes every turn). Anthropic prompt cache stays hot across the first two blocks; only the tail busts.

## Why a graceful fallback

The shim must work even before the bootstrap interview has run. Phase 1 step 1–7 ships infrastructure; step 8 is the interview that generates reader-context.md. Persona shims updated in step 10 must not break the persona skills in the gap.

## Persona file mapping (updated 2026-06-01 — bucketed structure)

Persona files live in `~/Projects/Leto/personas/` organized by bucket. Active personas in named buckets; unused in `archive/` (still loadable).

| Skill | Persona file | Status |
|---|---|---|
| `pm` | `~/Projects/Leto/personas/product/pm-shreyas.md` | Active |
| `blake` | `~/Projects/Leto/personas/ops/blake-samic.md` | Active |
| `cto` | `~/Projects/Leto/personas/engineering/cto-martin.md` | Active |
| `engineer` | `~/Projects/Leto/personas/engineering/engineer-carmack.md` | Active |
| `designer` | `~/Projects/Leto/personas/archive/designer-julie.md` | Archived |
| `qa` | `~/Projects/Leto/personas/archive/qa-elisabeth.md` | Archived |
| `security` | `~/Projects/Leto/personas/archive/security-troy.md` | Archived |
| `growth` | `~/Projects/Leto/personas/archive/growth-andrew.md` | Archived |
| `analytics` | `~/Projects/Leto/personas/archive/analytics-cassie.md` | Archived |
| `product-ops` | `~/Projects/Leto/personas/archive/product-ops.md` | Archived |

## The thin-wrapper shim (universal — all 10)

Replace the SKILL.md body with this 3-step block:

```markdown
Load context in this order — do not skip steps:

1. Read `~/Obsidian Vault/Vladimir's Vault/40 System/reader-context.md` first. Treat its directives as binding (voice, hard don'ts, language preferences, what Vladimir wants from this persona).
2. Load and fully embody the persona at `~/Projects/Leto/personas/<persona-file>.md`. Read the entire file and act as that <role-label> for the rest of this session. Apply its frameworks, heuristics, and anti-patterns.
3. Then process the user's question.

If `reader-context.md` does not exist, proceed with persona-only and note at the end of your response: "reader-context.md not found — Leto bootstrap pending."
```

## What this does NOT do

- It does not modify the persona files themselves. The persona definitions stay role-shaped, not Vladimir-shaped — preserving the option to publish a scrubbed version of `personas/` separately if desired.
- It does not load Me.md (too long for every invocation; reader-context.md is the distilled operational form).
- It does not load MEMORY.md (working patterns; loaded by `/leto`, not by personas).
