# Step 70 — Graph Editor 탄젠트 툴바 · Shift+S · G · Auto Key · Playblast

근거: `research/maya/workflows/animation.md` (§3 갭 표: 탄젠트 버튼 15, Playblast 12, Auto Key 10, Shift+S 9, Graph G 6; §2.14-21, §4 결정,
§5 키맵 위험, §6 후보 C·D), shots `animation_02_win1` (Graph Editor 툴바), `animation_08_win1` (Playblast 옵션), research/maya/marking_menus.json
`buildKeyframeTangentMM` (:284-571).

## 계획

### 탄젠트 대응 (delegated; `operators/time_keys.TANGENTS` 확장, animation.md:66)
| Maya | Blender | 비고 |
|---|---|---|
| Auto | BEZIER + AUTO_CLAMPED | Maya 2022 기본 탄젠트 |
| Spline | BEZIER + AUTO | |
| Clamped | BEZIER + AUTO_CLAMPED | Auto 와 구분 없음 [I] |
| Linear | LINEAR | |
| Flat | BEZIER + ALIGNED, 핸들 수평 | |
| Stepped | CONSTANT | |
| Stepped Next | CONSTANT + 안내 | 없음 (animation.md §4) |
| Plateau | BEZIER + AUTO_CLAMPED | 근사 |
| Fixed | BEZIER + ALIGNED (각도 유지) | |
| Break / Unify | 핸들 FREE / ALIGNED | 툴바 |

대상: Graph Editor 에서는 **선택한 키** (보이는 커브), 다른 곳 (3D View, 타임라인) 에서는 Channel Box 노드의 현재 프레임 / Time Slider 범위 키
(Maya timeSliderSetTangent, 기존 `time_keys.set_tangent`). 연산자 `maya_kit.set_tangent(kind)`.

### 설계 (모두 delegated)
1. **Graph Editor 툴바** (`ui/graph_editor.py`): `GRAPH_HT_header` 에 draw 함수 append (unregister 에서 remove): 「Tangents」 아이콘 줄
   Auto / Spline / Clamped / Linear / Flat / Stepped / Plateau | Break / Unify | Buffer Curve Snapshot / Clear (= ghost curves, 스왑 없음 안내).
   툴팁 = Maya 이름 + Blender 대응.
2. **Shift+S = 탄젠트 마킹 메뉴**: `marking/menus.py` `buildKeyframeTangentMM` (W Keys ▸ 8, E Tangents ▸ 8; 위치는 research JSON, test_step8 이 대조).
   Graph Editor 분기와 그 밖 분기는 같은 배치 → 메뉴 하나, 동작이 문맥으로 갈림 (Keys = Graph Editor 선택 키 / 그 밖 time_keys). 키: tap_hold binding
   `key_tangent` (탭 = 아무것도 안 함 = Maya, 홀드 + LMB = 메뉴). 자리: Object Mode · Pose (IC `anim.keyframe_insert` Shift+S 제거, IC:2462, 2535),
   Graph Editor, Dopesheet (Shift+S 없음). Mesh / UV 의 Shift+S 는 그대로 (UV Sew, step 66).
3. **Graph Editor 키**: G = `anim.scene_range_frame` (재생 범위 = preview 있으면 그것, Maya FramePlaybackRange; Graph Editor 키맵이 Screen 의
   `screen.repeat_last` 보다 먼저라 Graph Editor 에서만 바뀜), D = Auto 탄젠트 (`maya_kit.set_tangent(AUTO)`, Graph Editor 에 D 없음).
   F / A 행은 이미 IC (`graph.view_selected` / `view_all`) → 상태 IC.
4. **Auto Key = 키 있는 채널만**: prefs_preset 그룹 `autokey` = `edit.use_keyframe_insert_available` True (백업·복원, 옵션 "Maya Auto Key", 기본 켬,
   switch FOOTPRINT 에 추가). Channel Box 값 입력의 auto key 도 같은 규칙 (그 채널에 F-curve 가 있을 때만).
5. **Playblast** (`operators/playblast.py`, `maya_kit.playblast`): 3D View 에서 `render.opengl(animation=True)` (범위 = 재생 범위, step 48 측정) →
   임시 폴더 (`bpy.app.tempdir/playblast/`) 에 동영상 (FFMPEG MPEG-4) 또는 PNG → View 켜져 있으면 `render.play_rendered_anim` (Blender 플레이어).
   렌더 설정 (경로·형식·해상도 %·프레임 범위) 은 바꿨다가 끝나면 복원. `option_box` 속성 → 메뉴 □ = `invoke_props_dialog` (Time range Time Slider /
   Start-End, Start, End, Format Movie / Image, Quality 70, Scale 0.5 = Maya 기본 [O animation_08_win1], View).
6. 버퍼 커브 스왑 · Maya Animation 워크스페이스 · 그래프 1/2/3 · Insert Key 툴은 범위 밖 (PLAN 「남긴 것」).

검증: 헤드리스 `tests/test_step70_graph.py` (대응표, Graph Editor 선택 키 / 현재 프레임 키 탄젠트, Break/Unify, 마킹 메뉴 정의·연산자,
키맵 Shift+S/G/D·행, Only Insert Available 백업·복원, CB auto key 규칙, playblast 설정 저장·복원·경로), GUI `tests/gui/gui_step70_graph.py`
(키 둘 → Graph Editor 창 → 키 선택 → 툴바 Linear → LINEAR → G → 재생 범위 → Playblast □ 대화상자 → Playblast → 파일 + 플레이어 프로세스), dogfood.

## 한 것

- 탄젠트 표 (`operators/time_keys.TANGENTS` + `apply_tangent`, `TANGENT_LABELS`): Fixed / Stepped Next / Break / Unify 추가 (계획 표대로).
- `operators/graph_keys.py`: `maya_kit.set_tangent(kind)` (Graph Editor = 선택 키, 그 밖 = Channel Box 노드의 현재 시간 / Time Slider 범위 키;
  Stepped Next 안내, 툴팁 = Maya 이름 + Blender 대응), `maya_kit.key_edit(action)` (Delete / Cut / Copy / Paste / Convert to Key·Breakdown /
  Add·Remove Inbetween — Graph Editor 선택 키 또는 `time_keys`), Shift+S tap_hold `key_tangent`.
- `ui/graph_editor.py`: `GRAPH_HT_header` 에 아이콘 줄 (Auto / Spline / Clamped / Linear / Flat / Stepped / Plateau | Break / Unify | 고스트 커브 =
  Buffer Curve Snapshot / Clear).
- 마킹 메뉴 `buildKeyframeTangentMM` (`marking/menus.py`: W Keys ▸ 8, E Tangents ▸ 8, research JSON 위치 — test_step8 대조, 메뉴 23 개).
- 키맵 (`patch_graph_keys`): Graph Editor G = `anim.scene_range_frame` (Screen repeat_last 를 가림, shadows), D = Auto; Shift+S = tap_hold
  (Object Mode / Pose 의 IC `anim.keyframe_insert` 대체, Graph Editor · Dopesheet 추가). 행: G / D / Shift+S KIT, Graph F / A IC (구현 113, IC 10).
- Auto Key: prefs_preset 그룹 `autokey` (`edit.use_keyframe_insert_available` 켬, 환경설정 「Maya Auto Key」 기본 켬, 끄거나 kit 끄면 복원,
  switch FOOTPRINT), Channel Box 값 입력 auto key 도 같은 규칙 (`channel_box.auto_keys`).
- `operators/playblast.py`: `maya_kit.playblast` (렌더 설정 저장 → 임시 폴더 MPEG-4 / JPEG, Scale 0.5, Quality 70 → `render.opengl(animation)` →
  View 면 `render.play_rendered_anim` → 설정 복원), `option_box` = Playblast Options 대화상자. Windows / Playback 메뉴, 셸프 Playblast 가 이것.
- 발견: 헤드리스에서 연산자 호출 사이에 들고 있던 `KeyframePoint` 참조가 가끔 낡음 (전체 실행에서 간헐 실패) → 테스트는 매번 다시 읽음.

## 검증

- 헤드리스 `tests/test_step70_graph.py` 8/8 (5 번 연속 통과), step 6 (Auto Key 규칙) / step 8 (메뉴 수) / keymap (G shadow) 기대 갱신. 전체 헤드리스 574/574.
- GUI `tests/gui/gui_step70_graph.py` 7/7 (ui 1.0): 키 둘 → Graph Editor 창 → 전체 키 선택 → 툴바 Linear → LINEAR → Shift+S 홀드 + LMB 동쪽 (Tangents 하위
  메뉴 열림, 스크린샷) → 계속 동쪽 = Flat → ALIGNED + 수평 → G → 보기 −7..129 (재생 범위 1–120) → Playblast □ (대화상자 스크린샷) → Playblast 프레임 1–12
  `Scene_0001-0012.mp4` + 렌더 경로 그대로 → 플레이어 프로세스 확인 후 종료. 스크린샷 3 장 확인. GUI 전체 ui 0.8: 484/484. dogfood 47/47, 콘솔 오류 0.
- `docs/manual_checks.md` 「Step 70」 5 항목.

## 남은 것

- 툴바 버튼을 실제 마우스로 누르는 GUI 검증은 안 함 (헤더 버튼 위치를 Python 으로 알 수 없음; 같은 연산자를 헤더 문맥에서 실행해 확인) → manual_checks.
- Graph Editor 1 / 2 / 3 (보기 모드), Insert Key 툴, L / H / J, 버퍼 커브 스왑, Maya Animation 워크스페이스, 타임라인 RMB Tangents 의 Fixed / Stepped Next:
  PLAN 「남긴 것」.
- Plateau 와 Clamped 는 Blender 에서 Auto 와 같은 핸들 (근사, [I]).
