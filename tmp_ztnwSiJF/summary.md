# 0) 논문 정보
- 출간 연도: 2018
- 출간 저널: Soft Robotics
- citation 수: 610 (OpenAlex 기준)
### APA
> George Thuruthel, T. ; Ansari, Y. ; Falotico, E. ; Laschi, C. (2018). Control Strategies for Soft Robotic Manipulators: A Survey. Soft Robotics. https://doi.org/10.1089/soro.2017.0007
### BibTeX
> @article{George_Thuruthel_2018, title={Control Strategies for Soft Robotic Manipulators: A Survey}, volume={5}, ISSN={2169-5180}, url={http://dx.doi.org/10.1089/soro.2017.0007}, DOI={10.1089/soro.2017.0007}, number={2}, journal={Soft Robotics}, publisher={SAGE Publications}, author={George Thuruthel, Thomas and Ansari, Yasmin and Falotico, Egidio and Laschi, Cecilia}, year={2018}, month=apr, pages={149–163} }

# 1) 문제 상황
- 소프트/연속체 매니퓰레이터는 고차원·비선형 특성 때문에, 강체 로봇처럼 통일된 제어 설계 프레임워크가 부족하다.
- 설계/구동 방식(공압, 텐던, 다중 세그먼트)과 모델 불확실성 때문에 제어기 일반화가 어렵다.
- 따라서 본 논문은 기존 제어 전략을 체계적으로 분류·비교해 실무 적용 가이드를 제공하는 것을 목표로 한다.

# 2) Proposed Method
- 본 논문은 신규 단일 제어기를 제안하는 연구가 아니라 **제어 전략 서베이/분류 프레임워크**를 제시한다.
- 분류 축(핵심):
  - Modeling approach: model-based / model-free / hybrid
  - Operating space: low-level(구동/조인트), mid-level(역기구학·동역학), high-level(태스크)
  - 설계 요소: actuation 방식, 세그먼트/배치, 응용 맥락
- 문헌을 위 축으로 재정리하여 각 접근의 적용 범위와 한계를 비교한다.

# 3) 정량 및 정성적 결과
## 정량 결과
| 항목 | 값 |
|---|---|
| 논문 성격 | 서베이(리뷰) |
| 비교 대상 수치 성능 | 본문 확인 필요 |

## 정성 결과
- 모델 기반 제어는 해석 가능성과 안정성 분석 장점이 있으나, 정확한 모델 획득이 어려운 소프트 시스템에서 적용 비용이 크다.
- 모델 프리(학습 기반) 제어는 복잡 비선형 대응에 유리하지만, 데이터 요구량·해석 가능성·일반화가 주요 이슈다.
- 하이브리드 접근은 두 방식의 장단을 절충하는 유망 방향으로 제시된다.

## 한줄 평가
- 이 논문은 소프트 매니퓰레이터 제어를 공통 분류체계로 정리해, **모델 기반/학습 기반/하이브리드의 선택 기준과 연구 공백**을 명확히 제시한 기준점 역할의 서베이다.
