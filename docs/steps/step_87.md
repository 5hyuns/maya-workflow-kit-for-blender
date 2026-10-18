# Step 87 — 뷰 키 묶음 3 (Alt+A, Alt+P, Alt+화살표, `, \) + 대응표 `Shift+|` 행

재점검 5차 backlog 7 (docs/PLAN.md 「재점검 5차」 우선순위 7; docs/keymap_mapping.md 미검토 :133, :213, :233-236, :443, :448-449, :480).

## 근거 (Maya 2022 스크립트의 동작, 줄 = 설치본; 코드는 옮기지 않음)

- hotkeys_and_menus.md:53, :94, :98, :116; hotkeySetup.mel:241, 347, 370-373, 682, 697-698.
- **Alt+A CycleDisplayMode** = `switchDisplayMode` (others/createModelPanelMenu.mel): 포커스 모델 패널에서 optionVar
  `cycleDisplayLikeMobuVar` (전역, 처음 0) 로 3 상태를 돈다 — 0 → 조인트 X-ray 켬 + 조인트·커브·메시 보임 (→1), 1 → 조인트 X-ray 끔, 다
  보임 (→2), 2 → 조인트·NURBS 커브 숨김, 메시만 (→0).
- **Alt+P CameraModeToggle**: 포커스 패널 카메라가 perspective 면 `viewPlace -o` (ortho 로), 아니면 `-p` — 뷰는 그 자리.
- **Alt+←→↑↓ MoveLeft/…** = `editorDependentMove` → UV 에디터면 UV 넛지, 아니면 `PixelMove*` = `pixelMove ±1 0 / 0 ±1`: 선택을 뷰 평면에서
  1 픽셀.
- **` (홀드) STRSTweakModeOn/Off** = `strsTweakMode` (others/strsTweakMode.mel): 지금 툴이 Select / Move / Rotate / Scale 이면 누를 때
  tweak mode 켬 (Select 툴이면 Move 로 바꾸고 이전 툴 기억), 놓을 때 끄고 이전 툴로. tweak mode = 선택 안 된 것도 클릭-드래그로 바로 옮김
  (interaction.md:114).
- **\ (홀드) TogglePanZoom** = `activatePanZoom` / `deactivatePanZoom`: 누르는 동안 2D Pan/Zoom 컨텍스트 (카메라 필름백을 옮기고 확대,
  렌더 카메라는 그대로). [K] 드래그: LMB = 팬, MMB = 줌.
- Maya 키컨피그 현재 (측정): 이 이벤트들의 3D View 항목 없음; 같은 이벤트는 Sculpt Alt+A 파이, Font Alt+화살표, Text Alt+P / Alt+←→,
  File Browser / Sequencer / Clip / Node Alt+A·화살표 (다 다른 에디터·모드 키맵이라 그쪽이 먼저), Object Non-modal ` = `object.transfer_mode`.
- 대응표 `Shift+|` 행: 생성기가 셀의 `|` 를 `\|` 로 이스케이프 — GFM 에선 맞지만 백슬래시가 앞에 붙어 다른 렌더러·단순 분할 검사에서 열이
  하나 늘어남 (step 80 지적).

## 계획

1. `operators/view_keys3.py` (새):
   - `maya_kit.cycle_display`: 패널 = 커서 아래 3D View. 상태 0/1/2 (모듈 변수, Maya optionVar 처럼 전역·세션). 조인트 X-ray = 장면 아마추어의
     `show_in_front` (Blender 에 뷰별 조인트 X-ray 없음 — delegated; 켜기 전 값 기억 → 끌 때 복원), 조인트·커브 보이기 = 그 뷰의
     `show_object_viewport_armature` / `_curve`. 인뷰 메시지로 상태 이름 (step 72 `view_message`).
   - `maya_kit.camera_mode_toggle`: 사용자 뷰 = `view3d.view_persportho`; 카메라를 통해 보는 중이면 그 카메라 `type` PERSP ↔ ORTHO
     (ortho_scale = 카메라에서 뷰 중심까지 거리의 화면 폭 = 2·d·tan(fov/2), 그 자리 화면 크기 유지).
   - `maya_kit.pixel_move(dx, dy)`: 3D View 에서 매니퓰레이터 중심 (`manipulator.pivot_frame`) 을 화면에서 1 픽셀 옮긴 만큼 세계 이동
     (`region_2d_to_location_3d` 차) → `transform.translate(value)` (오브젝트·편집 모드, 언두 한 단계, 반복 키). UV 에디터 넛지는 안 함.
   - `maya_kit.tweak_hold` (` PRESS → 모달): 지금 툴이 select 계열 / move / rotate / scale 이면 Blender Tweak 툴 (`builtin.select`, 클릭-
     드래그 = 그 자리 이동) 로 바꾸고 놓을 때 원래 툴. 놓기 이벤트를 다른 모달이 먹으면 keystate + transform 끝 대기 (hold.py 방식).
   - `maya_kit.pan_zoom_hold` (\ PRESS → 모달): 카메라 뷰에서 LMB 드래그 = `view_camera_offset` 팬, MMB 드래그 = `view_camera_zoom`
     줌 (렌더 안 바뀜 = Maya 2D Pan/Zoom). 사용자 뷰에서는 안내 (Blender 에서는 카메라 뷰에만 2D 팬/줌).
2. 키맵 (`maya_patches.py` 42): "3D View" Alt+A, Alt+P, Alt+화살표 (repeat), `, \ — 셋 다 3D View (Maya modelPanel 동작). Object Non-modal `
   의 transfer_mode 제거. shadows = 위 측정의 다른 키맵. `mapping.py` 9 행 KIT.
3. 생성기: 셀 `|` → `&#124;` (HTML 엔티티, 백슬래시 없음) + 모든 표 행 열 수 검사 (다르면 exit 1).
4. 다음 단계 고려: 88 (manual_checks → GUI) 는 이 단계의 GUI 테스트를 그대로 포함.

## 검증 계획

- 헤드리스 `tests/test_step87_view_keys.py`: 순환 상태 표, 1 픽셀 이동량 (순수 함수: 화면 1 px 의 세계 길이), ortho_scale 식, 키맵 항목 /
  transfer_mode 제거, 대응표 열 수 (`docs/keymap_mapping.md` 모든 행 8 칸).
- GUI `tests/gui/gui_step87_view_keys.py`: Alt+A 세 번 (in_front / 아마추어 숨김 / 복원), Alt+P (persp ↔ ortho), Alt+→ 큐브 화면 1 px,
  ` 누르는 동안 Tweak 툴 → 놓으면 Move, 카메라 뷰 \ + LMB 드래그 = view_camera_offset 바뀜. 스크린샷.
- 전체 헤드리스·GUI, dogfood, manual_checks.

## 한 것

- `operators/view_keys3.py` (새): `cycle_display` (Maya 3 상태 순환, 조인트 X-ray = 아마추어 In Front 저장·복원, 조인트·커브 = 뷰 필터,
  인뷰 메시지), `camera_mode_toggle` (사용자 뷰 view_persportho, 카메라 뷰 = 카메라 타입 + ortho_scale = 2·d·tan(fov/2)), `pixel_move`
  (매니퓰레이터 중심을 화면 1 px 옮긴 세계 벡터로 transform.translate), `tweak_hold` (` 동안 Tweak 툴, 놓기를 다른 모달이 먹으면 keystate +
  transform 끝 대기), `pan_zoom_hold` (\ 동안 카메라 뷰 LMB 팬 = view_camera_offset, MMB 줌 = view_camera_zoom; 사용자 뷰 = Help Line 안내).
- `keymap/maya_patches.py` 42 `patch_view_keys_3` ("3D View" 9 항목, Object Non-modal ` transfer_mode 제거), `keystate` 에 BACK_SLASH (VK 0xDC).
- `keymap/mapping.py` 10 행 KIT (CycleDisplayMode, CameraModeToggle, MoveUp/Down/Left/Right, STRSTweakModeOn, TogglePanZoomPress / Release);
  `entry_for` 가 release 만 있는 행 (TogglePanZoomRelease) 도 찾음 → 대응표 구현 133 → 142, 미검토 246 → 237.
- `tools/gen_keymap_mapping.py`: 셀의 `|` = `&#124;` (`cell`), 표마다 열 수가 머리 행과 다르면 exit (`bad_rows`). `Shift+&#124;` 행 고침.
- 판단 (delegated): 조인트 X-ray 는 장면 아마추어의 In Front (뷰별 아님); UV 에디터 Alt+화살표 넛지 없음; 2D 팬/줌은 카메라 뷰에만
  (Blender 사용자 뷰에 필름백 없음); ` 는 Select/Move/Rotate/Scale/Transform 툴에서만 (Maya strsTweakMode 와 같은 조건).
- 덤: step_86.md 「검증」 의 줄바꿈 빠진 곳 고침.

## 검증

- 헤드리스 `tests/test_step87_view_keys.py` 6/6 (순환 표, In Front 저장·복원 + 뷰 필터, ortho_scale 식, 카메라 오프셋 방향·줌, 키맵 9 항목 +
  transfer_mode 제거, 대응표 모든 표의 열 수 + `Shift+&#124;`), 키맵 12/12.
- GUI `tests/gui/gui_step87_view_keys.py` 10/10 (MayaKit): Alt+A ×4 (In Front 켬 → 끔 → 아마추어·커브 숨김 → 다시 X-ray), Alt+P persp → ortho → persp,
  Alt+→ 큐브 화면 +1.041 px (y −0.003), ` 누름 = builtin.select / 놓음 = builtin.move, 카메라 뷰 \ + LMB 80 px 오른쪽 = view_camera_offset
  x 0 → −0.063 (카메라 그대로). 스크린샷 `gui_step87_pan_zoom.png`: 카메라 프레임이 오른쪽으로.
- 전체: 헤드리스 677/677, GUI (기본 배율) 621/621, dogfood 47/47 (콘솔 0). `docs/manual_checks.md` 「Step 87」 5 항목.

## 남은 것

- Maya 실행 비교 안 함 (\ 2D 팬/줌의 MMB = 줌은 [K]; 팬 감도는 카메라 프레임 폭 기준 추정).
- UV 에디터 Alt+화살표 (Maya performPolyNudgeUVs) 없음. 사용자 뷰 2D 팬/줌 없음 (Blender 한계, 안내만).
- 대응표 미검토 237 행 (time slider 북마크 Alt+T 등) 은 그대로.
- 다음: 88 manual_checks → GUI 테스트 정리 (재점검 5차 backlog 마지막).

