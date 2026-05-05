#!/usr/bin/env bash
# Principal Engineer Agent — John Carmack persona
# Usage: ./agents/engineer.sh [optional: task or file]
#
# Examples:
#   ./agents/engineer.sh                                    # open engineer session
#   ./agents/engineer.sh src/payments.ts                   # review a file
#   ./agents/engineer.sh "implement the login flow"         # pass a task directly

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERSONA="$SCRIPT_DIR/../personas/engineer-carmack.md"

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
