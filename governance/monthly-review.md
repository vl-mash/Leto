# Monthly Governance Review — Protocol

Runs on the first Friday of each month as part of `leto-weekly-review` (it's
a `PART D2 — Monthly Synthesis` extension, added as a review step).

## What gets reviewed

### 1. Standing approvals health
Run: `python3 ~/Projects/Leto/hooks/standing-approvals.py --status`

For each SA:
- **Expired** → must be explicitly re-affirmed or removed before next use
- **Review needed** (30d since last review) → update `reviewed=YYYY-MM-DD` in the `<!-- sa:... -->` marker
- **Fire count = 0** → consider whether it's still needed; if not, move to Expired section
- **Fire count high** → confirm scope is still appropriate

### 2. Hard exclusions list
Read `governance/hard-exclusions.md`. Verify:
- Are all listed HR-shaped people still in their roles? (Org changes happen)
- Any new stakeholders that should be added?
- Cross-check against `~/.claude/.../memory/user_*.md` files for role changes

### 3. Credential + blocker health  _(replaced brief-feedback, retired 2026-09-21)_
Run: `python3 ~/Projects/Leto/hooks/leto_secrets.py --check`
- Any secret not `ok` → rotate it; a credential file existing proves nothing (the Linear
  key returned 401 for 23 days while its file sat happily in place)

Then read `~/Projects/Leto/.local-data/blocker-state.json`:
- Any cause at tier ≥ 3 → a routine is degrading or standing itself down; surface it
- Any cause with `days` > 10 → it has been unactionable for two working weeks

This replaces brief-reaction health, which measured whether Vladimir reacted rather than
whether the routine worked. Structural signals only — see
`feedback_scheduled_output_shape.md`.

### 4. Learning loop health
Run: `python3 ~/Projects/Leto/hooks/learning-loop.py --stats`
- Review approval rates; if Section B approval rate < 30% → the EOD is over-proposing
- Review suppress list; if patterns seem wrong → prune with `--threshold` adjustment
- Confirm SA-002 fire count is consistent with the approval rate

## What the review produces

A `## Monthly Governance — <Month YYYY>` block appended to the weekly note, containing:
- SA status table (active / expired / review-needed counts)
- Hard-exclusions changes if any
- Brief health summary
- Learning loop stats
- Action items for next month

## Who does this

Leto runs the data collection automatically on the first Friday. Vladimir reviews the
block in the weekly note and confirms (or makes changes) with a session or Slack reply.
The review is advisory — Leto surfaces findings, Vladimir decides.

## Re-affirming a standing approval

In `Standing Approvals.md`, update the `<!-- sa:... -->` marker:
- Change `expires=YYYY-MM-DD` to new expiry (today + 90d)
- Change `reviewed=YYYY-MM-DD` to today

Then run `python3 ~/Projects/Leto/hooks/standing-approvals.py --status` to confirm.
