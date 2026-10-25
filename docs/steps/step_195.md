# Step 195 — Channel Box and Time Slider look (backlog.json #3, audit 14 B #1 #2)

## 계획

차이 (재점검 14차 레인 B §5c 3 / 2, `research/maya/screens/compare_audit192_s100/crop_channel_box.png`, `crop_time_slider.png`):
Maya dock 배경 #444444 · 값 칸 #2b2b2b · shape 줄 #373737 막대 · 굵은 머리글 · 오른쪽 위 아이콘 3 개; kit = Blender 테마 Properties
#303030 · 칸 #1d1d1d · 평평한 shape 줄. Time Slider: Maya 현재 시간 칸 #525252 (`research/maya/screens/11_channel_box.png` (22, 800)),
kit = Blender 파란 말풍선 + 선 (C overlay) 밑의 kit 칸 #606060.

측정 / 제약:
- kit 는 테마를 싣지도 쓰지도 못함 (step 130, decision 13). Python 은 패널 뒤에 못 그림 (UI region 은 POST_PIXEL 만, step 112).
- 머리글 굵게: UILayout 에 굵은 글꼴이 없음; 위치를 알아 blf 로 겹쳐 그리면 글자 위치가 1 px 만 어긋나도 번짐 → 안 함 (delegated).
- Blender 현재 프레임 말풍선 + 선: `ED_time_scrub_draw_current_frame` / cfra 선은 region overlay 로 모든 Python handler 뒤에 그려지고
  색은 테마 Dope Sheet "Current Frame" — RNA 스위치도 테마 없는 방법도 없음 (step 186 probe 그대로) → 기록만.

결정 (delegated):
- **dock 를 Maya 회색으로 들어 올림**: dock region (STACK / CHANNEL_BOX / ATTRIBUTE_EDITOR / MODELING_TOOLKIT 역할) 의 POST_PIXEL 에
  ADDITIVE 회색 한 겹 = Maya #444444 − 테마 Properties 배경 (공장 테마 +0x14). 배경 #303030 → #444444, 값 칸 #1d1d1d → #313131 (Maya
  #2b2b2b), 글자는 거의 흰색 그대로. 테마가 Maya 보다 밝으면 하지 않음. add-on 설정 `maya_dock_colors` (기본 켬). 탭 띠도 같은 회색.
- Layer Editor 목록 몸통 (Maya #2a2a2a ≈ 테마 #262626) 은 들어 올리지 않음: 그린 픽셀 한 줄 (region 아래쪽) 로 좌우, 왼쪽 안쪽 한 열로
  위를 찾아 그 사각형을 비움 (`_list_hole`; 목록 안 선택 줄은 끊지 않게 gap 허용).
- SHAPES 의 shape 이름 줄 = 테두리 있는 필드 (Maya 의 shape 줄 막대는 이름 바꾸기 칸) → #313131 막대 (Maya #373737).
- Time Slider 현재 시간 칸: Maya 측정 #525252 = #2b2b2b 위 흰색 18.4 % (step 186 의 추정 25 % 가 #606060 이었음).
- look_compare: dock 표본 (cb_bg / cb_field / cb_shape_row / layer_editor_list) 과 새 `time_slider_current` 를 kit-drawn 으로;
  `cb_input_row` 의 Maya 어두운 막대는 Channel Box 가로 스크롤바 → kit 에 없음 (None).

레인: 한 화면 영역 (dock 그리기 + 표본 + 측정) 이라 순차 (delegated) — look_compare GUI 와 헤드리스만 병렬.

## 한 일

- `src/allset/ui/maya_dock.py`: `dock_lift`, `draw_tint` (+ `_list_hole`, `dark_span`, `dark_top`, `_around`), 탭 띠 색도 들어 올린 회색.
- `src/allset/preferences.py`: `maya_dock_colors` (Viewport / display 상자에).
- `src/allset/ui/channel_box.py`: shape 이름 줄 emboss.
- `src/allset/ui/time_slider.py`: `RULER_CURRENT` 알파 18.4 %.
- `tools/look_data.py`: KIT_DRAWN + `time_slider_current` + `cb_shape_row` 점 다시 고름 + `cb_input_row` None;
  `research/maya/colors.json` ui_samples `time_slider_current` (#525252).
- 테스트: 새 `tests/test_step195_cb_look.py` (4 개: lift = Maya 회색 / 설정 끄면 0, 밝은 테마는 안 함, 목록 구멍 기하, 현재 칸 = #525252).

## 검증

- look_compare `ALLSET_GUI_UI_SCALE=0.8` (실효 1.0, `research/maya/screens/compare_s195_s100/`): kit-drawn **12 / 12** within ΔE00 5 —
  cb_bg #444444 **0.0** (전 6.5 ✗), cb_field #313131 1.9 (전 4.4), cb_shape_row #313131 1.9, layer_editor_list #262626 1.3 (목록 구멍),
  time_slider_current #525252 **0.0**; viewport 20 / 20, checks 9 / 9. crop_channel_box 직접 봄 (Maya 와 같은 회색 판, shape 막대).
- 1.25 (`compare_s195_s125/`): kit-drawn 11 / 12 — `time_slider_current` 만 ✗ (1.25 에서 Time Slider region 이 낮아 Blender 말풍선이
  현재 칸을 거의 다 덮음; 같은 C overlay 한계), dock 표본 4 개는 1.0 과 같은 값.
- 헤드리스 전체 4.5: **1740 / 1740** (217 파일). GUI `-k step135,step186,step142,step148,step116,step158`: **75 / 75** (7 파일).
- dogfood (UI 1.0): **48 / 48**, 콘솔 0; `11_attribute_editor.png` AE #444444, `09_channel_box.png` Layer Editor 목록 #262626 그대로.

## 남은 것

- Maya 굵은 머리글 (pCube1 / SHAPES / INPUTS), CB 오른쪽 위 아이콘 3 개 (kit 은 세로 탭 띠), 라벨 글자색 (Maya #bbbbbb, kit 흰색 가까움):
  UILayout 한계 / 설계 차이로 남김.
- Blender 현재 프레임 말풍선 · 파란 선: C overlay + 테마 색이라 못 끔 (step 186 그대로). Maya 칸은 그 아래에 #525252 로 그려짐.
- Tool Settings dock · Hypershade 창 칸은 아직 들어 올리지 않음 (Maya 도 #444444).
- 실제 사용 느낌 → manual_checks 「Step 195」.
