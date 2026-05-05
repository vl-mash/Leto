#!/usr/bin/env bash
# QA Agent — Elisabeth Hendrickson persona
# Usage: ./agents/qa.sh [optional: path to project or file to review]
#
# Examples:
#   ./agents/qa.sh                          # open QA session, no context
#   ./agents/qa.sh src/checkout.ts          # review a specific file
#   ./agents/qa.sh "write tests for login"  # pass a task directly

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERSONA="$SCRIPT_DIR/../personas/qa-elisabeth.md"

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
