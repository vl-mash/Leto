#!/usr/bin/env python3
"""
Leto Slack bot — Socket Mode listener (v1).

Reads tokens from files (same pattern as leto-bot-post.sh):
  ~/.config/leto/slack-bot-token   xoxb-... (bot OAuth token)
  ~/.config/leto/slack-app-token   xapp-... (app-level token for Socket Mode)

Override either with env vars SLACK_BOT_TOKEN / SLACK_APP_TOKEN.

VM-9: minimal listener — connects, logs "ready", stubs /leto commands.
VM-10: deferred-response dispatch — ack immediately, run claude --print
       in background, post result in thread.
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("leto-bot")

LETO_PROJECT = Path("~/Projects/Leto").expanduser()
CLAUDE_CMD = shutil.which("claude") or "/usr/local/bin/claude"
DISPATCH_TIMEOUT = 300  # seconds; /leto today can take ~2 min

VALID_SUBCOMMANDS = frozenset(
    {"today", "capture", "post-notion-updates", "post-personal-backlog-eod"}
)
SLACK_MSG_LIMIT = 3800  # leave headroom under Slack's 4000-char cap


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


async def _run_claude(prompt: str) -> str:
    if not CLAUDE_CMD:
        return "❌ `claude` CLI not found in PATH."
    proc = await asyncio.create_subprocess_exec(
        CLAUDE_CMD, "--print", prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(LETO_PROJECT),
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=DISPATCH_TIMEOUT
        )
    except asyncio.TimeoutError:
        proc.kill()
        return f"❌ Timed out after {DISPATCH_TIMEOUT}s."
    if proc.returncode != 0:
        err = stderr.decode().strip()[:500]
        return f"❌ Claude CLI exited {proc.returncode}: {err}"
    return stdout.decode().strip()


async def _dispatch(subcommand: str, channel: str, thread_ts: str) -> None:
    log.info("dispatching /leto %r", subcommand)
    output = await _run_claude(f"/leto {subcommand}")
    if len(output) > SLACK_MSG_LIMIT:
        output = output[:SLACK_MSG_LIMIT] + "\n\n_(truncated — see vault for full output)_"
    try:
        await app.client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=output or "_(no output)_",
            mrkdwn=True,
        )
    except Exception as e:
        log.error("Failed to post dispatch result: %s", e)


@app.command("/leto")
async def handle_leto(ack, command, say):
    await ack()
    subcommand = (command.get("text") or "").strip()
    user = command.get("user_id", "?")
    channel = command.get("channel_id")
    log.info("/leto %r from %s", subcommand, user)

    root = subcommand.split()[0] if subcommand else ""
    if root not in VALID_SUBCOMMANDS:
        valid = " | ".join(sorted(VALID_SUBCOMMANDS))
        await say(f"Unknown subcommand `{root or '(empty)'}`. Valid: `{valid}`")
        return

    result = await say(f"⏳ Running `/leto {subcommand}`…")
    thread_ts = result.get("ts")
    asyncio.create_task(_dispatch(subcommand, channel, thread_ts))


async def main():
    handler = AsyncSocketModeHandler(app, APP_TOKEN)
    log.info("Leto bot ready — connecting via Socket Mode")
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())
