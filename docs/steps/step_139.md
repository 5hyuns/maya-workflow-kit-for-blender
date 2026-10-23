# Step 139 — Edit Mesh and UV commands with Maya results (#70 #68 #16)

## 계획

backlog 6 (`step_133_work.md` M1–M4, M9, U1, U2; #16). 측정 = mayapy (MAYA_APP_DIR 는 tmp/), 결과 = `research/maya/re/edit_mesh_139.md`
(레인마다 절, 메인이 합침), 구현 = bmesh (`operators/poly_maya.py`, `extrude.py` 의 Record 패턴), 헤드리스 테스트가 mayapy 숫자와 비교.

### 결정 (delegated)

- **Connect (M1)**: Edit Mesh > Connect = Mesh Tools > Connect 와 같은 polyConnectComponents (step 110 `allset.connect`) — 마주 보는 엣지 2 개 →
  가운데를 잇는 엣지 (8/12/6 → 10/15/7). 정점 · 면 선택도 Maya 규칙 측정.
- **Merge (M2)**: polyMergeVert 의 `alwaysMergeTwoVertices` (기본 on) — 정점 2 개면 거리와 상관없이 합침 (Maya 위치 측정: 중점?). 옵션 창 값 사용.
- **Smooth (M3)**: Mesh > Smooth = polySmoothFace 를 실제 기하로 (선택한 면만 / 없으면 오브젝트 전체), divisions 1 기본, Maya 수 13/20/9 (면 1 개).
  킷 Smooth Preview (1/2/3) 와는 별개.
- **Symmetrize (M9)**: Maya 는 대칭 엣지를 클릭하라는 툴로 들어가고 메시는 그대로 — 킷 툴 (클릭한 엣지 → 그 평면 기준 대칭, 방향 = Maya 기본) 또는
  최소한 메시를 망가뜨리지 않는 툴 진입 + 클릭 후 실행.
- **Extrude edge / vertex (M4)**: Ctrl+E 엣지 / 정점 = polyExtrudeEdge / polyExtrudeVertex 를 바로 (마우스 드래그 없음), 결과 수 Maya (엣지 2 → 12/18/8,
  정점 → 11/18/9) 와 위치 측정, step 65 처럼 Record + In-View Editor 로 값 수정.
- **Bevel (#16)**: Ctrl+B / Edit Mesh > Bevel = polyBevel3 를 바로 (fraction 0.5, segments 1, Maya 기본 측정), 값은 In-View Editor / Adjust Last
  Operation 으로 수정, Esc 해도 남음.
- **UV (U1 U2)**: 오브젝트 모드 UV > Automatic / Contour Stretch = 오브젝트 전체 (Maya polyAutoProj 6 셸) — `menu_item` 의 poll 이 옵션 창
  오브젝트 모드 처리보다 먼저 끝나는 것을 고침. UV Editor > Create > Best Plane / Contour Stretch = 메인 UV 메뉴와 같은 동작.

### 레인 (병렬, worktree, 포그라운드)

| 레인 | 범위 | 파일 |
|---|---|---|
| EDIT | M1 M2 M3 M9 | `operators/poly_maya.py`, `option_windows.py` 의 merge / smooth, `ui/menu_map.py` 해당 줄, 새 Symmetrize 툴은 `ui/mesh_tools.py` 이나 새 모듈, `tests/test_step139_edit.py` |
| SHAPE | M4 #16 | `operators/extrude.py`, `operators/component.py` (bevel), 새 `operators/bevel_maya.py`, `ui/in_view.py` 필요 시, `option_windows.py` bevel / extrude, `tests/test_step139_shape.py` |
| UV | U1 U2 | `ui/menu_sets.py` (menu_item poll 순서), `option_windows.py` uv, `ui/editor_menu_map.py`, `operators/uv_tools.py`, `tests/test_step139_uv.py` |

`option_windows.py` · `menu_map.py` 는 레인마다 자기 항목만 (메인이 병합). research 는 레인마다 `research/maya/re/edit_mesh_139_<레인>.md` → 메인이
`edit_mesh_139.md` 로 합침. 메인: 병합, 헤드리스 전체, 메뉴 경로 GUI, GUI 전체 한 번, 커밋.

## 한 것

레인 3 개 (worktree, 포그라운드 동시). 레인 문서: `step_139_edit.md`, `step_139_shape.md`, `step_139_uv.md`. 측정 명세를 메인이
`research/maya/re/edit_mesh_139.md` 로 합침 (레인별 `edit_mesh_139_{edit,shape,uv}.md`, mayapy 스크립트 `research/scripts/edit_mesh_139_*`).

- **EDIT** (M1 M2 M3 M9): `operators/poly_maya.py` — Connect (정점 / 엣지 / 면, Maya 경우 20 개 모두 같은 수), Merge (alwaysMergeTwoVertices,
  중점 / 평균 위치), Smooth (선택 면만 / 전체, 실제 Catmull-Clark, 모디파이어 없음: 1 면 13/20/9, 전체 26/48/24), Symmetrize (엣지 클릭 툴,
  Esc = 그대로, 오브젝트 모드 = Maya 경고). Smooth 옵션 창은 Division levels 만 (나머지는 회색 알림).
- **SHAPE** (M4 #16): Ctrl+E 엣지 / 정점 = polyExtrudeEdge / polyExtrudeVertex 바로, Ctrl+B = polyBevel3 바로 (Fraction 0.5, Esc 해도 남음, 정점
  모드 = Chamfer Vertex). step 65 기록을 노드 종류별로 (In-View Editor, Channel Box INPUTS, AE 기록 탭, Adjust Last Operation 에서 수정, 화살표).
  측정한 모든 경우 mayapy 와 1e-4 안.
- **UV** (U1 U2): `allset.uv_automatic` (6 평면 bmesh 투영, 오브젝트 모드 가능; 큐브 · 원기둥 · 평면 셸 수 · UV 수 Maya 와 같음), `allset.uv_contour`,
  UV Editor > Create > Automatic / Best Plane / Contour Stretch 연결. `menu_item` 순서는 그대로 (새 연산자가 오브젝트 모드를 받음; delegated).
- **메인**: 병합 (충돌 없음), 마킹 메뉴 (Chamfer Vertex, Merge Vertices, Connect Components ×2, Bevel Edge / Face, UV Automatic) 와 셸프
  (performBevelOrChamfer, PolyMerge, Automatic Mapping) 가 Blender 연산자 대신 같은 메뉴 항목 `("item", path)` 으로 — 레인 셋이 각각 남긴 것.
