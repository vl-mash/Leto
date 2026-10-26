# Since-markers and the 7/14/21 escalation ladder

Borrowed verbatim from Dima Kushnikov's [obsidian-seed](https://github.com/dkushnikov/obsidian-seed). One of the elegant primitives of his system — three lines of convention that solve "stale tasks rot silently."

## The marker

Every TODO entry in `_claude/TODO.md` has an HTML comment with the date it was added:

```markdown
- [ ] Sketch out the Q3 product-ops deck <!-- since: 2026-04-30 -->
- [ ] Reply to Anna about the Linear pilot review <!-- since: 2026-04-22 -->
```

## The ladder

When `/leto` runs (or when Vladimir explicitly asks), Leto computes the age of each open TODO and applies escalating treatment:

| Age | Treatment |
|---|---|
| 0–6 days | Silent. No mention unless Vladimir asks. |
| **7–13 days** | **Soft mention** in the next session brief: "FYI, this has been open a week." One line, no pressure. |
| **14–20 days** | **Direct question**: "This has been open two weeks — is it still active? Want to break it down, schedule it, or drop it?" |
| **21+ days** | **Propose disposition**: "This has been open three weeks. Recommend one of: (a) park it explicitly with a reason, (b) schedule a dedicated 30-min session, (c) drop it. Which?" |

## Why this works for Vladimir specifically

From Me.md: "Procrastination root: Low stakes. Not perfectionism, not fear — just insufficient importance signal." The escalation ladder converts time-elapsed into signal. A task that survives 21 days without action either has a real reason (parked) or doesn't belong on the list (dropped). Either resolution is better than silent rot.

The ladder also matches Vladimir's feast-or-famine pattern: famine days don't get nagged on day 1, but persistent neglect across three weeks does get surfaced — because by then the famine is the problem, not the task.

## What the ladder does NOT do

- It does not auto-close TODOs. Disposition requires Vladimir.
- It does not escalate beyond 21 days. After 21 days, Leto continues to surface in the "propose disposition" tier every session until Vladimir resolves it. No nuclear option.
- It does not apply to *active* todos that Vladimir has marked in-progress (`- [/]` in some Markdown flavors) — those are tracked separately.
