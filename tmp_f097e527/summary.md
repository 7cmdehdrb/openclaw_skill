# 0) 논문 정보
- 출간 연도: 2021
- 출간 저널: Frontiers in Robotics and AI
- citation 수: 16 (OpenAlex 기준)
### APA
> Khin, P. ; Low, J. ; Ang, M. ; Yeow, C. (2021). Development and Grasp Stability Estimation of Sensorized Soft Robotic Hand. Frontiers in Robotics and AI. https://doi.org/10.3389/frobt.2021.619390
### BibTeX
> @article{Khin_2021, title={Development and Grasp Stability Estimation of Sensorized Soft Robotic Hand}, volume={8}, ISSN={2296-9144}, url={http://dx.doi.org/10.3389/frobt.2021.619390}, DOI={10.3389/frobt.2021.619390}, journal={Frontiers in Robotics and AI}, publisher={Frontiers Media SA}, author={Khin, P. M. and Low, Jin H. and Ang, Marcelo H. and Yeow, Chen H.}, year={2021}, month=mar }

# 1) 문제 상황
- 연구 목표: 센서가 내장된 소프트 로봇 핸드가 물체를 잡고 들어 올릴 때, **불안정/미끄럼 발생 여부를 실시간으로 추정**하도록 하는 것.
- 기존 한계:
  - 물체 종류가 다양해질수록(형상/무게/강성 차이) 데이터 수집 비용이 급증.
  - 제한된 물체로만 검증된 slip detection은 실제 일상 물체 확장성이 낮음.
- 중요성:
  - 물체 안정도 추정이 가능하면 공압 제어기가 필요한 압력만 사용해(예: 가벼운 물체는 저압) 에너지/안정성을 함께 개선 가능.

# 2) Proposed Method
- 하드웨어:
  - TPU-coated nylon 기반 fabric finger actuator(FFA)로 구성된 anthropomorphic soft hand.
  - 손가락에 flexible force sensor array를 통합해 접촉력 시계열을 획득.
- 실험 프로토콜:
  - 손이 물체를 탁자에서 **1.5 s 유지 후 1 s 내 리프트**.
  - 공압 조건: **50 / 80 / 120 kPa**.
- 학습 접근:
  - 데이터 수집 부담 완화를 위해 one-shot learning(OSL) + LSTM 계열 네트워크 사용.
  - 비교 모델 3종: Triplet LSTM, Siamese LSTM, LSTM.
- 핵심 아이디어:
  - 센서 시계열에서 안정/불안정(tilting, slip) 상태를 추정하여 공압 제어에 피드백.

# 3) 정량 및 정성적 결과
## 정량 결과
| 모델 | 안정도 추정 정확도(%) |
|---|---:|
| Triplet LSTM | 89.96 |
| LSTM | 88.00 |
| Siamese LSTM | 85.16 |

- 세 모델 중 Triplet LSTM이 최고 정확도를 보였음.

## 정성 결과
- 다양한 일상 물체(형상/강성 변화 포함)를 대상으로 안정도 추정 가능성을 보임.
- OSL 기반 접근으로 향후 신규 물체 추가 시 학습 확장성 측면의 이점을 제시.
- 단, 물체별 세부 오분류 패턴/일반화 한계의 정량 분해는 본문에서 추가 확인 필요.

## 한줄 평가
- 본 논문은 **센서 통합 소프트 핸드 + OSL 기반 시계열 추정**을 결합해, 물체 안정도 인지와 공압 제어 피드백의 실용적 가능성을 근거 기반으로 제시했다.
