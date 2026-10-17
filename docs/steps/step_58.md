# Step 58 — IK Handle·Bind Skin·Paint Skin Weights·가중치 복사/미러

근거: `research/maya/workflows/rigging.md` §1.2–1.3 (7 IK Handle Tool: 시작·끝 조인트 클릭 → `ikHandle1` + `effector1`, 8 Pole Vector
로케이터 → ikHandle 순서, 11 Bind Skin, 12 Paint Skin Weights (Influences 목록·잠금·Add/Replace/Smooth/Scale, Value, Flood), 14 Mirror /
Copy Skin Weights, Copy/Paste Vertex Weights), §2 7–15 (kit: `pose.ik_add` 포즈 모드만·끝 본 IK; Bind Skin = `parent_set(ARMATURE_AUTO)` 는
아마추어가 활성이어야 함; Paint = 메시만 웨이트 페인트, 영향 목록은 Properties; Mirror = 활성 그룹 하나; Copy 회색), §3 (Paint 20, IK 16,
Bind 16), §4 개념 7 (단위)·8 (스킨 = Armature 모디파이어 + 정점 그룹, influence = 본 이름 그룹), §5 후보 C,
shots `rigging_03.png` (ikHandle1), `rigging_04` (artAttrSkinContext), `rigging_05_win1.png` (Component Editor).
Spline IK, Component Editor 표는 PLAN 「Left out」 (이번에 안 함).

## 계획

### 실측 (Blender 4.5 헤드리스, `tmp/probe58/p.py`)
- `object.parent_set(type='ARMATURE_AUTO')` (아마추어 활성) = Armature 모디파이어 + 본 이름 정점 그룹 3 개 + 메시가 아마추어 자식.
  이어서 메시에 `parent_clear(CLEAR_KEEP_TRANSFORM)` = 부모 없음, 월드 그대로, 모디파이어·그룹 남음.
- 아마추어와 메시를 함께 고르고 메시 활성으로 `paint.weight_paint_toggle` = PAINT_WEIGHT + **아마추어가 자동으로 POSE** (Ctrl+클릭 본
  선택이 되는 상태); 끄면 둘 다 OBJECT.
- `object.data_transfer` 에 `use_reverse_transfer` (선택 → 활성), `layers_select_src/dst`. Kinematic 제약에 `chain_count`, `pole_target`,
  `pole_angle`, `use_tail`. `vertex_group_mirror` 는 `.L/.R` 이름으로만 그룹 짝을 찾음 (jointN 이름은 짝이 없음).

### 1. IK Handle Tool `maya_kit.ik_handle` (모달, delegated)
- Skeleton > Create IK Handle, 셸프 IKHandleTool. 포즈 모드에서 조인트 둘이 이미 선택돼 있으면 (루트 쪽 = 시작, 활성 = 끝) 바로 만듦,
  아니면 창 모달: 클릭 = 화면에서 가장 가까운 조인트 (조인트 = 본 머리, 끝 조인트 = 꼬리, 화면 거리 25 px × 배율 안), 첫 클릭 시작,
  둘째 클릭 끝 → 만들고 끝; Esc = 취소, 다른 이벤트 PASS_THROUGH (탐색). joint_tool 처럼 마우스 아래 3D 뷰를 직접 찾음.
- Maya 끝 조인트 = 점, Blender IK 는 본 꼬리를 목표로 끔 → **IK 제약은 끝 조인트로 들어오는 본** (끝 조인트를 머리로 가진 본의 부모 =
  꼬리가 끝 조인트인 본) 에, `chain_count` = 시작 조인트 본부터 그 본까지 본 수, `use_tail`. 끝 조인트가 체인의 끝 (꼬리) 이면 그 본.
- 목표 = 빈 오브젝트 `ikHandle1` (`naming`), 끝 조인트 월드 위치, 표시 크기 `maya_unit()` (결정 8). 만든 뒤 오브젝트 모드, ikHandle1 만
  선택·활성 (Maya: 바로 W 로 끌 수 있음). 제약 이름 `ikHandle1` (CB INPUTS 에 노드로 보임, step 55). effector 노드는 없음 (안내).
- Constrain > Pole Vector `maya_kit.pole_vector`: 로케이터 → ikHandle (활성) 순서. 활성 오브젝트를 목표로 하는 IK 제약을 찾아
  `pole_target` = 다른 선택, `pole_angle` = 지금 자세가 돌지 않는 각 (체인 첫 본 X 축과 극 방향의 부호 각).

### 2. Bind Skin `maya_kit.bind_skin` (delegated)
- 선택 순서 무관 (Maya: 조인트 먼저 메시 나중이 습관): 선택 중 아마추어 하나 + 메시들 (포즈 모드면 그 아마추어). 아마추어를 잠시 활성으로
  `parent_set(ARMATURE_AUTO)` → 메시마다 `parent_clear(CLEAR_KEEP_TRANSFORM)` (Maya skinCluster 는 메시를 조인트 밑에 두지 않음) →
  Max Influences (Maya 기본 5) 로 `vertex_group_limit_total` + 정규화. Bind to: Joint hierarchy (전체, 기본) / Selected joints (포즈 모드에서
  고른 본 그룹만 남기고 정규화). 끝나면 메시가 활성 (Maya 와 같은 선택). 옵션 = Adjust Last Operation (option box = 길게 누름).
- Unbind Skin `maya_kit.unbind_skin`: 아마추어를 쓰는 Armature 모디파이어와 그 본 이름 그룹 제거.

### 3. Paint Skin Weights `maya_kit.paint_skin_weights` + 영향 목록 패널 (delegated)
- 스킨된 메시 (Armature 모디파이어) 를 고르고 실행: 오브젝트 모드에서 메시 + 그 아마추어 선택, 메시 활성 → `weight_paint_toggle`
  (아마추어가 자동 포즈 = Ctrl+LMB 로 조인트 고르기). 이미 웨이트 페인트면 오브젝트 모드로 (Maya 도구 끄기).
- 패널 `MAYAKIT_PT_paint_skin_weights` (3D 뷰 사이드바 "Channel Box" 탭, 웨이트 페인트 모드만, 맨 위): Maya Tool Settings 의 Influences
  목록 = 아마추어 본 이름인 정점 그룹 (`template_list`, 잠금 아이콘 = `lock_weight`), 행 클릭 = 활성 그룹 = 칠할 조인트 (+ 그 본을 활성
  본으로). Paint operation Replace / Add / Scale = 브러시 blend MIX / ADD / MUL, Smooth = Blur 툴, Value = 브러시 weight, Opacity = strength,
  Flood = `paint.weight_set`. 메뉴 Paint Skin Weights 와 셸프도 이 연산자.

### 4. Copy / Mirror Skin Weights, Copy / Paste Vertex Weights
- Copy Skin Weights `maya_kit.copy_skin_weights`: 원본 → 대상 (활성) 순서 (Maya), `data_transfer(VGROUP_WEIGHTS, use_reverse_transfer,
  POLYINTERP_NEAREST, src ALL → dst NAME)`; 대상에 Armature 모디파이어가 없으면 원본의 아마추어로 만듦.
- Mirror Skin Weights `maya_kit.mirror_skin_weights` (Maya 기본 Mirror across YZ, Positive to negative): 모든 그룹; 정점 짝 = 반사 위치에
  가장 가까운 정점 (KDTree), 그룹 짝 = 반사 위치에 있는 조인트 (머리·꼬리 반사가 맞는 본, Mirror Joints 의 jointN 복제도), 없으면 같은
  그룹 (가운데 조인트). Blender `vertex_group_mirror` 는 `.L/.R` 이름 짝만 알아서 안 씀.
- Copy / Paste Vertex Weights `maya_kit.copy_vertex_weights` / `paste_vertex_weights`: 편집 모드 활성 정점의 가중치를 기억 → 선택 정점에.
- Set Max Influences `vertex_group_limit_total`. Smooth / Prune / Normalize / Go to Bind Pose 매핑 그대로.

### 5. 검증
- 헤드리스 `tests/test_step58_skin.py`: IK (체인 수, 대상 본, 위치, ikHandle1, 오브젝트 모드·선택, 잘못된 쌍 거절), 화면 픽 함수, Pole Vector
  (pole_target, 각으로 자세 유지), Bind Skin (순서 무관, 부모 없음, 그룹 3, Max Influences, Selected joints), Unbind, Paint 진입 (메시 웨이트
  페인트 + 아마추어 포즈, 토글), 패널 목록 = 영향, Copy (다른 메시로), Mirror (+X → −X, jointN 짝), Copy/Paste Vertex Weights, 메뉴·셸프 매핑.
- GUI `tests/gui/gui_step58_skin.py` (rigging_04 순서, 1.25 / 0.8): 실린더 + 조인트 3 → 조인트 (skeleton1) 클릭 → Shift+실린더 클릭 → Skin >
  Bind Skin → Armature + 그룹 3 → Skin > Paint Skin Weights → 패널 목록 joint2 클릭 → 메시 위 LMB 드래그 → joint2 가중치 합 증가, 스크린샷.
- dogfood 47/47.

## 실측 (구현 중)

- 백그라운드 `bpy.ops.X('INVOKE_DEFAULT')` 는 창이 없어 invoke 대신 execute 를 부름 → ik_handle 에 execute (선택된 두 조인트) 경로.
- `data_transfer(use_reverse_transfer=True)` 는 `layers_select_src` / `dst` 의 열거 항목이 서로 바뀜: 선택 → 활성 전체 그룹 =
  `layers_select_src='NAME', layers_select_dst='ALL'` (`tmp/probe58/dt.py`).
- Pole Vector 각: 해석식 (첫 본 X 축 ↔ 극 평면) 은 roll 에 따라 부호·반 바퀴가 달라 무릎이 뒤집힘 (측정 −y 로) → 후보 a, −a, a+π, −a+π 를
  평가해 체인이 가장 덜 움직이는 각 (`set_pole`).
- 머리 없는 사이드바 패널은 저장된 패널 순서 때문에 Channel Box / Layer Editor 아래로 감 (GUI 스크린샷) → Paint Skin Weights 설정은 CB
  패널 맨 위에 그림 (`paint_weights.draw`, 웨이트 페인트 모드만).

## 한 것

- `operators/skin.py` (새):
  - `maya_kit.ik_handle`: 포즈 모드에서 두 조인트가 선택돼 있으면 바로 (execute), 아니면 창 모달 — 클릭 = 화면에서 가장 가까운 조인트
    (`joints_of`: 본 머리 + 체인 끝 꼬리, 25 px × 배율), 시작 → 끝. `ik_chain` = 끝 조인트로 들어오는 본 + chain_count, `create_ik` = IK
    제약 (이름 ikHandleN, use_tail) + 빈 오브젝트 `ikHandleN` (표시 크기 `maya_unit()`) → 오브젝트 모드, 핸들만 선택·활성. effector 없음 안내.
  - `maya_kit.pole_vector` (로케이터 → ikHandle): `pole_target` + 자세를 지키는 `pole_angle`.
  - `maya_kit.bind_skin` (선택 순서 무관, Bind To Joint Hierarchy / Selected Joints, Max Influences 5): ARMATURE_AUTO → 메시 부모 해제
    (월드 유지) → limit_total + normalize. `maya_kit.unbind_skin`.
  - `maya_kit.paint_skin_weights`: 메시 + 아마추어 선택 → 웨이트 페인트 (아마추어 자동 포즈), 다시 = 끄기.
  - `maya_kit.copy_skin_weights` (원본 → 대상, 대상에 Armature 모디파이어), `maya_kit.mirror_skin_weights` (YZ / XY / XZ, +→− /
    −→+, 정점 짝 = KDTree 반사 위치, 그룹 짝 = 반사 위치의 조인트 `mirror_group_names`), `maya_kit.copy_vertex_weights` /
    `paste_vertex_weights` (편집 모드, bmesh deform 층).
- `ui/paint_weights.py` (새): `MAYAKIT_UL_influences` (조인트 그룹만, 이름 순, 잠금), `draw` (Influences 목록, Replace / Add / Scale =
  brush blend, Smooth = Blur 툴, Value / Opacity, Flood, Ctrl+LMB 안내) — `ui/channel_box.py` 가 웨이트 페인트 모드에서 맨 위에 그림.
- `ui/menu_map.py`: Skeleton > Create IK Handle, Constrain > Pole Vector, Skin > Bind / Unbind / Paint / Mirror / Copy Skin Weights,
  Copy / Paste Vertex Weights, Edit Influences > Set Max Influences. `ui/shelf_map.py`: IKHandleTool, SmoothBindSkin,
  ArtPaintSkinWeightsTool.

## 검증

- 헤드리스 `tests/test_step58_skin.py` 11/11, 전체 462/462 (step 57 451 + 11).
- GUI `tests/gui/gui_step58_skin.py` 8/8 (1.25 / 0.8), MayaKit 레이아웃: pCylinder1 (높이 분할) + skeleton1 (joint1–3) → 뷰에서 조인트
  클릭 → Shift+실린더 클릭 → Skin > Bind Skin (B) → Armature (skeleton1) + 그룹 3, 부모 없음 → Skin > Paint Skin Weights (P) → 웨이트
  페인트 + 아마추어 POSE → 도크 Influences 목록 joint2 클릭 → LMB 드래그 → joint2 가중치 합 증가. 스크린샷 직접 확인
  (`gui_step58_paint_panel.png`, `_painted.png`).
- GUI 전체 384/384 (0.8) · 383/383 (1.25), dogfood 47/47 (콘솔 오류 0).

## 남은 것

- PLAN 「Left out」: Spline IK, Component Editor 가중치 표 (정점 × 조인트), Interactive Bind Skin, Hammer / Reset / Move Weights,
  Export / Import Weight Maps.
- IK Handle Tool 은 GUI 로 클릭 경로를 돌리지 않음 (헤드리스: 선택 두 조인트 경로·화면 픽 함수) → manual_checks. Preferred Angle /
  IK 솔버 (RP/SC) 선택 없음, effector 노드 없음 (안내만).
- 웨이트 페인트 색은 Blender (파랑→빨강) — Maya 흑백 표시 아님. 목록 클릭이 뷰의 활성 본까지 바꾸지는 않음 (Ctrl+LMB 는 둘 다).
- Bind Skin 옵션은 Adjust Last Operation (길게 누름) — Maya 옵션 창의 Bind method / Skinning method / Dropoff 없음 (Blender = Bone Heat).
