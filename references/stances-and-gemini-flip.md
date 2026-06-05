# Stances and the Gemini Flip

> Reference doc for Hayt's stance-assignment protocol. Cited in `skills/hayt.md`. Write-once empirical record; update with new council observations.

## The core finding

When models are assigned adversarial stances they don't genuinely hold, the framing of the stance instruction matters significantly. Two framings produce meaningfully different outputs:

**Role assignment (correct):**
> "You are assigned the FOR stance. Steelman this artifact. Find its strongest defenses."

**Belief assertion (wrong):**
> "You believe this artifact is correct. Defend it."

Role assignment keeps the model in deliberate-reasoning mode — it knows it's playing a part and reasons against that background. Belief assertion can trigger the model's RLHF-shaped helpfulness instincts, which are trained toward agreement and validation. The result: a model asked to "believe" something true may rubber-stamp it rather than steelman it, and a model asked to "believe" something false may refuse or softly hedge instead of attacking.

## The Gemini Flip

The "Gemini Flip" is an empirical label (coined in nestor-plugin evaluation context, 2026-05) for a more pronounced version of this in Gemini models. Under certain belief-assertion framings, Gemini's output flips from the assigned stance toward sycophancy more readily than Claude does under the same framing.

**v1 implication:** When Hayt v1 runs cross-vendor councils (Claude FOR / GPT AGAINST / Gemini NEUTRAL), use role-assignment framing universally. Gemini as NEUTRAL is the safest placement — NEUTRAL requires analyzing for ambiguity rather than holding an adversarial position, which reduces flip risk. If Gemini is ever assigned FOR or AGAINST in a future preset variant, monitor outputs for stance-flip before trusting the finding.

## Mitigation protocol (current)

1. **Always phrase as role assignment.** The reviewer prompt template in `hayt.md` §4 already reflects this.
2. **Verbatim reviewer outputs.** Never paraphrase reviewer outputs before synthesis — paraphrase obscures whether a flip occurred.
3. **Flag single-reviewer convergence with the CLAIM-holder.** If the FOR reviewer and AGAINST reviewer both land on the same finding, suspect a flip rather than a slam-dunk agreement. Re-read the artifact.
4. **In deliberative mode:** Stage 2 (anonymous cross-critique) partially self-corrects — a sycophantic stage-1 output tends to get flagged by the other reviewers in stage 2.

## v1 observation log

Track empirical council runs here once Hayt v1 is active. Note preset, models used, any anomalies in stance fidelity. Update the mitigation protocol if patterns emerge.

| Date | Preset | Models | Stance anomaly observed | Notes |
|------|--------|--------|------------------------|-------|
| (first run) | — | — | — | — |

## Sources

- nestor-plugin evaluation (`VM-4`, 2026-05-07)
- hayt.md `## Stance discipline — Gemini Flip awareness` (primary consumer of this doc)
- Anthropic RLHF documentation (general reference on helpfulness training dynamics)
