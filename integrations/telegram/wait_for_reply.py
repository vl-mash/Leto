#!/usr/bin/env python3
"""
Leto — wait for next inbound signal from a specific Telegram chat.

Two signal types both count as "reply":
  1. New message from the OTHER party (msg_id > since_id)
  2. New emoji reaction added to the message you sent (msg_id == since_id)

Polls every --poll-interval seconds. Returns first signal as JSON, exits.

Usage:
    python wait_for_reply.py --chat-id 397366400 --since-id 12345 --timeout 600

Exit codes:
    0  — got a signal, printed JSON to stdout
    1  — timed out (no signal within --timeout seconds)
    2  — config or auth error

Output JSON:
    {"type": "message", "id": ..., "date": "...", "from_id": ..., "text": "...", "reply_to_id": ...}
    {"type": "reaction", "to_msg_id": <since_id>, "reactions": [{"emoticon": "❤", "from_self": false}, ...]}
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

SCRIPT_DIR = Path(__file__).resolve().parent
SESSION_PATH = SCRIPT_DIR / "leto.session"


def extract_reactions(msg, self_id: int) -> list[dict]:
    """Pull recent_reactions from a Message into a flat list, filtering self-reactions out."""
    out = []
    if not getattr(msg, "reactions", None):
        return out
    reactions = msg.reactions
    # recent_reactions is a list of MessagePeerReaction with .peer_id and .reaction
    recent = getattr(reactions, "recent_reactions", None) or []
    for r in recent:
        peer_id = None
        try:
            # peer_id can be a PeerUser, PeerChat, or PeerChannel
            peer = getattr(r, "peer_id", None)
            if peer is not None:
                peer_id = getattr(peer, "user_id", None) or getattr(peer, "channel_id", None) or getattr(peer, "chat_id", None)
        except Exception:
            pass
        # reaction can be ReactionEmoji (with .emoticon) or ReactionCustomEmoji (with .document_id)
        reaction = getattr(r, "reaction", None)
        emoticon = getattr(reaction, "emoticon", None)
        document_id = getattr(reaction, "document_id", None)
        from_self = (peer_id == self_id) if peer_id else False
        if from_self:
            continue  # skip our own reactions
        out.append({
            "emoticon": emoticon,
            "custom_emoji_document_id": document_id,
            "from_peer_id": peer_id,
        })
    # Fallback: if recent_reactions empty but counts present in private chat,
    # treat any non-zero as peer reaction (since 1:1 = either us or them)
    if not out:
        results = getattr(reactions, "results", None) or []
        for r in results:
            count = getattr(r, "count", 0)
            if count > 0:
                reaction = getattr(r, "reaction", None)
                emoticon = getattr(reaction, "emoticon", None)
                document_id = getattr(reaction, "document_id", None)
                # In a 1:1 chat, count > 0 + we didn't react = peer reacted
                out.append({
                    "emoticon": emoticon,
                    "custom_emoji_document_id": document_id,
                    "count": count,
                    "from_peer_id": None,
                })
    return out


async def main_async(chat_id: int, since_id: int, timeout: int, poll_interval: int) -> int:
    load_dotenv(SCRIPT_DIR / ".env")
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not SESSION_PATH.exists():
        print("No session file. Authenticate via mine.py list first.", file=sys.stderr)
        return 2

    client = TelegramClient(str(SESSION_PATH), api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        print("Session not authorized.", file=sys.stderr)
        await client.disconnect()
        return 2

    me = await client.get_me()
    self_id = me.id

    # Capture initial reactions on the since_id message so we only return NEW reactions
    initial_reactions = []
    if since_id > 0:
        try:
            initial_msgs = await client.get_messages(chat_id, ids=since_id)
            if initial_msgs:
                initial_reactions = extract_reactions(initial_msgs, self_id)
        except Exception:
            pass

    deadline = asyncio.get_event_loop().time() + timeout
    print(f"Polling chat {chat_id}: messages > {since_id} OR new reactions on msg {since_id} (timeout={timeout}s)...", file=sys.stderr)

    def reactions_changed(initial: list[dict], current: list[dict]) -> bool:
        # Simple comparison by emoticons present
        initial_set = {r.get("emoticon") for r in initial if r.get("emoticon")}
        current_set = {r.get("emoticon") for r in current if r.get("emoticon")}
        return current_set != initial_set and len(current_set) > 0

    while asyncio.get_event_loop().time() < deadline:
        # 1) Check for new message
        try:
            latest_msgs = await client.get_messages(chat_id, limit=1)
        except Exception as exc:
            print(f"Fetch error (latest): {exc}", file=sys.stderr)
            await asyncio.sleep(poll_interval)
            continue

        if latest_msgs:
            msg = latest_msgs[0]
            if msg.sender_id != self_id and msg.id > since_id:
                payload = {
                    "type": "message",
                    "id": msg.id,
                    "date": msg.date.astimezone(timezone.utc).isoformat() if msg.date else None,
                    "from_id": msg.sender_id,
                    "text": msg.message or "",
                    "reply_to_id": msg.reply_to_msg_id,
                }
                print(json.dumps(payload, ensure_ascii=False))
                await client.disconnect()
                return 0

        # 2) Check for new reaction on since_id
        if since_id > 0:
            try:
                target = await client.get_messages(chat_id, ids=since_id)
                if target:
                    current_reactions = extract_reactions(target, self_id)
                    if reactions_changed(initial_reactions, current_reactions):
                        payload = {
                            "type": "reaction",
                            "to_msg_id": since_id,
                            "reactions": current_reactions,
                        }
                        print(json.dumps(payload, ensure_ascii=False))
                        await client.disconnect()
                        return 0
            except Exception:
                pass

        await asyncio.sleep(poll_interval)

    print("TIMEOUT — no message or reaction within window.", file=sys.stderr)
    await client.disconnect()
    return 1


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Wait for next inbound Telegram signal (message OR reaction).")
    p.add_argument("--chat-id", type=int, required=True)
    p.add_argument("--since-id", type=int, default=0,
                   help="Reference message id. New messages must have id > this. Reactions are checked on this exact message.")
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--poll-interval", type=int, default=5)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    return asyncio.run(main_async(args.chat_id, args.since_id, args.timeout, args.poll_interval))


if __name__ == "__main__":
    sys.exit(main())
