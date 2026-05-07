# Convention — Linear is the command center for the Leto project

**As of 2026-05-07**, Linear is the source-of-truth for tracking Leto-project work. The vault `40 System/Claude/TODO.md` is no longer authoritative for Leto items — it's a historical receipt + a pointer to Linear.

## Where Leto work lives

| Surface | Role |
|---|---|
| **Linear: VM team / Leto project** ([URL](https://linear.app/manychat/project/leto-7001e5d3a829)) | Authoritative backlog, status, milestones, history |
| `~/Projects/Leto/CHANGELOG.md` | Long-form prose receipts of what shipped and why |
| `~/Obsidian Vault/Vladimir's Vault/40 System/Claude/TODO.md` | Pointer to Linear for Leto items; still usable for non-Leto vault commitments |
| Slack DM thread (per-routine) | Operational reactions on Tier 2 outputs (separate from work tracking) |

Issue-id format: `VM-###`. Always cite by ID + URL when referencing in conversation, vault notes, or commit messages — e.g., `[VM-8](https://linear.app/manychat/issue/VM-8)`.

## Auto-update behavior (the contract)

When Claude (or Leto) does work that maps to a Leto-project item, the **Linear ticket gets updated as part of the work**, not after. Concrete patterns:

### State transitions

| Trigger | Transition | Tool |
|---|---|---|
| Vladimir says "let's start on VM-X" or work clearly begins | Backlog/Todo → **In Progress** | `save_issue(id="VM-X", state="In Progress")` |
| Work has shippable interim artifact ready for review | In Progress → **In Review** | `save_issue(id="VM-X", state="In Review")` |
| Work shipped (committed / merged / deployed / vault-written) | → **Done** | `save_issue(id="VM-X", state="Done")` + comment with the receipts |
| Vladimir says "drop it" / "park it" | → **Canceled** | `save_issue(id="VM-X", state="Canceled")` |

### Comments document progress

Add a comment via `save_comment(issue="VM-X", body=...)` when:

- Starting non-trivial work (link to plan / approach)
- Hitting a blocker (what's blocked, what's needed, who decides)
- Shipping (commit hashes, file paths touched, what was decided)
- Switching direction (why)

Comment style: tight, factual, citation-heavy. No filler ("started working on this"). Same voice rules as everything else — direct, casual-but-specific, cite paths.

### New work emerges in conversation

When a commitment, task, or idea surfaces in chat that isn't already a VM ticket:

1. **Don't silently add to vault TODO** — that's the old pattern, not the new one.
2. Propose creating a Linear ticket: "This is a [phase-3 / slack-bot / etc.] item — create as VM-### in [milestone X / no milestone]?"
3. With Vladimir's "yes" (or auto-yes for routine items), call `save_issue(...)`. Capture the ID.
4. Mention the ID in the same response so Vladimir can find it.

### Closing dual-tracked items

The 7 historical TODOs in vault that have VM-### counterparts (VM-1 through VM-7): when their Linear ticket goes Done, the vault TODO line is already gone — vault TODO no longer carries them. Don't re-add.

### What if Linear is unreachable?

Network failure / Linear API outage during a write:
- Don't pretend it succeeded. Surface the failure: "Linear write to VM-X failed — work is shipped to vault/repo, but ticket state didn't update. Re-try when you tell me to."
- Capture the intended update in the session log so the next /leto can retry.

## Mapping intent to Linear field

| Concept | Linear field | Notes |
|---|---|---|
| Phase / lifecycle | label `phase-2` / `phase-3` / `phase-4` | Multiple labels OK |
| Vehicle (Slack bot, voice, integration, etc.) | label `slack-bot` / `voice` / `bootstrap` / `integration` | Topical |
| Milestone (M1..M6) | `projectMilestone` | One per issue |
| Parent/child | `parentId` | Use for breakdowns; child takes parent's milestone |
| Owner | `assignee` | Always Vladimir for Leto-project items |
| Priority | `priority` 0..4 | 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low |
| Due date | `dueDate` | Only when there's a real deadline |
| Source citation | first line of description | "Source: `40 System/Claude/TODO.md` (since: ...)" or "Source: Vladimir DM 2026-05-07" |

## What Linear does NOT replace

- **CHANGELOG.md** — narrative receipts, decision rationale, full context. Linear's Done issues are the structured form; CHANGELOG is the prose form. Both are intentional.
- **Session logs** — every /leto session writes one to `40 System/Sessions/<year>/`. They link to VM-### IDs but exist independently.
- **Memory** — `user_*.md`, `feedback_*.md`, `project_*.md` stay at `~/.claude/projects/-Users-vladimir-mashkovtsev-Projects-Leto/memory/`. Linear is not memory.
- **Vault TODO.md** — still usable for non-Leto vault commitments (personal life, vault hygiene, etc. that aren't Leto-project work).

## When this convention can be ignored

- One-off chat-only exchanges that produce no shipped artifact
- Trivial fixes that take <2 minutes and are clearly inside an already-In-Progress ticket
- Operational reactions on Tier 2 output (Slack thread reactions on daily-brief — those go in the Slack thread, not into Linear)

When in doubt, lean toward updating. Over-update beats silent drift.
