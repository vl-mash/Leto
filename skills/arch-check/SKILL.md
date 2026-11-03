---
name: arch-check
description: Architecture check of a plan, ADR, PRD solution section or design before code is written. Sends the design plus minimal code context to a `fable` subagent with a fixed checklist (hardest-to-reverse decision, essential vs accidental complexity, the simpler alternative, data ownership, failure modes and who notices, coupling, fitness functions, ops cost, missing VAST layer) and returns a verdict, the top 3 risks and the simpler alternative. Use for "architecture check", "check this design", "review this ADR", "is this over-engineered", or before a refactor or new service. Escalates to /hayt for commit-level calls.
---

# arch-check

One strong reviewer, one checklist, a typed answer. For a call that commits the org (a new system of record, an irreversible migration), use `/hayt` instead or after.

## Steps

1. **Collect the artifact**: a plan file, an ADR, a PRD's Solution section, or Vladimir's description. If it's only in his message, restate it in 5 lines and confirm.
2. **Collect minimal context**, not the repo: the module tree (2 levels), the files the design touches, existing ADRs it relates to (`docs/adr/` or where the repo keeps them), and the repo `CLAUDE.md` rules. Cap it at about 30K tokens.
3. **Spawn one reviewer**: `Agent`, `subagent_type: "Plan"`, `model: "fable"`. Give it the artifact, the context and the checklist below, and the output contract. Don't give it your own opinion of the design.
4. **Relay** the reviewer's answer in the output contract. Add one line of your own only if you disagree, and say why.
5. **Escalate**: if the verdict is *Rethink*, or the hardest-to-reverse decision has a wide blast radius, offer `/hayt` with CLAIM, ARTIFACT and CONTRACT pre-filled.

Failure path: if `fable` is unavailable, run the reviewer on `opus` and say so in the first line.

## Checklist (condensed from `personas/engineering/cto-martin.md`)

1. **Hardest to reverse.** Which decision, if wrong, is hardest to fix? Is it made as late and as reversibly as possible? (6 months from now, blast radius, a reversible alternative.)
2. **Essential vs accidental complexity.** What could be removed and still meet the need? Name **the simpler alternative**: a script before a service, a table before a database, a monolith module before a microservice, a manual step before automation.
3. **Data ownership.** For each entity: which system is the source of truth, who writes it, what copies exist and how they stay in sync.
4. **Failure modes.** For each dependency (API, credential, scheduled job, connector): what happens when it is down, slow or returns garbage? Does it fail loudly or silently, and **who notices, how fast**? Vladimir's history: silent failures in automations are the most common real defect.
5. **Coupling.** New dependencies between modules or services, and their direction. Domain logic must not depend on infrastructure.
6. **Fitness functions.** The property that must keep holding, and the automated check (test, validator, CI step) that enforces it.
7. **Ops cost.** Credentials, schedules, spend, and who runs this in 6 months if Vladimir is away.
8. **Anti-patterns.** Cargo-cult architecture, premature distribution, framework capture, resume-driven choices.
9. **VAST.** Which layer (Vision → Architecture → Strategy → Tactics) is missing or assumed?

## Output contract

```
arch-check: <artifact> — Go | Go with changes | Rethink

Top risks
1. <risk> · evidence: <where in the design> · fix: <change>
2. …
3. …

Simpler alternative: <one paragraph, or "None: the design is already minimal.">
Hardest to reverse: <decision> · reversible version: <if any>
Failure that nobody would notice: <the one, and the check that would catch it>
Missing VAST layer: <layer, or "none">
Questions only Vladimir can answer: <max 3>
ADR needed: yes (<title>) | no
```
