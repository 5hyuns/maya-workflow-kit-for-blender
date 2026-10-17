# Step 54 — Maya 워크플로우 기반: 단위 생성 경로·조명 세기·「Blender 에 없음」 안내

근거: `docs/PLAN.md` 「Maya 워크플로우 계획」 W3 (대체 + 안내, 공용 체계), W5 (Create 밖 생성 경로 → `maya_unit()`, 조명 × maya_unit²),
결정 8·10 (`docs/user_decisions.md`), `research/maya/workflows/rigging.md:63,100` (armature_add 1 BU), `fx.md:61-62,75-77,105`
(effector_add 1 BU Empty, quick_smoke 도메인 여유 1·1·2 BU, Gravity/Radial/Uniform 회색), `render.md:82-86,126,185-187` (light_add 10 W,
역제곱 미터, No Decay 없음).

## 계획

### (a) 생성 경로 (W5) — `operators/create.py` KINDS 로 모음 (delegated)
`maya_kit.create(kind)` 는 이미 원점·Maya 크기·Maya 이름 (step 10·21). 원시 연산자를 쓰던 항목을 KINDS 로 옮겨 같은 규칙을 탐:

| Maya 항목 | kind | Blender | 크기 (Maya 단위 × maya_unit) | 이름 |
|---|---|---|---|---|
| Skeleton > Create Joints, 셸프 Joint Tool | JOINT | `object.armature_add` | 본 길이 1 | 오브젝트 `skeleton1`, 본 `joint1`, 포즈 본 rotation XYZ (W1) |
| Create > Type, 셸프, 마킹 메뉴 | TEXT | `object.text_add` | 글자 크기 1 | `typeMesh1` |
| Create > Free Image Plane | IMAGE_PLANE | `object.empty_add(type='IMAGE')` (파일 창 없이, Maya 처럼 빈 평면) | 1 | `imagePlane1` |
| Fields/Solvers > Air / Drag / Gravity / Newton / Radial / Turbulence / Uniform / Vortex | FIELD_* | `object.effector_add` WIND / DRAG / WIND(아래로) / FORCE / FORCE / TURBULENCE / WIND(+X) / VORTEX | 표시 크기 1 | `airField1` … |
| Fluids > 3D Container, Effects > Fire / Smoke | — | `maya_kit.quick_smoke(style)` = `object.quick_smoke` 후 도메인 여유 (1,1,2)·Z 1 을 × maya_unit | 여유 × maya_unit | Blender 이름 |

- 조명: POINT/SPOT/AREA `energy` × maya_unit² (Blender 역제곱 감쇠가 미터 기준이라, Maya 단위 거리에서 m 장면과 같은 밝기), SUN 그대로
  (render.md:185-187). 정확한 렌더 측정은 남김.
- Gravity 필드: Blender 에 중력 필드가 없음 → 아래 (−Z = Maya −Y) 로 부는 WIND + 안내. Uniform = +X (Maya 기본 방향 (1,0,0)) WIND.

### (b) 공용 안내 (W3) — `ui/notices.py` (새)
- `NOTICES = {Maya 메뉴 경로: (대체, 한 줄 설명)}`. 회색 항목 (`maya_kit.menu_unavailable`) 과 대체가 있는 항목 (안내가 있으면
  `maya_kit.menu_item` 으로 그려 툴팁에 안내) 의 툴팁 = 「Maya: 항목 → Blender: 대체」 + 설명.
- Help Line: 툴팁이 만들어질 때 (`description`) 안내를 Help Line 에 올림 (`notices.show`, 5 s, 상태 표시줄 다시 그림). Maya Help Line 이
  메뉴 항목 설명을 보여 주는 것처럼.
- 문구 대상 (PLAN W3): Animation Layers → NLA, Character Sets → Keying Sets, Time Editor / Trax → NLA, Quick Select Sets → 컬렉션,
  Node Editor → 노드 연결 그래프 없음 (드라이버 / Shader Editor), Hypergraph → Outliner, Light Editor → (kit 목록 step 64), HumanIK /
  Quick Rig → Rigify, Namespace → `ns:` 이름 접두사, Reference → Link + Library Override, Set Project / Project Window → 상대 경로 `//`
  (kit 프로젝트 step 66), nucleus → 장면 중력·오브젝트별 설정, 조명 → 거리 제곱 감쇠, Gravity 필드 → 바람 필드. Texel Density 는 Maya
  메뉴 항목이 아님 (UV Toolkit) — step 63.

### (c) 검증
- 헤드리스 `test_step54_*`: 템플릿 (cm, 0.01) · Maya Units (1) · 팩토리 m (1) 세 단위에서 각 kind 크기 = Maya 값 × maya_unit, 조명 세기 =
  10 W × maya_unit², 이름; menu_map / shelf_map / 마킹 메뉴에 원시 생성 연산자가 남지 않음; NOTICES 키가 실제 메뉴 경로이고 각 항목
  툴팁에 안내.
- GUI (1.0·0.8): Create > Lights > Point Light → energy, Fields/Solvers > Gravity → 필드 크기, Windows > Animation Editors > Trax Editor 위에
  마우스 → 툴팁·Help Line 에 「NLA」 안내 (스크린샷).

## 실측
- `radius` 가 각 연산자에서 크기 하나를 정함 (헤드리스): `text_add` → `Curve.size`, `effector_add` / `empty_add` → `empty_display_size`,
  `armature_add` → 본 길이. 그래서 생성 후 따로 고칠 것 없이 `radius = 1 × maya_unit`.
- Blender 메뉴는 키보드로 항목을 골라도 툴팁이 뜨지 않음 (GUI 실측) → 안내는 마우스를 올렸을 때 (Maya 와 같음). 메뉴는 첫 항목이
  마우스 아래에 오도록 열리고 항목 간격 20 px × 배율 (스크린샷) — GUI 테스트가 이것으로 Trax Editor 위에 마우스를 둠.
- 상태 표시줄은 전역 영역이라 `screen.areas` 에 없음: Help Line 을 그릴 때 `context.area` 를 기억해 두고 안내가 바뀌면 그 영역을
  다시 그림 (`notices.remember_status_area`).

## 한 것
- `operators/create.py`: KINDS 에 JOINT (`skeleton1` + 본 `joint1`, 포즈 본 XYZ), TEXT (`typeMesh1`), IMAGE_PLANE (`imagePlane1`, 이미지
  빈 오브젝트, 정면), FIELD_AIR/DRAG/GRAVITY/NEWTON/RADIAL/TURBULENCE/UNIFORM/VORTEX (원점, 표시 크기 1 Maya 단위, Gravity = 아래로 부는
  바람, Uniform = +X 바람); POINT/SPOT/AREA 조명 `energy × maya_unit²` + 만들 때 보고에 감쇠 안내; `maya_kit.quick_smoke` (도메인 여유를
  Maya 단위로).
- `ui/menu_map.py`: Create > Type / Free Image Plane, Skeleton > Create Joints, Fields/Solvers 8 개 (Gravity / Radial / Uniform 새로),
  Fluids > 3D Container, Effects > Fire / Smoke 를 kit 경로로; 대체 매핑 Animation Layers → NLA, Hypergraph: Hierarchy → Outliner,
  Hypergraph: Connections → Drivers, Control > Create Character Set → Keying Set. `shelf_map` (Joint Tool, Type), 마킹 메뉴 Type.
- `ui/notices.py` (새): NOTICES 26 개 경로 (PLAN W3 + 조명 + Gravity 필드), 툴팁 (`menu_unavailable` / `menu_item`) + Help Line (5 s,
  ERROR 아이콘). 안내가 있고 대체가 연산자인 항목은 `maya_kit.menu_item` 으로 그림.
- `command_line`: Help Line 이 안내를 도구 도움말보다 먼저.
- 테스트: 새 `test_step54_units_notices` (6), `gui_step54_units_notices` (5).
- test_step21: 마킹 메뉴 생성 항목 목록에 Type 추가 (이제 maya_kit.create).

## 검증
- 헤드리스 **420/420** (전체 실행 419/420 → test_step21 기대값 고친 뒤 그 파일 8/8). test_step54 6/6: 세 단위 (템플릿 0.01, Maya Units 1,
  팩토리 1) 에서 본 길이·글자 크기·이미지 평면·필드 8 개 크기 = maya_unit, 이름, Gravity 아래·Uniform +X, 조명 10 W × maya_unit² (태양 1 W 그대로),
  smoke 도메인 = 반 크기 + (1,1,2) × maya_unit; 원시 생성 연산자 0; 안내 26 경로가 실제 메뉴 경로 + 툴팁에 문구.
- GUI 전체 **342/342** (`--ui-scale 0.8` = 실효 1.0) · **341/341** (1.25). gui_step54 5/5: Create > Lights > Point Light → pointLight1
  0.001 W (= 10 × 0.01²), Fields/Solvers > Gravity → gravityField1 0.01 BU, Trax Editor 위 마우스 → 툴팁 + Help Line 「Blender has no Trax:
  clips are actions laid out as NLA strips.」 (스크린샷 확인).
- dogfood **47/47** (콘솔 오류 0).

## 남은 것
- 조명 배율 (× maya_unit²) 은 계산 근거 (역제곱, 미터) — 렌더로 잰 것은 아님 (render.md:223 [U]).
- AE 라이트 Intensity 툴팁에 감쇠 안내는 못 넣음 (Blender 속성 툴팁은 바꿀 수 없음) — 메뉴 툴팁·Help Line·생성 보고에만.
- 안내는 메뉴에만: 셸프 버튼·마킹 메뉴 항목·핫박스에는 아직 없음. 회색 항목 대부분 (Character Set 나머지, Quick Select Set, Light Editor,
  Reference Editor, Namespace, HumanIK / Quick Rig) 은 안내만, 기능은 각 단계 (55 이후, 64 Light Editor, 66 Reference·Project, 63 Texel Density).
- Effects > Fire/Smoke 의 Mantaflow 해상도·시뮬 스케일·중력 (결정 10) 은 step 65. 필드 세기 (Maya magnitude) 는 그대로 Blender 기본.
- 수동 확인: `docs/manual_checks.md` 「Step 54」.
