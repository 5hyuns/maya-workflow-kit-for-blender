# Step 186 — Time Slider ticks and playhead (backlog_183.json #4, audit 13 #4)

## 계획

문제 (`docs/steps/step_182_quant.md` §5c-9, 아홉 번째 지적): kit Time Slider = Blender 의 큰 숫자 (5 프레임마다) + 파란 현재 프레임
말풍선, Maya 2022 = 작은 회색 숫자 + 눈금, 회색 현재 시간 칸.

먼저 잰다:
1. Blender 쪽 (GUI 프로브 `tmp/probe186/gui_probe186.py`): Time Slider WINDOW 에 POST_PIXEL 로 영역 전체를 칠하면 무엇이 남는가.
2. Maya 쪽 (GUI Maya 2022, `research/scripts/maya_ts186/`, 세 번): 위젯 폭 692 / 892 / 1292 / 1592 px × 범위 1-2 … 1-100000 의 43 경우,
   현재 시간 칸, 북마크 + 키 (`research/maya/re/time_slider_186.md`).
3. 그 결과로 Maya 자를 kit 이 직접 그린다 (Maya Workflow Kit 레이아웃의 Time Slider = 사이드바가 있는 TIMELINE).

레인: Maya 측정 (GUI Maya 1 개) 과 kit 그리기 (GUI Blender) 를 겹쳐 돌림 — Maya 세션이 도는 동안 프로브 · 코드; 측정이 규칙을 정하므로
step 규칙만 측정 뒤.

## 측정

- **Blender**: 영역 전체 POST_PIXEL 칠하기가 숫자 · 격자 · 프레임 선을 모두 가린다; **현재 프레임 상자 (파란 말풍선) 만** 위에 남는다 —
  Blender 가 region overlay (`draw_overlay`) 에서 모든 Python 핸들러 뒤에 그림. 끌 RNA 없음 (`SpaceDopeSheetEditor` 속성 목록),
  테마는 kit 이 못 씀 (결정 13), `draw_cursor_add` 는 마우스 아래 영역만 → **숨길 수 없음** (기록).
- **Maya** (1.0 배율, 32 px 위젯): 배경 #2b2b2b, 아래 3 px 띠 #373737, 눈금 = step 마다 2 px #7c7c7c (행 13-27), 칸 왼쪽 끝; 모든
  눈금에 라벨 #757575 (행 1-8, 눈금 + 2 + 0.2 × 프레임 폭); 프레임 사이 작은 눈금은 **없음** (backlog 의 「프레임마다 눈금」 은 프레임
  폭이 넓을 때 step 1 인 것); 현재 시간 = 그 프레임 칸 흰색 25 % (전체 높이) + 흰 번호 (행 16-23); 키 = 눈금 자리 빨강 1 px; 북마크 =
  위 띠 #454545 (행 0-8) 에 색 80 % (행 0-4) + 왼쪽 1 px 선, 라벨 · 눈금이 아래로.
- **step**: 1, 2, 5, 10, 20, 50 … 중 라벨이 들어가는 가장 작은 것 — 그러나 한 가지 임계값으로 43 경우를 다 설명할 수 없음 (폭 · step 에
  따라 다름, 4 / 400 / 4000 도 씀) [U]. REA 는 이 PC 에 deep provider 가 없어 추적 못 함.

## 한 일

- `src/allset/ui/time_slider.py`: `_draw_ruler` (Maya 레이아웃 Time Slider 에서만, `has_slider_panel`) — 배경, 띠, step 눈금 + 라벨,
  현재 시간 칸 + 흰 번호, 북마크 띠 (`operators/bookmarks.py` 마커 = kit 북마크, 색 = 측정한 (204, 92, 92), Maya 는 무작위 — delegated);
  Maya 32 px 의 행을 영역 높이에 비례 (`ROWS`, `ROWS_BOOKMARKS`, `_rows`). step = `tick_step` (임계값 max(25, 7 × 자릿수 + 3) px ×
  UI 배율, 끝 앞 라벨의 자릿수; Maya 43 경우 중 32 일치, 기본 1-120 · 짧은 범위 정확, 어긋나는 11 경우는 `STEP_DEVIATIONS`). 1-2-4
  step 격자 탐색이 33 을 맞췄지만 1-120 을 4 프레임마다 그려서 안 씀 (delegated).
- 프레임 칸 = kit 의 기존 규칙 [f − 0.5, f + 0.5] (`frame_at` 반올림, Shift 범위와 같음), 눈금 = 칸 왼쪽 끝. Maya 레이아웃에서 키 눈금도
  그 자리로 (`key_x`; Maya 키는 눈금 위), 북마크가 있으면 띠 아래까지만. 현재 프레임의 키를 감싸는 #38 처리 (Blender 상자 둘레) 는 그대로.
- `tools/look_data.py`: `time_slider_bg` 를 kit-drawn 으로. `tests/gui/gui_step73_time_slider.py`: 키 눈금 위치 = `key_x`.
- 테스트 `tests/test_step186_time_slider.py` (Maya 43 경우 표, 행 배치, playback 범위). `docs/manual_checks.md` Step 186.

## 검증

- look_compare UI 1.25: checks 9/9, kit-drawn **7/7** (`time_slider_bg` 이제 kit: Maya #2b2b2b vs kit #303030 ΔE 1.6), viewport 20/20.
  UI 1.0 (`ALLSET_LOOK_TAG=s186_s100`): checks 9/9, kit-drawn 7/7, viewport 20/20. crop `research/maya/screens/compare*/crop_time_slider.png`:
  Maya 와 같은 5 프레임 step, 작은 회색 라벨 + 눈금, 아래 띠 (파란 Blender 상자만 남음). 1.0 의 kit 영역은 36 px (Maya 32) → 라벨 9 px.
- 헤드리스 전체 **1696 / 1696** (+3 새). GUI `-k step56,step73` **17 / 17**.

## 남은 것

- Blender 의 파란 현재 프레임 상자는 Python 으로 숨길 수 없음 (C overlay) — Maya 칸 · 번호 위에 그대로 보인다. 없애려면 Time Slider 를
  overlay 가 없는 편집기 (shelf 처럼 Image Editor 띠) 로 옮겨 kit 이 전부 그려야 함 (레이아웃 · step 56 / 73 / 118 영향, 큰 일) — 후보.
- step 규칙의 폭 의존 [U] (11 / 43 어긋남).
