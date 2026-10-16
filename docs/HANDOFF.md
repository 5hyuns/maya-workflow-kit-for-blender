# HANDOFF

## 현재 작업

- Step 10 (M4-a 개념 연산자) 완료 — `docs/steps/step_10.md`. 헤드리스 160/160, GUI 100/100.
- 연산자 `src/maya_kit/operators/`: `freeze.py` (Freeze/Reset/Center Pivot; 피벗 = 원점, `delta_location` = Maya 피벗 오프셋),
  `parenting.py` (P/Shift+P, Parent Mode), `duplicate.py` (Ctrl+Shift+D, Shift+D), `history.py` (Alt+Shift+D, Delete (All) by Type),
  `create.py`+`naming.py` (Create 메뉴 = 원점·Maya 크기·pCube1/pCubeShape1), `units.py` (Maya Units 옵션 + load_post).
- 메뉴: `menu_map.EXTRA` 로 Modify Pivot 섹션(Center Pivot) 추가. A 홀드 + LMB = 마킹메뉴 `buildSelectAllMM`.
- Step 9 = `fdab64b` (핫박스·엔진), Step 8 = `078a6f9`, Step 7 = `dc31143`.

## 바로 다음 할 일

- **Step 11 — M4-b Maya식 Outliner·Attribute Editor** (사용자 번호; PLAN 표 #12): UIList 기반 Outliner 패널(DAG 계층, shape 표시 토글,
  더블클릭 이름 변경, MMB 드래그 부모 지정 = `operators/parenting.set_parent_maya` 재사용), Attribute Editor 노드 탭
  (transform: 채널 + Delta(피벗) / shape: 데이터 / 입력: 모디파이어 = history).
  - 근거: `research/maya/attribute_editor.md`, `ae_templates.json`, `research/blender/api_limits.md` #2–#3.
- 미뤄진 것: Range Slider·타임라인·`.` `,` 키, Status Line 입력 라인, 마킹메뉴 편집기, Step 10 「남은 것」 (PLAN 참고).
