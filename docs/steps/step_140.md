# Step 140 — 일상 옵션 창 (#32 #33 #35)

`step_133_quant.md` gap 2 (점수 12): Maya 옵션 상자 507 개 중 231 개 죽음, 62 개는 "Blender has no settings" 창. 이번 단계는
매일 쓰는 명령의 상자를 Maya 2022 옵션 창 (필드 · 공장 기본값 그대로) 으로 바꾼다.

## 계획

### 시작 수치 (`python tools/menu_count.py --options`, 새 도구 · 이번 단계)

| | window | dialog | tool | redo | generic | dead | Window spec |
|---|---|---|---|---|---|---|---|
| 시작 (aef175f) | 29 | 19 | 14 | 148 | 65 | 231 | 26 |

(step 133 의 "window 48" 은 dialog 를 함께 센 값 — 같은 분류 함수 `ui/menu_sets.option_kind`, 지금 dialog 19 + window 29 = 48.)

### 대상 (사용자 지시 순서)

Create Joints, Create IK Handle, Bind Skin (빠진 필드), Paint Skin Weights, Parent, Delete / Cut / Copy / Paste Keys, Scale Keys
(지금 회색 = dead 2), Blend Shape, Connect, Circularize, Insert Edge Loop, Duplicate Special 재확인, Aim / Pole Vector (Aim 은 Maya 처럼
+X 를 대상으로, 월드 up Y). 같은 묶음이라 함께: IK Spline, Set / Assume Preferred Angle, Unbind / Copy Skin Weights, Add Influence,
Scale constraint, Unparent / Ungroup, Snap Keys, Make Hole.

### 레인 (병렬; 파일 단위로 나눔)

| 레인 | 내용 | 파일 (그 레인만) |
|---|---|---|
| CAPTURE (Maya GUI 1 개) | Maya 2022 창 · Tool Settings 의 라벨 · 공장 기본값 · 도구 컨텍스트 기본값, Aim 기본 벡터 | `research/scripts/maya_options140/`, `research/maya/screens/options140/`, `research/maya/re/option_boxes_140.md` |
| RIG (worktree) | #32 + Aim / Pole Vector / Scale constraint + Blend Shape | `operators/option_windows_rig.py`, `operators/joints.py`, `skin.py`, `rig_maya.py`, `rig_tools.py`, `ui/paint_weights.py`, `tests/test_step140_rig.py` |
| EDIT (worktree) | #33 / #35: Parent / Unparent / Ungroup, Key 명령 (Scale Keys 새로), Connect, Circularize, Make Hole, Insert Edge Loop, Duplicate Special | `operators/option_windows_edit.py`, `time_keys.py`, `graph_keys.py`, `parenting.py`, `poly_maya.py`, `duplicate.py`, `ui/mesh_tools.py`, `tests/test_step140_edit.py` |
| 메인 | 골격 (`option_windows._extend`, 개수 테스트 `tests/test_step140_option_count.py`, `menu_count.py --options`), 병합, `ui/menu_map.py` · `notices.py` 충돌 정리, GUI 샷 3 창, 문서 · 커밋 | 공유 파일 |

순서가 필요한 것 (한 줄 이유): 구현 레인은 CAPTURE 결과 (필드 순서 · 기본값) 를 받은 뒤 시작 — 기본값이 테스트의 기준값이라서.
부하 제한 (PC 10-23 에 세 번 꺼짐): Maya 1 + Blender 최대 2 — 구현 레인 2 개는 각자 worktree 의 `tmp/` 에서 헤드리스만, GUI 샷은 메인이 병합 뒤.

### 설계 (delegated)

- 창 = step 103 의 `Window` 그대로 (`invoke_props_dialog`, Apply / Save / Reset, 값 저장 → 이후 평범한 클릭도 그 값으로). 새 창은
  `option_windows_rig.py` / `option_windows_edit.py` 에 두고 `option_windows._extend()` 가 목록에 붙인다 (두 레인이 같은 파일을 안 고침).
- Maya 에서 상자가 Tool Settings 를 여는 도구 (Create Joints, Create IK Handle, IK Spline, Paint Skin Weights, Insert Edge Loop) 도 같은
  `Window` 로: 제목 = Maya Tool Settings 의 도구 이름, 확인 버튼 = 도구 시작 (그 값으로). Maya 처럼 값은 도구에 남는다 (저장 → 메뉴 클릭도
  그 값으로 도구 시작). 킷 도구가 창 모달 (Joint / IK) 이라 Blender Tool Settings 패널에 붙일 곳이 없다.
- 필드는 연산자 속성으로 (Maya 이름 · 기본값), Blender 에 대응 없는 필드는 `missing` (회색 한 줄) — 거짓 필드 금지.
- Aim: Maya aimConstraint 기본 aimVector (1,0,0), upVector (0,1,0), worldUpType Vector, worldUpVector (0,1,0) — Maya Y-up 축을
  Blender 로 (X→X, Y→Z, Z→−Y, CLAUDE.md step 57) 바꿔 Track To (track +X, up Z) 로. 지금 `_con('TRACK_TO')` 는 −Z 대상 / up Y (step 133 R2).
- Scale Keys: 범위 안 키의 시간 / 값을 pivot 기준으로 늘리는 킷 연산자 (Graph Editor 밖에서도 — Channel Box 노드 기준, step 56 규칙).
