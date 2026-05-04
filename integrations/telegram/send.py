#!/usr/bin/env python3
"""
Leto — Telegram outbound (Phase 3 prereq).

Sends a single message on Vladimir's behalf with two-checkpoint approval:
  1. Script shows recipient (resolved name + chat type) and message preview
  2. Vladimir confirms Y/n at the terminal — only then does it call slack_send_message-equivalent

Every send is logged (append-only JSONL) to .local-data/telegram/sent-log.jsonl.

Hard exclusions:
- Cannot send to broadcast channels (use slack/email for announcements)
- Cannot send to bots (would be operationally pointless)
- HR-shaped recipients per Voice Signature.md / Leto guardrails: this script doesn't enforce
  per-recipient blocks; that's the LETO/Persona layer's job. send.py is a low-level send tool.
  When wired into Phase 3 flow, the calling layer applies the exclusion list.

Usage:
    # Inline message
    python send.py --chat-id 397366400 --message "Hello"

    # Read from file (preferred for multi-line / non-trivial)
    python send.py --chat-id 397366400 --file /tmp/draft.txt

    # Stdin (paste message, Ctrl-D to end)
    python send.py --chat-id 397366400

    # Dry-run: show preview + would-send confirmation, but don't actually send
    python send.py --chat-id 397366400 --message "Test" --dry-run

Args:
    --chat-id INT       Telegram dialog ID (positive for private DMs).
    --message STR       Inline message text. Mutually exclusive with --file.
    --file PATH         Path to file containing message text. Mutually exclusive with --message.
                        UTF-8 expected.
    --dry-run           Preview + confirm + LOG, but do NOT actually send.
    --yes               Skip Y/n prompt (assume yes). USE WITH CARE.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    from telethon import TelegramClient
    from telethon.tl.types import User, Chat, Channel
except ImportError as exc:
    print(f"Missing dependency ({exc.name}). Activate venv: source venv/bin/activate", file=sys.stderr)
    sys.exit(1)


SCRIPT_DIR = Path(__file__).resolve().parent
LETO_ROOT = SCRIPT_DIR.parent.parent
SESSION_PATH = SCRIPT_DIR / "leto.session"
LOG_PATH = LETO_ROOT / ".local-data" / "telegram" / "sent-log.jsonl"


def load_credentials() -> tuple[int, str]:
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        print(f"No .env at {env_path}. See README.md.", file=sys.stderr)
        sys.exit(2)
    load_dotenv(env_path)
    api_id_raw = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()
    if not api_id_raw or not api_hash:
        print("Missing TELEGRAM_API_ID or TELEGRAM_API_HASH in .env", file=sys.stderr)
        sys.exit(2)
    return int(api_id_raw), api_hash


def chat_kind(entity) -> str:
    if isinstance(entity, User):
        return "private" if not getattr(entity, "bot", False) else "bot"
    if isinstance(entity, Chat):
        return "group"
    if isinstance(entity, Channel):
        return "channel" if entity.broadcast else "supergroup"
    return "unknown"


def chat_title(entity) -> str:
    if isinstance(entity, User):
        parts = [entity.first_name or "", entity.last_name or ""]
        title = " ".join(p for p in parts if p).strip()
        if not title and entity.username:
            title = f"@{entity.username}"
        if not title:
            title = f"User {entity.id}"
        return title
    if isinstance(entity, (Chat, Channel)):
        return entity.title or f"Chat {entity.id}"
    return f"Entity {getattr(entity, 'id', '?')}"


def read_message(args) -> str:
    if args.message and args.file:
        print("Error: --message and --file are mutually exclusive.", file=sys.stderr)
        sys.exit(2)
    if args.message:
        return args.message
    if args.file:
        path = Path(args.file).expanduser().resolve()
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            sys.exit(2)
        return path.read_text(encoding="utf-8").rstrip("\n")
    # stdin
    print("Paste message text (end with Ctrl-D):", file=sys.stderr)
    return sys.stdin.read().rstrip("\n")


def confirm(prompt: str) -> bool:
    """Y/n prompt. Default no (must explicitly type y or yes)."""
    try:
        response = input(prompt).strip().lower()
    except EOFError:
        return False
    return response in ("y", "yes")


def append_log(record: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


async def main_async(args) -> int:
    message = read_message(args).strip()
    if not message:
        print("Empty message. Aborting.", file=sys.stderr)
        return 2

    api_id, api_hash = load_credentials()

    if not SESSION_PATH.exists():
        print(f"No session file at {SESSION_PATH}. Run `python -m mine list` first to authenticate.", file=sys.stderr)
        return 2

    client = TelegramClient(str(SESSION_PATH), api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        print("Session not authorized. Re-authenticate via `python -m mine list`.", file=sys.stderr)
        await client.disconnect()
        return 2

    me = await client.get_me()

    try:
        entity = await client.get_entity(args.chat_id)
    except Exception as exc:
        print(f"Could not resolve chat_id={args.chat_id}: {exc}", file=sys.stderr)
        await client.disconnect()
        return 2

    kind = chat_kind(entity)
    title = chat_title(entity)

    # Hard exclusions
    if kind == "channel":
        print(f"REFUSED: chat is a broadcast channel ({title}). send.py does not send to broadcast channels.", file=sys.stderr)
        await client.disconnect()
        return 3
    if kind == "bot":
        print(f"REFUSED: recipient is a bot ({title}). send.py does not send to bots.", file=sys.stderr)
        await client.disconnect()
        return 3

    # Preview
    print()
    print("=" * 70)
    print(f"  Recipient: {title} (id={args.chat_id}, type={kind})")
    print(f"  From:      {chat_title(me)} (you, id={me.id})")
    print(f"  Message length: {len(message)} chars, {len(message.splitlines())} lines")
    print("=" * 70)
    print(message)
    print("=" * 70)
    if args.dry_run:
        print("  DRY RUN — message will NOT be sent.")
    print()

    # Confirmation gate
    if args.yes:
        confirmed = True
        print("(--yes flag passed; skipping confirmation)")
    else:
        confirmed = confirm(f"Send this message to {title}? [y/N]: ")

    if not confirmed:
        print("Cancelled. Nothing sent.")
        await client.disconnect()
        return 1

    # Log intent (regardless of dry-run)
    log_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from_user_id": me.id,
        "from_username": me.username,
        "to_chat_id": args.chat_id,
        "to_chat_title": title,
        "to_chat_type": kind,
        "message_length": len(message),
        "message_text": message,
        "dry_run": bool(args.dry_run),
        "sent_message_id": None,
        "status": "pending",
    }

    if args.dry_run:
        log_record["status"] = "dry-run"
        append_log(log_record)
        print("Dry run logged. Did not send.")
        await client.disconnect()
        return 0

    # Actual send
    try:
        result = await client.send_message(entity, message)
        log_record["sent_message_id"] = result.id
        log_record["status"] = "sent"
        append_log(log_record)
        print(f"✓ Sent. message_id={result.id}, sent_at={result.date.isoformat()}")
        await client.disconnect()
        return 0
    except Exception as exc:
        log_record["status"] = "error"
        log_record["error"] = str(exc)
        append_log(log_record)
        print(f"✗ Send failed: {exc}", file=sys.stderr)
        await client.disconnect()
        return 4


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Leto — Telegram outbound (single message, two-checkpoint approval).")
    p.add_argument("--chat-id", type=int, required=True, help="Telegram dialog ID.")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--message", type=str, help="Inline message text.")
    src.add_argument("--file", type=str, help="Path to file containing message text.")
    p.add_argument("--dry-run", action="store_true", help="Preview + confirm + log, but do NOT actually send.")
    p.add_argument("--yes", action="store_true", help="Skip Y/n prompt (USE WITH CARE).")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
