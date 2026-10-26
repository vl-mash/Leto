# Leto — INDEX (v2)

The single map. **Every artifact has exactly one home.** When something moves, this file updates first. v2 since 2026-10-26; PRD at `docs/PRD.md`.

## Identity & context

| Artifact | Path | Owner | Read by |
|---|---|---|---|
| Identity narrative | `~/Obsidian Vault/Vladimir's Vault/40 System/Me.md` | Vladimir (never edited by Claude) | `/leto` for deep context |
| **Shared context** (operational identity) | `~/Projects/Leto/context/context.md`, imported by the global `~/.claude/CLAUDE.md` via `@~/Projects/Leto/context/context.md`. Work-safe: org facts, Q4 KRs → RND projects, project folders | Leto (`/leto bootstrap` refreshes) | Every session, every project, all personas, Granola intake |
| ~~reader-context.md~~ | Archived to `40 System/Archive/reader-context.archived-2026-10-26.md` (v1, Q3 horizon) | — | Nothing |
| Career profile | `~/Obsidian Vault/Vladimir's Vault/20 Work/Goals/Career/Career Profile.md` | Vladimir | Career work |
| Q4 priorities | **RND Linear initiatives** (KR 1.1–2.2, set Oct 16–19). Mirrored in `context/context.md`. The Career-folder draft KRs (Sep 30) are superseded | Teo / Vladimir | Today's 3 ranking |

## Memory

| Artifact | Path | Read by |
|---|---|---|
| Leto memory: people, politics, feedback, projects | `~/.claude/projects/-Users-vladimir-mashkovtsev-Projects-Leto/memory/` (index `MEMORY.md`) | `/leto`; the **only** home for people and politics facts. Other projects read it, they don't copy it |
| Per-project memory | `~/.claude/projects/-Users-vladimir-mashkovtsev-Projects-<project>/memory/` | That project's sessions |
| Memory → Obsidian sync | `~/.claude/scripts/sync_memory_to_obsidian.py` (PostToolUse hook) | Keeps vault People pages current |

## Tasks

| What | Where |
|---|---|
| All work | **Linear RND team** (`24fd43e6-dc8d-443d-a8a3-026b85733033`). Leto writes only Triage issues (capture) and in-session status changes and receipt comments |
| Leto's own work | This repo: `docs/PRD.md`, commits |
| Private items (career, comp) | `~/Projects/Career/` + memory, never Linear |
| ~~VM team~~ | Gone from Linear (found 2026-10-26) |

## Vault

| Artifact | Path | Notes |
|---|---|---|
| Meeting sources and extracts | `00 Inbox/Sources/granola/` | Written by Granola intake; immutable source, regenerable extract |
| People pages | `20 Work/People/` | Synced from memory |
| Session logs | `40 System/Sessions/YYYY/` | Only Granola intake still writes here. No interactive session-log ceremony in v2; scheduled briefs log to `.local-data/` JSONL. Clean-up is Phase 6 |
| Daily notes | `40 System/Journal/Daily/` | v1 preflight auto-created empty stubs; that stopped with preflight's retirement |
| Standing Approvals | `40 System/Standing Approvals.md` | Retired with v1. The file stays in the vault as history; nothing reads it |

## Leto repo (this repo)

| Artifact | Path | Purpose |
|---|---|---|
| Compass | `CLAUDE.md` | Who Leto is, modes, design rules, hard rules |
| This index | `INDEX.md` | The map |
| PRD | `docs/PRD.md` | v2 problem, outcome, phases, open questions |
| Leto skill | `skills/leto.md` (wrapper `~/.claude/skills/leto/SKILL.md`) | `/leto` modes |
| Doubt-driven review | `skills/doubt-driven.md` | In-flight adversarial review for high-stakes calls |
| Hayt council | `skills/hayt.md` (wrapper `~/.claude/skills/hayt/SKILL.md`) | 3-reviewer deliberation |
| Schedulers | `schedulers/*.md` | Pointer pattern: the registered task reads the doc at run time. Live: `granola-intake.md` |
| Conventions | `conventions/{frontmatter,persona-shim,anti-rationalization}.md` | Applied to generated artifacts and personas |
| Secrets helper | `hooks/leto_secrets.py` | Resolve and live-validate credentials (`--check`, `--names`) |
| References | `references/` (BEST_PRACTICES, PHILOSOPHY, ADR-001..003, CHANGELOG) | History and orchestration laws |
| Bootstrap | `BOOTSTRAP.md` | `/leto bootstrap` interview |
| v1 archive | `archive/v1/` | Retired 2026-10-26: hooks, schedulers, tiers, governance, eval, conventions, Slack listener, launchd plist. History, not live code |
| Older archive | `archive/*.archived-*` | Commitments register (2026-08-03), 9-section daily brief (2026-08-10) |

## Scheduled tasks (`mcp__scheduled-tasks`)

| Task | Status |
|---|---|
| `leto-granola-intake` | **Enabled**, 17:15 Mon–Fri, pointer → `schedulers/granola-intake.md` |
| `leto-daily-brief`, `leto-personal-backlog-eod`, `leto-weekly-review` | Disabled 2026-10-26 (v1). The daily brief v4 replaces them in Phase 2 |
| `linear-daily-digest`, `leto-weekly-collect` | Disabled earlier (2026-08 / 09) |
| `ops-sync-weekly-run` | Disabled; belongs to `~/Projects/ops-sync`, not Leto |
| `youtrack-daily-digest` | Not registered. Script `integrations/youtrack/digest.sh` kept until the YouTrack sunset (RND-458) |

## Integrations

| Integration | Path | Purpose |
|---|---|---|
| Linear | `integrations/linear/linear-graphql.sh` | GraphQL wrapper (scripts). Interactive work uses the Linear MCP |
| Slack (outbound) | `integrations/slack/leto-bot-post.sh` + `manifest.yaml` | Bot DMs to Vladimir. Listener retired |
| YouTrack | `integrations/youtrack/digest.sh` | Dormant |
| Telegram | `integrations/telegram/` | Voice corpus mining; data in `.local-data/telegram/` (gitignored) |
| Shared env loader | `integrations/lib/load-env.sh` | Bash-side secret resolution |

## Secrets

All credentials are in `~/.config/leto/leto.env` (mode 600), outside every git tree. Template and provenance: `.env.example`. Validate with `python3 hooks/leto_secrets.py --check`.

## Personas & skills

| Artifact | Path | Invoked by |
|---|---|---|
| Active personas | `personas/product/pm-shreyas.md`, `personas/ops/blake-samic.md`, `personas/engineering/{cto-martin,engineer-carmack}.md` | `/pm`, `/blake`, `/cto`, `/engineer` |
| Archived personas | `personas/archive/` | `/designer`, `/qa`, `/security`, `/growth`, `/analytics`, `/product-ops` (still loadable) |
| Lite personas | `personas/lite/` | `ask --lite` |
| Persona wrappers | `~/.claude/skills/<name>/SKILL.md` | Rely on the globally imported `context/context.md`, then load the persona |
| `vault-recall` agent | `agents/vault-recall.md` → symlinked into `~/.claude/agents/` | `/leto recall`, any skill |
| `blake` agent | `~/.claude/agents/blake.md` (not Leto-owned) | Agent tool |
| CLI | `agents/ask.sh` (alias `ask` in `~/.zshrc`), `agents/<role>.sh`, `agents/orchestrate.sh` | Terminal |

## Anti-fragmentation invariants

1. **No file lives in two places.** A duplicate here is a bug: fix the index, fix the duplicate.
2. **People and politics facts live only in Leto memory.** Repos and project CLAUDE.md files point to it; they don't copy it.
3. **Memory does not move.** `~/.claude/projects/.../memory/` stays where Claude Code expects it.
4. **Personas do not embed identity.** Vladimir-shaping happens at the wrapper level.
5. **The vault holds knowledge, not task state.** Tasks are Linear RND.
