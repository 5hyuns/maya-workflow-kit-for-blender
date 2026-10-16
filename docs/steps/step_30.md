# Step 30 — 선택 감각: 마키 관통 · 프리셀렉트 · 언두 큐

## 계획 (delegated)

### 근거

- Maya 마키(LMB 드래그)는 사각형 안의 모든 것을 선택한다. 가려진 컴포넌트도 포함하며, "Camera based selection"을 켜야 앞면만 잡힌다.
  (`selectPrefUseDepth false`, research/maya/interaction.md:68, research/maya/defaults.json:98)
- 프리셀렉트: 마우스 아래 컴포넌트·오브젝트를 하이라이트한다 (`preSelectHilite true`, interaction.md:73, defaults.json:96).
- 언두 큐는 무한이다 (`undoIsInfinite true`, interaction.md:222, defaults.json:130-134). Blender `edit.undo_steps` 기본 32, 상한 256 (실측).
- PLAN 「재점검 1차」 B6–B8 (docs/PLAN.md:97, :163).

### 1. 마키 관통 (Blender 실측)

- 편집 모드 박스 선택은 뷰의 **X-Ray 플래그**만 보고 가려진 요소를 포함한다. 투명도는 상관없어서 X-Ray + 알파 1.0 = 면은 불투명,
  선택은 관통 (GUI 실측: 기본 큐브 앞에서 박스 선택 7/8 → 8/8).
- 하지만 플래그를 켜 두면 숨은 엣지·정점이 비쳐 보이고 헤더 X-Ray 버튼이 켜진 것으로 보인다 → **드래그하는 동안만** 켠다.
- `maya_kit.select_through`: 셀렉트 툴 키맵 4개 (`3D View Tool: Select Box` / `Select Lasso` 와 `(fallback)` = Move/Rotate/Scale 툴의
  빈 곳 드래그) 맨 앞, LMB CLICK_DRAG 의 수정키 4조합. 메시 편집 모드 + 옵션 켜짐 + X-Ray 꺼짐이면 플래그 켬, 알파 1.0, PASS_THROUGH →
  뒤의 `view3d.select_box` / `select_lasso` 가 같은 이벤트를 받음. 타이머가 그 모달이 끝나면 (또는 1 초 안에 못 보면) 원래 값으로.
- 사용자가 X-Ray 를 켜 두었으면 손대지 않음 (이미 관통). 원(circle) 선택은 Maya 에 없어서 제외.
- 환경설정 `select_through` (기본 켬, Maya 기본).

### 2. 프리셀렉트 (4.5 에서 가능한 것)

- Blender 4.5 는 Poly Build / Loop Cut 툴 안에서만 프리셀렉트. 그 C 기즈모 타입 `GIZMO_GT_mesh_preselect_elem_3d` (blender.exe 문자열)를
  Python 기즈모 그룹에서 만들 수 있다 (실측). 빈 커스텀 키맵을 주면 호버가 안 됨 → Blender 기본 기즈모 키맵 유지; 클릭 선택·마키는
  그대로 셀렉트 툴로 감 (GUI 실측).
- 제한 (delegated): 셀렉트 툴일 때만 (test_select 기즈모가 매니퓰레이터 핸들보다 먼저 호버를 가져가므로 Move/Rotate/Scale 에서는 끔),
  정점 선택 모드일 때만 (이 기즈모는 선택 모드를 무시하고 면 모드에서도 정점을 밝힘 — 실측). 오브젝트 모드 프리셀렉트 없음.
- 환경설정 `preselect_highlight` (기본 켬).

### 3. 언두 큐

- `prefs_preset` 에 그룹 개념: navigation (기존) + undo (`edit.undo_steps` = 256, `use_maya_undo`, 백업 `undo_backup`). 첫 활성화에 백업 후
  적용, 옵션 끄기 / 애드온 끄기 = 복원. `tests/kit.py` 가 `preferences.edit` 도 스냅샷 → test_enable_disable 이 누수를 잡음.

### 검증

- GUI: 마키 8/8, 드래그 중 X-Ray (켬, 1.0), 끝나면 원래 (끔, 0.5); Move 툴 fallback 8/8; 옵션 끔 7/8; 사용자 X-Ray 유지; 정점 호버 =
  하이라이트, 클릭 선택, 하이라이트된 정점에서 시작한 마키; 면 모드·Move 툴 = 프리셀렉트 없음; 스크린샷.
- 헤드리스: 키맵 순서, 감시 타이머 복원, 기즈모 그룹 등록, 언두 256 ↔ 32, test_enable_disable (prefs.edit).

## 한 것

- `operators/marquee.py` (새): `begin()`, 감시 타이머 `_watch` (창의 `modal_operators` 에서 `VIEW3D_OT_select_box/lasso` 를 보고, 끝나면 복원),
  `restore_all()` (unregister), `maya_kit.select_through` (PASS_THROUGH).
- 키맵 patch 26 (`patch_select_through`): 위 4 키맵 × 4 수정키 조합 맨 앞, `PASS_THROUGH_FIRST` 에 추가, `shadows=(km,)` 선언.
- `operators/preselect.py` (새): `MAYAKIT_GGT_preselect` (3D, PERSISTENT, SELECT; `GIZMO_GT_mesh_preselect_elem_3d` 하나).
- `prefs_preset.py`: `UNDO_PRESET`, `GROUPS`, `apply/restore(group=...)`, register/unregister 가 모든 그룹 처리.
- `preferences.py`: `use_maya_undo` (+ `undo_backup`), `select_through`, `preselect_highlight` 와 환경설정 UI.
- `tests/kit.py`: `prefs_edit` 스냅샷. `tests/test_keymap_maya.py`: 셀렉트 툴 키맵 스택.
- 테스트: `tests/test_step30_selection.py` (5), `tests/gui/gui_step30_selection.py` (14 체크, 스크린샷 4장).

## 검증

- 헤드리스 `python tests/run.py`: **279/279** (29 파일, step 30 5개 포함; test_enable_disable 이 이제 `preferences.edit` 도 비교).
- GUI `python tests/gui/run.py`: **232/232** (23 파일). step 30 14 체크: 마키 8/8 (기본 7/8), 드래그 중 X-Ray (켬, 1.0) → 끝나면 (끔, 0.5),
  Move 툴 fallback 8/8, 옵션 끔 7/8, 사용자 X-Ray 유지, 정점 호버 하이라이트, 클릭 선택, 하이라이트된 정점에서 시작한 마키, 면 모드·Move 툴은
  프리셀렉트 없음.
- 스크린샷 (`tmp/shots30/`) 직접 확인: 드래그 중 숨은 엣지가 옅게 보이고 면은 불투명; 정점 하이라이트 = 정점 위 작은 하늘색 점.
- dogfood `python tools/dogfood.py`: **47/47**, 콘솔 오류 0.

## 남은 것

- 프리셀렉트는 정점 모드 + 셀렉트 툴만. 엣지/면 하이라이트, Move/Rotate/Scale 툴 중 하이라이트, 오브젝트 프리셀렉트는 직접 그려야 함
  (마우스 아래 요소 계산 + GPU 그리기). 하이라이트 점이 Maya(`MT_preSelectSize 16`)보다 작음: C 기즈모의 크기·색은 Python 에서 못 바꿈.
- 마키 관통은 메시 편집 모드만 (커브/라티스 편집은 Blender 가 원래 가림 검사 안 함). 원 선택은 그대로.
- 언두 256 단계 = Blender 상한 (Maya 무한과 차이). 시간 변경 묶기(`timeChangeUndoConsolidation`)는 미대응.
