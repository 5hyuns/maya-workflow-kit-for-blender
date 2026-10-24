# Step 158 — Channel Box menus complete (+#97)

Backlog `autodrive_bmk/backlog_155.json` #4 (step_154_remaining.md BS2, items 6 / 7).

## 계획

Maya 근거: research/maya/channel_box.md §2.4 (`generateChannelMenu.mel:87-178`), §2.5 (`generateCBEditMenu.mel`), :35
(RMB 어디서나 = Channels 팝업, Ctrl+RMB = Edit 팝업, `initChannelBox.mel:533-539`); Maya 2022 `channelBoxCommand.mel`
(읽기만): -breakdownall / -muteall / -unmuteall = 보이는 모든 채널 (selectedOnly false), -cut / -copy / -delete =
`cutKey / copyKey -t ":" -f ":"` (곡선 전체), -paste = `pasteKey -connect true -time <현재>`, Freeze = `makeIdentity -apply`
t / r / s / all, -selectConnection = 입력 노드를 고름 (`CBselectConnection`), anim curve 는 Graph Editor (`CBanimCurve`).

1. **RMB / Ctrl+RMB**: `allset.cb_channel_drag` (창 modal, UI 버튼 처리보다 먼저) 가 Channel Box 칸 위만이 아니라 Channel
   Box 부분 전체 (dock 의 위쪽 `cb_share`) 에서 시작되고, RMB = `ALLSET_MT_cb_channels`, Ctrl+RMB = `ALLSET_MT_cb_edit`.
   빈 곳에서도 Blender 메뉴 대신 이 메뉴.
2. **Channels 메뉴 = Maya 순서 전체**: Key Selected / Key All Keyable / Breakdown Selected / Breakdown All / Mute Selected /
   Mute All / Unmute Selected / Unmute All · Sync Selection in Graph Editor / Sync Timeline Display (체크) · Cut / Copy /
   Paste / Delete Selected · Duplicate Values · Freeze > Translate / Rotate / Scale / All · Break Connections / Select
   Connection · Lock … Make Selected Keyable · Add to / Remove From Selected Layers (Blender 4.5 에 애니메이션 레이어 없음 → 회색 +
   이유).
   - Cut / Copy / Paste Selected: 킷 채널 클립보드 (선택 채널의 곡선 전체, 노드별), Paste = 현재 시간에 곡선 시작을 맞춰
     붙임 (Maya `pasteKey -time <current>`, 기본 merge).
   - Sync Selection in Graph Editor (add-on pref `cb_sync_graph`, Maya factory off): 켜면 채널 선택이 F-curve 선택으로
     따라가고, S 는 선택한 채널만 키 (Maya setKeyframeWhich 1). Sync Timeline Display (`cb_sync_timeline`): Time Slider 의
     키 표시가 선택 채널만.
   - Select Connection: driver → 대상 객체 선택, constraint → 대상, 곡선 → 그 F-curve 만 선택하고 Graph Editor 창 (delegated:
     Blender 곡선은 노드가 아니다).
3. **SHAPES 채널**: SHAPES 줄 (조명 Color / Intensity / Cone Angle / Penumbra Angle, 카메라 Focal Length …, 래티스) 도 고를 수
   있는 채널 (`sh:<prop>` 키): 이름 클릭 / 드래그 선택, Key / Breakdown / Mute / Delete / Break, 상태 아이콘. 키는 실제
   Blender 경로에 (Intensity = `energy`, Color R = `color[0]`, Cone / Penumbra = `spot_size` + `spot_blend`).
4. **Spot light**: Maya spotLight keyable `coneAngle` (40) / `penumbraAngle` (0) 줄 (mayapy 확인 예정). Blender
   `spot_size` = 바깥 원뿔, `spot_blend` = 부드러운 비율 → cone c, penumbra p ≥ 0: size = c + 2p, blend = 2p / (c + 2p);
   p < 0: size = c, blend = 2|p| / c (부호는 광원의 `allset_penumbra` 에 기억).
5. **#97**: Bind Skin 이 Armature modifier 이름을 장면 전체 다음 `skinClusterN` 으로 짓고, INPUTS 줄은 AE 와 같은
   `attribute_editor.modifier_node` 이름 (Blender 자동 이름 → Maya `<type><n>`).

레인: 모두 `ui/channel_box.py` 를 고쳐 한 레인 (같은 파일 충돌), lights.py / skin.py 는 작아 같이. 검증만 따로.

## 한 것

- **RMB / Ctrl+RMB**: `allset.cb_hover` 가 Channel Box 칸이 아닌 곳 (dock 의 Channel Box 부분, `in_channel_part`) 에서도 창
  modal `allset.cb_channel_drag` 를 띄우고, 그 modal 이 RMB = Channels 메뉴, Ctrl+RMB = `ALLSET_MT_cb_edit` (선택 유지) 를
  연다 — 빈 곳 RMB 에 Blender 메뉴가 더는 안 뜸 (`ui/channel_box.py` `_on_rmb(edit=)`, `_is_cb_dock`).
- **Channels 메뉴 = Maya 순서 전체** (`ALLSET_MT_cb_channels` + `ALLSET_MT_cb_freeze`): 새 연산자 `ui/cb_channels.py` —
  `allset.cb_breakdown_all`, `cb_mute_all(mute)`, `cb_clipboard(CUT/COPY/PASTE)` (mayapy 규칙: 현재 시간에 시작, 값 연결,
  뒤 키 밀기; 곡선 없는 채널은 값 그대로), `cb_select_connection` (driver / constraint 대상 객체, 곡선 → 그 F-curve 만 선택 +
  Graph Editor). Freeze > T / R / S / All = `allset.freeze_transform`. Sync Selection in Graph Editor / Sync Timeline
  Display = add-on pref `cb_sync_graph` / `cb_sync_timeline` (채널 선택 → F-curve 선택, S 는 선택 채널만; Time Slider 키 표시 =
  선택 채널만). Add to / Remove From Selected Layers = 회색 + 알림 (Blender 4.5 애니메이션 레이어 없음 → NLA).
- **SHAPES 채널** (`sh:<prop>`): 이름 클릭 / 드래그 선택, Key / Breakdown / Mute / Delete / 붙여넣기, 상태 아이콘
  (`shape_owner` / `shape_paths` / `channel_fcurves` / `remove_channel_curves`). Light Intensity 키 = `energy`, Color R =
  `color[0]`, spot Cone Angle / Penumbra Angle = `spot_size` + `spot_blend`.
- **Spot Cone Angle / Penumbra Angle** 줄 (`lights.cone_penumbra` / `set_cone_penumbra`, Maya factory 40 / 0, 음수 penumbra
  = 안쪽으로 부드럽게, `allset_penumbra` 에 부호 기억).
- **Muted 상태**: `channel_state` 'MUTED' (아이콘 MUTE_IPO_ON; Blender UI 에 갈색 없음 — delegated).
- **#97**: Bind Skin (closest distance / Heat Map 둘 다) 이 Armature modifier 를 장면 전체 다음 `skinClusterN` 으로 이름 짓고
  (`skin.name_skin_cluster`, mayapy: skinCluster1 / skinCluster2), INPUTS 줄 이름 = `attribute_editor.modifier_node` (AE 와 같음).
- 근거: `research/maya/re/cb_menus_158.md` (MEL 읽기 + mayapy 붙여넣기 / 조명 속성 / skinCluster 이름 측정).

## 검증

- `tests/test_step158_cb_menus.py` 11/11: 메뉴 순서 · 항목 · 레이어 알림, Freeze, Breakdown / Mute All, Paste (mayapy 키 시간
  1 12 15 24 34 49 · 연결 값 · 곡선 없는 채널 15:0 24:5 34:2), Cut, Select Connection (driver / 곡선 / 없음), Sync Graph Editor
  (F-curve 선택 + S 선택 채널만) / Timeline, 조명 Intensity · Color 키 / 값 / mute / delete, spot cone / penumbra (±5),
  SHAPES 칸 선택, Bind Skin skinCluster1 / 2 / 3.
- 헤드리스 전체 **1460 / 1460**.
- GUI `-k gui_step158,gui_step148_cb` 11/11 — 새 `gui_step158_cb_menus`: 빈 곳 RMB → Channels 메뉴 → K (Key Selected) 로 Translate
  X 키, Ctrl+RMB → Edit 메뉴 (선택 유지), Color R 칸 클릭 = `sh:maya:colorR` 선택. 스크린샷 `tmp/shots158/` 눈으로 확인 (메뉴
  전체 + Freeze 하위 메뉴, Edit 메뉴). `gui_step148_cb` 는 메뉴가 길어져 창 위쪽으로 밀리므로 첫 줄 클릭 대신 밑줄 글자 K 로 고침.
- GUI 전체 묶음은 돌리지 않음 (사용자 규칙: release prep 에서만).

## 남은 것

- INPUTS 줄 (polyCube1 width …) 은 아직 고를 수 있는 채널이 아님 (SHAPES 만).
- Maya muted 갈색 / constraint 파랑 같은 칸 색은 Blender UI 로 못 칠함 (아이콘으로 표시).
- spot `dropoff`, shadow 속성 줄 없음 (Blender 에 대응 없음 / 렌더러별).
- Select Connection 의 곡선은 Maya 처럼 AE 에 animCurve 노드로 안 뜸 (Graph Editor 로 대신).
- Channels 메뉴가 길어 Blender 가 창 안으로 밀어 올림 — 메뉴 첫 줄이 마우스 아래 오지 않음 (Maya 도 화면 끝에선 같음).
