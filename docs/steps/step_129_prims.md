# Step 129 — lane P: Maya primitive topology + creation history in INPUTS (#11, #12)

User request (verbatim): "#12: 폴리 실린더 캡이 n-gon이 아니라 Maya처럼 중심 버텍스 삼각팬, Subdivisions Caps 옵션으로 링 추가; 모든 폴리
프리미티브 Maya 팩토리 토폴로지·버텍스/면 수 대조 테스트; — #11: 폴리곤(스피어·큐브·실린더 등)과 NURBS(원·네모 등) 모두 생성 시 — 회귀
가능성 큼, 언제 깨졌는지 git bisect로 확인 — Channel Box INPUTS에 생성 노드(makeNurbCircle1: Radius, Sections, Normal…)가 안 뜸 —
폴리곤처럼 히스토리 노드로 노출·수정 시 재생성"

## 계획

1. **bisect** (회귀인지): 헤드리스 검사 스크립트(`tmp/prims129/bisect_check.py`, 각 커밋의 `src/<pkg>` 를 샌드박스 확장으로 설치 →
   Create Cube → ID 속성·모디파이어·kit 히스토리 API 에서 `polyCube` 노드 찾기)로 `git bisect run`.
2. **Maya 측정** (mayapy, 새 `MAYA_APP_DIR`): Create 메뉴가 실제로 만드는 명령(`performPolyPrimitive <Op> 2`, `performNurbs<Op> 2`)과
   변형들의 점·면·하드 엣지·UV·노드 속성, NURBS CV/knot/form → `research/maya/re/primitives_129.md`,
   스크립트·원자료 `research/scripts/maya_prims129/`.
3. **빌더**: `operators/prim_shapes.py` (bpy 없음, Maya Y-up 좌표): 폴리곤 10종 + NURBS 8종을 Maya 규칙대로. 측정 비교 도구
   `compare.py` 로 위치·면 방향·UV(메뉴 경우)·CV 까지 대조.
4. **히스토리 노드**: `operators/prim_history.py` — 노드 = 셰이프 데이터(Mesh/Curve)의 ID 속성 `allset_history`
   (nurbsSquare/nurbsCube 는 그룹 empty, 파츠에 `allset_history_part`). 값 변경 = 같은 데이터에 다시 짓기(오브젝트·트랜스폼·재질 유지).
   점 시그니처가 kit 가 만든 그대로일 때만 노드를 보임(그 뒤 Blender 편집은 재생성하면 사라지므로; Maya 는 tweak 으로 보존).
5. **UI**: `ui/creation_inputs.py` — Channel Box INPUTS 행(Scene 텍스트 프록시, step 38 입력 규칙, 선택한 같은 타입 노드 전부),
   AE 탭 `CH`. `channel_box.py` 는 INPUTS 섹션에 두 줄만.
6. Delete History / Non-Deformer History 가 노드를 지움, Duplicate 는 노드를 복사하지 않음(Maya: input graph 없이 복제).

## 한 것

- bisect: 아래 「bisect」.
- `operators/prim_shapes.py` (새): `NODES` (Maya 노드 타입 → 속성명·라벨·메뉴 기본값·종류·범위), 빌더 `POLY` / `NURBS_BUILD`, `build()`.
  - 실린더 캡 = 중심 버텍스 삼각팬(메뉴 기본 Subdivisions Caps 1), Caps n = 동심 링 n−1 + 팬, 0 = n-gon, Round Cap = 반구 링.
  - 콘(밑면 n-gon 기본, Cap 링), 스피어(폴 팬, sawtooth UV), 토러스(twist), 플레인, 큐브(분할), 피라미드/프리즘(변 길이 기준, 정삼각 옆면),
    디스크(5 모드), 플라토닉(5 다면체 × 4 분할 모드, 구형 팽창).
  - NURBS: 원/호(주기 CV 반지름 6/(4+2cos(360/n)), 열린 호는 매듭 보간 + 끝 접선 위 현의 1/3), 사각형 4 커브, 회전체(구·원기둥·원뿔·
    토러스), 평면, 큐브 6 패치(left = +Z, front = +X; patchesU = 면의 낮은 축).
  - 하드 엣지: 실린더/콘 림 명시, 큐브·다면체 전부, 나머지는 면 법선 55도 초과(Maya 규칙이 순수 각도가 아님, spec §2.10).
- `operators/prim_history.py` (새): `create_object` (노드 저장, `map1` UV, 단위 규칙 `units.maya_unit()` × 길이), `rebuild`
  (편집 모드 메시는 edit bmesh 에 다시 씀; NURBS 곡면 행은 Python 으로 추가할 수 없어 임시 오브젝트 편집 모드에서 `curve.extrude` 로 만듦),
  `node_of` / `drop` / 시그니처.
- `operators/create.py`: 프리미티브 18종이 `prim_history.create_object` 로(블렌더 primitive op 제거); Maya 이름 끔 → 메뉴 라벨 이름.
- `operators/option_windows.py`: 프리미티브 옵션 창이 노드 속성을 채움(실린더/콘 Cap divisions·Round cap, 콘 Height divisions,
  토러스 Twist 추가 — 「missing」 에서 뺌). `operators/curve_tools.py`: 옛 nurbs_square/cube/cone 빌더 삭제(생성은 prim_history).
- `command_line/cmds_shim.py`: `polyCube/Sphere/Cylinder/Plane` 이 같은 빌더 + 노드(반환 `[pCube1, polyCube1]`, `ch=False` 면 노드 없음;
  맨 명령 기본값 = 캡 0).
- `ui/creation_inputs.py` (새), `ui/channel_box.py` (INPUTS 에 노드), `ui/attribute_editor.py` (탭 `CH` = "<Nice Type> History"),
  `operators/history.py` (Delete History 가 노드 삭제), `operators/duplicate.py` (복제본은 노드 없음).

## 검증

- `tests/test_step129_primitives.py` (11): 메뉴 10종 v/e/f·면 크기 = Maya 표, 실린더 캡 = 중심 팬(n-gon 없음, 림 40 sharp),
  변형 32종 카운트 = Maya, NURBS 8종 CV 격자·cyclic·order, Maya 원 CV 반지름 1.108194, INPUTS 행 + Subdivisions Caps 2 → 82 v
  (위치·재질·이름 유지), 상대 입력 `-=14`, `*=2`, AE 탭, NURBS 원 Radius/Sections/Sweep/Degree 재생성, 곡면 Spans·사각형 Spans Per Side
  재생성, 다중 선택, 편집/Delete History 로 노드 사라짐, 편집 모드에서 재생성, Duplicate 노드 없음.
- 측정 대조 `research/scripts/maya_prims129/compare.py`: 161 경우 중 151 일치(점 위치·면 방향·메뉴 UV·CV). 남은 10 = 맨 명령의
  축 X / 법선 Z 로 만든 NURBS(메뉴는 항상 +Y) 와 polyDisc Circle 모드 내부 점(최악 0.116, Coons 패치 근사).
- 기존 테스트 기대값 갱신: step10 실린더 면 22 → 60, step103 옵션 창 실린더 82 → 120 면, step109 NURBS 큐브 패치 위치(오브젝트 위치 → CV).
- 헤드리스 전체 / GUI: 「결과」.

## bisect

(아래 채움)

## 결과

(아래 채움)

## 남은 것

- polyDisc Circle 모드 내부 점은 근사(경계·스포크 정확). 플라토닉·디스크 UV 는 Maya 배치가 아님(구면/평면 투영).
- 축이 +Y 가 아닌 NURBS(맨 명령 기본 축 X)는 축 둘레 시작 각/패치 이름이 Maya 와 다를 수 있음(모양 집합은 같음 — 사각형/큐브 제외).
- 하드 엣지 규칙은 근사(spec §2.10).
- Maya 는 생성 뒤 버텍스 편집을 tweak 으로 보존하고 히스토리를 유지; kit 는 편집하면 노드를 숨김(재생성 시 편집을 잃지 않도록).
- Pipe / Helix / Gear / Soccer Ball / Super Ellipse / Spherical Harmonics / Ultra Shape 는 여전히 메뉴 notice(측정 카운트만 spec 에).
- CV / EP / Bezier 커브 툴은 생성 노드가 없음(Maya 도 makeNurbCircle 같은 노드 없음).
