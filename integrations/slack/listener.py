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

import ssl
import certifi

# Python 3.13 on macOS doesn't load system certs by default; patch before
# any network imports so aiohttp/slack_bolt pick up the correct CA bundle.
ssl._create_default_https_context = lambda: ssl.create_default_context(
    cafile=certifi.where()
)

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
VAULT_DRAFTS = Path("~/Obsidian Vault/Vladimir's Vault/00 Inbox/Drafts").expanduser()
CLAUDE_CMD = shutil.which("claude") or "/usr/local/bin/claude"
DISPATCH_TIMEOUT = 300  # seconds; /leto today can take ~2 min

VALID_SUBCOMMANDS = frozenset(
    {"today", "capture", "post-notion-updates", "post-personal-backlog-eod"}
)
# Short aliases → (full subcommand, drafts subdirectory for date auto-detection)
APPLY_ALIASES: dict[str, tuple[str, str]] = {
    "apply-backlog": ("post-personal-backlog-eod", "personal-backlog-eod"),
    "apply-notion":  ("post-notion-updates",        "notion-alignment"),
}
SLACK_MSG_LIMIT = 3800  # leave headroom under Slack's 4000-char cap

HELP_TEXT = """\
*/leto* commands:
• *today* — fresh daily brief
• *capture <thing>* — save URL / note / Slack thread to vault inbox
• *apply-backlog [date]* — apply EOD backlog proposals _(date optional, defaults to latest pending)_
• *apply-notion [date]* — apply Notion alignment proposals _(date optional, defaults to latest pending)_
• *post-personal-backlog-eod <date>* — same as apply-backlog (explicit date)
• *post-notion-updates <date>* — same as apply-notion (explicit date)
• *help* — this message
"""


def _latest_draft(subdir: str) -> str | None:
    """Return the stem (YYYY-MM-DD) of the most recent proposal file, or None."""
    d = VAULT_DRAFTS / subdir
    if not d.exists():
        return None
    files = sorted(d.glob("????-??-??.md"), reverse=True)
    return files[0].stem if files else None


def _build_prompt(subcommand: str) -> str:
    """Build the claude --print prompt for a /leto subcommand.

    Apply commands need an explicit non-interactive flag so claude doesn't
    stall waiting for the 'Proceed? yes/no' chat confirmation — the Slack
    reactions are already the approval signal.
    """
    is_apply = subcommand.startswith(
        ("post-notion-updates", "post-personal-backlog-eod")
    )
    if is_apply:
        return (
            f"Run the Leto apply command: /leto {subcommand}\n\n"
            "This is a non-interactive Slack bot invocation. "
            "The Slack reactions on the proposal thread are the approval — "
            "skip the chat confirmation gate ('Proceed? yes/no') and execute "
            "immediately. Reply with a concise completion summary: "
            "items applied ✓, skipped ⏭️, errors ❌."
        )
    return f"/leto {subcommand}"


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
    output = await _run_claude(_build_prompt(subcommand))
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

    # Help (and bare /leto with no args)
    if root in ("help", ""):
        await say(HELP_TEXT)
        return

    # Resolve short aliases with smart date defaulting
    if root in APPLY_ALIASES:
        full_cmd, draft_subdir = APPLY_ALIASES[root]
        parts = subcommand.split()
        if len(parts) > 1:
            date = parts[1]
        else:
            date = _latest_draft(draft_subdir)
            if not date:
                await say(f"No pending proposals found in `Drafts/{draft_subdir}/`.")
                return
        subcommand = f"{full_cmd} {date}"
        root = full_cmd

    if root not in VALID_SUBCOMMANDS:
        valid = "apply-backlog | apply-notion | capture | help | post-notion-updates | post-personal-backlog-eod | today"
        await say(f"Unknown subcommand `{root}`. Valid: `{valid}`")
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
