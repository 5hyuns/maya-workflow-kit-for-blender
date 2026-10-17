# Step 56 — Time Slider·키 감각: LMB 스크럽·K 드래그·Time Slider RMB 메뉴·S·키 삭제/브레이크다운/복사

근거: `research/maya/workflows/animation.md` §1.1–1.2 (1–11), §2 (kit 지금: 1, 3, 4, 6–10), §3 갭 표 (1 K 16, 2 타임라인 LMB 15,
4 CB RMB 12, 5 Time Slider RMB 12, 6 MMB 불가 12, 8 S 10, 11 Set Breakdown 9, 12 Delete Keys 9, 13 Copy/Paste 9, 15 Shift 범위 9),
§4 (MMB 시간 이동 = 불가 → 안내), §5 키맵 위험 (K, 타임라인 LMB, S), `docs/keymap_mapping.md:200` (K = IC knife),
Maya `others/TimeSliderMenu.mel:858-1170` (Time Slider 메뉴 순서; 레이블 = `resources/MayaStrings` `m_TimeSliderMenu.*`),
`:300-370` (Cut/Copy = `timeControl -q -range` = 강조 범위, 없으면 현재 프레임), `:1179-1189` (키 없으면 편집 항목 회색).

## 계획

### 1. 타임라인 본문 LMB = 시간 (delegated)
- Maya Time Slider 는 어디를 눌러도 시간 이동 (animation.md:6), 키를 클릭으로 고르지 않음. Blender 타임라인 = Dope Sheet
  TIMELINE 모드라 본문 LMB = `action.clickselect` / 드래그 = `select_box` (IC:1403-1433).
- `maya_kit.time_scrub` (모달): "Dopesheet" 키맵 **맨 앞** LMB PRESS (Shift 변형 포함, `first=True`, `PASS_THROUGH_FIRST`),
  `space.mode != 'TIMELINE'` 이면 PASS_THROUGH (Dope Sheet 본문 LMB 는 Maya 에서도 키 선택이라 그대로).
  누름·드래그 = `frame_current` = 마우스 아래 정수 프레임 (`region.view2d.region_to_view`), 놓으면 끝. Esc/RMB = 시작 프레임으로.
- **Shift+LMB 드래그 = 범위** (Maya 빨간 범위, `kNoRangeError` "Use Shift-LMB to select a range"): 누른 프레임–마우스 프레임을
  `WindowManager.maya_kit_time_range` (on, start, end; SKIP_SAVE) 에 두고 타임라인 WINDOW POST_PIXEL 로 빨간 반투명 띠를 그림.
  보통 클릭은 범위를 지움. 범위 안 키 이동/스케일 (Maya 가운데·끝 화살표) 은 이번에 안 함 (남은 것).

### 2. Time Slider RMB = Maya 메뉴 (delegated)
- "Dopesheet" 키맵 맨 앞 RMB PRESS = `maya_kit.time_slider_menu` (TIMELINE 아니면 PASS_THROUGH) → `MAYAKIT_MT_time_slider`.
- 순서·레이블 (TimeSliderMenu.mel:873-1170): Cut / Copy / Paste ▸ (Paste, Paste Connect = 회색) / Delete / Snap / Keys ▸
  (Convert to Key, Convert to Breakdown, Add Inbetween, Remove Inbetween) / Tangents ▸ (Spline, Linear, Clamped, Stepped, Flat,
  Plateau, Auto) / — / Playback Speed ▸ / Playback Looping ▸ / Set Range to ▸ (Start/End, Min/Max, Selected) / — / Playblast...
  (Grease Pencil, Display Key Ticks, Time Display, Audio, Stepped Preview, Auto snap keys 는 생략 — Blender 대응 없음 / 낮은 가치).
- 대상 = Channel Box 대상 노드 (`channel_box.targets`: 선택 오브젝트, 포즈 모드면 선택 본) 의 F-커브 (본이면 그 본 경로만), 시간 =
  범위가 있으면 [start, end], 없으면 현재 프레임 (`timeControl -q -range`). 연산자 `maya_kit.time_keys(action=…)` 는 bpy 가 적은
  `operators/time_keys.py`:
  - DELETE: 범위 안 키 지움 (빈 커브는 지움). CUT = COPY + DELETE. COPY: 노드별 `(경로, index) → [(프레임 − 범위 시작, 값, 키 종류,
    보간)]` 를 모듈 클립보드에. PASTE: 현재 프레임에 (원본 노드 1 개면 모든 대상에, 여럿이면 순서대로; 커브 없으면 만듦).
  - SNAP: 범위 안 키 프레임 반올림. Convert to Key / Breakdown: `keyframe.type`. Add / Remove Inbetween: 현재 프레임 뒤 키를 ±1.
  - Tangents (Maya → Blender, animation.md:14 대응표): Spline = BEZIER + AUTO, Clamped / Plateau / Auto = BEZIER + AUTO_CLAMPED,
    Linear = LINEAR, Stepped = CONSTANT, Flat = BEZIER + 핸들 수평 (ALIGNED, 핸들 y = 키 값). 표 `TANGENTS` 는 step 67 (Graph Editor
    탄젠트 버튼) 이 다시 씀.
  - Set Range to: Start/End = 재생 범위 = 애니메이션 범위, Min/Max = 대상 키 처음–끝, Selected = Shift 범위 (없으면 보고).
  - Playback Speed: Real-time = `sync_mode` FRAME_DROP, Play Every Frame Max Real-time = NONE (Blender 는 fps 로 제한), Free = 회색
    + 안내. Playback Looping: Continuous 만 (Blender 는 늘 반복), Once / Oscillate 회색 + 안내.
  - Playblast... = Playback > Playblast 와 같은 항목 (`menu_run` render.opengl).

### 3. K = 어디서나 시간 드래그 (delegated)
- `taphold.TimeDragBinding` ("time_drag"): K PRESS → `maya_kit.tap_hold`; 누른 채 LMB 드래그 = 시간 (dx px × 재생 범위 / 영역 폭,
  Maya 감도 미측정 [U] → 영역 폭 = 재생 범위 한 번), LMB 를 먹으니 선택은 그대로, 탭 = 아무것도 안 함, Esc/RMB = 시작 프레임.
  tap_hold 는 transform 모달이 RELEASE 를 삼켜도 keystate 로 끝냄 (step 3).
- 키맵: "Screen" K PRESS (전역, step 16 규칙). 에디터 키맵이 먼저라 같은 이벤트 제거: Mesh `wm.tool_set_by_id(builtin.knife)` (IC:3074;
  Maya Multi-Cut 은 Ctrl+Shift+X 로 이미 있음), Dopesheet `action.select_column` K (IC:1435; Ctrl/Shift/Alt+K 변형은 둠).
  "User Interface" K (keyingset_button_add, 버튼 위에서만 poll) / Outliner K 는 그대로 → `shadows` 로 기록.
- `keymap/mapping.py` `TimeDraggerToolActivate` 행 KIT.

### 4. S = 키 가능한 채널 전부, Key 메뉴 (delegated)
- `maya_kit.set_key` (`operators/time_keys.py`): 활성 Keying Set 이 있으면 그것 (`anim.keyframe_insert`, animation.md §4 Character
  Set → Keying Set), 없으면 Channel Box 대상 노드마다 CB 에 보이는 채널 중 키 가능한 것 전부 (`channel_box._visible_channels`,
  `is_keyable`: Translate/Rotate/Scale/Visibility + 커스텀 속성, Hide/Nonkeyable 제외 = Maya 의 keyable 속성). `breakdown=True` =
  Set Breakdown Key. 오브젝트 모드 "Object Mode" 와 "Pose" 의 S (IC `keyframe_insert_by_name` LocRotScale) 를 바꿈.
- Key 메뉴 (`ui/menu_map.py`): Set Key = set_key, Set Key on Animated / Insert Key / Hold Current Keys = `keyframe_insert_by_name`
  ('Available'), Set Breakdown Key = set_key(breakdown), Cut / Copy / Paste Keys = time_keys (현재 프레임 / 범위),
  **Delete Keys = `anim.keyframe_clear_v3d`** (Maya 기본 = 모든 키; 지금 `keyframe_delete_v3d` 는 현재 프레임만), Edit > Keys 도 같음.
  타임라인 RMB Delete 는 현재 프레임 / 범위만 (animation.md:98, TimeSliderMenu.mel:459).
- Channel Box 우클릭 = Key Selected 류: 채널 이름·값 칸 RMB 는 UI 버튼 문맥 메뉴 (C, 키맵으로 못 가로챔) → `UI_MT_button_context_menu`
  에 앞에 붙는 draw (CB 버튼일 때만: `context.button_operator` = `cb_select_channel` 또는 `button_pointer` = CB 프록시/행) 로
  Channels 메뉴 항목 (Key Selected, Breakdown Selected, Mute, Delete, Break Connections, Lock/Unlock, Hide, Keyable) 을 맨 위에.

### 5. MMB 시간 이동 = 불가 → 안내 (step 54 체계)
- Maya MMB 드래그 = 장면 갱신 없이 시간 이동 (포즈 복사 관용, animation.md:7). Blender 는 프레임이 바뀌면 늘 평가 → 불가.
  타임라인 MMB PRESS (TIMELINE 만, 맨 앞) = 1 과 같은 스크럽 + Help Line 안내 (`notices.show`) 「Blender always updates the scene
  when time changes: copy keys instead (RMB Copy / Paste on the Time Slider)」.

### 6. 검증
- 헤드리스 `tests/test_step56_time_keys.py`: set_key 채널 (가시성·커스텀 포함, Hide/Nonkeyable 제외, 포즈 본), breakdown, keying set,
  time_keys DELETE/CUT/COPY/PASTE/SNAP/convert/inbetween/tangents/set range (현재 프레임·범위), Delete Keys 매핑 = clear,
  키맵 (Dopesheet 맨 앞 LMB/Shift/RMB/MMB, Screen K, Mesh knife K·Dopesheet K 제거, S 교체), 메뉴 순서·레이블, 버튼 문맥 메뉴 draw.
- GUI `tests/gui/gui_step56_time_slider.py` (animation_01 순서, 0.8 / 1.25): 1 프레임 S → 타임라인 x(24) LMB → frame 24 → 이동 → S →
  키 [1, 24] → 24 에서 타임라인 RMB > Delete → 키 [1] → K 누른 채 뷰에서 LMB 드래그 → 프레임 바뀜, 선택 그대로 → Shift 드래그 범위 띠
  (스크린샷). `tools/gen_keymap_mapping.py`, dogfood 47/47.

## 실측

- `anim.keyframe_clear_v3d` / `keyframe_delete_v3d` 는 4.5 에서 `confirm` 속성이 있음 (메뉴 항목은 `confirm=False`). 둘 다, 그리고
  `anim.keyframe_insert` (keying set) 는 헤드리스에서 poll 실패 (3D 뷰 영역 필요) → set_key 는 poll 이 될 때만 keying set 경로.
- `Scene.sync_mode` = NONE / FRAME_DROP / AUDIO_SYNC; `ob.keyframe_insert("hide_viewport")` 는 됨 (Visibility 키).
- 팩토리 화면 타임라인 (본문이 숫자 줄 한 줄 높이) 에서도 Dopesheet 키맵 맨 앞 LMB/Shift/MMB/RMB 가 잡힘 (GUI). 타임라인이 창 아래라
  RMB 메뉴가 위로 열림 → GUI 테스트는 밑줄 키 (D = Delete) 로 고름.

## 한 것

- `operators/time_keys.py` (새): `maya_kit.set_key` (S, Key > Set Key; `breakdown` = Set Breakdown Key; 활성 Keying Set 우선),
  `maya_kit.time_keys` (CUT / COPY / PASTE / DELETE / SNAP / TO_KEY / TO_BREAKDOWN / ADD·REMOVE_INBETWEEN / TANGENT; 대상 =
  Channel Box 노드, 시간 = Shift 범위 또는 현재 프레임, 빈 커브 제거, 클립보드 = 노드별 상대 경로·프레임 오프셋), `maya_kit.time_set_range`
  (Start/End, Min/Max, Selected), `TANGENTS` 표.
- `operators/taphold.py`: `TimeDragBinding` (K + LMB 드래그 = 시간, 영역 폭 = 재생 범위, 최소 0.02 프레임/px, Esc = 되돌림).
- `ui/time_slider.py`: `maya_kit.time_scrub` (LMB 시간, Shift 범위, MMB 시간 + Help Line 안내, Esc 되돌림), `maya_kit.time_slider_menu`
  + `MAYAKIT_MT_time_slider` (Maya 순서·레이블, 하위 Paste/Keys/Tangents/Playback Speed/Playback Looping/Set Range to; 대응 없는 항목은
  `maya_kit.time_slider_unavailable` 회색 + 툴팁/Help Line), 빨간 범위 띠 (Dope Sheet WINDOW POST_PIXEL), WM `maya_kit_time_range(_on)`.
- `ui/channel_box.py`: 채널 이름·값 칸 RMB 메뉴 맨 위에 Key Selected … Make Selected Nonkeyable (`UI_MT_button_context_menu.prepend`,
  `is_cb_button`).
- `ui/menu_map.py`: Key > Set Key / Set Key on Animated / Set Breakdown Key / Insert Key / Cut·Copy·Paste·Snap Keys / Hold Current Keys,
  **Delete Keys (Key, Edit > Keys) = `keyframe_clear_v3d`** (모든 키), Edit > Keys > Cut/Copy/Paste, Playback > Set Range to ▸ (3),
  Playback Speed > Real-time. `ui/notices.py`: Playback Looping Once / Oscillate (Blender 는 늘 반복).
- 키맵 (`patch_time_slider`): Dopesheet 맨 앞 LMB / Shift+LMB / MMB = time_scrub, RMB = time_slider_menu (PASS_THROUGH_FIRST), Screen K =
  time_drag (Mesh knife K, Dopesheet K select_column 제거; UI·Outliner K 는 shadows 로 기록), Object Mode / Pose S = set_key.
  `keymap/mapping.py`: SetKey → KIT, TimeDraggerToolActivate → KIT; `docs/keymap_mapping.md` 재생성 (구현 97).

## 검증

- 헤드리스 `tests/test_step56_time_keys.py` 12/12, 전체 442/442 (step 55 430 + 12).
- GUI `tests/gui/gui_step56_time_slider.py` 9/9 (1.25 / 0.8): 1 프레임 S → 타임라인 x(24) LMB → frame 24 → 이동 → S → 키 [1, 24] →
  24 에서 RMB > Delete → [1] → K + LMB 드래그 → 24 → 35, 선택 그대로 → Shift 드래그 10..30 범위 → MMB = 시간 40 + 안내, 범위 지워짐.
  스크린샷 직접 확인: Time Slider 메뉴 (Maya 순서), 빨간 범위 띠 10–30.
- GUI 전체 365/365 (0.8) · 364/364 (1.25), dogfood 47/47 (콘솔 오류 0), `tools/gen_keymap_mapping.py` 재생성 (구현 95 → 97).

## 남은 것

- Shift 범위 안 키 드래그 이동·끝 화살표 스케일 (Maya), 범위 띠의 화살표 손잡이 — 안 함.
- Maya K 감도 [U] (영역 폭 = 재생 범위로 정함), K + MMB (Maya: 갱신 없는 시간) 없음.
- 메뉴 제목 줄 「Time Slider」 (Blender 팝업 메뉴는 제목이 붙음, Maya 는 없음). Display Key Ticks / Time Display / Audio / Grease Pencil /
  Stepped Preview / Auto snap keys 항목 생략.
- Channel Box RMB 메뉴는 GUI 로 열어 보지 않음 (헤드리스 draw + manual_checks). CB 값 칸 위 S (UI 키맵 `keyframe_insert_button`) [U] 그대로.
- Auto Key 의미 (키 있는 채널만, animation.md 갭 9), Shift+S 탄젠트 마킹 메뉴·Graph Editor 탄젠트 버튼 = step 67 (`TANGENTS` 재사용).
- Keying Set 경로는 3D 뷰가 있을 때만 (헤드리스 미검증).
