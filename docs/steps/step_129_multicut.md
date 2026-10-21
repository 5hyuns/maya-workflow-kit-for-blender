# Step 129 (Multi-Cut lane) — Maya Multi-Cut 툴 + Tool Settings

GitHub #27 (Multi-Cut 이 Maya 처럼 동작하지 않음), #28 중 Multi-Cut Tool Settings 부분.
사용자 요청: "#27 Multi-Cut Maya 방식, #28 툴 옵션(Tool Settings) 전수 구현 포함".

## 근거

- 진입: Mesh Tools > Multi-Cut, Shift+RMB 마킹 메뉴 W, Ctrl+Shift+X, Polygons 셸프 `dR_multiCutTool` → 컨텍스트
  `nexMultiCutCtx1` [O] research/maya/workflows/modeling.md:30, research/maya/hotkeys_and_menus.md:57, 258-261,
  research/maya/shelves.md:46.
- Tool Settings (Maya 2022 화면, 공장 설정) [O] research/maya/workflows/shots/modeling_06_win1.png:
  Snap Step % **10**, Cut / Insert Edge Loop Tool (Smoothing Angle **180**, Edge Flow 끔 + 조절 1.0 (회색),
  Subdivisions **1**), Slice Tool (Ignore Backfaces 끔, Delete Faces 끔, Extract Faces 끔 + 오프셋 0.5 0.5 0.5 (회색),
  Slice Along Plane YZ / ZX / XY), 접힌 Color Settings / Live Constraint Options / Keyboard/Mouse Shortcuts.
  이슈 본문의 "기본 25 %" 는 이 실측과 다르다 → 실측 10 유지 (delegated).
- 컷 결과 (mayapy 2022 실측, research/maya/re/multi_cut.md): `polySplit(ep=[(e, t), ...])` 의 t 는 엣지의 첫 정점에서의
  비율, 한 면을 가로지르는 두 점 컷 = 정점 +2, 엣지 +3, 면 +1 (큐브 8/12/6 → 10/15/7).
- 손 동작 (#27 기대 동작 목록, Maya 도움말 기억) [K]: 엣지 클릭 = 점 (% 표시), 면 안 클릭 = 면 위 점, 다음 점까지 미리보기 선,
  누른 채 드래그 = 엣지를 따라 미끄러짐, Shift = Snap Step, Ctrl 호버 = 링 전체 엣지 루프 미리보기, Ctrl+클릭 = 루프,
  Ctrl+Shift = 스텝 위치 루프, Ctrl+MMB = 가운데 루프, 정점 클릭 = 정점에서 시작, Backspace = 마지막 점 지우기,
  RMB / Enter = 완료 후 툴 유지, Esc = 취소 (점이 없으면 툴에서 나감 = Select), 면 위 드래그 = 슬라이스.
- 재료: step 64 `operators/mesh_tools.py` (`edge_ring` / `insert_loop` / `snap_factor` / `edge_factor`), step 74
  `operators/preselect.py` (`caches`, `project`, `pick_vert`, `pick_edge`, `MeshCache.ray` — numpy + BVH, 가림 판정),
  step 64/79 의 WorkSpaceTool 등록 방식 (`ui/mesh_tools.py`).

## 계획

1. **툴** `allset.multi_cut_tool` (WorkSpaceTool, EDIT_MESH, `ui/mesh_tools.py` 에 등록, knife 뒤). 키맵 (툴 키맵 =
   addon keyconfig):
   - LMB PRESS (any 수식키 = Ctrl / Shift / Ctrl+Shift) → `allset.multi_cut` (모달), Ctrl+MMB → `allset.multi_cut`
     (`center=True`).
   - MOUSEMOVE / Ctrl·Shift PRESS·RELEASE → `allset.multi_cut_hover` (PASS_THROUGH, 호버 상태만 갱신: 점이 없을 때의
     % 미리보기와 Ctrl 루프 미리보기). 시뮬레이션 이벤트도 수식키를 실어 오므로 GUI 테스트 가능.
   - 대체 선택 (KEYMAP_FALLBACK) 없음: Maya Multi-Cut 의 LMB 는 선택하지 않는다.
2. **피킹** `multi_cut.pick(context, mouse)` → `Hit(kind, ob, index, t / co)`: preselect 캐시로
   ① 정점 (반경 `VERT_PX` 10 px × UI 배율, 가림 제외) ② 엣지 (반경 16 px, 가림 제외, t = 화면 투영 비율 → 원근 보정
   `edge_factor`) ③ 면 (BVH ray, 맞은 점 = 면 위 점). select mode 와 상관없음 (Maya Multi-Cut 은 모드 무관).
3. **상태 기계** (`allset.multi_cut` 모달, 모듈 상태 `SESSION` 은 그리기용):
   - IDLE → (LMB 누름) 정점/엣지/면 위 = 점 추가 후 DRAG; 빈 곳/면에서 SLICE_PX (8 px) 넘게 끌면 SLICE.
   - DRAG: 마우스 이동 = 그 점을 같은 엣지 위에서 미끄러뜨림 (Shift 면 스텝), 면 점은 같은 면 위에서; 놓으면 POINTS.
   - POINTS: 이동 = 미리보기 선 (마지막 점 → 호버 점); LMB = 다음 점 (마지막 점과 면을 공유해야 함, 아니면 경고 후 무시;
     다른 메시는 무시); Backspace = 마지막 점 제거; Enter / RMB = **완료** (bmesh 컷, 언두 한 단계, FINISHED → 툴 유지);
     Esc = 취소 (점 없으면 Select 툴로); Alt / MMB / 휠 / 그 밖의 키 = PASS_THROUGH (네비게이션).
   - LOOP: Ctrl+LMB / Ctrl+Shift+LMB / Ctrl+MMB 는 툴 키맵에서 any-LMB 항목보다 앞의 step 64 `allset.multicut_loop`
     (누른 곳 / 스텝 / 가운데, 엣지가 없으면 PASS_THROUGH). 처음엔 모달 안에서 드래그로 미끄러뜨린 뒤 중첩 호출하려 했으나,
     모달 안의 `bpy.ops...('EXEC_DEFAULT', True)` 는 언두 단계를 남기지 않아 (GUI 실측: Ctrl+Z 가 편집 모드 진입 전까지
     갔다) 키맵 항목으로 바꿈 → 언두 한 단계 + Adjust Last Operation Position (드래그 미끄러뜨리기 대신).
   - SLICE (드래그): 화면 선 + 시선 방향의 평면으로 `bmesh.ops.bisect_plane` (Ignore Backfaces = 카메라 쪽 면만,
     Delete Faces = 평면 한쪽 면 삭제, Extract Faces = 한쪽을 떼어 오프셋 × `maya_unit()` 만큼 이동).
     Slice Along Plane YZ / ZX / XY 토글이 켜져 있으면 클릭한 면 점을 지나는 월드 평면 (Maya Y-up → Blender: YZ = X 법선,
     ZX = Z 법선, XY = Y 법선) 으로 한 번에 자름 [K].
4. **컷 알고리즘** (`multi_cut.cut(bm, points)`, bpy 없이 bmesh 만, 헤드리스 테스트):
   - 점 = `('VERT', i)` / `('EDGE', i, t)` (t = edge.verts[0] 에서) / `('FACE', i, co)`.
   - ① 경계 점 (정점/엣지) 을 BMVert 로: 엣지 점은 `bmesh.utils.edge_split`; 같은 엣지에 두 점이면 원래 엣지의 정점 사슬에서
     t 가 들어갈 구간을 찾아 다시 나눈다. ② 연속한 경계 점 A, B 사이의 면 점들은 `face_split(f, A, B, coords=...)` 의
     중간 점. A-B 가 공유하는 면 중 (면 점이 있으면 그 점이 든 면, 없으면) 컷 중점에 가장 가까운 면을 자른다; 이미 엣지로
     이어져 있으면 건너뜀. 끝에 남은 면 점 (경계 점으로 안 끝남) 은 버린다 [K].
   - Subdivisions n > 1: 새 엣지를 `subdivide_edges(cuts=n-1)`. Smoothing Angle: 새 엣지의 면 각 > 값이면 sharp
     (`e.smooth = False`), 180 = 모두 부드럽게. Edge Flow: Blender 에 없음 → 회색 + 안내.
5. **그리기**: POST_VIEW (깊이 테스트 끔) = 점 (Maya 컷 점 [I] 노란 원), 확정 구간 선, 미리보기 선, 루프 미리보기;
   POST_PIXEL = 엣지 점 옆 `NN%` (첫 정점 기준).
6. **Tool Settings** (`draw_settings`, Tool Settings 도크 = Properties Tool 탭에서 보임; 툴 헤더에는 Snap Step 만):
   Snap Step % 슬라이더, "Cut / Insert Edge Loop Tool" 상자 (Smoothing Angle, Edge Flow 회색, Subdivisions),
   "Slice Tool" 상자 (Ignore Backfaces, Delete Faces, Extract Faces + 오프셋 (Extract 꺼짐 = 회색, Maya 와 같음),
   Slice Along Plane 토글 3개), Color Settings / Live Constraint Options 회색 + 안내, Keyboard/Mouse Shortcuts 목록.
   설정은 `Scene.allset_mesh_tools` (기존 PG) 에 추가, Reset Tool 은 그 PG 값을 기본값으로 (`tool_settings` 의 Reset 에 연결).
7. **연결**: `mesh_tools.MULTI_CUT_TOOL` = 새 id → 메뉴 (`menu_map`), 셸프 (`shelf_map dR_multiCutTool`), 마킹 메뉴
   (`marking/menus.MULTI_CUT`), Ctrl+Shift+X (`maya_patches.patch_key_batch`, `mapping.py`), command line 도움말.
   step 64 의 knife 패치 (`patch_multi_cut`: knife 툴 Ctrl/Shift 항목 + knife 모달 Shift 재배치) 와 `multicut_snap` /
   스냅 보정 타이머는 Multi-Cut 이 knife 가 아니게 되어 제거 → Blender knife 는 Blender 그대로.
8. **테스트**: 헤드리스 `tests/test_step129_multi_cut.py` (컷 알고리즘: 두 엣지 점 = +2/+3/+1, 면 점 경유, 정점 시작, 같은 엣지
   두 점, 루프, 슬라이스, Subdivisions, Smoothing, 설정 기본값, 툴 등록 / 키맵 / 연결, 해제 깨끗), GUI
   `tests/gui/gui_step129_multi_cut.py` (엣지 두 번 클릭 + RMB = 면을 가로지르는 새 엣지, Ctrl+클릭 = 루프,
   Backspace = 점 제거, Shift = 스텝).

## 실측 / 가정 구분

| 항목 | 근거 |
|---|---|
| Tool Settings 필드와 기본값 | [O] modeling_06_win1.png |
| polySplit 의 t 기준과 결과 개수 | [O] mayapy (research/maya/re/multi_cut.md) |
| 클릭/드래그/수식키 동작 | [K] #27 목록 (GUI Maya 로 재지 않음: nex 컨텍스트는 mayapy 에서 안 뜸 — `nexMultiCutCtx` 명령 없음) |
| % 표시 기준 (첫 정점), 점 색, 정점 스냅 반경 | [I] |
| 슬라이스: 평면이 메시 전체를 자름, Delete Faces 가 지우는 쪽 | [K] |
| Slice Along Plane 이 클릭 점을 지나는 평면 | [K] |

## 한 일

- `src/allset/operators/multi_cut.py` (새): bmesh 컷 `cut` (polySplit: 엣지 점 t = 첫 정점 기준, 면 점 = `face_split` coords,
  같은 엣지 두 점 = 정점 사슬, Subdivisions = 사슬을 n 등분한 coords, Smoothing Angle = 새 엣지 `smooth`), `loop` /
  `loop_segments` (step 64 `insert_loop` / `edge_ring`), `slice_mesh` (`bisect_plane` + Delete / Extract), 피킹 `pick`
  (preselect 캐시: 정점 10 px → 엣지 16 px → 면 BVH, 가림 제외, select mode 무관), 모달 `allset.multi_cut` (상태
  PRESS / DRAG / POINTS / SLICE), 호버 `allset.multi_cut_hover` (MOUSEMOVE·Ctrl·Shift 키맵 항목, PASS_THROUGH),
  `allset.multi_cut_exit` (Esc, 점 없을 때 → `builtin.select_box`), `allset.multi_cut_reset`, POST_VIEW / POST_PIXEL 그리기.
- `ui/mesh_tools.py`: WorkSpaceTool `ALLSET_TL_multi_cut` + `draw_multi_cut` (Maya 순서의 Tool Settings, 회색 3 줄 =
  Edge Flow / Color Settings / Live Constraint Options, `PANEL_NOTICES`). 예전 knife 위 Multi-Cut 패널 append 제거.
- `operators/mesh_tools.py`: PG 에 Maya 필드 추가 (실측 기본값), `MULTI_CUT_TOOL` = 새 id, `multicut_loop` 이 Smoothing Angle
  적용, knife 용 `multicut_snap` / 스냅 보정 타이머 제거. `keymap/maya_patches.py`: `patch_multi_cut` 제거 (Blender knife 는
  Blender 그대로), Ctrl+Shift+X → 새 툴. 메뉴 / 셸프 / 마킹 메뉴 / `mapping.py` / command line 도움말 → 새 툴.
- `ui/tool_settings.py`: Reset Tool 이 Multi-Cut 이면 PG 값을 공장값으로. `ui/menu_sets.py` `menu_tool`: 편집 모드 진입을
  `undo=True` 로 (Multi-Cut 첫 컷 뒤 Ctrl+Z 가 오브젝트 모드로 빠지던 것, GUI 실측).
- 실측 기록: `research/maya/re/multi_cut.md` (mayapy: polySplit 결과, nex 컨텍스트 없음, optionVar 없음).

## 검증

- 헤드리스 `tests/test_step129_multi_cut.py` 13 개 (컷 개수 = mayapy 10/15/7, 면 점, 정점 시작, 같은 엣지, 면 공유 규칙,
  Subdivisions, 루프, 슬라이스 / Delete / Extract, 스냅, 기본값 / 리셋, 툴 키맵 / 해제, 연결, knife 원상태).
- GUI `tests/gui/gui_step129_multi_cut.py` 14 개 (엣지 두 번 클릭 + RMB = +2/+3/+1, 미리보기 호버, Backspace, 툴 유지, 언두
  한 단계, Ctrl 호버 루프 미리보기, Ctrl+클릭 루프, Shift 25 % 스텝 + Enter, Esc → Select), step 64 / 79 GUI 18 개 통과.
- 수동: `docs/manual_checks.md` 「Step 129 Multi-Cut」.

## 남은 것

- 점 찍는 중 Ctrl 루프, Ctrl+드래그로 루프 미끄러뜨리기 (지금은 Adjust Last Operation Position), Edge Flow, 슬라이스 범위를
  드래그한 선 길이로 제한할지 (지금은 메시 전체) — Maya GUI 에서 재서 정하기.
- #28 의 나머지 툴 (Move/Rotate/Scale 외 Select / Extrude / Bevel / Bridge / Insert Edge Loop / Quad Draw ...) 의 Tool Settings
  인벤토리는 이 레인 범위 밖.
