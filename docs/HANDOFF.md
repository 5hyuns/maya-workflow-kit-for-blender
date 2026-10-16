# HANDOFF

## 현재 작업

- Step 7 (M2-c 메뉴바·메뉴셋, Status Line, 커맨드 라인, Help Line) 완료 — `docs/steps/step_7.md`. 헤드리스 99/99, GUI 67/67.
- 메뉴바: `src/maya_kit/ui/menu_sets.py` (메뉴 클래스 `MAYAKIT_MT_<maya 메뉴 이름>`, `menu_idname()`), 데이터 `ui/menu_data.py` (`tools/gen_menu_data.py` 생성), 매핑 `ui/menu_map.py`. 상단 바 교체·Status Line: `ui/status_line.py` (TOPBAR `draw_left/right` 교체, Status Line 은 가장 큰 3D 뷰 툴 헤더 첫머리).
- 커맨드 라인: `src/maya_kit/command_line/` (`runner.py` 실행·MEL 힌트, `cmds_shim.py` maya.cmds 흉내, 상태바 prepend + Help Line, `import maya.cmds`).
- Step 1–6 은 이전 커밋들 (Step 6 = `0acc961`).

## 바로 다음 할 일

- **Step 8 — M3-a 마킹메뉴 1차** (사용자 번호; `docs/PLAN.md` 표의 #9): 파이메뉴(8방향)로 RMB 컨텍스트(객체: Vertex/Edge/Face/Object Mode/UV, 컴포넌트에서 반대), Shift+RMB 모델링 툴, Ctrl+RMB 변환, QWER+LMB 홀드 툴 옵션.
  - 근거: `research/maya/marking_menus.json`, `research/maya/hotkeys_and_menus.md`, `research/blender/api_limits.md` #5.
  - 재사용: 메뉴 항목 → Blender 동작 매핑 방식(`ui/menu_map.py` 의 op / v3d / tool 종류, `maya_kit.menu_run` / `maya_kit.menu_tool`), 홀드 키는 `operators/taphold.TapHoldBinding`.
  - 9 핫박스는 `menu_sets.menus_for_set()` + `menu_idname()` 으로 메뉴 행을 그린다.
- 미뤄진 것: Range Slider·타임라인 모양·`.` `,` 키 (PLAN 「Ordering after step 7」), Status Line 입력 라인/Symmetry/History 토글.

