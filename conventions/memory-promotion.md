# Memory → vault promotion rule

When does a stable pattern in `~/.claude/projects/-Users-vladimir-mashkovtsev/memory/` graduate to a permanent vault note in `80 System/`?

## Rule (locked at Phase 2 entry, 2026-05-01)

**Time-based: 90-day stable.** A memory file that hasn't been edited in ≥ 90 days is a candidate for vault promotion. Leto auto-proposes promotion at the next bootstrap refresh; Vladimir confirms or skips.

## Why this rule (not the alternatives)

- **Vladimir-flagged** would require him to remember to flag — friction that famine days will kill. Skipped.
- **Reference-count-based** would require session-log instrumentation we don't have at Phase 2. Could revisit at Phase 3+.
- **Time-based** is automatic, has a clear signal (90 days untouched = stable enough to be permanent), and lands at the bootstrap refresh which already exists as a 90-day cadence.

## What the rule means in practice

At every `/leto bootstrap` run (Phase 1 set this for 90-day cadence), Leto:

1. List all files in `~/.claude/projects/-Users-vladimir-mashkovtsev/memory/`.
2. For each file, check `git log --format="%at" -1 -- <file>` (or `stat -c "%Y" <file>` if not in git) — get the last edit timestamp.
3. Filter for files with last-edit ≥ 90 days ago.
4. For each candidate, propose:
   - **Promote**: move content into a vault note at `~/Obsidian Vault/Vladimir's Vault/80 System/<slug>.md` with appropriate frontmatter (`type:`, `origin: human` if Vladimir-authored, `origin: claude` if Leto-curated, `migrated-from: memory/<file>`).
   - **Keep in memory**: file is mutable working pattern, not permanent fact.
   - **Archive**: pattern is no longer relevant.

5. Vladimir picks per file. Promoted files are removed from memory and replaced with a stub pointer `# Migrated to <vault path>` (so MEMORY.md index stays valid).

## What does NOT auto-promote

- Files newer than 90 days (might still be evolving).
- Files Vladimir explicitly tagged `type: working-pattern` in their frontmatter (those stay in memory by design).
- Anything in `~/.claude/projects/-Users-vladimir-mashkovtsev-Projects-<project>/memory/` — those are project-scoped, not personal-context.

## Frontmatter schema for promoted files

```yaml
---
type: <category — e.g., user-context, feedback, project>
created: <original creation date if known>
updated: <date of promotion>
origin: <human | claude>
migrated-from: memory/<original-filename>
migration-date: <YYYY-MM-DD>
---
```

## Failure mode

If a file in memory references files in the vault (e.g., wikilinks `[[...]]`), promotion shouldn't break those references. The promotion procedure preserves the original filename slug in the migrated path when possible, e.g.:

- `memory/user_role.md` → `80 System/User Role.md` (or stays where Vladimir prefers).

If Vladimir wants a different filename, he edits during the promotion-proposal step.

## Reversibility

If a promotion turns out to have been premature (the file becomes mutable again):

- Demote back to memory: `git mv 80 System/<file>.md ~/.claude/projects/-Users-vladimir-mashkovtsev/memory/<file>.md`
- Restore the MEMORY.md index entry.
- Reset frontmatter to remove `migrated-from`.

This is rare but not impossible. Document any demotions in `Bootstrap Decisions.md` so future bootstrap rounds know.
