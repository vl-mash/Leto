#!/usr/bin/env bash
# Calls Linear's GraphQL API.
# Usage: linear-graphql.sh '<query>' [variables_json]
#    or: echo '<query>' | linear-graphql.sh - [variables_json]
# API key resolved by integrations/lib/load-env.sh, in this order:
#   $LINEAR_API_KEY → ~/.config/leto/leto.env → legacy ~/.config/leto/linear-api-key
# Plain token, no "Bearer" prefix needed — Linear accepts bare tokens.
set -euo pipefail

# shellcheck source=../lib/load-env.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/load-env.sh"

if ! API_KEY="$(leto_secret LINEAR_API_KEY linear-api-key)" || [[ -z "$API_KEY" ]]; then
  printf '{"errors":[{"message":"LINEAR_API_KEY not set — add it to ~/.config/leto/leto.env (see ~/Projects/Leto/.env.example). Get a key at https://linear.app/settings/api"}]}\n' >&2
  exit 1
fi

if [[ "${1:-}" == "-" ]]; then
  QUERY=$(cat)
  VARS="${2:-}"
[[ -z "$VARS" ]] && VARS="{}"
else
  QUERY="${1:?Usage: linear-graphql.sh '<query>' [variables_json]}"
  VARS="${2:-}"
[[ -z "$VARS" ]] && VARS="{}"
fi

# Build payload via Python: handles non-ASCII, escaping, and variable injection safely.
PAYLOAD=$(python3 -c "
import sys, json
query = sys.argv[1]
variables = json.loads(sys.argv[2])
print(json.dumps({'query': query, 'variables': variables}))
" "$QUERY" "$VARS")

exec curl -sS \
  -H "Content-Type: application/json" \
  -H "Authorization: $API_KEY" \
  -d "$PAYLOAD" \
  https://api.linear.app/graphql
