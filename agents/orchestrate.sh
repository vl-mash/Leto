#!/usr/bin/env bash
# Orchestrator — routes a question to 2-3 relevant specialists, fans out in parallel, synthesizes
#
# Usage:
#   ./agents/orchestrate.sh "<question>"
#   ask --multi "<question>"
#
# Examples:
#   ./agents/orchestrate.sh "should we add SSO before our enterprise launch?"
#   ./agents/orchestrate.sh "we're seeing 40% drop-off on step 2 of onboarding, what do we fix?"
#   ask --multi "is our current auth setup safe enough for GDPR?"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERSONAS_DIR="$SCRIPT_DIR/../personas"

QUESTION="${1:-}"

if [ -z "$QUESTION" ]; then
  echo "Usage: ./agents/orchestrate.sh \"<question>\""
  echo "  or:  ask --multi \"<question>\""
  exit 1
fi

# ── Step 1: Route ──────────────────────────────────────────────────────────────
# Explicit domain boundaries per Law #8 — no ambiguity, no overlap.

ROUTING_PROMPT='You are a routing agent. Given a question, output a JSON array of 2-3 agent names.
Output ONLY a valid JSON array — no markdown, no explanation, no trailing text.

Agent domains (mutually exclusive — pick the best fit, not all that could apply):
- "pm"          → product strategy, prioritization, user needs, build-vs-buy decisions, OKRs, roadmap, feature scoping
- "cto"         → system architecture, tech stack choice, scalability, tech debt, ADRs, infrastructure
- "engineer"    → implementation, code correctness, algorithms, performance, debugging, code review
- "qa"          → test strategy, edge cases, reliability, regression, quality risks
- "designer"    → UX flows, onboarding, information architecture, UI decisions, empty states, clarity
- "security"    → auth, vulnerabilities, data protection, compliance, threat modeling, OWASP
- "analytics"   → metrics, tracking plan, A/B testing, funnels, cohort analysis, North Star metric
- "growth"      → acquisition, retention, referral, virality, growth loops, channel-product fit
- "product-ops" → execution friction, delivery ops, cross-team coordination, planning process, stakeholder management

Rules:
- Select exactly 2 agents for focused questions, 3 for genuinely cross-domain ones
- Never select more than 3
- Prefer specificity — if "cto" and "engineer" both fit, pick the one whose domain is more relevant

Question: '"$QUESTION"'

Output (JSON array only):'

echo "Routing question to specialists..."
AGENTS_JSON=$(claude -p "$ROUTING_PROMPT" 2>/dev/null | tr -d '\n' | grep -o '\[.*\]' || true)

if [ -z "$AGENTS_JSON" ]; then
  echo "Error: routing failed — could not determine relevant agents."
  echo "Try rephrasing your question or invoke a specific agent directly."
  exit 1
fi

# Parse JSON array → space-separated agent list
AGENTS=$(echo "$AGENTS_JSON" | python3 -c "
import sys, json
try:
    agents = json.load(sys.stdin)
    valid = {'pm','cto','engineer','qa','designer','security','analytics','growth','product-ops'}
    filtered = [a for a in agents if a in valid]
    print(' '.join(filtered))
except Exception as e:
    print('')
" 2>/dev/null)

if [ -z "$AGENTS" ]; then
  echo "Error: routing returned invalid agent names. Raw: $AGENTS_JSON"
  exit 1
fi

echo "Consulting: $(echo "$AGENTS" | tr ' ' ', ')"
echo ""

# ── Step 2: Fan out in parallel ────────────────────────────────────────────────

declare -A TMPFILES
declare -A PIDS

for AGENT in $AGENTS; do
  case "$AGENT" in
    qa)          PERSONA="$PERSONAS_DIR/lite/qa.md" ;;
    pm)          PERSONA="$PERSONAS_DIR/lite/pm.md" ;;
    designer)    PERSONA="$PERSONAS_DIR/lite/designer.md" ;;
    cto)         PERSONA="$PERSONAS_DIR/lite/cto.md" ;;
    engineer)    PERSONA="$PERSONAS_DIR/lite/engineer.md" ;;
    security)    PERSONA="$PERSONAS_DIR/lite/security.md" ;;
    analytics)   PERSONA="$PERSONAS_DIR/lite/analytics.md" ;;
    growth)      PERSONA="$PERSONAS_DIR/lite/growth.md" ;;
    product-ops) PERSONA="$PERSONAS_DIR/product-ops.md" ;;
    *) echo "Warning: unknown agent '$AGENT', skipping." >&2; continue ;;
  esac

  if [ ! -f "$PERSONA" ]; then
    echo "Warning: persona file not found for '$AGENT', skipping." >&2
    continue
  fi

  TMPFILE=$(mktemp /tmp/orchestrate_XXXXXX)
  TMPFILES[$AGENT]=$TMPFILE
  claude -p --system-prompt "$(cat "$PERSONA")" "$QUESTION" > "$TMPFILE" 2>&1 &
  PIDS[$AGENT]=$!
done

# Wait for all specialist calls
for AGENT in "${!PIDS[@]}"; do
  wait "${PIDS[$AGENT]}" || true
done

# ── Step 3: Validate outputs ───────────────────────────────────────────────────

COMBINED=""
MISSING_AGENTS=""

for AGENT in $AGENTS; do
  TMPFILE="${TMPFILES[$AGENT]:-}"
  if [ -z "$TMPFILE" ] || [ ! -f "$TMPFILE" ]; then
    MISSING_AGENTS="$MISSING_AGENTS $AGENT"
    continue
  fi
  OUTPUT=$(cat "$TMPFILE")
  rm -f "$TMPFILE"

  if [ -z "$OUTPUT" ]; then
    MISSING_AGENTS="$MISSING_AGENTS $AGENT"
    continue
  fi

  COMBINED="$COMBINED

=== $AGENT ===
$OUTPUT"
done

if [ -z "$COMBINED" ]; then
  echo "Error: all specialist calls returned empty. Check your Claude Code auth."
  exit 1
fi

if [ -n "$MISSING_AGENTS" ]; then
  echo "Warning: no response from:$MISSING_AGENTS (proceeding with remaining specialists)"
  echo ""
fi

# ── Step 4: Synthesize ─────────────────────────────────────────────────────────

SYNTHESIS_PROMPT="You are synthesizing advice from multiple specialist advisors on one question.

Question: $QUESTION

Specialist responses:
$COMBINED

Write a concise synthesis in this exact structure:

**Recommendation**
The clearest action to take, 2-3 sentences max.

**Key tensions**
Where specialists disagreed or pulled in different directions. If they agreed, say so and why that convergence matters. 1-3 bullets.

**Per-specialist take**
One sentence per advisor, attributed by role name. Preserve their distinct perspective — don't blend them into generic advice."

echo "Synthesizing..."
echo "────────────────────────────────────────"
echo ""
claude -p "$SYNTHESIS_PROMPT"
