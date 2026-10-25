# Step 203 — Graph Editor depth 3 (backlog #2, Issue #110)

## 계획

근거: `docs/steps/step_201_remaining.md` §8 #1, `research/maya/screens/editors104/_editors104.json`, `step_198.md` 「남은 것」.
지금 Graph Editor 167 / 229, Dope Sheet 139 / 181 → 목표 ≥ 180 / ≥ 150.

먼저 (사용자 결정 10-25 의 첫 작업): 공용 Blender 슬롯 잠금 `tools/blender_slots.py` — 커밋 a162a62 「QA: blender slots」.

대상 (두 편집기 공통이 대부분): List > Load / Add Selected Objects, Graph Editor Curves > Pin / Unpin Channel, List > Show Upstream
Curves (GE), Hierarchy Below (DS), Show > Attributes 필터 (Hidden, Driven by Anim Curve / Expression / Driven Key, User Defined;
Published = 컨테이너 없음 → 회색 유지 검토), Show > Objects > IkHandles / Sets (+ DS Characters), Edit > Select Curve Nodes, Curves >
Change Rotation Interp 5, Key Sync Filter, Peak Removal Filter.

레인 (delegated; 레인 ≤ 4, Blender ≤ 2 = `blender_slots`, Maya ≤ 1). 측정과 구현에 의존이 있어 두 차례:
- 1 차: **M** (에이전트, Maya 만) GUI Maya 로 List / Pin / Show 동작, mayapy 로 Rotation Interp · Key Sync · Peak Removal 결과 →
  `research/maya/re/graph_editor_201.md` + 데이터. **B** (에이전트, Blender 헤드리스) kit outliner 쪽 (`ui/editor_chrome.py`,
  `ui/editor_menu_map.py`, `ui/notices.py`) 을 Maya 문서 [K] 로 먼저 구현, 가정 목록을 남김.
- 2 차: **C** (에이전트) M 의 데이터로 커브 명령 (`operators/graph_curves_203.py`); 메인 = B 의 가정을 M 명세와 맞춤, GUI 확인.
