---
name: chatgpt-pdf-to-notion-temporary
description: Use only when the user asks to summarize/analyze attached **research paper PDFs** and save to Notion with stable formatting. Do not auto-apply to arbitrary PDFs. ChatGPT/browser relay is optional; default to low-cost local summary pipeline (PDF text extraction + structured summary + Notion upload). Trigger for requests like: "논문 PDF 정리해서 노션에", "문제상황/방법/결과 요약", "GPT 없이 안정적으로 노션 반영".
---

# PDF Summary → Notion (Local-First)

Use a local-first pipeline for **paper PDFs**. Do NOT depend on browser automation unless the user explicitly demands ChatGPT web flow.

## Scope Guard

- This skill is for **논문 PDF** only.
- Do not run this skill on non-paper documents (invoices, manuals, random reports, forms, scanned receipts, etc.) unless the user explicitly asks to treat them as paper-style summaries.
- Even for paper PDFs, execute only when the user gives a direct run instruction.

## Fixed Workflow

1. Read PDF metadata/title (e.g., `pdfinfo`).
2. Extract text from key sections (abstract/introduction/method/results/conclusion) with local tools (e.g., `pdftotext`).
3. Fetch paper metadata (`scripts/paper_metadata.py --title "..."`) and prepare a new section:
   - `0) 논문 정보` (출간 연도, 출간 저널, citation 수)
   - Citation formatting rule:
     - `APA` / `BibTeX` 라벨은 quote가 아닌 `###` 또는 일반 **bold** 텍스트로 표기
     - 실제 citation 본문만 quote 블록으로 기록
   - If metadata confidence is low, verify via browser flow on Google Scholar.
4. Write structured markdown summary using schema from `references/prompt.txt`:
   - 문제 상황
   - Proposed method
   - 정량/정성 결과
5. Preserve useful technical symbols/terms from source.
6. Create Notion page under:
   - `IROL / 민동규 - (가제)Soft Robotics Sim To Real Transfer / 논문`
7. Page title = paper title (dedupe with ` (2)`, ` (3)` as needed).
8. Extract PDF images with `scripts/extract_pdf_images.py` and select key figures.
   - **High-priority mandatory rule**: include framework/architecture-type figures whenever present (e.g., pipeline/system block/architecture diagrams; figure number is irrelevant).
   - Priority order: framework/architecture > real setup/hardware photos > representative method diagrams.
   - De-prioritize pure result-only plots unless they are essential to the core claim.
9. Convert markdown with `scripts/markdown_to_notion.py` and append blocks.
10. Insert selected key images as **inline image blocks** near relevant paragraphs (not only as file attachments).
11. Add `### 원본 PDF` section and attach original PDF file.
12. Register temporary artifacts for cleanup in 6 hours:
   - source paper PDF path
   - extracted image directory path
   - use `scripts/register_temp_artifacts.py <paths...> --ttl-hours 6`
13. Run final validation checklist (`references/checklist.md`) before reporting.
14. Report page URL + what was extracted (pages/sections used).

## Hard Rules

- Default to local summary pipeline for cost and stability.
- Keep markdown fidelity high (`#`/`##`/`###`, bullets, tables, symbols).
- Use low-cost normalization in conversion script:
  - Convert indented `-` lines into true nested bullets.
  - Convert `**bold**` inside table cells into Notion bold annotations.
- Minimize hallucination: only claim values seen in extracted text.
- If a metric is missing/unclear, mark as "본문 확인 필요".

### Quality Baseline (must pass)

- Read broad text range (not first page only): abstract/introduction/method/results/conclusion.
- Always include `0) 논문 정보` with year/journal/citation count + APA/BibTeX format rule.
- Problem/Method/Result each must be grounded in extracted text.
- Never invent numeric performance claims.
- If robust numeric tables are unavailable, report verified qualitative outcome + explicit caveat.
- Prefer direct evidence phrasing over speculative wording.
- Write concise, publication-style summary (no filler, no generic claims).
- Keep structure stable for consistency:
  - `0) 논문 정보`
  - `1) 문제 상황`
  - `2) Proposed Method`
  - `3) 정량 및 정성적 결과`
  - `### 원본 PDF`

### Execution Guardrails (must pass before done)

- Do not report completion until all checklist items are verified.
- Do not skip image extraction when key-image insertion is expected.
- If extracted image count is 0, explicitly report and continue without image insertion only with clear reason.
- If inline image insertion fails, retry once; if still failing, report failure explicitly (do not claim success).
- Ensure placeholders like `(아래 이미지 삽입)` are removed when images are actually inserted.
- Ensure nested bullets are real child bullets (never leave raw `- ...` text lines).
- Place key images near the matching section context (not dumped at page bottom).

## Failure Handling

- PDF text extraction fails/scanned PDF only → report OCR requirement and pause.
- Metadata API match confidence low (<0.75) or missing fields → browser fallback:
  1) Open `https://scholar.google.co.kr/schhp?hl=ko&as_sdt=0,5`
  2) Search by full paper title
  3) Pick best match by title+authors+venue
  4) Read citation count and citation info manually
- Notion path lookup fails → stop and report which node failed.
- Duplicate title → append numeric suffix.

## Dependencies

- `scripts/extract_pdf_images.py` requires PyMuPDF:
  - `python3 -m pip install --user pymupdf`

## Helpers

- Summary schema: `references/prompt.txt`
- Notion markdown conversion helper: `scripts/markdown_to_notion.py`
- Paper metadata fetcher: `scripts/paper_metadata.py`
- PDF image extractor: `scripts/extract_pdf_images.py`
- Temp artifact registrar: `scripts/register_temp_artifacts.py`
- Temp artifact garbage collector: `scripts/temp_artifact_gc.py`
- Workflow checklist (operator): `references/checklist.md`
