# Step 181 — Surfaces basics (backlog_174 #8)

## 계획

Surfaces 메뉴 8 / 41 이 다섯 감사째 그대로 (step_173_quant.md §1a). Loft / Extrude 는 메시 · 커브 bevel 대용품이었다.

측정 (레인 M · B, 포그라운드 에이전트 2 개 동시):
- **M** — mayapy: `research/maya/re/surfaces_181.md/.json` (97 경우), `research/scripts/surfaces_181_mayapy.py` (`--check` =
  규칙을 순수 Python 으로 다시 계산). Loft / Revolve / Extrude (Tube · Flat · Distance) / Boundary / Square / Attach / Detach /
  Insert / Reverse / Duplicate patch 규칙이 Maya CV 와 ≤ 2.2e-7. Birail 1 은 레일이 한 평면에 있을 때만 정확 (꼬인 레일 [U]),
  Extrude Rotation / Scale [U], Rebuild / Close / Extend / Offset / Bevel 은 수치만 [U]. 출력은 모두 비유리 (가중치 1).
- **B** — Blender 4.5 레거시 NURBS 표면: `research/blender/nurbs_surface_181.md`. Endpoint (clamped uniform) · Cyclic (periodic
  uniform) 은 정확 (≤ 9e-7), 비균일 knot 은 Boehm 으로 Bezier 분해 + `use_bezier` + endpoint 로 모양 정확 (1.1e-6, CV 수
  1 + m·차수 일 때만), 사용자 knot 없음, 트림 없음. 점 인덱스 `points[j * point_count_u + i]`.

**표현 (delegated, 측정)**: Maya NURBS 표면 = Blender 레거시 NURBS 표면 (`prim_history.new_curve_data` 의 행 만들기 재사용),
Maya U = Blender u (행 방향), Maya V = 행 번호. 균일 → Endpoint / Cyclic, 비균일 열린 방향 → Bezier 분해, 차수 1 은 knot 과
무관. Maya 의 knot 벡터 · CV (분해 전) 는 데이터 ID 속성 `allset_nurbs` 에 기록 — 점이 그대로일 때만 유효 (step 65 기록과 같은 생각),
다음 Detach / Insert / Attach 가 Maya 매개변수를 이어받는다. Planar 은 트림 표면이라 Blender 표면이 될 수 없어 지금의 채운 2D 커브
그대로 (notice 유지). 메시로 가지 않는 이유: Maya 사용자는 Loft 결과의 CV 를 고치고 Insert Isoparms / Detach 를 이어서 쓴다.

수학 (`operators/surfaces_math.py`, bpy 없음, 오른손 좌표 어디서나 — Maya → Blender (X, −Z, Y) 는 회전이라 규칙이 그대로):
Loft (호환 knot, auto reverse, Uniform / Chord, Close, Section spans, Linear), Revolve (축 · 피벗 · 각 · 구간 · 차수), Extrude
(Tube at profile / at path / component pivot, Flat, Distance), Birail 1 (Proportional / Non), Boundary / Square (Coons), Attach
(Blend / Connect), Detach / Insert (Boehm), Reverse (U / V / Both / Swap), patch 잘라내기, Rebuild (곡선 Rebuild 를 방향마다, [U]
근사 — step 156 과 같은 처리), Blender 표현으로 바꾸기 (Bezier 분해, 비균일 periodic 은 열어서).

연산자 API (`operators/surfaces_maya.py`; 옵션 창 레인이 이 이름 · 속성에 맞춘다):
| 메뉴 | 연산자 | 속성 (factory) |
|---|---|---|
| Loft | `allset.loft` (curve_tools 의 메시 loft 대체) | `uniform` True, `close` False, `auto_reverse` True, `degree` '3' ('1'), `section_spans` 1 |
| Revolve | `allset.revolve` | `axis` 'Y' (Maya 축 X/Y/Z), `pivot` 'OBJECT' / 'PRESET', `pivot_point` (0,0,0), `start_sweep` 0, `end_sweep` 360, `degree` '3', `segments` 8 |
| Extrude | `allset.surface_extrude` | `style` 'TUBE' ('DISTANCE','FLAT'), `result_position` 'PROFILE' ('PATH'), `pivot` 'CLOSEST' ('COMPONENT'), `direction` 'NORMAL' ('X','Y','Z' Maya 축), `length` 1.0 |
| Birail 1 Tool | `allset.birail1` | `proportional` True |
| Boundary / Square | `allset.surface_boundary` | `kind` 'BOUNDARY' / 'SQUARE' |
| Attach | `allset.surface_attach` | `method` 'BLEND' ('CONNECT'), `bias` 0.5, `keep_originals` True |
| Detach | `allset.surface_detach` | `keep_original` False |
| Insert Isoparms | `allset.surface_insert_isoparm` | — |
| Duplicate NURBS Patch | `allset.duplicate_nurbs_patch` | — |
| Reverse Direction | `allset.surface_reverse` | `direction` 'U' ('V','BOTH','SWAP') |
| Rebuild | `allset.surface_rebuild` | `spans_u` 4, `spans_v` 4, `degree_u` '3', `degree_v` '3' |

선택 순서 (delegated): Blender 는 순서를 모른다 — Loft / Extrude / Attach = `modify_maya.selection_order` (활성 = 마지막, 나머지 이름순;
Extrude 경로 = 마지막). Birail 1 은 순서 대신 모양으로: 끝점 둘이 다른 두 곡선에 닿는 곡선이 profile, profile 시작에 닿는 쪽이 rail 1
(Maya 도구도 profile 이 레일에 닿아야 한다). Boundary 는 Maya factory "Automatic" 처럼 끝점으로 머리-꼬리 순서를 만든다. Detach / Insert /
Duplicate patch 는 Blender 가 isoparm · patch 를 고를 수 없어 편집 모드에서 고른 CV 로: CV 줄이 한 행 / 열이면 그 줄의 Greville 매개변수
(step 156 Detach 와 같은 처리).

레인:
- **메인**: `surfaces_math.py` + `surfaces_maya.py` + 헤드리스 테스트 (JSON 대비 1e-4), step109 테스트 갱신.
- **W (에이전트, 동시에)**: `operators/option_windows_surfaces.py` (Maya 옵션 창: 제목 · 필드 · factory 값 surfaces_181.md §1),
  `ui/menu_map.py` / `ui/notices.py` / `ui/shelf_map.py` 연결, `tests/test_step181_menus.py`. 메인 파일은 건드리지 않음.
- **G (메인이 끝난 뒤)**: GUI 스크린샷 (loft 표면) — 연산자가 있어야 해서 순서.

## 한 일

**측정** (레인 M, `research/maya/re/surfaces_181.md/.json`, 97 경우): mayapy standalone 은 `SurfaceUIExists` 조건이 없으면 모든
Surfaces perform proc 가 폴리곤 출력 (`-po 1`)을 강제한다 — 스크립트가 GUI 상태를 세팅 (§1). factory "Model with tools" 꺼짐 = 메뉴
항목이 선택에 바로 실행 (Birail 만 도구). 출력은 모두 비유리 NURBS 표면, 새 transform (월드 루트), 입력 곡선은 남는다.

**Blender 표현** (레인 B, `research/blender/nurbs_surface_181.md`): 위 「계획」 그대로 — 측정한 Maya 출력 105 개 중 81 개가 두 방향 모두
균일 (Endpoint / Cyclic 로 정확), 나머지는 Bezier 분해로 모양 정확, Planar 만 트림이라 표면 불가 (채운 2D 커브 유지).

**수학** (레인 C, `operators/surfaces_math.py`, bpy 없음): Loft (호환 knot · auto reverse · Uniform / Chord · Close · Section spans ·
Linear), Revolve, Extrude Tube / Flat / Distance, Birail 1, Boundary / Square (Coons, `order_boundary` = Automatic), Attach (Blend /
Connect), Detach / Insert / sub patch (Boehm), Reverse (U / V / Both / Swap), Rebuild ([U] 근사: 각 CV 줄을 0..1 로 펴고 Maya knot 의
Greville 점에서 보간 — knot 같음, 모양 0.035), `blender_grid` / `from_blender_grid` (+ 매개변수 지도 `map_u/v`).

**연산자** (메인, `operators/surfaces_maya.py`): 「계획」 표의 11 개 연산자. 결과 = SURFACE 오브젝트 (월드 원점, Maya 이름
`loftedSurface1` / `revolvedSurface1` / `extrudedSurface1` / `singleProfileBirailSurface1` / `boundarySurface1` / `squareSurface1` /
`<a>attachedSurface1` / `<a>detachedSurface1` / `duplicatedSurface1`, lambert1). 데이터 ID 속성 `allset_nurbs` = Maya knot · CV (점
서명이 맞을 때만 쓰임) → Detach / Insert 가 Maya 매개변수를 잇는다. Revolve / Extrude 의 Maya 축 = Blender (X, −Z, Y), 길이 · 피벗 점 ×
`maya_unit()`, Revolve factory 피벗 = 곡선 오브젝트 원점 (kit 의 Maya pivot). Blender order 최대 6 → Maya 차수 7 은 5 로.
curve_tools 의 메시 Loft / 커브 bevel Extrude 는 지움 (같은 bl_idname 을 이 모듈이 가짐).

**메뉴 / 옵션 창** (레인 W): `operators/option_windows_surfaces.py` — Loft / Revolve / Extrude / Birail 1 / Boundary / Square Surface /
Attach Surfaces / Detach Surfaces / Reverse Surface Direction / Rebuild Surface Options (Maya 제목 · 라벨 · factory 값, 못 따르는 필드는
`missing`). `menu_map`: Revolve (SCREW 모디파이어였음), Reverse Direction (`curve.switch_direction`), Insert Isoparms (`curve.subdivide`)
를 kit 연산자로, Birail 1 / Boundary / Square / Duplicate NURBS Patch / Attach / Detach / Rebuild 새로 연결. 거짓이 된 notice
(Loft = Mesh, Extrude = curve bevel) 삭제, 셸프 Revolve 는 메뉴 항목을 거침.

delegated: Blender 에는 선택 순서가 없어 Loft / Extrude / Attach 는 `modify_maya.selection_order` (활성 = 마지막); Birail 1 은 순서 대신
모양 (끝 둘이 다른 두 곡선에 닿는 곡선 = profile, profile 시작 쪽 = rail 1, profile 이 끝 쪽에 있으면 레일을 뒤집음); Boundary 는 끝점
사슬. Detach / Insert / Duplicate patch 는 편집 모드에서 고른 CV 줄 (한 행 = V isoparm, 한 열 = U, 한 점 = U) 의 Greville 매개변수.

순서가 필요했던 것: 연산자 (메인) 는 레인 C 의 수학 API 위에, GUI 샷은 연산자 뒤.

## 검증

- `tests/test_step181_surfaces_math.py` 12 / 12 (레인 C): mayapy 정답과 knot 같음 + CV — Loft 23 경우 1.2e-7, Revolve 14 경우 8.3e-8,
  Extrude 16 경우 8.5e-8, Birail (평면 레일) 4 경우 0, Boundary / Square 5.8e-8, Attach 2.8e-17, Detach / Insert / Reverse / patch
  1.0e-7; `blender_grid` 왕복 98 표면 (독립 Cox–de Boor 로 Blender knot 규칙 평가 = Maya 표본) 1.8e-7.
- `tests/test_step181_surfaces_ops.py` 8 / 8: Blender 오브젝트 위에서 연산자 → Blender 점 = Maya CV (≤ 9.5e-7) **그리고** Blender 가
  평가한 정점 = Maya 표면 (≤ 9.3e-6, float32) — Loft 12, Revolve 9, Extrude 7, Birail 4 (선택 순서 섞어도), Boundary / Square 3,
  Attach + Reverse 4 + Rebuild knot, 편집 모드 CV 선택으로 Detach / Insert / Duplicate patch, step 156 EP / CV 곡선 loft.
- `tests/test_step181_surface_menus.py` 5 / 5 (레인 W): 창 · 경로 · factory 값 = 연산자 기본값, notice 일관성, Surfaces ≥ 15.
- `python tools/menu_count.py`: Surfaces **8 → 15 / 41**, Modeling 185 → 192 / 349, 회색 notice 없음 0; `menu_consistency` 0 쌍.
- 헤드리스 전체 4.5: **1683 / 1683** (205 파일).
- GUI `gui_step181_surfaces` 10 / 10 — 메뉴 항목 Surfaces > Loft (EP 곡선 3 개 → 5 × 6 CV 표면이 곡선을 지남 1.5e-9) / Revolve (8 구간
  cyclic). 스크린샷 직접 봄 (`gui_step181_loft.png`: 세 곡선 사이 물결 표면이 lead 초록 와이어, Channel Box loftedSurface1 /
  loftedSurfaceShape1; `gui_step181_revolve.png`: 컵 모양 회전 표면). 관련 GUI `-k step109,step156,step103` 50 / 50.

## 남은 것

- [U] 그대로: Birail 1 꼬인 레일 (Maya 와 0.17–0.61), Extrude Rotation / Scale, Tube 의 차수 1 경로 (0.052), Rebuild 정확한 알고리즘,
  Open/Close (Blender cyclic 토글 그대로), Extend / Offset / Bevel / Move Seam (측정만, 회색 + notice).
- 비균일 knot 곡선 (chord EP, Detach 조각) 은 Blender 곡선에서 Bezier 분해로만 남아 (step 156) loft 매개변수가 Maya 와 달라질 수 있다 —
  곡선에도 `allset_nurbs` 같은 knot 기록을 두면 해결.
- Birail 2 / 3+, Align, Attach Without Moving, Intersect / Project / Trim / Untrim, Round, Stitch, Fillet, Sculpt Geometry, Surface Editing,
  Booleans: 측정 안 함 (회색 + notice). Planar 은 트림 불가라 채운 2D 커브.
- Insert Isoparms / Duplicate NURBS Patch 옵션 박스는 generic (kit 창 없음). Birail 은 Maya 처럼 도구 (클릭으로 profile / rail 고르기)가
  아니라 선택에 실행.
- manual_checks 「Step 181」.
