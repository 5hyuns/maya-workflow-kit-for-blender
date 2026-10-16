# HANDOFF

## 현재 작업

- Step 8 (M3-a 마킹메뉴 1차, 파이) 완료 — `docs/steps/step_8.md`. 헤드리스 110/110, GUI 74/74.
- 정의 `src/maya_kit/marking/menus.py` (Maya 방사 위치 데이터, Blender UI 와 무관), 파이 클래스·디스패치·Q/W/E/R 바인딩 `src/maya_kit/marking/__init__.py` (`maya_kit.marking_menu(trigger)`, `resolve()`, `idname()`), 키맵 `keymap/maya_patches.patch_marking_menus`.
- Step 7 (메뉴바·Status Line·커맨드 라인) = `dc31143`. 그 이전 단계는 git log.

## 바로 다음 할 일

- **Step 9 — M3-b 핫박스 + 커스텀 마킹메뉴 엔진** (사용자 번호; PLAN 표 #10): Space 홀드 = 풀스크린 핫박스(GPU 모달: 메뉴 행, 클릭 시 메뉴 열기, 중앙/4 영역 마킹메뉴), Space 탭 = 뷰 전환(이미 `taphold.SpaceBinding.tap`). 마킹메뉴 엔진: 드래그 방향 선택, 빠른 플릭, 그 자리 중첩, 옵션 박스.
  - 근거: `research/maya/hotkeys_and_menus.md` §4 (핫박스 구조), `research/maya/marking_menus.json` `hotbox`, `research/blender/api_limits.md` #4–#5.
  - 재사용: 메뉴 행 = `ui/menu_sets.menus_for_set()` + `menu_idname()`, 마킹메뉴 데이터 = `marking/menus.py` (`MENUS`, `walk`, `Sub`), 항목 실행 = `menu_map.normalize` 의 op/v3d/tool/menu.
  - 복잡 설계(모달 + GPU) → step_9.md 「계획」 먼저.
- 미뤄진 것: Range Slider·타임라인·`.` `,` 키, Status Line 입력 라인 등 (PLAN 「Ordering after step 7」).
