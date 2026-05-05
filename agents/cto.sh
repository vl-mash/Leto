#!/usr/bin/env bash
# CTO/Architect Agent — Martin Fowler persona
# Usage: ./agents/cto.sh [optional: task or file]
#
# Examples:
#   ./agents/cto.sh                                         # open architecture session
#   ./agents/cto.sh "review the system design"              # pass a task directly
#   ./agents/cto.sh src/                                    # review a directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERSONA="$SCRIPT_DIR/../personas/cto-martin.md"

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
