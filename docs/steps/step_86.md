# Step 86 — Dope Sheet · NLA · Node Editor 선택 수식

재점검 5차 backlog 6 (docs/PLAN.md 「재점검 5차」 blindspot 1, 대응표 72행 조작/단축키 Partial).

## 근거

- Maya 선택 수식 (research/maya/interaction.md:69-71 [K]): Shift+LMB = 토글, Ctrl+LMB = 해제, Ctrl+Shift+LMB = 추가 (빼지 않음); 마키도 같음.
- kit: `keymap/maya_patches.py` SELECT_RULES (step 2) 가 3D View · UV · Outliner · Graph Editor 의 클릭 / 박스에만 적용.
  `KeyconfigData.rewrite_modifier_set` 은 연산자의 Alt 없는 수식 묶음 (기본 항목이 있는 키맵 전부) 을 지우고 주어진 4 변형으로 바꾼다 —
  IC 에 Ctrl / Ctrl+Shift 항목이 없어도 만든다.
- IC 4.5 (`industry_compatible_data.py`):
  - Dopesheet: `action.clickselect` PRESS 없음 / Shift (extend) + Alt 변형 (column / channel), Ctrl+Shift+LMB PRESS =
    `action.select_leftright` (CHECK, 현재 프레임 왼쪽/오른쪽 키), `action.select_box` CLICK_DRAG 없음 / Shift ADD / Ctrl SUB.
  - NLA: `nla.click_select` 없음 / Shift, Ctrl+Shift+LMB = `nla.select_leftright`, `nla.select_box` 없음 / Shift / Ctrl.
  - Node Editor: `node.select` (`_template_node_select`) 없음 (deselect_all + select_passthrough) / Ctrl (그냥 선택) / Shift / Ctrl+Shift
    (toggle) + Alt 변형, Ctrl+Shift+LMB PRESS = `node.select_link_viewer`, `node.select_box` CLICK_DRAG 없음만, Ctrl+CLICK_DRAG =
    `node.link` (detach: 소켓에서 링크 떼기).
- 연산자 옵션 (4.5 측정): `action.clickselect` / `nla.click_select` = extend · deselect_all (deselect 없음 → Graph 처럼 Ctrl / Ctrl+Shift 도
  토글, step 2 workaround), `node.select` = extend · deselect · toggle · deselect_all (Maya 그대로 가능), 박스 셋 = SET / ADD / SUB (XOR 없음 →
  Shift 박스 = 추가, step 2 workaround).

## 계획

1. SELECT_RULES 에 6 규칙 추가:
   - `action.clickselect` PRESS: 없음 = deselect_all, Shift / Ctrl / Ctrl+Shift = extend (토글), keep column / channel.
   - `nla.click_select` PRESS: 같은 규칙.
   - `node.select` PRESS: 없음 = deselect_all + select_passthrough, Shift = toggle, Ctrl = deselect, Ctrl+Shift = extend.
   - `action.select_box`, `nla.select_box` CLICK_DRAG: `_BOX_NO_XOR` (SET / ADD / SUB / ADD), keep tweak · axis_range · wait_for_input.
   - `node.select_box` CLICK_DRAG: SET / Shift ADD / Ctrl+Shift ADD, **Ctrl 은 안 만듦** — Ctrl+드래그는 Blender `node.link` (소켓에서 링크
     떼기) 가 쓰고 같은 키맵에 같은 이벤트가 생기면 충돌 (delegated: Node Editor 의 Ctrl 마키 해제만 빠짐).
2. 같은 이벤트의 기존 항목 제거: Dopesheet `action.select_leftright` Ctrl+Shift+LMB, NLA `nla.select_leftright` Ctrl+Shift+LMB,
   Node Editor `node.select_link_viewer` Ctrl+Shift+LMB (Maya 추가가 이김; delegated — Viewer 연결은 Blender Node 메뉴 / Shift+Ctrl+Alt
   없음, 문서에). `[` / `]` 의 select_leftright 는 그대로.
3. Time Slider (TIMELINE 모드) 는 step 56 / 84 항목이 맨 앞이라 LMB / Shift+LMB 는 그대로, Ctrl+LMB 만 새로 키 해제 (보이지 않음, 해 없음).
4. 다음 단계 고려: 87 (뷰 키) 은 3D View 키, 88 (manual_checks) 과 무관.

## 검증 계획

- 헤드리스: `tests/test_keymap_maya.py` (새 충돌 없음, 섀도잉) + `tests/test_step86_select_modifiers.py` (세 에디터의 클릭 4 변형과 props,
  박스 변형, 지운 항목, Alt 변형 남음, node Ctrl 박스 없음 + node.link 남음; 배경 오버라이드로 연산자 동작은 GUI 에서).
- GUI `tests/gui/gui_step86_select_modifiers.py`: Dope Sheet 에 키 3 개 → 클릭 = 하나, Shift+클릭 = 토글 추가 / 다시 = 빠짐, Ctrl+클릭 =
  해제, Ctrl+Shift+클릭 = 추가 (이미 선택된 키는 그대로 — Blender 토글 한계면 문서에), Node Editor 노드 클릭 수식 4 가지.
- 대응표 조작/단축키 행 재평가, 전체 헤드리스·GUI, dogfood.

## 한 것

- `keymap/maya_patches.py`: SELECT_RULES 6 규칙 (`_NODE_CLICK`, `_NODE_BOX` 추가), `SELECT_CTRL_SHIFT_REMOVED` 3 항목을 `patch_selection` 에서 지움.
  `rewrite_modifier_set` 은 IC 에 Ctrl / Ctrl+Shift 항목이 없어도 그대로 만든다 (Alt 변형은 건드리지 않음).
- 판단 (delegated): Node Editor Ctrl 마키 해제 없음 (Ctrl+드래그 = node.link 링크 떼기 유지), Ctrl+Shift+클릭 Viewer 연결 없앰, Dope Sheet /
  NLA 의 Ctrl / Ctrl+Shift 클릭은 토글 (연산자에 deselect 없음 — Graph 와 같은 step 2 workaround).
- 대응표 (PLAN 「재점검 5차」 조작/단축키 행): Dope Sheet / NLA / Node 가 이제 Maya 수식 — 남은 것은 deselect 없는 연산자의 토글 한계
  (Outliner / Graph / Dope Sheet / NLA Ctrl, 박스 XOR 없음; API 한계) 뿐이라 Partial 유지 (한계 항목).

## 검증

- 헤드리스 `tests/test_step86_select_modifiers.py` 4/4 (세 에디터 클릭 4 변형 props, Alt 변형 남음, 박스 모드, node.link Ctrl 드래그 남음,
  Ctrl+Shift 항목 지움 + [ ] 키 남음), `tests/test_keymap_maya.py` 12/12 (새 충돌·섀도잉 없음).
- GUI `tests/gui/gui_step86_select_modifiers.py` 10/10: Dope Sheet 키 10 클릭 = [10], Shift 20 = [10, 20], 다시 = [10], Ctrl+Shift 1 = [1, 10],
  Ctrl 10 = [1]; Node Editor A 클릭 = [A], Shift B = [A, B], Ctrl+Shift C = [A, B, C], 다시 = 그대로 (Maya 추가), Ctrl A = [B, C].
  스크린샷 `gui_step86_nodes.png` 에서 B, C 테두리.- 전체: 헤드리스 671/671, GUI (기본 배율) 611/611, dogfood 47/47 (콘솔 0). `docs/manual_checks.md` 「Step 86」 3 항목.

## 남은 것

- Dope Sheet / NLA / Graph / Outliner 의 Ctrl / Ctrl+Shift 클릭은 토글 (연산자에 deselect 없음; 선택 안 된 것 Ctrl = 선택, 선택된 것
  Ctrl+Shift = 빠짐), 박스 XOR 없음 — 바꾸려면 kit 클릭 연산자 (키 아래 찾기) 가 필요, 지금은 안 함.
- Node Editor Ctrl 마키 해제 없음, Viewer 연결 키 없음. Animation Channels (채널 목록) 수식은 이번 범위 밖 (IC 그대로).
- 다음: 87 뷰 키 묶음 3 (Alt+A, Alt+P, Alt+화살표, backtick, 백슬래시).

