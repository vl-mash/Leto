#!/usr/bin/env python3
"""Send a Slack message via the Leto bot token.

Reads the bot token from $LETO_BOT_TOKEN_FILE (default: ~/.config/leto/slack-bot-token).
Posts to chat.postMessage and prints the JSON response to stdout.

Usage:
    leto-bot-post.py <channel> <text> [thread_ts]

Examples:
    leto-bot-post.py U06A5QCK073 "Hello from Leto bot"
    leto-bot-post.py U06A5QCK073 "Threaded reply" 1683500000.000123
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> int:
    token_path = Path(
        os.environ.get("LETO_BOT_TOKEN_FILE", "~/.config/leto/slack-bot-token")
    ).expanduser()

    if not token_path.exists():
        sys.stderr.write(
            f"error: token file not found at {token_path}\n"
            f"create it with: mkdir -p {token_path.parent} && "
            f"chmod 700 {token_path.parent} && "
            f"echo 'xoxb-...' > {token_path} && chmod 600 {token_path}\n"
        )
        return 1

    token = token_path.read_text().strip()
    if not token.startswith("xoxb-"):
        sys.stderr.write(
            f"error: token at {token_path} doesn't start with 'xoxb-' — "
            f"expected a bot token\n"
        )
        return 1

    if len(sys.argv) < 3:
        sys.stderr.write(
            "usage: leto-bot-post.py <channel> <text> [thread_ts]\n"
        )
        return 2

    channel, text = sys.argv[1], sys.argv[2]
    thread_ts = sys.argv[3] if len(sys.argv) > 3 else None

    payload: dict[str, str] = {"channel": channel, "text": text}
    if thread_ts:
        payload["thread_ts"] = thread_ts

    req = Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )

    try:
        with urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
    except HTTPError as e:
        sys.stderr.write(f"http error: {e.code} {e.reason}\n{e.read().decode()}\n")
        return 1
    except URLError as e:
        sys.stderr.write(f"network error: {e.reason}\n")
        return 1

    print(body)
    parsed = json.loads(body)
    return 0 if parsed.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
