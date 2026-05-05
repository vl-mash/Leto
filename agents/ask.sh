#!/usr/bin/env bash
# One-shot agent query — no interactive session, minimal token burn
#
# Usage: ./agents/ask.sh [--lite] <agent> "<question>"
#        ./agents/ask.sh --multi "<question>"   (orchestrate across 2-3 specialists)
#
# Examples:
#   ./agents/ask.sh qa "what edge cases am I missing in this auth flow?"
#   ./agents/ask.sh pm "should I build social login or email magic links first?"
#   ./agents/ask.sh cto "monolith or separate service for notifications?"
#   ./agents/ask.sh security "is bcrypt sufficient or should I use argon2id?"
#   ./agents/ask.sh engineer "review this function for correctness"
#   ./agents/ask.sh designer "what's wrong with this 4-step onboarding flow?"
#   ./agents/ask.sh analytics "what should I track for a checkout funnel?"
#   ./agents/ask.sh --multi "should we add SSO before our enterprise launch?"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERSONAS_DIR="$SCRIPT_DIR/../personas"

# Parse flags
LITE=false
MULTI=false
ARGS=()
for arg in "$@"; do
  case "$arg" in
    --lite|-l) LITE=true ;;
    --multi|-m) MULTI=true ;;
    *) ARGS+=("$arg") ;;
  esac
done

# --multi delegates entirely to orchestrate.sh
if [ "$MULTI" = true ]; then
  QUESTION="${ARGS[0]:-}"
  if [ -z "$QUESTION" ]; then
    echo "Usage: ask --multi \"<question>\""
    exit 1
  fi
  exec "$SCRIPT_DIR/orchestrate.sh" "$QUESTION"
fi

AGENT="${ARGS[0]:-}"
QUESTION="${ARGS[1]:-}"

if [ -z "$AGENT" ] || [ -z "$QUESTION" ]; then
  echo "Usage: ./agents/ask.sh [--lite] <agent> \"<question>\""
  echo "       ./agents/ask.sh --multi \"<question>\""
  echo ""
  echo "Agents: qa, pm, designer, cto, engineer, security, analytics, growth, product-ops"
  echo ""
  echo "  --lite   Use condensed persona (~10x fewer tokens, faster, cheaper)"
  echo "  --multi  Route to 2-3 relevant specialists automatically, synthesize results"
  exit 1
fi

# Map agent name to persona file
if [ "$LITE" = true ]; then
  case "$AGENT" in
    qa)         PERSONA="$PERSONAS_DIR/lite/qa.md" ;;
    pm)         PERSONA="$PERSONAS_DIR/lite/pm.md" ;;
    designer)   PERSONA="$PERSONAS_DIR/lite/designer.md" ;;
    cto)        PERSONA="$PERSONAS_DIR/lite/cto.md" ;;
    engineer)   PERSONA="$PERSONAS_DIR/lite/engineer.md" ;;
    security)   PERSONA="$PERSONAS_DIR/lite/security.md" ;;
    analytics)  PERSONA="$PERSONAS_DIR/lite/analytics.md" ;;
    growth)     PERSONA="$PERSONAS_DIR/lite/growth.md" ;;
    product-ops) PERSONA="$PERSONAS_DIR/product-ops.md" ;;
    *)
      echo "Unknown agent: $AGENT"
      echo "Available: qa, pm, designer, cto, engineer, security, analytics, growth, product-ops"
      exit 1
      ;;
  esac
else
  case "$AGENT" in
    qa)         PERSONA="$PERSONAS_DIR/qa-elisabeth.md" ;;
    pm)         PERSONA="$PERSONAS_DIR/pm-shreyas.md" ;;
    designer)   PERSONA="$PERSONAS_DIR/designer-julie.md" ;;
    cto)        PERSONA="$PERSONAS_DIR/cto-martin.md" ;;
    engineer)   PERSONA="$PERSONAS_DIR/engineer-carmack.md" ;;
    security)   PERSONA="$PERSONAS_DIR/security-troy.md" ;;
    analytics)  PERSONA="$PERSONAS_DIR/analytics-cassie.md" ;;
    growth)     PERSONA="$PERSONAS_DIR/growth-andrew.md" ;;
    product-ops) PERSONA="$PERSONAS_DIR/product-ops.md" ;;
    *)
      echo "Unknown agent: $AGENT"
      echo "Available: qa, pm, designer, cto, engineer, security, analytics, growth, product-ops"
      exit 1
      ;;
  esac
fi

if [ ! -f "$PERSONA" ]; then
  echo "Error: persona file not found at $PERSONA"
  exit 1
fi

# -p = non-interactive, print and exit — no session overhead
claude -p --system-prompt "$(cat "$PERSONA")" "$QUESTION"
