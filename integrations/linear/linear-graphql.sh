#!/usr/bin/env bash
# Calls Linear's GraphQL API.
# Usage: linear-graphql.sh '<query>' [variables_json]
#    or: echo '<query>' | linear-graphql.sh - [variables_json]
# API key read from ~/.config/leto/linear-api-key (plain token, no "Bearer" prefix needed — Linear accepts bare tokens).
set -euo pipefail

KEY_FILE="$HOME/.config/leto/linear-api-key"
if [[ ! -f "$KEY_FILE" ]]; then
  printf '{"errors":[{"message":"Linear API key missing — create ~/.config/leto/linear-api-key with a personal API token from https://linear.app/settings/api"}]}\n' >&2
  exit 1
fi
API_KEY=$(tr -d '[:space:]' < "$KEY_FILE")

if [[ "${1:-}" == "-" ]]; then
  QUERY=$(cat)
  VARS="${2:-{}}"
else
  QUERY="${1:?Usage: linear-graphql.sh '<query>' [variables_json]}"
  VARS="${2:-{}}"
fi

exec curl -sS \
  -H "Content-Type: application/json" \
  -H "Authorization: $API_KEY" \
  -d "$(jq -n --arg q "$QUERY" --argjson v "$VARS" '{query: $q, variables: $v}')" \
  https://api.linear.app/graphql
