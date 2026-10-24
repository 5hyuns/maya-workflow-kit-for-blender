# Step 175 — Repeat Last for Maya commands (G)

Audit 12 blindspot BS1 (step_173_remaining.md §4): Maya G = repeat the last command, including menu / shelf / marking-menu
items (research/maya/interaction.md:207). The kit's G was Blender's `screen.repeat_last`, and everything
`marking/modal.run_action` runs is never registered (undo_steps.py:4-6, step 147).

## 계획

0. 헤드리스 확인 (임시 탐침): 키로 Sphere 를 만들고 (등록됨) 메뉴 Mesh > Combine (run_action) 뒤 `wm.operators[-1]` 은 여전히
   Sphere, `screen.repeat_last` = Sphere 를 하나 더 만든다 — 결함 확인됨.
1. Maya GUI 측정 (`research/scripts/maya_repeat175/`): 메뉴 항목 · 셸프 버튼 · 옵션 창 Apply 뒤 `repeatLast -q -cnl / -cl`, Edit >
   Repeat 라벨 (`editMenuUpdate`: `Repeat "<cnl>"`), 스크립트로 부른 MEL 은 기록되지 않음 → `research/maya/re/repeat_175.md`.
2. `operators/repeat_maya.py`: 킷 기록 = (라벨, 메뉴 동작, 경로, 기록 순간의 마지막 등록 연산자). G = `allset.repeat_last`:
   기록 뒤에 Maya 가 반복하는 종류의 Blender 연산자가 등록되지 않았으면 기록을 `run_action` 으로 다시 실행 (옵션 창 명령은 저장된
   값), 아니면 그 Blender 연산자를 다시 실행 (`screen.repeat_history`). 선택 · 변형 · 뷰 · undo 연산자는 Maya 의 repeatLast 에 들어가지
   않으므로 건너뜀 (delegated, [I]). 기록 지점: `run_action` (메뉴 · 셸프 · 마킹 · MTK), 옵션 창 명령 / Apply.
3. Edit > Repeat 라벨 = `Repeat "<라벨>"` (menu_sets 동적 라벨), Edit > Recent Commands List · 핫박스 Recent Commands = 킷 메뉴
   (킷 기록 + Blender 연산자, 최신 먼저, 누르면 다시 실행), Shift+G 도 같은 반복.
4. undo: G 한 번 = undo step 하나 (run_action 의 command push 또는 Blender 반복의 undo=True).

## 한 것

- 측정: Maya 는 UI 로 실행한 메뉴 항목 · 옵션 창 Apply 를 repeatLast 에 넣고 G 가 그것을 다시 실행, 스크립트로 부른 MEL 은 안 넣음,
  Edit > Repeat = `Repeat "<명령>"` (`research/maya/re/repeat_175.md`). Combine / Delete / 셸프는 Qt 로 실행되지 않아 [U].
- `operators/repeat_maya.py`: `record` (킷 명령: 라벨 · 동작 · 경로 · 기록 순간 Blender 의 마지막 등록 연산자), `last` (킷 기록 뒤에
  반복할 만한 Blender 연산자가 등록됐으면 그것, 아니면 킷 기록 — 선택 · 변형 · 뷰 · undo · UI 연산자는 건너뜀), `repeat`,
  `recent`, `allset.repeat_last` (REGISTER · UNDO 없음: 반복된 명령이 undo step 을 만듦), `allset.repeat_item`,
  `ALLSET_MT_recent_commands`.
- 기록 지점: `marking/modal.run_action` 의 바깥 호출 (메뉴 · 셸프 · 마킹 · MTK; option=True 는 제외 — 창이 실행할 때 기록),
  옵션 창 명령 / Apply (`option_windows._record`, 경로가 없는 창은 MAP 에서 거꾸로 찾음).
- 키: Screen G = `allset.repeat_last` (IC `screen.repeat_last` 제거, Graph Editor / Grease Pencil 편집 G 는 그대로 — shadows), mapping
  RepeatLast IC → KIT. Shift+G (`repeat_at_mouse`) 도 같은 반복 (UNDO 연산자 안이라 `undo_steps.nested`). Edit > Repeat 라벨 =
  `menu_sets._dynamic_label`, Edit > Recent Commands List · 핫박스 Recent Commands = `ALLSET_MT_recent_commands`.

## 검증

- 헤드리스 `test_step175_repeat.py` **8 / 8**: 메뉴 Cube → G = pCube2, Combine → G 가 새 선택을 합침, 선택 연산자는 건너뛰고 키
  연산자 (구 생성) 가 더 새것이면 그것, G 한 번 = Ctrl+Z 한 번, 옵션 창 명령 기록, 마킹 항목 + Recent Commands, 키맵 / 메뉴.
  전체 **1611 / 1611** (keymap 그림자 테스트에 Graph Editor / Grease Pencil G 를 적은 뒤).
- GUI `gui_step175_repeat.py` **5 / 5** (메뉴 Cube → 실제 G 키 = pCube2, 라벨 `Repeat "Cube"`, Ctrl+D 뒤 G = 복제), Edit 메뉴
  스크린샷 `Repeat "Duplicate"  G` 확인. 관련 GUI step78 / step52 / step101 / step108 + manual sweep (m78 · m35 · m97) 통과.
- 헤드리스 탐침 (계획 0) 으로 고치기 전 결함 확인: 메뉴 Combine 뒤 `screen.repeat_last` = 그 전 키 명령 (Sphere).

## 남은 것

- 라벨이 Maya 의 runtime 명령 이름 ("CreatePolygonCube") 대신 메뉴 이름 ("Cube") — 이름 표가 배포 데이터에 없음 (delegated).
- Recent Commands List 는 Maya 창이 아니라 하위 메뉴.
- Maya 에서 Combine / 셸프 버튼 / 마킹 메뉴 기록은 직접 못 잼 (메뉴 항목 규칙으로 추정).
