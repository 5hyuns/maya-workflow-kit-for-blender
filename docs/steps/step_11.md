# Step 11 — M4-b Maya식 Outliner, Attribute Editor

PLAN 표 #12 (사용자 번호 11).

## 계획

근거: `research/maya/attribute_editor.md` (§1 창 구성 :7-40, §2 관련 노드 탭 :42-61, §3.1 editorTemplate :74-84,
§4 노드별 섹션 :96-145, §5 Blender 메모 :147-158), `research/maya/ae_templates.json` (transform/mesh/camera/
pointLight/directionalLight/lambert/standardSurface/polyCube 섹션·collapse 플래그), `research/maya/ui_layout.md`
:121 (CB·AE 같은 도크의 탭), :258-264 (Outliner 기본값 showShapes 0, showDagOnly 1, autoExpand 0),
`research/maya/concepts.md` §2 (transform/shape, :27 Outliner 는 shape 숨김), `research/blender/api_limits.md` #2-#3
(Properties 탭 추가 불가, Outliner 트리는 C → UIList 자체 트리, 드래그 재부모 불가).

### 1. 위치 (delegated)

- Maya 는 Channel Box/Layer Editor 와 Attribute Editor 가 **같은 도크의 탭**이고 Ctrl+A 가 둘을 오간다
  (ui_layout.md:121, hotkeys_default.json `ShowAttributeEditorOrChannelBox`). Blender 사이드바 탭(`active_panel_category`)은
  Python 에서 읽기 전용(Step 6 실측)이라 Ctrl+A 로 탭을 바꿀 수 없다. → 사이드바 "Channel Box" 카테고리 안에
  **도크 모드** (`WindowManager.maya_kit_dock`: CHANNEL_BOX / ATTRIBUTE_EDITOR) 를 두고 맨 위 헤더 없는 패널에
  `[Channel Box / Layer Editor] [Attribute Editor]` 탭 버튼. CB·LE 패널은 CHANNEL_BOX 일 때, AE 패널은
  ATTRIBUTE_EDITOR 일 때만 (`poll`).
- Maya Outliner: 3D 뷰 사이드바 카테고리 **"Outliner"** 의 UIList 패널. Blender 왼쪽 Outliner(템플릿, DAG 만
  보이게 설정됨)는 그대로 둔다 (드래그 재부모·다중 선택 등 C 기능은 거기에). Blender Outliner 영역에는 패널을
  넣을 수 없다 (`SpaceOutliner` 에 UI 영역 없음).

### 2. Outliner (`ui/outliner.py`)

- 행 데이터 `WindowManager.maya_kit_outliner_rows` (CollectionProperty): kind OBJECT/SHAPE, 객체 이름, depth, 자식 유무.
  그리기 중에는 ID 데이터를 못 쓰므로 `rebuild()` 를 `depsgraph_update_post` / `load_post` 핸들러와 펼치기·
  옵션 연산자에서 호출, 서명(객체·부모·데이터 이름·펼침·옵션)이 같으면 건너뜀.
- 순서: Maya DAG 순서 = 루트들(씬 순서) → 깊이 우선으로 자식(씬 순서). `autoExpand 0` → 기본 접힘; 펼침 상태는
  `Object.maya_kit_expanded` (파일에 저장). 화살표 클릭 = 펼치기/접기, Shift+클릭 = 하위 전부 (Maya).
- Shapes 토글 (`maya_kit_outliner_shapes`, 기본 끔 = showShapes 0): 켜면 객체 데이터가 그 객체의 첫 자식 행
  (`pCubeShape1`, 데이터 아이콘).
- 선택: 행 클릭 = UIList 활성 행 → 그 객체만 선택 (shape 행은 그 객체). 아이콘 버튼 클릭 + Ctrl = 토글, Shift = 범위
  (Maya Outliner) — UIList 행 클릭은 수정 키를 못 받는다. 선택된 객체 행은 강조(아이콘 눌림).
  숨긴 객체는 흐리게 (Maya 회색 글자).
- 이름 변경: 행 라벨은 get/set 속성(대상 객체/데이터 이름) → UIList 더블클릭 = 제자리 이름 변경.
- 재부모: UIList 는 드래그 앤 드롭이 없어 MMB 드래그는 불가 (api_limits.md #3). 대신 패널 헤더 **Parent / Unparent**
  버튼 (Step 10 `maya_kit.parent`/`unparent`, Maya P / Shift+P 와 같은 의미, 월드 유지) — delegated.
- 필터 문자열: 이름 포함 행만 평평하게 (UIList 기본 필터).

### 3. Attribute Editor (`ui/attribute_editor.py`, 데이터는 `ui/ae_layout.py`)

- **노드 탭** (attribute_editor.md:42-61, :147-152): transform = 객체, shape = 객체 데이터, 입력(history) =
  모디파이어마다 한 탭 (Maya polyCube1/polyExtrudeFace1 자리), 재질 = 재질 슬롯마다 한 탭 (lambert1 자리).
  탭 키 `T`, `S`, `M:<모디파이어 이름>`, `MAT:<슬롯 번호>`. 기본 탭 = 마지막으로 고른 **종류** 유지, 없으면 shape
  (Maya preferred node 가 shape/history [I]).
- 탭 헤더 (AEbuildTabHeader, :32-35): `노드 종류: [이름 필드]` (제자리 이름 변경) + 입력 탭이면 `◀ ▶` (in/out 화살표 =
  스택의 앞/뒤 모디파이어, attribute_editor.md:157-158).
- **섹션**: `ae_layout.py` 에 Maya 템플릿 섹션 이름·collapse → Blender 속성 목록 (데이터로). `layout.panel()`(4.1+)
  로 접는 섹션, `collapse=0` 은 열림, `1`/`true`/지정 없음은 닫힘 (Maya frameLayout 기본 접힘 [K]). 테스트가
  섹션 이름·collapse 를 ae_templates.json 과 대조하고, 모든 속성 경로가 Blender RNA 에 있는지 확인.
  - transform: Transform Attributes (Translate/Rotate/Scale/Rotate Order; shear·rotateAxis 는 없음 → 생략),
    Pivots (World Space = 원점 월드 위치 읽기 전용, Local Space = Step 10 피벗 오프셋 `delta_location`),
    Limit Information (Limit Location/Rotation/Scale 제약 — 있으면 값, 없으면 추가 버튼), Display (가시성, 로컬 축,
    Template = 선택 불가, Always Draw On Top = show_in_front, Bounding Box, Drawing Overrides = display_type/color),
    Extra Attributes (커스텀 속성).
  - mesh: Mesh Component Display (와이어, 모든 엣지, 뷰 노멀 오버레이), Mesh Controls (부드럽게/각지게 셰이딩),
    Smooth Mesh (Step 4 1/2/3 미리보기 = Subsurf), Render Stats (레이 가시성, 렌더 숨김), Extra Attributes.
  - camera: Camera Attributes (초점거리, near/far), Film Back (센서, 맞춤, 시프트), Depth of Field, Orthographic Views,
    Display Options. light: <Type> Light Attributes (종류, 색, 세기, diffuse/specular), Shadows (그림자, 반경/각도).
    그 밖의 데이터: 데이터 블록 일반 속성 + Extra Attributes.
  - 입력(모디파이어): "<종류> History" 섹션 (열림) 에 모디파이어 속성 일반 그리기 + Apply(이 노드만 Delete History)·
    Delete 버튼.
  - 재질: Principled BSDF 가 있으면 Maya standardSurface 섹션 Base/Specular/Transmission/Subsurface/Coat/Sheen/
    Emission/Thin Film/Geometry 를 소켓 이름에 매핑(연결된 소켓은 "connected" 표시), 없으면 뷰포트 색·금속·거칠기.
- 하단 (createAEWindowContents :4120-4140): **Select** (이 탭의 객체 선택) 버튼만. Notes/Presets/Copy Tab 없음.

### 4. 키

- Object Mode: **Ctrl+A** = `maya_kit.ae_toggle` (도크 모드 전환 + 사이드바 열기; 사이드바 표시는 연산자 안에서 바꾸면
  안 붙어서 타이머로 — Step 9 실측). IC Ctrl+A(전체 선택)·Ctrl+Shift+A(선택 해제)는 Maya 키로 옮김:
  **Ctrl+Shift+A** = 전체 선택 (`SelectAll`), **Alt+D** = 선택 해제 (`SelectNone`, IC 에서 비어 있음).

### 5. 테스트

- 헤드리스 `test_step11_outliner_ae.py`: 행 순서·깊이·접힘·Shift 펼치기·shape 행·라벨 이름 변경(객체/데이터)·
  선택(교체/토글/범위)·재빌드 건너뜀; AE 탭 목록·기본 탭·종류 유지·in/out 이동, 섹션 데이터 vs ae_templates.json,
  모든 속성 경로 존재, FakeLayout 로 각 탭 그리기 오류 없음, 모디파이어 Apply/Delete, 도크 모드 poll, 키 3개,
  `test_enable_disable` (핸들러·WM/Object 속성 누수).
- GUI `gui_step11_outliner_ae.py`: Ctrl+A 로 AE 전환, 탭 클릭, Outliner 더블클릭 이름 변경, 스크린샷
  (AE transform/shape/입력/재질, Outliner shapes 켬).

## 한 것

- `src/maya_kit/ui/outliner.py` — 사이드바 "Outliner" 탭: `MAYAKIT_UL_outliner` (DAG 순서, 들여쓰기, 펼침 화살표·Shift 하위 전체,
  타입 아이콘, 숨김 = 흐림), 헤더 **Shapes** 토글(데이터 행이 객체 첫 자식), 행 클릭 = 선택 교체, 아이콘 클릭 + Ctrl 토글 / Shift 범위,
  라벨 get/set → 더블클릭 이름 변경(객체·데이터), Parent / Unparent 버튼. 행은 `depsgraph_update_post`/`load_post`/연산자에서 재빌드
  (서명 같으면 건너뜀). 펼침 상태 `Object.maya_kit_expanded`.
- `src/maya_kit/ui/ae_layout.py` — Maya 템플릿 섹션 → Blender 속성 데이터 (transform, mesh, camera, point/directional/spot/area light,
  standardSurface(Principled BSDF 소켓), 노드 없는 재질).
- `src/maya_kit/ui/attribute_editor.py` — 도크 모드(`WindowManager.maya_kit_dock`) + 맨 위 탭 버튼, AE 패널: 노드 탭
  (transform / shape / 모디파이어마다 history / 재질 슬롯마다), 탭 헤더 `종류: [이름]`, history 탭 ◀ ▶ (in/out), 섹션 = `layout.panel`
  (Maya collapse 플래그), Extra Attributes (커스텀 속성), Limit Information (Limit 제약 값 또는 추가 버튼), Pivots (Step 10 피벗 오프셋 +
  월드 피벗), history 탭 Delete History(적용)/Delete, Select 버튼. CB·LE 패널은 도크 모드가 CHANNEL_BOX 일 때만.
- 키 (`maya_patches.patch_attribute_editor`, 17): Object Mode Ctrl+A = `maya_kit.ae_toggle`, Ctrl+Shift+A = 전체 선택, Alt+D = 선택 해제
  (IC Ctrl+A / Ctrl+Shift+A 교체). `mapping.py` ShowAttributeEditorOrChannelBox / SelectAll / SelectNone → KIT (구현 51).

### 계획과 다르게 된 것 / 실측으로 바뀐 것

- 선택: `view_layer.objects.get(name)` 로 "뷰 레이어에 있는지" 확인하면 마지막 뷰 레이어 동기화 뒤에 링크한 객체가 None 으로 나와
  선택이 조용히 건너뛰어졌다 (헤드리스 프로브로 확인). → `select_set` 의 RuntimeError 로 판단.
- Maya AE 의 float3 행처럼 Translate/Rotate/Scale 을 한 줄 세 칸으로 (첫 스크린샷에서 세로로 쌓여 바꿈).

## 검증

- 헤드리스 `python tests/run.py`: **175/175** (기존 160 + `test_step11_outliner_ae.py` 15). 섹션 이름·열림 상태 30개 이상을
  ae_templates.json 과 대조, 모든 속성 경로·소켓 이름이 Blender RNA 에 존재, FakeLayout 로 메시·카메라·스포트·선 라이트·재질 2종 모든 탭
  그리기, Outliner 순서·접힘·Shift 펼치기·shape 행·이름 변경·선택 3모드·재빌드 건너뜀, 모디파이어 적용/삭제, Limit 추가, 도크 poll, 키 3개,
  `test_enable_disable` (WM/Object 속성, 핸들러, 타이머 누수 없음).
- GUI `python tests/gui/run.py`: **107/107** (기존 100 + `gui_step11_outliner_ae.py` 7: Ctrl+A → AE + 사이드바 열림, 다시 Ctrl+A → CB,
  실제 depsgraph 핸들러로 만든 Outliner 행 순서).
- 스크린샷 확인 (`--shots`): `gui_step11_ae_shape.png` (mesh 탭, 섹션 접힘), `gui_step11_ae_transform.png` (Transform Attributes 열림,
  Translate/Rotate/Scale 한 줄), `gui_step11_ae_history.png` (subsurf History + ◀ ▶ + Delete History), `gui_step11_ae_material.png`
  (Base/Specular 열림, 나머지 접힘), `gui_step11_outliner.png` (group1 > Cube > Cube shape, 아이콘).
- `docs/manual_checks.md` Step 11 6항목.

## 결정 (delegated)

- AE 는 사이드바 "Channel Box" 탭 안의 도크 모드 (탭 이름은 그대로 "Channel Box"; 사이드바 탭은 Python 에서 못 바꿈). Outliner 는 별도
  사이드바 탭, 템플릿의 Blender Outliner 는 그대로.
- MMB 드래그 재부모 없음 → Parent/Unparent 버튼 (Maya P/Shift+P 의미). 행 클릭은 수정 키를 못 받아 Ctrl/Shift 는 아이콘 클릭으로.
- 기본 탭 = 마지막 고른 종류, 처음은 shape. 섹션 열림 = Maya `collapse` 0/false 만, 플래그 없음 = 닫힘. Maya 에 없는 속성(shear,
  rotateAxis, tessellation, depth map, Node Behavior, UUID)은 생략. 스포트·영역 라이트는 연구 자료에 템플릿이 없어 점 라이트 구조를 따름.
- Notes, Presets, Show/Hide, Copy Tab, Focus 는 구현 안 함. 모디파이어 일반 속성은 RNA 순서대로 전부.

## 남은 것

- Outliner: 드래그 재부모·순서 바꾸기, 컬렉션(세트) 표시, 검색 시 계층 유지, 키보드 탐색(Outliner 안 화살표), Maya Outliner 메뉴바(Display/Show).
- AE: 셰이딩 그룹(initialShadingGroup) 탭, 텍스처 노드 탭(입력 연결 따라가기), Notes, 노드 종류별 템플릿 확장(커브, 조인트 = 아마추어 본).
- Step 12 (셸프) 는 사이드바가 아니라 헤더/에셋 셸프 영역 검토.
