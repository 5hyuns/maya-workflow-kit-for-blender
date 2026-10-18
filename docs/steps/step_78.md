# Step 78 — 키 묶음: Graph 1/2/3 · Shift+Q / Alt+Q · Spin Edge · Shift+G · Ctrl+Shift+C

재점검 4차 backlog 7. `docs/keymap_mapping.md` 미검토 행 중 Maya 사용자가 자주 쓰는 다섯 묶음.

## 근거

| 키 | Maya | 근거 |
|---|---|---|
| Graph Editor 1 / 2 / 3 | Absolute / Stacked / Normalized 보기 (`graphEditorSetViewMode … 0/1/2`) | hotkeySetup.mel:148-150, research/maya/runtime_commands.json GraphEditor*View (defaultRunTimeCommands.mel:12992-13006) |
| Shift+Q (홀드) | 선택 툴 + 컴포넌트 모드, LMB = 컴포넌트 마스크 마킹 메뉴 (`buildSelectComponentMM` → `doSelectComponentMM`) | hotkeySetup.mel:286, research/maya/marking_menus.json `doSelectComponentMM` (buildSelectComponentMM.mel:31-160, popup :206 `-sh 1`) |
| Alt+Q (홀드) | 선택 툴, LMB = Vertices N / Edges E / Faces S / UVs W (`buildPolyMM` → `doSelectPolygonMM`) | hotkeySetup.mel:287, marking_menus.json `doSelectPolygonMM`, `buildPolyMM` (popup :49 `-alt 1`) |
| Ctrl+Alt+← / → | Spin Edge Backward / Forward (`performPolySpinEdge 1/0`) | hotkeySetup.mel:378-379, runtime_commands.json PolySpinEdge* (:9462-9471); 메뉴는 `ui/menu_map.py:283-284` |
| Shift+G | 마지막 동작 반복 후 마우스 위치로 이동 (`autoPlace -um; repeatLast; move x y z`) | hotkeySetup.mel:363, research/maya/interaction.md:208, defaultRunTimeCommands.mel:20561 |
| Ctrl+Shift+C | 뷰에서 카메라 만들기 (`MTcreateCameraFromView`) | hotkeySetup.mel:60, runtime_commands.json CreateCameraFromView (:740) |

IC 4.5 의 같은 이벤트 (덤프): Shift+Q = Grease Pencil 모드들 (편집선 토글), Alt+Q = Graph / Dope Sheet / NLA select_box (axis range),
Shift+G = Armature / Metaball / Grease Pencil select_similar · Clip / Sequencer select_grouped, Ctrl+Shift+C = Console 복사.
Object Mode / Mesh / Graph Editor 1/2/3 / Ctrl+Alt+화살표에는 IC 항목이 없다.

## 계획

1. **Graph 1/2/3** (`operators/graph_keys.py` `maya_kit.graph_view_mode`, "Graph Editor" 키맵): 1 = `use_normalization` 끔,
   3 = 켬. 2 Stacked 는 Blender 에 없음 → Normalized 와 같게 켜고 Help Line 안내 (delegated: 곡선을 띠로 나누는 그리기는
   데이터를 바꾸지 않고는 못 함). 키맵은 Graph Editor 에만 → 3D View 의 1/2/3 (Smooth Preview, step 15) 와 겹치지 않음.
2. **Shift+Q / Alt+Q** = `taphold.TapHoldBinding` 두 개 (Q/W/E/R 와 같은 "Object Mode" / "Mesh" 키맵; Grease Pencil 모드의
   Shift+Q 는 그대로).
   - 탭: Shift+Q = 선택 툴 + 컴포넌트 모드 (메시면 편집 모드로, `selectMode -component`), Alt+Q = 선택 툴.
   - 홀드 + LMB: `marking/menus.py` 에 `doSelectComponentMM` / `doSelectPolygonMM` 를 research JSON 위치 그대로.
     Blender 에 있는 것만 연결 — Poly Vertices / Poly Edges / Faces 체크 토글 (`maya_kit.component_mask`, 메시 select_mode 토글,
     필요하면 편집 모드로), All Components on / off, Select Objects = 오브젝트 모드. Alt+Q 네 항목 = F9 / F10 / F11 / F12 와 같은
     동작 (`maya_kit.component_mode`, `maya_kit.uv_component`). 나머지 (CV, 격자점, 파티클, 피벗, 핸들 …) 는 회색.
   - `tests/test_step8_marking_menus.py` 의 위치 검사에 두 메뉴를 넣는다.
3. **Spin Edge**: "Mesh" Ctrl+Alt+← = `mesh.edge_rotate(use_ccw=True)` (Backward), → = `use_ccw=False` (Forward) — 메뉴와 같은 값.
4. **Shift+G** = `maya_kit.repeat_at_mouse` ("3D View"): 마우스 아래 바닥 평면 점 (Maya Y=0 → Blender Z=0; 뷰가 평면과
   나란하면 원점 깊이의 뷰 평면) 을 먼저 구하고 `screen.repeat_last` 실행 → 오브젝트 모드면 선택 오브젝트마다 원점
   (Maya 피벗) 을 그 점으로 (`move x y z` 절대값 = 선택마다). 반복+이동이 언두 한 단계. Armature / Metaball 의 Shift+G
   (select_similar) 는 편집 키맵이 먼저라 그대로 (그림자 선언).
5. **Ctrl+Shift+C** = `maya_kit.camera_from_view` ("3D View", 오브젝트 모드): `create.KINDS['CAMERA']` 로 Maya 카메라
   (`camera1`, 클립) 를 만들고 뷰 행렬·렌즈 (원근) / ortho_scale (직교) 를 복사, 새 카메라 선택. 뷰는 그대로 (look-through
   안 함 — [I], delegated).
6. `keymap/mapping.py` 다섯 묶음 상태 → KIT, `python tools/gen_keymap_mapping.py`.
7. 다음 단계 79 (3D Cut and Sew) 의 x/s/d 는 UV 툴 키맵 안 — 여기 키와 겹치지 않음.

## 검증 계획

- 헤드리스 `tests/test_step78_key_batch.py`: 키맵 항목 (각 이벤트가 kit 연산자), graph_view_mode 세 값, component_mask 토글,
  repeat_at_mouse 의 바닥점 계산 (순수 함수) + 실제 반복 (큐브 생성 → 반복 → 두 번째 큐브가 그 점), camera_from_view 행렬,
  edge_rotate 바인딩, 메뉴 위치 (step 8 테스트).
- GUI: Shift+Q 홀드+LMB 메뉴 그림 (스크린샷), Alt+Q 메뉴 → Edges 선택 = 엣지 모드, Shift+G 마우스 위치, Ctrl+Shift+C, Graph 1/3.
- test_enable_disable, 키맵 섀도잉, 전체 테스트, dogfood.

## 한 것

- Graph Editor 1 / 2 / 3 = `maya_kit.graph_view_mode` (`operators/graph_keys.py`): Absolute / Normalized, Stacked = Normalized +
  Help Line 안내 (delegated).
- Shift+Q / Alt+Q = `marking.SelectComponentBinding` / `SelectPolygonBinding` ("Object Mode", "Mesh"): 탭 = 선택 툴 (Shift+Q 는 메시
  편집 모드로), 홀드 + LMB = `doSelectComponentMM` / `doSelectPolygonMM` (`marking/menus.py`, research JSON 위치 — step 8 위치 검사 통과).
  픽 마스크 체크 = `maya_kit.component_mask` (`display.toggled_mask`: Blender 는 모드 하나는 남김).
- Ctrl+Alt+← / → = `mesh.edge_rotate(use_ccw=True / False)` ("Mesh").
- Shift+G = `maya_kit.repeat_at_mouse` (`operators/key_batch.py`, "3D View"): 바닥점 (Z=0, 평면과 나란하면 원점 깊이) → `screen.repeat_last`
  → 오브젝트 모드면 선택 오브젝트마다 원점을 그 점으로 (부모가 함께 움직이면 자식은 따라감). 언두 한 단계.
- Ctrl+Shift+C = `maya_kit.camera_from_view` ("Object Mode"): Maya 카메라 (`create.create('CAMERA')`) + 뷰 역행렬 + 렌즈 = 뷰 렌즈 × 36/72
  (Blender 뷰포트 렌즈는 72 mm 센서 기준), 직교 = ortho_scale [I]. 뷰는 그대로 (delegated).
- `keymap/mapping.py` 9 행 → KIT, `docs/keymap_mapping.md` 재생성 (구현 113 → 122, 미검토 267 → 258).
- `tests/test_step8_marking_menus.py` 메뉴 수 23 → 25. manual_checks 6 항목, PLAN backlog 7 = 완료, CLAUDE.md 한 줄.

## 검증

- 헤드리스 `tests/test_step78_key_batch.py` 8/8 (키맵 9 항목, 메뉴 등록·위치, toggled_mask, component_mask, ground_point, move_to 자식,
  camera_matrix, graph_view_mode poll). step 8 마킹 메뉴 11/11 (위치 검사 포함), test_keymap_maya 12/12 (섀도잉), test_enable_disable 4/4.
- GUI `tests/gui/gui_step78_key_batch.py` 10/10: Alt+Q 홀드 + LMB 동쪽 = 엣지 모드 + 선택 툴, Shift+Q 메뉴 열림 (스크린샷 확인) + SE Faces
  토글, Shift+G = 두 번째 큐브가 마우스 아래 (2.99, 2.0, 0), Ctrl+Shift+C = camera1 행렬 오차 1e-6, Graph Editor 3 / 1.
- 전체: 헤드리스 627/627, GUI (기본 배율) 549/549, dogfood 47/47 (콘솔 오류 0).

## 남은 것

- Shift+Q 메뉴 항목에 Maya 체크 표시 (켜짐 상태) 가 없음 — 엔진 항목에 체크 상태 그리기가 필요.
- Stacked 보기는 Blender 에 없음 (Normalized 로 대신). Maya Graph Editor 툴바의 세 보기 버튼도 아직 없음.
- Camera from View 의 직교 크기 식은 실측 전 [I]; Maya 가 새 카메라로 Look Through 하는지 미확인 (kit 은 안 함).
- Shift+G 는 Live Surface (Make Live) 위 배치를 하지 않음 — 바닥 평면만.
