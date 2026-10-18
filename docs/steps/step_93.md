# Step 93 — 선택 마스크 다듬기 (Shift+Q 체크 표시, New / Open 에서 마스크, Reset Tool)

재점검 6차 backlog 4 (docs/PLAN.md 「재점검 6차」 우선순위 4; 재점검 5차 blindspot 6; PLAN:451, :491).

## 근거

- Shift+Q `doSelectComponentMM`: Poly Vertices / Poly Edges / Faces 는 체크 상자 항목 (현재 컴포넌트 마스크), All Components on / off 는 명령
  (research/maya/marking_menus.json, buildSelectComponentMM.mel:31-160). kit 는 `maya_kit.component_mask` (step 78) 로 동작하지만
  `marking/draw.checked` 가 그 상태를 몰라 체크 표시가 없음 (draw.py:145-158, engine.TOGGLE_OPS).
- **New / Open 의 마스크 — Maya 측정 결과가 backlog 문구와 반대** (`research/maya/re/selection_masks.md`; Maya 2022 GUI 실행
  `research/scripts/maya_masks/masks_gui.py`, 로그 `research/maya/screens/masks/_log.txt`): Status Line 오브젝트 마스크 (polymesh / nurbsCurve /
  joint 끔) 와 컴포넌트 마스크 (edge / face 끔), select mode 모두 `file -new` / `file -open` 뒤에도 **그대로**. Maya 마스크는 세션 상태.
  Blender 는 오브젝트 선택 필터 (`SpaceView3D.show_object_select_*`) 를 파일의 화면 데이터에, 메시 선택 모드를 장면에 저장하므로 New / Open
  때마다 파일의 값으로 바뀜 = Maya 와 다름. 그래서 "초기화" 대신 **세션 마스크를 로드 너머로 유지** 한다 (delegated, 측정 근거).
- Reset Tool: Maya Tool Settings 상단의 **Reset Tool** / Tool Help 버튼 (research/maya/ui_layout.md:267-268, initToolSettings.mel:53-55).
  Maya 툴 기본값: Move 축 World, Rotate / Scale 축 Object (pivot_snap.md P12), Step Snap 끔, 회전 스텝 15°, 스케일 스텝 1 (S3) — 템플릿이 이미
  같은 값 (tools/make_startup.py:353-361).

## 계획 (delegated)

1. 체크 표시: `engine.is_toggle` 이 `maya_kit.component_mask` 의 VERT / EDGE / FACE 를 토글로 인정 (ALL 은 명령이라 아님),
   `draw.checked` = `tool_settings.mesh_select_mode[i]`.
2. 마스크 유지: `ui/status_line.py` 에 load_pre / load_post 핸들러 — load_pre 에서 지금 창의 큰 3D 뷰의 `show_object_select_*` 와 장면의
   `mesh_select_mode` 를 기억, load_post 에서 새 파일의 모든 3D 뷰와 장면에 적용. 처음 켜질 때 (기억 없음) 는 아무것도 안 함. 파일의 다른
   화면 데이터는 그대로.
3. Reset Tool: `ui/tool_settings.py` (새) — `maya_kit.reset_tool` + `VIEW3D_PT_active_tool` 맨 위에 [Reset Tool] 줄 (prepend, unregister 때
   remove). 동작: 활성 WorkSpaceTool 의 툴 키맵에 있는 연산자마다 `tool.operator_properties(idname)` 의 속성을 `property_unset` (Blender 기본값),
   Move / Rotate / Scale 이면 Maya 기본값 — 그 툴의 축 슬롯 (GLOBAL / LOCAL / LOCAL), 피벗 ACTIVE_ELEMENT (step 59), 그 툴의 Step Snap 끔
   (`snap_align.set_step_snap`), 회전 스텝 15°, Move 면 Smart Duplicate / Smart Extrude 를 환경설정 기본값으로. Tool Help 는 만들지 않음 (Blender
   툴 툴팁·매뉴얼로 충분, delegated).
4. 다음 단계 고려: 94 (피벗 RMB 메뉴) 의 Pin / Reset 항목도 `checked` 경로를 쓸 수 있게 `is_toggle` 확장 방식을 일반적으로 둠.

## 검증 계획

- 헤드리스 `tests/test_step93_selection_masks.py`: is_toggle / checked (VERT·EDGE·FACE 상태, ALL = None), load_pre → read_homefile → load_post 뒤
  마스크와 선택 모드가 그대로 (기억 없을 때는 파일 값), Reset Tool (툴 연산자 속성 unset, Move/Rotate/Scale Maya 기본값 복원, Step Snap 끔).
- GUI `tests/gui/gui_step93_masks.py`: 편집 모드 Shift+Q 홀드 + LMB → 메뉴 스크린샷 (Points ▸ 안의 Poly Vertices 체크 / Faces 체크 상태),
  Status Line 마스크 끔 → File > New (read_homefile) → 여전히 끔, Tool Settings 팝업의 Reset Tool 버튼 스크린샷.
- 전체 헤드리스·GUI, dogfood.

## 한 것

- Maya 2022 측정: mayapy 는 `selectType` 이 None (UI 상태) → GUI Maya 실행 (`research/scripts/maya_masks/`) 로 다시 잼 → 마스크는 New / Open
  너머로 유지. 명세 `research/maya/re/selection_masks.md` (research 는 git 밖), `docs/PLAN.md` 의 "masks reset" 문구 두 곳에 측정 결과 덧붙임.
- `marking/engine.py`: `TOGGLE_OPS` + `maya_kit.component_mask`, `MASK_CHECKS` (VERT / EDGE / FACE 만 체크 상자). `marking/draw.py` `checked`:
  `mesh_select_mode`.
- `ui/status_line.py`: `session_masks` / `apply_masks` + load_pre / load_post 핸들러 (오브젝트 선택 필터 = 큰 3D 뷰에서 읽어 모든 3D 뷰에,
  메시 선택 모드 = 모든 장면에), unregister 때 제거.
- `ui/tool_settings.py` (새): `maya_kit.reset_tool` (툴 키맵 연산자 옵션 `property_unset`, Move/Rotate/Scale Maya 기본값: 축 World/Object/Object,
  피벗 ACTIVE_ELEMENT, Step Snap 끔, 회전 15°, Move = Smart Duplicate / Extrude 기본값) + `VIEW3D_PT_active_tool` 맨 위 [Reset Tool].

## 검증

- 헤드리스 `tests/test_step93_selection_masks.py` 6/6: 체크 상자 판정 (ALL 은 명령), `checked` = 선택 모드, Shift+Q 메뉴에 세 항목, 메시·커브
  필터 끔 + 엣지 모드 → `read_homefile` 뒤에도 그대로 (다른 필터는 켜짐), 기억 없으면 그대로, Rotate Reset (release_confirm unset, 축 LOCAL,
  피벗, 15°, Step Snap 끔), Move Reset (Smart Duplicate 기본값, 축 GLOBAL, transform.translate 포함), 패널 행. 관련: enable_disable 4/4,
  step 8 11/11, 78 8/8, 59 16/16, 60 4/4, 42 4/4.
- GUI `tests/gui/gui_step93_masks.py` 5/5: 편집 모드 Shift+Q 홀드 + LMB → 메뉴, Faces 체크 켜짐; Status Line 메시 마스크 끔 → File > New (MayaKit
  템플릿 다시 읽기) → 여전히 끔, 다른 마스크 그대로; Tool Settings 팝업에 Reset Tool. 스크린샷 직접 확인: `gui_step93_shift_q.png` (Faces 옆
  채워진 체크 상자, All Components on 은 상자 없음), `gui_step93_reset_tool.png` (팝업 맨 위 Reset Tool, 아래 Move Settings).
- 전체 헤드리스 `python tests/run.py`: **698/698** (84 파일). 전체 GUI `python tests/gui/run.py`: **698/698** (74 파일).
- `python tools/dogfood.py`: **47/47**, 콘솔 0.

## 남은 것

- 마스크 유지는 Blender 세션 안에서만 (Maya 처럼 재시작 너머로 저장하지는 않음 — Maya 는 optionVar 로 남는지 측정 안 함).
- Maya 의 selectMode (object / component) 유지는 하지 않음 — Blender 는 파일이 저장한 모드로 열림 (파일 데이터, delegated).
- Tool Help 버튼 없음. Reset Tool 은 OBJECT / EDIT_MESH 의 툴만 (manipulator.MODES).
- 다음: step 94 = 피벗 편집 RMB 마킹 메뉴.
