# Step 135 lane CB — collapsed INPUTS, fixed Channel Box / Layer Editor split (#55)

## 계획

### Maya 측정 (Maya 2022 GUI, factory prefs, 1600x900; `research/scripts/maya_cb135/`, 그림 `research/maya/screens/cb135/`)

QTest 클릭으로 Channel Box 목록 viewport 를 눌러 봤다 (`pass1/` = 첫 실행, `d*.png` = 둘째 실행).

| # | 조작 | 결과 | 그림 |
|---|---|---|---|
| M1 | polyCube 생성 | INPUTS `polyCube1` 한 줄, 접힘. SHAPES `pCube1Shape` 한 줄 | `d01_cube.png`, `pass1/c01` |
| M2 | `polyCube1` 클릭 | 그 아래 Width / Height / ... 펼침. Channel Box 부분에 세로 스크롤바, **Layer Editor 경계는 그대로** | `d02_clicked.png` |
| M3 | 다시 클릭 | 접힘 | `d07_toggled.png` (반대 방향) |
| M4 | 펼친 채 새 큐브 (lead 바뀜) | `polyCube2` 접힘 | `d03_second_cube.png` |
| M5 | `pCube1` 다시 선택 | `polyCube1` **접힘**: 펼침 상태는 lead 가 바뀌면 사라진다 | `d04_first_again.png` |
| M6 | 둘 다 선택, 새 장면 | 접힘 | `d05_both.png`, `d06_new_scene_cube.png` |
| M7 | polyExtrudeFacet | `polyExtrudeFace1` 도 접힘 | `pass1/c07_extruded_component.png`, `c07b` |
| M8 | 히스토리 8 개 (polyBevel) | 접혀도 길면 Channel Box 부분만 스크롤, LE 고정 | `pass1/c09_long_history.png`, `c10` |
| M9 | 카메라 / 스포트 라이트 | SHAPES `cameraShape1` / `spotLightShape1` 은 **펼친 채** (Film Aperture, Color R ...) | `pass1/c11_camera.png`, `c12_spot_light.png` |
| M10 | SHAPES 이름 클릭 | 이름 바꾸기 칸 (펼침 아님) | `pass1/c04_shape_clicked.png` |
| M11 | 분할 | ChannelBoxForm 299 px / LayerEditorForm 328 px (pane 633 px, `paneSize` 질의값 70 은 화면과 다름) = CB 0.48 | `_cb135.json` |

### 설계

1. **펼침 상태 = kit 쪽 파이썬 상태** (`channel_box._open`: lead 키 + 펼친 노드 키 집합). `mod.show_expanded` 는 더 이상 읽지도 쓰지도
   않는다 (사용자 데이터, Properties 의 modifier 패널 접힘과 한 값이라 Channel Box 클릭이 Properties 를 바꾸고 undo 단계까지 남겼다).
   WM / Scene 속성이 아닌 이유: Maya 에서 펼침은 UI 상태 (파일에 없음, undo 없음), lead 가 바뀌면 사라진다 (M5) — 그리기에서 lead
   변화를 보고 비워야 하는데 draw 에서 ID 속성은 쓰면 안 된다. (delegated)
   - 노드 키: modifier `mod:<name>`, 생성 노드 / kit 압출 기록 `node:<polyCube1 ...>`, 제약 `con:<pCube1_parentConstraint1>`.
   - lead 키 = 오브젝트 이름 (본은 armature + bone 이름). 다르면 집합을 비운다 (M4, M5). 파일 로드 때도 비운다.
   - 클릭 = `allset.cb_node_toggle` (UNDO 없음: Maya 의 펼침도 undo 되지 않는다). `rows_signature` 에 펼친 노드가 들어가서 text 행이 다시 만들어진다.
   - INPUTS 의 모든 노드 (생성 노드, kit 압출, modifier, 제약) 는 기본 접힘 (M1, M7). SHAPES 의 카메라 / 라이트 속성은 지금처럼 펼친 채 (M9),
     SHAPES 이름은 이름 칸 그대로 (M10).
   - 지금까지 `WindowManager.allset_creation_closed` (생성 노드 하나만 기본 펼침) 와 `ALLSET_OT_creation_node_toggle` 은 없앤다.
2. **고정 분할 + Channel Box 안 스크롤**. 한 Properties 영역 안에서는 일부만 스크롤하는 영역을 만들 수 없다. 후보:
   - (a) Properties 영역 두 개 (CB 위, LE 아래): 스크롤은 공짜지만 탭 스택 (AE / MTK 로 바꾸면 LE 영역을 닫고 다시 나눠야 함), tear-off,
     역할 플래그, `make_startup.py` 레이아웃이 모두 바뀐다. `area_close` / join 은 GUI 에서만, 위험이 크다.
   - (b) UIList: 자체 스크롤은 있지만 행 = 컬렉션 항목이라 step 129 드래그 선택 (`context.property` 의 `_sel` 버튼), 셀 팝오버를 다시 만들어야 한다.
   - (c) **kit 스크롤 창** (선택): Channel Box 의 머리 (메뉴 줄, 이름) 아래 모든 줄 (채널, SHAPES, INPUTS) 을 같은 높이 (`ROW_SCALE`) 의
     한 정렬 column 에 그리고, CB 몫 (`CB_SHARE` × 영역 높이) 에 들어가는 줄만 그린다. 넘치면 마지막 줄은 ▲ ▼ 단추, 휠은
     `allset.cb_scroll` ("Property Editor" WHEELUP/DOWN 맨 앞, Channel Box 부분 밖이거나 넘치지 않으면 PASS_THROUGH). 스크롤 위치는
     영역별 (area pointer) 파이썬 상태, lead 가 바뀌면 0. 그리는 함수는 두 번 돈다 (줄 수 세기 → 그리기). Layer Editor 는 언제나
     `1 − CB_SHARE` 자리에서 시작한다. (delegated)
   - `CB_SHARE` 0.50 은 그대로 (M11: 0.48).
3. Dock 탭 줄 (lane WIDTH 요청): 탭마다 `ui_units_x = ceil(글자 폭 / U + 1)` (11 pt × 배율), 손잡이 `글자 폭 / U + 1.5`, 왼쪽 정렬 —
   Blender 가 정렬 줄의 탭을 똑같은 폭으로 나눠 「Channel Box / Layer Editor」 가 잘리던 것. lane WIDTH 의 `toolbox.dock_need` 가 같은 식을 쓴다.

### 검증

- headless `tests/test_step135_channel_box.py`: 기본 접힘, 토글, lead 바뀌면 접힘, 다시 돌아와도 접힘, `show_expanded` 안 바뀜, text 행,
  스크롤 창 계산 (`window_lines`), 그리기 (Recorder) 에서 접힌 노드에 속성 줄 없음.
- GUI `tests/gui/gui_step135_dock.py`: 큐브 선택 → INPUTS `polyCube1` 접힘, Layer Editor Display / Anim 탭 보임, 클릭 → 펼침, 클릭 → 접힘,
  긴 히스토리에서 LE 그대로 + 휠 스크롤; 그림 1.0 / 1.25 / 1.5.
