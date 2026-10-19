# Step 108 — Maya hotkeys in kit menus and Maya menu look (step_98.md #12, #14)

## 계획 (delegated)

**측정 (GUI probe, `tests/gui` 임시 probe)**: Blender 메뉴 항목의 오른쪽 단축키 글자는 C 가 키맵에서 찾은 것만 그린다 (`|` 를 넣은
라벨은 그대로 `|` 로 그려짐 — UI_SEP_CHAR 처리는 Python 라벨에 적용되지 않음). 지금 kit File 메뉴는 Blender 가 찾은 키를 Blender
형식으로 보여 준다: Increment and Save 「Ctrl Alt S」 (kit 이 같은 연산자를 Window 키맵에 묶음), Recent Files / Recent Increments
「Shift Ctrl O」 (IC 의 `wm.call_menu` 키), Exit 「Ctrl Q」. 1.25 배율에서 File 메뉴 (제목 포함) 는 808 px.

1. **어떤 키를 보여 주나** — 새 생성기 `tools/gen_menu_hotkeys.py` → `ui/menu_hotkeys.py` (`HOTKEYS[label path] = "Ctrl+N"`):
   메뉴 항목의 Maya 명령 (menus.json `command`; `tools/gen_menu_data.py` 가 이제 `command_paths` 로 경로와 함께 내 줌) = 핫키의
   runTimeCommand MEL (hotkeys_default.json `press.command`), MEL 이 런타임에 만들어지는 항목 (`$cmd`) 은 핫키의 메뉴 분류 + 라벨
   (`Menu items.Common.Edit` + `Duplicate`). **kit 이 그 키를 Maya 뜻으로 묶은 것 (mapping KIT / IC) 만** — 다른 일을 하는 키는
   광고하지 않는다. 같은 명령에 키가 둘이면 첫 키, 단 Backspace 보다 Del (Maya 메뉴의 Ctrl+Del). 표기 = Maya (Qt) 형식
   `Ctrl+Alt+Shift+키`, Del / Left / PgUp (audit7 `menu_Modeling_Edit_Mesh.png`).
2. **어떻게 그리나** — 라벨 안에서 오른쪽 맞춤: 한 메뉴의 항목마다 꼬리 (`Ctrl+N`, 옵션 상자면 `Ctrl+N  ❒` / `❒`) 를 정하고, 메뉴
   글꼴 (`blf` 글꼴 0, `ui_styles[0].widget.points` × UI 배율) 로 잰 너비로 「라벨 + 채움 + 꼬리」 의 너비를 같게 만든다 (채움 =
   공백 + 아주 좁은 공백 U+200A, 글꼴에 없으면 공백만). Maya 처럼 옵션 상자 표시도 오른쪽 열에 모인다 (delegated: 꼬리 글자색은
   라벨과 같음 — Blender 는 Python 라벨 일부만 흐리게 할 수 없음).
3. **Blender 키를 숨김** — Blender 가 단축키를 찾지 못하게: 연산자 항목 (`op`) 은 모두 `maya_kit.menu_item(item=path)` 로 그린다
   (키맵에 없는 연산자 + 속성), Blender 메뉴로 가는 항목 (`menu`, 예: Recent Files) 은 그 메뉴를 그대로 그리는 kit 대리 메뉴
   (`MAYAKIT_MT_proxy_*`, 원래 클래스의 하위 클래스) 로 연다. `v3d` / `tool` 항목은 원래 kit 연산자라 키가 없음.
4. **File 메뉴 높이 (#14)** — 위 막대에서 연 File 메뉴가 900 px 창 (1.25) 에 Exit 까지 들어가는지 GUI 로 확인; 여유를 위해 절 이름
   줄을 Maya 처럼 작게 (scale_y 0.8).

검증: 헤드리스 — 그려진 File / Edit / Edit Mesh 항목의 글자 (라벨 + 오른쪽 키) 와 너비 정렬, Blender 키가 나올 수 있는 연산자가
메뉴에 남지 않음; GUI — File / Edit Mesh 메뉴 그림 (위 막대에서) 을 audit7 Maya 그림과 나란히.

## 한 것

- `tools/gen_menu_data.py` 에 `command_paths` (메뉴 항목 → Maya MEL 명령, 경로 규칙은 `option_paths` 와 같음; `menu_data.py` 출력은
  바이트 그대로). 새 생성기 `tools/gen_menu_hotkeys.py` → `ui/menu_hotkeys.py`: 메인 메뉴 **57 항목**에 Maya 키 (File: Ctrl+N / O / S,
  Ctrl+Shift+S, Ctrl+Alt+S, Ctrl+R, Ctrl+Q; Edit: Z, Shift+Z, G, Ctrl+X/C/V, Ctrl+D, Ctrl+G, P, Shift+P …; Edit Mesh: Ctrl+B, Ctrl+E,
  Ctrl+Del, Ctrl+Alt+Left / Right; Key, Playback, Select, Mesh Tools, Help). 매칭: 핫키의 runTimeCommand MEL = 항목 MEL, 아니면
  핫키 분류 (`Menu items.<…>.<메뉴>`) + 라벨; mapping 상태 KIT / IC 만.
- `ui/menu_sets.py`: `item_texts` / `aligned` / `filler` — 메뉴 하나의 꼬리 (키, 옵션 상자 표시) 를 메뉴 글꼴로 재 오른쪽 한 열에
  맞춘다 (채움 = 공백 + U+200A). 옵션 상자가 있는 메뉴에서는 상자 없는 항목의 키도 상자 열을 비워 같은 줄에서 끝난다 (Maya 와 같음).
  연산자 항목은 모두 `maya_kit.menu_item` 으로 (Blender 가 자기 단축키를 찾지 못함), Blender Python 메뉴로 가는 항목은 kit 하위 클래스
  (`MAYAKIT_MT_proxy_*`, 등록·해제), 절 이름 줄은 0.8 높이.
- `keymap/maya_patches.py` `patch_menu_shortcuts`: IC "Window" 의 Shift+Ctrl+O (`wm.call_menu` 최근 파일, C 메뉴라 하위 클래스로
  가릴 수 없음; Maya 에 Ctrl+Shift+O 없음) 제거 → Recent Files / Recent Increments 옆 「Shift Ctrl O」 사라짐.
- 테스트: 새 `tests/test_step108_menu_hotkeys.py` (5: 생성 표가 최신, 그려진 File / Edit Mesh 항목 글자에 Maya 키, 꼬리 너비 정렬
  ±3 px, 메뉴에 Blender 단축키를 낼 연산자 / 메뉴가 없음, 대리 메뉴 등록·해제), `tests/gui/gui_step108_menu_hotkeys.py` (3 + 그림).
  옛 기대값을 새 그리기에 맞춤: test_step7 (`_label`, menu_item 경유), test_step34 / step101 (가짜 layout 에 row), test_step51
  (상자 표시가 끝), test_step54 (Cube 도 menu_item), test_step103 (`_draw_boxed` 는 전체 글자를 받음).

## 검증

- 헤드리스 `python tests/run.py`: **810/810** (97 파일).
- GUI `gui_step108_menu_hotkeys` 3/3 (1.25 와 `--ui-scale 0.8`), 그림: File 메뉴 New Scene … Ctrl+N ❒ / Increment and Save Ctrl+Alt+S /
  Exit Ctrl+Q, Recent Files 옆 Blender 키 없음, 1.25 배율 900 px 창에서 제목 포함 File 메뉴 전체 (791 px) 가 스크롤 화살표 없이
  보임 (Exit · Blender File 까지); Edit Mesh 메뉴 Bevel Ctrl+B / Extrude Ctrl+E / Delete Edge/Vertex Ctrl+Del / Spin Edge Ctrl+Alt+Left
  / Right. 나란히: `research/maya/screens/step108/menu_Modeling_File_pair.png`, `menu_Modeling_Edit_Mesh_pair.png`.
- 전체 GUI `python tests/gui/run.py`: 84 파일 통과, `gui_manual_sweep` 의 M67-4 가 옛 상자 표시 형태로 비교하다 실패 → 정규화를 고치고
  sweep 재실행 331/331. 합계 **1063/1063**.

## 남은 것

- 키 글자는 라벨과 같은 색 (Maya 는 같은 흰색이라 맞음; Blender 의 흐린 단축키 색은 아님). 정렬은 글꼴 너비 계산이라 ±1–2 px.
- 편집기 메뉴 막대 (Graph Editor / Hypershade …) 의 Maya 키는 아직 안 붙임 (같은 `item_texts` 를 쓰지만 `HOTKEYS` 에 편집기 경로가
  없음; 캡처 JSON 에 Maya 가 보인 단축키가 있어 다음에 같은 방식으로 추가 가능). 핫박스 메뉴 행에는 키를 그리지 않음 (Maya 도 핫박스에선
  안 보임).
- Maya 메뉴 아이콘 (step_98 #12 후반) 은 결정 6 (Maya 자료 복사 안 함) 으로 하지 않음.
- 위 막대에서 연 메뉴를 GUI 테스트로 찍을 수 없음 (창 위쪽에서 연 팝업은 screenshot 에 안 나옴, 툴팁이 떠도 안 나옴 — 측정): 높이는
  창 가운데에서 연 메뉴로 확인.
