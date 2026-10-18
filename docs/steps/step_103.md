# Step 103 — Real option boxes for the top commands, Maya look

backlog 5 (docs/PLAN.md 「재점검 7차」 5): step_98.md #11; quant §0 (진짜 옵션 창 6 / 500, 죽은 상자 323).

## 계획

근거: Maya 2022 GUI 에서 옵션 창 26 개를 열어 찍고 위젯을 읽음 (`research/maya/re/option_boxes.md`,
`research/scripts/maya_options103/`).

1. **모양 측정 먼저** — Maya 의 □ 는 줄 오른쪽 끝. Blender 메뉴 한 줄에 두 번째 버튼을 넣으면 계단이 된다는 step 51
   측정을 다시 확인: GUI 프로브 (`row` + 오른쪽 정렬, `split`, `column().row()`, `grid_flow`). 홀로 있는 줄은 멀쩡하지만
   **연속된 줄은 모두 계단** (Edit Mesh 실제 메뉴 스크린샷으로도 확인) → 과제의 대안: 버튼 하나 유지 (누르고 있기 =
   Option Box), 왼쪽 「창」 아이콘과 Blender 말투 ("Press and hold: Option Box") 를 없애고 라벨 끝에 Maya 의 상자 기호
   「❒」 (delegated).
2. **옵션 창 틀** (`operators/option_windows.py`) — Window 명세 (제목, 명령 버튼, 필드: Maya 라벨·기본값, 실행 함수,
   Blender 에 없는 필드 목록) 에서 연산자 `maya_kit.opt_<key>` 를 만들어 `invoke_props_dialog` 로 연다: 확인 버튼 =
   Maya 명령 버튼 ("Create", "Bevel", "Add" …), Blender 의 Cancel = Close, 창 안 위쪽 Save Settings / Reset Settings, 아래쪽
   Apply (토글 버튼의 update 콜백이 바로 실행하고 되돌아감: 창이 열린 채). 값은 Maya optionVar 처럼 실행할 때 저장 (애드온
   설정 `option_settings` JSON) 되고, 그 뒤 메뉴 클릭·마킹 메뉴·셸프도 저장값으로 실행 (`marking/modal.run_action`).
   Blender 에 없는 Maya 필드는 회색 「Not in Blender:」 목록.
3. **창 26 개**: 폴리곤 기본형 6, Duplicate Special, Group, Freeze, Reset, Combine, Smooth, Extrude, Bevel, Bridge, Merge,
   Bind Skin, Parent / Point / Orient 제약, Set Key, Bake Simulation (두 메뉴), UV Planar / Automatic, New Scene, Save Scene.
   (기존 Mirror, Playblast, Set, Orient / Mirror Joints, Soften/Harden, 파일 대화상자 5 개는 그대로.) Triangulate 는 Maya 에
   옵션 상자가 없음 (menus.json); Unfold / Layout 은 kit Maya UV 메뉴에 없는 항목.
4. **빈 상자 없애기** — 매핑된 옵션 상자는 모두 창 / 대화상자 / 툴 설정 / 실행 후 설정 (Adjust Last Operation) 중
   하나를 연다 (`menu_sets.option_kind`). Blender 연산자에 설정이 하나도 없으면 (`generic`) 「Maya 의 설정이 Blender 에
   없음」 을 말하고 명령을 실행하는 창 `maya_kit.option_generic`.

## 한 것

- 위 1–4. `create.create(..., overrides=)` (기본형 옵션), 애드온 설정 `option_settings`, 큐브 분할 = 축 방향 모서리를
  잘라 (UV 유지), Maya Axis X / Z = 메시 회전, Maya Y-up → Blender 좌표 (Duplicate Special 이동·회전, 제약 축).
- 결정 (delegated): 객체 선택에서 Extrude / Bevel / Bridge / Merge / Automatic 창은 모든 컴포넌트에 (step 101 측정과 같은
  규칙); Smooth 창 = Subdivision Surface 모디파이어 (kit 의 Mesh > Smooth 와 같음); Automatic Planes → Smart UV
  Project 각도 (3 = 89° … 12 = 45°); Close 버튼 글자는 Blender 의 Cancel (props dialog 에서 바꿀 수 없음).

## 검증

- 헤드리스 `tests/test_step103_option_windows.py` 10/10: 매핑된 옵션 상자 전부가 무엇인가를 엶 (window 29, dialog 19,
  redo 144, tool 14, generic 50, menu 1, 빈 것 0), 서로 다른 진짜 옵션 창 **38** 개 (≥ 30), Maya 기본값, 상자 기호 /
  왼쪽 아이콘 없음, 기본형 크기·분할·축, 저장값으로 메뉴 클릭 / Reset, 편집 명령 (Bevel, Extrude, Smooth, Duplicate
  Special ×3, Reset), Combine 피벗 + Merge, 제약 축·가중치·Maintain offset, UV Planar / Automatic, Set Key Below, Bake,
  Apply / Save / Reset 토글. 전체 헤드리스 757/757, GUI 1031/1031 (manual sweep 의 Render 메뉴 라벨 비교에 ❒ 제거 반영).
- GUI `tests/gui/gui_step103_option_windows.py` 4/4 + 스크린샷: Edit Mesh 메뉴 (계단 없음, 라벨 끝 ❒), Polygon Primitives,
  옵션 창 3 개. Maya 와 나란히: `research/maya/screens/step103/{poly_cube,bevel,parent_constraint}_maya_vs_kit.png`.

## 남은 것

- □ 를 줄 오른쪽 끝의 따로 누르는 상자로 만들 수 없음 (Blender 메뉴 계단, 측정). 지금은 누르고 있기.
- Maya 창의 Edit > As Tool / As Action, Help 없음. 창 크기 고정 (Maya 는 크기 조절).
- 창에 없는 Maya 필드 (회색 목록) — Normalize / Cap divisions / Taper / Twist 등. 다음 후보: Extrude Taper / Twist (kit
  extrude 에 추가), Cone height divisions.
- 아직 Adjust Last Operation 인 옵션 상자 144 개 (Blender 설정은 보이지만 Maya 라벨이 아님).
