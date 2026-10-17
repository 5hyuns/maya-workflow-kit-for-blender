# Step 59 — 피벗 개념 · 스냅 전부 · 이동 매니퓰레이터 모양

Request (user, verbatim, 2026-10-18): 「피벗의 개념이나 각종 스냅 등등 그런 것들도 잊지 말라」 + 비교 이미지에서 이동 매니퓰레이터가
Blender 모양(작은 화살표·가운데 원)으로 남아 있음.

근거: Maya 2022 실측 `research/maya/workflows/pivot_snap.md` (P = 피벗, S = 스냅, M = 매니퓰레이터 행 번호), 그 밖에
research/maya/interaction.md §3-§5, research/maya/concepts.md §3/§5, docs/steps/step_10.md (피벗 = 원점, `delta_location` = 피벗 오프셋),
step_18 (편집 모드 D), step_22/26/28 (기즈모 키맵·Smart Duplicate·활성 핸들), step_25 (cm 그리드).

## 이미 한 것 (다시 하지 않음)

- step 3: X/C/V/J 홀드 = GRID/EDGE/VERTEX/INCREMENT, D 홀드 = Affect Only Origins, Insert = 토글 (`operators/hold.py`).
- step 10: Freeze 가 피벗 유지, Center Pivot = bbox 중심 (translate 불변), Ctrl+G 그룹 피벗 원점 (`operators/freeze.py`, `group.py`).
- step 18: 편집 모드 D = 3D 커서 피벗 + 커서 툴. step 25: X 그리드 = 1 cm 단계 (`grid_scale`). step 27: +/- = `gizmo_size`.
- step 28: 활성 핸들 기억 (`manip.HANDLES`) + MMB 아무 데나 드래그.
- Status Line 스냅 버튼 GRID/CURVE/POINT/LIVE 는 `ts` 를 그대로 그림 (`ui/status_line.py:121-146`).

## 계획

### 1. 피벗 편집이 Maya 의미가 되게 (P1, P3, P8, P13)

지금 D/Insert 의 Affect Only Origins 는 **location·rotation 채널을 바꾸고 자식을 움직인다** (Blender 측정, pivot_snap.md §4).
Maya 는 채널 불변, 자식 불변, 방향은 툴의 Custom 축 모드.

- 경로 후보: (a) Affect Only Origins 그대로 쓰고 변환이 끝난 뒤 kit 가 결과를 Maya 의미로 다시 쓴다 / (b) 피벗 전용 모달 (자체 드래그·스냅).
  **(a) 선택 (delegated)**: Blender 의 스냅·기즈모·축 구속·수치 입력을 그대로 얻는다. (b) 는 스냅을 다시 만들어야 한다.
- 피벗 모드 동안 `use_transform_skip_children` 도 켠다 (Blender 가 자식을 제자리에 둠).
- `operators/pivot.py` 감시자 (bpy.app.timers 0.1 s, 피벗 모드가 켜져 있거나 변환이 끝나기를 기다리는 동안만): 새로 등록된
  `TRANSFORM_OT_*` (wm.operators[-1] 포인터가 바뀜) 이 있고 실행 중인 변환 모달이 없으면, 선택 오브젝트마다 기준 상태 B0 (변환 전
  matrix_basis) 와 지금 B1 을 비교해서:
  - 피벗 월드 위치 = B1 의 이동, 채널은 그대로 → `B_final = T(B1.t) · B0.3x3` (location 원래 값, `delta_location = B1.t − location`),
  - 형상은 지금 월드 위치 그대로: 데이터에 `B_final⁻¹ · B1` 을 굽는다 (`freeze.bake_into_data`), 자식은 월드 유지 (`freeze.parent_frame`),
  - 방향이 바뀌었으면 (B1.3x3 ≠ B0.3x3) 사용자 변환 방향 「Maya Pivot」 = 피벗 월드 방향 을 만들고/갱신하고 이동 툴 슬롯을 거기로
    (Maya 축 모드 Custom, P8), 오브젝트에 `maya_kit_pivot_orient` (오브젝트 기준 쿼터니언) 를 남긴다 (Bake Pivot 용).
  - 다른 것 (채널 박스 입력·스크립트) 이 바꾼 값은 기준만 새로 잡는다 (변환 연산자가 아닐 때).
  - 언두: 변환이 끝난 상태가 언두 단계, kit 재작성은 그 뒤 (Ctrl+Z 한 번 = 변환 전). 재작성 뒤 `ed.undo_push` 는 하지 않는다 (delegated).
- 편집 모드 D (step 18 커서 피벗) 는 그대로; 커서 툴 드래그도 X/V 스냅을 받는지 GUI 로 확인.

### 2. 피벗 메뉴 · 연산자 (P5-P9)

- `maya_kit.reset_pivot` (D 모드 RMB 「Reset Pivot」, P6): 피벗 = 오브젝트 원점 (`delta_location` → 0, `freeze.shift_pivot`), 방향 리셋
  (`maya_kit_pivot_orient` 삭제, 이동 슬롯 World).
- `maya_kit.bake_pivot` (Modify > Bake Pivot, P8): 저장된 피벗 방향을 회전 채널로 (형상·자식 월드 유지), 이동 슬롯 → Object.
  위치는 kit 에서는 이미 진짜 피벗이라 굽지 않는다 (Maya 측정에서도 rp 그대로) — delegated.
- `maya_kit.match_pivots` (Modify > Match Transformations > Match Pivots, P7): 나머지 선택의 피벗 월드 위치 = 활성 (lead) 의 피벗.
- Modify 메뉴: Pivot 절 (Center Pivot, Bake Pivot) 을 Match Transformations 다음, Align 절 앞에 (S8, `menu_map.EXTRA` 수정).
- D 모드 RMB 메뉴 (Maya `buildObjectMenuItemsNow.mel:66-104`): 피벗 모드가 켜져 있을 때 오브젝트 RMB 마킹 메뉴 대신
  Reset Pivot (S) / Reset Pivot Position (SE) / Reset Pivot Orientation (SW) / Exit Pivot Mode (E). Pin / Snap Pivot 은 회색 (Blender 에 같은 것 없음).

### 3. 매니퓰레이터 위치·축 모드 (P10-P12)

- 오브젝트 모드 피벗 점 = lead (`ACTIVE_ELEMENT`), 컴포넌트 = bbox 중심 (`BOUNDING_BOX_CENTER`). `transform_pivot_point` 는 모든 모드가
  같이 쓰므로, 모드가 바뀔 때 (depsgraph 핸들러, symmetry 와 같은 방식) 값이 둘 중 하나일 때만 그 모드의 Maya 값으로 바꾼다
  (사용자가 고른 커서/개별 원점 등은 둠; 팩토리 파일의 MEDIAN_POINT 도 둠) — delegated. 템플릿은 ACTIVE_ELEMENT 로 저장.
- 축 모드 = 툴별 방향 슬롯: 이동 슬롯 1 = GLOBAL, 회전 2 = LOCAL, 스케일 3 = LOCAL (Maya 기본 P12). W/E/R 옵션 메뉴의 World/Object/Component…
  는 각 툴의 슬롯을 바꾼다 (지금은 슬롯 0). Tool Settings 팝업 (Status Line / W 메뉴 「Move Options」) 에 Maya 「Move Settings」:
  Axis Orientation, Step Snap (Off/Relative/Absolute), Retain Component Spacing, Pivot (Reset / Bake / Pivot Edit 토글).
- 템플릿 (`tools/make_startup.py`): 위 슬롯, 회전 스냅 15° (`snap_angle_increment_3d`, S3), 피벗 점 ACTIVE_ELEMENT.

### 4. 스냅 (S1-S13)

- X/C/V/J 홀드: `snap_target` = CENTER (매니퓰레이터 중심이 스냅, S4·S5; 놓으면 복원). X = GRID (절대 그리드 선, S2) 을 시작 위치 0.3 에서 확인.
- J / Step Snap: Relative = INCREMENT, Absolute = INCREMENT + `use_snap_grid_absolute` (S3). 값은 그리드 단계 (Maya 1 = 1 cm 와 같음); 다른 값은 불가 (안내).
- 회전 스텝 15°: W/E 옵션 메뉴 「Discrete Rotate」 = 회전 스냅 토글, Scale 「Snap Scale」/「Relative」 연결.
- Retain Component Spacing: Blender 스냅은 항상 간격 유지 (= Maya 기본 켬, S5). 끔 (모든 점이 한 점으로) 은 불가 → 회색 + 안내.
- V 의 피벗 스냅 대상 (로케이터 S4): Blender 정점 스냅은 빈 오브젝트 원점을 안 잡음 [측정] → 안내.
- Status Line: 홀드 시작/끝에 Maya strip 과 3D 뷰를 다시 그림 (S6, 버튼이 바로 눌림 표시).
- Snap Align Objects (S8-S11): `maya_kit.snap_points(count=1/2/3)` (오브젝트 모드 = 피벗, 편집 모드 = 각 메시의 선택 순서 정점;
  마지막 = 활성 오브젝트가 목표), `maya_kit.align_objects` (기본 X world, mid, 평균). Position Along Curve 회색.
- Snap Together Tool (S12): `maya_kit.snap_together` 모달: 첫 클릭 = 움직일 오브젝트 표면 점, 둘째 = 목표 표면 점 → 이동 + 법선 마주봄 (setOrientation).
- Make Live (S13): `Scene.maya_kit_live` (오브젝트), 켜면 FACE_PROJECT 스냅 + Status Line 칸에 이름, 빈 선택으로 실행하면 해제.
  live 표면만 잡는 것은 불가 (Blender 는 모든 표면) → 안내.

### 5. 매니퓰레이터 모양 (M1-M7)

- 경로 후보: (a) C 기즈모 그대로 + 테마/크기만 / (b) kit Python 기즈모 그룹 `MAYAKIT_GGT_xform` 을 Move/Rotate/Scale 툴의 위젯으로.
  C 기즈모 모양 (두꺼운 축, 가운데 원) 은 바꿀 수 없다 (research/blender/api_limits.md:62) → **(b) (delegated)**.
- 연결: `VIEW3D_PT_tools_active._tools['OBJECT'/'EDIT_MESH']` 의 builtin.move/rotate/scale ToolDef 를 `widget="MAYAKIT_GGT_xform"` 인
  복사본으로 바꾼다 (idname 같음 → tool_set_by_id·LAST 그대로), 켜져 있는 툴은 `WorkSpaceTool.setup` 으로 다시. unregister 에 원래대로.
  다른 모드 (포즈·커브 편집…) 와 Transform 툴은 C 기즈모 그대로.
- 핸들: 각 핸들 = kit Gizmo 하나 (`draw_custom_shape`), `target_set_operator("transform.translate"/"rotate"/"resize")` +
  constraint_axis / orient_type (슬롯에서), release_confirm. 화면 크기 고정 (`use_draw_scale`), 크기 = Maya 108 px (M4) × `gizmo_size`/75 → +/- 그대로.
  - Move: 1 px 축 선 + 원뿔, 가운데 빈 정사각 (뷰 정렬, 자유 이동), 평면 핸들 3 개 (채운 반투명, 법선 축 색).
  - Rotate: 축 링 3 개 (앞쪽 반), 바깥 뷰 링, 트랙볼 (회색 원 안쪽).
  - Scale: 축 선 + 끝 큐브, 가운데 노란 큐브 (균일), 평면 핸들.
  - 피벗 모드: Move + 작은 회전 링 (피벗 방향).
  - 활성 핸들 (`manip.HANDLES`, 기본 가운데) = 노랑 (M2).
- 위치·방향: 피벗 점 설정 (§3) 대로 Python 에서 계산 (오브젝트 원점 / 편집 메시 선택 정점), 방향 = 슬롯 (GLOBAL, LOCAL, NORMAL
  (편집 모드는 선택 법선 근사), GIMBAL≈LOCAL, VIEW, CURSOR, PARENT, 사용자).
- step 22/26/28 의 기즈모 키맵 (Smart Duplicate/Extrude, 활성 핸들) 이 이 그룹에서도 돌도록 `manip.XFORM_GROUPS` 에 추가.
- 비교: `tools/look_shots.py` 05/06 을 실제 Rotate/Scale 툴로 찍고 (지금은 Move 그대로), `tools/look_compare.py` 로 갱신.

### 6. 검증

- 헤드리스: 피벗 재작성 수학 (채널 불변·형상 불변·자식 불변·방향 → 사용자 방향), Reset/Bake/Match Pivots, 모드별 피벗 점, 홀드 snap_target
  복원, Snap Points 1/2/3, Align Objects, Make Live, 툴 위젯 교체/복원 (enable/disable 스냅샷), 메뉴 순서.
- GUI (Maya 와 같은 순서): D 누른 채 피벗 X 핸들 드래그 → Translate 0 그대로, 형상 그대로 → D 놓고 E 회전 → 새 피벗 둘레로 돎;
  D + X 드래그 → 피벗이 1 cm 선 위; X 누른 채 X 화살표 드래그 (시작 0.3 cm) → 정수 cm; V 누른 채 가운데 핸들 → 다른 큐브 정점;
  Status Line 그리드 버튼이 X 를 누른 동안 눌림; Maya 매니퓰레이터 스크린샷 (Move/Rotate/Scale/피벗 모드).
- manual_checks: 손 감각 (핸들 잡기 쉬움, 노란 활성 핸들, 화면 크기 고정, +/-).

## 한 것

- **Maya 실측** (`research/scripts/maya_pivot_snap/ps.py`, launch.ps1, 두 세트 29 단계, 합성 Qt 드래그) → `research/maya/workflows/pivot_snap.md`
  (P1-P14 피벗, S1-S13 스냅, M1-M7 매니퓰레이터, 샷 `pivot_snap/shots/`). 새로 안 것: X 스냅은 절대 그리드 선 (0.3 → 1/2/3 cm, 반 칸 없음),
  여러 오브젝트 = lead 피벗, 컴포넌트 = bbox 중심 (평균 아님), 피벗 방향은 채널을 안 바꾸고 축 모드 Custom, Bake Pivot = 방향을 Rotate 로,
  Reset Pivot = rp 0, 축 모드 기본 Move World / Rotate·Scale Object, 회전 스텝 15°, Retain Spacing 기본 켬.
- **피벗 개념** (`operators/pivot.py`): D / Insert = Affect Only Origins + Affect Only Parents, 감시자가 변환이 끝나면 Maya 식으로 다시 씀
  (location·rotation 채널 원래대로, 새 피벗 → `delta_location`, 피벗 회전 → 「Maya Pivot」 사용자 방향 + Move 슬롯, 형상·자식 제자리).
  `maya_kit.reset_pivot` / `bake_pivot` / `match_pivots`, 모드별 피벗 점 (오브젝트 ACTIVE_ELEMENT ↔ 편집 BOUNDING_BOX_CENTER, 사용자 선택은 둠).
- **스냅** (`operators/hold.py`, `operators/snap_align.py`): X/C/V/J 동안 `snap_target` CENTER (매니퓰레이터 중심), Status Line·뷰 즉시 다시
  그림, 변환 중에 키를 놓으면 변환이 끝난 뒤 복원 (변환이 끝나며 스냅 상태를 다시 써서 복원이 지워지던 것, GUI step 3 이 잡음).
  `maya_kit.step_snap` (Off/Relative/Absolute, 회전 15°), `snap_points` (Point to Point / 2 / 3 Points), `align_objects` (X mid 평균),
  `match_transform`, `snap_together` (두 클릭, 법선 마주봄), `make_live` (`Scene.maya_kit_live`, 면 스냅, Status Line 「No Live Surface」 칸).
- **매니퓰레이터** (`ui/manipulator.py`): `MAYAKIT_GGT_xform` = Move/Scale 툴의 위젯 (ToolDef 복사본 교체 + 켜진 툴 `WorkSpaceTool.setup`,
  0.5 s 타이머와 load_post 로 다시 맞춤, 끄면 원래대로). Move = 얇은 축 + 원뿔 + 빈 가운데 사각 + 평면 핸들, Scale = 끝 큐브 + 노란 가운데 큐브,
  피벗 모드 = 작은 피벗 방향 링. 활성 핸들 노랑, Maya 108 px × gizmo_size/75 (화면 크기 고정, +/- 그대로). 위치·방향은 피벗 점·툴 슬롯대로.
  기즈모 키맵 = Generic Gizmo Maybe Drag (Smart Duplicate/Extrude·활성 핸들 그대로), `TOOL_FALLBACK_KEYMAP` (빈 곳 마키 유지).
- Tool Settings 팝업에 Maya Move/Rotate/Scale Settings (Axis Orientation, Pivot, Step Snap, Retain Component Spacing, Edit Pivot/Reset/Bake).
- W/E/R 옵션 메뉴: 방향 항목이 각 툴의 슬롯 (1/2/3), Discrete Move/Rotate · Snap Scale · Relative 연결.
- 메뉴: Modify 의 Pivot 절 (Center Pivot, Bake Pivot) 을 Match Transformations 다음으로 (Maya 순서), Match Transformations / Snap Align Objects
  하위 항목, Snap Together Tool, Make Live 매핑, 안내 (Make Live, Bake Pivot).
- 템플릿 (`tools/make_startup.py` → startup.blend): 슬롯 Move GLOBAL / Rotate·Scale LOCAL, 피벗 점 ACTIVE_ELEMENT, 회전 스텝 15°.
- `tools/look_shots.py`: 05/06 이 3D View 문맥 없이 툴을 바꿔 Move 로 남던 것 → 실제 Rotate/Scale. `tools/look_compare.py` 로 비교 이미지 갱신.

### 계획과 다르게 된 것 (delegated)

- **Rotate 툴은 Blender C 기즈모 그대로**: Python `GIZMO_GT_dial_3d` 는 뒤쪽 반 자르기 (clip plane) 와 트랙볼 채우기가 C 처럼 안 됨
  (불투명 흰 원판이 바닥에 누움, 링 안 보임 — GUI 샷). C 회전 기즈모는 이미 Maya 배치 (축 링 앞쪽 반, 카메라 링, 트랙볼) 에 Maya 테마 색.
- Retain Component Spacing 끔 (모든 점이 한 점으로, S5) 은 Blender 에 없음 → Tool Settings 에 켜짐 표시만.
- Bake Pivot 은 방향만 굽는다 (kit 피벗 위치는 이미 진짜 피벗).
- 피벗 재작성은 언두 단계를 따로 만들지 않음: Ctrl+Z 한 번 = 피벗 편집 전.

## 검증

- Maya 2022 실측: `_ps_run.json` 23 단계 + `_ps_run2.json` 7 단계 (드래그 결과까지 Maya 툴 컨텍스트가 계산).
- 헤드리스 `python tests/run.py`: **478/478** (55 파일; 새 `test_step59_pivot_snap.py` 16 개: 피벗 이동 = Translate·형상·자식 불변, 피벗 회전 →
  「Maya Pivot」 방향 → Bake Pivot, Reset / Match Pivots, Freeze 뒤 피벗 유지, 모드별 피벗 점, D 홀드 Affect Only Parents, 홀드 snap_target CENTER,
  Point to Point / 2·3 Points, Align Objects, Make Live, Move/Scale 툴 위젯 교체 (Rotate/Transform·다른 모드 그대로), 모양·중심 계산,
  툴별 방향 슬롯, Modify 메뉴 순서, 선택 폴백 유지). `test_enable_disable` 이 툴 위젯 복원도 스냅샷.
- GUI `python tests/gui/run.py --ui-scale 0.8`: **399/399** (44 파일; 새 `gui_step59_manip.py` 15 개, Maya 순서: 템플릿 기본값, Maya 매니퓰레이터
  133 px (기대 135), X 화살표 드래그 + 활성 핸들, X 홀드 시작 0.3 cm → 10 cm 정수, Status Line 그리드 버튼 눌림, D 드래그 = 피벗만,
  D + X = 피벗 16 cm 정수, E 링 = 새 피벗 둘레 회전, V + 가운데 핸들 = 다른 큐브 정점). step 59 GUI 는 1.0 / 1.25 에서도 15/15.
  - 이 단계에서 고친 기존 GUI 테스트: step 3 (홀드 복원이 변환 뒤로 — 코드 수정), step 8 (W 메뉴 World = Move 슬롯 1), step 30 (Move 툴 빈 곳 마키
    — `TOOL_FALLBACK_KEYMAP` 코드 수정), step 10 헤드리스 (Pivot 절 위치).
  - `--ui-scale 1.25` 전체: 392/398 — 실패 중 step 26 은 다시 돌리면 통과 (간헐), step 37 (Shading > Wireframe), step 51 (스케일 1.56 셸프),
    step 9 (To Vertices 하위 메뉴) 는 **step 59 변경을 stash 한 상태에서도 똑같이 실패** (이 환경의 기존 문제, step 59 와 무관).
- `python tools/look_compare.py`: 15 비교 이미지 갱신 (`research/maya/screens/compare/02/05/06`: Maya 모양 Move·Scale, 05/06 이 이제 실제 Rotate/Scale 툴),
  테마 0/38 ΔE>5, 킷 Move Y 화살표 ≈ 96 px vs Maya 98 px.
- `python tools/dogfood.py`: **47/47**, 콘솔 오류 0. `python tools/release_check.py`: PASS (16).

## 남은 것

- V 의 피벗 스냅 대상 (Maya 는 로케이터 피벗에도 붙음, S4): Blender 정점 스냅은 빈 오브젝트 원점을 안 잡음.
- Make Live 는 모든 표면에 스냅 (live 표면만은 불가), live 표면의 어두운 와이어 표시 없음.
- 편집 모드 NORMAL 축 표시는 Blender 계산의 근사 (선택 법선 + 가장 긴 엣지) — 드래그는 Blender 의 진짜 축.
- D 모드 RMB 피벗 마킹 메뉴 (Pin / Snap Pivot / Reset / Exit) 미구현 (Reset·Bake 는 Tool Settings 와 메뉴), Pin Component Pivot 없음.
- Move 축 모드 Custom (임의 방향) · Live Object Axis 회색, Align Tool · Position Along Curve 회색, Shift+V = V (Maya 와 같음, 뷰 평면 스냅 버튼은 회색).
- 회전 매니퓰레이터를 Maya 모양으로 그리기 (클립되는 링을 Python 으로 직접 그리는 것) 는 다음 기회.
