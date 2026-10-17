# Step 63 — Modeling Toolkit 도크 · 소프트 선택 Maya 단위 · Separate / Combine / Mirror / Boolean 의 Maya 의미

근거: `research/maya/workflows/modeling.md` §1 A2·C9·E18·E19, §2 (2, 9, 18, 19), 갭 표 (MTK 16, Separate 16, 소프트 선택 15,
Mirror 12, Combine 8), §4 결정 (MTK·Soft Select·Mirror·Combine), §5 후보 1·3; Maya 샷 `shots/modeling_03.png` (MTK 탭),
`modeling_13_win1.png` (Mirror Options), `modeling_14.png`; Status Line 편집기 토글 순서 `research/maya/ui_layout.md:212-216`.

## 계획

### 실측 (Maya 2022.4 mayapy, `MAYA_APP_DIR` = `tmp/maya63/app` = 팩토리, 스크립트 `tmp/maya63/probe*.py`)

- `softSelect -q`: Enabled 0, **Distance 5.0** (cm), Falloff 0 (Volume). (rigging 실행의 1.5 는 스크립트 값이었다.)
- 메뉴 **Combine** (`CombinePolygons` 런타임 명령) = `polyUnite -ch 1 -mergeUVSets 1 -centerPivot -name pCube1 pCube1 pSphere1` →
  **pCube2** (원래 pCube1·pSphere1 은 빈 transform 으로 남아 이름 1 이 차 있음), 피벗 = **바운딩 박스 중심** (1.75, 0, 0), translate 0.
  (modeling.md 의 「피벗 원점」 [K] 는 틀림.) 명령으로 직접 `polyUnite` 하면 `polySurface1`.
- 메뉴 **Separate** (`SeparatePolygon`) = `polySeparate pCube2Shape` → `polySurface1`, `polySurface2` 가 **pCube2 의 자식** (pCube2 는 그룹이 됨),
  둘 다 피벗 월드 원점.
- Blender: `mesh.separate` 는 편집 모드 전용, `object.join` 은 활성 오브젝트 이름·변환 유지, Mirror 모디파이어는 오브젝트 원점 기준.

### 1. Modeling Toolkit 도크 (delegated)

- `WindowManager.maya_kit_dock` 세 번째 항목 `MODELING_TOOLKIT` ("Channel Box" 사이드바 탭 공유, 맨 위 도크 전환 줄).
  `ui/modeling_toolkit.py` 패널, modeling_03 순서: 선택 모드 (Multi-Component · Object / Vertex / Edge / Face / UV 아이콘), "N face selected",
  Pick/Marquee · Drag · Tweak/Marquee (= 선택 툴 box / circle / tweak), Highlight Backfaces (회색), Highlight Nearest Component
  (= kit `preselect_highlight`), Camera Based Selection (= kit `select_through` 의 반대), Symmetry (`status_line.draw_symmetry`),
  Selection / Transform Constraint (회색 + 안내), 접히는 절 (`layout.panel`) ▸Soft Selection, ▾Mesh (Combine · Separate · Smooth · Boolean),
  ▾Components (Extrude · Bevel · Bridge · Add Divisions), ▾Tools (Multi-Cut · Target Weld (회색, step 64) · Connect · Quad Draw).
  버튼은 메뉴와 같은 동작 (`maya_kit.menu_item(item=Maya 메뉴 경로)`), Extrude 는 Maya 처럼 바로 압출 + Move 매니퓰레이터 (모달 없음).
- 진입: Status Line 편집기 토글 맨 앞 MTK 아이콘 (Maya 순서), Windows > Modeling Editors > Modeling Toolkit, Mesh Tools > Show/Hide Modeling Toolkit.

### 2. 소프트 선택 Maya 단위 (delegated)

- MTK Soft Selection: 켜기, **Falloff radius = `proportional_size / maya_unit()`** (Maya 단위로 보이고 입력), Falloff mode Volume / Surface
  (= `use_proportional_connected` 끔 / 켬; Global / Object 회색), Falloff curve, Reset (= 5 Maya 단위).
- B 탭/드래그로 켤 때 반경이 아직 Blender 기본 1.0 BU 면 Maya 기본 5 × `maya_unit()` 로 (사용자 동작 때만; 파일을 열 때 몰래 바꾸지 않음).
  드래그 머리글도 Maya 단위.

### 3. Combine / Separate / Mirror / Boolean (delegated)

- `maya_kit.combine`: 오브젝트 모드, 메시 2+ → join, 정점을 월드로 (변환 identity), Center Pivot (`freeze.center_pivot`, 채널 0) →
  이름 = 첫 선택 (활성이 아닌 것 중 이름순 첫째 — Blender 는 선택 순서가 없음) 의 base + 원래 이름들도 찬 것으로 친 다음 번호 (= Maya 의 pCube2).
  원래 transform 은 남기지 않음 (Maya 에서 Delete History 한 상태, modeling.md §4).
- `maya_kit.separate`: 오브젝트 모드에서 (편집 모드면 그대로 Blender separate LOOSE), 셸마다 오브젝트 → 원래 이름의 빈 그룹 (같은 변환) 아래
  `polySurfaceN` 들 (Maya 계층). 셸이 하나면 안내.
- `maya_kit.mirror` (bmesh, 메시에 적용 — Maya 에서 history 를 지운 결과): Cut Geometry, Mirror Axis Position World / Object / Bounding Box,
  Offset (Maya 단위), Mirror Axis X / Y / Z (Maya Y-up → Blender X / Z / −Y, step 57 규칙), Direction + / −, Combine with Original,
  Merge border vertices + Threshold (Automatic). 메뉴 클릭 = 지난 설정으로 실행, □ (누른 채) = `invoke_props_dialog` 옵션 창
  (`run_action` 이 `option_box` 속성이 있는 연산자에 넘김 — PLAN 「Not possible」 option boxes 의 대체). 셸프·마킹 메뉴도 이 연산자.
- `maya_kit.boolean(operation)`: Maya 순서 (첫 선택 = 바탕, 둘째 = 연산 대상 = Blender 활성) → Boolean 모디파이어 적용, 대상 삭제
  (Delete History 상태). Mesh > Booleans > Union / Difference / Intersection, MTK Boolean = Union.

### 4. 검증

- 헤드리스 `test_step63_modeling_toolkit.py`: 도크 항목·패널 poll·Status Line 토글, MTK 버튼 경로가 MAP 에 있음, Combine (pCube1+pSphere1 →
  pCube2, bbox 중심 피벗, 채널 0, 정점 월드 위치 그대로), Separate (그룹 + polySurface1/2, 정점 위치 그대로), Mirror (Cut + World X −, 병합,
  Y/Z 축 매핑, Combine 끔 = 새 오브젝트, Object 위치), Boolean, 소프트 선택 반경 Maya 단위 (cm 템플릿 값 0.05).
- GUI `gui_step63_mtk.py` (modeling_02·14): Status Line MTK 아이콘 → 도크 MTK → 면 선택 → Extrude 버튼 → 면 수 늘어남; 큐브 + 구 →
  Combine 버튼 → pCube2 하나 → Separate 버튼 → 둘. 스크린샷 (vs modeling_03).
- dogfood, manual_checks.

## 한 것

- **Modeling Toolkit** (`ui/modeling_toolkit.py`): dock 세 번째 항목 `MODELING_TOOLKIT` (`attribute_editor.DOCK_ITEMS`), modeling_03 순서 그대로 —
  Multi-Component + Object/Vertex/Edge/Face/UV(회색) 아이콘, "N faces selected" (편집 모드 통계, Maya 복수형), Pick/Marquee · Drag · Tweak/Marquee
  (= select box / circle / tweak 툴), Highlight Backfaces (회색), Highlight Nearest Component (= kit `preselect_highlight`), Camera Based Selection
  (= `select_through` 반대), Symmetry (`status_line.draw_symmetry`), Selection/Transform Constraint (회색), 접히는 절 (`layout.panel`) Soft Selection ·
  Mesh · Components · Tools. 버튼 = Maya 메뉴와 같은 동작 (`maya_kit.menu_item(item=경로)`); 회색 행의 안내는 `notices.PANEL_NOTICES`
  (Maya 메뉴 경로가 아닌 것 — step 54 테스트가 NOTICES 는 실제 메뉴 경로만 허용), Target Weld 는 메뉴 안내 (`NOTICES`).
- 진입: Status Line 편집기 토글 맨 앞 MTK 아이콘 (`status_line.EDITORS`, 다시 누르면 Channel Box), Windows > Modeling Editors > Modeling Toolkit,
  Mesh Tools > Show/Hide Modeling Toolkit.
- **MTK Extrude** = `maya_kit.mtk_extrude`: 바로 압출 (`mesh.extrude_context`) + Move 툴 (Maya 처럼 매니퓰레이터로 뺌, 사이드바에서 모달 없음).
- **소프트 선택 Maya 단위**: Maya 팩토리 반경 5 (mayapy 실측) — B 로 켤 때 반경이 Blender 기본 1.0 그대로면 5 × `maya_unit()` (`taphold.maya_soft_radius`),
  B 드래그 머리글 Maya 단위, MTK Falloff radius = `Scene.maya_kit_soft_radius` (`proportional_size / maya_unit()`), Volume / Surface
  (`use_proportional_connected`), Global 회색, Falloff curve, Reset.
- **Combine** `maya_kit.combine`: join → 정점 월드로·변환 identity·부모 없음 → `freeze.center_pivot` (채널 0, 피벗 = bbox 중심) → 이름 = 첫 선택 base +
  원래 이름도 찬 것으로 친 번호 (pCube1 + pSphere1 → **pCube2**, Maya 와 같음). 첫 선택 = 활성이 아닌 것 중 이름순 첫째 (delegated: Blender 는 선택 순서 없음).
- **Separate** `maya_kit.separate`: 오브젝트 모드 = 편집 진입 → LOOSE → 원래 이름의 빈 그룹 (같은 변환) 아래 `polySurfaceN`, 조각 Translate 0, 피벗 = 그룹의
  원점 (Maya: 월드 원점) — separate 가 원래 피벗 delta 를 조각마다 복사하므로 지우고 `freeze.shift_pivot` 로 되돌림. 편집 모드 = Blender separate.
- **Mirror** `maya_kit.mirror` (bmesh, 메시에 적용): Cut (bisect, 받는 쪽 지움) · World/Object/Bounding Box · Offset · X/Y/Z (Maya → Blender X / Z / −Y) ·
  + / − · Combine (끄면 새 오브젝트) · Merge border + Automatic/Custom threshold. 메뉴 클릭 = 지난 설정, □ = `invoke_props_dialog` Mirror Options —
  `marking/modal.run_action(option=True)` 이 `option_box` 속성이 있는 연산자에 넘김 (다른 연산자는 그대로 Adjust Last Operation).
- **Boolean** `maya_kit.boolean`: 첫 선택 − 둘째 (= 활성), Boolean 모디파이어 EXACT 적용, 대상 삭제. Mesh > Booleans 세 개, MTK Boolean = Union.
- 메뉴·셸프 (CombinePolygons, MirrorPolygonGeometry)·마킹 메뉴 (Mirror, Separate, Combine) 를 새 연산자로.

### 계획과 다르게 된 것 (delegated)

- 실측이 modeling.md 를 고침: Combine 피벗은 원점이 아니라 **bbox 중심** (`polyUnite -centerPivot`), Separate 조각은 그룹 아래.
- Separate 조각의 피벗: Maya 는 월드 원점, 킷은 그룹의 원점 (Combine 결과의 그룹은 원점이 월드 원점이라 같음; 회전된 원본은 그 로컬 원점).
- 도크 전환 줄의 세 이름이 사이드바 폭에서 잘림 ("Channel Bo..."): 툴팁에 전체 이름. Maya 는 세로 탭.

## 검증

- mayapy (Maya 2022.4, 팩토리 `MAYA_APP_DIR` = `tmp/maya63/app`): softSelect Distance 5.0 / Falloff 0, CombinePolygons → pCube2 (bbox 중심 1.75),
  SeparatePolygon → pCube2 아래 polySurface1/2 (피벗 원점). Maya 는 끝나고 종료됨 (standalone).
- 헤드리스 `python tests/run.py`: **505/505** (59 파일; 새 `test_step63_modeling_toolkit.py` 10 개: 도크·Status Line 순서·메뉴, MTK 버튼 = MAP 경로,
  Combine 이름·피벗 1.75·채널 0·정점 그대로, Separate 그룹·조각 이름·Translate 0·정점 그대로·셸 하나 = 취소, Mirror 기본 (−0.75…0.75, 정점 12),
  Y 축·Combine 끔·Object 위치·Z 축, 옵션 박스 경로, Boolean Difference, 소프트 선택 Maya 단위 (m / cm), 메뉴·셸프·마킹 메뉴, MTK Extrude 면 10).
- GUI `python tests/gui/run.py --ui-scale 0.8`: 426/427 → 실패 1 은 step 3 의 B 드래그 (시작 반경 1.0 = Blender 기본이라 이제 Maya 5 로 바뀜) —
  테스트를 사용자 반경 2 → 4 로 고쳐 17/17 (0.8, 기본 배율). 새 `gui_step63_mtk.py` 8/8 (기본·0.8): Status Line MTK 아이콘 → 도크 MTK, Face 아이콘,
  Extrude 버튼 → 면 10 + Move 툴, Object 아이콘, Combine → pCube2, Separate → 그룹 + 둘, Mesh > Mirror □ → Mirror Options 창 (샷).
  샷 `tmp/shots63/gui_step63_explore*.png`, `gui_step63_mtk_object.png`, `gui_step63_mirror_options.png`.
- `python tools/dogfood.py`: **47/47**, 콘솔 오류 0.

## 남은 것

- Maya 의 소프트 선택 색 그라데이션 (Blender 는 원) — 안내만. Global / Object falloff 없음.
- Combine 의 첫 선택은 추정 (선택 순서를 기록하지 않음); Boolean 결과 이름은 바탕 이름 그대로 (Maya 이름 미측정).
- Mirror 의 Border 「Bridge border edges」/「Don't merge」 구분·Smoothing Angle·UV Flip 없음.
- Highlight Backfaces, Selection / Transform Constraint, UV 컴포넌트 (step 66), Target Weld (step 64), MTK 의 Object / Help 메뉴 줄.
