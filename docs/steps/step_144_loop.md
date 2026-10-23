# Step 144 LOOP — Insert Edge Loop / Offset Edge Loop / Slide Edge (GitHub #31)

## 계획

근거: Maya 동작 측정 `research/maya/re/edge_loops_144.md` (mayapy: polySplitRing / polyDuplicateEdge /
polySlideEdge), 필드·기본값 `research/maya/re/options_144.md:87-108`, `option_boxes_140.md:239-245`,
스크린샷 `research/maya/screens/options144/{insert_edge_loop,offset_edge_loop,slide_edge}.png`.

### 모듈
- `operators/edge_loops.py` (bmesh, bpy 연산자): 순수 함수 `ring(edge, side_vert)` (링 순서 + 사이 면),
  `insert_loops(bm, edge, t, mode, count, smoothing)`, `loop_path(edge)` (엣지 루프), `offset_loops(bm, edges,
  offset, mode, delete_edge, smoothing)`, `slide_sides(bm, edges)` / `slide(…)`, `snap(f, points, tol)`.
  설정 `Scene.allset_loop_tools` (PropertyGroup, Maya 공장값).
  연산자: `allset.insert_edge_loop` (LMB PRESS 모달), `allset.offset_edge_loop` (LMB PRESS 모달 + exec =
  선택 엣지), `allset.slide_edge` (MMB PRESS 모달), `allset.loop_tool_exit`.
- `ui/mesh_tools_loop.py`: WorkSpaceTool 3개 (`allset.insert_edge_loop_tool`, `allset.offset_edge_loop_tool`,
  `allset.slide_edge_tool`, EDIT_MESH, `KEYMAP_FALLBACK` = LMB 선택 유지), 툴 헤더 / Tool Settings 필드 draw.
- `ui/tool_settings.py`: INSERT_EDGE_LOOP / SLIDE_EDGE 종류를 Blender `builtin.loop_cut` / `edge_slide` 대신
  kit 툴에 연결하고 필드를 `allset_loop_tools`에 바인딩, OFFSET_EDGE_LOOP 종류 추가 (Description + Settings).

### 모달 입력
- Insert: PRESS → `mesh_tools.pick`(EDGE) → 눌린 점의 비율 t (`edge_factor`) → 즉시 루프 삽입. 드래그 =
  누를 때 저장한 메시(임시 Mesh)로 되돌리고 새 t로 다시 삽입(링 따라 슬라이드). RELEASE = 확정 (UNDO 한 단계),
  ESC/RMB = 원래대로. 아무 엣지도 없으면 PASS_THROUGH (선택 fallback). Multiple = 클릭 위치 무관 k/(N+1).
  Equal = 클릭이 가까운 쪽 끝에서 d = t·len, 최단 링 엣지로 clamp, d가 엣지 길이에 닿으면 그 정점 통과.
- Offset: PRESS → 엣지 루프 (4가 정점 통과, 경계/극점에서 멈춤), 양쪽 면이 없으면 Maya 경고. 이동 3 px 이상이면
  offset = 드래그 거리 / 눌린 엣지 옆 엣지들의 최단 화면 길이 (0.01–0.99), 움직이지 않고 떼면 0.5 (Maya optionVar
  polyDuplicateEdgeOffset). 같은 되돌리기-재실행 방식.
- Slide: MMB PRESS → 선택 엣지(없으면 경고). 각 정점의 옆 엣지 A/B를 면 기준으로 일관되게 정하고, 마우스에서
  가까운 정점의 A 방향 화면 벡터에 드래그를 투영 → f (음수면 B 쪽). Snapping: 0, ±k/(points+1) 근처
  tolerance 안이면 붙음. Relative = 각 옆 엣지 비율, Absolute = 그쪽 최단 옆 엣지 × f 거리.
  Slide는 정점 위치만 바꾸므로 원래 좌표 배열로 되돌림.

### 메뉴 / 옵션 박스
- menu_map: 세 줄을 kit 툴로 (`("tool", id, True)`). 마킹 메뉴 Insert / Slide 항목도 `_item(path)`로.
  RMB "To Edge Loop and Duplicate"(LOOP_DUPLICATE) = kit offset exec (선택 엣지 루프, offset 0.5).
- Insert ❒: step 140 창 "Insert Edge Loop Tool" 유지 (delegated: step 140 규칙 "Tool Settings 여는 박스 = 툴 이름
  창, 확인 = 툴 시작"), 값은 `allset_loop_tools`에 쓰고 kit 툴 시작. Smoothing angle 필드 추가 (이제 구현됨).
- Offset ❒: 창 "Offset Edge Loop Options" (Enter Tool And Close / Enter Tool / Close), Maya 필드.
- Slide ❒: Tool Settings (tool 종류) 그대로.

### 검증
- `tests/test_step144_loop.py`: strip/grid/cube에서 mayapy 숫자와 비교 (relative / equal / clamp / multiple,
  offset relative / equal / delete edge, slide relative / absolute / snap), 메뉴·툴·키맵 등록/해제, 창 필드.
- `tests/gui/gui_step144_loop.py`: 실제 뷰에서 클릭 → 루프가 클릭 지점에, 드래그 슬라이드, offset 드래그,
  MMB 슬라이드, 스크린샷.
