# Step 99 — 첫 화면: Maya Outliner 기본 행, 125 % Tool Box, 도크 탭

backlog 1 (step 98 #1–#3). 근거: `research/maya/screens/audit7/pairs/a01_first_screen.png`, `kit_scale125/a01_first_screen.png`,
`research/maya/screens/audit7/maya/a01_outliner_crop.png`.

## 계획 (delegated)

측정 먼저 (`tmp/p99b.py` GUI probe, mayapy `tmp/m99.py`):

- mayapy (Maya 2022, factory): 새 장면 최상위 DAG = persp, top, front, side (startupCamera 1, visibility 0) + 사용자 노드.
  `defaultLightSet` = 모든 라이트 (`select defaultLightSet` → 라이트 선택), `defaultObjectSet` = 비어 있음, `select persp` → 숨은
  카메라 선택.
- Blender 4.5: Item 탭은 C 패널 `VIEW3D_PT_transform` (bpy.types 에 없음). 같은 bl_idname 의 Python 패널을 등록하면 Item 탭이
  **사라지지만**, 등록을 풀어도 C 패널이 **돌아오지 않는다** (재시작 전까지 Item > Transform 손실 — probe 스크린샷 3 장) → 쓰지 않는다.
- `screen.area_move` poll = `screen.active_region == NULL`: 마우스가 영역 위면 False, 커서를 영역 사이 틈 (Tool Box 열 오른쪽
  x + width + 1) 로 옮기면 True (probe `poll at edge (57, 433) True`).
- Make Blender Maya 의 「Maya Density」 프리셋이 effective scale 을 1.0 으로 맞추므로 (probe: 1.25 PC 에서 `scale 1.0`), Tool Box 가
  비는 건 프리셋 없이 125 % 로 쓰는 경우 (dogfood, step 98 첫 세션, 사용자가 해상도 배율을 바꾼 경우).

결정:

1. **Outliner 기본 행 = 그린 행** (step 96 세트 행과 같은 POST_PIXEL 겹침, `ui/outliner_sets.py`). 진짜 카메라 오브젝트는 안 만든다:
   Blender 사용자 뷰는 카메라가 아니라 persp 를 골라도 뷰와 상관없는 값이 되고, 렌더 카메라·FBX 내보내기·Frame All·정렬
   (front < pCube1 < persp) 에 섞인다. 순서는 Maya 대로 카메라 4 → defaultLightSet / defaultObjectSet → kit 세트. Blender C 행을
   아래로 밀 방법이 없어 (view2d 는 내용 위로 스크롤 안 됨) 오브젝트가 있으면 카메라가 DAG 행 **뒤**에 온다 — 새 장면 (첫 화면) 은
   Maya 와 같다. 클릭: 카메라 = 오브젝트 선택 해제 + 행 강조 (뒤에 카메라가 없음), defaultLightSet = 라이트 선택 (Ctrl 토글 / Shift
   추가), defaultObjectSet = 선택 해제. RMB 는 통과. Outliner 줄무늬 끔 (테마 `outliner.row_alternate` alpha 0, `tools/make_theme.py`).
2. **Tool Box 열**: `MAYAKIT_OT_fit_columns` (작은 모달) — 열·셸프 줄 크기가 틀리고 poll 이 실패하면 커서를 영역 틈으로 옮기고,
   타이머 틱마다 `fit_columns` 를 다시 돌려 이동이 끝나면 (또는 12 틱) 커서를 원래 자리로 (사용자가 그사이 움직였으면 그대로).
   파일 로드마다 화면당 3 번까지. 이벤트 시뮬레이션에서는 워프가 OS 이동을 만들지 않으므로 `window.event_simulate` 로 같은 이동을 보냄.
3. **도크 탭 = Blender 사이드바 세로 카테고리 탭** (Maya 처럼 오른쪽 가장자리 세로 글씨): 카테고리 이름 「Channel Box / Layer Editor」
   「Attribute Editor」「Modeling Toolkit」, 패널 하나씩 (poll 없음 — 처음 그릴 때 모두 생겨 Item 앞에 놓임, step 91 의 순서 문제 피함).
   `WindowManager.maya_kit_dock` 은 그대로 kit 의 상태 (Ctrl+A, Windows 메뉴, RMB 가 씀): update 콜백이 탭을 바꾸고, 0.2 s 타이머가
   사용자가 누른 탭을 따라감. Item 탭은 C 패널이라 숨길 수 없어 오브젝트가 있으면 네 번째로 남는다 (누르면 열어 둠). 위의 가로 전환
   버튼은 없앰.
4. **CB / LE 비율**: `initChannelsLayers.mel` 은 70 % (ui_layout.md:252) 지만 Maya 2022 팩토리 화면은 Display / Anim 탭이 도크
   132–785 중 y 473 (≈ 절반). 측정값을 따라 `CB_SHARE` 0.5: CB 패널이 내용 높이를 추정해 (`body` 가 UI 단위 반환) 빈칸을 채우고,
   Layer Editor 목록은 아래 끝까지 (`layer_editor.list_rows`). INPUTS 가 있거나 CB 가 더 길면 채우지 않음 (Blender 패널은 따로 스크롤 안 됨).

## 한 것

- **Outliner 기본 행** (`ui/outliner_sets.py`): `default_entries()` = persp / top / front / side (`CAMERA`, 회색 글자 + kit 카메라
  그림) → defaultLightSet / defaultObjectSet (`DEFAULT_SET`, 세트 그림) → kit 세트. 클릭은 `_default_row` (카메라 = 선택 해제 + 행
  강조 `_picked`, defaultLightSet = 라이트 선택 Ctrl/Shift, defaultObjectSet = 해제), RMB 는 통과. 테마 `outliner.row_alternate`
  alpha 0 (`tools/make_theme.py` → `theme/maya.xml` 재생성) — Maya 처럼 평평한 목록.
- **Tool Box 열 125 %** (`ui/toolbox.py`): `MAYAKIT_OT_fit_columns` + `fit_columns(start_fit)` 이 poll 실패한 이동의 경계점을 모아
  커서를 그 틈으로 옮긴 뒤 이동 (열 → Outliner → 셸프 줄 순서, 경계가 바뀔 때마다 다시 옮김), 사용자가 마우스를 움직이면 멈춤.
  Outliner 도 열 옆에서 Maya 패널 폭 260 × 배율 (`OUTLINER_PX`) 을 유지 (열을 넓히면 Outliner 가 그만큼 줄었음). 이벤트 시뮬레이션
  세션 (GUI 테스트, dogfood) 에선 자동 실행 안 함 (`auto_warp`, `MAYA_KIT_FIT_WARP=1` 로 켬): 스크립트 단계 중간의 워프가 메뉴를 닫아
  step 54 / 57 GUI 테스트가 깨졌다.
- **크래시 수정**: 타이머가 `show_region_toolbar` 를 바꿀 때 컨텍스트 창이 방금 닫힌 창이면 `WM_window_get_active_workspace` 에서
  EXCEPTION_ACCESS_VIOLATION (manual sweep M66, UV Editor 창을 닫은 뒤; 열이 넓어져 fallback 을 끄는 경로가 처음 실행됨) → 그 창으로
  `temp_override` 해서 설정.
- **도크 탭** (`ui/channel_box.py`, `ui/attribute_editor.py`, `ui/layer_editor.py`): 카테고리 「Channel Box / Layer Editor」
  (CB + LE), 「Attribute Editor」 (`MAYAKIT_PT_dock_attribute_editor`), 「Modeling Toolkit」 (`MAYAKIT_PT_dock_modeling_toolkit`).
  `maya_kit_dock` 의 update = `show_dock_category`, `_sync_tick` (0.2 s) = 사용자가 고른 탭 → `maya_kit_dock`, 탭이 아직 없던 사이드바
  는 나중에 맞춤, 사용자가 연 Item 탭은 그대로. 위의 가로 전환 버튼 대신 Maya 도크 제목 줄 자리의 빈 줄 (`dock_title_row`; Maya 도
  메뉴 위에 아이콘 줄이 있다, y 141) — 그래서 CB 행 위치는 전과 같다.
- **CB / LE 분할**: `CB_SHARE` 0.5, `fill_pane` (CB 높이 추정 `body()` → 빈칸), `layer_editor.list_rows` (목록이 아래 끝까지).
  SDK 창이 LE 자리를 쓸 때와 INPUTS 가 있을 때는 분할 없음.
- `tools/make_startup.py` `DOCK_CATEGORY` 새 이름 → 템플릿 재생성. 테스트 문자열 「Channel Box」 → 새 카테고리
  (tests/gui 의 goto_tab / active_panel_category), `gui_step11` 은 AE 탭으로, `gui_step91` 은 AE 탭이 열리는 것으로,
  `gui_step96` 은 세트 행이 기본 행 6 개 뒤, `test_step11_outliner_ae.test_dock_mode_switches_panels` 는 탭 네 패널을 확인.
- look_compare 표본점 (`tools/look_data.py`): Range Slider 막대 / 손잡이 (step 73 에 생겼는데 「없음」 으로 남아 있었음),
  Layer Editor Display 탭 (Blender 파랑이라 ✗ 로 정직하게), Tool Box Move 버튼 위치 다시 잡음.
- 새 GUI 테스트 `tests/gui/gui_step99_first_screen.py` (1.25 / `--ui-scale 0.8` 둘 다), manual checks 4 개.

## 검증

- GUI `gui_step99_first_screen`: effective 1.25 **12/12** (column 70 px = want 70, TOOLS 70 px, Outliner 325 px, 기본 행 6, persp 가
  맨 위, 탭 CB → AE → 사용자 탭 = dock, 큐브 뒤 기본 행, defaultLightSet = pointLight1, persp = 선택 없음), `--ui-scale 0.8` (effective
  1.0) **12/12** (column 56, TOOLS 56).
- 나란히 비교 `research/maya/screens/step99/pair_s99_first_screen_100.png` / `_125.png`, `pair_s99_cube_selected_*` 직접 확인: 왼쪽
  Outliner = persp … defaultObjectSet, 도크 오른쪽 세로 탭 세 개, Display/Anim 탭 y 493 (Maya 473), 목록이 아래 끝까지.
- look_compare: pixels **34 중 25 일치** (ΔE00 > 5 는 5, kit 에 없음 4; 전 31 중 19), rects **5/12** (변화 없음, 아래 「남은 것」),
  viewport 11/12, scene 3/3, density 6/6.
- 전체: 헤드리스 **719/719**, GUI **1015/1015** (78 파일; 중간 실행에서 깨진 28 개 = 도크 맨 위 줄을 없애 바뀐 CB 위치, 시뮬레이션 중
  커서 워프, 세트 행 위치, 옛 「Channel Box」 카테고리 → 빈 제목 줄 · auto_warp · 테스트 갱신으로 해결; manual sweep 의 크래시는 위
  「크래시 수정」), dogfood **47/47** 콘솔 0 (dogfood_session / release_shots 의 탭 이름 갱신).

## 남은 것

- **rects 9/12 목표는 이번 구조로 불가 (delegated 판단)**: Blender 의 헤더 (26 px) · 상태바 (23 px) 높이가 고정이고 Maya 는 Time
  Slider / Range Slider / Help Line 사이에 6 px 틈이 있어, 아래 세 줄이 Maya 보다 22 px 짧다 → 가운데 줄 (Tool Box, Outliner, 뷰) 이
  29 px 길고 Time Slider·Range Slider 가 18–24 px 아래. 맞추려면 Time Slider 를 60 px 로 키워야 해서 그 높이가 틀어진다. 도크는 3D 뷰
  헤더 밑에서 시작해 y +24 (사이드바는 헤더 위로 못 올라감), Tool Box 폭 56 은 Blender 툴바 한 칸의 최소값 (Maya 40). 도크를 3D 뷰
  밖의 별도 영역으로 옮기면 도크 y 와 뷰 폭은 맞출 수 있으나 큰 레이아웃 변경 — 후보로 남김.
- 오브젝트가 있으면 카메라 행이 DAG 행 뒤 (Blender C 행을 밀 수 없음). 사이드바 kit Outliner (UIList) 에는 기본 행을 아직 안 넣음.
- Item 탭 (C 패널) 은 숨길 수 없음 — 측정: Python 대체 등록은 해제 후 C 패널을 되살리지 못함.
- Layer Editor Display / Anim 탭이 Blender 파랑 (Maya 활성 탭 #444444), LE 목록 바탕 #444444 (Maya #2a2a2a) — look_compare ✗ 2.
- CB 높이 추정은 근사 (행 수 기반): 화면에서 Display 탭이 Maya 보다 20 px 아래.
