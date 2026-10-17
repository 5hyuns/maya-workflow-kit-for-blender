# Step 62 — Set Driven Key · 포즈 모드 제약 · Add Attribute · Blend Shape · Quick Rig 안내

근거: `research/maya/workflows/rigging.md` §1.4–1.7 (흐름 18–27), §2 (18, 20, 21, 23, 26, 27), 갭 표 (Set Driven Key 20, 제약 20,
Add Attribute 12, Blend Shape 12, Quick Rig 8, HumanIK 10), §4 결정 3·4·6, 후보 D; Maya 창 `shots/rigging_06_win1.png`,
`rigging_08_win1.png`; 메뉴 `research/maya/menus.md:1139-1142` (Key > Set Driven Key > Set... / Go to Previous / Go to Next),
`research/maya/runtime_commands.json:4659-4685` (AddAttribute / RenameAttribute "Edit Attribute..." / DeleteAttribute = Modify 의
Attributes 절, ModObjectsMenu.mel 이 실행 때 만듦), Channel Box Edit 메뉴 (`research/maya/channel_box.md:124-127`).

## 계획

### 실측 (Blender 4.5, `tmp/probe62/`)

- 드라이버 (`driver_add` → 기본 Generator 모디파이어, 키 0) 의 모디파이어를 지우고 (드라이버 값, 피동 값) 키를 넣으면 Maya
  animCurveUU 와 같은 매핑: tx 0 → ry 0, tx 1 → ry 90 이면 tx 0.5 → **45°** (Bezier AUTO_CLAMPED, 바깥은 CONSTANT = Maya 기본 infinity).
- **드라이버가 걸린 값을 사용자가 바꾸면 다음 업데이트에 드라이버 결과로 되돌아간다** (원본에 flush: ry 90 입력 → update → 0).
  Maya 는 SDK 창에서 피동 값을 CB 로 바꾼 뒤 Key 를 누른다 (흐름 21) — 그대로는 Blender 에서 안 됨.
- `pose.constraint_add_with_targets` (포즈 모드, 컨트롤 오브젝트도 선택된 상태) → 활성 본에 제약, 대상 = 그 오브젝트.
  지금 kit 의 `object.constraint_add_with_targets` 는 포즈 모드에서도 아마추어 오브젝트에 붙는다 (rigging.md §2-18).
- `object.join_shapes` (타깃 선택 → 베이스 활성 = Maya 순서) → 베이스에 `Basis` + 타깃 이름의 키 (값 0). 다시 하면 `smile.001`.
- Rigify 는 코어 애드온, 기본 꺼짐; `object.armature_human_metarig_add` 는 Rigify 를 켜야 생긴다.

### 1. Set Driven Key 창 (delegated)

- **위치**: Maya 는 떠 있는 창. kit 은 사이드바 dock 의 Channel Box **아래** (Layer Editor 자리, 열려 있는 동안) — CB 가 위에 그대로 보여서
  Maya 처럼 CB 로 값을 바꾸며 Key 를 누를 수 있다. Layer Editor 패널의 draw 가 대신 그린다 (헤더 없는 패널 순서 문제 회피, step 50).
- **모양** (`rigging_06_win1.png`): 「Driver」 머리줄, 노드 목록 | 속성 목록; 「Driven」 머리줄, 노드 목록 | 속성 목록; 아래 버튼 줄
  Key · Load Driver · Load Driven · Close. 속성 = 그 노드의 CB 채널 (보이는 MAIN + 숫자 커스텀 속성), 라벨은 CB 와 같음.
- **Load Driver** = lead 노드 (오브젝트 또는 포즈 본), 속성 선택 = CB 에서 선택한 채널 첫째. **Load Driven** = 선택한 노드 전부,
  속성 선택 = CB 선택 채널 전부. 목록 클릭 = 그 속성 선택 (Driven 은 Ctrl 로 여러 개).
- **Key** = 피동 노드 × 피동 속성마다: 드라이버 없으면 만들고 (AVERAGE, 변수 `sdk` = SINGLE_PROP, 대상 = 드라이버 노드의 ID,
  경로 = 그 채널 전체 경로 + `[i]`; 포즈 본은 아마추어 오브젝트·`pose.bones["b"]...`), Generator 모디파이어 제거, 키 (드라이버 값,
  피동 값) — 같은 x 의 키는 값 교체, AUTO_CLAMPED. 값은 원시 단위 (라디안·미터) 그대로 — 곡선 모양은 Maya 와 같다.
- **피동 값 잡아두기 (위 실측 문제)**: SDK 창이 열려 있고, CB (`channel_box.set_value` — 입력·슬라이더·드래그 모두 여기로) 가 kit SDK
  드라이버 (변수 이름 `sdk`) 가 걸린 채널에 값을 쓰면 그 드라이버 F-커브를 **mute** → 값이 남는다. Key 가 기록한 뒤 unmute, Close 도
  unmute (기록 안 한 포즈는 버림 = Maya 에서 드라이버를 움직이면 버려지는 것과 같음). 파일을 열면 (load_post) kit SDK 드라이버의 mute 를
  푼다. 매니퓰레이터로 피동 채널을 돌리는 것은 Blender 가 드라이버를 덮어써서 안 됨 → 안내 (CB 로 입력).
- **Go to Previous / Next** (Key 메뉴) = 불러온 피동 채널들의 SDK 커브 키 x 중 지금 드라이버 값 앞/뒤 → 드라이버 채널에 그 값.
- 진입: Key > Set Driven Key > Set..., CB Edit > Set Driven Key..., 셸프 SetDrivenKey. 상태는 WindowManager (Maya 창 상태처럼 undo 밖).
- CB 는 이미 드라이버 채널을 DRIVEN 으로 표시 (`ui/channel_box.py:260-281`).

### 2. Constrain 메뉴 모드 분기 (delegated, rigging.md §4-3)

- `maya_kit.constrain(type)`: 포즈 모드 = `pose.constraint_add_with_targets` (활성 본, 대상 = 선택 오브젝트 또는 본), 아니면 오브젝트.
  대상이 없으면 안내 「컨트롤을 먼저, 조인트를 마지막에 선택하세요 (포즈 모드에서 조인트).」 Parent (Child Of) 는 Blender 가 만들 때
  inverse 를 설정 = Maya 기본 Maintain Offset 켬. Point / Orient / Scale 의 Maintain Offset 은 남은 것.
- Constrain 메뉴, 셸프의 제약 버튼 모두 이 연산자로.

### 3. Add / Edit / Delete Attribute (delegated)

- Modify 의 Attributes 절 (Evaluate Nodes 다음, `menu_map.EXTRA`) + CB Edit 메뉴: `maya_kit.add_attribute` 대화상자 = Long name,
  Data Type (Float / Integer / Boolean), Minimum / Maximum (켜기) / Default. 선택한 노드 (오브젝트·포즈 본) 마다 커스텀 속성 +
  `id_properties_ui` min/max/default → CB 에 행 (이미 숫자 커스텀 속성을 그림). 이름은 Maya 규칙 (글자·숫자·_, 숫자로 시작 안 함).
- CB 라벨 = Maya nice name (`fingerCurl` → "Finger Curl", `curl` → "Curl"; Maya 기본 Channel Names = Nice, channel_box.md:131).
- `maya_kit.edit_attribute` = CB 선택 커스텀 채널 하나의 min/max/default, `maya_kit.delete_attribute` = CB 선택 커스텀 채널 삭제
  (선택 노드 전부, 그 채널의 키·드라이버도).

### 4. Blend Shape (delegated)

- `maya_kit.blend_shape` = `object.join_shapes` (타깃 → 베이스 순서 그대로), 정점 수가 다르면 안내. Deform > Blend Shape, Deform >
  Blend Shape (Edit) > Add, 셸프 CreateBlendShape.

### 5. Quick Rig / HumanIK (delegated, rigging.md §4-6)

- Skeleton > Quick Rig, Windows > Animation Editors > Quick Rig, 셸프 QuickRigEditor = `maya_kit.quick_rig`: Rigify 가 꺼져 있으면 확인 대화상자
  (켜기 = 사용자 환경설정의 애드온 목록이 바뀜) → 켜고 Human Meta-Rig 추가 (3D 커서, 실제 크기 1.8 m). 안내는 step 54 의 notices 그대로
  (툴팁·Help Line). HumanIK 는 회색 + 같은 안내.

### 6. 검증

- 헤드리스 `test_step62_rigging_tools.py`: SDK 두 번 Key → 0.5 에서 45°, 같은 x 다시 Key = 교체, 피동 값 mute/unmute, Go to Next/Previous,
  포즈 본 드라이버·피동, 커스텀 속성 드라이버; 포즈 모드 제약이 본에; Add/Edit/Delete Attribute + nice name; Blend Shape (Basis + 타깃,
  정점 수 다름 = 안내); Quick Rig (Rigify 켜기 + 메타 리그); 메뉴·셸프 매핑.
- GUI `gui_step62_sdk.py` (rigging_06 순서): 로케이터 tx 를 CB 에서 선택 → Load Driver, 큐브 ry 선택 → Load Driven → Key → 로케이터 tx 1,
  큐브 ry 90 입력 → Key → 로케이터 tx 0.5 → 큐브 ry 45. 스크린샷.
- dogfood, manual_checks.

## 한 것

- **Set Driven Key** (`operators/driven_key.py`, `ui/set_driven_key.py`): 창 = dock 의 Channel Box 아래 (Layer Editor 자리, 열린 동안). Driver 노드 |
  속성, Driven 노드 | 속성 = 4줄 스크롤 UIList (처음엔 평범한 행 → 10 채널이 버튼을 사이드바 밖으로 밀어냄, GUI 샷), 버튼 Key · Load Driver ·
  Load Driven · Close = 2×2 (한 줄이면 "Load Dr..." 로 잘림, 샷) — 읽는 순서는 Maya 와 같음. Load = lead / 선택 노드 + CB 선택 채널, 목록 클릭 =
  속성 고르기 (Driven 은 Ctrl 추가), Key = 드라이버 (AVERAGE, 변수 `sdk`) + 키 (드라이버 값, 피동 값), 같은 x = 교체, AUTO_CLAMPED.
  포즈 본·커스텀 속성 모두 (드라이버 경로 `pose.bones["b"].rotation_euler`, 변수 경로 `["curl"]`). Go to Previous / Next.
- **피동 값 잡아두기**: `channel_box.WRITE_HOOKS` (CB 쓰기 전 훅) → SDK 창이 열려 있으면 kit SDK 드라이버를 mute; Key 가 기록 후 unmute, Close·파일 열기가 unmute.
- **CB 커스텀 속성 쓰기가 depsgraph 를 태그** (`set_value` → `id_data.update_tag()`): Python 의 ID 속성 대입은 아무것도 태그하지 않아, 커스텀 속성을
  읽는 드라이버가 갱신되지 않았다 (헤드리스 테스트가 잡음 — 기존 CB 에도 있던 문제).
- **Constrain** = `maya_kit.constrain` (메뉴 `_con`, 셸프 제약 버튼): 포즈 모드 = 활성 본에 (`pose.constraint_add_with_targets`, 대상 = 선택 컨트롤
  오브젝트 / 본), 아니면 오브젝트. 대상 없음 → 「Select the control first, then the joint last」.
- **Add / Edit / Delete Attribute** (`operators/rig_tools.py`): Modify 의 Attributes 절 (`menu_map.EXTRA` "Modify/Evaluate Nodes" 뒤) + CB Edit 메뉴.
  Add = 이름 (Maya 규칙) · Float/Integer/Boolean · Min/Max/Default (값은 범위로 잘림) → 선택 노드 전부; Edit = 이름 바꾸기 (키·드라이버 경로·
  다른 드라이버의 변수 경로까지) + 범위; Delete = CB 선택 커스텀 채널 + 그 F-커브·드라이버. CB 라벨 = Maya nice name (`channel_box.nice_name`).
- **Blend Shape** = `maya_kit.blend_shape` (`object.join_shapes`, 타깃 → 베이스): Deform > Blend Shape, Blend Shape > Add, 셸프. 정점 수 다름 = 오류.
- **Quick Rig** = `maya_kit.quick_rig`: Rigify 꺼짐 → 확인 → 켜기 + Human Meta-Rig. Skeleton / Windows > Animation Editors > Quick Rig, 셸프 QuickRigEditor.
  step 54 안내 (Rigify) 는 툴팁에 그대로, HumanIK 는 회색 + 안내.
- 셸프 SetDrivenKey = SDK 창, CB Edit > Set Driven Key... 연결.

### 계획과 다르게 된 것 (delegated)

- Point / Orient / Scale 의 Maintain Offset 은 이번에 안 함 (Parent 는 Blender 가 만들 때 inverse 를 설정해 Maya 기본과 같음).
- Maya SDK 창의 메뉴 줄 (Load / Options / Key / Select / Help) 없음 — Go to Previous / Next 는 Key 메뉴에.
- 피동 노드가 여럿이면 선택한 피동 속성을 그 속성이 있는 모든 피동 노드에 키 (Maya 는 목록에서 고른 노드만).

## 검증

- 헤드리스 `python tests/run.py`: **495/495** (58 파일; 새 `test_step62_rigging_tools.py` 9 개: rigging_06 순서 0.5 → 45°, 같은 x 교체,
  상수 바깥, Go to Previous/Next, Close 가 포즈 버림, 창이 닫혀 있으면 드라이버가 이김, 커스텀 속성 → 포즈 본 rz (5 → 45°), 포즈 모드 제약이 본에
  / 대상 없음 / 오브젝트 모드, Add/Edit/Delete Attribute (+ 키 따라감, 잘못된 이름), Blend Shape (Basis + 타깃, 정점 수 오류), Quick Rig (Rigify
  켜기 + 메타 리그, 끝나고 끔), 메뉴·셸프·안내 매핑, nice name).
- GUI `python tests/gui/run.py --ui-scale 0.8`: 417/419 — 실패 2 는 step 26 (RMB cancel) 로, 다시 돌리면 8/8 두 번 (step 59 문서의 간헐 실패).
  새 `gui_step62_sdk.py` 9/9 (기본 배율·0.8 모두): CB Translate X 클릭 → Load Driver, pCube1 Rotate Y 클릭 → Load Driven → Key → CB 에 tx 1·ry 90 입력
  (ry 90 유지) → Key → tx 0.5 → ry **45.00**; Add Attribute 대화상자 샷. 버튼 위치 = 사이드바 내용 위에서의 거리 + `region.view2d.view_to_region`
  (스크롤 따라감). 샷 `tmp/shots62/gui_step62_sdk_result.png` (큐브 45°, CB Rotate Y 드라이버 표시), `gui_step62_add_attribute.png`.
- `python tools/dogfood.py`: **47/47**, 콘솔 오류 0.

## 남은 것

- Point / Orient / Scale Maintain Offset, Constrain 옵션 박스.
- SDK 창 메뉴 줄, 피동 노드별 속성 선택 (지금은 모든 피동 노드에 같은 속성).
- 매니퓰레이터로 피동 채널 포즈 (Blender 가 드라이버로 되돌림 — CB 로 입력하라는 안내뿐).
- Shape Editor 창 (Windows > Animation Editors > Shape Editor), Set Blend Shape Target Weight Keys, Blend Shape > Remove / Swap.
- Duplicate Attribute, Maya 의 Enum / Vector / String 속성.
