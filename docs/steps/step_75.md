# Step 75 — Status Line 입력 줄 + Construction History

## 계획 (delegated)

재점검 3·4차 남은 것. Maya Status Line 오른쪽 Input Line (research/maya/ui_layout.md:208-211).
동작은 Maya 2022 `scripts/startup/statusLine.mel:1928-2245`, `numericalInputChangeCommand.mel`, `renameSelectionList.mel` 를 읽고 다시 구현한다 (복사 안 함).

| Maya | 동작 |
|---|---|
| 모드 버튼 (LMB 메뉴) | Absolute transform / Relative transform / Rename / Select by name. optionVar `quickFieldMode`, 처음엔 Abs (statusLine.mel:3206) |
| Abs / Rel | X / Y / Z 칸 세 개 (40 px). Enter 로 현재 툴 (Move / Rotate / Scale, 다른 툴이면 Move) 을 적용한다. 빈 칸 = 그 축 그대로 (numericalInputChangeCommand.mel:25-45, :250-291). 적용 뒤 칸을 비운다 |
| Abs Move | `move -rotatePivotRelative`: 피벗의 월드 위치를 그 값으로 |
| Rel | `move / rotate / scale -r`: 더하기 (Scale 은 곱하기) |
| Rename | 칸 (166 px) 에 리드 노드 이름을 보여 준다 (statusLineUpdateInputField). Enter = 선택한 것 모두 이름 바꾸기. 공백 → `_`. 이름 규칙 `[a-zA-Z_][a-zA-Z0-9_]*` 가 아니면 오류. 여럿이면 숫자를 붙인다 (renameSelectionList.mel:62-160) |
| Select by name | `*` `?` 와일드카드로 바꿔 선택한다. 맞는 것이 없으면 오류이고 글자는 남는다. 맞으면 결과를 보여 주고 칸을 비운다 (quickWildcardSelect) |
| Construction History (:3017-3032) | Blender 에는 히스토리가 없다 → 회색 버튼 + 안내 (`notices.PANEL_NOTICES`) |

### kit 설계

- `ui/input_line.py`.
  - `Scene.maya_kit_input` (PropertyGroup) 의 `mode` enum 과 `x / y / z / text` StringProperty 를 둔다.
    - 문자열은 get / set 함수로 만든다. get = 보여 줄 글자 (Rename 은 리드 이름, 나머지는 빈 칸). set = Enter 때 동작한다.
    - Scene 프로퍼티라 UI 편집이 undo 단계를 남긴다 (step 38).
  - 숫자는 `cb_entry` 를 재사용한다 (`_number` / `from_display`): `5` = 표시 단위 (MayaKit cm), `5 m`, `2*3` 도 된다. 회전은 도.
  - 축 X / Y / Z 는 Blender 축이다 (Channel Box 와 같은 글자, step 46).
- 적용 대상:
  - 오브젝트 모드, 선택 오브젝트:
    - Move abs = `matrix_world` 이동값의 그 축 (delta 유지).
    - Move rel = 월드 이동.
    - Rotate = `rotation_euler` 축 값 (abs 대입 / rel 더하기).
    - Scale = `scale` 축 (abs 대입 / rel 곱하기).
  - 메쉬 편집 모드, 선택 정점:
    - Move abs = 선택 중심의 그 월드 축을 그 값으로 옮긴다. rel = 월드 이동.
    - Rotate / Scale = 선택 중심 기준 월드 축 회전 / 배율. abs 도 rel 처럼 한다 [delegated: 컴포넌트에는 채널 값이 없음].
- Rename:
  - 리드 (활성) 오브젝트가 먼저 그 이름을 받는다. 이름이 이미 있으면 `name1`, `name2` … 가장 작은 빈 번호를 붙인다. 나머지는 이름순으로 다음 번호.
  - 데이터가 단독 사용자면 `nameShape(번호)` 로 함께 바꾼다 (Maya 처럼 셰이프가 따라감, naming.py 규칙).
- Select by name: `fnmatch.fnmatchcase` 로 뷰 레이어의 선택 가능한 오브젝트를 고른다. 선택을 바꾸고, 활성 = 마지막.
- 피드백: 결과와 오류는 Help Line (`notices.show`) 에 띄운다.
- Status Line 그룹 순서 (Maya): … Symmetry, **History**, Render, **Input**, Editors.

### 검증

- 헤드리스: 각 모드 setter.
  - abs `1 2 3` → cm 템플릿 단위로 위치, rel, 빈 칸 축 유지, Rotate / Scale 툴 (툴 id 교체).
  - 편집 모드 Move.
  - rename (단일 / 여럿 / 이미 있는 이름 / 잘못된 이름 / 셰이프 따라감).
  - select `pCube*` / `?` / 없음.
  - undo 가 되는 Scene 프로퍼티인지.
- GUI: Status Line 칸에 타이핑 (CLAUDE.md GUI typing) → abs 이동, Rename, Select. 스크린샷.
- 전체 테스트, dogfood, manual_checks.

## 한 것

- `ui/input_line.py`:
  - `Scene.maya_kit_input` (mode + x / y / z / text, get / set 문자열).
  - `transform` (오브젝트: Move abs = 월드 위치 축 / rel 더하기, Rotate 축, Scale 축 곱하기; 편집 메쉬: 선택 중심 기준 Move / Rotate / Scale).
  - `rename` (리드 먼저, 빈 번호, `<name>Shape` 따라감, Maya 이름 규칙).
  - `select_by_name` (fnmatch 와일드카드, 활성 = 마지막, 없으면 글자 남김).
  - 결과·오류는 Help Line 에 띄운다.
- Status Line (`ui/status_line.py`):
  - 그룹 HISTORY (회색 Construction History + `PANEL_NOTICES` 안내) 와 INPUT (모드 드롭다운 + X / Y / Z 칸 또는 텍스트 칸) 을 Maya 순서로 넣었다.
  - 다른 레이아웃의 3D View 툴 헤더에 그려질 때 (`compact`) 는 입력 줄을 에디터 토글 뒤에 둔다 [delegated]. 그 헤더는 이미 넘쳐서, 앞에 두면 토글이 화면 밖으로 밀린다.
- `gui_step63_mtk`: Status Line 의 MTK 아이콘을 고정 x (1190) 로 누르던 것을 툴 헤더를 훑어 찾게 바꿨다 (`ui.copy_python_command_button`). 그룹이 늘어 위치가 바뀌어 실패했었다.

## 검증

- 헤드리스 `python tests/run.py`: **604/604** (70 파일). 새 `test_step75_input_line.py` 8:
  - abs cm 단위 / `5 m` / 칸 비움, 빈 축 유지 + delta 유지, rel + Rotate / Scale 툴, 편집 모드 Move.
  - 이름 규칙 / 계획, 다중 rename + 셰이프 + 잘못된 이름, 와일드카드 선택 + 없음, History 안내 + 그룹 순서.
- GUI `python tests/gui/run.py`: **516/516** (58 파일). 새 `gui_step75_input_line.py` 6 (MayaKit 레이아웃, 실제 타이핑):
  - X 칸 찾기 → `10` Enter → x = 10 cm.
  - Rename 칸에 pCube1 → `crate` → crate / crateShape.
  - Select `pSph*` → pSphere1.
- `python tools/dogfood.py`: **47/47**, 콘솔 0.
- 스크린샷 직접 확인: `gui_step75_abs_typing.png` (X: 10 입력 중, Y: Z: 칸), `gui_step75_rename_field.png` (pCube1 표시, 큐브가 x 10 으로 이동).

## 남은 것

- Maya 입력 줄의 다른 편집기 대상 (Graph Editor 키, UV 에디터 UV 의 `localContextTransform`), 피벗 편집 모드 (D) 중 입력, 대칭 반영 (`-rfl`) 은 없다.
- Maya History 그룹의 input / output 풀다운은 없다.
- 컴포넌트 회전 / 배율 abs 는 rel 로 처리한다.
- 손 확인: `docs/manual_checks.md` 「Step 75」.
