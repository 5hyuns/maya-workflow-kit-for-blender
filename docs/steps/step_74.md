# Step 74 — 프리셀렉션 하이라이트 확대 (엣지 · 면 · 변형 툴)

## 계획 (delegated)

재점검 4차 우선순위 3. Step 30 의 프리셀렉트는 정점 모드 + 선택 툴에서만 된다 (`operators/preselect.py`).

### Maya 실측 (Maya 2022 GUI, `research/scripts/maya_pre/pre.py`, 화면 `research/maya/screens/pre/`, 저장소 밖)

커서는 SendInput 으로 4×4×4 큐브의 정해진 점 위에 둔다.

| 경우 | 결과 |
|---|---|
| 오브젝트 모드, 큐브 위 (pre_01) | **하이라이트 없음** (큐브 그대로) |
| 정점 모드, 꼭짓점 (pre_02) | 5 px 빨간 사각 #ff0100 |
| 엣지 모드, 엣지 가운데 (pre_03) | 그 엣지 2 px 빨간 선 |
| 엣지 모드, 꼭짓점 근처 (pre_04) | 여전히 **엣지** (선택 모드를 따른다) |
| 면 모드, 면 안 (pre_05) | 면 테두리 빨강 + 한 칸 건너 빨간 점무늬 #d84240 |
| Move 툴 + 면 모드 (pre_06) | 같은 하이라이트 (변형 툴에서도 된다) |

### Blender 실측 (임시 GUI 프로브, 지움)

`GIZMO_GT_mesh_preselect_elem_3d` 는 엣지 가운데, 꼭짓점 근처, 면 가운데, 면의 엣지 근처, 꼭짓점 어디서든 같은 정점 (vert 2) 을 골랐다 (작은 큐브, 엣지 / 면 모드).
선택 모드를 바꿀 속성도 없다: RNA 에는 vert / edge / face index 와 공통 기즈모 속성만 있다.
→ 엣지 / 면 모드에는 쓸 수 없다.

### 설계

`operators/preselect.py` 를 Python 기즈모 `MAYAKIT_GT_preselect` 하나로 바꾼다. 정점 / 엣지 / 면을 같은 규칙으로 다룬다.

- 고르기: 순수 함수, numpy, bpy 없음 → 헤드리스 테스트.
  - 화면 좌표: 편집 메쉬의 정점을 `perspective_matrix` 로 한 번에 투영한다.
  - 정점: 커서에서 반지름 R 안의 가장 가까운 보이는 정점.
  - 엣지: 커서에서 선분까지의 화면 거리가 R 안인 가장 가까운 보이는 엣지.
    - 없고 커서가 면 위면 그 면의 가장 가까운 엣지다 (Maya 엣지 모드 클릭과 같은 뜻 [delegated]).
  - 면: 커서 아래 면 (BVH ray cast).
  - R = 16 px × UI 배율 (`MT_preSelectSize 16`, defaults.json:99 [I]).
- 가림:
  - 편집 메쉬별 `BVHTree.FromBMesh` 를 캐시한다. depsgraph 갱신이 오면 버린다.
  - 요소는 커서 아래 면에 속하거나, 그 점으로 쏜 광선이 앞에서 막히지 않을 때 보인다.
  - X-ray (셰이딩 플래그) 면 가림 검사를 하지 않는다.
  - 숨긴 요소는 뺀다.
- 그리기: 기즈모 `draw` 에서 gpu 로 그린다 (월드 좌표, 깊이 검사 없음).
  - 정점: 5 px 사각.
  - 엣지: 2 px 선 (`POLYLINE_UNIFORM_COLOR`).
  - 면: 2 px 테두리 + 붉은 반투명 채움 (Maya 점무늬의 평균색, [I] 근사).
- 변형 툴 (Move / Rotate / Scale) 에서도 켠다.
  - Python 기즈모의 test_select 는 매니퓰레이터 손잡이보다 먼저 이긴다 (step 30 측정).
  - 그래서 커서가 손잡이 위면 -1 을 돌려준다.
    - kit Move / Scale (`ui/manipulator`): 가운데 사각 + 세 축 선분 (화면 투영, 화살 길이 `ARROW_PX` × gizmo_size / 75 × UI 배율) 에서 12 px 안.
    - Rotate (Blender C 기즈모): 가운데에서 반지름 gizmo_size / 2 × UI 배율 × 1.25 안.
    - 매니퓰레이터 위치는 `manipulator.center_of` (선택 정점 캐시) 로 구한다.
- 클릭: 기즈모에 invoke / modal 이 없으면 클릭은 선택 툴로 간다 (step 30 의 C 기즈모와 같음). GUI 테스트로 다시 확인한다.
- 오브젝트 모드: Maya 2022 기본값은 오브젝트를 하이라이트하지 않는다 (pre_01). 그래서 만들지 않는다 (C 가 아니라 「Maya 에 없음」).

### 검증

- 헤드리스:
  - 고르기 함수 (투영된 정점 / 엣지 / 면 배열로 정점 · 엣지 · 면 선택, 반지름, 가림 콜백).
  - 손잡이 제외 함수.
  - 기즈모 그룹 poll (정점 / 엣지 / 면 × select / move / rotate / scale 툴, 오브젝트 모드, 환경설정 끔).
- GUI:
  - 엣지 모드 엣지 위 호버 → 그 엣지 + 스크린샷.
  - 엣지 모드 꼭짓점 근처 → 엣지.
  - 면 모드 면 위 → 그 면 + 스크린샷.
  - Move 툴에서 면 → 하이라이트. 화살 위 → 없음.
  - 클릭은 여전히 선택한다.
- step 30 GUI 테스트 (정점) 그대로 통과. 전체 테스트, dogfood, manual_checks.

## 한 것

- `operators/preselect.py` 를 다시 썼다.
  - `MAYAKIT_GT_preselect` (Python 기즈모) 가 정점 / 엣지 / 면을 선택 모드대로 고른다.
    - numpy 투영 + 화면 거리 (R 16 px), 가림은 BVH 광선, X-ray 면 가림 없음, 숨긴 요소 제외.
    - 엣지는 꼭짓점 근처에서도 엣지, 면 위 먼 곳 = 그 면의 가장 가까운 엣지.
  - 그리기: 정점 5 px 사각, 엣지 2 px 선, 면 = 2 px 테두리 + 붉은 반투명 채움.
  - 편집 메쉬 캐시 (`MeshCache`): numpy 좌표, 숨긴 면이 없으면 `BVHTree.FromBMesh`, 면 목록은 필요할 때 읽는다.
    - depsgraph 갱신이 지오메트리 / 변형이면 버리고, 선택만 바뀌면 선택 정보만 잊는다.
    - 10만 정점: 캐시 0.25 s (편집 뒤 첫 호버만), 호버 계산 0.02 s.
  - 선택 툴 + Move / Rotate / Scale / Transform 툴에서 켠다.
    - 매니퓰레이터 위에서는 끈다: kit Move / Scale 는 가운데 사각 + 세 축 화살표 12 px 안, Rotate 는 gizmo_size / 2 × 1.25 원 안.
  - `gz.hide_keymap = True`: 'SELECT' 옵션 그룹에서는 하이라이트된 기즈모 위 클릭이 'Generic Gizmo Select' (gizmo_tweak) 로 가서 선택 툴에 닿지 않았다 (`--debug-handlers` 로 확인). 이걸 켜면 호버는 그대로이고 클릭은 툴로 간다.
- 오브젝트 모드: Maya 2022 기본값은 오브젝트를 하이라이트하지 않아서 (pre_01) 만들지 않았다. 「불가 (C)」가 아니라 「Maya 에 없음」이다.
- 환경설정 설명 갱신. `research/maya/interaction.md:73` 에 측정값을 더했다. 측정 스크립트는 `research/scripts/maya_pre/` (저장소 밖).
- step 30 GUI 테스트의 두 기대값을 새 동작으로 바꿨다: 면 모드 = 면 하이라이트, Move 툴 = 정점 하이라이트.

## 검증

- 헤드리스 `python tests/run.py`: **596/596** (69 파일). 새 `test_step74_preselect.py` 7:
  - 투영, 정점 / 엣지 고르기 (반지름, 가림, 꼭짓점 근처 엣지, 면 fallback, t 전달), 손잡이 제외.
  - MeshCache (월드 좌표, 숨긴 면, 광선), 툴 × 선택 모드 poll, 캐시 유지 / 버림.
- GUI `python tests/gui/run.py`: **510/510** (57 파일). 새 `gui_step74_preselect.py` 6:
  - 엣지 가운데 → 엣지 7, 꼭짓점 옆 → 여전히 엣지, 면 → 면 4.
  - 하이라이트된 면 클릭 → 선택.
  - Move 툴에서 다른 면 → 하이라이트, 화살표 위 → 없음.
- `python tools/dogfood.py`: **47/47**, 콘솔 0.
- 스크린샷 직접 확인: `gui_step74_edge.png` (위 앞 엣지 빨강), `gui_step74_face.png`, `gui_step74_move_tool.png` (윗면 빨간 테두리 + 채움, 매니퓰레이터 그대로).

## 남은 것

- Maya 의 점무늬 채움 대신 반투명 채움이다 [I].
- Rotate 툴 제외는 원 근사이고, Blender C 이동 기즈모 (kit 매니퓰레이터를 안 쓰는 레이아웃) 의 화살 길이는 kit 값으로 어림한다.
- 엣지 모드 Maya 루프 미리보기, UV 에디터 프리셀렉트, 오브젝트 / 커브 / 아마추어 편집 모드는 없다.
- 손 확인: `docs/manual_checks.md` 「Step 74」 (큰 메쉬 체감 포함).
