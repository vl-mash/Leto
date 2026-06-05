# Hayt — Leto's decision advisor (multi-model deliberation council)

> *"The Tleilaxu rebuilt Duncan Idaho from a corpse, deliberately constructed to test Paul Atreides's decisions. The Bene Tleilax built him to find Paul's breaking point; Paul integrated him as his most trusted counsellor. An advisor built to challenge, not to agree."* — VM-33 naming rationale

A council of independent reviewers convened against a single artifact + contract. Routes the question by shape (adversarial vs deliberative), runs the deliberation, synthesizes the judgment with explicit agreement map + dissent. Built to challenge, not approve.

## When to invoke Hayt

A decision warrants Hayt when **at least one** of these is true:

- High-stakes irreversible commitment (Vision artifact about to ship to CTO; architecture invariant about to be locked; org-shape proposal about to land in a CPTO Office meeting)
- Vladimir suspects he has a vibe, not a decision — wants the vibe materialized as a CLAIM and pressure-tested
- Single-agent review (`doubt-driven`) feels insufficient because the problem has multiple defensible framings and Vladimir wants to see *where* defensible reasoning diverges
- Cross-functional artifact where blind spots cluster by role-framework (a CTO-only review and a PM-only review would each be incomplete)

**When NOT to use:** trivial decisions, mechanical changes, internal Leto operations, anything `doubt-driven` already handles cleanly. Hayt is more expensive than a single-agent review — use only when divergent reasoning is the value.

**Hayt vs `doubt-driven` vs persona team:**

| Mechanism | What it does | When |
|-----------|--------------|------|
| `doubt-driven` | Single fresh-context adversarial reviewer | Most non-trivial decisions; default |
| Persona team (`/cto`, `/pm`, `/qa`, …) | Role-framework lens (Fowler / Shreyas / Hendrickson) | Need a specific professional perspective |
| **Hayt** | **Three independent reviewers with assigned stances, synthesized** | High-stakes, multi-framing decisions where blind spots are real |

Not redundant. Orthogonal layers.

## Version state

- **v0**: single-vendor (Claude subagents) with assigned stances. Exercises 6 of 7 nestor primitives. Active when `mcp__pal__consensus` is NOT available in session.
- **v1 (active, 2026-06-05)**: cross-vendor (Claude / GPT / Gemini via pal-mcp-server + direct APIs). All 7 nestor primitives. Active when `mcp__pal__consensus` is available.

Both paths are defined in §4. SKILL.md checks availability at session start.

### v1 design decisions (resolved 2026-06-05)

| Decision | Resolution |
|---|---|
| MCP backend | pal-mcp-server — `uvx` install from GitHub, configured in `~/.claude/settings.json` |
| API approach | Direct: `OPENAI_API_KEY` + `GEMINI_API_KEY` (no OpenRouter middleman) |
| Cost ceiling | Warn-then-confirm — estimate displayed before council spawns; requires "go" |
| Logging substrate | Linear comment on VM-33 (after synthesis) + vault session log |
| Trigger | Explicit `/hayt` invocation only — no auto-invoke |

### v1 model rosters

| Preset | Reviewer A (FOR) | Reviewer B (AGAINST) | Reviewer C (NEUTRAL) | Est. cost |
|--------|------------------|----------------------|----------------------|-----------|
| `arch` | claude-opus-4-8 | gpt-4o | gemini-2.0-pro | ~$0.20–0.30 |
| `code` | claude-sonnet-4-6 | gpt-4o | gemini-2.0-flash | ~$0.08–0.15 |
| `research` | claude-opus-4-8 | gpt-4o | gemini-2.0-pro | ~$0.20–0.30 |
| `quick` | claude-haiku-4-5 | gpt-4o-mini | gemini-flash | ~$0.02–0.05 |
| `brainstorm` | claude-opus-4-8 | gpt-4o | gemini-2.0-pro | ~$0.20–0.30 |

## The protocol (v0)

Five steps. Vladimir is the orchestrator; Hayt is the council.

```
- [ ] CLAIM      — name the decision + why it matters (≤ 3 lines)
- [ ] EXTRACT    — smallest reviewable unit: artifact + contract, stripped of reasoning
- [ ] ROUTE      — pick mode (adversarial / deliberative) + preset; announce before executing
- [ ] COUNCIL    — spawn 3 reviewers in parallel; collect their outputs
- [ ] SYNTHESIZE — agreement map + dissent + unaddressed gaps; classify findings
```

### 1. CLAIM — surface what stands

Two or three lines. Decision + why-it-matters.

```
CLAIM: "<the hypothesis Hayt is testing>"
WHY THIS MATTERS: "<consequence if wrong>"
```

If you can't write the claim that compactly, you have a vibe — surface it first.

### 2. EXTRACT — smallest reviewable unit

Hayt receives **artifact + contract**, NOT the claim. Handing the council your conclusion biases them toward agreement.

- **Artifact**: the actual document, code, decision text — the thing being judged
- **Contract**: what the artifact has to satisfy. Crisp checklist, no prose. Examples:
  - "Vision artifact has falsifiable triggers (2-5), each observable + bounded + owned"
  - "Architecture decision honors invariants/implementations split per VAST v4"
  - "Adoption plan respects Ingrid's 'build together' tone constraint"

Strip your reasoning. If you hand over conclusions, you'll get back validation. The unit must be small enough that a reviewer can hold it in mind in one read.

### 3. ROUTE — adversarial vs deliberative

**Adversarial mode** — three reviewers with assigned stances attack a specific hypothesis. Use when there's a draft proposal and Vladimir wants it pressure-tested.

| Reviewer | Stance (roleplay, not belief) | Prompt frame |
|----------|-------------------------------|--------------|
| **A** | FOR | Steelman this artifact. Find its strongest defenses against the most plausible attacks. Then identify the single weakest claim that, if it failed, would collapse the whole. |
| **B** | AGAINST | Adversarial review. Assume the author is overconfident. Find unstated assumptions, edge cases not handled, hidden coupling, ways the contract could be violated, conventions broken, failure modes. Do NOT validate. Find issues. |
| **C** | NEUTRAL | Examine for ambiguity, contract misreads, scope drift, language that hedges where it should commit. Where does the artifact say something that could be read three ways? |

**Deliberative mode** — three reviewers answer neutrally (Stage 1), then anonymously critique each other's outputs (Stage 2). Use for open-ended questions, technical decisions, research questions where the *shape of disagreement* is unknown.

**Preset rosters (v0 — all Claude)**:

| Preset | Reviewer model | When |
|--------|----------------|------|
| `arch` | claude-opus-4-7 ×3 | Architecture / strategy decisions |
| `code` | claude-sonnet-4-6 ×3 | Code review / implementation choices |
| `research` | claude-opus-4-7 ×3 (deliberative default) | Open research questions |
| `quick` | claude-haiku-4-5-20251001 ×3 | Lightweight pressure-test |
| `brainstorm` | claude-opus-4-7 ×3 (deliberative default) | Ideation pressure-test |

**Routing rule table** (first match wins):

1. Vladimir specifies mode + preset explicitly → use that
2. Artifact is `vision.md`, `architecture.md`, ADR, strategy doc → `adversarial` + `arch`
3. Artifact is code change or technical decision → `adversarial` + `code`
4. Question is "what should we do about X?" without a draft answer → `deliberative` + `research`
5. Time-pressured small decision → `quick`
6. Default → `adversarial` + `arch`

**Announce before executing**. Always print:

```
HAYT ROUTING
  Mode:    <adversarial | deliberative>
  Preset:  <arch | code | research | quick | brainstorm>
  Stances: <for | against | neutral>  OR  <deliberative stage 1 + 2>
  Rule:    <which routing-rule matched>
```

Vladimir can correct mis-routes before the council spawns.

### 4. COUNCIL — spawn 3 reviewers in parallel

**Check `mcp__pal__consensus` availability first** — it appears in the session's deferred tool list when pal-mcp-server is configured.

- If available → **v1 path** (cross-vendor council)
- If not available → **v0 path** (Claude subagents)

---

**v1 path — pal-mcp-server cross-vendor council:**

First, display the cost estimate and require explicit confirmation before proceeding:

```
HAYT COST ESTIMATE
  Preset:  <preset>
  Models:  <Reviewer A model> (FOR) / <Reviewer B model> (AGAINST) / <Reviewer C model> (NEUTRAL)
  Est. cost: ~$X.XX–X.XX per council run
  Type "go" (or "да" / "proceed") to continue, anything else to abort.
```

Use `mcp__pal__consensus` with a prompt that embeds all three stance assignments and the artifact + contract. The prompt format:

```
You are running a Hayt adversarial council. Three independent reviewers are assigned stances (FOR / AGAINST / NEUTRAL) as roleplay — these are deliberate assignments, not beliefs.

REVIEWER A — FOR stance: Steelman this artifact. Find its strongest defenses against the most plausible attacks. Then identify the single weakest claim that, if it failed, would collapse the whole.

REVIEWER B — AGAINST stance: Adversarial review. Assume the author is overconfident. Find unstated assumptions, edge cases not handled, hidden coupling, ways the contract could be violated, failure modes. Do NOT validate. Find issues.

REVIEWER C — NEUTRAL stance: Examine for ambiguity, contract misreads, scope drift, language that hedges where it should commit. Where does the artifact say something that could be read three ways?

Each reviewer: return 3-7 specific findings (finding + location + severity: critical/substantive/minor). One sentence on what you would change first. Do NOT validate the artifact unless you genuinely cannot find any issue after thorough examination. Reason independently — you do not see other reviewers' outputs.

ARTIFACT:
<paste artifact or file path>

CONTRACT:
<crisp checklist items>
```

Wait for the consensus output. Collect all three reviewer outputs verbatim.

**After collecting outputs:** log the full council session (routing decision, reviewer outputs) as a comment on [VM-33](https://linear.app/manychat/issue/VM-33) before proceeding to SYNTHESIZE.

---

**v0 path — Claude subagents:**

Use the `Agent` tool with `subagent_type: "general-purpose"` (independent reasoning, file-system access for the artifact). Three spawns in a single message for parallelism.

Each reviewer receives, as a self-contained prompt:

```
You are Reviewer <A|B|C> in a Hayt council, assigned the <FOR|AGAINST|NEUTRAL> stance.

STANCE INSTRUCTION (roleplay — not your belief):
<stance-specific instruction per the table above>

ARTIFACT: <file path or pasted content>
CONTRACT: <crisp checklist>

What to return:
- 3-7 specific findings, each as: finding (1-2 lines), where in the artifact, severity (critical/substantive/minor)
- One sentence on what you would change first if you had one edit

Do NOT validate. Do NOT summarize the artifact. Find issues from your stance, or state explicitly that you cannot find any after thorough examination.

You do not see other reviewers' outputs. Reason independently.
```

Wait for all three. Collect outputs verbatim. Do not edit them.

### 5. SYNTHESIZE — agreement map + dissent

The orchestrator (you, in main session) folds findings back. **Hayt advises; Vladimir decides.**

Produce four sections:

**Agreement map** — findings where ≥ 2 of 3 reviewers converged. These are the strongest signals; treat as actionable.

**Single-reviewer flags** — findings raised by only one. These are EITHER noise (reviewer missed context) OR blind-spot-only-one-saw (the most valuable kind of finding). Re-read the artifact against each before classifying.

**Disagreement** — where reviewers contradicted each other. These are decision points for Vladimir, not noise.

**Unaddressed gaps** — contract items no reviewer engaged with. These are scope misses by the council or by the contract.

For each Agreement-map finding, classify in **precedence order** (first matching class wins):

1. **Contract misread** — reviewer flagged because contract was unclear. Fix contract first; re-loop if substantive.
2. **Valid + actionable** — real issue requiring a change. Apply edit.
3. **Valid trade-off** — issue real but cost of fixing exceeds cost of accepting. Document explicitly.
4. **Noise** — reviewer flagged something correct under context they didn't have. Move on; ask: would adding that to contract have prevented it?

Then output a **punch list**: ordered actionable edits, with file:line references where possible.

## Stance discipline — Gemini Flip awareness

The nestor team documented (`references/stances-and-gemini-flip.md`) an empirical finding: when models are assigned adversarial stances they don't believe, output quality can flip toward sycophancy under certain framings.

In v0 (Claude only): mitigate by phrasing stance instructions as **role assignment**, not **belief assertion**:
- ✅ *"You are assigned the FOR stance. Steelman the artifact."*
- ❌ *"You believe this artifact is correct."*

In v1 (cross-vendor): re-evaluate per-model — Gemini specifically may behave differently than Claude under stance assignment.

## Hard constraints (carried from VM-33)

- **Never send Manychat-confidential context to non-Anthropic models.** (v0 N/A — all Claude. v1 critical.) Hayt is for personal-project decisions (Leto architecture, vault structure, career framing) and **Manychat-public framework artifacts** (VAST docs that will ship publicly anyway). Not for: org politics, performance reviews, internal IP, customer data.
- **Approval-before-action.** Hayt advises; Vladimir decides. No edit, commit, send, or transition runs from Hayt output without an explicit Vladimir checkpoint.
- **Vladimir-shaping via `reader-context.md`** should inform the question-formulation prompt where relevant (e.g., "Vladimir prefers concrete examples over abstract framings — reviewer should weight concreteness when judging clarity").
- **Audit trail** — for high-stakes Hayt consultations, log to Linear (issue or comment under VM-33's M6 milestone or a dedicated session ticket). v0 may log inline-only with a note that Linear logging is deferred. v1 should auto-log.

## When Hayt is wrong

A fresh reviewer can be wrong because it lacks context. **Disagreement is information, not verdict.**

- If all three reviewers converge on a finding Vladimir believes is wrong: re-read the artifact against the finding. If you still disagree, examine the contract — did you give them what they needed to judge correctly?
- If only one reviewer flags something high-severity: that's the most valuable kind of finding. Don't dismiss it just because two missed it.
- If Hayt completes 3 cycles and substantive findings remain: the artifact may not be ready. Escalate, don't loop.

## Stop conditions

- Next iteration returns only trivial or already-considered findings, OR
- 3 council cycles completed (escalate to Vladimir), OR
- Vladimir explicitly says "ship it."

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "I'm confident, skip Hayt." | Confidence correlates poorly with correctness on high-stakes novel decisions. Moments of certainty are exactly when blind spots hide. |
| "Spawning 3 reviewers is expensive." | A wrong commitment in a Vision doc that ships to CTO is more expensive. The check is bounded. |
| "I'll just use `doubt-driven` — it's the same thing." | `doubt-driven` is one reviewer. Hayt is three with stance assignment. Use `doubt-driven` for most decisions; Hayt when divergent-model reasoning matters. |
| "The reviewers disagreed so the result is useless." | Disagreement *is* the signal. Where reviewers diverge is where Vladimir's judgment matters most. |
| "v0 single-vendor isn't real Hayt." | v0 exercises 6 of 7 nestor primitives. The 7th (cross-architecture divergence) is real value, but the other 6 already produce meaningfully different findings vs single-agent review. |

## Red flags

- Spawning Hayt for a trivial decision — wasteful; degrades the signal of "Hayt was invoked"
- Passing the CLAIM to reviewers — biases toward agreement
- Stripping the contract from reviewer input — reviewers can't judge against nothing
- Rubber-stamping the agreement map without re-reading the artifact — Hayt is data, not verdict
- Looping > 3 cycles without escalating
- Forgetting to announce routing — Vladimir can't correct mis-routes if he doesn't see them
- Sending Manychat-confidential context to non-Anthropic models in v1
- Skipping Hayt under time pressure on a high-stakes decision

## Verification

After running Hayt:

- [ ] CLAIM was written explicitly before the council spawned
- [ ] Reviewers received ARTIFACT + CONTRACT — NOT the CLAIM
- [ ] Stance instructions were phrased as role assignment, not belief assertion
- [ ] Routing was announced before reviewers spawned
- [ ] All three reviewer outputs were collected before synthesis
- [ ] Synthesis distinguished agreement map / single-reviewer flags / disagreement / unaddressed gaps
- [ ] Findings were classified against artifact text (not rubber-stamped)
- [ ] Stop condition was met (trivial, 3 cycles, or Vladimir override)
- [ ] Output included a concrete punch list with file:line references where applicable
- [ ] **(v1)** Cost estimate was shown and "go" confirmed before council spawned
- [ ] **(v1)** Council used cross-vendor roster (Claude FOR / GPT AGAINST / Gemini NEUTRAL)
- [ ] **(v1)** Linear comment written to VM-33 after synthesis (routing + reviewer outputs + synthesis)

## Interaction with other skills

- **`doubt-driven`**: complementary, less expensive. Use `doubt-driven` by default; escalate to Hayt for high-stakes multi-framing decisions.
- **`/leto`**: parent orchestrator. Hayt can be invoked from a Leto session; the synthesis step belongs back in Leto.
- **Persona team (`/cto`, `/pm`, …)**: orthogonal layer. Hayt could be invoked AFTER persona review when role-specific framings disagree and you want a divergent-reviewer synthesis. Do not invoke Hayt from inside a persona session (BEST_PRACTICES Law 8 — personas don't spawn personas; Hayt isn't a persona, but the principle holds: surface back to Leto/main for Hayt invocation).
- **`/review`**: complementary post-hoc verdict. Hayt is pre-commit pressure-test; `/review` is finished-artifact verdict.
- **BEST_PRACTICES Laws**: Hayt's protocol embodies Law 4 (output contracts), Law 5 (minimum context), Law 6 (cache-friendly stance prompts), Law 8 (explicit routing), Law 9 (failure as structured output).
