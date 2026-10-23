# Step 139 lane UV — 오브젝트 모드 UV 투영, UV Editor Create (#68, step_133_work.md U1 / U2)

측정: `research/maya/re/edit_mesh_139_uv.md` (mayapy, 스크립트 `research/scripts/edit_mesh_139_uv_*.py`).

## 한 것

- **UV > Automatic** = 새 `allset.uv_automatic` (`operators/uv_tools.py` `auto_project`): Maya polyAutoProjection 을 bmesh 로.
  면마다 가장 마주 보는 투영 평면 (6 = ±X ±Y ±Z, 동점은 Maya X 먼저), 같은 평면의 이어진 면 = 한 셸, 평면에 정투영,
  셸 전부 한 배율로 0–1 에 선반 배치 (간격 0.2 %, Maya 경계 0.002–0.998). 오브젝트 모드 = 선택한 메시의 모든 면
  (Maya 가 오브젝트 선택을 면으로 바꿈), 컴포넌트 모드 = 선택한 면만. 옵션 창 `uv_automatic` 은 이 연산자를 부르고
  `match` 가 생겨서 UV Editor > Create > Automatic 도 같은 옵션 박스. Blender `uv.smart_project` 는 더 이상 안 씀.
- **UV > Contour Stretch** = 새 `allset.uv_contour`: Follow Active Quads (활성 면이 없으면 첫 사각면) 후 0–1 로 늘림
  (Maya: 한 줄 10 면이 0–1 을 채움). 오브젝트 모드 = 모든 면.
- U1 원인 (menu_item 이 `uv.smart_project` poll 실패로 끝남) 은 연산자가 오브젝트 모드를 직접 받아서 사라짐.
  `menu_sets.ALLSET_OT_menu_item` 의 순서는 그대로 둠 (delegated: 옵션 창 경로를 poll 앞에 두면 저장값이 없을 때
  날 Blender 연산자가 돌고, step 101 의 Maya 식 경고가 Blender 오류로 바뀜).
- `menu_map.OBJECT_MODE` 에 UV/Cylindrical, UV/Spherical ('ALL', 'FACE') 추가 (Maya 투영은 오브젝트 선택 = 모든 면,
  performPolyProjectionArgList.mel:621-634). 전에는 오브젝트 모드에서 "select UVs (UV Editor) first" 경고.
- **U2**: `ui/editor_menu_map.py` 에 UV Editor > Create > Best Plane (`allset.uv_planar`) / Contour Stretch
  (`allset.uv_contour`), Automatic → `allset.uv_automatic` — 메인 UV 메뉴와 같은 동작. 쓸모없어진 notice
  `"UV Editor/Create"` 삭제 (test_step101 의 죽은 규칙), Auto Seams notice 문구 갱신.

## 검증

Automatic, 오브젝트 모드, 기본값 (셸 / 셸당 면 / UV 수):

| 오브젝트 | Maya 2022 | 킷 |
|---|---|---|
| 큐브 | 6 / 1×6 / 24 | 6 / 1×6 / 24 |
| 구 20×20 | 6 / 104 104 72 72 24 24 / 482 | 6 / 104 104 56 56 40 40 / 474 |
| 실린더 (Create 메뉴 기본, 캡 1) | 6 / 20 20 6 6 4 4 / 90 | 6 / 20 20 6 6 4 4 / 90 |
| 평면 10×10 | 1 / 100 / 121 | 1 / 100 / 121 |
| 토러스 | 10 / 96 96 36×4 16×4 / 536 | 10 / 112 112 28×4 16×4 / 536 |

컴포넌트 모드 큐브 f[1] → 3 셸 (3, 2, 1), f[0:1] → 5 셸 (2, 1, 1, 1, 1): Maya 와 같음.
Contour Stretch: 평면 (오브젝트) 1 셸 / 121 UV / 0–1 = Maya; 한 줄 10 면 → 2 셸 (90, 10) = Maya; 큐브 1 셸 (Maya 1 셸,
UV 8 개 vs 킷 14 개). Blender `uv.smart_project` (66°) 는 구 106 106 48 48 46 46 이라 쓰지 않음.

- `python tests/run.py -k step139,step66,step101,step103,step104,enable_disable,step130,step136,step54`: 91 passed, 0 failed
  (13 파일; `test_step139_uv` 7 개).
- `python tests/gui/run.py -k step139_uv,step66,step104`: 22 passed, 0 failed. `gui_step139_uv`: 오브젝트 모드 큐브 →
  킷 UV 메뉴 (키보드 Home + ↓4 + Return) Automatic → (1 셸, 14 UV) → (6, 24); UV Editor > Create > Best Plane 활성,
  실행 → 1 셸; Contour Stretch 실행 → 1 셸, 컴포넌트 모드 유지. 그림 `gui_step139_uv_menu.png`,
  `gui_step139_uv_editor_create.png`.

## 남은 것

- Maya 기본 Optimize "Less distortion" (-o 1) 의 면 재배치 규칙은 못 풀었음: 구 / 토러스 셸 크기만 다름 (셸 수는 같음).
  킷 = Maya "Fast" (-o 0) 규칙 (구 측정 104 104 56 48 48 40 과 동점 처리만 다름). delegated.
- Planes 3 / 4 / 5 / 8 / 12 의 평면 방향은 근사 (3 = 6 축, 4 / 8 / 12 = 정다면체 면, 5 = 위 / 아래 + 둘레 3): Maya 와
  셸 수 비교는 6 만. delegated.
- Contour Stretch 는 Maya 의 4 모서리 곡면 보간이 아님 (Follow Active Quads): 큐브 / 구의 UV 모양은 다름.
- 마킹 메뉴 UV 방사 "Automatic" (`marking/menus.py`) 와 Polygons 셸프 Automatic Mapping (`ui/shelf_map.py`) 은 아직
  `uv.smart_project` (이 레인 파일 범위 밖).
- Camera-based 오브젝트 모드는 그대로 (뷰가 필요).
