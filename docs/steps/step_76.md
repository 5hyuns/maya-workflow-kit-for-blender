# Step 76 — 선택 우선순위 (핸들·조인트·커브가 메시보다 먼저)

재점검 4차 blindspot 1 (docs/PLAN.md 「재점검 4차」), backlog 항목 5.

## 근거

- Maya 클릭 선택은 겹친 후보 중 **타입 우선순위**가 가장 높은 것을 고른다 (`selectPrefPriorityMode "animation"`,
  `ignoreSelectionPriority false`) — research/maya/interaction.md:74, research/maya/defaults.json:92,97,105
  (PREF:753,759,779-847).
- 팩토리 표 (PREF:781-847, 오브젝트 모드에 해당하는 것): handle 10, ikHandle 10, joint 9, nurbsCurve 4, curveOnSurface 3,
  그 밖 (polymesh, nurbsSurface, light, camera, locator, lattice, cluster, particle, field, imagePlane …) 모두 2.
- Blender `view3d.select` (오브젝트 모드) 은 GPU 깊이 픽 + 반복 클릭 순환이라 메시 앞/뒤의 컨트롤 커브·아마추어를 눌러도
  메시가 잡힐 수 있다.
- `clickBoxSize 4` (PREF:756, defaults.json:95) = 커서 둘레 선택 상자.

## 계획

1. **연산자** `maya_kit.select_priority` (`operators/select_priority.py`). 오브젝트 모드 클릭 선택 앞에서:
   - 오브젝트 모드가 아니거나, 환경설정 「Selection Priority」 (Maya `ignoreSelectionPriority false` = 기본 켬) 가 꺼져 있거나,
     Tool Box 기둥 3D View (`ui/toolbox.is_toolbox`) 면 PASS_THROUGH.
   - 클릭 반경 안의 **우선순위 > 2 후보만** 찾는다. 메시 등 2 는 Blender 픽과 같은 층이라 찾지 않는다 — 후보가 없으면
     PASS_THROUGH 로 `view3d.select` 가 평소대로 (순환 포함) 고른다.
   - 있으면 (우선순위 큰 것, 화면 거리 가까운 것, 이름) 순으로 하나 골라 Maya 수식대로 선택하고 FINISHED (언두 한 단계).
2. **우선순위 표** (`PRIORITY`, kit 개념 대응):
   - ikHandle 10 = IK 제약의 목표 오브젝트 (아마추어 아님) — kit 의 `ikHandleN` 엠프티 (step 58 `skin.create_ik`), 이름이 아니라
     「IK 목표」 로 판단 (이름을 바꿔도, Blender 식으로 만든 IK 목표도 같은 뜻).
   - joint 9 = 아마추어 오브젝트 (오브젝트 모드에서 본을 누르면 아마추어가 잡힘; step 55 의 조인트 = 포즈 본).
   - nurbsCurve 4 = `CURVE` 오브젝트. (curveOnSurface 3 은 Blender 에 없음.) 텍스트·서피스·엠프티 (locator)·라이트·카메라는 Maya 대로 2.
   - Maya 「handle」 (Selection Handle 표시) 은 kit 에 없음 — 표에만 남김.
3. **맞힘 판정** (화면 거리, 깊이 무시 = Maya 우선순위는 가려진 것도 고른다):
   - 커브: 평가된 커브의 `to_mesh()` 엣지 (베벨이면 표면 엣지) 를 투영, 선분 거리 ≤ r.
   - 아마추어: 보이는 포즈 본마다 head→tail 선분, 거리 ≤ r + 0.1 × 화면 길이 (팔면체 본의 두께) . 숨긴 본·모든 컬렉션이
     숨은 본은 뺀다.
   - IK 목표 엠프티: 원점에서 ±로컬 축 × `empty_display_size` 선분 (PLAIN_AXES 모양 그대로; 다른 모양은 근사).
   - r = 5 px × UI 배율 [I]: `clickBoxSize 4` 상자 (반폭 4) 의 반대각 ≈ 5.7 을 반올림하지 않고 5 로.
   - 보이는 것만: `visible_get(viewport=space)` (로컬 뷰·뷰포트 숨김 포함), `hide_select`, 뷰의 타입별 선택 가능
     (`show_object_select_<type>`).
   - 투영·선분 거리는 `operators/preselect.project` / `segment_distance` 재사용; 순수 함수 `rank()` 는 bpy 없이 테스트.
4. **수식** (research/maya/interaction.md:68-71, step 2 와 같음): 없음 = 나머지 해제 후 선택 + lead (active), Shift = 토글,
   Ctrl = 해제, Ctrl+Shift = 추가.
5. **키맵 충돌**: 같은 이벤트 앞에 `first=True`, `PASS_THROUGH_FIRST` 등록:
   - "3D View" LEFTMOUSE CLICK × (없음, Shift, Ctrl, Ctrl+Shift) — `view3d.select` 앞 (step 49 `toolbox_guard` 와 같은 자리;
     둘 다 PASS_THROUGH 라 순서 무관, 그래도 이 연산자는 Tool Box 에서 스스로 빠진다).
   - "3D View Tool: Tweak" LEFTMOUSE PRESS × 4 — Tweak 툴의 `view3d.select` 앞. 드래그 이동은 CLICK_DRAG 항목이라 그대로.
   - Shift+Alt / Ctrl+Shift+Alt (Blender enumerate 목록) 는 건드리지 않는다.
   - 기즈모 (매니퓰레이터·프리셀렉트) 는 키맵보다 먼저라 영향 없음. 편집·포즈 모드는 PASS_THROUGH.
6. **다음 단계 고려**: 77 (편집 모드 Insert/D) 은 다른 이벤트·모드라 겹치지 않음. 78 키 묶음, 79 3D Cut and Sew 도 무관.

판단 (delegated): 우선순위 2 층은 Blender 에 맡김 (반복 클릭 순환 유지), 반경 5 px, IK 목표 = ikHandle,
엠프티 (locator) 는 Maya 대로 2.

## 검증 계획

- 헤드리스 `tests/test_step76_select_priority.py`: `rank()` 정렬 (우선순위 > 거리 > 이름, 반경 밖 제외), `priority()` 표
  (IK 목표 엠프티 10, 아마추어 9, 커브 4, 메시·엠프티·라이트 2), 키맵 항목이 `view3d.select` 앞에 있고 PASS_THROUGH_FIRST 에 있음,
  배경 오버라이드로 메시 앞 커브 클릭 → 커브 / 후보 없음 → PASS_THROUGH / 수식 4가지.
- GUI `tests/gui/gui_step76_select_priority.py`: 메시 앞 (그리고 뒤) 커브 클릭 → 커브, Shift → 토글 추가, Ctrl → 해제,
  아마추어 본 클릭 → 아마추어, 빈 곳 클릭 → 평소, 메시만 클릭 → 메시. 스크린샷 확인.
- 전체 헤드리스·GUI, dogfood. 조작감은 `docs/manual_checks.md`.

## 한 것

- `operators/select_priority.py` — `maya_kit.select_priority` (계획 1–4 그대로). 순수 함수 `priority` / `rank` / `bone_width` /
  `segments_hit`, 장면 쪽 `ik_targets` / `hits` / `apply`. 투영·선분 거리는 `preselect.project` / `segment_distance`.
  본 두께는 팔면체처럼 0.1 지점이 가장 두껍고 양 끝에서 0 (계획의 「0.1 × 길이」 를 균일 대신 가늘어지게 — delegated).
- 키맵 `maya_patches.patch_select_priority` (`SELECT_PRIORITY_ITEMS`: "3D View" CLICK, "3D View Tool: Tweak" PRESS × 4 수식,
  `first=True`, `PASS_THROUGH_FIRST`). `tests/test_keymap_maya.py` 그림자 검사 스택에 Tweak 툴 키맵 추가.
- 환경설정 「Selection Priority」 (기본 켬, Maya `ignoreSelectionPriority false`).
- `docs/manual_checks.md` step 76 4 항목, CLAUDE.md 한 줄, PLAN 재점검 4차 항목 5 = 완료.

## 검증

- 헤드리스 `tests/test_step76_select_priority.py` 8/8: 우선순위 표, 정렬, 키맵 순서, 메시 앞·뒤 커브, 반경 (3 px 맞음 / 8 px 아님),
  본 두께 (두꺼운 쪽 10 px 맞음, 가는 끝 아님), IK 핸들 > 본 > 커브, 숨김·선택 불가·숨긴 본·IK 아닌 엠프티 (2) 제외, 수식 4가지.
- GUI `tests/gui/gui_step76_select_priority.py` 12/12: 메시 앞 커브 클릭 → 커브 (lead), 메시만 → 메시, Shift 토글 켬/끔,
  Ctrl+Shift 추가 (두 번째도 유지), Ctrl 해제, 메시 뒤 가려진 커브 → 커브, 옵션 끔 → Blender 깊이 픽 = 메시, 메시 앞 본 → 아마추어.
  스크린샷 (front / behind / joint) 직접 확인.
- 전체: 헤드리스 612/612 (첫 실행 611/612 — Tweak 키맵이 그림자 검사 스택에 없어서; 추가 후 test_keymap_maya 12/12),
  GUI (기본 배율) 528/528, dogfood 47/47 (콘솔 오류 0).

## 남은 것

- Tweak 툴에서 커브를 눌러 바로 드래그 (PRESS 를 이 연산자가 먹은 뒤 CLICK_DRAG 이동) 는 manual_checks 로만.
- Maya 「handle」 (Selection Handle 표시) 10, curveOnSurface 3 은 Blender 대응이 없어 표에만.
- 편집·포즈 모드의 컴포넌트·본 우선순위 (Maya 표에서 컴포넌트는 모두 2) 는 손대지 않음.
- 엠프티 모양은 축 선분으로 근사 (PLAIN_AXES 외 모양의 테두리 클릭은 덜 맞을 수 있음).
