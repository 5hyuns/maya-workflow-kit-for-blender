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
- L17: `reorderDeformers A B` puts A right after B (output side) — measured later: by moving B (see 한 것).

## 한 것

- **Lane P (A1 A2 A5 A6, sub-agent)** — Flood = Maya 2026 formulas in plain data writes (`weight_paint.flood`):
  Replace / Add / Scale / Smooth (Smooth = the vertex + its edge neighbours averaged, `w + o(avg − w)`, Value ignored —
  Blender's `vertex_group_smooth` leaves the vertex out, so the kit smooths itself), the change goes to the unlocked
  other influences in their old ratio, locks kept, the selected vertices only when any is selected (mask on or off),
  one undo step; Alt+F = kit flood. Influences RMB = Maya's 7 items in Maya's order (`paint_weights.MAYA_RMB`; Select /
  Add / Remove Affected Vertices = weight > 0, vertex mask on; nothing picked → "Please select an influence first"),
  kit extras below a separator, sort Alphabetically (natural) / By Hierarchy / Flat. Keys: Ctrl+Alt+C / V copy / paste
  vertex weights, Ctrl+. / Ctrl+, cycle Paint → Select → Paint Select, Alt+R X reflection; Shift+B notice only (no
  lower radius in Blender). Entry with some vertices selected turns the vertex mask on; Mode row + Select Geometry.
  Delegated: "picked" influence = the active list row only; Select = box select + mask, Paint Select = circle select +
  mask.
- **Lane C (L6 L7, sub-agent)** — `rig_maya.create_spline_ik(..., curve, root_on_curve, snap_curve, parent_curve,
  spans)` with the Maya 2026 Tool Settings / option window (Auto create curve, Root on curve, Auto parent curve, Snap
  curve to root, Number of spans), click tool root → end → curve; Cluster on curve / surface / lattice points = Hook on
  exactly the selected CV indices, pivot = their centre (object mode = all CVs).
  **Root on curve off (delegated, Blender limit)**: Maya keeps the root and walks the joints along the curve; Blender's
  Spline IK has no start parameter, so the kit uses Chain Offset (root and bone lengths kept, shape 1.35 units off).
- **Lane D (L17 L15b, main)** — `operators/deformer_order.py`: Maya `reorderDeformers A B` = **B moves to directly
  before A** (mayapy `research/scripts/maya_bs218/reorder218.json`: evaluation c1 c2 c3 → (c3, c1) c2 c1 c3, (c1, c3)
  c3 c1 c2, (c1, c2) c2 c1 c3, (c2, c1) "already in the specified order" warning) on the modifier stack (smooth preview
  stays last); All Inputs list rows get ▲ / ▼ (Maya MMB drag). New deformers already land at the end (Maya Default) and
  blend shapes are shape keys, evaluated first (= Maya automatic, before the skin) — tested. L15b: Maya 2026 keyed
  **nothing** in 13 selection states (mayapy + GUI Maya with the Shape Editor, `research/maya/re/maya2026_deform.md`
  「L15b 재측정」); kit `allset.key_blend_shape_weights` keys the selected objects' shape key Values (delegated, the
  menu name's meaning), empty selection = Maya's "No shape was selected.".

Lanes P and C ran as parallel sub-agents (WIP commit 29b775c); lane D in the main session at the same time was not
possible (foreground agents block the main loop), so it ran after them.

## 검증

- Flood vs Maya (12 cases, every sampled vertex × 3 joints): max |kit − formula| ≤ 4.2e-8, max |kit − Maya| ≤ 1.9e-6
  (json has 6 decimals); changed-vertex counts equal Maya's (180 / 20).
- Spline IK: Root on curve 7.0e-5, Snap curve 7.0e-5 (cv0 exactly at the root); cluster tip after handle x+2 2.5e-5,
  after control z+3 2.9e-5; Root on curve off 1.35 (see above, not asserted).
- Headless: lane P 185 / 185 (18 files), lane C 168 / 168 (13 files) + 50 / 50, `test_step218_deform_order` 7 / 7;
  full suite 2176 / 2177 — the one failure was `test_step107_keys` still expecting Blender's Alt+F (updated; 13 / 13).
- GUI: lane P `-k paint,skin,deform,weight` 35 / 35 (new `gui_step218_paint` 10 checks); final run related + smoke
  (paint, skin, deform, weight, step60 / 129 switch, step49 layout, step3) 84 / 84.

## 남은 것

- Root on curve off shape (Blender Spline IK has no start offset along the curve).
- Deformer option windows' Deformation order (Before / After / Split / Parallel / Front of chain) not offered.
- Right-click on an Influences list row shows Blender's own rows above Maya's 7 (Python can't reorder; the menu button
  next to the search field shows Maya's first).
- What Maya's Set Blend Shape Target Weight Keys really needs stays [U].
- Manual checks 「Step 218」.
