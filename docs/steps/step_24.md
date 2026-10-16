# Step 24 — 컴포넌트 Delete (메뉴 없이 삭제)

## 계획 (delegated)

- 근거: Maya Delete = `doDelete` (research/maya/runtime_commands.json `Delete`, defaultRunTimeCommands.mel:1161), 컴포넌트에서는
  선택한 요소를 바로 지운다 [K]. 엣지 = `DeleteEdge` "Delete non-border edges and cleanup their vertices"
  (`polyDelEdge -cv true`, :9369), 정점 = `DeleteVertex` "Delete selected vertices and their attached edges" (:9363).
  Ctrl+Delete / Ctrl+Backspace = `DeletePolyElements` (hotkeySetup.mel:375-376, Delete Edge/Vertex).
- 지금: IC "Mesh" 키맵 DEL / BACK_SPACE = `VIEW3D_MT_edit_mesh_delete` 메뉴 (IC:3061-3062) — step_23 탐색 세션 a2_05.
- `maya_kit.delete_components` (operators/component.py): 선택 모드 우선순위 면 > 엣지 > 정점 (`tool_settings.mesh_select_mode`),
  편집 중인 모든 메시에 bmesh 로
  - 면: `bmesh.ops.delete(context='FACES')` (안 쓰이게 된 엣지·정점도 사라짐 = Maya 면 삭제),
  - 엣지: 면 두 개 사이 엣지만 `dissolve_edges(use_verts=True)` (2-valence 정점 정리), 경계 엣지는 남기고 알림,
  - 정점: `dissolve_verts` (붙은 엣지가 사라지고 면이 합쳐짐).
  끝나면 선택 없음. 아무것도 없으면 CANCELLED.
- 키맵 (patch 22): Mesh DEL / BACK_SPACE 의 메뉴 항목 제거 → `maya_kit.delete_components`. Ctrl+DEL / Ctrl+BACK_SPACE 는 IC
  `mesh.dissolve_mode` 그대로 (엣지·정점에서 Maya Delete Edge/Vertex 와 같은 dissolve) → mapping 행 IC. 오브젝트 모드 Delete 는 그대로.

## 한 것

- `operators/component.py`: `delete_components(bm, mode)` + `maya_kit.delete_components` (편집 중인 모든 메시, 선택 모드 우선순위
  면 > 엣지 > 정점, 끝나면 선택 없음, 경계 엣지만 있으면 경고 + CANCELLED).
- 키맵 patch 22 (`patch_component_delete`): Mesh DEL / BACK_SPACE 의 Delete 메뉴 → `maya_kit.delete_components`.
  Ctrl+DEL / Ctrl+BACK_SPACE 는 IC `mesh.dissolve_mode` 유지; `keymap/mapping.py` `DeletePolyElements` = IC 로 검토,
  `docs/keymap_mapping.md` 재생성 (IC 6 → 8, 미검토 292 → 290; 일반 Delete 는 Maya 에서 hotkeySetup 행이 아니라 표에 없음).

## 검증

- 헤드리스 `python tests/run.py`: **246/246** (23 파일, 새 `test_step24_component_delete.py` 7개: 키맵 (Delete/Backspace = 킷, Ctrl =
  dissolve, 오브젝트 모드 Delete 그대로), 면 전체 → 0/0/0, 면 하나 → 8/12/5, 엣지 하나 → 6/9/5 (두 면 합치고 2-valence 정점 정리),
  경계 엣지 유지 (CANCELLED), 정점 하나 → 7/9/4, 선택 없음 CANCELLED).
- GUI `python tests/gui/run.py`: **179/179** (17 파일, 새 `gui_step24_component_delete.py` 7개: F11 → Ctrl+Shift+A → Delete = 면 0, 메뉴
  없음 (스크린샷 `tmp/shots24/gui_step24_deleted.png` 확인); F10 + Backspace = 엣지 dissolve; F8 → 오브젝트 모드 Delete = 오브젝트 삭제).
- `python tools/dogfood.py`: **46/47** (남은 실패 `=`), 콘솔 오류 0.

## 남은 것

- 정점 Delete 는 dissolve (면이 합쳐짐): Maya polyDeleteVertex 가 3개 이상 엣지가 붙은 정점에서 다르게 동작하는지 Maya 로 비교 필요
  (manual_checks).
- 커브/아마추어 편집 모드 Delete 는 IC 메뉴 그대로 (Maya 커브 CV 삭제는 다음에).
- UV Editor Delete (Maya DeleteUVs, hotkeySetup.mel:516) 미검토.
