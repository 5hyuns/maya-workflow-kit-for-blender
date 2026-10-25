# Step 190 — Seven Polygon Primitives

backlog_183.json #8 (마지막): audit 13 #9 — Create > Polygon Primitives 의 Pipe, Helix, Gear, Soccer Ball, Super Ellipse,
Spherical Harmonics, Ultra Shape 회색 (Create 57 %, 감사 11 부터 그대로).

## 계획

| 레인 | 내용 | 파일 | 누가 |
|---|---|---|---|
| 측정 | mayapy: 메뉴 runtime 명령 7 개 (e1.json) + 속성 변화 134 경우 (v1.json) | `research/scripts/maya_prims190/explore.py`, `variants.py` | 메인 (순차: 두 레인의 입력) |
| A | polyPipe / polyHelix / polyGear / polyPrimitiveMisc 빌더 (bpy 없음) + plain python 비교 | `operators/prim_shapes_more.py`, `compare_a.py` | 포그라운드 서브에이전트 |
| B | polySuperShape (세 모양) 빌더 + 비교 | `operators/prim_supershape.py`, `compare_b.py` | 포그라운드 서브에이전트 (A 와 동시) |
| 통합 | NODES / POLY 합치기, KIND_NODES, create.KINDS, menu_map, 마킹 메뉴, 테스트, GUI 샷 | 기존 파일 | 메인 |

A / B 는 새 파일만 쓰고 Blender 를 띄우지 않음 (JSON 대 순수 python) → 동시에 안전. 통합은 두 레인 결과가 필요해 뒤에.

## 한 것

- 측정: `research/maya/re/poly_prims_185.md` (레인 A / B 절 합침; 원본 `poly_prims_185_a.md` / `_b.md`), 데이터
  `research/scripts/maya_prims190/*.json` (e1, v1, 레인 A `v2a`, 레인 B `b1` / `b2` / `minmax_b`).
- 빌더 (Maya Y-up, Maya 단위, `prim_shapes.Mesh`):
  - `prim_shapes_more.py`: polyPipe (높이 = Height / 2 로 지어짐, 링은 +X 에서 시작, 단면 순서 inner → top → outer →
    bottom, Round Cap 반원), polyHelix (steps = max(1, ⌊coils + 0.5⌋) × Subdivisions Coil, 수직면 단면, Direction,
    캡 / 둥근 캡, Maya 실린더 UV 배치), polyGear (변당 6 점 이빨, 안쪽 링 2n, twist / taper 높이별, Internal Radius 0 =
    가운데 정점), Soccer Ball (깎은 정이십면체, 면 / UV 망 순서는 측정 표), Pipe / Soccer 축은 +Y → +Z → 축 (`orient_z`),
    딱딱한 엣지 = 30° 규칙.
  - `prim_supershape.py`: polySuperShape 하나 (shape enum 0 / 1 / 2 = Super Ellipse / Spherical Harmonics / Ultra),
    격자 4 × divisions, float32 각도 (double 로는 지수가 작을 때 0.039 차이), 세로 우선 정점 순서, 극 = 삼각형 부채,
    super-ellipsoid / Bourke 식 spherical harmonics / Gielis superformula (ultra0..7 가로, 8..15 세로), Mirror, UV
    Sawtooth / Pinched, 30° 딱딱한 엣지. Revolutions / Vertical Offset / Internal Radius / X·Z Offset 는 Maya 2022 에서
    아무 효과 없음 (측정).
- 통합: `prim_shapes` 끝에서 두 모듈의 NODES / POLY 합침; `prim_history.KIND_NODES` 7 개 + `KIND_VALUES` (세 메뉴 항목이
  같은 polySuperShape 를 shape 값만 달리해 만듦); `create.KINDS`, `menu_map._PRIMS`, Create 마킹 메뉴 (Shift+RMB) Pipe /
  Helix / Gear; 이름 pPipe1 / pHelix1 / pGear1 / pSolid1 / pSuperShape1 + 노드 polyPipe1 … (Maya). Channel Box INPUTS
  편집 = 기존 primitive 와 같은 `prim_history.rebuild`. "Create/Polygon Primitives" notice 는 이제 Interactive Creation /
  Exit On Completion 만 덮으므로 문구 고침.
- step 189 문서 정정: `--options` 의 "generic 0" 은 출력 필터 실수였음 (generic 34; Insert Isoparms 는 그 안에 없음).

## 검증

- 순수 python: `compare_a.py` 89 / 90 경우 정확 (위치 ≤ 1e-4 — 최대 9.95e-6, 면 목록 동일, UV ≤ 2e-6, 딱딱한 엣지 동일);
  `compare_b.py` 253 / 253 (위치 최대 7e-6, UV 5e-7, 16 / 16 메뉴 기본 포함).
- 헤드리스 `test_step190_primitives` 3 / 3: Blender 안에서 22 경우 (메뉴 Pipe / Soccer + 변형) 정점 위치 1e-4, 면 목록,
  코너 UV, 딱딱한 엣지가 mayapy 와 같음, 큰 메뉴 기본 (Helix 1208 / Gear 1408 / super shape 4034 정점) 은 개수 + 앞 24 점;
  Maya 이름 / 노드, INPUTS rebuild. step129 primitive 11 / 11 그대로. 헤드리스 전체 1727 / 1730 → Pipe 를 회색 예로 쓰던 옛 기대 3 개
  (step7 / step21 / step136 마킹 notice) 고친 뒤 그 파일들 통과 = 1730 / 1730.
- `tools/menu_count.py`: Create 40 → 47 / 70 (**67 %**), Common 291 → 298, 전체 850 → 857 / 1486 (57.7 %), 회색 notice 없음 0;
  `menu_consistency` 0. 새 primitive 옵션 상자는 기존 Disc / Prism 처럼 "redo".
- GUI `gui_step190_primitives` 2 / 2 + 스크린샷 (일곱 개 한 줄, 이름, INPUTS polySuperShape3) 눈으로 확인.

## 남은 것

- `gear_s6_off0` (Gear Offset 0 = 넓이 0 이빨 면): kit 은 4 엣지를 딱딱하게, Maya 는 부드럽게 — 넓이 0 면의 노멀 잡음 [U].
- Soccer Ball 면 / UV 망 순서는 규칙을 못 찾아 측정 표 (`SOCCER_FACES` / `SOCCER_NET`) [I].
- In-View Editor 는 kit 에서 extrude 기록에만 있음 — 기존 primitive 처럼 새 7 개도 INPUTS 편집만 (delegated; 다음 감사 후보).
- Interactive Creation / Exit On Completion 은 notice (Blender 는 드래그로 크기 정하는 생성 없음).
