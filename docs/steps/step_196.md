# Step 196 — Maya option windows for primitives and character sets (backlog.json #4, Issue #103)

## 계획

문제 (재점검 14차 A NB3 / B #3): 옵션 상자 중 Maya 는 창을 여는데 kit 은 Blender Adjust Last Operation (redo) 이나 일반 상자
(generic) 를 여는 것 — Polygon Primitives 11 (Disc, Platonic Solid, Pyramid, Prism, Pipe, Helix, Gear, Soccer Ball, Super Ellipse,
Spherical Harmonics, Ultra Shape), NURBS Primitives 8, Create (Sub)Character Set (Control / Key 4 경로), Curves Cut / Detach /
Reverse Direction / Smooth (#2) / Straighten, Two / Three Point Circular Arc, UV Merge UVs / Contour Stretch, Skeleton Set / Assume
Preferred Angle, Skin Add Influence. 측정 시작점: `tmp/q196/results/option_kinds.json` — window 120, redo 127, generic 34.

레인 (포그라운드 에이전트 2 개 동시, 파일 단위로 나눔; delegated):
- **A — 프리미티브 창 19 개** → `src/allset/operators/option_windows_prims.py` + `research/maya/re/options_196_prims.md` (+ json) +
  `tests/test_step196_prim_windows.py`. 필드 · 라벨 · 공장 기본값은 Maya 2022 의 옵션 창 MEL (설치 폴더 scripts, 읽기만) + mayapy 로
  optionVar 기본값 확인; 창은 `create.create(context, kind, overrides=<Maya 노드 속성>)` 로 만든다 (step 103 / 129 / 190 의 노드).
- **B — 나머지 창 ~12 개** (Character Set 4 경로, Curves 5 + 2 arc, Merge UVs, Contour Stretch, Preferred Angle 2, Add Influence) →
  `src/allset/operators/option_windows_misc196.py` + `research/maya/re/options_196_misc.md` + `tests/test_step196_misc_windows.py`.
- **메인**: `option_windows._extend()` 에 두 모듈 연결, option_count 재측정 (window ≥ 135), GUI 샷 두 창, 헤드리스 전체, 문서 · 커밋.
  순서: 레인 → 메인 (합치기는 두 파일이 있어야 함).

## 한 일

- 레인 A (`src/allset/operators/option_windows_prims.py`, 근거 `research/maya/re/options_196_prims.md` / `.json`, mayapy 스크립트
  `research/scripts/maya_prims196/`): Polygon Primitives 11 (Disc, Platonic — Maya 메뉴가 부르는 `performPolyPlatonic` 창, Pyramid, Prism,
  Pipe, Helix, Gear, Soccer Ball, Super Ellipse / Spherical Harmonics / Ultra Shape = Maya 의 한 창 "Polygon Super Shape Options" 41 필드,
  Shape 필드 기본값 = 그 메뉴 항목) + NURBS Primitives 8 (Sphere, Cube, Cylinder, Cone, Plane, Torus, Circle, Square). 버튼 "Create",
  필드 = Maya 노드 속성 (`create.create(overrides=...)`), 공장 기본값 = mayapy optionVar (MEL setOptionVars 와 같음). 못 하는 필드
  (`missing`): Normalize / Preserve aspect ratio, Super Shape "Pinched at pole", NURBS Active view / tolerance / caps / degree 2·5·7.
- 레인 B (`src/allset/operators/option_windows_misc196.py`, 근거 `research/maya/re/options_196_misc.md` / `.json`): Create Character Set /
  Subcharacter Set (Control · Key 두 메뉴), Cut Curve, Detach Curves, Reverse Curve, Smooth Curves (+ nHair 쌍둥이), Smooth Curve (#2),
  Straighten Curves (+ nHair), Three / Two Point Circular Arc, Merge UVs, Contour Stretch Mapping, Set / Assume Preferred Angle, Add
  Influence = 15 창. 연산자 속성 추가 (`SKIP_SAVE`, REGISTER 인 것은 숨김): `character_create` (이름 · 속성 범위 · 제외 · hierarchy),
  `curve_cut` (last_only, keep_longest), `curve_straighten` (straightness, preserve_length), 새 `allset.curve_smooth_curves(factor)`,
  arc 도구 degree / sections, 새 `allset.uv_merge(distance)` (같은 정점의 UV 를 거리 안에서 평균으로 — Maya polyMergeUV),
  preferred angle hierarchy, `add_influence` (lock_weights, default_weight). 수학은 `curves_math.py` (straighten, smooth_cvs, cut 옵션).
- 메인: `option_windows._extend()` 에 두 모듈; 그냥 클릭도 Maya 규칙으로 (delegated) — Curves > Smooth = `allset.curve_smooth_curves`,
  UV > Merge UVs · UV Editor Cut/Sew > Merge · UV 마킹 메뉴 Merge UVs = `allset.uv_merge` (전에는 Blender `curve.smooth` / `uv.weld`:
  모든 선택 UV 를 한 점으로); `test_step147_undo` 의 redo 예 = Create > Lights > Point Light (NURBS Circle 은 이제 창).
- GUI 테스트 `tests/gui/gui_step196_option_windows.py` (Gear · Create Character Set 상자 → Maya 창, 샷).

## 검증

- option_count (`ALLSET_SANDBOX=q196b ... -k step140_option_count`): window 경로 **120 → 158**, redo 127 → 104, generic 34 → 19 (dialog 22,
  tool 10, dead 193 그대로).
- 새 헤드리스: `test_step196_prim_windows` 7 / 7 (기본값 = Maya json, 기본값 실행 = 그냥 만들기, 바꾼 필드가 노드 · 형상에, NURBS 는
  SURFACE / CURVE, Maya 단위), `test_step196_misc_windows` 17 / 17. 관련 묶음 (`-k step196,step147,step140,step8_,step166,step101,step54,
  step156,step155,step187,step110,step66`) 172 / 172.
- 헤드리스 전체 4.5: 1763 / 1764 — 실패 1 = `test_step103_option_windows` (arc 창 제목이 "Options" 로 안 끝남) → 제목을 Maya Tool Settings
  이름 "Three / Two Point Arc Settings" 로, 테스트가 그 꼴을 받게 고친 뒤 그 파일 + step196 **34 / 34**.
- GUI: 새 `gui_step196_option_windows` 3 / 3 (UI 1.0 샷: Polygon Gear Options 11 필드, Create Character Set Options + "Create Character
  Set" 버튼 — 직접 봄), `step103` 함께 통과; 바뀐 모듈 `-k step156,step187,step155,step178,step110` 56 / 56, `step66_uv` 6 / 6.

## 남은 것

- `missing` 필드 (Normalize / Preserve aspect ratio, NURBS tolerance · caps · degree 2/5/7, Super Shape Pinched, Cut 방향 · 허용치,
  Keep original (Cut / Detach), Smooth#2 Smoothness, Contour Stretch 필드 전부, Add Influence 의 geometry / dropoff / samples, Redirection).
- Add Influence: mayapy 로 보니 Maya 공장 설정은 새 joint 근처에 거리 가중치를 줌 — `modeling_rigging_110.md:65` ("어디나 0") 와 다름.
  kit 은 아직 0 (Lock weights + Default weight 는 Maya 와 같음) → step 199 (Skin and Constrain 2) 에서.
- redo 104 / generic 19 / dead 193 남음 (조명 4, 라이트 · 필드 · nParticles 등).
