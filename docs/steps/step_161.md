# Step 161 — Viewport messages and views

Backlog `autodrive_bmk/backlog_155.json` #7: the step-154 dogfood differences G1–G4 (docs/steps/step_154.md:33-36) and
the look_compare marking-menu samples.

## 계획

- G1 결과 글: Maya 는 명령 결과를 Command Line 결과 칸 (`// Result: group1`) 에 보이고 Help Line 위로 뜨는 것은 없다
  (research/maya/ui_layout.md:111, :290-293). 킷 INFO 보고 99 곳 → `src/allset/results.result(op, text)` →
  `command_line.show_result`. WARNING / ERROR 는 보고로 둠 (Maya 경고 · 오류도 Help Line / Command Line 에 색으로).
  남기는 INFO: 도구 사용 힌트 3 곳 (Quad Draw ×2, 3D Cut and Sew — Maya 는 도구 도움말을 Help Line 에, 킷 레이아웃에서
  Blender 보고 배너 자리가 Help Line) 과 Script Editor 의 echo (기록 창 = Blender Info 편집기가 보고를 나열). delegated.
- G2 RMB 목록: Maya 는 목록을 한 열로 둔다 (14_marking_menu_object.png 에서 창 아래로 넘침). `engine.fit_ring`: 링 아래에
  들어가면 그대로, 아니면 **한 열로 링 옆**, 그다음 위, 창보다 길 때만 여러 열 (step 52 방식). 위로 밀면 S 상자 · 제스처를
  덮으므로 옆 (delegated). 옆 = 가는 길에 방사 하위 메뉴가 없는 쪽 (RMB 메시: E = UV 하위 메뉴가 길에서 열림 — GUI 에서
  측정, 그래서 W 쪽). 영역 경계를 피해 옮긴 뒤 링과 겹치면 다른 쪽.
- G3 네 뷰: Blender 는 새 quad 칸에 단일 뷰의 위치 · 거리를 준다 (측정: F 뒤 1 cm 큐브 → 3 단위 폭). Maya 직교 카메라는
  orthographicWidth 30 이고 자기 pan / zoom 을 기억 (16_four_view.png: 1 단위 큐브 ≈ 16 px / 495 px 칸 ≈ 31 단위).
  들어갈 때 각 직교 칸 = 기억한 (위치, 거리) 또는 Maya 기본 (원점, 30 단위), 나올 때 기억. Blender 정사영 폭 (긴 변) =
  view_distance × 72 / lens (GUI 측정 3 cm, lens 70 → 3.086). 머리줄 하나 = 툴팁 알림 (`view.FOUR_VIEW_NOTE`).
  16_four_view.png 를 확대해 보니 **Maya 는 top / front / side 칸 모두 칸 전체에 자기 평면 격자** — step 45 의
  "front / side 는 격자 없음" 은 잘못 읽은 것: 축 정사영 뷰는 그 평면에, 보이는 범위 전체에 (`maya_grid.span_segments`).
- G4 와이어: dogfood 09 재현 = pCube2 (pCube1 의 자식, x 3) 가 side 뷰에서 pCube1 앞을 가림. Maya 는 선택한 부모의 자손 전부를
  가장 가까운 선택 조상의 색으로 그린다 (research/maya/screens/parent/parent_03_parents_selected.png: group1 선택 → 자식 흰색,
  lead pCube2 → 자식 pCube3 초록) → `selection_wire.highlighted`.
- (5) look_data KIT_POINTS: marking_menu_box / marking_menu_list_bg 가 킷 쪽에서 뷰 배경 #5c5c5c 를 읽어 ΔE 3.5 로 우연히
  통과하고 있었음 → step 151 링 · 한 열 목록 기준으로 다시 고름.
- 레인: 네 항목이 서로 다른 파일이지만 각자 GUI 측정이 필요하고 Blender 동시 2 개 제한 — 메인에서 G3/G4 → G1 → G2 → (5)
  순서로, 헤드리스 전체는 별도 sandbox 로 동시에.

## 한 것

- G1: `src/allset/results.py` (새), INFO 보고 99 곳 → `results.result` (52 파일). Group 결과 = Maya `Result: group1`.
  Command Line 줄이 결과 칸을 창 밖으로 밀고 있었음 (고정 UI 단위 33.75 + 45.75 = UI 1.25 의 1600 px 창에서 1988 px):
  `command_line.units_for` 가 Maya 비율 (675 / 915 / 입력 335 px of 1600) 을 상태 줄 폭에 맞춰 나눔, 언어 버튼 · 결과 칸 폭
  고정 (결과 글이 버튼을 밀지 않게). `tools/look_shots.py` 도 같은 폭.
- G2: `marking/engine.fit_ring` (위 계획), 테스트 `test_step52_hotbox_rmb.test_rmb_list_under_the_ring` 새 규칙,
  `gui_step129_marking_bounds` 는 Time Slider 위 줄 = Assign … Material cascade (열림 확인), `gui_step151_ring` 은 아래 21 px
  또는 옆 한 열.
- G3: `operators/view.py` `ortho_key` / `maya_ortho_distance` / `remember_ortho` / `maya_ortho_panes`, Space tap · Panels >
  Layouts · 핫박스 단일 뷰가 사용. 알림: `panel_menus.TIPS["LAYOUT_FOUR"]`, Tool Box Quick Layout Four View 설명, 연산자 설명.
  `ui/maya_grid.py`: `plane_for_view` 가 축 정사영 뷰 평면, `fills_view` / `span_segments` / `view_span` (청크 단위 캐시).
- G4: `ui/selection_wire.highlighted` (자손 = 가장 가까운 선택 조상의 lead / other 색).
- (5): `tools/look_data.py` marking_menu_box (-33, -55), marking_menu_list_bg (-200, -141), command_line_field 300,
  help_line_bg 530, command_result_field 새 표본 (전에는 "no result field").

## 검증

- 헤드리스 새 테스트: `test_step161_messages` 3/3 (남은 INFO 보고 = 힌트 목록과 정확히 같음, 결과 칸, Group 결과),
  `test_step161_views` 2/2 (계층 강조 색, 정사영 키 · 폭), `test_step45_grid.test_ortho_grid_fills_the_view`.
- 헤드리스 전체 **1498 / 1498** (G2 첫 버전 뒤), 마지막 수정 뒤 다시 전체 **1498 / 1498**.
- GUI 스모크 + step 161 마지막: `-k step161,step7_top_ui,step151_tooltip,step147_hud,step150_view,step132_new_scene,
  step124_welcome,step49_layout` 71/71.
- GUI: `gui_step161_views` 12/12 (정사영 칸 30.0 단위 ×3, 칸마다 격자 가장자리까지, side 확대 뒤 lead 초록 1.00 + 자식 초록
  1.00, side 줌 60 기억 · 나머지 30), `gui_step161_messages` 8/8 (Group 뒤 Help Line 변화 0.000, 결과 칸에 글자, RMB 낮게 = 한 열,
  링과 안 겹침, 링 왼쪽, 창 안). 바뀐 모듈 관련 GUI 20 파일 197/202 → 실패 5 는 옛 여러 열 전제 검사, 고친 뒤
  `step129_marking_bounds, step151_ring, step136_edges, step136_items, step161_messages, step9_hotbox` 69/70 + ring 13/13.
- look_compare: kit-drawn **6 / 6** (marking_menu_box / list_bg 이제 실제 상자 #535353, ΔE00 0.3 — 전에는 배경 #5c5c5c 3.5),
  rects 3 → 5 / 12 (상태 줄 폭), Command Line 결과 칸 표본 생김 (no kit element 2 → 1).
- 스크린샷 직접 확인: `tmp/s161/gui_step161_quad_125.png` (Maya 16_four_view 와 같은 배치 · 격자), `..._rmb_low_125.png`,
  `sb_after_group.png` ("Result: group1").
- GUI 전체 묶음은 훅이 막음 (릴리스 준비 때만) — 규칙대로 관련 파일만.

## 남은 것

- 정사영 칸 이름표 "top -Z" / "front +Y" 는 Maya "top -Y" / "front -Z" 와 다름 (Y-up 축 표기) — 범위 밖.
- 정사영 격자는 아주 멀리 줌아웃하면 (선 4000 개 넘음) 그리지 않음; Maya 가 그때 어떻게 줄이는지 측정 안 함.
- 링 옆 목록은 Maya 에 없는 배치 (Maya 는 화면 끝에서 Qt 가 메뉴를 옮김; 킷은 창 안에서 링을 가리지 않게) — manual_checks.
- `gui_step129_panel_toolbar` 머리 폭 의존 실패, Modeling - Expert 뷰포트 머리줄의 Blender 위젯 (step 160 에서 알려짐) 그대로.
