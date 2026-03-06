# Operator Checklist

## A. 입력/메타데이터
- [ ] 입력 카디널리티 확인: 사용자 입력 기준 canonical PDF 1개만 선택
- [ ] 내부 중복 파일(tmp copy/분할본/이름만 다른 동일본) 제거 후 canonical 경로 고정
- [ ] source fingerprint 계산/기록 (prefer SHA256)
- [ ] PDF title/metadata 확인 (`pdfinfo` 등)
- [ ] 논문 메타데이터 조회 (`scripts/paper_metadata.py`) 및 `0) 논문 정보` 섹션 작성
- [ ] citation 형식 확인: `APA`/`BibTeX` 라벨은 heading/bold, citation 본문만 quote
- [ ] Notion 반영 후 APA/BibTeX 본문이 실제 `quote` 블록인지 확인 (문자 `>` 잔존 금지)
- [ ] confidence 낮으면 Google Scholar 수동 검증(제목+저자+저널 기준)

## B. 본문 요약 품질
- [ ] 본문 텍스트 추출 완료 (`pdftotext` 등)
- [ ] 핵심 섹션(문제/방법/결과) 근거 문장 확보
- [ ] `references/prompt.txt` 스키마로 마크다운 요약 작성
- [ ] `# 1)`, `# 2)`, `# 3)` 제목 아래 한 줄 공백(빈 줄) 규칙 적용 확인
- [ ] 수치가 확실할 때만 정량표 작성 (불확실 수치 추정 금지)
- [ ] 방법/결과 문단은 근거 문장 기반으로 작성(추정 금지)
- [ ] 문체 점검: 짧고 단정한 기술 요약(군더더기 제거)

## C. 노션 반영
- [ ] Notion path resolved: IROL / 민동규 - (가제)Soft Robotics Sim To Real Transfer / 논문
- [ ] 기존 페이지 탐색: title/fingerprint 기준으로 upsert 대상 1개 확정
- [ ] 신규 생성 시 fingerprint marker 즉시 기록
- [ ] 출력 카디널리티 확인: canonical PDF 1개당 Notion page 1개만 유지(중복 생성 금지)
- [ ] Notion formatting rule applied (`#`/`##`/`###`, nested bullets, table bold)
- [ ] heading 블록 QA: heading_1/2/3 각 블록의 텍스트가 단일 라인인지 확인(개행 포함 금지)
- [ ] heading 블록에 불릿/마크다운 본문(`- `, `##`, `###`)이 섞여 있지 않은지 확인

## D. 핵심 이미지(누락 방지)
- [ ] 이미지 추출 실행 완료 (`scripts/extract_pdf_images.py`) 및 추출 개수 확인
- [ ] 프레임워크/아키텍처 유형 도식(파이프라인/시스템 블록/모듈 구조; figure 번호 무관) 존재 시 **반드시 포함**
- [ ] 그 다음 우선순위: 실험/실물 이미지 > 대표 방법 도식
- [ ] 결과 그래프는 핵심 주장에 필수일 때만 선택
- [ ] 이미지 전처리 확인: 알파 채널 제거 + 투명 영역 흰색 채움
- [ ] 핵심 이미지는 본문 문맥 위치에 인라인 삽입
- [ ] placeholder 문구(예: `(아래 이미지 삽입)`) 제거 확인

## E. 마감
- [ ] `### 원본 PDF` 섹션 + 원본 PDF 첨부
- [ ] 원본 PDF 첨부는 로컬 경로 텍스트가 아닌 실제 Notion file block 업로드인지 확인
- [ ] 불릿 QA: 중첩 항목이 raw `-` 텍스트가 아닌 실제 자식 불릿인지 확인
- [ ] 이미지 QA: 핵심 이미지가 관련 섹션 근처에 인라인 삽입되었는지 확인
- [ ] 구조 QA 실행: `scripts/validate_notion_page.py --page-id <id>`
- [ ] 구조 QA 실패 시 해당 페이지 rollback(in_trash=true) 후 실패로 보고
- [ ] 이미지/첨부 업로드 실패 시 재시도 결과 기록(실패면 완료 보고 금지)
- [ ] 임시 파일 등록: source PDF + extracted image dir 를 `--ttl-hours 6`로 등록
- [ ] 최종 URL/핵심 추출 근거 보고
- [ ] 위 체크리스트 미완료 항목 0개 확인 후에만 "완료" 보고
