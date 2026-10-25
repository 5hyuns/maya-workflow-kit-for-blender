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
