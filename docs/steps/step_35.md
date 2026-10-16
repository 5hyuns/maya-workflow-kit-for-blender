# Step 35 — Maya 키 묶음: 박스 줌 · Ctrl+T · Y · Multi-Cut · Quad Draw · Return · F2–F6

## 계획 (delegated)

키와 근거 (research/maya/interaction.md, hotkeySetup.mel 줄은 `docs/keymap_mapping.md` 의 Maya 열 기준):

| 키 | Maya | 여기 |
|---|---|---|
| Ctrl+Alt+LMB 드래그 | 박스 줌. 왼→오 = 확대, 오→왼 = 축소 (interaction.md:43, CTX:270-272) | `maya_kit.box_zoom` (3D View, PRESS): 모달로 사각형을 그리고, 놓을 때 `view3d.zoom_border` exec. 오른쪽에서 왼쪽으로 끌면 `zoom_out` |
| Ctrl+T | Universal Manipulator (interaction.md:97, HK:313) | Object Mode / Mesh `wm.tool_set_by_id(builtin.transform)` (menu_map 의 같은 툴) |
| T | Show Manipulator (HK:315) | IC 가 이미 builtin.transform (그대로, 대응표 IC) |
| Y | 마지막 "비 sacred" 툴. Q/W/E/R/T 는 sacred (interaction.md:96, HK:316) | `operators/tools.py`: 0.25 s 타이머가 모드별로 마지막 비 sacred 툴을 기억하고, `maya_kit.last_tool` 이 그 툴로 돌아간다 |
| Ctrl+Shift+X | Multi-Cut (HK:320) | `maya_kit.menu_tool(builtin.knife, edit)`. 오브젝트 모드에서는 메시 편집으로 들어간다 (메뉴와 같은 동작) |
| Ctrl+Shift+Q | Quad Draw (HK:319) | `maya_kit.menu_tool(builtin.poly_build, edit)` |
| Return | 현재 툴 완료 (HK:353) | Blender 모달 툴(knife, poly build 등)은 자기 모달 키맵에서 Return 으로 확정한다. 모달 밖의 3D 뷰 Return 은 IC 의 이름 바꾸기 팝오버라서 Maya 사용자가 Enter 를 누르면 엉뚱한 창이 뜬다 → 제거. 대응표는 "해당 없음" + 메모 |
| F2–F6 | 메뉴 세트 Modeling / Rigging / Animation / FX / Rendering (HK:322-327) | `maya_kit.menu_set(set)` 을 Screen 키맵에 (전역) |

F 키 충돌 (delegated):
- IC 3D View 의 F2 = 오른쪽, F3 = 위, F4 = 카메라, F5 = 180° 회전은 지운다.
- 직교 뷰로 가는 길은 그대로 남는다: 핫박스(Space) 가운데 / 북쪽 Views 마킹 메뉴, Space 탭 4분할, 3D 뷰 View 메뉴,
  IC F1 (앞) 과 Ctrl+F1/F2/F3 (뒤 / 왼 / 아래).
- 이미지·파일 브라우저 같은 편집기의 F 키 (확대 비율, 이름 바꾸기) 는 그 편집기에서 먼저 처리되도록 남긴다 (`shadows`).

검증: 헤드리스 (키맵 항목, 대응표 행, 가림 테스트, 마지막 툴 기억 로직), GUI (Ctrl+Alt+드래그 왼→오 = view_distance 감소,
오→왼 = 증가, Ctrl+T 툴 id, Y 복귀, Ctrl+Shift+X = knife, F3 → Rigging 메뉴 세트 + 스크린샷), 전체 테스트, dogfood.

## 한 것

- `operators/tool_keys.py` (새):
  - `maya_kit.box_zoom`: 모달이 사각형을 그리고, 놓을 때 `view3d.zoom_border` 를 실행한다. 6 px 미만 드래그는 무시, ESC/RMB 는 취소.
  - `maya_kit.last_tool` + `LAST` / `remember` / `_watch` (persistent 타이머).
  - `maya_kit.menu_set`.
- 키맵 patch 27 (`patch_key_batch`):
  - 3D View: Ctrl+Alt+LMB = 박스 줌.
  - Object Mode / Mesh: Ctrl+T, Y, Ctrl+Shift+X, Ctrl+Shift+Q.
  - Screen: F2–F6. Image·File Browser 의 자기 F 키는 `shadows` 로 둔다.
  - IC 3D View 의 F2 / F3 / F4 / F5 와 Return 이름 바꾸기 팝오버 제거.
- `keymap/mapping.py`: ShowModelingUI…ShowRenderingUI, UniversalManip, NonSacredTool, MultiCut, QuadDraw = 구현,
  ShowManipulators (T) = IC 일치, CompleteCurrentTool (Return) = 해당 없음 + 메모. `docs/keymap_mapping.md` 재생성:
  구현 88 → 95, IC 8 → 9, 계획 5 → 0, 해당 없음 10 → 11, 미검토 289 → 285.
- 테스트: `tests/test_step35_keys.py` (6), `tests/gui/gui_step35_keys.py` (10 체크, 스크린샷 2장). 가림 테스트용으로
  `tests/test_keymap_maya.py` 는 바꾸지 않았다 (F 키는 "Screen" 스택 = 전체 키맵 검사, 그래서 shadows 선언).

## 검증

- 헤드리스 `python tests/run.py`: **300/300** (33 파일, 키맵 가림 테스트 포함). GUI `python tests/gui/run.py`: **261/261** (27 파일).
  dogfood **47/47**, 콘솔 오류 0.
- GUI 체크:
  - Ctrl+Alt 드래그 왼→오: 뷰 거리 17.99 → 2.94 (확대), 선택 그대로. 오→왼: 2.94 → 15.48 (축소).
  - Ctrl+T = builtin.transform.
  - Ctrl+Shift+X = 편집 모드 + knife, W → move, Y → knife.
  - F3 = riggingMenuSet, F2 = modelingMenuSet. Return 은 팝오버 없음.
- 스크린샷 (`tmp/shots35/`) 직접 확인: F3 뒤 상단 메뉴 바가 Skeleton / Skin / Deform / Constrain / Control (Rigging),
  Return 뒤 화면에 팝업 없음.

## 남은 것

- 박스 줌은 사각형만 그린다 (Maya 는 줌 미리보기 없음 [K] — 같음). 직교·카메라 뷰 감각은 manual_checks 에 남겼다.
- F1 은 IC 그대로 앞 뷰다 (Maya F1 = 도움말). Maya 키가 아니어도 직교 뷰 접근용으로 남겼다 (delegated).
- Y 는 3D 뷰 툴만 기억한다 (Maya 는 모든 컨텍스트). 기억은 세션 동안만.
