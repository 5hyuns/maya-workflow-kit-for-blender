# Step 73 — 타임 슬라이더 키 틱 + Range Slider 드래그

## 계획 (delegated)

재점검 4차 (step_71.md): kit 타임라인은 키를 찍어도 표시가 없다. Range Slider 바는 버튼일 뿐 끌 수 없다 (step_50.md:67).

### Maya 실측 (Maya 2022 GUI, `research/scripts/maya_ts/ts.py`, 화면 `research/maya/screens/ts/`, 저장소 밖)

| 항목 | 값 |
|---|---|
| 키 틱 색 | `displayRGBColor timeSliderKey` = (1, 0, 0) [O], screens/_maya_ui_dump.json |
| 브레이크다운 색 | `timeSliderBreakdown` (0, 1, 0) [O] |
| 틱 폭 | 1 px (`timeSliderTickSize 1`, PREF createPreferencesOptVars.mel:477) |
| 틱 높이 | timeControl 전체 높이 (y 793–820, 28 px) [O] |
| 어떤 키를 보이나 | 선택된 노드 (`timeSliderShowKeys "active"`, PREF:473; ui_layout.md:278) |

틱 위치: ts_01_window.png 에서 키 1·12·24 가 x 18.7 / 136 / 264 (10.67 px/프레임) 이다. 틱은 프레임 눈금 위치에 그려지고, 프레임 칸의 가운데가 아니다.

Range Slider (`rangeControl`, ts_01 의 y 836–860):

- 트랙 #373737 이 애니메이션 범위 (1–200) 전체 폭이다.
- 재생 범위 (1–120) 는 둥근 구간 #5d5d5d 다 (x 207–574).
- 구간 양끝 안쪽에 손잡이 사각형 #919191 이 있다 (13×14 px, 끝에서 5 px 안).
- 시작·끝 숫자는 손잡이 옆, 밝은 회색이다.

### 1. 키 틱 (`ui/time_slider.py`)

- `key_frames(nodes)`: 순수 함수 (bpy 객체만 읽음).
  - 입력은 `channel_box.targets` 노드의 F-curve (`time_keys.node_fcurves`: 뼈는 자기 `pose.bones["n"]` 커브만).
  - 결과는 [(frame, is_breakdown)] 정렬. 같은 프레임은 하나로 합치고, 한 커브라도 보통 키면 빨강이다.
- 그리기: 기존 Dope Sheet WINDOW POST_PIXEL 핸들러 (`_draw_range`) 옆에 둔다. TIMELINE 모드에서만 그린다.
  - x = `view2d.view_to_region(frame)`.
  - 폭 max(1, round(ui_scale)) px, 지역 전체 높이.
  - 빨강 / 초록.

### 2. Range Slider 바 (`ui/range_bar.py`, 새 모듈)

헤더 레이아웃 안의 위치는 Python 으로 알 수 없다. 그래서 바 자리에는 빈 `label` (ui_units_x 18) 을 둔다. 버튼이면 UI 가 LMB 를 먹으므로 label 이어야 한다.

- 헤더 POST_PIXEL 핸들러가 자기가 그리기 전에 헤더 가운데 한 줄을 `gpu framebuffer.read_color` 로 읽는다.
  - 실측: 헤더 지역 좌표로 읽힌다. 바탕색 run 과 필드 run 이 그대로 보인다.
  - 바탕색 (x=2 픽셀) 이 아닌 구간들 중 3 번째 뒤의 첫 넓은 바탕색 run 이 바 자리다: [편집기 종류][start][playback start] → 바.
  - 순수 함수 `bar_span(row, bg, min_w)`.
- 그 자리에 Maya 바를 그리고, 사각형을 (창, 영역) 포인터별로 기억한다.
  - 트랙은 애니메이션 범위, 구간은 재생 범위다. `use_preview_range` 가 꺼져 있으면 재생 범위 = 애니메이션 범위.
  - 손잡이 두 개, 숫자 두 개.
- MayaKit 레이아웃 (`has_slider_panel`, 헤더에 transport 없음) 에서만 이렇게 한다.
  - 다른 타임라인 헤더는 지금처럼 토글 + 버튼이다. 앞에 늘어나는 spacer 가 있어 위치 찾기가 맞지 않는다 [delegated].
- Maya 에 없는 `use_preview_range` 토글 버튼은 이 모드에서 뺀다.
  - 대신 바를 끌면 켜진다.
  - 바 더블클릭 = 전체 애니메이션 범위 ↔ 재생 범위 전환 (`use_preview_range` 토글) [K: Maya 바 더블클릭].

### 3. 드래그 (`maya_kit.range_bar_drag`, 모달)

- "Screen" 키맵에 LMB PRESS 와 DOUBLE_CLICK 을 넣는다.
  - 헤더의 빈 label 위 LMB 는 지역 핸들러가 먹지 않아 창 키맵까지 온다.
  - 기억한 바 사각형 밖이면 PASS_THROUGH 한다.
- 영역 판정 `zone(x)`: 순수 함수.
  - 손잡이 (또는 구간 끝에서 손잡이 폭 안) → START / END.
  - 구간 안 → MOVE.
  - 구간 밖 트랙 → None (PASS_THROUGH) [delegated].
- 드래그 `drag_range(zone, start_range, dframes, s, e)`: 순수 함수.
  - MOVE 는 길이를 지키고 [s, e] 안에 머문다.
  - START / END 는 반대쪽 끝을 넘지 않는다 (최소 길이 1 프레임).
  - 프레임은 정수다 (마우스 dx / 프레임당 px, 반올림).
- 끝: 놓으면 FINISHED + UNDO, ESC / RMB 는 처음 값으로 되돌린다.
- 재생 범위가 바뀌면 msgbus 가 타임라인을 다시 맞춘다 (step 20, 이미 있음).
- 다른 사각형 판정용 상태는 `_bars` 에 둔다.
  - 영역 포인터가 해제되고 재사용될 수 있다.
  - 그래서 이벤트 때 `context.area` 가 같은 포인터이고, 그 영역이 실제 TIMELINE 헤더를 가진 경우에만 쓴다.

### 검증

- 헤드리스: `key_frames` (오브젝트, 뼈, 브레이크다운, 중복), `bar_span`, `zone`, `drag_range`.
- GUI:
  - MayaKit 레이아웃에서 S 키 1·12 → 타임라인 스크린샷에서 그 프레임 x 픽셀이 빨강.
  - 바 구간 가운데 드래그 → 미리보기 범위가 같은 길이로 이동.
  - 끝 손잡이 드래그 → 끝만 바뀜. 더블클릭 → 전체 범위.
- 전체 테스트, dogfood, manual_checks.

## 한 것

- 키 틱 (`ui/time_slider.py`):
  - `key_frames(nodes)`: Channel Box 노드의 키를 모은다. 같은 프레임은 합치고, 보통 키가 하나라도 있으면 빨강이다.
  - `_draw_keys`: Dope Sheet WINDOW POST_PIXEL 에서 TIMELINE 만 그린다. 빨강 / 초록 1 px (ui 배율만큼), 지역 전체 높이.
- Range Slider 바 (`ui/range_bar.py`, 새 모듈):
  - MayaKit 레이아웃 타임라인 헤더에서는 바 자리가 빈 label 이다. Blender 의 미리보기 토글과 버튼은 빠졌다.
  - HEADER POST_PIXEL 이 헤더 한 줄을 읽어 자리를 찾는다 (`bar_span`). 그 자리에 Maya 바 (트랙 / 구간 / 손잡이 / 숫자) 를 그리고 사각형을 기억한다.
- `maya_kit.range_bar_drag`:
  - "Screen" 키맵 LMB PRESS / DOUBLE_CLICK 이다.
  - 그 키맵에 LMB 를 쓰는 편집기 키맵들은 shadows 로 적었고, 이 아이템 아래에 둔다. 처리되지 않은 클릭만 온다.
  - 구간 = 이동, 손잡이 = 그 끝, 트랙의 빈 곳 = 통과.
  - ESC / RMB 는 취소한다. 움직이지 않은 클릭은 undo 단계를 남기지 않는다.
  - 더블클릭 = `toggle_whole` (전체 범위 ↔ 재생 범위).
- 다른 타임라인 (transport 가 헤더에 있는 경우) 은 예전 토글 + 버튼 그대로다 [delegated].
- `TIME_SLIDER_SHADOWS` 에 "Screen" 을 넣었다 (time_scrub LMB 가 새 Screen 아이템보다 먼저다).
- Maya 실측 스크립트 `research/scripts/maya_ts/` + `research/maya/screens/ts/` (저장소 밖, 출력 폴더 이름을 assert 한다).
  `research/maya/ui_layout.md` §4.10 / §4.11 에 측정값을 더했다.

## 검증

- 헤드리스 `python tests/run.py`: **589/589** (68 파일; 새 `test_step73_time_slider.py` 8).
  - key_frames: 오브젝트, 브레이크다운 합치기, 뼈별 커브.
  - bar_span, zone / segment, drag_range, set_playback 순서, 더블클릭 토글.
- GUI `python tests/gui/run.py`: **504/504** (56 파일). 새 `gui_step73_time_slider.py` 8:
  - 스크린샷 픽셀: 프레임 12 = (255, 0, 0), 프레임 20 = 바탕.
  - 헤더에서 바를 찾았다 (x 291–743).
  - 구간 30 프레임 드래그 → 1–120 이 31–150.
  - 끝 손잡이 −40 → 31–110.
  - 움직이지 않은 클릭 = 변화 없음.
  - 더블클릭 동작 → 전체 범위. 타임라인이 1–200 을 보여 준다.
- `python tools/dogfood.py`: **47/47**, 콘솔 0.
- 스크린샷 직접 확인:
  - `gui_step73_ticks.png`: 1 · 12 빨간 선, 바 1–120 (손잡이·숫자).
  - `gui_step73_range_moved.png`: 구간 31–150, 타임 슬라이더 30–150.

## 남은 것

- 더블클릭은 이벤트 시뮬레이션이 DOUBLE_CLICK 을 만들 수 없어 동작 함수만 테스트했다. 다른 UI 배율에서 바 위치는 확인하지 않았다 → `docs/manual_checks.md` 「Step 73」.
- Maya 의 선택된 키 (timeSliderActiveKey 노랑), 사운드 파형, 애니메이션 범위 바깥 영역으로 바 늘리기 [K]: 없음.
- Shift 범위 안의 키 끌어 옮기기 / 늘이기 (step_56.md:113) 는 그대로 남았다.
- 반복 모드 once / oscillate 없음 (Blender).
