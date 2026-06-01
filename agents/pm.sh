#!/usr/bin/env bash
# PM Agent — Shreyas Doshi persona
# Usage: ./agents/pm.sh [optional: task or file]
#
# Examples:
#   ./agents/pm.sh                                      # open PM session
#   ./agents/pm.sh "prioritize this backlog: ..."       # pass a task directly
#   ./agents/pm.sh backlog.md                           # review a backlog file

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERSONA="$SCRIPT_DIR/../personas/product/pm-shreyas.md"

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
