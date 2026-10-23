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

진행 기록: 첫 RIG / EDIT 레인은 백그라운드로 띄웠다가 20:08 에 중단 (메인이 알림만 기다림 — 같은 실패 세 번째). 두 worktree 변경을
WIP 커밋 bf15718 로 살리고, 같은 범위를 포그라운드 동기 레인 2 개로 끝냈다 (상세: `step_140_rig.md`, `step_140_edit.md`).

## 한 일

- Maya 2022 GUI 캡처 26 창 / Tool Settings (`research/maya/re/option_boxes_140.md`, 샷 `research/maya/screens/options140/`),
  mayapy 결과 측정 (`research/maya/re/option_boxes_140_edit.md`).
- 새 Maya 창 26 개 (Window spec 26 → 50): RIG 11 (`option_windows_rig.py`: Joint Tool, IK Handle Tool, IK Spline Handle
  Tool, Bind Skin (모든 필드), Detach Skin, Copy Skin Weights, Paint Skin Weights Tool, Blend Shape, Aim / Pole Vector / Scale
  Constraint), EDIT 15 (`option_windows_edit.py`: Delete / Cut / Copy / Paste / Scale / Snap Keys 를 Key 와 Edit > Keys 둘 다,
  Parent / Unparent / Ungroup, Duplicate Special (+ Smart transform), Connect Components / Connect Tool, Polygon Circularize,
  Make Hole Tool, Insert Edge Loop Tool). 옛 `bind_skin` / `duplicate_special` spec 은 삭제 (새 창이 대신).
- 연산자에 Maya 옵션을 실제 속성으로: Joint Tool 방향 · Create IK handle, IK solver RP / SC, Bind normalize / remove unused /
  colorize, Unbind history, Copy weights association, Paint 도구 설정, Blend Shape node / origin / topology, 키 명령 범위
  (`time_keys.KeyScope`: Objects / Hierarchy / Channels / Driven / Shapes / Time range) · Paste method · Scale / Snap Keys,
  Parent Preserve position, Circularize · Connect · Make Hole 옵션.
- **Aim = Maya**: 창 · 평범한 메뉴 클릭 모두 로컬 +X 가 대상, 로컬 +Z (Maya Y) 가 월드 위 (Track To track X / up Z), World up
  None = Damped Track (`rig_tools.aim`).
- Key > Scale Keys (dead 2) 를 살림. `tools/menu_count.py --options` (옵션 상자 분류, 헤드리스 Blender 로 `test_step140_option_count`).
- 옵션 창 그리기: 라벨 없는 enum (Maya 의 옆 콤보, Joint Tool " + ") 은 값 열의 드롭다운 — 펼친 버튼은 빈 막대 두 줄로 그려졌다
  (GUI 샷에서 발견).

## 검증

| | window | dialog | tool | redo | generic | dead | Window spec |
|---|---|---|---|---|---|---|---|
| 시작 (aef175f) | 29 | 19 | 14 | 148 | 65 | 231 | 26 |
| 끝 | **60** | 19 | 13 | 138 | **47** | **229** | **50** |

- 헤드리스 전체 `python tests/run.py`: **1191 / 1191** (146 파일; step140_rig 15, step140_edit 16 — 창마다 경로 = window,
  필드 · 라벨 · 기본값 = Maya, 기본값 / 바꾼 값으로 실행한 결과 = Maya 또는 mayapy 숫자).
- `python tools/menu_count.py`: 고유 경로 1318, 작동 587 → 589 (44.7 %), 알림 없는 회색 0.
- GUI `tests/gui/gui_step140_option_windows.py` 9/9, 샷 3 장 직접 확인 (`research/maya/screens/step140/`: Joint Tool,
  Delete Keys Options, Aim Constraint Options — Maya 캡처와 필드 순서 · 기본값 같음, Maya 에 없는 필드는 "Not in Blender" 회색).
- GUI 전체 (`tests/gui/run.py`, 127 파일): 한 번 돌림 — 1 시간 상한에서 116 파일까지 1343 PASS, 실패 2 파일. 나머지 12 파일은
  `-k` 로 이어 돌려 110 / 110. 실패 재실행: `gui_step63_mtk` 혼자 13 / 13 (전체 묶음에서만 나는 흔들림),
  `gui_step75_input_line` 은 결과 없이 시간 초과 — step 140 전 커밋 aef175f 에서도 똑같이 멈춤 (회귀 아님, 이 PC 환경:
  `wm.clipboard` 를 쓰는 테스트, 원인 미확인 → 남은 것).

## 남은 것

- Maya 에만 있는 필드는 창에 회색 줄 (`missing`) — 목록은 레인 문서.
- 근사: IK SC solver (핸들 회전 복사), IK Spline Root on curve = Chain Offset, Connect edge flow (구 하나로 맞춘 Hermite),
  Connect 도구 Slide 방향 (여러 면 링), Paste Replace + Current 의 범위, Insert 의 offset 미측정.
- 창 없음 (캡처에 필드 없음): Set / Assume Preferred Angle, Add Influence, Blend Shape > Add. Paste Fit / Scale clipboard
  adjustment.
- Graph Editor 안의 Key 명령은 Channel Box 노드 기준 (Maya 는 Graph Editor 선택 키) — 141 이후 후보.
- dead 229 는 대부분 Blender 에 없는 기능 (Asset, Convert Subdiv, Sculpt Target, Wire 등) — 이번 범위 밖.
- 손 확인: `docs/manual_checks.md` 「Step 140」.
- `gui_step75_input_line` 이 aef175f 에서도 결과 없이 멈춤 — 시스템 클립보드 의심, 다음 단계에서 확인.
