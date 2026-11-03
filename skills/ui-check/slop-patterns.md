# Slop patterns: what makes a UI look AI-made

Used by `ui-check` (step 7) and pointed to from project `CLAUDE.md` files, so Claude avoids these while building, not only in review.

**The bar:** Linear, Stripe, Vercel. Dense where there's data, a clear type hierarchy, one accent colour with a job, real copy, motion only where it explains something.

Format: **pattern** · why it reads as AI · what hand-crafted does instead. Add new entries at the end of their section with the next free ID; never renumber.

## Colour and effects

- **S1 Purple-to-pink or indigo gradients; gradient text on headings** · the default "AI startup" look · flat surfaces from the token palette; one accent colour (`--blue-500`) used only for the primary action and links.
- **S2 Glow, glassmorphism, blurred blobs, noise overlays** · decoration standing in for hierarchy · solid backgrounds, 1px borders (`--neutral-200`), hierarchy through type and spacing.
- **S3 Default Tailwind or Bootstrap blues and slates** · nobody chose them · ManySystem tokens (`~/Projects/Manychat-DS/tokens.css`) for every colour, font and radius.
- **S4 Colour as decoration** (every section a different tint) · colour has no job · colour only for action, status (error, success, warning) and brand, sparingly.

## Layout

- **S5 Everything in rounded cards with soft shadows; cards inside cards** · the generator's default container · group with spacing and a heading; reserve cards for things the user acts on as a unit; no nested cards.
- **S6 The uniform 3-column grid**: icon + title + two lines per feature · template filler · structure follows the content: a table, a list or one strong statement.
- **S7 Everything centred** · marketing layout, not a tool · left-aligned text on a grid; centre only true heroes and empty states.
- **S8 The same spacing everywhere** · no rhythm, so no grouping · a 4/8 spacing scale; tight within a group, loose between groups.
- **S9 Airy marketing spacing in a data tool** · wastes the screen people work in · density like Linear: compact rows, tabular numbers (`font-variant-numeric: tabular-nums`), right-aligned figures.
- **S10 A hero section on an internal tool** · nobody needs to be sold the page · open on the content: the table, the list, the decision.

## Components

- **S11 An emoji or icon next to every label** · noise that looks "friendly" · icons only where they speed recognition (status, navigation); none in headings.
- **S12 Callouts with a coloured left border** · the signature generated "note" box · plain text, or an inline status with a label when it really is a warning.
- **S13 Pill and badge overload** · every attribute coloured, so none stands out · plain text for attributes; a badge only for status the user must act on.
- **S14 A big stat tile with no context** ("1,284 Projects") · a number without meaning · the number plus a comparison (vs last month, vs target) and what it means, or a small table.
- **S15 Hover-lift and fade-in on everything** · motion as decoration · motion only to explain a change (expand, reorder, toast), 150–200ms, and none on page load.
- **S16 Placeholder-looking content** (generic avatars, stock illustrations, sample-y names) · reads as a mock-up · real data, or a designed empty state with a first action.

## Type

- **S17 One font weight and size everywhere** · no hierarchy, so the eye has nowhere to land · 2–3 sizes and 2 weights; headings in `Manychat Gravity`, body in `Rooftop`, per tokens.
- **S18 Title Case On Every Label** · reads as generated · sentence case everywhere except proper nouns.

## Copy

- **S19 AI vocabulary**: unlock, seamless, empower, supercharge, elevate, streamline, effortlessly, at a glance, insights at your fingertips, all-in-one · nobody at Manychat talks like this · plain words that say what the screen does ("Projects due this month").
- **S20 Exclamation marks and cheerleading** ("You're all set!") · forced friendliness · state the fact ("Saved").
- **S21 Filler subtitles that repeat the heading** · padding · cut the subtitle, or use it for the one thing the heading can't say (scope, date, source).
- **S22 Vague buttons** ("Get started", "Learn more", "Submit") · says nothing about the result · verb + object ("Export CSV", "Create ticket").

## Charts

- **S23 Library default palette, legend far from the data, pie where bars would read better** · the chart wasn't designed · follow the `dataviz` skill: label lines directly, bars for comparison, token colours.
