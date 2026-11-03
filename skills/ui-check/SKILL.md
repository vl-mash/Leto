---
name: ui-check
description: Review a UI as a world-class designer would, in Claude's own browser pane, before Vladimir sees it. Opens the page at desktop and phone widths in light and dark, checks states, console errors, ManySystem tokens, accessibility basics, the 5-second test, and runs a slop pass for patterns that make a UI look AI-made. Returns screenshots and a numbered fix list. Use after any UI change, before a merge (`/ship` calls it), or when asked "check the UI", "does this look right", "is this AI-looking".
---

# ui-check

The bar is a product that looks hand-crafted and world-class (Linear, Stripe, Vercel), not "AI-made". Claude checks it in the browser pane itself; Vladimir is never the tester.

## Input

A URL (local server or live) and, if known, what changed (diff, screen name). No URL: find the dev server in the project's `.claude/launch.json` or `CLAUDE.md` and start it with `preview_start`.

## Steps

1. **Open** the page in the built-in browser pane (`preview_start` with `url`, or by `name`). Load the `anthropic-skills:built-in-browser` skill first if it isn't loaded this session.
2. **Capture the changed screen four ways**: desktop and `resize_window` preset `mobile` (375px), each in `colorScheme` light and dark. Then `read_console_messages` with `onlyErrors`.
3. **States.** Reach the empty, loading and error states where the UI allows (a filter with no results, a missing field, long text, zero data). A state that can't be reached is a finding only if users will hit it.
4. **Purpose.** Write the 5-second test as one line: "A first-time viewer notices X, understands Y, is unsure about Z." Name the one primary action. If there isn't one, that's the top finding.
5. **Tokens** (Manychat-facing work). Compare computed colours and fonts (`javascript_tool`, `getComputedStyle` on body, headings, primary button, borders) with `~/Projects/Manychat-DS/tokens.css`. Off-palette values are findings.
6. **Basics.** Text contrast WCAG AA, visible focus states, 44px tap targets on mobile, no horizontal scroll at 375px.
7. **Slop pass.** Go through `slop-patterns.md` in this folder. Each hit gets its pattern ID, where it is, and the hand-crafted fix from the list.
8. **Charts.** If the page has any, apply the `dataviz` skill's rules.
9. Reset the viewport: `resize_window` preset `desktop`.

## Output

```
ui-check: <page> — Ship | Fix first
5-second test: <one line>

Fix list (most impact first)
1. <what> · <where> · <why it matters> · fix: <specific change>
...

Slop hits
- S<id> <pattern> · <where> · fix: <hand-crafted alternative>
(or "None found.")

Screenshots: <desktop light, desktop dark, mobile light, mobile dark>
```

No praise padding and no "overall looks great". If it's clean, say "Ship" and list nothing.

## Rules

- Review only. Edit code only when Vladimir says to fix.
- Never sign in with real credentials (see the browser skill's test-credential rules).
- **The list learns.** When Vladimir rejects something as AI-looking or generic, add it to `slop-patterns.md` in the same session (pattern · why it reads as AI · what hand-crafted does instead), so he never has to flag it twice.
