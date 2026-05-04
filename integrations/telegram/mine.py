#!/usr/bin/env python3
"""
Leto — Telegram voice corpus miner.

V1: pull-based extraction of Vladimir's authored messages from selected Telegram
chats, output as JSON for downstream voice-pattern processing.

Usage:
    python mine.py list                          # list all chats with IDs
    python mine.py mine                          # mine all 1:1 DMs since 6mo ago
    python mine.py mine --chats 12345,67890      # mine specific chats by ID
    python mine.py mine --since 2024-11-04       # custom date range
    python mine.py mine --output path.json       # custom output path

Stores nothing in the Leto or vault git repos. Outputs land in
~/Projects/Leto/.local-data/telegram/ (gitignored).

See README.md for setup steps (credentials, venv, first-run auth).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    from telethon import TelegramClient
    from telethon.tl.types import (
        User,
        Chat,
        Channel,
        Message,
    )
except ImportError as exc:
    print(
        f"Missing dependency ({exc.name}). Run:\n"
        f"  cd ~/Projects/Leto/integrations/telegram\n"
        f"  python3 -m venv venv && source venv/bin/activate\n"
        f"  pip install -r requirements.txt\n",
        file=sys.stderr,
    )
    sys.exit(1)


SCRIPT_DIR = Path(__file__).resolve().parent
LETO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_OUTPUT_DIR = LETO_ROOT / ".local-data" / "telegram"
SESSION_PATH = SCRIPT_DIR / "leto.session"


def load_credentials() -> tuple[int, str, str, str | None]:
    """Load API creds from .env. Fail fast with helpful message."""
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        print(
            f"No .env found at {env_path}. Copy .env.example to .env and fill in"
            f" your credentials (see README.md step 1).",
            file=sys.stderr,
        )
        sys.exit(2)
    load_dotenv(env_path)

    api_id_raw = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()
    phone = os.getenv("TELEGRAM_PHONE", "").strip()
    pw_2fa = os.getenv("TELEGRAM_2FA_PASSWORD", "").strip() or None

    if not api_id_raw or not api_hash or not phone:
        print(
            "Missing one or more env values: TELEGRAM_API_ID, TELEGRAM_API_HASH,"
            " TELEGRAM_PHONE. See .env.example.",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        api_id = int(api_id_raw)
    except ValueError:
        print(f"TELEGRAM_API_ID must be an integer, got: {api_id_raw!r}", file=sys.stderr)
        sys.exit(2)

    return api_id, api_hash, phone, pw_2fa


def chat_kind(entity) -> str:
    """Return 'private' / 'group' / 'channel' / 'supergroup' / 'unknown'."""
    if isinstance(entity, User):
        return "private"
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


async def cmd_list(client: TelegramClient) -> None:
    """List all chats the account has interacted with."""
    print(f"{'ID':<20} {'Type':<12} {'Title'}")
    print("-" * 80)
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        kind = chat_kind(entity)
        title = chat_title(entity)
        print(f"{dialog.id:<20} {kind:<12} {title}")


def message_to_dict(msg: Message, reply_to_excerpt: str | None) -> dict:
    """Serialize a message authored by self, with reply context."""
    media_type = None
    if msg.media is not None:
        media_type = type(msg.media).__name__
    return {
        "id": msg.id,
        "date": msg.date.astimezone(timezone.utc).isoformat() if msg.date else None,
        "text": msg.message or "",
        "reply_to_id": msg.reply_to_msg_id,
        "reply_to_excerpt": reply_to_excerpt,
        "media_type": media_type,
    }


async def fetch_chat_messages(
    client: TelegramClient,
    dialog,
    since: datetime,
    self_user_id: int,
) -> dict | None:
    """Fetch self-authored messages from a chat since a date. Returns None if no messages."""
    entity = dialog.entity
    chat_id = dialog.id
    kind = chat_kind(entity)
    title = chat_title(entity)

    self_messages: list[dict] = []
    total_count = 0
    participants: set[str] = set()

    async for msg in client.iter_messages(entity, offset_date=None, reverse=False):
        if msg.date is None:
            continue
        if msg.date < since:
            break  # older than range; iter_messages is newest-first
        total_count += 1

        # Track participant names (Vladimir + others) for chat metadata
        sender = await msg.get_sender()
        if sender:
            participants.add(chat_title(sender))

        # Only keep messages authored by self
        if msg.sender_id != self_user_id:
            continue
        if not (msg.message or "").strip():
            continue  # skip empty / media-only

        # Reply context (short excerpt only)
        reply_excerpt: str | None = None
        if msg.reply_to_msg_id:
            try:
                reply_msg = await msg.get_reply_message()
                if reply_msg and reply_msg.message:
                    excerpt = reply_msg.message.strip()
                    if len(excerpt) > 200:
                        excerpt = excerpt[:200] + "…"
                    reply_excerpt = excerpt
            except Exception:
                pass  # best-effort

        self_messages.append(message_to_dict(msg, reply_excerpt))

    if not self_messages:
        return None

    return {
        "chat_id": chat_id,
        "chat_title": title,
        "chat_type": kind,
        "participants": sorted(participants),
        "messages_total_count": total_count,
        "messages_authored_by_self_count": len(self_messages),
        "messages_authored_by_self": list(reversed(self_messages)),  # chronological
    }


async def cmd_mine(
    client: TelegramClient,
    chat_filter: str,
    chat_ids: list[int] | None,
    since: datetime,
    output_path: Path,
) -> None:
    me = await client.get_me()
    self_user_id = me.id

    print(f"Mining as: {chat_title(me)} (id={self_user_id})")
    print(f"Since: {since.isoformat()}")
    print(f"Filter: {chat_filter}")
    print(f"Output: {output_path}")
    print()

    chats_data: list[dict] = []
    skipped = 0
    matched = 0

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        kind = chat_kind(entity)
        chat_id = dialog.id

        # Apply filters
        if chat_ids is not None:
            if chat_id not in chat_ids:
                skipped += 1
                continue
        elif chat_filter == "all-private-dms":
            if kind != "private":
                skipped += 1
                continue
        # else: no filter, mine everything (rarely useful)

        matched += 1
        title = chat_title(entity)
        print(f"  [{matched}] mining: {title} (id={chat_id}, type={kind})...", end="", flush=True)

        try:
            chat_data = await fetch_chat_messages(client, dialog, since, self_user_id)
            if chat_data is None:
                print(" no self-authored messages — skipped")
                continue
            chats_data.append(chat_data)
            print(f" {chat_data['messages_authored_by_self_count']} messages")
        except Exception as exc:
            print(f" ERROR: {exc}")
            continue

    output = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exporter": "leto.telegram.mine v1",
        "self_user_id": self_user_id,
        "self_username": me.username,
        "self_display_name": chat_title(me),
        "scope": {
            "since": since.isoformat(),
            "chat_filter": chat_filter,
            "explicit_chat_ids": chat_ids,
        },
        "chats": chats_data,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total_messages = sum(c["messages_authored_by_self_count"] for c in chats_data)
    print()
    print(f"Done. {len(chats_data)} chats, {total_messages} self-authored messages.")
    print(f"Output: {output_path}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Leto — Telegram voice corpus miner.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List all chats with IDs.")

    m = sub.add_parser("mine", help="Mine self-authored messages from selected chats.")
    m.add_argument(
        "--chats",
        type=str,
        default=None,
        help="Comma-separated chat IDs to mine. If omitted, mines all 1:1 DMs.",
    )
    m.add_argument(
        "--since",
        type=str,
        default=None,
        help="ISO date (YYYY-MM-DD). Default: 6 months ago.",
    )
    m.add_argument(
        "--output",
        type=str,
        default=None,
        help=f"Output JSON path. Default: {DEFAULT_OUTPUT_DIR}/export-<timestamp>.json",
    )

    return p.parse_args()


async def main_async() -> int:
    args = parse_args()
    api_id, api_hash, phone, pw_2fa = load_credentials()

    client = TelegramClient(str(SESSION_PATH), api_id, api_hash)
    await client.start(phone=phone, password=pw_2fa)

    try:
        if args.cmd == "list":
            await cmd_list(client)
            return 0

        # mine
        if args.since:
            since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
        else:
            since = datetime.now(timezone.utc) - timedelta(days=180)

        if args.chats:
            chat_ids = [int(x.strip()) for x in args.chats.split(",") if x.strip()]
            chat_filter = "specific-chats"
        else:
            chat_ids = None
            chat_filter = "all-private-dms"

        if args.output:
            output_path = Path(args.output).expanduser().resolve()
        else:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            output_path = DEFAULT_OUTPUT_DIR / f"export-{ts}.json"

        await cmd_mine(client, chat_filter, chat_ids, since, output_path)
        return 0
    finally:
        await client.disconnect()


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
