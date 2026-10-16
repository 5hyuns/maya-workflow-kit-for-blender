# Step 39 — 컴포넌트 픽워크와 Alt+Shift 축 고정 내비게이션

## 계획 (delegated)

Maya 근거:
- 화살표 = pickWalk (research/maya/interaction.md:83, research/maya/hotkeys_and_menus.md:78, HK:364-367). Maya 2022
  `pickWalkUp/Down/Left/Right.mel`:
  - 엣지가 선택돼 있으면 Up/Down 은 `-type edgering`, Left/Right 는 `-type edgeloop`.
  - 면은 Left/Right 가 `-type faceloop`, Up/Down 은 type 없음.
  - 정점은 type 없음 (C++ 기본: 인덱스 순서 [K]).
- Alt+Shift+드래그 = 텀블/트랙을 처음 우세한 축 (가로 또는 세로) 하나로 고정 (interaction.md:46, [K] hardcoded).

Blender 4.5 지금 상태:
- 픽워크는 오브젝트 모드만 (`operators/pickwalk.py`, keymap/maya_patches.py:175-190).
- Mesh 키맵의 ↑/↓ 는 IC `mesh.select_more` / `select_less`. Maya 에서는 Shift+> / < 이고, 이미 step 18 에 있다.
- 3D View Alt+Shift+LMB 는 IC CLICK = `view3d.select` (toggle, enumerate) 다. Alt+Shift+MMB 는 비어 있다.
  Mesh Alt+Shift+LMB 더블클릭은 링 루프 선택이다.

설계:
1. **컴포넌트 픽워크** (`operators/pickwalk.py` 확장, bmesh, 이웃 계산은 순수 함수):
   - 엣지 (Maya 그대로): Up/Down = 링 이웃 (인접 사각형의 맞은편 엣지), Left/Right = 루프 이웃 (끝 정점에서 면을 공유하지 않는 엣지).
     후보 두 개 (양쪽) 중에서 화면에서 그 방향에 가까운 것을 고른다.
   - 면·정점 (delegated): Maya 는 면 Left/Right 만 faceloop 이고, 정점은 인덱스 순서라서 화면에서 예측하기 어렵다.
     그래서 화면 방향으로 정한다. 면은 엣지를 공유하는 이웃, 정점은 엣지로 이어진 이웃 중에서 화면에 투영한 방향이 화살표 방향에
     가장 가까운 것을 고른다 (사각형 격자에서는 face loop 를 따라가는 것과 같다).
   - 투영: 3D View 의 `region_3d.perspective_matrix`. 영역이 없으면 (헤드리스) 앞 뷰 (x, z) 로 투영한다.
     함수는 `project` 콜백을 받아 테스트할 수 있게 한다.
   - 각 선택 요소를 걷고, 결과만 선택한다. 활성 요소 (select_history) 도 옮긴다. 갈 곳이 없으면 그대로.
   - 키맵 (Mesh): ↑/↓ 의 IC select_more/less 를 지우고 네 화살표에 `maya_kit.pick_walk_component` 를 둔다 (repeat).
2. **Alt+Shift 축 고정** (`operators/view.py` `maya_kit.view_axis_lock`, 모달):
   - Alt+Shift+LMB = 텀블, Alt+Shift+MMB = 트랙 (3D View, PRESS).
   - 4 px 넘게 움직이면 그때 우세한 축 (|dx| ≥ |dy| → 가로) 으로 고정한다.
   - 텀블 가로 = 월드 Z 축 둘레 회전, 세로 = 뷰 오른쪽 축 둘레 회전 (중심 = view_location = Maya COI).
     감도 = 환경설정 `view_rotate_sensitivity_turntable`. 직교 측면 뷰는 기존 ortho 텀블 잠금을 따른다.
   - 트랙: 커서 아래 깊이 (view_location) 에서 픽셀 → 월드 변화량 (`region_2d_to_location_3d`) 을 고정 축 성분만 반영한다.
   - 이전 마우스 위치는 모달이 직접 기억한다 (시뮬레이션은 mouse_prev 가 갱신되지 않음).
   - 버튼을 놓으면 끝, ESC/RMB 는 처음 뷰로 되돌린다.
   - IC 의 Alt+Shift+LMB CLICK 선택은 PRESS 항목이 먼저 받으므로 쓸 수 없게 된다 (delegated: Maya 키에 없는 Blender 선택).
3. 키맵 대응표: PickWalk 행 메모 갱신, Alt+Shift 는 대응표 행이 없으므로 (Maya hotkey 아님) step 문서에만 남긴다.

검증:
- 헤드리스 `tests/test_step39_pickwalk_axis.py`:
  - 큐브/격자에서 정점·엣지·면 방향별 다음 요소 (앞 뷰 투영), 엣지 링/루프, 여러 선택, 활성 요소, 끝에서 멈춤.
  - 축 고정 순수 함수 (축 고르기, 텀블 회전 축, 트랙 성분).
  - 키맵 항목.
- GUI: 앞 직교 뷰에서 Alt+Shift+MMB 대각선 드래그 → view_location 이 가로 한 축 (x) 만 변함.
  Alt+Shift+LMB 세로 우세 드래그 → 뷰가 오른쪽 축 둘레로만 회전.
  편집 모드 정점에서 → 키 → 다음 정점.
- 키맵 대응표 재생성, 전체 헤드리스·GUI·dogfood.

## 한 것

- `operators/pickwalk.py`: 컴포넌트 픽워크.
  - 순수 함수 `edge_loop_next` / `edge_ring_next` / `neighbours` / `step_component` / `walk_components`, 투영은 `view_projector`.
  - 연산자 `maya_kit.pick_walk_component`. 선택 모드 (정점/엣지/면) 의 선택 요소마다 걷고, 활성 요소도 옮긴다.
  - 엣지: Left/Right = 루프, Up/Down = 링, 두 후보 중 화면 방향에 가까운 쪽. 경계에서 반대쪽밖에 없으면 그대로.
  - 정점·면: 화면에서 그 방향 (약 72° 안) 의 이웃.
- `operators/view.py`: `maya_kit.view_axis_lock` 모달 (TUMBLE / TRACK).
  - 4 px 뒤 우세한 축으로 고정한다.
  - 텀블은 Blender 턴테이블 수학이다: 가로 = 월드 Z, 세로 = 뷰 오른쪽 축, 감도는 환경설정.
  - 트랙은 view_location 깊이의 픽셀 → 월드 변화량.
  - ESC/RMB 는 처음 뷰로 되돌린다. ortho 측면 뷰 텀블 잠금을 따른다.
- 키맵 patch 28 (`patch_component_pick_walk`):
  - Mesh ↑/↓ 의 select_more/less 를 지우고 네 화살표에 컴포넌트 픽워크를 둔다.
  - 3D View: IC Alt+Shift+LMB CLICK 선택을 지우고 Alt+Shift+LMB / MMB = 축 고정 텀블 / 트랙.
  - 페인트 모드 키맵의 자기 Alt+Shift+LMB 선택은 `shadows` 로 둔다.
- `keymap/mapping.py` PickWalk 메모를 갱신하고 `docs/keymap_mapping.md` 를 재생성했다 (구현 95 그대로, 행 내용에 Mesh 바인딩).

## 검증

- 헤드리스 `tests/test_step39_pickwalk_axis.py` 6/6. 다음을 확인한다:
  - XZ 격자 (앞 뷰 투영) 에서 정점·면 네 방향, 엣지 루프/링, 세로 엣지, 경계 엣지.
  - 연산자: 여러 선택 + 활성 요소, 면 모드.
  - 축 고르기·고정 성분·텀블 회전 축.
  - 키맵 항목.
- `test_keymap_maya` 12/12 (가림 테스트 포함).
- 전체 헤드리스 **339/339** (37 파일), GUI **281/281** (31 파일), dogfood **47/47**, 콘솔 오류 0.
- GUI `tests/gui/gui_step39_pickwalk_axis.py` 4/4 (실제 이벤트):
  - Alt+Shift+LMB 세로 우세 드래그 → 0.39 rad 회전, 뷰 오른쪽 축 변화 0.
  - 앞 뷰 Alt+Shift+MMB 대각선 드래그 → view_location (−1.76, 0, 0) 로 X 만 변함.
  - 정점 (1,−1,1) 에서 ← → (−1,−1,1).
  - 스크린샷 `gui_step39_pickwalk.png`.
- `docs/manual_checks.md` Step 39 항목 5개.

## 남은 것

- Maya 정점 픽워크는 인덱스 순서이고 면 Up/Down 은 type 없음이다. 여기서는 화면 방향으로 했다 (delegated). Maya 와 다르게 느껴지는지는 수동 확인.
- Ctrl+PgUp / PgDn (PickWalkIn/Out, 대응표 미검토), UV 편집기 화살표 (Maya 는 UV nudge) 는 하지 않았다.
- Alt+Shift+RMB (돌리 고정) 는 Maya 에 의미가 없어 두지 않았다. 축 고정 텀블에서 Blender 의 auto perspective 전환은 없다.
- Mesh Alt+Shift+LMB 더블클릭 (IC 링 선택) 은 첫 누름을 축 고정 텀블이 받아서 쓰기 어렵다.
