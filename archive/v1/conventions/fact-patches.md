# Fact-patches convention (VM-75)

A **fact-patch proposal** is created whenever `leto-granola-intake` detects a direct
contradiction between a freshly captured meeting extract and a binding source
(`reader-context.md` or a `project_*.md` / `user_*.md` memory file).

Proposals are written to vault, read by `leto-daily-brief`, and surfaced in Slack for
one-tap approval. The actual edits are never auto-applied — approval is always required.

## File location

```
~/Obsidian Vault/Vladimir's Vault/00 Inbox/Drafts/fact-patches/
  <YYYY-MM-DD>-<meeting-slug>.md
```

One file per meeting run that produced contradictions. Multiple contradictions from the
same meeting go in the same file.

## File schema

```markdown
---
type: fact-patch-proposal
created: <ISO timestamp>
origin: claude
generated-by: leto-granola-intake
source-meeting: <granola-slug>
status: pending        # pending | applied | dismissed
---

# Fact-patch proposal — <YYYY-MM-DD> <Meeting Title>

## ⚠️ Contradictions detected

### 1. <Subject: e.g. "VAST deadline">
**Binding source:** `<relative vault path>` (updated <date>)
> "<exact quote or paraphrase from binding source — the stale claim>"

**New evidence:** `<relative vault path of extract>`
> "<exact quote or paraphrase from extract — the fresh claim>"

**Confidence:** high | medium
**Suggested patch:**
Replace: `<stale text>`
With: `<fresh text>`

---

### 2. <Next contradiction if any>
...

---

## Apply instructions

To apply patches: start a `/leto` session and say "apply fact-patches for <date>".
  Leto will: read this file, apply each patch to the binding source, mark status=applied.

To dismiss: in a `/leto` session, say "dismiss fact-patches for <date>".
  OR: manually edit `status: pending` → `status: dismissed` in this file's frontmatter.
```

## Contradiction check rules (for granola-intake Step 7d)

Only flag **clear, direct contradictions** — different values for the same fact about the
same subject. Do NOT flag:

- Additions (new information not in binding source) — just update memory, not a patch
- Clarifications (adds nuance to something accurate) — not a patch
- Ambiguous differences (could be read either way) — skip
- Minor wording differences — skip
- Things that changed long ago (binding source may already know) — skip if both plausible

Flag these categories:
- **Dates/deadlines:** binding says "June 9", extract says "June 22" for same milestone
- **Status changes:** binding says "In Progress", extract says "Done/Canceled/Paused"
- **Ownership:** binding says "Vladimir leads X", extract says "Nadia / someone else leads X"
- **People changes:** new manager, org-chart change not in binding source
- **Scope changes:** project dropped, merged, or significantly reshaped

Confidence levels:
- **high** — direct quote vs direct quote, same unambiguous subject, clearly different values
- **medium** — strong implication but requires one inference step
- **low** — skip (too uncertain to propose a patch)

## staleness check (for daily-brief)

`fact-freshen.py` checks `reader-context.md` frontmatter `updated:` date.
- > 7 days old → flag as stale, recommend `/leto bootstrap` re-run
- > 14 days old → flag more strongly (14-day ladder matches TODO escalation)

The `patches_pending` count tells daily-brief how many unresolved proposals exist.

## Patch apply flow (manual /leto session)

1. Vladimir says "apply fact-patches" (or reacts to a Slack message)
2. Leto reads each `pending` patch file
3. For each patch: shows old vs new, asks "apply this one? (yes/no/edit)"
4. Applies approved patches to binding sources (reader-context.md or memory files)
5. Marks `status: applied` in the patch file
6. Writes a session log
