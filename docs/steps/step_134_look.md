# Step 134 — 레인 LOOK: look_compare 를 지금 레이아웃에 맞춤 (#75)

`tools/look_compare.py` / `look_data.py` / `look_shots.py` / `look_second_start.py` 를 step 113 (헤더 없는 셸프 행), step 116
(Maya 도크 = Properties 영역), step 130 (app template · 테마 없음, Maya 레이아웃 = 번들 startup.blend) 에 맞췄다. Maya 쪽
(`research/maya/screens/*`, `colors.json`, `_maya_ui_dump.json`) 은 그대로. `src/` 는 건드리지 않았다.

## 방법

- 빌드 → `tmp/look_env_<tag>` 샌드박스 (`release_check.sandbox_env`, `BLENDER_USER_*` 를 먼저 만듦) → GUI Blender 1600x900 에서
  `look_shots.py` (환영 대화상자 Return = 「Make Blender feel like Maya」 → Maya 레이아웃 새 파일), 두 번째 시작
  `look_second_start.py`, 그 다음 `blender -b` 에서 표 계산.
- 두 배율: `ALLSET_GUI_UI_SCALE=0.8 ALLSET_LOOK_TAG=step134_s100` (이 125 % PC 에서 effective 1.0) 와
  `ALLSET_LOOK_TAG=step134_s125` (effective 1.25). 결과 `research/maya/screens/compare_step134_s100/`, `compare_step134_s125/`
  (side-by-side 15 장, crop 6 장, `marks_<shot>.png`, `*.md`, `summary.md`), 로그 `tmp/look134_s100.txt` / `tmp/look134_s125.txt`
  (worktree 의 tmp).
- worktree 에는 research/ 가 없으므로 `look_data.RESEARCH` 가 `ALLSET_RESEARCH` → 이 checkout → 가장 가까운 상위 폴더 순으로
  research/ 를 찾는다 (worktree 는 메인 checkout 의 research 를 읽고 그 안에 결과를 쓴다).

## 고친 것

- **검사 (FAIL 4 개 → 0)**: app template · splash 검사를 뺐다 (step 130: 템플릿 없음, 환경설정을 쓰지 않으므로 splash 는 Blender
  것). 대신 「Return → Maya 모드 켜짐」, 「Maya 레이아웃 = 제목 없는 새 파일」 (`switch.is_maya_workspace`), 두 번째 시작에서
  「Maya 모드 유지」 + 「Maya 레이아웃 새 파일」 (`first_start` load_post) + 「환영 대화상자 다시 없음」. 결과 줄 `checks: 9/9 pass`.
- **anchor**: `dock` = `maya_dock.role` 이 STACK / CHANNEL_BOX 인 Properties 영역, `tooldock` = Tool Settings (`tool_dock.is_dock`),
  `shelf.tabs` / `shelf.icons` = 헤더 없는 셸프 WINDOW 의 위 `TAB_PX` × 배율 / 나머지, `gap.outliner_view` = Outliner 와 뷰
  사이 틈. `view3d.UI` / `shelf.HEADER` 를 쓰는 곳 없음 (`tests/test_step41_look_tools.py` 가 확인). RECTS / CROPS 의 CB/LE =
  `dock`, KIT_ONLY 에서 `view3d.TOOL_HEADER` (step 113 부터 Maya 패널 툴바 = modelPanel4 의 일부) 를 빼고 `tooldock`, `view3d.UI` 추가.
- **오프셋 단위 (delegated)**: KIT_POINTS 의 int = effective 1.0 픽셀, 샷의 배율 (`geometry.json` `ui_scale`) 을 곱함; (-1, 1) 사이
  float = anchor 크기의 비율 (영역 크기를 따르는 것: 타임라인 눈금, 왼쪽 / 오른쪽 정렬 항목 사이 빈칸, 너비가 배율을 따르지 않는
  도크의 탭). 모든 점을 1.0 샷에서 다시 골라 `marks_<shot>.png` 로 1.0 / 1.25 둘 다 눈으로 확인했다.
- **출처 분류 (delegated)**: `look_data.KIT_DRAWN` = 킷이 자기 색으로 그리는 것 / 레이아웃 파일이 정하는 것 — viewport_bg (레이아웃
  파일), Range Slider 막대 · 손잡이 (`ui/range_bar.py`), 마킹 메뉴 상자 · 목록 · 핫박스 행 (`marking/draw.py`). 나머지는
  **theme** (Blender 테마 색; 셸프 줄 색도 테마의 Image Editor 헤더 색에서 계산 — `ui/shelf.py`): ΔE00 은 표에 남기되 「다름」
  으로 세지 않는다.
- **밀도 (delegated)**: kit px ÷ 샷 배율로 판정 (Maya 도 125 % 면 위젯이 커진다). 표에는 kit px 와 나눈 값을 둘 다 적음. 셸프
  아이콘 크기는 `shelf.icon_rect` 로 샷 때 기록 (예전 `shelf.WINDOW` 높이 − 4 는 헤더 없는 행에서 의미 없음).
- **ViewCube 찾기**: 사이드바가 비어 3D View 오른쪽 끝에 사이드바 토글 화살표가 보여 상자가 오른쪽 끝까지 늘어났다 → 검색
  상자 오른쪽 14 px 제외 (Maya 큐브는 오른쪽에서 26 px 안쪽).
- 1.25 샷에 셸프 툴팁 (「Freeze Transformations」) 이 남아 3D View 헤더를 가렸다: fit 때 마우스를 셸프 행 가운데 아래가 아니라 왼쪽
  끝에 둔다.
- 섹션마다 한 줄 요약 (`look_compare: <section>: ...`, `summary.md` 에도), 결과 점 확인용 `marks_<shot>.png`.

## 수치 (today's master + 이 레인, 다른 레인 병합 전)

| 섹션 | effective 1.0 | effective 1.25 |
|---|---|---|
| checks | 9/9 | 9/9 |
| pixels | kit-drawn **6/6** ΔE00 < 5; theme 30 (> 5: 20); 킷에 없음 2; anchor 없음 **0** | 같음 |
| viewport | 1/12 (조작기 X 빨강만) | 1/12 |
| rects | 5/12 (Status Line, Shelf, Menu bar, Help Line, Command Line) | 3/12 (Menu bar, Status Line, Range Slider) |
| scene | 3/3 | 3/3 |
| density (÷ 배율) | 5/6 — 메뉴 바 26.0/27, 메뉴 행 20.1/20, CB 행 16.0/16, 셸프 64/64, 아이콘 32/32; ✗ 메뉴 위치 −6/0 | 5/6 (26.4, 20.0, 15.9, 64, 32; ✗ −10.4/0) |
| grid | lines FAIL (median ΔE00 7.1 / 7.1 / 7.1), corners 0/4, 0.13 ms | 같음 (0.126 ms) |
| furniture | 2/3 (ViewCube ✓, 라벨 ✓, 축 원점 ✗) | 2/3 |

step 133 (같은 도구, 고치기 전): 1.0 — pixels 「16/25 다름, 13 없음」, rects 5/12, density 4/6, furniture 1/3, checks 4 FAIL.

- **theme 로 분류된 30 개** (1.0 에서 ΔE00): 메뉴 바 14.0, Status Line 6.5, 셸프 탭 줄 3.8 / 현재 탭 5.6 / 다른 탭 3.8 / 아이콘
  줄 5.6, Tool Box 6.5 / 활성 툴 9.1, Outliner 메뉴 9.1 / 검색 4.4 / 목록 4.8 / 선택 행 21.0 / 컴포넌트 모드 행 11.1, 패널 메뉴 바
  6.5, 패널 툴바 6.5, 뷰 테두리 (영역 틈) 22.8, CB 배경 6.5 / 필드 4.4 / SHAPES 행 2.3 / INPUTS 행 4.4, Layer Editor 목록 1.3,
  Display 탭 26.5, 도크 탭 9.7, 타임 슬라이더 1.6, 현재 프레임 필드 13.5, 범위 필드 13.5, 하단 바 6.5, Command Line 4.4,
  Help Line 14.0, Create 메뉴 18.7.
- kit-drawn 6 개: viewport_bg 0.0, range_slider_bar 0.0, range_slider_handle 0.0, marking_menu_box 0.3, marking_menu_list_bg 0.3,
  hotbox_row_bg 0.3.
- 킷에 없는 요소 2: Outliner 도크 제목, Command 결과 필드.

## 도구 탓이 아닌 FAIL (킷 쪽, 다른 레인 / 이슈)

- viewport 1/12, 「tint」 (선택 면) 49.5: 선택 · 컴포넌트 색이 Blender 테마 색 (레인 SEL). tint 의 킷 면 색은 아직 step 43 의
  `#e4ac79` 를 가정한다 — SEL 레인이 킷 색을 정하면 그 값으로 바꿔야 한다.
- grid ΔE00 7.1, corners 0/4 (레인 GRID, #59).
- 1.25 에서 `layer_tab_active` / `layer_editor_list` 는 Layer Editor 가 도크 밖으로 밀려 (step_133_ui #4) 다른 것을 잰다 (theme 이라
  세지 않음).
- rects: Tool Box · Outliner · 뷰 · 도크 · 타임라인 크기 차이는 실제 레이아웃 차이 (1.25 에서는 Outliner 325 px, 도크 278 px 고정 —
  step_133_ui #8). density 「메뉴 위치」 −6 / −10 px 는 Create 메뉴가 메뉴 바와 겹쳐 열림 (step 51 부터 같은 항목).

## 검증

- `python tests/run.py -k step41,step81 --no-build`: 9 passed (resolve 의 배율 / 비율, `source`, 옛 anchor 금지 추가).
- 두 배율 전체 실행 rc 0, side-by-side · `marks_*` 를 열어 봄: 모든 점이 이름의 요소 위 (1.25 의 Layer Editor 두 점 제외, 위 참고).

## 남은 것

- SEL / GRID / HUD 레인 병합 뒤 메인이 다시 잰다 (`step_134.md`).
