# Step 144 (POLY lane) — Quad Draw / Create Polygon / Append to Polygon (#30)

사용자 요청 (0.4.0): "Maya modeling tools: Quad Draw / Create Polygon / Append, ... Implement Maya interaction (clicks,
modifier keys, Tool Settings with Maya fields/defaults) instead of Blender's Poly Build ..." — 이 레인은 #30 만.

## 근거

- 지금: `ui/menu_map.py` 의 세 메뉴, 셸프 `dR_quadDrawTool`, Ctrl+Shift+Q 모두 Blender Poly Build (`builtin.poly_build`) [O]
  (#30 본문, `tests/gui/audit128/tool_inventory.py`).
- Quad Draw: 컨텍스트 `nexQuadDrawCtx1`, Tool Settings = Auto-weld ✓ 10, Relax Auto-Lock, Extend Edge, Quad Strip Width 20,
  Clear Dots, 접힌 Live Constraint Options / Keyboard/Mouse Shortcuts [O] research/maya/workflows/modeling.md:34,
  research/maya/workflows/shots/modeling_07_win1.png. 손 동작은 Maya 도움말 기억 [K] (#30 목록): 클릭 = 라이브 표면 위 점,
  Shift+클릭 = 점 4 개 사이 쿼드, Ctrl+클릭 = 엣지 루프, Shift+드래그 = Relax, Tab+드래그 = 경계 엣지 연장 / 빈 곳 쿼드 띠,
  Ctrl+Shift+클릭 = 지우기, 드래그 / MMB 드래그 = 옮기기 (표면에 붙어서).
- Make Live: `Scene.allset_live` (step 21 S13, `operators/snap_align.py:240`).
- Maya 2022 Tool Settings 실측 (CAPTURE 레인 화면, `research/maya/screens/options144/`) [O]:
  - `create_polygon.png`: 제목 "Create Polygon Tool", Description + Settings: Divisions **1** "(vertices added per edge)",
    Keep new faces planar **끔**, Limit the number of points **끔** + Limit points to **4** (끄면 회색), Texture space
    **Normalize (scale to fit)** / Unitize (use corners and boundary) / None.
  - `append_polygon.png`: 제목 "Append To Polygon Tool", 같은 필드 + Rotation angle 0.0000 (회색).
  - `quad_draw.png`: Auto-weld ✓ 10, Relax Auto-Lock, Extend Edge, Quad Strip Width 20, Clear Dots; Live Constraint Options =
    Wireframe Overlay ✓ (검정), Mesh Color ✓ (파랑), Mesh Alpha ✓ 0.75, Surface Offset 끔 0, Snap to Backfaces 끔;
    Keyboard/Mouse Shortcuts 표 (메시 밖: LMB 클릭 점, LMB/MMB 드래그 점 옮기기, Ctrl+Shift+LMB 점 지우기, Tab+LMB 쿼드 띠,
    Tab+MMB 띠 크기, Shift+LMB 점 사이 클릭 = 면; 메시 안: LMB/MMB 드래그 옮기기, Ctrl+LMB 엣지 클릭 루프, Ctrl+MMB 가운데 루프,
    Shift+LMB 드래그 relax, Shift+MMB 강조된 점 relax, Tab+LMB 경계 엣지 연장, Tab+MMB 경계 루프 연장, Ctrl+Shift+LMB 클릭 /
    드래그 면 지우기 · 엣지 클릭 = 엣지 루프 지우기, Ctrl+Shift+MMB 엣지 드래그 = 엣지 루프 옮기기, Ctrl+Shift+RMB 옵션).
  - `_options144.json` `_runtime_commands`: `CreatePolygonToolOptions` / `AppendToPolygonToolOptions` / Quad Draw 상자 =
    `...; toolPropertyWindow` → 옵션 상자 = Tool Settings.
- 재료: step 129 Multi-Cut (`operators/multi_cut.py` `pick` / `loop_segments`, `ui/mesh_tools.py` 툴 등록), step 74
  `preselect.caches`, step 64 `mesh_tools.insert_loop`, step 57 `joints.click_point` (Maya 그리드 / 뷰 평면 위 점),
  step 63 `mesh_maya._maya_rename` (polySurfaceN), step 100 `material.give_default` (lambert1).

## 계획

1. **모듈**: 새 `operators/poly_draw.py` (Create Polygon / Append: 순수 bmesh 함수 + 모달 + 설정 PropertyGroup
   `Scene.allset_poly_tools`), 새 `operators/quad_draw.py` (Quad Draw 순수 함수 + 모달 + 그리기), 새 `ui/mesh_tools_poly.py`
   (WorkSpaceTool 세 개 + Tool Settings 그리기). 등록은 `operators/__init__.py` / `ui/__init__.py` 에 한 줄씩.
2. **진입** (메뉴 / 셸프 / 마킹 메뉴 / Ctrl+Shift+Q): 시작 연산자 `allset.create_polygon_start`,
   `allset.append_polygon_start`, `allset.quad_draw_start` (각자 `option_box` 속성: 옵션 상자 = 툴 + Tool Settings 독,
   Maya 의 옵션 상자가 Tool Settings 를 여는 것과 같음 — 툴이 WorkSpaceTool 이라 step 140 의 창 대신 독 섹션; delegated).
   - Create Polygon: 오브젝트 / 편집 모드 툴 (둘 다 등록). 끝내면 새 오브젝트가 선택된 오브젝트 모드, 툴은 그대로.
   - Append: 선택된 메시의 편집 모드 툴 (메시가 없으면 Maya 식 경고).
   - Quad Draw: 편집할 메시 = 편집 / 선택 중인 메시 (라이브 표면이 아니면), 아니면 새 빈 메시 `polySurfaceN` (원점).
     기준 표면 = 라이브 표면, 없으면 편집 중이 아닌 보이는 다른 메시 전부, 그것도 안 맞으면 그리드 / 뷰 평면 [K, delegated].
     툴이 켜진 동안 뷰의 Retopology 오버레이를 켜서 (Maya 처럼 새 메시를 표면 위에 보임) 툴을 떠나면 되돌린다.
3. **Create Polygon** (`allset.create_polygon` 모달, 툴 LMB PRESS): 클릭 = 점 (`joints.click_point`: 원근 뷰 = 바닥, 직교
   = 뷰 평면), 누른 채 드래그 = 그 점 옮기기, MMB 드래그 = 마지막 점 옮기기 [K], Backspace / Delete = 마지막 점 지우기,
   Enter = 완료 (3 점 이상: 새 `polySurfaceN`, 정점은 월드 좌표, 원점 피벗 [K], lambert1), Limit points 에 닿으면 자동 완료,
   Esc = 점 버림 (없으면 Select 툴). 순수 함수 `polygon_points(points, divisions, planar)` / `polygon_uvs(texture)`.
4. **Append** (`allset.append_polygon` 모달): 첫 클릭은 경계 엣지 (그 엣지의 두 정점이 새 면의 첫 두 정점, 이웃 면과
   감김 방향이 맞게 반대 순서), 다음 클릭 = 다른 경계 엣지 (그 두 정점 추가) 또는 빈 곳 점 (첫 엣지를 품고 시선에 가장
   수직인 평면 위, delegated), Backspace / Enter / Esc 는 3 과 같음. 순수 함수 `append_face(bm, edge_index, points)`.
5. **Quad Draw** (툴 키맵, EDIT_MESH): LMB PRESS (수식키 any) → `allset.quad_draw` 가 누른 순간의 수식키로 나눔:
   - 없음: 정점 / 엣지 / 면 / 점 위면 드래그 = 옮기기 (표면에 투영, 놓을 때 Auto-weld 화면 거리 안의 정점과 합침), 빈 곳 = 점.
   - Shift: 클릭 = 채우기 (가까운 점 / 경계 정점 4 개, 안 되면 3 개가 마우스를 둘러싸면 그 면; 화면 반시계 = 카메라 쪽 법선),
     드래그 = Relax 붓 (화면 반경 안 정점 라플라시안 → 표면 투영; Auto-Lock = 붓에 안쪽 정점이 있으면 경계 고정).
   - Ctrl: 엣지 클릭 = 그 자리 엣지 루프 (새 정점 표면 투영). Ctrl+Shift: 클릭한 점 / 정점 / 엣지 / 면 지우기.
   - MMB 드래그 = 옮기기 (`allset.quad_draw_tweak`). Tab 누름 = `allset.quad_draw_tab` 모달 (Tab 놓을 때까지): LMB 드래그를
     경계 엣지에서 = 연장 (Extend Edge = 그 엣지, Loop = 경계 루프 전체), 빈 곳에서 = Quad Strip Width px 폭의 쿼드 띠.
   - 호버 (`allset.quad_draw_hover`, MOUSEMOVE / Shift·Ctrl 누름·뗌, PASS_THROUGH): Shift = 채울 면 미리보기, Ctrl = 루프
     미리보기, Ctrl+Shift = 지울 것 빨갛게.
   - 순수 함수 (헤드리스 테스트): `fill_candidates`, `fill_order(points_xy, mouse)`, `fill_face`, `strip_quads(path, width)`,
     `extend_edges`, `relax(bm, verts, lock)`, `delete_at`.
6. **Tool Settings**: `ui/tool_settings.py` 의 Quad Draw 종류를 새 툴에 붙이고 (Poly Build 행 제거), Create Polygon / Append
   종류 추가; 필드 = options_144.md 의 Maya 공장값.
7. 테스트: `tests/test_step144_poly.py` (순수 함수 + 연산자 결과), `tests/gui/gui_step144_poly.py` (뷰에서 클릭 + 수식키).

## 한 일

- 새 `operators/poly_draw.py` (Create Polygon / Append: 순수 함수 `polygon_points` / `polygon_uvs` / `build_polygon` /
  `append_face` / `edge_start`, 모달 `allset.create_polygon` / `allset.append_polygon`, 시작 연산자, 설정
  `Scene.allset_poly_tools`), 새 `operators/quad_draw.py` (순수 함수 `fill_order` / `fill_face` / `extend_edges` /
  `border_loop` / `edge_loop` / `strip_pairs` / `strip_faces` / `relax` / `delete_at` / `weld_target` / 점 =
  `add_dot` / `dots` / `clear_dots`; 모달 `allset.quad_draw` (LMB any / MMB / Ctrl+MMB), `allset.quad_draw_tab`,
  호버 `allset.quad_draw_hover`, `allset.quad_draw_start`, Clear Dots, Exit), 새 `ui/mesh_tools_poly.py`
  (WorkSpaceTool 4 개: Quad Draw, Create Polygon 오브젝트 / 편집 모드, Append; Tool Settings 그리기 + 단축키 표).
- 메뉴 세 줄 = 시작 연산자 (`option_box` → 툴 + Tool Settings 독). 셸프 `dR_quadDrawTool`, Ctrl+Shift+Q
  (`maya_patches.patch_key_batch`, `mapping.QuadDrawToolNameCommand`), Command Line 도움말, `ui/tool_settings.py`
  의 QUAD_DRAW 종류 (Poly Build 행 / 회색 안내 제거) + CREATE_POLYGON / APPEND_POLYGON 종류, Reset Tool.
- **점 (dot) = 표시가 붙은 떨어진 정점** (int 레이어 `allset_dot`, 모서리가 생기면 일반 정점): 처음엔 모듈 상태 목록이었으나
  Ctrl+Z 가 빈 단계만 되돌려 바꿈 → 점도 메시와 함께 언두 (GUI 실측: Ctrl+Z 로 마지막 점 사라짐). 툴을 떠나면 점과 레이어 삭제,
  면이 하나도 없는 새 polySurfaceN 삭제, Retopology 오버레이 원래대로 (0.5 s `_watch` 타이머, 공간은 `live_refs` 포인터).
- Maya 근거 추가 확인: CAPTURE 의 `research/maya/screens/options144/_options144.json` `_runtime_commands`:
  `CreatePolygonToolOptions` / `AppendToPolygonToolOptions` / Quad Draw 상자 = `...; toolPropertyWindow` [O] →
  옵션 상자 = Tool Settings (독 섹션) 가 Maya 와 같음. `polyCreateFacetCtx -pc \`optionVar -q polyKeepFacetsPlanar\``.

### 위임한 결정 (delegated)

- 옵션 = Tool Settings 독 섹션 (step 140 의 창 대신): Maya 상자가 toolPropertyWindow 를 열고, 킷 툴이 WorkSpaceTool 이라서.
  `option_windows_poly.py` 없음 → `option_windows._extend()` 변경 없음.
- Quad Draw 편집 대상 = 선택 / 편집 중인 메시 (라이브 표면이 아니면), 아니면 새 빈 `polySurfaceN`. 기준 표면 = 라이브 표면,
  없으면 편집 중이 아닌 보이는 메시 전부, 메시가 없으면 구성 평면. 자동 Make Live 는 하지 않음 (스냅 설정을 바꾸므로).
- Append 의 새 점 = 첫 경계 엣지를 품고 시선에 가장 수직인 평면 위. Create Polygon 점 = Joint Tool 과 같은 구성 평면,
  X / V 홀드 스냅 반영. 새 다각형 피벗 = 원점.
- Quad Draw: Shift+클릭 채우기 = 마우스에서 가까운 후보 6 개 중 마우스를 품는 가장 작은 단순 사각형 (없으면 삼각형),
  화면 반시계 = 카메라 쪽 법선, 이웃 면과 감김이 반대면 뒤집음. Relax 붓 반경 50 px, 한 번에 이웃 평균 쪽 50 %.
  Ctrl+Shift+클릭 엣지 = 그 엣지 루프를 녹임 (경계 엣지는 그 면 삭제), 정점 = 녹임 / 경계면 삭제 (Maya 표에 정점은 없음).
  Ctrl+Shift+MMB 드래그 = 엣지 루프 전체를 표면 위로 옮김. Shift+MMB = 마우스 아래 강조 요소의 점만 relax.
  Tab = 누르는 동안 도는 모달 (Tab+LMB 를 키맵 수식키로 못 받으므로). Tab+LMB 는 Extend 설정 (Edge / Loop), Tab+MMB 는 항상 루프.
  Divisions N = 변마다 N 개 엣지 (기본 1 = 나눔 없음; Maya 라벨 "vertices added per edge" 의 1 이 새 정점 0 개인지는 [K]).
- 처음 구현한 Ctrl+MMB = Edge Slide 는 Maya 표 (Ctrl+MMB = 가운데 루프) 를 보고 바꿈.

## 검증

- `tests/test_step144_poly.py` 22 개 통과 (순수 함수 + 객체 생성 + 툴 / 키맵 등록 · 해제 + 설정 기본값).
- 관련 헤드리스 (step64, step129, step54, step101, enable_disable, step130, step35, step136, step140, step108, step109,
  step106, step133): 268 통과 / 0 실패 (29 파일).
- GUI `tests/gui/gui_step144_poly.py` 31 통과 / 0 실패 (Create Polygon 5 클릭 + Backspace + Enter, Limit points, Append,
  Ctrl+Shift+Q, 점 4 개 + Ctrl+Z, Shift 미리보기 + 채우기, Ctrl 루프, Ctrl+Shift+MMB 루프 옮기기, 정점 드래그, Tab 연장,
  Ctrl+Shift 삭제, Tool Settings 독, Esc, 오버레이 복원). 스크린샷 `tmp/poly144/shots/` 직접 확인 (점, 채우기 미리보기,
  연장 미리보기, Tool Settings 독이 Maya 화면과 같은 순서).

## 남은 것

- Live Constraint Options 의 Wireframe Overlay / Mesh Color / Mesh Alpha / Surface Offset, Tab+MMB 빈 곳 띠 크기,
  Ctrl+Shift+RMB 옵션 메뉴 = 회색 + 안내 (notices.PANEL_NOTICES). 클릭 동작 자체 (점 위치 규칙, 채우기 선택) 는 Maya GUI 에서
  재지 않음 [K].
- 채우기에 쓰인 점은 언두해도 점으로 돌아오지만, 점 놓기도 언두 단계 하나씩.
- Quad Strip / Extend 는 화면 픽셀 폭; Maya 의 정확한 폭 규칙은 미측정.
