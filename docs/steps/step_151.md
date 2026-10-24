# Step 151 — Manipulators, rings and texts like Maya (#98 #99 #100, audit 9)

## 계획

- **#99 링**: RMB marking menu 의 상자가 누른 점에서 ~80 px (Maya ~55 px, Edge 상자 중심 55 px 위), 상자 폭이 글자 길이 (Maya 는 고정 폭,
  UV 에 하위 메뉴 화살표). 근거 `research/maya/screens/14_marking_menu_object.png` (누름 815, 459; Edge 404; Vertex / UV 상자 99 px),
  `15_marking_menu_shift_rmb.png`.
- **Ctrl+E 매니퓰레이터**: 킷은 로컬 Z 화살표 하나 (`ui/in_view.ALLSET_GGT_extrude`). Maya 는 세 축 화살표 · 평면 손잡이 · 가운데
  상자 · 축별 크기 상자 (`research/maya/screens/audit7/maya/c01_model_extrude.png`). polyExtrudeFace 의 Local Translate / Scale 에
  묶는다 (step 65 `Record` / `allset.extrude_edit`).
- **#98**: Move / Scale 매니퓰레이터에 Blender 툴팁 "Move selected items" — Maya 매니퓰레이터는 툴팁 없음.
- **#100**: 상태 표시줄의 Blender 보고 문구 (keying set, "Blender has ...", non-uniform scale, Anim Player) → Maya 말 또는 조용히.

레인 (파일이 겹치지 않게, delegated; 동시에 에이전트 2 개 = PC 부하 규칙):
- **A — 링** (worktree 에이전트): `marking/engine.py`, `marking/draw.py`, engine 테스트.
- **B — Ctrl+E 매니퓰레이터** (worktree 에이전트): `ui/in_view.py`, `operators/extrude.py` (필요한 만큼), 테스트.
- **C — 메인**: #98 (`ui/manipulator.py`), #100 (보고 문구: `operators/skin.py` 등), 통합 · 검증 · 커밋. A / B 가 도는 동안 메인은
  포그라운드 에이전트를 기다리므로 C 는 그 뒤 (에이전트 호출이 동기).
