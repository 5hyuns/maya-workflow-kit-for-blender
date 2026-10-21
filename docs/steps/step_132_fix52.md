# Step 132 — panel toolbar overflow (#52)

## 계획

- 문제: step 130 이후 kit 가 UI 배율을 바꾸지 않으므로 125 % Windows (유효 배율 1.25) 에서 Maya 레이아웃 메인 뷰포트의
  패널 툴바 (`ui/panel_toolbar.py`, 3D View tool header) 가 헤더보다 넓어 끝 버튼 (gamma, 색 관리) 이 잘림.
  `gui_step129_panel_toolbar` 는 1.25 에서 35 개 중 32 개만 찾았음 (그래서 테스트가 배율을 1.0 으로 바꿔 돌렸음).
- Maya 2022: 패널이 좁으면 툴바 오른쪽 끝에 » 버튼이 생기고 그 아래로 숨은 버튼이 펼쳐짐.
- Blender 헤더 레이아웃은 항목 위치를 알려주지 않음 (CLAUDE.md step 73). 그래서 폭을 **측정해서 공식으로** 만든다:
  `tmp/m52/gui_measure.py` (1 px 간격으로 마우스를 옮기며 `ui.copy_python_command_button` 로 버튼 x 범위) 를
  유효 배율 1.0 / 1.25 / 1.5 에서 돌린 결과 (region 963 px 폭):

  | 배율 | 아이콘 버튼 U | 그룹 사이 (bar + 간격 2) | 첫 버튼 | 노출 칸 (2.2 U) |
  |---|---|---|---|---|
  | 1.0 | 20 | 20 = 10 + 2×5 | 23 | 44 |
  | 1.25 | 25 | 24 = 12 + 2×6 | 28 | 55 |
  | 1.5 | 29 | 28 = 14 + 2×7 | 32 | — (잘림) |

  → U = ⌊18·s + ½⌋ + 2·pixel_size (Blender widget_unit), 간격 = ⌊5·s⌋, 앞 여백 = ⌊0.4·U⌋, bar = ⌊0.5·U⌋,
  칸 = ⌊2.2·U⌋, view transform = 6·U. 1.0 에서도 마지막 view transform 칸이 10 px 잘렸었음.
- 맞춤 (`ui/toolbar_fit.py`, bpy 없음 → 헤드리스 테스트): 그룹 단위 (Maya 순서: 카메라, 게이트·격자, 셰이딩·조명,
  효과, isolate / X-ray, 색 관리) 로 앞에서부터 들어가는 만큼 보이고, 하나라도 남으면 오른쪽 끝에 » (폭 1.5 U 고정 줄)
  자리를 빼고 계산. 오른쪽 여백 ⌊0.4·U⌋ + 안전 여유 2 px. 모두 들어가면 » 없음.
- » = `layout.popover` (`ALLSET_PT_panel_toolbar_more`, VIEW_3D HEADER popover) — 같은 연산자 / 속성 / 아이콘, 한 줄에
  한 항목 (아이콘 + Maya 이름, Maya 오버플로 메뉴처럼), 그룹 사이 구분선; 색 관리는 아이콘 버튼 + 값 칸 줄.
  숨은 그룹 시작 번호는 헤더 draw 가 area 포인터별로 기억 (`_FIRST_HIDDEN`), popover draw 가 읽음 (ID 데이터 아님).
  » 아이콘은 kit 가 그린 `pt_more` (status_icons 그림은 손대지 않음).
- 테스트: `tests/test_step132_toolbar_fit.py` (측정값 재현 + 맞춤), `gui_step129_panel_toolbar` 는 배율 강제 제거,
  툴바를 훑고 » 가 있으면 popover 를 열어 세로로 훑어 모든 버튼 (35 + 값 칸) 을 찾고, popover 안 버튼도 두 번 클릭.
  1.0 (`--ui-scale 0.8`), 1.25 (기본), 1.5 (`--ui-scale 1.2`) 에서 실행.

### delegated

- 접는 단위 = 그룹 (버튼 하나씩이 아니라): 그룹이 Maya 의 구분선 단위이고 popover 에서도 그룹으로 나뉨.
- » 위치 = 헤더 오른쪽 끝 (`separator_spacer`), Maya 처럼 툴바 끝에 붙지 않고 오른쪽 정렬 — 패널 폭이 바뀌어도 같은 자리.
- » 는 popover (Blender 헤더의 드롭다운 화살표 포함) — Maya 메뉴처럼 클릭으로 열리고, 값 칸 (노출 / 감마 / view
  transform) 도 그대로 넣을 수 있음.
- popover 의 항목은 아이콘 + 이름 (Maya 오버플로 메뉴는 이름 있는 메뉴 줄).

## 한 일

- `src/allset/ui/toolbar_fit.py` (bpy 없음): `unit` / `spacing` / `starts` / `fit` / `more_x` — 위 측정 규칙.
- `src/allset/ui/panel_toolbar.py`: 그리기를 `_draw_item` / `_bar` / `_draw_cm` 로 나눔; `draw_toolbar` 가
  `shown_groups` 만큼 그리고 나머지는 오른쪽 끝 » (`ALLSET_PT_panel_toolbar_more` popover, 아이콘 `pt_more`).
  popover 한 줄 = 같은 연산자 / 속성 + 같은 kit 아이콘 + Maya 이름 (왼쪽 정렬), 색 관리 줄은 아이콘 버튼 | 값 칸.
- 1600×900 창 (메인 뷰포트 963 px): 1.0 / 1.25 → 색 관리 묶음이 », 1.5 → X-ray 묶음 + 색 관리가 ».

## 검증

- `ALLSET_SANDBOX=fix52 python tests/run.py -k step132,step113,enable_disable,step131_icons,step129_viewport,step37,step130_package,step114`
  → 40 passed, 0 failed.
- `ALLSET_SANDBOX=fix52 python tests/gui/run.py -k step129_panel_toolbar,step113,step37` (1.25) → 51 passed;
  같은 것 `--ui-scale 0.8` (1.0) → 51 passed; `-k step129_panel_toolbar --ui-scale 1.2` (1.5) → 36 passed.
  모든 배율에서 32 개 아이콘 버튼 + 3 개 값 칸을 막대 또는 popover 에서 찾고, popover 안 버튼도 두 번 클릭해 확인.
- 스크린샷 (popover 열림): `tmp/m52/shots/gui_step132_more_1.png`, `gui_step132_more_1.25.png`,
  `gui_step132_more_1.5.png` — 눈으로 확인.
- GUI 테스트는 버튼 위치를 tool header 기준 상대 좌표로 저장 (Maya strip 줄이 레이아웃 로드 뒤 자리 잡으면서 헤더가
  아래로 움직여, 절대 좌표 클릭이 패널 메뉴 줄에 맞았음).

## 남은 것

- 버튼 단위가 아니라 그룹 단위로 접음 (delegated). 실제 마우스로 » 열기 / 닫기 느낌은 manual_checks.
