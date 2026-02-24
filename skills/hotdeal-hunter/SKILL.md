---
name: hotdeal-hunter
description: Scan hot-deal boards (arca, fmkorea, quasarzone), filter for free/high-discount/good-value electronics (excluding food, clothing, and PC components), suppress already-sent links, and report concise picks with name/price/link.
---

# hotdeal-hunter

웹 핫딜 3개 소스를 순회해 조건에 맞는 항목만 추출하고, 이미 추천한 링크는 다시 알리지 않는다.

## 대상 사이트

1. https://arca.live/b/hotdeal
2. https://m.fmkorea.com/hotdeal
3. https://quasarzone.com/bbs/qb_saleinfo

요청상 1~2페이지 기준이지만, 기본 구현은 각 메인 리스트 기준으로 최신글을 우선 수집한다.

## 필터 규칙

포함:
- 무료 항목
- 매우 저렴한 항목(초저가)
- 가격이 괜찮은 전자기기(단, 컴퓨터 부품 제외)

제외:
- 식품
- 의류
- PC 부품(CPU/그래픽카드/메인보드/램/SSD/HDD/파워/쿨러/케이스 등)

## 중복 방지

- 중복 기준은 **제품명 아님, 링크 URL**.
- 저장 파일: `/home/soyu/.openclaw/workspace/memory/hotdeal-seen-links.json`
- 이미 저장된 링크는 다음 실행에서 제외.
- 동일 제품이라도 링크가 다르면 허용.

## 실행

```bash
python /home/soyu/.openclaw/workspace/skills/hotdeal-hunter/scripts/hotdeal_scan.py
```

## 결과 형식

사용자에게 전달할 때는 각 항목에 아래 필드를 포함:
- 이름
- 가격
- 링크

필요시 `tag`(무료/초저가/가성비 전자기기/고할인)도 함께 전달 가능.

## 운영 메모

- 사이트 구조 변경으로 파싱 실패 가능성이 있으므로, 결과가 0건이면 원문을 짧게 재확인하고 정규식을 보정한다.
- 외부 발송(다른 채널 전송)은 사용자 승인 후 수행한다.
