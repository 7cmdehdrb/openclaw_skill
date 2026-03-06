# 0) 논문 정보
- 출간 연도: 2021
- 출간 저널: IEEE Robotics and Automation Letters
- citation 수: 23 (OpenAlex 기준)
### APA
> Ding, Z. ; Loo, J. ; Baskaran, V. ; Nurzaman, S. ; Tan, C. (2021). Predictive Uncertainty Estimation Using Deep Learning for Soft Robot Multimodal Sensing. IEEE Robotics and Automation Letters. https://doi.org/10.1109/lra.2021.3056066
### BibTeX
> @article{Ding_2021, title={Predictive Uncertainty Estimation Using Deep Learning for Soft Robot Multimodal Sensing}, volume={6}, ISSN={2377-3774}, url={http://dx.doi.org/10.1109/lra.2021.3056066}, DOI={10.1109/lra.2021.3056066}, number={2}, journal={IEEE Robotics and Automation Letters}, publisher={Institute of Electrical and Electronics Engineers (IEEE)}, author={Ding, Ze Yang and Loo, Junn Yong and Baskaran, Vishnu Monn and Nurzaman, Surya Girinatha and Tan, Chee Pin}, year={2021}, month=apr, pages={951–957} }

# 1) 문제 상황
- 소프트 로봇은 높은 순응성을 가지지만, 센싱/지각 모델의 불확실성이 커져 예측 정확도와 신뢰도가 저하된다.
- 기존 연구는 불확실성 하에서 동작하는 제어를 다뤘지만, **예측값 자체의 신뢰도(predictive uncertainty)** 를 함께 출력하는 일반 프레임워크는 부족하다.
- 센서 집적이 어려운 소프트 로봇 특성상, 최소 센서로 다중 물리량을 추정할 때 신뢰도 표기가 필수다.

# 2) Proposed Method
- 시계열 멀티모달 센싱 문제를 RNN(LSTM) 기반 지도회귀로 구성.
- 출력은 점추정이 아니라 평균/분산을 함께 예측하는 확률적 모델로 구성하여 aleatoric uncertainty를 학습.
- 다중 모델 앙상블을 결합해 epistemic uncertainty를 반영.
- 단일 flex 센서(+압력 입력)로 다음을 동시 추정:
  - 액추에이터 full-body configuration(여러 마커 좌표)
  - 외력 크기 및 접촉 위치

# 3) 정량 및 정성적 결과
## 정량 결과
| 항목 | 결과 |
|---|---|
| 예측 대상 | 다중 마커 좌표 + 외력 크기/위치 |
| 비교 결과 | 제안법이 baseline 및 MC-dropout 대비 더 낮은 NLL/RMSE 보고 |
| 모델 구성 예 | 앙상블 M=10 설정으로 성능-비용 균형 |

## 정성 결과
- 예측 불확실성이 높은 구간에서 실제 오차 증가와 함께 분산이 커지는 경향을 보여, 신뢰도 표현이 가능함.
- OOD(센서 드리프트 모사) 조건에서 불확실성이 상승해 안전한 판단(개입/보수적 제어)에 유용함을 보임.
- 최소 센서 기반 멀티모달 추정 프레임워크로 확장성 및 해석 가능성을 제시.

## 한줄 평가
- 이 논문은 소프트 로봇 지각에서 점추정 중심 한계를 넘어, **예측값과 신뢰도를 함께 제공하는 딥러닝 기반 불확실성 프레임워크**를 실험적으로 검증했다.
