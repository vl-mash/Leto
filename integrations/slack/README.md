# Slack — Leto bot integration

v0 — bot identity for clean Slack notifications. Replaces the current "send to self via user token" pattern. After v0, Slack DMs from Leto render as `Leto` (the bot) rather than from Vladimir, and notifications fire by Slack's standard rules.

## What's here

| File | Purpose |
|---|---|
| `manifest.yaml` | Slack App manifest. Minimal scopes (`chat:write`, `im:write`). v1+ will add events/commands/socket mode separately. |
| `leto-icon.png` | 512×512 bot avatar — `:heart_babble_manychat:` (Vladimir's favorite Slack reaction). Upload via App dashboard → Display Information. |
| `leto-icon-source.webp` | Original 128×128 emoji as downloaded from Slack workspace. Source-of-truth for re-rendering at other sizes. |
| `leto-bot-post.sh` | Helper script — reads bot token from a file, posts to `chat.postMessage`. Schedulers call this instead of the user-token MCP `slack_send_message`. |
| `README.md` | This file. |

## One-time setup (Vladimir)

### 1. Create the Slack app

1. Open <https://api.slack.com/apps> and click **Create New App** → **From a manifest**.
2. Pick the Manychat workspace.
3. Paste the contents of `manifest.yaml` (YAML tab).
4. Review scopes (`chat:write`, `im:write` only — minimal for v0). Click **Create**.

### 2. Set the icon

Sidebar → **Basic Information** → scroll to **Display Information** → **App icon** → upload `leto-icon.png` (512×512, the heart-babble Manychat emoji). This is the avatar you'll see on every bot DM.

### 3. Install to the workspace

1. Sidebar → **Install App** → **Install to Workspace**.
2. If Manychat workspace requires admin approval, you'll see "Request to Install" instead — submit and wait. (Likely outcome on managed workspaces. The minimal scope helps.)
3. After install, copy the **Bot User OAuth Token** (starts with `xoxb-`). This is the credential the bot uses to post.

### 4. Save the token locally

```bash
mkdir -p ~/.config/leto
chmod 700 ~/.config/leto
# Paste the xoxb-... token. ⚠️ Never commit this file. Already gitignored at the repo level.
echo 'xoxb-PASTE-YOUR-TOKEN-HERE' > ~/.config/leto/slack-bot-token
chmod 600 ~/.config/leto/slack-bot-token
```

The path is configurable via `LETO_BOT_TOKEN_FILE` env var if you want a different location (e.g., a Keychain-backed file).

### 5. Test

```bash
~/Projects/Leto/integrations/slack/leto-bot-post.sh U06A5QCK073 "Hello from Leto v0 bot"
```

Expected output: a JSON blob with `"ok": true` and a `"ts": "..."` field. Check your Slack — you should get a DM from Leto.

If you get `not_in_channel` or a similar error: open a DM with the Leto bot in Slack (search for "Leto" in the DM list) — first DM may need to be initiated from your side.

If you get `not_authed` / `invalid_auth`: the token is wrong or the file has whitespace.

## Cutover (Claude — Phase 3)

Once you confirm the test works, ping me and I'll:

1. Update the 4 Slack-sending schedulers (`daily-brief`, `weekly-review`, `notion-alignment`, `personal-backlog-eod`) to call `leto-bot-post.sh` via the Bash tool, capturing the `ts` from the JSON response.
2. Remove the `<@U06A5QCK073>` self-mention hack — bot DMs notify natively.
3. Commit.

After cutover, the user-token Slack MCP (`mcp__bb6718...`) stays in use for *reading* (search, threads, reactions) since bots don't have those scopes. Bot is write-only in v0.

## v1 setup — Socket Mode + slash commands (VM-9 / VM-10 / VM-11)

### 1. Enable Socket Mode in the Slack app dashboard

1. Open <https://api.slack.com/apps> → Leto app.
2. Sidebar → **Settings** → **Socket Mode** → toggle **Enable Socket Mode**.
3. You'll be prompted to create an app-level token. Name it anything (e.g., `leto-socket`), add the `connections:write` scope, click **Generate**.
4. Copy the `xapp-...` token.

### 2. Save the app-level token

```bash
echo 'xapp-PASTE-YOUR-TOKEN-HERE' > ~/.config/leto/slack-app-token
chmod 600 ~/.config/leto/slack-app-token
```

### 3. Update the app manifest

In the Slack app dashboard: **App Manifest** → paste the updated `manifest.yaml` (now has `socket_mode_enabled: true` and the `/leto` slash command). Save.

If prompted to reinstall: do so — this picks up the new slash command registration.

### 4. Install the Python listener

```bash
cd ~/Projects/Leto/integrations/slack
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Smoke test

```bash
python listener.py
```

Expected output:
```
2026-05-07T14:00:00 INFO Leto bot ready — connecting via Socket Mode
2026-05-07T14:00:01 INFO Connected to Slack
```

Then in Slack: type `/leto today` in any channel or DM. The bot should reply with "⏳ `/leto today` received — command dispatch coming in VM-10."

If you see `FileNotFoundError` for `slack-app-token`: step 2 above.
If you see `invalid_auth`: check both tokens are correct and the app is installed.

### 6. Stop

`Ctrl-C`. The daemon packaging (launchd auto-start) is VM-11.

## What v0 does NOT do

- No slash commands (v1)
- No event subscriptions / inbound (v1)
- No socket mode listener (v1)
- No reaction handling (v1)
- No drafts in your voice (v2)

## Security notes

- Token is workspace-scoped (Manychat). If you leave Manychat, the token becomes invalid — re-run setup elsewhere.
- Token file at `~/.config/leto/slack-bot-token` mode 600 — readable only by you.
- Rotation: Slack app dashboard → OAuth & Permissions → re-install to rotate. Tokens don't auto-rotate (config in manifest sets `token_rotation_enabled: false` because v0 is read-only-from-Slack-side; rotation adds operational complexity for a single-user setup).
- Audit: every `chat.postMessage` is logged in Slack workspace audit logs as the bot user, distinct from your user activity.
