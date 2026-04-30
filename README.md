# Leto

Vladimir Mashkovtsev's personal AI assistant — connective tissue over Obsidian vault, Claude Code memory, persona team, and MCP connectors. Holds full context of work and personality. Acts only when asked, drafts on Vladimir's behalf with approval, never autonomously.

Inspired by [Dima Kushnikov's obsidian-seed](https://github.com/dkushnikov/obsidian-seed) and [mnemon](https://github.com/dkushnikov/mnemon). Adapted to Vladimir's context: existing infrastructure, work-artifact intake (Slack/Linear/Granola), graduated reactive→proactive ladder.

## Status

**Phase 1 (Foundation)** — in progress.

- ✅ Repo scaffolding (this commit)
- ⏳ `/leto` skill registered
- ⏳ Persona shim across 10 skills
- ⏳ Bootstrap interview (`reader-context.md` generation)
- ⏳ Vault session-log dir + `_claude/TODO.md`

## Quick map

| What | Where |
|---|---|
| The compass | `CLAUDE.md` |
| Artifact map | `INDEX.md` |
| Bootstrap script | `BOOTSTRAP.md` |
| Stance & principles | `PHILOSOPHY.md` |
| Per-tier policy | `tiers/tier-{0..4}-*.md` |
| Conventions (shared) | `conventions/*.md` |
| Skill definition | `skills/leto.md` |
| Roadmap milestones | `CHANGELOG.md` |

## How to use

- `/leto` — open a Leto session.
- `/leto bootstrap` — one-time interview to generate reader-context.md.
- `/leto today` — on-demand brief.
- `/leto capture <thing>` — manually capture a source (Phase 1: stub; Phase 3: full).
- Persona skills (`/pm`, `/cto`, `/designer`, `/engineer`, `/qa`, `/security`, `/growth`, `/analytics`, `/blake`, `/product-ops`) load reader-context.md automatically once Phase 1 step 10 ships.

## Roadmap

| Phase | Tier | Adds | Status |
|---|---|---|---|
| 1 | 0 → 1 | Identity layer, persona shim, bootstrap, session logs, TODO ladder | In progress |
| 2 | 2 | Daily brief, weekly review, monthly sweep (scheduled) | Roadmap |
| 3 | 3 | Approval-gated drafts (Slack-on-behalf) | Roadmap |
| 4 | 4 | Standing approvals (narrow pre-auth patterns) | Roadmap |

Each phase requires explicit promotion. No automatic graduation.

## Anti-fragmentation

Leto is a dedicated repo, but artifacts live in their canonical homes — vault for data, memory for working patterns, Agents repo for personas. This repo holds orchestration code, conventions, schedulers, and the artifact index. See `INDEX.md` for the single map.
