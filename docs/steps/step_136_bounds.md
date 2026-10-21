# Step 136 — 레인 BOUNDS (#56): 마킹 메뉴가 영역 경계에 잘리지 않게

계획: `docs/steps/step_136.md` 「설계」 A.

## 한 것

- **경계 띠** — `draw.window_edges(window, region)`: 창의 영역 사이 틈 + 각 영역 가장자리 위의 테두리를 띠 (x0, y0, x1, y1, region
  픽셀) 로 돌려준다. GUI 그림에서 잰 값 (`tmp/probe136/out/layout_1.0.png`, `layout_1.25.png`): 영역 틈 3 px, 양쪽 테두리 2 px,
  배율 1.0 / 1.25 모두 같음 (테두리 두께는 UI 배율을 따르지 않음, `pixel_size` 만 곱함). 띠 = 틈 + 양쪽 (2 + 1) px. 창 바깥 가장자리도 띠.
- **engine** (bpy 없음) — `fit_ring(..., edges=())`, `Session(..., edges=())`:
  - 목록 줄: 위에서 아래로 한 칸에 놓고, 가로 띠에 걸치는 줄은 띠 아래로 (Maya 처럼 한 칸 유지), 창 바닥에서만 다음 칸 (step 52).
    칸이 세로 띠에 걸치면 그 띠 오른쪽으로 넘긴다 (`_flow`, `_settle_list`).
  - 칸이 세로 경계 사이 빈 폭에 다 안 들어가면 (창 중간 높이의 RMB 목록 = 4 칸) 세로 경계선이 가로지르는 줄이 가장 적은 자리를 고른다
    (delegated: 세로 경계는 줄을 가르는 얇은 선이라 이 경우만 허용, 한 칸까지).
  - 방사 상자: 띠에 걸치면 띠의 변에 상자 변을 붙이는 후보 (x · y 조합) 중 가장 짧은 이동 + 창 안 + 이미 놓인 상자와 안 겹치는 곳으로
    (가까운 두 경계 사이에 안 들어가는 넓은 상자도 넘어간다).
  - 리스트 하위 메뉴 (`Session._inside_bounds` → `_around_edges`) 도 같은 규칙.
- **그리기 순서** — `draw.activate()` 가 마킹 핸들러를 지웠다 다시 추가 (`_draw_last`): 메뉴가 열릴 때 각 영역 POST_PIXEL 목록의 끝이
  되어 Time Slider 숫자 · Range Slider · 선반 등 나중에 등록된 킷 핸들러 위에 그린다. 핫박스도 `activate` 를 거친다.
- **modal.py** — `ALLSET_OT_mm_engine.invoke` 의 bounds 줄에 `edges = draw.window_edges(...)` 전달만 (핫박스 bounds 줄은 그대로).

## 검증

- 헤드리스 `python tests/run.py -k step33,step52,step129,step8,step136,enable_disable`: **184 passed, 0 failed (23 files)**.
  `tests/test_step136_bounds.py` 5 개: 모든 마킹 메뉴 × 뷰 위 56 점 = 1456 배치에서 창 밖 0, 가로 띠 위 0, 방사 상자 띠 위 0, 목록이 고리 위 0,
  줄 순서 유지; 세로 경계가 줄을 가르는 배치 14 개 (dagMenuProc / dagMenuProc_curve, 뷰 높이 300 의 7 점, 4 칸) — 각각 한 칸만.
  리스트 하위 메뉴, 띠 아래로 내린 줄이 한 칸 유지, edges 없으면 배치 그대로.
- GUI `python tests/gui/run.py -k step136,step129_marking,step33,step52` (1.25): **36 passed, 0 failed (4 files)**.
  `tests/gui/gui_step136_edges.py` 배율 1.0 (`--ui-scale 0.8`) 도 **2 passed**: 오브젝트 / vertex / edge / face × RMB / Shift+RMB /
  Ctrl+RMB × 뷰 위 · 아래 · 왼쪽 · 오른쪽 = 48 메뉴 모두 열림, 문제 0 (세로 경계 fallback 0).
- 그림 (`--shots`, 레포 밖 `tmp/shots136/s125`, `s100`, 각 48 장) 확인: 목록 줄이 3D View / Time Slider 경계를 넘어 그 아래로 이어지고
  (예 `1.25_object_rmb_left.png` 의 Select Similar, `1.00_object_shift_left.png` 의 Booleans), Time Slider 숫자가 메뉴 위에 안 보임,
  위 가장자리의 방사 상자는 뷰 헤더 위로 (경계 띠 아래), 왼쪽 가장자리의 넓은 상자는 Outliner | 뷰 경계 오른쪽으로.

## 남은 것

- Dope Sheet (Time Slider) 의 View2D 가로 스크롤바는 Blender 가 POST_PIXEL 뒤에 그려 메뉴 상자 위에 얇은 선으로 보인다
  (`1.00_object_rmb_bottom.png` 의 Vertex Face 상자 아래쪽). Python 으로 막을 수 없음.
- 핫박스 줄은 경계 띠를 피하지 않는다 (이번 범위 밖, 기존 bounds 만).
- 세로 경계 fallback (줄이 너무 많아 경계 사이에 안 들어갈 때) 은 한 칸이 세로선에 가린다.
- 오브젝트 모드 Ctrl+RMB 가 RMB 와 같은 dagMenuProc 메뉴를 연다 (GUI 로그) — 항목 레인 / 메뉴 정의 쪽 확인 필요.
