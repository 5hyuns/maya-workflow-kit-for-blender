# Step 44 — Maya 위젯 감각: 평면 위젯·밀도 (ui_scale)·Segoe UI

backlog 4 (`docs/PLAN.md` 「Maya 동일화 계획」). 근거: `research/maya/colors.json` `ui_style` = `adskdarkflatui` (각진 평면),
`metrics` (Segoe UI 11 px, Channel Box 행 16 px, 메뉴 항목 20 px, 메뉴바 27 px, 125 % 화면에서 Qt dpr 1.0),
`research/maya/screens/compare/02_cube_selected_move.png` (step 43 의 kit: 행 약 25 px, 둥근 0.4 위젯, 엠보스),
step_40.md blindspot 9 (밀도), 10 (폰트), 11 (위젯 모양). step_43.md 「남은 것」 의 와이어 안티에일리어싱도 여기서.

## 실측 (step 44)

- 이 PC (125 % 화면, 1600×900 창): `view.ui_scale` 1.0 → `system.ui_scale` **1.25** (dpi 90), `view.ui_scale` 0.8 → `system.ui_scale`
  **1.0** (dpi 72). 즉 Blender 의 실효 배율 = OS 배율 × Resolution Scale, Maya 는 OS 배율을 무시 (dpr 1.0).
- 실효 배율 1.0 에서: 위젯 글자 11 px (Blender 11 pt × 1.0 = Maya Segoe UI 11 px), 행·메뉴 항목 20 px (= Maya 메뉴 항목),
  상단 바 26 px (Maya 메뉴바 27), 상태 바 23 px.
- 배경 실행 (`-b`) 에서는 `system.ui_scale` = 0 (창 없음).
- `blf.load(font_path_ui 와 같은 파일)` = 0: Blender 는 `view.font_path_ui` 를 blf 글꼴 0 번으로 읽는다 → 마킹 메뉴 (`marking/draw.py`, 글꼴
  0) 는 따로 손대지 않아도 Segoe UI 로 그려진다.
- 테마 4.5: `ThemeWidgetColors` 에 `roundness`·`show_shaded` (wcol_state 는 다른 구조라 없음), `user_interface.widget_emboss` (기본 알파 0.15),
  `menu_shadow_fac` (최솟값 0.01 로 저장됨) / `menu_shadow_width` (0 = 그림자 없음), `panel_roundness` (기본 0.4).
- 면 채움: step 43 은 `face_mode_select` α 0.07 을 kit 02 (기본 샷) 대비로 맞췄는데, 그 상자에 Move 매니퓰레이터가 걸려 있었다
  (새 밀도에서 뚜렷: 02 의 그 점 = 파란 Z 화살표). 같은 뷰·매니퓰레이터 없는 03 을 기준으로 다시 재면 0.07 → 실효 0.07.
  프로브 (같은 뷰, 선택 전후): α 0.07 / 0.15 / 0.25 / 0.35 / 0.5 → 실효 (채널 평균) 0.14 / 0.22 / 0.31 / 0.40 / 0.54, 즉 α 1 당 약 0.86.
  → α **0.28** 로 바꾸니 실효 0.28, ΔE00 1.2.

## 계획 (delegated)

1. **평면 위젯** (`tools/make_theme.py` → `maya.xml`): 모든 `wcol_*` roundness 0, `show_shaded` 끔, `widget_emboss` 알파 0,
   `menu_shadow_fac` 0 + `menu_shadow_width` 0, `panel_roundness` 0.
2. **환경설정 그룹** (`prefs_preset.GROUPS`, 백업 JSON 은 애드온 환경설정, 끄거나 애드온을 끄면 복원):
   - 「Maya density」 `maya_density` → `view.ui_scale` = 1 / OS 배율 (`system.ui_scale / view.ui_scale`, 0.5–2 로 제한; 125 % → 0.8,
     100 % → 1.0, 150 % → 0.667). 시작 중 등록 때는 창이 아직 없을 수 있어 타이머로 적용 (`LATE`).
   - 「Maya font」 `maya_font` → Windows 에서만 `view.font_path_ui` = `%WINDIR%\Fonts\segoeui.ttf` (동봉 안 함, D3); 파일이 없으면 아무 것도 안 함.
   - 「Aliased wires」 `maya_wire` → `system.use_overlay_smooth_wire` / `use_edit_mode_smooth_wire` 끔.
   - 세 옵션 기본 끔 (D2: 전역 설정은 사용자가 고를 때만). 「Make Blender Maya」 가 셋을 켜고 (폰트는 있으면) 「Revert Maya Look」 이 끈다.
3. **Channel Box 행**: 채널 열 `scale_y` 0.8 (`channel_box.ROW_SCALE`) → 실효 1.0 에서 16 px (Maya), 1.25 에서 20 px. Maya 처럼 항상 촘촘하게
   (delegated: CB 만, 메뉴는 Blender 20 px = Maya 20 px 그대로).
4. 마킹 메뉴 글자: `font_size()` 는 이미 11 px × 실효 배율 → 밀도를 켜면 Maya 와 같은 11 px; 글꼴은 위 실측대로 자동.
5. **테스트**: `tests/gui/run.py --ui-scale 0.8` (모든 테스트에 Resolution Scale, 템플릿 전환 뒤 load_post 로 다시), `sim.px()` = 1.25 에서 잰
   픽셀 값을 지금 배율로. 헤드리스 `test_step44_widgets.py`, `tests/kit.py` 스냅샷에 와이어 설정 추가.
6. **비교**: `look_compare.py` → `density.md` (메뉴바 높이 = kit 상단 바, 메뉴 항목·CB 행 간격 = 두 샷 모두에서 글자 줄 중심 간격의 최빈값,
   `look_data.line_pitch`; 메뉴 영역 = 메뉴 배경색 영역 `colour_area`).

## 한 것

- `tools/make_theme.py` `ROUNDNESS`·`SHAPE` + 재생성 `src/maya_kit/theme/maya.xml`; `face_mode_select` α 0.07 → 0.28 (위 실측).
- `src/maya_kit/prefs_preset.py`: 그룹 `density` / `font` / `wire`, 프리셋이 함수일 수 있음 (`preset_of`), 빈 프리셋은 건너뜀, `os_scale()` /
  `maya_ui_scale()` / `font_available()` / `SEGOE_UI`, 밀도는 타이머로 늦게 적용 (unregister 에서 타이머 해제).
- `src/maya_kit/preferences.py`: `maya_density` / `maya_font` / `maya_wire` (+ `*_backup`), 환경설정 첫 상자에 표시 (Segoe UI 없으면 회색).
- `src/maya_kit/first_start.py`: make / revert 에 세 옵션.
- `src/maya_kit/ui/channel_box.py`: `ROW_SCALE` 0.8. `src/maya_kit/marking/draw.py`: 근거 주석.
- `tests/gui/run.py` `--ui-scale`, `tests/gui/sim.py` `UI_SCALE` / `scale()` / `px()`; `gui_step37_panel_menus.py` (헤더 x 를 `px`, 처음 마우스도
  `px(200)` — 다른 버튼 위에 있다가 같은 틱에 누르면 메뉴가 안 열림), `gui_step38_channel_box_multi.py` (필드 위치를 UI 영역 기준 + `px`).
- `tools/look_data.py` `DENSITY` / `MENU_BG` / `colour_area` / `line_pitch`, 면 채움의 kit 기준 샷 03; `tools/look_compare.py` `density.md`;
  `tools/look_shots.py` Create 클릭 x 를 `sim.px(150)` (0.8 에서는 150 이 Select 였음).
- `docs/manual_checks.md` step 44 항목.

## 검증

- `python tests/run.py`: **헤드리스 356/356** (step 43: 349; 새 `test_step44_widgets` 7; 첫 실행 355/356 — step 43 테스트의 face_mode_select 0.07 단언을 0.28 로 고침).
- `python tests/gui/run.py`: **GUI 1.0 281/281**, `--ui-scale 0.8`: **281/281** (처음 0.8 실행 278/281 — 픽셀 고정 좌표 3 개, 위처럼 고침).
- `python tools/dogfood.py`: **47/47**.
- `python tools/look_compare.py` (깨끗한 설치 → 환영 대화상자 Return = Make Blender Maya → 밀도·Segoe UI·각진 위젯):
  - `density.md` **3/3**: 메뉴바 26 px (목표 27±2, Maya 샷 27), Create 메뉴 항목 간격 19.4 px (20±1, Maya 샷 19.1), CB 행 간격 16.0 px
    (16±1, Maya 샷 16.2).
  - theme ΔE00 0/38 > 5, viewport 8/10 < 5 (면 채움 1.2 ✓ 로 회복, 비선택 와이어 6.9 → 5.8, 매니퓰레이터 Z 5.1 ✗ 새로), 큐브 3/3,
    pixels 29 중 ΔE>5 9 + kit 에 없음 9, rects 1/12 (레이아웃 단계 몫).
- 스크린샷 직접 확인: `crop_channel_box.png` (각진 필드, Segoe UI, 16 px 행 — Maya 와 나란히 같은 높이), `12_create_menu.png` (Create 메뉴 크기·
  항목 간격 Maya 와 같음, 그림자 없음).

## 남은 것

- 매니퓰레이터 Z ΔE 5.1: 실효 배율 1.0 에서 기즈모 선이 1 px 로 얇아져 배경과 섞임 (Maya 화살표 선이 더 굵음) — 매니퓰레이터 모양
  (PLAN 「Later candidates」).
- 비선택 와이어 5.8: 안티에일리어싱을 꺼도 Blender 의 1 px 와이어가 #111a5f (Maya #000460) — 오버레이 와이어 밝기/두께 (step 47 선택 와이어에서 함께).
- 실행 중 모니터 배율이 바뀌면 밀도는 처음 계산한 값 그대로 (옵션을 껐다 켜면 다시 계산) — delegated, manual_checks.
- Blender 고유 위젯 (체크박스·숫자 필드 화살표·패널 헤더) 의 모양은 테마로 바꿀 수 없는 부분이 남음; Layer Editor / Outliner 크롬은 step 48.
- 메뉴 영역 탐지 (`colour_area`) 는 kit 메뉴 배경 #535353 에 의존 — 테마 메뉴 색을 바꾸면 `look_data.MENU_BG` 도 바꿀 것.
