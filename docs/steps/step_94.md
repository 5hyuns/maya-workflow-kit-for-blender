# Step 94 — 피벗 편집 RMB 마킹 메뉴

재점검 6차 backlog 5 (docs/PLAN.md 「재점검 6차」 우선순위 5).

## 근거

- research/maya/interaction.md:81 (RMB-hold in pivot-edit mode), :127-130 (Reset pivot = `xform -cp; manipPivot -rp -ro`,
  Pin component pivot = `manipMoveContext -pinPivot`: 사용자 컴포넌트 피벗이 선택이 바뀌어도 남음).
- 위치·항목은 research/maya/marking_menus.json `menus.buildObjectMenuItemsNow` (buildObjectMenuItemsNow.mel 의 `$editMode` 가지,
  :61-115): N Pin Component Pivot ☐ · S Reset Pivot · NW Snap Pivot Orientation ☐ · NE Snap Pivot Position ☐ · SW Reset Pivot
  Orientation · SE Reset Pivot Position · W Show Orientation Handle ☐ · E Exit, 목록 Bake Pivot Orientation ☐ (☐ = checkBox).
  같은 proc 의 다른 가지 (아무것도 없는 곳 RMB: Select All / Complete Tool) 는 이미 `RMB_EMPTY` 가 같은 이름을 씀 → 새 메뉴는
  `buildObjectMenuItemsNow_pivot` (dagMenuProc_curve 처럼 변형 이름; test_step8 의 위치 검사에 research proc 별칭 추가).
- Maya Move 툴 피벗 옵션 기본값: snapPivotPos True, snapPivotOri True, bakePivotOri False, pinPivot False
  (research/maya/workflows/pivot_snap.md P13).
- kit 피벗 편집: 오브젝트 = `tool_settings.use_transform_data_origin` (D 홀드 / Insert, `hold.set_pivot_mode`), 편집 모드 =
  `hold.COMPONENT` (3D 커서 = 피벗, 커서 툴로 놓음, step 77). D 홀드 모달은 RMB 를 PASS_THROUGH → RMB 마킹 메뉴 키맵에 감.

## 계획 (delegated)

1. `marking/menus.py`: `PIVOT_EDIT` = 위 9 항목 (research 위치 그대로). 동작:
   - Reset Pivot / Reset Pivot Position / Reset Pivot Orientation = `maya_kit.pivot_reset(position, orientation)`: 오브젝트 모드 →
     `pivot.reset_pivot` (delta_location 0 / 사용자 피벗 방향 삭제, step 59 의 Reset 과 같음), 편집 모드 → 3D 커서를 선택의 bbox 중심으로
     (위치) / 커서 회전 단위행렬 (방향), 그 자리를 "움직이지 않음" 기준으로 (D 를 놓으면 사용자 피벗 없음 = bbox 중심).
   - Pin Component Pivot / Snap Pivot Position / Snap Pivot Orientation = `maya_kit.pivot_option(option)` 체크 상자 (WindowManager
     세션 속성, Maya 기본값 끔 / 켬 / 켬). Snap Pivot Orientation = 커서 툴 orientation GEOM ↔ NONE, Snap Pivot Position = 커서 툴
     `use_depth` (클릭한 면 위로) ↔ 끔. **Pin**: 꺼져 있으면 (Maya 기본) 사용자 컴포넌트 피벗 (D 를 놓았을 때 커서가 움직여 피벗 = CURSOR)
     이 선택이 바뀌는 순간 bbox 중심으로 돌아감 — 선택 서명 (`total_vert/edge/face_sel` + 활성 요소) 을 component 타이머가 비교. 켜져 있으면
     남음 (지금까지의 kit 동작).
   - Exit = `maya_kit.pivot_exit`: 오브젝트 = 피벗 모드 끔 (+ D 홀드 상태 정리), 편집 모드 = `COMPONENT.finish`.
   - Show Orientation Handle / Bake Pivot Orientation = 회색 (Blender 커서 툴에 방향 핸들 없음; Bake 는 Modify > Bake Pivot 이 따로 있음).
2. `marking/__init__.resolve`: RMB 이고 피벗 편집 중이면 (오브젝트 `use_transform_data_origin`, 편집 모드 `COMPONENT.on`) 이 메뉴.
   `engine.TOGGLE_OPS` + `maya_kit.pivot_option`, `draw.checked` = WindowManager 값.
3. 다음 단계 고려: 95 (V 스냅) 는 피벗 편집 중 V 스냅과 같은 hold 경로 — 이번 변경은 hold 그룹을 건드리지 않음.

## 검증 계획

- 헤드리스 `tests/test_step94_pivot_menu.py`: 메뉴 위치 = research (test_step8 의 검사에 들어감), resolve (피벗 편집일 때만), 체크 상자,
  오브젝트 Reset (delta_location 0), 편집 모드 Reset (커서 = bbox 중심, 회전 단위), Pin 꺼짐 + 선택 바뀜 → bbox 중심 / Pin 켬 → CURSOR 유지,
  Exit, 옵션 → 커서 툴 설정.
- GUI `tests/gui/gui_step94_pivot_menu.py`: 사용자 피벗이 있는 큐브, D 누른 채 RMB → 메뉴 스크린샷, 남쪽 드래그 → Reset → delta_location 0.
- 전체 헤드리스·GUI, dogfood.

## 한 것

- `marking/menus.py` `PIVOT_EDIT` (`buildObjectMenuItemsNow_pivot`): research 위치 그대로 8 방사 + 목록 1, Show Orientation Handle / Bake
  Pivot Orientation 회색. `marking/__init__.resolve`: RMB + 피벗 편집 중 (`pivot_menu.pivot_editing`) → 이 메뉴. `engine.TOGGLE_OPS` +
  `maya_kit.pivot_option`, `draw.checked` = WindowManager 옵션.
- `operators/pivot_menu.py` (새): `maya_kit.pivot_option` (PIN / SNAP_POS / SNAP_ORI, WindowManager 세션 속성, Maya 기본값),
  `maya_kit.pivot_reset` (오브젝트 = `maya_kit.reset_pivot`, 편집 모드 = `COMPONENT.reset`), `maya_kit.pivot_exit`.
- `operators/hold.py`: `cursor_orientation` / `apply_cursor_options` (Snap 옵션 → 커서 툴 orientation GEOM↔NONE, `use_depth`),
  `selection_signature`, `selection_center`, `ComponentPivotEdit.reset` + `custom` / `sel_sig` (Pin 꺼짐 = 선택이 바뀌면 사용자 피벗 → bbox
  중심, component 타이머가 그동안 계속 돔).
- `tests/test_step8_marking_menus.py`: `RESEARCH_PROC` 별칭 (변형 메뉴 → Maya proc), 메뉴 수 26.

## 검증

- 헤드리스 `tests/test_step94_pivot_menu.py` 6/6: 위치·라벨 = Maya, resolve (피벗 편집일 때만, 오브젝트 위·빈 곳 둘 다), 체크 상자 기본값 (Pin
  끔, Snap 둘 켬) + 토글, 오브젝트 Reset (delta_location 1 → 0, 정점 세계 위치 그대로) + Exit, 편집 모드 Reset (커서 = 윗면 bbox 중심
  (0, 0, 1), 회전 0, 놓으면 사용자 피벗 없음), Pin 꺼짐: 같은 선택 = 유지 / 선택 바뀜 = bbox 중심, Pin 켬 = 유지, 오브젝트 모드로 나가면
  정리, Snap 옵션 → 커서 툴 GEOM/use_depth ↔ NONE/끔. test_step8 11/11 (research 위치 검사 290 → 이 메뉴 8 항목 포함).
  관련: step 77 7/7, 59 16/16, 18 8/8, 3 16/16, enable_disable 4/4, 78 8/8.
- GUI `tests/gui/gui_step94_pivot_menu.py` 4/4: 사용자 피벗 (delta 1.0) 큐브, D 누름 = 피벗 편집, RMB = 피벗 메뉴 (9 항목), 남쪽 드래그
  놓기 → delta 0, D 놓기 → 피벗 편집 끝. 스크린샷 직접 확인 (`gui_step94_pivot_menu.png`: N Pin ☐, NW / NE Snap ☑, W 회색, E Exit, SW / S /
  SE Reset, 목록 Bake 회색).
- 전체 헤드리스 `python tests/run.py`: **704/704** (85 파일). 전체 GUI `python tests/gui/run.py`: **702/702** (75 파일).
- `python tools/dogfood.py`: **47/47**, 콘솔 0.

## 남은 것

- Show Orientation Handle (Maya 피벗 방향 회전 핸들) 없음 — Blender 커서 툴에 방향 핸들이 없음. Bake Pivot Orientation 옵션 (방향을 바꾸면 바로
  굽기) 없음 (Modify > Bake Pivot 은 있음).
- Pin 꺼짐의 선택 변화 판정은 선택 개수 + 활성 요소 — 개수가 같고 활성이 같은 다른 선택은 못 알아챔 (드묾, delegated).
- 오브젝트 피벗 편집에서 Pin / Snap 옵션은 컴포넌트에만 의미 (Maya 도 같음).
- 다음: step 95 = 확대 상태 V 스냅.
