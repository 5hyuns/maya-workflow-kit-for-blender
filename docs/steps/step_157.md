# Step 157 — Graph Editor keys in Maya terms

Backlog `autodrive_bmk/backlog_155.json` #3 (step_154_remaining.md item 3, step_140.md:93).

## 계획

Maya 근거 (Maya 2022 스크립트를 읽고 mayapy 로 측정, 동작만 기록; 코드 복사 없음):

- **Graph Editor Edit 의 키 명령** (`doCutKeyArgList.mel` / `doClearKeyArgList` / `doCopyKeyArgList` / `doScaleKeyArgList` /
  `doSnapKeyArgList`): Graph Editor 에서 부르고 (`fromGraphEditor`) 선택 키가 있고 option 이 "keys" 면 **선택 키**에 작동,
  아니면 시간 범위 × 노드. 주 메뉴 Key / Edit > Keys 는 `fromGraphEditor = 0` (`defaultRunTimeCommands.mel:958, 997`) 이라
  지금처럼 Channel Box 노드 기준이 맞다.
- **Keys > Add / Remove Inbetween** (`loadAnimMenuLibrary.mel` `doKeyEdit`): 현재 시간 이후 키를 ±1 프레임
  (`keyframe -time "t:" -relative -timeChange ±1 -option over`), 대상 = Graph Editor 에 보이는 곡선 (main list connection) —
  Channel Box 노드가 아님.
- **Keys > Mute / Unmute Key** (`doMuteKey`): 선택 키의 곡선 채널에 mute 노드, mute 속성을 선택 키 시간에 1 (step 키), 바로
  다음의 선택 안 된 키에 0. mayapy (`tmp/maya157/mute2.py`): 키 10 을 mute → 10–20 동안 키 10 의 값 유지, 20 부터 곡선 그대로;
  10 과 20 을 mute → 10–30 동안 5 유지; 마지막 키 mute → 그 뒤 유지. Unmute = 그 시간에 0.
  Blender 에는 키별 mute 가 없지만 **Stepped F-modifier + 제한 범위** (step = 아주 큼, offset = 시작 키, 범위 = [시작, 다음
  안 mute 된 키 − 0.001]) 가 같은 값을 낸다 (측정: 1, 5, 9, 10, 12, 15, 19, 19.99, 20, 25, 30 프레임이 Maya 와 같음).
  modifier 이름 `"Maya mute"` 로 킷 것임을 표시; mute 된 키 = 킷 modifier 범위 안의 키 → mute 집합 ± 선택 → 연속 구간마다
  modifier 를 다시 만든다.
- **Select 메뉴** (`graphEditorPanel.mel:903-945`): All / Only Curve = `selectType` 프리셋, Curve / Key / In Tangent / Out
  Tangent = 고를 수 있는 종류 체크 (optionVar → 킷 add-on pref). Blender 에는 Graph Editor 선택 마스크가 없다 →
  **0.05 s 타이머가 새로 선택된 요소만 걸러낸다** (이전 선택 플래그와 numpy 비교): Key 가 꺼져 있고 Curve 가 켜져 있으면
  새로 골라진 키의 곡선 전체를 고르고 (Maya 곡선 선택 = 곡선 전체가 움직임), 아니면 그 키를 놓는다; In / Out 이 꺼져 있으면
  새로 골라진 왼 / 오른 핸들을 놓는다. 마스크가 모두 켜져 있으면 아무것도 안 한다. (delegated: 키맵 가로채기 대신 타이머 —
  클릭 / 박스 / 올가미 모두에 같은 규칙, 최대 50 ms 늦게 반영.) Pre-Select Highlight 는 Blender Graph Editor 에 hover
  강조가 없어 회색 + 알림.
- **Default In / Out Tangent** (`doSetDefaultTangent` 류, `keyTangent -e -global -itt/-ott`; Maya factory auto / auto,
  research/maya/defaults.json:22-23): Blender 환경설정은 쓰지 않는다 (#40) → 킷 add-on pref `default_in_tangent` /
  `default_out_tangent`, 킷이 키를 만드는 곳 (S / Shift+W/E/R / Channel Box Key / 킷 Auto Key) 에서 새 키에 적용. Auto =
  Blender 기본 (Auto Clamped) 이라 손대지 않음.

레인: 메뉴 맵 / notices / prefs 가 모든 기능에 공유되어 구현은 한 레인 (순서 필요: 기능 → 메뉴 연결 → 개수). 검증 레인
(헤드리스 + GUI) 만 따로.

## 한 것

- `operators/graph_key_menu.py` (새): 선택 키 버전 Delete / Cut / Copy / Paste / Scale / Snap, Add / Remove Inbetween
  (`allset.graph_inbetween`), Mute / Unmute Key (`allset.mute_key`, Stepped F-modifier "Maya mute"), Select 마스크
  (`allset.graph_select_type` All / Only Curve + 0.05 s `_mask_tick`), Default In / Out Tangent (`after_insert`).
- `option_windows_edit.py`: Delete / Cut / Copy / Paste / Scale / Snap Keys 창이 Graph Editor · Dope Sheet Edit 메뉴 상자에도
  붙음 (`_paths`); 키 편집기에서 선택 키가 있고 Method Keys 면 선택 키에 (Maya fromGraphEditor 규칙), 아니면 그대로 노드 범위.
  Paste 는 마지막 복사가 편집기 버퍼면 `graph.paste` / `action.paste` + 시간 / 값 오프셋 · Copies · Insert (`_clip`).
- `preferences.py`: `graph_select_curve/key/in/out`, `default_in_tangent` / `default_out_tangent` (Maya factory Auto).
  Blender 환경설정은 여전히 안 씀 (#40).
- 기본 탄젠트 적용 지점: `channel_box.keyframe` (S, Shift+W/E/R, Channel Box Key), 킷 Auto Key, Key > Set Key on
  Translate / Rotate / Scale (메뉴 · 셸프를 `allset.set_key(channels=...)` 로 바꿈). 한쪽만 다르면 Linear = Vector 핸들,
  Flat = Free 핸들 수평, Stepped (out) = Constant (delegated: Blender 보간은 키 뒤 구간 것이라 이전 키는 건드리지 않음).
- 메뉴: Graph Editor Select All / Only Curve / Curve / Key / In / Out Tangent, Keys Mute / Unmute / Add / Remove Inbetween,
  Tangents Default In / Out 전부 (Flat 포함) — Dope Sheet 도 Keys / Default Tangent. notices: 쓰이지 않게 된 Keys /
  Default Tangent / Select 규칙 정리, Pre-Select Highlight · Add Key Tool 만 회색 알림.
- 근거 명세: `research/maya/re/graph_keys_157.md` (MEL 읽기 + mayapy mute 측정).

## 검증

- `tests/test_step157_graph_keys.py` 13/13: Mute 값이 mayapy 숫자와 같음 (키 10 / 1 / 10+20 / 30, 11 프레임), Unmute, Dope
  Sheet Mute, Inbetween, 창 연결 12 경로, Delete 창 선택 키 vs 노드, 주 메뉴는 노드, Scale / Snap 선택 키, Copy → Paste
  (값 오프셋), 마스크 필터, 프리셋, 기본 탄젠트 (Flat in / Stepped out / Auto / Linear), 메뉴 맵.
- 헤드리스 전체 1447 / 1449 → 실패 2 (step103 OPTION_BOXES 가 편집기 메뉴 상자를 모름, step104 기본 탄젠트 기대값) 를 새 동작에
  맞춰 고침 → 해당 + step140 / 101 / enable_disable 105/105.
- `tools/menu_count.py`: Graph Editor 145 → **154 / 229 (67 %)**, Dope Sheet 120 → **124 / 181 (69 %)**, 알림 없는 회색 0.
- GUI `-k gui_step157,gui_step150,gui_step70` 26/26 — 새 `gui_step157_graph_keys`: Only Curve 클릭 = 곡선 전체, All 클릭 = 그 키,
  Mute 스크린샷 `tmp/shots157/gui_step157_muted.png` (키 10–20 수평 유지 후 곡선 복귀, Maya 와 같음) 눈으로 확인.
- GUI 전체 묶음은 돌리지 않음 (사용자 규칙 10-24: release prep 에서만, 훅이 막음).

## 남은 것

- 마스크는 타이머 필터라 최대 50 ms 늦게 반영; Curve 를 끄더라도 Blender 의 곡선 선 클릭 (곡선 전체 키) 은 박스 선택과 구별이
  안 돼 걸러지지 않음. Pre-Select Highlight (hover 강조) 없음.
- Mute 는 Channel Box 의 mute 색 (Maya 갈색) 으로 아직 안 보임 — 158 Channel Box Mute / Unmute 와 함께.
- 기본 탄젠트가 Auto 일 때는 Blender 새 키 그대로 (끝에 붙은 키가 이전 키의 Constant 보간을 물려받는 Blender 동작 포함).
  Blender 자체 연산자 (I, Key > Set Key on Animated 등) 로 만든 키에는 적용 안 됨.
- Paste 창 「Selected keys override specified time range」 는 여전히 회색 (편집기 버퍼 Paste 는 현재 시간 기준).
- 5.x 에서 FModifier `name` 검증은 안 함 (4.5 만 실행).
