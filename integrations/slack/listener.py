#!/usr/bin/env python3
"""
Leto Slack bot — Socket Mode listener (v1).

Reads tokens from files (same pattern as leto-bot-post.sh):
  ~/.config/leto/slack-bot-token   xoxb-... (bot OAuth token)
  ~/.config/leto/slack-app-token   xapp-... (app-level token for Socket Mode)

Override either with env vars SLACK_BOT_TOKEN / SLACK_APP_TOKEN.

VM-9: minimal listener — connects, logs "ready", stubs /leto commands.
VM-10: replace the stub handler with actual dispatch to Claude CLI.
"""

import asyncio
import logging
import os
from pathlib import Path

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("leto-bot")


def read_token(path: str, env_var: str) -> str:
    if env_var in os.environ:
        return os.environ[env_var]
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(
            f"Token file not found: {p}\n"
            f"Create it or set the {env_var} environment variable."
        )
    return p.read_text().strip()


BOT_TOKEN = read_token("~/.config/leto/slack-bot-token", "SLACK_BOT_TOKEN")
APP_TOKEN = read_token("~/.config/leto/slack-app-token", "SLACK_APP_TOKEN")

app = AsyncApp(token=BOT_TOKEN)


@app.command("/leto")
async def handle_leto(ack, command, say):
    """Slash command handler. VM-10 replaces the stub body with real dispatch."""
    await ack()
    subcommand = (command.get("text") or "").strip()
    user = command.get("user_id", "?")
    log.info("/leto %r from %s", subcommand, user)
    # VM-10: dispatch subcommand → Claude CLI subprocess → post result
    await say(f"⏳ `/leto {subcommand}` received — command dispatch coming in VM-10.")


async def main():
    handler = AsyncSocketModeHandler(app, APP_TOKEN)
    log.info("Leto bot ready — connecting via Socket Mode")
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())
