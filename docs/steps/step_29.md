# Step 29 — Maya 식 재질 지정

## 계획 (delegated)

### 근거

- Lighting/Shading 메뉴 (`mainShadingMenu`, research/maya/menus.md:1652-1657): Material Attributes, Assign New Material...,
  Assign Favorite Material ▸, Assign Existing Material ▸. 지금 넷 다 `ui/menu_map.py` 에 없어 회색.
- RMB 오브젝트 메뉴 목록 아래 재질 항목 (research/maya/hotkeys_and_menus.md:252): Maya 2022 `dagMenuProc` 는 목록 끝에
  구분선 → Material Attributes... → 구분선 → `buildShaderMenus` (Assign New Material... / Assign Favorite Material ▸ /
  Assign Existing Material ▸) 를 넣는다 (Maya 2022 설치본 `scripts/others/dagMenuProc.mel:2755-2764`,
  `scripts/startup/buildShaderMenus.mel:364-418`; 동작만 참고, 복사 없음).
  선택이 있으면 선택에, 없으면 메뉴를 연 오브젝트(커서 아래)에 지정 (`buildShaderMenus.mel:372-374`).
- Assign New Material = 재질 종류 목록 창 (검색 가능한 tree lister), Favorite = 즐겨찾기 종류 하위 메뉴 (새로 만들어 지정),
  Existing = 씬 재질 이름 하위 메뉴 (`hyperShade -assign`). 새 재질을 만들면 AE 가 그 재질을 보여 줌 (`AEpopupWhenCreatingShaders`).
- 단축키 Shift+T = AssignNewMaterial (research/maya/hotkeys_and_menus.md:135, hotkeySetup.mel:705). IC 의 Shift+T 는 Dope Sheet 뿐
  (Object Mode / Mesh 에 없음) → 충돌 없음.
- Maya 개념: 재질 지정 = 셰이딩 그룹 세트 멤버십, 면 단위 가능 (research/maya/concepts.md:113-115). Blender = 재질 슬롯 +
  polygon `material_index`.

### 설계

1. `operators/material.py` (새): 셸프의 `MATERIALS`·재질 생성 코드를 옮기고 지정 로직을 한 곳에.
   - 대상: 편집 모드 = `objects_in_mode`; 오브젝트 모드 = 선택된 MESH/CURVE/SURFACE/FONT/META, 선택이 없고 RMB 메뉴에서 왔으면
     (`rmb=True`) 메뉴를 연 오브젝트 (`WindowManager.maya_kit_mm_target`).
   - **면 지정**: 메시 편집 모드 + 면 선택 모드 + 선택된 면이 있으면 그 면에만: 같은 재질 슬롯을 찾거나 추가하고 선택 면의
     `material_index` 를 바꿈 (bmesh). 슬롯이 하나도 없으면 빈 슬롯(기본 회색 = Maya lambert1/initialShadingGroup)을 먼저 둬서
     나머지 면이 새 재질을 받지 않게 한다. 정점/엣지 모드나 선택 면이 없으면 오브젝트 전체 (delegated).
   - **오브젝트 지정** = Maya 처럼 셰이프 전체가 그 재질: 슬롯을 그 재질 하나로 바꾸고 모든 면/스플라인 `material_index` = 0.
     (지금 셸프는 활성 슬롯만 바꿔서 다른 슬롯 면은 옛 재질로 남았다.)
   - 새 재질을 만들면 AE 탭을 그 재질로 (`attribute_editor.set_tab`), 독 전환은 하지 않음 (Channel Box 유지, delegated).
2. 오퍼레이터 / 메뉴:
   - `maya_kit.shelf_material(kind, rmb)` (그대로, 새 지정 로직 사용) = Favorite 항목.
   - `maya_kit.assign_new_material(kind, rmb)`: invoke = 검색 팝업 (Maya 의 종류 목록 창), exec = 만들고 지정. Shift+T.
   - `maya_kit.assign_material(material, rmb)`: 기존 재질 지정.
   - `maya_kit.material_attributes(rmb)`: 독을 AE 로, 탭을 활성 재질로, 사이드바 표시.
   - `MAYAKIT_MT_assign_favorite_material` (Lambert / Blinn / Phong / standardSurface), `MAYAKIT_MT_assign_existing_material`
     (씬 재질, 그리스 펜슬 재질 제외), RMB 용 `_rmb` 변형.
3. `menu_map`: 네 항목. Material Attributes 는 `v3d` (가장 큰 3D 뷰의 사이드바).
4. `marking/menus.py` RMB_MESH / RMB_CURVE 목록 끝에 Maya 순서대로 재질 항목. Favorite = 목록 `Sub`, Existing = `("menu", id)`
   (동적 목록) — 엔진이 `menu` 항목에도 ▸ 표시.
5. 키맵: Object Mode / Mesh Shift+T → `maya_kit.assign_new_material`, 대응표 AssignNewMaterial = KIT.

### 검증

- 헤드리스: menu_map 4 항목 (회색 아님, 연산자/메뉴 존재), 오브젝트 지정 (슬롯 1개, 다른 슬롯 면 정리), 면 지정
  (`material_index`, 나머지 면 빈 슬롯), 정점 모드 = 오브젝트 전체, 기존 재질 지정, RMB 대상 (선택 없음 → 커서 오브젝트),
  Favorite/Existing 메뉴 항목, RMB 목록 항목, Shift+T 키맵, enable/disable.
- GUI 스크린샷: Lighting/Shading 메뉴 + Assign Existing 하위 메뉴, RMB 마킹 메뉴의 재질 항목, AE 재질 탭.

## 한 것

- `operators/material.py` (새): 셸프에서 옮긴 `MATERIALS` + `new_material()`, `targets()` (편집 오브젝트 / 선택 / RMB 메뉴를 연
  오브젝트), `assign()` (면 선택 모드 + 선택 면 = 면에만, 아니면 오브젝트 전체), `assign_object()` (슬롯 1개, 모든 면/스플라인
  인덱스 0), `assign_faces()` (슬롯 찾기/추가, 슬롯이 없으면 빈 슬롯 먼저). 새 재질을 만들면 AE 탭을 그 재질로.
  - `maya_kit.shelf_material(kind, rmb)` (id 그대로, `ui/shelf.py` 에서 이리로; 셸프 버튼도 이제 면 지정·전체 지정이 Maya 식),
    `maya_kit.assign_new_material` (검색 팝업 = Maya 종류 목록 창, Shift+T), `maya_kit.assign_material(material)`,
    `maya_kit.material_attributes` (독 → AE, 탭 → 활성 재질, 사이드바 표시).
  - 메뉴 `MAYAKIT_MT_assign_favorite_material` (Lambert / Blinn / Phong / Standard Surface), `MAYAKIT_MT_assign_existing_material`
    (+ `_rmb`; 그리스 펜슬 재질 제외, 이름순).
- `ui/menu_map.py`: Lighting/Shading 4 항목 (Material Attributes 는 `v3d`).
- `marking/menus.py`: RMB_MESH / RMB_CURVE 목록 끝에 구분선 · Material Attributes... · 구분선 · Assign New / Favorite ▸ / Existing ▸.
- 마킹 메뉴 엔진 (GUI 에서 찾은 것 2):
  - `("menu", id)` 항목에도 ▸ 표시 (`engine.Layout._text`).
  - 목록 하위 메뉴가 영역 밖으로 나가면 안으로 밀어 넣음 (`Session(bounds=...)`, `view.visible_bounds`): 화면 중앙 큐브에서도
    Favorite 의 Standard Surface 가 타임라인 아래로 잘렸다.
  - 클릭 모드에서 고른 항목은 그 버튼을 **뗄 때** 실행 (`modal._pending`): 누를 때 실행하면 항목이 연 팝업(Assign Existing Material)이
    같은 클릭의 RELEASE 를 받아 첫 행을 바로 골랐다 (GUI 실측).
- 키맵 patch 25 (`patch_materials`): Object Mode / Mesh Shift+T → `maya_kit.assign_new_material`. 대응표 AssignNewMaterial = 구현.
- 테스트: `tests/test_step29_materials.py` (11), `tests/gui/gui_step29_materials.py` (12 체크, 스크린샷 7장).

## 검증

- 헤드리스 `python tests/run.py`: **274/274** (28 파일, step 29 11개 포함).
- GUI `python tests/gui/run.py`: **218/218** (22 파일). step 29: RMB 목록 재질 항목, Favorite ▸ 호버 → Blinn 클릭 = 커서 아래 큐브에
  blinn1 (선택 없음), Existing ▸ 클릭 → 팝업이 열린 채 남음 (릴리스가 첫 행을 고르지 않음), Material Attributes → AE 재질 탭 +
  사이드바, Shift+T → "phong" 입력 → Enter = phong1. 스크린샷 (`tmp/shots29/`) 직접 확인: RMB 목록, Favorite 하위 메뉴(영역 안),
  Existing 팝업, Lighting/Shading 메뉴 (4 항목 활성, 나머지 회색), AE 재질 탭, Shift+T 검색 팝업.
- dogfood `python tools/dogfood.py`: **47/47**, 콘솔 오류 0.
- 키맵 대응표: 구현 88 (87 → 88), IC 8, 계획 5, 미검토 289.

## 남은 것

- Maya 의 Assign Existing 은 셰이더 분류별 구분선, Favorite 끝의 "Open Attribute Editor" 체크 상자 (`AEpopupWhenCreatingShaders`) 는
  없음: 새 재질은 AE 탭만 바꾸고 독은 Channel Box 그대로 (delegated).
- Remove Material Override (Legacy Render Layer 전용), Transfer Maps / Light Linking 항목은 회색 그대로.
- Ctrl+5 / Ctrl+Shift+5 (기본 재질 사용 토글, hotkeys_and_menus.md:115) 는 미검토 행으로 남김.
- 루트 RMB 목록 자체는 마우스 위치에 고정 (방사 메뉴 중심): 뷰 아래쪽에서 열면 목록 끝이 잘릴 수 있음 → manual_checks 에 추가.
- 커브 편집 모드에서는 스플라인 단위 지정 없이 오브젝트 전체.
