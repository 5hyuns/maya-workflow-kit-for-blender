# Step 145 — 레인 A 살아 있는 세션 (재점검 9차)

사용자 지시 (2026-10-24) 중 이 레인 몫: (1) 헤드리스 전체 + 깨끗한 설정에 설치 → GUI 를 Maya 사용자처럼 써 보기 (레이아웃, Channel Box,
마킹 메뉴, 핫박스, 키, 모델링 · UV · 애니 · 리깅 · FX · 렌더 · 파일) 와 (5) 의 시각 · 조작 부분. 비판 기준 (사용자 2026-10-19):
「기본 Maya 에 Blender 기능이 붙은 모습」 — 칭찬 없이 차이만. 고치지 않았다 (점검 단계). 새 버그는 바로 GitHub 이슈 (#91–#100).

점수 = 심각도 S (1–5) × 빈도 F (1–3, 3 = 매일 여러 번). 등급: look (보이는 것) / operation (조작) / function (결과). 판정: CONFIRMED = 그림 ·
로그로 확인, PLAUSIBLE = 한 번 보고 원인 추정.

## 방법

- 헤드리스 전체: `python tests/run.py` (기본 `tmp/test_env`, 빌드 포함).
- 깨끗한 설치 + 스크립트 세션: `python tools/dogfood.py` (`tmp/release_env`, 결과 `tmp/dogfood/`).
- 이 레인의 GUI 세션 (모두 자기 샌드박스 `tmp/audit145a/env_<tag>/` 에 `extension install-file --enable`, `--factory-startup` 없이
  `BLENDER_USER_*` 를 미리 만든 tmp 폴더로; 1600 x 900, `--enable-event-simulate`; 띄운 Blender PID 만 종료; Blender 는 한 번에 하나):
  - `tmp/audit145a/run_session.py` + `session.py` (step 133 세션을 0.3.0 zip 으로 다시): 환영 대화상자 Return → Maya 레이아웃 → 큐브,
    W/E/R, Ctrl+A ×2, Space 핫박스, RMB / Shift+RMB / Ctrl+RMB (오브젝트 · 정점 모드), F8–F11, b, Tool Settings, Layer Editor, Q/T/Y,
    F/A, Alt 탐색, Ctrl+D/G, P, Shift+P, h, Ctrl+Z, Insert, 3/1/4/5/6/7, S, Shift+W, F2–F6, X 홀드, Ctrl+S, Ctrl+N.
    effective 1.0 (`ALLSET_GUI_UI_SCALE=0.8`, Maya `grab()` 과 같은 논리 픽셀) → `tmp/audit145a/s100/shots/` 31 장.
  - `wf.py` (작업 흐름, effective 1.25 = 이 PC 의 실제 배율, 환영 없이 opt-in): F11 + Ctrl+E + 드래그, F10 + Ctrl+B, Multi-Cut, Insert
    Edge Loop, Quad Draw, UV > Automatic + UV Editor, S 키 + Graph Editor, Create Joints (3 클릭) + Create IK Handle + 원기둥 Bind Skin +
    Paint Skin Weights, Deform > Lattice, nParticles > Create Emitter + 40 프레임, nCloth + 30 프레임, Render Current Frame, Hypershade,
    File > Export All 대화상자 + FBX 내보내기 / 가져오기 → `tmp/audit145a/wf125/shots/` 27 장.
  - `wf2.py` (wf 의 Multi-Cut / Insert Edge Loop 좌표 수정, Delete 뒤 이름, 균일 크기 원기둥 Bind Skin + 관절 키 + 재생, 격자 CB 행,
    3 smooth preview) → `tmp/audit145a/wf2_125/shots/` 13 장.
- 기존 GUI 테스트 중 위 시나리오 모듈 (`-k step144,step139,step137,step131_hypershade,step102,step70,step57,step58,step68,step66,step17,
  step25,step99,step136,step143`, `--shots tmp/audit145a/guishots`).
- `ALLSET_GUI_UI_SCALE=0.8 ALLSET_LOOK_TAG=audit145_s100 python tools/look_compare.py` (step 142 과 같은 1.0 측정) →
  `research/maya/screens/compare_audit145_s100/`.
- Maya 쪽: Maya 를 새로 띄우지 않고 기존 캡처 (`research/maya/screens/01–21`, `audit7/maya/`, `ts106/`, `ivm/`, `hypershade131/`) 와
  나란히 봤다. 모든 kit 그림을 직접 열어 봤다.

## 수치

| 항목 | step 133 (8차) | step 142 | **지금 (145)** |
|---|---|---|---|
| 헤드리스 전체 | 1025 / 0 (127 파일) | 1227 / 0 (149) | **1307 passed, 0 failed (156 파일)**, traceback 0 |
| dogfood (깨끗한 설치 + 세션) | 48 / 48, 콘솔 0 | – | **48 / 48, 콘솔 오류 · 경고 0** |
| GUI 시나리오 테스트 묶음 | – | – | **206 passed, 0 failed (22 파일)** |
| 이 레인 core 세션 checks | 35 / 40 | – | 35 / 40 (FAIL 5 = Alt+LMB/MMB/RMB 같은 틱 시뮬레이션 조건, X 홀드 드래그 — 둘 다 step 133 과 같은 시뮬레이션 쪽 원인, 1 은 모디파이어를 숨김 = 설계) |
| look_compare viewport (ΔE00 < 5) | 1/12 | 11/12 | **11/12** (남은 것 = 면 점묘 tint 측정, #76 셋째 항목) |
| look_compare pixels kit-drawn | – | 6/6 | **6/6**; 테마 샘플 30 중 **19 개 > 5** (계산 제외) |
| look_compare rects (±10 px) | 5/12 | – | **5/12** (Tool Box / Outliner / 뷰포트 / 도크 높이 +37, Time Slider y +24) |
| density | 4/6 | – | **5/6** (메뉴 위치 −6 px) |
| grid | FAIL | ok | **ok** (ΔE00 0.7, 모서리 4/4) |
| furniture | 1/3 | – | **2/3** (축 표시 outline only) |
| checks | 4 FAIL (도구 낡음) | 9/9 | **9/9** |

콘솔: 모든 세션 · 테스트에서 traceback 0 (내 스크립트 실수 1 건 제외: `wf125` `at()` 인자). 종료 때마다 Blender 의 `Error: Not freed memory
blocks: 5–54, total unfreed memory < 0.004 MB` (step 133 과 같은 종류).

## 발견 (점수순)

증거 경로: `s100/` = `tmp/audit145a/s100/shots/`, `wf/` = `tmp/audit145a/wf125/shots/`, `wf2/` = `tmp/audit145a/wf2_125/shots/`,
Maya = `research/maya/screens/`. 「이슈」 = 이번에 올린 것 (#91–#100) 또는 열린 / 닫힌 기존 이슈. 「decided」 = 이미 정한 결정의 결과.

| # | 차이 | 등급 | S | F | 점 | 증거 (kit / Maya) | kit 쪽 (추정) | 이슈 · 판정 |
|---|---|---|---|---|---|---|---|---|
| 1 | **선택 와이어가 변형을 따라가지 않는다**: 스킨된 원기둥을 재생하면 메시는 굽는데 초록 리드 와이어는 쉬는 자세 그대로 (재생 중 · 멈춘 뒤 모두), nCloth 평면도 와이어와 셰이딩 위치가 다름 | function/look | 4 | 3 | 12 | `wf2/d06_skinned_playing_wire.png`, `wf2/d07_skinned_stopped_wire.png`, `wf/f02_ncloth_frame30.png` / Maya: 와이어 = 변형된 메시 | `ui/selection_wire.py:207-219` (배치를 `depsgraph_update_post` 에서만 버림, 프레임 변경 없음) | **#91** CONFIRMED |
| 2 | UI 색이 Blender 어두운 테마: 메뉴 바 #181818 (Maya #444444), 팝업 메뉴 #181818 (#525252), 필드 #545454 (#2b2b2b), Outliner 선택 행 #334d80 (#5285a6), 편집기 경계 #161616 (#5c5c5c) — 테마 샘플 19/30 이 ΔE00 > 5 | look | 3 | 3 | 9 | `compare_audit145_s100/pixels.md`, `12_create_menu.png` | step 130 (테마 없음) | decided (#45) |
| 3 | **RMB 링이 크다**: 박스가 누른 점에서 약 80 px (Maya 약 55 px), 박스 너비가 글자에 맞춤 (Maya 같은 너비), UV 하위 메뉴 화살표 없음 → Maya 손 기억의 짧은 튕김이 박스에 닿지 않음 | operation | 3 | 3 | 9 | `s100/m14_rmb_object.png` / `14_marking_menu_object.png` | `marking/engine.py`, `marking/draw.py` | **#99** CONFIRMED (step 133 #11 에서 측정, 이슈 없었음) |
| 4 | **Graph Editor**: 곡선이 미터로 그려져 Translate X (0→5) 가 Scale (1) 옆에서 바닥에 붙은 평선; visibility 채널 이름이 「Hide Viewport」; 모든 속성 행이 파랑으로 칠해져 빨강/초록/파랑 글자가 안 읽힘; 장면 범위 밖이 갈색, Blender 재생 헤드 | look/function | 3 | 3 | 9 | `wf/c02_graph_editor.png` / `audit7/maya/e02_graph_editor_win1.png` | `ui/editor_chrome.py:459` (`MAYA_ATTR` 에 hide_viewport 없음), 행 `SELECT` | **#96** CONFIRMED (#66 후속) |
| 5 | Ctrl+E 조작기가 노란 Local Translate Z 화살표 하나뿐 (Maya polyExtrudeFace 조작기 = 로컬 축 화살표 3 + 평면 핸들 + 가운데 크기 상자) | operation | 3 | 3 | 9 | `wf/a02_ctrl_e_face.png`, `wf/a03_ctrl_e_after_drag.png` / `audit7/maya/c01_model_extrude.png` | `operators/extrude.py`, `ui/in_view.py` | gap (이슈 없음) |
| 6 | **Bind Skin 이 비균일 크기 메시에서 관절 하나를 빠뜨린다**: Scale Y 8 로 늘린 원기둥 → 영향 joint1 · joint3 만 (joint2 없음), 상태 줄 「Active object has non-uniform scale」. 크기를 얼린 원기둥은 3 개 모두 | function | 4 | 2 | 8 | `wf/d05_paint_skin_weights.png`, `wf125/session.log` vs `wf2_125/session.log` | `operators/skin.py:341` (ARMATURE_AUTO 열 가중치) | **#94** PLAUSIBLE |
| 7 | Adjust Last Operation 패널이 Ctrl+E (「Extrude」), Ctrl+B (「Bevel」), Create IK Handle, Joint Tool 뒤 뷰포트 왼쪽 아래에 뜨고 다른 명령 여러 개 뒤에도 남는다 (In-View Editor 와 같은 값 중복) | look | 2 | 3 | 6 | `wf/a02_ctrl_e_face.png`, `wf/a04_ctrl_b_edge.png`, `wf/d03_ik_handle.png`, `wf/e01_lattice.png` | `operators/extrude.py:669`, `component.py:77`, `skin.py:148`, `joints.py:172` (REGISTER+UNDO) | **#92** CONFIRMED (#58 · #86 와 같은 종류) |
| 8 | 큐브를 Delete 로 지우고 다시 만들면 pCube2 (Maya pCube1); 세션 내내 pCube3…6 으로 올라감 — 지운 오브젝트의 pCubeShape1 메시가 0 사용자로 남음 | function | 2 | 3 | 6 | `wf2_125/session.log`, `wf2/k02b_smooth_3.png` | `operators/naming.py:47-50` | **#93** CONFIRMED (#73 와 같은 패턴) |
| 9 | 조작기에 Blender 툴팁 「Move selected items」 | look | 2 | 3 | 6 | `s100/c03_attribute_editor.png` / `10_attribute_editor.png` | `ui/manipulator.py:499-513` | **#98** CONFIRMED (step 133 #13, 이슈 없었음) |
| 10 | 상태 줄에 Blender 보고 문구: 「Successfully added 3… keying set 'Location'」 (Shift+W), 「Blender has n…e bone that ends at the end joint」 (IK), 「Active object has non-uniform scale」, 「Pivot e…」, 「Anim Player」; Help Line 이 W 뒤 한 박자 늦게 「Select Tool」 그대로 | look | 2 | 3 | 6 | `s100/k06_keys_timeslider.png`, `wf/d03_ik_handle.png`, `s100/b02_cube_selected_move.png` | `operators/skin.py:23`, Blender `anim.keyframe_insert` 보고 | **#100** CONFIRMED |
| 11 | Deform > Lattice: ffd1Lattice Scale 0.02 (Maya 2), 격자가 Blender 주황 선택색 (Maya 초록 리드), Outliner 에 ffd1Base 없음 | function/look | 3 | 2 | 6 | `wf/e01_lattice.png`, `wf2/e02_lattice_framed.png` | `operators/deformers.py:334` | **#95** CONFIRMED |
| 12 | 1.25 배 (이 PC 기본) 에서 뷰포트 850 px (Outliner 325 + 도크 346), 셸프 오른쪽 아이콘 잘림, 패널 툴바 » 넘침; Tool Settings 글자 잘림 (「Transform Constr...」, 「Absol...」, 「Show Orientation Ha...」) | look | 2 | 3 | 6 | `wf/w00_layout.png`, `s100/c02_tool_settings_move.png` | `ui/toolbox.fit_columns`, `ui/tool_settings.py` | #85 (열림) |
| 13 | RMB 목록이 두 칸으로 갈라지고 첫 칸 끝 (DG Traversal / Inputs) 이 빈 띠를 건너 Time Slider 위에 그려짐; DG Traversal · Inputs · Outputs · Metadata · Time Editor 회색 (Maya 활성) | look/function | 2 | 3 | 6 | `s100/m14_rmb_object.png`, `s100/m17_rmb_vertex_mode.png` / `14_marking_menu_object.png` (한 칸) | `marking/engine.fit_ring` (step 136 설계) | decided (step 136, #56 닫힘) |
| 14 | Channel Box: 채널 이름이 가운데 정렬 (Maya 칸에 붙은 오른쪽 정렬), 키 찍힌 칸 짙은 빨강 + 오른쪽에 Blender 키 다이아몬드 장식, SHAPES / INPUTS 노드 줄에 Maya 의 어두운 막대 없음 | look | 2 | 3 | 6 | `s100/k06_keys_timeslider.png`, crop `tmp/audit145a/crop_cb.png` / `11_channel_box.png` | `ui/channel_box.py` | gap |
| 15 | Outliner: 새 오브젝트가 persp/top/front/side 위 (Maya: 카메라 → 오브젝트 → set), 아이콘 Blender 주황 삼각형, 「Outliner」 제목 없고 검색 칸 「Sear」 잘림 | look | 2 | 3 | 6 | `s100/b02_cube_selected_move.png`, `tmp/audit145a/crop_outliner.png` / `11_channel_box.png` | `ui/outliner_sets.py` (C 행 뒤) | gap (step 133 #10 그대로) |
| 16 | UV Editor: 머리줄이 Blender 위젯 (선택 모드 / 동기, New · Open, 「map1」, 피벗 · 스냅), UV 캔버스에 Blender 2D 커서 · 확대/손 기즈모, 선택 면 주황, UV Toolkit 이 Blender 사이드바 탭 (UV Toolkit / Image / Tool / View) 안, 창이 작아 캔버스가 반 | look | 3 | 2 | 6 | `wf/b02_uv_editor_window.png` / `audit7/maya/d01_uv_editor_win1.png` | `ui/shelf.py` 이미지 머리줄, UV 창 열기 | gap |
| 17 | Hypershade: Graph 에 lambert1 대신 Blender Principled BSDF + Material Output 노드, 1.25 에서 창 850 x 655 → 탭 「Mate… Textu…」, Create 분류 「Surf… Volu…」 잘림, Browser 견본에 이름 없음, Create 목록이 Blender 버튼 (Maya 아이콘 목록) | look/function | 3 | 2 | 6 | `wf/g03_hypershade.png` / `hypershade131/hypershade_default_grab.png` | `ui/hypershade.py`, `ui/hypershade_layout.py` | gap |
| 18 | Multi-Cut 뒤 Channel Box INPUTS 에서 polyCube1 이 사라짐 (Maya: polySplit1 이 쌓임); Quad Draw 편집 모드에서도 INPUTS 없음 | function | 2 | 2 | 4 | `wf2/a08_insert_loop_hover.png`, `wf/a11_quad_draw_dots.png` | `ui/channel_box.py` history 노드 | gap |
| 19 | Bind Skin 뒤 INPUTS 이름 「Armature」 + Blender 모디파이어 표시 아이콘 (Maya skinCluster1) | look | 2 | 2 | 4 | `wf/d04_bind_skin.png` | `operators/skin.py:341` | **#97** CONFIRMED |
| 20 | Tool Settings 가 Outliner 와 뷰포트 사이에 붙음 (Maya: 창 맨 왼쪽, Tool Box 바깥), Axis Orientation 「Global」 (Maya 「World」 + 0.0000 칸 3 개), Transform Constraint 가 회색 버튼 (Maya 드롭다운 + Along Normals / Closest Point), Step Snap 이 버튼 세 개 | look | 2 | 2 | 4 | `s100/c02_tool_settings_move.png` / `ts106/a_docked_left_main.png` | `ui/tool_dock.py`, `ui/tool_settings.py` | gap |
| 21 | AE: shape 섹션 6 (Maya 12), 섹션 머리가 막대 없는 글자, Notes · Select / Load Attributes / Copy Tab 이 섹션 바로 아래 (Maya 창 바닥) | look | 2 | 2 | 4 | `s100/c03_attribute_editor.png` / `10_attribute_editor.png` | `ui/attribute_editor.py` | gap (step 133 #14 그대로) |
| 22 | 관절: Blender 팔면체 회색 본, 3 클릭에 관절 공 4 개 (끝 꼬리), IK 핸들이 주황 십자만 (Maya 핸들 선), 웨이트 페인트에서 본이 빨강 | look | 2 | 2 | 4 | `wf/d01_joint_tool_3_clicks.png`, `wf/d03_ik_handle.png`, `wf/d05_paint_skin_weights.png` | `operators/joints.py`, Blender 아마추어 그리기 | gap |
| 23 | Render View: 배경 회색 (Maya Arnold 검정), 머리줄이 Blender (Render / Keep Image / Remove Image / Slot / View / Image / Render Result) — Maya 메뉴 (File View Render IPR Options Display Render Target Help) + 아이콘 줄 없음 | look | 2 | 2 | 4 | `wf/g01_render_view.png` / `audit7/maya/h04_render_view_win1.png` | `ui/render_view.py` | gap |
| 24 | Insert Edge Loop: 모서리 위에 마우스를 둬도 미리 보기 고리 없음 (Maya 점선 미리 보기) | operation | 2 | 2 | 4 | `wf2/a08_insert_loop_hover.png` | `operators/edge_loops.py` | gap, PLAUSIBLE (한 틱만 봄) |
| 25 | Time Slider 120 뒤 · Graph Editor 0 앞이 갈색 (장면 범위 밖), 시뮬레이션 캐시 빨강/파랑 줄이 Time Slider 에 | look | 1 | 3 | 3 | `tmp/audit145a/crop_timeline_r.png`, `wf/f01_emitter_frame40.png` | `ui/time_slider.py` | gap |
| 26 | 패널 툴바 노출 / 감마 칸이 파란 채움 「0.0」 「1.0」 (Maya 회색 「0.00」 「1.00」), 색 관리 「AgX」 (Maya ACES) | look | 1 | 3 | 3 | `s100/a01_first_screen.png` / `01_layout_empty.png` | `ui/panel_toolbar.py` | gap |
| 27 | nParticles 이미터: Outliner 에 nParticle1 / nucleus1 없음 (emitter1 하나, 메시 아이콘) | look | 2 | 1 | 2 | `wf/f01_emitter_frame40.png` | `operators/fx.py` | gap |
| 28 | 7 (모든 조명) + 조명 없음 = 하얀 큐브 (Maya 검정), 배경도 바뀜 | look | 2 | 1 | 2 | `s100/k05_lights_7.png` | `operators/display.apply_display_mode` | gap (step 133 #18 그대로) |
| 29 | 첫 실행: 환영 대화상자가 왼쪽 아래 Blender splash 위에 겹쳐 뜸 | look | 2 | 1 | 2 | `s100/w00_welcome.png` | `welcome.py` | gap (step 133 #21 그대로) |
| 30 | b 의 in-view 메시지 「Soft Select is on.」 (Maya 「Soft Select mode is on.」) | look | 1 | 2 | 2 | `s100/c07_soft_select.png` / `ivm/ivm_07_soft_select.png` | `ui/view_message.py` 문구 | gap |

이미 정한 것 (다시 판단할 거리, 점수 표에서 뺌): Y-up 아님 (조작기 파랑 = 위, 결정 5), Command Line 「Python」 (step 98 #8), 핫박스 가운데
「Maya Workflow Kit」 (결정 12), Ctrl+S / Export 가 Blender 파일 브라우저 (step 102; Export All 옵션은 Files of type + Maya Units 두 칸뿐,
`wf/h01_export_all_dialog.png`).

## step 133 대비 고쳐진 것 (확인만)

Ctrl+N 이 Save / Don't Save / Cancel (`s100/k09_ctrl_n.png`, #57), 그리드 ok, 선택 · 컴포넌트 색 11/12, 도크 너비 287 (1.0), F8–F11 / 3
의 Adjust Last Operation 없음 (#58), INPUTS 접힘으로 Layer Editor 유지 (#55), 컴포넌트 RMB 의 Select All 활성 (#62), Render Current
Frame 이 그림을 냄 (#67), FBX 내보내기 → 가져오기 이름 pCube6 유지.

## 상위 10 (점수순)

1. 선택 와이어가 변형 · 재생을 따라가지 않음 — 12 (#91)
2. UI 테마 색 (메뉴 · 팝업 · 필드 · 선택 행) — 9 (decided #45)
3. RMB 링 반지름 · 박스 너비 — 9 (#99)
4. Graph Editor 미터 곡선 · 「Hide Viewport」 · 행 강조 — 9 (#96)
5. Ctrl+E 조작기가 화살표 하나 — 9 (gap)
6. 비균일 크기 메시 Bind Skin 이 관절 영향 누락 — 8 (#94)
7. Ctrl+E / Ctrl+B / IK / Joint Tool 뒤 Adjust Last Operation 패널 — 6 (#92)
8. Delete 뒤 이름이 다시 1 부터 시작하지 않음 — 6 (#93)
9. 조작기 Blender 툴팁 — 6 (#98)
10. 상태 줄의 Blender 보고 문구 — 6 (#100) (같은 6 점: 격자 크기 #95, 1.25 좁은 뷰포트 #85, Channel Box · Outliner · UV · Hypershade 모양)

## 올린 이슈

#91 와이어 변형 · #92 Adjust Last Operation · #93 이름 재사용 · #94 Bind Skin 비균일 · #95 격자 Scale 0.02 · #96 Graph Editor ·
#97 INPUTS 「Armature」 · #98 조작기 툴팁 · #99 RMB 링 크기 (maya-parity) · #100 Blender 보고 문구. 모두 milestone 0.4.0, 라벨
found-by-audit + bug.

## 남은 것

- Maya 2022 를 띄워 같은 장면 (Ctrl+E 조작기, Insert Edge Loop 미리 보기, 3 의 와이어, Paint Skin Weights 기본 색) 을 다시 찍지 않았다 —
  표의 Maya 쪽은 기존 캡처와 Maya 동작 지식.
- `wf` 세션의 첫 Multi-Cut / Insert Edge Loop 는 좌표 실수로 무효 → `wf2` 에서 다시 함. Quad Draw Shift 미리 보기 단계는 스크립트 오류로
  못 봄. Alt 탐색 · X 홀드는 이 세션 방식 (같은 틱) 의 시뮬레이션 한계라 기존 GUI 테스트 (`gui_step17`, `gui_step25` 통과) 로 대신.
- look_compare 는 1.0 만 (step 142 와 같은 기준); 1.25 는 하지 않았다.
