# Step 18 — 편집 모드(메시) 키: D 피벗, 선택, 즉시 Extrude/Bevel, 선택 확장·변환

재점검 1차 backlog 4 (`docs/steps/step_14.md` B3·B5, dogfood Shift+> 실패).

## 계획

근거: research/maya/interaction.md §2 (:75 Ctrl+Shift+A / Alt+D — SelectNone 은 오브젝트 모드로 돌아감, :79 Ctrl+F9–F12 변환,
:82 `>` `<` (Ctrl: loop) 확장/축소), §4 (:124 D 홀드 = 피벗 편집, :127 컴포넌트 피벗, :129 pin pivot);
hotkeySetup.mel 줄은 docs/keymap_mapping.md (HK:59, 62, 262-269, 355, 384-385).

현재 Maya 키컨피그의 Mesh 키맵 (실측): D = Annotate 툴, Ctrl+Shift+A = 전체 **해제**, Alt+D 없음, Ctrl+E/Ctrl+B = Extrude/Bevel **툴 전환**,
Shift+> / Shift+< / Ctrl+F9–F11 없음.

결정 (모두 delegated):

1. **D (메시 편집)** = 새 홀드 `maya_kit.hold(name="component_pivot")`: 누르는 동안 피벗 = 3D 커서 + 커서 툴 (LMB 드래그로 피벗 위치를
   옮김; X/C/V 홀드 스냅도 함께 씀). 놓으면 원래 툴로 돌아가고,
   - 누르는 동안 커서를 옮겼으면 피벗을 커서에 **남긴다** (Maya 의 사용자 컴포넌트 피벗 = 유지, :127-129),
   - 그냥 탭(커서 그대로)이면 사용자 피벗을 **지운다**: 원래 피벗이 커서였으면 Median Point 로, 아니면 원래 값으로
     (Maya "Reset pivot" 에 해당; research 의 "탭 = 모드 토글" 은 [I] 라 이쪽을 택함).
   오브젝트 모드 D(Affect Only Origins)는 그대로. Blender 의 오브젝트 원점처럼 "선택이 바뀌면 리셋" 은 하지 않는다 (남은 것).
2. **Ctrl+Shift+A** = `mesh.select_all(SELECT)`. **Alt+D** = 새 `maya_kit.select_none`: 컴포넌트 선택 해제 → 오브젝트 모드 →
   객체 선택 해제 (Maya SelectNone, :75).
3. **Ctrl+E** = `view3d.edit_mesh_extrude_move_normal` (압출 + 바로 이동 모달 = Maya 압출 후 매니퓰레이터 드래그에 해당).
   **Ctrl+B** = 새 `maya_kit.bevel`: 정점만 선택 모드면 `mesh.bevel(affect='VERTICES')`, 아니면 `affect='EDGES'` 를 INVOKE (모달 드래그).
4. **Shift+> / Shift+<** = `mesh.select_more` / `mesh.select_less`; **Ctrl+Shift+> / <** (Maya: 루프 방향 확장/축소) =
   `mesh.select_next_item` / `mesh.select_prev_item` (선택 순서 따라 한 칸 — 근사).
5. **Ctrl+F9 / F10 / F11** = `mesh.select_mode(type=VERT/EDGE/FACE, use_expand=True)` (Maya 변환은 닿는 요소 포함). Ctrl+F12(UV) = 해당 없음.
6. 키맵 지뢰: 모두 Mesh 키맵 안에서 IC 항목을 지우고 추가 → 가림/충돌 검사 (`_STACKS["Mesh"]`). `.`/`,` (step 20 의 다음/이전 키)와는
   Shift 유무로 다른 이벤트.

검증: 헤드리스 (바인딩, 피벗 놓기 규칙 함수, select_none, bevel affect 선택, 매핑 행), GUI (면 하나 선택 → Shift+> 개수 증가 → Shift+<
원래대로, Ctrl+E 후 면 수 증가, Ctrl+B 후 면 수 증가, Ctrl+F9 면→정점 변환, D 홀드 중 커서 툴·피벗 CURSOR, 놓으면 툴 복원, Alt+D 오브젝트 모드),
`python tools/dogfood.py` Shift+> PASS.

## 한 것

- `keymap/maya_patches.py` 19 `patch_mesh_components` (Mesh 키맵): D → `maya_kit.hold(component_pivot)` (IC Annotate 제거),
  Ctrl+Shift+A → `mesh.select_all(SELECT)` (IC 해제 대신), Alt+D → `maya_kit.select_none`, Ctrl+E →
  `view3d.edit_mesh_extrude_move_normal` / Ctrl+B → `maya_kit.bevel` (IC 툴 전환 제거), Shift+> / Shift+< → `select_more` / `select_less`,
  Ctrl+Shift+> / < → `select_next_item` / `select_prev_item`, Ctrl+F9/F10/F11 → `maya_kit.convert_selection`.
- `operators/hold.py`: `ComponentPivotGroup` + `component_pivot_after` (놓을 때 규칙), 홀드 중 커서 툴로 바꾸고 놓으면 원래 툴.
- `operators/component.py` (새): `maya_kit.select_none`, `maya_kit.bevel` (`bevel_affect`), `maya_kit.convert_selection`
  (`touching` / `select_only`). 계획 5 의 `mesh.select_mode(use_expand=True)` 는 4.5 에서 **선택을 비움** (실측: 면 하나 → 0/0/0),
  `use_expand=False` 는 "포함된" 요소만 (Maya 의 To Contained) → bmesh 로 "닿는" 요소 변환을 직접 구현. 모드 전환이 선택을 다시
  flush 하므로 먼저 읽고 → 모드 전환 → 선택 적용 순서.
- `keymap/mapping.py`: ConvertSelectionTo Vertices/Edges/Faces, Grow/Shrink(+Loop)PolygonSelectionRegion, PolyExtrude, BevelPolygon = KIT,
  ConvertSelectionToUVs = NO, SelectAll/SelectNone/EnterEditModePress 비고. `docs/keymap_mapping.md` 재생성: 구현 65 → 74, 미검토 298 → 292.
- 테스트: `tests/test_step18_mesh_keys.py` 7개, `tests/gui/gui_step18_mesh_keys.py` 14개; `tools/dogfood_session.py` Ctrl+E 체크를 "즉시 압출 모달" 기준으로.

## 검증

- `python tests/run.py` → `218 passed, 0 failed, 18 file(s)` (가림·충돌·매핑 행 검사 포함).
- `python tests/gui/run.py` → `147 passed, 0 failed, 13 file(s)`: 면 하나 → Shift+> 5개 → Shift+< 1개, Ctrl+F9 정점 4개, Ctrl+F11 닿는 면 5개,
  Ctrl+E 즉시 압출 모달 + 클릭 확정 후 면 6→10, Ctrl+B 즉시 베벨 모달 + 확정 후 면 증가, D 홀드 중 커서 툴·커서 피벗, LMB 로 피벗 배치,
  놓으면 원래 툴 + 피벗 유지, D 탭 → Median Point, Alt+D → 오브젝트 모드·선택 없음.
- `python tools/dogfood.py` → 45 중 42 (41→42): Shift+> PASS, Ctrl+E PASS. 남은 실패 3 = Ctrl+D 이름 (step 19), `.` (step 20), `=`. 콘솔 오류 0줄.

## 남은 것

- 사용자 컴포넌트 피벗은 선택이 바뀌어도 남음 (Maya 는 pin 하지 않으면 리셋) — D 탭으로 지움. 피벗 방향(orientation) 편집 없음.
  Insert(피벗 모드 토글)는 편집 모드에 없음.
- 커브·서피스 편집 모드의 같은 키들(D, Ctrl+Shift+A 등)은 IC 그대로.
- Ctrl+Shift+> / < 는 루프 방향이 아니라 선택 순서 기준 근사.
- Maya 압출은 매니퓰레이터(이동·회전·스케일 핸들)를 띄움; 여기서는 법선 방향 이동 모달 하나.
