# Convention — Linear is the command center

**As of 2026-05-07**, Linear is the source-of-truth for Leto-project work. **As of 2026-08-03 ([ADR-002](../references/adr-002-linear-only-commitments.md)), Linear is the source-of-truth for _every_ commitment** — project work, R&D Ops work, interpersonal promises, personal follow-ups. There is no second store.

**The vault holds no task state.** `40 System/Claude/Commitments.md` and `TODO.md` are archived under `40 System/Archive/`. Don't write a checkbox to the vault and don't resurrect either file; if something is worth tracking, it's worth a Linear issue.

## Where work lives

| Surface | Role |
|---|---|
| **Linear: VM team** ([Leto project](https://linear.app/manychat/project/leto-7001e5d3a829)) | Authoritative for everything personal or private — Leto work, career, comp, HR-shaped counterparties, personal follow-ups |
| **Linear: RND team** | Authoritative for R&D Ops function work the team should see tracked |
| `~/Projects/Leto/CHANGELOG.md` | Long-form prose receipts of what shipped and why |
| Vault (`Sessions/`, `Sources/`, `Journal/`, memory) | Knowledge only — what happened, what it means. Never task state. |
| Slack DM thread (per-routine) | Operational reactions on Tier 2 outputs, and the EOD approve/skip loop |

Issue-id format: `VM-###` / `RND-###`. Always cite by ID + URL when referencing in conversation, vault notes, or commit messages — e.g., `[VM-8](https://linear.app/manychat/issue/VM-8)`.

## Which team (routing)

Absorbed from the retired commitments convention:

| Condition | Team |
|---|---|
| Personal interaction — career, private conversation, personal follow-up | `VM` |
| HR-shaped counterparty (Teo, Dima, Sophia, Ingrid, Nastya, …) | `VM` always |
| Team deliverable Teo / Anna would expect to see tracked | `RND` |
| Project not yet formally approved as R&D Ops work | `VM` until approved |

**Things others owe Vladimir are not tracked as tasks.** Record them in the meeting extract and the relevant memory file. If an inbound promise blocks Vladimir's own work, note it as context on *his* issue rather than opening one to track someone else. Never create a ticket assigned to another person on their behalf.

## Capture is propose-only

No automation creates a ticket silently.

- **`leto-personal-backlog-eod`** is the single automated write path: it matches the day's signals (Granola extracts, Slack `from:me`, vault + repo commits, session logs) against open VM issues and proposes state changes + new tickets in a Slack DM thread. Vladimir replies with the item IDs he wants; `/leto post-personal-backlog-eod <date>` applies them. (SA-002 still auto-applies high-confidence, non-HR items — the one standing exception.)
- **In a `/leto` session**, propose the ticket and create it on an explicit yes (see "New work emerges in conversation" below).
- **Granola intake** writes knowledge only — `source.md`, `extract.md`, memory. It does not create or update tickets.

## Escalation runs on Linear fields

- `dueDate` → the daily brief's NUDGE surfaces past-due / due-today / due-soon issues.
- `updatedAt` → the 7/14/21 staleness ladder (soft mention / direct question / propose disposition) that used to run on vault `since:` markers.

Set a due date when there's a real deadline; that's what makes the nudge fire.

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

1. **Never write it to the vault** — no checkbox, no register, no TODO file (ADR-002).
2. Propose creating a Linear ticket, naming the team: "This is a [phase-3 / R&D Ops / personal] item — create as VM-### / RND-### in [milestone X / no milestone]?"
3. With Vladimir's "yes" (or auto-yes for routine items), call `save_issue(...)`. Capture the ID.
4. Mention the ID in the same response so Vladimir can find it.

### No dual-tracking

There is nothing to reconcile any more: Linear state is the only state. If you find a vault file carrying task state, it's a leftover — archive it and cite ADR-002, don't sync it.

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
| Source citation | first line of description | "Source: `granola/2026-08-03-<slug>.extract.md`" or "Source: Vladimir DM 2026-08-03" — cite where the commitment came from |
| Counterparty | description body | Name the person a promise is to; there's no `to:`/`from:` field any more |

## What Linear does NOT replace

- **CHANGELOG.md** — narrative receipts, decision rationale, full context. Linear's Done issues are the structured form; CHANGELOG is the prose form. Both are intentional.
- **Session logs** — every /leto session writes one to `40 System/Sessions/<year>/`. They link to VM-### IDs but exist independently.
- **Memory** — `user_*.md`, `feedback_*.md`, `project_*.md` stay at `~/.claude/projects/-Users-vladimir-mashkovtsev-Projects-Leto/memory/`. Linear is not memory.
- **Granola extracts** — what was said in a meeting, including what others committed to. Knowledge, not task state.

## What no longer exists

`40 System/Claude/Commitments.md`, `40 System/Claude/TODO.md`, `hooks/commitments.py`, `conventions/commitments.md`, the `C-NNN` id space, the Slack `done C-NNN` reply grammar, and SA-003. All archived 2026-08-03 under [VM-138](https://linear.app/manychat/issue/VM-138). See [ADR-002](../references/adr-002-linear-only-commitments.md) for why.

## When this convention can be ignored

- One-off chat-only exchanges that produce no shipped artifact
- Trivial fixes that take <2 minutes and are clearly inside an already-In-Progress ticket
- Operational reactions on Tier 2 output (Slack thread reactions on daily-brief — those go in the Slack thread, not into Linear)

When in doubt, lean toward updating. Over-update beats silent drift.
