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
- Create Polygon / Append to Polygon Tool Settings: CAPTURE 레인의 `research/maya/re/options_144.md` (나오기 전엔 [K]).
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

(작성 중)
