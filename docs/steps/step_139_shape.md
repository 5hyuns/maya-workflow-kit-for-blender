# Step 139 — 레인 SHAPE: 엣지 / 정점 Extrude, Bevel (#70 M4, #16)

측정: `research/maya/re/edit_mesh_139_shape.md` (mayapy 스크립트 `research/scripts/edit_mesh_139_shape_mayapy*.py`),
테스트 데이터 `tests/maya139_shape_data.py`.

## 한 것

- **Ctrl+E / Edit Mesh > Extrude** (엣지 · 정점 모드): Blender extrude + 마우스 드래그 대신 polyExtrudeEdge /
  polyExtrudeVertex 를 바로 bmesh 로 (`operators/extrude.py` `extrude_edges` / `extrude_vertices`). 어느 것을 할지는
  선택 모드 먼저 (Maya 는 선택한 컴포넌트 종류로 고름). 엣지: 엣지마다 따로 (Maya 기본 Keep Faces Together off), 길이 0,
  Thickness · Local Translate Z = 인접 면 법선 평균 방향, Offset = Z x 엣지 방향. 정점: 원래 정점이 끝 (길이 = 면 법선
  평균 x Length), 바닥 링 = 각 엣지 길이 x Width, Divisions = 바닥 → 끝 사이 링.
- **Ctrl+B / Edit Mesh > Bevel**: 모달 대신 polyBevel3 을 바로 (`operators/bevel_maya.py`, 연산자는
  `component.ALLSET_OT_bevel` / `ALLSET_OT_bevel_edit`). Fraction 기준 = 선택 전체에 한 길이 (미끄러지는 엣지 중 가장
  짧은 것, 양 끝이 쓰이면 반), 너비 x 0.9999 (Maya 측정값), Depth → 슈퍼타원 profile t², 0.0001 안 정점은 중점으로 합침
  (Merge Vertices). 정점 모드 = Chamfer Vertex (엣지의 0.25). Esc / 마우스 없음 = 그대로 남음 (모달이 없음).
- step 65 기록을 노드 종류별 `Spec` 으로 일반화: polyExtrudeEdgeN / polyExtrudeVertexN / polyBevelN 이름 (종류마다 번호),
  In-View Editor 줄 · Channel Box INPUTS · AE 히스토리 탭 (`polyExtrudeEdge`, `polyBevel3`) · Adjust Last Operation
  (제목 = 노드, 편집 연산자 `allset.extrude_edge_edit` / `extrude_vertex_edit` / `bevel_edit`) 이 그 노드의 Maya 필드를
  보임. 화살표 매니퓰레이터: 엣지 = Local Translate Z, 정점 = Length, 베벨 = 없음 (In-View 만).
- 메뉴 `Edit Mesh/Bevel` = `allset.bevel` (오브젝트 모드는 기존 `OBJECT_MODE` 규칙으로 모든 엣지 = Maya 24/48/26),
  옵션 창 Bevel 도 `allset.bevel` 로 (값 그대로 편집 가능). `menu_sets.WHOLE_MESH_PROPS` 의 Blender bevel 인자 한 줄 삭제
  (UV 레인 파일 — 병합 시 확인).
- 한 명령 = 한 undo 단계 (편집도 각각 한 단계, GUI 로 확인).

## 검증

| 경우 | Maya (v/e/f, 위치) | 킷 |
|---|---|---|
| 엣지 2개 Extrude | 12/18/8, 길이 0 | 같음 (위치 1e-4 안) |
| + Thickness 0.5 / LTZ 0.5 / Offset 0.1 / Div 2 | (−0.85355, 0.85355) / 같음 / (−0.42929, 0.57071) / 16/24/10 | 같음 |
| 윗면 엣지 4개 Extrude (+LTZ / Thickness 0.5) | 16/24/10 | 같음 |
| 정점 Extrude | 11/18/9, 끝 (−1.07735 ×3) | 같음 |
| + Width 0.2 / Length 0.5 / Div 2 / 상자 4×1×2 | 바닥 0.2×엣지 / … / 14/24/12 / 엣지 길이 비례 | 같음 |
| Bevel 엣지 1개 | 10/15/7, 0.49995 | 같음 |
| Fraction 0.2 / Seg 2 / Seg 3 / Offset 0.1 절대 | 0.19998 / 12/18/8 원호 / 14/21/9 / 0.09999 | 같음 |
| Depth 0.5 / 0 / −0.5 / −1 (Seg 2 가운데) | 0.3018 / 0.25003 / 0.19825 / 0.14648 | 같음 |
| 윗면 루프 · 면 1개 · 오브젝트 전체 (Seg 2) | 12/20/10 · 같음 · 24/48/26 (56/108/54) | 같음 |
| 상자 엣지 · 두 셸 · 이웃 엣지 조합 6가지 | 짧은 미끄럼 엣지 기준, 전역 한 길이 | 같음 |
| Fraction 1 | 6/9/5 (합침) | 같음 |
| 길이 0 Extrude 뒤 Bevel (Ctrl+E → Ctrl+B) | 12/20/10, 캡 ±0.25 (인셋) | 같음 |
| Chamfer Vertex (정점 모드 Ctrl+B) | 10/15/7, 엣지의 0.25 | 같음 |

- 헤드리스 `python tests/run.py -k step139,step65,step26,step103,step106,enable_disable,step130`: 80 passed, 0 failed
  (10 파일). 확장 묶음 (+step7_, step18, step110, step101, step54, step136, step38, step135): 182 passed.
  `test_step139_shape.py` 16 개.
- GUI `python tests/gui/run.py -k step139_shape,step65,step26`: 27 passed (step139_shape 11). `gui_step18_mesh_keys`
  (Ctrl+B 기대값 변경) 14 passed.
- 스크린샷 (`--shots tmp/shots139`, 직접 봄): `gui_step139_bevel.png` (polyBevel1 In-View 5줄, 모서리 베벨),
  `gui_step139_bevel_seg2.png` (Segments 2 둥근 베벨), `gui_step139_extrude_edges.png` (polyExtrudeEdge1 4줄, 파란
  화살표, Thickness 0.496), `gui_step139_extrude_vertex.png` (polyExtrudeVertex1 Width/Length/Divisions, 원뿔 + 화살표).

## 결정 (delegated)

- 엣지 Offset 의 방향은 엣지 정점 순서 (a → b) 를 따름 — Maya 도 엣지 저장 순서를 따르므로, 킷 큐브 엣지 순서가 Maya 와
  다른 곳 (M11) 에서는 반대쪽일 수 있음.
- 엣지 Extrude 는 Keep Faces Together 를 노출하지 않음 (Maya 기본 off, 따로 떨어진 엣지에서는 결과 같음).
- Depth ≠ 1, 0 이면서 Segments ≠ 2 인 경우는 슈퍼타원 근사 (Segments 2 만 정확히 측정 일치).
- 베벨 뒤 선택 없음 (mayapy `ls -sl` = []) — In-View Editor 는 선택이 베벨이 남긴 그대로 (= 없음) 인 동안 보임.
- Chamfer Vertex 는 바로 실행만, 편집 노드 없음.

## 남은 것

- Chamfer off (Maya 옵션) 미지원. Mitering / Miter Along / Smoothing Angle / Auto Fit 미지원 (옵션 창 missing 목록 그대로).
- 마킹 메뉴 "Bevel Edge / Bevel Face" (`marking/menus.py`), 셸프 `performBevelOrChamfer` (`ui/shelf_map.py`) 는 아직
  `mesh.bevel` — 레인 범위 밖, `allset.bevel` 로 바꾸면 같은 결과 (메인 판단).
- `operators/preselect.py` `_extrude_block` 은 베벨 (화살표 없음) 에서도 가운데 축 근처 hover 를 막음 — 범위 밖, 영향 작음.
- 매니퓰레이터 화살표는 엣지 / 정점 Extrude 의 한 값만 (Maya 엣지 Extrude 매니퓰레이터의 이동 · 회전 · 스케일 핸들 없음).
