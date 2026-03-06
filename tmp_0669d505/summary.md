# 0) 논문 정보
- 출간 연도: 2018
- 출간 저널: IEEE Robotics and Automation Letters
- citation 수: 170 (OpenAlex 기준)
### APA
> Choi, C. ; Schwarting, W. ; DelPreto, J. ; Rus, D. (2018). Learning Object Grasping for Soft Robot Hands. IEEE Robotics and Automation Letters. https://doi.org/10.1109/lra.2018.2810544
### BibTeX
> @article{Choi_2018, title={Learning Object Grasping for Soft Robot Hands}, volume={3}, ISSN={2377-3774}, url={http://dx.doi.org/10.1109/lra.2018.2810544}, DOI={10.1109/lra.2018.2810544}, number={3}, journal={IEEE Robotics and Automation Letters}, publisher={Institute of Electrical and Electronics Engineers (IEEE)}, author={Choi, Changhyun and Schwarting, Wilko and DelPreto, Joseph and Rus, Daniela}, year={2018}, month=jul, pages={2370–2377} }

# 1) 문제 상황
- 기존 그리핑 학습은 2D/2.5D 입력, 고정 top grasp 방향에 치우쳐 6-DoF 추론 일반화가 제한됨.
- 소프트 핸드는 순응성(compliance) 장점이 있지만, 손가락 변형 예측이 어려워 모델 기반 접촉 예측이 어렵다.
- 목표는 **사전 물체 모델 없이** 부분 포인트클라우드만으로 미지 물체의 grasp pose를 예측해 안정적으로 집는 것.

# 2) Proposed Method
- Baxter + soft hand + depth sensor 기반 end-to-end 비전 그리핑 시스템 구성.
- 입력 포인트클라우드를 object segmentation 후 voxel grid로 변환하여 3D CNN에 입력.
- 3D CNN이 grasping direction과 wrist orientation을 각각 확률로 출력.
  - 방향 제약: Nδ = 6 (top/side 계열)
  - 손목 회전 제약: Nω = 4 (0°, 45°, 90°, 135°)
- 네트워크 입력은 32 × 32 × 32 voxel grid.
- 핵심은 3D 기하 정보를 직접 학습해 top+side grasp를 모두 고려하는 점.

# 3) 정량 및 정성적 결과
## 정량 결과
| 항목 | 결과 |
|---|---|
| 미지 물체 grasp 성공률 | 87% |
| 평가 조건 | noise/occlusion 비교 평가 수행 |

## 정성 결과
- 소프트 핸드의 순응성과 3D CNN 기반 grasp pose 예측이 상호 보완적으로 동작함을 보임.
- 사전 3D object model, proprioceptive sensor 없이도 새로운 물체에 대해 실사용 가능한 grasp 성능을 달성.

## 한줄 평가
- 이 논문은 소프트 핸드 그리핑에서 2D 중심 접근의 한계를 넘어, **3D CNN 기반 다방향 grasp pose 예측**을 통해 미지 물체 일반화 성능을 실험적으로 입증했다.
