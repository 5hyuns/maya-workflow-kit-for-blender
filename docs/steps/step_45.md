# Step 45 — Maya 그리드: 유한 12 칸 그리드·축선·X 스냅 일치

backlog 5 (`docs/PLAN.md` 「Maya 동일화 계획」, step 43 테마 다음). 근거: `research/maya/screens/01_layout_empty.png`,
`research/maya/colors.json` `metrics.grid` {size 12, spacing 5, divisions 5} 와 `viewport.displayColor` grid / gridAxis / gridHighlight
(모두 index 2 = #404040), `research/maya/interaction.md:183` (initialGUI.mel:188-226: spacing 5, divisions 5, size 12, 축 강조),
`research/maya/concepts.md:143`, step_40.md blindspot 4·8, PLAN 「재점검 3차」 10 (step 25 에서 "5 cm 주 그리드선 불가" 로 남긴 것).

## 실측 (Maya 2022 팩토리 샷 01)

- 뷰 영역 (440–1190, 340–720) 의 픽셀이 **딱 두 색**: 배경 #5c5c5c 266154 개, 선 #404040 18846 개 → 안티에일리어싱 없는 계단선.
- 4× 확대: 보조선 1 px, 5 칸마다 주선 2 px, 원점을 지나는 축선 2 px — 모두 같은 #404040 (축은 색이 아니라 굵기로 강조).
- 크기: 원점에서 ±12 단위 (spacing 5 = "Grid lines every 5", divisions 5 → 보조선 1 단위). 주선 = 5 의 배수 (±5, ±10), 가장자리 ±12 는
  보조선.
- 4 분할 (`16_four_view.png`): **top 패널에만 그리드**, front -Z / side -X 패널은 그리드 없음 — Maya 그리드는 바닥 (XZ) 평면에만 있고
  옆에서 보면 한 줄로 겹쳐 안 보인다. (처음 계획의 "정사영 뷰마다 그 평면에 그리드" 는 이 샷을 보고 고침.)

## 계획 (delegated)

1. **자체 그리드** `src/maya_kit/ui/maya_grid.py`:
   - bpy 없는 수식: `segments(size, spacing, divisions)` → (minor, major, axis) 선분 목록 (Maya 단위, 평면 좌표 u/v),
     `plane_points(segs, plane, unit)` → Blender 3D 점, `project(matrix, point, width, height)` (= `location_3d_to_region_2d`).
     평면: 바닥 = Blender XY (Maya XZ, Y-up → Z-up); 바닥을 옆에서 보는 정사영 front/side 뷰는 그리지 않음 (Maya 와 같음).
   - 그리기: SpaceView3D `POST_VIEW` 핸들러 1 개. 셰이더 `POLYLINE_UNIFORM_COLOR` (`lineSmooth` 끔 = Maya 계단선), 선 굵기 1 / 2 / 2,
     색 = 테마 `view_3d.grid` (Maya 테마에서 #404040; 테마 없이도 그 뷰의 그리드 색), 깊이 검사 LESS_EQUAL (물체가 가림). 배치는
     (단위, 평면) 마다 한 번 만들어 둔다. 단위 = `units.maya_unit()` (Maya 길이 1 = 표시 단위 1, 결정 8) — `units.grid_scale` 로 맞춘
     Blender 의 가장 촘촘한 원근 그리드 단계와 같은 값이므로 X 홀드 GRID 스냅 (Blender 단계 1 / 10 단위) 이 항상 그리드선 위.
   - 그리는 시간: 핸들러 안에서 `time.perf_counter` 로 재서 최근 120 번 평균을 `frame_ms()` 로 (검증에 기록).
2. **뷰별 상태** (delegated): SpaceView3D 는 ID 가 아니라 Python 속성을 못 붙인다. 4.x 에서 쓰이지 않는 `overlay.grid_lines`
   (UI 에도 없음, `$S\startup\bl_ui\space_view3d.py:6994-6999` 는 show_floor / show_ortho_grid 만) 를 표시로 쓴다:
   Maya 그리드 = `grid_lines == 0` 이고 `show_floor`·`show_ortho_grid` 둘 다 꺼짐. 파일에 저장되고 4 분할 뷰 전체가 같은 공간을 쓴다.
   `set_grid(space, on)`: 켜기 = Blender 바닥·정사영 그리드·X/Y 축선 끔 + grid_lines 0, 끄기 = grid_lines 16 (Blender 기본).
   Show > Grid (패널 메뉴) 와 Display > Grid (메뉴 바) = `maya_kit.toggle_grid`: 그리드가 보이면 (Maya 든 Blender 든) 모두 끄고,
   안 보이면 Maya 그리드를 켠다. Blender 바닥을 다시 켠 뷰는 Blender 그리드 (사용자가 고른 것) — 자체 그리드는 그리지 않는다.
3. **템플릿** (`tools/make_startup.py` `maya_views`): 모든 3D 뷰 Maya 그리드 켬 (show_floor / show_ortho_grid / axis 끔, grid_lines 0),
   grid_scale 0.01 은 그대로 (스냅 단계). 재생성.
4. **검증**:
   - 헤드리스 `test_step45_grid.py`: 선 개수·위치 (축 1 + 주선 4 + 보조선 20 / 방향, 끝 ±12), 평면 변환, 투영 수식 = Blender
     `location_3d_to_region_2d` (±1 px, 원근·정사영 행렬), 상태 켜기/끄기, 템플릿 뷰가 켜져 있음, 핸들러 해제.
   - `look_compare`: 샷 01 에서 투영한 그리드선 지점의 렌더 픽셀 ΔE00 < 5 (`grid.md`), 그리드 네 모서리 = 투영 계산 ±1 px 안에 그리드 색.
   - `gui_step25_grid_snap` 통과 (Blender 바닥을 꺼도 GRID 스냅이 같은 단계인지) + 스냅된 값이 그리드선 위.
   - 프레임 시간 기록 (GUI, `frame_ms`).
5. 다음 단계 고려: 46 (뷰 가구) 은 Blender 오버레이를 숨기는 같은 템플릿 코드를 쓴다; 47 (선택 와이어) 은 같은 POST_VIEW 배치 방식을
   재사용할 수 있게 셰이더·깊이 상태 처리를 함수로 둔다.

## 한 것

- `src/maya_kit/ui/maya_grid.py` (새): 수식 `segments` / `plane_points` / `plane_for_view` / `project` / `corners`, 상태 `is_on` / `visible` /
  `set_grid` / `toggle`, `maya_kit.toggle_grid`, POST_VIEW 그리기 (POLYLINE_UNIFORM_COLOR, lineSmooth 끔, 1 / 2 / 2 px, 테마 그리드 색,
  깊이 검사, (평면, 단위) 별 배치 캐시), `frame_ms()`. `ui/__init__.py` 에 등록.
- 바닥을 옆에서 보는 정사영 front/side 뷰는 그리지 않음 (위 실측: Maya 4 분할 샷).
- Show > Grid (`ui/panel_menus.py` `GRID` set 행, Apply Current to All 에 grid_lines / show_ortho_grid 추가), Display > Grid
  (`ui/menu_map.py`) = `maya_kit.toggle_grid`.
- `tools/make_startup.py` `maya_views`: 모든 3D 뷰 show_floor / show_ortho_grid 끔 + grid_lines 0 → startup.blend 재생성.
- `tools/look_shots.py` `record_grid` (샷 01 의 그리드 투영 점·모서리·그리기 시간), `tools/look_compare.py` `grid.md`.
- 테스트: `tests/test_step45_grid.py` (6), `gui_step25_grid_snap.py` (+2: Maya 그리드 켜짐 + 스냅 값이 그리드선, 그리기 시간),
  `gui_step7_top_ui.py` (Display > Grid = toggle_grid).
- `docs/PLAN.md` 재점검 3차 10 의 "5 cm 주 그리드선 불가" 를 해결로 고침, `docs/manual_checks.md` step 45.

## 검증

- 헤드리스 `python tests/run.py`: **362/362** (새 6: 선 개수·위치 (축 1·주선 4·보조선 20 / 방향, 끝 ±12), 평면·뷰 평면, 모서리 투영 =
  `location_3d_to_region_2d` ±1 px (원근·정사영 행렬), 상태 토글, 템플릿 뷰 모두 Maya 그리드 + grid_scale 0.01, disable 시 핸들러 해제).
- GUI `python tests/gui/run.py`: **283/283**, `--ui-scale 0.8`: **283/283**. `gui_step25`: 템플릿 X 스냅 9 cm = 그리드선, Maya Units 9 cm,
  팩토리 3 m (Blender 바닥을 꺼도 GRID 스냅 단계는 그대로).
- `python tools/look_compare.py` → `grid.md`: 그리드선 위 렌더 픽셀 보조 160 / 주 32 / 축 8 점 모두 ΔE00 < 5 (중앙값 0.7, kit #424242 vs
  Maya #404040), 네 모서리 모두 투영 ±1 px 안에 그리드 색 + 4 px 밖은 배경 (ΔE 0.0) = 12 단위에서 끝남. density 3/3, viewport 8/10,
  큐브 3/3 (변화 없음).
- 프레임 시간: 그리드 그리기 평균 **0.22 ms** (gui_step25) / **0.27 ms** (look_shots 01), GUI 1600×900.
- `python tools/dogfood.py`: **47/47**, 콘솔 오류 0.
- 스크린샷 직접 확인: `compare/01_layout_empty.png` (유한 정사각 그리드, 5 칸마다 굵은 선, 회색 축선, 계단선),
  `compare/16_four_view.png` (top 만 그리드, front/side 없음 — Maya 와 같음).

## 남은 것

- 템플릿 01 뷰는 템플릿 자신의 카메라라서 그리드가 Maya 샷보다 작게 보인다 (Maya 샷 영역이 더 넓고 kit 뷰 영역이 좁음) — 레이아웃 단계 48.
- X 스냅 단계는 Blender 의 그리드 단계 (원근: 줌에 따라 1 / 10 단위, 정사영에서 크게 확대하면 1 단위보다 잘게) — Maya 는 그리드선만.
  그리드선 위에는 늘 맞지만 정사영 확대 시 더 잘게 붙을 수 있음 (manual_checks).
- 이미 저장된 사용자 파일 (Blender 바닥) 은 그대로; 메뉴 Show > Grid 를 두 번 누르면 Maya 그리드.
- Maya 의 그리드 옵션 (크기·간격 변경, real-world 모드 100/5/500) 은 없음 — 고정 12/5/5.
