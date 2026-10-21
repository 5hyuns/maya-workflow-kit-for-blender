# Step 134 — 레인 GRID: Maya 그리드 대비 · 3D 커서 (#59)

## 계획

근거: `step_133_ui.md` #3 (그리드 대비 표준편차 3.9 vs Maya 9.4, 선 #555555 vs Maya #404040, 원점의 3D 커서),
`research/maya/screens/compare_audit133_s100/grid.md` (모든 선 ΔE00 7.1, 모서리 0/4), `step_45.md` 「실측」.

### 원인

`ui/maya_grid.py` 는 선 색을 `preferences.themes[0].view_3d.grid` 에서 읽는다. step 45 에는 킷 Maya 테마가 이 값을
#404040 으로 두었지만 step 130 (결정 13) 이후 킷은 테마를 쓰지 않으므로 Blender 기본 테마 그리드 색 (#545454 → 화면 #555555)
이 #5c5c5c 배경 위에 그려져 거의 보이지 않는다. 3D 커서는 템플릿 뷰의 `overlay.show_cursor` 가 Blender 기본 (켬) 이라 보인다.

### 측정 (Maya 쪽, 이번 레인에서 다시 잼)

- `01_layout_empty.png`, `03_cube_unselected.png`, `audit7/pairs/a01_first_screen.png` 의 Maya 반쪽: 그리드 영역에 있는 색은
  배경 (#5c5c5c, a01 은 검은 GL 버퍼) 과 **#404040 하나뿐** — 축선도 같은 #404040 이고 굵기 (2 px) 로만 진해 보인다
  (`tmp/grid134/maya_crop_centre.png`, 4× 확대). step_133_ui 의 「검은 굵은 축선」은 2 px 선이 진해 보인 것이지 다른 색이 아니다.

### 할 일

1. **선 색 = 킷 고정색 #404040** (`maya_grid.LINE_RGB`, Maya displayColor grid / gridAxis / gridHighlight = index 2;
   결정 13 이 허용하는 킷 고정 색). 테마를 읽지 않는다 → 테마와 무관 (헤드리스 테스트: 테마 grid 색을 바꿔도 `line_colour()` 같음).
   굵기 1 / 2 / 2 px (보조 / 5 칸 주선 / 축) 는 step 45 실측 그대로.
2. **Blender 자체 그리드**: Maya 레이아웃 뷰는 이미 `show_floor` / `show_ortho_grid` / `show_axis_x/y` 끔 (`make_startup.maya_views`)
   — 밑에 깔리는 Blender 그리드 없음. 바꿀 것 없음 (GUI 테스트가 Blender 그리드 색 픽셀이 없음을 확인).
3. **3D 커서 숨김**: `tools/make_startup.py` `maya_views()` 에 `overlay.show_cursor = False` → `startup.blend` 재생성 (GUI).
   `first_start.new_maya_scene` (이 파일을 읽음) 과 `switch.enter_layout` (이 파일의 워크스페이스를 붙임) 둘 다 이 값을 받는다.
   기존 파일에 남은 옛 레이아웃은 건드리지 않는다 (사용자 파일 데이터).
4. **D / Insert 컴포넌트 피벗** (`operators/hold.ComponentPivotEdit`, step 18 / 77): 피벗 = 3D 커서라서 커서가 안 보이면 피벗 편집이
   보이지 않는다. `start()` 에서 커서를 숨긴 3D 뷰 (`show_cursor` False) 만 켜고 그 공간 포인터를 기억, `finish()` 에서 그것들만
   다시 끈다 (원래 켜져 있던 뷰는 안 건드림). 공간은 매번 `bpy.data.screens` 를 새로 훑어 포인터로 찾는다 (닫힌 창의 낡은 참조를
   만지지 않음, step 129 #36). 피벗을 놓은 뒤 (custom, pivot CURSOR) 의 표시는 Maya 처럼 조작기가 한다 — 커서는 다시 숨김.
5. 테스트: 헤드리스 `tests/test_step134_grid.py` (색 상수 · 테마 무관, 커서 숨김 / 보임 복원 로직),
   GUI `tests/gui/gui_step134_grid.py` (첫 화면 스크린샷에서 그리드 선 색 ΔE00, 그리드 안 표준편차를 같은 방식으로 잰 Maya 값과 비교,
   축선이 보조선보다 진함, 원점에 커서 색 픽셀 없음; Insert / D 중 커서 보임, 끝나면 다시 숨김). 1.25 와 `--ui-scale 0.8`.
6. 나란히 그림: `tmp/grid134/` (Maya 첫 화면 | 킷 첫 화면, 그리드 확대).

### 결정 (delegated)

- 축선 색은 Maya 실측대로 #404040 (굵기로만 강조), 검정으로 하지 않는다 — 실측 픽셀에 더 어두운 색이 없다.
- 선 굵기는 UI 배율에 따라 바꾸지 않는다 (Maya GL 선은 장치 픽셀; 1.25 에서도 1 / 2 px).
- 커서는 컴포넌트 피벗 편집 중에만 보인다 (오브젝트 D = 원점 편집은 커서를 쓰지 않으므로 그대로 숨김).

## 한 일

- `ui/maya_grid.py`: 선 색 = `LINE_RGB` #404040 (`line_colour()`), 테마를 읽지 않음. 굵기 · 선 배치는 step 45 그대로.
- `tools/make_startup.py` `maya_views()`: `overlay.show_cursor = False` → `startup.blend` 재생성 (GUI). 새 Maya 장면과
  `switch.enter_layout` 이 붙이는 워크스페이스 모두 커서 없음.
- `operators/hold.py`: `show_cursors()` / `hide_cursors()` — `ComponentPivotEdit.start` 가 숨겨진 뷰의 커서만 켜고 `finish` 가
  그 뷰만 다시 끈다 (D 홀드 · Insert 토글 공통).
- 테스트: `tests/test_step134_grid.py` (5), `tests/gui/gui_step134_grid.py` (12 검사).

## 검증

측정 (GUI 스크린샷, 그리드 사각형을 85 % 로 줄인 안쪽의 회색 표준편차 · 가장 흔한 선 색; Maya 는 같은 함수로
`research/maya/screens/01_layout_empty.png`):

| | 표준편차 | 선 색 | ΔE00 (vs #404040) | 축선 / 보조선 어두운 폭 | 원점 커서 빨강 px |
|---|---|---|---|---|---|
| Maya 2022 | 9.15 | #404040 | 0 | 2 px / 1 px (step 45) | 0 |
| 킷 이전 (1.25) | 3.91 | #555555 (배경과 7 차) | 7.1 (audit 133) | 측정 안 됨 (선이 문턱 위) | 38 |
| 킷 이후 1.25 | 9.63 | #424242 | 0.66 | 2.5 / 1.0 | 0 |
| 킷 이후 1.0 (`--ui-scale 0.8`) | 9.64 | #424242 | 0.66 | 2.5 / 1.0 | 0 |

- Insert (컴포넌트 피벗 편집) 중 커서 그려짐 (빨강 48 px), 끝나면 `show_cursor` 다시 False.
- `ALLSET_SANDBOX=grid134 python tests/run.py -k step134,step45,step25,enable_disable,step130`: 34/34.
- `ALLSET_SANDBOX=grid134 python tests/gui/run.py -k step134_grid,step45,step77,step99,step5_layout`: 41/41 (1.25),
  `--ui-scale 0.8` 41/41 (gui_step45 파일은 없음).
- 그림: `tmp/grid134/side_maya_vs_kit100.png`, `side_maya_vs_kit125.png`, `side_kit125_before_vs_after.png`,
  `crop_maya_vs_kit100_x4.png`, `maya_crop_centre.png` — 직접 봄: 그리드가 Maya 처럼 또렷하고 원점 축이 굵게, 커서 없음.

## 남은 것

- look_compare `grid.md` 수치 (모서리 4/4 기대) 는 LOOK 레인 (#75) 병합 뒤 메인이 다시 잰다.
- 킷 첫 화면의 그리드가 Maya 보다 조금 작게 보인다 (뷰포트 너비 차이; 이 레인 범위 밖).
- 사용자가 예전 레이아웃으로 저장한 파일의 뷰는 커서가 그대로 보인다 (파일 데이터는 건드리지 않음, delegated).
