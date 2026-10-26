#!/usr/bin/env python3
"""Render the Leto daily brief as Slack Block Kit and post it as the Leto bot.

The routine writes the brief's *content* as JSON (schema below); this script owns the
*layout*, so the brief looks the same every day and the model never hand-formats Slack
markup. RND-### ids are linked to Linear automatically.

Usage:
  brief_blocks.py render <brief.json>          # print both payloads (JSON) — no network
  brief_blocks.py post   <brief.json>          # post both as the bot; exit 1 on failure
  brief_blocks.py mrkdwn <brief.json>          # plain-text fallback for the Slack connector,
                                               # messages separated by a line '-----'

Token: $LETO_SLACK_BOT_TOKEN, else $SLACK_BOT_TOKEN. Leto has its own variable name
because a shared cloud environment can hold another app's SLACK_BOT_TOKEN. On 2026-10-26,
Default held a token with only channels:history,users:read. Before posting, the script
checks with auth.test that the token is the Leto bot and has chat:write. Transport is
curl with the header on stdin, so the token never reaches argv (same reason as
hooks/leto_secrets.py).

Schema (every key optional except date_label and today3):
{
  "date_label": "Tuesday, 27 Oct",
  "run_note": "manual run 17:25 · window: rest of today + tomorrow to 13:00",
  "today3":   [{"action": "...", "why": "... RND-471 ...", "bring": "..."}],
  "prep":     [{"time": "11:00", "who": "Irina", "they_owe": "...", "you_owe": "...", "decide": "..."}],
  "at_risk":  ["RND-471 Intercom trial testing — due Thu 30 Oct"],
  "captured": ["RND-501 Send the triage-teams list to Irina"],
  "waiting":  [{"who": "Anya", "where": "DM", "what": "...", "link": "https://..."}],
  "didnt_get":["Weekly Planning 10:30 — not recorded in Granola"],
  "ai":       [{"title": "...", "url": "https://...", "source": "Anthropic", "date": "24 Oct", "why": "..."}],
  "ideas":    [{"idea": "...", "target": "Insights Hub v.2 · KR 2.2", "first_step": "..."}],
  "warning":  null
}
"""
import json
import os
import re
import subprocess
import sys

CHANNEL = "U06A5QCK073"
LINEAR = "https://linear.app/manychat/issue/"
ISSUE = re.compile(r"(?<![\w/|<])(RND-\d+)\b")
SECTION_MAX = 2900  # Slack hard limit is 3000 per section text


def link_ids(text):
    return ISSUE.sub(lambda m: f"<{LINEAR}{m.group(1)}|{m.group(1)}>", text or "")


def section(text):
    return {"type": "section", "text": {"type": "mrkdwn", "text": text[:SECTION_MAX]}}


def context(text):
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": text[:SECTION_MAX]}]}


def header(text):
    return {"type": "header", "text": {"type": "plain_text", "text": text[:150], "emoji": False}}


DIVIDER = {"type": "divider"}


def message_one(b):
    blocks = [header(b["date_label"])]
    if b.get("warning"):
        blocks.append(context(f"Sent from your account · {b['warning']}"))
    if b.get("run_note"):
        blocks.append(context(b["run_note"]))

    blocks.append(section("*Today's 3*"))
    for i, item in enumerate(b["today3"][:3], 1):
        lines = [f"*{i}  {item['action']}*", link_ids(item.get("why", ""))]
        if item.get("bring"):
            lines.append(f"_Bring:_ {link_ids(item['bring'])}")
        blocks.append(section("\n".join(l for l in lines if l)))

    if b.get("prep"):
        blocks += [DIVIDER, section("*Prep*")]
        for p in b["prep"][:3]:
            parts = [f"*{p.get('time', '')}  {p.get('who', '')}*".strip()]
            for key, label in (("they_owe", "They owe you"), ("you_owe", "You owe"), ("decide", "Get a decision on")):
                if p.get(key):
                    parts.append(f"{label}: {link_ids(p[key])}")
            blocks.append(section("\n".join(parts)))

    if b.get("at_risk"):
        blocks += [DIVIDER, section("*At risk*\n" + "\n".join(f"• {link_ids(r)}" for r in b["at_risk"][:5]))]

    if b.get("waiting"):
        rows = []
        for w in b["waiting"][:3]:
            who = f"<{w['link']}|{w['who']}>" if w.get("link") else w.get("who", "")
            rows.append(f"• {who} ({w.get('where', '')}): {w.get('what', '')}")
        blocks += [DIVIDER, section("*Waiting on you*\n" + "\n".join(rows))]

    footer = []
    if b.get("captured"):
        footer.append("Captured to Triage: " + ", ".join(link_ids(c) for c in b["captured"]))
    if b.get("didnt_get"):
        footer.append("Not in this brief: " + "; ".join(b["didnt_get"]))
    if footer:
        blocks += [DIVIDER, context("\n".join(footer))]

    first = b["today3"][0]["action"] if b["today3"] else "Brief"
    return {"channel": CHANNEL, "text": f"{b['date_label']} — 1. {first}", "blocks": blocks,
            "unfurl_links": False, "unfurl_media": False}


def message_two(b):
    if not b.get("ai") and not b.get("ideas"):
        return None
    blocks = [header("AI this week")]
    if b.get("ai"):
        for a in b["ai"][:5]:
            title = f"<{a['url']}|{a['title']}>" if a.get("url") else a["title"]
            blocks.append(section(f"*{title}*\n{a.get('why', '')}"))
            meta = " · ".join(x for x in (a.get("source"), a.get("date")) if x)
            if meta:
                blocks.append(context(meta))
    else:
        blocks.append(context("Quiet week: nothing dated in the last 14 days was worth your time."))
    if b.get("ideas"):
        blocks += [DIVIDER, section("*Try this*")]
        for i, idea in enumerate(b["ideas"][:3], 1):
            lines = [f"*{i}  {idea['idea']}*"]
            if idea.get("target"):
                lines.append(f"For: {link_ids(idea['target'])}")
            if idea.get("first_step"):
                lines.append(f"First step: {link_ids(idea['first_step'])}")
            blocks.append(section("\n".join(lines)))
    return {"channel": CHANNEL, "text": "AI this week", "blocks": blocks,
            "unfurl_links": False, "unfurl_media": False}


def payloads(b):
    return [p for p in (message_one(b), message_two(b)) if p]


def as_mrkdwn(payload):
    """Flatten blocks to mrkdwn for the connector fallback (no Block Kit there)."""
    out = []
    for blk in payload["blocks"]:
        t = blk["type"]
        if t == "header":
            out.append(f"*{blk['text']['text']}*")
        elif t == "section":
            out.append(blk["text"]["text"])
        elif t == "context":
            out.append("_" + blk["elements"][0]["text"].replace("\n", "_\n_") + "_")
        elif t == "divider":
            out.append("")
    return "\n".join(out).strip()


def check_token(token):
    """Return None if the token is the Leto bot with chat:write, else a short reason."""
    r = subprocess.run(
        ["curl", "-sS", "-K", "-", "-D", "-", "-X", "POST", "https://slack.com/api/auth.test"],
        input=f'header = "Authorization: Bearer {token}"\n', capture_output=True, text=True, timeout=30)
    parts = re.split(r"\r?\n\r?\n", r.stdout, maxsplit=1)  # text=True already folds CRLF to LF
    head, body = (parts + [""])[:2]
    scopes = next((l.split(":", 1)[1].strip() for l in head.splitlines()
                   if l.lower().startswith("x-oauth-scopes:")), "")
    try:
        resp = json.loads(body)
    except ValueError:
        return f"auth.test unreachable ({(r.stderr or 'no response').strip()[:120]})"
    if not resp.get("ok"):
        return f"auth.test failed ({resp.get('error')})"
    if "chat:write" not in scopes.split(","):
        return f"token is not the Leto bot (user={resp.get('user')}, scopes={scopes})"
    return None


def post(payload, token):
    cfg = (f'header = "Authorization: Bearer {token}"\n'
           'header = "Content-Type: application/json; charset=utf-8"\n')
    with open("/tmp/leto-brief-payload.json", "w") as f:
        json.dump(payload, f)
    r = subprocess.run(
        ["curl", "-sS", "-K", "-", "-X", "POST", "https://slack.com/api/chat.postMessage",
         "--data-binary", "@/tmp/leto-brief-payload.json"],
        input=cfg, capture_output=True, text=True, timeout=30)
    try:
        resp = json.loads(r.stdout)
    except ValueError:
        return False, (r.stderr or r.stdout or "no response").strip()[:200]
    if resp.get("ok"):
        return True, "ok"
    detail = resp.get("error", "unknown")
    if resp.get("needed") or resp.get("provided"):
        detail += f"; needed={resp.get('needed')} provided={resp.get('provided')}"
    if resp.get("response_metadata", {}).get("messages"):
        detail += f"; {resp['response_metadata']['messages'][:3]}"
    return False, detail


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("render", "post", "mrkdwn"):
        print(__doc__.split("Schema")[0].strip(), file=sys.stderr)
        sys.exit(2)
    brief = json.load(open(sys.argv[2]))
    msgs = payloads(brief)
    if sys.argv[1] == "render":
        print(json.dumps(msgs, indent=1, ensure_ascii=False))
    elif sys.argv[1] == "mrkdwn":
        print("\n-----\n".join(as_mrkdwn(m) for m in msgs))
    else:
        token = os.environ.get("LETO_SLACK_BOT_TOKEN") or os.environ.get("SLACK_BOT_TOKEN", "")
        if not token:
            print("FAILED: no LETO_SLACK_BOT_TOKEN / SLACK_BOT_TOKEN in the environment", file=sys.stderr)
            sys.exit(1)
        problem = check_token(token)
        if problem:
            print(f"FAILED: {problem}", file=sys.stderr)
            sys.exit(1)
        for m in msgs:
            ok, detail = post(m, token)
            print(f"{'sent' if ok else 'FAILED'}: {m['text'][:60]} ({detail})")
            if not ok:
                sys.exit(1)


if __name__ == "__main__":
    main()
