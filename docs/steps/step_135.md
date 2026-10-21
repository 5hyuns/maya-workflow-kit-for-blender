# Step 135 — Dock and Channel Box like Maya (#55 #60)

## 계획

backlog 2 (PLAN 「재점검 8차」 우선순위 2; `step_133_ui.md` #4 #8). 큐브를 선택하면 Channel Box 가 polyCube1 INPUTS 를 펼쳐 Layer Editor 를
밀어낸다 (1.25 에서 화면 밖, 1.0 에서 80 px). Maya 는 INPUTS / SHAPES 노드를 접은 채 보이고 이름을 눌러 펼치며, Channel Box / Layer
Editor 경계가 고정이다 (`research/maya/screens/11_channel_box.png`, `research/maya/channel_box.md`). Dock 은 278 px 로 고정인데 Outliner 는
배율을 따라 넓어져 탭 · 라벨 · AE 메뉴 줄이 잘린다.

### 레인 (병렬, worktree)

| 레인 | 이슈 | 파일 |
|---|---|---|
| CB | #55 INPUTS / SHAPES 접힘 + 이름 클릭으로 펼침, CB / Layer Editor 고정 분할 (Layer Editor 늘 보임) | `ui/channel_box.py`, `ui/maya_dock.py`, `ui/layer_editor.py` |
| WIDTH | #60 배율별 dock 폭 (step 132 #53 규칙: 불러온 그대로의 화면에서만), 탭 · 라벨 · AE 메뉴 줄 안 잘림 | `ui/toolbox.py` (fit_columns), 필요하면 `tools/make_startup.py` |

메인: 병합, 1.0 / 1.25 / 1.5 GUI 그림 (큐브 선택, Layer Editor 탭 보임, 잘린 라벨 없음) 을 Maya 11_channel_box 와 나란히, GUI 전체 한 번, 커밋.
두 레인은 파일이 겹치지 않는다 (dock 폭은 area 경계 이동 = toolbox.fit_columns 의 일, dock 안 분할은 maya_dock 의 일).

## 한 것

레인 2 개 (worktree; 세션이 몇 번 끊겨 WIP 커밋으로 이어 감) + 병합 뒤 메인의 수정. 레인 문서: `step_135_cb.md`, `step_135_width.md`.

- **CB** (#55, `step_135_cb.md`): Maya 2022 를 GUI 로 측정 (`research/maya/screens/cb135/`) — INPUTS 노드는 접힌 채, 이름 클릭으로 펼침 · 접힘,
  lead 가 바뀌면 다시 접힘, 카메라 / 라이트 SHAPES 는 펼친 채, 분할 0.48. 펼침 상태는 킷 파이썬 상태 (`channel_box._open`; modifier
  `show_expanded` 는 더 이상 쓰지 않음 — Properties 의 패널 접힘과 한 값이라 undo 단계까지 남았다), `allset.cb_node_toggle`. Channel Box
  부분은 킷 스크롤 창 (`Lines`, `window_lines`) 이라 Layer Editor 가 늘 고정 위치, dock 탭은 글자 폭 (lane WIDTH 와 맞춘 식).
- **WIDTH** (#60, `step_135_width.md`): `toolbox.fit_columns` 가 dock 폭도 배율에 맞춤 (불러온 그대로의 화면에서만, step 132 규칙) = 내용이
  필요한 폭 (탭 줄 · 가장 긴 채널 이름 · AE 메뉴 줄), 277 × 배율 이상 480 × 배율 이하; `make_startup.DOCK_PX` 466 → `startup.blend` 재생성.
- **병합 뒤 메인이 고친 것** (레인이 다 못 끝낸 GUI 실패):
  - 휠: `allset.cb_scroll` 이 "Property Editor" 에 있어 영역의 "View2D Buttons List" (먼저 처리, 영역 전체 스크롤) 에 먹혔다 → "View2D Buttons
    List" 맨 앞 (PASS_THROUGH), `tests/test_keymap_maya._STACKS` 에 그 순서.
  - ▲▼ 스크롤 단추를 lead 이름 줄로 옮김: 마지막 내용 줄을 차지하던 단추가 막 펼친 노드 줄을 대신해서 두 번째 클릭이 노드를 접지 못했다.
  - 분할 몫 `cb_share(region, u)`: 0.48 (Maya) 기본, 짧은 dock 에서는 큐브의 접힌 Channel Box (14 줄) 가 들어가게 최대 0.62 까지 (delegated).
  - 테스트: step 129 드래그 테스트가 이름 칸을 dock 폭의 30 % 에서 찾던 것을 값 칸 줄을 따라 찾게, step 135 dock 테스트의 탐색 간격 · 시간 한도 ·
    두 번째 클릭 전 대기 (더블클릭 시간) · 한 틱에 휠 하나.

## 검증

- 관련 헤드리스 `-k step135,step11,step38,step55,step129,step116,step106,enable_disable,step130`: 237/237 (병합 직후), 수정 뒤
  `-k step135,keymap,step130,enable_disable` 46/46.
- 관련 GUI `-k step135,step11,step38,step116,step129_channel,step62,step99,step113`: 1.25 96/96, 1.0 (`--ui-scale 0.8`) 수정 뒤 24/24
  (step135_dock + step129_channel), 1.5 (`--ui-scale 1.2`) step135_dock 13/13 · step129_channel 통과. 1.5 의 `gui_step113_top` 과
  `gui_step62_sdk` 실패는 step 135 전 커밋 2a1c963 에서도 같다 → #77.
- 그림을 직접 봄: 1.0 접힌 polyCube1 + Layer Editor (`tmp/s135/shots_0.8/s135_cube_collapsed_100.png`), 1.25 (`tmp/s135/shot125/`),
  1.5 (`tmp/s135/shot150/` — ▲▼ 가 이름 줄, Layer Editor 보임), Maya 대비 dock 폭 (`tmp/width135/side_first_screen.png`).
