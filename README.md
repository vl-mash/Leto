# Leto — Personal AI Assistant Framework

A personal AI assistant built on top of [Claude Code](https://claude.ai/code) that holds full context of your work, routes to specialist personas, runs scheduled automations, and drafts on your behalf — with your approval.

**The core idea:** Claude is powerful but stateless. Every session starts from zero. Leto fixes that by giving Claude a persistent identity layer, a memory system, a team of specialist roles, and automated routines — all wired together into a single orchestration layer over your existing tools.

---

## What it does

**Holds context.** Instead of re-explaining who you are and what you're working on in every session, Leto reads a compact operational identity file (`reader-context.md`) that captures your role, communication style, priorities, and working preferences. Every specialist persona loads this automatically.

**Routes to specialists.** Rather than asking a generic Claude for product strategy and architecture decisions in the same conversation, you have named personas — each deeply calibrated to a specific role and framework set. `/pm` thinks like Shreyas Doshi. `/cto` thinks like Martin Fowler. `/engineer` thinks like John Carmack. You invoke whichever lens fits the problem.

**Runs scheduled automations.** Every morning, a daily brief lands in your inbox summarizing open items, upcoming commitments, and signals from your tools. Meeting transcripts are captured and processed automatically. Weekly reviews write themselves into your vault. All read-only until you approve action.

**Drafts on your behalf.** At higher capability tiers, Leto can draft Slack messages, Linear comments, or document sections in your voice — and hold them for your approval before sending. Nothing goes out without an explicit sign-off.

**Maintains memory.** Durable preferences, stakeholder context, project state, and operating patterns accumulate in a structured memory store. Leto reads the relevant files at session start so it doesn't ask you the same questions twice.

---

## Architecture

Leto is not a new app. It's an orchestration layer over tools you probably already use:

```
Your tools                    Leto layer
─────────────────────         ──────────────────────────────────────
Obsidian vault          ←──   Session logs, drafts, captured sources
Linear / task tracker   ←──   Project tracking, state transitions
Slack                   ←──   Scheduled DMs, draft approval surface
Granola / Zoom          ←──   Meeting transcript intake
Claude Code             ←──   Runtime: skills, schedulers, memory, hooks
```

**Five layers, bottom to top:**

| Layer | What it is | Where it lives |
|-------|-----------|---------------|
| Config | Permissions, model routing, hooks | `~/.claude/settings.json`, `CLAUDE.md` |
| Skills | Thin wrappers that invoke persona files | `~/.claude/skills/<name>/SKILL.md` |
| Personas | Deep role definitions (frameworks, heuristics, anti-patterns) | `personas/<bucket>/<name>.md` |
| Schedulers | Automated routines (daily brief, weekly review, intake) | `~/.claude/scheduled-tasks/` |
| Memory | Durable context (preferences, projects, stakeholders) | `~/.claude/projects/<project>/memory/` |

The orchestrator (`skills/leto.md`) reads identity, memory, and recent session logs at startup, then routes to personas or schedulers as needed.

---

## How to build your own

### Prerequisites

- [Claude Code](https://claude.ai/code) installed and configured
- A note-taking system with a clear directory structure (Obsidian recommended, but any works)
- A task tracker (Linear, Notion, or similar) for durable commitments
- Slack or another messaging surface for approval flows (Phase 3+)

You don't need to set up everything at once. The phases below are designed to deliver value at each step.

---

### Phase 1 — Identity layer (1–2 hours)

**Goal:** Claude knows who you are across every session.

**1. Write your operational identity (`reader-context.md`).**

This is the most important file in the system. It's read at the start of every session, by every persona. Keep it under 80 lines. Cover:

- Your role and what you're trying to accomplish in the next 90 days
- How you make decisions (what you optimize for, what you avoid)
- Communication preferences (how you like to receive information, what you find annoying)
- Hard constraints (things Claude should never do on your behalf without asking)
- Voice signature (how you write — tone, structure, what you never say)

Store it somewhere stable (e.g., `~/Notes/System/reader-context.md`).

**2. Write your compass (`CLAUDE.md`).**

This file lives in the root of your Leto repo and tells Claude what to do when it opens a session:
- Where to find your identity file
- Where your memory lives
- What your hard guardrails are (never send without approval, never delete, etc.)
- The session-start procedure (what to read, what to surface)
- The session-end procedure (what to write, where)

**3. Register your Leto skill.**

Create `~/.claude/skills/leto/SKILL.md` — a short file that tells Claude to read the compass and process the session.

**4. Run the bootstrap.**

Open a Claude Code session, invoke `/leto bootstrap`. Walk through the interview. It should generate or refine your `reader-context.md`. Takes 30–45 minutes the first time.

---

### Phase 2 — Persona team (2–4 hours per persona)

**Goal:** Specialist roles you can invoke by name, each calibrated to your context.

**Pick 2–3 roles you reach for most.** Don't build all of them — build the ones you actually need. Common starting set for a product/ops leader:

- `/pm` — product strategy, prioritization, spec writing
- `/cto` — architecture decisions, system design, technical tradeoffs
- `/blake` — ops, cross-functional coordination, launch planning

**For each persona, create two files:**

`personas/<bucket>/<role>.md` — the deep role definition. This is the person Claude becomes when you invoke the skill. Include:
- Who they are and what they optimize for
- Their key frameworks (2–5, concrete and applicable)
- Their anti-patterns (what this person would push back on)
- How they communicate

`~/.claude/skills/<role>/SKILL.md` — the thin wrapper. Three steps: read `reader-context.md`, load the persona file, process the question.

**Organize personas in buckets** (`product/`, `ops/`, `engineering/`) rather than a flat directory. It keeps the inventory honest — you see what's active vs. archived.

---

### Phase 3 — Scheduled automations (1–2 hours per scheduler)

**Goal:** Recurring work happens without you initiating it.

**Start with one scheduler: the daily brief.**

A daily brief that runs every morning and surfaces:
- Open commitments from your task tracker
- Items that have been sitting too long (use an age ladder: mention at 7 days, ask at 14, propose disposition at 21)
- Signals from the day before (meetings, messages, decisions)

Register it as a Claude Code scheduled task with a `SKILL.md` that defines what to read and what to output. Output should go to your note vault and optionally your Slack DM (to yourself).

**Then add intake schedulers** as you feel the need:
- Meeting transcript capture (runs after work hours, catches new transcripts)
- Weekly review (Friday afternoon, past week + next week)
- Tool-specific alignment (reads your task tracker, surfaces stale items)

**Key guardrail for all schedulers:** read-only until you approve. Schedulers surface and draft — they never mutate your tools, send messages, or create tasks without an explicit approval step.

---

### Phase 4 — Approval-gated drafts (when Phase 3 is stable)

**Goal:** Claude drafts on your behalf; you approve before anything goes out.

This is where Leto moves from assistant to delegate. When wired correctly:

1. Leto drafts a Slack message or Linear comment in your voice
2. It posts the draft to your own DM (or a private channel) for review
3. You react ✅ to send, ⏭️ to skip, or reply to edit
4. Leto sends — or waits — based on your reaction

**Hard rule:** nothing goes to another person without a reaction from you in this session. Standing approvals (pre-authorizing categories of message) come later, if at all, and only for low-stakes, easily-reversible sends.

---

## Case study: one real setup

This repo is the working implementation of the framework above, built for a Head of Product Operations at a SaaS company. Here's what the full system looks like in practice.

**Identity layer:**
- `reader-context.md` — 70 lines covering role, decision style, communication preferences, hard constraints, voice
- `CLAUDE.md` compass — session-start/end procedures, tier boundaries, guardrails
- Bootstrap took one 45-minute session; updated quarterly

**Persona team (active):**
- `/pm` — used for roadmap decisions, spec writing, prioritization calls
- `/blake` — used for cross-functional coordination, ops design, stakeholder framing
- `/cto` and `/engineer` — used for architecture reviews and technical tradeoffs
- `/leto` — the orchestrator; opens every working session

Six other personas (designer, QA, security, growth, analytics, product-ops) are built and archived — available but not actively maintained. The rule: if a persona hasn't been invoked in 90 days, it moves to `archive/`.

**Schedulers (7 running):**
- Daily brief at 10:15 — 9-section brief covering open items, meeting prep, and signals
- Granola intake at 17:45 — captures new meeting transcripts as immutable source files
- Weekly review Friday 16:30 — past week summary + next week preview
- Monthly sweep first Sunday — monthly synthesis block
- Notion alignment Monday 08:30 — reads project tracker, surfaces stale items
- EOD backlog 18:00 weekdays — reconciles work signals against personal backlog
- Slack intake every 30 min — captures new DMs as source files for later processing

**Memory:** ~50 files across two stores — stakeholder profiles, project context, operating patterns, tool constraints. Updated at session end when new durable facts emerge.

**Approval surface:** Slack DM to self. Scheduled tasks post draft artifacts as DM threads; approval is a reaction.

**Vault:** Obsidian. Every session produces a log. Every decision has a path. Schedulers write audit docs to `Inbox/Drafts/`.

---

## Key design principles

**One source of truth per concern.** Identity lives in `reader-context.md`. Memory lives in Claude Code memory files. Project tracking lives in Linear. The vault is for human-readable records. Never store the same thing in two places.

**Approval-gated always.** Nothing goes to another person without explicit sign-off in this session. This is a hard rule, not a default that gets relaxed later. The trust you build with this system is built on that rule holding.

**Immutable source, regenerable extract.** When Leto captures a meeting transcript or Slack thread, the raw content is sacred — never modified. Summaries and extracts are regenerated as needed. If your voice or routing evolves, you re-run the extract; you never touch the source.

**Read-only schedulers.** Automated routines read from your tools; they never write back without approval. This keeps automation from accumulating mistakes silently.

**Build phases, not features.** The four-phase ladder (identity → personas → schedulers → drafts) is the right order because each phase makes the next phase safe. Don't skip to drafts before you trust the identity layer. Don't trust the identity layer before you've run the bootstrap.

---

## What to expect

**Phase 1 delivers value in week 1.** Once `reader-context.md` is written and the persona shim is working, every session feels materially different — Claude already knows the context you used to re-explain every time.

**Phase 2 is where it becomes a team.** Having a PM persona and a CTO persona you can fork to in the same session changes how you think through problems. You stop switching contexts mentally; you switch personas.

**Phase 3 takes 2–4 weeks to trust.** Schedulers are only useful if you actually read them. Start with one (daily brief), measure whether it changes what you do in the first hour of your day, then add more based on signal not anxiety.

**Phase 4 is optional.** Many people stop at Phase 3 and get 90% of the value. Approval-gated drafts are powerful but require discipline — both in setting up the approval surface correctly and in actually reviewing what Leto drafts before sending.

---

## Repository structure

```
CLAUDE.md              The compass — what Leto reads at session start
INDEX.md               Artifact map — where everything lives
BOOTSTRAP.md           One-time interview script for reader-context.md
BEST_PRACTICES.md      11 laws for building agentic systems
personas/
  product/             Active product personas
  ops/                 Active ops personas
  engineering/         Active engineering personas
  archive/             Unused personas (recoverable)
  lite/                Lightweight versions for quick terminal queries
skills/
  leto.md              Core orchestrator definition
  hayt.md              Adversarial review council
  doubt-driven.md      In-session doubt cycle
agents/                Shell scripts for terminal persona sessions
tiers/                 Tier 0–4 policy definitions
conventions/           Shared standards (frontmatter, memory, tracking)
schedulers/            Scheduler definitions (source of truth)
integrations/
  slack/               Slack bot for outbound DMs
hooks/                 Stop-event hook for factual review
```

---

## Credits

Inspired by [Dima Kushnikov's obsidian-seed](https://github.com/dkushnikov/obsidian-seed) and [Addy Osmani's agent-skills](https://github.com/addyosmani/agent-skills). Persona frameworks draw from the published writing and talks of Shreyas Doshi, Martin Fowler, John Carmack, Julie Zhuo, Elisabeth Hendrickson, Andrew Chen, Troy Hunt, Cassie Kozyrkov, and Blake Samic.
