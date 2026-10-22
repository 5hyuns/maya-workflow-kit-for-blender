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
