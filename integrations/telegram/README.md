# Leto — Telegram integration

Telethon-based pull integration for Telegram. Built initially for voice corpus mining (filling the Personal/family/friends gap in `Voice Signature.md`); reusable for Phase 3+ Telegram drafting.

## What this does (V1)

- Lists your Telegram chats with their IDs
- Mines messages **you authored** from selected chats
- Outputs JSON to `~/Projects/Leto/.local-data/telegram/` (gitignored — never lands in any repo)

## What this does NOT do (yet)

- No outbound — Phase 3+ adds drafting/sending with approval
- No real-time intake — pull-based, run when needed
- No MCP wrapper — script-first; if patterns emerge, graduate to a Leto Telegram MCP

## Setup (one-time, ~15 min)

### 1. Get Telegram API credentials

1. Visit https://my.telegram.org and sign in (you'll receive a code in your Telegram app)
2. Click **API development tools**
3. Fill the form (any reasonable values — "Leto" / "personal-ai" works)
4. Note down:
   - `api_id` (a number)
   - `api_hash` (a string)

These are credentials for the Telegram API — keep them private. They're stored locally in `.env`, gitignored.

### 2. Set up Python environment

You need Python 3.8+. Check with `python3 --version`.

```bash
cd ~/Projects/Leto/integrations/telegram
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure credentials

```bash
cp .env.example .env
# edit .env — paste your api_id, api_hash, and phone number (with country code, e.g. +34...)
```

### 4. First-run auth (one-time)

```bash
source venv/bin/activate  # if not already in venv
python mine.py list
```

On first run, Telegram sends a code to your Telegram app. Paste it. If you have 2FA, it'll ask for that too. After auth, a `leto.session` file is created (gitignored) — keeps you logged in for future runs.

`mine.py list` will then print all your chats with their IDs.

### 5. Mine voice corpus

```bash
# Mine ALL your one-on-one DMs (private chats only, no groups/channels) since 6 months ago
python mine.py mine

# Or mine specific chats by ID (from the `list` output)
python mine.py mine --chats 12345,67890

# Custom date range
python mine.py mine --since 2024-11-04

# Custom output path
python mine.py mine --output ~/somewhere-else.json
```

Default output: `~/Projects/Leto/.local-data/telegram/export-<timestamp>.json`.

### 6. Hand the file path to Leto

Tell Leto where the output file is. It'll mine voice patterns and propose additions to `80 System/Voice Signature.md` for your review. Raw Telegram content stays local; only curated voice patterns + ~30 verbatim quotes land in the vault (with your approval per item).

## Privacy

- **Raw exports stay at `.local-data/telegram/`** — gitignored, never committed, never synced
- **`.env` and `leto.session` are gitignored** — credentials never leave your machine
- **Voice mining curates, not copies** — patterns + selected quotes go to vault, not full message history
- **Per-quote approval** — Leto surfaces proposed additions; you approve before commit

## What's in the export JSON

```json
{
  "exported_at": "2026-05-04T...",
  "exporter": "leto.telegram.mine v1",
  "self_user_id": 12345,
  "self_username": "vlmash",
  "scope": {
    "since": "2024-11-04",
    "chat_filter": "all-private-dms" | "specific-chats"
  },
  "chats": [
    {
      "chat_id": -123,
      "chat_title": "Asya",
      "chat_type": "private",
      "participants": ["Vladimir Mashkovtsev", "Asya"],
      "messages_total_count": 245,
      "messages_authored_by_self": [
        {
          "id": 1,
          "date": "2026-04-12T...",
          "text": "...",
          "reply_to_id": null,
          "reply_to_excerpt": null,
          "media_type": null
        }
      ]
    }
  ]
}
```

Only your messages are stored verbatim. Reply context (when you replied to someone) includes a short excerpt of the message you replied to — useful for tone calibration but not full content.

## Polling for replies — `wait_for_reply.py` (added v1.1, 2026-05-04)

Polls a chat for the next inbound signal, exits when one arrives. Two signal types both count as "reply":

1. **New message** from the other party (msg_id > since_id)
2. **New emoji reaction** added to your most recent send (msg_id == since_id)

Used to drive interactive dialog tests paired with `send.py`.

```bash
# Wait up to 10 min for a reply or reaction to msg 284443
python wait_for_reply.py --chat-id 397366400 --since-id 284443 --timeout 600

# Faster polling (every 2s)
python wait_for_reply.py --chat-id 397366400 --since-id 284443 --poll-interval 2
```

Output is JSON to stdout — `{"type": "message", ...}` or `{"type": "reaction", ...}`. Exit code 0 = got signal, 1 = timeout.

## Sending — `send.py` (added v1.1, 2026-05-04)

Single-message outbound with two-checkpoint approval.

### Two-checkpoint approval flow

1. **Draft** — Leto produces draft using `Voice Signature.md`. You review in chat.
2. **Send** — You run `send.py` with the message. Script shows recipient + preview + Y/n confirmation. Only on `y` does it actually call Telethon's send.

### Usage

```bash
# Inline message
python send.py --chat-id 397366400 --message "Hello"

# Read from file (preferred for multi-line / non-trivial)
python send.py --chat-id 397366400 --file /tmp/draft.txt

# Stdin (paste message, Ctrl-D to end)
python send.py --chat-id 397366400

# Dry-run — preview + confirm + LOG, but do NOT actually send
python send.py --chat-id 397366400 --message "Test" --dry-run

# Skip Y/n prompt (CAREFUL — bypasses the second checkpoint)
python send.py --chat-id 397366400 --message "..." --yes
```

### Hard exclusions

- **Cannot send to broadcast channels** — use Slack / email for announcements.
- **Cannot send to bots** — operationally pointless, refused.
- **HR-shaped recipients** (per Voice Signature.md / Leto guardrails) — `send.py` doesn't enforce per-recipient exclusions; that's the LETO/persona layer's job. When wired into Phase 3 flow, the calling layer applies the HR-shaped block before invoking `send.py`.

### Audit log

Every send (real, dry-run, error) is logged to `.local-data/telegram/sent-log.jsonl` (append-only JSONL). Includes timestamp, recipient, message text, sent_message_id, status. The full message text is logged so you can audit later.

### Privacy

- Logs land in `.local-data/` which is gitignored — never enters the Leto or vault repos.
- Session reuses the existing `leto.session` (no fresh auth needed).
- Connection torn down after each send.

## Future use cases

- **Phase 3 full draft flow** — `00 Inbox/Drafts/telegram/<slug>/{source.md, extract.md, decision.md}` per the tier-3-drafts.md design. Vladimir flips `decision.md` `status: approved` → scheduled task picks up, calls `send.py`, posts.
- **Intake** — scheduled `leto-telegram-intake` task pulls new messages on a cadence (mirroring `leto-granola-intake`).
- **MCP wrap** — if patterns emerge across multiple use cases, wrap as `mcp__leto-telegram` for native invocation.

## Troubleshooting

- **"FloodWaitError"** — Telegram rate-limited you. Wait the indicated seconds, retry.
- **Session expired** — delete `leto.session`, re-run, re-auth.
- **Chat not in `list` output** — make sure you've opened that chat at least once in any Telegram client. Telethon only sees chats your account has interacted with.
- **2FA password not working** — make sure it's the cloud password (the one you set in Telegram → Privacy → Two-Step Verification), not the SMS code.
