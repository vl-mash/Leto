#!/usr/bin/env bash
# Send a Slack message via the Leto bot token.
#
# Reads the bot token from $LETO_BOT_TOKEN_FILE
# (default: ~/.config/leto/slack-bot-token).
# Posts to chat.postMessage and prints the JSON response to stdout.
# Exits non-zero on failure (token missing, network error, or Slack ok:false).
#
# Usage:
#   leto-bot-post.sh <channel> <text> [thread_ts]
#
# Examples:
#   leto-bot-post.sh U06A5QCK073 "Hello from Leto bot"
#   leto-bot-post.sh U06A5QCK073 "Threaded reply" 1683500000.000123

set -euo pipefail

TOKEN_FILE="${LETO_BOT_TOKEN_FILE:-$HOME/.config/leto/slack-bot-token}"

if [[ ! -f "$TOKEN_FILE" ]]; then
  cat >&2 <<EOF
error: token file not found at $TOKEN_FILE
create it with:
  mkdir -p $(dirname "$TOKEN_FILE") && chmod 700 $(dirname "$TOKEN_FILE")
  printf '%s' 'xoxb-...' > $TOKEN_FILE && chmod 600 $TOKEN_FILE
EOF
  exit 1
fi

TOKEN="$(tr -d '[:space:]' < "$TOKEN_FILE")"
if [[ ! "$TOKEN" =~ ^xoxb- ]]; then
  echo "error: token at $TOKEN_FILE doesn't start with 'xoxb-' — expected a bot token" >&2
  exit 1
fi

if [[ $# -lt 2 ]]; then
  echo "usage: leto-bot-post.sh <channel> <text> [thread_ts]" >&2
  exit 2
fi

CHANNEL="$1"
TEXT="$2"
THREAD_TS="${3:-}"

# Build JSON payload with jq for safe escaping
if [[ -n "$THREAD_TS" ]]; then
  PAYLOAD=$(jq -nc \
    --arg c "$CHANNEL" \
    --arg t "$TEXT" \
    --arg ts "$THREAD_TS" \
    '{channel: $c, text: $t, thread_ts: $ts}')
else
  PAYLOAD=$(jq -nc \
    --arg c "$CHANNEL" \
    --arg t "$TEXT" \
    '{channel: $c, text: $t}')
fi

RESPONSE=$(curl --fail-with-body -sS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "$PAYLOAD") || {
  echo "$RESPONSE" >&2
  echo "error: HTTP request to chat.postMessage failed" >&2
  exit 1
}

echo "$RESPONSE"

OK=$(echo "$RESPONSE" | jq -r '.ok // false')
if [[ "$OK" != "true" ]]; then
  ERROR=$(echo "$RESPONSE" | jq -r '.error // "unknown"')
  echo "error: Slack returned ok=false (error: $ERROR)" >&2
  exit 1
fi
