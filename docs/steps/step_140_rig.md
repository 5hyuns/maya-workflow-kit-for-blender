# Step 140 — 레인 RIG: 리깅 · 스킨 · 블렌드 셰이프 · 컨스트레인트 옵션 창 (#32, #35 Aim / Pole Vector)

근거: `research/maya/re/option_boxes_140.md` (Maya 2022 공장 값, 샷 `research/maya/screens/options140/`). 계획 ·
설계는 `docs/steps/step_140.md`.

## 한 일

`src/allset/operators/option_windows_rig.py` `WINDOWS` (11 창, 키 → 경로):

| 키 | 제목 / 버튼 | 경로 | 실제로 하는 필드 |
|---|---|---|---|
| `joint_tool` | Joint Tool / Create Joints | Skeleton/Create Joints | Secondary Axis (X 금지 · Y · Z · None), Secondary Axis World Orientation X/Y/Z + / −, Create IK handle + IK 설정 |
| `ik_handle_tool` | IK Handle Tool / Create IK Handle | Skeleton/Create IK Handle | Current solver (RP / SC), Solver enable, Weight |
| `ik_spline_tool` | IK Spline Handle Tool | Skeleton/Create IK Spline Handle | Root on curve (off = Spline IK Chain Offset) |
| `bind_skin_maya` | Bind Skin Options / Apply and Close | Skin/Bind Skin | Bind to, Skinning method, Normalize weights, Max influences, Remove unused influences, Colorize skeleton |
| `unbind_skin` | Detach Skin Options / Detach | Skin/Unbind Skin | History Delete / Keep / Bake, Remove joint colors |
| `copy_skin_weights` | Copy Skin Weights Options / Copy | Skin/Copy Skin Weights | Surface Association 3 종, Influence Association 1–3, Normalize |
| `paint_skin_weights` | Paint Skin Weights Tool | Skin/Paint Skin Weights | Paint operation, Profile, Normalize, Opacity, Value, Radius(U), Screen projection, Show wireframe, XRay Joints |
| `blend_shape` | Blend Shape Options / Create | Deform/Blend Shape | BlendShape node (Key 이름, 비면 blendShapeN), Origin Local / World, Check topology, Delete targets |
| `aim_constraint` | Aim Constraint Options / Add | Constrain/Aim | Aim vector, Up vector, World up type (Scene up / Vector / None), World up vector (0 1 0 만), Weight |
| `pole_vector` | Pole Vector Constraint Options / Add | Constrain/Pole Vector | Weight (1 만) |
| `scale_constraint` | Scale Constraint Options / Add | Constrain/Scale | Maintain offset, Offset, Constraint axes, Weight |

연산자 쪽: `joints.ALLSET_OT_joint_tool` 에 Maya 속성 + `orient_new` (bone Z = Maya Y, bone X = Maya Z 를 월드 방향으로
`align_roll`) + Create IK handle (첫 joint → 마지막 joint, `skin.create_ik`) + 스크립트용 `points` (클릭 없이 execute);
`rig_maya.ALLSET_OT_ik_spline_handle.root_on_curve`; `rig_tools.ALLSET_OT_blend_shape` 의 node_name / origin /
check_topology / delete_targets. bf15718 에서 이미 된 것 (aim, IK solver, bind / unbind / copy / paint 속성) 은 검토 후 유지.

## 위임한 결정 (delegated)

- 도구 창 제목 = Maya Tool Settings 의 도구 이름 ("Joint Tool" 등, "Options" 로 안 끝남). 버튼 = 도구 시작.
- Blender 가 못 하는 필드는 `missing` 줄로만: Joint 의 Degrees of freedom / Symmetry / Scale compensate / Orient Joint
  to World / Primary Axis / Bone Radius, IK 의 Autopriority / Snap / Sticky / Priority / POWeight, Aim 의 Maintain offset ·
  Offset · Constraint axes · Object up 계열, Blend Shape 의 Envelope · In-between, Bind 의 Bind method 등.
- Aim World up vector 는 (0,1,0) 만 받음 (Track To 의 up 은 월드 Z 고정) — 다른 값은 Maya 식 경고 문장으로 거절.
- Pole Vector Weight: Blender IK pole 에 가중치가 없음 → 1 이 아니면 거절 (창은 Maya 처럼 Weight 한 줄).
- Scale constraint Offset / Maintain offset: Copy Scale `use_offset` 은 자기 scale 을 곱하므로 owner 의 scale 채널을
  offset 값 (Maintain offset = owner / target) 으로 둔다. 기본값 (1 1 1, off) 은 아무것도 안 바꿈.
- SC solver = IK `use_rotation` (핸들이 끝 joint 방향으로 시작) — 근사.
- Joint Tool 기본 (Secondary Y, +Y) 은 이제 평범한 클릭에도 roll 을 맞춘다 (Maya yup).
- IK Spline "Root on curve" off = Blender Chain Offset (근사).
- Set / Assume Preferred Angle, Add Influence, Blend Shape > Add 창은 캡처에 없어 (option_boxes_140.md) 만들지 않음.

## 검증

- `python tests/run.py -k step140_rig`: 15/15 (창 · 경로 · 필드 / 기본값, Aim +X / up Z, World up None = Damped Track,
  IK RP / SC, Pole weight, Joint orientation + Create IK, Unbind keep / delete, Copy weights 옵션, Paint 설정, Blend
  Shape 옵션, 저장 값으로 평범한 클릭).
- 지정 묶음 (step103, 58, 62, 110, 101, enable_disable, step140_option_count, step57): `test_step103 ::
  test_windows_registered_with_maya_titles_and_buttons` 만 실패 — 도구 창 제목이 "Options" 로 안 끝남 (메인이
  테스트를 고쳐야 함, 이 레인 파일 아님).

- 전체 `python tests/run.py`: 1170 통과 / 5 실패 — step103 제목 검사 (위), worktree 에 `research/` 가 없어서 3 개
  (test_keymap_maya, step107, step108), step56 copy/paste/cut (EDIT 레인의 time_keys WIP, bf15718).
- 옵션 상자 수 (test_step140_option_count 결과): window 29 → 40, generic 65 → 56, redo 148 → 146, dead 231 그대로
  (dead = 매핑 안 된 경로; 이 레인의 경로는 이미 매핑돼 있었음). Window spec 26 → 37.

## 남은 것

- 병합 때 메인: `option_windows.py` 의 옛 `bind_skin` Window 삭제 (안 지우면 `find(action)` 마킹 메뉴 / 셸프가 옛 창),
  `test_step103` 의 `bind_skin` 기본값 줄 → `bind_skin_maya`, 제목 검사에 도구 창 허용.
- GUI 샷 (메인).
