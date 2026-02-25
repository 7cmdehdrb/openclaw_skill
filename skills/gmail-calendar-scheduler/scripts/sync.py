#!/usr/bin/env python3
import argparse
import base64
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib import parse, request

API_GMAIL = "https://gateway.maton.ai/google-mail/gmail/v1/users/me"
API_CAL = "https://gateway.maton.ai/google-calendar/calendar/v3/calendars/primary/events"

INTENT_RE = re.compile(r"(회의|미팅|약속|일정|면담|콜|call|meeting|appointment|deadline)", re.IGNORECASE)
DATE_PATTERNS = [
    re.compile(r"(20\d{2})[/-](\d{1,2})[/-](\d{1,2})"),
    re.compile(r"(\d{1,2})[/-](\d{1,2})"),
    re.compile(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일"),
]
TIME_PATTERNS = [
    re.compile(r"\b(\d{1,2}):(\d{2})\b"),
    re.compile(r"(오전|오후)\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?"),
    re.compile(r"\b(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?\b"),
]


def read_key():
    k = os.getenv("MATON_API_KEY", "").strip()
    if k:
        return k
    p = Path.home() / ".config/maton/api_key"
    if p.exists():
        return p.read_text().strip()
    raise RuntimeError("MATON_API_KEY not found")


def api_json(url, key, method="GET", body=None):
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    with request.urlopen(req, timeout=30) as r:
        return json.load(r)


def decode_body(payload):
    if not payload:
        return ""
    body = payload.get("body", {})
    if body.get("data"):
        try:
            return base64.urlsafe_b64decode(body["data"] + "==").decode("utf-8", "ignore")
        except Exception:
            pass
    for part in payload.get("parts", []) or []:
        txt = decode_body(part)
        if txt:
            return txt
    return ""


def parse_datetime(text, now_local):
    date_obj = None
    for p in DATE_PATTERNS:
        m = p.search(text)
        if not m:
            continue
        g = m.groups()
        if len(g) == 3 and len(g[0]) == 4:
            y, mo, d = map(int, g)
        else:
            y = now_local.year
            mo, d = map(int, g[-2:])
        try:
            date_obj = datetime(y, mo, d)
            break
        except ValueError:
            continue

    if not date_obj:
        return None, None, True

    hour = minute = None
    for p in TIME_PATTERNS:
        m = p.search(text)
        if not m:
            continue
        g = m.groups()
        if len(g) >= 2 and g[0] in ("오전", "오후"):
            ap, h = g[0], int(g[1])
            mm = int(g[2] or 0)
            if ap == "오후" and h < 12:
                h += 12
            if ap == "오전" and h == 12:
                h = 0
            hour, minute = h, mm
            break
        elif len(g) >= 2 and g[1] is not None:
            hour, minute = int(g[0]), int(g[1])
            break

    if hour is None:
        return date_obj.date().isoformat(), None, True

    start = datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute)
    end = start + timedelta(hours=1)
    return start.isoformat(), end.isoformat(), False


def load_state(path):
    if not path.exists():
        return {
            "thread_latest_processed": {},
            "created_event_by_message": {},
            "last_run_at": None,
        }
    return json.loads(path.read_text())


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=15)
    ap.add_argument("--tz", default="Asia/Seoul")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key = read_key()
    workspace = Path(__file__).resolve().parents[3]
    state_path = workspace / "memory/gmail-calendar-sync-state.json"
    log_path = workspace / "memory/gmail-calendar-processed.jsonl"
    state = load_state(state_path)

    now_local = datetime.now()
    q = parse.urlencode({"maxResults": args.max, "q": "in:inbox", "includeSpamTrash": "false"})
    ids = api_json(f"{API_GMAIL}/messages?{q}", key).get("messages", [])

    created = skipped = errors = 0

    for m in ids:
        mid = m["id"]
        try:
            msg = api_json(f"{API_GMAIL}/messages/{mid}?format=full", key)
            thread_id = msg.get("threadId")
            internal_ms = int(msg.get("internalDate", "0"))

            if state["created_event_by_message"].get(mid):
                skipped += 1
                continue

            prev_thread_ms = int(state["thread_latest_processed"].get(thread_id, 0))
            if internal_ms <= prev_thread_ms:
                skipped += 1
                continue

            headers = {h.get("name", ""): h.get("value", "") for h in msg.get("payload", {}).get("headers", [])}
            subject = headers.get("Subject", "")
            snippet = msg.get("snippet", "")
            body = decode_body(msg.get("payload", {}))
            text = "\n".join([subject, snippet, body])

            if not INTENT_RE.search(text):
                state["thread_latest_processed"][thread_id] = internal_ms
                skipped += 1
                append_jsonl(log_path, {
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "message_id": mid,
                    "thread_id": thread_id,
                    "subject": subject,
                    "action": "skip",
                    "reason": "no_intent_keyword",
                })
                continue

            start, end, all_day = parse_datetime(text, now_local)
            if not start:
                state["thread_latest_processed"][thread_id] = internal_ms
                skipped += 1
                append_jsonl(log_path, {
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "message_id": mid,
                    "thread_id": thread_id,
                    "subject": subject,
                    "action": "skip",
                    "reason": "no_date_detected",
                })
                continue

            event = {
                "summary": subject[:120] or "메일 기반 일정",
                "description": f"Gmail 자동생성\n\nThread: {thread_id}\nMessage: {mid}\n\nSnippet:\n{snippet}",
            }
            if all_day:
                d = start
                next_day = (datetime.fromisoformat(d) + timedelta(days=1)).date().isoformat()
                event["start"] = {"date": d}
                event["end"] = {"date": next_day}
            else:
                event["start"] = {"dateTime": start, "timeZone": args.tz}
                event["end"] = {"dateTime": end, "timeZone": args.tz}

            event_id = None
            if not args.dry_run:
                created_event = api_json(API_CAL, key, method="POST", body=event)
                event_id = created_event.get("id")
                state["created_event_by_message"][mid] = event_id

            state["thread_latest_processed"][thread_id] = internal_ms
            created += 1
            append_jsonl(log_path, {
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "message_id": mid,
                "thread_id": thread_id,
                "subject": subject,
                "action": "create_event" if not args.dry_run else "dry_run_create",
                "event_id": event_id,
                "all_day": all_day,
                "start": event["start"],
                "end": event["end"],
            })

        except Exception as e:
            errors += 1
            append_jsonl(log_path, {
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "message_id": m.get("id"),
                "action": "error",
                "error": str(e),
            })

    state["last_run_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state_path, state)

    print(json.dumps({
        "scanned": len(ids),
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "state": str(state_path),
        "log": str(log_path),
        "dry_run": args.dry_run,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
