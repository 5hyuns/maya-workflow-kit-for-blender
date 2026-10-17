# HANDOFF

## 현재 작업

- Step 53 (Blender 5.x 호환·안전한 설치) 완료 — `docs/steps/step_53.md`. 대상 4.5 그대로, 매니페스트 `blender_version_max = "5.3.0"`.
  5.2.2 에서 처음엔 켜기 실패 (Timeline = Dope Sheet 모드) → 얇은 버전 분기 (time_slider, theme `_rna_xml` + MOVED, keymap STRICT/DRIFT,
  select_loops, 5.x 타임라인 버튼 위치). 헤드리스 4.5 / 5.0.1 / 5.1.2 / 5.2.2 모두 414/414, GUI 4.5 337/337 · 336/336, 5.2 337/337,
  다른 에디터 GUI 9/9 (두 버전), release_check: 설치가 사용자 애드온·테마·설정을 지키고 kit 을 끄면 전부 원래대로 (8 단언, 4.5·5.2),
  dogfood 47/47.
- Step 52 (핫박스·RMB 충실도) 완료 — `docs/steps/step_52.md`. 핫박스 = Maya 8 줄 (공통 + Cache/Help, 패널 메뉴, Recent | Maya | Controls,
  메뉴 세트 5 줄, Show All 기본), 대각 영역선, 영역 이름·어둡게 하기 없음; 마킹 메뉴·핫박스가 창 전체에 그려짐 (사이드바·타임라인 위);
  RMB 목록 = Maya 2022 순서 (「pCube1...」 → AE, Select All/Deselect All/Invert, Select Similar □, 회색 ▸ 9 개), 링 아래 (넘치면 열 나눔);
  버그: Segoe UI 에 ▸ 가 없어 목록 폭이 수백만 px (step 41 부터) → 화살표 삼각형. 헤드리스 407/407, GUI 328/328 · 327/327,
  픽셀 ΔE>5 5/31 (메뉴 3 지점 0.3), dogfood 47/47, release_check PASS.
- Step 51 (메뉴 옵션 박스·셸프 줄) 완료 — `docs/steps/step_51.md`. Maya 옵션 박스 494 항목 = 창 아이콘 + 길게 누르기 「Option Box」
  (같은 줄 두 번째 버튼은 메뉴가 계단처럼 깨짐), 셸프 줄 64 px = 탭 줄 (머리, #373737 로 어둡게) + kit 제작 32 px 컬러 아이콘 줄
  (`ui/shelf_icons.py`, 이미지 편집기 POST_PIXEL + 기즈모 풀 고르기). 헤드리스 398/398, GUI 314/314 (0.8) · 313/313 (1.25),
  look_compare density 6/6 (셸프 64, 아이콘 32), rects 5/12, 셸프 픽셀 4 지점 ΔE ≤ 2.4, dogfood 47/47, release_check PASS.
  후속: Status Line 그룹 접기 손잡이 (Maya openBar, `maya_kit.status_group`) — 헤드리스 399/399, GUI 316/316 · 315/315.
- Step 50 (에디터 크롬) 완료 — `docs/steps/step_50.md`. Channel Box: 패널 머리·톱니 대신 메뉴 줄 Channels/Edit/Object/Show, 상자 없는
  이름·SHAPES·INPUTS, Maya 빈 선택 문구; Layer Editor: Display/Anim 탭 + Layers/Options/Help; Outliner (Maya 식) 머리 = Display/Show/Help
  + 검색 (`ui/maya_outliner.py`), 눈 열 없음; Time Slider 오른쪽 (타임라인 사이드바) 현재 프레임 + 재생 버튼 8, 헤더 = Maya 순서 Range
  Slider (Blender 메뉴는 오른쪽 끝 설정 메뉴로). 헤드리스 392/392, GUI 309/309 (0.8; 1.25 고친 파일 다시 통과), 픽셀 ΔE>5 7 → 5/28,
  CB 행 16.0 px, dogfood 47/47.
- Step 49 (레이아웃 동등화) 완료 — `docs/steps/step_49.md`. MayaKit = Status Line 줄 / Shelf 줄 (헤더만 있는 두 영역) /
  [툴박스 열 (좁은 3D 뷰, Maya 툴만 그리기 필터, `ui/toolbox.py`) | Outliner 260 | 뷰 + 사이드바 도크 277] / Time Slider + 아래 Range
  Slider (헤더 뒤집음) / Help Line | Command Line 한 줄. 오른쪽 Outliner·Properties 열 없음 (AE = 도크, Render Settings = 새 창).
  사이드바 「Channel Box Dock Only」 (`ui/dock_tabs.py`, Item 의 C 패널은 남음). 생성기 `tools/make_startup.py` 는 이제 GUI Blender
  (헤드리스 area_close/join 불가). 헤드리스 385/385, GUI 307/307 (1.25·0.8), rects 1/12 → 4/12 (x/w 대부분 ✓, y 는 셸프 높이 = step 51).
  미해결 확인: step 42 사고로 사용자 실제 설정에서 node_wrangler 가 켜진 채 (사용자 확인 필요); step 40 의
  `research/scripts/maya_shots/shots.py` 는 화면 영역 캡처라 다시 돌리기 전에 위젯 캡처로 바꿀 것.
- Step 48 (Maya 고유 워크플로우 분석·계획) 완료 — `docs/steps/step_48.md`, `docs/PLAN.md` 「Maya 워크플로우 계획」, 결정 10
  (`docs/user_decisions.md`: 시뮬레이션 스케일 = Maya nucleus spaceScale 1 처럼). Maya 2022 를 실제로 띄워 7 분야 47 단계 기록
  (`research/scripts/maya_workflows/wf.py`, `research/maya/workflows/*.md` + shots, Maya 위젯만 찍음), 분야별 분석 7 개, blindspot 12 건,
  brainstorm (결정 8 개 delegated), 독립 검토 반영 (v2). backlog 14 개 → 단계 54–67 (큐의 49–53 뒤). 버그 수정: bevel exec 너비 Maya 단위.
  헤드리스 375/375, GUI step 18 14/14 (1.0·0.8), dogfood 47/47.
- Step 47 (선택 와이어) 완료 — `docs/steps/step_47.md`. `ui/selection_wire.py`: 선택 오브젝트의 평가된 엣지를 kit 이 직접 그림 (POST_VIEW,
  사용자 셰이더 + 깊이 바이어스, 오브젝트별 numpy 배치 캐시, 테마 리드/선택 색을 선형으로). Blender `show_wire` 는 선택 색을 테마 wire 쪽으로
  최대 19 % 섞어 (실측) 버림 — 그래서 ID 데이터에 아무것도 안 씀 (저장·언두 잔존 0). 템플릿 선택 외곽선 끔. viewport 10/12 (리드 0.2, 흰색 0.0),
  10 만 폴리 프레임 +3–14 %. 헤드리스 374/374, GUI 293/293 (1.0·0.8), dogfood 47/47.
- Step 46 (뷰 가구) 완료 — `docs/steps/step_46.md`. `ui/view_furniture.py`: ViewCube (Python 기즈모, 면 클릭 → view_axis, 평소 0.5,
  4 분할은 마우스가 있던 패널에만), 카메라 라벨 (persp / top −Z / front +Y / side −X, 카메라 이름), 축 삼각 (Blender 축) — Blender 내비 기즈모가
  꺼진 뷰에서; 템플릿은 내비 기즈모·텍스트 정보 끔. HUD 메뉴 Camera Names / View Axis / View Cube = 애드온 환경설정. look_compare
  `furniture.md` 3/3 ±10 px, 텍스트 오버레이 픽셀 0. 헤드리스 369/369, GUI 289/289 (1.0·0.8), dogfood 47/47.
- Step 45 (Maya 그리드) 완료 — `docs/steps/step_45.md`. 자체 GPU 그리드 `ui/maya_grid.py`: ±12 단위, 1 단위마다 1 px, 5 마다 2 px,
  축 2 px, 모두 테마 그리드 회색, 계단선, 깊이 검사. 바닥에만 (4 분할 front/side 는 그리드 없음 = Maya). 뷰별 상태 = Blender 바닥·정사영
  그리드 끔 + `overlay.grid_lines == 0` (delegated). Show > Grid / Display > Grid = `maya_kit.toggle_grid`. 템플릿 뷰 모두 켬.
  look_compare `grid.md`: 그리드선 200 점 ΔE00 0.7, 모서리 4/4 ±1 px. 그리기 0.22–0.27 ms. 헤드리스 362/362, GUI 283/283 (1.0·0.8),
  dogfood 47/47.
- Step 44 (Maya 위젯 감각) 완료 — `docs/steps/step_44.md`. 테마: 모든 위젯 각지고 평평 (roundness 0, shade·엠보스·메뉴 그림자 없음,
  panel_roundness 0). 환경설정 그룹 「Maya Density」 (`view.ui_scale` = 1 / OS 배율, 125 % 화면 → 0.8 = Maya 와 같은 픽셀), 「Maya Font」
  (Windows Segoe UI, 동봉 안 함), 「Aliased Wireframes」 — 백업/복원, Make Blender Maya 가 켬. CB 행 scale_y 0.8 (16 px). GUI 테스트
  `--ui-scale 0.8` + `sim.px()`. look_compare `density.md` 3/3 (메뉴바 26, 메뉴 항목 19.4, CB 행 16.0 px). 면 채움 α 재보정 0.28
  (step 43 기준 샷에 매니퓰레이터가 걸려 있었음). 헤드리스 356/356, GUI 1.0 281/281 · 0.8 281/281, dogfood 47/47.
  미해결 확인 (step 42): 사용자 실제 설정에서 node_wrangler 가 켜진 채 남음 (사용자 확인 필요).
- Step 43 (Maya 테마 v2 색) 완료 — `docs/steps/step_43.md`. 컴포넌트 (하늘색 와이어, 보라/연노랑 정점, 살구색 엣지·면 — 면은 Maya 점묘
  평균에 맞춘 알파), 매니퓰레이터 (Z = 실제로 그려지는 순파랑), Outliner (#373737, 리드 행 파랑, 이름 흰색), 탭, 현재 프레임 회색,
  3D 뷰 헤더·툴바·사이드바 불투명, 템플릿 빨강/초록 그리드 축선 끔, 프리셀렉트 빨강. 새 `viewport.md` (렌더 픽셀 10 요소).
  theme ΔE00 38/38 < 2, viewport 9/10 < 5, 헤드리스 349/349, GUI 281/281, dogfood 47/47.
- Step 42 (켜자마자 Maya) 완료 — `docs/steps/step_42.md`. 템플릿 `userpref.blend` 는 실측 후 기각 (템플릿 안에서 사용자 add-on 목록·테마·
  ui_scale 을 통째로 바꿈). 대신 첫 GUI 시작의 환영 대화상자 → 「Make Blender Maya」 1 번 = 레이아웃 설치·Maya 테마·스플래시 끔·
  다음부터 Maya 레이아웃으로 시작, 「Revert Maya Look」 으로 모두 되돌림 (`first_start.py`, 결정 3 개정 = user_decisions 9). 테마는 옵션 +
  끄면 복원. 버그 수정: 오퍼레이터 안 템플릿 전환이 Blender 를 죽이던 것 (layout_open 포함). kit 시작 화면 그림 `tools/make_splash.py`.
  뷰 배경 단색 #5c5c5c. 헤드리스 348/348, GUI 281/281, dogfood 47/47, look_compare 체크 9/9 (메뉴바·패널·뷰 배경 ΔE 0.0).
  **주의: 실험 중 사용자 실제 userpref.blend 를 덮어쓴 사고 — 3 값은 되돌렸고 node_wrangler 는 켜진 채 (step_42.md 「실측」).**
- Step 41 (비교 기준 정확화) 완료 — `docs/steps/step_41.md`. `tools/look_shots.py` 가 Maya 와 같은 카메라 (Maya f_px 973 px, pCube1 화면
  높이를 Maya 샷에 맞춘 거리)·같은 선택 상태·메뉴바에서 연 Create 메뉴로 찍고, `tools/look_compare.py` 가 `pixels.md` (렌더 픽셀 ΔE,
  kit 지점 = `tools/look_data.py` 앵커 표), `rects.md` (영역 ±10 px), `scene.md` (큐브 크기 ±10 %), `crop_*.png` 6장을 만든다.
  결과: 큐브 3/3 (−1.3 %), 픽셀 29 중 ΔE>5 9 + kit 에 없음 9, 사각형 12 중 1. 헤드리스 344/344.
- Step 40 (Maya 동일화 조사·계획) 완료 — `docs/steps/step_40.md`, `docs/PLAN.md` 「Maya 동일화 계획」. Maya 2022.4 를 팩토리 prefs 로 띄워
  스크린샷 22장 + 실측 색·크기 (`research/maya/colors.json`), kit 비교 도구 `tools/look_compare.py` (+ `look_shots.py`: 나란히 이미지,
  테마 ΔE00), 경쟁 제품 22개 (`research/competitors.md`), blindspot 18건, self-review 반영. 버그 수정: 리드(연두)/다른 선택(흰색)
  색이 반대였음 → ΔE 28.5 → 0. 테마 ΔE00>5 13/31 → 11/31. 헤드리스 339/339. backlog 12개 (`autodrive_bmk/backlog.json`).
- Step 39 (컴포넌트 픽워크 + Alt+Shift 축 고정) 완료 — `docs/steps/step_39.md`. 편집 모드 화살표 = `maya_kit.pick_walk_component`
  (엣지 루프/링, 정점·면은 화면 방향), Alt+Shift+LMB/MMB = `maya_kit.view_axis_lock` (처음 우세한 축으로 텀블/트랙).
  헤드리스 339/339, GUI 281/281, dogfood 47/47. **재점검 3차 backlog 7개 모두 처리 (step 33–39).**
- Step 38 (Channel Box 다중 선택·상대값, AE 재질 라벨) 완료 — `docs/steps/step_38.md`. CB 값 필드 = 텍스트 (Maya 숫자 표시,
  `+=5`/`*=2`, 모든 선택·고른 채널 모두), 사용자 속성/SHAPES/INPUTS 도 같은 이름 채널에 적용 (`Scene.maya_kit_cb.rows`),
  재질 `maya_kit_type` → AE `lambert: lambert1` + lambert/blinn/phong/surfaceShader 섹션. 헤드리스 333/333, GUI 277/277, dogfood 47/47.
  재점검 3차 backlog 7개 중 1–6 처리.
- Step 37 (뷰 패널 메뉴 바) 완료 — `docs/steps/step_37.md`. 3D 뷰 헤더 메뉴 = Maya View/Shading/Lighting/Show/Renderer/Panels
  (`ui/panel_menus.py`, `VIEW3D_MT_editor_menus.draw_collapsible` 덮어쓰기, Blender 메뉴는 「Blender ▸」, 환경설정 Panel Menus).
  매핑 67 / 회색 51. 헤드리스 322/322, GUI 272/272, dogfood 47/47. 재점검 3차 backlog 7개 중 1–5 처리.
- Step 36 (대칭 Symmetry) 완료 — `docs/steps/step_36.md`. 전역 Maya 대칭 상태 `Scene.maya_kit_symmetry` → 메시 `use_mirror_*`
  (`operators/symmetry.py`, 편집 모드 진입 시 적용 + 헤더 미러 버튼 역반영), Status Line 대칭 그룹 (토글 + ▾ Off/Object/World/Topology),
  Tool Settings 「Symmetry Settings」, W/E/R 홀드 N Symmetry ▸. 헤드리스 312/312, GUI 267/267, dogfood 47/47.
  재점검 3차 backlog (`C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_33.json`) 7개 중 1–4 처리.
- Step 35 (Maya 키 묶음) 완료 — `docs/steps/step_35.md`. Ctrl+Alt+LMB 박스 줌, Ctrl+T, Y (마지막 비 QWERT 툴), Ctrl+Shift+X/Q,
  F2–F6 메뉴 세트 (IC 3D 뷰 F2–F5 제거), 3D 뷰 Return 팝오버 제거. 키맵 대응표 구현 95 / 계획 0. 헤드리스 300/300, GUI 261/261, dogfood 47/47.
- Step 34 (메뉴 막다른 길) 완료 — `docs/steps/step_34.md`. `menu_map.CHILDREN` (Maya 가 실행 중에 만드는 하위 메뉴: Windows > ... Editors,
  HUD), 편집기는 새 창 (`maya_kit.open_editor`), Edit > Ungroup, UV Editor/Planar/Normal-Based, HUD Poly Count, Increment and Save
  (Maya 번호 규칙), Export Selection (선택만). 헤드리스 294/294, GUI 251/251, dogfood 47/47.
- Step 33 (메뉴가 화면 안에) 완료 — `docs/steps/step_33.md`. `engine.fit_ring`: 마킹 메뉴 중심(누른 점)은 그대로, 방사 상자는 안으로,
  목록은 링 아래/위/옆으로; 핫박스 행이 위로 넘치면 가운데 상자 아래로. 헤드리스 287/287, GUI 246/246, dogfood 47/47.
- Step 32 (재점검 3차) 완료 — `docs/steps/step_32.md`, `docs/PLAN.md` 「재점검 3차」. 코드(`src/`) 변경 없음. 헤드리스 281/281, dogfood 47/47,
  탐색 세션 15 중 13 (실패: 세션 bmesh 선택 탓 1, 박스 줌 미구현 1). 대응표 33행: 완료 25, 부분 6, 불가 2. 새 발견: RMB 루트 목록이 뷰 아래로 잘림,
  AE 재질 라벨이 모두 standardSurface, 메뉴 막다른 길 (Windows 편집기, UV, Ungroup, HUD, Increment and Save), 대칭 없음.
- Step 31 (레이아웃 다듬기) 완료 — `docs/steps/step_31.md`. MayaKit 템플릿 왼쪽 Outliner 폭 0.2 + 컬렉션 행·렌더 열 숨김 (Maya DAG),
  쿼드 → 단일 때 축 뷰 이름 유지 (`is_orthographic_side_view`), 홀드 메뉴 체크 켜짐 색 강조 + 파이 폴백 체크 아이콘, release 스크린샷 재생성.
  타임라인 프레임 상자 겹침은 C 그리기라 미해결. 헤드리스 281/281, GUI 239/239, dogfood 47/47. backlog.json 8 항목 모두 처리.
- Step 30 (선택 감각) 완료 — `docs/steps/step_30.md`. 편집 모드 박스/라쏘 = 가려진 요소까지 (드래그 동안만 X-Ray 플래그, `operators/marquee.py`),
  정점 모드 + 셀렉트 툴 프리셀렉트 하이라이트 (`operators/preselect.py`, C 기즈모 `GIZMO_GT_mesh_preselect_elem_3d`), 언두 256 단계
  (`prefs_preset.GROUPS["undo"]`, disable 시 복원, `tests/kit.py` 가 prefs.edit 스냅샷). 헤드리스 279/279, GUI 232/232, dogfood 47/47.
- Step 29 (Maya 식 재질 지정) 완료 — `docs/steps/step_29.md`. `operators/material.py`: Lighting/Shading Material Attributes /
  Assign New (검색 팝업, Shift+T) / Favorite ▸ / Existing ▸, RMB 목록 끝 같은 항목 (선택 없으면 커서 아래 오브젝트), 면 선택 모드 = 면에만,
  아니면 오브젝트 전체 (슬롯 1개). 엔진: 목록 하위 메뉴 영역 안으로, 클릭 모드 항목은 버튼을 뗄 때 실행. 헤드리스 274/274, GUI 218/218,
  dogfood 47/47.
- Step 28 (MMB = 마지막 핸들) 완료 — `docs/steps/step_28.md`. 기즈모 LMB 누름 감시 → 등록된 transform 의 제약을 툴별로 기억,
  Tool 키맵 MMB = `maya_kit.manip_mmb` (CB 슬라이더 우선), 같은 툴 키 재탭 = 리셋. 헤드리스 264/264, GUI 206/206, dogfood 47/47.
- Step 27 (매니퓰레이터 크기·뷰 키) 완료 — `docs/steps/step_27.md`. = / Shift+= / - gizmo_size (`prefs_preset.set_runtime`, disable 시 복원),
  PgUp/PgDn 스무스 단계, 0, Home (Maya persp), Alt+5 와이어프레임. 키맵 대응표 구현 87 / 계획 5 (F2–F6). 헤드리스 260/260, GUI 202/202,
  dogfood **47/47**.
- Step 26 (Smart Extrude) 완료 — `docs/steps/step_26.md`. 면/엣지 Shift+기즈모 드래그 = 압출 후 변환, 안 움직이면 (Shift+클릭·취소)
  사본/압출을 되돌림, xform 기즈모만 (`context.gizmo_group`), 홀드 메뉴 체크 상자. 헤드리스 256/256, GUI 195/195, dogfood 46/47.
- Step 25 (cm 그리드와 그리드 스냅) 완료 — `docs/steps/step_25.md`. 원인: Blender 원근 뷰는 1 m 아래 그리드 단계를 건너뜀 →
  `overlay.grid_scale` = 표시 단위의 미터 값 (`units.grid_scale`, 템플릿 0.01, Maya Units 적용/복원). X 스냅 템플릿 9 cm / Maya Units 9 cm /
  팩토리 3 m. 헤드리스 249/249, GUI 187/187, dogfood 46/47.
- Step 24 (컴포넌트 Delete) 완료 — `docs/steps/step_24.md`. 편집 모드 Delete / Backspace = `maya_kit.delete_components` (면 삭제,
  경계 아닌 엣지 dissolve + 정점 정리, 정점 dissolve, 메뉴 없음). Ctrl+Delete = IC dissolve. 헤드리스 246/246, GUI 179/179, dogfood 46/47.
- Step 23 (재점검 2차) 완료 — `docs/steps/step_23.md`, `docs/PLAN.md` 「재점검 2차」. 코드(`src/`) 변경 없음; `tools/dogfood.py --session`.
  헤드리스 239/239, GUI 172/172, dogfood 46/47, 탐색 세션 13 중 12 (면 Delete 가 메뉴), 콘솔 오류 0.
  대응표 33행: 완료 23, 부분 8, 미착수 0, 불가 2 (1차 21/8/2/2). 키맵 468행: 구현 79 + IC 6, 계획 13, 미검토 292.
  새 발견: 컴포넌트 Delete, cm 템플릿 그리드 안 보임 + X 스냅 0 cm, Outliner 이름 잘림; blindspot 8건 (MMB 마지막 핸들, 재질 지정 등).
- Step 22 (매니퓰레이터 Shift+드래그 = Smart Duplicate) 완료 — `docs/steps/step_22.md`. Maya 키컨피그의 기즈모 키맵
  (`Generic Gizmo Maybe Drag` / `Drag`) 맨 앞 Shift+LMB PRESS → `maya_kit.manip_duplicate` (복제 후 PASS_THROUGH → 기즈모가 사본 변환).
  Shift 정밀은 그대로 (실측: 누른 채 시작한 드래그는 정밀 아님). W/E/R 홀드 메뉴 Smart Duplicate = 환경설정 토글.
  헤드리스 239/239, GUI 172/172, dogfood 47 중 46 (남은 실패: `=`).
- Step 21 (생성 경로 단위 통일) 완료 — `docs/steps/step_21.md`, 결정 8 (`docs/user_decisions.md`). Maya 길이 1 = 씬 표시 단위 1
  (`operators/units.maya_unit()`): Create/셸프/메뉴/마킹 메뉴/핫박스/Ctrl+G/`cmds` 가 같은 크기, Maya FBX 임포트 크기와도 같음.
  MayaKit 템플릿 pCube1 = 0.01 BU = "1 cm", 템플릿 3D 뷰 = Maya persp (28, 21, 28 cm) + 클립 0.1 / 10000 cm; Maya Units 켬 = 1 BU = "1 cm".
  헤드리스 235/235, GUI 162/162, dogfood 47 중 46 (남은 실패: `=`).
- Step 20 (타임라인) 완료 — `docs/steps/step_20.md`. `.` `,` = 다음/이전 키, Alt+`.` Alt+`,` = 프레임 (Frames 키맵, 3D View 피벗/방향 파이 제거),
  타임라인 헤더 = Maya Time Slider 버튼 + Range Slider 4 필드, 타임라인 뷰가 재생 범위를 따라감, MayaKit 템플릿 애니메이션 1–200 / 재생 1–120.
  헤드리스 227/227, GUI 156/156, dogfood 47 중 46 (남은 실패: `=`).
- Step 19 (복제 이름) 완료 — `docs/steps/step_19.md`. Ctrl+D = `maya_kit.duplicate` (제자리, 하위 계층, pCube2 / pCubeShape2, group1 → group2,
  Shift+D 스마트 반복과 연결); 메뉴 Edit > Duplicate 도 같음. 헤드리스 223/223, GUI 147/147, dogfood 45 중 43 (남은 실패: `.`, `=`).
- Step 18 (편집 모드 키) 완료 — `docs/steps/step_18.md`. Mesh: D = 컴포넌트 피벗 홀드(3D 커서, 놓으면 유지 / 탭 = 리셋),
  Ctrl+Shift+A 전체 선택, Alt+D 해제 + 오브젝트 모드, Ctrl+E 즉시 압출, Ctrl+B 즉시 베벨(정점 모드 = 정점), Shift+> / < 확장·축소,
  Ctrl+F9–F11 닿는 요소로 변환 (`maya_kit.convert_selection`). 헤드리스 218/218, GUI 147/147, dogfood 45 중 42 (남은 실패: Ctrl+D 이름, `.`, `=`).
- Step 17 (Maya 프레이밍 여백 + 핫박스 잘림) 완료 — `docs/steps/step_17.md`. F/A/Shift+F/Shift+A/Ctrl+Shift+F 가 보이는 영역(사이드바·툴바·
  투명 헤더 제외)의 0.95 에 경계 상자를 맞춤 (`operators/framing.py`, `maya_kit.frame`); 핫박스 행은 보이는 영역 안으로 밀고 긴 행은 줄바꿈.
  헤드리스 211/211, GUI 133/133, dogfood 45 중 41 (남은 실패: Ctrl+D 이름, `.`, `=`, Shift+>).
- Step 16 (언두·가시성·아이솔레이트 키) 완료 — `docs/steps/step_16.md`. z/Shift+Z/Ctrl+Y (Screen, border 4개 제거), h·Ctrl+H·Alt+H·
  Shift+H·Ctrl+Shift+H (`maya_kit.visibility`, 오브젝트 모드; Mesh 는 hide/reveal), Ctrl+1 아이솔레이트(카메라 고정), Ctrl+Shift+I 반전.
  헤드리스 203/203, GUI 127/127, dogfood 45 중 41 (남은 실패: Ctrl+D 이름, `.`, `=`, Shift+>). 키맵 대응표 구현 51→63.
- Step 15 (스무스 프리뷰 = 표시 전용) 완료 — `docs/steps/step_15.md`. 3 이 Set Shade Smooth 노드 모디파이어 + 프리뷰 Subsurf(마지막)로
  매끈하게 보이고 메시 데이터는 그대로; Delete History 는 프리뷰를 굽지 않음; 1/2/3 은 사용자 Subsurf 를 건드리지 않음; INPUTS/AE 탭에서 숨김.
  헤드리스 196/196, GUI 115/115, dogfood 45 중 37 통과 (실패 8 = backlog 2·5 의 키·이름).
- Step 14 (재점검 1차) 완료 — `docs/steps/step_14.md`, `docs/PLAN.md` 「재점검 1차」. 코드(`src/`) 변경 없음.
  헤드리스 188/188, GUI 115/115. 새 도구 `tools/dogfood.py` (깨끗한 설치 + Maya 사용자 첫 세션 이벤트 재생):
  체크 43개 중 35 통과, 실패 8 = 아직 없는 Maya 키(z, Shift+Z, h, Ctrl+1, `.`, `=`, Shift+>) + Ctrl+D 이름 `pCube1.001`; 콘솔 오류 0.
- 구현률 (research 대응표 33행): 완료 21, 부분 8, 미착수 2, 불가 2. 키맵 468행: 구현 51 + IC 8, 계획 26, 미검토 306.
- 발견: PLAN 8행(M1-d 나머지 키 25개)이 번호 변경 때 빠져 미구현; blindspot 14건 (Delete History 가 스무스 프리뷰를 구움,
  생성 경로 단위 100배 차이, 편집 모드 D/Ctrl+Shift+A 충돌, Shift+매니퓰레이터 복제 미계획 등).
- Step 13 (통합·배포) 완료 — release 0.1.0 (`c0f37b0`).

## 바로 다음 할 일

- 드라이버 큐 순서: backlog.json 의 Maya 워크플로우 54–67 (PLAN 「Maya 워크플로우 계획」 표: 54 기반 (단위·안내),
  55 포즈 본 CB, 56 Time Slider·키, 57 Joint Tool, 58 IK·스킨, 59 SDK·제약, 60 MTK, 61 Target Weld, 62 Extrude/In-View, 63 UV, 64 Hypershade,
  65 FX, 66 씬 관리, 67 Graph Editor). 각 단계 근거 = `research/maya/workflows/<분야>.md` (research/ 는 추적 안 함 — 지우지 말 것).
- Maya 를 다시 띄울 때: `research/scripts/maya_workflows/launch.ps1` (스크린샷은 Maya 위젯만; 화면 영역 캡처 금지 — step 48 사고).
- 검증은 `python tools/look_compare.py` (`delta_e.md`, `pixels.md`, `viewport.md`, `rects.md`, `density.md`, `grid.md`, `furniture.md`); 샷은 Maya 밀도 (실효 배율 1.0)
  로 찍힌다. GUI 테스트는 두 배율로: `python tests/gui/run.py` 와 `--ui-scale 0.8` (새 고정 픽셀 좌표는 `sim.px()`).
- Blender 를 손으로 띄울 때는 `BLENDER_USER_*` 폴더를 먼저 만들 것 (CLAUDE.md, step 42 사고).
- 외형 검증: `python tools/look_compare.py` (Maya 자료 다시 찍기: `research/scripts/maya_shots/launch.ps1` → `mayapy research/scripts/maya_colors.py`).
- 이전 남은 항목: step_36–39 「남은 것」, PLAN 「재점검 3차」 8–9, step_49 「남은 것」 (Item 탭, AE 460), step_51 「남은 것」 (다른 배율의 셸프 줄 높이, Status Line 아이콘은 Blender 것), step_50 「남은 것」 (Outliner 카메라 행, 목록 바탕색).
