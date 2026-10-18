# Step 90 — 전역 키 묶음 4 (Ctrl+X, Alt+X, Alt+\, Alt+1/2/4, 스무드 프록시 키) + IC 행 정리

재점검 6차 backlog 1 (docs/PLAN.md 「재점검 6차」 blindspot 1–3, 5, 6; docs/keymap_mapping.md 미검토 :35, :450, :483, :472-474,
:436-438 와 IC 로 바꿀 :26, :28, :36-37, :282-283).

## 근거 (Maya 2022 스크립트의 동작, 줄 = 설치본; 코드는 옮기지 않음)

- research/maya/hotkeys_and_menus.md:99, :113, :121, :132, :168; research/maya/interaction.md:51, :174.
- **Ctrl+X CutSelected** = `cutCopyPaste "cut"` (startup/defaultRunTimeCommands.mel:1135-1139): 선택을 클립보드 파일
  (`maya_sceneClipBoard.mb`, 히스토리·셰이더 포함) 로 내보낸 뒤 `delete`. Paste 는 그 파일을 import (`renamingPrefix "pasted_"`,
  others/bulletCutCopyPaste.mel:23-41 이 같은 구조).
- **Alt+X WalkContext_Command**: Walk 툴 (hotkeySetup.mel:701, nameCommand; 컨텍스트는 컴파일됨, hotkeys_and_menus.md:281).
- **Alt+\ PlaybackRangeAnimStartEnd** (defaultRunTimeCommands.mel:20629-20634): `playbackOptions -min = -ast, -max = -aet` — 재생
  범위를 애니메이션 범위로.
- **Alt+1 / 2 / 4** = `toggleNurbsCurvesOption` / `togglePolygonsOption` / `toggleImagePlaneOption` (others/createModelPanelMenu.mel):
  포커스 모델 패널의 `modelEditor -nurbsCurves / -polymeshes / -imagePlane` 를 뒤집음 (그 패널만).
- **Ctrl+` / Shift+~ / Ctrl+Shift+~** = `smoothingDisplayToggle 1` / `smoothingDisplayToggle 0` / `performSmoothProxy 0`
  (others/smoothingDisplayToggle.mel): 프록시 (원래 메시 = 케이지) 와 스무드 메시의 보이기를 서로 바꿈 (둘 다 보이면 → 케이지만), 0 = 둘
  다 보이기. Ctrl+Shift+~ = Mesh > Smooth Proxy > Subdiv Proxy.
- Maya 키컨피그 현재 (측정, 이번 단계 헤드리스 probe): Ctrl+X = Text / Console / Font / Grease Pencil Edit Mode 에만 (3D View·Object
  Mode 없음), Alt+X = "3D View" `view3d.toggle_xray` (IC), Alt+\ / Alt+1/2/4 / Ctrl+` / Shift+` / Ctrl+Shift+` = 없음.
  Ctrl+Q = Window `wm.quit_blender`, Ctrl+N = Window `wm.read_homefile`, Ctrl+C / Ctrl+V = 3D View `view3d.copybuffer` /
  `pastebuffer`, Outliner Return = `outliner.item_rename`, F = `outliner.show_active` — 이미 Maya 동작.

## 계획

1. `operators/global_keys4.py` (새):
   - `maya_kit.cut`: Object Mode, 선택 있음. `view3d.copybuffer` (Blender 클립보드 = 선택 오브젝트를 임시 .blend 로) 뒤 선택 삭제
     (`object.delete(use_global=False)`, 확인 없음). 언두 한 단계. Ctrl+V = IC `view3d.pastebuffer` 그대로 (Maya `pasted_` 접두사는
     안 함 — Blender 는 이름이 비면 원래 이름으로 붙음, delegated).
   - `maya_kit.playback_range_anim`: 재생 범위 = 애니메이션 범위. kit 규칙 (step 20) 에서 재생 범위 = 프리뷰 범위, 애니메이션 범위 =
     frame_start/end 이므로 `use_preview_range = False` (프리뷰 값은 남겨 Range Slider 더블클릭 `range_bar.toggle_whole` 이 되돌릴 수
     있게, delegated). 타임라인 다시 그림.
   - `maya_kit.toggle_show(kind)`: 커서 아래 3D View. CURVES = `show_object_viewport_curve` (Maya NURBS 커브; 서피스는 따로),
     POLYGONS = `show_object_viewport_mesh`, IMAGE_PLANES = Blender 에 이미지 엠프티만 거르는 뷰 필터가 없음 (`empty` 는 그룹·로케이터도
     숨김) → 장면의 이미지 엠프티 (`empty_display_type == 'IMAGE'`, kit Free Image Plane, create.py:82) 의 `show_empty_image_perspective`
     / `_orthographic` 를 함께 뒤집음 (모든 뷰에 적용, delegated). 하나라도 보이면 숨김, 아니면 보임.
   - `maya_kit.smooth_proxy(action)`: kit 의 Subdiv Proxy = 사용자 Subsurf (menu_map.py:268, preview 가 아닌 마지막 SUBSURF).
     CREATE = 선택 메시에 Subsurf 추가 (메뉴와 같은 결과, 이미 있으면 그대로), TOGGLE = 그 Subsurf `show_viewport` 뒤집기 (둘 다 보기
     상태면 → 케이지만), BOTH = Subsurf 켬 + 케이지 와이어 (`show_wire`, smooth preview 2 와 같은 방식·같은 플래그 규칙). 프록시가 없으면
     Help Line 안내 (Maya 경고와 같은 뜻).
2. 키맵 (`maya_patches.py` 43 `patch_global_keys_4`):
   - "Object Mode" Ctrl+X = cut; "Outliner" Ctrl+X = cut (Outliner 선택 = 오브젝트 선택 동기화). shadows = Text, Console, Font,
     Grease Pencil Edit Mode (다른 에디터·모드).
   - "3D View" Alt+X: `view3d.toggle_xray` 제거, `view3d.walk` 추가.
   - "Screen" Alt+\ = playback_range_anim (전역, step 16 규칙).
   - "3D View" Alt+1 / Alt+2 / Alt+4 = toggle_show (VIEW3_SHADOWS — Sculpt 등 모드 키맵이 먼저).
   - "Object Mode" + "Mesh" Ctrl+` / Shift+` = TOGGLE / BOTH, "Object Mode" Ctrl+Shift+` = CREATE.
     ` (수식 없음) 는 step 87 tweak_hold 그대로 — 수식이 달라 겹치지 않음.
3. `mapping.py`: 9 행 KIT (CutSelected, WalkContext_Command, PlaybackRangeAnimStartEnd, Toggle*OptionCmd 3, SmoothingDisplayToggle /
   ShowBoth, SmoothProxy) + 6 행 IC (Quit, NewScene, CopySelected, PasteSelected, outlinerPanel:OutlinerRenameSelectedItem /
   OutlinerRevealSelected) → `tools/gen_keymap_mapping.py` 로 대응표 다시 만듦. `menu_map.py` Edit/Cut = maya_kit.cut.
4. 다음 단계 고려: 91 (뷰 표시 수정) 은 3D View 오버레이 — 여기서 건드리지 않음. 92 (Graph Editor t, Alt+/) 는 Graph Editor 키맵이라 이번
   전역 키와 안 겹침. 93 (선택 마스크) 무관.

## 검증 계획

- 헤드리스 `tests/test_step90_global_keys.py`: 키맵 항목 (이벤트별 하나, Alt+X toggle_xray 없음), cut → 오브젝트 없음 → pastebuffer 로
  같은 이름 돌아옴, Alt+\ 뒤 재생 범위 = frame_start/end (`range_bar.playback`), toggle_show 세 종류, smooth_proxy CREATE / TOGGLE / BOTH,
  Edit/Cut 메뉴 매핑.
- GUI `tests/gui/gui_step90_global_keys.py`: Ctrl+X (큐브 사라짐) → Ctrl+V (돌아옴), Alt+X (walk 모달 시작) → ESC, Alt+2 (메시 숨김) 스크린샷.
- 전체 헤드리스·GUI, dogfood, gen_keymap_mapping.

## 한 것

- `operators/global_keys4.py` (새):
  - `maya_kit.cut`: 선택 + 그 아래 계층 (`cut_targets`) 을 `view3d.copybuffer` 로 복사한 뒤 오브젝트 삭제, 사용자 없는 data 도 지움
    (Maya 는 shape 도 지움 — 안 지우면 붙여넣은 메시가 `pCubeShape1.001`, GUI 스크린샷에서 발견).
  - `maya_kit.paste` (계획에 없던 것, delegated): Blender `view3d.pastebuffer` 는 잘라낸 뒤 활성 오브젝트를 비워 두어 Channel Box 가 빈다 →
    붙여넣은 첫 최상위 노드를 lead 로 (Maya pasteScene 이 첫 노드만 선택, bulletCutCopyPaste.mel:40-41). Ctrl+V (Object Mode) 와 Edit > Paste.
  - `maya_kit.playback_range_anim` (프리뷰 범위 끔, 값은 남김), `maya_kit.toggle_show` (커브 / 메시 = 그 뷰의 필터, 이미지 플레인 = 이미지
    엠프티의 perspective / orthographic 표시, 모든 뷰), `maya_kit.smooth_proxy` (CREATE = Subsurf 추가, kit 미리보기 앞에; TOGGLE; BOTH =
    Subsurf + 케이지 와이어, 둘 다 → 케이지).
- `keymap/maya_patches.py` 43 `patch_global_keys_4`: Object Mode / Outliner Ctrl+X, Object Mode Ctrl+V, 3D View Alt+X (IC toggle_xray 제거) =
  `view3d.walk`, Screen Alt+\, 3D View Alt+1/2/4, Object Mode + Mesh Ctrl+` / Shift+`, Object Mode Ctrl+Shift+`.
- `keymap/mapping.py` 10 행 KIT (CutSelected, PasteSelected, WalkContext_Command, PlaybackRangeAnimStartEnd, Toggle*OptionCmd 3,
  SmoothingDisplayToggle / ShowBoth, SmoothProxy) + 5 행 IC (Quit, NewScene, CopySelected, Outliner Return / f) → 대응표 구현 142 → 152,
  IC 10 → 15, 미검토 237 → 222. `ui/menu_map.py` Edit/Cut = `maya_kit.cut`, Edit/Paste = `maya_kit.paste`.
- `docs/manual_checks.md` step 90 절 5 항목 (353 중 자동 13).

## 검증

- 헤드리스 `tests/test_step90_global_keys.py` 8/8: 키맵 항목 (이벤트별 하나, Alt+X toggle_xray 없음, ` = tweak_hold 그대로), 그룹 cut → 계층째
  사라짐 → paste = 같은 이름·부모, 그룹이 lead, shape 이름 그대로, poll, Alt+\ 뒤 `range_bar.playback` = (1, 120) 이고 더블클릭 토글이 (20, 40)
  으로 되돌림, toggle_show 세 종류 (로케이터 엠프티는 그대로), smooth_proxy CREATE (미리보기 둘이 스택 끝) / 한 번만 / TOGGLE / BOTH / 둘 다
  → 케이지, 프록시 없으면 CANCELLED, Edit/Cut · Edit/Paste 매핑.
- GUI `tests/gui/gui_step90_global_keys.py` 10/10: Ctrl+X → 큐브 없음, Ctrl+V → pCube1 + lead + shape `.001` 없음, Alt+X → `VIEW3D_OT_walk`
  모달, X-ray 안 켜짐, ESC → 모달 끝, Alt+2 숨김 / 다시 보임, Alt+\ → 프리뷰 범위 꺼짐. 스크린샷 직접 확인 (`gui_step90_paste.png`: Channel Box
  에 pCube1, SHAPES pCubeShape1 — 고치기 전 첫 실행은 Channel Box 가 비고 shape 가 `.001` 이었음; `gui_step90_alt2.png`: 메시 숨김).
- 전체 헤드리스 `python tests/run.py`: **685/685** (82 파일). 전체 GUI `python tests/gui/run.py`: **677/677** (71 파일).
- `python tools/dogfood.py`: **47/47**, 콘솔 0. `python tools/gen_keymap_mapping.py`: 468 행, 구현 152 · IC 15 · 해당 없음 11 · 미검토 222 ·
  macOS 68.

## 남은 것

- Maya Paste 의 `pasted_` 접두사 / 그룹 참조 (others/bulletCutCopyPaste.mel:33-37) 는 안 함 — Blender 는 이름이 비면 원래 이름, 아니면
  `.001` (delegated).
- 오브젝트 모드 Delete / Backspace 는 IC `object.delete` 그대로 — Maya 는 그룹을 지우면 자식도 지우지만 Blender 는 자식을 남긴다 (이번에 cut
  만 계층째로; 다음 키 묶음이나 재점검 후보).
- Alt+4 이미지 플레인은 모든 뷰 (Blender 에 뷰별 이미지 엠프티 필터 없음); Panels Show 메뉴의 Image Planes 항목은 여전히 회색.
- Walk 는 Blender 모달 (Maya 는 툴을 바꿀 때까지 남는 툴) — manual check.
- 스무드 프록시는 Subsurf 하나로 근사 (Maya 는 별도 프록시 메시 + 반투명 셰이더, Remove Subdiv Proxy Mirror 는 없음).
- 다음: step 91 = 뷰 표시 수정 (부모 관계 점선, RMB 목록 위 HUD, AE 전환 때 탭 순서).
