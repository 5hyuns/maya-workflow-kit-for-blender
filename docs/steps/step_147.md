# Step 147 — Undo steps and redo panel hygiene (#88 #92 #86)

## 계획

### 측정 (헤드리스 탐침 `tests/test_step147_probe.py`, 끝난 뒤 지움; Blender 4.5 소스)

- `bpy.ops.ed.undo_push` 는 `-b` 에서도 undo 스택을 만든다 (`ed_undo.cc` #60934 예외) → 헤드리스로 undo 를 잴 수 있다.
- `WM_operator_call_py` (`wm_event_system.cc:1944`): Python 의 `bpy.ops.x()` 를 **undo=False 로 부르면 `op_undo_depth++`** →
  그 안에서 끝나는 모든 연산자는 undo step 을 만들지 않고 등록 (`wm_operator_register_check`, depth == 0 필요) 도 안 된다.
  `ED_undo_push` 자체는 depth 를 보지 않는다 (`ed.undo_push` 는 어디서든 step 을 만든다).
- 그래서 `marking/modal.run_action` 이 부르는 모든 연산자 (메뉴 · 셸프 · 마킹 메뉴 · MTK · 편집기 아이콘) 는 **자기 undo step 이 없다**:
  - Create > Polygon Primitives > Cube 메뉴 → 이동 (undo step) → Ctrl+Z 한 번 = 이동과 큐브가 함께 사라짐 (측정).
  - #88: Mesh Tools > Insert Edge Loop (오브젝트 모드에서) → 편집 모드 → 첫 편집 → Ctrl+Z = OBJECT (측정). `menu_tool` 의
    `mode_set(..., True)` 는 `run_action` 이 undo 없이 부른 `menu_tool` 안이라 depth 1 → step 없음.
  - 옵션 상자 "redo" 종류 (176 경로: 실행 + Adjust Last Operation) 는 연산자가 등록되지 않아 `screen.redo_last` 가 아무것도
    못 보여준다 (측정: `wm.operators` 0 개).
- HUD (`interface_region_hud.cc last_redo_poll` → `WM_operator_ui_poll`): 마지막 **등록된** 연산자가 REGISTER+UNDO 이고 보이는
  (HIDDEN 아닌) 속성이나 `draw` 가 있을 때만 열린다. 키로 직접 부른 연산자, 창 수준 모달 도구 (끝날 때 depth 0), 확인한 props
  대화상자 (`allset.opt_*`) 가 해당 — 인벤토리: 키 / 모달 38 + 옵션 창 65.

### 결정 (delegated)

1. **Maya 명령 하나 = undo step 하나** (`src/allset/undo_steps.py`): `run_action` 의 맨 바깥 호출이 끝나고 FINISHED 면
   `ed.undo_push(message=<Maya 라벨>)`. 안쪽 호출 (menu_item → run_action 재귀) 은 깊이 카운터로 건너뜀. UNDO 연산자 안에서
   부르는 곳 (`component_command`) 은 `undo_steps.nested()` 로 감싸 두 번 쌓이지 않게. RUNNING_MODAL (도구 · 대화상자) 은
   push 없음 — 모달 / 대화상자가 끝날 때 자기 step 을 만든다.
2. **옵션 상자 "redo"** 는 연산자를 `undo=True` 로 불러 등록 + 자기 step (wrapper 는 push 안 함) → Adjust Last Operation 이
   다시 그 명령의 설정을 보여 준다 (Maya 옵션 상자의 대체, step 51 설계대로).
3. **HUD 없음** (Maya 에는 redo 패널이 없다):
   - 창 수준 모달 도구 · props 대화상자 · 파일 브라우저 연산자 → REGISTER 를 뺀다 (UNDO 는 둔다; 반복할 일 없음).
     Joint Tool, IK Handle Tool, Insert / Offset Edge Loop, Slide Edge, Target Weld, Crease, 3D Cut and Sew, Multi-Cut loop,
     Snap Together, Create Reference, Bookmark 대화상자, 모든 `allset.opt_*` 옵션 창.
   - 키로 부르고 Maya 의 G (Repeat Last) 가 반복하는 명령 → REGISTER 는 두고 속성을 HIDDEN, `draw` 없음
     (`undo_steps.no_redo_panel`): Ctrl+E / Ctrl+B 와 `*_edit`, pick walk, 키 명령, 가시성, 부모, UV cut / sew …
     값 변경은 In-View Editor / Channel Box INPUTS (Maya 방식) 로.
4. 검증: 헤드리스 = 메뉴 경로마다 undo 스택 (명령 뒤 다른 step, Ctrl+Z 한 번 = 그 다음 step 만), #88 경로, HUD 인벤토리 0;
   GUI = Ctrl+E / Ctrl+B / Joint Tool / IK Handle 뒤 HUD 영역 없음, 셸프 Create Joints 뒤 IK Handle 셸프 클릭이 됨.

순서 이유: undo wrapper 와 HUD 플래그는 서로 다른 파일이지만 테스트가 둘 다 필요하고 한 Blender 샌드박스를 쓰므로 메인에서 차례로
(레인 나눌 독립 작업 없음, PC 부하 규칙 ≤ 2 Blender).

## 한 일

- `src/allset/undo_steps.py`: `command` (맨 바깥 명령이 FINISHED 면 `ed.undo_push(<Maya 라벨>)`), `nested`, `mark_pushed`,
  `no_redo_panel` (상속 속성까지 HIDDEN 으로 다시 만든다).
- `marking/modal.run_action` = `undo_steps.command(_label, _run_action)` → 메뉴 · 셸프 · 마킹 메뉴 · MTK · 편집기 아이콘 ·
  option_generic 이 모두 한 step. 옵션 상자 "redo" 는 `op('INVOKE_DEFAULT', True, ...)` (등록 + 자기 step).
  `component_command` 는 `nested()` (자기가 UNDO step).
- REGISTER 뺌 (UNDO 유지): joint_tool, ik_handle, insert / offset_edge_loop, slide_edge, target_weld, crease_drag,
  cut_sew_stroke, multicut_loop, snap_together, create_reference, bookmark_create / frame, 모든 `allset.opt_*` (`option_windows._make`).
- `@undo_steps.no_redo_panel`: extrude (+ `extrude_edit` / `extrude_edge_edit` / `extrude_vertex_edit`), bevel (+ `bevel_edit`),
  component_command, convert_selection, delete_history, duplicate_special, insert_key, nudge_keys, select_key, set_key,
  set_tangent, loop_pick, parent / unparent, pick_walk / _component / _joint, pixel_move, script_run, smooth_proxy,
  uv_cut / uv_sew / uv_layout, visibility, assign_new_material. extrude / bevel 의 redo 패널용 `draw` 와 `_draw_fields` /
  `_draw_bevel` 삭제 (값은 In-View Editor / Channel Box INPUTS).
- 테스트: `tests/test_step147_undo.py` (6), `tests/gui/gui_step147_hud.py` (11), `gui_step144_loop.py` 의 #88 우회
  `undo_push` 삭제 + "Ctrl+Z 뒤에도 편집 모드 + 도구" 확인, `gui_step134_display.py` 양성 대조를 Shift+H → Alt+W
  (Blender Clear Location) 로.

## 검증

- 헤드리스 전체 **1319/1319** (158 파일); 관련 13 파일 327/327 (step 146 / 65 / 139 / 134 / 103 / 140 / 144 / 129 / 101 / 51 /
  57 / 58 포함).
- GUI: step147_hud + step134_display 31/31 (대조 Alt+W 가 HUD 를 보여 줌 → 탐지기 유효; Ctrl+E · Ctrl+B · 셸프 Joint Tool ·
  IK Handle Tool 뒤 HUD 0, Create Joints 뒤 셸프 IK Handle 클릭이 도구를 시작), step144_loop / 139_shape / 57_joints / 58 /
  129_multi_cut / 22_manip / 16_undo / 144_poly 110/110, step103 / 140 / 144_deform / 146 / 143 / 51 / 109 / 136 / 39 / 107 /
  65 / 29 113/113. 스크린샷 (`gui_step147_joints.png`: 셸프 위 패널 없음) 직접 확인.

## 남은 것

- 옵션 창의 Apply (창이 열린 채 실행, update 콜백) 는 아직 따로 undo step 이 아니다 — 창의 Create / 확인 때 한 step.
- HIDDEN 이 된 속성은 환경설정 키맵 편집기의 항목 속성 칸에도 안 보인다 (키 항목 값은 그대로 동작).
- 다른 kit REGISTER+UNDO 연산자 (294 중 키 · 모달 · 옵션 창으로 닿지 않는 것) 는 메뉴로만 불려 등록되지 않으므로 HUD 가 안 뜬다;
  새 키 / 모달 / 창을 추가하면 `test_no_kit_command_opens_adjust_last_operation` 이 잡는다.
- Edit > Undo History 의 step 이름은 Maya 항목 라벨 (예: "Cube", "Insert Edge Loop") — Maya 의 명령 이름 (polyCube) 과는 다르다.
