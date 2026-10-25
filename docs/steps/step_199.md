# Step 199 — Skin and Constrain tools 2 (backlog #7, Issue #106)

## 계획

Targets: Skin 19 → ≥ 24 / 28, Constrain 11 → ≥ 16 / 20 (tools/menu_count.py), each command matched to mayapy within
1e-5. Two independent lanes (own files, own mayapy measurement, git worktrees), main line = registration stubs,
menu maps, notices, option windows wiring, docs:

- **S (agent)** `operators/skin_tools_199.py`: Skin > Move Weights to Influences, Bake Deformation to Skin Weights...,
  Normalize Weights > Enable Weight Post Normalization, Export Weight Maps... / Import Weights Maps..., Substitute
  Geometry. Spec `research/maya/re/skin_tools_199.md`. Tests `tests/test_step199_skin.py`.
- **C (agent)** `operators/constrain_199.py`: Constrain > Normal, Tangent (Blender constraint combinations matched to
  mayapy), Remove Target, Set Rest Position, Modify Constrained Axis.... Spec `research/maya/re/constrain_199.md`. Tests
  `tests/test_step199_constrain.py`.

Order: stubs first (so lanes never edit `operators/__init__.py`), menu wiring after the lanes (needs their ids).

## 한 것

- **Lane S** (`operators/skin_tools_199.py`, spec `research/maya/re/skin_tools_199.md`, mayapy probes
  `research/scripts/skin_tools_199_mayapy_*.py`): Skin > Move Weights to Influences (`allset.move_skin_weights`:
  first joint = source, every unlocked target *set* to the source weight, Interactive rescales — mayapy 1e-6),
  Normalize Weights Disable / Enable / Enable Post (`allset.skin_normalize_mode`: Maya None / Interactive deform by
  Σw·M·p, Post divides by Σw = Blender's Armature; None / Interactive get a hidden Geometry Nodes `<skin>WeightSum`
  modifier after the Armature — all three within 1e-5 of Maya), Export / Import Weight Maps (`.weightMap` file + one
  image per influence, PNG default — pixel parity with Maya not measurable in mayapy), Substitute Geometry (distance 0
  exact; distance 1 interior < 5e-5, outer quads up to 9e-4 [U]), Bake Deformation to Skin Weights (per-vertex
  non-negative least squares over a ±45° X/Y/Z range of motion; pure skin source within 1e-5; skin + cluster
  half-weight members differ [U]).
- **Lane C** (`operators/constrain_199.py`, spec `research/maya/re/constrain_199.md`): Constrain > Normal / Tangent (a
  Track To on a hidden helper moved in double precision from Maya's angle × area weighted normals / exact NURBS
  tangents — mayapy ≤ 3e-7, 6e-6 near a sphere pole), Remove Target, Set Rest Position, Modify Constrained Axis...
  (all within 1e-6). Delegated choices listed in the spec (parent keeps its offset, X/Y/Z = Channel Box axes, Set Rest
  Position writes the own channels, aim axes can't be skipped).
- **Main line**: menu map (Skin 6 + normalize radio as one operator, Constrain 5), stale notices removed, option
  windows `operators/option_windows_199.py` (Normal / Tangent / Remove Target / Modify Constrained Axis / Substitute
  Geometry, MayaStrings titles, MEL factory values), Channel Box / AE / RMB node names `normalConstraint` /
  `tangentConstraint` with the surface as `<surface>W0` (`channel_box.maya_constraint_type`), the weight-sum helper
  hidden from INPUTS and AE tabs.

## 검증

- Headless: `test_step199_skin` 15, `test_step199_constrain` 19, `test_step199_menu` 3 (mayapy numbers per command);
  full **1841 / 1841** (updated old expectations in test_step159_menus, test_step125_name hidden marker).
- GUI: `step11_outliner_ae, step140_option, step148_cb, step55_pose, step58_skin, step62_sdk` + smoke 100 / 100.
- `tools/menu_count.py`: Skin **25 / 28** (was 19), Constrain **16 / 20** (was 11); unique 762 / 1318 (57.8 %);
  `menu_consistency` 0.

## 남은 것

- Skin: Interactive Bind Skin / Tool (volume capsules), Move Skinned Joints. Constrain: UV Pin, Proximity Pin, Flow
  Path Object, Set Motion Path Key.
- Weight-map pixel values vs Maya, Substitute Geometry distance rule, Bake with half-weight cluster members [U].
- Normal / Tangent helpers update after evaluation: an F12 animation render can lag one frame for animated objects;
  helper empties are listed in Blender's Outliner (hidden).
