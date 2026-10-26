#!/usr/bin/env python3
"""List Slack accounts deactivated since the last run (leaver signal for the politics brief).

Humaans won't let Vladimir's account filter on employment end dates, so the weekly politics
brief detects leavers from three sources; this script is the Slack one. It pages through
users.list, compares the deactivated (deleted, non-bot) user ids with the previous snapshot,
prints the new ones as JSON and saves the new snapshot.

Usage:
  leavers.py [--dry-run]   # --dry-run prints the diff but keeps the old snapshot

Output: {"baseline": bool, "since": "<previous run date>", "new": [{"id", "name", "title"}]}
On the first run there is no snapshot, so "baseline" is true and "new" is empty.

Token: $LETO_SLACK_BOT_TOKEN, else $SLACK_BOT_TOKEN (users:read is enough). Transport is
curl with the header on stdin, as in brief_blocks.py, so the token never reaches argv.
The snapshot lives in .local-data/ (gitignored): Slack ids and names only.
"""
import json
import os
import subprocess
import sys
from datetime import date

SNAPSHOT = os.path.join(os.path.dirname(__file__), "..", "..", ".local-data", "slack-deactivated.json")


def users(token):
    cursor = ""
    while True:
        r = subprocess.run(
            ["curl", "-sS", "-K", "-", f"https://slack.com/api/users.list?limit=1000&cursor={cursor}"],
            input=f'header = "Authorization: Bearer {token}"\n', capture_output=True, text=True, timeout=60)
        resp = json.loads(r.stdout or "{}")
        if not resp.get("ok"):
            sys.exit(f"users.list failed: {resp.get('error') or r.stderr.strip()[:120]}")
        yield from resp["members"]
        cursor = resp.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            return


def main():
    token = os.environ.get("LETO_SLACK_BOT_TOKEN") or os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        sys.exit("no LETO_SLACK_BOT_TOKEN / SLACK_BOT_TOKEN in the environment")
    deleted = {u["id"]: {"id": u["id"], "name": u.get("real_name") or u.get("name", ""),
                         "title": u.get("profile", {}).get("title", "")}
               for u in users(token) if u.get("deleted") and not u.get("is_bot")}
    try:
        prev = json.load(open(SNAPSHOT))
    except (OSError, ValueError):
        prev = None
    new = [] if prev is None else [deleted[i] for i in sorted(set(deleted) - set(prev["ids"]))]
    print(json.dumps({"baseline": prev is None, "since": prev and prev["date"], "new": new},
                     ensure_ascii=False, indent=1))
    if "--dry-run" not in sys.argv:
        with open(SNAPSHOT, "w") as f:
            json.dump({"date": date.today().isoformat(), "ids": sorted(deleted)}, f)


if __name__ == "__main__":
    main()
