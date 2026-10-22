# Step 136 — Marking menus complete and inside the window (#56 #62 #74)

## 계획

backlog 3 (PLAN 「재점검 8차」; `step_133_quant.md` gap 1 / §7, `step_133_ui.md` #7 #16). 헤드리스로 센 마킹 메뉴 항목 464 개 중 128 개가
회색 (빈 `Sub` 포함; step 133 은 410 / 112 로 셈). 그중 25 개 이상은 메인 메뉴에서 이미 작동한다. 컴포넌트 모드 RMB 목록의 Select All /
Deselect All / Select Hierarchy / Invert 는 `object.*` poll 때문에 회색. 목록이 영역 경계에서 잘린다
(`tmp/audit133_ui/pairs/zoom_m14_list.png`, `zoom_m15_clip.png`, `tmp/dogfood/shots/05_rmb_marking_menu.png`).

### 원인 (그림과 코드에서)

1. **틈**: bounds 는 이미 창 전체 (`draw.window_bounds`, step 52) 인데, 영역 사이 경계선 (Blender `ED_screen_draw_edges`, 영역을 다 그린
   뒤 창이 그림) 은 어떤 영역의 POST_PIXEL 도 그릴 수 없다. 목록 줄이 가로 경계 (3D View / Timeline) 에 걸치면 그 줄이 반쯤 가려진다
   (m14 「Assign Existing Material」, m15 「Booleans」, 05 「Select Similar」 「UV Sets」).
2. **그리기 순서**: 마킹 메뉴 핸들러는 `marking` 등록 때 추가되고, 뒤에 등록되는 킷 POST_PIXEL 핸들러 (`ui/time_slider.py` Dope Sheet
   WINDOW, `ui/range_bar.py` HEADER, `ui/shelf.py`, `ui/outliner_sets.py`, …) 가 같은 영역에서 나중에 그려 메뉴 위에 숫자 · 눈금이 보인다
   (m14 의 80 / 85 / 90).
3. **회색**: 마킹 메뉴 항목은 메인 메뉴 경로를 모르고 자기 동작만 들고 있어 step 63 / 101 / 110 의 매핑 · 컴포넌트 모드 규칙
   (`menu_map.OBJECT_MODE` / `EDIT_MODE`) · 옵션 창을 못 받는다. 회색 항목엔 알림도 없다 (메인 메뉴는 step 101 부터 회색 = 알림).

### 설계 (delegated)

- **A. 경계 (#56)** — `engine.fit_ring(layout, center, bounds, edges=())`: `edges` = 창 안쪽의 가로 영역 경계 띠 (y0, y1, x0, x1;
  `draw.window_edges(window, region)`, 두께 = 경계선 + 여유, UI 배율에 비례). 목록 줄은 한 칸씩 위에서 아래로 놓되 띠에 걸치면 띠 아래로
  내리고 (Maya 처럼 한 칸 유지), 창 바닥에 닿으면 step 52 의 다음 칸으로. 방사 상자도 띠에 걸치면 띠 밖으로 민다. 리스트 하위 메뉴
  (`Session._inside_bounds`) 도 같은 규칙. 그리기 순서: 메뉴가 열릴 때 (`draw.activate`) 마킹 핸들러를 지우고 다시 추가해 각 영역 목록의
  끝 = 마지막에 그려지게. 세로 경계 (Outliner / dock 옆) 는 줄 하나를 가르는 얇은 선이라 이번 범위 밖 (남은 것에 기록).
- **B. 항목 (#74 #62)** — 새 동작 형태 `("item", "<Maya 메뉴 경로>")` = 메인 메뉴 항목 그대로 (`allset.menu_item`: 컴포넌트 모드 규칙,
  object 모드 규칙, Maya 경고, 옵션 창 / 옵션 상자는 `run_action(..., option=True, path=)`). 활성 = 경로가 `menu_map.MAP` 에 있으면
  (메인 메뉴처럼 poll 실패는 회색이 아니라 Maya 경고). 25 개 + 같은 Maya 명령이 있는 나머지를 이것으로 연결. Select All / Deselect All /
  Invert = `SelectAll` / `SelectNone` / `InvertSelection` (dagMenuProc.mel:2592-2595, 메인 메뉴와 같은 runTimeCommand) → 메인 메뉴 경로;
  Select Hierarchy = `select -hierarchy <$object>` → 킷 연산자 (메뉴를 연 오브젝트 + 자식, 선택 교체). RMB 목록의 빈 하위 메뉴 중 Blender 에
  같은 것이 있는 것 (Actions = Template / Untemplate / Unparent / Bounding Box, UV Sets, Color Sets: createActionsMenuItems :1851-1854,
  createColorSetMenuItems :2216-2252) 은 채운다. 남는 회색은 모두 알림 (`notices.MARKING`, 키 = `<proc>/<라벨 경로>`; 메뉴에서 회색 항목에
  마우스를 올리면 Help Line 에 표시, step 54 의 `notices.show`). 테스트: 회색 항목 = 알림 있는 것만, 알림 키 = 실제 회색 항목,
  `("item", path)` 의 path 는 MAP 에 있음, step 8 방사 위치 그대로.
- 검증: 헤드리스 회색 수 (전 / 후, 알림 없는 회색 0), GUI 그림 — 오브젝트 / 컴포넌트 모드의 RMB / Shift+RMB / Ctrl+RMB 를 뷰포트
  네 가장자리 근처 (위 · 아래 · 왼쪽 · 오른쪽) 에서, 배율 1.0 (`ALLSET_GUI_UI_SCALE=0.8`) 과 1.25.

### 레인 (병렬, worktree)

| 레인 | 이슈 | 파일 |
|---|---|---|
| BOUNDS | #56 | `marking/engine.py`, `marking/draw.py`, `marking/modal.py` 의 bounds 전달 줄만, `tests/test_step136_bounds.py`, `tests/gui/gui_step136_edges.py` |
| ITEMS | #74 #62 | `marking/menus.py`, `marking/modal.py` 의 `poll_action` / `run_action` / hover 알림, `ui/notices.py` (`MARKING`), 새 연산자 · 메뉴 (`marking/rmb_items.py`), `tests/test_step136_items.py` |

`modal.py` 는 두 레인이 다른 함수만 고친다 (메인이 병합). 메인: 병합, 회색 수, 두 배율 GUI 그림 확인, GUI 전체 한 번, 커밋.

## 한 것

레인 2 개 (worktree). 첫 실행이 세션 중단 (07:18 「Request interrupted」) 으로 멈춰, 남은 변경을 WIP 커밋 (d32a09e, 9139ba4) 한 뒤 두 레인을
포그라운드로 다시 돌려 끝냄 (교훈: 백그라운드 레인을 기다리며 턴을 끝내지 말 것). 레인 문서: `step_136_bounds.md`, `step_136_items.md`.

- **BOUNDS** (#56): `draw.window_edges` (영역 틈 3 px + 양쪽 테두리 2 px, GUI 측정, `pixel_size` 비례) → `engine.fit_ring(..., edges)` /
  `Session(..., edges)`: 목록 줄은 경계 띠를 건너뛰어 한 칸 유지, 창 바닥에서만 다음 칸; 방사 상자 · 리스트 하위 메뉴도 띠를 피함.
  `draw.activate` 가 마킹 핸들러를 다시 추가해 다른 킷 POST_PIXEL (Time Slider 숫자 등) 보다 나중에 그림.
- **ITEMS** (#74 #62): 동작 형태 `("item", "<Maya 메뉴 경로>")` = 메인 메뉴 항목 그대로 (`allset.menu_item`: 컴포넌트 / 오브젝트 모드 규칙,
  Maya 경고, 옵션 창). 25 개 + 같은 runTimeCommand 가 있는 나머지 연결, RMB Select All / Deselect All / Invert = Select 메뉴 경로
  (dagMenuProc.mel:2592-2595), Select Hierarchy = `allset.mm_select_hierarchy`, RMB Actions / UV Sets / Color Sets 채움
  (`marking/rmb_items.py`), 남은 회색은 `notices.MARKING` 알림 (회색 항목 위에서 Help Line).
- **메인 (병합 뒤)**:
  - Ctrl+RMB 를 메시 오브젝트 위 오브젝트 모드에서도 `polyConvertMM` 로 (`buildConvertMM.mel:85-106` 은 모드가 아니라 lead 의 shape
    종류로 고른다, research/maya/hotkeys_and_menus.md:232): 항목은 활성, 고르면 컴포넌트 모드 + 전체 선택 뒤 실행 = Maya 처럼 오브젝트
    전체를 변환 (`marking/__init__.resolve`, `modal.CONVERT_FROM_OBJECT`; delegated). BOUNDS 레인이 GUI 로그에서 찾은 것.
  - Camera-Based Selection 을 체크 박스로 (`engine.TOGGLE_OPS`, `draw.checked` = select-through 꺼짐).
  - 목록 몸통의 구분선은 Maya 구분선 자리 (목록 번호가 `DIVIDER` 를 건너뛸 때) 에만: 줄이 경계를 건너뛴 틈에 가짜 구분선이 그려졌다
    (GUI 전체에서 step 91 그림으로 발견). `gui_step91_view_chrome` 의 HUD 검사는 줄 대신 목록 몸통 (줄 사이 틈 포함) 의 픽셀을 본다.

## 검증

- 회색 수 (헤드리스, `tests/test_step136_items.py` 가 출력): 항목 464 → 472 (RMB Actions ▸ 4 개 × 2 메뉴), 회색 **128 → 73**, 알림 없는 회색 **0**,
  회색 아닌 알림 키 0. 남은 73 개 = Blender 에 같은 것이 없는 Maya 항목 (표: `step_136_items.md`; 그중 23 개는 Shift+Q 비메시 pick mask).
- 헤드리스 전체 `python tests/run.py`: 1072 passed, 1 failed (134 files) — 실패 1 = step 8 dispatch: 빌드가 Ctrl+RMB 수정 전 zip 이라 새 기대값과
  달랐다. 다시 빌드해 `-k step8_,step9_,step33,step52,step129_marking,step136,step94,enable_disable,step101`: **88 passed, 0 failed (10 files)**.
- 경계: `test_step136_bounds` = 모든 마킹 메뉴 × 뷰 위 56 점 = 1456 배치에서 창 밖 0, 가로 경계 위 줄 0, 경계 위 방사 상자 0.
- GUI (병합 뒤, 메인): `-k step136,step129_marking,step8_marking` 배율 1.25 **39 passed, 0 failed (4 files)**; `-k step136` 배율 1.0
  (`ALLSET_GUI_UI_SCALE=0.8`) **16 passed, 0 failed (2 files)**. `gui_step136_edges` = 오브젝트 / vertex / edge / face × RMB / Shift+RMB /
  Ctrl+RMB × 뷰 위 · 아래 · 왼쪽 · 오른쪽 = 48 메뉴, 배율마다 그린 상자가 창 안 · 경계 띠 밖. `gui_step136_items` = 컴포넌트 모드 RMB 의
  Select All 등 활성 · 실행, 회색 Time Editor 알림, Ctrl+RMB 오브젝트 모드 = 변환 메뉴 → To Shell = 컴포넌트 모드 + 오브젝트 전체.
- 그림 직접 확인 (`tmp/shots136m/`, `tmp/shots136m/s100/`): `1.25_object_ctrl_bottom` (변환 메뉴, 줄 · 상자 경계 밖), `1.00_vertex_rmb_bottom`
  (목록이 고리 위로, 회색 아닌 Select All 등), `1.00_face_shift_right` (dock 위 목록, Target Weld Tool 이 경계 아래로).
- GUI 전체 (`tests/gui/run.py`, 커밋 전 한 번): **1381 passed, 1 failed (118 files)** — 실패 1 = `gui_step91_view_chrome` 「list rows cross
  the HUD panel」: 줄이 경계 띠를 건너뛰어 HUD 가 줄 사이 틈 (목록 몸통) 아래에 놓임 → 검사를 몸통 기준으로 고치고 가짜 구분선 수정 뒤
  그 파일만 다시: **8 passed, 0 failed**; 마킹 관련 GUI 다시 (`-k step136,step129_marking,step8_marking,step52`): **50 passed, 0 failed**.

## 남은 것

- 넷째 칸이 세로 경계 (뷰 | dock) 를 피하느라 셋째 칸에서 떨어져 dock 위에 놓일 수 있다 (`tmp/s91/gui_step91_rmb_over_hud.png`,
  Assign Existing Material). Maya 는 한 칸이 화면 밖까지 — 칸 수를 줄이는 다른 배치 (목록을 고리 위로 일부) 는 다음 기회.
- Time Slider View2D 스크롤바가 POST_PIXEL 뒤에 그려져 그 위 상자에 얇은 선 (Python 으로 못 막음). 핫박스 줄은 경계 띠를 아직 안 피함.
- 회색 73 개 = Blender 에 없는 Maya 항목 (알림 있음). hotbox Time Slider / Range Slider 토글은 레이아웃 변경이라 회색 + 알림.
- Ctrl+RMB 오브젝트 모드 To Edge Loop and Duplicate 등은 전체 선택에 적용 (Maya 도 오브젝트 전체 변환) — Maya 에서 직접 비교는 안 함.
