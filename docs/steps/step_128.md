# Step 128 — Bug audit for 0.2.1 (점검만, 수정 없음)

## 계획

- 범위: 사용자 보고 #1–#4 근본 원인 추적(코멘트), Maya 모드 dogfood, 사용자 유형 기준 전수 검사(토글 왕복, Create, 메뉴 경계,
  Channel Box / Layer Editor, 카메라·패널, Tool Box, 홀드 키), 추가 지시(10-21): 모든 툴의 조작 방식 + Tool Settings / 옵션 박스 전수 표.
- 방식(사용자 지시 변경 10-21, delegated): 앞선 서브에이전트 4개가 중단된 뒤로는 메인이 직접 GUI 시뮬레이션으로 점검하고 문제마다 즉시
  `gh issue create` (중복은 `gh issue list` 로 확인). 사용자가 같은 시간에 #5–#14, #22, #23, #25, #27, #28 을 올렸으므로 그와 겹치는
  것(패널 툴바 토글 = #10, 프리미티브 INPUTS/토폴로지 = #11/#12, 마킹 메뉴 경계 = #5, Quick Layout = #8, 카메라 F = #9, Multi-Cut = #27,
  툴 옵션 전반 = #28)은 새로 만들지 않고 툴 계열별로 구체화(#29–#35, #28 링크).

## 한 것

- 이슈 #1–#4 에 근본 원인 코멘트 (파일:줄 + 수정 방향):
  - #1 B+MMB: `operators/taphold.py:117` 이 LEFTMOUSE 만 드래그로 받음 → MMB 는 뷰 회전으로 빠짐. 「기본 켜짐」은 깨끗한 설정에서
    재현 안 됨(측정) — 소프트 셀렉트가 오브젝트/컴포넌트 두 플래그(#15) + 장면 저장값이라 생기는 것으로 판단.
  - #2 미구현 (Blender 에 감쇠 색 표시 없음) → POST_VIEW 점 그리기 + preselect BVH 캐시 패턴 제안.
  - #3 Tool Box 아이콘 = C 툴바 버튼, 더블클릭이 키맵에 오지 않음 → 같은 툴 재설정 시간 감지(tool_keys 타이머) 제안.
  - #4 `area_dupli` 는 복사한 영역 크기의 창을 만듦; `maya_dock.tear_menu` 가 가장 높은 영역을 복사 → 원하는 높이로 split 후 복사 제안.
- 새 이슈 18개 (#15–#21, #24, #26, #29–#36, #39), 라벨 bug + found-by-audit (+ maya-parity).
- 툴 전수 표: `docs/steps/step_128_tools.md` (Maya 옵션 박스가 있는 메뉴 항목 386개: Maya 필드 옵션 창 27, 툴 14, Blender redo 124,
  「설정 없음」 50, 연산자 창 11, 미매핑 160). Tool Box: Maya Tool Settings 섹션은 Move/Rotate/Scale 만 (#29).

## 이슈 목록

| # | 제목 | 심각도 | 출처 |
|---|---|---|---|
| #1 | Soft Select (B): middle-mouse drag does not change the falloff radius; soft select seems on by default | — | user |
| #2 | Soft Select: vertices inside the falloff are not coloured by influence | — | user |
| #3 | Tool Box: double-clicking a tool icon does not open its Tool Settings | — | user |
| #4 | Torn-off panels (::::: handle): floating window size feels wrong, always tall regardless of content | — | user |
| #5 | Marking menu closes by itself while dragging down, and whenever the cursor moves over the Time Slider / key area below the viewport | — | user |
| #6 | Channel Box: drag over value fields to select several channels; one typed value goes into all of them | — | user |
| #7 | Layer Editor UX and icon sizes differ a lot from Maya (rows, V/P boxes, toolbar icons, tabs) | — | user |
| #8 | Quick Layout: Single Perspective View shows the Top view, and the perspective camera is hard to get back from Four View | — | user |
| #9 | Looking through a created camera (Panels > Perspective > camera1), pressing F jumps back to the persp view instead of framing with that camera | — | user |
| #10 | Viewport panel toolbar: several buttons can't be toggled off again, and some do nothing | — | user |
| #11 | Primitives show no INPUTS in the Channel Box: polygon (sphere, cube, cylinder...) and NURBS (circle, square...) creation attributes are missing | — | user |
| #12 | Poly Cylinder (and other primitives) do not use Maya's topology: caps should be triangle fans around a centre vertex, with Subdivisions Caps | — | user |
| #13 | UV Editor: checker toggle can be turned on but not off again | — | user |
| #14 | Material colour changes don't show in the viewport (shaded mode ignores the material colour) | — | user |
| #15 | Soft Select state is not shared between object and component mode (B in object mode, F11 -> off) | P2 | audit |
| #16 | Ctrl+B Bevel starts a mouse-following modal; Esc leaves no bevel (Maya bevels at once) | P2 | audit |
| #17 | Ctrl+D in component mode duplicates faces inside the mesh instead of duplicating the object | P2 | audit |
| #18 | Delete History (Alt+Shift+D, Edit > Delete by Type > History) does nothing in component mode | P2 | audit |
| #19 | Switching Maya -> Blender in the Maya Workflow Kit layout leaves empty Maya strips / dock, and File > New still opens the Maya template | P1 | audit |
| #20 | Paint Skin Weights does not normalize: painted / flooded weights sum to 2 (Maya default = Interactive normalization) | P1 | audit |
| #21 | Torn-off Display menu: Hide / Show do nothing in the floating window | P3 | audit |
| #22 | Component selection: no Maya double-click loop select or 'pick two, select the run between' (edge / vertex / face) | — | user |
| #23 | Icons are too different from Maya's: shelves, Status Line, Tool Box and menus are hard to tell apart | — | user |
| #24 | Status Line IPR toggle: turning IPR off always returns Solid shading (Wireframe / other modes lost) | P3 | audit |
| #25 | Hypershade window layout is completely different from Maya's (Browser, Create, Material Viewer, Graph work area, Property Editor) | — | user |
| #26 | Visibility is split across three Blender flags: h, Channel Box Visibility and Display Layer V overwrite or ignore each other | P1 | audit |
| #27 | Multi-Cut does not work like Maya's (click/drag points, Shift snap %, Ctrl edge-loop cut, Backspace, RMB to finish) | — | user |
| #28 | Tools have no options: Tool Settings are missing for Multi-Cut and most other tools | — | user |
| #29 | Select / Lasso / Paint Selection tools: Tool Settings have no Maya sections (selection options, soft selection, symmetry) | P2 | audit |
| #30 | Quad Draw, Create Polygon and Append to Polygon all open Blender's Poly Build: no Maya interaction or options | P2 | audit |
| #31 | Insert Edge Loop / Slide Edge / Offset Edge Loop are Blender's tools: different clicks and no Maya options | P2 | audit |
| #32 | Rigging tools have no Maya options: Joint Tool, IK Handle, IK Spline, Paint Skin Weights, Unbind / Copy Skin Weights open a 'no settings' window | P2 | audit |
| #33 | Modeling commands: option boxes show Blender's redo fields or 'no settings' instead of Maya option windows (only 28 Maya windows exist) | P3 | audit |
| #34 | Deform menu: Lattice / Wrap / Delta Mush / Nonlinear etc. are bare Blender modifiers without Maya creation options; Paint Weights items don't pick the deformer's weights | P2 | audit |
| #35 | Key menu and constraints: Cut/Copy/Paste/Delete/Snap Keys and Aim/Scale/Pole Vector constraints have no Maya options; Scale Keys missing | P3 | audit |
| #36 | Crash: closing an editor window opened from a Maya menu (Wireframe Color, Shape Editor, UV Set Editor...) within 2 s crashes Blender | P0 | audit |
| #37 | No Auto Key button: keyed channels are not keyed automatically when changed on another frame | — | user |
| #38 | Time Slider shows no key markers (ticks/diamonds) at keyed frames | — | user |
| #39 | Component mode: Select All / Inverse / Deselect All, Edit > Delete, Group, Freeze and most Edit menu items say 'select objects first' and do nothing | P1 | audit |

## 검증 / 재현 스크립트

- GUI 재현 (`tests/gui/run.py --dir tests/gui/audit128 -k <이름>`, `--dir` 는 이번에 추가):
  `gui_model_session` (#15 #16 #17), `gui_model_session2` (#18), `gui_switch_template_blender` (#19), `gui_rig_paint_normalize` (#20),
  `gui_ui_torn_menu_run` (#21), `gui_toggle_roundtrip` (#24; Status Line 스냅 4·마스크 6·대칭·에디터 토글 4·그룹 9 왕복 PASS, 패널 툴바
  실패 5 = #10), `gui_scene_concepts` (#26; Create 이름 10/11 PASS — joint 는 skeleton1 = step 57 의도, CB 다중 선택 입력 PASS).
- 툴 표: `tests/gui/audit128/tool_inventory.py` (blender -b).
- 메뉴 전수 실행 스윕 `gui_menu_sweep` (2차 세션): Edit/Modify/Display/Select/Create/Mesh/Edit Mesh/Mesh Tools/Mesh Display/Deform/
  Skeleton/Skin/Constrain/Key/Control/Curves/Surfaces/UV 의 매핑된 항목 626개 (오브젝트 모드 + 컴포넌트 모드)를 클릭처럼 실행.
  1차 실행이 Blender 를 크래시시킴 → #36 (P0, `gui_props_window_close_crash` 로 단독 재현). 그 항목을 빼고 재실행: Python 트레이스백 0,
  크래시 0, 정상 431, 오류 195 (대부분 Blender poll 실패 = 실제 클릭에서는 Maya 식 경고로 바뀜). 컴포넌트 모드 Edit/Select 항목은
  실제 메뉴 연산자로 다시 재서 #39 (`gui_component_mode_menus`, 6 FAIL). 결과 TSV 는 tmp/audit128_issues/sweep.tsv (추적 안 함).
- `tools/dogfood.py`: 전 항목 PASS, 콘솔 오류 0 (새 문제 없음).
- 이 단계는 src/ 를 바꾸지 않음 → 헤드리스·GUI 전체 묶음은 돌리지 않음 (테스트 대상 변경 없음; `tests/gui/run.py` 는 `--dir` 옵션만 추가,
  기본값은 기존 폴더).

## 남은 것

- 점검 못 한 영역: 홀드 키 C/V/J 실측(기존 GUI 테스트 PASS 로 갈음), Graph Editor 조작 세부, UV 툴킷 토글(사용자 #13 외), 셸프 버튼 전수
  실행, Hypershade(#25 사용자). 메뉴 스윕은 File/Windows/Render 와 새 창을 여는 항목(#36 경로)을 뺐음 — 그쪽은 따로 점검 필요.
- 심각도는 audit 이슈에만 매김; 사용자 이슈 #5–#14, #22, #23, #25, #27, #28 은 129 에서 분류.
- 129 = #1–#4 + P0/P1 (#36, #19, #20, #26, #39) 수정 배치.
