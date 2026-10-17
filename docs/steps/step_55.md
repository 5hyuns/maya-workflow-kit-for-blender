# Step 55 — 포즈 본 = Maya 조인트 선택: Channel Box·Outliner·AE 와 제약 가중치

근거: `research/maya/workflows/rigging.md:63-65` (CB 가 `active_object` 만 봄, 본 기본 쿼터니언, Outliner 에 조인트 계층 없음),
`:99` (점수 25), `:134-136` (개념 결정 1·2: 조인트 = 본, 포즈 모드 = 조인트 선택 상태), `:154-155` (후보 B),
`research/maya/workflows/animation.md:42` (Maya 제약 결과 `pCube1_parentConstraint1`, 가중치 `locator1W0`, 제약 채널 파랑),
`:74` (kit: 가중치 = influence 하나, CB 에 제약 행 없음), `:126` (제약 가중치 = influence, CB INPUTS 에 `<타깃>W0`),
`research/maya/channel_box.md:138-139` (필드 색: constraint = blue), `research/maya/ae_templates.json` `joint`
(`AEjointTemplate.mel:25-54`: Transform Attributes / Joint (+ Joint Labelling) / Pivots / Limit Information / Display),
`docs/PLAN.md` W1.

## 계획

### 실측 (Blender 4.5, `tmp/probe55/probe.py`, 헤드리스)
- `PoseBone.path_from_id("location")` = `pose.bones["joint2"].location`; `pb.keyframe_insert("location", index=0)` 와
  `pb.keyframe_insert('["curl"]')` 모두 아마추어 오브젝트의 액션에 들어가고 F-커브 그룹 = 본 이름.
  `action_get_channelbag_for_slot(ad.action, ad.action_slot)` (step 38 의 `_fcurves`) 로 그대로 찾음.
- PoseBone 은 ID 속성 (`pb["maya_kit_cb_hidden"]`), `lock_location/rotation/scale`, `rotation_mode`, `constraints` 를 Object 와 같은 이름으로 가짐.
- 4.5 PoseBone 에 `select` 없음 → `pb.bone.select` (5.x 는 `PoseBone.select` 가 생겼을 수 있어 `getattr` 로 둘 다).
- 본 가시성 `Bone.hide` 의 경로는 아마추어 데이터 (`bones["joint2"].hide`) — 오브젝트 액션에 키를 못 넣음.
- `context.active_pose_bone` 은 헤드리스에서도 있음 (선택 안 된 활성 본도 돌려줌).

### 1. 노드 = Object 또는 PoseBone (delegated) — `ui/channel_box.py`
- 채널 함수 (`has_channel/get_value/set_value/is_locked/set_locked/is_hidden/is_keyable/keyframe/fcurve/driver/channel_state`)
  의 `ob` 는 이제 "노드": Object 또는 PoseBone. 이름이 같은 RNA (location / rotation_euler / scale / lock_* / rotation_mode /
  ID 속성) 를 그대로 쓰고, 애니메이션 쪽만 `node.id_data` (아마추어 오브젝트) 의 animation_data 에서
  `full_path(node, path)` = `node.path_from_id(path)` (본) / `path` (오브젝트) 로 찾는다. 키는 `node.keyframe_insert` (본이면 아마추어 액션,
  그룹 = 본 이름).
- 가시성 (v): 본은 `bone.hide` (반전). 키 불가 (경로가 아마추어 데이터라 Maya 처럼 같은 액션에 못 넣음) — `is_keyable(pb, "v")` False.
- `lead()` / `targets()`: 활성 오브젝트가 포즈 모드 아마추어면 **활성 본이 선택돼 있으면 그 본, 아니면 선택된 첫 본, 없으면 None**
  (Maya: 선택이 없으면 빈 CB). targets = 포즈 모드인 모든 아마추어의 선택된 (숨지 않은) 본, lead 먼저. 그 밖은 지금처럼 오브젝트.
- 아마추어 편집 모드: CB 는 「Placing joints — channels are in pose mode」 한 줄 (rigging.md:136; 조인트 배치는 step 57 Joint Tool).
- 오브젝트 모드에서 아마추어가 lead: 머리 아래 안내 「Joint channels: Ctrl+Tab (pose mode)」.
- 쿼터니언 / 축-각 노드: 지금의 「Rotation mode …」 줄 + 「Rotate Order XYZ」 버튼 (`maya_kit.cb_rotate_order`, targets 모두;
  `rotation_mode` RNA 설정은 Blender 가 값을 변환하므로 자세 유지).
- Object 메뉴 (Maya: 선택 목록에서 lead 고르기) / `cb_make_lead`: 포즈 모드면 본 목록, 고르면 활성 본.
- SHAPES 는 오브젝트만, INPUTS = 모디파이어 (오브젝트) + 제약 (아래 3).
- 행 다시 만들기 (`rebuild_rows`) 와 서명은 lead 노드 기준 (본이면 아마추어 + 본 이름 + 커스텀 키 + 제약).

### 2. 포즈 모드 진입·슬라이더 (delegated)
- Maya 에는 포즈 모드가 없다: 조인트를 클릭하면 그냥 고른 상태. Blender 는 오브젝트 모드에서 아마추어를 클릭하면 아마추어 전체.
  자동 진입은 하지 않는다 (rigging.md:136: 다른 오브젝트 선택이 끊김). 대신
  - **Ctrl+Tab** = `object.posemode_toggle` ("Object Non-modal", Blender 기본 키맵과 같은 키; 아마추어가 아니면 PASS_THROUGH (실측) → Screen 의
    Ctrl+Tab 그대로). 가림은 `shadows` 로 기록.
  - kit Outliner 의 조인트 행 클릭 = 포즈 모드 + 그 본 선택 (아래 4).
- MMB 가상 슬라이더: `cb_virtual_slider` 가 포즈 모드에서도 (본 채널), "Pose" 키맵에 MMB 항목 (Object Mode 와 같이).

### 3. 제약 가중치 행·제약 채널 파랑 (delegated)
- Blender 제약은 대상 하나 = 제약 하나 (animation.md:126). INPUTS 에 노드의 제약마다 Maya 노드 이름
  `<노드>_<mayaType><n>` (CHILD_OF parentConstraint, COPY_LOCATION pointConstraint, COPY_ROTATION orientConstraint, COPY_SCALE
  scaleConstraint, TRACK_TO / DAMPED_TRACK / LOCKED_TRACK aimConstraint, COPY_TRANSFORMS parentConstraint, 그 밖 = Blender 이름)
  한 줄 + 가중치 행 `<타깃>W0` = `constraint.influence` (타깃 아마추어 + 본이면 본 이름, 타깃 없으면 `W0`).
  행은 `Scene.maya_kit_cb.rows` 의 kind `CONSTRAINT` (mod_type = 제약 type, nth = 그 type 중 순서) → 입력은 선택된 모든 노드의 같은
  제약에 (step 38 규칙). 끈 제약 (`enabled` False / mute) 은 이름을 흐리게.
- 제약된 채널: 켜진 제약이 움직이는 채널 (축 플래그 반영: CHILD_OF use_location_x… / COPY_LOCATION·ROTATION·SCALE use_x/y/z /
  COPY_TRANSFORMS·ARMATURE 전부 / TRACK 계열 회전) 의 값 칸을 **눌린 버튼** 으로 그린다 — 테마 `wcol_tool.inner_sel` = Maya 선택 파랑
  #5285a6 (tools/make_theme.py:42) 이라 Maya 의 파란 제약 칸처럼 보임. 클릭 = 채널 선택 (Maya 에서도 제약 채널 값은 제약이 정함),
  상태 아이콘 `CONSTRAINT`. 입력 (`apply_entry`, 여러 채널 선택 + 다른 칸에 입력) 은 막지 않음 (Blender 는 제약 전 값도 의미가 있음).
  UILayout 에 색 지정이 없어 이것이 유일한 파랑 (alert = 빨강은 키 상태가 씀).

### 4. Outliner 조인트 행 — `ui/outliner.py` (delegated)
- 행 종류 `JOINT` (+ `bone` 이름): 펼친 아마추어 오브젝트 아래에 뿌리 본부터 깊이 우선 (본 순서), 본마다 펼침 상태
  (`Bone.maya_kit_expanded`, Maya autoExpand 0 = 접힘), 아이콘 `BONE_DATA`, 눌림 = 본 선택, 이름 편집 = 본 이름.
- 클릭: 아마추어를 활성으로, 포즈 모드가 아니면 포즈 모드로, 본 선택 (Ctrl 토글, Shift 범위는 같은 아마추어의 본만), 활성 본.
  포즈 모드에서 오브젝트 행을 클릭하면 오브젝트 모드로 나간 뒤 지금처럼 선택.
- MayaKit 레이아웃의 Outliner 는 Blender 의 C 트리 (step 49) 라 행을 더할 수 없다: 그 Outliner 에서는 Display > Shapes (오브젝트 내용) 를
  켜면 Armature 아래에 본 계층이 나온다 (남은 것에 기록). kit Outliner (사이드바 "Outliner" 탭, Dock Only 끄면) 는 위대로.

### 5. AE joint — `ui/attribute_editor.py`, `ui/ae_layout.py`
- lead 가 본이면 AE = 탭 `joint1` (joint) + 제약마다 탭 (Maya 노드 이름, 형식 = 일반 속성 목록 + Weight = influence).
- `JOINT` 섹션 (템플릿 `joint` 로 테스트가 이름 검사): Transform Attributes (Translate/Rotate/Scale, Rotate Order) / Joint
  (Joint Orient = rest 방향, 부모 rest 기준 오일러 XYZ 읽기 전용, 「Blender 조인트는 Y 축이 다음 조인트를 향함 (Maya Primary X)」,
  Draw Style = 아마추어 `display_type`, Stiffness = `ik_stiffness_x/y/z`, Segment Scale Compensate ≈ `bone.inherit_scale`) /
  Limit Information (Translate / Rotate / Scale = 본 Limit 제약, 버튼이 본에 붙임) / Display (Visibility = bone.hide, Display Local
  Axis = 아마추어 `show_axes`, Display as Control Shape = `custom_shape`, Always Draw On Top = 아마추어 오브젝트 `show_in_front`) /
  Extra Attributes (본 ID 속성).
- 아마추어 편집 모드 = CB 와 같은 한 줄.

### 6. 검증
- 헤드리스 `tests/test_step55_pose_cb.py`: lead/targets (포즈 모드·선택 없음·편집 모드), 채널 읽기/쓰기·`+=10` 입력 (여러 본),
  Key Selected / Breakdown / Mute / Delete / Break / Lock / Hide / Nonkeyable / Duplicate Values 가 본에 (경로
  `pose.bones["joint1"].rotation_euler`), 쿼터니언 행 + Rotate Order XYZ (자세 유지), 제약 행 이름·`locator1W0` 입력 → influence 0.5,
  제약 채널 집합, Outliner 행 (계층·펼침·클릭 = 포즈 모드 + 선택), AE joint 섹션이 템플릿에 있는 이름, 등록 해제 시 `Bone` 속성 정리.
- GUI `tests/gui/gui_step55_pose.py` (0.8 / 1.25): 아마추어 (kit Create Joints + 본 2 개) → Ctrl+Tab 포즈 모드 → 뷰에서 본 클릭 → CB
  머리 = 조인트 이름, Translate/Rotate/Scale 행 (XYZ) → Rotate Z 칸에 `+=10` → S → 키 → Rotate 행 선택 + Channels > Lock Selected →
  뷰에서 E 회전 드래그해도 회전 그대로; 로케이터 대상 Copy Location 제약 → CB `locator1W0` 행에 0.5 → influence 0.5, Translate 칸 파랑
  (스크린샷 확인).
- `docs/manual_checks.md`, dogfood 47/47, 헤드리스 전체.

## 한 것

- `ui/channel_box.py`: 노드 = Object 또는 PoseBone. `lead()` / `targets()` 가 포즈 모드에서 활성 (선택된) 본 / 선택된 본 (포즈 모드인
  모든 아마추어), `is_bone`, `bone_selected` / `set_bone_selected` (4.5 `Bone.select`, 새 버전 `PoseBone.select` 대비), `pose_armature`,
  `placing_joints`, `full_path` (= `path_from_id`; 본 가시성은 None). `_fcurves` / `fcurve` / `driver` / Break Connections 가
  `node.id_data` 의 animation_data 를 씀 → Key Selected·Key All·Breakdown·Mute·Delete·Break·Lock·Hide·Nonkeyable·Duplicate
  Values·`+=` 입력·MMB 슬라이더가 본에도. 본 가시성 = `bone.hide`, 키 불가.
- 쿼터니언 / 축-각 노드: 「Rotation mode …」 줄 + 「Rotate Order XYZ」 (`maya_kit.cb_rotate_order`, targets 모두, 자세 유지).
- 아마추어 편집 모드 = 「Placing joints: / channels are in pose mode」, 오브젝트 모드 아마추어 = 「Joint channels: Ctrl+Tab (pose mode)」.
- Object 메뉴·`cb_make_lead` 가 포즈 모드에서 본 목록 / 활성 본.
- 제약 = INPUTS 노드: `constraints()` (Limit 제외), `constraint_node_name` (`joint2_pointConstraint1`), `weight_name`
  (`locator1W0`, 아마추어 대상은 본 이름), 행 kind `CONSTRAINT` (= influence, 선택된 모든 노드의 같은 제약에),
  `constrained_keys` (축 플래그·켜짐 반영) → 그 칸을 눌린 버튼 (테마 선택 파랑) + `CONSTRAINT` 아이콘으로.
- 키맵 (`maya_patches.patch_pose_joints`): Ctrl+Tab = `object.posemode_toggle` ("Object Non-modal", Screen 의 Ctrl+Tab 을 가림 →
  `shadows=("Screen",)` 로 기록; 메시에서는 PASS_THROUGH 실측), "Pose" MMB = `cb_virtual_slider` (슬라이더 invoke 가 POSE 허용).
  Maya 단축키 행이 아니라 `keymap/mapping.py` 행은 없음 (F8 처럼 kit 보조 키).
- `ui/outliner.py`: `JOINT` 행 (`bone`), 펼친 아마추어 아래 본 계층 (`Bone.maya_kit_expanded`, 기본 접힘), 클릭 = 포즈 모드 + 본
  (Ctrl 토글, Shift 같은 아마추어 범위), 포즈 모드에서 오브젝트 행 = 오브젝트 모드로, 이름 편집 = 본 이름, 아이콘 `BONE_DATA`,
  활성 행 = 활성 본.
- `ui/attribute_editor.py` + `ui/ae_layout.py`: 본이면 탭 `joint` + 제약 노드 탭; `JOINT` 섹션 (Maya `joint` 템플릿 이름·열림 상태,
  test_step11 이 검사), Joint Orient (부모 rest 기준 rest 회전, 읽기 전용) + 축 안내, Stiffness, Draw Style, Segment Scale
  Compensate ≈ `inherit_scale`, Limit 버튼이 본에, Display as Control Shape; 제약 탭 = Enabled + `<타깃>W0` (influence) + 설정.
- `tests/kit.py` 스냅샷에 `Bone` / `PoseBone` 속성 추가 (새 `Bone.maya_kit_expanded` 해제 검사).

## 검증

- 헤드리스 `tests/test_step55_pose_cb.py` 10/10, 전체 430/430 (step 54 420 + 10).
- GUI `tests/gui/gui_step55_pose.py` 14/14 (1.25 / 0.8 모두): skeleton1 → Ctrl+Tab 포즈 모드 → 뷰에서 joint2 클릭 → CB lead joint2
  (Euler 행) → Rotate Z 칸 `+=10` → 10° → S → `pose.bones["joint2"].rotation_euler` F-커브 → 채널 이름 클릭 = 채널 선택 → Lock
  Selected → `transform.rotate` 두 번 해도 그대로 → Copy Location (locator1) → CB `locator1W0` 칸에 0.5 → influence 0.5 → AE joint
  탭. 스크린샷 (`gui_step55_cb_joint.png`, `_cb_weight.png`, `_ae_joint.png`) 직접 확인: 조인트 이름 머리, 키 행 빨강, 잠긴 Rotate
  흐림, 제약된 Translate 파랑, INPUTS `joint2_pointConstraint1` / `locator1W0 0.5`, AE Transform Attributes / Joint 섹션.
- GUI 전체 356/356 (0.8) · 355/355 (1.25) (step 54 342 · 341 + 14), dogfood 47/47 (콘솔 오류 0).

## 남은 것

- MayaKit 레이아웃의 Outliner 는 Blender C 트리라 조인트 행을 더할 수 없음: Display > Shapes (오브젝트 내용) 를 켜야 Armature 아래 본
  계층이 보이고, 오브젝트 모드에서 그 본을 눌러도 포즈 모드로 안 들어감 (Blender 동작). kit Outliner (사이드바, Dock Only 끔) 만 Maya 식.
- CB 값은 Blender 의 제약 전 값 (Maya 는 제약 결과를 보여 줌). 파란 (제약) 칸은 버튼이라 그 칸에 직접 입력 못 함 (여러 채널 선택 후
  다른 칸 입력은 적용됨). 제약 여러 대상 블렌드 (W0/W1…) 는 Blender 제약 하나 = 대상 하나라 없음 (Armature 제약 targets 는 미처리).
- Constrain 메뉴가 포즈 모드에서 본에 붙는 분기, Maintain Offset = step 59. Joint Tool·조인트 픽워크 (↑↓) = step 57 — 이번 GUI 는
  본을 스크립트로 만들고 Shift+클릭 대신 채널 선택을 스크립트로 둠 (시뮬레이션 Shift 가 UI 버튼 연산자 event 에 안 닿음).
- 본 가시성 키, Joint Labelling / Preferred Angle (Blender 대응 없음), Joint Orient 값은 Blender 본 축 (Y = 본 방향) 기준이라 Maya
  숫자와 다름 (안내만, 결정 1).
- 5.x 에서 `PoseBone.select` 사용 여부는 shim 만 넣고 측정 안 함 (다음 5.x 회차에 `--blender` 로 확인).
