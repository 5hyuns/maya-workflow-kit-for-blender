# Step 66 — UV 워크플로우: UV Editor 진입 · UV Toolkit · UV 마킹 메뉴 · Cut / Sew / Unfold / Layout · Texel Density

근거: `research/maya/workflows/uv.md` §1 (1, 3–7), §2 (1, 3–7), 갭 표 (UV Toolkit 20, UV 컴포넌트 20, Cut 20, Unfold 20, Layout 20,
Sew 16, UV Editor 열기 15, UV Editor RMB 15, Texel Density 15), §4 개념 결정, §5 후보 A·B·C; Maya 샷 `shots/uv_01_win1.png` (UV Toolkit),
`uv_02_win1.png`, `uv_03_win1.png`; 키 `docs/keymap_mapping.md` polyTexturePlacementPanel 행 (hotkeySetup.mel:516-536).

## 계획

### 측정

- **UV Editor RMB 마킹 메뉴** (research 에 없던 것): Maya 2022 설치본 `scripts/others/texturePanelMenus.mel`
  `textureWindowCreatePopupRadialMenu` (polygon 판, popupType 0) — **S Face · N Edge · E UV · W Vertex · NW UV Shell**, 그 아래 목록 =
  UV Editor 메뉴 막대 복제 (`textureWindowCreatePopupMenubar`). texturePanel.mel:312-313 이 RMB (`-b 3`) 에 붙임. 이것을
  `research/maya/marking_menus.json` 에 `textureWindowCreatePopupRadialMenu` 로 기록 (출처 file:line) → test_step8 이 비교.
  Shift+RMB (UV / UV Shell) = 이미 research 에 있는 `contextPolyToolsUVMM` / `contextPolyToolsUVShellMM`.
- **Blender 섬 계산과 솔기** (`tmp/probe64/p66b.py`, 두 쿼드 + 가운데 솔기, UV 는 붙은 채): `uv.unwrap` (ANGLE_BASED / MINIMUM_STRETCH) 은
  솔기에서 나뉨, **`uv.pack_islands` · `uv.average_islands_scale` 은 솔기를 무시** (UV 좌표가 붙어 있으면 한 섬), sync 켜도 끄도 같음.
  → Maya Cut (그 자리에서 UV 를 끊음) 은 솔기만으로는 안 됨: 솔기 + **한쪽 셸을 2e-4 (1024 맵에서 0.2 px) 안쪽으로** 떼어 섬을 실제로 나눔.

### 1. UV Editor 진입 · UV 컴포넌트 (delegated)

- `maya_kit.open_editor(ui_type='UV')` (UV > UV Editor, Windows > Modeling Editors > UV Editor): 활성 메시를 편집 모드로, `use_uv_select_sync`
  켬 (메시 선택 = UV 선택, UV 가 다 보임). 이미 UV Editor 가 열려 있으면 새 창을 또 만들지 않음 (`uv_tools.find_uv_editor`).
- `maya_kit.uv_component(mode)`: UV Editor 를 보장한 뒤 Maya 컴포넌트로 — Vertex / Edge / Face = sync 켬 + 메시 선택 모드;
  **UV = sync 끔 + UV 정점 모드, UV Shell = sync 끔 + 섬 모드** (Maya 의 UV 는 메시 정점과 따로 고르는 점; Blender 는 sync 를 꺼야 따로 고름).
  sync 를 끈 Blender UV Editor 는 선택된 면의 UV 만 그리므로 이때 면을 모두 선택 (3D 뷰에는 면이 선택돼 보임 — 안내).
  F12 = UV, Alt+F12 = UV Shell (Object Mode / Mesh 키맵, Screen 의 F12 는 3D 뷰에서 가려짐 — shadows), 3D 뷰 RMB E 「UV」 = UV.
  Ctrl+F12 (ConvertSelectionToUVs) 는 「해당 없음」 그대로.

### 2. UV Editor 마킹 메뉴 (delegated)

- UV Editor RMB = `textureWindowCreatePopupRadialMenu` (위 다섯 + 목록: Cut / Sew / Unfold / Layout / UV Snapshot 없음 …은 메뉴 막대 대신 Maya
  UV 메뉴 핵심 몇 개), Shift+RMB = UV 모드면 `contextPolyToolsUVMM`, 섬 모드면 `contextPolyToolsUVShellMM` (Cut / Sew / Unfold / Layout /
  Optimize / Flip / Delete …, 없는 것 회색). "UV Editor" 키맵의 IC RMB 컨텍스트 메뉴 (`IC:614`) 를 `maya_kit.marking_menu` 로 바꿈;
  `marking.resolve` 가 IMAGE_EDITOR (UV 모드) 를 봄. 마킹 메뉴 엔진은 이미 이미지 편집기에서도 그림 (핫박스, step 9/52) — GUI 로 확인.

### 3. `operators/uv_tools.py` (delegated)

- 섬 계산 `islands(bm, uv, faces, seams=True)`: 엣지를 사이에 둔 두 면은 그 엣지의 두 끝 UV 가 같고 (1e-5) 솔기가 아닐 때만 같은 섬.
- **Cut** `maya_kit.uv_cut`: 선택 엣지 (sync = 메시 엣지, 아니면 UV 엣지 선택) 에 솔기 → 솔기로 섬이 둘로 나뉜 곳은 작은 쪽 섬의 그 엣지 끝 UV
  (그 섬 안에서 같은 좌표인 루프 모두) 를 섬 중심 쪽으로 2e-4 옮김 (섬이 실제로 나뉨, 눈으로는 그 자리). 안 닫힌 자르기는 솔기만 (다음 Unfold 가 엶).
- **Sew** `maya_kit.uv_sew`: 선택 엣지의 솔기 지움 → 엣지 양쪽이 다른 섬이면 작은 섬을 닮음 변환 (엣지 두 끝이 큰 쪽 두 끝에 오도록 이동·회전·
  크기) 하고 그 루프들을 같은 좌표로. 엣지마다 차례로 (섬이 합쳐지면 다음 엣지는 붙이기만).
- **Unfold** `maya_kit.uv_unfold`: 대상 = 선택 섬 (없으면 전부) → `uv.seams_from_islands` (지금 셸 경계 유지) → 그 면만 선택해
  `uv.unwrap(method='MINIMUM_STRETCH')` → 섬마다 원래 경계 상자 중심으로 되돌림 (Maya Unfold 는 셸 자리를 유지) → 선택 복원.
  안내: "Unfold3D 가 아니라 Blender Unwrap (Minimum Stretch) — 모양이 Maya 와 다를 수 있음".
- **Layout** `maya_kit.uv_layout`: `uv.pack_islands(rotate=True, margin_method='FRACTION', margin=패딩 px / 맵 크기)`, 대상 = 선택 섬 (없으면 전부).
  셸 패딩 기본 2 px, 맵 1024 ([K], uv.md:140).
- **Texel Density** `maya_kit.uv_texel_get` / `uv_texel_set`: 밀도 = √(Σ UV 면적 · 맵² / Σ 월드 면적 [Maya 단위²]) (px / Maya 단위 = 킷 템플릿에서
  px/cm, `units.maya_unit()`). Set = 섬마다 UV 중심 기준 균일 크기 (선택 오브젝트 모두). 설정 = `Scene.maya_kit_uv` (map_size 1024,
  texel_density, shell_padding 2).
- 키 ("UV Editor" 키맵, `maya_patches._add`): Shift+X Cut (IC 스냅 파이 제거), Shift+S Sew, Ctrl+U Unfold, Ctrl+L Layout (IC `uv.select_linked` 제거 —
  Maya 엔 셸 선택 키가 없음), Ctrl+Shift+X = 회색 (Create UV Shell 근접 없음). mapping.py polyTexturePlacementPanel 행 상태 + 문서 재생성.
- 메뉴: UV > Cut UV Edges / Sew UV Edges / Unfold / Layout (Maya UV 메뉴 경로 확인), UV Editor 셸프 항목, 3D Cut and Sew UV Tool = 회색 + 안내
  (다음 UV 단계, PLAN 「남긴 것」).

### 4. UV Toolkit (`ui/uv_toolkit.py`, delegated)

- IMAGE_EDITOR 사이드바 탭 "UV Toolkit" (UV 모드), uv_01_win1 순서: 컴포넌트 아이콘 (Vertex · Edge · Face | UV · UV Shell), "N object selected",
  Pick/Marquee · Drag · Tweak/Marquee (UV 선택 툴), Symmetry / Selection Constraint / Transform Constraint (회색), All · Clear · Inverse, 접는 절
  Pinning (Pin / Unpin / Invert) · Select By Type (Overlapping = `uv.select_overlap`, 나머지 회색) · Soft Selection (UV 비례 편집) · Transform
  (Texel Density: 맵 크기 · 값 · Get · Set; Flip U/V; Rotate ±90) · Create (Automatic / Planar / Cylindrical / Spherical / Camera-Based = 메뉴와 같은
  동작) · Cut and Sew (Cut · Sew · 3D Cut and Sew Tool 회색) · Unfold (Unfold · Optimize = `uv.minimize_stretch` · Straighten 회색) · Align and Snap
  (Align U/V 최소·최대 = `uv.align`) · Arrange and Layout (Layout + 셸 패딩 · Orient Shells = `uv.align_rotation`) · UV Sets (UV 맵 목록).
  회색 항목 안내 = `notices.PANEL_NOTICES`.

### 5. 검증

- 헤드리스 `test_step66_uv.py`: 섬 계산 (솔기 경계), Cut (두 쿼드 → pack_islands 가 두 섬으로 봄 = 측정 반대), Sew (붙고 솔기 없음, 작은 섬이 옮겨짐),
  Unfold (셸 중심 유지, 펼친 뒤 겹침 없음), Layout (0–1 안, 겹침 없음), Texel Density (단위 정사각형 = 계산값, Set 후 둘째 오브젝트 ±1%),
  uv_component 모드 (sync / select mode), open_editor 의 편집 모드 + sync, 키·메뉴·마킹 메뉴 (research 비교 = test_step8), 툴킷 등록.
- GUI `gui_step66_uv.py` (uv_01–03): 큐브 → UV > UV Editor → 새 창 UV 모드·편집 모드·sync, UV 보임 (샷) → 3D 에서 엣지 몇 개 선택 → UV Editor 에서
  Shift+X → 솔기 + 섬 분리 → Ctrl+U → Ctrl+L → 겹침 없음·0–1 안 → RMB 마킹 메뉴 NW UV Shell → 섬 모드, UV Toolkit 탭 (샷 vs uv_01_win1).
- `docs/manual_checks.md`, dogfood.

## 한 것

- **UV Editor 진입** (`operators/menu_extras.open_editor`, `operators/uv_tools.prepare`): UV 모드면 활성 메시를 편집 모드 + UV Sync Selection,
  UV Editor 가 이미 어느 창에 있으면 새 창을 만들지 않음. **`maya_kit.uv_component(mode)`** = Vertex / Edge / Face (sync 켬 + 메시 선택 모드),
  UV (sync 끔 + UV 정점), UV Shell (sync 끔 + 섬; 면을 모두 선택해 UV 가 다 보이게), Open. F12 / Alt+F12 (Object Mode · Mesh), 3D RMB E 「UV」.
- **UV Editor 마킹 메뉴**: RMB = `textureWindowCreatePopupRadialMenu` (Maya 설치본 texturePanelMenus.mel 에서 읽어 research JSON 에 기록:
  S Face · N Edge · E UV · W Vertex · NW UV Shell + 목록 Cut/Sew/Unfold/Layout/Select All/Pin/Unpin), Shift+RMB = `contextPolyToolsUVMM` /
  `contextPolyToolsUVShellMM` (Mapping ▸ 투영 8 방향, Cut · Sew · Merge = uv.weld · Unfold · Layout · Optimize = minimize_stretch · Flip U; 없는 것 회색).
  `marking.resolve` 가 이미지 편집기 UV 모드를 봄; IC UV Editor RMB 컨텍스트 메뉴 제거.
- **Cut** (`maya_kit.uv_cut`): 솔기 + 솔기로 나뉜 곳의 작은 셸을 그 섬 중심 쪽으로 2e-4 → Blender 의 pack / 섬 선택이 두 셸로 봄 (측정상 솔기만으로는
  안 나뉨). **Sew** (`maya_kit.uv_sew`): 솔기 지움 + 작은 셸을 닮음 변환 (복소수 a·z+b) 으로 엣지에 맞춤, 같은 셸 안 틈은 가운데로 붙임.
  **Unfold** (`maya_kit.uv_unfold`): 셸 경계에 솔기 → 그 면만 sync 로 골라 `uv.unwrap(MINIMUM_STRETCH)` → 셸마다 원래 경계 상자 중심으로, 선택·sync
  복원; 안내 문구. **Layout** (`maya_kit.uv_layout`): `pack_islands(rotate, FRACTION, 패딩 px / 맵)`, 셸끼리 텍셀 밀도 같음 (측정 157 / 157).
  **Texel Density** Get / Set (px / Maya 단위, `Scene.maya_kit_uv` map 1024 · density · padding 2). 대상 = 선택에 닿은 셸, 없으면 전부.
- 키 ("UV Editor"): Shift+X Cut (IC 스냅 파이 제거), Shift+S Sew, Ctrl+U Unfold, Ctrl+L Layout (IC select_linked 제거), RMB / Shift+RMB 마킹 메뉴.
  mapping: SelectUVMask / SelectMeshUVShell / polyTexturePlacementPanel Cut·Sew·Unfold·Layout = 구현 (구현 99 → 105).
- 메뉴: UV > Cut UV Edges / Sew UV Edges = 킷, Merge UVs = uv.weld, 3D Cut and Sew UV Tool · Auto Seams = 안내.
- **UV Toolkit** (`ui/uv_toolkit.py`): UV Editor 사이드바 「UV Toolkit」 탭, uv_01_win1 순서 (컴포넌트 아이콘 · "N object selected" · Pick/Drag/Tweak ·
  Symmetry/Constraint 회색 · All/Clear/Inverse · Pinning · Select By Type · Soft Selection · Transform (Texel Density, Flip, Rotate ±90) · Create ·
  Cut and Sew · Unfold · Align and Snap · Arrange and Layout · UV Sets), 회색 행 안내 = PANEL_NOTICES.

### 계획과 다르게 된 것 (delegated)

- 안 닫힌 자르기 (셸이 둘로 안 나뉨) 는 솔기만 — 다음 Unfold 가 엶 (Maya 는 그 자리에서 틈이 생김).
- UV / UV Shell 모드에서 3D 뷰의 면이 모두 선택돼 보임 (Blender 는 sync 를 끄면 선택된 면의 UV 만 그림).

## 남은 것

- 3D Cut and Sew UV Tool (뷰포트에서 에지 긋기, x / s / d) — PLAN 「남긴 것」, 다음 UV 단계.
- UV Editor 표시 키 4/5/6/7/8/9 · Ctrl+1, 체커 (툴바 버튼, Assign Checker Shader), Create UV Shell, Straighten, Distribute, Back-Facing 선택.
- Maya Layout 옵션 창 (타일 패딩, 회전 단계, 크기 모드) — 지금은 셸 패딩만.

## 검증

- Blender 측정 `tmp/probe64/p66b.py`: 두 쿼드 + 솔기 (UV 붙음) — unwrap 은 나눔, pack_islands · average_islands_scale 은 안 나눔 (sync 켬/끔 같음).
  Maya 설치본 `texturePanelMenus.mel` 에서 UV Editor RMB 방향 기록 (`research/maya/marking_menus.json`).
- 헤드리스 `python tests/run.py`: **538/539 → step 9 테스트가 「RMB E UV = 회색」 을 예로 쓰던 것을 Vertex Face 로 바꿔 539/539** (62 파일; 새
  `test_step66_uv.py` 10 개: 섬과 솔기, Cut = 그 자리 + pack 이 둘로 봄, Sew = 회전·이동된 셸이 붙음, Unfold = 셸 수·중심 유지, Layout = 0–1·겹침 없음,
  Texel Get 512 / 256 · Set 1 % 안, UV 컴포넌트 모드, 마킹 메뉴 resolve·방향, 키·메뉴·툴킷, 큐브 Cut→Unfold→Layout 밀도 같음).
  step 8 (메뉴 22 개, research 비교 통과) · 키맵 (그림자 검사) · 54 (안내 문구) 갱신.
- GUI `gui_step66_uv.py` 6/6: UV > UV Editor → 새 창 UV · 편집 모드 · sync, 윗면 엣지 → Shift+X → 솔기 4 · 셸 1 → 2, Ctrl+U 셸 유지, Ctrl+L 0–1 · 겹침 없음
  (삼각형 교차 검사), RMB NW → 섬 모드 · sync 끔, 사이드바 UV Toolkit 탭. 샷 `tmp/shots66/gui_step66_uv_editor.png`, `gui_step66_rmb.png` (Maya 방향의
  마킹 메뉴), `gui_step66_layout.png`, `gui_step66_toolkit.png` (uv_01_win1 순서).
- GUI 전체 `python tests/gui/run.py --ui-scale 0.8`: **452/452** (50 파일). `python tools/dogfood.py`: **47/47**, 콘솔 오류 0. 키맵 매핑 문서 재생성.
