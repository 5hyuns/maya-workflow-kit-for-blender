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

## 한 일

레인 A (`a6bd509`, worktree 에이전트) — #99 링 (`marking/engine.py`, `draw.py`, `menus.py`):
- Maya 측정 (`research/maya/re/marking_ring_151.md`, 14 / 15 캡처 픽셀): R = 55, d = round(55·cos45°) = 39 — N / S 상자 중심 ±55,
  E / W 상자 가까운 변 55, 대각선은 가까운 세로 변 39 · 바깥 가로 변 39 (NE 상자 = 위 18–39 px). 상자 높이 21 (안 19), 1 px 검은 테,
  #525252. 폭은 고정이 아니라 글자 + 양쪽 25 px (옵션 상자 + 5 px) — 이슈의 "고정 폭" 은 캡처 측정으로 틀림 (Vertex 85, UV 67).
  하위 메뉴 화살표 4 × 7 px 삼각형 (오른쪽 여백 안). Maya 2022 의 RMB "UV" 는 하위 메뉴 (E UV, S UV Shell, `dagMenuProc.mel:989-1006`).
- `Params` ring_h 21 / ring_pad 25 / ring_opt 5 / ring_list_gap 21 (UI 배율), `Layout.ring_rect` 가 Maya 규칙, `has_arrow`, RMB_MESH E =
  UV 하위 메뉴, `fit_ring` 장애물 규칙 하나 (작아진 링에서 pivot 메뉴 줄이 SW 상자 위로 오던 것). 테스트 `test_step66_uv` /
  `test_step8_marking_menus` / `gui_manual_sweep` M66-1 은 UV 하위 메뉴에 맞춤.

레인 B (`44789cf`, worktree 에이전트) — Ctrl+E 매니퓰레이터 (`ui/in_view.py`, `operators/extrude.py`):
- 손잡이: X 빨강 / Y 초록 / Z (법선) 파랑 화살표 = Local Translate X / Y / Z, 화살표 끝 너머 크기 상자 = Local Scale X / Y / Z, 평면
  사각형 3 개 = 두 축 이동, 가운데 사각형 = 균일 크기; 놓을 때 `set_params` 한 번 = undo 한 단계, 툴팁 없음 (`use_tooltip = False`).
- polyExtrudeFace Local Translate X / Y, Local Scale X / Y / Z 를 bmesh 로 (mayapy 42 경우, 오차 ≤ 2e-4; 스크립트
  `research/scripts/extrude_manip_151_mayapy.py`, `_mayapy2.py`): 면마다 frame (Z 법선, X = 월드 X 를 면에 투영), 크기는 면 정점 평균
  기준, 공유 정점은 면 이동의 평균.
- `operators/preselect.py` `_extrude_block` → `in_view.handles_hit` (레인 범위 밖 수정 — 사전 선택 기즈모가 새 손잡이를 가로채서, 받아들임).
- delegated: Maya 회전 고리 · world/local 아이콘 없음, 새 값은 매니퓰레이터만 바꿈 (In-View Editor / CB INPUTS 행 추가 안 함), In-View
  상자 위치 70 → 150 px.

메인 — #98 / #100:
- #98: `ui/manipulator.py` `_new` / `_dial` 의 모든 손잡이 `use_tooltip = False`.
- #100: Shift+W / E / R = `allset.set_key(channels=TRANSLATE / ROTATE / SCALE)` (IC `keyframe_insert_by_name` 의 "Successfully added ...
  keying set" 대신; `keymap/mapping.py` SetKeyTranslate / Rotate / Scale 행 KIT), S 의 "Key: N channel(s)" 보고 없앰 (Maya 는 조용함),
  IK Handle = Command Line 결과 칸 "Result: ikHandle1" (`command_line.show_result`, Blender effector 설명 문구 삭제), Insert 의 "Pivot edit
  on/off" 보고 없앰. 상태 줄: `template_status_info` 를 그리지 않음 — "Active object has non-uniform scale / negative scale" 는 Blender
  상태 정보의 경고 (blender.exe 문자열로 확인, 4.5) 이고 Maya 상태 줄은 Help Line + Command Line 뿐 (delegated: 장면 통계도 같이 빠짐,
  Maya 는 HUD). 재생 중에는 `template_running_jobs` 를 그리지 않음 ("Anim Player").

## 검증

- 레인 A: 헤드리스 91/91 + 85/85, GUI (UI 1.0) step52 / 136 / 151 40/40; 상자 폭 · 위치 Maya 와 ±1 px (Object Mode 117 vs 122 = 글꼴).
- 레인 B: 헤드리스 79/79, GUI step65 / 151_extrude / 74 / 139_shape 30/30.
- 병합 뒤 헤드리스 전체 1368/1368 (`test_step151_texts` 5 포함: 툴팁 꺼짐, Shift+W/E/R 채널, IK 결과, Pivot 보고 없음, 상태 줄).
- GUI 관련 파일 한 번 (`-k step151,step52,step136,step65,step74_preselect,step59_manip,step7_top,step56_time`) 98/98 / 11 파일 —
  `gui_step151_tooltip`: X 화살표에 1.6 s 멈춰도 커서 옆 상자 변화 0 % (손잡이 노랑 강조 확인). 스크린샷 `tmp/shots151/`: RMB 링을 Maya 14 와,
  Ctrl+E 매니퓰레이터를 Maya modeling_03 과 나란히 봄. GUI 전체 묶음은 돌리지 않음 (규칙: release prep 에서만).

## 남은 것

- 링: 목록 줄 높이 (Maya 20 vs 킷 22), 가운데 원 / dead zone, 옵션 상자 글리프 8 vs 11 px, Shift+RMB 항목 아이콘.
- 매니퓰레이터: Maya 회전 고리, world/local 토글, 새 Local Translate X/Y · Local Scale 값이 In-View Editor / Channel Box 에 안 보임;
  비균일 스케일 물체는 근사.
- 상태 줄: Blender 의 장면 통계도 사라짐 (Maya HUD 의 Poly Count 는 따로 — 152 에서 볼 것).
