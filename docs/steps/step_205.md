# Step 205 — Deform 2 (backlog #4, Issue #112)

## 계획

근거: `docs/steps/step_201_remaining.md` §8 #2 (G1), `research/maya/re/deform_169.md` · `options_144.md`. Deform 48 / 74 → 목표 ≥ 55.
회색 Deform 26 중 이번 대상 (delegated): Tension (+ Paint Weights > Tension), Solidify, Morph, Jiggle > Jiggle Deformer (+ Paint Weights >
Jiggle), Sculpt (+ Prune Membership > Sculpt), Display / Hide Intermediate Objects, Wrap#2 Add / Remove Influence; Constrain > UV Pin /
Proximity Pin. 각 디포머 = Maya 이름 (`tension1` …), INPUTS 행, AE 탭, 옵션 창 (Maya 공장값), Delete Non-Deformer History 에서 남음
(`history.is_deformer`), 자기 vertex group (Paint Weights, step 144 규칙). 남김: Wrinkle, Muscle, Pose Space Deformation, Jiggle Disk Cache,
Add Tweak, Blend Shape#2 / ShrinkWrap#2 / Wire#2 하위 항목, Edit Membership Tool, Proximity Wrap.

레인 (레인 ≤ 4, Blender ≤ 2 = `blender_slots`, Maya ≤ 1):
- 1 차: **M** (Maya 만) mayapy 로 각 디포머 / pin 의 공장값 · 단순 메시 결과 → `research/maya/re/deform_205.md` + `tests/maya205_deform_data.py`.
  **P** (Blender) UV Pin / Proximity Pin + Display / Hide Intermediate Objects + Wrap Add / Remove Influence 를 [K] 로 (`operators/pins_205.py`,
  기존 `deformers.py` 손대지 않음). 
- 2 차 (M 데이터 뒤): **A** Tension · Solidify · Sculpt (`operators/deformers_205a.py`), **B** Morph · Jiggle (`operators/deformers_205b.py`),
  메인 = P 를 측정에 맞춤, 메뉴 · notices 합치기, GUI. 순서 이유: 디포머 수식이 측정 데이터에 기댐.

진행 메모: 1 차 M (측정) + P ([K] pins) → WIP 56b6021; 2 차 A (Tension · Solidify · Sculpt) + B (Morph · Jiggle) + C (pins 를 측정에 맞춤) 동시 →
WIP 254df6c; 메인 = 메뉴 · notices · 옵션 창 · AE 연결, GUI.

## 한 일

- **측정** (레인 M, mayapy 123 경우): `research/maya/re/deform_205.md` / `.json`, `tests/maya205_deform_data.py`, 순수 Python 모델
  `research/scripts/deform_205/*_model.py` (Maya 와 2.5e-7).
- **Tension / Solidify / Sculpt** (`operators/deformers_205a.py`, GN 모디파이어): Tension = Repeat zone 의 Jacobi 반복 (짝 표는 hidden INT
  속성, rest = 생성 시 위치), Sculpt = `sculptor1` 구 Empty + `sculpt1StretchOrigin`, Solidify = 멤버 영역의 강체 맞춤 (polar 분해, 측정 [U]
  부분은 delegated). Prune Membership > Sculpt = `allset.prune_sculpt`.
- **Morph / Jiggle** (`operators/deformers_205b.py`, GN): Morph 5 모드 · Object/World · mirror, Maya Orig = 숨은 helper (`morph1Rest`),
  Jiggle = Simulation zone 의 Maya 스프링 규칙 (world space, Ignore Transform = object space).
- **UV Pin / Proximity Pin** (`operators/pins_205.py`): helper empty + 핸들러, Copy Transforms (Before Original) = Maya offsetParentMatrix,
  측정 규칙 (bilinear quad, Maya 정점 노멀, 첫 삼각형 dP/du 탄젠트, Proximity = 원본 메시 최근접점 매 평가). Display / Hide Intermediate
  Objects (`<shape>Orig`), Wrap#2 Add / Remove Influence.
- 각 디포머: Maya 이름, 자기 vertex group (Paint Weights), Channel Box INPUTS 행, AE 탭 (`draw_ae`), Maya 공장값 옵션 창, Delete
  Non-Deformer History 에서 남음 (`history.is_deformer` = `deformers.base_of` 로 킷 GN 디포머 전부), 되돌리기 한 단계.
- 메인 연결: `ui/menu_map.py` (문자 그대로 — menu_count 는 bpy 없이 읽음), notices 5 + Paint Weights 정리, `option_windows._extend` 에 세
  모듈 windows, Paint Weights > Tension 창 (Paint Attributes Tool), AE 연결. GUI 에서 메뉴가 `kind="tension"` 을 넘겨 enum ('TENSION')
  과 안 맞던 것 고침 + 재발 막는 `tests/test_step205_menu.py` (메뉴 항목 = 모듈 MENU, enum 값 검사).

## 검증

- mayapy 대조 (1e-4): Tension 31 / 31 (1.3e-6), Sculpt 7 / 7, Morph 23 / 23 · Jiggle 12 / 12 (1.5e-6), pins 16 / 16 (2.3e-6); Solidify 는 [U]
  라 측정된 사실만 (Borders 전체 = 움직임 없음, Full 강체, envelope 선형).
- 헤드리스 전체 **1964 / 1964** (238 파일). GUI: 새 `gui_step205_deform` (메뉴로 Tension / Sculpt, AE 에 tension1 탭, sculptor1 선택) +
  step144 / step169 / 스위치 / 레이아웃 44 / 44, AE 샷 직접 봄.
- 메뉴: Deform 48 → **60 / 74**, Constrain 16 → 18 / 20, 전체 세트 합 922 / 1486 (62.0 %), `menu_consistency` 0.

## 남은 것

- [U]: Solidify 회전 규칙 (잔차 최대 0.13), Sculpt 를 원점 밖으로 옮긴 Stretch (가장 흔한 쓰임, ~1.3 차이), Morph 구 Retarget / neighbor
  level, Jiggle weight < 1 · Direction Bias · only-after-stops.
- 남은 회색 Deform 14: Wrinkle, Muscle, Pose Space Deformation, Jiggle Disk Cache 2, Add Tweak, Blend Shape#2 3, Proximity Wrap#2,
  ShrinkWrap#2 2, Wire#2 Add Holder, Edit Membership Tool.
- Proximity Pin 창의 Tangent None / UV set / Normalize isoparms / Output Matrix 칸, Wrap 여러 influence 의 거리 혼합 (킷은 가장 가까운 하나).
- Jiggle 은 Maya 처럼 jiggle1Cache 를 선택하지 않고 변형된 오브젝트를 선택 (cache = Blender simulation cache).
