# Step 144 — (0.4.0) Maya 모델링 도구 · Deform 메뉴 (#30 #31 #34)

## 계획

| 차례 | 레인 | 내용 | 파일 (그 레인만) |
|---|---|---|---|
| 1 | CAPTURE (Maya GUI 1 개) | Maya 2022 Tool Settings / 옵션 창: Quad Draw, Create Polygon, Append to Polygon, Offset Edge Loop, Slide Edge, Deform 메뉴 전부 (Lattice, Wrap, ShrinkWrap, Delta Mush, Tension, Texture, Nonlinear 6 종, Cluster, Soft Modification, Wire, Wrinkle, Jiggle, Proximity Wrap, Sculpt, Point On Curve) | `research/scripts/maya_options144/`, `research/maya/re/options_144.md` |
| 1 | POLY (worktree) | #30 Quad Draw = 라이브 표면 위 kit 도구 (Maya 클릭 · 수정키), Create Polygon / Append to Polygon = bmesh 모달 | 새 `ui/mesh_tools_poly.py` / `operators/poly_draw.py`, menu_map 의 해당 3 줄, tests |
| 2 | LOOP (worktree) | #31 Insert Edge Loop (한 번 클릭, 클릭한 곳), Offset Edge Loop, Slide Edge (MMB) + Maya Tool Settings | 새 `operators/edge_loops.py` / `ui/mesh_tools_loop.py`, option_windows_edit 의 insert_edge_loop, menu_map 해당 줄, tests |
| 2 | DEFORM (worktree) | #34 Deform 메뉴 = Maya 같은 디포머 생성 + 옵션 창 + Channel Box INPUTS + Paint Weights 가 그 디포머 가중치 | 새 `operators/deformers.py`, 새 `operators/option_windows_deform.py`, menu_map Deform 줄, notices Deform, channel_box INPUTS 연결, tests |

순서가 필요한 것: LOOP · DEFORM 은 CAPTURE 의 Maya 공장값이 테스트 기준이라 2 차례 (POLY 는 상호작용이 주라서 캡처와 함께 시작하고, 기본값은 캡처 md 가 나온 뒤 맞춤).
부하: 동시에 레인 2 개, Maya GUI 1 개 + Blender 1 개. 테스트: 기능 테스트 먼저 + 헤드리스 전체 + 바뀐 모듈 GUI 만.
새 문제는 즉시 GitHub 이슈 (마일스톤 0.4.0).
