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

0. Enforce **single-input invariant** before anything else.
   - Compute and persist a stable source fingerprint for the canonical PDF (prefer SHA256 of file bytes; fallback: title+first-page DOI+page count).
   - Use this fingerprint as run key to prevent duplicate page creation.
   - Treat one user-provided paper PDF as exactly one job unit.
   - If multiple PDF candidates appear internally (tmp copies, chunked exports, duplicate names), dedupe and select only one canonical source by this order:
     1) exact path explicitly provided by the user
     2) largest file size
     3) newest mtime
   - Hard-stop and ask clarification if multiple distinct papers are detected (different title/metadata/hash), instead of processing all.
   - Never create multiple Notion pages from one user PDF input.
1. Read PDF metadata/title (e.g., `pdfinfo`) from the canonical source.
2. Extract text from key sections (abstract/introduction/method/results/conclusion) with local tools (e.g., `pdftotext`) using the same canonical source only.
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
   - Formatting guard: `# 1)`, `# 2)`, `# 3)` heading lines must be followed by exactly one blank line before body bullets/paragraphs.
5. Preserve useful technical symbols/terms from source.
6. Resolve Notion target under:
   - `IROL / 민동규 - (가제)Soft Robotics Sim To Real Transfer / 논문`
7. **Idempotent page upsert (mandatory)**
   - First, search existing child pages under the target parent by either:
     - exact title match, and/or
     - a marker block/property containing the source fingerprint (`source_fingerprint: <sha256>`)
   - If an existing page is found for the same fingerprint, **update that page** (do not create a new page).
   - Create a new page only when no matching page exists.
   - When newly creating, write fingerprint marker immediately near top of page.
8. Page title = paper title (use suffix only when genuinely different paper with same title).
9. Extract PDF images with `scripts/extract_pdf_images.py` and select key figures.
   - **High-priority mandatory rule**: include framework/architecture-type figures whenever present (e.g., pipeline/system block/architecture diagrams; figure number is irrelevant).
   - Priority order: framework/architecture > real setup/hardware photos > representative method diagrams.
   - De-prioritize pure result-only plots unless they are essential to the core claim.
9. Convert markdown with `scripts/markdown_to_notion.py` and append blocks.
   - Main body insertion must use `scripts/markdown_to_notion.py` (or equivalent markdown parser), not ad-hoc heading block construction.
   - Never send multiline heading content to Notion. Heading text must be one line only (no embedded `\n`, bullets, or markdown markers).
10. Insert selected key images as **inline image blocks** near relevant paragraphs (not only as file attachments).
    - For selection, run `scripts/select_key_images.py --pdf <canonical_pdf> --images-dir <extracted_dir>` first.
    - Never choose by filename/page number alone; verify with caption text and visual check (diagram vs plot vs photo).
11. Add `### 원본 PDF` section and attach original PDF file.
12. Register temporary artifacts for cleanup in 6 hours:
   - source paper PDF path
   - extracted image directory path
   - use `scripts/register_temp_artifacts.py <paths...> --ttl-hours 6`
13. Run final validation checklist (`references/checklist.md`) before reporting.
14. Run structural post-check: `scripts/validate_notion_page.py --page-id <id>`.
    - If validation fails (heading newline/marker contamination, missing inline image, or missing PDF file block), mark run failed.
    - On failed final check, do not report success; rollback the just-created/updated page to trash and report failure reason.
15. Report page URL + what was extracted (pages/sections used).

## Hard Rules

- **One PDF in → one summary page out**. Do not split one source into multi-page output.
- Pin all downstream steps (metadata/text/images/attachment) to one canonical PDF path.
- Default to local summary pipeline for cost and stability.
- Keep markdown fidelity high (`#`/`##`/`###`, bullets, tables, symbols).
- Use low-cost normalization in conversion script:
  - Convert indented `-` lines into true nested bullets.
  - Convert markdown `> ...` lines into actual Notion `quote` blocks (do not leave literal `>` text).
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
- Input cardinality QA: exactly 1 canonical PDF selected for the run.
- Output cardinality QA: exactly 1 Notion page per canonical PDF (upsert target must be unique by fingerprint).
- Acquire a per-fingerprint run lock before page mutation; if lock exists, wait/retry or abort with clear report (never run two writers for one PDF).
- Do not skip image extraction when key-image insertion is expected.
- If extracted image count is 0, explicitly report and continue without image insertion only with clear reason.
- If inline image insertion fails, retry once; if still failing, mark run as failed (do not claim success).
- If original PDF attachment fails, retry once; if still failing, mark run as failed (do not claim success).
- Ensure placeholders like `(아래 이미지 삽입)` are removed when images are actually inserted.
- Ensure nested bullets are real child bullets (never leave raw `- ...` text lines).
- Place key images near the matching section context (not dumped at page bottom).
- Incomplete pages from prior runs should not be auto-deleted unless explicitly requested by user.
- Any skill update must follow `commit -> push` (both required).

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
