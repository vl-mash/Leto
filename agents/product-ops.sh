#!/usr/bin/env bash
# Product Ops Lead / Chief of Staff persona
# Usage: ./agents/product-ops.sh [optional: task or file]
#
# Examples:
#   ./agents/product-ops.sh                                       # open session
#   ./agents/product-ops.sh "draft a 1-pager for X"               # pass a task
#   ./agents/product-ops.sh decision.md                           # review a doc

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERSONA="$SCRIPT_DIR/../personas/product-ops.md"

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
