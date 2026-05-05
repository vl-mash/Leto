#!/usr/bin/env bash
# Designer Agent — Julie Zhuo persona
# Usage: ./agents/designer.sh [optional: task or file]
#
# Examples:
#   ./agents/designer.sh                                    # open design session
#   ./agents/designer.sh "review the checkout flow"         # pass a task directly
#   ./agents/designer.sh wireframe.md                       # review a file

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERSONA="$SCRIPT_DIR/../personas/designer-julie.md"

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
