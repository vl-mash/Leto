#!/usr/bin/env bash
# Install the doubt-driven Stop hook into ~/.claude/settings.json.
#
# Idempotent — re-running with the same path replaces the existing entry.
# Uses jq to merge cleanly. Backs up settings.json before writing.
#
# Uninstall: bash install.sh --uninstall

set -euo pipefail

SETTINGS_FILE="$HOME/.claude/settings.json"
HOOK_SCRIPT="$(cd "$(dirname "$0")" && pwd)/doubt-stop.py"
HOOK_MARKER="doubt-stop.py"  # used to identify our entry on uninstall / re-install

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required. Install with: brew install jq" >&2
  exit 1
fi

if [[ ! -f "$SETTINGS_FILE" ]]; then
  echo "Error: $SETTINGS_FILE does not exist" >&2
  exit 1
fi

if [[ ! -x "$HOOK_SCRIPT" ]]; then
  chmod +x "$HOOK_SCRIPT"
fi

BACKUP="$SETTINGS_FILE.bak.$(date +%Y%m%d-%H%M%S)"
cp "$SETTINGS_FILE" "$BACKUP"
echo "Backed up settings to: $BACKUP"

if [[ "${1:-}" == "--uninstall" ]]; then
  jq --arg marker "$HOOK_MARKER" '
    if .hooks.Stop then
      .hooks.Stop |= map(select(.hooks[]?.command | contains($marker) | not))
      | if (.hooks.Stop | length) == 0 then del(.hooks.Stop) else . end
      | if (.hooks // {} | length) == 0 then del(.hooks) else . end
    else . end
  ' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp"
  mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
  echo "Uninstalled doubt-stop hook from $SETTINGS_FILE"
  exit 0
fi

jq --arg cmd "$HOOK_SCRIPT" --arg marker "$HOOK_MARKER" '
  .hooks //= {}
  | .hooks.Stop //= []
  | .hooks.Stop |= map(select(.hooks[]?.command | contains($marker) | not))
  | .hooks.Stop += [{
      "matcher": "",
      "hooks": [{"type": "command", "command": $cmd}]
    }]
' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp"
mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"

echo "Installed doubt-stop hook:"
echo "  Hook script:  $HOOK_SCRIPT"
echo "  Settings:     $SETTINGS_FILE"
echo "  Log dir:      $HOME/.claude/logs/doubt-stop/"
echo ""
echo "Restart any active Claude Code sessions for the hook to take effect."
echo "Uninstall with: bash $(dirname "$0")/install.sh --uninstall"
