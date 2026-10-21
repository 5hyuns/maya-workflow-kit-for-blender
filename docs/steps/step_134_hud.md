# Step 134 lane HUD — no Adjust Last Operation after display / mode keys (#58), smooth Smooth Preview (#61)

Lane HUD of step 134 (`docs/steps/step_134.md`). Audit 8 findings `step_133_ui.md` #9 and #15.

## 계획

### #58 Adjust Last Operation 패널

- Blender 가 HUD (Adjust Last Operation) 를 여는 조건 (`wm_event_system.cc` `wm_operator_finished`, `WM_operator_last_redo`):
  연산자에 `REGISTER` **와** `UNDO` 가 둘 다 있고 편집 가능한 속성이 있을 때. `UNDO` 만 있으면 undo 단계는 그대로 쌓이고
  HUD 는 닫힌다 (hud_status CLEAR). `REGISTER` 만 있으면 아무 일도 없다 (이전 연산의 패널이 그대로).
- 그래서 Maya 표시 / 모드 키의 연산자에서 `REGISTER` 만 뺀다. `UNDO` 는 Maya 가 그 동작을 undo 큐에 넣는지에 따라 정한다.
- Maya 측정 (mayapy 2022, `MAYA_APP_DIR` 은 tmp/, `undoInfo -state on -infinity on` 뒤 `mel.eval` 로 명령, `undoInfo -q -undoName` 과 `undo` 뒤 값 비교):
  - `displaySmoothness -polygonObject 3` → 이름 없는 undo 항목, `undo` 해도 값 3 그대로 = 사실상 undo 안 됨.
  - `selectMode -component` / `selectType -vertex` → undo 큐에 항목 없음 (툴 설정과 같음).
  - `hilite pCube1` (F9 등 컴포넌트 모드 진입의 실체) → undo 큐 항목, `undo` 로 hilite 해제 = undo 됨.
- 결정 (delegated):
  - 컴포넌트 모드 (F7/F9/F10/F11, RMB 마킹 메뉴 Vertex/Edge/Face, Status Line 오브젝트/컴포넌트, F8, Shift+Q 마스크,
    UV 컴포넌트): `{'UNDO'}` — Maya 의 hilite 처럼 undo 로 돌아간다. Blender 편집 모드 진입도 undo 단계.
  - Smooth preview 1/2/3, PgUp/PgDn: `{'UNDO'}` 유지. Maya 는 undo 하지 않지만 Blender 의 memfile undo 는 마지막 push
    상태로 되돌리므로, push 를 빼면 **다음** 연산 (예: 이동) 을 Ctrl+Z 할 때 미리보기까지 사라진다 (Maya 와 더 어긋남).
    push 를 두면 3 직후 Ctrl+Z 가 미리보기를 끄는 한 단계만 Maya 와 다르다.
  - Alt+A (cycle_display), Alt+P (camera_mode_toggle), Alt+R (symmetry): `{'UNDO'}` (오브젝트 / 카메라 / 씬 데이터를 바꿈).
  - 4–7 (`display_mode`), Alt+B, 그리드 토글, Insert (pivot_toggle) 는 이미 `REGISTER` 만이라 HUD 를 열지 않는다 — 그대로
    (Shift+G / Repeat Last 가 계속 반복할 수 있게).
  - 부작용: `REGISTER` 를 뺀 연산자는 `screen.repeat_last` (Maya G) 와 Info 로그에 남지 않는다. Maya 의 G 도 표시 키를
    반복하지 않는다 [K].
- Q/W/E/R 은 C 연산자 `wm.tool_set_by_id` — HUD 없음 (GUI 테스트 대상 밖, step 133 조작 결과에서 확인).

### #61 Smooth preview 가 각진 면

- 원인 (측정, 헤드리스): Maya 프리미티브 (step 129 `operators/prim_history.py` `fill_bmesh`) 는 polyCube 의 hard edge 를
  `sharp_edge` 로 저장하고 면은 smooth 로 둔다 (Maya 의 hard edge = 면 법선). step 15 의 "Maya Smooth Preview Shading"
  노드 그룹은 Set Shade Smooth 를 **면** 에만 걸어 `sharp_face` 만 지웠다. Subsurf 는 `sharp_edge` 를 자식 에지에
  넘기므로 평가된 메시의 `normals_domain` 이 `CORNER` (각짐) 로 남았다. step 15 테스트는 Blender 의 primitive_cube_add
  (sharp_edge 없음) 로만 쟀기 때문에 놓쳤다.
- 고침: 그룹에 Set Shade Smooth (domain EDGE) 노드를 하나 더 — 미리보기 메시의 `sharp_edge` 도 지운다 (원본 메시 데이터는
  그대로, 1 = Subsurf · 셰이딩 모디파이어 숨김 → 원래 hard edge 각진 모습). 0.2.x 로 저장된 파일의 면 전용 그룹은 3 을
  누를 때 같은 이름으로 다시 만든다 (`_shade_group_current`).
- Maya 의 smooth mesh preview 는 hard edge 와 상관없이 매끈하게 그린다 (`research/maya/interaction.md:166-172`, 이슈 #61).

### 검증

- 헤드리스 `tests/test_step134_display.py`: 연산자 bl_options, Maya 키맵의 1–7 / F7–F11 / PgUp/PgDn / Alt+A/B/P/R 항목이
  REGISTER+UNDO 가 아닌지, Maya 큐브 3 → `sharp_edge`/`sharp_face` 없음 + `normals_domain == 'POINT'` + 면 안 corner
  법선이 다름, 1 → 다시 각짐, 2 → 매끈 + 와이어, 옛 그룹 업그레이드, undo 유지.
- GUI `tests/gui/gui_step134_display.py`: Shift+H 로 HUD 를 띄운 뒤 (검출기 확인) 3, 2, 1, 4–7, F9–F11, F8, Alt+A 를 누를 때마다
  HUD 없음; 3 / 1 스크린샷에서 큐브를 가로 · 세로로 지나는 줄의 이웃 픽셀 밝기 최대 차이 / 전체 범위.
- 감추어진 HUD 는 크기를 유지하고 창 rect 만 0 이 된다 (`hud_region_hide`) → 검출기는 `(x, y) != (0, 0)` 도 본다.

## 한 일

- `src/allset/operators/display.py`: `_shade_group` 에 EDGE domain Set Shade Smooth, 옛 그룹 재구성
  (`_shade_group_current`), `_ensure_shade_modifier` 가 옛 그룹을 바꿔 끼움. smooth_preview / smooth_level /
  component_mode / component_mask → `{'UNDO'}`.
- `REGISTER` 제거: `tool_keys.toggle_sel_mode` (F8), `ui/status_line.select_mode`, `marking.mm_component`,
  `uv_tools.uv_component`, `view_keys3.cycle_display` (Alt+A), `view_keys3.camera_mode_toggle` (Alt+P),
  `symmetry.symmetry` (Alt+R).
- `tests/gui/gui_step91_view_chrome.py`: HUD 를 띄우던 3 대신 Shift+H (Show Selected).

## 검증 결과

- 헤드리스 `ALLSET_SANDBOX=hud134 python tests/run.py -k step134,step15,step16,step18,step129,enable_disable`: 142 passed, 0 failed (16 files).
- GUI `ALLSET_SANDBOX=hud134 python tests/gui/run.py -k step134_display,step15,step18,step72,step91`:
  - 기본 배율 (1.25): 53 passed, 0 failed (step91 수정 후 재실행 8/8 포함).
  - `--ui-scale 0.8`: 52 passed, 1 failed — `gui_step91_view_chrome::list rows cross the HUD panel` 은 변경 전 코드
    (HEAD 0.2.1) 에서도 0.8 에서 같은 FAIL (6 passed, 1 failed): 기존 문제, 이 레인과 무관.
- 셰이딩 측정 (이웃 픽셀 밝기 최대 차이 / 범위, 행 / 열): 변경 전 3 = 0.242 / 0.209 (각짐), 변경 후 3 = 0.024 / 0.014
  (1.25), 0.014 / 0.014 (0.8); 1 = 0.547 / 0.582. GUI 임계 0.1.
- 변경 전 GUI: 3, 2, 1, F9, F10, F11 뒤 HUD 있음 (13 FAIL) — `before/gui_step134_after_f9.png` 에 「Component Mode」.
- 그림: `tmp/hud134_shots/before/`, `tmp/hud134_shots/after/`, `tmp/hud134_shots/after_080/`
  (`gui_step134_smooth3.png`, `gui_step134_smooth1.png`, `gui_step134_after_f9.png`).

## 남은 것

- 4–7 은 HUD 를 만들지 않지만 이전 연산의 패널을 닫지도 않는다 (REGISTER 만, UNDO 없음 — 뷰 표시는 undo 대상이 아니라
  UNDO 를 넣으면 빈 undo 단계가 생김). Python 에서 HUD 만 닫는 API 는 없다.
- Maya 3 모드에서 선택된 오브젝트는 원래 케이지 와이어만 그리는지 (Blender 는 세분된 메시 와이어 전체) — 확인 안 함.
