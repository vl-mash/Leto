# Anti-rationalization tables

Every persona should include a table of common excuses for skipping its discipline, paired with the rebuttal. Captures the failure mode in writing so future-Vladimir (and future-Claude) can see the excuse coming and decline to make it.

**Pattern source:** Addy Osmani's [agent-skills](https://github.com/addyosmani/agent-skills) (MIT). See `00 Inbox/Sources/2026-05-12-addyosmani-agent-skills.source.md` in the vault for the capture and decision log.

## Format

A section called `## Common rationalizations` near the bottom of the persona file (between the persona's core content and its anti-patterns / interaction-with-other-skills sections). Two-column Markdown table:

```markdown
## Common rationalizations

| Rationalization | Reality |
|---|---|
| "<excuse — written in the voice of someone about to skip the discipline>" | <rebuttal — short, sharp, evidence- or principle-based> |
```

The excuse goes in quotes (it's a thing someone might say); the rebuttal does not.

## When a row earns its place

A row earns inclusion when **all three** are true:

1. **Plausibility.** The excuse is one Vladimir or a future agent will plausibly make under time pressure or low confidence. If no one would actually say it, it doesn't belong.
2. **Concrete consequence.** The rebuttal points to a specific bad outcome the skip causes (regression, lost trust, technical debt, political blowback, audit-trail gap). Not moralizing.
3. **Persona-grounded rebuttal.** The rebuttal flows from the persona's framework or from a specific empirical claim — not from generic platitudes. A Carmack rationalization should sound like Carmack disagreeing; a Shreyas rationalization should sound like Shreyas.

A row does **not** earn its place if it is:

- A generic platitude ("measure twice, cut once").
- A re-statement of the discipline ("don't skip tests" is the rule, not the rationalization for skipping it).
- A snowflake case unlikely to recur.
- An excuse the persona's existing "anti-patterns" or "red flags" section already covers from the inverse angle.

## When to add rationalizations to a persona

- When promoting a new persona to the team — add a starter row or three based on the most likely failure modes.
- When a real session ended in "we should have done X but didn't" — add the rationalization that justified the skip, with the consequence as the rebuttal. This is the highest-signal source for new rows.
- When reviewing personas during the bi-weekly agent-discovery ritual (BEST_PRACTICES Law 11) — add any patterns observed ≥ 2 times.

Rows should rarely be removed. An outdated rationalization is still useful as a historical marker; only delete if the rebuttal has become factually wrong.

## When to add a rationalizations section to a skill

Skills (not just personas) can also carry rationalizations tables when they encode a discipline that has known shortcuts. `skills/doubt-driven.md` does this — the discipline is "stop and verify"; the rationalizations are excuses for not stopping.

## Existing examples

- `personas/engineering/engineer-carmack.md` — engineering discipline rationalizations (the proof-of-concept; first persona to receive this pattern, 2026-05-12).
- `skills/doubt-driven.md` — doubt-cycle rationalizations.

## Relationship to other persona sections

| Section | Purpose | Voice |
|---|---|---|
| `Anti-patterns you call out` | Bad code/design patterns the persona spots in *others' work* | "When I see X, I push back because Y." |
| `Red flags` | Behavioral signals that a discipline is being skipped | Observable signs ("doubting only after commit") |
| `Common rationalizations` | Excuses for *self*-skipping the discipline, with rebuttals | First-person voice of the excuse; consequence-based rebuttal |

These three serve different purposes and should not collapse into each other. Anti-patterns face outward; rationalizations face inward.
