#!/usr/bin/env bash
# Security Agent — Troy Hunt persona
# Usage: ./agents/security.sh [optional: task or file]
#
# Examples:
#   ./agents/security.sh                                    # open security session
#   ./agents/security.sh src/auth.ts                       # review auth code
#   ./agents/security.sh "review the login flow"            # pass a task directly

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERSONA="$SCRIPT_DIR/../personas/archive/security-troy.md"

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
