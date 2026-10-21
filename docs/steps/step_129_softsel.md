# Step 129 (soft select lane) — one Maya soft select state, B + MMB radius drag, falloff colour overlay

Issues: #1 (B hold + MMB drag does nothing; "on by default"), #2 (no falloff colours), #15 (object / component
soft select are two Blender flags). User request: Maya mode starts with soft select off, B toggles, B hold + MMB
drag left / right sets the radius (circle + value on screen, Maya sensitivity); with soft select on, the affected
vertices show Maya's falloff ramp (yellow → red → black) as a GPU overlay that uses the same radius and curve as
the transform, fast on dense meshes.

## 계획

### 0. Maya facts (measured this step)

- mayapy, factory prefs (`tmp/maya129/q.py`): `softSelect -q`: `sse 0` (off), `ssd 5.0`, `ssf 0` (Volume),
  `softSelectCurve "0,1,2,1,0,2"` (value 1 at 0 → 0 at 1, interp 2 = smooth = Blender SMOOTH 3t²−2t³),
  **`softSelectColorCurve "1,1,0,1,1, 1,0,0,0.5,1, 0,0,0,0,1"`** = (r,g,b,position,interp) keys:
  weight 1 → yellow (1,1,0), 0.5 → red (1,0,0), 0 → black (0,0,0), linear; `enableFalseColor 1`.
- Maya GUI (`tmp/maya129/scripts/softsel.py`, shot `softsel_00_on.png`): the falloff colours are drawn on the
  **wireframe** (edges coloured by the end weights, yellow at the selection, red, black at the radius) and the
  vertices. While B + drag runs, the Help Line reads `Falloff Radius: 5` (`softsel_01_dragging.png`).
- B + drag sensitivity: **not measured** — QTest drags into the GL viewport don't reach Maya's screen slider
  (`ssd` read 0.0 after every synthetic drag, with and without moving the OS cursor). The kit keeps step 3's
  law (radius × 2 per 100 px right, ÷ 2 per 100 px left: relative, so it feels the same at every scale) and
  records it as [K] (delegated).

### 1. One state (#15, #1 "default off")

`operators/soft_select.py`: `STATE["on"]` (module, Maya's global `softSelect -sse`; starts False = Maya factory).
Blender has two per-scene flags (`use_proportional_edit_objects` object mode, `use_proportional_edit` edit /
UV); the kit keeps **both flags of every scene equal to the state**:
- `set_on(value)` writes the state and pushes it into both flags of every scene (turning on also applies Maya's
  radius 5 × maya_unit when Blender's radius is untouched, step 63).
- `pull(scene)`: a flag that differs from the state was changed by Blender UI (header button, `wm.context_toggle`
  menu item, UV toolkit) → the state flips and is pushed. Called from `depsgraph_update_post` and from a msgbus
  subscription on both ToolSettings props (re-made in load_post; msgbus is cleared by file loads).
- `load_post` / `undo_post` / `redo_post` push (re-baseline): a file saved with soft select on, or an undo past
  the toggle, follows the global state (Maya keeps it as a global option, not in the scene).
- register pushes the state from a 0 s timer (Maya mode starts off; bpy.data is restricted during register).
- B tap = `pull` then `set_on(not on)`. MTK / Tool Settings checkbox = `Scene.allset_soft_select` (get/set
  the state).

### 2. B + MMB drag (#1)

`TapHoldBinding.buttons` (default `{'LEFTMOUSE'}`); `SoftSelectBinding.buttons = {'LEFTMOUSE', 'MIDDLEMOUSE'}`.
The tap/hold modal starts a drag on a PRESS of any of its buttons, remembers it, ends on that button's RELEASE;
the MMB press is consumed (RUNNING_MODAL), so the 3D View orbit never starts. While dragging, `ui/soft_overlay`
draws (POST_PIXEL) a circle of the radius around the soft select centre (selected vertices' mean in edit mode,
the active object's origin in object mode, else the press point; radius = world radius projected at that depth)
and `Falloff Radius: <maya units>` next to the mouse; the header text stays.

### 3. Falloff colours (#2)

Weights = Blender's transform rule so the colours match what G / R / S do:
- distance (`transform_convert`'s `set_prop_dist` / `editmesh_set_connectivity_distance`): selected = 0;
  Volume (connected off) = nearest selected vertex in world space, with Projected = only the part in the view
  plane; Surface (connected) = shortest path along the edges (and straight across faces).
- `calculatePropRatio`: d > r → 0; t = (r − d) / r; SHARP t², SMOOTH 3t²−2t³, ROOT √t, LINEAR t, CONSTANT 1,
  SPHERE √(2t−t²), INVSQUARE t(2−t), RANDOM drawn as LINEAR (Blender re-rolls per transform), CUSTOM =
  the tool settings' curve.
- colour = Maya's colour curve (above). Drawn: edges with an end weight > 0 (smooth colour, POLYLINE), vertices
  with weight > 0 in vertex select mode (points); a projection-matrix depth bias puts them over Blender's edit wire.
- Only in Edit Mesh with soft select on and something selected.

Checked headlessly against Blender itself: on a grid, `transform.translate(z=1, proportional…)` moves each
vertex by exactly its weight — the overlay weights must equal those offsets for every falloff, Volume and Surface.

### 4. Performance

Per object cache (like `preselect.py`): world positions, edges, selection mask, weights, GPU batches.
- depsgraph handler only marks objects dirty (geometry / anything); draw re-reads the bmesh selection when dirty
  and recomputes weights only when (selection, radius, falloff, connected, projected view axis, geometry) changed.
- During a running transform (window `modal_operators` has a `TRANSFORM_OT_*`), Blender's own weights are
  fixed at the start, so the kit keeps its weights and re-reads only the positions of the drawn vertices.
- Volume distances: numpy over the vertices inside the selection's box ± r, in chunks; a `mathutils.kdtree` of
  the selection when selection × candidates is large. Surface: Dijkstra limited to r.
- Budget checked in a headless test on a ~100k vertex grid.

### Files

`operators/soft_select.py` (state, maths), `operators/taphold.py` (buttons, binding), `ui/soft_overlay.py`
(draw handlers, cache), `ui/modeling_toolkit.py` (checkbox = state), tests `tests/test_step129_soft_select.py`,
`tests/gui/gui_step129_soft_select.py`.

## 한 일

- `operators/soft_select.py`: global `STATE` + push / pull (depsgraph, msgbus, load / undo / redo), `Scene.allset_soft_select`
  (MTK / Tool Settings checkbox), falloff maths (Volume / Projected / Surface = Blender's edge + across-triangle
  geodesic propagation, frontier relaxation inside the radius), Maya ramp.
- `operators/taphold.py`: `TapHoldBinding.buttons`; the modal drags on any of them and ends on that button's
  release; `SoftSelectBinding` = LMB + MMB, uses the state, shows the radius through `ui/soft_overlay.radius_drag`.
- `ui/soft_overlay.py`: POST_VIEW falloff colours (POLYLINE_SMOOTH_COLOR edges, POINT_FLAT_COLOR points in vertex
  mode, projection depth bias), POST_PIXEL radius circle + `Falloff Radius:` text, per object cache.
- `ui/modeling_toolkit.py`: Soft Select checkbox = the state.

## 검증

- `tests/test_step129_soft_select.py` 14 tests (written first, failed on the missing module): weights equal Blender's
  own `transform.translate` offsets for SMOOTH / SPHERE / ROOT / INVERSE_SQUARE / SHARP / LINEAR / CONSTANT (Volume)
  and SMOOTH / LINEAR (Surface) to 1e-4; 100,489-vertex grid: first 0.22 s, cached 0.1 ms, radius change 5 ms,
  Surface 0.5 s.
- `tests/gui/gui_step129_soft_select.py` 12 checks; shots `gui_step129_overlay*.png`, `gui_step129_radius_drag.png`.
- Audit repros `tests/gui/audit128/gui_model_soft_select.py` (3/3) and the soft select checks of `gui_model_session.py`
  now pass.

## 남은 것

- Maya's B-drag rate is unmeasured (×2 per 100 px kept, delegated) — manual check.
- Overlay is per object (Blender's Volume distance spans all objects in edit mode; multi-object edit can differ).
- RANDOM falloff is drawn as LINEAR. Object mode draws no colours (Maya neither for objects).
- Maya scripts for the measurement are in `tmp/maya129/` of the step 129 worktree (copy to `research/scripts/maya_softsel129/`).
