# Step 139 — 레인 EDIT: Connect / Merge / Smooth / Symmetrize (#70 #68, step_133_work.md M1 M2 M3 M9)

계획: `step_139.md` 「계획」. 측정 = `research/maya/re/edit_mesh_139_edit.md` (mayapy + Maya GUI, 스크립트
`research/scripts/edit_mesh_139_edit_mayapy.py`, `research/scripts/maya_sym139/`, 원본 JSON `edit_mesh_139_edit_raw/`).

## 한 것

- **Connect (M1)**: `Edit Mesh/Connect` = `allset.connect` (Mesh Tools > Connect 와 같음). `poly_maya.connect` 를 Maya 규칙으로
  다시 씀: 면마다 선택 정점 + 선택 엣지 중점을 인덱스 순 사이클로 잇고, 테두리 이웃 / 교차는 건너뜀. 면 선택 = 선택 면끼리
  공유 엣지 중점, 띠 끝 면은 이웃이 2 개 이상이면 반대 엣지까지 (§1).
- **Merge (M2)**: `Edit Mesh/Merge` = 새 `allset.merge` — 임계값 안 묶음은 **평균** 위치로, 정점 2 개면 거리와 상관없이
  (alwaysMergeTwoVertices). 값 = 옵션 창 저장값 (없으면 0.01 / on). 옵션 창도 같은 연산자. 엣지 / 면 선택은 경계 엣지에만
  임계값 (Maya polySewEdge) (§2).
- **Smooth (M3)**: `Mesh/Smooth` = 새 `allset.smooth` — 모디파이어 대신 실제 Catmull-Clark 기하. 컴포넌트 모드는 선택 면
  (엣지 / 정점 선택은 그 면들), 오브젝트 모드는 메시 전체. 선택 경계 정점 고정, 경계 엣지는 중점, 이웃 면은 n-gon (§3).
  옵션 창은 Division levels 만 (Vertex Boundary / Smooth UVs 는 회색 missing 으로 옮김).
- **Symmetrize (M9)**: `Edit Mesh/Symmetrize` = 새 `allset.symmetrize` — 창 단위 모달 "Select a mesh edge for symmetry",
  메시는 클릭 전까지 그대로, Esc / 우클릭 = 취소, 엣지 클릭 = 그 엣지를 위상 대칭 이음매로 양쪽을 면 단위로 걸어 짝을 만들고
  선택한 쪽이 짝을 거울 위치로 옮김 (평면 = 이음매 정점들에 맞춘 평면). 오브젝트 모드 / 선택 없음 = Maya 오류 문구
  (`OBJECT_MODE` 에 추가) (§4).
- `tests/test_step103_option_windows.py` smooth 단언, `tests/gui/gui_manual_sweep.py` M63-2 Smooth 체크를 기하 기준으로 바꿈.

## 검증

`python tests/run.py -k step139,step110,step101,step63,step103,enable_disable,step130` → 82 passed, 0 failed (10 파일).
`python tests/gui/run.py -k step139_edit,step110,step63` → 20 passed, 0 failed (step110 GUI 파일은 없음).

| 경우 | Maya | 킷 |
|---|---|---|
| Connect 마주 보는 엣지 2 | 10/15/7, 중점 (0,.5,±.5) | 10/15/7, 같은 위치 |
| Connect 이웃 엣지 2 / 엣지 3 / 링 4 / 엣지 1 | 10/15/7 · 11/18/9 · 12/20/10 · 8/12/6 | 같음 |
| Connect 대각 정점 / 한 엣지의 정점 2 / 정점 3 | 8/13/7 · 8/12/6 · 8/13/7 | 같음 |
| Connect 면 1 / 2 / 띠 3 / 링 4 / 모서리 3 | 8/12/6 · 9/13/6 · 12/19/9 · 12/20/10 · 11/18/9 | 같음 |
| Connect 평면 3x3 한 줄 / 2x2 / L / 2 | 20/31/12 · 20/32/13 · 20/31/12 · 17/25/9 | 같음 |
| Merge 이웃 정점 2 | 7/11/6 at (0,-.5,.5) | 같음 |
| Merge 먼 정점 2 / 면 대각 | 7/12/6 at 원점 · 7/10/5 at (0,.5,0) | 같음 |
| Merge 3 개 중 한 쌍 / 3 개 묶음 / 옮긴 쌍 | (-.4975..) · 6/9/5 (-.4983,-.499,.5) · (.2,-.35,.4) | 같음 |
| Merge always off / 엣지 선택 / 오브젝트 | 8/12/6 | 8/12/6 |
| Smooth 오브젝트 | 26/48/24, ±.2778 / .375 / .5 | 같음 |
| Smooth 면 1 / 면 2 / 정점 0 | 13/20/9 · 17/27/12 (0,.375,.375) · 20/33/15 | 같음 |
| Smooth 평면 (가운데 +0.5) | 25/40/16, .28125 / .1875 / .125 | 같음 |
| Symmetrize -X 선택 / +X 선택 / 전부 / 정점 1 | +X→.5 · -X→-.8 (위 .7) · -X 가 이김 · 짝 하나만 | 같음 |
| Symmetrize 메뉴 직후 / 오브젝트 모드 | 툴, 메시 그대로 · "No components selected for Symmetrize." | 같음 (GUI: 모달 대기, Esc, 클릭) |

## 남은 것

- Connect: 한 면에 점 4 개 이상이면 모양이 Maya 인덱스 순서에 따름 (Maya 큐브 위 면 4 엣지 = 12/19/9). 킷 큐브 엣지 번호가
  Maya 와 달라 (M11) 같은 모양이 보장 안 됨; 면 6 개 전부 (Maya 13/22/11) 는 규칙 밖 — 테스트 안 함.
- Symmetrize: 양쪽이 다 선택됐을 때 "가장 작은 인덱스 정점 쪽이 기준" 은 측정 1 건에 맞춘 규칙 (delegated). Maya 클릭 쪽 영향은
  QTest 클릭이 Maya 뷰포트에 안 들어가 측정 못 함 (마지막 명령이 엣지만 받으므로 영향 없을 것). 킷 엣지 고르기는 가림 검사 없음
  (화면상 가장 가까운 엣지, delegated). 월드 대칭 모드는 다루지 않음.
- Smooth: Maya UV 경계 규칙 (osdFvarBoundary 3) 대신 UV 는 선형 보간 (모서리 / 중점 / 중심). 크리스 / 하드 엣지 무시.
- 셸프 PolyMerge (`ui/shelf_map.py`) 와 마킹 메뉴 Merge Vertices / Connect Components (`marking/menus.py`) 는 아직
  `mesh.remove_doubles` / `mesh.vert_connect_path` — 이 레인 파일 범위 밖이라 메인이 `("item", "Edit Mesh/...")` 로 바꿀 것.
