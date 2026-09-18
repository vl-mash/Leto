#!/usr/bin/env bash
# Send a Slack message via the Leto bot token.
#
# Bot token resolved in this order:
#   $SLACK_BOT_TOKEN → ~/.config/leto/leto.env → $LETO_BOT_TOKEN_FILE
#   → legacy ~/.config/leto/slack-bot-token
# Posts to chat.postMessage and prints the JSON response to stdout.
# Exits non-zero on failure (token missing, network error, or Slack ok:false).
#
# Usage:
#   leto-bot-post.sh <channel> <text> [thread_ts]
#   leto-bot-post.sh <channel> - [thread_ts]    # read text from stdin
#   leto-bot-post.sh --auth-check               # auth.test only, sends nothing; exit 0/1
#
# Examples:
#   leto-bot-post.sh U06A5QCK073 "Hello from Leto bot"
#   leto-bot-post.sh U06A5QCK073 "Threaded reply" 1683500000.000123
#   echo "Long message here" | leto-bot-post.sh U06A5QCK073 -
#   cat brief.md | leto-bot-post.sh U06A5QCK073 - 1683500000.000123

set -euo pipefail

# shellcheck source=../lib/load-env.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/load-env.sh"

# LETO_BOT_TOKEN_FILE stays honoured for callers that set it explicitly; it now
# sits between leto.env and the legacy default rather than being the only path.
TOKEN=""
if ! TOKEN="$(leto_secret SLACK_BOT_TOKEN)" || [[ -z "$TOKEN" ]]; then
  if [[ -n "${LETO_BOT_TOKEN_FILE:-}" && -f "$LETO_BOT_TOKEN_FILE" ]]; then
    TOKEN="$(tr -d '[:space:]' < "$LETO_BOT_TOKEN_FILE")"
  elif [[ -f "$HOME/.config/leto/slack-bot-token" ]]; then
    TOKEN="$(tr -d '[:space:]' < "$HOME/.config/leto/slack-bot-token")"
  fi
fi

if [[ -z "$TOKEN" ]]; then
  leto_secret_missing SLACK_BOT_TOKEN \
    "Get one at api.slack.com/apps -> OAuth & Permissions -> Bot User OAuth Token."
  exit 1
fi
if [[ ! "$TOKEN" =~ ^xoxb- ]]; then
  echo "error: resolved SLACK_BOT_TOKEN doesn't start with 'xoxb-' — expected a bot token" >&2
  exit 1
fi

# --auth-check: verify the token against auth.test without posting anything.
# Used as the EOD v3 pre-mutation gate (no receipt channel → no mutations).
if [[ "${1:-}" == "--auth-check" ]]; then
  RESPONSE=$(curl --fail-with-body -sS -X POST https://slack.com/api/auth.test \
    -H "Authorization: Bearer $TOKEN") || {
    echo "error: HTTP request to auth.test failed" >&2
    exit 1
  }
  echo "$RESPONSE"
  OK=$(echo "$RESPONSE" | jq -r '.ok // false')
  if [[ "$OK" != "true" ]]; then
    echo "error: Slack auth.test returned ok=false ($(echo "$RESPONSE" | jq -r '.error // "unknown"'))" >&2
    exit 1
  fi
  exit 0
fi

if [[ $# -lt 2 ]]; then
  echo "usage: leto-bot-post.sh <channel> <text> [thread_ts]" >&2
  exit 2
fi

CHANNEL="$1"
if [[ "$2" == "-" ]]; then
  TEXT="$(cat)"
else
  TEXT="$2"
fi
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
