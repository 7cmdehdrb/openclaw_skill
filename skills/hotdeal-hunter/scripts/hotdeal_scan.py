#!/usr/bin/env python3
import json
import re
from pathlib import Path
from typing import List, Dict

import requests

SEEN_PATH = Path('/home/soyu/.openclaw/workspace/memory/hotdeal-seen-links.json')
SOURCES = {
    'arca': 'https://r.jina.ai/http://arca.live/b/hotdeal',
    'fmkorea': 'https://r.jina.ai/http://m.fmkorea.com/hotdeal',
    'quasarzone': 'https://r.jina.ai/http://quasarzone.com/bbs/qb_saleinfo',
}

EXCLUDE_KEYWORDS = ['식품', '먹', '라면', '과자', '의류', '옷', '패션']
ELECTRONICS_HINT = ['이어폰', '헤드폰', '태블릿', '모니터', '스피커', '마우스', '키보드', '로봇청소기', '공기청정기', 'TV', '노트북', '스마트폰', '충전기']
PC_PARTS_EXCLUDE = ['CPU', '그래픽카드', '메인보드', '램', 'SSD', 'HDD', '파워', '쿨러', '케이스']


def load_seen() -> set:
    if not SEEN_PATH.exists():
        return set()
    try:
        return set(json.loads(SEEN_PATH.read_text(encoding='utf-8')))
    except Exception:
        return set()


def save_seen(links: set):
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEEN_PATH.write_text(json.dumps(sorted(list(links)), ensure_ascii=False, indent=2), encoding='utf-8')


def parse_price(text: str):
    m = re.search(r'([0-9][0-9,]*)\s*원', text)
    if m:
        return int(m.group(1).replace(',', ''))
    if '무료' in text:
        return 0
    return None


def classify(title: str, price_val):
    t = title.lower()
    if any(k.lower() in t for k in EXCLUDE_KEYWORDS):
        return None
    if any(k.lower() in t for k in PC_PARTS_EXCLUDE):
        return None
    if '무료' in title or price_val == 0:
        return '무료'
    if price_val is not None and price_val <= 5000:
        return '초저가'
    if any(k.lower() in t for k in ELECTRONICS_HINT) and price_val is not None and price_val <= 300000:
        return '가성비 전자기기'
    if '%' in title:
        return '고할인'
    return None


def scan_arca(md: str) -> List[Dict]:
    out = []
    pat = re.compile(r'\[(?P<title>[^\]]+)\]\((?P<link>https://arca\.live/b/hotdeal/\d+\?p=1)\)')
    for m in pat.finditer(md):
        title = m.group('title').strip()
        link = m.group('link').strip()
        if 'Notice' in title or '핫딜 채널 이용 안내' in title:
            continue
        # nearby chunk for price
        start = m.end()
        chunk = md[start:start+120]
        price_val = parse_price(title + ' ' + chunk)
        tag = classify(title, price_val)
        if tag:
            price_str = '무료' if price_val == 0 else (f"{price_val:,}원" if price_val is not None else '확인필요')
            out.append({'source': 'arca', 'name': title, 'price': price_str, 'link': link, 'tag': tag})
        if len(out) >= 20:
            break
    return out


def scan_generic(md: str, domain: str) -> List[Dict]:
    out = []
    # generic markdown link capture
    pat = re.compile(r'\[(?P<title>[^\]]{6,140})\]\((?P<link>https?://[^)]+)\)')
    for m in pat.finditer(md):
        title = m.group('title').strip()
        link = m.group('link').strip()
        if domain not in link:
            continue
        if any(x in title.lower() for x in ['공지', 'notice', '로그인', '회원가입']):
            continue
        chunk = md[m.end():m.end()+120]
        price_val = parse_price(title + ' ' + chunk)
        tag = classify(title, price_val)
        if tag:
            price_str = '무료' if price_val == 0 else (f"{price_val:,}원" if price_val is not None else '확인필요')
            out.append({'source': domain, 'name': title, 'price': price_str, 'link': link, 'tag': tag})
        if len(out) >= 20:
            break
    return out


def fetch(url: str) -> str:
    return requests.get(url, timeout=20).text


def run() -> Dict:
    seen = load_seen()
    found = []

    for k, url in SOURCES.items():
        md = fetch(url)
        if k == 'arca':
            items = scan_arca(md)
        elif k == 'fmkorea':
            items = scan_generic(md, 'fmkorea.com')
        else:
            items = scan_generic(md, 'quasarzone.com')

        for it in items:
            if it['link'] in seen:
                continue
            found.append(it)

    # keep concise top candidates
    found = found[:15]
    seen.update(i['link'] for i in found)
    save_seen(seen)

    return {'count': len(found), 'items': found}


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=False, indent=2))
