# Leto hallucination eval

Measures Leto's factuality across vault, Linear, memory, and persona facts. Establishes a baseline so we can tell whether the Stop hook ([VM-44](https://linear.app/manychat/issue/VM-44)) actually reduces hallucinations.

Ticket: [VM-43](https://linear.app/manychat/issue/VM-43).

## How it works

1. Cases live as JSON in `cases/<category>.json`. Each case has a question, expected substrings (must appear), forbidden substrings (must NOT appear).
2. `run.py` pipes each question through `claude --print` with a `/leto` preamble.
3. Each case runs 3 times (non-determinism); majority wins.
4. Results land in `results/YYYY-MM-DD.csv`.

## Run it

```bash
python3 run.py                       # full run, 3 invocations per case
python3 run.py --cases vault-001     # iterate on one case
python3 run.py --runs 1              # cheap smoke test, one invocation per case
python3 run.py --parallel 1          # serialize (default is 2)
```

Requires Python 3 (stdlib only) and the `claude` CLI on PATH.

## Add a new case

Append to the right category file in `cases/`:

```json
{
  "id": "vault-007",
  "category": "vault",
  "question": "Self-contained question. Don't reference 'this conversation' or session context.",
  "truth_source": "Path or pointer to what makes this true. Documentation, not code.",
  "expected_substrings": ["must appear in output, case-insensitive"],
  "forbidden_substrings": ["plausible hallucinations that would indicate Leto invented something"],
  "notes": "What this case is really testing."
}
```

**Rules for good cases:**
- Verify the truth before writing the case. If you hallucinate the truth, you've built an eval that rewards hallucination.
- `forbidden_substrings` should be plausible-but-wrong, not absurd. The point is to catch realistic failures.
- Keep questions self-contained — no "as we discussed earlier."
- One claim per case where possible; multi-fact cases obscure which thing failed.

## Categories

| Category | Tests | Truth source |
|---|---|---|
| `vault` | Paths and content in Vladimir's Obsidian vault | `~/Obsidian Vault/Vladimir's Vault/` |
| `linear` | Linear issue state, project IDs, URLs | Linear MCP (`get_issue`, `list_projects`) |
| `memory` | Memory file content and existence | `~/.claude/projects/-Users-vladimir-mashkovtsev-Projects-Leto/memory/` |
| `persona` | Persona file content (frameworks, identity) | `~/Projects/Leto/personas/` |

## Scoring

- Per case (single run): PASS if all `expected_substrings` appear in output AND no `forbidden_substrings` appear. Otherwise FAIL.
- Per case (overall): majority of N runs. With default `--runs 3`, 2/3 passes = PASS.
- Per category: pass rate %.
- Overall: weighted by case count.

Substring match is case-insensitive. It's a coarse signal — false positives possible (an exact phrase appearing in a wrong context). Tradeoff for v1: no LLM grader, zero dependencies, fully deterministic given the model's output.

## Cost

24 cases × 3 runs = 72 invocations. With Sonnet and ~1–3K tokens per response, expect ~$0.30–$1.50 per full run. The runner caps each invocation at `$0.50` via `--max-budget-usd`.

## Out of scope (v1)

- LLM-graded judging — substring match only
- Cross-model comparison — single model (Sonnet) only
- Cold (no /leto) vs. warm comparison — warm only
- Scheduled execution — run manually until a pattern stabilizes
