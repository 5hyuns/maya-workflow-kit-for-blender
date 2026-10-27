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

## 한 것

레인 2 개 병렬 (A 인비트윈·조합, B Pose Space Deformation; 파일 단위로 나눔, `operators/__init__.py` 는 메인이 스텁 등록).

- **A** (`operators/blend_shapes_227.py`, `ui/shape_editor.py`, `ui/editor_menu_map.py`, `ui/notices.py` 5 개 삭제):
  Shape Editor Create > Add In-Between Target (❒ 가중치) / Add Selection as In-Between / Add Combination Target / Add Selection
  as Combination / Shapes > Set as Combination Target 동작. 인비트윈 = 숨은 키 `<target>_ib<1000w>` + `<target>_ibfix`, 값
  드라이버 = 조각 선형 기저 (끝 구간 연장) 단순 식; 타깃 키 값 = Maya 가중치 그대로. 조합 = 새 타깃 (Add Target 이름 규칙),
  방법 드롭다운 (Multiplication / Lowest / Smooth = 조화 평균). 기록 = Key ID 속성 `allset_inbetweens` / `allset_combinations`,
  depsgraph → 0 s 타이머 `sync` 가 보정 키를 타깃과 맞춤. Maya 스크립트 규칙 따름 (빈 인비트윈 = 그 가중치의 현재 모양 복사 후
  Edit, `doBlendShapeAddInBetweenTarget.mel:174-189`; 가중치 (0, 1), 중복 오류) — delegated.
- **B** (`operators/pose_space_227.py`, `ui/pose_editor.py`, `ui/marked_window.py` POSE_EDITOR, `ui/menu_map.py` 3 항목):
  Deform > Pose Space Deformation > Create Pose Interpolator (❒ twist axis) / Pose Editor, Windows > Animation Editors > Pose
  Editor (셸프 Sculpting/Pose Editor 도). 노드 = Empty `<joint>_poseInterpolator` (Outliner 에 보임, 그림 없음); 숨은 tip /
  포즈 헬퍼 (`.AllsetPoseHelpers`, 장면 밖); 가중치 = `max(0, 1 − 2·asin(min(1, d/2r))/θ₀)` (LOC_DIFF, 트위스트 무시);
  Add Shape = 포즈 이름의 교정 셰이프 키 (값 = 출력 가중치), Edit = 포즈로 가서 Armature 모디파이어 on cage 의 Edit Mode;
  Go to Pose / Delete. 중립 3 포즈 출력은 없음, 사용자 포즈만 (delegated).
- 메인: SDK Driven 목록 (`driven_key.channels`) 과 Set Blend Shape Target Weight Keys (`deformer_order.blend_shape_keys`)
  가 숨은 인비트윈 키를 뺌 (`blend_shapes_227.target_blocks`).

## 검증

- vs mayapy (`shapes_227.json`): inbetween_one 37 표본 1.0e-7, inbetween_two 37 표본 4.2e-7, combination_two 3 × 64 3.9e-7,
  combination_three 3 × 4 4.4e-7, pose_one 스윙 범위 안 + 트위스트 행 4.9e-7 (모두 1e-4 이내); 모든 드라이버
  `is_simple_expression` True (Auto Run Python Scripts 꺼진 상태에서).
- 범위 밖 PSD 차이 [U, 기록]: rz −105 kit 0.833 / Maya 1.019, −180 0 / 1.111, +45 0 / 0.056, (0, 60, −45) 0.230 / 0.530,
  포즈 2 개 −45 0.5 / 0.476 (Maya RBF 상호작용), Gaussian 은 Linear 만 (회색 + 안내).
- FBX Export All → 다시 가져오기: 셰이프 키 `smile, blink, smile_ib500, smile_ibfix, face1` 유지 (엔진엔 드라이버 없이 키만).
- 헤드리스 `-k step227,step226_sdk,step218,step213_shape,step62` 87 / 87; 레인 A `-k ...step139_shape,step101,step166` 61 / 61,
  레인 B `-k step227_pose,step213,step101,step166,step54_,enable_disable` 72 / 72 + 73 / 73.
- GUI `-k shape_editor` 5 / 5 (인비트윈 행이 타깃 아래, 숨은 키 안 보임, 샷 확인), `gui_step227_pose_editor` 5 / 5 (샷 확인).

## 남은 것

- PSD 는 포즈마다 독립 선형: 포즈 밖·여러 포즈 겹침·Gaussian 은 Maya RBF 와 다름 [U]. 포즈 상수 (뼈 길이, θ₀) 는 포즈 추가 때
  고정 (나중에 비균일 스케일 / 본 이동하면 가중치 바뀜).
- 타깃 이름을 Blender 에서 바꾸면 인비트윈 기록·헬퍼 이름이 안 따라감; 인비트윈 가중치 변경 (`blendShapeChangeInBetweenWeight`)
  없음; 엔진 FBX 는 인비트윈을 드라이버 없이 받음 (보통 선형).
- Pose Editor 메뉴 바는 Maya 캡처가 없어 없음; 교정 셰이프 조각 느낌은 `docs/manual_checks.md`.
