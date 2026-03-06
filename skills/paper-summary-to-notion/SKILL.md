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
   - 삽입 순서는 논문 원문 순서(페이지 오름차순 → 페이지 내 이미지 인덱스 오름차순)
4. 표 사용은 기본 지양
   - 불릿/자식 불릿 중심
5. Notion 문법 오염 절대 금지
   - heading 본문 침범 금지
   - 가짜 불릿(`-` 텍스트 노출) 금지

## Workflow
0. 입력 PDF canonical path 1개 확정
1. `sha256` fingerprint 계산
2. 동시 실행 락 확보
   - lock key: `paper-summary-to-notion:<sha256>`
   - 동일 key 실행 중이면 대기/스킵 (중복 쓰기 금지)
3. 중복성 검사 (부모: `IROL / 민동규 - (가제)Soft Robotics Sim To Real Transfer / 논문`)
   - 중복이면 생성/수정 없이 스킵 보고
4. 메타데이터 수집 (`scripts/paper_metadata.py`)
5. 텍스트 추출 (`pdftotext` 등)
6. 요약 작성 (**특히 `제안하는 방법` 최우선 품질 영역**)
   - 이 섹션은 가장 많은 노력/토큰을 배분한다. (다른 섹션보다 상세하게)
   - 강제 형식(열거 나열 금지):
     1) 먼저 1개 짧은 문단으로 방법의 전체 목적/핵심 원리를 설명
     2) 그 다음 단계형 흐름(예: 입력 → 처리 → 판단/전환 → 출력)을 불릿으로 정리
     3) 마지막에 왜 이 흐름이 유효한지(기존 대비 장점/의도)를 연결 문장으로 마무리
   - 즉, `제안하는 방법`은 "흐름이 보이는 설명"이 반드시 포함되어야 하며, 단순 요소 나열만으로 끝내지 않는다.
   - 필요 시 이 섹션만 별도 재요약(2차 압축/확장)해서 디테일을 보강한다.
7. Notion 페이지 upsert
   - 제목: `원문 논문 제목 (연도)`
   - 상단에 `source_fingerprint: <sha256>` 기록
8. 이미지 추출 (`scripts/extract_pdf_images.py`)
   - 300px 규칙 통과 이미지 전체를 `## 논문 이미지` 섹션에 인라인 삽입
   - 삽입 순서: 페이지 오름차순 → 페이지 내 이미지 인덱스 오름차순
   - `## 논문 이미지` 섹션 하위로 넣어야 하며, 페이지 최하단 임의 추가 금지
   - 이미지 caption은 사용하지 않는다. (caption 비움)
9. `## 원본 PDF` 섹션에 원본 PDF file block 첨부
   - `## 원본 PDF` 섹션 하위로 넣어야 하며, 별도 말미 추가 금지
10. 요약 지시 문장(예: `(아래에 ... 첨부)`)은 최종 페이지에 남기지 않는다.
11. 구조 검증 (`scripts/validate_notion_page.py --page-id <id>`)
   - 실패 시 성공 보고 금지 + rollback(in_trash)
11. 임시 파일 등록
   - **실제로 사용된 파일만** 등록
   - TTL **1주일(168시간)**
   - `scripts/register_temp_artifacts.py <paths...> --ttl-hours 168`
12. 락 해제 (성공/실패 모두)

## Formatting Guard
- `## 논문 정보`, `## 문제 상황`, `## 제안하는 방법`, `## 결과` 아래는 본문 시작 전 한 줄 공백 유지
- heading 텍스트는 단일 라인만 허용

## Cron Hardening (품질 편차 방지)
- 배치/크론 실행 시에도 동일 QA를 적용한다. (수동 실행과 예외 없이 동일)
- 다건 실행 전 `canary 1건`을 먼저 수행하고 통과 시에만 나머지를 진행한다.
- 인터벌은 처리시간보다 충분히 길게 잡고(권장 10분+), 이전 실행 미종료 시 다음 작업 시작 금지.
- 보고는 성공 URL만; 실패는 실패 원인 + rollback 여부를 분리 보고.

## Checklist
- `references/checklist.md`를 최종 게이트로 사용한다.
- 체크리스트 미완료 항목이 하나라도 있으면 완료 보고 금지.
