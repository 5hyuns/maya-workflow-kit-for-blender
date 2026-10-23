# Step 141 lane SELECT — Select 메뉴 / Ctrl+RMB 변환 (quant gap 3)

측정: `research/maya/re/select_convert_141.md` (mayapy, 스크립트 `research/scripts/select_convert_141_mayapy*.py`, 3 회).
대상: `docs/steps/step_133_quant.md` 3 행 — Select 메뉴 회색 42 개 중 변환 / 루프 항목, polyConvertMM 회색 4 개.

## 한 것

- 새 `src/allset/operators/select_convert.py` = `allset.select_convert(kind)` (bmesh, 여러 오브젝트 편집 모드):
  Grow / Shrink Along Loop, To Vertex / Edge / Face Perimeter, To Face Path, To Shell Border, To UV Shell Border,
  To UVs, To UV Perimeter, To UV Edge Loop. 규칙은 전부 mayapy 측정 (명세 파일 각 절). 핵심:
  - Grow Along Loop: 선택된 이웃이 있는 면 / 정점 / 모서리는 그 줄 방향으로 양 끝에서 한 칸, 외톨이 면 / 정점은 모든
    이웃으로, 모서리는 루프 따라 양 끝 한 칸. 정점은 선택 정점 사이 모서리를 키운 결과 (Maya 결과가 정확히 이 규칙).
  - Shrink Along Loop: 줄의 끝 제거 (한 방향에서 한쪽만 선택 = 끝, 열린 경계 = 비선택), 정점은 줄인 모서리의 정점
    (3×3 정점 블록 → 없음, Maya 그대로).
  - 둘레: 영역 = 선택 면, 아니면 담긴 면, 아니면 닿은 면 (정점의 면 / 모서리 자기 면). Face Perimeter 는 담긴 면이
    없으면 선택 유지 (Maya 그대로).
  - To Face Path = 닿은 모서리들의 edge ring 의 면. To Shell Border = 선택 일부가 열린 경계에 있을 때만 그 셸의 경계
    요소 (같은 타입), 아니면 빈 선택 (Maya 그대로). To UV Shell Border = 닿은 셸의 열린 경계 요소; UV 일 때는 UV 셸 경계 UV.
  - To UVs: 면 → 그 면의 UV, 모서리 → 옆 면들 안의 그 모서리 UV, 정점 → 정점의 모든 UV. UV 결과 = UV Sync 끔 +
    모든 면 표시 (`uv_tools.set_component(UV)`, step 66 의 Maya UV 컴포넌트) + 루프 UV 선택, GUI 면 UV Editor 창 열기.
- `compat.set_uv_vert_selected` / `set_uv_edge_selected` 추가 (4.5 `loop[uv].select`, 5.x `loop.uv_select_vert`).
- `ui/menu_map.py` Select 줄: 위 11 항목 + Components > UV / UV Shell (`allset.uv_component`, F12 / Alt+F12 과 같음).
  To Vertices / Edges / Faces 는 `mesh.select_mode(use_expand)` 대신 `allset.convert_selection` (닿은 요소 = Maya
  ConvertSelectionTo*, Ctrl+F9–F11 과 같은 연산자); To Edge / Face Perimeter 는 `mesh.region_to_loop` 대신 킷 연산자
  (region_to_loop 은 Face Perimeter 에 모서리를 줬고, 정점 / 모서리 선택에서 Maya 와 다름).
- `marking/menus.py` polyConvertMM: 모든 변환 항목 = `("item", "Select/...")` (메뉴와 마킹 메뉴가 같은 연산), 회색 0.
  변환 후 동작 항목 (To Edge Loop and Delete 등) 은 그대로 `allset.mm_poly`. Selection Boundary 는 손대지 않음.
- `ui/editor_menu_map.py` UV Editor > Select: Grow / Shrink Along Loop, To Vertex / Edge / Face Perimeter, To Face
  Path, To UV Shell Border, To UV Perimeter, To UV Edge Loop → 같은 연산자.
- `ui/notices.py`: polyConvertMM MARKING 4 개 삭제, `Select/Convert Selection` 문구 = vertex face 전용 (남은 회색
  To Vertex Faces), `Select/Components/Vertex Face` 새 문구, `UV Editor/Select/Convert Selection` 문구 갱신.

## 결정 (delegated)

- **Vertex Face (Components > Vertex Face, To Vertex Faces) 는 회색 + notice.** Blender 엔 면 모서리 (face corner)
  선택 컴포넌트가 없다. UV Editor 의 Sticky Selection 끔으로 모서리 하나씩 고를 수는 있지만 그건 UV 공간이고, Maya
  vertex face 의 쓰임 (면별 노멀 / 색) 은 Blender 에서 면 선택 + Mesh > Normals 로 한다 → 거짓 매핑 대신 안내.
- **Sync 끔의 해석 (`select_convert.uv_source`).** Sync 끔은 Blender 공장 상태라서 그것만으로 UV 선택이라 보지 않는다:
  UV Editor 안에서, 또는 3D View 에서 보이는 면이 전부 선택 + UV 일부만 선택 (set_component 가 만드는 상태) 일 때만 UV
  가 원천. 그때 메시 대상 변환은 그 UV 의 정점에서 출발하고 결과 후 sync 를 켠다 (Maya 컴포넌트 모드로). Grow / Shrink
  Along Loop 를 UV 에서 하면 정점 기준으로 키운 뒤 그 정점들의 UV 전부.
- **To Shell Border 는 Maya 그대로** (경계에 닿지 않은 선택 → 빈 선택). step 136 의 `mm_poly SHELL_BORDER`
  (열린 모서리) 는 더 이상 메뉴에서 안 씀.
- **To UV Shell Border (메시 요소) 의 묶음 = 메시 셸** — 측정 (열린 큐브에서 다른 UV 조각의 경계 면도 포함).
- 루프 연속 규칙: 안쪽 4-모서리 정점은 면을 공유하지 않는 모서리, 열린 경계의 3-모서리 정점은 다음 경계 모서리,
  모서리 (2) 에서 끝 (측정: e2 → 0,2,4, e0 → 0,2). To UV Edge Loop 은 정점의 UV 가 하나일 때만 지나가고, UV 이음선 위
  모서리는 이음선을 따라감 (큐브는 모든 모서리 그대로 — 측정과 같음).

## 검증

- `tests/test_step141_select.py` 6 개 통과: Maya 측정 99 경우 (플레인 4×4 / 6×6, 큐브, 열린 큐브 — Maya 번호 그대로
  만든 메시) 전부 같음 + UV 원천 3 + sync 끔 공장 상태 1, 메뉴 경로 / 마킹 항목 / menu_item 경로, 킷 큐브.
- `python tests/run.py -k step141_select,step18,step101,step136,step8,step66,step39,enable_disable,...` 통과
  (step101 notice 문구 "Blender" 규칙 한 번 고침).
- GUI `tests/gui/gui_step141_select.py` 11/11: Ctrl+RMB 제스처로 Grow Selection ▸ Grow Along Loop (정점 모드, 외톨이
  정점 → 이웃 3), To Vertices ▸ To Vertex Perimeter (면 → 정점 4, 정점 모드), 목록 To Face Path (면 6, 면 모드).
  처음엔 GUI 에서 sync 끔 (Blender 기본) 을 UV 모드로 읽어 모든 면이 선택되고 UV Editor 창이 열렸음 → `uv_source`.
- `python tools/menu_count.py`: Select 메뉴 working 39 → 50 (회색 42 → 31), 전체 664 → 675 (44.7 → 45.4 %),
  UV Editor 86 → 95, 회색 notice 없음 0.

## 남은 것

- 회색 유지: Components > Vertex Face, To Vertex Faces (위 결정), UV Editor 의 To Edge Loop / Ring / Contained /
  Connected Faces (sync 끔 UV 에선 Blender 연산이 메시 선택을 읽음; notice 로 3D View 메뉴 안내).
- `marking/rmb_items.py` 의 `mm_poly` VERTEX_PERIMETER / SHELL_BORDER 는 이제 메뉴에서 안 쓰는 옛 규칙 (test_step136_items
  가 직접 부름) — 정리는 별도.
- 오브젝트 모드에서 Select 메뉴 변환 = `menu_item` 의 poll 경고 (Ctrl+RMB 는 step 136 대로 전체 선택 후 변환).
- Grow / Shrink Along Loop on UVs 는 정점 기준 근사 (Maya 는 UV 공간 루프) — UV 자르기 이음선 근처에서 다를 수 있음.
