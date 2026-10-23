# Step 140 레인 EDIT — 키 명령 · Edit · 메시 옵션 창 (#33 #35)

계획 / 공통 설계: `docs/steps/step_140.md`. 필드 · 라벨 · 공장 기본값 = `research/maya/re/option_boxes_140.md` (Maya 2022 GUI
캡처), 값이 하는 일 = mayapy 측정 `research/maya/re/option_boxes_140_edit.md` (스크립트 `research/scripts/maya_options140_edit/
measure.py`, 원자료 `measure.json`).

## 한 일

창 15 개 (`src/allset/operators/option_windows_edit.py`, `allset.opt_<key>`):

| key | 제목 / 버튼 | 메뉴 경로 |
|---|---|---|
| delete_keys | Delete Keys Options / Delete Keys | Key/Delete Keys, Edit/Keys/Delete Keys |
| cut_keys | Cut Keys Options / Cut Keys | Key/Cut Keys, Edit/Keys/Cut Keys |
| copy_keys | Copy Keys Options / Copy Keys | Key/Copy Keys, Edit/Keys/Copy Keys |
| paste_keys | Paste Keys Options / Paste Keys | Key/Paste Keys, Edit/Keys/Paste Keys |
| scale_keys | Scale Keys Options / Scale Keys | Key/Scale Keys, Edit/Keys/Scale Keys (지금까지 회색 = dead 2) |
| snap_keys | Snap Keys Options / Snap Keys | Key/Snap Keys, Edit/Keys/Snap Keys |
| parent / unparent / ungroup | Parent / Unparent / Ungroup Options | Edit/Parent, Edit/Unparent, Edit/Ungroup |
| duplicate_special_maya | Duplicate Special Options | Edit/Duplicate Special (step 103 창 + Smart transform) |
| connect | Connect Components Options / Connect | Edit Mesh/Connect |
| connect_tool | Connect Tool / Connect | Mesh Tools/Connect (Slide 0.5, Segments 1) |
| circularize | Polygon Circularize Options / Circularize | Edit Mesh/Circularize |
| make_hole | Make Hole Tool / Make Hole | Mesh Tools/Make Hole (Merge mode None) |
| insert_edge_loop | Insert Edge Loop Tool / Insert Edge Loop | Mesh Tools/Insert Edge Loop (Blender Loop Cut 도구 시작 + 값) |

- `operators/time_keys.py`: `copy_scope` / `paste_scope` (Time range Start · Start/End · Current · Clipboard, Time / Value
  offset, Copies, Paste method Insert / Replace / Merge, Replace region Time range / Entire curve) / `delete_scope`
  (Method Keys / Segments, Adjustment Collapse, Connect; Cut = 복사 후 삭제) / `scale_scope` (Scale/Pivot · Start/End,
  Only scale specified keys) / `snap_scope` (Times / Values / Both, 배수). 모두 `KeyScope` (Objects / Hierarchy / Channels /
  Driven / Shapes / Time range) 로. mayapy 숫자와 같은지 테스트로 확인 (§1–§5).
- Time Slider 복사 / 붙여넣기 (`copy_keys` / `paste_keys`) 도 같은 함수 (반 프레임 여유 유지). `allset.time_keys` 에
  `time_range` (SLIDER 기본 / ALL) — Key · Edit > Keys 의 Cut / Copy / Snap 은 Maya 공장 옵션 (Time range All) 으로 실행.
- `parenting.py` / `group.py`: `preserve_position` (끄면 `parent -relative`: 로컬 값 유지), Ungroup `under` Parent / World,
  Preserve 끄면 그룹 로컬 변환을 자식 로컬에 합침 (mayapy §6).
- `poly_maya.py`: Circularize `normal_offset` / `radial_offset` / `twist` / `evenly_distribute` / `divisions` (§7),
  Connect `insert_with_edge_flow` / `adjust_edge_flow` (§8) 와 도구용 `segments` / `slide`, Make Hole `merge_mode` 7 가지 (§9).
- `ui/menu_map.py`: Key/Scale Keys · Edit/Keys/Scale Keys = `allset.opt_scale_keys`; Cut / Copy / Snap 에 `time_range: 'ALL'`.
  `ui/notices.py`: "Key/Scale Keys" 공지와 "Edit/Keys" 범주 삭제 (그 아래 회색 항목이 없어짐, test_step101).

## delegated

- Key/Scale Keys 평범한 클릭 = 창 열기: Maya 공장값 (배율 1) 이면 아무 일도 안 일어나서. 저장된 값이 있으면 그 값으로 실행 (run_action 규칙).
- Key/Delete Keys 매핑은 `anim.keyframe_clear_v3d` 그대로 — `tests/test_step56_time_keys.py:205` 가 그 값을 단정하고 이 레인은 그
  파일을 못 고친다. 공장값 (All, Selected, Shapes) 과 결과가 같다. 저장된 값이 있으면 킷 범위 함수로 실행.
- Paste Replace + Current / Start: Maya 는 범위가 필요하다고 거절 → 킷은 붙여넣는 길이 (copies × (span + offset)) 를 범위로 씀.
  Insert 의 밀기 길이도 같은 값 (offset 있는 Insert 는 측정 안 함).
- Edge flow: Maya 공식 미상. Hermite (접선 0.7 × (다음 − 이전)) 가 8 x 8 구 측정과 1e-4 안에서 맞음 — 다른 메시에선 근사.
- Connect 도구 Slide: 면을 따라 같은 쪽 끝을 기준으로 (`_orient`), 여러 면이 이어진 링에서 Maya 와 방향이 다를 수 있음.
- Insert Edge Loop: Multiple edge loops → Loop Cut Number of Cuts, Equal distance → Edge Slide Even, Insert with edge flow →
  Loop Cut Smoothness = Adjust Edge Flow (Blender 의 가장 가까운 것).
- Duplicate Special Smart transform: 켜면 킷 Duplicate with Transform (Shift+D) 을 Number of copies 번.
- 도구 창 제목은 Maya 도구 이름 ("Make Hole Tool", "Insert Edge Loop Tool", "Connect Tool") — test_step103 의 `endswith("Options")`
  검사는 메인이 병합 때 완화해야 함.

## 검증

- `python tests/run.py -k step140_edit,step110,step139,step56,step70`: 87 passed, 0 failed.
- `-k step103,step101,enable_disable,step140_option_count`: 28 passed, 1 failed — test_step103 제목 검사 (위 delegated).
- `python tools/menu_count.py --options`: window 29 → 49, generic 65 → 52, redo 148 → 144, tool 14 → 13, dead 231 → 229
  (RIG 레인 창 미포함 — 병합 뒤 다시).
- 전체 헤드리스: 아래 (마지막 실행).

## 남은 것

- Maya 에만 있는 필드 (`missing`, 회색): Control points, Cut/Copy Method Range, Paste Clipboard adjustment Scale / Fit (측정 결과
  규칙 미상) · Selected keys override · Connect, Parent Add instance / Unparent Remove instance, Duplicate input graph /
  connections / instance leaf / unique names, Circularize Relax Interior / Alignment / Smoothing Angle / Supporting Edges,
  Connect tool Pinch, Insert Edge Loop Use Equal Multiplier / Auto complete / Fix Quads / Smoothing angle.
- Graph Editor 안에서 Key 명령은 선택된 키가 아니라 Channel Box 노드 기준 (Maya 는 Graph Editor 선택 키).
- GUI 샷 (메인 몫).
