# Step 165 — Component-mode Channel Box and RMB node submenus

Backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_164.json` item 2 (audit 11: `step_163_quant.md` §5c-1 /
§5c-4, look_compare image 08, dogfood 05). HANDOFF called the file `backlog.json`; it is `backlog_164.json`.

## 계획

Measure first (Maya 2022 GUI, factory prefs): `research/scripts/maya_cb165/` (launch.ps1 + cb165.py, audit7 / cb135 style:
Channel Box dock grabs + `cmds.channelBox` queries; the RMB list built by `dagMenuProc` into a popup, every submenu filled
by running its postMenuCommand as Maya does, then grabbed as a QMenu). Result spec: `research/maya/re/cb_component_164.md`.

Lanes: sequential on purpose (one lane): the Maya measurement decides the rows / items, and both code parts are small and
share `attribute_editor.tabs` as the node list. Parallel agents would only wait on the same measurement (delegated).

A. Channel Box, component mode (`ui/channel_box.py`): the lead object in edit mode → Maya's shape view: the shape name,
   `CVs (click to show)` when points are selected (click = the selected points' rows), INPUTS (same node rows as object
   mode). No Translate / Rotate / Scale / Visibility rows, no SHAPES header.
B. RMB list (`marking/menus.py`, bpy-free): `with_nodes(menu, nodes)` replaces the greyed DG Traversal / Inputs / Outputs
   with submenus built when the menu opens (`marking/modal.py`, like `with_object_name`); the node lists come from
   `marking/rmb_nodes.py` (bpy) = `attribute_editor.tabs` order (history record, modifiers, creation node, constraints).
   Inputs = Select All / Enable All / Disable All, the nodes by Maya type nice name (option box = Attribute Editor on that
   node), All Inputs... ; Outputs = the same frame over what this object drives (modifiers / constraints of other objects
   that use it); DG Traversal = Select <object>, History / Future node names, each a submenu (Select <node>).
   Picking a node = Maya `select -add <node>`: the object stays selected and the Channel Box opens that node under
   INPUTS (+ the Attribute Editor tab follows).
C. Tests: headless rows in edit mode, marking data (`test_step8`, `test_step52`, `test_step136` notices), the new
   submenus; GUI screenshot RMB > Inputs; look_compare 08 crop.

## 한 것

- Maya 측정 (GUI Maya 2022, 두 번 실행: 첫 실행은 Channel Box 가 idle 에서 갱신돼 한 단계 늦은 상태를 찍음 → 1.5 s 뒤 찍기):
  `research/scripts/maya_cb165/`, 명세 `research/maya/re/cb_component_164.md`, 화면 `research/maya/screens/cb165/`.
  - 컴포넌트 모드: 점 선택 = shape 이름 + `CVs (click to show)` + INPUTS (transform 행·SHAPES 없음), 클릭 = 선택 점 표
    (인덱스, X Y Z, 다음 선택에도 열린 채), 모서리 / 면 = shape + INPUTS, 아무것도 안 고름 = 빈 Channel Box 안내.
  - RMB Inputs = Select / Enable / Disable All, 노드 (타입 nice name, 새것 먼저, 옵션 상자 = AE), All Inputs...;
    Outputs = 같은 틀, 메시는 비어 있음 (backlog 의 "shading group / deformers" 는 측정과 다름 → 측정을 따름);
    DG Traversal = Select pCube1, History / Future 노드 이름, 각각 하위 메뉴.
- `ui/cb_points.py` (새): CVs 줄 / 표 (Scene 프록시 `allset_cb_points.p<k>_<x|y|z>`, 표시 단위, 상대 입력, 64 점까지 + "+N").
  값은 Maya 의 tweak (0) 대신 물체 공간 정점 위치 — Blender 에 tweak 층이 없음 [delegated].
- `ui/channel_box.py`: `component_mode` (MESH / CURVE / SURFACE / LATTICE 편집 모드) → `_draw_component_lines`
  (shape 이름 머리 + CVs + `draw_inputs`), 선택 없음 = `draw_empty`. INPUTS 그리기를 `draw_inputs` 로 떼어 냄.
  `reveal(node)`: 고른 노드로 Channel Box 부분을 스크롤 (Maya 는 고른 노드 속성이 보임).
- `marking/menus.py`: `NodeList` (열릴 때 채움, 회색 아님), `fill` / `with_nodes`; `marking/rmb_nodes.py` (새): 노드 목록
  (= Channel Box INPUTS 순서: 압출 기록, 모디파이어, 생성 노드, 제약; shape, shading group; Outputs = 이 물체를 쓰는 다른
  물체의 모디파이어 / 제약), 연산자 `allset.mm_node` (select -add / -r, CB 노드 열기 + AE 탭, 옵션 상자 = AE),
  `mm_node_all` (Select / Enable / Disable All = 모디파이어 viewport + render, 제약 enabled), `mm_node_table`
  (All Inputs... 창: 노드별 Normal / Has No Effect), `mm_node_label` (History / Future 줄). `modal.py` 가 메뉴를 열 때 채움,
  파이 대체 경로 (`marking/__init__`) 도 그림. notices 의 DG Traversal / Inputs / Outputs 알림 삭제 (회색 marking 항목 6 줄 감소).

## 검증

- 헤드리스 `tests/test_step165_component_cb.py` 13/13 (편집 모드 행 목록, CVs 표 + 입력, 모서리 / 면 / 빈 선택, Inputs /
  Outputs / DG Traversal 데이터 = Maya 캡처, 노드 고르기, Enable / Disable / Select All, Outputs 사용자, 표 창).
  `test_step52` 갱신 (Inputs 는 이제 NodeList). 헤드리스 전체 **1540 / 1540**.
- GUI `tests/gui/gui_step165_component.py` 9/9: RMB > Inputs 화면 (`tmp/shots165/gui_step165_rmb_inputs_125.png`: Select All /
  Enable / Disable, Non Linear ❒, Poly Cube ❒, All Inputs...), Non Linear 고르기 → Channel Box 가 bend 노드로 스크롤되어 열림,
  컴포넌트 모드 화면 (shape + CVs + INPUTS, 표 열기).
- look_compare (`ALLSET_LOOK_TAG=s165`): 08 crop 의 킷 dock = pCubeShape1 / CVs (click to show) / INPUTS / polyCube1 (전에는
  Translate X … Visibility 10 행). 옛 Maya 샷 08 에 CVs 줄이 없는 것은 아마 그 캡처가 Channel Box 의 idle 갱신 전에 찍혔기 때문 (cb165 재측정
  `cb_vtx_three.png` 에는 있음). kit-drawn 6/6, viewport 11/12, scene 3/3, checks 9/9.

## 남은 것

- CVs 표는 Maya 처럼 3 줄 높이의 자체 스크롤이 아니라 Channel Box 스크롤 안의 줄들; 곡선 / 격자 편집 모드는 shape + INPUTS 만
  (CV 표는 메시만).
- DG Traversal 은 shape 아래 한 단계만 (Maya 는 노드마다 끝없이 들어감); Maya 의 "More..." (25 줄 넘음) 없음.
- 고른 노드의 줄 강조 (Maya 파랑) 없음 — 열림 + 스크롤만.
- 관련 GUI `-k step52,step136_items,step151_ring,step161_messages,step135_dock,step148_cb,step129_cb,step9_` 79 / 81:
  실패 2 = `gui_step52_hotbox_rmb` "the list is under the ring" 두 줄 — 165 이전 코드 (`git stash` 로 src 만 되돌려) 에서도
  같은 2 실패. step 161 의 "RMB 목록을 링 옆에" (판단 보류, manual_checks Step 161) 와 같은 건이라 이 단계에서 안 건드림.
  GUI 전체 묶음은 안 돌림 (Hermes 10-24: 릴리스 준비 때만).
