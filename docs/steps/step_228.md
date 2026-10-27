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

## 한 것

레인 2 개 병렬 (A L8, B L9 + L10; 파일 단위, `operators/__init__.py` 는 메인이 스텁 등록).

- **A Attach to Motion Path / Set Motion Path Key** (`operators/motion_path_228.py`, `option_windows._extend` 2 줄,
  `ui/menu_map.py` 2 항목, `ui/notices.py` 의 "Constrain/Motion Paths" 범주 안내 삭제): Follow Path `motionPathN`
  (forward X, up Z = Maya Y, Fixed Position + `offset_factor` 키 Time Slider 시작 0 → 끝 1, Maya auto 탄젠트 =
  `driven_key.maya_auto` 재사용), 선택 순서 무관, 오브젝트 위치·회전 0 (Maya 측정), 경로 커브 resolution = 스플라인당 약 1024
  평가점 (4 스팬 = 256; 기본 12 는 5.1e-3 어긋남). Set Motion Path Key = Maya 처럼 커브에 edit point 를 넣어 다시 맞춘 뒤
  (`curves_math.interpolate`, Bezier 로 정확히 씀) 새 커브 위 비율로 키. 옵션 창 "Attach to Motion Path Options" (Maya factory,
  Parametric length = Maya 매개변수 키를 프레임마다 호 길이 비율로 굽기; 못 하는 World up / Bank 는 회색) — delegated.
- **B Flow Path Object** (`operators/flow_path_228.py` + 옵션 창): step 144 격자 (`ffd1` / `ffd1Base` / `ffd1Lattice` 5×2×2,
  Linear) + 격자에 Curve 모디파이어 `flow1`, 셰이프 키 `flow1` 가 격자를 경로 길이만큼 밀고 드라이버 = 오브젝트의 offset_factor;
  오브젝트의 Follow Path 는 mute. 경로가 원점이 아니면 Child Of. 모션 패스가 없으면 경고.
- **B Loft Output geometry Polygons** (`operators/surfaces_maya.py`, `option_windows_surfaces.py`): Maya `-po 1` 처럼 메시
  `loftedSurface1` + UV "map1" 만 (서피스 오브젝트 없음), 킷 히스토리 = 입력 커브가 바뀌면 depsgraph → 타이머로 다시 만듦
  (ID 속성 `allset_loft`, 메시를 편집하면 끊김).

## 검증

- vs mayapy: mp_default 18 프레임 위치 9.5e-5 / 회전 9.7e-4°, 선택 순서 반대·오프셋·회전된 오브젝트 같음; mp_parametric
  3.8e-5; mp_3d 위치 9.2e-5 (롤 최대 9.7° 차이 — Blender Follow Path 의 up 규칙 [U]); mp_setkey50 위치 1.07e-4 (Maya 자체 호 길이
  근사가 1.23e-4 이라 이 경우만 1.5e-4 허용). Loft: 정점 / 면 / UV 40 / 56 / 40 = Maya, Maya 정점의 UV 에서 킷 서피스 = Maya
  정점 1.0e-6. Flow: 격자 끝 평면 정점 1.8e-4, 안쪽은 최대 0.075 (Maya 격자 = Bernstein 볼륨, Blender Linear 가 가장 가까움) [U].
- 헤드리스 `-k step228,step181,step101,step103` 67 / 68 — 실패 1 = `test_step103` `paint_weights_membership`
  (step 219 c1129b7 가 Maya 2026 메뉴에서 "Set Membership" 을 뺀 뒤부터, 이번 단계와 무관 → Release prep). 레인 A
  `-k step228_motion_path,step156,step207,step101,step166` 69 / 69, 레인 B `-k step228_flow_loft,step181,step144,...` 164 / 165 (같은 step103).
- GUI `-k curves` 53 / 53 (gui_step228_curves 4 / 4: 메뉴로 붙이기, 프레임 60 위치 4.7e-5, 진행 방향 44.977° = Maya, 키 50; 샷 확인).

## 남은 것

- 3D 경로 롤 (Maya world-up 투영과 다름, 최대 9.7°), Flow 안쪽 정점 (≤ 0.075, 정확히는 GN Bernstein 디포머 필요),
  Flow 만든 뒤 경로를 고치면 이동량이 낡음, Lattice around Curve / Local effect 없음.
- 모션 패스 없는 오브젝트에 Set Motion Path Key = Maya 는 경로 커브를 만듦, 킷은 경고만. Delete History 가 loft 기록을 안 끊음.
- Release prep: `test_step103` Set Membership, `test_step169_deform` 2 개 (step 219 메뉴 변경 뒤).
