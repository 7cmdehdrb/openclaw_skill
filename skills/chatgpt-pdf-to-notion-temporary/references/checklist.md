# Operator Checklist

## A. 입력/메타데이터
- [ ] PDF title/metadata 확인 (`pdfinfo` 등)
- [ ] 논문 메타데이터 조회 (`scripts/paper_metadata.py`) 및 `0) 논문 정보` 섹션 작성
- [ ] citation 형식 확인: `APA`/`BibTeX` 라벨은 heading/bold, citation 본문만 quote
- [ ] confidence 낮으면 Google Scholar 수동 검증(제목+저자+저널 기준)

## B. 본문 요약 품질
- [ ] 본문 텍스트 추출 완료 (`pdftotext` 등)
- [ ] 핵심 섹션(문제/방법/결과) 근거 문장 확보
- [ ] `references/prompt.txt` 스키마로 마크다운 요약 작성
- [ ] 수치가 확실할 때만 정량표 작성 (불확실 수치 추정 금지)
- [ ] 방법/결과 문단은 근거 문장 기반으로 작성(추정 금지)
- [ ] 문체 점검: 짧고 단정한 기술 요약(군더더기 제거)

## C. 노션 반영
- [ ] Notion path resolved: IROL / 민동규 - (가제)Soft Robotics Sim To Real Transfer / 논문
- [ ] Page created with paper title (중복 시 suffix)
- [ ] Notion formatting rule applied (`#`/`##`/`###`, nested bullets, table bold)

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
- [ ] 최종 URL/핵심 추출 근거 보고
- [ ] 위 체크리스트 미완료 항목 0개 확인 후에만 "완료" 보고
