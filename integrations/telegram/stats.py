#!/usr/bin/env python3
"""
Quick stats — for each private DM, count self-authored messages in the last N years.
Sort descending. Surfaces who Vladimir talks to most. Excludes already-mined chats.

Uses a SEPARATE session file (`leto-stats.session`) to run alongside the main miner
without contention. Make a copy first:

    cp leto.session leto-stats.session

Run:
    venv/bin/python -u stats.py
    venv/bin/python -u stats.py --years 5 --top 50 --include-groups
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import User, Chat, Channel

SCRIPT_DIR = Path(__file__).resolve().parent
SESSION_PATH = SCRIPT_DIR / "leto-stats.session"

# Already mined — exclude from stats
ALREADY_MINED = {
    397366400,    # Жена 😻
    2649179,      # АВ Фролов (uncle)
    321095003,    # Марина Фролова (uncle's wife)
    79833350,     # Катя Фролова (cousin's wife)
    1815998512,   # Алла Машковцева (cousin)
    51154358,     # Саша Фролов (cousin)
    125167890,    # Таня Дворкина (close friend)
    767358841,    # Светлана Бузенкова (mother-in-law)
    198862489,    # Ася (Asya, Perm)
    737089016,    # Вадик Опутин (Vadik, Perm)
    1424502,      # Саша Белов (Tarragona ex-Tutu)
    71102605,     # Ариэль Лейва (Ariel, Tarragona)
}


def chat_kind(entity) -> str:
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


async def count_self_messages(client, entity, since, self_id) -> int:
    """Count Vladimir's authored text messages in this chat since `since`."""
    count = 0
    try:
        # Server-side filter by from_user — much faster than iterating all messages
        async for msg in client.iter_messages(entity, from_user=self_id):
            if msg.date is None:
                continue
            if msg.date < since:
                break  # newest-first iteration; older than range, stop
            if msg.message and msg.message.strip():
                count += 1
    except Exception:
        return -1  # signal error
    return count


async def main_async(years: int, top: int, include_groups: bool):
    load_dotenv(SCRIPT_DIR / ".env")
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")

    client = TelegramClient(str(SESSION_PATH), api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        print("ERROR: leto-stats.session is not authorized. Run `cp leto.session leto-stats.session` first.", file=sys.stderr)
        await client.disconnect()
        return 1

    me = await client.get_me()
    self_id = me.id
    since = datetime.now(timezone.utc) - timedelta(days=years * 365)

    print(f"Counting self-authored text messages since {since.isoformat()[:10]} ({years}y)...")
    print(f"Excluding {len(ALREADY_MINED)} already-mined chats.")
    print()

    results = []  # list of (count, chat_id, kind, title)
    scanned = 0

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        kind = chat_kind(entity)

        if kind == "private":
            pass  # always include
        elif kind in ("group", "supergroup") and include_groups:
            pass
        else:
            continue

        if dialog.id in ALREADY_MINED:
            continue

        scanned += 1
        if scanned % 20 == 0:
            print(f"  scanned {scanned} chats...", file=sys.stderr)

        title = chat_title(entity)
        count = await count_self_messages(client, entity, since, self_id)
        if count > 0:
            results.append((count, dialog.id, kind, title))

    await client.disconnect()

    results.sort(reverse=True)
    print()
    print(f"=== Top {top} chats by Vladimir's self-message count (last {years}y) ===")
    print(f"{'Count':>6}  {'ID':>15}  {'Type':<10}  Title")
    print("-" * 90)
    for count, chat_id, kind, title in results[:top]:
        print(f"{count:>6}  {chat_id:>15}  {kind:<10}  {title[:60]}")

    return 0


def main():
    p = argparse.ArgumentParser(description="Stats: who Vladimir talked to most.")
    p.add_argument("--years", type=int, default=5)
    p.add_argument("--top", type=int, default=50)
    p.add_argument("--include-groups", action="store_true",
                   help="Also count messages in groups/supergroups (slower).")
    args = p.parse_args()
    sys.exit(asyncio.run(main_async(args.years, args.top, args.include_groups)))


if __name__ == "__main__":
    main()
