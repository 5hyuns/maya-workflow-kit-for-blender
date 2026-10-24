# Step 162 — Option box and menu gestures

Backlog `autodrive_bmk/backlog_155.json` #8.

## 계획

- 레인 (서로 다른 파일, worktree 에이전트 2 개 동시 + 메인):
  1. 메인: Display > Toggle Show/Hide ❒ 와 Edit > Delete by Type > Non-Deformer History ❒ — step 147 이 연산자 속성을
     HIDDEN 으로 만든 뒤 "Blender has no settings" 창으로 떨어짐 (step_154_quant.md:189-191). Maya 창을 GUI Maya 로 캡처
     (`research/scripts/maya_options162/`, step 140 캡처 스크립트 복사) + 동작을 mayapy 로 측정 → `option_windows` 스펙.
  2. 에이전트 S: Maya Ctrl+Shift+클릭 = 메뉴 항목을 현재 셸프에 (research/maya/shelves.md:17) — `ui/menu_sets.py`, `ui/shelf.py`.
  3. 에이전트 H: Hypershade 스와치 MMB 드래그를 물체에 놓으면 재질 할당 (step_67.md:80 남은 것) — `ui/hs_drag.py`.
- 저장: 요청은 "add-on prefs" 지만 사용자 셸프는 step 12 부터 확장 사용자 폴더의 `shelves.json` (step 130 스토어 규칙: Blender
  환경설정에 안 씀) — 같은 곳에 둠 (delegated).

## 한 것

- (1) Maya 측정 (`research/maya/re/options_162.md`):
  - "Toggle Visibility Options": First Selection Independent (기본, optionVar 1) / Dependent (2); Apply and Close / Apply / Close.
    mayapy: Independent = 각자 뒤집기, Dependent = 모두 첫 선택의 반대 (0 은 1 과 같음 — MEL 은 2 만 Dependent).
  - "Delete Non Deformer History Options": Delete: All non-deformer history (기본, prePostDeformers) / History before deformers
    only; Delete / Apply / Close. mayapy: All 은 디포머 **뒤** 비디포머 (polyBevel1) 도 없앰 — 킷의 기존 규칙은 "before only"
    였음 → 기본을 Maya 에 맞춤 (`history.delete_history(..., before_only)`; 디포머만 켜 둔 채 나머지를 굽고 디포머 유지).
  - `option_windows_display.py` `toggle_show_hide`, `option_windows_edit.py` `non_deformer_history`; `visibility.toggle`
    (선택 = 보이는 선택 + 숨겨진 채 선택 `KEPT`; 첫 선택 = Blender 에 선택 순서가 없어 `mesh_maya._first_selected`,
    delegated), h 와 메뉴 클릭이 저장 값을 따름 (`visibility.toggle_dependent`).
- (2) 에이전트 S (`ecabccf`): Ctrl+Shift+메뉴 클릭 = 현재 셸프 탭 끝에 그 메뉴 항목 버튼 (`menu_sets.add_to_shelf_if_asked` →
  `shelf.add_menu_item`; 팩토리 탭은 `shelves.json` `"extra"[shelf]` 에 Maya 슬롯 뒤로 — step 109 슬롯 번호 유지). 버튼 =
  `run_action(("item", path))` (메뉴와 같은 규칙), Ctrl+클릭 = 옵션 상자, 아이콘 = 메뉴 아이콘 / 셸프 그림 / 머리글자.
  Maya 근거 menuItemToShelf (사실만 확인, 복사 안 함). 마킹 메뉴의 Ctrl+Shift 는 실행 (플래그 `clicked` 가 메뉴 행에만).
  Command Line 결과 "Cube added to the Animation shelf".
- (3) 에이전트 H (`ee1118f`, 옛 기준점에서 만든 커밋을 cherry-pick, `ui/__init__.py` / `maya_patches.py` 충돌 해결):
  Browser 스와치 이름 버튼에서 MMB 누름 → 창 모달 (커서 옆 스와치 + 이름), 놓은 화면 점 → 그 아래 창 / 3D View → `scene.ray_cast`
  → `material.assign`. 키맵 항목은 PASS_THROUGH 우선 (`allset.hs_swatch_drag`, "View2D Buttons List"). 측정: 키맵 연산자는
  `context.property` 만 읽음 (`button_operator` 없음) → 스와치 이름 = `Material.allset_hs_pick` 토글 속성; `Window.x/y` =
  화면 좌하단 기준 (Win32 로 확인).

## 검증

- 헤드리스: `test_step162_option_windows` 6/6 (두 경로 option_kind = window, 제목 · 버튼 · 기본값, Independent / Dependent =
  mayapy 표, 저장 값이 h 를 바꿈, Non-Deformer All / before only = mayapy), 관련 12 파일 92/92
  (step 10 Non-Deformer 테스트는 before only + 새 All 확인으로 고침). 레인 S `test_step162_shelf_add` 8/8, 레인 H
  `test_step162_hs_drag` 7/7. 헤드리스 전체 (세 레인 합친 뒤) **1518 / 1518**.
- `python tools/menu_count.py --options`: window 78 → **85**, generic 43 → 44, dead 232 → 225. 경로별 비교 (step 154
  `tmp/option_count154/results/option_kinds.json`): Toggle Show/Hide · Non-Deformer History generic → window, 나머지 변화는
  step 156 Curves 의 dead → window / generic, Create CV Curve Tool redo → window — **회귀 0**.
- GUI `-k gui_step162,gui_step146_option_box,gui_step131_hypershade,gui_step12_shelf,gui_step109_shelves,
  gui_step16_undo_visibility,gui_step140_option_windows` 86/88 → 실패 2 (테스트 문제: 팩토리 스플래시가 이벤트를 먹음,
  hs_drag undo 확인이 장면 준비에 undo step 없음) 고친 뒤 `-k gui_step162` 28/28. 스크린샷 `tmp/s162/gui_step162_toggle_show_hide.png`
  = Maya 캡처와 같은 항목 (First Selection Independent / Dependent, Apply and Close / Apply / Cancel).

## 남은 것

- 셸프: 긴 팩토리 탭 (Poly Modeling 43 개) 은 1600 px 창 UI 1.25 에서 추가 버튼이 화면 밖 (킷 셸프는 스크롤 없음).
  체크박스 / 라디오 메뉴 항목 (`layout.prop`) 은 Ctrl+Shift 를 받을 수 없음. 실제 키보드 확인 = manual_checks.
- Hypershade 드래그: 실제 마우스로 창 밖에서 놓기 (GHOST 마우스 캡처) 는 미확인, 링크된 재질은 드래그 안 됨, 스와치 클릭이
  undo step 하나를 남김, Maya 의 면 위 놓기 규칙은 측정 안 함 (킷 assign 규칙).
- Toggle Dependent 의 "첫 선택" 은 Blender 에 선택 순서가 없어 추정 (이름순 / 활성).
