---
name: chatgpt-pdf-to-notion-temporary
description: Use when the user asks to summarize/analyze attached PDFs and save to Notion with stable formatting. ChatGPT/browser relay is optional; default to low-cost local summary pipeline (PDF text extraction + structured summary + Notion upload). Trigger for requests like: "논문 PDF 정리해서 노션에", "문제상황/방법/결과 요약", "GPT 없이 안정적으로 노션 반영".
---

# PDF Summary → Notion (Local-First)

Use a local-first pipeline. Do NOT depend on browser automation unless the user explicitly demands ChatGPT web flow.

## Fixed Workflow

1. Read PDF metadata/title (e.g., `pdfinfo`).
2. Extract text from key sections (abstract/introduction/method/results/conclusion) with local tools (e.g., `pdftotext`).
3. Write structured markdown summary using schema from `references/prompt.txt`:
   - 문제 상황
   - Proposed method
   - 정량/정성 결과
4. Preserve useful technical symbols/terms from source.
5. Create Notion page under:
   - `IROL / 민동규 - (가제)Soft Robotics Sim To Real Transfer / 논문`
6. Page title = paper title (dedupe with ` (2)`, ` (3)` as needed).
7. Convert markdown with `scripts/markdown_to_notion.py` and append blocks.
8. Add `### 원본 PDF` section and attach original PDF file.
9. Report page URL + what was extracted (pages/sections used).

## Hard Rules

- Default to local summary pipeline for cost and stability.
- Keep markdown fidelity high (`#`/`##`/`###`, bullets, tables, symbols).
- Use low-cost normalization in conversion script:
  - Convert indented `-` lines into true nested bullets.
  - Convert `**bold**` inside table cells into Notion bold annotations.
- Minimize hallucination: only claim values seen in extracted text.
- If a metric is missing/unclear, mark as "본문 확인 필요".

## Failure Handling

- PDF text extraction fails/scanned PDF only → report OCR requirement and pause.
- Notion path lookup fails → stop and report which node failed.
- Duplicate title → append numeric suffix.

## Helpers

- Summary schema: `references/prompt.txt`
- Notion markdown conversion helper: `scripts/markdown_to_notion.py`
- Workflow checklist (operator): `references/checklist.md`
