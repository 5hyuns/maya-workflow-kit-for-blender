# Step 168 — Modify menu and Smooth Mesh Preview to Polygons

Backlog `backlog_164.json` #5 (재점검 11차: `step_163_quant.md` §6 #2 Modify 41 % / 53 greyed, `step_163_remaining.md`
§4 BS3 Smooth Mesh Preview to Polygons = `object.convert`, bakes every modifier incl. skinCluster).

## 계획

Lanes: (A) mayapy measurement → `research/maya/re/modify_168.md`, (B) kit module + option window, (C) menu map /
notices, (D) tests. B–D need A's rules (warning texts, enum values, which history stays), so A ran first; B–D are
small and touch shared files (`menu_map.py`, `notices.py`, `operators/__init__.py`), so they ran in one lane
(delegated: a second lane would have edited the same files).

Count target: Modify 90 leaves, 60 % = 54 working. Backlog's cheap list = Default Object Manipulator 5, Align Tool,
Position Along Curve, Geometry to Bounding Box, Evaluate Nodes IK Solvers / Constraints / Ignore All = 11 → 48
(53 %): not enough, so every Evaluate Nodes item with a Blender counterpart (Expressions = drivers, Fluids, nCloths,
nParticles, nRigids, Particles, Rigid Bodies) and Show Manipulator Tool (uses the Default Object Manipulator) were
added (delegated) → 56 (62 %).

## 한 것

- **Smooth Mesh Preview to Polygons** = `allset.smooth_to_polygons` (`operators/modify_maya.py`): applies only the
  kit preview modifiers ("Maya Smooth Preview Shading" nodes, then the "Maya Smooth Preview" Subsurf) with
  `object.modifier_apply` at their place; Armature (skinCluster1), kit deformers and history modifiers stay. Meshes
  without a shown preview are skipped; Maya's warnings "No polygonal objects selected were in smooth preview mode." /
  "No polygonal objects selected."; display mode 2's cage wireframe goes off. Edit mode: leaves and comes back.
  Blender applies a non-first modifier to the base mesh and carries vertex groups through the Subsurf, so the skin
  deforms the dense mesh (Maya: `polySmoothFace1` after `skinCluster1`; same at bind pose, `modify_168.md` §1).
  Shared mesh data / shape keys: a warning, that object stays.
- **Default Object Manipulator** None / Move / Rotate / Scale / Transform = `allset.default_manip(value)` → object ID
  prop `allset_manip_default` (Maya `showManipDefault` 0–4, warning "No objects selected."); **Show Manipulator
  Tool** = `allset.show_manipulator` (v3d): the lead's value picks the tool, None = Transform (the kit's T).
- **Align Tool** = `allset.align_tool`: popup with X / Y / Z × Min / Mid / Max (`allset.align_to_lead`: the selection
  lines up with the last selected object's world bounding box). Maya draws icons on the bounding box; Blender
  gets a popup (delegated, notice in the tooltip).
- **Position Along Curve** = `allset.position_along_curve`: Maya's rule (curve = last selected curve, others at the
  parameter percentage i / (n − 1), pivot onto the point; Maya's two error texts). Selection order = name order with
  the active last (Blender keeps none; like `curve_tools._curves`). mayapy-exact on the measured 4-CV curve.
- **Geometry to Bounding Box** = `allset.geometry_to_bbox` + option window "Convert Geometry to Bounding Box Options"
  (`operators/option_windows_modify.py`: Name, Name suffix `_BBox`, Represent hierarchy as One bounding box / One per
  shape, Color 0.5 grey, Keep original; Combine / Bake Animation listed as not in Blender; button Convert). Lone mesh
  = object-space box with its transform, hierarchy = world box with identity, material `BBoxLambertN`, original
  (with hierarchy) deleted unless Keep original, new boxes selected.
- **Evaluate Nodes**: `Scene.allset_eval` (PropertyGroup, saved with the file) drawn as Maya check items through the
  menu `("prop", ...)` kind; IK Solvers = IK / Spline IK constraints muted (on again unmutes only those the kit
  muted: Maya's global solve leaves per-handle solverEnable alone), Constraints = every other constraint `mute`
  (on = all unmuted, like Maya's nodeState 0 for all), Expressions = drivers muted except kit Set Driven Key drivers,
  Fluids / nCloths / Particles / nParticles = modifier visibility (kit particle settings `nParticleN` =
  nParticles), nRigids = `collision.use`, Rigid Bodies = scene rigid body world; Evaluate All / Ignore All =
  `allset.evaluate_all(on)`. Dynamic Constraints, nucleuses, Global Stitch, Snapshots stay greyed with notices.
- Notices: `Modify/Transformation Tools` and `Modify/Evaluate Nodes` category texts no longer claim Default Object
  Manipulator / every item is missing; mapped-item notices for the items that differ from Maya.

## 검증

- `research/maya/re/modify_168.md` (mayapy: preview levels 1 / 2 / 3 = × 4^level, skinned mesh keeps skinCluster1
  after the smooth node, warnings, showManipDefault enum, setState rules, geomToBBox results, positionAlongCurve
  numbers).
- `tests/test_step168_modify.py` 12 / 12: skinned mesh keeps `skinCluster1`, faces × 4² and still deforms when
  posed; levels 1 / 3, history modifier stays, mode 2; warnings; Default Object Manipulator; Align Tool; Position
  Along Curve (0 / 1.75 / 6 like mayapy); Geometry to Bounding Box single / hierarchy / per shape / keep + option
  window; Evaluate Nodes switches and menu items; **Modify 56 / 90 = 62 %** (was 37 / 90 = 41 %).
- `python tools/menu_count.py --options`: window 86 (Geometry to Bounding Box dead → window), Modify row window 2 →
  3, dead 17 → 16, tool / redo / generic unchanged — no Modify box lost its window.
- Headless full: see 「결과」 below. GUI: `tests/gui/gui_step168_modify.py`.

## 결과

- Headless full: 1565 / 1566 on the first run — `test_step101_menu_honesty::test_category_rules_all_used` (the
  `Modify/Evaluate Nodes` category rule was no longer used: every greyed Evaluate Nodes item has its own notice) →
  rule removed, step101 + step168 26 / 26; total **1566 / 1566** (167: 1554 + 12 new).
- GUI: `gui_step168_modify` 6 / 6 + `gui_step101_menus`, `gui_step103_option_windows` (14 / 14 together). Screenshots
  checked: Evaluate Nodes submenu = Maya's check items (Constraints unticked after switching it off; Global Stitch /
  Dynamic Constraints / nucleuses / Snapshots greyed), Align Tool popup X / Y / Z × Min / Mid / Max over two cubes.
- Menus: Modify 37 → **56 / 90 (62 %)**; unique paths 674 / 1318 (51.1 %); option boxes window 86, Modify dead 17 → 16.

## 남은 것

- Geometry to Bounding Box: Combine resulting bounding boxes and Bake Animation (Maya bakes the box per frame) are
  not done; mayapy left the original in place without Keep original (namespace `BBoxNS`), the GUI behaviour is [U]
  — the kit deletes it.
- Smooth Mesh Preview to Polygons on a posed skinned mesh: Blender's result is skin(smooth(base)) vs Maya's
  smooth(skin(base)) — equal at bind pose only.
- Still greyed in Modify (34): Type Manipulator, Evaluate Nodes Dynamic Constraints / nucleuses / Global Stitch /
  Snapshots, Paint Scripts / Attributes Tool, Asset (15), Convert subdiv / Paint Effects / displacement / fluid /
  nParticle conversions (12).
