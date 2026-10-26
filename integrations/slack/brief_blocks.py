#!/usr/bin/env python3
"""Render the Leto daily brief as Slack Block Kit and post it as the Leto bot.

The routine writes the brief's *content* as JSON (schema below); this script owns the
*layout*, so the brief looks the same every day and the model never hand-formats Slack
markup. RND-### ids are linked to Linear automatically.

Usage:
  brief_blocks.py render <brief.json> [style]  # print the payloads (JSON) — no network
  brief_blocks.py post   <brief.json> [style]  # post as the bot; exit 1 on failure
  styles: cards (default) · compact · glance · digest; "style" in brief.json also works
  brief_blocks.py mrkdwn <brief.json>          # plain-text fallback for the Slack connector,
                                               # messages separated by a line '-----'
  brief_blocks.py check                        # verify the token is the Leto bot; posts nothing
  brief_blocks.py render-doc|post-doc|mrkdwn-doc <doc.json>
                                               # generic cards document (weekly politics brief);
                                               # schema in render_doc()'s docstring

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
  "week":     {"label": "Week of 27 Oct", "last_week": "6 done: RND-466, RND-478 … · KR 1.2 didn't move",
               "three": [{"outcome": "...", "why": "..."}], "stuck": ["RND-450 … · 9 days"],
               "due": ["RND-471 · Thu 30 Oct"],
               "teo": {"when": "Thu 14:00", "tell": "...", "ask": "...", "flag": "..."}},   # Mondays only
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


def render_doc(doc, channel=CHANNEL):
    """Generic cards document, used by the Monday week message and the weekly politics brief.

    doc = {"title": "...", "subtitle": "...", "sections": [{"heading": "...", "note": "...",
           "items": [{"title": "...", "body": "...", "meta": "..."}]}], "footer": "..."}
    Items: title in bold, body under it, meta as a small grey line (use it for sources and dates).
    """
    blocks = [header(doc["title"])]
    if doc.get("subtitle"):
        blocks.append(context(doc["subtitle"]))
    for sec in doc.get("sections", []):
        if not sec.get("items") and not sec.get("note"):
            continue
        blocks += [DIVIDER, section(f"*{sec['heading']}*")]
        if sec.get("note"):
            blocks.append(context(link_ids(sec["note"])))
        for it in sec.get("items", [])[:5]:
            text = "\n".join(x for x in (f"*{link_ids(it['title'])}*" if it.get("title") else "",
                                         link_ids(it.get("body", ""))) if x)
            if text:
                blocks.append(section(text))
            if it.get("meta"):
                blocks.append(context(link_ids(it["meta"])))
    if doc.get("footer"):
        blocks += [DIVIDER, context(link_ids(doc["footer"]))]
    if len(blocks) > 50:  # Slack's hard cap; keep the head, say what was cut
        blocks = blocks[:49] + [context("Trimmed to fit Slack's 50-block limit.")]
    return {"channel": channel, "text": doc["title"], "blocks": blocks,
            "unfurl_links": False, "unfurl_media": False}


def message_week(b):
    """Monday-only weekly shape (b["week"]), drawn as a cards document."""
    w = b.get("week")
    if not w:
        return None
    teo = w.get("teo") or {}
    teo_lines = "\n".join(f"{k.capitalize()}: {v}" for k, v in (("tell", teo.get("tell")), ("ask", teo.get("ask")),
                                                                   ("flag", teo.get("flag"))) if v)
    doc = {"title": w.get("label", "This week"), "sections": [
        {"heading": "Last week", "note": w.get("last_week", "")},
        {"heading": "This week's 3", "items": [
            {"title": f"{i}  {t['outcome']}", "body": t.get("why", "")} for i, t in enumerate(w.get("three", [])[:3], 1)]},
        {"heading": "Stuck", "note": "\n".join(f"• {s}" for s in w.get("stuck", [])[:4])},
        {"heading": "Due this week", "note": "\n".join(f"• {d}" for d in w.get("due", [])[:5])},
        {"heading": f"Teo 1:1 · {teo['when']}" if teo.get("when") else "Teo 1:1",
         "items": [{"body": teo_lines}] if teo_lines else []},
    ]}
    return render_doc(doc)


def style_cards(b):
    """A, the original: numbered cards with bold action, why and bring lines, dividers, plus a second message for AI.
    On Mondays a weekly-shape message sits between them."""
    return [p for p in (message_one(b), message_week(b), message_two(b)) if p]


def _ai_compact(b, title="AI this week"):
    blocks = [header(title)]
    for a in (b.get("ai") or [])[:5]:
        link = f"<{a['url']}|{a['title']}>" if a.get("url") else a["title"]
        meta = " · ".join(x for x in (a.get("source"), a.get("date")) if x)
        blocks += [section(f"*{link}*"), context(" · ".join(x for x in (a.get("why"), meta) if x))]
    if b.get("ideas"):
        blocks += [DIVIDER, section("*Try this*")]
        for idea in b["ideas"][:3]:
            bits = [link_ids(idea.get("target", "")), link_ids(idea.get("first_step", ""))]
            blocks += [section(f"*{idea['idea']}*"),
                       context(" · ".join(x for x in (f"For {bits[0]}" if bits[0] else "", f"First step: {bits[1]}" if bits[1] else "") if x))]
    return blocks


def style_compact(b):
    """B: bold one-line actions with small grey 'why' under each, and a 2-column grid for prep, risks and waiting."""
    blocks = [header(b["date_label"])]
    for note in (b.get("warning") and f"Sent from your account · {b['warning']}", b.get("run_note")):
        if note:
            blocks.append(context(note))
    for i, item in enumerate(b["today3"][:3], 1):
        blocks.append(section(f"*{i}.  {item['action']}*"))
        grey = link_ids(item.get("why", ""))
        if item.get("bring"):
            grey += f"  ·  Bring: {link_ids(item['bring'])}"
        blocks.append(context(grey))
    cells = []
    if b.get("prep"):
        cells.append("*Prep*\n" + "\n".join(
            f"{p.get('time', '')} {p.get('who', '')}: {link_ids(p.get('decide') or p.get('you_owe') or '')}".strip()
            for p in b["prep"][:3]))
    if b.get("at_risk"):
        cells.append("*At risk*\n" + "\n".join(link_ids(r) for r in b["at_risk"][:4]))
    if b.get("waiting"):
        cells.append("*Waiting on you*\n" + "\n".join(
            (f"<{w['link']}|{w['who']}>" if w.get("link") else w.get("who", "")) + f": {w.get('what', '')}"
            for w in b["waiting"][:3]))
    if b.get("captured"):
        cells.append("*Captured*\n" + "\n".join(link_ids(c) for c in b["captured"][:4]))
    if cells:
        blocks += [DIVIDER, {"type": "section", "fields": [{"type": "mrkdwn", "text": c[:1900]} for c in cells[:10]]}]
    if b.get("didnt_get"):
        blocks.append(context("Not in this brief: " + "; ".join(b["didnt_get"])))
    first = b["today3"][0]["action"] if b["today3"] else "Brief"
    msgs = [{"channel": CHANNEL, "text": f"{b['date_label']} — 1. {first}", "blocks": blocks,
             "unfurl_links": False, "unfurl_media": False}]
    if b.get("ai") or b.get("ideas"):
        msgs.append({"channel": CHANNEL, "text": "AI this week", "blocks": _ai_compact(b),
                     "unfurl_links": False, "unfurl_media": False})
    return msgs


def style_glance(b):
    """C: a glanceable top message (3 actions, one status line), with every detail in a thread reply."""
    lines = "\n".join(f"*{i}.*  {item['action']}" for i, item in enumerate(b["today3"][:3], 1))
    status = []
    if b.get("prep"):
        status.append(" · ".join(f"{p.get('time', '')} {p.get('who', '').split(' ')[0]}" for p in b["prep"][:2]))
    if b.get("at_risk"):
        status.append(f"{len(b['at_risk'])} at risk")
    if b.get("waiting"):
        status.append(f"{len(b['waiting'])} waiting on you")
    if b.get("ai"):
        status.append(f"{len(b['ai'])} AI reads")
    top = [header(b["date_label"]), section(lines)]
    if b.get("warning"):
        top.insert(1, context(f"Sent from your account · {b['warning']}"))
    top.append(context("  ·  ".join(status + ["details in the thread"])))
    detail = message_one(b)["blocks"][1:]  # cards body without the header
    if b.get("ai") or b.get("ideas"):
        detail += [DIVIDER, section("*AI this week*")] + _ai_compact(b)[1:]  # swap the header for a bold line
    first = b["today3"][0]["action"] if b["today3"] else "Brief"
    return [{"channel": CHANNEL, "text": f"{b['date_label']} — 1. {first}", "blocks": top,
             "unfurl_links": False, "unfurl_media": False},
            {"channel": CHANNEL, "text": "Details", "blocks": detail[:50], "_thread": True,
             "unfurl_links": False, "unfurl_media": False}]


def _rich(text, bold=False):
    """Split text into rich_text elements, turning RND ids into links."""
    out, pos = [], 0
    for m in ISSUE.finditer(text or ""):
        if m.start() > pos:
            out.append({"type": "text", "text": text[pos:m.start()], **({"style": {"bold": True}} if bold else {})})
        out.append({"type": "link", "url": LINEAR + m.group(1), "text": m.group(1)})
        pos = m.end()
    if pos < len(text or ""):
        out.append({"type": "text", "text": text[pos:], **({"style": {"bold": True}} if bold else {})})
    return out


def style_digest(b):
    """D: one message with native Slack numbered lists, everything on one line, and AI reduced to linked titles."""
    items = [{"type": "rich_text_section",
              "elements": _rich(item["action"], bold=True) + [{"type": "text", "text": " — "}] + _rich(item.get("why", ""))}
             for item in b["today3"][:3]]
    blocks = [header(b["date_label"])]
    if b.get("warning"):
        blocks.append(context(f"Sent from your account · {b['warning']}"))
    blocks.append({"type": "rich_text", "elements": [{"type": "rich_text_list", "style": "ordered", "elements": items}]})
    rows = []
    if b.get("prep"):
        rows.append("*Prep*  " + "  ·  ".join(
            f"{p.get('time', '')} {p.get('who', '')}: {link_ids(p.get('decide') or p.get('you_owe') or '')}" for p in b["prep"][:2]))
    if b.get("at_risk"):
        rows.append("*At risk*  " + "  ·  ".join(link_ids(r) for r in b["at_risk"][:4]))
    if b.get("waiting"):
        rows.append("*Waiting*  " + "  ·  ".join(f"{w.get('who')} ({w.get('where', '')})" for w in b["waiting"][:3]))
    if b.get("ai"):
        rows.append("*AI*  " + "  ·  ".join(
            (f"<{a['url']}|{a['title']}>" if a.get("url") else a["title"]) + (f" ({a['date']})" if a.get("date") else "")
            for a in b["ai"][:4]))
    if b.get("ideas"):
        rows.append("*Try*  " + "  ·  ".join(f"{i['idea']} → {link_ids(i.get('target', ''))}" for i in b["ideas"][:2]))
    if rows:
        blocks += [DIVIDER] + [context(r) for r in rows]
    if b.get("didnt_get"):
        blocks.append(context("Not in this brief: " + "; ".join(b["didnt_get"])))
    first = b["today3"][0]["action"] if b["today3"] else "Brief"
    return [{"channel": CHANNEL, "text": f"{b['date_label']} — 1. {first}", "blocks": blocks,
             "unfurl_links": False, "unfurl_media": False}]


STYLES = {"cards": style_cards, "compact": style_compact, "glance": style_glance, "digest": style_digest}


def payloads(b, style=None):
    return STYLES[style or b.get("style") or "cards"](b)


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
    """Return None if the token is the Leto bot with chat:write, else a short reason.

    Headers and body go to separate files. Behind the cloud's HTTPS proxy, curl's
    header dump starts with a CONNECT "Connection established" block, so splitting
    stdout on the first blank line broke the first cloud run (2026-10-26).
    """
    hdr, body = "/tmp/leto-auth-headers.txt", "/tmp/leto-auth-body.json"
    r = subprocess.run(
        ["curl", "-sS", "-K", "-", "-D", hdr, "-o", body, "-X", "POST", "https://slack.com/api/auth.test"],
        input=f'header = "Authorization: Bearer {token}"\n', capture_output=True, text=True, timeout=30)
    try:
        scopes = next((l.split(":", 1)[1].strip() for l in open(hdr).read().splitlines()
                       if l.lower().startswith("x-oauth-scopes:")), "")
        resp = json.load(open(body))
    except (OSError, ValueError):
        return f"auth.test unreachable (curl exit {r.returncode}: {(r.stderr or 'no output').strip()[:120]})"
    if not resp.get("ok"):
        return f"auth.test failed ({resp.get('error')})"
    if "chat:write" not in scopes.split(","):
        return f"token is not the Leto bot (user={resp.get('user')}, scopes={scopes})"
    return None


def post(payload, token, thread_ts=None):
    cfg = (f'header = "Authorization: Bearer {token}"\n'
           'header = "Content-Type: application/json; charset=utf-8"\n')
    body = {k: v for k, v in payload.items() if not k.startswith("_")}
    if thread_ts:
        body["thread_ts"] = thread_ts
    with open("/tmp/leto-brief-payload.json", "w") as f:
        json.dump(body, f)
    r = subprocess.run(
        ["curl", "-sS", "-K", "-", "-X", "POST", "https://slack.com/api/chat.postMessage",
         "--data-binary", "@/tmp/leto-brief-payload.json"],
        input=cfg, capture_output=True, text=True, timeout=30)
    try:
        resp = json.loads(r.stdout)
    except ValueError:
        return False, (r.stderr or r.stdout or "no response").strip()[:200]
    if resp.get("ok"):
        return True, resp.get("ts") or "ok"
    detail = resp.get("error", "unknown")
    if resp.get("needed") or resp.get("provided"):
        detail += f"; needed={resp.get('needed')} provided={resp.get('provided')}"
    if resp.get("response_metadata", {}).get("messages"):
        detail += f"; {resp['response_metadata']['messages'][:3]}"
    return False, detail


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "check":
        name = "LETO_SLACK_BOT_TOKEN" if os.environ.get("LETO_SLACK_BOT_TOKEN") else (
            "SLACK_BOT_TOKEN" if os.environ.get("SLACK_BOT_TOKEN") else None)
        if not name:
            print("check: FAILED — neither LETO_SLACK_BOT_TOKEN nor SLACK_BOT_TOKEN is set")
            sys.exit(1)
        problem = check_token(os.environ[name])
        print(f"check: using {name} — " + (f"FAILED — {problem}" if problem else "OK, Leto bot with chat:write"))
        sys.exit(1 if problem else 0)
    if len(sys.argv) == 3 and sys.argv[1] in ("render-doc", "post-doc", "mrkdwn-doc"):
        msg = render_doc(json.load(open(sys.argv[2])))
        if sys.argv[1] == "render-doc":
            print(json.dumps(msg, indent=1, ensure_ascii=False))
        elif sys.argv[1] == "mrkdwn-doc":
            print(as_mrkdwn(msg))
        else:
            token = os.environ.get("LETO_SLACK_BOT_TOKEN") or os.environ.get("SLACK_BOT_TOKEN", "")
            problem = check_token(token) if token else "no LETO_SLACK_BOT_TOKEN / SLACK_BOT_TOKEN in the environment"
            if problem:
                print(f"FAILED: {problem}", file=sys.stderr)
                sys.exit(1)
            ok, detail = post(msg, token)
            print(f"{'sent' if ok else 'FAILED'}: {msg['text'][:60]} ({'ok' if ok else detail})")
            sys.exit(0 if ok else 1)
        return
    if len(sys.argv) not in (3, 4) or sys.argv[1] not in ("render", "post", "mrkdwn") or (
            len(sys.argv) == 4 and sys.argv[3] not in STYLES):
        print(__doc__.split("Schema")[0].strip(), file=sys.stderr)
        sys.exit(2)
    brief = json.load(open(sys.argv[2]))
    style = sys.argv[3] if len(sys.argv) == 4 else None
    msgs = payloads(brief, style)
    if sys.argv[1] == "render":
        print(json.dumps(msgs, indent=1, ensure_ascii=False))
    elif sys.argv[1] == "mrkdwn":
        # The connector fallback has no Block Kit, so it always flattens the cards layout.
        print("\n-----\n".join(as_mrkdwn(m) for m in style_cards(brief)))
    else:
        token = os.environ.get("LETO_SLACK_BOT_TOKEN") or os.environ.get("SLACK_BOT_TOKEN", "")
        if not token:
            print("FAILED: no LETO_SLACK_BOT_TOKEN / SLACK_BOT_TOKEN in the environment", file=sys.stderr)
            sys.exit(1)
        problem = check_token(token)
        if problem:
            print(f"FAILED: {problem}", file=sys.stderr)
            sys.exit(1)
        parent_ts = None
        for m in msgs:
            ok, detail = post(m, token, thread_ts=parent_ts if m.get("_thread") else None)
            print(f"{'sent' if ok else 'FAILED'}: {m['text'][:60]} ({'ok' if ok else detail})")
            if not ok:
                sys.exit(1)
            if not m.get("_thread"):
                parent_ts = detail


if __name__ == "__main__":
    main()
