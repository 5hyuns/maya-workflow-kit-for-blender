# Step 137 — Animation and render basics (#66 #67 #71)

## 계획

backlog 4 (`step_133_work.md` A1, X1, X2, X5). Maya 값은 step 133 감사의 mayapy 측정 그대로 쓴다
(`tmp/audit133_work/out/m07_mat.json`, `m04_scene.json`; 이 단계에서 `research/maya/re/render_defaults_137.md` 로 옮겨 적는다):
blinn1 color 0.5 · diffuse 0.8 · incandescence 0 · specularRollOff 0.7 · eccentricity 0.3 · specularColor 0.5 · reflectivity 0.5;
phong1 같은 색 · cosinePower 20; point / spot / directional light decay 0 (No Decay), intensity 1; defaultResolution 960 × 540;
renderable camera = perspShape.

### 결정 (delegated)

- **Graph Editor 단위 (#66)**: Blender 의 Graph Editor 는 F-curve 원래 값을 그리고 회전만 도로 바꾼다 (C `ANIM_unit_mapping_get_factor`).
  킷 템플릿은 결정 1 · 8 (m 유지 + cm 표시) 이라 이동 곡선이 0.05 로 보인다. 결정 1 을 뒤집어 템플릿을 Maya Units (scale_length 0.01) 로
  바꾸는 것은 물리 · 임포트 · 기존 장면 · 테스트 전부에 번지므로 하지 않는다 (그 길은 이미 add-on 설정 「Maya Units」 로 있다). 대신 킷이
  Graph Editor 의 값 눈금 숫자를 표시 단위로 다시 그린다: 보이는 곡선이 모두 길이 속성일 때 Blender 의 값 숫자 칸을 덮고 같은 자리에
  `값 / maya_unit()` 로 적는다 (cm 는 ×100 이라 눈금 간격이 그대로 맞는다). 길이 · 회전 · 배율 곡선이 섞여 보일 때는 Blender 숫자 그대로
  (한 축에 두 단위를 맞출 수 없음, 남은 것에 기록). 선택 키 값은 이미 표시 단위 (Stats 칸 `allset_key_value`, 사이드바 Active Keyframe).
- **Render Current Frame (#67)**: Maya 는 활성 패널의 카메라 (새 장면 = persp) 로 렌더한다. 킷: 카메라를 통해 보는 뷰면 그 카메라, 아니면
  `persp` 카메라 (ID 속성 `allset_persp`, 없으면 그때 만듦) 를 메인 3D View 의 시점 · 렌즈 (뷰포트 렌즈는 72 mm 센서 기준, step 78) 에 맞춰
  `scene.camera` 로 두고 렌더 → Render View (Blender 렌더 창). Render Sequence 도 같은 카메라. 킷 Outliner 의 기본 persp 행과 겹치지 않게.
- **기본값 (#71)**: Blinn / Phong = Maya 측정값 (`operators/material.MATERIALS`, Lambert 의 step 100 규칙을 따름), 새 점 / 스포트 / 면 조명의
  Decay Rate = No Decay (Blender 조명은 늘 역제곱 — Cycles 의 Light Falloff 노드 Constant 로 가능한지 재고, 안 되면 AE Decay Rate 알림),
  Render Settings 960 × 540 (`tools/make_startup.py` 생성기 → 다시 생성; 새 Maya 장면 경로도 확인).

### 레인 (병렬, worktree, 포그라운드)

| 레인 | 이슈 | 파일 |
|---|---|---|
| GRAPH | #66 | 새 `ui/graph_units.py` (+ `ui/__init__` 등록 한 줄), `tests/test_step137_graph_units.py`, `tests/gui/gui_step137_graph_units.py` |
| RENDER | #67 | 새 `operators/render_persp.py` (+ 등록), `ui/menu_map.py` Render 항목, 필요하면 `ui/outliner_sets.py`, `tests/test_step137_render.py`, `tests/gui/gui_step137_render.py` |
| DEFAULTS | #71 | `operators/material.py`, `operators/create.py` (조명), `ui/ae_layout.py` / `notices.py` (Decay), `tools/make_startup.py` + `startup.blend`, `research/maya/re/render_defaults_137.md`, `tests/test_step137_defaults.py` |

등록 목록 (`ui/__init__.py`, `operators/__init__.py`) 은 레인마다 한 줄씩이라 메인이 병합 때 맞춘다. 메인: 병합, 헤드리스 전체, 관련 GUI,
GUI 전체 한 번, 커밋.

## 한 것

레인 3 개를 worktree 에서 포그라운드로 동시에 (step 136 교훈). 레인 문서: `step_137_graph.md`, `step_137_render.md`, `step_137_defaults.md`.

- **GRAPH** (#66): 계획의 「값 숫자 칸 덮기」 는 안 된다 — Blender 4.5 는 값 숫자를 영역 overlay 에 그리고 overlay 는 Python POST_PIXEL 뒤
  (빨간 사각형으로 측정, space_graph.cc:352-358 → view2d_draw.cc:340-400). 그 뒤에 그려지는 것은 `WindowManager.draw_cursor_add` (마우스가 있는
  영역만) 뿐이라: POST_PIXEL 이 Blender 와 같은 규칙으로 눈금을 계산하고 숫자 칸의 overlay 전 픽셀을 저장, draw cursor 가 그 픽셀을 다시 붙이고
  `값 / maya_unit()` 를 Blender 글꼴 · 자리에 쓴다 (`ui/graph_units.py`, delegated). 보이는 곡선이 모두 길이 속성일 때만, 정규화 끔.
  마우스가 곡선 영역에 있을 때 0–5, 다른 영역에 있으면 Blender 의 0.00–0.05 (Blender 한계, 남은 것).
- **RENDER** (#67): `allset.render_current_frame` / `allset.render_sequence` (`operators/render_persp.py`): 뷰가 보는 카메라, 아니면 킷 `persp`
  카메라 (그때 만들고 다시 씀, 컬렉션 없음 + fake user, 킷 Outliner 의 그린 persp 행이 대신; delegated) 를 뷰 위치 · 렌즈 (×36/72) · Maya
  클립으로 두고 렌더 → Render View 창. 메인 메뉴 · 핫박스 · 셸프 · Status Line · Render View 머리줄의 Render 항목을 모두 여기로.
- **DEFAULTS** (#71): mayapy 측정 (`research/maya/re/render_defaults_137.md`): lambert 계열 Color 0.5 · Incandescence 검정 · Specular Color 0.5,
  Blinn Roll Off 0.7, Eccentricity 0.3 / Cosine Power 20 = 거칠기 환산 속성 (AE 에 Maya 숫자), 조명 Intensity / Decay Rate 속성 (기본 No Decay,
  Cycles Light Falloff 로 정확, EEVEE 는 10 단위 거리에서만 맞춤, 공식은 레인 문서), 템플릿 Render Settings 960 × 540 (`make_startup.py` 재생성).
- **메인**: 병합 (`operators/__init__.py` 등록 줄 충돌 손으로), 측정 명세를 `research/maya/re/` 로 복사, 손 확인 항목, CLAUDE.md 메모.

## 검증

- 헤드리스 전체 (병합 뒤): **1096 passed, 0 failed (137 files)**. 레인별: GRAPH `-k step137,step104,step70,enable_disable` 30/30, RENDER 관련 92/92,
  DEFAULTS 관련 110/110 (+ Blender 5.2.2 / 5.0.1 `-k step137,enable_disable` 각 14/14).
- GUI 전체 (커밋 전 한 번; 세션이 중간에 끊겨 두 번에 나눠 이어 돌림, 같은 빌드): 앞 16 파일 **447 passed, 0 failed**, 나머지 105 파일
  **954 passed, 1 failed** — 실패 1 = `gui_step54_units_notices` 의 점 조명 세기 기대값 (예전 10 W × unit², 새 No Decay 규칙 4π² × 10² × unit²
  = 0.394784 W 가 측정값과 정확히 같음) → 기대값 고친 뒤 그 파일만 **4 passed, 0 failed**.
- 레인 GUI: GRAPH 24/24 (배율 1.25 · 1.0 각각: 눈금 숫자 0–5, Blender 격자선과 0.6 px 이내, 섞인 곡선은 Blender 숫자), RENDER 6/6 (새 장면 → 큐브 →
  Render Current Frame → Render View, 480 × 270 결과에 큐브 183 픽셀 가운데), DEFAULTS 29/29.
- 그림 직접 확인: `gui_step137_graph_cm_numbers.png` (0–5 가 격자선 위), `gui_step137_render_view.png` (persp 로 렌더한 큐브),
  `gui_step137_blinn_ae.png` (Color 0.5 회색, Incandescence 검정, Eccentricity 0.300, Specular Roll Off 0.700).

## 남은 것

- Graph Editor: 마우스가 곡선 영역 밖이면 Blender 의 m 숫자 (draw cursor 는 마우스가 있는 영역만); 길이 · 회전 · 배율 곡선이 섞이면 Blender 숫자.
  정확한 길은 add-on 설정 「Maya Units」 (1 BU = 1 cm).
- 렌더: 조명 없는 장면이 어둡다 — Maya Software 의 기본 조명 (default light) 이 없음 (다음 후보). 렌더 크기와 뷰 비율이 다르면 Blender AUTO
  sensor fit (Maya film gate 아님). 그린 persp Outliner 행을 눌러도 카메라 오브젝트가 선택되지 않음 (step 99 그대로).
- 기본값: Channel Box 의 조명 행은 아직 Blender Power (Intensity 아님), EEVEE 에서 No Decay / Linear 는 10 단위 거리에서만 맞음, Maya 단위
  설정을 바꿔도 기존 조명은 다시 계산 안 함, volume / ambient light 없음, diffuse 0.8 을 빼서 렌더가 Maya 보다 1.25 배 밝음.
