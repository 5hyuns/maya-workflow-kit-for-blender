# Step 41 — 비교 기준 정확화 (같은 장면·렌더 픽셀 ΔE·영역 사각형)

backlog 1 (`docs/PLAN.md` 「Maya 동일화 계획」). 이후 외형 단계 (42–52) 의 검증 도구.

## 계획 (delegated)

카메라 (행렬 수학이라 먼저 적음):
- Maya persp = 35 mm 렌즈, 수평 조리개 36 mm (1.417 in), Fill 맞춤 → 뷰가 필름보다 넓으므로 수평 맞춤, 수평 FOV
  2·atan(18/35) = 54.43° [K]. GL 뷰 = modelPanel4 (`_maya_ui_dump.json` [315,133,1001,651]) − 패널 메뉴바·아이콘 바 39 px
  = [315,172,1001,612]. → Maya 픽셀 초점거리 f_px = 500.5 / tan(27.2°) = **973.2 px**.
- Blender 뷰포트는 넓은 쪽에 tan(fov/2) = 36 / lens (C `BKE_camera_params_compute_viewplane`: 센서 36 mm × zoom 2) →
  f_px = 폭 · lens / 72. kit 뷰 폭이 Maya 와 달라도 **같은 f_px** 를 쓰면 같은 거리에서 같은 픽셀 크기·같은 원근이 된다.
- Maya viewFit 의 거리 공식은 재현하지 않는다. 대신 Maya 샷에서 pCube1 와이어 색 (리드 #43ffa3, 컴포넌트 #64dcff) 픽셀의
  bbox 를 재고, kit 에서 같은 방향 (Maya 눈 (28,21,28) Y-up = Blender (28,−28,21)) · 같은 f_px 로 pCube1 투영 높이가 같아지는
  거리를 이분법으로 푼다. 너비가 따로 맞으면 (높이만 맞췄으므로) FOV·방향 모델이 맞다는 독립 검증이 된다.
- 뷰 중심 = pCube1 bbox 중심 (viewFit 이 맞춘 상자를 가운데 둠: Maya 큐브 중심 (815,482) ≈ GL 뷰 중심 (815,478)).
- `01_layout_empty` 는 템플릿 뷰 그대로 둔다 (사용자가 실제로 보는 화면).

표:
- 픽셀: colors.json `ui_samples` 38 지점마다 kit 대응 지점 — 좌표를 고정하지 않고 **앵커** (영역·리전·상단바·상태바·창·누른 점)
  + 오프셋 (음수 = 오른쪽/아래에서) 으로 적어 레이아웃이 바뀌어도 표가 따라간다 (`tools/look_data.py` KIT_POINTS). kit 에 없는
  요소는 `(None, 이유)` → 표에 "—" 로 남는다 (그것도 발견).
- 사각형: Maya 위젯 geometry 대 kit 앵커, ±10 px. kit 에만 있는 영역도 줄로.
- 크롭: 같은 요소를 두 샷에서 잘라 위아래/나란히.
- 실행: GUI 1회 (샷 + `geometry.json`) + 헤드리스 1회 (표·이미지). Maya 쪽은 이미 있는 자료만 읽는다.

## 한 것

- `tools/look_data.py` (새): 카메라 상수 (`maya_f_px`), `CUBE_FITS`, `KIT_POINTS` (38: 비교 29, kit 에 없음 9), `RECTS` (12 + kit 전용 2),
  `CROPS` (6), 이미지 도우미 (`load_rgb`, `sample`, `colour_bbox`, `maya_cube_bbox`, `resolve`).
- `tools/look_shots.py`: `maya_camera()` (위 계획), Maya 와 같은 상태 (pCube2/3 = ±2 cm, `select pCube2 pCube1` → 리드 pCube1,
  면 f[1] f[4], 정점 vtx[0:2], 엣지 e[0] e[5]), Create 메뉴는 Maya 처럼 **상단 메뉴바의 Create 클릭**으로 연다 (전에는 커서 위치
  팝업), 샷마다 앵커 사각형, 맞춘 샷은 pCube1 투영 bbox·f_px·lens 를 `geometry.json` 에 기록.
- `tools/look_compare.py`: `pixels.md`, `rects.md`, `scene.md`, `crop_*.png` 추가; ΔE 는 `de2000_lab` 로 분리 (테스트용).
- `tests/test_step41_look_tools.py`: CIEDE2000 Sharma 기준쌍 3개, 앵커 해석, Maya 카메라 상수, 표 모양, 색 bbox/샘플.

## 검증

- `python tools/look_compare.py`: GUI 1회 + 헤드리스 1회 (+ 빌드·설치), 약 31 초. 출력:
  - `scene.md`: **3/3** — pCube1 화면 크기 02 / 04 / 07 모두 Δw −1.3 %, Δh 0.0 % (Maya 180×189 / 182×191 px, kit 178×189 / 180×191),
    kit f_px 973.2 = Maya. 높이만 맞췄는데 너비도 1.3 % 안 → 방향·FOV 모델 확인.
  - `pixels.md`: 비교 29 중 ΔE00 > 5 **9**, kit 에 없는 요소 **9** (셸프 탭 3, Outliner 도크 제목, INPUTS 행, Layer Editor 탭,
    Range Slider 막대·손잡이, Command 결과 필드).
  - `rects.md`: Maya 요소 12 중 ±10 px **1** (메뉴바) + kit 전용 영역 2 (오른쪽 Blender Outliner, Properties).
  - 크롭 6장, 나란히 15장 — 02·04·12·13·14 와 크롭 CB·셸프를 직접 열어 확인.
- 헤드리스 `python tests/run.py`: **344/344** (38 파일, 새 테스트 5). `src/` 변경 없음 → GUI 테스트·dogfood 는 돌리지 않음.

## 발견 (다음 단계 입력)

| 발견 | 근거 | 단계 |
|---|---|---|
| 템플릿 뷰 렌즈 50 = 수평 FOV 71.5°, Maya persp 54.4° (Blender lens ≈ 70 이 같은 각). 새 장면이 Maya 보다 광각 | 계획의 공식, `make_startup.maya_views` 가 lens 를 안 정함 | 45 (뷰 가구) 또는 43 |
| 3D 뷰 헤더·툴 헤더가 투명이라 그라디언트가 비침 (#575d64, #7f93a6; Maya #444444) | pixels.md panel_menu_bar_bg / panel_toolbar_bg | 43 |
| 툴바에 패널 배경 없음 (뷰 위에 떠 있음, #1c1c1d; Maya 툴박스 #444444) | pixels.md toolbox_bg | 47 (레이아웃) |
| Outliner 선택 행 = 밝은 파랑 #6b9dc0 (`outliner.active`), Maya #5285a6; 편집 모드에서도 그대로 (Maya 는 #414d5a 로 어두워짐) | pixels.md outliner_row_selected* | 43 |
| 영역 경계선 #161616 이 보임 (Maya 는 뷰 테두리가 배경색) | pixels.md viewport_border | 43/44 |
| Layer Editor 목록 바탕 = 패널 회색 (Maya 목록 #2a2a2a), 사이드바 탭 띠 #181818 (Maya #373737) | pixels.md | 48 (CB 크롬) |
| Status Line / Shelf 가 1321 px 까지만 (오른쪽 Blender 열 때문), 셸프 높이 32 (Maya 64) | rects.md | 47, 49 |
| 4분할 직교 뷰 라벨이 Blender 그리드 단위 글자 ("Meters × 0.01") — 장면 문제가 아니라 텍스트 오버레이 | compare/16 | 45 |

## 남은 것

- KIT_POINTS 의 오프셋은 step 41 레이아웃에서 고른 값: 레이아웃 단계 (47) 에서 앵커가 바뀌면 표에 "anchor not found" 가 뜨므로
  그때 다시 고른다.
- Maya 쪽 그리드·뷰 배경 픽셀 지점은 colors.json 에 그대로 (다시 찍을 필요 없음). Maya 재촬영 절차는 step_40.md 「남은 것」.
