# Step 129 — Fix batch for 0.2.1 (#36 crash + user-report issues + P1 audit issues)

## 계획

- 순서상 먼저: `origin/hotfix/crash-36` merge (menu_extras 타이머가 Window 를 포인터로 재조회). 그다음 같은 패턴을 모든
  `bpy.app.timers.register` 46곳에 적용 (레인 T).
- 범위 (delegated): user-report 이슈 전부 (#1–#14, #22, #27, #28, #36, #37, #38) + P1 audit (#19, #20, #26, #39); 같은 원인으로 묶이는
  #15 (#1), #29 (#28), #24 (#10 계열), #17/#18 (#39 의 컴포넌트 모드 표). #23 아이콘·#25 Hypershade 는 step 130.
  나머지 P2/P3 audit 이슈 → 마일스톤 0.3.0, 이번에 고친 것 → 0.2.1.
- 병렬 레인 (worktree 격리, 파일 소유 단위로 나눔; 같은 파일을 만지는 레인끼리는 hunk 단위 병합):
  | 레인 | 이슈 | 주 파일 |
  |---|---|---|
  | T timers | #36 패턴 전수 | 46 타이머 사이트, `src/allset/live_refs.py` |
  | S softsel | #1 #2 #15 | operators/taphold.py, 새 soft select 표시 모듈 |
  | TS tool settings | #3 #28 #29 | ui/tool_settings.py, ui/toolbox.py(더블클릭), ui/tool_dock.py |
  | MC multi-cut | #27 (+ #28 Multi-Cut 옵션) | 새 operators/multi_cut.py, ui/mesh_tools.py |
  | P prims | #11 #12 | operators/create.py, INPUTS (channel_box / history) |
  | V viewport | #10 #13 #24 #8 #9 | ui/panel_toolbar.py, ui/panel_menus.py, ui/uv_toolkit.py, status_line IPR, quick layout, operators/framing.py |
  | M marking | #5 | marking/ |
  | CB channel box | #6 #7 #26 | ui/channel_box.py, ui/cb_entry.py, ui/layer_editor.py, operators/visibility.py |
  | X misc | #4 #14 #22 #37 #38 | ui/maya_dock.py tear-off, material display, loop select, auto key, time slider ticks |
  | A audit P1 | #19 #20 #39 (#17 #18) | switch.py, operators/skin.py, ui/menu_sets.py edit-mode table |
- 순차인 것: hotfix merge → 레인 시작 (모든 레인이 merge 된 HEAD 에서 출발해야 함); 레인 병합 → 헤드리스 전체 → GUI 전체 1회.

## 한 것

10개 레인을 worktree 서브에이전트로 동시에 진행하고 메인이 병합했다 (레인별 상세 = `step_129_<lane>.md`).

| 레인 | 이슈 | 결과 | 문서 |
|---|---|---|---|
| hotfix + T | #36 | hotfix merge; `src/allset/live_refs.py`, 46 타이머 전수: 17곳이 창·영역 포인터를 매 tick 재조회 | `step_129_timers.md` |
| S | #1 #2 #15 | 소프트 셀렉트 = Maya 전역 상태 1개 (기본 꺼짐, 두 Blender 플래그 동기화), B+LMB/MMB 반경 드래그 + 반경 원, 감쇠 색 오버레이 (Maya 램프 측정, Blender transform 과 1e-4 일치, 10만 버텍스 캐시) | `step_129_softsel.md` |
| TS | #3 #28 #29 | Tool Box 더블클릭 → Tool Settings; Select / Lasso / Paint Select / Insert Edge Loop / Slide Edge / Target Weld / Crease / Quad Draw 의 Maya 섹션 + 팩토리 값 (Maya GUI 측정) | `step_129_tool_settings.md` |
| MC | #27 (#28 Multi-Cut) | Multi-Cut = 킷 WorkSpaceTool (점 찍기·% 표시·Shift 스냅 10 %·Ctrl 루프·Backspace·RMB/Enter 완료·슬라이스), Maya Tool Settings | `step_129_multicut.md` |
| P | #11 #12 | 18개 프리미티브 Maya 토폴로지 (mayapy 측정 151/161 일치), 생성 노드 (polyCylinder1, makeNurbCircle1 …) INPUTS·AE, 값 수정 = 재생성. bisect: 회귀 아님 (처음부터 없었음, step 10 범위 밖) | `step_129_prims.md` |
| V | #8 #9 #10 #13 #24 | 패널 툴바 버튼 전부 Maya 대로 (토글 21, 명령 3, 회색 8), 카메라 뷰 F/A = 카메라 이동, Quick Layout persp 복귀, UV 체커 토글, IPR 끄면 원래 셰이딩 | `step_129_viewport.md` |
| M | #5 | 원인 = 목록의 하위 메뉴 줄 위를 지나면 하위 메뉴만 남던 것 (영역 경계 문제 아님); 하위 메뉴를 줄 옆에 열고 부모 유지 | (커밋 9fadd9f) |
| CB | #6 #7 #26 | CB 채널 드래그 다중 선택 + 값 한 번에 입력, Layer Editor Maya 행·V/P 박스·툴바, 가시성 = `hide_viewport` 하나 (레이어 V/P = view-layer 플래그) | `step_129_cb.md` |
| X | #4 #14 #22 #37 #38 | 떼어낸 창 내용 높이, 킷 머티리얼 뷰포트 색 동기화, 더블클릭 루프·Shift 사이 선택, Auto Key 키 아이콘, 현재 프레임 키 표시 | 커밋 메시지 |
| A | #19 #20 #39 #17 #18 | 컴포넌트 모드 메뉴 표 (Maya GUI 측정대로; 이슈 본문 일부는 Maya 와 달랐음), Paint Skin Weights 정규화, 템플릿에서 Blender 전환 | `step_129_audit_p1.md` |

- 병합 후 통합 수정 (메인): `switch.py` 에 `live_refs` import 누락 (레인 T, 전환 시 NameError) 수정; 새 Maya 프리미티브는
  편집 모드에 들어가면 아무것도 선택돼 있지 않고 면 순서가 Maya 순서라 테스트 5개의 면 선택 방식을 순서 무관하게 고침;
  떼어낸 창이 한 tick 뒤에 열리게 바뀐 것에 맞춰 `gui_step129_timers` 대기 추가; manual sweep 이 `hide_viewport` 가시성 모델을 따르게.
- 마일스톤: 0.2.1 (이번 + step 130 대상), 0.3.0 (#16 #21 #30–#35).
- 순차였던 것: hotfix merge → 레인 시작 (모두 같은 HEAD 에서), 레인 병합 → 통합 테스트 (병합 결과에서만 가능).

## 검증

- 헤드리스 전체 (모든 레인 병합 후): 999/999 (119 파일).
- GUI 전체 1회: 1092/1102 → 실패 10 = 병합 통합 문제 (위 「통합 수정」). 실패 파일만 `-k` 로 재실행:
  `gui_step60_switch`, `gui_step106_tool_settings`, `gui_step129_timers`, `gui_step129_loop`, `gui_step47_selection_wire`
  (성능 +20.6 % 는 재실행에서 통과) 225/226 → `gui_manual_sweep` 수정 후 331/331. 수정한 헤드리스 파일 31/31.
- audit128 재현: `gui_props_window_close_crash` PASS (#36), `gui_ui_torn_menu_run` 3/3 (#21 도 해결 — Display > Hide/Show 가
  `allset.visibility` 로 바뀜), `gui_scene_concepts` 가시성 4건 PASS, `gui_component_mode_menus` 는 Maya GUI 측정에 맞게 기대값 수정.

## 남은 것

- step 130: #23 아이콘, #25 Hypershade 레이아웃. 0.3.0: #16 (Ctrl+B), #30–#35 (툴·옵션 창 나머지).
- 손 확인 (`docs/manual_checks.md` 「Step 129 …」): Tool Box 실제 더블클릭, B+MMB 감도 (Maya 측정 실패 — QTest 드래그가 Maya 슬라이더에
  닿지 않음, 기존 100 px 당 ×2 유지, delegated), Multi-Cut 조작감, CB 드래그 선택, 마킹 메뉴 하위 메뉴, 떼어낸 창 깜빡임.
- 레인별 「남은 것」: Multi-Cut Edge Flow·Ctrl 드래그 루프 슬라이드, polyDisc Circle 내부점 근사, CB 이름 정렬, 레이어 색은
  Blender 컬렉션 색 태그, 첫 area_split 때 템플릿 레이아웃이 다시 맞춰지는 문제 (`tools/make_startup.py` 최소 크기, 레인 X 발견).
- 이슈 본문과 Maya 실측이 달랐던 것 (#17 #18 #39 일부): Maya 측정대로 구현 (`step_129_audit_p1.md`).
