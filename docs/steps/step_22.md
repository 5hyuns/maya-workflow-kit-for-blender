# Step 22 — 매니퓰레이터 Shift+드래그 = 복제 (backlog 8, blindspot B4)

## 계획

### Maya 동작

- 오브젝트에서 Move/Rotate/Scale 매니퓰레이터를 Shift+드래그 = **Smart Duplicate**: 선택을 복제하고 사본을 변환,
  원본은 제자리. 면/엣지에서는 **Smart Extrude**. 기본 켬 (`manipSmartDuplicate 1`, `manipSmartExtrude 1`,
  research/maya/interaction.md:107, PREF:371-374). 동작 세부는 [K].
- W/E/R 홀드 메뉴의 "Smart Duplicate" / "Smart Extrude" 는 이 옵션 토글 (marking/menus.py OPT_MOVE/ROTATE/SCALE, 지금 회색).
- 지금 Blender: 기즈모의 `gizmogroup.gizmo_tweak` 은 Shift 와 상관없이 실행되고 (`any_except("alt")`,
  `$S\presets\keyconfig\keymap_data\blender_default.py:500-503`, IC `industry_compatible_data.py:3713-3721`), 변환 모달에서
  Shift 는 정밀 모드 (`PRECISION` LEFT/RIGHT_SHIFT, IC:3611-3612) → 원본이 느리게 움직임 (step_14 B4).

### 경로 후보

| | 방법 | 장점 | 단점 |
|---|---|---|---|
| (a) | Maya 키컨피그의 기즈모 키맵 `Generic Gizmo Maybe Drag` (xform 기즈모가 쓰는 키맵) 맨 앞에 Shift+LMB CLICK_DRAG → `maya_kit.manip_duplicate` (PASS_THROUGH_FIRST). 복제(`maya_kit.duplicate`, step 19 이름 규칙)만 하고 PASS_THROUGH → 같은 이벤트로 다음 항목 `gizmo_tweak` 이 강조된 기즈모의 transform 을 실행 → 선택(= 사본)이 움직임 | C 기즈모 그대로 (축 강조·스냅·방향·편집 모드 지원 유지). 코드 작음 | 기즈모 핸들러가 PASS_THROUGH 후 같은 키맵 다음 항목을 계속 보는지, 사용자 키컨피그의 기즈모 키맵이 쓰이는지 실측 필요. 같은 키맵을 쓰는 다른 기즈모(라이트 등)에도 걸릴 수 있음 → 툴 조건으로 거름 |
| (b) | 킷 Move/Rotate/Scale 툴 + 자체 GizmoGroup (`target_set_operator`, api_limits.md:62-65 W) | 완전 제어 (Maya 중앙 사각형 등) | 기즈모 전체 재구현, 편집 모드·방향·스냅 표시 재검증, 일이 큼 |

**선택 (delegated): (a)**. 실측에서 막히면 (b) 로. GizmoGroup 은 매니퓰레이터 모양 자체를 Maya 처럼 바꾸는 별도 단계에서.

### 설계

1. `operators/manip.py` `MAYAKIT_OT_manip_duplicate` (`maya_kit.manip_duplicate`): 조건이 맞으면 `duplicate.duplicate(context)`
   후 `{'PASS_THROUGH'}`; 아니면 아무것도 안 하고 `{'PASS_THROUGH'}`. 조건: 오브젝트 모드, 선택 있음, 환경설정
   `smart_duplicate` (기본 켬), 오브젝트 모드 활성 툴이 move/rotate/scale/transform 이거나 3D 뷰의 오브젝트 기즈모
   (`show_gizmo_object_translate/rotate/scale`) 가 켜짐. 편집 모드(압출)는 다음 단계라 지금은 그냥 통과 → Blender 기본.
2. 키맵 (maya_patches 21): `Generic Gizmo Maybe Drag` 와 `Generic Gizmo Drag` 맨 앞에 Shift+LMB →
   `maya_kit.manip_duplicate`. PASS_THROUGH_FIRST 에 추가. (실측으로 CLICK_DRAG → **PRESS**: 아래 「한 것」)
3. 정밀 모드 대체 키 (delegated): 처음 안은 Transform Modal Map 의 `PRECISION` (Shift) 를 **Alt** 로 옮기는 것.
   (실측으로 바뀜: 아래 「한 것」 — Shift 정밀은 그대로 둔다.)
4. 언두: 복제와 변환이 한 언두 단계 (중첩 호출은 언두를 따로 쌓지 않음). 드래그를 RMB/Esc 로 취소하면 사본은 제자리에 남는다
   (Maya 도 복제는 남음 [K]) — manual_checks 에서 확인.
5. W/E/R 홀드 메뉴 "Smart Duplicate" → 환경설정 토글 (`maya_kit.manip_option`). "Smart Extrude" 는 압출 구현 때 연결.
6. 압출 (다음): 편집 모드 면/엣지에서 같은 키맵 항목이 `mesh.extrude_region` (이동 없이) 후 PASS_THROUGH → 기즈모가 새 면을
   변환. 회전/스케일 기즈모도 같은 방식.

### 검증

- 헤드리스: 키컨피그에 항목이 있고 gizmo_tweak 앞, Transform Modal Map 의 PRECISION = Alt, Shift PRECISION 없음; 연산자 조건별
  복제/통과 (오브젝트 모드·선택 없음·옵션 끔·편집 모드).
- GUI: 이동 툴 + 기즈모 X 화살표 위에서 Shift+LMB 드래그 → 오브젝트 2개, 사본이 X 로 이동, 원본 제자리, 이름 pCube2;
  Shift 없이 드래그 → 1개 그대로 이동; 회전 기즈모 Shift+드래그 → 사본 회전.
- manual_checks: 손 감각 (Shift 를 누른 채 계속 드래그해도 느려지지 않음, Alt 정밀, 취소 시 사본).

## 한 것

- `operators/manip.py`: `maya_kit.manip_duplicate` (조건이 맞으면 `duplicate.duplicate` = step 19 의 Maya 이름 복제, 항상
  PASS_THROUGH), `maya_kit.manip_option` (W/E/R 홀드 메뉴의 Smart Duplicate 토글). 환경설정 `smart_duplicate` (기본 켬, Scene
  Concepts 상자).
- 키맵 patch 21 (`maya_patches.patch_manip_duplicate`): `Generic Gizmo Maybe Drag`, `Generic Gizmo Drag` 맨 앞에 Shift+LMB **PRESS**.
  `PASS_THROUGH_FIRST` 에 추가, shadowing 테스트 스택에 기즈모 키맵 추가.
- `marking/menus.py`: OPT_MOVE / OPT_ROTATE / OPT_SCALE 의 "Smart Duplicate" 연결 ("Smart Extrude" 는 회색 그대로).
- `tests/gui/run.py`: 환경 변수 `MAYA_KIT_GUI_ARGS` 로 Blender 인자 추가 (`--debug-handlers` 로 기즈모 키맵 매칭을 본다).

### 계획과 다르게 된 것 / 실측으로 바뀐 것

- **CLICK_DRAG → PRESS**: `--debug-handlers` 로 보니 xform 기즈모는 Shift+LMB **PRESS** 에서 이미 `gizmogroup.gizmo_tweak` 이
  매칭돼 모달을 시작한다 (Maya 키컨피그 항목은 CLICK_DRAG shift=0 인데도). CLICK_DRAG 항목은 차례가 오지 않아 연산자가 불리지
  않았다. PRESS 항목을 맨 앞에 두니 매칭 → PASS_THROUGH → 같은 PRESS 로 gizmo_tweak (로그 `item matched
  'MAYA_KIT_OT_manip_duplicate'` 다음 `'GIZMOGROUP_OT_gizmo_tweak'`). 결과: 누르는 순간 복제 — 드래그 없이 Shift+클릭만 해도
  제자리 사본이 생긴다 (manual_checks 에서 Maya 와 비교).
- **정밀 모드 대체 키 = 없음 (Shift 그대로)**: 실측에서 Shift 를 누른 채 시작한 드래그는 정밀 모드가 아니다 (사본 1.758 vs
  Shift 없는 드래그 2.137 같은 80 px, 정밀이면 약 0.2). Blender 정밀은 드래그 **도중** Shift 를 누를 때만 켜진다. 또 Alt 는
  Transform Modal Map 에서 노드 에디터 `NODE_ATTACH_ON/OFF` (IC:3607-3608) 가 먼저 쓰고 모달 키맵은 처음 맞는 항목만 쓰므로 Alt 로
  옮기면 충돌. 그래서 Transform Modal Map 은 바꾸지 않는다 (delegated). 테스트가 Shift PRECISION 이 남아 있음을 확인.
- 언두: 복제 + 변환이 한 단계 (GUI 테스트: Ctrl+Z 한 번에 사본이 사라짐).

## 검증

- 헤드리스 `python tests/run.py`: **239/239** (22 파일, 새 `test_step22_manip.py` 4개: 기즈모 키맵 맨 앞 항목·PASS_THROUGH_FIRST,
  Shift PRECISION 유지, 조건별 복제/통과 (오브젝트 모드·옵션 끔·선택 없음·편집 모드·기즈모 없음), 홀드 메뉴 토글).
- GUI `python tests/gui/run.py`: **172/172** (16 파일, 새 `gui_step22_manip_duplicate.py` 10개: Move 툴 X 화살표 일반 드래그 =
  원본 X 이동; Shift+드래그 = pCube2 / pCubeShape2 생성, 원본 제자리, 사본 X 이동 (정밀 아님), 사본만 선택·활성;
  Rotate 기즈모 Shift+드래그 = 사본 회전, 원본 회전 그대로; Ctrl+Z 한 번에 사본 제거). 스크린샷 `tmp/shots22/gui_step22_shift_drag.png`
  (드래그 중: 사본이 X 축으로, 원본 제자리, 헤더 "D: 1.758 m").
- `python tools/dogfood.py`: **46/47** (이전과 같음, 남은 실패 `=`), 콘솔 오류 0.

## 남은 것

- **Smart Extrude (다음 단계)**: 편집 모드 면/엣지에서 같은 키맵 항목이 압출 (`mesh.extrude_region`, 이동 없이) 후 PASS_THROUGH →
  기즈모가 새 면을 변환. "Smart Extrude" 홀드 메뉴 항목·환경설정도 그때.
- Shift+클릭(드래그 없음)도 복제됨 — Maya 와 다르면 드래그가 시작되지 않은 경우 사본을 지우는 처리 필요 (manual_checks).
- 드래그를 RMB/Esc 로 취소하면 사본이 제자리에 남는다 (Maya 비교 필요).
- 같은 기즈모 키맵을 쓰는 다른 기즈모(라이트 크기·스포트 등)는 툴 조건(이동/회전/스케일/변환 툴 또는 오브젝트 기즈모 표시)으로만
  거른다 — 그 기즈모를 Shift+드래그하면 복제될 수 있다.
- Shift+D (Duplicate with Transform, step 10) 의 "마지막 오프셋 반복" 과 이 복제의 연결 (Maya smartTransform) 은 안 함.
