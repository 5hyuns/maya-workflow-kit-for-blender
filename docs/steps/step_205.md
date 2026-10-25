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
