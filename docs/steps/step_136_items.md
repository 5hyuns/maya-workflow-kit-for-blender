# Step 136 — 레인 ITEMS (#74 #62): 마킹 메뉴 항목

계획: `docs/steps/step_136.md` 「계획」 B. 레인 BOUNDS (#56, 경계 / 그리기 순서) 는 따로.

## 한 것

- **`("item", "<Maya 메뉴 경로>")` 동작 형태** (`marking/menus.py` `_item`, `ui/menu_map.normalize` → `allset.menu_item`):
  마킹 메뉴 항목이 메인 메뉴 항목을 그대로 실행한다 — 컴포넌트 모드 규칙 (`menu_map.EDIT_MODE`), 오브젝트 모드 규칙
  (`OBJECT_MODE`), Maya 경고, 옵션 창. `marking/modal.py`: `poll_action` = 경로가 `menu_map.MAP` 에 있으면 활성 (poll 실패는
  회색이 아니라 Maya 경고), `run_action` 의 옵션 상자 = `run_action(MAP[path], option=True, path=path)`.
- **step_133_quant.md §7 의 25 개** 모두 연결 (Shift+RMB Extrude / Fill Holes / Quadrangulate / Booleans ×3, Vertex Normal Edit
  Tool, Detach, Circularize ×3, Soften/Harden, Edit Edge Flow, Wedge, Reverse Normals, Quad Draw, To UV Shell, Best Plane ×2,
  Contour Stretch ×2, UV Set Editor ×2, Make Live ×2). 그 밖에 같은 Maya 명령이 메인 메뉴에 있는 것: Append to Polygon / Create
  Polygon Tool, Bake Pivot Orientation (Modify/Bake Pivot), Toggle Outliner (Windows/Outliner), 3D Grab UV Tool (UV Editor Grab,
  delegated: 이 메뉴는 UV Editor 에서 열림), Select Similar (component mode = `mesh.select_similar`, `EDIT_MODE` 에 추가, delegated).
  `OBJECT_MODE` 에 Extrude (모든 면) / Fill Hole / Quadrangulate (오브젝트 전체) 추가 (delegated, Shift+RMB 오브젝트 메뉴에서 실행).
- **#62**: RMB 목록 Select All / Deselect All / Invert = 메인 메뉴 Select/All, Deselect All, Inverse (dagMenuProc.mel:2592-2595
  같은 runTimeCommand) → 컴포넌트 모드에선 `EDIT_MODE` 규칙 (Select All = 모든 컴포넌트, Deselect All = 비우고 오브젝트 모드,
  Invert = 컴포넌트 반전). Select Hierarchy = `allset.mm_select_hierarchy` (`select -hierarchy $object` :2594): 메뉴의 오브젝트
  (`allset_mm_target`, 없으면 active) + 자손으로 선택 교체, 컴포넌트 모드면 먼저 오브젝트 모드 (delegated).
- **새 연산자 / 메뉴** `marking/rmb_items.py`: `allset.mm_object_item` (메뉴의 오브젝트 하나에 메인 메뉴 항목 실행, 선택은
  되돌림 — Maya 가 `$object` 를 넘기는 것), `allset.mm_bounding_box` (toggleBoundingBoxDisplay), Actions ▸ = Template /
  Untemplate / Unparent / Bounding Box (createActionsMenuItems :1851-1854), `ALLSET_MT_uv_sets_rmb` (UV Set Editor + UV 맵, 체크 =
  현재, :2060-2104), `ALLSET_MT_color_sets_rmb` (Color Set Editor + color attribute, :2216-2252), `allset.mm_poly` (Ctrl+RMB
  To Edge Loop and Delete / Duplicate, To Edge Ring and Split / Collapse, To Vertex Perimeter, To Shell Border, Shift+RMB 면
  Reverse Propagate — research/maya/runtime_commands.json PolyConvertTo*), `allset.mm_camera_based` (Camera-Based Selection =
  킷 설정 「Marquee Selects Hidden Components」 반대). Paint Select ×3 = 원 선택 도구, Toggle Soft Edge / Vertex / Face Normal
  Display = 3D View 오버레이 체크 박스, Hypergraph / Set Editor (hotbox South) = Outliner 창, Shelf (hotbox East) =
  `allset.shelf_strip_toggle`.
- **알림**: 남은 회색은 모두 `ui/notices.MARKING` (키 `<proc>/<라벨 경로>` → (대체, 한 줄)). 마킹 메뉴가 회색 항목을 가리키면
  `marking/modal.hover_notice` → `notices.show` 로 Help Line 에 표시 (메인 메뉴 회색 항목의 툴팁과 같은 자리, step 54).

### delegated

- 3D Grab UV Tool → UV Editor Grab 도구; Select Similar 컴포넌트 모드 = `mesh.select_similar`; `OBJECT_MODE` 의 Extrude / Fill
  Hole / Quadrangulate = 오브젝트 전체 [K]; Select Hierarchy 를 컴포넌트 모드에서 = 오브젝트 모드로 가서 선택.
- To Edge Loop and Duplicate = 루프 선택 후 Blender Offset Edge Loop (3D View 에선 슬라이드 모달; Maya 는 offset 0.5 즉시).
- To Shell Border = 선택이 닿은 셸의 열린 경계 에지; Reverse Propagate = 선택 면 뒤집고 셸을 그 방향으로 맞춤 (manifold 에지만).
- Camera-Based Selection 은 체크 박스 표시 없음 (체크 상태 표시는 `engine.TOGGLE_OPS` = BOUNDS 레인 파일): 실행 시 상태를
  INFO 로 보고.

## 검증

- 헤드리스 회색 수 (`tests/test_step136_items.py` 가 출력): 항목 **464 → 472** (Actions ▸ 의 4 항목 × RMB 2 메뉴),
  회색 **128 → 73**, 알림 없는 회색 0, 회색 아닌 알림 키 0.
- `python tests/run.py -k step8,step101,step54,step136,step52,step29,step129,enable_disable,step130`: **227 passed, 0 failed** (29 files; research/ 를 worktree 에 junction 으로 연결해 step 8 방사 위치 290 개 대조 포함)
  (step 52 테스트: UV Sets / Color Sets 는 이제 Blender 메뉴 ▸, Make Live 매핑 — 기대값 갱신).
- 전체 헤드리스 `python tests/run.py`: 1064 passed, 4 failed (133 files) — 3 개는 worktree 에 research/ 가 없어서 (test_keymap_maya, step107, step108), 1 개는 step 94 기대값 (Bake Pivot Orientation 이 이제 Modify/Bake Pivot) → 테스트 갱신 후 research 연결해서 그 4 파일 + step 8 / 136 재실행 55 / 55 통과
- GUI `python tests/gui/run.py -k step136` (`tests/gui/gui_step136_items.py`): 9 / 9 — 컴포넌트 모드 RMB 의 Select All / Deselect
  All / Select Hierarchy / Invert / Select Similar 활성, 회색 Time Editor 위에서 Help Line 에 알림, Select All 놓기 = 8 정점
  선택 + 컴포넌트 모드 유지. 그림 `tmp/shots136/gui_step136_rmb_component.png`.

## 남은 것

- 남은 회색 73 개 = Blender 에 같은 것이 없는 Maya 항목 (아래 표, 알림 있음). Shift+Q pick mask 의 비메시 23 개는 한 알림
  (「Pick mask」) 을 같이 쓴다.
- Time Slider / Range Slider 토글 (hotbox East) 은 타임라인 영역 숨기기로 만들 수 있으나 레이아웃 변경이라 이번 범위 밖.
- 마킹 메뉴 체크 박스로 Camera-Based Selection 상태 표시 (engine `TOGGLE_OPS`, BOUNDS 레인 병합 뒤).
- 경계 / 그리기 순서 (#56) 는 레인 BOUNDS.

| 회색 항목 (`notices.MARKING` 키) | 알림의 대체 |
|---|---|
| `doSelectComponentMM/<비메시 컴포넌트 23 개>` (Points / Parm Points / Lines / Hulls / Pivots / Handles / Misc.) | Pick mask |
| `dagMenuProc/Vertex Face` | Face corners |
| `dagMenuProc/DG Traversal` | Modifier stack |
| `dagMenuProc/Inputs` | Channel Box INPUTS |
| `dagMenuProc/Outputs` | Outliner |
| `dagMenuProc/Metadata` | Custom properties |
| `dagMenuProc/Time Editor` | NLA Editor |
| `dagMenuProc_curve/Curve Point` | Control points |
| `dagMenuProc_curve/Hull` | Control points |
| `dagMenuProc_curve/Edit Point` | Control points |
| `dagMenuProc_curve/DG Traversal` | Modifier stack |
| `dagMenuProc_curve/Inputs` | Channel Box INPUTS |
| `dagMenuProc_curve/Outputs` | Outliner |
| `dagMenuProc_curve/Metadata` | Custom properties |
| `dagMenuProc_curve/Time Editor` | NLA Editor |
| `buildObjectMenuItemsNow/Complete Tool` | Enter |
| `buildObjectMenuItemsNow_pivot/Show Orientation Handle` | Transform orientation |
| `contextPolyToolsVertexMM/Reorder Vertices` | Sort Mesh Elements |
| `contextPolyToolsEdgeMM/Merge/Collapse Edges/Merge Edge Tool` | Merge / Bridge |
| `contextPolyToolsFaceMM/Assign Invisible Faces` | Delete faces / Hide |
| `contextPolyToolsDefaultMM/Pipe` | Extra Objects add-on |
| `contextPolyToolsDefaultMM/Helix` | Extra Objects add-on |
| `contextPolyToolsDefaultMM/Gear` | Extra Objects add-on |
| `polyConvertMM/Grow Selection/Grow Along Loop` | Select Loops |
| `polyConvertMM/To UVs/To UV Perimeter` | UV Editor |
| `polyConvertMM/Shrink Selection/Shrink Selection Along Loop` | Shrink |
| `polyConvertMM/To Face Path` | Shortest Path |
| `translateMarkingMenuImpl/Snap/Face Center` | Snap to Face |
| `translateMarkingMenuImpl/Keep Spacing` | Snap With |
| `translateMarkingMenuImpl/Axis/Live Object Axis` | Custom orientation |
| `translateMarkingMenuImpl/Axis/Custom` | Custom orientation |
| `rotateMarkingMenuImpl/Custom/Custom` | Custom orientation |
| `rotateMarkingMenuImpl/Custom/Reset` | Orientation: Object |
| `scaleMarkingMenuImpl/Axis/Live Object Axis` | Custom orientation |
| `buildSelectAllMM/Enable All Outputs` | Modifier stack |
| `buildSelectAllMM/Select All Outputs` | Modifier stack |
| `buildSelectAllMM/Disable All Outputs` | Modifier stack |
| `buildSelectAllMM/Select All Inputs` | Modifier stack |
| `HotboxNorthMenu/Persp/Relationship Editor` | Workspaces |
| `HotboxEastMenu/Time Slider` | Timeline area |
| `HotboxEastMenu/Range Slider` | Timeline header |
| `HotboxWestMenu/Hierarchy` | Select > Hierarchy |
| `HotboxWestMenu/Dynamics Mask` | Object types filter |
| `contextPolyToolsUVMM/Create UV Shell` | Unwrap |
| `contextPolyToolsUVMM/Delete UVs` | Unwrap / Reset |
| `contextPolyToolsUVMM/Auto Seams` | Smart UV Project |
| `contextPolyToolsUVMM/Texture Borders` | Seams overlay |
| `contextPolyToolsUVShellMM/Auto Seams` | Smart UV Project |
| `contextPolyToolsUVShellMM/Texture Borders` | Seams overlay |
| `doSelectComponentMM/All Components off` | Mesh select mode |
| `doSelectComponentMM/Save to shelf` | Quick Favorites |
