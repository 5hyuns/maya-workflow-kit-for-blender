# Step 138 레인 CARRY — Open 때 Maya 레이아웃 (#63), 전역 도구 설정 (#64)

## 한 것

- 새 `src/allset/ui/scene_carry.py` (`ui/__init__` 마지막에 등록, unregister = load_pre / load_post 핸들러 · 타이머 제거).
- **도구 설정 전역 (#64)**: Maya 는 도구 설정을 optionVar 에 둔다 (`rememberCtxSettings`, research/maya/interaction.md:31;
  대칭 · soft select 전역, :159). load_pre 에서 현재 장면 값을 읽고 load_post 에서 읽은 파일의 **모든 장면**에 쓴다.
  모든 로드에 적용: File > Open, Open Recent, Revert, New Scene (킷 startup.blend), Blender File > New (delegated:
  Maya 의 Revert 도 도구 설정은 유지).
  - 옮기는 것: 방향 슬롯 0–3 type (+ `use`) = Move / Rotate / Scale 축; ToolSettings `use_snap`, `snap_elements`,
    `use_snap_translate/rotate/scale`, `use_snap_grid_absolute`, `snap_angle_increment_3d` (step snap · 스냅 토글),
    `transform_pivot_point`, `use_transform_skip_children` / `use_transform_correct_face_attributes` (Preserve Children /
    UVs), `proportional_edit_falloff`, `use_proportional_connected` / `_projected`; soft select 반경은 **Maya 단위**로
    (cm 장면 ↔ m 파일에서 4 단위 = 4 단위); `Scene.allset_symmetry`, `allset_mesh_tools`, `allset_uv` 그룹 전체;
    `Scene.allset_auto_key`; WM 피벗 옵션 (Pin / Snap Position / Orientation).
  - 이미 전역이라 안 옮기는 것: soft select 켜짐 (`soft_select.STATE`), Smart Duplicate / Extrude (add-on 설정),
    MTK camera-based / nearest (add-on 설정), 선택 마스크 (step 93 `status_line`).
  - 안 옮기는 것 (delegated): 사용자 방향 "Maya Pivot" (장면 데이터 = 한 물체의 피벗 축) — 그 슬롯은 파일 값 그대로.
    피벗 편집 모드 (`use_transform_data_origin`, 일시 모드).
  - delegated: Maya 모드가 켜진 직후 Blender 시작 장면 (Maya 레이아웃 아님, 아직 로드 없음) 은 Maya 설정이 아니므로
    옮기지 않는다 (`carries_from_current`) — 첫 New Scene 이 템플릿의 Maya 기본값 (Move World, Rotate/Scale Object,
    Active Element) 을 유지. 그 뒤 로드부터는 항상 옮긴다.
- **Open 때 Maya 레이아웃 (#63)**: add-on 설정 `maya_layout_on_open` 「Keep Maya Layout When Opening Files」 (기본 켬,
  Maya 모드 상자의 Start in Maya Layout 아래). Maya 모드 + 설정 켬 + 경로 있는 파일 + 창이 Maya 워크스페이스가 아님 →
  load_post 가 타이머 (0 s, 창 없으면 0.1 s 로 20 번까지) 를 걸고, 타이머에서 첫 창에 `show_maya_layout`:
  파일 안 Maya 워크스페이스가 있으면 그것 (자기 템플릿 것 먼저, 다음 switch 가 붙인 것), 없으면 `switch.enter_layout`.
  - `switch.enter_layout` 은 PREV_KEY 없는 워크스페이스만 찾아서, switch 가 붙인 Maya 워크스페이스를 뒤에 두고 저장한 파일에
    두 번째 사본을 붙인다 → `scene_carry.maya_workspace()` 로 먼저 찾음 (switch.py 는 수정 금지 레인이라 여기 둠).
  - 새 워크스페이스의 3D 뷰에 step 93 마스크를 다시 적용 (load_post 의 마스크 적용은 붙이기 전 뷰에만 감).
  - 경로 없는 로드 (킷 New Scene, Blender File > New, 시작 파일) 는 건드리지 않음 — first_start 의 일. Blender 모드면 안 함.
  - 첫 창만 (delegated: Maya 메인 창만 레이아웃을 가짐). 파일의 다른 워크스페이스는 남김.
  - 측정: Open + 레이아웃 붙인 뒤 `bpy.data.is_dirty` = False. 붙인 화면은 처음 보는 screen 이라 `toolbox.fit_columns` 무장됨.

## 검증

- 헤드리스 `tests/test_step138_carry.py` 12/12 (Open · 두 장면 · New Scene · Revert 유지, 반경 Maya 단위, 사용자 방향,
  규칙 함수, 기본값, 백그라운드 타이머 없음, 첫 Maya 장면 = 템플릿 기본값).
- `python tests/run.py -k step138,step93,step115,step60,step129_switch,step132,enable_disable,step130,step36,step59,step129_soft,step129_tool,step106,step10_`
  → 157 passed, 0 failed, 17 files.
- GUI `gui_step138_open.py` 11/11: 팩토리 레이아웃 파일 Open → Maya-style (strip / shelf / Tool Box / dock 모두), Move 축 ·
  step snap · 대칭 유지; Maya 워크스페이스를 뒤에 두고 저장한 파일 → 그 워크스페이스 (사본 1 개); 설정 끔 → 파일의 Layout;
  Blender 모드 → Layout. 샷 `gui_step138_open_maya.png` (열린 파일의 Cube 가 Maya 레이아웃 · Channel Box 에),
  `gui_step138_open_option_off.png` (Blender Layout + Properties) 확인.
- GUI `-k step93,step115,step132,step60_switch,step129_switch` 24/24 (4 files), `-k step69_scene,step99_first` 18/18.

## 남은 것

- 세션 사이 유지는 없음 (Maya 는 prefs 에 저장): Blender 를 다시 열면 첫 New Scene 은 템플릿 기본값.
- m 파일을 Maya 레이아웃으로 열면 뷰 거리는 `_fit_views` 비율 그대로 (샷에서 큐브가 작게 보임) — 프레이밍은 F.
- 두 번째 이후 창은 파일 레이아웃 그대로.
