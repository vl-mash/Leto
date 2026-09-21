#!/usr/bin/env bash
# YouTrack daily digest — active projects (new/updated tickets) + new projects created,
# diffed against the previous run's snapshot.
#
# Prints a Markdown digest to STDOUT (which the scheduled routine posts to Slack).
# Writes an updated snapshot to state.json ONLY on success.
#
# Exit codes:
#   0  success (digest on stdout)
#   3  setup incomplete (token not filled in)
#   4  YouTrack API call failed
set -euo pipefail

# Runtime data (snapshot) stays where it has always lived, so the diff baseline
# survives this script moving into version control. Override with YT_DIGEST_DIR.
DIR="${YT_DIGEST_DIR:-$HOME/.claude/scheduled-tasks/youtrack-daily-digest}"
STATE="$DIR/state.json"

# --- credentials ---------------------------------------------------------
# Resolved from the consolidated ~/.config/leto/leto.env via the shared loader,
# with this task's own legacy .env kept as a fallback. Until 2026-09-21 the two
# YouTrack keys lived in a SECOND env file all of their own — the only Leto
# credentials outside the main store, and invisible to leto_secrets --check.
# shellcheck source=../lib/load-env.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/load-env.sh"
YOUTRACK_BASE_URL="$(leto_secret YOUTRACK_BASE_URL || true)"
YOUTRACK_TOKEN="$(leto_secret YOUTRACK_TOKEN || true)"
if [ -z "${YOUTRACK_TOKEN:-}" ] && [ -f "$DIR/.env" ]; then
  # shellcheck disable=SC1091
  source "$DIR/.env"
fi
: "${YOUTRACK_BASE_URL:?YOUTRACK_BASE_URL not set — add it to ~/.config/leto/leto.env}"
if [ -z "${YOUTRACK_TOKEN:-}" ] || [ "${YOUTRACK_TOKEN}" = "REPLACE_ME" ]; then
  echo "SETUP_INCOMPLETE: set YOUTRACK_TOKEN in ~/.config/leto/leto.env (see .env.example)" >&2
  exit 3
fi

API="$YOUTRACK_BASE_URL/api"
H=(-H "Authorization: Bearer $YOUTRACK_TOKEN" -H "Accept: application/json")

NOW_MS=$(( $(date +%s) * 1000 ))
NOW_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)

epoch_to_date() { # $1 = epoch seconds -> UTC YYYY-MM-DD
  date -u -r "$1" +%Y-%m-%d 2>/dev/null || date -u -d "@$1" +%Y-%m-%d
}

# --- baseline vs incremental --------------------------------------------
if [ -f "$STATE" ]; then
  BASELINE=0
  LAST_MS=$(jq -r '.lastRunMs // 0' "$STATE")
  PREV_PROJECTS=$(jq -c '.projects // {}' "$STATE")
  LAST_ISO=$(jq -r '.lastRunAt // "unknown"' "$STATE")
else
  BASELINE=1
  LAST_MS=0
  PREV_PROJECTS='{}'
  LAST_ISO="baseline"
fi

# --- fetch projects ------------------------------------------------------
PROJECTS=$(curl -fsS "${H[@]}" \
  "$API/admin/projects?fields=id,name,shortName,archived&\$top=500") \
  || { echo "CURL_FAIL: could not fetch projects from $API" >&2; exit 4; }

# --- fetch issues updated since last run (incremental only) --------------
ISSUES='[]'
if [ "$BASELINE" -eq 0 ]; then
  # Pull a day earlier than last run to be safe; filtered precisely by ms below.
  SINCE_DATE=$(epoch_to_date $(( LAST_MS/1000 - 86400 )))
  QUERY=$(printf 'updated: %s .. *' "$SINCE_DATE" | jq -sRr @uri)
  ISSUES=$(curl -fsS "${H[@]}" \
    "$API/issues?query=$QUERY&fields=idReadable,summary,created,updated,project(shortName,name),reporter(login,fullName),updater(login,fullName)&\$top=5000") \
    || { echo "CURL_FAIL: could not fetch issues from $API" >&2; exit 4; }
fi

# --- compute new state (written only at the very end) --------------------
NEW_STATE=$(echo "$PROJECTS" | jq \
  --arg now "$NOW_ISO" --argjson nowms "$NOW_MS" \
  '{lastRunAt:$now, lastRunMs:$nowms,
    projects: (map({(.shortName): {name:.name, archived:.archived}}) | add // {})}')

# --- baseline digest -----------------------------------------------------
if [ "$BASELINE" -eq 1 ]; then
  PCOUNT=$(echo "$PROJECTS" | jq '[.[] | select(.archived==false)] | length')
  {
    echo "*YouTrack daily digest — $(date -u +'%A, %d %b %Y')*"
    echo "_Baseline captured._ Tracking ${PCOUNT} active projects. Daily change reports start on the next run."
  }
  echo "$NEW_STATE" > "$STATE"
  exit 0
fi

# --- incremental digest --------------------------------------------------
LAST_HUMAN=$(echo "$LAST_ISO" | sed 's/T/ /; s/Z/ UTC/')

BODY=$(jq -n -r \
  --argjson last "$LAST_MS" \
  --argjson projects "$PROJECTS" \
  --argjson issues "$ISSUES" \
  --argjson prev "$PREV_PROJECTS" \
  '
  ($prev | keys) as $prevKeys
  | [ $projects[] | . as $p | select(($prevKeys | index($p.shortName)) | not) ] as $newProjects
  | [ $issues[] | select(.updated >= $last) ] as $act
  | ($act | group_by(.project.shortName)
      | map(
          (.[0].project.shortName) as $short
          | (.[0].project.name) as $name
          | ([.[] | select(.created >= $last)] | length) as $new
          | ([.[] | select(.created <  $last)] | length) as $upd
          | ( [ .[] | { who: (if .created >= $last
                              then (.reporter.fullName // .reporter.login // "unknown")
                              else (.updater.fullName // .updater.login // "unknown") end) } ]
              | group_by(.who) | map({who:.[0].who, n:length}) | sort_by(-.n)
              | map("\(.who) (\(.n))") | join(", ") ) as $who
          | { short:$short, name:$name, new:$new, upd:$upd, total:length, who:$who })
      | sort_by(-.total)) as $active
  | ($act | length) as $ticketTotal
  | (
      if ($active | length) == 0 and ($newProjects | length) == 0 then
        ["No YouTrack activity since last run (" + ($last|tostring) + ")."]
      else
        (
          if ($active | length) > 0 then
            ["*Active projects* — \($ticketTotal) ticket(s) touched across \($active|length) project(s)"]
            + ($active | map("• \(.short) — \(.name): \(.new) new, \(.upd) updated — \(.who)"))
            + [""]
          else
            ["*Active projects*: none", ""]
          end
        )
        +
        (
          if ($newProjects | length) > 0 then
            ["*New projects created*"]
            + ($newProjects | map("• \(.shortName) — \(.name)" + (if .archived then " _(archived)_" else "" end)))
          else
            ["*New projects created*: none"]
          end
        )
      end
    )
  | .[]
  ')

{
  echo "*YouTrack daily digest — $(date -u +'%A, %d %b %Y')*"
  echo "_Activity since ${LAST_HUMAN}_"
  echo ""
  echo "$BODY"
}

# persist snapshot only after the digest was produced successfully
echo "$NEW_STATE" > "$STATE"
