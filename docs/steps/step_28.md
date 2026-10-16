# Step 28 — MMB 드래그 = 마지막으로 잡은 핸들

## 계획 (delegated)

### 근거

- Maya: Move/Rotate/Scale 툴에서 **MMB 드래그 = 현재 활성 핸들** (마지막으로 클릭한 축/평면), 매니퓰레이터를 맞힐 필요 없음.
  `manipsRememberActiveHandle true`, `manipsRememberActiveHandleAfterToolSwitch true`, `manipMiddleMouseRepos false`
  (research/maya/interaction.md:103, defaults.json:63-65, PREF:357-359). 같은 툴 키를 다시 누르면 중앙 핸들(자유)로 [K].
- 지금 (생성된 Maya 키컨피그 실측): `3D View Tool: Move/Rotate/Scale` 의 MMB PRESS = `transform.translate/rotate/resize` (제약 없음),
  그 앞에 `maya_kit.cb_virtual_slider` (Channel Box 채널 선택 시만, 아니면 PASS_THROUGH, step 6).

### 어떤 핸들을 잡았는지 아는 방법

- C 기즈모의 개별 핸들은 Python 으로 알 수 없지만, 핸들을 끌고 나면 그 transform 이 `wm.operators` 에 등록되고 `constraint_axis`,
  `orient_type` (회전은 `orient_axis`) 가 남는다. step 26 의 감시 타이머(`Window.modal_operators` 로 모달 끝 대기)를 재사용해
  **기즈모 LMB 누름 → 변환이 끝나면 마지막 transform 의 제약을 툴별로 기억**한다. 중앙(화면 평면) 핸들은 제약 없음 = 자유.
- 키맵: 기즈모 키맵 (`Generic Gizmo Maybe Drag` / `Drag`) 맨 앞에 수정키 없는 LMB PRESS → `maya_kit.manip_press` (PASS_THROUGH,
  xform 기즈모일 때만 감시). Shift 누름 (`manip_duplicate`) 도 같은 기억을 한다.

### MMB

- `maya_kit.manip_mmb(mode)` : 기억한 제약으로 `transform.translate / rotate / resize` 를 INVOKE (release_confirm). 기억이 없으면 자유
  (지금과 같음). Tool 키맵의 IC MMB PRESS 항목을 이것으로 교체 (CB 슬라이더 항목 뒤 그대로).
- 리셋: Q/W/E/R 탭 (`ToolOptionsBinding.tap`) 에서 이미 그 툴이면 그 툴의 기억을 지움 (Maya 중앙 핸들로).
- 기억은 세션 동안만 (Maya 는 optionVar), 툴별 (`TRANSLATE` / `ROTATE` / `RESIZE`), 툴을 바꿔도 유지 (AfterToolSwitch true).

### 검증

- 헤드리스: 등록된 transform 연산자 → 기억 변환 (축·평면·자유·회전 축), 리셋, 키맵 항목 순서 (CB 슬라이더 → manip_mmb).
- GUI: Move 툴 X 화살표 클릭-드래그 → 뷰 빈 곳 MMB 드래그 → X 로만 이동; W 다시 탭 → MMB 드래그 → 자유 (Y/Z 도 바뀜).

## 한 것

- `operators/manip.py`: `HANDLES` (툴별 마지막 핸들), `handle_from_op()` (등록된 transform 의 `constraint_axis` / `orient_type` /
  회전 `orient_axis` → 핸들, 제약 없음·뷰 링 = 자유), `remember_last_op()`, `reset_handle()`. `finish()` 가 감시 끝에 핸들을 기억
  (Shift 복제·압출이 움직였을 때도). `maya_kit.manip_press` (기즈모 일반 LMB 누름 → 감시, PASS_THROUGH),
  `maya_kit.manip_mmb(mode)` (기억한 제약으로 `transform.*` INVOKE, release_confirm).
- 키맵 patch 24 (`patch_active_handle`): 기즈모 키맵 맨 앞 LMB PRESS → `manip_press`; `3D View Tool: Move/Rotate/Scale` 의 IC MMB PRESS
  `transform.*` 를 같은 자리(CB 슬라이더 뒤)에서 `manip_mmb` 로 교체. `PASS_THROUGH_FIRST` 에 `manip_press`.
- `marking/__init__.py` `ToolOptionsBinding.tap`: 이미 그 툴이면 그 툴의 핸들 리셋 (중앙 = 자유).
- `test_step22_manip.py`: 기즈모 키맵 맨 앞이 이제 `manip_press` 라 순서 검사를 "gizmo_tweak 보다 앞" 으로.

### 실측

- 이벤트 시뮬레이션에서 MMB 누름으로 시작한 중첩 transform 모달은 같은 틱의 마우스 이동을 받지 못함 → GUI 테스트는 누름 / 이동 /
  놓기를 다른 틱으로 (실제 입력은 이벤트가 시간 간격을 두고 오므로 해당 없음).

## 검증

- 헤드리스 `python tests/run.py`: **264/264** (27 파일, 새 `test_step28_active_handle.py` 4개: 축·평면·자유·회전 축·뷰 링 판별, 리셋, 키맵
  순서 (기즈모 맨 앞 manip_press, Tool 키맵 MMB = CB 슬라이더 → manip_mmb), poll).
- GUI `python tests/gui/run.py`: **206/206** (21 파일, 새 `gui_step28_active_handle.py` 4개: X 화살표 드래그 → 기억 (X, GLOBAL); 기즈모에서 먼
  곳 MMB 대각선 드래그 → (2.693, 0, 0) X 만; W 다시 탭 → 리셋; MMB 드래그 → (0.958, 0.954, −0.987) 자유).
- `python tools/dogfood.py`: **47/47**, 콘솔 오류 0.

## 남은 것

- Maya 는 활성 핸들을 노랗게 표시 — C 기즈모 색은 바꿀 수 없음 (헤더 텍스트 등 대체 표시는 안 함).
- Shift+MMB = 드래그 방향에 가까운 축 자동 선택 (interaction.md:106) 은 안 함 (Blender 변환 중 MMB 자동 제약으로 비슷하게 가능).
- Ctrl+LMB 축 핸들 = 수직 평면 (interaction.md:104) 은 안 함.
- 핸들 기억은 세션 동안만 (Maya 는 optionVar 로 저장).
