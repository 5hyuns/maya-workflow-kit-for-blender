# Step 150 — Graph Editor in Maya terms (#96)

## 계획

이슈 #96 (감사 9): Graph Editor 에서 (1) visibility 채널이 "Hide Viewport", (2) 모든 속성 줄이 선택 파랑, (3) 길이 곡선이 미터로
그려져 Translate 가 Scale 옆에서 납작, (4) 킷 outliner 가 pose bone / shape key 곡선을 안 보이고 스크롤이 없음, (5) View / Show 메뉴
47 항목이 회색, (6) 2D 편집기에서 Ctrl+A 가 select all (Maya 는 AE / Channel Box).

Maya 기준: `research/maya/screens/audit7/maya/e02_graph_editor_win1.png` (pCube1 줄만 파랑, Translate X / Y 는 축 색 기울임꼴),
`research/maya/screens/graph/graph_00_frame_all_ge.png` (Translate X 0 → 5 → 0 곡선, 세로 눈금 Maya 단위),
`research/maya/screens/editors104/_editors104.json` (View / Show 메뉴, 체크 상태).

레인 (파일이 겹치지 않게, delegated):
- **A — View / Show 메뉴** (worktree 에이전트): `ui/editor_menu_map.py`, 새 `ui/graph_view.py`, `ui/notices.py`, 테스트
  `tests/test_step150_menus.py`. Blender 가 할 수 있는 것 연결 (Auto Frame, Curve Name 그리기, 버퍼 곡선 = ghost curves 등),
  나머지는 notice.
- **B — 킷 outliner** (worktree 에이전트): `ui/editor_chrome.py` + `tests/test_step150_outliner.py`. Maya 이름 (Visibility ...),
  Maya 식 줄 강조 (outliner 에서 고른 줄만), pose bone / shape key 노드, 스크롤 연산자.
- **C — 메인**: Ctrl+A / 스크롤 키맵 (`keymap/maya_patches.py`, `keymap/mapping.py`), 곡선 높이 (미터) 조사, 통합 · GUI 비교 · 커밋.
  키맵은 B 의 연산자 이름에 기대므로 B 다음 (keymap 파일은 한 레인만 고친다).

곡선 높이 (3) 조사 메모: Blender 의 Graph Editor 는 곡선을 `ANIM_unit_mapping_get_factor` 로만 변환해 그리고, 이 함수는 회전
(라디안 → 도) 과 Normalize 만 다룬다 (길이 단위 · `scale_length` 없음). Python 에서 F-curve 별 표시 배율을 줄 방법이 없다 — 아래
「한 일」 에 확인 결과.

## 한 일

레인 A (`ed99d75`, worktree 에이전트) — Graph Editor View / Show 메뉴:
- 새 `ui/graph_view.py`: View > Auto Frame (선택이 바뀌면 각 Graph Editor `graph.view_all`, 0.25 s 타이머), Auto Frame Time
  (시간 축만: `anim.scene_range_frame` 에 키 범위 + 5 % 를 preview range 로 한 번 주고 바로 되돌림), Curve Name Always / Never /
  Active Only (곡선 색 "pCube1.translateX" 를 마지막 키 위에, Normalized View 에서는 안 그림). 애드온 설정 `graph_auto_frame` (켬,
  Maya 공장값), `graph_auto_frame_time` (끔), `graph_curve_names` (Never) — Blender 설정은 쓰지 않음.
- Show > Objects / Attributes > Clear Below (`allset.graph_show_clear`), Subdiv Objects = `show_meshes` (delegated).
- 회색으로 남는 항목은 항목별 notice (Undo View Change, Clip Time, Show Results, Show Buffer Curves → Curves > Buffer Curve >
  Snapshot 의 ghost curve, Play Range Shades, Highlight Affected Curves, Keys > Never, Key View, Time Ruler Placement, Simple
  Toolbar, Driven by ..., User Defined, Clips, Characters). Buffer Curves 체크를 ghost curve 에 묶지 않은 이유: ghost curve 는 숨긴 채
  보관할 수 없어 체크 상태가 거짓이 된다 (delegated).
- menu_count: Graph Editor 137 → 145 작동, 회색 92 → 84 (notice 없는 회색 0); Dope Sheet 117 → 120 (Show 공유).

레인 B (`c8d9a74`, worktree 에이전트) — 킷 outliner (`ui/editor_chrome.py`):
- 이름 = Channel Box 표 (`channel_box.MAIN`): `hide_viewport` → Visibility, `hide_render` → Primary Visibility (delegated),
  속성 줄은 Maya 순서 (translate, rotate, scale, visibility, 나머지).
- 강조: outliner 에서 고른 줄만 (`_picked`, 장면 선택이 바뀌면 지움; 아무것도 안 골랐으면 선택된 노드 줄만, 속성 줄은 안 칠함).
- 노드: 애니메이션 있는 pose bone = JOINT 줄, shape key = blendShape 노드 + 타깃 줄 (`compat.id_fcurves(key)`).
- 스크롤: `allset.graph_channel_scroll(delta)` (영역마다 오프셋, 스크롤 막대).

메인:
- `keymap/maya_patches.py`: Ctrl+A = `allset.ae_toggle`, Ctrl+Shift+A = 전체 선택 — Graph Editor / Dopesheet / NLA Editor /
  Animation Channels (`CTRL_A_MODES`, step 141 규칙). 휠 = `allset.graph_channel_scroll` 을 "View2D" 맨 앞에: 채널 영역의 휠은
  "View2D" 가 받고 "Animation Channels" 까지 가지 않는다 (`--debug-handlers` 로 측정 — 처음 "Animation Channels" 에 둔 항목은 GUI 에서
  0 → 0). 연산자 `invoke` 는 킷 Graph Editor 의 CHANNELS 영역이 아니면 PASS_THROUGH.
- `keymap/mapping.py` Ctrl+A 행 메모, `docs/keymap_mapping.md` 재생성, `tests/test_keymap_maya._STACKS` (View2D, NLA Editor).
- 곡선 높이 (미터): F-curve (`FCurve` 속성: color, hide, modifiers ...) 에도 `SpaceGraphEditor` (`use_normalization` 뿐) 에도
  곡선별 표시 배율이 없고 (4.5 RNA 목록 측정), Blender 는 회전만 도로 바꿔 그린다 → Python 으로는 길이 곡선을 Maya 단위 높이로 그릴
  수 없다. 섞인 곡선 (Translate + Scale) 의 높이 비는 Blender 그대로; 길이 곡선만 보일 때는 step 137 의 Maya 단위 눈금 (마우스가
  편집기 위일 때). 대안 = View > Normalized View (연결됨). 한계는 「남은 것」 에.
- `tests/gui/gui_step150_compare.py`: Maya 재현 (Translate X 0 → 5 → 0, 프레임 1 / 10 / 20) + Frame All 스크린샷, Ctrl+A, 휠.

## 검증

- 레인 A: `tests/run.py -k step150_menus,step101,step104,enable_disable` 38/38, 더 넓게 (step54 / 114 / 130 / 70 / 92 / 137) 102/102,
  GUI `gui_step150_view` 4/4 (곡선 이름, Auto Frame 스크린샷 확인) + Graph Editor 관련 GUI 36/36, 32/32.
- 레인 B: `-k step150_outliner,step104,enable_disable,step147,step130,step118` 46/46, GUI `step104_editors` 10/10,
  `gui_step150_outliner` 7/7 (스크린샷: pCube1 만 파랑, Translate X 빨강 / Y 초록 줄은 안 칠함 — Maya e02 와 같음).
- 병합 뒤 헤드리스 전체 1345 / 실패 1 (`test_keymap_maya` 그림자 검사: NLA Editor / View2D 스택 없음) → 고친 뒤 keymap · enable_disable ·
  step130 / 141 / 104 / 147 / 150 86/86.
- GUI `gui_step150_compare` 5/5: outliner pCube1 > Translate X, Graph Editor 위 Ctrl+A → Attribute Editor, 휠 → 킷 줄 0 → 3.
  스크린샷 `tmp/shots150/gui_step150_graph_frame_all.png` 를 Maya `research/maya/screens/graph/graph_00_frame_all_ge.png` 와 나란히
  봄: outliner (pCube1 만 파랑, Translate X 빨강) · 곡선 모양 같음; 세로 눈금은 0.00–0.05 (마우스가 편집기 밖, 위 한계).
- GUI 전체 묶음 (커밋 전 한 번): 1614 통과 / 실패 1 / 142 파일 (GUI_SKIP 2) — 실패 `gui_step143_user` #82 Grid 상자 클릭, 혼자 다시
  돌리면 15/15 (불안정, 150 과 무관).

## 남은 것

- 섞인 곡선의 높이: Translate (미터) 가 Scale 옆에서 Maya 보다 납작하다 — Blender 4.5 에 곡선별 표시 배율이 없어 Python 으로 못 고침
  (위 「한 일」). 길이 곡선만 보일 때의 Maya 단위 눈금은 마우스가 편집기 위일 때만 (step 137).
- Dope Sheet View > Auto Frame 은 회색 그대로 (watcher 는 Graph Editor 만).
- Curve Name 의 Maya 실제 글자 / 위치는 캡처에 없어 미확인 ("node.attribute" 형식은 delegated).
- outliner 노드 줄에 Maya 노드 아이콘 없음, 속성 줄 글자는 기울임꼴 아님, blendShape / joint 는 위계 없이 맨 위 줄.
