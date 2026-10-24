# Step 166 — Menu consistency: same item greyed in one menu, working in another

Backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_164.json` item 3 (audit 11: `step_163_quant.md` §6 #9 #10,
`step_163_remaining.md` §3 #7 / BS4).

## 계획

Lanes: one (delegated) — the checker decides which items to map, and the mapping / operators are small edits in
`ui/menu_map.py`, `ui/editor_menu_map.py` and two operator modules; parallel agents would only wait on the checker.

1. Checker `tools/menu_consistency.py`: a leaf's identity = label (no `#n`) + the Maya command it runs — main menus:
   `menus.json` command / rtc (`gen_menu_data.command_paths`), else the runtime command of that label in that menu
   category (`runtime_commands.json` "Menu items.Common.Select.All by Type"); editor menu bars: the item's annotation in
   the Maya GUI capture (Maya shows the runTimeCommand's annotation); marking menus: the `marking_menus.json` item
   command. Commands become their runtime command's annotation, so main and editor items compare on one text. Report
   every greyed leaf whose identity equals a working leaf's.
2. Map what it finds to the working item's action (`menu_map.TWINS`), the Dope Sheet curve commands through a Graph
   Editor call, Dope Sheet View > Auto Frame, the UV Editor Tools brushes the backlog names.
3. Select / Delete All by Type > IK Handles / Clusters for the kit's own nodes.

## 한 것

- `tools/menu_consistency.py` (새): the checker above (`pairs` is pure; the CLI exits 1 while pairs remain). First run:
  10 pairs — Dope Sheet Curves Euler Filter / Smooth Filter ×2 / Resample Curve / Isolate Curve (Graph Editor works),
  Key > Create Character Set (Control works), Hypershade Edit > Select All by Type > Lights (Select works), UV Editor
  Select > Convert Selection > To Contained Edges / Edge Loop / Edge Ring (main Select works).
- `ui/menu_map.py` `TWINS`: twin path → the working path's action (+ To Contained Faces; UV Editor Tools > Unfold / Cut /
  Sew / Pin → Modify > Unfold, Cut/Sew > Cut / Sew, Edit > Pin Selection: Maya's brush tools run as the command on the
  selection, Blender's UV editor has no unfold / cut / sew brush [delegated]).
- Dope Sheet Curves: `allset.dope_graph_op` (`operators/graph_key_menu.py`): the curves with selected keys become the
  selected curves, the Dope Sheet area turns into a Graph Editor (`ui_type = 'FCURVES'`), the Graph Editor command runs
  (`graph.euler_filter` / `butterworth_smooth` / `gaussian_smooth` / `bake_keys` / `hide(unselected)`), then the area
  turns back and the curve selection is restored.
- Dope Sheet View > Auto Frame: add-on pref `dope_auto_frame` (Maya factory off in the Dope Sheet, on in the Graph
  Editor — `_editors104.json` `checked`); `ui/graph_view.auto_frame` also frames Dope Sheets (`action.view_all`) on a
  selection change.
- `operators/by_type.py` (새): `allset.select_all_by_type` (IK Handles = the empties IK constraints target; Clusters =
  handles of kit `clusterN` Hooks and plain Hooks, not `softModN` / `ffd1Base`; Particles; Rigid Bodies) for Select > All
  by Type > IK Handles / Clusters / Particles / Rigid Bodies. Delete All by Type > IK Handles (new: IK + Spline IK
  constraints and their handle empties when nothing else uses them) and Clusters (now only clusters, with their
  handles and vertex groups; before it removed every Hook — soft modifications and lattice bases too — and left the
  handles behind). The Select / Delete category notices no longer cover these items.

## 검증

- `python tools/menu_consistency.py`: **0 pairs** (10 before). Headless `tests/test_step166_menu_consistency.py` 8/8:
  live-kit checker 2659 leaves / 2185 with a Maya command / 0 greyed twins, a planted pair is found, TWINS share the
  action, menu counts, select / delete by type (IK handle and cluster handle selected; IK constraint + handle, cluster +
  handle + weights removed, softMod kept), particles. `test_step101` (notice rules) passes. Headless full **1548 / 1548**.
- `python tools/menu_count.py`: Dope Sheet 124 → **130** / 181 (+6), UV Editor 110 → **118** / 172 (+8), Common 266 →
  271, total 720 → 726 (48.9 %), greyed without a notice 0.
- GUI `tests/gui/gui_step166_dope_curves.py` 7/7 (Dope Sheet Euler Filter removes a 350° flip only on the curve with
  selected keys, Resample Curve keys every frame, the area is a Dope Sheet again, Auto Frame frames it). Related GUI
  `-k step101_menus,step104_editors,step150_view,step155_uv,step157_graph` 32/32. Full GUI suite not run (release prep
  only).

## 남은 것

- Hypershade Select All by Type > Shading Groups and Materials / Cameras and Image Planes stay greyed (Hypershade node
  selection is not the scene selection; different Maya commands, so the checker doesn't pair them).
- Label-only look-alikes with different Maya commands (Surfaces > Attach vs Curves > Attach, ...) are not twins; they
  belong to the Surfaces / Curves steps.
- Dope Sheet Isolate Curve hides the other curves in the Graph Editor only (Blender's Dope Sheet has no per-curve hide).
