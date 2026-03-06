---
name: paper-summary-to-notion
description: Summarize research paper PDFs and upload to Notion with strict formatting/QA. Use when user asks to 정리/요약 논문 PDF를 Notion에 올리기. Trigger examples: "논문 요약해서 노션에", "paper summary to notion", "문제상황/제안방법/결과 정리 후 노션 업로드".
---

# Paper Summary → Notion (API-only, No Browser)

## Scope
- 대상은 **논문 PDF**만.
- 브라우저 자동화 금지. (Notion/API 기반으로만 처리)

## Output Contract (고정)
본문 섹션 순서/제목을 아래로 고정한다:
1. `## 논문 정보`
2. `## 문제 상황`
3. `## 제안하는 방법`
4. `## 결과`
5. `## 논문 이미지`
6. `## 원본 PDF`

## Critical Rules
1. 페이지 제목은 반드시 `원문 논문 제목 (연도)`
   - 축약/의역 금지
2. 중복 검사 최우선
   - 동일 논문 페이지가 이미 `논문` 부모 페이지 아래 있으면 **스킵**
   - 판정 기준: `(제목 + 연도)` 또는 `source_fingerprint(sha256)` 일치
3. 이미지는 **선별이 아니라 전체 삽입**
   - 단, `max(width, height) >= 300px`만 추출/삽입
4. 표 사용은 기본 지양
   - 불릿/자식 불릿 중심
5. Notion 문법 오염 절대 금지
   - heading 본문 침범 금지
   - 가짜 불릿(`-` 텍스트 노출) 금지

## Workflow
0. 입력 PDF canonical path 1개 확정
1. `sha256` fingerprint 계산
2. 중복성 검사 (부모: `IROL / 민동규 - (가제)Soft Robotics Sim To Real Transfer / 논문`)
   - 중복이면 생성/수정 없이 스킵 보고
3. 메타데이터 수집 (`scripts/paper_metadata.py`)
4. 텍스트 추출 (`pdftotext` 등)
5. 요약 작성 (특히 `제안하는 방법`을 디테일하게)
   - 입력/출력
   - 핵심 아이디어
   - 절차(파이프라인)
   - 기존 대비 차별점
6. Notion 페이지 upsert
   - 제목: `논문명 (연도)`
   - 상단에 `source_fingerprint: <sha256>` 기록
7. 이미지 추출 (`scripts/extract_pdf_images.py`)
   - 300px 규칙 통과 이미지 전체를 `## 논문 이미지` 섹션에 인라인 삽입
8. `## 원본 PDF` 섹션에 원본 PDF file block 첨부
9. 구조 검증 (`scripts/validate_notion_page.py --page-id <id>`)
   - 실패 시 성공 보고 금지 + rollback(in_trash)
10. 임시 파일 등록
   - **실제로 사용된 파일만** 등록
   - TTL **1주일(168시간)**
   - `scripts/register_temp_artifacts.py <paths...> --ttl-hours 168`

## Formatting Guard
- `## 논문 정보`, `## 문제 상황`, `## 제안하는 방법`, `## 결과` 아래는 본문 시작 전 한 줄 공백 유지
- heading 텍스트는 단일 라인만 허용

## Checklist
- `references/checklist.md`를 최종 게이트로 사용한다.
- 체크리스트 미완료 항목이 하나라도 있으면 완료 보고 금지.
