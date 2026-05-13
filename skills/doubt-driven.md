# Doubt-Driven Development

A confident answer is not a correct one. Long sessions accumulate context that quietly turns assumptions into "facts." Doubt-driven is the discipline of materializing a fresh-context reviewer — biased to **disprove**, not approve — before any non-trivial decision stands.

This is not `/review`. `/review` is a verdict on a finished artifact. This is an in-flight posture: non-trivial decisions get cross-examined while course-correction is still cheap.

**Origin:** distilled from Addy Osmani's [agent-skills](https://github.com/addyosmani/agent-skills) (MIT) — see `00 Inbox/Sources/2026-05-12-addyosmani-agent-skills.source.md` in the vault for the full upstream version.

## When to use

A decision is **non-trivial** when at least one of these is true:

- Introduces or modifies branching logic.
- Crosses a module / service / data boundary.
- Asserts a property the type system or compiler can't verify (thread safety, idempotence, ordering, invariants).
- Correctness depends on context a future reader can't see.
- Blast radius is irreversible (production deploy, data migration, public API change, sent message, Linear state transition that propagates downstream).

**When NOT to use:** mechanical renames or formatting, following a clear unambiguous instruction, summarizing existing code, one-line changes with obvious correctness, pure tooling operations (running tests, listing files), or when Vladimir has explicitly asked for speed over verification.

If you doubt every keystroke, you ship nothing. The skill applies only to non-trivial decisions as defined above.

## The five steps

```
- [ ] CLAIM     — name the decision + why it matters in ≤ 3 lines
- [ ] EXTRACT   — smallest reviewable unit: artifact + contract, stripped of reasoning
- [ ] DOUBT     — invoke a fresh-context reviewer with an adversarial prompt
- [ ] RECONCILE — classify findings (contract misread / actionable / trade-off / noise)
- [ ] STOP      — trivial findings, 3 cycles, or user override
```

### 1. CLAIM — surface what stands

Two or three lines. The decision plus why-it-matters.

```
CLAIM: "The Linear auto-update flow is safe to run from session-end."
WHY THIS MATTERS: a wrong transition leaves a stale ticket and erodes the audit trail.
```

If you can't write the claim that compactly, you have a vibe, not a decision. Surface it first.

### 2. EXTRACT — smallest reviewable unit

A fresh-context reviewer needs the **artifact** and the **contract**, not the journey.

- Code: the diff or the function — not the whole file.
- Decision: 3–5 sentences plus the constraints it has to satisfy.
- Assertion: the claim plus the evidence supposedly supporting it (kept distinct from the Step-1 CLAIM block, which is the orchestrator's hypothesis under scrutiny).

Strip your reasoning. If you hand over conclusions, you'll get back validation of conclusions. The unit must be small enough that a reviewer can hold it in mind in one read — if it's a 500-line PR, decompose first.

### 3. DOUBT — invoke the fresh-context reviewer

The reviewer's prompt **must be adversarial**. Framing decides the answer.

```
Adversarial review. Find what is wrong with this artifact.
Assume the author is overconfident. Look for:
- Unstated assumptions
- Edge cases not handled
- Hidden coupling or shared state
- Ways the contract could be violated
- Existing conventions this might break
- Failure modes under unexpected input

Do NOT validate. Do NOT summarize. Find issues, or state explicitly
that you cannot find any after thorough examination.

ARTIFACT: <paste artifact>
CONTRACT: <paste contract>
```

**Pass ARTIFACT + CONTRACT only. Do NOT pass the CLAIM.** Handing the reviewer your conclusion biases it toward agreement. The reviewer must independently determine whether the artifact satisfies the contract.

How to spawn the reviewer (in Claude Code):

- **Sub-agent**: `general-purpose` or `Plan` agent in a fresh context, prompt = the adversarial block above. (The role-specific agents like `code-reviewer` are also usable; paste the adversarial prompt verbatim so it overrides their default balanced response shape.)
- **Cross-model** (optional, interactive only): offer Vladimir the choice — *"Single-model review complete. Want a cross-model second opinion? Codex CLI, Gemini CLI, manual external review, or skip?"* Don't silently skip in an interactive cycle; skipping is fine, silent skipping is not. Each external CLI invocation is its own authorization — confirm the exact command + flags with Vladimir before running. Never interpolate the artifact into a shell-quoted argument; pipe via stdin or heredoc.

**Personas do not spawn personas.** Apply this skill from the main Leto session, not from inside a `/cto` or `/engineer` call. (BEST_PRACTICES Law 8 / `conventions/persona-shim.md`.) If you're already inside a persona session, surface back to Leto to run the doubt cycle — or, last resort, run a degraded self-questioning fallback and flag the result as degraded.

### 4. RECONCILE — fold findings back

The reviewer's output is data, not verdict. **You are still the orchestrator.** Re-read the artifact text against each finding before classifying — rubber-stamping the reviewer is the same failure mode as ignoring it.

Classify in this **precedence order** (first matching class wins):

1. **Contract misread** — reviewer flagged something because the CONTRACT you provided was unclear or incomplete. Fix the contract first, re-classify on the next cycle.
2. **Valid + actionable** — real issue requiring a change. Change it, re-loop.
3. **Valid trade-off** — issue is real but cost of fixing exceeds cost of accepting. Document the trade-off explicitly so Vladimir sees it.
4. **Noise** — reviewer flagged something correct under context the reviewer didn't have. Note it, move on, and ask: would adding that context to the contract have prevented the false flag?

A fresh reviewer can be wrong because it lacks context. Don't defer just because it's "fresh."

### 5. STOP — bounded loop, not recursion

Stop when:

- Next iteration returns only trivial or already-considered findings, **or**
- 3 cycles completed (escalate to Vladimir; don't grind a fourth alone), **or**
- Vladimir explicitly says "ship it."

If after 3 cycles the reviewer still surfaces substantive issues, the artifact may not be ready. Surface this — three unresolved cycles is information about the artifact, not a reason to keep looping.

If 3 cycles is "obviously insufficient" because the artifact is large: the artifact is too big — return to Step 2 and decompose. Do not lift the bound.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "I'm confident, skip the doubt step." | Confidence correlates poorly with correctness on novel problems. Moments of certainty are exactly when blind spots hide. |
| "Spawning a reviewer is expensive." | Debugging a wrong commit in production is more expensive. The check is bounded; the bug isn't. |
| "I'll do doubt at the end with `/review`." | `/review` is a final gate. Doubt-driven catches wrong directions early when course-correction is cheap. By PR time it's too late. |
| "If I doubt every step I'll never ship." | The skill applies to non-trivial decisions, not every keystroke. Re-read "When NOT to use." |
| "The reviewer disagreed so I was wrong." | The reviewer lacks your context — disagreement is information, not verdict. Re-read the artifact, classify, then decide. |
| "Cross-model is always better." | Cross-model catches blind spots a single model shares with itself, but it adds cost and tool fragility. Offer it every interactive cycle; let Vladimir decide whether the artifact warrants it. |

## Red flags

- Spawning a fresh-context reviewer for a one-line rename or formatting change.
- Treating reviewer output as authoritative without re-reading the artifact text.
- Looping > 3 cycles without escalating.
- Prompting the reviewer with "is this good?" instead of "find issues."
- Skipping doubt under time pressure on a high-stakes decision.
- Re-spawning fresh-context on an unchanged artifact (you'll get the same findings; you're stalling).
- **Doubt theater (checkable signal):** across 2+ cycles where the reviewer surfaced substantive findings, zero findings were classified as actionable. You are validating, not doubting. Stop and escalate.
- Doubting only after committing — that's `/review`, not doubt-driven.
- Hardcoding an external CLI invocation without confirming the tool exists, is configured, and accepts that exact syntax.
- Silently skipping cross-model in an interactive doubt cycle.
- Stripping the contract from the reviewer's input.
- Passing the CLAIM to the reviewer (biases toward agreement).

## Interaction with other skills

- **`/review`**: complementary. `/review` is post-hoc verdict on a finished artifact; doubt-driven is in-flight per-decision. Use both.
- **`/engineer` (Carmack)**: doubt-driven is the formal version of Carmack's "check your assumptions; the bug is usually in something you were sure was correct." The Step-3 reviewer materializes that check.
- **TDD**: a failing test produced by TDD's RED step satisfies the doubt step for behavioral claims — it's a disproof attempt made concrete.
- **`debugging-and-error-recovery`**: when the reviewer surfaces a real failure mode, drop into scientific-method debugging to localize and fix.
- **BEST_PRACTICES Law 9 (failure as structured output)**: classify findings as structured data (contract-misread / actionable / trade-off / noise), not prose.

## Verification

After applying doubt-driven:

- [ ] Every non-trivial decision was named explicitly as a CLAIM before standing.
- [ ] At least one fresh-context review per non-trivial artifact (a failing TDD test satisfies this for behavioral claims).
- [ ] The reviewer received ARTIFACT + CONTRACT — NOT the CLAIM, NOT your reasoning.
- [ ] The reviewer's prompt was adversarial ("find issues"), not validating ("is it good").
- [ ] Findings were classified against the artifact text (not rubber-stamped) using the precedence: contract misread / actionable / trade-off / noise.
- [ ] A stop condition was met (trivial findings, 3 cycles, or Vladimir override).
- [ ] In interactive mode, cross-model was **explicitly offered** (regardless of artifact stakes) and the response was acknowledged in the output.
- [ ] Any external CLI invocation was preceded by a PATH check, a working-binary test, syntax confirmation, and explicit authorization to run.
