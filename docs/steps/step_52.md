# Step 52 — 핫박스·RMB 마킹 메뉴 충실도 (불렀을 때 보이는 것)

backlog 11 (`docs/PLAN.md` 「Maya 동일화 계획」 표 「Hotbox / RMB menu」, step_40.md blindspot 14).
근거: `research/maya/screens/13_hotbox.png`, `14_marking_menu_object.png` (compare/13·14 = Maya | kit),
`research/maya/marking_menus.json` (`hotbox` = HotboxMenus.mel:26-245, `menus.dagMenuProc` = dagMenuProc.mel:2582-2847).

## 계획

### 실측 (Maya 13·14 번 화면, 실효 배율 1.0 픽셀)
- 핫박스 = 커서 줄 (Recent Commands | **Maya** | Hotbox Controls, 따로 떨어진 상자 셋, Maya 상자 62×26) + 위 2 줄 (공통 메뉴
  File … Windows Cache Help / 패널 메뉴 View Shading Lighting Show Renderer Panels) + 아래 5 줄 (Modeling, Rigging, Animation, FX,
  Rendering 메뉴 세트). 줄 간격 35 px (상자 26 + 틈 9), 줄마다 가운데 정렬된 한 띠. 메뉴 세트 줄 = 모든 세트 (Hotbox Controls
  기본 Show All). MASH 는 플러그인 메뉴 (kit 데이터 없음).
- 영역선: 대각선 4 개 짧은 선 (각 축 28 px), 위 두 개는 맨 위 줄 바로 위, 아래 두 개는 맨 아래 줄 아래. 영역 이름 글자는 없음.
- RMB (오브젝트 위): 링 아래 가운데에 목록 (178 px 폭, 링 중심 아래 87 px 에서 시작), 첫 줄 `pCube1...` (= showEditor), 그다음
  Select / Select All / Deselect All / Select Hierarchy / Invert Selection | Select Similar □ | Make Live | DG Traversal ▸ / Inputs ▸ /
  Outputs ▸ / Paint ▸ / Metadata ▸ / Actions ▸ / UV Sets ▸ / Color Sets ▸ / Time Editor ▸ | Material Attributes... | Assign New
  Material... / Assign Favorite Material ▸ / Assign Existing Material ▸ (dagMenuProc.mel:2582-2764). Maya 목록은 뷰를 넘어 화면 아래로
  내려감 (Time Editor 가 잘림) — Maya 의 메뉴는 패널이 아니라 창 위에 그려짐.
- kit (지금): 핫박스 = 현재 세트만, 가운데 「Maya Kit · Modeling」, 영역 이름 글자, 줄이 사이드바 (Channel Box 도크) 를 피하려고
  접힘; RMB 목록 = 다른 항목, 뷰 폭 전체로 그려지고 링 아래가 아님.

### 결정 (delegated)
1. **창 전체 오버레이**: Maya 의 핫박스·마킹 메뉴는 패널이 아니라 창 위에 뜬다. `marking/draw.py` 의 그리기 처리기를 편집기 종류 ×
   영역 종류 (WINDOW, UI, TOOLS, HEADER, TOOL_HEADER) 로 늘리고, 같은 창의 모든 영역이 연 영역 기준 좌표를 자기 위치만큼 옮겨
   그린다 (각 영역이 자기 사각형에서 잘림 = 이어 붙여 보임). 그래서 사이드바·툴바·옆 편집기 위에도 그려짐. 모달은 원래 영역
   좌표 (영역 밖이면 음수/폭 초과) 로 그대로 판정. `bounds` = 창의 화면 영역들 (위·아래 전역 줄 제외) 을 연 영역 좌표로.
   어둡게 하기 (DIM) 는 연 영역에만.
2. **핫박스 줄 = Maya**: `engine.HotboxLayout(rows, …, below=…, side=…)` — `rows` (위, 위→아래), `side` = (왼쪽, 오른쪽) 커서 줄
   상자, `below` (아래, 위→아래). 크기 = Maya (줄 간격 35 = 상자 26 + 틈 9, 실효 배율 1.0 기준; 줄은 한 띠, 메뉴 이름마다 칸).
   `modal.hotbox_rows` = 공통 + Cache/Help, 패널 메뉴 (`panel_menus.BAR`, 3D View 에서만), 메뉴 세트 줄. 「Show All Menu Sets」 기본
   켬 (Maya 기본). 가운데 라벨 「Maya」. 영역 이름 글자 빼고 대각선 4 개 (`HotboxLayout.zone_lines`). 위로 넘치면 위 줄들을 아래 줄
   밑으로, 아래로 넘치면 아래 줄들을 위 줄 위로 (그래도 안 되면 밀어 넣기).
3. **RMB 목록 = 2022 화면**: `menus.RMB_MESH` 목록을 위 순서로. `<object>...` 첫 줄 = 커서 아래 오브젝트 이름 (`menus.OBJECT_TITLE`,
   모달이 세션 전에 이름을 넣은 사본을 만듦) → `maya_kit.object_attributes` (AE 도크에 그 오브젝트). Select All / Deselect All /
   Invert Selection = `object.select_all`, Select Similar □ = `object.select_grouped(type=TYPE)` (옵션 박스 = Adjust Last Operation),
   Paint ▸ = Paint Skin Weights, Make Live / DG Traversal / Inputs / Outputs / Metadata / Actions / UV Sets / Color Sets / Time Editor =
   회색 (빈 `Sub` = 회색 ▸; Blender 대응 없음 또는 Maya 노드 그래프 전용). 커브 목록도 같은 앞부분.
4. **목록은 링 아래** (Maya): 창 전체 bounds 로 대부분 들어감. 아래로 다 안 들어가면 링 아래에 열을 나눠 (넘치는 줄이 오른쪽 열로)
   — Maya 처럼 잘리지 않고 모든 항목에 닿음. 링 아래에 한 줄도 안 들어갈 때만 예전 위/옆 규칙 (step 33).
5. 파이 대체 (Blender Pies) 는 같은 데이터: 빈 `Sub` 는 회색 항목.
6. 검증: 헤드리스 = 핫박스 줄 수·줄별 메뉴 이름이 Maya 13 번 줄과 같음 (MASH 제외), 가운데 「Maya」, 영역선 4 개; RMB 목록 순서 =
   14 번 화면 목록 (`test_step8` 확장), 열 나눔·링 아래 엔진 단언; GUI = 핫박스·RMB 를 연 상태에서 목록 사각형이 링 아래, 줄이
   사이드바 위에도 그려짐 (스크린샷); look_compare 13·14 다시.

### 실측 (구현 중)
- **RMB 목록이 뷰 폭 전체로 그려지던 원인**: 「Maya Font」 (Segoe UI) 에 「▸」 글리프가 없어 `blf.dimensions` 가 약 5 000 000 px 를
  돌려줌 (look_shots 실측) → 하위 메뉴 항목이 있는 목록 폭이 터짐 (step 41 부터의 kit 14 번 화면). 화살표는 이제 글리프가 아니라
  그린 삼각형 (`draw.ARROW`, 폭 = 글꼴 크기 × 0.9).
- 핫박스 줄 색이 kit 뷰 회색과 같아 안 보였음 → Maya 값으로: 어둡게 하기 없음, 줄 = #444444 70 % (Maya #5c5c5c 뷰 위 #4c4c4c,
  colors.json hotbox_row_bg), 메뉴 상자·목록 = #525252 (marking_menu_box / marking_menu_list_bg). 3D 뷰 POST_PIXEL 은 선형 공간에서
  섞이지만 이 값들은 Maya 픽셀과 맞음 (ΔE 0.3).
- 창 전체 오버레이: 같은 창의 영역마다 그리기 처리기 (`draw.COVER_SPACES` × `REGION_TYPES`) 가 연 영역 기준 좌표를 자기 위치만큼
  옮겨 그림 → 목록이 타임라인 위로, 핫박스 줄이 Channel Box 도크 위로 이어짐 (스크린샷).

## 한 것
- `marking/engine.py`: `HotboxLayout` = Maya 배치 (위 줄 `rows`, 커서 줄 `side`, 아래 줄 `below`, 줄 간격 35 = 26 + 9, 줄마다 한 띠
  `bands`, 가운데 상자 = 제목 + 여백, 대각 영역선 `zone_lines`, 위/아래로 넘치면 반대쪽으로 옮김). `fit_ring`: 링 아래에 다 안
  들어가면 링 아래에서 열을 나눔 (`_columns`, 최소 4 줄). 빈 `Sub` = 회색.
- `marking/menus.py`: RMB 목록 = Maya 2022 순서 (`_object_items`, 메시·커브 공통), `OBJECT_TITLE` → `with_object_name`, `unavailable()`
  / `is_unavailable()`, Select Similar 옵션 박스.
- `marking/modal.py`: `hotbox_rows` = (공통 + Cache/Help, 패널 메뉴 (3D 뷰), 옆 상자, 모든 메뉴 세트 줄); 제목 「Maya」; bounds =
  `draw.window_bounds`; 세션 전에 오브젝트 이름을 넣음; `poll_action` 빈 Sub = 회색.
- `marking/draw.py`: 창 전체 오버레이 (`activate`, `window_bounds`, `redraw`, 영역마다 이동해 그림), Maya 색, 목록 = 열마다 한 몸통 +
  구분선, 하위 메뉴 화살표 삼각형, 영역 이름 글자·어둡게 하기 제거.
- `ui/attribute_editor.py`: `maya_kit.object_attributes` (RMB 「pCube1...」 = AE 도크에 그 오브젝트). 파이 대체: 제목 줄 이름, 회색 하위 메뉴.
- 환경설정 「Show All Menu Sets」 기본 켬 (Maya 기본, delegated).
- 테스트: 새 `test_step52_hotbox_rmb` (8), `gui_step52_hotbox_rmb` (12); test_step8 (파이 순서에 제목 줄), test_step9 (줄 형식, 처리기 수),
  gui_step17·33 (경계 = 창). look_data 핫박스·마킹 메뉴 지점 다시 고름.

## 검증
- 헤드리스 **407/407** (step 51: 399). 핫박스 줄 = Maya 13 번 화면 8 줄 (MASH 플러그인 제외), 줄 간격 35, 「Maya」, 대각선 4 개,
  가장자리에서도 창 안·가운데 상자와 안 겹침; RMB 목록 순서 = 14 번 화면 21 줄 + 재질 4 줄; 목록이 링 아래 (열 나눔 포함);
  ▸ 너비 회귀 테스트. `test_enable_disable` 누수 0.
- GUI 전체 **328/328** (0.8) · **327/327** (1.25). gui_step52: 핫박스 8 줄이 Channel Box 도크 위로 이어짐, RMB 「pCube1...」 + 2022 순서,
  목록 사각형이 링 아래·가운데.
- look_compare: 픽셀 ΔE>5 **5/31** — marking_menu_box 0.3 (전 3.5), marking_menu_list_bg 0.3 (전 22.9), hotbox_row_bg 0.3; 13·14 번
  나란히 화면 직접 확인. release_check PASS (스크린샷 03·04 재생성), dogfood 47/47 (콘솔 오류 0).

## 남은 것
- Maya 목록은 화면 밖까지 한 열로 내려가며 잘림; kit 은 링 아래에서 열을 나눔 (모든 항목에 닿게, delegated).
- 회색 항목: Make Live, DG Traversal, Inputs, Outputs, Metadata, Actions, UV Sets, Color Sets, Time Editor (Inputs = 모디파이어 목록,
  UV Sets = UV 맵 목록 같은 동적 하위 메뉴는 나중에). Maya 의 조건부 항목 (Scene Assembly, Remove Material Override, 레퍼런스, Custom ▸)
  없음.
- 영역선 위치는 화면에서 잰 근삿값 (줄 끝 + 20 px, 길이 28 px); Maya 의 아래 선은 조금 더 멀리 있음.
- 핫박스 줄에 MASH 등 플러그인 메뉴 없음 (kit 데이터 없음). 핫박스가 다른 창 (떼어낸 창) 으로는 넘어가지 않음.
- 수동 확인: `docs/manual_checks.md` 「Step 52」.
