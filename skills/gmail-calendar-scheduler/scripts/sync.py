#!/usr/bin/env python3
import argparse
import base64
import json
import os
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib import parse, request

API_GMAIL = "https://gateway.maton.ai/google-mail/gmail/v1/users/me"
API_CAL = "https://gateway.maton.ai/google-calendar/calendar/v3/calendars/primary/events"

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

ACTION_PATTERNS = [
    re.compile(r"(발표|제출|미팅|회의|면담|콜|인터뷰|점검|리뷰|보고|작성|수정|검토|요청|마감)"),
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


def tokenize(text):
    text = (text or "").lower()
    # keep Korean/English/number tokens
    return re.findall(r"[a-zA-Z0-9가-힣]+", text)


def train_nb_from_logs(log_path):
    """Train a tiny multinomial Naive Bayes from historical processed logs.
    Positive: create_event, Negative: skip/no_intent_keyword/no_date_detected.
    """
    pos_counts = {}
    neg_counts = {}
    pos_docs = neg_docs = 0

    if not log_path.exists():
        return None

    for line in log_path.read_text(encoding="utf-8").splitlines():
        try:
            o = json.loads(line)
        except Exception:
            continue
        subject = o.get("subject", "")
        reason = o.get("reason", "")
        action = o.get("action", "")

        label = None
        if action in ("create_event", "dry_run_create"):
            label = 1
        elif action == "skip" and reason in ("no_intent_keyword", "no_date_detected"):
            label = 0
        if label is None:
            continue

        tokens = tokenize(subject)
        if not tokens:
            continue

        if label == 1:
            pos_docs += 1
            for t in tokens:
                pos_counts[t] = pos_counts.get(t, 0) + 1
        else:
            neg_docs += 1
            for t in tokens:
                neg_counts[t] = neg_counts.get(t, 0) + 1

    if pos_docs < 3 or neg_docs < 3:
        return None

    vocab = set(pos_counts.keys()) | set(neg_counts.keys())
    return {
        "pos_counts": pos_counts,
        "neg_counts": neg_counts,
        "pos_docs": pos_docs,
        "neg_docs": neg_docs,
        "vocab_size": max(len(vocab), 1),
        "pos_total": max(sum(pos_counts.values()), 1),
        "neg_total": max(sum(neg_counts.values()), 1),
    }


def nb_predict_schedule_prob(model, text):
    if model is None:
        return 0.0
    tokens = tokenize(text)
    if not tokens:
        return 0.0

    import math
    pos_prior = model["pos_docs"] / (model["pos_docs"] + model["neg_docs"])
    neg_prior = 1.0 - pos_prior
    log_pos = math.log(max(pos_prior, 1e-9))
    log_neg = math.log(max(neg_prior, 1e-9))
    V = model["vocab_size"]

    for t in tokens:
        pc = model["pos_counts"].get(t, 0)
        nc = model["neg_counts"].get(t, 0)
        # Laplace smoothing
        log_pos += math.log((pc + 1) / (model["pos_total"] + V))
        log_neg += math.log((nc + 1) / (model["neg_total"] + V))

    # stable sigmoid from log odds
    z = log_pos - log_neg
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def parse_datetime(text, now_local):
    date_obj = None
    date_match = None
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
            date_match = m
            break
        except ValueError:
            continue

    if not date_obj:
        return None, None, True

    hour = minute = None

    # Prefer explicit Korean time expressions first: 오전/오후, N시
    for p in TIME_PATTERNS[1:]:
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

    # HH:MM is accepted only when near the detected date context (avoid email header/noise time)
    if hour is None:
        for m in TIME_PATTERNS[0].finditer(text):
            hh, mm = int(m.group(1)), int(m.group(2))
            if hh > 23 or mm > 59:
                continue
            if date_match is not None:
                dist = abs(m.start() - date_match.end())
                if dist > 40:
                    continue
            hour, minute = hh, mm
            break

    if hour is None:
        return date_obj.date().isoformat(), None, True

    start = datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute)
    end = start + timedelta(hours=1)
    return start.isoformat(), end.isoformat(), False


def derive_event_title(subject, text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Prefer explicit actionable line from body/snippet
    for l in lines[:20]:
        if any(k in l for k in ["요청", "회의", "미팅", "면담", "콜", "인터뷰", "발표", "제출", "마감", "점검", "리뷰", "보고", "작성", "검토"]):
            cleaned = re.sub(r"^(re:|fwd:|fw:)\s*", "", l, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            if 4 <= len(cleaned) <= 80:
                return cleaned

    # Then use subject but strip mail prefixes/brackets noise
    s = re.sub(r"^(re:|fwd:|fw:)\s*", "", subject or "", flags=re.IGNORECASE)
    s = re.sub(r"\[[^\]]+\]\s*", "", s).strip()
    s = re.sub(r"\s+", " ", s)

    # If subject still looks email-ish and contains action keyword, keep compact chunk
    if s:
        for p in ACTION_PATTERNS:
            m = p.search(s)
            if m:
                return s[:80]

    return (s[:80] if s else "업무 일정")


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
    ap.add_argument("--days", type=int, default=None, help="Gmail lookback window in days (e.g., 90)")
    ap.add_argument("--ignore-state", action="store_true", help="Ignore existing processed state for this run")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key = read_key()
    workspace = Path(__file__).resolve().parents[3]
    state_path = workspace / "memory/gmail-calendar-sync-state.json"
    log_path = workspace / "memory/gmail-calendar-processed.jsonl"
    state = {
        "thread_latest_processed": {},
        "created_event_by_message": {},
        "last_run_at": None,
    } if args.ignore_state else load_state(state_path)

    now_local = datetime.now()
    gmail_query = "in:inbox"
    if args.days is not None:
        after_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y/%m/%d")
        gmail_query = f"in:inbox after:{after_date}"
    q = parse.urlencode({"maxResults": args.max, "q": gmail_query, "includeSpamTrash": "false"})
    ids = api_json(f"{API_GMAIL}/messages?{q}", key).get("messages", [])

    created = skipped = errors = 0
    created_details = []

    ml_model = train_nb_from_logs(log_path)

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

            # ML-based schedule classification (subject+snippet+body)
            prob = nb_predict_schedule_prob(ml_model, text)
            is_schedule = prob >= 0.55

            if not is_schedule:
                state["thread_latest_processed"][thread_id] = internal_ms
                skipped += 1
                append_jsonl(log_path, {
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "message_id": mid,
                    "thread_id": thread_id,
                    "subject": subject,
                    "action": "skip",
                    "reason": "ml_not_schedule",
                    "ml_schedule_prob": round(prob, 4),
                })
                continue

            start, end, all_day = parse_datetime(text, now_local)
            if not start:
                # ASAP rule: if schedule intent but no explicit date/time,
                # create all-day event covering received day ~ +1 day (2-day window)
                received_local = datetime.fromtimestamp(internal_ms / 1000, tz=timezone.utc).astimezone(ZoneInfo(args.tz))
                day0 = received_local.date().isoformat()
                day2 = (received_local.date() + timedelta(days=2)).isoformat()  # end is exclusive
                start, end, all_day = day0, day2, True

            event_title = derive_event_title(subject, text)
            event = {
                "summary": event_title[:120],
                "description": f"Gmail 자동생성\n\n원본 메일 제목: {subject}\nThread: {thread_id}\nMessage: {mid}\n\nSnippet:\n{snippet}",
            }
            if all_day:
                d = start
                # For parsed date without time, end may be None -> one-day all-day.
                # For ASAP fallback, end is precomputed as +2 days (exclusive end).
                end_day = end if end else (datetime.fromisoformat(d) + timedelta(days=1)).date().isoformat()
                event["start"] = {"date": d}
                event["end"] = {"date": end_day}
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
            created_details.append({
                "subject": subject,
                "event_summary": event["summary"],
                "event_id": event_id,
                "all_day": all_day,
                "start": event["start"],
                "end": event["end"],
            })
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
        "created_details": created_details,
        "skipped": skipped,
        "errors": errors,
        "state": str(state_path),
        "log": str(log_path),
        "dry_run": args.dry_run,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
