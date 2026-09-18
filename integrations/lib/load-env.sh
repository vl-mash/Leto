# shellcheck shell=bash
# Leto secret resolution for bash consumers. Source, don't execute:
#
#   source "$(dirname "${BASH_SOURCE[0]}")/../lib/load-env.sh"
#   TOKEN="$(leto_secret SLACK_BOT_TOKEN slack-bot-token)" || { ...; }
#
# ONE env file holds every Leto credential: ~/.config/leto/leto.env (mode 600),
# same `export KEY=value` format the youtrack digest already uses.
#
# Resolution order for every key (no flag day — legacy files keep working):
#   1. already-set environment variable
#   2. ~/.config/leto/leto.env
#   3. legacy single-value file ~/.config/leto/<basename>, if a 2nd arg is given
#   4. non-zero exit, empty output
#
# Safe under `set -euo pipefail`: returns 1 rather than tripping unbound-variable.

LETO_ENV_FILE="${LETO_ENV_FILE:-$HOME/.config/leto/leto.env}"
LETO_CFG_DIR="${LETO_CFG_DIR:-$HOME/.config/leto}"

# Parse leto.env into the environment. An already-set variable always wins, so
# callers can override any key inline for testing. Idempotent.
leto_load_env() {
  [[ -f "$LETO_ENV_FILE" ]] || return 0
  local line key val
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"          # ltrim
    [[ -z "$line" || "$line" == \#* ]] && continue
    line="${line#export }"
    [[ "$line" != *=* ]] && continue
    key="${line%%=*}"
    val="${line#*=}"
    key="${key//[[:space:]]/}"
    [[ -z "$key" ]] && continue
    val="${val#"${val%%[![:space:]]*}"}"             # ltrim value
    val="${val%"${val##*[![:space:]]}"}"             # rtrim value
    val="${val%\"}"; val="${val#\"}"                 # strip paired quotes
    val="${val%\'}"; val="${val#\'}"
    [[ -n "${!key:-}" ]] && continue                 # env var wins
    export "$key=$val"
  done < "$LETO_ENV_FILE"
}

# leto_secret KEY [legacy-file-basename] — prints the value, or exits 1.
leto_secret() {
  local key="${1:?leto_secret: KEY required}" legacy="${2:-}"
  leto_load_env
  if [[ -n "${!key:-}" ]]; then
    printf '%s' "${!key}"
    return 0
  fi
  if [[ -n "$legacy" && -f "$LETO_CFG_DIR/$legacy" ]]; then
    tr -d '[:space:]' < "$LETO_CFG_DIR/$legacy"
    return 0
  fi
  return 1
}

# Uniform "you need to set this" message, so every consumer fails the same way.
leto_secret_missing() {
  local key="${1:?}" extra="${2:-}"
  cat >&2 <<EOF
error: $key is not set.
  Add it to $LETO_ENV_FILE:
    mkdir -p "$LETO_CFG_DIR" && chmod 700 "$LETO_CFG_DIR"
    printf 'export %s=%s\n' "$key" '<value>' >> "$LETO_ENV_FILE"
    chmod 600 "$LETO_ENV_FILE"
  See ~/Projects/Leto/.env.example for every key Leto uses.${extra:+
  $extra}
EOF
}
