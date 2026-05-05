#!/usr/bin/env bash
# Setup — adds `ask` alias to your shell config
# Run once per machine after cloning: bash setup.sh

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASK_CMD="alias ask='$REPO_DIR/agents/ask.sh'"

# Detect shell config file
if [ -f "$HOME/.zshrc" ]; then
  SHELL_CONFIG="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
  SHELL_CONFIG="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
  SHELL_CONFIG="$HOME/.bash_profile"
else
  echo "Could not detect shell config. Add this manually:"
  echo "  $ASK_CMD"
  exit 1
fi

# Avoid duplicate entries
if grep -q "alias ask=" "$SHELL_CONFIG"; then
  echo "Alias 'ask' already exists in $SHELL_CONFIG — skipping."
else
  echo "" >> "$SHELL_CONFIG"
  echo "# Agent team" >> "$SHELL_CONFIG"
  echo "$ASK_CMD" >> "$SHELL_CONFIG"
  echo "Added 'ask' alias to $SHELL_CONFIG"
fi

echo ""
echo "Run: source $SHELL_CONFIG"
echo ""
echo "Then use:"
echo "  ask --lite pm \"should I build X or Y first?\""
echo "  ask --lite security \"review my auth flow\""
echo "  ask cto \"design the data model for this feature\""
