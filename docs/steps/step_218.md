# Step 218 — Anim chain fixes 2: paint shortcuts, Spline IK, curve clusters, deformer order (Issue #129)

Basis: `docs/strategy/ATTACH_PLAN.md` rows A1, A2, A5, A6 (Issue #126 small part), L6, L7, L15b, L17;
Maya 2026 specs `research/maya/re/maya2026_paint_skin_weights.md`, `maya2026_curve_rigs.md`, `maya2026_deform.md`.

## 계획

| Lane | Items | Files | Who |
|---|---|---|---|
| P paint | A1 Influences RMB 7 items (Maya labels) + natural Alphabetical sort; A2 Flood = Maya formulas, redistribution, locks, selected-vertex limit, Alt+F; A5 paint keys (Alt+F, Ctrl+Alt+C/V, Ctrl+. / Ctrl+,, Alt+R); A6 vertex selection on entry → mask on, Mode Paint / Select / Paint Select | `operators/weight_paint.py`, `ui/paint_weights.py`, `keymap/maya_patches.py`, `keymap/mapping.py`, `tests/test_step218_paint.py` | sub-agent |
| C curve rig | L6 Spline IK on an existing curve (Auto create curve off, Root on curve, Snap curve to root, Auto parent curve); L7 Cluster on curve CVs = Hook on the CV indices, pivot = CV centre | `operators/rig_maya.py`, `operators/option_windows_rig.py`, `tests/test_step218_curve_rig.py` | sub-agent |
| D deformer order + L15b | L17 new Blend Shape before the skin (shape keys are always first = Maya automatic), Cluster / others at the end (= Default), All Inputs list move up / down = `reorderDeformers A B` (A after B) on the modifier stack; L15b measured in GUI Maya 2026 first | `marking/rmb_nodes.py`, `ui/notices.py` (L15b row), menu row, `tests/test_step218_deform_order.py` | main |

The lanes touch different files; `menu_map.py` rows are added only by lane D / C at different lines. Blender
processes ≤ 2 (tools/blender_slots.py); one Maya.

Rules taken from the specs (numbers are the test oracles):
- Flood (paint spec §4): Replace w' = w + o(v − w); Add w' = min(1, w + o·v); Scale w' = w(1 − o(1 − v)); Smooth =
  one neighbour-average step × o, Value ignored; the change goes to the unlocked other influences in their old
  ratio; locked influences keep their weight; selected vertices only when any is selected; one undo step.
- L6: Root on curve (default) moves the root to the curve start and keeps bone lengths; Snap curve to root moves the
  curve's first CV to the root; Root on curve off keeps the root, the chain follows the curve shape.
- L7: CVs cv[3:4] → handle pivot = CV centre (0.5, 7, 0) Maya = Blender (0.5, 0, 7); handle x+2 → cv3 x+2.
- L17: `reorderDeformers A B` puts A right after B (output side).
