# Step 10 — M4-a 개념 레이어 (연산자)

PLAN 표 #11 (사용자 번호 10). Freeze / Reset / Center Pivot, Delete History·By Type,
Maya식 부모 지정, Duplicate Special 일부, Maya식 생성·명명, Maya 단위 옵션.

## 계획

근거: `research/maya/concepts.md` §3 (:35-62 행렬), §4 (:64-74 history), §5 (:76-85 freeze/reset/center
pivot), §7 (:96-101 parenting), §8 (:103-108 instance), §12 (:138-148 단위), §13 (:150-154 명명),
§14 (:156-159 생성 기본값); `research/maya/defaults.json` `edit_ops` (freeze/reset/centerPivot/
deleteHistory/parent/unparent/duplicateSpecial 팩토리 값), `camera` (clip 0.1/10000, PREF:569-570);
`research/maya/interaction.md:200-209` (Ctrl+D / Shift+D / Ctrl+Shift+D); `research/blender/concepts.md:15-19`
(parent inverse, delta transforms, apply transforms, origin), `research/blender/api_limits.md:76-78` (cm);
`docs/user_decisions.md` #1 (단위), #2 (부모 지정).

### 0. 핵심 모델: 피벗 = 원점, 델타 = Maya 피벗 오프셋 (delegated)

- 이 키트에서 Maya 피벗은 Blender 원점이다 (Step 3 D 홀드 = Affect Only Origins). Maya 는 피벗을
  `rotatePivot`/`rotatePivotTranslate` 에 따로 저장해서 **translate 값을 바꾸지 않고** 피벗을 옮긴다
  (concepts.md:46-50, interaction.md:133).
- Blender 에서 같은 효과: **`delta_location` 을 Maya 피벗 보정값으로 쓴다**. `matrix_basis` =
  T(location + delta_location) · R(rotation ∘ delta) · S(scale × delta_scale) 이고 Channel Box(Step 6)는
  `location/rotation_euler/scale` 만 보여 주므로, 피벗 위치를 델타에 넣으면 채널은 0 이 되고 원점(피벗)은
  제자리에 남는다 (research/blender/concepts.md:17 "Can be used to implement freeze transforms while keeping
  the visible values at zero").
- 실측 (Blender 4.5 헤드리스): `matrix_basis` 대입은 델타를 유지하고 `location` 등을 역산한다
  (loc=(1,2,3), dloc=(10,0,0) 에 basis=T(5,5,5) → loc=(-5,5,5), dloc 그대로). 그래서 `matrix_world` 를
  쓰는 기존 코드(Ctrl+G, 부모 지정)와 델타가 충돌하지 않는다.

### 1. Freeze Transformations (`maya_kit.freeze_transform`)

Maya: `makeIdentity -apply true -t 1 -r 1 -s 1 -n 0 -pn 1` (defaults.json `freezeTransformations`);
결과 T/R/S = 0/0/1, 피벗은 월드에서 제자리, 정점은 월드에서 제자리 (concepts.md:78-79). 자식이 있으면
자식까지 적용된다 [K].

대상 = 선택 + 모든 자손, 부모 먼저 처리. 객체마다:

1. `W_old` = 처리 전 월드 행렬 (전부 미리 저장).
2. 부모 프레임 `F = W_new(parent) @ matrix_parent_inverse` (부모가 대상이 아니면 현재 월드). 대상이 아닌
   부모 아래(프레임 불변)면 `B_eff = matrix_basis`, 아니면 `B_eff = F⁻¹ @ W_old`.
3. 굽기 가능 = 데이터가 `transform()` 을 가진 MESH/CURVE/SURFACE/LATTICE/META. 그 외(빈 객체=그룹,
   카메라, 라이트, 아마추어, 텍스트)는 회전·스케일을 굽지 않는다 (delegated: 형상이 없으니 Maya 도 변환만
   남긴다 [I]; 조인트는 jointOrient 개념이라 범위 밖).
4. 채널 결정 (`B_eff` = T·R·S 분해 `t, q, s`):
   - translate 동결: `location = 0`, `delta_location = t` (피벗 유지). 아니면 `location = t − delta_location`.
   - rotate 동결(굽기 가능일 때): 회전·델타 회전 = 단위. 아니면 프레임 불변이면 그대로, 바뀌었으면 `q` 를
     객체 rotation_mode 로 (델타 단위).
   - scale 동결(굽기 가능일 때): scale·delta_scale = 1. 아니면 같은 규칙.
5. `B_new` = 새 채널의 `matrix_basis`, 데이터 보정 `D = B_new⁻¹ @ B_eff` → `data.transform(D)`
   (메시는 shape_keys=True). R 만/S 만 동결해도 `D` 가 정확하다 (S 만: D=S, R 만: D=S⁻¹RS — 비균일
   스케일이면 메시가 전단된다, Maya 도 같은 결과 [I]).
6. `det(D) < 0` 이면 메시 면 뒤집기 (Maya preserve normals `-pn 1`).
7. 다중 사용자 데이터는 먼저 단일 사용자로 복사 (Blender `isolate_users` 와 같은 선택, delegated) + 보고.
8. 결과 `W_new = F @ B_new` 는 `W_old` 와 같아야 한다 (테스트로 검증).

옵션(Adjust Last Operation = Maya 옵션 박스, Step 9 run_action): translate/rotate/scale (기본 모두 켬).

### 2. Reset Transformations (`maya_kit.reset_transform`)

Maya `performResetTransformations` (t,r,s 기본 켬, defaults.json): 채널을 0/0/1 로. 델타(= 마지막
Freeze 의 피벗)는 그대로 → "마지막 Freeze 상태로 돌아감". 데이터 불변, 자식은 따라 움직인다.

### 3. Center Pivot (`maya_kit.center_pivot`)

Maya `xform -cpc`: 피벗을 바운딩 박스 중심으로, **정점·translate 불변** (interaction.md:129).

- 중심 `c` = 평가된 객체의 로컬 바운딩 박스 중심 (`ob.bound_box`, 모디파이어 결과 = Maya shape 출력,
  delegated). 형상 없는 빈 객체(그룹)는 자손 월드 바운딩 박스의 중심을 로컬로.
- `B_new = B_old @ T(c)` 가 되도록 `delta_location += (B_old 의 3x3) @ c` (location 불변), 데이터는
  `T(−c)`. 자식은 월드 유지: 자식 basis 는 순수 이동만 바뀌므로 자식 `delta_location` 에 흡수 (자식 채널도
  불변 — Maya 는 피벗이 행렬을 바꾸지 않아 자식 값이 그대로).

### 4. 부모 지정 P / Shift+P (`maya_kit.parent`, `maya_kit.unparent`)

- Maya: 마지막 선택 = 부모, `parentPreserve 1` (월드 유지), 로컬 값 재계산 (concepts.md:98-101,
  defaults.json `parent*`). Blender: 마지막 선택 = 활성 객체.
- 환경설정 **Parent Mode**: `MAYA`(기본, decision 2: `matrix_parent_inverse` = 단위, `matrix_world` 유지 →
  채널이 부모 기준 값) / `BLENDER`(`object.parent_set(keep_transform=True)`, parent inverse 유지).
- 순환(부모가 자식의 자손) 은 건너뛰고 경고 (Maya 도 거부 [K]).
- Shift+P: 월드로, 월드 유지 (`unparentPreserve 1`), parent inverse 정리.
- 키: Object Mode 에서 IC P = `object.parent_set`, Shift+P = `object.parent_clear` 를 교체; Outliner 에도 추가
  (IC Outliner 에 P 없음). `Edit > Parent/Unparent` 메뉴도 이 연산자로.

### 5. Duplicate Special 일부, Duplicate with Transform

- `maya_kit.duplicate_special` (Ctrl+Shift+D, Edit > Duplicate Special): 팩토리 값 = copy, count 1,
  group under Parent, T/R = 0, S = 1 (defaults.json `duplicateSpecial`). 지원: Geometry type Copy/Instance
  (Instance = 데이터 공유, concepts.md:108), Group under Parent/World/New Group (New Group = Ctrl+G 의
  `make_group`), Translate/Rotate/Scale 오프셋, Number of Copies. 계층은 서브트리째 복제 (Maya duplicate 는
  자식 포함). k번째 사본 채널 = t + k·T, r + k·R, s × S^k (delegated: Maya 의 누적 상대 변환 [K]).
  옵션은 마지막 값을 기억, 실행 뒤 Adjust Last Operation 으로 수정.
- `maya_kit.duplicate_with_transform` (Shift+D, Edit > Duplicate with Transform): 직전에 이 키트 연산자로
  복제한 객체가 선택돼 있으면 (원본→사본) 월드 변화량 `Δ = W_dup @ W_src⁻¹` 을 사본에 한 번 더 적용
  (`duplicate -smartTransform`, interaction.md:205). 아니면 제자리 복제. 짝은 모듈 상태 (이름 기준).
- 이름: Maya 처럼 끝 숫자 증가 (`pCube1` → `pCube2`, 데이터 `pCubeShape2`), 가장 작은 빈 번호.
- Ctrl+D 는 IC(`object.duplicate_move`) 그대로 (범위 밖).

### 6. Maya식 생성·명명 (`maya_kit.create`)

- Maya 팩토리: 대화형 생성 꺼짐, **원점에 기본 크기** (concepts.md:158): polyCube 1×1×1, polySphere r=1,
  polyPlane 1×1 10×10. 나머지 값은 Maya 기본값 [K]: sphere 20×20, cylinder r=1 h=2 20축, cone r=1 h=2 20축,
  torus r=1 단면 0.5 20×20, prism 변 3 길이 2, pyramid 변 4, platonic = ico 1 [U], disc r=1 [U].
  Y-up 원기둥 축 → Blender Z 축(같은 "위" 방향), Maya XZ 바닥 평면 → Blender XY.
- 이름: 객체 `pCube1`, 데이터 `pCubeShape1` (concepts.md:152, 같은 번호; 객체·데이터 모두 빈 번호 중 가장
  작은 수). NURBS `nurbsSphere1` 등, 라이트 `pointLight1`/`directionalLight1`/`spotLight1`/`areaLight1`,
  카메라 `camera1`, 로케이터 `locator1`, 빈 그룹 `null1` [K]. Maya 의 history 노드 `polyCube1` 은 대응 없음.
- 방향 있는 카메라·라이트는 Maya 처럼 수평(−Z of Maya = Blender 정면 +Y 방향)으로: 회전 X 90° (delegated).
- 편집 모드에서 호출하면 오브젝트 모드로 나가서 새 객체 (Maya 는 항상 새 객체).
- 환경설정 **Maya Naming** (기본 켬): 끄면 Blender 이름 (`Cube`). Create 메뉴 항목을 이 연산자로 교체.
  Blender Shift+A 메뉴는 그대로.

### 7. 단위 (decision 1)

- 크기 규칙 (delegated): **Maya 1 단위 = Blender 1 BU**. 기본(decision 1: m 유지 + cm 표시)에서는 1×1×1
  큐브가 그리드 한 칸이고 "100 cm" 로 표시된다 (api_limits.md:78 의 100배 표시 차이 그대로). **Maya Units**
  옵션을 켜면 1 BU = 1 cm 이라 표시 값도 Maya 와 같다 ("1 cm").
- 환경설정 **Maya Units (1 BU = 1 cm)** (기본 끔): 켜면 현재 파일의 모든 씬 `length_unit = CENTIMETERS`,
  `scale_length = 0.01`, 3D 뷰 `clip_start/clip_end = 0.1/10000` (Maya PREF:569-570, 단위 = cm = BU).
  이전 값은 씬 커스텀 속성 `maya_kit_units_backup`(JSON)에 남기고 끌 때 복원. 새 파일(저장 경로 없는
  홈 파일)을 열 때도 `load_post` 핸들러가 적용 — **저장된 기존 파일은 자동으로 바꾸지 않는다** (스케일
  의미가 바뀌므로). 그리드는 단위를 따라 1 BU 간격이라 별도 조정 없음 (`overlay.grid_scale_unit` 실측 1.0).
- 부작용 (문서화): 물리·라이트 감쇠·임포트 스케일은 BU = m 을 가정 (api_limits.md:78).

### 8. Delete History, Delete by Type

- `maya_kit.delete_history` (Alt+Shift+D, `delete -ch`, defaults.json `deleteHistory`): 메시 객체의 모디파이어
  스택 + 셰이프 키를 평가 결과로 구워 (`bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers)`)
  새 데이터로 바꾸고 모디파이어·셰이프 키 제거. 이름은 원래 데이터 이름. 뷰포트에서 꺼진 모디파이어는
  효과 없이 사라진다 (Maya 에 없는 개념, 보고).
- `non_deformer=True` (Delete Non-Deformer History, `BakeNonDefHistory`, concepts.md:68): 디포머(Armature,
  Lattice, Hook, Mesh/Surface Deform, Corrective Smooth, Simple Deform, Wave, Cast, Curve, Shrinkwrap,
  Displace, Smooth/Laplacian, Warp, Mesh Cache)와 셰이프 키는 남기고, **스택 앞쪽의 연속된 비디포머만** 굽는다
  (디포머 뒤 비디포머는 디포머까지 굽지 않고는 못 구우므로 남기고 보고). 셰이프 키가 있으면 위상 변경
  모디파이어를 구울 수 없어 건너뛰고 보고 (Blender 제약, delegated).
- `maya_kit.delete_by_type(type, all)` — Edit > Delete by Type (선택) / Delete All by Type (씬 전체):
  History, Non-Deformer History, Channels(애니메이션 제거), Static Channels(값이 변하지 않는 F-커브),
  Constraints, Motion Paths, Rigid Bodies; 전체 전용: Joints(아마추어), Lattices, Cameras, Lights,
  Image Planes(이미지 빈 객체), Clusters(Hook), Nonlinears(Simple Deform/Wave/Cast), Particles.
- 커브 객체의 모디파이어 굽기는 메시 변환이 필요해 건너뜀 (보고).

### 9. 메뉴·마킹메뉴·키

- `menu_map`: Modify > Reset/Freeze Transformations, Modify **Pivot 섹션** (Maya 메뉴 데이터에 없는 동적
  섹션 → `menu_map.EXTRA` "이 항목 뒤에 끼워 넣기", `menu_sets.children` 이 데이터처럼 내보내서 메뉴·핫박스·
  테스트가 같이 본다) > Center Pivot; Edit > Delete by Type/…, Delete All by Type/…, Duplicate Special,
  Duplicate with Transform, Parent, Unparent; Create > 폴리곤/NURBS 프리미티브, 라이트, 카메라, 로케이터,
  Empty Group → `maya_kit.create`.
- A 홀드 + LMB 마킹메뉴 `buildSelectAllMM` (marking_menus.json): NW Delete History, NE Delete Non-Deformer
  History, SE Freeze Transforms (옵션 박스), W/E/N/S (입출력 선택·활성화)는 대응 없음 → 회색. Step 3 의
  임시 Blender 선택 메뉴 대신 엔진/파이로 연다.
- 키 (`maya_patches.patch_concepts`): Object Mode P / Shift+P (IC 항목 교체), Shift+D, Ctrl+Shift+D,
  Alt+Shift+D; Outliner P / Shift+P. `mapping.py` 행 Parent/Unparent/DeleteHistory/DuplicateSpecial/
  DuplicateWithTransform → KIT.

### 10. 테스트 (`tests/test_step10_concepts.py`, 헤드리스 수치)

- Freeze: 회전·비균일 스케일·이동 + 델타가 있는 객체 → 채널 0/0/1, `matrix_world` 의 이동 = 이전 원점
  (피벗 유지), 정점 월드 좌표 불변(전 정점 비교), 부모-자식 계층 전부 동결 + 자식 월드 불변, 음수 스케일 →
  법선 방향 유지, t/r/s 부분 동결 각각 월드 불변, 공유 메시 단일 사용자화, 빈 객체(그룹)는 이동만.
- Reset: 동결 후 이동·회전 → 리셋 → 동결 직후 월드와 같음.
- Center Pivot: 정점 월드 불변, 원점 = 바운딩 박스 중심(월드), 채널 불변, 자식 월드·채널 불변.
- Parent: 회전·스케일된 부모 아래 → 월드 불변, parent inverse = 단위, `location` = 부모 기준 로컬
  (`parent.matrix_world⁻¹ @ W` 의 이동); Blender 모드 → parent inverse ≠ 단위; 순환 거부; Unparent 월드 불변.
- Duplicate Special: 사본 수·이름(`pCube2..`)·오프셋 누적 행렬·Instance 데이터 공유·New Group·서브트리.
  Duplicate with Transform: 이동한 사본에서 다음 사본 = Δ 적용.
- Create: 이름/데이터 이름, 원점, 크기(dimensions), 면 수(Plane 100), 번호 채우기, Maya Naming 끔.
- Units: 켬 → 씬·뷰 값, 끔 → 복원, 저장된 파일은 load_post 가 건드리지 않음.
- Delete History: 모디파이어 결과 정점 수 보존 + 모디파이어 0, 셰이프 키 제거; Non-Deformer: Subsurf 굽고
  Armature 유지; By Type 각 유형.
- 키맵: P/Shift+P/Shift+D/Ctrl+Shift+D/Alt+Shift+D 바인딩, A 마킹메뉴 정의; enable/disable 누수
  (`test_enable_disable`), 마킹메뉴 수 19.

## 한 것

- 연산자 (`src/maya_kit/operators/`):
  - `freeze.py` — `maya_kit.freeze_transform` (계층 전체, t/r/s 옵션, 공유 데이터 단일화, 음수 스케일 면 뒤집기),
    `maya_kit.reset_transform`, `maya_kit.center_pivot` (그룹은 자손 바운딩 박스).
  - `parenting.py` — `maya_kit.parent` / `maya_kit.unparent` (Parent Mode Maya/Blender, 순환 거부).
  - `duplicate.py` — `maya_kit.duplicate_special` (Copy/Instance, 사본 수, 누적 T/R/S, Parent/World/New Group, 서브트리),
    `maya_kit.duplicate_with_transform` (smart transform, 짝은 모듈 상태 `PAIRS`).
  - `history.py` — `maya_kit.delete_history` (+Non-Deformer), `maya_kit.delete_by_type` (15 유형, 선택/전체).
  - `create.py` + `naming.py` — `maya_kit.create` (프리미티브 10 + NURBS 5 + 라이트 4 + 카메라·로케이터·빈 그룹).
  - `units.py` — Maya Units 적용/복원 + `load_post` 핸들러 (새 파일만).
- 환경설정 "Scene Concepts": Parent Mode, Maya Naming, Maya Units.
- 키 (`maya_patches.patch_concepts`, 16): Object Mode P / Shift+P (IC 교체), Shift+D, Ctrl+Shift+D, Alt+Shift+D;
  Outliner P / Shift+P. `mapping.py` Parent/Unparent/DeleteHistory/DuplicateSpecial/DuplicateWithTransform → KIT,
  `docs/keymap_mapping.md` 재생성 (구현 48).
- 메뉴: Modify Reset/Freeze, **Pivot 섹션 > Center Pivot** (`menu_map.EXTRA` + `menu_sets.children`), Edit Delete by Type 7 /
  Delete All by Type 15, Duplicate Special / with Transform, Parent / Unparent, Create 전부 `maya_kit.create`.
- A 홀드 + LMB = 마킹메뉴 `buildSelectAllMM` (엔진/파이; Step 3 임시 Blender 선택 메뉴 대체). 마킹메뉴 19개.

### 계획과 다르게 된 것 / 실측으로 바뀐 것

- **부모 지정의 전단(shear)**: 회전된 자식을 비균일 스케일 부모 아래에 넣으면 로컬 행렬에 전단이 생겨 TRS 채널로는
  월드를 유지할 수 없다 (첫 테스트 실패로 발견). Maya 는 `shear` 속성에 넣는다. → 전단이 있을 때만 그 잔여분을
  `matrix_parent_inverse` 에 넣고 채널은 가장 가까운 TRS (월드 정확). 전단이 없으면 parent inverse = 단위 (decision 2 그대로).
- `matrix_basis` 대입이 델타를 보존한다는 것을 먼저 실측해서 Ctrl+G·부모 지정 코드를 손대지 않았다.

## 검증

- 헤드리스 `python tests/run.py`: **160/160** (기존 130 + `test_step10_concepts.py` 30). Step 7/8 테스트 2곳은 의도된 변경
  (Create = `maya_kit.create`, 마킹메뉴 18 → 19) 으로 기대값 수정.
  - 수치: Freeze 후 채널 0/0/1, 월드 = T(이전 피벗), 전 정점 월드 좌표 불변 (1e-4), 델타 접기·재동결 멱등, t/r/s 부분 동결 4조합,
    3단 계층, 음수 스케일 법선, 공유 메시, 빈 그룹; Reset → 동결 직후 정점; Center Pivot 원점 = 박스 중심·채널/자식 불변;
    Parent 월드 불변·PI 단위·location = 부모 기준 로컬, 전단 잔여, Blender 모드, 순환; Duplicate Special 이름·누적 행렬·
    인스턴스·새 그룹·서브트리, Duplicate with Transform 행렬 Δ 반복; Create 이름·데이터 이름·원점·치수·면 수·빈 번호;
    Units 적용·복원·저장 파일 보호·새 파일 적용; Delete History 정점 수·셰이프 키 굽기, Non-Deformer, By Type 6유형; 키 7개, 메뉴, 마킹메뉴.
- GUI `python tests/gui/run.py`: **100/100** (기존 90 + `gui_step10_concepts.py` 10: P/Shift+P/Shift+D/Alt+Shift+D 실제 키,
  A 홀드 + LMB 엔진 열림, SE 드래그로 Freeze).
- 스크린샷 확인 (`--shots`): `gui_step10_a_menu.png` (Maya 방사 위치, Freeze `[]`, 입출력 항목 회색),
  `gui_step10_modify_menu.png` (Pivot 섹션, Freeze 후 N 패널 0 m / 0° / 1.000).
- `docs/manual_checks.md` Step 10 8항목 (조작감·시각).

## 결정 (delegated)

- 피벗 = 원점, **`delta_location` = Maya 피벗 오프셋** (Freeze 의 피벗 유지, Center Pivot 의 translate 유지). N 패널 Delta Transform 에 값이 보인다.
- Freeze 는 자손까지 적용 [K]; 형상 없는 객체(빈 객체·카메라·라이트·아마추어·텍스트)는 이동만 동결.
- 공유 데이터는 Freeze 전에 단일 사용자로 복사. Center Pivot 중심 = 평가된(모디파이어 포함) 바운딩 박스.
- Parent Mode 기본 Maya, 전단은 parent inverse 잔여로 (위). Shift+P 는 모드와 무관하게 월드 유지.
- Duplicate Special 오프셋 누적 = 채널 산술 (t + kT, r + kR, s·S^k); 이름은 가장 작은 빈 번호. Ctrl+D 는 IC 그대로.
- 크기 규칙 1 Maya 단위 = 1 BU; 기본 단위 설정에서는 "100 cm" 로 표시 (decision 1 의 100배 차이). 카메라·방향 라이트 회전 X 90°.
- Maya Units 는 저장된 파일을 자동으로 바꾸지 않고 현재 파일(켤 때)과 새 파일(load_post)만.
- Delete History = 평가 결과로 메시 교체 (뷰포트에서 꺼진 모디파이어는 효과 없이 사라짐); Non-Deformer 는 스택 앞의 연속 비디포머만,
  셰이프 키가 있으면 건너뜀; 커브 객체는 건너뜀. buildSelectAllMM 의 입출력 4항목은 대응 없어 회색.

## 남은 것

- Maya 의 분리된 rotate/scale 피벗, 컴포넌트 피벗, Bake Pivot, Match Transformations (회색).
- Duplicate Special 의 Smart Transform·Instance Leaf·Duplicate Input Graph/Connections, Ctrl+D 를 제자리 복제로 바꾸는 것.
- Delete All by Type 의 나머지 (Clips, IK Handles, Sculpt Objects, Wires, Shading Groups and Materials, Fluids, nCloth 등) — 회색.
- history 를 남기는 생성 (polyCube1 노드 = Geometry Nodes 대체) 은 범위 밖. 파라미터는 생성 직후 Adjust Last Operation 에서만 (Blender 연산자 기본).
- Step 11 (Outliner/AE): AE 의 transform/shape/입력 탭이 여기의 델타(피벗)·모디파이어(history) 개념을 보여 줄 것.
