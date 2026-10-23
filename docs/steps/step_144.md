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

## 한 일 (상세: `step_144_poly.md`, `step_144_loop.md`, `step_144_deform.md`)

- CAPTURE: Maya 2022 Tool Settings / 옵션 창 29 개 + 디포머 24 종의 노드 · 이름 · INPUTS 값 · Paint Weights 대상
  (`research/maya/re/options_144.md`, 샷 `research/maya/screens/options144/`).
- #30: Quad Draw (라이브 표면 위 점 · Shift 채움 · Ctrl 루프 · Ctrl+Shift 삭제 · Tab 연장 · MMB 이동 · Shift 이완 — Maya
  Keyboard/Mouse Shortcuts 표대로), Create Polygon (클릭 점 → Enter = 새 polySurfaceN, Backspace, Limit points),
  Append to Polygon (경계 엣지 + 점 → 면) = 킷 도구 (`operators/poly_draw.py`, `quad_draw.py`, `ui/mesh_tools_poly.py`),
  Maya Tool Settings 섹션. 남은 것은 #89.
- #31: Insert Edge Loop (한 번 클릭 = 그 자리, 끌기 = 미끄러짐, Relative / Equal / Multiple, edge flow), Offset Edge Loop
  (끌기 = 양쪽 루프, Delete edge), Slide Edge (MMB) = 킷 도구 (`operators/edge_loops.py`, `ui/mesh_tools_loop.py`), 결과는 mayapy
  측정과 같음 (`research/maya/re/edge_loops_144.md`); Offset Edge Loop ❒ = Maya 창 (Enter Tool And Close / Enter Tool / Close).
- #34: Deform 메뉴 = Maya 같은 디포머 (`operators/deformers.py`): Lattice (선택 bbox 에 맞춘 ffd1Lattice, Maya 2 5 2, ffd1 /
  ffd1Base), Delta Mush, Wrap, Proximity Wrap, ShrinkWrap, Cluster, Soft Modification, Nonlinear 6 종 (+ Handle), Texture,
  Curve Warp; 옵션 창 14 개 (`option_windows_deform.py`), Channel Box INPUTS 에 Maya 속성 (Envelope, Smoothing Iterations,
  Curvature ...), Paint Weights > 디포머 = 그 디포머의 가중치 그룹. Blender 에 대응 없는 Tension / Solidify / Morph / Jiggle /
  Wire / Wrinkle / Sculpt 은 회색 + 알림.

## 검증

- 헤드리스 전체 (병합 뒤): **1307 / 1307** (156 파일; step144_poly 24, step144_loop 18, step144_deform 17).
- GUI (바뀐 모듈 + 관련, 한 번의 `-k`): step144 3 파일 + step129_tool_settings + step140_option + step136 — **89 / 89**.
  레인 안: poly 31 / 31, loop 14 / 14, deform 9 / 9; 스크린샷 (Create Polygon 점, Quad Draw 점 · 채움 · 연장, Insert / Offset / Slide 결과,
  Tool Settings dock, Lattice + INPUTS ffd1, Lattice Options 창) 레인이 직접 확인.
- 옵션 상자: window 74 / generic 43 / dead 233 (Deform 의 회색 항목이 dead 로 셈).
- GUI 전체 묶음은 돌리지 않음 (사용자 결정: 출시 준비에서만).

## 남은 것 / 새 이슈

- #88 Mesh Tools 메뉴로 편집 모드에 들어갈 때 되돌리기 단계가 없음 (첫 Ctrl+Z 가 오브젝트 모드까지 감).
- #89 Quad Draw 남은 것 (오버레이 색 옵션, Tab+MMB 빈 곳, Ctrl+Shift+RMB 메뉴, [K] 규칙).
- Insert Edge Loop Auto complete off / Fix Quads, Offset / Slide 드래그 감도, Lattice local mode, Sine / Flare / Squash 모양 근사,
  Nonlinear / Lattice 페인트 대상 추론.
