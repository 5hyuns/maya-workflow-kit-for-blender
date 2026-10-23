# Step 143 (user) — 0.3.0 전 사용자 보고 #80 · #82 · #84

GitHub 이슈 세 개를 재현하고 원인을 찾아, 작고 안전한 것만 고쳤다. 테스트: `tests/test_step143_user.py` (헤드리스),
`tests/gui/gui_step143_user.py` (GUI, 4.5 와 5.2.2 에서 실행).

## #84 Double click select edge loop error — 고침

- 재현: 첨부 스크린샷 = Blender 5.2 에서 `operators/loop_pick.py:172`
  `bpy.ops.mesh.loop_select('INVOKE_DEFAULT', ..., ring=False)` → `TypeError: ... keyword "ring" unrecognized`.
  GUI 테스트를 수정 전 코드로 5.2.2 에서 돌리면 같은 traceback (같은 줄) 이 난다.
- 원인: 5.1 부터 `mesh.loop_select` 에 `ring` 이 없다 (링 선택은 `mesh.edgering_select` 로 분리; 5.1.2 / 5.2.2 측정 —
  속성 `delimit_edge_loop, delimit_face_loop, extend, deselect, toggle, object/edge/vert/face_index`). 4.5 는
  `ring` 이 있고 기본값 False.
- 고침: `loop_select_args(extend)` = `extend / deselect / toggle` 만 (모든 지원 버전에 있음, `ring=False` 는 4.5
  기본값이라 빼도 같다). 버전 분기가 아니라 compat 를 거칠 필요 없음.
- 검증: `test_loop_select_keywords_exist_in_this_blender` (실행 중인 Blender 의 RNA 와 대조 — 수정 전 5.2 에서 실패),
  `test_loop_pick_passes_no_ring_keyword` (4.5 용 소스 검사), GUI `#84` (5.2.2 수정 전 FAIL → 수정 후 PASS).

## #80 압출 후 평소처럼 못 옮김 / F9–F12 선택 모드 — 고침 (둘 다)

### 압출 후 이동

- 재현: 면 → Ctrl+E → 압출 매니퓰레이터 (Local Translate Z 화살표) + In-View Editor. 이때 킷 Move 매니퓰레이터는
  숨는다 (step 65: "보이는 동안 킷 Move/Scale 매니퓰레이터 숨김"). Move 툴이 이미 켜져 있으니 W 를 눌러도 아무것도
  바뀌지 않아 새 면을 Move 매니퓰레이터로 옮길 길이 없다. GUI: 수정 전 `W after Ctrl+E` FAIL (extrude True, move False).
- 원인: 압출 매니퓰레이터의 표시 조건이 "기록 유효 + 뚜껑 면 선택" 뿐이라 툴 키로 끌 수 없었다. Maya 는 압출 뒤
  W/E/R 을 누르면 그 툴의 매니퓰레이터로 바뀌고 polyExtrudeFace 노드는 INPUTS 에 남는다 [K]. Maya 압출 매니퓰레이터의
  로컬 이동·회전·스케일 핸들은 킷에 없다 (step 65 「남은 것」).
- 고침: `extrude.Record.dismissed` + `extrude.dismiss(context)`; Q/W/E/R 툴 키 (`marking.ToolOptionsBinding._set_tool`,
  탭과 hold+LMB 둘 다) 가 압출 기록을 dismissed 로 표시 → `in_view.record` 가 None → In-View Editor·화살표 숨김, Move
  매니퓰레이터 복귀. 기록은 남아 Channel Box INPUTS / `extrude_edit` 로 계속 편집 가능, 새 Ctrl+E 는 새 기록이라 다시
  표시. (delegated: 다시 켜는 키 없음 — Maya 의 T Show Manipulator 에 해당하는 킷 키는 IC transform 툴.)
- 검증: 헤드리스 `test_tool_keys_swap_the_extrude_manipulator_for_the_tool` (Q/W/E/R), `test_dismissed_extrusion_stays_editable`,
  `test_new_extrusion_shows_its_manipulator_again`; GUI Ctrl+E → W → Move 매니퓰레이터 poll True, 가운데 핸들 드래그로
  뚜껑 면 0.57 이동.

### F9–F12

- 재현: 뷰포트에서 F9/F10/F11 (오브젝트·편집 모드) 자체는 4.5 / 5.2 모두 정상 (GUI PASS). 문제는 F12 (Maya UV 모드):
  UV Editor 가 아직 없을 때 첫 F12 는 UV Sync Selection 이 켜진 채로 끝나고 (GUI: `sync True, windows 1 -> 2`), 메시의
  모든 면이 선택된다. 그 뒤 F9 를 누르면 정점 12 개 전부가 선택돼 있다 (F12 전 선택 = 엣지 1 개).
- 원인 1: `uv_component.execute` 가 `set_component('UV')` (sync 끔) **다음에** `allset.open_editor(ui_type='UV')` 를 불렀고,
  그 안의 `uv_tools.prepare()` 가 sync 를 다시 켰다 → 첫 F12 는 UV 모드가 아님.
- 원인 2: F9/F10/F11 (`allset.component_mode`) 은 `mesh_select_mode` 만 바꿔 sync 를 되돌리지 않았고, F12 가 UV 를 다
  보이려고 모든 면을 선택한 것이 그대로 메시 선택으로 남았다. Maya 는 컴포넌트 종류별 선택을 따로 기억해 F12 → F9 에서
  F12 전의 정점 선택이 보인다 [K].
- 고침: 에디터를 먼저 열고 `set_component` 를 나중에; F12/Alt+F12 가 메시 모드에서 들어올 때 메시 선택을 기억
  (`uv_tools.remember_mesh_selection`), F9/F10/F11 과 UV Editor 의 Vertex/Edge/Face (`set_component`) 는
  `leave_uv_mode` = sync 켬 + (요소 수가 같으면) 기억한 선택 복원. Select > Convert 의 UV 변환은 기억을 지운다
  (`forget_mesh_selection`). BMesh 함정: 면/엣지의 `select = False` 는 그 정점까지 끈다 — 전부 끈 뒤 정점·엣지·면 순으로 켠다.
- 검증: 헤드리스 `test_f12_then_f9_is_vertex_mode_with_the_old_selection` (F9/F10 = 엣지 1 개 복원, F11 = 면 0 — F12 없이
  F11 한 것과 같음), `test_f12_twice_keeps_the_first_selection`, `test_component_mode_without_uv_mode_keeps_the_selection`;
  GUI F12 → `sync False, windows 1 -> 2`, F9 → `sync True, verts 2 of 12`.
- 남은 것: 사용자의 "F9–F12 가 제대로 안 된다" 가 이것인지 확인 못 함 (단계 설명 없음). 마우스가 Outliner / Channel Box
  위에 있을 때는 F9–F11 이 3D View 키맵 ("Object Non-modal") 에만 있어 안 먹는다 (Maya 는 전역) — 이번에 바꾸지 않음.

## #82 메뉴 옵션 박스가 안 열림 — 고치지 않음 (0.4.0 제안)

- 재현 (GUI, Display > Grid): 줄 오른쪽 끝 ❒ 를 클릭하면 **명령** (Toggle Grid) 이 실행된다 (`[('item', 'Display/Grid')]`).
  누른 채 유지하면 Blender 가 줄 **아래**에 "Option Box" 한 줄짜리 메뉴를 열고, 버튼을 누른 채 그 줄로 내려가 놓아야
  옵션 박스가 열린다 (`[('box', 'Display/Grid')]`, 샷 `143_hold_menu.png`). 누른 자리에서 놓으면 아무것도 안 된다.
  툴팁 (`ALLSET_OT_menu_item.description`) 에는 hold 안내가 없다 (클래스 docstring 에만 있음). Toggle Show/Hide, Set Key,
  Constrain > Parent 도 같은 `_draw_boxed` 경로.
- 원인: step 103 결정 — 메뉴 줄에 버튼을 둘 두면 Blender 메뉴가 계단 모양으로 깨져서 항목 하나 (`operator_menu_hold`) 에
  ❒ 를 라벨 끝 글자로 붙였다. 클릭 위치로 나눌 수 없다: 메뉴 항목 연산자는 메뉴를 연 영역의 context 로 실행되고 (측정:
  `context.region` = 3D View WINDOW, 팝업 영역 아님) Python 에서 팝업 메뉴 영역의 위치·폭을 알 수 없다.
- 제안 (0.4.0):
  1. hold 를 한 단계로: `ALLSET_MT_option_box` 대신 hold 함수가 바로 옵션 창을 열게 (누르고 ~0.3 초 = 옵션 박스,
     놓을 필요 없음) — 팝업이 버튼을 누른 상태에서 뜨는 것의 안전성 측정 필요.
  2. 수정 키 클릭: `menu_item.invoke` 에서 Shift (또는 Ctrl) + 클릭 = 옵션 박스 (시뮬레이션 Shift 가 UI 버튼 연산자의
     `event.shift` 에 안 닿으므로 수동 확인).
  3. 0.3.0 에 바로 할 수 있는 최소안: 옵션 박스가 있는 항목의 툴팁에 "Option box ❒: press and hold, then pick Option Box"
     한 줄 추가 + README/매뉴얼에 안내.
- 테스트: GUI `#82` 세 줄은 현재 동작을 기록 (❒ 클릭 = 명령, hold → Option Box 줄 = 옵션 박스).
