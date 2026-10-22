# Step 137 lane GRAPH — Graph Editor 값 눈금을 표시 단위로 (#66)

계획: docs/steps/step_137.md 「계획」 Graph Editor 결정. 근거: docs/steps/step_133_work.md A1,
research/maya/screens/editors104/graph_editor_win1.png (Maya 는 0 – 5).

## 결정 (delegated)

- **결정 1 · 8 유지** (main session, delegated): 템플릿은 m + cm 표시 그대로, scale_length 0.01 로 바꾸지 않는다. 정확한 길은
  add-on 설정 「Maya Units」 로 남는다. 킷은 Graph Editor 의 값 숫자만 표시 단위로 다시 적는다.
- **덮는 방법 (delegated, 이 lane)**: 계획의 「POST_PIXEL 로 Blender 숫자 칸을 덮는다」 는 안 된다. Blender 4.5 는 값 숫자를
  WINDOW region 의 *overlay* 에서 그린다 (Blender 소스 space_graph.cc:352-358 `graph_main_region_draw_overlay` →
  view2d_draw.cc:340-400 `draw_vertical_scale_indicators`). overlay 는 region 의 Python POST_PIXEL 다음에 그려진다 — 빨간 사각형으로
  측정: 숫자가 그 위에 남음 (tmp 실험 shot). overlay 다음에 그려지는 Python 그림은 `WindowManager.draw_cursor_add` (paint cursor,
  wm_draw `wm_paintcursor_draw`) 뿐이고, Blender 는 이것을 **마우스 아래 region** 에만 그린다. 그래서:
  1. POST_PIXEL (`_snapshot`) 이 Blender 와 같은 계산으로 숫자 위치 · 글자를 구하고, 숫자 칸 띠의 region 픽셀 (overlay 전) 을
     `read_color` 로 텍스처에 보관;
  2. draw cursor (`_cursor`) 가 Blender 숫자 상자만 그 픽셀로 다시 붙이고 (다른 픽셀은 그대로), `값 / maya_unit()` 을 Blender 와
     같은 모양 (기본 글꼴 11 pt × UI scale, `wcol_scroll.text`, `TH_BACK` 외곽선, x = 8 px × scale, y = 선 − (높이 "0"/2 − pixel_size))
     으로 적는다.
  - draw cursor 의 투영은 GLA_PIXEL_OFS (0.375 px) 만큼 밀려 있어 글자 · 붙인 픽셀이 흐려졌다 → 정확한 pixel ortho 를 load
    (Blender 글자와 픽셀 차 합 ~260 / 라벨, 이전 ~7400).
  - 텍스처는 sRGB→linear 변환 없이 'IMAGE' 로 (window framebuffer 에서는 변환이 없음: 변환하면 어두워짐, 측정).
  - draw cursor 는 마우스가 움직일 때마다 창을 다시 그리게 하므로 Graph Editor 가 열려 있을 때만 등록 (`_sync` 0.5 s timer).
- 눈금 간격: Blender 와 같은 규칙 (`continuous_value_scales`, 최소 `view2d_grid_spacing_min` × scale px, view2d_draw.cc:40-67) 으로
  계산 → cm 는 ×100 이라 같은 선에 정수가 붙는다 (0.01 BU → 1). 글자 형식은 표시 단위 step 에 Blender 규칙 (`view_to_string__value`),
  int() 잘림 대신 반올림. inch / ft 처럼 10 의 거듭제곱이 아닌 비율은 step 의 유효숫자 3 자리.
- 적용 조건: FCURVES 모드, 정규화 꺼짐, `maya_unit() != 1`, `context.visible_fcurves` 가 모두 RNA unit 'LENGTH'
  (4.5 F-curve 의 id_data 는 Action → 그 Action 을 쓰는 ID 에서 path 를 풀어 unit 확인; 사용자 속성 = 단위 없음).
  길이 · 회전 · 배율이 섞이면 Blender 숫자 그대로. 마킹 메뉴가 떠 있으면 붙이지 않는다.

## 한 것

- 새 `src/allset/ui/graph_units.py` (bpy-free 계산 `major_step` / `tick_indices` / `blender_label` / `display_label` / `labels` /
  `all_length`, `curve_units`, `factor`, POST_PIXEL `_snapshot`, draw cursor `_cursor`, `_sync`), `ui/__init__.py` 등록.
- `tests/test_step137_graph_units.py` (7), `tests/gui/gui_step137_graph_units.py` (7 check).

## 검증

- `python tests/run.py -k step137,step104,step70,enable_disable`: **30 passed, 0 failed** (4 files).
  추가로 `-k step130,step114,step118`: 28 passed (package scan / guidelines / compat).
- `python tests/gui/run.py -k step137_graph,step104,step70`: UI scale 1.25 **24 passed, 0 failed**; `ALLSET_GUI_UI_SCALE=0.8`
  (실효 1.0) **24 passed, 0 failed**.
- GUI check (두 scale 모두): 라벨 `['0','1','2','3','4','5']`; 각 라벨 중심이 Blender 격자선에서 ≤ 0.6 px; Blender 의 "0.05" 가 있던
  자리 (cm 글자 오른쪽) = overlay 전 픽셀과 차 0.0; 라벨 띠 옆 열은 Blender shot 과 차 0.000; Translate X + Rotate Z 는 Blender 숫자.
- shot 직접 확인 (`--shots`): `gui_step137_graph_blender_numbers.png` (채널 위 마우스 = Blender 0.00–0.05),
  `gui_step137_graph_cm_numbers.png` (곡선 위 마우스 = 0–5, 격자선 위, 갈색 범위 밖 음영 · 격자 · 키 점 그대로),
  `gui_step137_graph_mixed.png` (0–50 도, Blender 그대로).

## 남은 것

- 마우스가 같은 창의 다른 region (Graph Editor 채널 목록 · 헤더, 또는 Graph Editor 가 있는 창의 다른 편집기) 위에 있으면 Blender
  숫자 (m) 가 보인다 — draw cursor 한계. 곡선 영역에서 창 밖으로 바로 나가면 relabel 이 남는다 (active region 유지, 측정).
  docs/manual_checks.md 에 「Graph Editor 숫자: 곡선 위 cm / 채널 위 m 전환이 거슬리는지」 추가 필요 (이 lane 은 파일 제한으로 안 함).
- 길이 + 회전 / 배율이 섞여 보일 때는 Blender 숫자 (한 축에 두 단위 불가). Drivers 모드 · 정규화는 대상 아님.
- 그 밖의 overlay 요소: 플레이헤드 선이 라벨 상자를 지나가면 상자 안에서 끊긴다 (Blender 숫자도 그 자리를 덮음). (마커 · preview range 는
  region draw 안, POST_VIEW 앞에 그려져 snapshot 에 들어간다: space_graph.cc:300-318.)
- 5.x 는 확인 안 함 ('IMAGE' 쉐이더 · overlay 순서 · read_color 경계는 같은 API 지만 측정 필요).
