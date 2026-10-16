# Step 26 — Smart Extrude, 그리고 Shift+매니퓰레이터의 남는 사본 정리

## 계획 (delegated)

### 근거

- Maya: 면/엣지에서 매니퓰레이터 Shift+드래그 = Smart Extrude (`manipSmartExtrude 1`, research/maya/interaction.md:107,
  PREF:371-374). W/E/R 홀드 메뉴의 "Smart Extrude" / "Smart Duplicate" 는 그 옵션 토글 (marking/menus.py OPT_MOVE/ROTATE/SCALE).
- step 22: Maya 키컨피그 기즈모 키맵 맨 앞 Shift+LMB PRESS → `maya_kit.manip_duplicate` (복제 후 PASS_THROUGH, 기즈모가 변환).
  남은 것: 드래그 없는 Shift+클릭과 RMB/Esc 취소 때 사본이 남음, 같은 키맵을 쓰는 다른 기즈모(라이트 등)도 걸릴 수 있음.

### 측정 (임시 GUI 프로브)

- 기즈모 키맵에서 불린 연산자의 `context.gizmo_group.bl_idname` = `"VIEW3D_GGT_xform_gizmo"` → 어떤 기즈모를 잡았는지 정확히 안다.
- `Window.modal_operators` 에 드래그 중 `TRANSFORM_OT_translate`, RMB 취소 뒤 빈 목록 → 변환이 끝난 때를 타이머로 안다.
- RMB 취소 뒤 사본 `Cube1` 이 원점에 남음 (`wm.operators` 에 새 항목 없음).

### 설계

1. `operators/manip.py` `maya_kit.manip_duplicate` (이름 유지, 키맵 그대로) 가 두 경우를 처리:
   - 잡은 기즈모가 xform 기즈모가 아니면 (`gizmo_group.bl_idname` ∉ {`VIEW3D_GGT_xform_gizmo`, `VIEW3D_GGT_xform_gizmo_context`})
     아무것도 안 함 → 라이트·카메라·스포트 기즈모 제외. (이전의 툴/오버레이 조건은 이것으로 대체.)
   - 오브젝트 모드 + 선택 + `smart_duplicate` → 복제 (step 22).
   - 메시 편집 모드 + 면 또는 엣지 선택 모드 + 선택 있음 + `smart_extrude` (새 환경설정, 기본 켬) → `mesh.extrude_region`
     (이동 없이; 엣지도 region 압출이라 이어진 띠가 됨 = Maya polyExtrudeEdge keepFacesTogether 기본 [K]; 지시의 extrude_edges_indiv
     대신 delegated). 정점 모드는 그냥 통과.
   - 항상 PASS_THROUGH → 기즈모가 새 사본/새 요소를 변환.
2. 정리 감시 (bpy.app.timers, 0.05 s): 변환 모달이 끝날 때까지 기다린 뒤
   - 사본/새 요소가 움직였으면 (사본 `matrix_world` 또는 선택 정점 좌표가 누를 때와 다름) 그대로 둔다.
   - 안 움직였으면 되돌린다:
     - 변환이 확정되어 등록됐으면 (`wm.operators` 마지막 항목이 새 transform) `ed.undo` 한 번 — 복제/압출은 중첩 호출이라 언두
       단계가 없으므로 한 번에 누르기 전 상태로 (redo 로 다시 가능).
     - 취소였으면 (새 등록 없음, 언두 단계도 없음) 직접 되돌림: 사본 삭제 + 원래 선택 복원 / 압출 전 메시 복사본으로 bmesh 교체.
3. 환경설정 `smart_extrude` (기본 켬), `maya_kit.manip_option(option='SMART_EXTRUDE')`, 홀드 메뉴 "Smart Extrude" 연결.
4. 토글 표시: marking engine 이 토글 액션 (`wm.context_toggle`, `maya_kit.manip_option`) 의 라벨 폭에 체크 상자 자리를 남기고,
   draw.py 가 오른쪽에 상자 (켜짐 = 채움) 를 그린다. 상태는 data_path / 환경설정에서 읽음.

### 검증

- 헤드리스: 압출 함수 (면/엣지 → 면 수 증가, 정점 모드 통과), xform 기즈모가 아니면 통과, 옵션 끔, 토글 상태 읽기, 엔진 라벨 폭.
- GUI: F11 면 하나 → Shift+X 화살표 드래그 → 면 수 증가 + 새 면 이동 (원래 면 위치 그대로); Shift+클릭만 → 변화 없음 (면 수·오브젝트
  수); 오브젝트 Shift+드래그 후 RMB 취소 → 사본 없음; W 홀드 메뉴 스크린샷 (체크 표시).
- 전체 헤드리스·GUI·dogfood, manual_checks.

## 한 것

- `operators/manip.py`: `kind()` = xform 기즈모 (`context.gizmo_group.bl_idname`) + 오브젝트 모드 → `DUPLICATE`, 메시 편집 모드의 면/엣지
  선택 → `EXTRUDE` (`mesh.extrude_region`, 이동 없이). `watch()` 타이머가 `Window.modal_operators` 로 변환 끝을 기다린 뒤 `finish()`:
  움직였으면 유지, 안 움직였으면 확정 등록 시 `ed.undo` 한 번 / 취소 시 `revert()` (사본 삭제 + 선택 복원, 또는 저장해 둔 메시로 bmesh
  교체). 이전의 툴/오버레이 조건(`gizmo_shown`)은 기즈모 그룹 판별로 대체.
- 환경설정 `smart_extrude` (기본 켬), `maya_kit.manip_option` 에 `SMART_EXTRUDE`, W/E/R 홀드 메뉴 "Smart Extrude" 연결.
- 마킹 메뉴 체크 상자: `engine.is_toggle()` (`wm.context_toggle`, `maya_kit.manip_option`) 라벨 폭에 상자 자리, `draw.checked()` 가
  data_path / 환경설정을 읽어 오른쪽에 상자 (켜짐 = 파란 채움).

### 계획과 다르게 된 것 / 실측

- 엣지도 `extrude_region` (이어진 엣지 띠가 이어진 채 압출, Maya keepFacesTogether 기본 [K]) — 지시의 extrude_edges 대신 (delegated).

## 검증

- 헤드리스 `python tests/run.py`: **256/256** (25 파일, 새 `test_step26_smart_extrude.py` 7개: 모드·옵션·기즈모 그룹별 kind, 면 압출 후
  revert (8/12/6 로) + 저장 메시 정리, 이동하면 유지, 엣지 압출 10/15/7, 사본 revert 와 선택 복원, 홀드 메뉴 토글·체크 상태;
  `test_step22_manip.py` 를 새 판별 함수에 맞춤).
- GUI `python tests/gui/run.py`: **195/195** (19 파일, 새 `gui_step26_smart_extrude.py` 8개: F11 윗면 Shift+Z 화살표 드래그 → 6 → 10 면, 윗면
  z 2.23 (원래 윗면 제자리); Shift+클릭만 → 그대로; 오브젝트 Shift+드래그 → 사본 생김 → RMB 취소 → 사본 없음, 원본 선택·활성;
  `--debug-handlers` 로 세 번 모두 `MAYA_KIT_OT_manip_duplicate` 매칭 확인). 스크린샷 `tmp/shots26/gui_step26_smart_extrude.png`,
  `gui_step26_w_menu_checks.png` (Smart Extrude / Smart Duplicate 채움, Preserve UVs / Children 빈 상자).
- `python tools/dogfood.py`: **46/47** (남은 실패 `=`), 콘솔 오류 0.

## 남은 것

- 회전·스케일 기즈모에서의 압출 (Maya 도 압출 후 회전/스케일) 은 같은 경로지만 GUI 로는 이동만 확인 (manual_checks).
- 정점 모드 Shift+드래그는 Blender 기본 (Maya 의 정점 Smart Extrude 없음 [K]).
- 압출 + 이동은 언두 한 단계 (Maya 는 polyExtrude 노드 + 이동이 따로일 수 있음).
- 파이 메뉴 스타일(Blender pie) 에는 체크 표시 없음.
