# HANDOFF

## 현재 작업

- Step 9 (M3-b 핫박스 + 마킹메뉴 엔진) 완료 — `docs/steps/step_9.md`. 헤드리스 130/130, GUI 90/90.
- 엔진 로직 `src/maya_kit/marking/engine.py` (bpy 없음), 그리기 `marking/draw.py`, 모달·핫박스·존 연산자 `marking/modal.py`, 정의 `marking/menus.py` (마킹메뉴 13 + 핫박스 존 5). 환경설정 Marking Menus(엔진/파이), Hotbox Style, Show All Menu Sets. Space = `maya_kit.hotbox` (6개 에디터).
- Step 8 = `078a6f9` (파이), Step 7 = `dc31143`.

## 바로 다음 할 일

- **Step 10 — M4-a 개념 레이어 (연산자)** (사용자 번호; PLAN 표 #11): Freeze Transformations(Maya 의미: 피벗 위치 보존, 변환을 메시에 굽고 Channel Box 0/1), Center Pivot, Delete History(모디파이어 적용+정리, By Type), Reset Transformations, 생성 시 Maya 명명 등.
  - 근거: `research/maya/concepts.md` §4–§5, §13–§14, `research/blender/concepts.md`, decision 2 (부모 지정 Maya 방식).
  - 메뉴 연결: Step 7 `ui/menu_map.py` 의 Modify/Edit 회색 항목(Freeze/Reset/Delete by Type…)과 Step 8 마킹메뉴(A 홀드 메뉴: Delete History, Freeze 등 `buildSelectAllMM`)에 새 연산자를 연결. Modify 의 Pivot 섹션(Center Pivot)은 메뉴 데이터에 없음(동적 라벨) → `menu_map` 에 추가 항목 방식 필요.
  - 행렬 수학 → step_10.md 「계획」 먼저.
- 미뤄진 것: Range Slider·타임라인·`.` `,` 키, Status Line 입력 라인, 마킹메뉴 편집기 (PLAN 참고).
