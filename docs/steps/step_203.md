# Step 203 — Graph Editor depth 3 (backlog #2, Issue #110)

## 계획

근거: `docs/steps/step_201_remaining.md` §8 #1, `research/maya/screens/editors104/_editors104.json`, `step_198.md` 「남은 것」.
지금 Graph Editor 167 / 229, Dope Sheet 139 / 181 → 목표 ≥ 180 / ≥ 150.

먼저 (사용자 결정 10-25 의 첫 작업): 공용 Blender 슬롯 잠금 `tools/blender_slots.py` — 커밋 a162a62 「QA: blender slots」.

대상 (두 편집기 공통이 대부분): List > Load / Add Selected Objects, Graph Editor Curves > Pin / Unpin Channel, List > Show Upstream
Curves (GE), Hierarchy Below (DS), Show > Attributes 필터 (Hidden, Driven by Anim Curve / Expression / Driven Key, User Defined;
Published = 컨테이너 없음 → 회색 유지 검토), Show > Objects > IkHandles / Sets (+ DS Characters), Edit > Select Curve Nodes, Curves >
Change Rotation Interp 5, Key Sync Filter, Peak Removal Filter.

레인 (delegated; 레인 ≤ 4, Blender ≤ 2 = `blender_slots`, Maya ≤ 1). 측정과 구현에 의존이 있어 두 차례:
- 1 차: **M** (에이전트, Maya 만) GUI Maya 로 List / Pin / Show 동작, mayapy 로 Rotation Interp · Key Sync · Peak Removal 결과 →
  `research/maya/re/graph_editor_201.md` + 데이터. **B** (에이전트, Blender 헤드리스) kit outliner 쪽 (`ui/editor_chrome.py`,
  `ui/editor_menu_map.py`, `ui/notices.py`) 을 Maya 문서 [K] 로 먼저 구현, 가정 목록을 남김.
- 2 차: **C** (에이전트) M 의 데이터로 커브 명령 (`operators/graph_curves_203.py`); 메인 = B 의 가정을 M 명세와 맞춤, GUI 확인.

진행 메모: 1 차 (M + B) → WIP 729fa4e; 2 차 = **C** (커브 명령) + **D** (B 의 [K] 가정을 M 측정에 맞춤) 동시. 순서 이유: 구현이 측정
데이터에 기댐.

## 한 일

- **측정** (레인 M, GUI Maya 3 번 + mayapy 4 번, 한 번에 Maya 하나): `research/maya/re/graph_editor_201.md` / `.json`, 테스트 사본
  `tests/maya203_graph_data.py`, 스크립트 `research/scripts/graph_editor_201/`, 샷 `research/maya/screens/graph_editor_201/`.
- **List** (`ui/editor_chrome.py`, `allset.graph_list`): Auto Load (공장값 켬, `WindowManager.allset_auto_load`) 켜진 동안 Load / Add 는
  회색 (Maya; 메뉴 줄은 `editor_menu_map.GREY_ON_POLL` → `menu_sets.draw_item` 이 Blender poll 로 그림), Auto Load 끄면 지금 목록이
  고정, Load = 선택으로 바꿈 (없으면 빈 목록), Add = 덧붙임 (Maya 의 "Load 직후 첫 Add 가 load 한 것을 버림" 은 안 따라함, delegated).
  목록은 편집기마다 kit collection (`.AllsetList`, ID prop `allset_list`) 을 Blender Collection 필터로 씀.
- **Pin / Unpin** (Graph Editor, `allset.graph_pin`): 하이라이트한 행 (node 행 = 모든 채널), 없으면 아무것도 안 함 + 경고; 핀 채널은
  선택이 바뀌어도 node 아래에 남고 그 node 는 목록 아래; 핀 행 = 똑바른 핀, 나머지 = 회색 옆 핀 (Maya grab 22).
- **Show > Attributes** Hidden / Driven by Anim Curve / Expression / Driven Key / User Defined: 공장값 모두 끔 = 거르지 않음, 여럿 = 합집합,
  Show All = 모두 해제 (`allset.graph_attr_clear`). Published = 에셋 컨테이너 없음 → 회색 + notice 그대로.
- **Show > Objects** IkHandles / Sets / Characters (두 편집기): 그 종류의 node 만 (Sets 는 character 포함). Dope Sheet 는 Blender 채널
  목록이라 멤버 오브젝트로 거름 (delegated).
- **Show Upstream Curves** (GE, Maya 공장값 켬): SDK 채널 아래에 `> 드라이버.속성` (SDK 커브) + 드라이버 자신의 커브 행. F-Curve 모드에선
  Blender 가 드라이버 커브를 그리지 않음 (행만, delegated). **Hierarchy Below** (DS, 끔): Maya 는 자손 키를 부모 행에 합치지만 Blender
  Dope Sheet 목록은 못 합쳐 자손을 행으로 넣음 (delegated).
- **Curves** (`operators/graph_curves_203.py`, 레인 C): `allset.rotation_interp` (Independent / Synchronized Euler / Quaternion
  Slerp / Cubic / Tangent Dependent; 한 채널 = 세 채널, 키 시각 합집합, Synchronized Euler 는 depsgraph + 0.1 s timer 로 키 이동 /
  추가 / 삭제를 나머지 두 채널에, 쿼터니언 = Blender QUATERNION W/X/Y/Z 커브 (구간별 Bezier 맞춤), Euler 커브는 `allset_rot_euler` 에
  보관해 되돌리기), `allset.key_sync_filter`, `allset.peak_removal_filter`, `allset.select_curve_nodes` (씬 노드가 아니라 그 채널을
  선택, 결과 칸에 `pCube1_translateX` 꼴 이름, delegated). 메뉴 매핑은 `editor_menu_map` 에 직접 (menu_count 는 bpy 없이 읽음).

## 검증

- 헤드리스: `test_step203_list` 23 / 23, `test_step203_curves` 12 / 12 (Synchronized Euler 1e-3°, Slerp 0.0011°, Cubic / Tangent
  Dependent 0.093°, Key Sync 5 / 5 정확, Peak Removal 깨끗한 80+ 경우 정확, noisy 7 경우는 느슨하게 — 최대 0.43 [U]).
  헤드리스 전체 1900 / 1902 → 실패 2 (`Dope Sheet/Curves` notice 규칙이 안 쓰임, `.AllsetList` 이름) 고친 뒤 관련 28 / 28, 마지막 전체 **1902 / 1902** (231 파일).
- GUI: 새 `gui_step203_outliner` 6 / 6 (핀 행이 선택 밖에서도 남음, Auto Load 켜짐 = Load 회색, Load 뒤 목록 고정; 샷 직접 봄 — 똑바른
  핀 / 회색 옆 핀, 핀 커브 그려짐) + Graph Editor · Dope Sheet · 레이아웃 관련 14 파일 113 / 113.
- 메뉴: Graph Editor 167 → **187 / 229**, Dope Sheet 139 → **158 / 181**, `menu_consistency` 0.

## 남은 것

- Graph Editor 회색 42 (View 19 — Undo / Redo View Change, 테마, Key View …, Bookmarks 3, Buffer Curve Reference, Spreadsheet, Show
  Objects Asset / Clips / MASH, Published, Select Attributes / Entry 들), Dope Sheet 23.
- Pin / 필터 상태는 편집기 모두 공유 (Maya 는 편집기마다), 세션 상태 (파일에 저장 안 됨).
- Hierarchy Below 는 자손을 행으로 넣음 (Maya 는 부모 행에 합침); Upstream 행 이름은 속성 이름 그대로 (`userA`, Maya `User A`).
- Peak Removal noisy 커브 규칙 [U]; Select Curve Nodes 뒤 Maya AE 모습 측정 못 함.
