# Step 183 — Option box click opens the window (backlog.json #1, audit 13 #1, #82)

## 계획

문제 (#82, 여섯 감사째 점수 16): Maya 메뉴 항목의 ❒ 를 클릭하면 명령이 실행되고, 옵션 창은 0.2 s hold (step 146) 나 Shift / Ctrl+클릭
으로만 열린다. step 146 의 측정: 연산자는 EXEC 라 클릭 위치 · 팝업 위치를 모른다.

먼저 잰 것 (GUI 탐침 3 개, 끝난 뒤 지움; `research/blender/menu_click_183.md`):
1. `Menu.draw` 의 `context.region` = 메뉴를 부른 region (팝업 자신 아님), `Screen` 에 팝업 region 없음.
2. **`execute` 안에서 부른 `INVOKE_DEFAULT` 연산자의 event = 행 위의 LEFTMOUSE RELEASE** → 클릭 x · y 는 안다.
3. `execute` 안의 screenshot 은 이미 닫힌 메뉴 → 화면에서 행 끝을 읽을 수 없다.
4. 메뉴 위치 · 폭은 kit 이 계산할 수 있다 (스크린샷, UI 1.0 / 1.25): 메뉴 바 pulldown 의 왼쪽 = 버튼 왼쪽 (kit 이 `ui_units_x` 로 놓은
   버튼: region x + int(1.48 u) + 앞 버튼 폭), 글자 시작 = 메뉴 왼쪽 + 1.6 u, ❒ 끝 = 글자 시작 + kit 이 정렬한 글 폭 (오차 1 px), 메뉴 폭
   = 1.6 u + 가장 긴 줄 + 1.6 u (서브메뉴 줄 있음) / 1.28 u (없음), 서브메뉴 왼쪽 = 부모 오른쪽.

결정 (delegated):
- ❒ 클릭 = 메뉴 바에서 연 Maya 메뉴 (와 그 서브메뉴) 에서: 클릭 x 가 ❒ 칸 (❒ 글자 왼쪽 0.5 u 부터 메뉴 오른쪽 끝까지 — Maya 의 ❒
  칸처럼 행 오른쪽 끝) 안이면 `allset.menu_option_box`, 아니면 명령 (`ui/option_click.py`, `menu_item.execute`).
- 모델을 믿을 수 없을 때는 늘 명령: 메뉴가 메뉴 바에서 안 열림 (`Menu.draw` 의 area 가 그 창의 top bar 가 아님 — 핫박스 · 마킹 메뉴 ·
  편집기 메뉴 바 · 떼어낸 메뉴), » 로 잘린 메뉴 바, 메뉴 세트 필드가 메뉴 바 안 (Status Line 없음 — 안 잼), 클릭이 모델 메뉴 밖, 키보드
  (LEFTMOUSE 아님). 그곳들은 step 146 의 hold / Shift / Ctrl+클릭 그대로.
- 툴팁 `BOX_TIP` = "click the box, or press and hold …".

순서: 측정 → 설계 → 구현 → 검증이 한 줄 의존 (탐침 결과로 방법이 정해짐) — 독립 레인 없음 (병렬 안 함).

## 한 일

- `src/allset/ui/option_click.py` (새): `note_draw` (메뉴 바에서 열렸는지, 창별), `rows` / `width` (kit 이 그리는 글 그대로로 폭),
  `top_left` (메뉴 바 버튼 왼쪽), `box_zone` (❒ 칸 · 메뉴 좌우, 서브메뉴 사슬, 창 오른쪽 넘침 처리), `ALLSET_OT_click_point`
  (INVOKE 로 클릭 위치), `on_box`.
- `src/allset/ui/menu_sets.py`: 맨 위 Maya 메뉴 draw 가 `note_draw`, `ALLSET_OT_menu_item.execute` 가 `on_box` 면 옵션 상자, `BOX_TIP`.
- 테스트: `tests/test_step183_option_click.py` (6), `tests/gui/gui_step183_option_click.py` (메뉴 7 개 모델 vs 화면 왼쪽 · 오른쪽 ·
  ❒ 픽셀, Edit Mesh > Bevel / Create > Polygon Primitives > Cube 의 ❒ 클릭 = 옵션 창 · 라벨 클릭 = 명령, 뷰에서 연 메뉴 = 칸 없음).

## 검증

- GUI `gui_step183_option_click` UI 1.25: **24 / 24**, UI 1.0 (`ALLSET_GUI_UI_SCALE=0.8`): **24 / 24** — 메뉴 왼쪽 오차 ≤ 1 px, 오른쪽 ≤ 4
  px, ❒ 클릭 (Bevel 739 / 602 px, Cube 610 / 490 px) → `menu_option_box` (Polygon Cube Options 창 스크린샷 직접 봄, Maya 메뉴 닫힘),
  라벨 클릭 → 명령만.
- 관련 GUI `-k step146,step103,step140,step183,step108`: **61 / 61**.
- 헤드리스 관련 `-k step183,step146,step108,step103`: 27 / 27; 헤드리스 전체 **1689 / 1689** (206 파일).

## 남은 것

- ❒ 클릭은 메뉴 바에서 연 메뉴만. 핫박스 · 마킹 메뉴 (kit 이 그려 위치를 아니까 다음에 가능), 편집기 메뉴 바 (Graph Editor 등 —
  버튼 위치 모델 필요), » 메뉴, 떼어낸 메뉴, Status Line 없는 화면 (메뉴 세트 필드) 은 hold / Shift / Ctrl+클릭.
- UI 배율 1.0 / 1.25 만 잼 (`LEAD_UNITS` 1.48 은 두 배율 맞춤) — 1.5 / 2.0 · 5.x 는 GUI 테스트를 그 배율로 돌려 확인할 것.
- 실제 하드웨어 클릭 → manual_checks 「Step 183」.
