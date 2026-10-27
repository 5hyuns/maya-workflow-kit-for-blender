# Step 226 — Controls from NURBS curves (bone custom shapes) (Issue #136)

기준: `docs/strategy/DECISIONS7.md` 결정 1 (컨트롤 = 본 Custom Shape, 클릭 = 그려진 모양, 내보내기에서 모양 커브 제외),
`docs/strategy/ATTACH_PLAN.md` L1–L5, `research/maya/re/maya2026_controls.md` (+ `.json`), 이번 mayapy 측정
`research/maya/re/controls_226.json` (스크립트 `research/scripts/maya_controls226/measure.py`, Maya 2026).
Offset Parent Matrix = 하지 않음 (ATTACH_PLAN L3 (d)).

## 계획

### 이번 측정 (mayapy 2026, `controls_226.json`)
- SDK 커브: 키 2 개 (0,0)(10,90) → x 0.5 = 0.6525 (끝 탄젠트 평평, smoothstep); 키 3 개 / 4 개(오버슈트) 표본 29 개씩.
- 드라이버 2 개 = `blendWeighted1` 이 **더함**: curl (0,0)(10,90) + spread (0,0)(4,−10)(10,−30) 표본 20 쌍; 회전 10/10 → 60,
  세 번째 드라이버 (0,0)(1,5) → 65.
- 여러 타깃 컨스트레인트 (가중치 = 타깃마다 `<target>W<i>`, 정규화 w/Σw):
  - Point: (1,4.5)(−3,4) → 같은 가중치 (−1,4.25), W1 = 3 → (−2,4.125); **모두 0 = 같은 가중치** (−1,4.25); W0 0.5 · W1 0 → 타깃 A 그대로.
  - Scale: **가중 기하 평균** (2,2,2)(1,3,1) → (1.414, 2.449, 1.414); W1 = 3 → (1.189, 2.711, 1.189).
  - Orient (interpType 1 Average): **가중 쿼터니언 합 정규화 (nlerp)**: 45° / −15° 같은 가중치 15°, W1 = 3 → −0.26148° (각도 선형이면 0).
  - Parent (mo): 타깃마다 오프셋 위치의 가중 평균: ctrl x+2 → (1, 4, 0); ctrl rz 90 → (1.75, 3.75) rz 45; W1 = 3 → (0.875, 3.875) rz 21.598.

### 설계 (레인별, 파일이 겹치지 않게)
1. **L1 컨트롤 모양** (`operators/control_shapes.py`, `command_line/cmds_dag.py`, `operators/select_priority.py`,
   `operators/file_io.py`): `allset.parent_shape(relative)` = Maya `parent -s [-r]`. 대상이 본이면 커브 데이터 복사본을
   본 공간으로 구워(`Curve.transform`) Custom Shape 로 (`use_custom_shape_bone_size` 끔, custom_shape 변환은 항등).
   - `-r`: CV 로컬 값을 조인트 Maya 좌표로 읽음 — 조인트 Maya X/Y/Z = 본 Y/Z/X, 커브의 Maya 로컬 (x, z, −y) → 본 공간
     (−y, x, z) = Z 축 +90° 회전. 절대: 본 월드⁻¹ × 커브 월드.
   - 모양 오브젝트 = `<shape 이름>` 커브, 장면 밖 숨김 컬렉션 `.AllsetControlShapes` + fake user (커브를 지워도 안 끊김).
     같은 본에 두 번째 모양 = Maya 처럼 **추가** (스플라인 합침), `replace=True` = 교체.
   - 원래 커브: `-r` 이면 Maya 처럼 빈 트랜스폼 (Empty, 같은 이름·행렬·부모) 이 남고, 절대면 사라짐.
   - 대상이 커브 오브젝트 = 스플라인 합치기 (두 셰이프 한 컨트롤). Empty / 그룹 대상 = Blender 가 셰이프를 못 줌 → 경고.
   - Command Line `cmds.parent(shape, joint, s=True, r=True)` 받음.
   - 클릭: `select_priority` 의 조인트 히트가 Custom Shape 가 있으면 그 와이어 (평가된 커브 선분 투영) 로 판정.
   - 내보내기: Custom Shape 원본 (장면 안에 있어도, Rigify WGT 포함) 은 Export All / Selection 에서 뺌.
2. **L2 색** (`operators/wire_color.py`, `ui/menu_map.py`, `ui/ae_layout.py`, `operators/option_windows*.py`):
   Maya `colorIndex` 32 색 표 (값만), Display > Wireframe Color… = Maya 창 (user palette 8 = 인덱스 24–31, RGB, Apply).
   오브젝트 = `Object.color` + Maya 레이아웃 3D View `shading.wireframe_color_type = 'OBJECT'`; 본 (Custom Shape 컨트롤 포함)
   = 포즈 본 `color.palette = 'CUSTOM'`. AE Drawing Overrides (Enable Overrides, Color 인덱스 / RGB).
3. **L3 Match + L4 여러 타깃** (`operators/constrain_multi.py`, `operators/rig_tools.py`, `operators/option_windows.py`
   `_constraint`, `ui/channel_box.py`, `operators/snap_align.py`):
   - Match Transformations: 대상 (리드) 가 포즈 본이면 그 본의 월드 행렬 (조인트 Maya 축 포함).
   - 타깃 2 개 이상 = 타깃마다 같은 종류 컨스트레인트를 쌓음; Maya 가중치 = 소유자 ID 속성 `allset_w_<con.name>`
     (키·SDK 가능), influence = 드라이버 (단순 식, Python 자동 실행 불필요).
     - Point / Orient / Parent: 누적 `i_k = w_k / S_k if S_k > 0 else 1/(k+1)` (S_k = Σ_{j≤k} w_j) — 위치는 정확한 가중 평균,
       모두 0 = 같은 가중치 (측정).
     - Parent: Child Of 를 쌓으면 앞 결과에 곱해져 평균이 안 됨 → 타깃마다 숨은 오프셋 Empty (타깃의 자식, mo 면 소유자 월드)
       + Copy Transforms (World) 누적 influence. 단일 타깃은 지금처럼 Child Of.
     - Scale: Copy Scale `power = w_k / Σw` (첫째 교체, 나머지 `use_offset` 곱) = 가중 기하 평균 (정확).
     - 회전: Blender influence 섞기는 slerp → 같은 가중치 2 타깃은 Maya 와 같고, 다른 가중치는 nlerp 와 최대 ~0.3° 차이
       (W1 = 3 에서 0.26°) [U, 기록].
   - Channel Box: 한 묶음 = Maya 노드 하나 (`<owner>_<type>1`), 행 = `<target>W0`, `<target>W1` (가중치 속성).
   - Delete / 비활성 / Bake 의 mute 는 묶음 단위 (숨은 Empty 정리).
4. **L5 SDK** (`operators/driven_key.py`, `ui/set_driven_key.py`): 커브 = Auto Clamped + `auto_smoothing 'CONT_ACCEL'`
   (step 223 측정: Maya auto), Driven 목록에 셰이프 키 값 (blendShape), 컨스트레인트 가중치 / influence, IK ikBlend
   (커스텀 속성 그대로). 다른 드라이버로 두 번째 키 = Maya blendWeighted: 드라이버마다 숨은 속성 `allset_sdk_<n>` 에 드라이버
   + 키 커브, 채널 드라이버 = SUM.

### 레인 (병렬, 사용자 규칙 — 파일 단위로 나눔)
- A = 1, B = 2, C = 3, D = 4. 공용 파일 `operators/__init__.py` 는 메인이 먼저 스텁 3 개 등록 (레인은 손대지 않음).
- 테스트: 레인마다 `tests/test_step226_<lane>.py` (`ALLSET_SANDBOX=s226<lane>`), GUI 는 A 의 클릭 하나만
  (`tests/gui/gui_step226_control_click.py`). Blender 프로세스는 `tools/blender_slots.py` 가 2 개로 줄 세움.

### 검증
- SDK 값 vs mayapy 1e-4 (`controls_226.json` 표본 전부), 여러 타깃 Point / Scale / Parent 위치 1e-4, Orient 같은 가중치 1e-4 +
  다른 가중치 차이 기록, L1 `-r` / 절대 CV 월드 = Maya (5.68, 2.39, −0.78) / (1.78, 0, −0.78) (Y-up → Z-up, × maya_unit),
  내보낸 FBX 에 모양 메시 없음, GUI 클릭이 Custom Shape 위에서 본 선택.

## 한 것

레인 4 개 병렬 (A L1 · B L2 · C L3/L4 · D L5, 파일 단위로 나눔; 공용 `operators/__init__.py` 는 메인이 스텁을 먼저 등록).

- **L1 컨트롤 모양** (`operators/control_shapes.py`): `allset.parent_shape` + `parent_shape()` = Maya `parent -s [-r]`.
  본 대상 = 커브 데이터 복사본을 본 공간에 구워 Custom Shape (`.AllsetControlShapes` 장면 밖 + fake user, bone size 끔).
  `-r` = Z +90° (조인트 Maya 축), 절대 = 본 월드⁻¹ × 커브 월드. 두 번째 모양 = 스플라인 추가 (Maya), `replace` = 교체.
  `-r` 뒤 원래 커브 = 같은 이름의 빈 트랜스폼 (Empty), 절대 = 사라짐. 커브 대상 = 스플라인 합침, Empty 대상 = 경고.
  `cmds.parent(s=True, r=True)` (`command_line/cmds_dag.py`). 클릭: `select_priority` 조인트 히트 = Custom Shape 와이어 투영
  (팔면체 아님). 내보내기: 장면 안의 Custom Shape 원본 (Rigify WGT 포함) 은 Export All / Selection 에서 뺌 (`file_io.py`).
- **L2 색** (`operators/wire_color.py`, `ui/ae_layout.py`, `ui/menu_map.py`): Maya colorIndex 32 색 표 (값만),
  Display > Wireframe Color… = Maya 창 (Indexed / RGB, user palette 8 = 24–31, Apply / Default / Close), AE Drawing Overrides
  (Enable, Index / RGB). 오브젝트 = `Object.color` (scene linear 로 변환, 측정) + Maya 워크스페이스 3D View 만
  `wireframe_color_type` THEME → OBJECT (킷 색이 없어지면 되돌림), 본 = 포즈 본 color CUSTOM (sRGB).
- **L3 Match**: 리드가 포즈 본이면 그 본의 월드 행렬 (`snap_align.py`).
- **L4 여러 타깃** (`operators/constrain_multi.py`, `rig_tools.py`, `option_windows._constraint`, `ui/channel_box.py`):
  타깃마다 컨스트레인트를 쌓고 Maya 가중치 = 소유자 속성 `allset_w_<member>` (키·SDK 가능), influence = 단순 식 드라이버
  `w_i / S_i if S_i > 0 else 1/(i+1)`; Scale = power w/Σw (가중 기하 평균); Maintain Offset = 숨은 오프셋 Empty
  (`.AllsetConstraintHelpers`, 장면 밖, 지우면 정리). CB = Maya 노드 하나 + `<target>W<i>` 행.
- **L5 SDK** (`operators/driven_key.py`, `ui/set_driven_key.py`): Maya 2026 auto 탄젠트 규칙 직접 계산 (끝 평평, 가운데 =
  (y₊ − y₋)/(x₊ − x₋), 극값 평평; Blender 핸들 유형으로는 3 키에서 2.58 차이 — 측정) → ALIGNED 핸들 (delegated).
  다른 드라이버 = blendWeighted 더하기: 드라이버마다 숨은 `allset_sdk_<n>` + 채널 드라이버 SUM; Key = 다른 입력을 뺀 값을 그
  입력에 (delegated). Driven 노드에 blendShape (셰이프 키 value), 컨스트레인트 가중치 (W 속성 또는 influence), IK ikBlend.

## 검증

- 헤드리스 `-k step226`: **36 / 36** (shapes 8, colors 11, constraints 10, sdk 7).
  - SDK vs mayapy: two_keys 1.46e-5, three_keys 1.26e-5, four_keys_overshoot 5e-7, two_drivers 0 (20 쌍), 회전 60° / 65° — 1e-4 이내.
  - 여러 타깃 Point / Scale / Parent 위치 1e-4 (모두 0 = 같은 가중치 포함). 회전 차이 (slerp vs Maya nlerp) [U]:
    orient coaxial W1 = 3 0.259°, skew W1 = 3 0.532°, skew 같은 가중치 0, parent W1 = 3 회전 0.901°.
  - L1 `-r` / 절대 CV 월드 = Maya 표, FBX Export All 에 모양 오브젝트 없음.
- 관련 기존 헤드리스 (step62 · 76 · 199 · 102 · 138 · 101 · 54 · 166 · 208 · 216 · 217 · 223 · 169): 163 / 165, 실패 2 =
  `test_step169_deform` 두 개 (223 커밋부터 있던 실패, Release prep).
- GUI: `gui_step226_control_click` 4 / 4 (와이어 클릭 → Pose + joint1 리드, 원 안 빈 곳 = 조인트 안 고름),
  `gui_step226_colors` 5 / 5 (선택 안 된 커브 와이어 빨강 1210 px, 인덱스 18 = sRGB 값 쪽; 측정을 1 px 안티앨리어스
  선에 맞게 고침). 샷 확인.

## 남은 것

- 회전 섞기는 Blender slerp: 다른 가중치에서 Maya 와 최대 ~0.9° (parent). nlerp 흉내는 하지 않음 [U].
- Drawing Override 와 Wireframe Color 가 둘 다 있을 때 우선순위는 Maya 에서 재지 않음 [U, delegated: override 우선].
- SDK 창에서 blendShape / 컨스트레인트 값을 포즈할 때 msgbus 로 잡는 것은 GUI 미확인 (`docs/manual_checks.md`).
- Blender Custom Shape 는 본 그림을 대체 (Maya 는 조인트 구 + 커브 둘 다 보임) — 결정 1 대로.
