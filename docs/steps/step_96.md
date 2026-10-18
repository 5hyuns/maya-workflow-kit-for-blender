# Step 96 — Outliner Sets

재점검 6차 backlog 7 (docs/PLAN.md 「재점검 6차」 7: 대응표 UI 의 마지막 Partial = Maya Outliner, 이유 = Sets 없음, step_82.md 「남은 것」).

## 근거

- Maya 메뉴: Create > Sets = Set (❑) / Partition / Quick Select Set... (research/maya/menus.json, `startup/ModCreateMenu.mel:1002-1035`),
  Select > Quick Select Sets ▸ (`startup/buildSelectMenu.mel:321-327`, 항목 = text 가 `gCharacterSet` 인 세트마다 `select -r <set>`,
  없으면 회색 한 줄).
- Maya 동작 실측 (mayapy 2022, 팩토리 `MAYA_APP_DIR` = `tmp/maya63/app`, 스크립트 `tmp/maya96/probe.py`, 결과 `research/maya/re/sets.md`):
  - `CreateSet` = `performCreateSet false` → `sets -name "set1"` (이름 기본 `set1`, 있으면 set2, set3 … 비어 있는 가장 작은 번호), 선택은 그대로
    (pCube1 pCube2), 아무것도 선택 안 했으면 빈 세트.
  - `select set2` → 멤버 (pCube1) 선택, `select -noExpand set2` → 세트 노드 자체.
  - Quick Select Set... = `defineCharacter`: 이름 묻는 창 (기본 텍스트 "Set", OK / Cancel / Add to Shelf) → `sets -text "gCharacterSet" -name <이름>`.
  - `sets -add` / `-remove` 로 멤버 추가·제거, 멤버 오브젝트를 지우면 세트에서 빠짐.
  - Outliner: 세트는 DAG 오브젝트 뒤 (계층 밖) 에 `defaultLightSet`, `defaultObjectSet` 과 함께 보이고 펼치면 멤버 (research/maya/workflows/scene.md:36,
    screens scene_04.png). 세트 RMB 메뉴 (`others/OutlinerEdMenu.mel:1288-1330` `buildOutlinerEdSetMenu`): `selectPref -autoSelectOutlinerSetMembers`
    가 꺼져 있으면 (팩토리 = False, 실측) **Select Set Members** (`select -r <set>`), 켜져 있으면 Select Set (`select -r -noExpand`); 그 아래 Show Set Members ☐.
    멤버 행 RMB (`buildOutlinerEdSetMemberMenu`, :1249): Select Set Members, Remove From Current Set.
- 이전 설계: research/maya/workflows/scene.md:102 (세트 = 씬에 연결 안 한 컬렉션 + ID 속성 `maya_kit_set`, 다중 소속 OK), :117 (후보 3).
- Blender: MayaKit 레이아웃의 Outliner 는 Blender 의 C Outliner (`ui/maya_outliner.py`, View Layer 모드, 컬렉션 행 끔) — Python 으로 행을 끼울 수
  없음 (research/blender/api_limits.md #3). 트리 펼침 상태 (TreeStoreElem) 도 RNA 에 없음. 사이드바 kit Outliner (UIList, `ui/outliner.py`) 는 "Channel Box
  Dock Only" 를 끄면 보임.

## 계획 (delegated)

1. **데이터** (`operators/sets.py`, bpy 의존 최소): 세트 = `bpy.data.collections` 의 컬렉션, 씬에 연결하지 않음, `use_fake_user` (저장됨), ID 속성
   `maya_kit_set` = 생성 순번 (Outliner 순서 = Maya 처럼 만든 순서), Quick Select Set 은 `maya_kit_set_text` = "gCharacterSet" (Maya `-text`).
   멤버 = `collection.objects` (오브젝트는 원래 컬렉션에도 그대로 — 장면 구조 영향 없음, 디스플레이 레이어 컬렉션 (`ui/layer_editor.py`) 과 섞이지 않음).
   이름 = `set<N>` 비어 있는 가장 작은 N (Maya 실측). 함수: `all_sets()`, `create(name, objects, text)`, `members(coll, scene)`, `select_members(context, coll, mode)`,
   `add` / `remove` / `delete` / `quick_sets()`.
2. **연산자**: `maya_kit.create_set` (Create > Sets > Set; `option_box` 속성 → ❑ = 이름 대화상자, 선택 그대로, 리포트 "Result: set1"),
   `maya_kit.create_quick_select_set` (항상 이름 대화상자, 기본 "Set"; Add to Shelf 버튼은 안 함), `maya_kit.select_set_members(name, mode)`,
   `maya_kit.set_edit(name, action = ADD / REMOVE / DELETE / RENAME / TOGGLE_EXPAND)`. 메뉴 `MAYAKIT_MT_quick_select_sets` (Select > Quick Select Sets,
   없으면 회색 "No Quick Select Sets"). `menu_map.py`: Create/Sets/Set, Create/Sets/Quick Select Set..., Select/Quick Select Sets 매핑, notices 의 두 항목 제거.
   Partition 은 회색 + 안내 (Blender 에 배타 세트 없음).
3. **레이아웃 Outliner (C 목록) 의 세트 행** = Outliner WINDOW 의 POST_PIXEL 그리기 (`ui/outliner_sets.py`, `maya_outliner.is_maya_outliner` 인 것만):
   - Blender 목록이 끝나는 줄을 찾는다: 행 높이 = `UI_UNIT_Y` (20 px × `system.ui_scale`), 줄 i 의 가운데 한 픽셀 줄을 framebuffer 에서 읽어
     (range_bar 의 `read_color` 와 같은 방식) 색이 고르면 빈 줄 — 행은 위에서부터 빈틈없이 이어지므로 이진 탐색 (줄 수 log₂ 번 읽기).
   - 그 다음 줄부터 세트 행: 펼침 삼각형 (멤버가 있으면), kit 가 그린 세트 아이콘 (Maya 아이콘 복사 안 함: 겹친 두 원), 이름 (테마 텍스트 색).
     펼친 세트는 멤버 행 (들여쓰기, 이름) — Maya Show Set Members. 목록이 영역 밑까지 차서 자리가 없으면 영역 아래쪽에 불투명 배경으로 고정
     (Blender 가 자기 목록 끝 너머로 스크롤하지 않으므로).
   - 그린 행 사각형을 영역별로 기억 → "Outliner" 키맵 맨 앞 항목 (`PASS_THROUGH_FIRST`): LMB CLICK (아무 수식키) = `maya_kit.outliner_set_click`
     (세트 행: 삼각형 = 펼침, 행 = 멤버 선택 — Ctrl 토글 / Shift 추가; 멤버 행 = 그 오브젝트 선택), RMB PRESS = `maya_kit.outliner_set_menu`
     (`MAYAKIT_MT_outliner_set`: Select Set Members, Show Set Members ☐, Add Selected Objects, Remove Selected Objects, Rename..., Delete Set; 멤버 행 =
     Select Set Members, Remove From Current Set). 세트 행 밖이면 PASS_THROUGH → Blender 항목.
   - **클릭 = 멤버 선택** (delegated): Maya 팩토리는 세트 노드를 선택하지만 Blender 에는 선택할 세트 노드가 없음 → Maya 의
     "Auto select set members" 켠 동작으로. RMB 첫 항목은 팩토리처럼 Select Set Members.
   - defaultLightSet / defaultObjectSet 행은 그리지 않음 (delegated: Blender 대상 없음, `maya_outliner.py` 독스트링과 같은 판단).
4. **사이드바 kit Outliner** (`ui/outliner.py`): `kind` 에 SET 추가, DAG 행 뒤에 세트 행 (클릭 = 멤버 선택). 멤버 행은 안 함.
5. 다음 단계 고려: 97 (manual checks → GUI) 는 이 단계와 무관 — 세트 행 조작은 GUI 테스트로 바로 덮는다 (DOUBLE_CLICK 이름 바꾸기는 안 함 = 시뮬레이션 불가).

## 검증 계획

- 헤드리스 `tests/test_step96_sets.py`: create (이름 set1/set2, 빈 세트, 선택 유지, 씬에 연결 안 됨, fake user), members / select_members (REPLACE·
  TOGGLE·ADD, 뷰 레이어 밖 멤버 무시, 활성 = 마지막 멤버), add / remove / delete / rename, Quick Select Set + 메뉴 항목, 오브젝트 삭제 → 멤버에서 빠짐,
  저장 / 다시 열기 후 세트·멤버·순서 유지, 사이드바 Outliner SET 행, menu_map 항목, enable/disable 깨끗함.
- GUI `tests/gui/gui_step96_sets.py`: MayaKit 템플릿, 큐브 셋 → 둘 선택 → Create > Sets > Set (menu_item) → Outliner 에 `set1` 행이 DAG 뒤 → 선택 해제 →
  세트 행 클릭 = 두 큐브 선택, Ctrl 클릭 = 토글, 삼각형 = 멤버 행, 멤버 행 클릭, RMB 메뉴 → Remove Selected Objects. 스크린샷을 직접 확인.
- 대응표 (`research/README.md` UI 의 Maya식 Outliner 행, `docs/PLAN.md` 재점검 6차 표 주석) → Done. 전체 헤드리스 / GUI.

## 한 것

- `operators/sets.py`: 세트 데이터 (`all_sets` / `create` / `members` / `select_members` / `add` / `remove` / `delete` / `quick_sets`, 이름 `set<N>`),
  연산자 `maya_kit.create_set` (❑ = Create Set Options 이름 창, 리포트 "Result: set1"), `maya_kit.create_quick_select_set` (이름 창, 기본 "Set"),
  `maya_kit.select_set_members`, `maya_kit.set_edit` (ADD / REMOVE / REMOVE_MEMBER / DELETE / RENAME / EXPAND), 메뉴 `MAYAKIT_MT_quick_select_sets`.
  `Collection.maya_kit_expanded` (Show Set Members).
- `ui/outliner_sets.py`: 레이아웃 Outliner (Blender C 목록) 밑의 세트 / 멤버 행 그리기 (framebuffer 한 줄 읽기 + 이진 탐색으로 마지막 행 찾기, 자리가
  없으면 아래쪽 고정), 클릭 (`maya_kit.outliner_set_click`: 행 = 멤버 선택, Ctrl 토글, Shift 추가, 삼각형 = 펼침, 멤버 행 = 그 오브젝트),
  RMB (`maya_kit.outliner_set_menu` → `MAYAKIT_MT_outliner_set`: Select Set Members, Show Set Members ☑, Add / Remove Selected Objects, Rename..., Delete Set;
  멤버 행 = Select Set Members, Remove From Current Set). 행 높이 측정: 배율 1.25 에서 25 px (= round(18 × 1.25) + 2), 행 k 의 view y = −k·U.
- `keymap/maya_patches.py` 45: "Outliner" LMB CLICK (any) / RMB PRESS 맨 앞 (`PASS_THROUGH_FIRST`, 같은 키맵 shadow 선언).
- 사이드바 kit Outliner (`ui/outliner.py`): DAG 행 뒤 SET 행 (클릭 = 멤버, 이름 바꾸기).
- `ui/menu_map.py`: Create/Sets/Set, Create/Sets/Quick Select Set..., Select/Quick Select Sets 매핑; `ui/notices.py`: 두 「Not in Blender」 안내 삭제,
  Partition 안내 추가.
- Maya 동작 명세 `research/maya/re/sets.md` (mayapy 측정 + 메뉴 스크립트 위치), 대응표 행 (research/README.md) Done, `docs/PLAN.md` 재점검 6차 7 → done
  (UI 9/0/0/0, 합계 30/1/0/2 = 91 %).
- delegated: 클릭 = 멤버 선택 (Maya 팩토리는 세트 노드 선택; Blender 에 세트 노드 없음 → "Auto select set members" 켠 동작), defaultLightSet /
  defaultObjectSet 행 없음, Partition 없음 (안내), Quick Select Set 창의 Add to Shelf 없음, 세트 아이콘 = kit 가 그린 겹친 두 원, Edit > Select Set Members
  는 Maya 2022 메뉴에 없음 (menus.json) → Outliner RMB 와 Select > Quick Select Sets 가 그 자리.

## 검증

- 헤드리스 `tests/test_step96_sets.py` 9/9 (만들기·이름·선택 유지·빈 세트, 선택 REPLACE/ADD/TOGGLE·뷰 레이어 밖 멤버, 추가·제거·이름·삭제·멤버 삭제,
  Quick Select Set + 메뉴, 매핑·안내, 저장 / 다시 열기, 사이드바 SET 행, 오버레이 이진 탐색·행 목록, 키맵 맨 앞).
- GUI `tests/gui/gui_step96_sets.py` 10/10: 메뉴 항목으로 set1 → Outliner 셋째 DAG 행 바로 밑 (y 546–571, 행 3 top 571) → 클릭 = pCube1 pCube2, Ctrl 클릭 토글,
  삼각형 = 멤버 행 2, 멤버 행 클릭 = pCube1, RMB = 세트 메뉴, Blender 행 클릭은 그대로 (pCube3). 스크린샷 `gui_step96_outliner_set.png`,
  `_members.png`, `gui_step96_set_menu.png` 직접 확인 (행 높이·글자 위치가 Blender 행과 맞음, 멤버 들여쓰기, 메뉴 항목).
- 전체: 헤드리스 **713/713** (86 파일; 첫 실행 1 실패 = `test_keymap_maya` shadow 검사 → 같은 키맵 shadow 선언 후 통과), GUI **718/718** (77 파일), dogfood **47/47** (콘솔 오류 0).

## 남은 것

- 세트 행 더블클릭 이름 바꾸기 (event_simulate 가 DOUBLE_CLICK 을 못 보냄 — RMB > Rename... 으로 대신), MMB 로 오브젝트를 세트 행에 끌어 넣기 (step 82 의
  `outliner_drag` 에 세트 행 드롭 추가 후보), 컴포넌트 세트 (vertex group), Partition, 세트 안의 세트.
- 목록이 영역보다 길면 세트 행이 아래쪽에 고정됨 (Blender 가 자기 목록 끝 너머로 스크롤하지 않음) — manual check.
- UI 배율 0.8 / 1.5 와 5.x 에서 행 높이 공식 확인 안 함 (manual check; 기본 배율 1.25 만 측정).
- 다음: step 97 manual checks 정리 2 (step_88.md 「분류」 의 시뮬레이션 가능 58 항목).
