# Step 206 — UV Editor depth 2 (backlog #5, Issue #113)

Source: `docs/steps/step_201_remaining.md` §3 V1 / §8 #8, menu capture `research/maya/screens/editors104`, Maya
measurements `research/maya/re/uv_201.md` (+ `uv_201.json`, shots `research/maya/screens/uv_201/`).

## Plan

Measure first (mayapy, then GUI Maya for the HUDs), then implement the four commands as pure bmesh rules that match
the measured results, the three heads-up displays as an Image Editor POST_PIXEL handler, and the cheap UV Sets items.
Order: measurement lane before implementation (the rules came from the data: Cycle's walk direction depends on Maya
edge ids, Create Shell (Grid)'s orientation needed four passes). One Maya at a time (PC limit), so passes ran
sequentially; Blender test runs went through the slot lock.

## Done

- **Measurement** (`research/scripts/uv_201/`): 4 mayapy passes (125 cases) + 3 GUI Maya sessions (HUD states). Rules in
  `uv_201.md` §1–5.
- **Modify > Cycle** = `allset.uv_cycle` (`operators/uv_206.py`): first face of the selection, cut out, Maya's
  `getLoopVertices` walk over Maya edge ids (= creation order over the faces, checked on every measured mesh).
- **Cut/Sew > Split** = `allset.uv_split`: selection → edges, `map_cut` (polyMapCut: each UV splits into the fans the
  cut separates; split-off fans move `uv_tools.NUDGE`, the step 66 convention).
- **Cut/Sew > Create Shell (Grid)** = `allset.uv_grid_shell`: `rect_coords` (pure) + border cut; origin = lower vertex id,
  U along the first face edge holding the origin.
- **Cut/Sew > Auto Seams** = `allset.uv_auto_seams`: cut graph (dual spanning tree, pruned on vertex + UV nodes), closed
  genus-0 shells get one shortest path between their two farthest vertices (delegated rule; Unfold3D's exact choice is
  [U]). Edge counts equal Maya's on every closed genus-0 primitive.
- **View > Heads-Up Display** Isolate Select / UV Position / UV Statistics = `ui/uv_hud.py` (WindowManager toggles,
  on by default like Maya's factory UV Editor; Maya's text, position, number format and shell rule).
- **UV Sets**: Rename Current UV Set... (`allset.uv_set_rename`, props dialog), Copy UVs to UV Set > map1
  (`allset.uv_set_copy_to`), map1 (`allset.uv_set_current`; falls back to the first UV map when none is called map1).
- Main menu **UV > Auto Seams** / **UV > Split UVs** (same runtime commands, `SplitUV` = `polySplitTextureUV`) and the
  Auto Seams items of the `contextPolyToolsUVMM` / `contextPolyToolsUVShellMM` marking menus run the same commands
  (menu twins, `test_step166`).
- **Modify > Warp Image**: notice (Blender has no image warp between UV sets: Cycles bake) — `notices.NOTICES`.
- UV Editor menu: **136 → 146 / 172** (`python tools/menu_count.py`).

Delegated:
- Split / grid borders / Auto Seams nudge split UVs 2e-4 apart (Blender can't keep a cut at identical coordinates);
  four Cycles of one quad merge back (Maya keeps the face cut).
- HUD totals are always shown (Maya shows them only for objects selected as objects; Blender's edit-mode objects are
  always selected).
- Auto Seams on a torus / pipe makes discs (kit 14 / 12 edges vs Maya 12 / 10, which leave distortion to Unfold).

## Verification

- `python tests/run.py -k step206`: 17 / 17 — Cycle 12 cases and Create Shell (Grid) 50 cases within 2e-7 of mayapy
  (worst 5e-10), Split 9 cases within NUDGE with Maya's UV and shell counts, grid rule pure on 30+ meshes, Maya edge
  ids, Auto Seams (genus-0 paths, discs untouched, torus / pipe become discs, factory cube untouched), HUD texts against
  the GUI Maya states, UV sets, undo.
- `python tests/gui/run.py -k step206 --shots tmp/shots206`: 8 / 8; shots `gui_step206_uv_hud.png` (UV Position bottom
  left, UV Statistics bottom right) and `gui_step206_uv_isolate.png` (Isolated Selection line) checked by eye against
  `research/maya/screens/uv_201/run3/t_isolate_screen.png`.
- Related GUI + common smoke (`-k step206,step155_uv,step178_uv,step66_uv,step139_uv,smoke,switch,layout,enable`): 81 / 81.
- Full headless `python tests/run.py`: 1981 / 1981 (239 files; first run caught 2 menu-rule failures — dead "UV Editor/Modify" category, main UV / marking Auto Seams twins — fixed).

## Left

- UV Editor 26 greyed with notices: Tools Lattice / Smudge / Smear / Symmetrize, Modify Symmetrize, View Custom Shelf /
  Undo / Redo View Change / Isolate Select > Load Set, Image Dim / Unfiltered / Image Range / Image Ratio / Baking /
  Measure Pixel Distance / PSD networks, UV Sets per-instance sharing / Auto-Load Textures, Reset UV Editor UI, Filter
  Selection > Faces of Selected Images, No texture found, Highlight What's New, Warp Image.
- UV Statistics HUD Options window (Maya's percentage of used UV space, off by default) not made.
- Auto Seams option box (segment / pipe cut / select instead of cut) not made: the menu runs the factory command.
