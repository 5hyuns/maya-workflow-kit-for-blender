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
