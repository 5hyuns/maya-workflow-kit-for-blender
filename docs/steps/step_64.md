# Step 64 — Target Weld · Crease Tool · Multi-Cut 감각

근거: `research/maya/workflows/modeling.md` §1 B6·B8·C11 (:30-41, :49), §2 (6, 8, 11 = :98-116), 갭 표 (Target Weld 20 :146,
Multi-Cut 15 :150, Crease 12 :153), §4 결정 (:178-179), §5 후보 2 (:203-213); Maya 샷 `shots/modeling_06_win1.png` (Multi-Cut Tool
Settings), `modeling_08_win1.png` (Target Weld Tool Settings). 마킹 메뉴 슬롯 (지금 줄): `marking/menus.py:216,229,261,268,287,301`.

## 계획

### 실측 / 출처

- Maya 2022 문자열 (`$MAYA\resources\MayaStrings`, 복사 안 함 — 뜻만):
  - Target Weld 설명 (`m_targetWeldContextProperties.kTargetWeldToolDesc`): 정점이나 엣지를 끌어 목표에 놓는다, **선택된 정점·엣지가
    모두 병합**된다. 설정 Merge To: Target / Center, Preserve UVs (modeling_08_win1: Target, ✓).
  - Crease Tool (`kPolyCreaseToolLongAnnot`, `s_TpolyCreaseCtxStrings`): 컴포넌트 (정점/엣지) 를 고르고 **MMB 를 좌우로 끌기** —
    왼쪽 = 덜, 오른쪽 = 더. 머리글 "Crease Mode: Absolute/Relative   Crease Value: n.nn". 설정 Mode Absolute / Relative,
    Extend to creased components.
  - Multi-Cut (`kMTKMultiCutToolLongAnnot`): 엣지/면을 클릭해 자르기, 끌어서 slice. modeling_06_win1: Snap Step % 10,
    Cut/Insert Edge Loop (Smoothing Angle 180, Edge Flow, Subdivisions 1), Slice Tool. Ctrl+클릭 = 엣지 루프, Ctrl+MMB = 가운데 루프,
    Shift = Snap Step [K] (modeling.md:33).
- mayapy (`tmp/maya64/probe.py`): standalone 에서는 툴 컨텍스트가 만들어지지 않음 (`polyCreaseCtx`/`targetWeldCtx` → False) —
  기본값은 샷/[K]. `polyCrease -value 2.5` → 질의 2.5 (Maya crease 값 = 레벨 수 단위 sharpness).
- Blender 4.5 실측 (`tmp/probe64/p2.py`, 큐브 12 엣지 crease b, Subsurf 2 (limit surface 끔)): b ≥ √0.2 = 0.447 에서 완전히 각짐,
  0.437 은 아님; 레벨 1 은 √0.1 경계 → **Blender sharpness = 10·b²**. 그래서 **Maya c ↔ Blender b = √(min(c, 10)/10)** (c = 1 → 0.316,
  2 → 0.447, 10 → 1.0). 엣지 crease 는 일반 속성 `crease_edge` (정점 `crease_vert`, 없으면 만든다).
- `bmesh.ops.subdivide_edges(cuts=1, edge_percents=…)` 로 엣지 링을 자르면 쿼드마다 이어져 루프가 됨 (큐브: 정점 12, 엣지 20, 면 10;
  percent 0.25 = 그 엣지 verts[0] 에서 25 %).
- `bpy.utils.register_tool` 은 툴 키맵을 addon 키컨피그에 만들고 default 에 빈 키맵을 둔다 → Maya 키컨피그가 활성이어도 합쳐진다
  (`$S\modules\bpy\utils\__init__.py:1078-1092`). 지금 Multi-Cut = `builtin.knife`; 그 툴 키맵 "3D View Tool: Edit Mesh, Knife" 는 IC
  데이터 (blender_default 에서 옴, `$S\presets\keyconfig\keymap_data\blender_default.py:7424-7433`) 에 있어 `maya_patches` 로 고칠 수 있음.

### 1. Target Weld (delegated)

- 툴 `maya_kit.target_weld_tool` (WorkSpaceTool, VIEW_3D / EDIT_MESH, 라벨 "Target Weld", Knife 그룹 뒤), 키맵: LMB PRESS →
  `maya_kit.target_weld` (+ `KEYMAP_FALLBACK`: 정점 근처가 아니면 PASS_THROUGH → 선택 fallback).
- 모달: 누른 곳에서 가장 가까운 정점 (엣지 선택 모드면 엣지) 을 화면 거리로 고름 (반경 15 px × UI 배율, 같은 거리면 카메라에 가까운 것;
  가림은 무시 — delegated). 드래그 중 원본 → 마우스 고무줄 선 + 목표 후보 점 (POST_PIXEL). 놓은 곳의 가장 가까운 다른 정점/엣지
  (같은 오브젝트) 가 목표; 없으면 취소. ESC/RMB 취소.
- 병합 (bmesh, 순수 함수 `weld_vertices` / `weld_edges`): 정점 — 끈 정점이 선택돼 있으면 **선택된 정점 모두** + 끈 정점 → 목표
  (Maya 설명문), 아니면 끈 정점만. Target = 목표 위치, Center = 병합되는 정점들 (목표 포함) 평균. 엣지 — 끈 엣지의 두 끝을 목표 엣지의
  두 끝에 짝지음 (공유 정점이 있으면 나머지 끝끼리, 아니면 거리 합이 작은 쪽), Target = 목표 끝, Center = 짝의 중점.
  `bmesh.ops.pointmerge`; Preserve UVs 켬 = 병합된 정점의 UV 를 목표 정점 것으로 (`pointmerge_facedata`, 뜻은 [U] delegated).
  남은 정점 선택. 실행 (exec) 은 `source`/`target` 인덱스 속성으로 (테스트·redo), 한 언두 단계.
- 설정 = `Scene.maya_kit_mesh_tools` (weld_merge_to TARGET/CENTER, weld_preserve_uvs): 툴 헤더와 Tool Settings (Maya 순서).
- 정점 모드 + 이 툴이면 pre-selection 하이라이트 (`operators/preselect._enabled`) 도 켬 (Maya 는 끌 정점을 강조).
- 연결: 메뉴 `Mesh Tools/Target Weld`, Shift+RMB Object N / Vertex Merge▸S / Edge Merge▸S, 셸프 Polygons `MergeVertexTool`,
  MTK Tools 버튼 (MENU_NOTICES 의 회색 안내 삭제). Help Line 문구.

### 2. Crease Tool (delegated — 사용자 지시 「MMB 드래그 = transform.edge_crease」 와 다름)

- Maya 는 **좌우** 드래그, Blender `transform.edge_crease` 는 선택 중심에서의 거리 (spring) 라 손 감각이 다르고 값이 0–1 로만 보인다.
  그래서 킷 모달 `maya_kit.crease_drag`: MMB PRESS → 가로 이동 px × 0.02 (50 px = Maya 1, UI 배율 반영 — 감도는 [U]) 만큼 Maya crease
  값을 바꾸고 Blender 값 √(c/10) 로 씀; 머리글 "Crease Mode: Absolute   Crease Value: 2.00   (Blender 0.45)". MMB 놓기 = 확정
  (한 언두), ESC/RMB = 되돌림. Absolute = 모두 같은 값 (시작 = 선택 중 최댓값), Relative = 각자 더함. 기본 Absolute ([K]).
  엣지/면 모드 = 엣지 crease, 정점 모드 = 정점 crease. 선택이 없으면 Maya 머리글처럼 "Select components to crease".
  exec (`value`, `mode`) 로 테스트/redo.
- 툴 `maya_kit.crease_tool` (WorkSpaceTool, MMB PRESS → crease_drag, `KEYMAP_FALLBACK` = LMB 선택). 설정: Mode, Extend (회색).
- 안내 (`notices.NOTICES["Mesh Tools/Crease Tool"]`): Blender 는 0–1 로 저장 (1 = 완전히 각짐), 킷은 Maya 값으로 보여 주고
  √(값/10) 으로 저장; `3` 스무스 프리뷰 (Subsurf `use_creases`) 에서 보임.
- 연결: 메뉴 `Mesh Tools/Crease Tool`, Shift+RMB Object / Vertex / Edge 의 "Crease Tool" 항목.

### 3. Multi-Cut 감각 (delegated)

- "3D View Tool: Edit Mesh, Knife" 에 (`maya_patches._add`, knife 의 LMB PRESS 와 수식키가 달라 같은 이벤트 아님):
  - Ctrl+LMB PRESS → `maya_kit.multicut_loop` = 커서 아래 엣지의 링에 **클릭 위치 비율로** 엣지 루프 (뷰 광선과 엣지의 최근접점,
    `edge_percents`), Ctrl+Shift+LMB = 그 비율을 Snap Step 으로, Ctrl+MMB = 가운데 (Maya). 엣지가 없으면 PASS_THROUGH.
    쿼드가 아닌 면에서 링이 멈춤 (Blender Loop Cut 과 같음). exec (`object`, `edge`, `factor`) → Adjust Last Operation 으로 비율 조정.
  - Shift+LMB PRESS → `maya_kit.multicut_snap` = 커서 아래 엣지의 Snap Step % 지점으로 커서를 옮기고 (`Window.cursor_warp`) knife 를
    그 점에서 시작 (툴의 knife 설정을 넘김). 엣지가 없으면 PASS_THROUGH.
- "Knife Tool Modal Map": Shift = IGNORE_SNAP → **SNAP_MIDPOINTS** (자르는 중 Shift = Snap Step 50 %; Blender 는 중점만 가능 — 안내).
  Ctrl 중점 스냅은 그대로.
- Tool Settings (VIEW3D_PT_active_tool 에 덧붙임, Multi-Cut 일 때): Snap Step % (`Scene.maya_kit_mesh_tools.snap_step`, 10),
  Cut / Insert Edge Loop Tool (Smoothing Angle · Edge Flow · Subdivisions 회색), Slice Tool (회색, "Blender Bisect 툴") + Blender knife 설정.
- Help Line: "Multi-Cut: click edges to cut, Enter to complete. Ctrl+click: edge loop, Shift: snap step".
- 키맵 매핑 (`keymap/mapping.py`): MultiCutToolNameCommand 행 note 갱신 (Maya 핫키 표에는 툴 안 Ctrl/Shift 가 없음), 문서 재생성.

### 4. 등록 / 해제

- `operators/mesh_tools.py` (bmesh 함수, 연산자, Scene 설정) + `ui/mesh_tools.py` (WorkSpaceTool 둘, Tool Settings 덧붙임).
  `unregister` 는 `unregister_tool` (키맵도 지움), 덧붙인 draw 제거, 실행 중 draw 핸들러 제거. step 59 의 `_tools` 교체와는 순서 무관
  (등록 역순 해제).

### 5. 검증

- 헤드리스 `test_step64_mesh_tools.py`: crease 매핑 실측 (b = √0.2 에서 레벨 2 각짐, 그 아래 아님), crease exec (Absolute/Relative,
  정점 crease), weld 정점 (Target 위치, Center 평균, 선택된 것 모두, 정점 수 −1/−n, 언두), weld 엣지 (공유 정점/평행), multicut 루프
  (큐브 12/20/10, 비율 0.25 위치, 링이 삼각형에서 멈춤), snap 비율 함수, 툴 등록 (tool_set_by_id) + 키맵, 메뉴·마킹 메뉴·셸프·MTK 연결,
  knife 키맵 항목과 modal map Shift, 안내.
- GUI `gui_step64_mesh_tools.py` (modeling_06·08): Shift+RMB Object 메뉴 N = Target Weld → 편집 모드 + 툴 → F9 정점 모드 → 정점 PRESS /
  MOUSEMOVE / 다른 정점에서 RELEASE (따로 틱) → 정점 8 → 7, 위치 = 목표; Ctrl+Shift+X → Ctrl+엣지 클릭 → 정점 +4; Shift+클릭 → knife
  시작점이 Snap Step 지점; Crease 툴 MMB 드래그 → crease > 0, `3` 프리뷰 스크린샷.
- `docs/manual_checks.md`, dogfood.

## 한 것

- **Target Weld** (`operators/mesh_tools.py` `maya_kit.target_weld`, 툴 `maya_kit.target_weld_tool` in `ui/mesh_tools.py`): Knife 그룹 뒤에
  등록된 편집 메시 툴, LMB PRESS = 모달 (정점/엣지 근처가 아니면 PASS_THROUGH → 선택 fallback). 드래그 중 노란 고무줄 선 + 목표 빨간 점,
  머리글 "Target Weld: release over the target vertex". 놓으면 `weld()`: 정점 — 끈 정점이 선택돼 있으면 선택된 정점 모두 + 끈 정점 → 목표,
  아니면 끈 정점만 (`pointmerge`, 목표가 남음, Center = 평균); 엣지 — 끝을 짝지어 병합 (공유 정점 유지 / 거리 합이 작은 짝). Preserve UVs =
  `pointmerge_facedata` (목표 UV). 결과 정점 선택, 한 언두, Adjust Last Operation 에 Merge To / Preserve UVs. 정점 모드 + 이 툴이면
  pre-selection 강조 (`preselect._enabled`).
- **Crease Tool** (`maya_kit.crease_drag`, 툴 `maya_kit.crease_tool`): MMB PRESS → 가로 드래그 50 px = Maya 1 (UI 배율 반영), 머리글
  "Crease Mode: Absolute   Crease Value: 2.00   (Blender 0.45)", 놓기 = 확정, ESC/RMB = 원래 값. Absolute (선택 중 최댓값에서 시작, 모두 같은 값) /
  Relative (각자 더함). 엣지 (면 모드 = 선택된 엣지) `crease_edge`, 정점 모드 `crease_vert`. 저장 = √(c/10) (실측 sharpness = 10·b²).
  선택 없으면 "Select components to crease". 툴 설정 Mode + Extend (회색).
- **Multi-Cut** (knife 그대로): "3D View Tool: Edit Mesh, Knife" 에 Ctrl+LMB = `maya_kit.multicut_loop` (클릭한 자리 비율, 뷰 광선 ∩ 엣지),
  Ctrl+Shift+LMB = Snap Step 자리, Ctrl+MMB = 가운데, Shift+LMB = `maya_kit.multicut_snap` (커서를 Snap Step % 점으로 `cursor_warp` →
  knife 시작, 툴의 knife 설정 전달; 커서는 정수 픽셀이라 knife 가 끝나면 타이머가 그 엣지 위 새 정점을 정확한 단계로 옮김). 루프 = 쿼드 링
  (`edge_ring`) + `subdivide_edges(edge_percents)`, 삼각형·경계에서 멈춤. "Knife Tool Modal Map" Shift = 중점 스냅. Tool Settings (패널) 에
  Snap Step % (Scene.maya_kit_mesh_tools, 10) + 회색 Smoothing Angle / Edge Flow / Subdivisions / Slice Tool (툴팁 안내).
- 연결: 메뉴 Mesh Tools > Target Weld / Crease Tool, Shift+RMB Object N · Vertex Merge▸S · Edge Merge▸S · Face 목록 Target Weld (research
  :396 에 있는데 빠져 있던 항목) · Crease Tool 세 곳, 셸프 Polygons `MergeVertexTool`, MTK Tools Target Weld (회색 안내 삭제), Help Line 문구,
  `notices` Crease 안내. 메뉴 □ (option box) = 툴 + Tool Settings (기존 `run_action`).
- 키맵 매핑: Ctrl+Shift+X / Ctrl+Shift+Q 행이 nameCommand 만 있어서 (runTimeCommand 없음) step 35 의 KIT 항목이 「미검토」 로 나오던 것을
  `mapping.entry_for` 가 nameCommand 로도 찾게 고침 → 둘 다 「구현」 (구현 97 → 99).

### 계획과 다르게 된 것 (delegated)

- Crease 는 사용자 지시의 `transform.edge_crease` 대신 킷 모달: Maya 문자열이 「MMB 를 좌우로」 이고 Blender 의 edge_crease 는 중심 거리
  (spring) 라 손 감각과 값 표시 (Maya 값) 가 다름. Undo / Adjust Last Operation (값·모드) 은 같음.
- Multi-Cut Shift 는 첫 점만 Snap Step % 단계, 자르는 중에는 Blender knife 가 중점 (50 %) 만 지원.

## 검증

- Blender 실측 `tmp/probe64/p2.py`: crease b 와 Subsurf 2 (limit 끔) 의 모서리 → b ≥ √0.2 각짐, 0.437 아님, 레벨 1 은 √0.1 → sharpness = 10·b²
  (테스트로도 고정).
- 헤드리스 `test_step64_mesh_tools.py` 12 개 (crease 매핑·exec·정점 crease, weld 정점 Target/Center·선택 따라옴·엣지 둘, snap 함수,
  루프 위치 0.25 → y 0.5 / 12·20·10, 삼각형에서 멈춤, snap 보정, 툴 등록·키맵·끄면 사라짐, knife 키·modal Shift, 메뉴·마킹 메뉴·셸프·MTK·안내).
- 헤드리스 `python tests/run.py`: **516/516** (60 파일; 그 뒤 snap 보정 테스트를 더해 step 64 단독 12/12).
- GUI `gui_step64_mesh_tools.py` 12/12 (기본 배율): Shift+RMB N → 편집 모드 + Target Weld, F9, 정점 PRESS / MOUSEMOVE / RELEASE (따로 틱) →
  8 → 7 정점·목표 위치, Ctrl+Z → 8, Ctrl+Shift+X → knife, Ctrl+클릭 0.3 → 루프 (+4 정점, 0.304), Snap Step 25 + Shift+클릭 0.33 → 첫 점 0.25,
  Crease 툴 MMB 100 px → 위 엣지 4 개 Blender 0.447 (Maya 2), 3 → 스무스 프리뷰. 샷 `tmp/shots64/gui_step64_weld_drag.png` (고무줄 선 + 빨간
  목표 점 + 머리글), `gui_step64_crease_preview.png` (위가 각진 프리뷰, 툴 헤더 Absolute / Relative), `gui_step64_multicut_snap.png`.
- GUI 전체 `python tests/gui/run.py --ui-scale 0.8`: **439/439** (48 파일).
- `python tools/dogfood.py`: **47/47**, 콘솔 오류 0. 키맵 매핑 문서 재생성 (구현 99).

## 남은 것

- Multi-Cut: 자르는 중 Shift 는 50 % 만 (Maya 는 Snap Step 단위), Shift 를 누른 채 호버할 때 스냅 점 미리보기·% 표시 없음, 끌어서 Slice 없음
  (Bisect 툴 안내), Edge Flow / Smoothing Angle / Subdivisions 없음.
- Target Weld: 가림 검사 없음 (뒤쪽 정점도 집힘), 엣지 모드에서 「선택된 엣지 모두」 병합 없음, Preserve UVs 의 정확한 Maya 의미 [U].
- Crease: 드래그 감도 (50 px = 1) 는 Maya 와 비교 안 함 [U], Extend to creased components · Crease Sets 없음; snap 보정은 knife 언두 단계 밖
  (같은 단계에 들어가지 않음).
