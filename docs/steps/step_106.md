# Step 106 — Tool Settings and Attribute Editor parity (step_98.md #20–#22)

## 계획 (delegated)

근거: Maya 2022 GUI 캡처 `research/scripts/maya_ts106/` → `research/maya/screens/ts106/_ts106.json` + 그림
(공장 설정, `MAYA_APP_DIR` = `tmp/maya_app_ts106`). research/ 는 추적하지 않는다.

**측정한 것 (Maya)**
- `MoveToolOptions` (공장): Tool Settings 는 **떠 있는 창** 460 x 800 (`move_tool_options.floating = True`). initMainWindow
  의 자리 (`dockToMainWindow left`, research/maya/ui_layout.md:47) 로 붙이면 메인 창 맨 왼쪽, 메뉴 막대 아래 전체 높이,
  너비 460 (`docked_left`). 사용자 요청은 「왼쪽 도크」 — 그것을 따른다.
- 창 머리: "Move Tool" + Reset Tool / Tool Help (audit7 `c02_tool_settings_move_win1.png`).
- 절 순서와 처음 펼침 (`frames_default`): Move Settings (펼침), Joint Orient Settings, Move Snap Settings, Common Selection
  Options, Soft Selection, Symmetry Settings, Smart Duplicate Settings (접힘). Rotate / Scale: Rotate|Scale Settings, Common
  Selection Options, Soft Selection, Symmetry Settings, Smart Duplicate Settings (`*_ts_full0.png`).
- Move Settings 줄 (`move.scroll_inner.widgets`): Axis Orientation (World + 3 값), Pivot: Edit Pivot | Reset, ☑ Position
  ☑ Orientation ☐ Pin Component Pivot ☐ Bake Pivot Orientation ☑ Show Orientation Handle, Transform Constraint Off (Along
  Normals / Closest Point), Step Snap Off 1.00, Preserve Children ☐, Preserve UVs ☐, Tweak Mode ☐. Rotate 는 + Rotate
  Center (Default / Object / Manip / Selection), Modify Translation, Free Rotate ☑, Step 15.00; Scale 은 + Scale Center
  (Default / Object / Manip), Prevent Negative Scale ☑.
- ToggleToolSettings 세 번: 보임 → 숨김 → 보임 → 숨김 (`toggle`).
- AE (pCube1 + polyExtrudeFacet): 탭 pCube1 | pCube1Shape | polyExtrudeFace1 | polyCube1 | initialShadingGroup |
  lambert1; 메뉴 막대 List / Selected / Focus / Attributes / Display / Show / Help (항목은 `ae.bars`); 이름 칸 오른쪽
  Focus / Presets / Show / Hide (툴팁 `ae.widgets`); 아래 Select / Load Attributes / Copy Tab; Notes: <node>.

**설계**
1. **Tool Settings 도크** (`ui/tool_dock.py`): 메인 3D 뷰를 세로로 나눠 (factor < 0.5 → 새 영역이 왼쪽, GUI 측정)
   Properties 편집기를 TOOL 탭으로 두고 머리·탐색 막대 숨김 (`show_region_header` False + `screen.region_toggle
   NAVIGATION_BAR`, 다른 탭 `show_properties_*` False). 표시 = 「TOOL 탭 + 머리 숨김」 Properties (저장 후 다시 열어도
   알아봄). 토글 = 있으면 `screen.area_close` (원래 배치로 돌아옴, 측정), 없으면 만든다. 너비 280 px × UI 배율, 메인 뷰의
   35 % 이하 (delegated: Maya 의 460 은 1600 창에서 너무 넓다; 자리는 Outliner 와 뷰포트 사이 — Blender 는 창 가장자리
   전체 높이의 새 열을 만들 수 없고, Tool Box 열 / Outliner 를 나누면 둘 다 좁아진다). `context` 는 타입을 바꾼 다음
   틱에만 설정할 수 있어 (enum 이 비어 있음, 측정) 타이머로 마무리한다. 옛 `wm.call_panel` 팝업 (두 번째 토글에도 남던
   것) 은 없앤다. option box 의 「tool」 종류는 열기만 (`editor_toggle(show=True)`).
2. **Maya 절** (`ui/tool_settings.py` 의 `MAYAKIT_PT_tool_settings`, VIEW_3D UI "Tool" 범주 → Properties TOOL 탭에만
   poll): 머리 줄 = 도구 아이콘 + "Move Tool" + Reset Tool + Tool Help (회색, 안내). Move / Rotate / Scale 에서는 Maya
   절을 `layout.panel` 로 Maya 순서·펼침 그대로, 각 줄은 kit 상태에 묶는다: Axis Orientation = 방향 슬롯, Edit Pivot /
   Reset = `pivot_toggle` / `reset_pivot` (편집 모드: 컴포넌트 피벗), Position / Orientation / Pin Component Pivot =
   step 94 WM 옵션, Rotate / Scale Center = `transform_pivot_point`, Step Snap = `snap_align`, Preserve Children =
   `use_transform_skip_children`, Preserve UVs = `use_transform_correct_face_attributes`, Common Selection = 선택
   통과 / 근접 하이라이트 (MTK 와 같은 WM 프록시), Soft Selection = MTK 의 그리기, Symmetry = `status_line
   .draw_symmetry`, Smart Duplicate = 환경설정 `smart_extrude` / `smart_duplicate`. 상태가 없는 줄 (Bake Pivot
   Orientation, Show Orientation Handle, Transform Constraint, Tweak Mode, Joint Orient, Snap to live polygon, Drag 선택
   방식, Highlight backfaces, Selection Constraint, Geometry Type, Free Rotate, Modify Translation, Prevent Negative Scale)
   은 회색 + 툴팁 안내 (`notices.PANEL_NOTICES["Tool Settings/..."]`). Move / Rotate / Scale 일 때 도크 안의 Blender
   도구 패널은 숨긴다 (`dock_tabs._hidden` 이 도크도 본다), 다른 도구 (조각 브러시 등) 는 Blender 패널이 그대로 아래에.
3. **AE**: 탭에 kit 압출 기록 (`H` = polyExtrudeFace1, CB INPUTS 와 같은 프록시 필드, 절 "Poly Extrude Face History"),
   모디파이어는 Maya 노드 이름·타입 (`MODIFIER_NODES`: SUBSURF → polySmoothFace … , 이름 = kit 이 만든 Maya 이름이면
   그대로, 아니면 `<type><n>`), lambert1 / initialShadingGroup 은 step 100 그대로. 메뉴 막대 7 개 (List: Auto Load
   Selected Attributes 체크 = 꺼지면 AE 가 그 노드에 고정, Load Selected Attributes; Selected = 선택 목록; Focus =
   최근 노드; Attributes = Add / Delete / Edit Attribute; Display > Attribute Names Nice / Long / Short; Show = Show
   Notes 등; Help = 회색 + 안내). 이름 칸 오른쪽 Focus / Presets / Show / Hide (Hide = 이 노드 타입 탭 숨김, Show = 다시
   모두), Notes (`maya_kit_notes` ID 속성, Scene 프록시 — undo), 아래 Select / Load Attributes / Copy Tab (Copy Tab =
   그 데이터에 고정한 Properties 창).
4. **설명문 → 툴팁** (#22): CB INPUTS 의 「Blender keeps no edit-mode history」 3 줄 → 노드 이름 버튼 툴팁,
   Project Window 문단 → Current Project 칸 툴팁, AE nucleus / joint 설명문 → 머리 줄 툴팁. Hypershade 는 step 105
   이후 설명문 없음 (확인).
5. 검증: 헤드리스 (절 목록·바인딩·툴팁·탭·메뉴), GUI `gui_step106_tool_settings.py` (토글 두 번 → 도크 닫힘, 세 번 →
   열림, 도구 바꾸면 절 바뀜) + 나란히 그림 c02 / c03 (`--ui-scale 0.8`).

## 한 것

- **Maya 측정** `research/scripts/maya_ts106/` (launch.ps1 · userSetup.py · ts106.py, Maya 2022 GUI, 공장 설정; 끝나면 Maya 가
  스스로 종료). 결과 `research/maya/screens/ts106/` (`_ts106.json` + Tool Settings Move / Rotate / Scale 전체 그림, AE 그림,
  AE 메뉴 그림). 공장 MoveToolOptions = 떠 있는 창, 왼쪽 도크로 붙이면 창 맨 왼쪽 전체 높이 (계획 참고).
- **Tool Settings 도크** `ui/tool_dock.py` (새): 메인 뷰를 나눠 왼쪽에 Properties (Tool 탭, 머리·탭 열 숨김). 토글 =
  `editor_toggle(TOOL_SETTINGS)` (Status Line 버튼, Windows > General Editors > Tool Settings, 핫박스), 도구 option box 는
  `show=True` (열기만). 옛 `wm.call_panel` 팝업 제거 → 두 번째 토글에 닫힌다. `status_line._properties_area` 는 도크를 빼고
  찾는다 (AE 토글이 도크를 Object 탭으로 바꾸지 않게).
- **Maya 절** `ui/tool_settings.py` `MAYAKIT_PT_tool_settings` (Properties 에서만 poll): 머리 줄 (도구 아이콘 + "Move Tool",
  Reset Tool, Tool Help 회색) + Move / Rotate / Scale 의 Maya 절 (순서·처음 펼침 = Maya). 묶인 상태: 방향 슬롯, Edit Pivot /
  Reset (오브젝트 / 컴포넌트), Position / Orientation / Pin Component Pivot (step 94), Rotate / Scale Center (2 x 2, pivot
  point), Step Snap + 회전 각도, Preserve Children / UVs, Camera-based selection / Highlight nearest (MTK 와 같은 프록시), Soft
  Selection (MTK `draw_soft`), Symmetry + Reset, Smart Duplicate 두 체크. 상태 없는 17 줄은 회색 + 툴팁 (`TS_NOTICES` →
  `notices.PANEL_NOTICES`). 도크 안에서 Move / Rotate / Scale 이면 Blender 도구 패널을 숨김 (`dock_tabs._hidden` 의 WINDOW
  영역 분기), 다른 도구는 Blender 패널이 머리 줄 아래에.
- **AE** `ui/attribute_editor.py`: 탭 `H` = kit 압출 기록 polyExtrudeFace1 (편집 모드, "Poly Extrude Face History" + CB 와
  같은 프록시 칸), 모디파이어 탭 = Maya 노드 타입 (`MODIFIER_NODES`) 과 이름 (Blender 자동 이름이면 `polyBevel1` 식, 사용자·kit
  이름은 그대로), 메뉴 막대 7 개 (List: Auto Load / Load Selected Attributes, Selected, Focus = 최근 노드, Attributes = Add /
  Delete / Edit Attribute, Display > Attribute Names Nice / Long / Short, Show = By Node Type / Show Notes, Help = 회색 + 안내;
  좁으면 두 줄로), 이름 줄 아래 Focus (노드 고정) / Presets / Show / Hide (노드 타입 탭 숨김), Notes (`maya_kit_notes` ID 속성,
  Scene 프록시라 undo), 아래 Select / Load Attributes / Copy Tab (그 물체에 고정한 Properties 창).
- **설명문 → 툴팁** (#22): `notices.tip` (`maya_kit.tip`: 툴팁 = 글, 누르면 Help Line). CB INPUTS 노드 이름, AE nucleus 머리
  줄, AE Joint Orient 줄, Soft Selection (MTK / 도크), Project Window (Current Project 칸 설명). Hypershade 는 step 105 이후
  설명문이 없음을 GUI 그림으로 확인 (`research/maya/screens/step105/h01_hypershade_pair.png`).
- 테스트: 새 `tests/test_step106_tool_settings_ae.py` (15), `tests/gui/gui_step106_tool_settings.py` (12). 바뀐 기대값:
  test_step11 (모디파이어 탭 타입 = Maya 노드 타입, FakeLayout.menu), test_step55 / test_step68 (설명문 = 툴팁),
  gui_step7 / gui_step36 (팝업 대신 도크, 두 번째 토글로 닫힘), gui_manual_sweep M65-4.

## 검증

- 헤드리스 `python tests/run.py`: **792/792** (95 파일).
- GUI `gui_step106_tool_settings`: 12/12 — 토글 1 열림 (Properties Tool 탭, 머리·탭 열 없음, 뷰포트 왼쪽, 348 px at 1.25),
  토글 2 닫힘 (영역 6 개, 뷰포트 1278 px 로 복원), 토글 3 열림, show-only 유지, Rotate / Select 도구, AE 탭 (pCube1 |
  pCubeShape1 | initialShadingGroup | lambert1; 편집 모드에서 polyExtrudeFace1 추가).
- 나란히 그림 (`--ui-scale 0.8`, 왼쪽 Maya): `research/maya/screens/step106/c02_tool_settings_pair.png`,
  `c02_rotate_pair.png`, `c02_docked_pair.png`, `c03_attribute_editor_pair.png`, `c03_history_pair.png`.
- 전체 GUI `python tests/gui/run.py`: **1059/1060** — 남은 1 개 (sweep M68-4 가 nucleus 설명문을 글로 찾음) 는 툴팁을 보도록 고친 뒤 `MAYA_KIT_SWEEP_ONLY=m68_` 다시 실행 18/18. 따라서 1060/1060.

## 남은 것

- 도크 자리: Maya 는 창 맨 왼쪽 전체 높이, kit 은 Outliner 와 뷰포트 사이 (Blender 는 창 가장자리에 새 전체 높이 열을 못 만든다).
- AE: polyCube1 같은 생성 노드 탭 없음 (Blender 는 만든 뒤 생성 값을 남기지 않음); 압출 기록 탭은 편집 모드에서만 (kit 기록이
  편집 모드에서만 유효, step 65). Presets / Show 의 필터·뷰 / Help 는 회색 + 안내. Notes 는 한 줄 칸 (Blender 는 여러 줄 입력
  칸이 없음). Attribute Names Short 는 Blender 속성 이름의 머리글자 (Maya 의 짧은 이름 표가 아님).
- Tool Settings: Transform Constraint, Tweak Mode, Joint Orient, Snap to live polygon, Drag 선택 방식 등 17 줄은 회색 (툴팁 안내).
- 다른 Maya 창의 설명문 (Light Editor `NOTICE`, option window 안내 문단, CB `POSE_HINT`) 은 이번 범위 밖 — 같은 `notices.tip` 으로
  옮길 수 있음.
