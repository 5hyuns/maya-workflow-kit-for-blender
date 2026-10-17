# Step 46 — 뷰 가구: ViewCube·축 삼각·persp 라벨·Blender 오버레이 숨김

backlog 6 (`docs/PLAN.md` 「Maya 동일화 계획」). 근거: `research/maya/screens/01_layout_empty.png`, `02_cube_selected_move.png`,
`16_four_view.png`, `compare/01·16` (kit: Blender 내비 기즈모 + 확대/이동 버튼, "User Perspective (1) Collection" 글자),
step_40.md blindspot 7.

## 실측 (Maya 2022 팩토리 샷, 1600×900, 뷰 GL 영역 `look_data.MAYA_VIEW_RECT` = (315, 172, 1001, 612))

| 요소 | 샷 01 / 02 (단일 뷰) | 샷 16 (4 분할) |
|---|---|---|
| ViewCube | [1225, 199, 65, 65] = 뷰 오른쪽에서 26 px, 위에서 27 px | 한 패널 (활성, top) 에만: [730, 205, 48, 49] |
| 카메라 라벨 | "persp" [792, 768, 28, 7] (x-height), 글자 #e3e3e3, 바닥에서 9 px 위, 가로 중심 806 (뷰 중심 815.5 의 −9.5) | 패널마다 "top -Y" / "persp" / "front -Z" / "side -X", 패널 중심의 약 −10 |
| 축 삼각 | [328, 737, 27, 25]: 원점 ≈ (341, 758) = 왼쪽에서 26, 바닥에서 26; 선 약 13 px, 소문자 x/y/z 글자, 빨강/초록/파랑 | 패널마다 같은 자리 |

- ViewCube 색: 앞면 #adadad, 오른면 #9b9b9b, 모서리 #666666, 배경 #5c5c5c → 흰 면 (≈ 254) 을 **불투명도 0.5** 로 그린 값
  (0.5·254 + 0.5·92 = 173). 면 글자 FRONT / RIGHT / TOP 은 면을 따라 기울어 있다. 4 분할에서는 작아짐 (65 → 48).
- Maya persp 의 방향 (kit `MAYA_EYE_BLENDER` (28, −28, 21)) 에서 보이는 면 = FRONT (Blender −Y), RIGHT (+X), TOP (+Z).

## 계획 (delegated)

1. **Blender 가구 숨김** (템플릿 `tools/make_startup.py` `maya_views`): `show_gizmo_navigate` False (내비 기즈모 + 확대/이동 버튼),
   `overlay.show_text` False ("User Perspective (1) Collection").
2. **뷰별 상태**: Maya 가구는 "Blender 것을 대신한다" — ViewCube·축 삼각 = 그 뷰의 `show_gizmo_navigate` 가 꺼져 있을 때, 카메라 라벨 =
   `overlay.show_text` 가 꺼져 있을 때 (+ `show_overlays`, ViewCube 는 `show_gizmo` 도). 애드온 환경설정 「Maya View Furniture」 (기본 켬) 로
   전부 끌 수 있다. 팩토리 뷰는 Blender 가구 그대로. (SpaceView3D 에 Python 속성을 못 붙임 — step 45 와 같은 이유.)
3. **ViewCube** = Python 기즈모 그룹 `MAYAKIT_GGT_view_cube` (VIEW_3D / WINDOW, PERSISTENT) + 기즈모 `MAYAKIT_GT_view_cube`:
   - 수식 (bpy 없음, `ui/view_furniture.py`): 단위 정육면체 6 면을 뷰 회전의 역으로 돌려 정사영 → 화면 다각형, 앞을 향한 면만 (뒤→앞 순),
     점-다각형 포함 판정 (`hit_face`), 면 → `view3d.view_axis` type (TOP +Z, BOTTOM −Z, FRONT −Y, BACK +Y, RIGHT +X, LEFT −X).
   - 그리기: 기즈모 `draw` 안에서 픽셀 정사영 행렬로 2D; 면 = 흰색 × 면 방향 음영, 모서리 어두운 회색, 면 글자 = blf (면 가로 방향으로
     회전, 크기 = 면 크기; 많이 기운 면은 생략 — Maya 의 기울임은 blf 로 못 함). 평소 불투명도 0.5, 마우스가 올라가면 1.0 + 가리킨 면 하늘색.
   - 크기: 단일 뷰 65 px (× 실효 배율), 작은 뷰는 Maya 두 측정에 맞춘 `65·(min(w, h) / 612)^0.42` (4 분할 48). 위치: 보이는 영역
     (`view.visible_bounds`, 사이드바 제외) 오른쪽 위에서 26 / 27 px.
   - 클릭: `test_select` 가 가리킨 면을 고르고 `target_set_operator("view3d.view_axis")` 의 type 을 그 면으로 → 기즈모 클릭이 실행.
   - 4 분할: Maya 처럼 한 패널에만 — 마우스가 마지막으로 있었던 패널 (`test_select` 에서 기억, 처음은 사용자 원근 패널).
4. **카메라 라벨 + 축 삼각** = SpaceView3D `POST_PIXEL` 핸들러 1 개 (모든 WINDOW 영역 = 4 분할 패널마다):
   - 라벨: 카메라 뷰 = 카메라 오브젝트 이름; 정사영 측면 뷰 = Maya 이름 + 보는 방향 (Blender 축, Channel Box 와 같은 축):
     top −Z, bottom +Z, front +Y, back −Y, side −X (Blender right), left +X; 그 밖 (사용자 원근·정사영) = "persp".
     Maya 처럼 바닥에서 9 px 위, 가로 중심 −9 px, 11 px × 배율, #e3e3e3.
   - 축 삼각: Blender 축 (Z 위 — kit 은 Y-up 불가, 결정 5; 라벨이 Channel Box 의 X/Y/Z 와 같아야 함) 을 뷰 회전으로 투영, 원점 = 왼쪽·아래
     26 px, 길이 13 px, 1 px 선 + 소문자 x/y/z, 테마 축 색 (Maya 매니퓰레이터와 같은 빨강/초록/파랑, step 43). 전역 `mini_axis_type`
     은 건드리지 않는다 (뷰별이 아니고 Blender 글자·모양).
5. 메뉴: Display > Heads Up Display > View Cube 가 있으면 그 뷰의 show_gizmo_navigate 반전 (= ViewCube 켜기/끄기).
6. **검증**: 헤드리스 (투영·포함 판정·면 → view_axis, 라벨 이름, 크기 공식, 템플릿 플래그, 등록 해제), GUI 새 `gui_step46_view_furniture.py`
   (ViewCube 위 면 클릭 → Top 뷰, 4 분할 라벨 4 개 = top/persp/side/front, 스크린샷), look_compare `furniture.md` (kit ViewCube·라벨·삼각 사각형의
   뷰 모서리 기준 위치 vs Maya ±10 px, Blender 텍스트 오버레이가 있던 왼쪽 위에 글자 픽셀 없음).
7. 다음 단계: 47 (선택 와이어) 은 POST_VIEW, 48 (레이아웃) 은 뷰 크기를 바꾸므로 가구는 모두 영역 모서리 기준으로 둔다.

## 한 것

- `src/maya_kit/ui/view_furniture.py` (새): 수식 (`faces_2d`, `point_in_poly`, `hit_face`, `label_for`, `cube_size`, `layout`, `triad`),
  ViewCube 기즈모 `MAYAKIT_GT_view_cube` / 그룹 `MAYAKIT_GGT_view_cube` (면 6 개 = 파트 6 개, 파트마다 `target_set_operator("view3d.view_axis")`,
  4 분할은 마우스가 마지막으로 있던 패널에만), POST_PIXEL 라벨·축 삼각. `ui/__init__.py` 등록.
- 애드온 환경설정 `maya_viewcube` / `maya_camera_names` / `maya_view_axis` (기본 켬, UI Elements 상자). Display > Heads Up Display 의
  Camera Names / View Axis / View Cube (새 항목) = 이 환경설정 토글 (`menu_map._kit_pref`; 전에는 Blender show_text / 내비 기즈모 토글).
- 템플릿 `tools/make_startup.py`: `show_gizmo_navigate` False, `overlay.show_text` False → 재생성.
- 측정 도구: `look_shots` 가 `view3d.visible` (보이는 뷰 사각형) 기록, `look_data` `FURNITURE` / `furniture_box` / `corner_offsets` /
  `triad_origin`, `look_compare` `furniture.md`.
- 테스트: `tests/test_step46_view_furniture.py` (7), `tests/gui/gui_step46_view_furniture.py` (6).
- 실측 중 고침: `view.visible_bounds` 는 이미 영역 기준 좌표 (처음에 영역 원점을 한 번 더 빼서 큐브가 엉뚱한 곳에); `blf.draw` 뒤에는
  블렌딩이 꺼진다 → 첫 면 글자 뒤 면들이 불투명하게 (238) 그려졌음 → 면마다 `blend_set('ALPHA')`.

## 검증

- 헤드리스 `python tests/run.py`: **369/369** (새 7: Maya persp 에서 FRONT/RIGHT/TOP 이 보이고 상자 65 px·FRONT 왼쪽, 면 중심 → 그 면 /
  밖 → None, top 뷰는 TOP 만, 면 이름 = view_axis type, 라벨, 크기 (65 / 4 분할 48 ±1.5 / 배율), Maya 뷰에서의 위치 (26 / 27, −9 / 9, 26 / 26),
  축 삼각 방향, 템플릿 플래그, HUD 메뉴·등록 해제).
- GUI `python tests/gui/run.py`: **289/289**, `--ui-scale 0.8`: **289/289** (`gui_step46` 6: 템플릿 플래그, ViewCube TOP 면 클릭 → top 정사영
  (보는 방향 (0, 0, −1)), 4 분할 라벨 = front +Y / top −Z / side −X / persp).
- `python tools/look_compare.py` → `furniture.md` **3/3** ±10 px: ViewCube 오른쪽 30 / 위 27 (Maya 26 / 27), 라벨 중심 −8 / 바닥 6 (Maya −9 / 9),
  축 삼각 원점 26 / 27 (Maya 26 / 27); Blender 텍스트 오버레이 자리 밝은 픽셀 **0**. ViewCube 면 색 183 / 178 (Maya 173 / 155).
  grid ok·4/4, density 3/3, viewport 8/10, 큐브 3/3 (변화 없음).
- `python tools/dogfood.py`: **47/47**, 콘솔 오류 0.
- 스크린샷 직접 확인: `tmp/shots46/gui_step46_single.png` (오른쪽 위 ViewCube FRONT/RIGHT/TOP, 왼쪽 아래 z/y/x, 아래 persp), `gui_step46_quad.png`
  (4 패널 라벨, ViewCube 는 persp 패널 하나), `compare/02_cube_selected_move.png`.

## 남은 것

- ViewCube 모서리·꼭짓점 클릭, 큐브 드래그 텀블, 홈 아이콘·회전 화살표 (Maya ViewCube 의 나머지) 없음.
- 면 글자는 blf 회전만 (Maya 는 면을 따라 기울임); 많이 기운 면은 글자 생략.
- kit ViewCube 57 px (Maya 65): kit 의 보이는 뷰가 Maya 보다 작아서 작은 패널 공식이 줄임 — 레이아웃 단계 48 에서 뷰 크기가 맞으면 같아짐.
- 4 분할 라벨의 축 글자가 Maya 와 다름 (kit = Blender 축: top −Z, front +Y) — 결정 5 (Y-up 불가) 에 따름, manual_checks.
- 오른쪽 면 음영 (Maya 155 vs kit 178): Maya 는 광원 방향으로 면마다 다르게 칠함.
