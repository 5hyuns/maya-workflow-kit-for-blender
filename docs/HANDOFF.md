# HANDOFF

## 현재 작업

- Step 11 (M4-b Outliner·Attribute Editor) 완료 — `docs/steps/step_11.md`. 헤드리스 175/175, GUI 107/107.
- `ui/attribute_editor.py` + `ui/ae_layout.py`: 사이드바 "Channel Box" 탭의 도크 모드(CB/LE ↔ AE, Ctrl+A), 노드 탭 transform/shape/history(모디파이어)/재질,
  Maya 템플릿 섹션(collapse 플래그 그대로). `ui/outliner.py`: 사이드바 "Outliner" 탭 UIList (DAG, Shapes 토글, 더블클릭 이름 변경, Parent/Unparent 버튼).
- 키: Object Mode Ctrl+A = AE 전환, Ctrl+Shift+A 전체 선택, Alt+D 선택 해제.
- Step 10 = `86f3c29` (개념 연산자), Step 9 = `fdab64b`.

## 바로 다음 할 일

- **Step 12 — M5 셸프** (사용자 번호; PLAN 표 #13): `research/maya/shelves.json` 팩토리 셸프(Poly Modeling 등)를 Blender 연산자 버튼으로
  (아이콘은 Blender 내장, Maya 아이콘 복사 금지), 셸프 탭 전환, 사용자 셸프(버튼 = Python 스크립트), 메뉴셋 F2–F6.
  - 근거: `research/maya/shelves.md`, `shelves.json`, `research/blender/api_limits.md` #11. 버튼 동작은 Step 7 `menu_map` 값 형식과
    Step 10 연산자(`maya_kit.create`, freeze, delete_history…) 재사용.
- 미뤄진 것: Range Slider·타임라인·`.` `,` 키, Status Line 입력 라인, 마킹메뉴 편집기, Step 10/11 「남은 것」 (PLAN 참고).
