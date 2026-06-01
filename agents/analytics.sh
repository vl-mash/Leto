#!/usr/bin/env bash
# Analytics Agent — Cassie Kozyrkov persona
# Usage: ./agents/analytics.sh [optional: task or file]
#
# Examples:
#   ./agents/analytics.sh                                   # open analytics session
#   ./agents/analytics.sh "define metrics for the signup flow"
#   ./agents/analytics.sh "review this A/B test design"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERSONA="$SCRIPT_DIR/../personas/archive/analytics-cassie.md"

if [ ! -f "$PERSONA" ]; then
  echo "Error: persona file not found at $PERSONA"
  exit 1
fi

TASK="${1:-}"

if [ -n "$TASK" ]; then
  claude --system-prompt "$(cat "$PERSONA")" "$TASK"
else
  claude --system-prompt "$(cat "$PERSONA")"
fi
