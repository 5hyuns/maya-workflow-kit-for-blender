# Step 137 — 레인 RENDER (#67, step_133_work.md X1)

## 한 것

- 새 `src/allset/operators/render_persp.py`: `allset.render_current_frame` / `allset.render_sequence`.
  Maya 는 활성 패널의 카메라로 렌더하고, 새 장면의 renderable 카메라는 `perspShape` (mayapy, `tmp/audit133_work/out/m04_scene.json:33-34`).
  - 뷰가 카메라를 통해 보면 그 카메라 (뷰의 local camera, 아니면 `scene.camera`).
  - 아니면 `persp` 카메라 (오브젝트 `persp` / 데이터 `perspShape`, ID 속성 `allset_persp`) 를 처음 렌더 때 만들고 계속 씀.
    뷰의 `view_location / view_rotation / view_distance` 로 행렬을 만들고 (`framing.view_matrix`; `rv3d.view_matrix` 는 뷰가 그려질 때만
    갱신돼 스크립트로 바꾼 직후엔 옛 값 — `-b` 에서 측정), 렌즈 = 뷰 렌즈 × 36 / 72 (`key_batch.VIEW_SENSOR`, step 78 / 81: 템플릿 70 → 35 mm),
    ortho 뷰는 ORTHO + `ortho_scale = distance × 72 / lens`, 클립 = `units.clip` (Maya 0.1 / 10000 cm). `scene.camera` 로 둔 뒤 Blender 렌더
    (INVOKE → 렌더 창 = Maya Render View; Keep Image 그대로 동작).
  - 뷰 = 연산자가 실행된 3D View (Tool Box 열 제외), 아니면 메인 창의 가장 큰 3D View.
- 연결: `ui/menu_map.py` Render/Render Current Frame · Redo Previous Render · Render Sequence, Playback/Render Current Frame (핫박스도 같은
  MAP), `ui/shelf_map.py` RenderSequence · BatchRender, Status Line 렌더 버튼 (`ui/status_line.py`), Render View 헤더 Render 버튼
  (`ui/render_view.py`). 마킹 메뉴 · `editor_menu_map.py` 에는 렌더 실행 항목이 없음 (확인).
- 기존 테스트 기대값 갱신: `test_step67_render`, `test_step7_top_ui`, `test_step51_shelf_menus`, `gui_manual_sweep` (M67-4 헤더).

### 결정 (delegated)

- **persp 는 어떤 컬렉션에도 링크하지 않는다**: 킷 Outliner 가 이미 Maya 기본 `persp` 행을 그리고 있어 (`ui/outliner_sets.default_entries`,
  step 99) 그 행이 이 카메라를 대신한다. 링크하지 않으면 Blender Outliner 에 두 번째 행이 없고, 뷰포트에서 선택 · 렌더 · 내보내기 대상이 아니다.
  `scene.camera` 는 사용자로 세지 않아 `use_fake_user` 로 지킨다 (Maya 의 시작 카메라처럼 모든 장면에 있는 노드). 측정 (`tmp/probe137/p1.py`):
  링크 안 된 `scene.camera` 로 렌더됨, 위치를 바꾸면 따라감, 저장 / 다시 열기 후에도 남음. orphan purge 도 남김 (헤드리스 테스트).
- 사용자 뷰에서 렌더하면 장면에 다른 카메라가 있어도 persp 로 렌더하고 `scene.camera` = persp 로 남긴다 (Maya: 활성 패널의 카메라).
- 연산자는 UNDO 없음 (`REGISTER` 만): 렌더는 Maya 에서도 되돌리기 단계가 아니다. 되돌리기로 persp 가 사라지면 다음 렌더 때 다시 만든다.
- Render Sequence / Batch Render 셸프도 같은 카메라 규칙 (Maya 의 Render Sequence 는 Render Settings 의 renderable 카메라 — 새 장면 = persp).

## 검증

- 헤드리스 `python tests/run.py -k step137`: 6/6 (`tests/test_step137_render.py`: 필요할 때 생성 · 뷰 행렬 / 렌즈 35 mm / 클립 일치 · 재사용 ·
  컬렉션 없음 + fake user + purge 생존 · ortho · 카메라 뷰 / local camera 우선 · Workbench 64×36 실제 렌더에 큐브가 보이고 뷰를 돌리면 배경만 ·
  매핑).
- `python tests/run.py -k step137,step67,step105,step99,step54,step101,enable_disable,step130,step7_top,step51`: 92 passed, 0 failed (12 파일).
- GUI `python tests/gui/run.py -k step137_render --shots`: 6/6 — Maya 레이아웃 새 장면 (카메라 없음) → Cube → `allset.menu_item("Render/Render
  Current Frame")` → Render Result 를 보여 주는 Render View 창, scene.camera = persp (35 mm, 컬렉션 없음), Render Result 480×270 에 큐브 픽셀
  183 개, 중심 0.50 / 0.50 (뷰와 같은 자리), 다시 렌더해도 persp 하나, 렌더 창 닫힘. 샷 확인: `gui_step137_render_view.png` (Render · Keep
  Image · Remove Image 헤더, 가운데 작은 큐브), `gui_step137_main.png` (Outliner 의 persp 행 하나, pCube1).
- GUI `-k step67,step105`: 16 passed, 0 failed.

## 남은 것

- 렌더된 큐브가 어둡다: 새 장면에 조명이 없고 Maya 의 기본 조명 (Render Settings 의 Default Light) 에 해당하는 것이 없음 — 이 레인 범위 밖.
- 렌더 해상도와 뷰 비율이 다르면 Blender 카메라 sensor fit AUTO 규칙으로 맞춤 (Maya 의 Fill / film gate 는 재현하지 않음).
- persp 는 킷 Outliner 의 그려진 행에서 선택되지 않는다 (step 99 그대로: 행을 눌러도 오브젝트 선택 없음).
