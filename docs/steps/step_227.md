# Step 227 — Blend shape in-betweens, combinations and corrective shapes (Issue #137)

기준: 결정 문서 (비공개 bmk-strategy) ATTACH_PLAN L15 / L16 (b), `research/maya/re/maya2026_deform.md` §L15 §L16,
이번 mayapy 측정 `research/maya/re/shapes_227.json` (스크립트 `research/scripts/maya_shapes227/measure.py`, Maya 2026).
L5 (SDK 가 셰이프 가중치를 구동) 는 step 226 에서 됨 (blendShape = driven 노드).

## 계획

### 이번 측정 (mayapy 2026)
- **인비트윈** (`inbetween_one` / `inbetween_two`, w −0.4 … 1.4 37 개): 중단점 0 < p₁ < … < 1 (인비트윈 가중치, 인덱스
  5000 + 1000·w) 사이 **조각 선형**, 범위 밖은 **끝 구간을 그대로 연장** (w −0.4 → 첫 구간, 1.4 → 마지막 구간).
- **조합** (`combination_two` 8×8 격자 × 3 방법, `combination_three`): multiplication (기본) = 곱 (음수 포함),
  lowest = min, smooth = **조화 평균** n·Πa / Σ(n−1 개 곱) (2ab/(a+b)), 입력 하나라도 ≤ 0 → 0. 속성은 combinationMethod 하나.
- **Pose Interpolator** (`pose_one` 26 회전, `pose_two`, `pose_one_gaussian`): 기본 Linear, 포즈 하나 = 중립과 포즈 사이
  **스윙 각에 선형** (rz −45 → 0.5, −90 → 1, −5 → 0.0556), **트위스트 (드라이버 축 X 회전) 무시** ((90,0,−45) → 0.5).
  포즈 밖 (−105 → 1.0185, +45 → 0.0556) 과 포즈 2 개의 상호작용 (−45 → 0.4757) 은 Maya RBF 고유 [U].

### 설계 (delegated, ATTACH_PLAN (b) — 셰이프 키 + 단순 식 드라이버, Python 자동 실행 불필요)
- **A 인비트윈 + 조합** (`operators/blend_shapes_227.py`, `ui/shape_editor.py`, `ui/editor_menu_map.py`, `ui/notices.py`
  Shape Editor 항목):
  - 사용자 손잡이 = 타깃 셰이프 키 `smile` 의 value (Maya 가중치) 그대로 — CB / Shape Editor / SDK / 키 / FBX 가 지금처럼 동작.
  - 인비트윈 = 숨은 키 `smile_ib<w×1000>` (인비트윈 모양의 델타), 보정 키 `smile_ibfix` (타깃 델타 복사본):
    값 드라이버 = 조각 선형 기저 함수 (끝 구간 연장) 의 단순 식, 보정 = coef_target(w) − w. 합이 Maya 와 정확히 같음.
    슬라이더 범위 −10 … 10 (음수 계수).
  - 조합 = 새 키, 값 드라이버 `a*b` / `min(a, b)` / 조화 평균 (≤ 0 → 0), 방법은 Key ID 속성 (Shape Editor 에서 바꿈).
  - Shape Editor: 인비트윈을 타깃 아래 행으로, 조합 표시, Create 메뉴 Add In-Between Target (가중치 입력) / Add Combination
    Target 동작, 숨은 키는 목록에서 감춤.
- **B Pose Space Deformation** (`operators/pose_space_227.py`, 창 UI, `ui/marked_window.py` 종류 하나, `ui/menu_map.py`
  Deform > Pose Space Deformation 두 항목 + Windows > Animation Editors > Pose Editor):
  - Create Pose Interpolator = 조인트 선택 → `<joint>_poseInterpolator` 노드 (Empty, ID 속성) + 중립 포즈.
  - 포즈 = 드라이버 본 끝 (tail) 을 따르는 숨은 Empty 와, 부모 본에 붙은 "포즈 때의 끝 위치" 숨은 Empty; 거리 d (LOC_DIFF)
    → 스윙 각 θ = 2·asin(d / 2r) (트위스트 무시), 교정 키 값 = max(0, 1 − θ / θ₀) 단순 식.
  - Pose Editor = 킷 창 (포즈 목록, Add Pose, Add Shape (교정 셰이프 키 만들고 Edit), Go to Pose, Delete).
- 공용 `operators/__init__.py` 는 메인이 스텁 2 개를 먼저 등록.

### 검증
- 헤드리스: 인비트윈 정점 = mayapy 37 표본 × 2 경우 (1e-4), 조합 3 방법 × 64 + 3 입력 4 경우 (1e-4), PSD pose_one 의
  스윙 범위 안 표본 + 트위스트 표본 (1e-4) / 밖·포즈 2 개는 차이 기록, `driver.is_simple_expression` 전부 True,
  FBX Export All 이 셰이프 키를 유지.
- GUI: `-k shape_editor` (Shape Editor 인비트윈 행).
