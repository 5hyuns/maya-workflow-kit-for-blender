# Step 17 — Maya 프레이밍 여백 (F/A) + 핫박스 잘림

재점검 1차 backlog 3: dogfood `tmp/dogfood/shots/03` (F 후 1 BU 큐브가 35 mm persp 뷰를 넘침, view_distance 1.07),
shots/07 (핫박스 행이 오른쪽 사이드바 밑으로 잘림).

## 계획

근거: research/maya/interaction.md:191-196 — F = 선택(자식 제외) 프레이밍, Shift+F 모든 패널, Ctrl+Shift+F 자식 포함 모든 패널,
A 탭 = 전체, Shift+A 모든 패널, fit factor 0.95 (PREF:576). Blender `view3d.view_selected` 는 경계 구를 영역 **가로**에만 맞추고
(Region Overlap 사이드바 밑까지 영역으로 침) 세로가 짧은 뷰에서 넘친다.

1. **계산 (`operators/framing.py`, bpy 없음 → 헤드리스 테스트)**: 대상 점들의 축 정렬 경계 상자 8점을 현재 뷰 회전 그대로
   투영해, 투영 상자가 "보이는 영역" 의 0.95 에 꼭 맞는 거리를 이분 탐색(로그 스케일 60회)하고, 투영 상자 중심이 보이는 영역 중심에
   오도록 뷰 평면에서 팬 → 거리 재탐색 (원근은 팬이 크기를 조금 바꾸므로 4회 반복).
   - 4.5 에 `RegionView3D.update()` 가 없어 거리를 바꿔도 `perspective_matrix` 가 다음 그리기까지 갱신되지 않음(실측) →
     view 행렬은 위치·회전·거리로 직접 만들고(`cam = T(loc)·R·T(0,0,d)`, view = cam⁻¹), window 행렬은 현재 값
     (원근: 거리와 무관, 직교: x/y 가 거리에 반비례) 을 쓴다.
   - 점 하나(로케이터·라이트)만 있으면 반 크기 0.5 BU 상자 (delegated).
2. **보이는 영역**: 같은 영역의 UI(사이드바)·TOOLS(툴바) 리전이 WINDOW 리전과 겹치면 그 폭을 뺀다 (Region Overlap 이 꺼져 있으면
   겹치지 않으니 그대로). 남는 폭이 1/4 미만이면 전체 사용.
3. **대상 (delegated)**: 오브젝트 모드 F = 뷰에 보이는 선택 객체의 평가된 bound_box (메시·커브 등) 또는 위치(빈 객체·라이트·카메라);
   선택이 없으면 전체 (Maya F 와 같음). Ctrl+Shift+F = 선택 + 보이는 자손 전부. A / Shift+A = 보이는 모든 객체 (어느 모드든).
   편집 모드(메시) F = 선택 정점 (없으면 편집 중인 객체 전체). 다른 편집·포즈·페인트·스컬프트 모드와 카메라 뷰는 Blender
   `view_selected` / `view_all` 그대로. 애니메이션(smooth view) 없이 바로 이동 — Maya 기본도 즉시 [K].
4. **바인딩**: 3D View F = `maya_kit.frame(selected)` (IC `view_selected` 대체), Ctrl+Shift+F = `maya_kit.frame_all_views(children)`,
   Shift+F / Shift+A = `frame_all_views` 가 같은 계산을 쓰고, A 탭(`taphold.SelectAllBinding.tap`)도 같은 계산. 메뉴
   Display > Frame Selection with Children 에 children 추가.
5. **핫박스**: `engine.HotboxLayout(bounds=...)` — 각 행을 커서 중심에 두되 보이는 영역 안으로 옆으로 밀고, 보이는 폭보다 넓은 행은
   왼쪽 끝부터. 가장자리 존 이름(E/W)도 보이는 영역 기준. 세로는 행이 항상 가운데 상자 바로 위라 그대로.

검증: 헤드리스 (fit: 원근/직교, 사이드바 제외 영역에서 0.95·중심, 점 하나; visible_rect; 핫박스 bounds; 키 바인딩·매핑),
GUI (MayaKit 아닌 팩토리 레이아웃 + 사이드바 열고 F: 큐브 8점 투영이 보이는 영역 안, 짧은 축 비율 ≈0.95; A; Ctrl+Shift+F 자식 포함;
Shift+F 쿼드; 핫박스 행이 사이드바 왼쪽), dogfood 스크린샷 03·07 직접 확인, `python tests/gui/run.py` 전체.

## 한 것

- `operators/framing.py` (새, bpy 없음): `view_matrix`, `window_matrix_at`, `project`, `box_corners`, `fit` (거리 이분 탐색 + 보이는 영역
  중심으로 팬, 4회), `visible_rect` (겹치는 리전 제외: 넓고 낮은 리전 = 헤더류는 위/아래, 나머지는 중심이 있는 쪽 옆).
  처음엔 좌우만 잘랐는데 GUI 스크린샷에서 (a) 투명 헤더·툴 헤더 밑으로 큐브 윗부분이 들어가고 (b) 쿼드 오른쪽 뷰에서 사이드바가
  뷰 중심보다 왼쪽에서 시작해 제외되지 않는 것을 보고 규칙을 바꿈.
- `operators/view.py`: `frame_points` (오브젝트 모드 bound_box/위치, 편집 메시 선택 정점, 자식 포함, 선택 없으면 전체, 그 밖의 모드 None),
  `visible_bounds`, `frame_region` (카메라 뷰·기타 모드는 Blender 연산자로), 새 `maya_kit.frame(selected, children)`,
  `maya_kit.frame_all_views` 가 같은 계산 + `children`. 두 연산자 속성은 `SKIP_SAVE` — Blender 가 마지막 값을 기억해 Ctrl+Shift+F 의
  children=True 가 다음 Shift+F 에 남던 것을 GUI 테스트가 잡음 (쿼드 3개 뷰가 0.22 로 작게).
- `operators/taphold.py`: A 탭이 `frame_region(selected=False)`.
- 키: 3D View F = `maya_kit.frame` (IC `view_selected` 제거), Ctrl+Shift+F = `frame_all_views(children)`. 매핑: FrameSelectedWithoutChildren
  IC→KIT, FrameSelectedInAllViews STEP→KIT (`docs/keymap_mapping.md` 재생성). 메뉴 Display > Frame Selection with Children 에 children.
- 핫박스 (`marking/engine.py` `HotboxLayout(bounds=…)`, `marking/modal.py`, `marking/draw.py`): 행을 보이는 영역 안으로 옆으로 밀고,
  보이는 폭보다 긴 행은 줄바꿈 (순서 유지). 존 이름 E/W 는 가운데 상자를 피하고 자리가 없으면 안 그림.
- 테스트: `tests/test_step17_framing.py` 8개, `tests/gui/gui_step17_framing.py` 6개, `tests/test_step4_view.py` F 바인딩 기대값 갱신.

## 검증

- `python tests/run.py` → `211 passed, 0 failed, 17 file(s)`.
- `python tests/gui/run.py` → `133 passed, 0 failed, 12 file(s)`: 사이드바 연 팩토리 뷰에서 F 후 큐브 경계 상자 투영이 보이는 영역 안,
  짧은 축 비율 0.950; Ctrl+Shift+F (큐브 + 12 BU 떨어진 자식) 0.950; A 0.950; 쿼드 Shift+F 4개 뷰 모두 0.95; 핫박스 행 오른쪽 끝 ≤ 사이드바 왼쪽.
  (비율은 다음 그리기 뒤 Blender 의 `location_3d_to_region_2d` 로 잼 — 직접 만든 투영과 독립.)
- 스크린샷 직접 확인: `step17_f.png` (헤더·사이드바 밑으로 안 들어감), `step17_quad.png`, `step17_hotbox.png`, dogfood `03_move_tool.png`
  (F 거리 1.07 → 1.5, 큐브 전체가 보임), `07_hotbox.png` (모든 행 보임, Generate 줄바꿈).
- `python tools/dogfood.py` → 45 중 41 (변화 없음, F 체크 PASS 유지), 콘솔 오류 0줄.

## 남은 것

- 0.95 는 Maya 값이지만 꽤 꽉 찬다 — Maya 2022 와 나란히 비교 (manual_checks).
- 카메라 뷰(Numpad 0)에서 F/A 는 Blender 동작 (Maya 는 카메라를 옮김). 커브·아마추어 편집, 포즈, 페인트 모드도 Blender 연산자.
- 프레이밍이 애니메이션 없이 즉시 (Blender smooth view 미사용). 먼 거리로 프레이밍해도 clip_end 는 그대로.
- 핫박스 세로: 커서가 위쪽 가장자리 근처면 행이 화면 밖으로 (행은 항상 가운데 상자 바로 위).
