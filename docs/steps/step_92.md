# Step 92 — Graph Editor 키 묶음 (t, Alt+/, i Insert Key 툴)

재점검 6차 backlog 3 (docs/PLAN.md 「재점검 6차」 blindspot 4; step_83.md 「남은 것」; docs/keymap_mapping.md :79, :201, :471).

## 근거

동작 명세: `research/maya/re/graph_editor_keys.md` — 팩토리 Maya 2022 GUI 관찰 (스크립트 `research/scripts/maya_graph/graph.py`,
QTest 마우스 이벤트를 Graph Editor 캔버스에 보냄; 로그 `research/maya/screens/graph/_log_run1.txt`, `_log.txt`; 그림 `graph_*_ge.png`).
REA 는 필요 없었음 (모든 규칙을 관찰로 확정).

- **t** = `animCurveEditor -lookAt currentTime`: 현재 시간이 곡선 영역 가운데로 오게 가로로만 팬, 시간 확대·값 범위 그대로.
- **Alt+/** = optionVar `snapTimeToSelection` **토글** (한 번 맞추기가 아님; Graph Editor View 메뉴의 체크 항목 "Snap Time To
  Selection"). 켜져 있으면 Graph Editor 에서 키 선택이 바뀔 때마다 (클릭 / 마키 / Shift 추가 / Ctrl 빼기) 현재 시간 = **선택된 키 중 가장
  이른 시간**; 선택이 비면 시간 그대로. 스크립트 `selectKey` 로는 안 움직임.
- **i 홀드** = Insert Key 툴 (`insertKeySuperContext`, 놓으면 이전 툴): MMB 클릭 = 선택된 곡선마다 마우스 아래 **정수 프레임**에 곡선 값
  그대로 키 (모양 유지), MMB 드래그 = **놓은** 곳 프레임, 새 키만 선택, 현재 시간 그대로, 선택된 곡선이 없으면 아무것도 안 함.
- Maya 키컨피그 현재 (측정): Graph Editor 계열 키맵에 T / Alt+/ / I 없음 (MMB = View2D scroller_activate PRESS, Graph Editor
  transform.translate CLICK_DRAG). 전역 I = Mesh inset (IC) — research/maya/workflows/animation.md:142 대로 그대로 둠.

## 계획 (delegated)

1. `operators/graph_keys.py`:
   - `maya_kit.graph_center_time`: `view2d.view_to_region(frame)` 으로 현재 프레임의 화면 x → 영역 가운데와의 차이만큼 `view2d.pan(deltax)`
     (가로만; Blender `graph.view_frame` 은 환경설정 view_frame_type 에 따라 확대도 바꿀 수 있어 안 씀). 순수 함수 `center_delta`.
   - Snap Time To Selection: 애드온 환경설정 `snap_time_to_selection` (Maya optionVar 처럼 사용자 설정, CORE `preferences.py`) +
     `maya_kit.snap_time_toggle` (Alt+/) + Graph Editor View 메뉴 체크 항목 (`GRAPH_MT_view` append, unregister 때 remove).
     감시 = 0.15 s 타이머 (켜져 있고 Graph Editor 가 열려 있을 때만 계산): 장면 오브젝트 액션의 선택된 키 서명 (numpy foreach_get) 이
     바뀌고 비어 있지 않으면 `frame_set(가장 이른 선택 키)`. 파일 로드 때 기준 초기화 (load_post), kit 자신의 선택 변경 (Insert Key 툴) 뒤에는
     기준을 갱신해 시간을 안 옮김 (Maya 삽입 = 시간 그대로). 선택 변경이 어느 에디터에서 왔는지는 Python 이 모름 → Graph Editor 가 열려 있을 때
     생긴 모든 키 선택 변경에 반응 (delegated).
   - `maya_kit.insert_key_tool` (I PRESS → 모달, step 87 pan_zoom_hold 와 같은 홀드 구조): MMB PRESS = 시작, MOUSEMOVE = 세로선 위치
     (Graph Editor WINDOW POST_PIXEL 에 점선), MMB RELEASE = 놓은 곳의 정수 프레임에 대상 곡선마다 `key_insert.insert_keep_shape` (step 83),
     새 키만 선택, `ed.undo_push` (클릭마다 되돌릴 수 있게). 대상 곡선 = 편집 가능한 보이는 곡선 중 선택된 키가 있거나 채널이 선택된 것. I 를
     놓으면 끝 (keystate + TIMER 대비). MMB 밖의 이벤트는 PASS_THROUGH (LMB 선택 그대로).
2. 키맵 (`maya_patches.py` 44): "Graph Editor" T / Alt+SLASH / I. shadows 없음 (측정상 겹치는 항목 없음; I 는 Graph Editor 키맵이라 Mesh
   inset 과 다른 에디터).
3. `mapping.py`: `graphEditor:GraphEditorFrameCenterView`, `graphEditor:SnapTimeToSelection` KIT, `InsertKeyToolActivate` KIT (전역 행이지만
   check = Graph Editor 키맵), 대응표 다시 만듦.
4. 다음 단계 고려: 93 (Shift+Q 체크 표시) 는 마킹 메뉴 체크 — 이번 메뉴 체크 항목은 Blender 메뉴라 별개. 94 (피벗 RMB) 무관.

## 검증 계획

- 헤드리스 `tests/test_step92_graph_keys.py`: `center_delta`, 가장 이른 선택 키 규칙 (`snap_target`), 서명 변화 → frame_set / 빈 선택 →
  그대로 / 끔 → 그대로, 삽입 프레임 반올림 (`insert_frame`), 대상 곡선 규칙, 삽입 뒤 값 그대로 (곡선 평가 전후 같음) + 새 키만 선택, 키맵 항목,
  매핑, 환경설정 토글.
- GUI `tests/gui/gui_step92_graph_keys.py`: Graph Editor 영역에서 t (현재 프레임이 가운데), Alt+/ 켬 → 키 클릭 → 시간 = 그 키, I 누른 채 MMB
  클릭 → 키 추가·모양 유지, 스크린샷.
- 전체 헤드리스·GUI, dogfood, gen_keymap_mapping.

## 한 것

- Maya 2022 관찰 세 번 (스크립트 `research/scripts/maya_graph/`, QTest 로 Graph Editor 캔버스에 마키 / Shift / Ctrl / MMB) → 명세
  `research/maya/re/graph_editor_keys.md` (research 는 git 밖). 첫 시도의 `cmds.selectKey` 는 Snap 을 일으키지 않아 (에디터의 선택 툴에만
  반응) 화면 이벤트로 다시 잼.
- `operators/graph_keys.py`: `maya_kit.graph_center_time` (`center_delta` 만큼 `view2d.pan`), Snap Time To Selection (애드온 환경설정
  `snap_time_to_selection`, `maya_kit.snap_time_toggle`, Graph Editor View 메뉴 체크, 0.15 s 타이머 `snap_step` / `snap_target`, load_post 에서
  기준 초기화, `remember_selection`), `maya_kit.insert_key_tool` (I 홀드 모달, MMB 동안 점선, 놓으면 정수 프레임에 `key_insert.insert_keep_shape`
  + 새 키만 선택 + undo 단계).
- `preferences.py` `snap_time_to_selection`; `keymap/maya_patches.py` 44 `patch_graph_keys_2`; `keymap/mapping.py` 3 행 KIT → 대응표 구현
  152 → 155, 미검토 222 → 219.

## 검증

- 헤드리스 `tests/test_step92_graph_keys.py` 7/7: `center_delta`, 가장 이른 선택 키 (Maya 관찰 4 경우), 서명 변화 → 시간 / 같음·빈 선택·끔 →
  그대로 / kit 선택 뒤 기준 갱신, 정수 프레임, 대상 곡선 (선택 없음·잠금 = 없음), 삽입 값 = 삽입 전 곡선 값, 4–9 프레임 곡선 그대로, 새 키만
  선택, 토글 연산자 + View 메뉴 + 타이머, 키맵 3 항목. 관련: keymap_maya 12/12, enable_disable 4/4, step 70 8/8, step 83 10/10.
- GUI `tests/gui/gui_step92_graph_keys.py` 8/8: t → 프레임 15 가 x 432 → 334 (가운데 333), Alt+/ 켬, 키 20 클릭 → 선택 + 시간 20,
  I 누른 채 MMB 클릭 → 프레임 7 키 0.03704 (= 곡선 값; Maya 3.7037 의 cm 판), 새 키만 선택, 시간 20 그대로, I 놓으면 모달 끝. 첫 실행 실패는
  테스트 탓 (MMB 를 곡선 위 0.02 에 눌러 시간 눈금 영역에 떨어짐). 스크린샷 직접 확인: `gui_step92_insert_line.png` (프레임 7 점선),
  `gui_step92_inserted.png` (키 7 = 3.7 cm, 곡선 모양 그대로, Help Line "Snap Time To Selection: on").
- 전체 헤드리스 `python tests/run.py`: **692/692** (83 파일). 전체 GUI `python tests/gui/run.py`: **693/693** (73 파일).
- `python tools/dogfood.py`: **47/47**, 콘솔 0. `python tools/gen_keymap_mapping.py`: 구현 155 · IC 15 · 해당 없음 11 · 미검토 219 · macOS 68.

## 남은 것

- Snap 은 어느 에디터에서 키 선택이 바뀌었는지 모름 — Graph Editor 가 열려 있으면 Dope Sheet 의 키 선택도 시간을 옮긴다 (Maya 의 Dope Sheet 동작은
  관찰 안 함, delegated).
- Insert Key 툴의 Maya preserveTangent / breakdown 옵션은 없음 (kit 는 늘 모양 유지). MMB 드래그 중 Maya 의 점선 모양 (색·간격) 은 관찰
  못함 — [I].
- 대응표 Graph Editor 미검토: l (value lines), h / j (채널 잠금), Graph Editor 메뉴 단축키 몇 개는 그대로.
- 다음: step 93 = 선택 마스크 다듬기 (Shift+Q 체크 표시, 새 장면에서 마스크 초기화, Reset Tool).
