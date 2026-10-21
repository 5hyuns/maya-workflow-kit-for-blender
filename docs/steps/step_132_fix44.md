# Step 132 fix lane #44: Ctrl+N = Maya New Scene in the Maya layout

## Cause

Maya's New Scene key (Ctrl+N, `research/maya/hotkeys_default.json` NewScene) was an IC row in `keymap/mapping.py`
(`wm.read_homefile` in "Window"). Until step 129 that opened the Maya layout because the app template copy in the
user's scripts folder was the active template; step 130 removed that copy, so Ctrl+N opened Blender's default
General file. File > New Scene, the Status Line "new" button and the New Scene option window already ran
`allset.new_maya_scene` (step 130 lane C).

## Fix

- `keymap/maya_patches.patch_scene_files`: IC's Window Ctrl+N `wm.read_homefile` is removed (switched off in the
  active keyconfig) and replaced by `allset.new_maya_scene` (add-on keymap item), next to the step 69 Ctrl+O/S keys.
  The Text editor's own Ctrl+N (`text.new`) runs first there and stays (`shadows=("Text",)`) — delegated.
- `keymap/mapping.py` NewScene: IC -> KIT, check `("Window", "allset.new_maya_scene", {})`;
  `docs/keymap_mapping.md` regenerated. `ui/menu_hotkeys.py` regenerated with no change (File > New Scene still
  shows Ctrl+N; the key now really runs the same operator as the menu item).
- grep of `src/`: no other place runs plain `wm.read_homefile` for Maya's New Scene (`first_start.new_maya_scene`
  reads the bundled `startup.blend` with `filepath=`). Blender-mode Ctrl+N is untouched (the item is a Maya-mode
  add-on item) — delegated.

## Verification

- `tests/test_step132_new_scene.py`: the Maya keymap's only Window Ctrl+N item is `allset.new_maya_scene`; mapping
  row, menu map and menu hotkey agree.
- `ALLSET_SANDBOX=fix44 python tests/run.py -k step132,keymap,step130,enable_disable,step108`: 39 passed, 0 failed
  (8 files; the first run caught the Text editor shadow, fixed as above).
- `tests/gui/gui_step132_new_scene.py`: Ctrl+N over the viewport of a factory file in Maya mode opens an untitled
  file with the Maya Status Line + Shelf strips. `ALLSET_SANDBOX=fix44 python tests/gui/run.py -k step132`:
  2 passed, 0 failed.
