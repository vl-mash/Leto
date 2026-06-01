#!/usr/bin/env bash
# Growth Agent — Andrew Chen persona
# Usage: ./agents/growth.sh [optional: task or prompt]
#
# Examples:
#   ./agents/growth.sh                                      # open growth session
#   ./agents/growth.sh "design a referral loop for my app"  # pass a task directly
#   ./agents/growth.sh "review my go-to-market plan"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERSONA="$SCRIPT_DIR/../personas/archive/growth-andrew.md"

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
