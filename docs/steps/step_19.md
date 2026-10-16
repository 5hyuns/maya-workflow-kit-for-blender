# Step 19 — Maya 이름 규칙의 복제 (Ctrl+D → pCube2)

재점검 1차 backlog 5 (`docs/steps/step_14.md` dogfood: Ctrl+D 사본 = `pCube1.001`).

## 계획

근거: research/maya/concepts.md:150-154 — 복제는 끝 숫자를 올리고(`pCube2`) shape 이름도 transform 에 맞춤; Maya Duplicate 는
하위 계층을 통째로, 제자리에 (research/maya/interaction.md:204-206).

현황: Shift+D(`duplicate_with_transform`)·Ctrl+Shift+D(`duplicate_special`)는 step 10 에서 이미 `duplicate.copy_subtree` →
`naming.apply_maya_name` 으로 Maya 이름을 붙임. 남은 것은 Ctrl+D = IC `object.duplicate_move` 뿐 (Blender 이름 `.001` + 이동 모달).

결정 (delegated): post-op 이름 바꾸기(IC 연산자 뒤에 이름만 고침) 대신 **킷 연산자 `maya_kit.duplicate`** 로 교체 — 이미 Maya 의미
(제자리, 하위 계층, 이름, 사본만 선택, Shift+D 스마트 반복용 PAIRS 기록)를 가진 `copy_subtree` 경로를 그대로 쓰므로 세 복제 명령이
한 규칙을 공유. 매핑 행 Duplicate 는 IC → KIT (step_14 B9 의 IC idname 고정은 행 갱신으로 해소). 메뉴 Edit > Duplicate 도 같은 연산자.
편집 모드 Ctrl+D 는 IC `mesh.duplicate_move` 그대로.

## 한 것

- `operators/duplicate.py`: `duplicate(context)` + `MAYAKIT_OT_duplicate` (`maya_kit.duplicate`).
- `keymap/maya_patches.py` 16: Object Mode Ctrl+D `object.duplicate_move` 제거 → `maya_kit.duplicate`.
- `keymap/mapping.py` Duplicate = KIT; `docs/keymap_mapping.md` 재생성 (구현 74 → 75, IC 일치 7 → 6). `ui/menu_map.py` Edit/Duplicate.
- 테스트: `tests/test_step19_duplicate.py` 5개 (바인딩·메뉴, 연속 3번 pCube2..4 + pCubeShape2..4 + 제자리 + 사본만 선택 + 지오메트리 복사,
  group1 복제 → group2 / pCube2 / pSphere2 + 월드 위치, Ctrl+D 후 이동 → Shift+D 가 pCube3 을 같은 간격에, Blender 이름 Cube → Cube1).

## 검증

- `python tests/run.py` → `223 passed, 0 failed, 19 file(s)`.
- `python tests/gui/run.py` → `147 passed, 0 failed, 13 file(s)`.
- `python tools/dogfood.py` → 45 중 43 (42→43): 이벤트로 누른 Ctrl+D → `['pCube1', 'pCube2']`, 제자리, 이동 모달 없음. 남은 실패 2 = `.` (step 20), `=`.
  콘솔 오류 0줄.

## 남은 것

- 복제본의 애니메이션: `Object.copy()` 는 액션을 공유 (Maya 기본 Duplicate 는 입력 연결을 복제하지 않음 [K]) — 확인 필요 (manual_checks).
- Maya 는 형제 사이에서만 이름이 유일하면 되지만 Blender 는 전역 유일 → 다른 그룹 아래라도 번호가 계속 올라감 (문서화).
- Outliner 에서의 Ctrl+D, 편집 모드 Ctrl+D(면 복제) 는 Blender 그대로.
