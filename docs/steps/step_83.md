# Step 83 — 키 삽입·이동 묶음 (Alt+I, Ctrl+Shift+W/E/R, Shift+( ), Ctrl+Alt+, .)

재점검 5차 backlog 3 (docs/PLAN.md 「재점검 5차」 blindspots 2–3, docs/keymap_mapping.md 미검토 행 :219-220, :467-470, :476-477).

## 근거

- Maya 핫키 (research/maya/hotkeys_and_menus.md:158-166; hotkeySetup.mel:356-357, 729-732, 739-740):
  Ctrl+Shift+W / E / R = InsertKeyTranslate / Rotate / Scale, Alt+i = InsertKey, Shift+( / ) = NudgeSelectedKeysBackward /
  Forward, Ctrl+Alt+, / . = SelectPreviousKey / SelectNextKey. 모두 global.
- runtime 명령 (research/maya/runtime_commands.json, defaultRunTimeCommands.mel):
  - InsertKeyTranslate / Rotate / Scale = `setKeyframe -insert -at translate|rotate|scale` (:11980-11994) — **곡선 모양을 바꾸지 않고**
    (insert) 그 채널의 기존 곡선에 현재 시간 키. -insert 는 새 곡선을 만들지 않는다 [K].
  - InsertKey = `insertKey` (:11972; proc :200-222 동작): 곡선 = Graph Editor 에서 키가 선택된 곡선 → 없으면 Graph Editor 에 보이는 곡선
    → 없으면 선택 오브젝트의 곡선; 그 곡선들에 `setKeyframe -insert`.
  - Nudge = `keyframe -e -iub true -animation keys -r -o over -tc ±1` (:1019, :1026): 선택 (활성) 키를 1 프레임, 겹치면 덮어씀 (`-o over`).
  - SelectNext / PreviousKey = `selectNextOrPrevKey` (proc :225-241 동작): 마지막 선택 키의 시간에서 다음 / 이전 키 시간을 찾고, 키 선택을
    지우고 그 시간의 키를 선택하고, 현재 시간을 그리로.
- Blender: `FCurve.keyframe_points.insert(frame, value)` 는 이웃 auto 핸들을 다시 계산해서 곡선 모양이 바뀐다 (auto-clamped 기본).
  같은 모양을 지키려면 베지어 구간을 그 시간에서 나눠야 한다 (de Casteljau).

## 계획

1. `operators/key_insert.py` (bpy 순수 함수 + 연산자 3개), 노드 = Channel Box 노드 (`time_keys.nodes`, 오브젝트 / 포즈 본).
2. **모양 유지 삽입** `insert_keep_shape(fc, frame)`:
   - 그 프레임에 키가 있으면 아무것도 안 함. 값 = `fc.evaluate(frame)`.
   - 앞 키가 BEZIER 이고 뒤 키가 있으면: 구간 (P0 = 앞 co, P1 = 앞 오른 핸들, P2 = 뒤 왼 핸들, P3 = 뒤 co) 에서 x(t) = frame 인 t 를
     이분법으로 찾아 de Casteljau 분할 → 새 키 (co, 핸들) + 앞 키 오른 핸들 / 뒤 키 왼 핸들 줄임. auto / auto-clamped 인 쪽은 ALIGNED,
     vector 는 FREE 로 (위치 그대로 고정, 다시 계산 안 되게). 새 키 핸들 ALIGNED (분할점은 한 직선 위).
   - LINEAR / CONSTANT 구간 = 값만 (보간 = 앞 키 것). 곡선 밖 (처음 앞 / 끝 뒤) = 외삽 값으로 평평한 핸들, 끝 키 auto 핸들은 ALIGNED 고정.
   - `insert` 는 배열을 다시 잡아 기존 KeyframePoint 참조가 무효 → 필요한 값은 먼저 읽고, 삽입 뒤 x 로 다시 찾는다.
3. **연산자**
   - `maya_kit.insert_key(channels='ALL'|'TRANSLATE'|'ROTATE'|'SCALE')`:
     ALL = Graph Editor 안이면 키 선택된 곡선 → 보이는 곡선, 그 밖이면 노드 곡선. T/R/S = 노드의 그 채널 곡선 (location / rotation_* /
     scale, 본은 `pose.bones["n"].` 접두). 새 곡선은 만들지 않음 (곡선 없으면 경고).
   - `maya_kit.nudge_keys(delta=±1)`: Graph Editor / Dope Sheet (Timeline 모드 제외) 안이면 선택 키 (`editable_fcurves` 의 선택
     control point); 그 밖 (3D View, Time Slider) 이면 노드의 Time Slider 범위 키 (Shift 범위, 없으면 현재 프레임 키) — 범위 / 현재 프레임도
     같이 옮겨 다시 누르면 계속 옮겨짐 (delegated; Maya 의 활성 키가 없을 때의 동작은 [U]). 겹치는 자리의 키는 지움 (`-o over`).
   - `maya_kit.select_key(direction='NEXT'|'PREVIOUS')`: 곡선 = Graph Editor 안이면 보이는 곡선, 그 밖이면 노드 곡선. 기준 시간 = Graph Editor / Dope Sheet
     안이면 선택 키 (다음 = 가장 늦은, 이전 = 가장 이른), 그 밖이면 현재 프레임 (delegated, 구현 중 변경: 3D View 에서는 키 선택이 안
     보이고 Blender 는 넣은 키를 모두 선택해 둔다; Maya 는 고른 키로 시간을 옮기므로 반복 결과가 같다). 다음 / 이전 키 시간을 찾아
     그 곡선들의 키 선택을 지우고 그 시간 키만 선택, 현재 프레임 이동.
   - 모두 REGISTER | UNDO.
4. **키맵** (`keymap/maya_patches.py` 39): "Screen" 에 Alt+I, Ctrl+Shift+W/E/R, Shift+9 / Shift+0, Ctrl+Alt+, / . — 3D View / Graph
   Editor / Dope Sheet / 타임라인 어디서든 (Maya global). 같은 이벤트의 에디터 / 모드 키맵 (Weight Paint Alt+I 등) 은 그쪽이 먼저 —
   shadows 로 명시. `mapping.py` 행 상태 KIT + gen_keymap_mapping.
5. 다음 단계 고려: 84 (Shift 범위 드래그 이동) 는 같은 `time_range` 와 이동 함수 (`time_keys._move`, 겹침 덮어쓰기) 를 쓰게 둔다.
   85, 86 과 이벤트 겹치지 않음.

## 검증 계획

- 헤드리스 `tests/test_step83_key_insert.py`: 베지어 (auto-clamped, 오버슈트 있는 곡선) 중간 삽입 전후 `evaluate` 가 0.25 프레임 간격
  전 구간에서 같음 (1e-4), 선형 / 상수 구간, 곡선 밖 삽입, 이미 키가 있으면 그대로; T/R/S 채널 고르기, 곡선 없음 = 새 곡선 안 만듦,
  본 접두; nudge (선택 키 ±1, 겹침 덮어쓰기, 현재 프레임 따라감), select next / previous (선택·현재 프레임), 키맵 항목·섀도잉.
- GUI `tests/gui/gui_step83_key_insert.py`: 3D View 에서 Ctrl+Shift+W → 키 추가 + 곡선 값 그대로, Alt+I, Shift+) / ( , Ctrl+Alt+. / ,
  Graph Editor 안에서 선택 키 nudge.
- 전체 헤드리스·GUI, dogfood, manual_checks.

## 한 것

- `src/maya_kit/operators/key_insert.py` (새 파일): `maya_kit.insert_key(channels)`, `maya_kit.nudge_keys(delta)`, `maya_kit.select_key(direction)`.
  - 모양 유지 삽입 `insert_keep_shape`: **측정** — Blender 4.5 `keyframe_points.insert` 는 auto / auto-clamped 키 사이 구간을 스스로
    나눠 모양을 지킨다 (오차 1e-6, 핸들 auto 유지) 하지만 FREE 오버슈트 핸들에서는 0.36 어긋난다. 그래서 양쪽이 auto 인 구간은 Blender
    insert (auto 유지 = Maya Auto 탄젠트처럼 나중 편집에 따라감), 그 밖 (free / aligned / vector) 은 de Casteljau 분할 + 닿는 핸들 고정,
    선형·상수·곡선 밖은 값 + 평평한 핸들.
  - nudge: 키 에디터 안 = 선택 키, 그 밖 = Channel Box 노드의 Time Slider 범위 / 현재 시간 키 + 범위·시간 같이 이동; 도착 자리 키 덮어씀.
  - select key: 기준 = 키 에디터 안 선택 키, 그 밖 = 현재 프레임 (계획에서 바꿈, 위 3).
- `keymap/maya_patches.py` 39 `patch_key_insert`: "Screen" Alt+I, Ctrl+Shift+W/E/R, Shift+9 / Shift+0 (반복), Ctrl+Alt+, / . (shadows =
  같은 이벤트를 가진 페인트·GP·Mask·UI·Animation Channels·Text 키맵). `mapping.py` 8 행 KIT → `docs/keymap_mapping.md` 구현 125 → 133.

## 검증

- 헤드리스 `tests/test_step83_key_insert.py` 10/10: auto 구간 4 곳 삽입 전후 `evaluate` 같음 (0.25 프레임 간격, 1e-4) + auto 유지,
  Blender insert 가 FREE 오버슈트에서 어긋남 (대조) / kit 분할은 같음, vector, 선형·상수·곡선 밖·이미 키, T/R/S 채널만 + 새 곡선 안 만듦,
  본 접두, 덮어쓰기 이동, nudge 반복 (시간 따라감), 키 없으면 CANCELLED, select next / previous, 키맵 8 항목.
- GUI `tests/gui/gui_step83_key_insert.py` 8/8 (3D View 실제 키 이벤트 + Graph Editor 의 선택 키 nudge).
- 전체: 헤드리스 656/656, GUI 585/587 — 실패 2 = gui_step26 RMB 취소 (step 67 부터 기록된, 전체 실행 때만 나는 간헐 실패; 단독 8/8),
  dogfood 47/47 (콘솔 0). `docs/manual_checks.md` 「Step 83」 4 항목.

## 남은 것

- Maya 에서 활성 키가 없을 때 Nudge 가 하는 일 [U] — kit 는 현재 시간 키를 옮기고 시간도 같이 (delegated). Maya 실행 확인 안 함.
- Graph Editor 의 Insert Key **툴** (i 홀드 = InsertKeyToolActivate, keymap_mapping.md:201) 은 이번 범위 밖 (미검토 그대로).
- 키 에디터 밖의 select key 는 키 선택을 기준으로 쓰지 않음 (위 판단). 다른 곡선만 키가 있는 시간도 "키" 로 침 (Maya findKeyframe 와 같음 [I]).
- 84 (Shift 범위 드래그 이동·늘이기) 에서 `move_keys` (덮어쓰기) 와 `time_keys.time_range` 를 다시 쓸 수 있다.

