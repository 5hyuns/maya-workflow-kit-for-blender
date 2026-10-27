# Step 228 — Curve rig leftovers: motion path, flow path, loft (Issue #138)

기준: 결정 문서 (비공개 bmk-strategy) ATTACH_PLAN L8–L10, `research/maya/re/maya2026_curve_rigs.md` §L8–L10, 이번 mayapy 측정
`research/maya/re/curve_rigs_228.json` (스크립트 `research/scripts/maya_curves228/measure.py`, Maya 2026).

## 계획

### 이번 측정 (mayapy 2026)
- Attach to Motion Path (factory: fraction mode, Follow, Front X, Up Y, World up Vector, Time Slider 1–120): u 키 (1 → 0),
  (120 → 1) auto (= 끝 평평), 18 프레임 위치·회전 (`mp_default`). **오브젝트 원래 위치·회전은 더하지 않음** — (2, 1, −3) /
  ry 30 에서 붙여도 결과가 같음 (`mp_offset`, `mp_rotated_obj`; maya2026_curve_rigs.md 의 "원래 위치를 더함" 은 틀림).
  3D 경로 (`mp_3d`, up = world Y 벡터라 뱅크 회전 생김), parametric (fraction 끔, `mp_parametric`).
- Set Motion Path Key at 50: u 키 [1, 50, 120] 값 [0, 0.370764, 1] (그때 u), 탄젠트 auto (`mp_setkey50`, 위치 18 개).
- Flow Path Object: `flow -divisions 5 2 2` → ffd1 / ffd1Lattice / ffd1Base, 정점 12 개 × 5 프레임 (`flow`).
- Loft Output Polygons: 정점 40 / 면 56 / UV 40 (nurbsTessellate general, uNumber/vNumber 3), CV 를 움직이면 메시가 따라감.

### 설계 (delegated)
- **A L8** (`operators/motion_path_228.py`, `ui/menu_map.py` Constrain > Motion Paths, 옵션 창): `allset.motion_path_attach`
  = Follow Path (`use_curve_follow`, forward X, up Z = Maya Y, `use_fixed_location` + `offset_factor` 키 Time Slider 시작 0 →
  끝 1, Maya auto 탄젠트), 선택 순서 무관 (커브 = 경로), 오브젝트 위치·회전 0 (Maya 처럼 경로에 붙음), 경로 커브
  resolution 을 올려 호 길이 정확도 확보; Set Motion Path Key = 현재 u 를 현재 프레임에 키 (Maya auto 기울기 규칙).
  옵션 창 = Maya Attach to Motion Path Options.
- **B L9 + L10** (`operators/flow_path_228.py`, `operators/surfaces_maya.py` / `option_windows_surfaces.py`): Flow Path =
  Lattice 5×2×2 `ffd1Lattice` 로 오브젝트를 감싸고 Lattice 모디파이어 `ffd1`, 격자는 경로를 따라 휨 (근사). Loft Output
  Geometry Polygons = 메시 + UV, 커브를 움직이면 다시 만듦 (킷 히스토리).

### 검증
- 헤드리스: mp_default / mp_setkey50 / mp_3d / mp_parametric 위치 1e-4 (축 변환 후), 회전 기록; Flow 노드 구성 + 정점 차이
  기록; Loft 정점 / UV 수 + 히스토리. GUI `-k curves`.
