# Step 57 — Joint Tool·Orient/Mirror Joint·포즈 픽워크·P

근거: `research/maya/workflows/rigging.md` §1.1 (1–6: Joint Tool 클릭·Enter, joint1…, Orient Joint □ Primary X / Secondary Y /
SAO Y+, Mirror Joints □ YZ / Behavior / Search·Replace, 화살표 pick-walk, P), §2 1–6 (kit: `object.armature_add` 한 개
`ui/menu_map.py:303`, `ui/shelf_map.py:76`; Orient = `calculate_roll` 편집 모드만·옵션 없음; Mirror = `symmetrize` .L/.R 이름 필요;
P = 오브젝트 모드만), §3 (Joint Tool 20), §4 개념 1 (조인트 = 한 아마추어 안의 본, `skeleton1` / `joint1`, XYZ, Y 축 안내), 7 (단위),
§5 후보 A, shots `rigging_01.png` (Outliner joint1 계층), `rigging_02_win1.png` (Orient Joint 옵션 창).
`$S\startup\bl_ui\space_toolsystem_toolbar.py:728-746` (`armature.click_extrude`), docs/steps/step_55.md (포즈 본 = 조인트 선택).

## 계획

### 1. Joint Tool `maya_kit.joint_tool` (모달, delegated)
- Skeleton > Create Joints, 셸프 JointTool 이 부름 (지금 `create(JOINT)` = 본 하나). 어디서 불려도 (메뉴 = 상단 바 문맥) 창
  모달: 이벤트마다 마우스 아래 3D 뷰 WINDOW 영역을 직접 찾음 (`screen.areas`), 그 `region_3d` 로 투영.
- LMB 누름 (수정키 없음, 3D 뷰 위) = 조인트 하나. 깊이 (delegated, Maya 와 같게): 정사영 뷰 = 원점을 지나는 뷰 평면, 원근 뷰 = 바닥
  (z = 0) 과 시선의 교점 (평행이면 원점 깊이). Alt / MMB / 휠 등 그 밖의 이벤트와 3D 뷰 밖 클릭은 PASS_THROUGH (탐색·메뉴 그대로).
- Maya 조인트 = 점, Blender 본 = 선분 → 클릭 N 개 = 본 N 개: 본 `jointK` 머리 = 클릭 K, 꼬리 = 클릭 K+1 (다음 클릭이 오면 옮김),
  마지막 본 (Maya 끝 조인트) 꼬리 = 머리 + 이전 마디 방향 × 그 길이의 ½ (첫 본만 있을 때는 + 뷰 위쪽 × `maya_unit()`). 이어진 본은
  `use_connect`. 이름 = 모든 아마추어에서 비어 있는 가장 작은 `jointN` (Maya 처럼 장면 전체 번호), 오브젝트 `skeleton1`
  (`naming.apply_maya_name`), 아마추어 데이터 `skeletonShape` 없음 (Maya 에 대응 노드 없음).
- 첫 클릭에 아마추어를 원점 단위 행렬로 만들고 편집 모드 (놓는 동안 본이 보임). 시작할 때 활성 아마추어가 편집 모드이고 활성 본이
  있으면 그 본 꼬리에서 이어 붙임 (Maya: 기존 조인트를 클릭하면 거기서 가지).
- Enter / 숫자패드 Enter = 끝: 포즈 모드, 새 포즈 본 rotation XYZ, 마지막 조인트만 선택·활성 (CB lead = joint3, step 55). Esc = 끝
  (만든 조인트는 남김, 하나도 없으면 취소). 헤더 안내 「Joint Tool: click to place joints, Enter to finish」.
- 로직은 bpy 가 적은 함수 (`click_point`, `add_joint`, `finish`) 로 → 헤드리스 테스트, 모달은 GUI.

### 2. Orient Joint □ / Mirror Joints □ (invoke_props_dialog, delegated)
- Maya option box = 설정 창 (PLAN 「Not possible」 option boxes 의 대체: 메뉴 누름 = `invoke_props_dialog`, 확인 = 실행; 길게 누름 =
  지금처럼 실행 + Adjust Last Operation).
- **Orient Joint** (`maya_kit.orient_joint`): Maya 옵션 Primary Axis (X/Y/Z) · Secondary Axis · Secondary World Orientation (X+ … Z−,
  None) · Orient children. Blender 본은 국소 Y 가 다음 조인트를 향하고 roll 이 국소 Z 를 정함 → Primary Axis 는 안내만 (「Blender joints
  point their Y axis at the child joint (Maya Primary Axis X): only the secondary axis can be set.」), Secondary World Orientation →
  `armature.calculate_roll(type=GLOBAL_POS/NEG_*)` (Maya Y-up → Blender Z-up: Maya X→X, Y→Z, Z→−Y, 결정 5), None = `POS_Z`(정렬 안 함
  대신 이전 roll 유지 → 아무것도 안 함). 대상 = 선택 조인트 (+ Orient children = 자손), 포즈·편집 모드 모두 (잠시 편집 모드).
- **Mirror Joints** (`maya_kit.mirror_joints`): Mirror across XY / YZ / XZ (Maya 평면 → Blender: YZ = x 반전, XY = y 반전 (Maya z = −y),
  XZ = z 반전), Mirror function Behavior / Orientation, Search for / Replace with. 선택 조인트와 그 아래 계층을 원점 평면으로 반사한 복제
  본 (부모 = 복제된 부모, 없으면 원본의 부모), 이름 = 검색·치환 (바뀌지 않거나 겹치면 다음 `jointN`), 회전 = 반사 행렬에서 한 축을 뒤집어
  오른손 좌표 (Behavior: 국소 X 반전 = Blender symmetrize 와 같음, Orientation: 원본 축 방향 유지 = roll 그대로). `armature.symmetrize`
  는 .L/.R 이름이 필요해 안 씀.

### 3. 포즈 모드 화살표 = 조인트 pick-walk, P / Shift+P
- `maya_kit.pick_walk_joint` (Pose 키맵 ↑↓←→, IC `pose.select_hierarchy` ↑↓ (IC:2453-2459) 와 Pose 의 ←→ `screen.frame_offset` 제거 — 프레임은
  Alt+, / Alt+. (step 20)): ↑ 부모, ↓ 첫 자식, ←/→ 형제 (같은 부모, 이름 순, 둘레). 선택 본마다, 활성도 따라감.
- P = `maya_kit.parent_joint` (Maya: 자식들 먼저, 부모 마지막 선택 = 활성 본): 포즈·아마추어 편집 모드에서 선택 본들의 부모 = 활성 본,
  `use_connect` 끔 (월드 위치 유지 = Keep Offset). Shift+P = `maya_kit.unparent_joint` (부모 없음). IC Pose P `object.parent_set`
  (IC:2434), Armature P / Shift+P `armature.parent_set` / `parent_clear` (IC:3099-3100) 바꿈. `keymap/mapping.py` Parent / Unparent 노트.

### 4. 검증
- 헤드리스 `tests/test_step57_joints.py`: click_point (정사영 평면 / 원근 바닥), add_joint 3 번 → skeleton1, joint1>joint2>joint3,
  연결, 길이, finish → 포즈 모드·XYZ·lead joint3, 두 번째 스켈레톤 joint4…, Orient (calculate_roll type 대응, 자손), Mirror (YZ: 6 본, 위치
  반사, 부모, 이름 l_→r_, roll 반전), pick-walk, P / Shift+P, 키맵 (Pose 화살표·P, Armature P), 메뉴·셸프 매핑.
- GUI `tests/gui/gui_step57_joints.py` (rigging_01 순서, 1.25 / 0.8): Skeleton > Create Joints → front 뷰 세 번 클릭 → Enter → 포즈
  모드, CB lead joint3 → ↑ ↑ → joint1 → Mirror Joints □ (대화상자 OK, YZ) → 본 6 → 스크린샷.
- dogfood 47/47, `tools/gen_keymap_mapping.py`.

## 한 것

- `operators/joints.py` (새):
  - `maya_kit.joint_tool` — 창 모달 (메뉴·셸프 어디서 불려도), 이벤트마다 마우스 아래 3D 뷰 WINDOW (Tool Box 열 제외) 를 찾아 투영;
    `click_point` (정사영 = 원점 지나는 뷰 평면, 원근 = 바닥 z = 0), `new_skeleton` (`skeleton1`, 원점, 편집 모드), `add_joint`
    (본 K = 클릭 K → K+1, 끝 조인트 = 이전 마디 방향 ½ 길이, 첫 본만 = 뷰 위쪽 × `maya_unit()`, `use_connect`, 이름 = 장면 전체에서 빈
    `jointN`, 같은 자리 클릭 무시, 시작할 때 편집 모드 활성 본이 있으면 거기서 가지), `finish` (포즈 모드, XYZ, 마지막 조인트만 선택 =
    CB lead). Enter = 끝, Esc = 끝 (아무것도 없으면 취소), 그 밖의 이벤트는 PASS_THROUGH (탐색 그대로), 상태 표시줄 안내.
  - `maya_kit.orient_joint` (옵션 창 = `invoke_props_dialog`: Primary / Secondary Axis, Secondary World Orientation, Orient Children +
    Y 축 안내) → `armature.calculate_roll` (`SAO_ROLL`: Maya Y+ = GLOBAL_POS_Z, Z+ = GLOBAL_NEG_Y …), 포즈·편집 모드 (잠시 편집 모드).
  - `maya_kit.mirror_joints` (옵션 창: XY / YZ / XZ, Behavior / Orientation, Search For / Replace With) → `mirror()`: 선택 + 자손을
    월드 원점 평면으로 반사한 복제 (`EditBone.matrix` = 반사 회전에서 X (Behavior) 또는 Z (Orientation) 뒤집기, 부모 = 복제된 부모 /
    원본 부모), 이름 치환 (안 바뀌거나 겹치면 다음 번호).
  - `maya_kit.pick_walk_joint` (↑ 부모, ↓ 첫 자식, ←→ 이름순 형제 순환), `maya_kit.parent_joint` / `unparent_joint` (선택 → 활성 본,
    connect 끔 = 제자리, 고리 방지).
- `ui/menu_map.py`: Skeleton > Create Joints / Mirror Joints / Orient Joint → 위 연산자; `ui/shelf_map.py` JointTool → joint_tool.
  (Create > ... 의 `create(JOINT)` 본 하나는 그대로 — Maya 에 없는 경로라 남김.)
- 키맵 `patch_joints`: Pose ↑↓←→ = pick_walk_joint (IC `select_hierarchy` ↑↓, `frame_offset` ←→ 제거), Pose / Armature P = parent_joint,
  Shift+P = unparent_joint (IC Pose `object.parent_set`, Armature `parent_set` / `parent_clear` 제거). `keymap/mapping.py` Parent /
  Unparent / PickWalk* 노트, `docs/keymap_mapping.md` 재생성. `tests/test_step3_hold.py` 의 「Pose ← = frame_offset」 기대를 바꿈.

## 검증

- 헤드리스 `tests/test_step57_joints.py` 9/9, 전체 451/451 (step 56 442 + 9).
- GUI `tests/gui/gui_step57_joints.py` 11/11 (1.25 / 0.8), MayaKit 레이아웃: Skeleton > Create Joints (C) → Joint Tool 모달 → persp 뷰
  세 번 클릭 → 본 3 (z = 0 바닥) → Enter → 포즈 모드, joint1 > joint2 > joint3, CB lead joint3, XYZ → ↑ ↑ → joint1 → Skeleton > Mirror
  Joints (M) → 옵션 창 (YZ, Behavior) → Enter → 조인트 6, joint4 = joint1 의 YZ 반사. 스크린샷 직접 확인 (`gui_step57_joint3.png`,
  `_mirror_dialog.png`, `_mirrored.png`).
- GUI 전체 376/376 (0.8) · 375/375 (1.25), dogfood 47/47 (콘솔 오류 0), `tools/gen_keymap_mapping.py` 재생성.

## 남은 것

- 레이아웃의 Outliner (Blender C 트리) 는 조인트 계층을 안 보여 줌 (step 55 남은 것 그대로; kit 사이드바 Outliner 는 보여 줌).
- Joint Tool 옵션 (Orientation, 조인트 반지름, Create IK Handle 등), 놓는 중 드래그로 위치 조정, Backspace 로 마지막 조인트 지우기 없음.
  정사영 클릭 깊이는 원점 평면 고정 (Maya 와 같음), Insert Joints / Connect Joint / Reroot Skeleton 은 그대로 (회색 / Blender 연산자).
- Orient Joint 의 Primary / Secondary Axis 는 안내만 (Blender 본 Y = 다음 조인트, roll 은 국소 Z 를 정함), Reorient local scale axes
  없음. Mirror 의 Orientation 은 근사 (국소 Z 반전).
- 아마추어 편집 모드 화살표 (IC select_more/less) 는 그대로, 포즈 모드 ←→ 프레임 이동은 Alt+, / Alt+. 로만.
