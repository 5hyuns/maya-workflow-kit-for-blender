# Step 202 — Audit 15 fix batch (backlog #1, Issue #109)

## 계획

근거: `docs/steps/step_201_remaining.md` §4 NB7–NB10, `step_201_quant.md` §0 (time_slider_current 1.25), `step_201.md` G1 / G2.

레인 (포그라운드 에이전트 2 개 동시, Blender 최대 2 개; 파일이 겹치지 않게 나눔 — delegated):
- **X — history / 삭제 / by type** (에이전트): (1) Delete Non-Deformer History 가 킷 GN 디포머 (Wire, skin weight-sum) 를 디포머로
  봄; (2) 제약 오브젝트 삭제 · Delete by Type > Constraints 가 Normal / Tangent helper empty 도 지움; (3) Select / Delete All by Type >
  Wires / nCloths / nParticles / nRigids (Fluids) 를 킷 노드로 연결. 파일: `operators/history.py`, `operators/dag.py`,
  `operators/constrain_199.py`, `operators/by_type.py`, `ui/notices.py`, `ui/menu_map.py`, 새 테스트 `tests/test_step202_history.py`.
- **Y — Add Influence 거리 가중치** (에이전트, mayapy + 헤드리스): (4) Maya 공장값 (Use geometry on, Dropoff 4.0) 의 가중치 규칙을
  mayapy 로 측정 → `research/maya/re/add_influence_202.md`, `operators/rig_maya.py` `add_influence`, 테스트 `tests/test_step202_add_influence.py`.
- **메인 (레인 뒤, GUI)**: (5) UI 1.25 Time Slider 현재 칸 측정 후 고침 (`ui/time_slider.py`); (6) Channel Box 메뉴 바 "Chann..." 잘림,
  컴포넌트 모드 kit Outliner 의 Blender 모드 열. 레인 동안 메인은 에이전트를 기다려야 해서 (포그라운드) GUI 일을 그 뒤로 둠.
