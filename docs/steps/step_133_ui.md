# Step 133 — 레인 UI (핵심 UI 의 외형 + 조작, 재점검 8차)

사용자 지시 (2026-10-22) 중 이 레인 몫: 깨끗한 설정에 설치 → GUI 를 Maya 사용자처럼 써 보고 (레이아웃, Channel Box, 마킹 메뉴, 핫박스,
키 조작) 스크린샷을 보고 Maya 2022 와 나란히 비교, `tools/look_compare.py` 수치. 비판 기준: 「기본 Maya 에 Blender 기능이 붙은 모습」 —
칭찬 없이 차이만. 등급 · 점수는 step 98 과 같다 (look / operation / function / missing, 점수 = 하루 빈도 F (1–5) × 심각도 S (1–5)).
고치지 않았다 (점검 단계; 이슈는 메인 레인).

## 방법

- 빌드 `dist/maya-workflow-kit-0.2.1.zip` (look_compare 가 만든 것) 을 이 레인 전용 샌드박스 `tmp/audit133_ui/env_<tag>/` 에
  `blender --command extension install-file --enable` 로 설치 (`tmp/audit133_ui/run_session.py`; `release_check.sandbox_env`, 실제
  `%APPDATA%` 안 건드림, 시작한 Blender PID 만 종료).
- GUI 세션 `tmp/audit133_ui/session.py` (1600x900, `--enable-event-simulate`, `ALLSET_FIT_WARP=1`): **새 사용자처럼 환영 대화상자를 띄운 채
  Return** (= 「Make Blender feel like Maya」) → Maya 레이아웃 새 장면 → 큐브 → W/E/R, Ctrl+A ×2, Space 핫박스, RMB / Shift+RMB /
  Ctrl+RMB (오브젝트 · 정점 모드), F9/F10/F11/F8, b, Tool Settings, Layer Editor, 그리고 키 (Q/T/Y/W, F/A, Alt+LMB/MMB/RMB, Ctrl+D,
  Ctrl+G, P, Shift+P, h, Ctrl+Z, Insert ×2, 3/1, 4/5/6/7, S, Shift+W, F2–F6, X 홀드 드래그, Ctrl+S, Ctrl+N).
  - effective UI scale 1.0 (`ALLSET_GUI_UI_SCALE=0.8`, Maya `grab()` 과 같은 논리 픽셀) → `tmp/audit133_ui/s100/shots/` 32 장.
  - effective 1.25 (이 PC 의 실제 배율) → `tmp/audit133_ui/s125/shots/` 32 장.
  - 실제 사용자 상태 확인 (Region Overlap 켜진 채 = step 130 이후 기본, 1.25): `tmp/audit133_ui/ovl125/shots/`.
  - 확인용 probe: `probe.py` (Alt 탐색 3 방식, X 홀드, F9 툴 유지), `probe2.py` (F / A 프레이밍 투영), `probe3.py` (X / C / V 홀드
    드래그), `probe4.py` (1/2/3 smooth preview), `probe5.py` (opt-in 뒤 환경설정 dirty).
- Maya 쪽: 기존 Maya 2022 그림 (`research/maya/screens/` 01–21, `audit7/maya/`, `ts106/`, `le129/`, `ivm/`) 재사용. Maya 를 새로 띄우지
  않았다 (Ctrl+RMB / 정점 모드 RMB 의 Maya 그림은 없음 — kit 동작은 `marking/__init__.py:139` 가 buildConvertMM.mel 을 인용, 화면 비교 못 함).
- 나란히: `tmp/audit133_ui/pairs.py` → `tmp/audit133_ui/pairs/s100_*.png` · `s125_*.png` (왼쪽 Maya, 오른쪽 kit), 뷰포트 확대
  `pairs/vp_*.png` (look_compare 의 카메라 맞춘 쌍에서 잘라냄), 그리드 `pairs/crop_grid_s100.png`, 표시 키 `pairs/k_display_keys.png`,
  메뉴 잘림 `pairs/zoom_m14_list.png` · `zoom_m15_clip.png`. 모든 쌍을 직접 열어 봤다.
- `tools/look_compare.py` 2 회: `ALLSET_LOOK_TAG=audit133` (1.25) → `research/maya/screens/compare_audit133/`,
  `ALLSET_GUI_UI_SCALE=0.8 ALLSET_LOOK_TAG=audit133_s100` (1.0) → `compare_audit133_s100/`. 로그 `tmp/audit133_ui/look_compare*.txt`.

## look_compare 수치 (step 98 대비)

| 항목 | step 98 기록 (theme 있음) | 4.5 기준 10-20 (theme 있음) | **지금 1.0** | **지금 1.25** |
|---|---|---|---|---|
| rects (±10 px) | 5/12 | – | **5/12** | 3/12 |
| pixels (ΔE00 > 5 = 다름) | 「5/31」 (34 비교, 5 다름, 4 없음) | 25 비교, 4 다름, 13 없음 | **25 비교, 16 다름, 13 없음** | 25 비교, 18 다름, 13 없음 |
| viewport 요소 ΔE00 < 5 | – | – | **1/12** (조작기 X 빨강만) | 1/12 |
| density | – | – | 4/6 | 1/6 |
| grid | – | – | **FAIL**, 모서리 0/4, 선 ΔE00 7.1 (kit #555555 / Maya #404040) | 같음 |
| scene (큐브 상자 ±10 %) | – | – | 3/3 | 3/3 |
| furniture | – | – | 1/3 (ViewCube 위치 ✗) | 1/3 |

- 픽셀 「다름」 4 → 16 은 step 130 (테마를 싣지 않음) 의 결과: 메뉴 바 #282828 (Maya #444444), Status Line 끝 #b6b6b6, Outliner 선택 행
  #334d80 (Maya #5285a6), 메뉴 팝업 #181818 (Maya #525252), Range Slider 손잡이, 필드 #545454 (Maya #2b2b2b) 등.
- **도구가 낡았다 (tools bug)**: `look_shots.py` / `look_second_start.py` 가 app template (`prefs.app_template == "Maya_Workflow_Kit"`) 과
  splash 를 검사해 4 FAIL (step 130 에서 템플릿이 없어짐). `look_data.py` 의 anchor `view3d.UI` (도크 — step 116 부터 Properties 영역) 와
  `shelf.HEADER` (step 113 부터 헤더 없음) 가 없어 Channel Box / Layer Editor rect 가 「missing」, 픽셀 7 개가 「?」. 수치 일부는 측정 불가.

## 발견 (점수순)

증거 경로는 `tmp/audit133_ui/` 기준. 「이슈」 = 열린 GitHub 이슈와 겹침. 「bug」 = 이슈로 올릴 kit 결함, 「gap」 = Maya 동등성 차이,
「decided」 = 이미 정한 결정의 결과 (다시 판단할 거리).

| # | 차이 | 등급 | F | S | 점 | 증거 | kit 쪽 | 종류 |
|---|---|---|---|---|---|---|---|---|
| 1 | **선택 표시가 Blender**: 선택 오브젝트 = 주황 외곽선만 (Maya: 리드 = 초록 #43ffa3 전체 와이어, 다른 선택 = 흰 와이어), 정점 검정/주황 (Maya 보라 #c800c8 / 노랑 #fdff88), Outliner 선택 행 어두운 파랑 + 주황 글자 (Maya #5285a6 + 흰 글자). viewport 요소 1/12 만 ΔE00 < 5 | look | 5 | 4 | 20 | `pairs/vp_02_cube_selected_move.png`, `vp_08_verts_selected.png`, `compare_audit133_s100/viewport.md` | 테마 없음 (step 130), `ui/` 그리기 | decided (닫힌 #45) |
| 2 | **UI 전체 색이 Blender 어두운 테마**: 메뉴 바 · 패널 · 팝업 메뉴 · 필드가 #181818–#303030 (Maya #444444 / #525252 / #2b2b2b). 픽셀 샘플 다름 4 → 16 / 25 | look | 5 | 3 | 15 | `compare_audit133_s100/pixels.md`, `pairs/s100_a01_first_screen.png` | step 130 결정 | decided |
| 3 | **그리드가 거의 안 보인다**: 대비 표준편차 3.9 (Maya 9.4), 선 #555555 (Maya #404040), 원점 축 굵은 선 없음 (Maya 검은 굵은 X/Z 축선). 대신 원점에 Blender 3D 커서 (빨강·흰 점선 원) — Maya 에 없는 물건이 첫 화면 한가운데 | look | 5 | 3 | 15 | `pairs/crop_grid_s100.png`, `compare_audit133_s100/grid.md` | `ui/maya_grid.py`, 템플릿 overlay (`tools/make_startup.py`, `show_cursor`) | bug |
| 4 | **Layer Editor 가 밀려 사라진다**: Channel Box 가 polyCube1 INPUTS 를 늘 펼쳐 (Width … Axis Z 9 행) 1.0 에서 Layer Editor 가 80 px 로 줄고, **1.25 (이 PC 기본) 에서는 Display / Anim 탭까지 화면 밖**. Maya: INPUTS 노드는 접힌 한 줄, CB / LE 경계 고정 (첫 화면과 같은 높이) | look/operation | 5 | 3 | 15 | `s100/shots/b02_cube_selected_move.png` (LE y 660–810), `s125/shots/b11_channel_box.png` (LE 없음), Maya `11_channel_box.png` | `ui/channel_box.py`, `ui/maya_dock.py` | bug |
| 5 | Y-up 이 아니다: 조작기 파랑 = 위, 초록 = 옆 (Maya 초록 Y 위), 축 표시 z/y | look/operation | 5 | 3 | 15 | `pairs/vp_02_cube_selected_move.png`, `vp_06_scale_manip.png` | 결정 5 (불가능 목록) | decided |
| 6 | **Ctrl+N (변경 있음)**: 「New Scene in Maya Layout — unsaved changes are lost」 OK / Cancel. Maya: 「Save changes to untitled scene?」 Save / Don't Save / Cancel — 저장 경로가 없어 작업을 잃기 쉽다 | function | 3 | 4 | 12 | `s100/shots/k09_ctrl_n.png` | `first_start.py:91-95` (`invoke_confirm`) | bug |
| 7 | **마킹 메뉴 목록이 영역 경계에서 잘린다**: RMB 오브젝트 목록이 창 아래에 닿자 두 칸으로 나뉘고 둘째 칸 「Assign Existing Material」 이 반만 그려진 뒤 나머지 (Maya 의 이후 항목) 가 없다; Shift+RMB 목록의 「Booleans」 행은 3D View 와 Timeline 사이 틈에서 위쪽이 잘림. Maya: 한 칸 목록이 그대로 화면 밖까지 | look/operation | 4 | 3 | 12 | `pairs/zoom_m14_list.png`, `pairs/zoom_m15_clip.png` | `marking/draw.py` (COVER 영역 사이 틈), `marking/engine.fit_ring` | bug |
| 8 | 도크 너비가 UI 배율을 따르지 않는다: Properties 도크 278 px 가 1.0 과 1.25 에서 같고 Outliner 는 260 → 325. 1.25 에서 탭 「Chann... Attribu... Modeli...」, CB 「Subdivisions Hei...」 잘림. 1.0 에서도 AE 탭 「pCube... polyCu... initialS...」 잘리고 AE 메뉴 바가 두 줄 | look | 5 | 2 | 10 | `s125/shots/a01_first_screen.png`, `s100/shots/c03_attribute_editor.png`, 세션 로그 `areas` | `ui/maya_dock.py`, `ui/toolbox.fit_columns` | bug |
| 9 | F9 / F10 / F11 / 3 뒤 Blender 의 Adjust Last Operation 패널 (「Component Mode」, 「Smooth Mesh Preview」) 이 뷰포트 왼쪽 아래에 남는다. Maya 에 없음 | look | 5 | 2 | 10 | `s100/shots/c07_soft_select.png`, `pairs/k_display_keys.png` | `operators/display.py:150,223` (`bl_options` REGISTER) | bug |
| 10 | Outliner: 새 오브젝트가 persp/top/front/side 위에 온다 (Maya: 카메라 → 오브젝트 → set 순), 아이콘 Blender 주황 삼각형 (Maya transform 아이콘), 줄무늬 배경, 「Outliner」 제목 · 넓은 검색 칸 없음 (「Sear」 잘림) | look | 5 | 2 | 10 | `compare_audit133_s100/crop_outliner.png` | `ui/outliner_sets.py` (`default_entries` 가 C 행 뒤) | gap (#54 아이콘 부분) |
| 11 | RMB 마킹 링이 크다: 박스 중심까지 약 80 px (Maya 약 55 px), 박스 너비가 글자에 맞춤 (Maya 같은 너비 박스), UV 박스 하위 메뉴 화살표 없음 — 제스처 거리가 Maya 보다 길다 | look/operation | 5 | 2 | 10 | `s100/shots/m14_rmb_object.png` vs Maya `14_marking_menu_object.png` | `marking/engine.py` 반지름 | gap |
| 12 | X 홀드 그리드 스냅이 기본 뷰에서 5 cm 단위 (3.9 cm 드래그 → 5, 5). Maya 기본 그리드 (12 / 5 / 5) 는 세분선 1 단위에 스냅하는 것으로 안다 — **Maya 에서 재확인 필요** | operation | 4 | 3 | 12 | `probe3/session.log` (`X-hold centre drag … -> (0.05, 0.05, 0.0)`) | `operators/hold.py` / Blender 줌 의존 증분 | gap (확인 필요) |
| 13 | Blender 조작기 툴팁: 마우스를 조작기에 두면 「Move selected items / Shortcut: drag-Left Mouse」 가 뜬다. Maya 없음 | look | 4 | 2 | 8 | `s100/shots/c03_attribute_editor.png` | `ui/manipulator.py` | bug |
| 14 | AE: shape 섹션 6 (Maya 12: Tessellation, Tangent Space, Displacement Map, Component Tags, Node Behavior, UUID 없음), Notes · Select / Load Attributes / Copy Tab 가 섹션 바로 아래 (Maya 창 바닥) | look | 4 | 2 | 8 | `pairs/s100_c03_attribute_editor.png` vs `ts106/ae_transform.png` | `ui/attribute_editor.py` | gap |
| 15 | 3 (smooth preview) 결과가 각진 면 셰이딩 (면이 평평하게 보임, 주황 와이어가 세분된 메시 전체에). Maya 3 = 매끈한 셰이딩 | look | 3 | 3 | 9 | `probe4/shots/p20_smooth3.png` | `operators/display.py` `_ensure_shade_modifier` | bug |
| 16 | 컴포넌트 모드 RMB 목록에서 Select All / Deselect All / Select Hierarchy / Invert Selection 이 회색 (`object.select_all` 은 편집 모드에서 poll 실패). Maya 는 활성 | function | 3 | 2 | 6 | `s100/shots/m17_rmb_vertex_mode.png` | `marking/menus.py:137-140` | bug |
| 17 | Time Slider: 프레임마다의 작은 눈금 없음, 현재 프레임이 파란 상자, 키 뒤 현재 프레임 상자가 빨강, 키를 찍으면 왼쪽 끝에 0 이 보임. Range Slider 줄에 Auto Key · 사운드 · 루프 · 재생 속도 드롭다운 없음 (텍스트 「24 fps」) | look | 5 | 1 | 5 | `compare_audit133_s100/crop_time_slider.png`, `crop_range_slider.png`, `s100/shots/k09_ctrl_n.png` | `ui/time_slider.py`, `ui/range_bar.py` | gap |
| 18 | 7 (모든 조명) 에 조명이 없으면 Material Preview 처럼 하얀 큐브 + 어두운 배경. Maya 7 + 조명 없음 = 검은 물체 | look | 2 | 2 | 4 | `pairs/k_display_keys.png` (오른쪽 아래) | `operators/display.apply_display_mode` | gap |
| 19 | RMB 링의 Vertex Face 회색 (Maya 활성) | missing | 2 | 2 | 4 | `s100/shots/m14_rmb_object.png` | Blender 에 vertex-face 모드 없음 | gap |
| 20 | Tool Settings 도크 글자 잘림 (「Transform Constr...」, 「Show Orientation Ha...」, 「Absol...」), Layer Editor 행의 색 견본 자리에 X 아이콘 | look | 3 | 1 | 3 | `s100/shots/c02_tool_settings_move.png`, `le03_layer_editor.png` | `ui/tool_settings.py`, `ui/layer_editor.py` | gap |
| 21 | 첫 실행: 환영 대화상자가 마우스 위치 (창 왼쪽 아래) 에 Blender splash 와 겹쳐 뜨고, Blender splash 는 매 시작마다 뜬다 (look_compare 「Blender splash off」 FAIL) | look | 1 | 2 | 2 | `s100/shots/w00_welcome.png` | `welcome.py` | gap |

이미 정한 것 (step 98 이후 그대로, 참고): Ctrl+S / Open 이 Blender 파일 브라우저 (`s100/shots/k08_ctrl_s_win.png`, step 98 #15, 결정 step 102),
Command Line 「Python」 (step 98 #8), 핫박스 가운데 「Maya Workflow Kit」 (결정 12).

## 조작 결과 (이벤트 시뮬레이션, 1.0 / 1.25 같음)

Maya 와 같게 동작: 환영 Return → Maya 모드 + Maya 레이아웃, 첫 툴 = Select, Create Cube → pCube1 (lambert1, 선택), W/E/R/Q/T, Ctrl+A
AE ↔ CB, F9/F10/F11/F8 (F8 뒤 in-view 메시지), b 소프트 선택, F/A, Alt+LMB/MMB/RMB (Alt 를 먼저 누르고 다음 틱에 끌면 됨), Ctrl+D →
pCube2 선택, Ctrl+G → group1 선택, P → pCube2 가 pCube1 아래, Shift+P → 월드, h → `hide_viewport`, Ctrl+Z 복구, Insert 피벗 편집 켬/끔,
3 / 1 smooth preview (1 은 모디파이어를 숨김), 4 와이어 / 5 솔리드 / 6 텍스처 / 7 조명, S = 10 채널 키 (visibility 포함), Shift+W = 이동 3 채널,
F2–F6 메뉴 세트, X / C / V 홀드 드래그 이동, F9 뒤에도 Move 툴 유지, Ctrl+S = 프로젝트 scenes 폴더 Save As.

차이는 위 표 (#6 Ctrl+N, #12 X 스냅 간격). 테스트 도구 쪽 주의: 같은 틱에 Alt PRESS 와 드래그를 보내면 탐색이 안 된다 (`probe.py` (c)) —
실제 입력에서는 생기지 않는 시뮬레이션 조건이라 발견에서 뺐다.

## 콘솔

- 세션 4 + probe 6 회: traceback 0, WARN 0. 종료 때마다 Blender 의 `Error: Not freed memory blocks: 10, total unfreed memory 0.000977 MB`
  (Blender 4.5 아이콘/프리뷰 해제 쪽 추정, kit 확인 못 함).
- 환영 대화상자 opt-in 뒤 `preferences.is_dirty = True` → 종료 때 Blender 자동 저장이 샌드박스 `userpref.blend` 를 쓴다 (`probe5`). kit 은
  `welcome_done` (자기 add-on 환경설정) 만 바꾸므로 결정 (step 130: 자기 환경설정만) 과 맞다 — 기록만.

## bug 후보 (이슈용 재현)

1. **Layer Editor 사라짐** (#4): 깨끗한 설정, effective 1.25, Make Blender feel like Maya → Create > Polygon Primitives > Cube →
   오른쪽 도크에 Display / Anim 탭이 보이지 않음 (1.0 에서는 80 px 로 줄어듦).
2. **Ctrl+N 저장 질문 없음** (#6): 큐브를 만든 뒤 Ctrl+N → OK / Cancel 만, Save 없음.
3. **마킹 메뉴 목록 잘림** (#7): 1.0, 큐브 선택, 뷰포트 가운데에서 RMB 길게 → 목록 둘째 칸 마지막 행이 반만, 나머지 없음;
   Shift+RMB → 「Booleans」 행 위쪽이 Timeline 경계에서 잘림.
4. **그리드 / 3D 커서** (#3): 첫 화면 그리드 선 ΔE00 7.1, 축선 없음, 원점의 3D 커서.
5. **도크 너비 고정** (#8): 1.25 에서 Outliner 325 px, 도크 278 px — 탭 · 채널 이름 잘림.
6. **Adjust Last Operation 패널** (#9): F9 → 뷰포트 왼쪽 아래 「Component Mode」 패널; 3 → 「Smooth Mesh Preview」.
7. **조작기 툴팁** (#13): Move 툴, 마우스를 조작기 위에 멈춤 → Blender 툴팁.
8. **smooth preview 셰이딩** (#15): 큐브 → 3 → 면이 각져 보임.
9. **컴포넌트 RMB 목록 회색** (#16): F9 → RMB → Select All 등 회색.
10. **look_compare 도구 낡음**: `python tools/look_compare.py` → app template / splash 4 FAIL, anchor `view3d.UI` · `shelf.HEADER` 없음.

## 남은 것

- Maya 2022 에서 Ctrl+RMB / 컴포넌트 모드 RMB / X 그리드 스냅 간격 (#12) 을 직접 찍어 확인하지 않았다.
- look_compare 의 anchor 와 app template 검사를 고쳐야 CB / LE / 셸프 탭 픽셀이 다시 측정된다.
