# Step 142 lane UI — dock width, UI scale 1.5, manipulator colours (#78 #77 #76)

## 계획

- #78: Maya 의 탭 스택은 탭이 오른쪽 세로 띠라 Channel Box 일 때 277–280 px, AE 를 올리면 480 px
  (`research/maya/screens/01_layout_empty.png`, `10_attribute_editor.png`). 킷은 가로 탭 줄 때문에 466 / 574 / 672 px (step 135).
- #77: UI 1.5 배 (`--ui-scale 1.2`) 1600 px 창에서 메뉴 막대가 Workspace 밑으로 넘침 (「Deform U」), Set Driven Key 창의 버튼이 독
  아래로 밀려남.
- #76: Move / Scale 조작기 축 색이 Blender 테마 기즈모 색, 와이어프레임에서 선택 안 된 오브젝트가 #181818 (Maya #000460).

테스트 먼저: `tests/test_step142_ui.py` (규칙: 폭, 띠 기하, 클릭 매핑, 넘침 분할, SDK 줄 수, 색 상수), `tests/gui/gui_step142_ui.py`
(독 폭 CB / AE, 뷰포트 폭, 띠 클릭, 메뉴 넘침, 조작기 · 와이어 화소).

## 한 것

### #78 — Maya 세로 탭 띠 (delegated)

- 고른 것: **세로 탭 띠** (`ui/maya_dock.py` `draw_strip`, Properties WINDOW POST_PIXEL, blf 회전 −90° = Maya 처럼 위에서 아래로 읽음)
  + 탭이 바뀔 때 스택 폭을 Maya 처럼 바꿈. 버린 것: 가로 탭 줄을 유지하고 폭만 탭을 따라가게 — 277 × 배율에서는 짧은 캡션
  (「Channel Box」 · 「Attribute Editor」 · 「Modeling Toolkit」) 으로도 탭 줄이 340 px 넘게 필요해 두 줄이 되거나 잘린다.
- 띠: 폭 18 × s px (Maya 16), 탭 = 글자 + 양끝 11 × s, 탭 사이 2 × s, 첫 탭은 영역 위 4 × s 아래 (Maya 133–294 / 297–404 / 407–520).
  색은 테마를 읽기만: 띠 배경 = 영역 배경 × 0.63, 내려간 탭 × 0.81, 글자 × 0.62 (Maya 43 / 55 / 68, 146 / 238). 올라간 탭 = 영역 배경.
- 클릭: `allset.dock_strip_click` 를 "View2D Buttons List" LMB PRESS 맨 앞에 (그 영역 핸들러가 "Property Editor" 보다 먼저, 스크롤바가
  같은 가장자리), 띠 밖은 PASS_THROUGH (`maya_patches.PASS_THROUGH_FIRST`).
- 내용은 띠를 피한다: `maya_dock.StripClear` — 패널 루트 레이아웃에 들어가는 항목마다 자기 split (내용 | 빈 띠 열). 처음에는 split
  하나의 열에 전부 그렸는데, 중첩 열은 항목 간격이 style `buttonspacey`, 루트는 `templatespace` 라 Channel Box 줄이 1.5 배에서 줄마다 4 px
  위로 올라가 GUI 테스트의 줄 위치 (gui_step62) 가 어긋났다 (측정). 항목마다 split 이면 루트 간격 그대로.
- 폭 규칙 (`toolbox.dock_width(scale, kind=...)`): CB / MTK = max(277 × s, 라벨 필요 폭 + 띠 + 틈), 상한 480 × s; AE = 480 × s
  (Maya 의 AE 스택, `WIDE_KINDS`). 1.0 / 1.25 / 1.5: **CB 286 / 346 / 418** (Maya 277 / 346 / 416; 이전 466 / 574 / 672),
  **AE 480 / 600 / 720** (뷰포트 하한 280 × s 로 잘림: 1.5 에서 660). `attribute_editor.fits` 는 띠 폭을 뺀다 (AE 메뉴 막대 한 줄 판정).
- 탭이 바뀌면 (`maya_dock.tab_drawn` → `toolbox.tab_changed`, 그리기에서는 타이머만 등록): 좁은 ↔ 넓은 종류가 바뀌고, 스택이 이전 탭의
  킷 폭 그대로일 때만 (사용자가 바꾼 폭은 유지) 한 번 맞춘다 — `area_move` 가 바로 poll 되면 바로, 아니면 커서 맞춤
  (`ALLSET_OT_fit_columns`, `_tab_target` 는 그 연산자가 도는 동안만; #53 처럼 나중에 적용되지 않음). 이벤트 시뮬레이션에서는 커서 맞춤이
  `ALLSET_FIT_WARP=1` 일 때만.
- `tools/make_startup.py` `DOCK_PX` = 286, startup.blend 다시 만듦 (스택 287, 1.0 뷰포트 954 px; 이전 773).
- 테스트 갱신: `test_step116_dock` (탭 버튼 없음), `test_step135_width` (띠 왼쪽 라벨, AE 폭), `gui_step135_width` (탭 줄 확인 제거,
  탭 전환 뒤 기다림), `gui_step99_first_screen` (띠 클릭, `sim.dock_tab_point`).

### #77 — 메뉴 막대 » 넘침, SDK 버튼

- `ui/status_line.py` `draw_menu_bar_fit`: 왼쪽 헤더 영역 폭에 맞는 메뉴만 그리고 끝에 Maya 의 » (패널 툴바 `pt_more` 글리프,
  step 132 #52 와 같은 방식: 폭은 Blender 레이아웃 규칙 = `menu_width_units` × U, 앞 0.4 U, 로고 1.6 U, 여유 0.5 U, » 1.5 U).
  » = `ALLSET_MT_menu_more` (숨은 메뉴를 하위 메뉴로). 모두 맞으면 `menu_sets.draw_menu_bar` 그대로. 1600 px: 1.0 / 1.25 모두 18 개,
  1.5 는 13 개 + » (Deform, UV, Generate, Cache, Help).
- `ui/set_driven_key.py`: 목록 줄 수가 Channel Box 아래 남은 높이를 따른다 (`remember_room`: `maya_dock` 이 CB `body` 의 높이 추정을
  넘김; `list_rows` = (남은 U − 9) / 2, 2–4 줄), 도움말 줄은 자리가 있을 때만. 1.5 배에서 버튼 네 개가 독 안 (GUI 샷).

### #76 — 조작기 축 색, 휴면 와이어

- `ui/manipulator.py` `MAYA_AXIS`: X #e60000, Y #00e600 (`colors.json` manip_x / manip_y), Z #0000ff (Maya 가 그린 Z 선,
  manip_z_rendered; displayRGBColor 「Zaxis」 #4a92ff 는 그리드 / 뷰 축 색). 활성 · 호버 손잡이는 Maya 노랑 #ffff00 그대로.
  테마를 읽지 않는다.
- **Rotate 는 Blender C 기즈모 그대로 (테마 축 색)**: Python 으로 C 기즈모 색을 바꾸려면 테마를 써야 해서 (결정 13) 불가, step 59 의
  이유 (Python dial 은 뒤쪽 절반을 C 처럼 자르지 못함) 도 그대로. 기록만.
- `ui/selection_wire.py`: 와이어프레임 셰이딩에서 선택 안 된 오브젝트 (오브젝트 모드, 보이는 것, 뷰의 타입 표시 · 로컬 뷰 존중 —
  툴 박스 열은 모든 타입을 숨김) 를 Maya #000460 으로 같은 POST_VIEW 패스에서 그린다. X-ray 와이어프레임이면 깊이 테스트 없이
  (Maya 와이어프레임처럼 가려진 선도). 환경설정 "Selection Wireframe" 이 둘 다 켜고 끔 (설명 갱신; 새 환경설정은 만들지 않음, delegated).
- look_compare 의 면 점묘 'tint' 측정 재검토: 하지 않음 (비싸지 않은 범위를 넘음, 아래 남은 것).

## 검증

- 헤드리스 전체 `ALLSET_SANDBOX=ui142 python tests/run.py`: **1227 passed, 0 failed** (149 파일; 첫 실행에서 실패 2 개 —
  `test_keymap_maya` 그림자 목록에 Screen / Property Editor 추가, `test_step7_top_ui` 의 가짜 context 에 region 없음 → `getattr` — 고친 뒤).
- GUI 1.25 (기본): `-k step142,step113,step62,step135,step134,step59,step99,step116` **141 / 1** → gui_step59 의 화살표 길이 측정이
  테마 axis_z 색을 찾고 있었음 → 킷 Maya 색으로 바꾼 뒤 `-k step59` **14 / 0**.
- GUI 1.5 (`--ui-scale 1.2`): `-k step142,step113,step62` **35 / 0** (이전 gui_step113 메뉴 1 개, gui_step62 SDK 9 개 실패).
- GUI 1.0 (`--ui-scale 0.8`): `-k step142,step135_width,step99,step62` 41 / 1 → 조작기 화소 문턱 (1.0 에서 Y 선 18 px) 20 → 10, 다시
  `-k step142` **12 / 0**.
- 본 그림 (`tmp/ui142out/`, `tmp/ui142/s150`): `s125/gui_step142_cb_125.png` (띠, 346 px 독), `gui_step142_ae_125.png` (AE 600 px, 메뉴
  한 줄), `gui_step142_wireframe_125.png` (Maya 04 그림과 같은 짙은 파랑), `s150/gui_step142_menu_more_150.png` (» 메뉴),
  `s150/gui_step62_sdk_result.png` (1.5 SDK 버튼), `s100/gui_step142_move_100.png` (조작기 Maya 색, 1.0 독 287 / 뷰포트 990).
- `tools/look_compare.py` (1.0, `ALLSET_LOOK_TAG=s100`): viewport **11/12** (step 134: 7/12) — 조작기 X / Y / Z ΔE00 **0.0 / 0.3 / 0.0**
  (이전 15 / 8 / 21), 휴면 와이어 **1.9** (이전 26); 남은 하나는 면 점묘 tint (측정 방법). rects: 독 287 × 690 (Maya 260 + 띠; 이전 466),
  뷰포트 988 (Maya 1003). checks 9/9, pixels 6/6, grid ok.

## 남은 것

- 새 이슈 #83: 1.5 배에서 Channel Box 칸이 스크롤하면서 Layer Editor 위에 약 두 줄 빈자리 (`channel_box.pane_room` 추정, 이 레인 파일 밖).
- 탭 전환 폭 맞춤은 커서를 잠깐 독 왼쪽 모서리로 옮긴다 (step 99 맞춤과 같은 방식) — 손으로 확인 (`docs/manual_checks.md` Step 142 — UI).
- look_compare 면 점묘 'tint' 측정 방법 재검토 (#76 세 번째 항목).
