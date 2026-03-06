#!/usr/bin/env python3
import argparse
import json
import os
import requests

NV = "2025-09-03"


def plain(rt):
    return "".join(x.get("plain_text", "") for x in (rt or []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page-id", required=True)
    args = ap.parse_args()

    key = os.getenv("NOTION_API_KEY")
    if not key:
        raise SystemExit("NOTION_API_KEY is required")

    h = {"Authorization": f"Bearer {key}", "Notion-Version": NV}
    r = requests.get(f"https://api.notion.com/v1/blocks/{args.page_id}/children?page_size=100", headers=h, timeout=30)
    r.raise_for_status()

    bad = []
    has_image = False
    has_file = False

    for b in r.json().get("results", []):
        t = b.get("type")
        if t == "image":
            has_image = True
        if t == "file":
            has_file = True
        if t in {"heading_1", "heading_2", "heading_3"}:
            txt = plain(b.get(t, {}).get("rich_text", []))
            if "\n" in txt:
                bad.append({"block": b.get("id"), "reason": "heading contains newline", "text": txt[:200]})
            if txt.strip().startswith(("#", "- ", "> ")):
                bad.append({"block": b.get("id"), "reason": "heading contains markdown marker", "text": txt[:200]})

    ok = (len(bad) == 0) and has_image and has_file
    print(json.dumps({"ok": ok, "badHeadings": bad, "hasImage": has_image, "hasFile": has_file}, ensure_ascii=False))


if __name__ == "__main__":
    main()
