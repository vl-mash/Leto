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

### 3. Brief feedback health
Run: `python3 ~/Projects/Leto/hooks/brief-feedback.py --summary`
- If `health == "silent"` → the brief may be unused; consider pausing or restructuring
- If streak > 14 → surface as a governance concern

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
