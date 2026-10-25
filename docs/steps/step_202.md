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

## 한 일

- **(1) Non-Deformer History** (레인 X): `operators/history.py` `is_deformer` = `DEFORMERS` 종류 + 킷 Wire
  (`wire_deformer.is_wire`) + skin weight-sum (`skin_tools_199.is_part`); "All" / "before deformers only" 둘 다. 전체 Delete History 는
  Maya 처럼 모두 굽는다.
- **(2) 제약 helper**: `constrain_199.helpers_owned_by` / `remove_helpers`; `dag.delete_hierarchy` (allset.delete, Edit > Delete) 와
  Delete by Type > Constraints 가 Normal / Tangent helper empty 도 지움. Outliner Delete · Blender X 는 그대로 (delegated).
- **(3) All by Type**: `operators/by_type.py` Wires / nCloths / nParticles / nRigids (select + delete; wire = 커브 선택 — Maya 는 wire
  노드, 킷 wire 는 오브젝트 없는 모디파이어라 delegated), `history.TYPES`, `menu_map`. Fluids 는 회색 그대로.
- **(4) Add Influence** (레인 Y, mayapy 23 경우, `research/maya/re/add_influence_202.md`): w_i = d_i^-dropoff_i (조인트 선분까지 거리,
  기존 influence 는 bind 때 dropoff 4, 새 것은 옵션 값), 잠금 없음 + 개수 ≤ max = 전부 다시 계산 (칠한 가중치 버림), 개수 > max = 큰 것
  max 개 (새 것 + 전에 > 0 인 것만), 잠금 = 남은 1 − Σlocked 를 비례 분배. `rig_maya.maya_add_weights` / `add_influence(dropoff=4.0)`.
  [U] 1 정점 (`plane_max2_lock_j2`, 동점 + 잠금) 은 테스트에서 뺌. max influences = 메시 ID prop `allset_max_influences` 또는 5 (delegated).
- **(5) Time Slider 현재 칸 (UI 1.25)**: 원인 = 템플릿 timeline 영역 높이가 px 고정이라 1.25 에서 header 가 커지며 ruler 가 29 px 로 줄고
  Blender 의 현재 프레임 상자가 칸을 거의 다 덮음 (1.0 = 36 px). `ui/toolbox.fit_columns` 가 shelf 처럼 Time Slider 를
  `TIME_SLIDER_PX` (36) × scale + header 로 맞춤 (1.25: 61 → 77 px, ruler 45 px). look_compare 표본은 고정 x 가 칸을 벗어나 있어
  `look_shots` 에 `timeline.current` (현재 프레임 칸) 앵커를 추가하고 표본을 거기로. 더 낮아진 dock 에서 Layer Editor 목록 몸통 찾기
  (`maya_dock._list_hole`) 가 한 줄만 읽어 놓쳐서 목록이 #3a3a3a 로 들렸음 → 위로 훑고 맞은 줄을 기억.
- **(6) Channel Box 메뉴 바**: 맞춘 폭 (look_compare 1.25 dock 346 px) 에선 "Channels" 가 다 보임; dogfood 의 "Chann..." 은 event-simulated
  세션이 dock 폭을 안 맞춰서 (265 px). 사용자가 좁힌 dock 도 잘리지 않게 AE (step 197) 처럼 `wrap_rows` 로 줄바꿈 (delegated).
  **Outliner 모드 열**: 템플릿 (`tools/make_startup.py`, startup.blend 다시 만듦) 과 `maya_outliner.setup` 에서 `show_mode_column = False`.
  Blender 는 모드 열이 켜져 있으면 object 모드에서도 1 unit 을 비워 두므로, 킷이 그리는 기본 행 / set 행 (`ui/outliner_sets.py`) 을
  모드 열 상태에 맞춰 1 unit 왼쪽으로 (안 그러면 persp 등이 pCube1 보다 25 px 오른쪽).

## 검증

- 새 헤드리스: `test_step202_history` 13 / 13, `test_step202_add_influence` 5 / 5 (mayapy 23 경우 8.1e-7), `test_step202_ui` 5 / 5.
  레인 관련 묶음 130 + 70 + 101 통과. 헤드리스 전체 **1867 / 1867** (229 파일, 마지막 변경 뒤).
- look_compare kit-drawn **12 / 12 (1.0 · 1.25 둘 다)**, viewport 20 / 20 (time_slider_current 1.25 ΔE 13.8 → 0.3, 1.0 0.0).
- GUI 관련 + 스모크 19 파일 160 / 161 → 실패 1 (`gui_step82_outliner_drag`: 고정 x = r.x + 90 이 모드 열 자리에 기대 있었음 → 행 이름
  위치로) 고친 뒤 4 파일 43 / 43; `gui_step96_sets` · `gui_step131_toolbox_icons` 16 / 16 (모드 열에 맞춘 x; step131 Layer Editor
  teal 은 step 195 의 dock lift 가 아이콘까지 올려 195 이후 실패하던 것 — 화면 색 = TEAL + lift 로 기대값 갱신).
- dogfood 48 / 48, 콘솔 0 (좁은 dock 에서 메뉴 바 "Channels Edit Object / Show" 두 줄, 컴포넌트 모드 Outliner 모드 열 없음, 그린 행 정렬 — 샷 직접 봄).

## 남은 것

- dock 의 additive lift 가 Layer Editor 툴바 아이콘 (teal) 도 +lift 만큼 밝힘 (step 195 부터) — 아이콘을 lift 만큼 미리 어둡게 그리면 정확.
- Outliner Delete · Blender 자체 X 삭제는 제약 helper 를 남김; All by Type > Fluids 회색.
- Add Influence: [U] 1 정점, Bind Skin 이 `allset_max_influences` 를 아직 안 씀 (기본 5), 옵션 창에 Dropoff 필드 없음.
- event-simulated 세션 (dogfood) 은 dock 폭 · Time Slider 높이를 안 맞춤 (`ALLSET_FIT_WARP`) — 수동 점검에 추가.
