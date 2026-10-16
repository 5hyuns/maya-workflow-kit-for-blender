# Step 21 — 생성 경로 단위 통일 (backlog 7, blindspot B2)

## 계획

### 문제

decision 1 기본(m 유지 + cm 표시)에서 Create/셸프 `pCube1` 은 1 BU (Channel Box "100 cm"), 커맨드 라인
`cmds.polyCube()` 는 1 cm (`command_line/cmds_shim.py:424-429`, `linear_factor`) — 같은 이름의 두 큐브가 100배 차이.
마킹 메뉴 Shift+RMB Create(`marking/menus.py` SHIFT_DEFAULT)는 Blender 연산자를 그대로 불러 2 BU 큐브에 Blender 이름.

### 근거

- Maya 길이는 "현재 linear unit" 으로 입력·표시되고 기본은 cm (research/maya/defaults.json:10, 내부 단위도 cm :13).
  Channel Box 의 1 = 1 cm. 기본 큐브 1×1×1, 카메라 클립 0.1 / 10000 (defaults.json:45-46).
- Maya FBX(UnitScaleFactor 1 = cm)를 Blender 로 가져오면 `global_scale = UnitScaleFactor / (100 · scale_length)`
  (`$S\addons_core\io_scene_fbx\import_fbx.py:3133-3135`, `fbx_utils.py:216-217`):
  - 기본(scale_length 1): Maya 1 cm 큐브 → 0.01 BU, 표시 "1 cm".
  - Maya Units(scale_length 0.01): → 1 BU, 표시 "1 cm".
  즉 임포터는 두 모드 모두 "Maya 1 단위 = 표시 1 cm".
- research/blender/api_limits.md:78: m 유지 + cm 표시에서는 수치가 Maya 와 100배 다르다 (step 10 이 받아들인 차이).

### 규칙 (delegated)

**Maya 길이 1 = 씬 표시 길이 단위 1** (Maya 의 current linear unit 과 같은 뜻). BU 로는
`k = units.maya_unit(scene)` = 표시 단위의 미터 값 / `scale_length` (`system == 'NONE'` 이면 1).

| 씬 | k | Create 큐브 | 표시 | Maya FBX 큐브 |
|---|---|---|---|---|
| MayaKit 템플릿 (m + cm, decision 1) | 0.01 | 0.01 BU | 1 cm | 0.01 BU |
| Maya Units 켬 (cm, scale 0.01) | 1 | 1 BU | 1 cm | 1 BU |
| 팩토리 씬 (m 표시) | 1 | 1 BU | 1 m | 0.01 BU |

팩토리 씬에서는 Maya 의 working unit 을 m 로 바꾼 것과 같다 (Maya 도 단위를 m 로 바꾸면 polyCube 기본이 1 m [K]).
step 10 「계획」 7 의 "1 Maya 단위 = 1 BU" 를 대체한다. 버린 대안: cmds 를 1 BU 로 → Channel Box 의 "100 cm" 와
`getAttr` 1 이 어긋나고 FBX 와 100배 차이.

### 구현

1. `operators/units.py`: `maya_unit(scene)` (cmds_shim 의 `linear_factor` 를 옮김, cmds_shim 은 그것을 씀).
   Maya 뷰 값은 Maya 단위로: 클립 0.1 / 10000, persp 카메라 Maya (28, 21, 28) [K] → Blender (28, −28, 21).
   `apply_file(rescale_views)`: 클립 = Maya 값 × k_new; 새 파일(load_post)에서는 뷰 거리·위치에 k_new / k_old 를 곱해
   템플릿 뷰가 같은 cm 장면을 본다 (팩토리 홈 파일은 k 가 1 → 1 이라 그대로). 비율은 백업에 넣고 restore 가 되돌림.
2. `operators/create.py`: 길이 속성(size, radius, depth, radius1/2, major/minor_radius)에 k 를 곱한다. 로케이터·빈 그룹
   `radius` = k, 카메라 표시 크기 k + 클립 0.1k / 10000k, 라이트는 Blender 기본 길이(shadow_soft_size, area size) × k.
   커브 툴(CV / Bezier)도 `maya_kit.create` 종류로 (`curve1` / `bezier1`, 반지름 k).
3. 마킹 메뉴 SHIFT_DEFAULT Create 항목 → `maya_kit.create` (Maya 이름·크기).
4. `menu_map` / `shelf_map`: 이미 `_create`; 커브 툴 두 개를 새 종류로.
5. `framing.py` MIN_HALF (점 하나 프레이밍 반폭 0.5) 도 Maya 단위 × k.
6. `tools/make_startup.py`: 템플릿 3D 뷰 클립 0.001 / 100 m (= Maya 0.1 / 10000 cm), persp 뷰 = Maya 기본 카메라 위치.
   startup.blend 재생성.
7. 문서: `docs/user_decisions.md` 결정 8, README 「단위」 절 (한국어·English).

### 검증

- 헤드리스 `tests/test_step21_units.py`: 템플릿 단위 / Maya Units 켬 / 팩토리 m 세 경우에서 create 큐브·구·원기둥·평면과
  `cmds.polyCube/polySphere/polyCylinder/polyPlane` dimensions 같음; 마킹 메뉴 Create 항목이 `maya_kit.create`;
  Blender FBX 왕복(UnitScaleFactor 1 = Maya cm 파일)으로 임포트 크기 = Create 크기; Maya Units 껐다 켜기 왕복 복원.
- GUI: 템플릿에서 Create 큐브 + cmds 큐브, Channel Box·AE 스크린샷 ("1 cm").
- 전체 헤드리스·GUI·dogfood.

## 한 것

- `operators/units.py`: `maya_unit(scene)` (BU per Maya length = 표시 단위의 미터 값 / `scale_length`), `CLIP` (Maya 0.1 / 10000),
  `clip(scene)`. `apply_file(rescale_views)`: 3D 뷰 클립 = Maya 값 × k; 새 파일(load_post)은 뷰 거리·위치에 k_new / k_old 를 곱하고
  비율을 백업(`view_scale`)에 넣어 `restore_file` 이 되돌림. `cmds_shim.linear_factor` 는 이것을 부른다.
- `operators/create.py`: 길이 속성(`LENGTHS`)에 k 를 곱함. 로케이터·빈 그룹 `radius` = k, 카메라 표시 크기 k + 클립 0.1k / 10000k,
  라이트 `shadow_soft_size`·area `size` × k. 새 종류 `CV_CURVE` (`curve1`) / `BEZIER_CURVE` (`bezier1`).
- `operators/group.py`: Ctrl+G 그룹 Empty 표시 크기 = 1 Maya 단위 (실측: 1 BU 축이 view_all 을 100 cm 로 늘려 릴리스 스크린샷에서
  물체가 점이 됨).
- 마킹 메뉴 Shift+RMB Create(`SHIFT_DEFAULT`) 10항목 → `maya_kit.create` (이전엔 Blender 연산자 그대로: 2 BU 큐브, `Cube` 이름).
  메뉴 Create > Curve Tools 와 셸프 EP/Bezier 커브 → `maya_kit.create`.
- `operators/framing.py`: 점 하나 프레이밍 반폭 `min_half` = 0.5 Maya 단위 (view.py 가 k 를 곱해 넘김).
- `tools/make_startup.py` `maya_views()`: 템플릿의 모든 워크스페이스 3D 뷰 = Maya persp (28, 21, 28 cm → 거리 0.4482 BU), 클립
  0.001 / 100 m. startup.blend 재생성.
- `tools/release_shots.py` 물체 위치를 Maya 단위로, `tools/dogfood_session.py` 거리 출력 자릿수. `docs/screenshots/` 재생성 (구도 동일).
- 문서: `docs/user_decisions.md` 결정 8, README 「단위」/「Units」 절, step_10 「계획」 7 에 대체 표시, PLAN 「재점검 1차」 4 완료,
  manual_checks Step 21.

### 계획과 다르게 된 것 / 실측으로 바뀐 것

- 템플릿에는 General 외에도 팩토리 워크스페이스(Modeling, Animation …)의 3D 뷰가 남아 있어 모두 Maya 뷰로 맞춤.
- `scale_length` 가 float32 라 Maya Units 에서 k = 1.0000000224 (테스트 허용 오차 1e-6).
- Ctrl+G 그룹 Empty 크기는 계획에 없었음 (릴리스 스크린샷으로 발견).

## 검증

- 헤드리스 `python tests/run.py`: **235/235** (21 파일, 새 `test_step21_units.py` 8개: 세 단위 모드에서 create = cmds 크기
  (큐브·구·원기둥·평면), 템플릿 큐브 "1 cm" + `cmds.move(5)` = 5 cm, 로케이터·그룹·카메라·커브·area 라이트 크기, 모든 생성 경로가
  `maya_kit.create`, 마킹 메뉴 Cube 실행, FBX 왕복(UnitScaleFactor 1 파일 = Maya cm)이 템플릿·Maya Units 둘 다 Create 크기와 같음,
  템플릿 뷰 Maya persp/클립 + Maya Units 켜고 끌 때 뷰 스케일 왕복).
- GUI `python tests/gui/run.py`: **162/162** (15 파일, 새 `gui_step21_units.py` 6개). 스크린샷 `--shots tmp/shots21`:
  `gui_step21_channel_box.png` (pCube2 Translate X "2 cm", 셸프 큐브·cmds 큐브가 Maya persp 에 같은 크기),
  `gui_step21_attribute_editor.png` (transform 탭 Translate "2 c" — 3열 칸이 좁아 잘림, 기존 표시).
- `python tools/dogfood.py`: **46/47** (이전과 같음, 남은 실패 `=` 매니퓰레이터 크기), 콘솔 오류 0.
- `python tools/release_check.py`: build·validate·설치·활성화 PASS, 스크린샷 7장 재생성 (01_layout 구도 이전과 동일 확인).

## 남은 것

- `object.text_add` (Create > Type, 셸프 Type) 는 Blender 기본 크기 1 BU 그대로 (Maya Type 은 별도 노드 체계라 대응 미정).
- 라이트 세기(W)는 물리 단위라 스케일하지 않음 — cm 크기 장면에서 Maya 라이트 intensity 1 과의 대응은 미정.
- Blender 뷰포트 렌즈 화각이 Maya persp 35 mm 와 같은지 미확인 (manual_checks Step 21).
- AE transform 탭 3열 길이 필드가 좁아 "2 c" 로 잘림 (기존 문제, 이번 범위 밖).
- 그리드: Maya gridSize 12 / spacing 5 (defaults.json:29-31) 는 맞추지 않음 (Blender 그리드는 단위 단계를 따름).
