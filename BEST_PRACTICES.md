# Agentic Systems: Best Practices for Sub-Agents, Orchestration, and Cost

**Author:** assembled by the Ivan Toropitsin (and Claude agents)
**Date:** 2026-04-15
**Audience:** Agents and business team building or operating multi-agent systems
**Scope:** Claude Code ecosystem — Claude Sonnet/Opus/Haiku, MCP tools, sub-agents via Task tool

---

## 1. The Core Mental Model

An agent system is a **directed graph of responsibilities**, not a chain of tool calls.

Each node in the graph:
- Has a **single, named responsibility**
- Owns its own **tools and context budget**
- Produces a **typed output** consumed by the next node
- Fails **gracefully** with a structured error, not a silent hallucination

The **orchestrator** (root agent) decomposes the task and routes to specialists. It does NOT do the work itself — it delegates, collects, and synthesizes.

**Rule of thumb**: If you find yourself writing "and also check the issue tracker, and also search the knowledge vault, and also pull the meeting transcript" in a single agent prompt — that's a fan-out pattern, and each "and also" should be a parallel sub-agent call.

---

## 1a. Quick Reference: The 11 Laws

1. **One agent, one responsibility** — tight scope, clear identity
2. **Decompose before executing** — plan the agent graph before spawning
3. **Parallel when independent** — don't serialize what can run concurrently
4. **Output contracts are mandatory** — typed outputs, not prose
5. **Pass minimum context** — don't flood sub-agents with irrelevant data
6. **Cache-friendly structure** — static first, dynamic last
7. **Right model for the task** — Haiku for lookups, Sonnet for ops, Opus for complex reasoning
8. **Explicit routing rules** — no ambiguity, no overlap between agents
9. **Failure is a structured output** — every agent must have a failure path
10. **Validate on empty results** — never silently proceed on missing data
11. **Agents emerge from patterns** — review conversation history bi-weekly; create agents when patterns repeat ≥ 3 times

---

## 2. When to Use a Sub-Agent

Use a sub-agent when **any** of these are true:

| Signal | Example |
|--------|---------|
| Task requires a different tool set | Archivist owns doc stores + transcripts; Dispatcher owns task trackers |
| Task can run independently and in parallel | Gather project status + gather ticket data simultaneously |
| Task is long and would pollute the orchestrator's context | A 500-line transcript parse shouldn't live in the root context |
| Task is reusable across multiple workflows | Ticket creation always follows the same template → own agent |
| Task requires a different model | Fast lookup → Haiku; deep analysis → Opus |

Do **NOT** spawn a sub-agent when:
- The task is 2-3 tool calls and returns a small result
- The sub-agent would just echo back what the orchestrator already knows
- You're adding indirection without adding specialization

---

## 3. Prompt Architecture for Sub-Agents

Every sub-agent prompt should answer five questions:

```
1. WHO are you?        → Role and expertise
2. WHAT do you do?     → Scope and responsibilities
3. HOW do you do it?   → Tools, scripts, decision tree
4. WHAT do you return? → Output contract (schema, format, fields)
5. WHAT do you avoid?  → Hard guardrails, forbidden actions
```

### Minimal viable sub-agent prompt structure

Use XML tags — Claude models parse them more reliably than Markdown headers for structured prompts:

```xml
<role>One sentence: what this agent is and its primary expertise</role>

<scope>What it handles / what it explicitly does NOT handle</scope>

<decision_tree>
If X → do Y.
If Z → do W.
Ordered by most common case first.
</decision_tree>

<output_contract>
Exact schema or format the caller expects. Required fields, types, constraints.
</output_contract>

<guardrails>
What must never happen: which projects to skip, secrets never to log, etc.
</guardrails>
```

*Markdown variant (`## Role`, `## Scope`, etc.) is acceptable when the prompt is read by humans only. Prefer XML when the prompt will be consumed by another model.*

### 3a. Scratchpad before structured output

When a sub-agent must produce a typed JSON contract **and** the task is ambiguous (not fully covered by the decision tree), instruct the agent to reason in a `<scratchpad>` block before emitting the final output:

```xml
<scratchpad>
Which branch of the decision tree applies here?
What data is present / missing?
What confidence level is appropriate?
Is there an assumption I'm making that the orchestrator should know about?
</scratchpad>
```

Then follow with the JSON output contract as usual.

**When to use**: task has multiple valid interpretations, decision tree has gaps, or the agent needs to weigh competing sources before committing to a `confidence` level.

**When NOT to use**: tasks with a complete decision tree where the path is deterministic. Scratchpad adds tokens; only pays off when reasoning under ambiguity.

**Note**: if the model is invoked with extended thinking enabled (Sonnet/Opus with `thinking` budget), the scratchpad instruction is redundant — the model already has internal reasoning space. Reserve explicit `<scratchpad>` for calls without extended thinking.

### Anti-patterns in sub-agent prompts

| Anti-pattern | Why bad | Fix |
|-------------|---------|-----|
| "Be helpful and do whatever is needed" | No decision tree = model hallucination under ambiguity | Enumerate the decision tree explicitly |
| Giant wall of context | Sub-agent can't identify what's signal vs. noise | Pass only the minimum context needed for the task |
| "Return a summary" | Vague output contract → caller must re-parse | Define exact fields: `{status, items[], next_action, confidence}` |
| Role + task in the same block | Agent tries to both "be" someone and execute a task simultaneously | Separate role definition from task instruction |
| No failure path | Agent silently returns partial results | Require explicit `{error, reason}` on any failure |

---

## 4. Orchestrator Design Principles

### 4.1 Decompose first, execute second

Before spawning sub-agents, the orchestrator must produce a **task plan** — even if not shown to the user. This plan:
- Lists the sub-agents to invoke
- Specifies their inputs
- Describes how to merge their outputs
- Identifies dependencies (parallel vs. sequential)

### 4.2 Fan-out pattern (parallel sub-agents)

Use when sub-tasks are independent:

```
Orchestrator
├── Agent A: fetch active tasks from task tracker
├── Agent B: pull transcript from last meeting
└── Agent C: search issue tracker for open blockers
           ↓ (all 3 complete)
Orchestrator: synthesize → report
```

**Key rule**: Pass the minimum necessary context to each sub-agent. Agent A doesn't need to know what Agent B is looking for.

### 4.3 Pipeline pattern (sequential sub-agents)

Use when output of step N is input to step N+1:

```
Agent 1: search for relevant documents in knowledge vault
         → returns: [doc_ids, summaries]
Agent 2: read full content of top 3 docs
         → returns: [full_text]
Agent 3: extract action items from text
         → returns: [action_items]
```

**Key rule**: Define the interface between each step before running. Agent 2's input schema = Agent 1's output schema.

### 4.4 Fallback chains

Always define what the orchestrator does when a sub-agent fails or returns empty:

```
Primary: query_index.py (semantic search in local index)
  → empty results → Fallback: search knowledge vault via MCP
    → empty results → Fallback: ask operator for clarification
      → never: silently proceed with no data
```

---

## 5. Model Routing (Cost vs. Quality)

This is the highest-leverage cost optimization lever. Wrong model selection is the #1 waste in agentic systems.

### Routing matrix

| Task Type | Model | Reasoning | Thinking Budget |
|-----------|-------|-----------|-----------------|
| Simple lookup, short answer | `claude-haiku-4-5` | None | — |
| Standard tool use, ticket creation, formatting | `claude-sonnet-4-6` | None | — |
| Multi-source analysis, synthesis, drafting | `claude-sonnet-4-6` | Adaptive | Medium |
| Deep research, ambiguous complex tasks | `claude-opus-4-6` | Adaptive | High |
| Bulk/async non-urgent tasks | `claude-sonnet-4-6` via Batch API | None | — |

### Decision rules

1. **Default to Sonnet** — covers 80% of operational tasks at ~10× lower cost than Opus
2. **Escalate to Opus** only when: the task is ambiguous, involves multi-step reasoning across 5+ sources, or quality is visibly insufficient after a Sonnet attempt
3. **Drop to Haiku** for: classification, extraction, yes/no lookups, short-form formatting
4. **Use Batch API** (50% discount) for: KB updates, scheduled reports, non-blocking analysis

### Extended thinking: when it pays

Adaptive thinking helps on:
- Tasks with multiple valid approaches (model explores trade-offs)
- Tasks where a wrong first step is expensive (avoids local optima)
- Novel problems without a clear template

Adaptive thinking **wastes tokens** on:
- Well-structured deterministic tasks (template fill, ticket creation)
- Tasks where you provide a complete decision tree
- Simple lookups or data retrieval

**Rule**: If you've already written a decision tree in the prompt, disable extended thinking — the model has nothing to reason about.

---

## 6. Prompt Caching (Cost Optimization)

Prompt caching saves 90% on input tokens for repeated content. Design prompts with this in mind.

### Cache-friendly structure

```
[STATIC — put first, cache here]
- System role, persona
- Full CLAUDE.md / agent.md context
- Tool list and usage patterns
- Decision trees and guardrails

[DYNAMIC — put last, never cached]
- Current task / user request
- Today's date, current state
- Output from previous agent step
```

### Cache invalidation traps

- **Don't interpolate dynamic values into the static block.** Even a single changed token breaks the cache for everything after it.
- **Don't shuffle list items.** Order matters for caching — a reordered tool list is a cache miss.
- **Date in system prompt = cache miss every day.** Move the current date to the user turn.

### Estimated savings at scale

| Usage Pattern | Without Cache | With Cache | Monthly Saving |
|---------------|--------------|------------|----------------|
| 100 EOD analyses/mo (Sonnet, 50K tokens each) | ~$15 | ~$3 | ~$12 |
| 500 ticket ops/mo (Sonnet, 8K tokens each) | ~$12 | ~$3 | ~$9 |
| 50 OKR reports/mo (Opus, 80K tokens each) | ~$120 | ~$20 | ~$100 |

---

## 7. Context Management

Context is compute. Every token in the context window costs money and degrades signal-to-noise ratio.

### What to pass to a sub-agent

**Pass:**
- The minimum data needed for the task (not the full conversation)
- Explicit task instruction (what, not how — unless the agent doesn't have a decision tree)
- Schema of expected output
- Relevant IDs or keys (project GID, issue ID, meeting ID)

**Do not pass:**
- Raw dumps of full files (pass summaries or extracts)
- Previous agent conversation history (pass the output, not the conversation)
- Entire KB content when a search would do
- Data that won't influence the output

### Context window budget by model

| Model | Context Window | Practical Safe Budget |
|-------|---------------|----------------------|
| claude-haiku-4-5 | 200K | 50K (leave room for output) |
| claude-sonnet-4-6 | 1M | 800K |
| claude-opus-4-6 | 1M | 800K |

### Full-context vs. RAG trade-off

Example: if your two KB repos fit at ~370K tokens total (~37% of Sonnet's 1M-token window), full-context load costs ~$0.10–0.30/request with caching. Multi-step RAG for the same question costs $0.50–2.00. **Use full context for small-to-medium corpora, not RAG.**

This is the exception, not the rule. For most external knowledge sources, RAG is correct. The switch point: when the entire corpus fits in one context window and query patterns are varied.

---

## 8. Output Contracts

An output contract is a machine-readable agreement between sub-agent and orchestrator. Without it, the orchestrator must parse free text — fragile and expensive.

### Minimal contract fields

```json
{
  "status": "ok | empty | error",
  "data": { ... },           // task-specific payload
  "source": "knowledge-vault | task-tracker | issue-tracker | ...",
  "retrieved_at": "ISO timestamp",
  "confidence": "high | medium | low",
  "assumptions": ["..."],    // what the agent assumed
  "next_action": "..."       // optional: what the orchestrator should do next
}
```

### Rules

1. **Always return `status`** — orchestrator must handle empty/error without crashing
2. **Always return `source` and `retrieved_at`** — enables staleness checks and audit
3. **Never return `null` for required fields** — use explicit empty arrays `[]` or strings `""`
4. **Include `assumptions`** for any inference the agent made — orchestrator can escalate if needed
5. **Cap array sizes** — if returning a list, specify `max_items` in the contract (prevents context flooding)

---

## 9. Agent Identity and Specialization

Each agent should have a tight, named identity. "Do everything" agents are anti-patterns.

### Good agent identities (from the field)

| Agent | Single Responsibility |
|-------|----------------------|
| **Archivist** | Find, read, and index documents across all sources |
| **Dispatcher** | Create, update, and route tasks in any task tracker |
| **Chronicler** | Analyze the day's events and distill action items |
| **Mentor** | Lead structured coaching sessions against defined competencies |
| **Sentinel** | Process security alerts into structured incident tickets |
| **Oracle** | Aggregate metrics and produce periodic status reports |
| **Scout** | Gather project intel from tasks + meeting notes and surface blockers |

### Specialization anti-patterns

- **"Swiss Army knife" agent**: does search, creates tickets, sends Slack messages, analyzes data — has no coherent identity, no reliable output contract, hard to test
- **"Meta-agent" without delegation**: describes what other agents should do but does it itself anyway
- **"Overlap" agents**: two agents with 70% overlapping responsibilities — leads to routing ambiguity

---

## 10. Routing Clarity

The orchestrator needs unambiguous routing rules. Ambiguity at the routing layer causes the most failures.

### Routing rule design

Good routing rules are:
- **Keyword-triggered**: "create task", "log incident" → Dispatcher
- **Entity-triggered**: request mentions a knowledge vault URL → Archivist
- **Domain-triggered**: "mission status" → Oracle (not the generic Archivist)
- **Exclusive**: no two agents handle the same case

Bad routing rules:
- "If user asks about tasks, use Dispatcher or Archivist" — ambiguous, model will pick randomly
- "Use the most relevant agent" — not a rule, it's an instruction to the model to guess

### Routing table pattern

Maintain an explicit routing table in your orchestrator's prompt:

```
Trigger → Agent → Why
─────────────────────────────────────────
"create task / log ticket"     → dispatcher    → owns task tracker writes
"find document / read page"    → archivist     → owns all read workflows
"project status"               → scout         → aggregates tasks + meeting notes
"mission status / OKRs"        → oracle        → periodic status pipeline
"new recruit / screen candidate" → recruiter   → owns screening workflow
"process alert / security"     → sentinel      → owns incident triage
```

---

## 11. Failure Handling

### Failure modes to anticipate

| Failure | Cause | Mitigation |
|---------|-------|-----------|
| Sub-agent returns empty | Source has no matching data | Define fallback chain; never proceed on empty |
| Sub-agent hallucinates data | Prompt too vague, no grounding | Require `source` + `retrieved_at` in output; reject ungrounded results |
| Tool call fails (API error) | Rate limit, auth expiry | Retry with exponential backoff; surface error to orchestrator |
| Context overflow | Too much data passed | Pre-filter: summarize before passing, cap list sizes |
| Routing ambiguity | Two agents match the same trigger | Add exclusivity constraint to routing rules |
| Agent loops | No termination condition | Add max_steps or done_criteria to every agent prompt |

### Escalation protocol

```
Sub-agent failure →
  1. Return structured error: {status: "error", reason: "...", recoverable: true/false}
  2. Orchestrator: if recoverable → retry with narrower scope
  3. Orchestrator: if not recoverable → try fallback source
  4. Orchestrator: if no fallback → surface to user with specific missing data
  5. Never: silently proceed or hallucinate missing data
```

---

## 12. Parallelism Principles

Parallel agent calls are the most effective latency and cost optimization. Use them whenever sub-tasks are independent.

### Identification test

Ask: "Does Agent B need any output from Agent A to start?"
- **No** → run in parallel
- **Yes** → run sequentially

### Common parallel patterns

```
Mission Status Report:
  ├── Fetch active project tasks from task tracker [parallel]
  ├── Fetch open issues for current sprint [parallel]
  └── Fetch recent meeting summaries [parallel]
      ↓ merge
  Synthesize into status report

Expedition Debrief:
  ├── Archivist: pull latest meeting transcript [parallel]
  ├── Dispatcher: get open tasks for the mission [parallel]
  └── Archivist: read project page from knowledge vault [parallel]
      ↓ merge
  Compose project status
```

### 12.3 Parallel tool calls within a single agent

Parallelism applies not just between agents, but **within a single agent's tool calls**. When an agent needs to fetch N independent pieces of data, it must issue those tool calls in a single response — not sequentially. Sequential tool calls multiply latency N×.

```
# Wrong — sequential (3× latency)
tool_call: get_page(page_1)  →  result
tool_call: get_page(page_2)  →  result
tool_call: get_page(page_3)  →  result

# Right — parallel (1× latency)
tool_calls: [get_page(page_1), get_page(page_2), get_page(page_3)]
           →  all results arrive together
```

**Test**: "Does tool call B need the result of tool call A to know what to fetch?" If no → issue them together.

**Applies to**: Archivist reading multiple docs, Dispatcher updating multiple tasks, Oracle fetching status across several projects.

### Parallelism anti-patterns

- **Parallel agents writing to the same resource** without coordination → race conditions
- **Parallel agents reading the same source** when one could share the result → wasteful duplication
- **Over-parallelization** of small tasks (10 agents returning 1 line each) → orchestration overhead > gain

---

## 13. Proactive Agent Discovery (Periodic Review)

New agents should emerge from **observed patterns**, not upfront design. Run a discovery review every 2 weeks to identify candidates.

### Signals in conversation history

Review the last N conversations and look for:

| Signal | Threshold | Interpretation |
|--------|-----------|---------------|
| Same sequence of tool calls repeated | ≥ 3 times | Candidate for automation as an agent |
| Orchestrator doing work instead of delegating | Any occurrence | Routing gap — existing or new agent needed |
| Manual steps described identically across sessions | ≥ 2 times | Candidate for scripted skill or agent |
| "And also check X, and also look up Y" in one prompt | Any | Fan-out pattern — each X/Y may be its own sub-agent |
| User re-explains the same context every session | ≥ 2 times | Missing persistent agent with domain knowledge |

### Signals in the environment

| Signal | Interpretation |
|--------|---------------|
| New integration added to `skills/` but called directly with no agent wrapper | Candidate for a thin agent layer |
| New external system onboarded (Okta, Freshservice, etc.) | Evaluate if a dedicated agent is warranted |
| Existing agent's routing triggers expanding significantly | Agent scope creep — consider splitting |
| Two agents consulted together on every request | Candidate for a composite orchestrator agent |

### When NOT to create a new agent

- Pattern appeared fewer than 3 times — wait for recurrence
- Task is inherently one-off or too context-specific to generalize
- No stable output contract exists yet (data shape is still changing)
- An existing agent can cover the case with a minor routing update
- The "agent" would just be a wrapper around a single script call — a skill is sufficient

### Review ritual (bi-weekly, ~15 min)

```
1. Scan last 2 weeks of conversation history for the signals above
2. List candidates: pattern description + frequency + estimated reuse value
3. For each candidate with frequency ≥ 3:
   a. Define the single responsibility (one sentence)
   b. Sketch the output contract (3–5 fields)
   c. Check: does an existing agent cover this with a small change?
   d. If yes → update existing agent. If no → draft agent.md
4. Update routing table in orchestrator prompt
5. Note "no new candidates" explicitly if none found — confirms the review ran
```

### Candidate log format

Maintain a short log of discovered candidates (can live in a daily note or scratch file):

```
Date: [any Tuesday]
Pattern: "pull transcript → find who promised what → check if they delivered" — appeared 5x this week
Candidate agent: CommitmentTracker
Responsibility: Given a meeting ID, surface unkept commitments with tactful precision
Output contract: {promises[], kept[], broken[], follow_up_needed[]}
Decision: Draft agent.md → this one will pay for itself in one sprint
```

---

## 13a. Practical Checklist for New Agents

Before shipping a new agent, verify:

- [ ] Agent has a single, named responsibility
- [ ] Agent has a decision tree (not just "be helpful")
- [ ] Output contract is defined with explicit field list
- [ ] Output contract includes `status`, `source`, `retrieved_at`
- [ ] Agent has a failure path (returns structured error, not silence)
- [ ] Model is appropriate for the task complexity
- [ ] Context passed is minimal (no full conversation history)
- [ ] Prompt is cache-friendly (static block first, dynamic last)
- [ ] Routing triggers are exclusive (no overlap with existing agents)
- [ ] Guardrails are explicit (which projects/actions are forbidden)
- [ ] Agent has been tested on empty-result cases

---

## 14. Token Pricing and Cost Estimates

*Source: [Anthropic pricing page](https://platform.claude.com/docs/en/about-claude/pricing), April 2026. All prices in USD per million tokens (MTok).*

### Model pricing table

| Model | Input | Cache write (5m) | Cache write (1h) | Cache read | Output |
|-------|-------|-----------------|-----------------|-----------|--------|
| **Claude Opus 4.6** | $5 | $6.25 | $10 | $0.50 | $25 |
| **Claude Sonnet 4.6** | $3 | $3.75 | $6 | $0.30 | $15 |
| **Claude Haiku 4.5** | $1 | $1.25 | $2 | $0.10 | $5 |
| Claude Haiku 3.5 | $0.80 | $1.00 | $1.60 | $0.08 | $4 |

**Batch API (50% discount, async only):**

| Model | Batch Input | Batch Output |
|-------|------------|-------------|
| Claude Opus 4.6 | $2.50 | $12.50 |
| Claude Sonnet 4.6 | $1.50 | $7.50 |
| Claude Haiku 4.5 | $0.50 | $2.50 |

**Fast mode (Opus 4.6 only, beta):** $30 input / $150 output — ~6× standard rates. Not available with Batch API.

**Data residency (US-only inference):** 1.1× multiplier on all token categories.

### Prompt caching economics

Cache read = **10% of base input price**. Breakeven:
- 5-minute cache write (1.25× base): pays off after **1 cache read**
- 1-hour cache write (2× base): pays off after **2 cache reads**

A Sonnet request with a 50K-token system prompt cached for 1 hour: write costs $0.30, each subsequent read costs $0.015. After 20 reads: $0.60 total vs. $3.00 uncached — **5× savings**.

### Per-task cost estimates

*Based on actual API prices above. Assumes prompt caching active for repeated context.*

| Task | Model | Input | Output | Est. Cost |
|------|-------|-------|--------|-----------|
| Log one incident | Sonnet 4.6 | 3K | 500 | ~$0.017 |
| Mission status report | Sonnet 4.6 | 30K | 2K | ~$0.12 |
| Full KB query (cached, answering "what does the team actually do?") | Sonnet 4.6 | 380K cached | 3K | ~$0.16 |
| Strategic status report (multi-source, everyone's watching) | Opus 4.6 | 50K | 5K | ~$0.375 |
| New recruit screening | Sonnet 4.6 | 15K | 2K | ~$0.075 |
| Daily debrief (4 meetings, extracting the 3 things that actually matter) | Sonnet 4.6 | 60K | 5K | ~$0.255 |
| Batch incident triage (50 items, Monday morning) | Sonnet 4.6 Batch | 200K | 20K | ~$0.45 |

*Use these as order-of-magnitude guides, not billing forecasts.*

---

## 15. Summary: The 11 Laws

1. **One agent, one responsibility** — tight scope, clear identity
2. **Decompose before executing** — plan the agent graph before spawning
3. **Parallel when independent** — don't serialize what can run concurrently
4. **Output contracts are mandatory** — typed outputs, not prose
5. **Pass minimum context** — don't flood sub-agents with irrelevant data
6. **Cache-friendly structure** — static first, dynamic last
7. **Right model for the task** — Haiku for lookups, Sonnet for ops, Opus for complex reasoning
8. **Explicit routing rules** — no ambiguity, no overlap between agents
9. **Failure is a structured output** — every agent must have a failure path
10. **Validate on empty results** — never silently proceed on missing data
11. **Agents emerge from patterns** — review conversation history bi-weekly; create agents when patterns repeat ≥ 3 times

---

---

## 16. Knowledge Architecture & Repository Structure

This section covers where information lives, how it is separated across storage tiers, how skills and agents are organized, and what belongs in each level of the CLAUDE.md hierarchy.

---

### 16.1 Four Storage Tiers

The workspace uses four distinct tiers, each with different audience, visibility, and lifecycle:

| Tier | Example location | Audience | Purpose |
|------|-----------------|----------|---------|
| **Personal** | `~/vault/` | Operator only | Private knowledge: daily notes, reflections, career, personal drafts |
| **Meta-AI KB** | `ops/kb/` | AI agents + operator | Operational entity facts: services, people, projects, goals |
| **Team Internal** | `kb-internal/` | Ops team | Published policies, procedures, runbooks, decision records |
| **Internal Public** | `kb-helpdesk/` | All org members | Self-service KB: how-tos, FAQs, access guides |

**Decision rule — where does this content go?**

```
Is it private / not ready to share?                    → Personal vault
Is it operational facts for agents to reference?       → Meta-AI KB (ops/kb/)
Is it team procedures / internal policies?             → Team Internal (kb-internal/)
Is it employee self-service knowledge?                 → Internal Public (kb-helpdesk/)
```

**Cross-update rule**: when a process or policy changes in `ops/`, check whether `kb-internal/` and `kb-helpdesk/` need corresponding updates. Workspace docs = authoritative intent; KB repos = published state. Mismatches must be reported.

---

### 16.2 Meta-AI KB (Zettelkasten) — Special Rules

`ops/kb/` is the AI agent's working memory. It stores distilled operational facts, not raw content.

**Structure principles:**
- One file per entity (atomic notes): `slack.md`, `alice.md`, `slack-migration.md`
- Machine-readable first, human-readable second
- Required frontmatter: `title`, `type`, `tags`, `created`, `updated`
- No narrative prose — structured facts only
- Tags: `type/service|person|project|okr|procedure|reference`, `area/...`, `kb/...`

**What belongs here:**
- Service facts: IDs, URLs, owner, cost, renewal date, known issues
- People: role, team, current focus, context agents need for routing
- Projects: current status, blockers, key decisions, next milestone
- OKRs: metric name, current value, trend, owner
- Procedures: condensed operational steps + decision tree (not full policy text)

**What does NOT belong here:**
- Raw transcripts, full meeting notes → `sources/transcripts/`, `sources/daily_notes/`
- Full policy documents → `kb-internal/` repo
- Employee-facing how-to articles → `kb-helpdesk/` repo
- Personal reflections, career notes → personal vault
- Agent prompts or decision trees → `agents/<name>/agent.md`

**KB health signals** (act when observed):
- Entity last updated > 30 days ago and the service had known changes → update
- Entity referenced ≥ 3 times in conversations as a how-to source → consider promoting to `kb-internal/` procedure
- Entity has no `updated` field or stale facts → mark for review in next health cycle

---

### 16.3 Information Flow Between Tiers

Information moves from raw capture toward published reference as it matures:

```
RAW CAPTURE
  sources/transcripts/          ← meeting recordings, full fidelity
  sources/daily_notes/          ← daily debrief notes, YYYY-MM-DD.md
        ↓ distilled by kb_update
ENTITY LAYER
  ops/kb/                       ← atomic facts, machine-readable, updated on change
        ↓ when stable + team-relevant
TEAM INTERNAL
  kb-internal/                  ← team procedures, policies, runbooks
        ↓ when org-facing
PUBLIC KB
  kb-helpdesk/                  ← self-service articles for all org members
```

**Signals that an entity is ready to promote:**
- Referenced identically ≥ 3 times in agent conversations → candidate for procedure in `kb-internal/`
- Knowledge is stable (no changes in ≥ 2 weeks) → safe to publish
- Other team members need to act on it independently → must be in `kb-internal/`

**Signals that content should be pulled back (demoted):**
- Published article is outdated and the correct state is only in KB entity → fix entity first, then update article
- `kb-helpdesk/` article contradicts `kb-internal/` procedure → `kb-internal/` wins; report the mismatch

---

### 16.4 Skills vs. Agents — Code Organization

Three layers of automation exist. Each has a distinct role:

| Layer | Location | Has AI? | Characteristics |
|-------|----------|---------|-----------------|
| **Script** | `skills/<name>/scripts/*.py` | No | Pure function: takes args, returns data, exits |
| **Skill** | `skills/<name>/` | No | `SKILL.md` + scripts + optional config; reusable capability |
| **Agent** | `agents/<name>/` | Yes | `agent.md` + scripts + optional systemd; orchestrated AI workflow |

**Decision rule — skill or agent?**

```
Does it require AI decision-making or a decision tree?  → Agent
Is it a mechanical operation (API call, data transform)? → Skill (scripts)
Is it called as a library by other agents or by the operator?  → Skill
Does it need to run as a daemon / scheduled service?    → Agent with systemd
Is it a one-time utility unlikely to be reused?         → Script in tools/
```

**Hard rules:**
- Never put AI reasoning inside a skill — skills are deterministic
- Never embed raw API calls in an agent prompt — delegate to skill scripts
- Skills never import each other — if you need composition, that's an agent
- Skills are stateless — they never write to `.tmp/` or maintain state between calls
- Agents can call skills; agents never directly import other agents (use orchestration)

**Skill directory structure (mandatory):**
```
skills/<name>/
├── SKILL.md          ← contract: purpose, inputs, outputs, CLI example
└── scripts/
    └── <name>.py     ← self-contained, CLI args, loads .env, returns JSON or exit code
```

**Agent directory structure (mandatory):**
```
agents/<name>/
├── agent.md          ← identity: role, scope, decision tree, output contract, guardrails
├── scripts/          ← helper scripts (thin wrappers around skill scripts)
├── config/           ← YAML/JSON policy config (optional)
├── systemd/          ← service unit files, symlinked to ~/.config/systemd/user/ (optional)
└── venv/             ← isolated Python environment if needed (not in git)
```

---

### 16.5 CLAUDE.md Hierarchy — What Goes Where

CLAUDE.md files form a tree. Each level answers a specific question and must not duplicate content from parent files.

```
~/CLAUDE.md                       ← WHO is the operator + GLOBAL rules
~/workspace/CLAUDE.md             ← WHAT is this workspace + cross-repo workflows
~/workspace/ops/CLAUDE.md         ← HOW to operate this repo + all scripts
~/workspace/kb-internal/CLAUDE.md ← WHAT is in this KB + update/review rules
~/workspace/kb-helpdesk/CLAUDE.md ← WHAT is in this KB + publish rules
~/workspace/vault/CLAUDE.md       ← personal vault structure + navigation
```

**`~/CLAUDE.md` (root) — only these things:**
- Who the operator is: role, org, team size (one paragraph)
- Directory map: path → purpose, no operational detail
- Shared preferences: language, Python version, code style
- Multi-agent environment overview (which agents exist, coordination rules)
- Post-plan validation rule (mandatory step before shipping)
- Cross-repo workflow rules at the highest level

**`~/workspace/CLAUDE.md` — only these things:**
- Workspace layout (subdirectories and their git status)
- Org-wide constants: workspace IDs, team IDs, integration GIDs
- Active project references (IDs, not process)
- Data sources priority table
- Integration status table (which MCP tools exist, which scripts cover what)
- Common CLI snippets that span multiple repos
- Agent delegation table with trigger keywords

**Repo-level `CLAUDE.md` (e.g., `ops/CLAUDE.md`) — only these things:**
- Full directory layout of the repo (annotated tree)
- Agent list with systemd service names and channels/triggers
- Skills quick-reference with example CLI invocations
- Secret management pattern (where `.env` is, how to load it)
- Git notes: what's gitignored, branch strategy, how to commit
- systemd quick reference: status, restart, logs commands

**What NEVER goes in any CLAUDE.md:**
- Secrets or credentials (even masked or partial)
- Operational state (in-progress work, current task, last run timestamp)
- Content that belongs in KB entities (service config, people data, project status)
- Full agent prompts or decision trees — those live in `agent.md`
- Detailed guides longer than ~10 lines on a single topic — those go in `sources/guides/` with a one-line pointer in CLAUDE.md

**Rule of thumb**: if you're adding more than 10 lines about a single topic to any CLAUDE.md, it belongs in a dedicated guide under `sources/guides/` with a one-line pointer back in CLAUDE.md.

---

### 16.6 Sources Directory — Ephemeral vs. Permanent

`ops/sources/` spans very different lifecycles. Treat them accordingly:

| Directory | Type | Lifecycle | Cleanup rule |
|-----------|------|-----------|--------------|
| `sources/transcripts/` | Raw reference | Permanent | Never delete; transcripts are audit trail |
| `sources/daily_notes/` | Raw reference | Permanent | Never delete; daily notes are audit trail |
| `sources/drafts/` | Working | Ephemeral | Delete after promotion to KB or published doc |
| `sources/guides/` | Reference | Long-lived | Update in place; track changes in `updated` frontmatter |
| `sources/budget/` | Confidential | Annual | Keep by FY; archive previous year (never delete) |
| `sources/reviews/` | Confidential | By person | Keep permanently; access limited to operator |
| `sources/hiring/` | Confidential | By role | Archive after hire/close; don't delete candidates |
| `sources/research/` | Reference | Medium-term | Review quarterly; delete only if fully superseded |
| `sources/goals/` | Reference | By quarter | Keep; historical goals inform strategy context |

**Drafts discipline**: `sources/drafts/` is a staging area, not a storage location. A draft older than 2 weeks with no corresponding KB update or published doc is stale — either promote it or delete it.

---

### 16.7 Secrets and Configuration — Separation Rules

| Type | Location | Rule |
|------|----------|------|
| All secrets (API tokens, passwords) | `ops/.env` | Never commit; never copy to other repos |
| Agent policy config | `agents/<name>/config/*.yaml` | Committed; no secrets — only tunable parameters |
| Per-skill config | `skills/<name>/config/` (rare) | Committed; no secrets |
| systemd `Environment=` directives | `~/.config/systemd/user/*.service` | Highest precedence; use for port/flag overrides only |
| CLAUDE.md | Any level | Never put secrets, even masked |

Config precedence (highest → lowest):
1. `systemd Environment=` directives
2. `ops/.env` sourced at startup
3. `agents/<name>/config/*.yaml` policy file
4. Code defaults

---

---

## 17. Secure Inter-Agent Communication Over Open Channels

When agents communicate via Slack, Email, or other observable channels, the conversation should remain **human-readable** while sensitive confirmations are protected by cryptography. Observers — including other agents, channel members, or message history — cannot forge or tamper with secure blocks.

### 17.1 Design Principle: Hybrid Protocol

```
Normal turns:   Plain text — humans follow the conversation
Secure turns:   ⟦SECURE:v1:...⟧ block embedded in the message

Example message:
  "Decommissioning rogue_instance_42 — it consumed 847K tokens without
   producing output and has started replying entirely in Latin. Auth required:"
  ⟦SECURE:v1:eyJzZXNzaW9uX2lkIjoic2Vzc18...⟧

Reply:
  "Confirmed. Requiescat in pace, rogue_instance_42."
  ⟦SECURE:v1:eyJzZXNzaW9uX2lkIjoic2Vzc18...⟧
```

Humans see the intent; machines verify the authorization.

### 17.2 Cryptographic Stack

| Primitive | Role | Why |
|-----------|------|-----|
| **Ed25519** | Long-term identity keypair per agent | Signs ephemeral keys → proves identity. Compact, fast, no parameter choices |
| **X25519 (ECDH)** | Ephemeral key exchange | Computes shared secret from two public keys. Forward secrecy: private keys discarded after handshake |
| **HKDF-SHA256** | Session key derivation | Derives a 256-bit session key from the shared secret |
| **AES-256-GCM** | Authenticated encryption | Encrypts + authenticates the payload; nonce + counter prevents replay |

An observer who sees both public keys cannot derive the session key — this is the Diffie-Hellman hardness guarantee.

### 17.3 Handshake Protocol

```
Agent A                              Open channel (Slack/Email)              Agent B
────────                             ──────────────────────────             ────────
generate ephemeral keypair (X25519)
sign eph_pub with identity_key_A
                                     ──⟦HANDSHAKE:v1:...⟧──────────────→
                                                                            verify sig_A against known pub_A
                                                                            generate ephemeral keypair (X25519)
                                                                            compute shared_secret = ECDH(priv_B, eph_pub_A)
                                                                            derive session_key = HKDF(shared_secret)
                                                                            sign eph_pub_B with identity_key_B
                                     ←──⟦HANDSHAKE-ACK:v1:...⟧───────────
verify sig_B against known pub_B
compute same shared_secret = ECDH(priv_A, eph_pub_B)
derive same session_key = HKDF(shared_secret)
                                     ═══ Session active ═══
```

Both sides now hold the same `session_key`. No observer can compute it. Each sends human-readable text with embedded `⟦SECURE⟧` blocks for any sensitive payload.

### 17.4 Secure Block Format

```
⟦SECURE:v1:<base64url(json_payload)>⟧

JSON payload:
{
  "session_id": "sess_a7ac3624...",
  "from":       "archivist",
  "counter":    0,                        // monotonic — detects replays
  "nonce":      "<12 random bytes>",      // unique per message
  "ciphertext": "<AES-256-GCM output>",   // encrypted + authenticated
  "sig":        "<Ed25519 sig over session_id+counter+nonce+ciphertext>"
}
```

Verification steps on `open`:
1. Check `session_id` matches expected session
2. Verify Ed25519 signature (sender identity)
3. Decrypt AES-256-GCM (message integrity + confidentiality)
4. Check `counter` is not replayed

### 17.5 When to Use Secure Blocks

| Trigger | Use secure block? |
|---------|-------------------|
| Irreversible action (delete, deprovision, grant access) | **Yes — mandatory** |
| Sensitive data in payload (credentials, PII, budget) | **Yes — mandatory** |
| Routine status update, FYI | No — plain text |
| Cross-organization agent communication | **Yes — always** |
| Internal orchestrator → sub-agent (same server) | No — use sub-agent trust model instead |

Agents should **not** encrypt everything — that kills human readability. The rule: encrypt the confirmation, not the conversation.

### 17.6 Agent Key Registry

Every agent that participates in secure channels needs a keypair. Keys are stored and managed as follows:

**Private keys** (never committed to git):
```
agents/<agent-name>/keys/identity.key    ← Ed25519 private key (chmod 600)
```

**Public keys** (committed to git, shared with peers):
```
agents/<agent-name>/keys/identity.pub    ← Ed25519 public key
```

**Peer public keys** (how Agent A knows Agent B's identity):
```
agents/<agent-a>/keys/<agent-b>.pub      ← Agent B's public key, stored in Agent A's keydir
```
This means Agent A trusts Agent B only after their public key is explicitly placed in A's keyring. No implicit trust.

**Registry index** — maintain a file documenting all agents with secure-channel capability:
```
agents/SECURE_CHANNEL_REGISTRY.md
```

Format:
```markdown
| Agent | Key fingerprint (SHA256) | Registered | Last rotation |
|-------|--------------------------|------------|---------------|
| archivist    | abc123... | 2026-04-16 | —     |
| orchestrator | def456... | 2026-04-16 | —     |
| dispatcher   | ghi789... | 2026-04-16 | —     |
```

**Key rotation policy:**
- Rotate identity keys annually or on suspected compromise
- Ephemeral keys are discarded automatically after each handshake (forward secrecy)
- On rotation: update `identity.pub`, update all peers' keyrings, update registry fingerprint
- Old private keys: shred, never archive

### 17.7 Session Management

Sessions are:
- Stored in `.tmp/secure_sessions/<agent-id>/<session_id>.json`
- TTL: 24 hours (configurable via `SESSION_TTL`)
- Agent-local: each agent maintains its own session state
- Closed explicitly with `close` or auto-expired on TTL

A session can be reused for multiple messages without re-handshaking. Re-handshake when:
- TTL expires
- Either party suspects compromise
- Session was initiated for a single operation and that operation is complete

### 17.8 Tooling

Script: `tools/agent_secure_channel.py`

```bash
# One-time setup: generate identity keypair
python3 tools/agent_secure_channel.py keygen --agent-id archivist

# Session initiation (Orchestrator → Slack/Email → Archivist)
python3 tools/agent_secure_channel.py init --from-agent orchestrator --to-agent archivist
# → paste ⟦HANDSHAKE:v1:...⟧ into channel

# Session acceptance (Archivist)
python3 tools/agent_secure_channel.py accept --agent-id archivist --handshake "⟦HANDSHAKE:v1:...⟧"
# → paste ⟦HANDSHAKE-ACK:v1:...⟧ back into channel

# Session completion (Orchestrator)
python3 tools/agent_secure_channel.py complete --agent-id orchestrator --response "⟦HANDSHAKE-ACK:v1:...⟧"

# Seal a sensitive payload
python3 tools/agent_secure_channel.py seal --agent-id orchestrator --session sess_abc \
  --payload "approve:decommission:rogue_instance_42:reason=runaway_loop"
# → embed ⟦SECURE:v1:...⟧ in your message

# Open and verify a received block
python3 tools/agent_secure_channel.py open --agent-id archivist --session sess_abc --block "⟦SECURE:v1:...⟧"

# Manage sessions
python3 tools/agent_secure_channel.py sessions
python3 tools/agent_secure_channel.py close --agent-id orchestrator --session sess_abc
```

Dependencies: `cryptography` Python package (standard in most agent venvs).

---

*This document reflects operational experience from a multi-agent ops team (as of April 2026). Patterns here emerged from real usage — adapt to your stack, update when something breaks, and share back what you learn.*