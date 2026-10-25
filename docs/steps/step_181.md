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
