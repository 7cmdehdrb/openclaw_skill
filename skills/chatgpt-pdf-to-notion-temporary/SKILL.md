---
name: chatgpt-pdf-to-notion-temporary
description: Use when the user asks to analyze an attached PDF with ChatGPT and save the result to Notion while enforcing temporary (incognito-like) chat hygiene. Trigger for requests like: "GPT에 PDF 올려서 분석하고 노션에 정리", "임시 채팅으로 하고 끝나면 리셋", "논문 PDF를 문제상황/방법/결과로 정리해서 Notion에 붙여넣기".
---

# ChatGPT PDF → Notion (Temporary Chat Mode)

Follow this exact sequence.

## Fixed Workflow

1. Open ChatGPT in temporary mode: `https://chatgpt.com/?temporary-chat=true`.
2. Verify temporary mode is ON (임시 채팅 체크 상태 확인).
3. Refresh once before starting a new task.
4. Upload the user PDF to ChatGPT.
5. Send the fixed prompt from `references/prompt.txt`.
6. Wait for response completion.
7. If the response is truncated, ask for continuation without summarizing:
   - `남은 부분을 같은 형식으로 이어서 출력해줘.`
8. Extract final response text preserving markdown structure.
9. Create a Notion page under:
   - `IROL / 민동규 - (가제)Soft Robotics Sim To Real Transfer / 논문`
10. Page title = paper title.
11. Paste response preserving markdown (headings, bullets, tables, symbols/equations).
12. Refresh ChatGPT page to reset temporary chat content.

## Hard Rules

- Always start in temporary mode.
- Do not reuse previous GPT conversation context.
- Prefer preserving original GPT wording over rewriting.
- Keep markdown fidelity high.
- **When attaching PDF results to Notion, use only `###` headings for section separation** (no markdown tables; avoid deep heading nesting).
- If Notion path lookup fails, stop and report which node failed.

## Failure Handling

- Relay not attached → ask user to enable Relay ON on the active tab.
- Upload path blocked → copy file to a safe path like `/tmp/openclaw/uploads/` and retry.
- GPT UI truncation → request continuation, then merge text in order.
- Duplicate Notion title → append ` (2)`, ` (3)`.

## Helpers

- Prompt template: `references/prompt.txt`
- Notion markdown conversion helper: `scripts/markdown_to_notion.py`
- Workflow checklist (operator): `references/checklist.md`
