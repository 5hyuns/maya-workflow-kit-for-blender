# Step 82 — Outliner 드래그 = Maya 부모 지정

재점검 5차 backlog 2 (docs/PLAN.md 「재점검 5차」 우선순위 2, research/README.md 대응표 90행 Outliner Partial).

## 근거

- Maya Outliner (research/maya/ui_layout.md:258-264): 기본 `showDagOnly 1`, 정렬 없음 (DAG = 만든 순서).
- [K] Maya Outliner 드래그 (Autodesk 도움말에서 문장 근거를 찾지 못함 — Maya 2022 사용 지식):
  - **MMB 드래그** 를 다른 항목 **위에** 놓기 = 그 항목의 자식으로 (`parent`, 월드 위치 유지 = P 와 같음,
    research/maya/concepts.md:98-101, defaults.json `parentPreserve 1`).
  - 두 항목 **사이에** 놓기 = 그 자리로 순서 바꾸기 (그 자리의 부모 아래로 옮김 포함).
  - **빈 곳에** 놓기 = 월드로 (Unparent, 위치 유지).
  - 드래그는 선택을 바꾸지 않는다. 선택된 항목을 끌면 선택 전부, 선택 안 된 항목을 끌면 그것 하나.
  - Alt+MMB = Outliner 패닝 (Autodesk Outliner 도움말 "To pan in the Outliner Alt + middle-click").
- treeView MEL 문서: "re-ordering / re-parenting operations can be performed with the middle mouse button" (pymel treeView,
  Maya UI 의 같은 규칙).

### Blender 4.5 측정 (GUI 이벤트 시뮬레이션, MayaKit 레이아웃의 Outliner, 임시 probe)

- LMB 드래그 → 항목 위 드롭 = `OUTLINER_OT_parent_drop` (wm.operators 에 등록됨). 결과는 **Blender 부모 지정**:
  parent inverse = 부모 월드 역행렬, 로컬 값은 그대로 (Channel Box 숫자가 Maya 와 다름 — 결정 2 위반).
- LMB 드래그 → 빈 곳 드롭 = `OUTLINER_OT_parent_clear` (Shift 없이도), 월드 위치 유지.
- MMB 드래그 = 아무 일 없음 (WM 드래그는 LMB 놓기에서만 드롭; MMB 는 View2D `scroller_activate` 만, 스크롤바 밖이면 통과).
- IC "View2D" Alt+MMB = `view2d.pan` — Maya 패닝과 이미 같음.
- `outliner.item_activate('INVOKE_DEFAULT', deselect_all=True)` 를 Outliner 오버라이드로 부르면 커서 아래 행이 선택되고
  `context.selected_ids` 로 그 ID 를 읽을 수 있다 (빈 곳 = 빈 목록). Python 에서 C 트리를 맞혀 볼 유일한 방법.
- 템플릿 Outliner 는 `use_sort_alpha = True` (Blender 기본) → 순서 바꾸기는 보이지 않는다.
- **정렬을 끈 Outliner 의 순서 (구현 중 측정, 킷 없이 팩토리 Blender 에서도 같음)**: 목록마다 **첫 항목이 맨 뒤에** 그려진다.
  Z, Y, X 순서로 링크 → Y, X, Z. 컬렉션 행이 없으면 view layer base 목록 전체 (Z Y X Q P M → Y X Q P M Z), 컬렉션 행이 있으면
  컬렉션마다. 그래서 정렬을 끄면 처음 만든 pCube1 이 맨 아래에 나온다 — Maya (만든 순서) 와 더 멀어진다.

## 계획

1. **LMB 드래그 (Blender 드래그) 결과를 Maya 방식으로** (`operators/outliner_drag.py`):
   - `depsgraph_update_post` 핸들러가 `wm.operators[-1]` 이 새로 `OUTLINER_OT_parent_drop` / `parent_clear` 가 된 것을 보면
     (환경설정 Parent Mode = Maya, 오브젝트 모드) 타이머 한 번을 건다.
   - 타이머: 드롭 뒤 상태 (오브젝트별 부모, 선택, active) 기록 → `ed.undo` (드롭 전) → 바뀐 오브젝트만
     `parenting.parent_maya` / `unparent` 를 `maya_kit.outliner_reparent` (undo=True) 로 → 언두 한 단계 「Parent」, 드롭 결과의 선택 복원.
     드롭 단계는 redo 에서 사라진다 (언두 두 번이 필요 없게).
   - 본 부모 (`parent_type != 'OBJECT'`, 아마추어 본 행에 놓기) 는 건드리지 않는다 (Maya 조인트 부모 지정은 step 57 P 로).
   - 언두가 꺼져 있으면 (undo_steps 0) 그 자리에서 선택된 오브젝트의 parent inverse 만 identity 로 바꾼다 (월드 유지).
2. **MMB 드래그 = Maya 드래그** (`maya_kit.outliner_drag`, "Outliner" MIDDLEMOUSE PRESS; View2D 의 MMB `scroller_activate`
   는 스크롤바 밖에서 통과하므로 shadows=("View2D",)):
   - 누를 때 `item_activate` 로 커서 아래 오브젝트를 찾고 선택을 바로 되돌림 (오브젝트 선택·active·active 컬렉션). 끌 대상 =
     그 행이 선택돼 있었으면 선택 전부, 아니면 그 하나. 오브젝트 행이 아니면 PASS_THROUGH.
   - 3 px × 배율 이상 움직이면 드래그. 행 띠 (높이 = UI_UNIT_Y = 20 × 배율, View2D 로 스크롤 반영) 의 가운데 절반 = **위에**,
     위 / 아래 1/4 = **사이에**. Outliner WINDOW POST_PIXEL 로 대상 행 테두리 / 사이 선을 그리고, 상태 바에 「Parent to X」 등.
   - 놓을 때 같은 방식으로 대상 행을 찾고 선택 복원 후:
     - 위에 → 대상 아래로 (자기 자신·자기 자손이면 건너뜀, 경고).
     - 사이에 → 그 행 오브젝트의 부모 아래로 (최상위면 월드), 정렬이 꺼져 있고 같은 컬렉션이면 그 행 앞 / 뒤로 순서까지.
     - 빈 곳 → 월드로.
     - Parent Mode = Blender 이면 Blender 식 (parent inverse = 부모 월드 역행렬).
   - ESC / RMB = 취소. 언두 한 단계. 오브젝트 모드에서만 (다른 모드는 poll False → 통과).
3. **순서 바꾸기 범위** (delegated): Blender Outliner 순서는 정렬 끔일 때 컬렉션 `objects` 링크 순서뿐 — 같은 컬렉션 안의
   형제만 바꿀 수 있다 (unlink + link 다시, 뒤쪽 오브젝트를 순서대로 다시 링크; 오브젝트별 선택·숨김 (base 상태) 복원).
   다른 컬렉션 사이 순서·컬렉션 행 순서는 안 함. ~~MayaKit 템플릿 Outliner 정렬 끄기~~ → **정렬은 켜 둔다** (delegated, 위 측정:
   정렬을 끄면 첫 오브젝트가 맨 아래로 가서 Maya 이름 pCube1, pCube2 … 의 순서가 정렬 켬 (자연 정렬) 보다 더 어긋난다).
   순서 바꾸기는 Display > Sort Alphabetically 를 끈 Outliner 에서만; 링크 순서는 `displayed` / `linked` (첫 항목 맨 뒤 규칙) 로
   계산한다.
4. **키맵**: `_add(kd, "Outliner", "maya_kit.outliner_drag", MIDDLEMOUSE PRESS, shadows=("View2D",))`. LMB 항목은 그대로
   (Blender 드래그 + 1 의 변환). `mapping.py` 의 Outliner 행 (드래그) 갱신.
5. 사이드바 kit Outliner (UIList, step 11) 는 드래그가 불가 (UIList) — 그대로, 문서에.
6. 다음 단계 고려: 83 (키 삽입 Alt+I 등), 84 (타임 슬라이더 Shift 드래그), 85 (매니퓰레이터 Ctrl) 는 다른 에디터·이벤트라
   겹치지 않는다. 언두 되돌리기 + 재적용 패턴은 84 의 키 이동에는 필요 없다 (자체 모달).

## 검증 계획

- 헤드리스 `tests/test_step82_outliner_drag.py`: 순수 함수 (행 띠 → 위/사이, 대상 결정, 순서 재배열 목록),
  `maya_kit.outliner_reparent` (parent inverse identity, 월드 유지, 빈 곳 = 월드, 자손 건너뜀, Blender 모드),
  순서 바꾸기 (링크 순서·선택·숨김 유지), 키맵 항목, 템플릿 정렬 끔.
- GUI `tests/gui/gui_step82_outliner_drag.py`: LMB 드롭 → parent inverse identity + 월드 유지 + 언두 한 번 = 드롭 전,
  빈 곳 LMB 드롭 (Maya 자식) → 월드 유지, MMB 위에 / 사이에 / 빈 곳, MMB 동안 선택 그대로, 순서 바꾸기, 스크린샷.
- 대응표 Outliner 행 재평가, 전체 헤드리스·GUI, dogfood, manual_checks.

## 한 것

- `src/maya_kit/operators/outliner_drag.py` (새 파일)
  - `maya_kit.outliner_drag` — "Outliner" MMB PRESS 모달. 누를 때·놓을 때 `outliner.item_activate` 로 행을 맞혀 보고 선택을 되돌림
    (`object.select_all` 연산자를 한 번 거쳐야 Outliner 강조가 오브젝트 선택을 다시 읽는다 — Python `select_set` 만으로는 안 됨, 측정).
    3 px 움직이면 드래그; 행 가운데 = 위에 (흰 테두리), 위/아래 1/4 = 사이 (흰 선), 빈 곳 = 월드. 자기 자손 위 = 건너뜀 + 경고.
    Parent Mode = Blender 이면 Blender 식 (parent inverse).
  - LMB 드롭 변환: `depsgraph_update_post` 가 새로 등록된 `OUTLINER_OT_parent_drop` / `parent_clear` 를 보면 타이머 →
    `ed.undo` → 바뀐 부모만 `maya_kit.outliner_reparent` (undo=True, 「Parent」 한 단계) 로 Maya 방식, 드롭 뒤 선택 복원.
    본 부모 (parent_type ≠ OBJECT) 면 `ed.redo` 로 Blender 결과 유지. 언두가 없으면 그 자리에서 parent inverse 를 identity 로.
  - 순서: `displayed` / `linked` (측정한 첫 항목 맨 뒤 규칙), `reorder` (컬렉션 다시 링크, 선택·숨김·active 복원).
- `keymap/maya_patches.py` 38 `patch_outliner_drag`: "Outliner" MIDDLEMOUSE PRESS, shadows View2D / View2D Buttons List
  (Outliner 트리에는 스크롤바 밖에서 통과하는 `scroller_activate` 뿐). Alt+MMB 패닝은 IC View2D 그대로 (= Maya).
- `operators/__init__.py` 등록 / 핸들러.
- 판단 (delegated): Maya Outliner 드래그 규칙은 [K] (Autodesk 문서 문장 못 찾음); 템플릿 정렬은 켬 유지; 사이 드롭은 정렬이 켜져 있으면
  그 행 부모 아래로만; 본 행 드롭은 Blender 그대로; 드래그 상태 문구는 넣지 않음 (Maya 에도 없음; 행 테두리 / 선만).
- 대응표 (PLAN 「재점검 5차」 UI 행) Outliner 는 여전히 **Partial** — 드래그 부모 지정·순서는 끝, Sets (Maya 세트 노드) 가 남음.

## 검증

- 헤드리스 `tests/test_step82_outliner_drag.py` 9/9: 드롭 구역, `reordered` / `displayed` / `linked`, 드롭 부모 규칙, Maya 부모 지정
  (inverse identity, 월드 유지, 로컬 값이 부모 기준, 자손 건너뜀, 빈 곳 = 월드), Blender 모드, 다시 링크 순서 + 선택·숨김·active,
  `outliner_reparent` 연산자, 핸들러·키맵 항목 (MMB 하나, Alt+MMB 패닝 남음).
- GUI `tests/gui/gui_step82_outliner_drag.py` 20/20: LMB 드롭 → `MAYA_KIT_OT_outliner_reparent`, inverse identity, 월드 유지,
  언두 한 번 = 드롭 전, 리두 = Maya 결과; MMB 위에 (드래그 중에는 변화 없음, 선택·Outliner 강조 그대로); 빈 곳 = 월드;
  정렬 끔 행 순서 B D A C (첫 링크 맨 뒤) → MMB 사이 드롭 → 링크 D A B C, 행 A C B D; LMB 빈 곳 드롭 (회전·스케일 부모의 Maya 자식)
  → 월드 유지; 자기 자식 위 MMB = 건너뜀. 스크린샷 `gui_step82_outliner_drag.png` 에서 놓을 행 흰 테두리 확인.
- 전체: 헤드리스 646/646 (처음 645/646 — 키맵 섀도잉 테스트가 View2D Buttons List 의 MMB 를 같은 에디터로 봄 → shadows 에 추가),
  GUI (기본 배율) 579/579, dogfood 47/47 (콘솔 0), `gen_keymap_mapping` 변화 없음 (MMB 드래그는 Maya 단축키 표 밖).
- `docs/manual_checks.md` 「Step 82」 5 항목 (드래그 감각, 큰 장면에서 누름 반응, 패닝).

## 남은 것

- 사이드바 kit Outliner (UIList, step 11) 는 드래그 불가 (UIList 한계) — 그대로. Maya Outliner 의 Sets 행도 그대로 (대응표 Partial 이유).
- Shift+MMB / Ctrl+MMB 드롭 (Maya: 복사·인스턴스 등) 은 안 함 [K 불확실]. 드래그 중 커서 모양도 바꾸지 않음 (Python API 의
  `Window.cursor_modal_set` 으로 가능하나 Maya 커서 근거 없음).
- 펼친 부모 바로 아래 (첫 자식 위) 1/4 에 놓기는 Maya 에서 그 부모의 첫 자식이 되지만 kit 는 그 행 (부모) 의 형제 뒤로 놓는다.
- 컬렉션 행이 보이는 (Blender 식) Outliner 에서 다른 컬렉션 사이 순서·컬렉션 행 위 MMB 드롭은 안 함 (컬렉션 위 = PASS 없이 무시).
- 정렬 끔 Outliner 의 첫 항목 맨 뒤 규칙은 4.5 측정 — 5.x 확인 안 함 (다음 5.x GUI 실행 때).
- Maya 실행으로 드래그 규칙을 확인하지 않았다 (C++ Outliner, 화면 조작만 가능) — 손 확인 항목에 포함.
