# Step 85 — 매니퓰레이터 Ctrl+축 = 평면, Shift+MMB = 자동 축

재점검 5차 backlog 5 (docs/PLAN.md 「재점검 5차」 blindspot 4; step_28.md:60-61 「남은 것」 에서 빠진 것).

## 근거

- research/maya/interaction.md:104 [K]: Move 매니퓰레이터 축 핸들 **Ctrl+LMB** = 그 축에 수직인 평면이 활성 핸들이 되고 (나머지 두 축으로) 이동.
  :105 [K]: Scale 도 Ctrl+축 드래그 = 나머지 두 축 스케일. 가운데 핸들 Ctrl+클릭 = 축 고정 해제 (활성 핸들 = 가운데, 화면 평면 자유 이동).
- :106 [K]: **Shift+MMB 드래그** = 드래그 방향에 가장 가까운 축을 자동으로 고름.
- :103 [O] 활성 핸들은 기억되어 MMB 드래그가 그것을 쓴다 (step 28 `operators/manip.HANDLES`).
- kit: Move / Scale 툴의 매니퓰레이터 = `ui/manipulator.MAYAKIT_GGT_xform` (Python 기즈모, step 59), 키맵 "Generic Gizmo Maybe Drag"
  (`setup_keymap`), Rotate 는 Blender C 기즈모 그대로. MMB = 툴 키맵 ("3D View Tool: Move / Scale") 의 `maya_kit.manip_mmb` (step 28).
- Blender: 기즈모 키맵에서 부른 연산자는 `context.gizmo_group` 을 본다 (step 26); 하이라이트된 핸들 = `Gizmo.is_highlight`.
  IC "Transform Modal Map" 에서 Ctrl 누름 = SNAP_INV_ON (IC:3582) — Ctrl 을 누른 채 시작한 이동이 스냅을 뒤집는지 측정 필요.
  CLICK_DRAG 로 부른 transform 은 그 버튼 놓기로 확정 (release_confirm; launch event = 버튼).

## 계획

1. **Ctrl+LMB** (`maya_kit.manip_ctrl`, GIZMO_KEYMAPS LEFTMOUSE PRESS Ctrl 맨 앞, PASS_THROUGH_FIRST):
   - `context.gizmo_group` 이 kit 그룹이고 하이라이트된 핸들이 축 (ARROW / SCALE_AXIS) 이면: 활성 핸들 = 나머지 두 축 (`HANDLES[kind]`,
     평면 핸들이 노랗게) 으로 정하고 `transform.translate / resize(constraint_axis=나머지 두 축, orient_type=슬롯 축, release_confirm)` 를
     invoke → 끌면 평면 이동 / 두 축 스케일.
   - Move 가운데 핸들이면 활성 핸들 = 가운데 (축 고정 해제), 이동 없음, FINISHED (기즈모 트윅 안 함).
   - 그 밖 (평면 핸들, Scale 가운데, 다른 그룹) = PASS_THROUGH.
   - 핸들이 어느 축인지: `MAYAKIT_GT_maya_handle` 에 `handle_axis` 슬롯 (빌드 때 저장).
   - Ctrl 을 누른 채 끄는 동안 Blender 스냅 반전이 켜지면 (측정) Maya 와 다르다 → 측정 결과에 따라 `snap=False` 로 막거나 문서에.
2. **Shift+MMB** (`maya_kit.manip_mmb_auto`, MMB_TOOLS 의 Move / Scale 툴 키맵):
   - Shift+MMB PRESS = 누른 자리 기록 + PASS_THROUGH, Shift+MMB CLICK_DRAG = 누른 자리 → 지금 자리 방향과 화면에 투영한 각 축 방향의
     |cos| 가 가장 큰 축 (`pick_axis`, 순수 함수) 으로 `transform.*(constraint_axis=그 축, orient_type=슬롯 축, release_confirm)` invoke
     (CLICK_DRAG 의 launch event = MMB → MMB 놓기로 확정).
   - 축 = 매니퓰레이터와 같은 곳·같은 방향 (`manipulator.pivot_frame(context, kind)`: 중심, 축 행렬, 방향 이름). 화면에서 거의 점인 축
     (보는 방향) 은 고르지 않음. 활성 핸들은 바꾸지 않음 (delegated: 한 번 드래그용).
   - Rotate 툴은 C 기즈모 + Maya 근거 없음 → 안 함.
3. 키맵 충돌: Ctrl+LMB 는 기즈모 키맵 (하이라이트된 기즈모 위에서만), 맨 앞 + PASS_THROUGH. Shift+MMB 는 툴 키맵 (3D View 에 Shift+MMB
   항목 없음, IC 3D View pan = Alt+MMB). 변환 중 Shift+MMB = AUTOCONSTRAINPLANE (모달 맵) 은 그대로.
4. 다음 단계 고려: 86 (Dope Sheet / NLA / Node 수식) 과 겹치지 않음. 87 (Alt+A 등 뷰 키) 무관.

## 검증 계획

- 헤드리스 `tests/test_step85_manip_ctrl.py`: `pick_axis` (각 방향, 보는 방향 축 제외, 동률), `plane_of(axis)`, 키맵 항목 / PASS_THROUGH_FIRST,
  manip_ctrl 이 gizmo_group 없으면 PASS_THROUGH.
- GUI `tests/gui/gui_step85_manip_ctrl.py`: W 툴, X 화살표 위 Ctrl+LMB 드래그 → X 그대로, Y/Z 바뀜 (YZ 평면), 활성 핸들 = YZ 평면,
  가운데 Ctrl+클릭 = 활성 핸들 해제, Shift+MMB 오른쪽 드래그 (앞 뷰) = X 축만, 위로 = Z 축만, Scale 툴 Ctrl+X = Y/Z 스케일, 스크린샷.
- 전체 헤드리스·GUI, dogfood, manual_checks.

## 한 것

- `operators/manip.py`: `plane_of`, `pick_axis` (순수), `MAYAKIT_OT_manip_ctrl` (Ctrl+LMB: 하이라이트된 kit 핸들의 역할·축을 보고 축 =
  나머지 두 축 transform + 활성 핸들, Move 가운데 = 활성 핸들 해제, 그 밖 PASS_THROUGH), `axis_dirs`, `MAYAKIT_OT_manip_mmb_auto`
  (Shift+MMB PRESS → 짧은 모달: 6 px × 배율 움직이면 그 방향에 가까운 축으로 transform invoke).
- `ui/manipulator.py`: 핸들 기즈모에 `handle_role` / `handle_axis` 슬롯, `pivot_frame(context, kind)` (중심·축·방향 이름).
- `keymap/maya_patches.py` 41 `patch_manip_ctrl`: GIZMO_KEYMAPS Ctrl+LMB PRESS 맨 앞 (PASS_THROUGH_FIRST), Move / Scale 툴 키맵 Shift+MMB PRESS.
- **측정**:
  - Ctrl 을 누른 채 시작해 끈 이동은 스냅이 켜지지 않았다 (YZ 이동 −5.645 / 7.388 cm, 증분 아님) — IC 의 SNAP_INV_ON 은 변환 중 Ctrl
    누름 이벤트에만 반응. `snap=False` 같은 우회는 필요 없었다.
  - 시뮬레이션에서 Shift+MMB CLICK_DRAG 키맵 항목은 한 번도 불리지 않았다 (PRESS 는 옴) → 계획의 CLICK_DRAG 대신 PRESS + 모달.
  - 모달 안 MOUSEMOVE 에서 부른 transform (release_confirm) 도 MMB 놓기로 확정됐다 (놓은 뒤 window.modal_operators 비어 있음).
  - 같은 틱에 몰아 보낸 움직임은 새 transform 이 보지 못함 (CLAUDE.md step 28 함정과 같음) → GUI 테스트는 첫 움직임과 나머지를 다른 틱에.
- 판단 (delegated): Shift+MMB 는 활성 핸들을 바꾸지 않음; Rotate (C 기즈모) 는 안 함; Scale 가운데 Ctrl+클릭 = Blender 그대로 (균일).

## 검증

- 헤드리스 `tests/test_step85_manip_ctrl.py` 5/5: plane_of (= 매니퓰레이터 평면 핸들), pick_axis (방향·반대 방향·보는 방향 축 제외·0),
  키맵 (기즈모 키맵 첫 Ctrl+LMB, Move / Scale 툴 Shift+MMB, Rotate 없음), 기즈모 없으면 통과, 슬롯.
- GUI `tests/gui/gui_step85_manip_ctrl.py` 7/7 (MayaKit 템플릿): Ctrl+X 화살표 드래그 = X 0, Y −5.645, Z 7.388 cm + 활성 핸들 YZ, 가운데
  Ctrl+클릭 = 해제 + 안 움직임, 앞 뷰 Shift+MMB 옆 = X 만 / 위 = Z 만, Scale Ctrl+X = (1, 1.649, 1.649). 스크린샷
  `gui_step85_active_yz.png` 에서 YZ 평면 핸들이 노랗게.
- 전체: 헤드리스 667/667 (처음 666/667 — step 28 테스트가 기즈모 키맵 첫 항목과 MMB 목록을 고정하고 있어 Ctrl / Shift 항목을 빼고 보게
  고침, 단독 4/4), GUI (기본 배율) 601/601, dogfood 47/47 (콘솔 0). `docs/manual_checks.md` 「Step 85」 4 항목.

## 남은 것

- Maya 실행으로 Ctrl 동작 (가운데 Ctrl+클릭 = 해제, Scale 가운데 Ctrl) 과 Shift+MMB 판정 각도를 확인하지 않음 ([K]); 손 확인 항목.
- Rotate 툴 (C 기즈모): Ctrl+링 = Blender 스냅 그대로, Shift+MMB 자동 축 없음.
- 실제 마우스의 Shift+MMB CLICK_DRAG 는 시험하지 않음 (PRESS + 모달이라 무관).
- 다음: 86 Dope Sheet · NLA · Node Editor 선택 수식.

