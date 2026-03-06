# 0) 논문 정보
- 출간 연도: 2019 (ACC)
- 출간 저널/학회: 2019 American Control Conference (ACC)
- citation 수: 23 (OpenAlex 기준)
### APA
> Loo, J. ; Tan, C. ; Nurzaman, S. (2019). H-infinity based Extended Kalman Filter for State Estimation in Highly Non-linear Soft Robotic System. 2019 American Control Conference (ACC). https://doi.org/10.23919/acc.2019.8814869
### BibTeX
> @inproceedings{Loo_2019, title={H-infinity based Extended Kalman Filter for State Estimation in Highly Non-linear Soft Robotic System}, url={http://dx.doi.org/10.23919/acc.2019.8814869}, DOI={10.23919/acc.2019.8814869}, booktitle={2019 American Control Conference (ACC)}, publisher={IEEE}, author={Loo, Junn Yong and Tan, Chee Pin and Nurzaman, Surya Girinatha}, year={2019}, month=jul, pages={5154–5160} }

# 1) 문제 상황
- 소프트 연속체 매니퓰레이터는 강한 비선형 동역학/기구학과 모델 불확실성 때문에 상태추정이 어렵다.
- 센서를 많이 넣기 어려운(softness 훼손) 특성상, 제한된 측정으로 신뢰도 있는 상태추정이 필요하다.
- 표준 EKF는 모델 미스매치와 샘플링/이산화 오차가 큰 조건에서 추정 오차가 커질 수 있다.

# 2) Proposed Method
- 논문은 **H∞ 기반 Extended Kalman Filter(H∞-EKF)** 를 제안해, 소프트 연속체 매니퓰레이터 상태를 강건하게 추정한다.
- 대상 시스템: 3개의 pneumatic muscle actuator(pMA)로 구성된 section 모델.
- 상태공간 재구성 후, tip position 좌표를 측정 입력으로 사용해 다음을 추정:
  - pMA elongation
  - elongation rate
  - 추정 elongation을 통해 task-space 좌표(X, Y, Z) 재구성
- 핵심은 모델 불확실성/이산화 오차가 있는 조건에서도 추정 안정성을 높이려는 강건 필터 설계다.

# 3) 정량 및 정성적 결과
## 정량 결과
| 항목 | 결과 |
|---|---|
| pMA elongation 추정 오차 | **2 × 10⁻⁴ m 이하** (논문 본문 서술) |
| task-space 좌표(X,Y,Z) | ξ=0.8 지점에서 시뮬레이션 좌표와 정확 추종 보고 |
| elongation rate 오차 | 정상구간에서 약 **0.02** 수준으로 수렴(일부 구간 0 수렴 미달) |

## 정성 결과
- elongation과 task-space 좌표는 매우 잘 추종하는 반면, elongation rate는 모델 불확실성/큰 time-step 영향으로 상대적으로 성능이 떨어진다고 보고.
- 입력 전환 시점(특히 t=0s)에서 오차 스파이크가 발생하며, 비선형 전파 상태 overshoot가 원인으로 제시됨.

## 한줄 평가
- 이 논문은 소프트 로봇 상태추정에서 EKF의 취약 구간을 보완하기 위해 **H∞-EKF 강건 추정 프레임워크**를 제시하고, elongation/작업공간 좌표 추정의 실효성을 수치적으로 보여준다.
