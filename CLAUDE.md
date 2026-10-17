# blender-maya-kit

Make Blender 4.5 feel like Maya 2022 to a Maya user: keymap, interaction feel,
UI/UX layout and scene concepts, not just hotkeys. Shipped as one Blender 4.2+
extension (`maya_kit`).

## Where things are

| Path | What |
|---|---|
| `research/` | Evidence base. `README.md` = index + Maya→Blender table + milestones M1–M5. `maya/*`, `blender/*` hold the facts with file:line and [O]/[I]/[K]/[U] tags. Read the relevant file before implementing a feature. Not tracked in git (contains extracted Maya MEL text, see decision 6). |
| `docs/user_decisions.md` | Decisions already made (units, parenting, packaging, target version, no Maya assets, protect user config). Follow them. |
| `docs/PLAN.md` | Step-by-step plan: research table → steps, each with P/W/C verdict and how it is verified. |
| `docs/HANDOFF.md` | Current work and the next thing to do. Update at the end of every step. |
| `docs/steps/step_<n>.md` | Per step: plan (for complex designs), what was done, verification, what is left. |
| `docs/manual_checks.md` | Checklist for things headless tests can't prove (modal input, feel, visuals). |
| `src/maya_kit/` | The extension. `blender_manifest.toml`, `__init__.py` (registers sub-packages in order), `preferences.py`, `keymap/`, `operators/`, `ui/`, `theme/`, `app_template/`. |
| `tools/build.py` | Builds `dist/maya_kit-<ver>.zip` (extension, via `blender --command extension build`) and `dist/maya_kit-<ver>-legacy.zip`. |
| `tests/` | Headless harness `run.py`, in-Blender runner `_bootstrap.py`, helpers `kit.py`, tests `test_*.py`. |

## Rules

- **Never touch the user's real Blender settings** (`%APPDATA%/Blender Foundation`). Every Blender run uses `--factory-startup` and/or `BLENDER_USER_CONFIG` / `BLENDER_USER_SCRIPTS` / `BLENDER_USER_EXTENSIONS` pointed into `tmp/`. If you start a GUI Blender, kill only that PID afterwards.
- Run `blender --command ...` with stdin redirected (`< /dev/null`, `stdin=DEVNULL`); with a console stdin it hangs.
- Do not copy Maya MEL, icons or resource files into `src/` or `docs/`. Re-implement behaviour; cite `research/...:line` as the source.
- Cite evidence in code comments or step docs as `research/<file>:<line>` or `$S\...:line` (`$S` = `C:\Program Files\Blender Foundation\Blender 4.5\4.5\scripts`).
- Every sub-package has `register()` / `unregister()`; `unregister()` must undo everything (classes, props, keymap items via `keymap.add_item`, handlers, `.append()`ed draw funcs). `test_enable_disable.py` enforces this.
- Operator ids: `maya_kit.<name>`; class prefix `MAYAKIT_`.
- Complex designs (modal input, GPU hotbox, matrix math, keymap conflicts): write the plan in `docs/steps/step_<n>.md` 「계획」 first, then implement.
- Decisions made without asking are recorded in docs as `delegated`.
- Commit messages in English. No push (no remote). Don't stage `.serena/`, `.claude/`, `tmp/`, `dist/`.

## Testing

```
python tests/run.py              # build + install into tmp/test_env + run all tests/test_*.py
python tests/run.py -k enable    # only matching test files
python tests/run.py --no-build   # reuse dist/ zip
python tools/build.py            # build only
python tools/gen_keymap_mapping.py  # regenerate docs/keymap_mapping.md (exit 1 if an IC/KIT row is unbound)
python tests/gui/run.py [--shots DIR]  # GUI tests: simulated key/mouse events (a Blender window opens briefly)
python tools/make_startup.py     # regenerate app_template/MayaKit/startup.blend (headless)
python tools/make_theme.py       # regenerate theme/maya.xml from its colour table
python tools/gen_menu_data.py    # regenerate ui/menu_data.py (Maya menu structure) from research/maya/menus.json
python tools/gen_shelf_data.py   # regenerate ui/shelf_data.py (Maya factory shelves) from research/maya/shelves.json
python tools/release_check.py    # build, extension validate, clean-config install + enable, docs/screenshots/
python tools/look_compare.py     # Maya look check: kit shots vs research/maya/screens (side by side) + theme ΔE00 vs research/maya/colors.json
python tools/dogfood.py          # clean-config install + scripted Maya-user session: checks, tmp/dogfood/shots/, console errors (expected-behaviour checks may FAIL)
```

- Each test file runs in its own `blender -b --factory-startup` process. The extension module is `bl_ext.user_default.maya_kit`; it is enabled automatically unless the test module sets `AUTO_ENABLE = False`.
- A test is a top-level `test_*` function that raises on failure. Shared helpers in `tests/kit.py` (`enable`, `disable`, `snapshot`, `diff`).
- Logs: `tmp/test_env/logs/<test>.log`. Results: `tmp/test_env/results/<test>.json`.
- Keymap work: patches go in `src/maya_kit/keymap/maya_patches.py` (record new bindings via `_add` so the shadowing test sees them); update the row status in `keymap/mapping.py`, then regenerate the mapping doc.
- GUI event tests (`tests/gui/gui_*.py`, helpers in `tests/gui/sim.py`): Blender runs with `--enable-event-simulate`; key events need a position (default 0,0 hits the status bar), the factory splash eats events until ESC, and simulated keys never reach the OS so `keystate.is_down` is replaced by the simulated state.
- Modal keys: Maya hold keys use a PRESS → modal (`operators/hold.py`), not PRESS/RELEASE keymap pairs, because the transform modal swallows RELEASE; new tap/hold keys subclass `taphold.TapHoldBinding`.
- Blender preferences (not scene data) the kit changes go through `prefs_preset.py` (backup in add-on prefs, restore on disable); `tests/kit.py` snapshots `preferences.inputs`/`view`, so a leak fails `test_enable_disable`.
- Generated binaries (`startup.blend`, `maya.xml`) are never edited by hand: change the generator and rerun it. Headless screen editing: `screen.area_split` works under a window/screen override (sizes appear after loading in a UI), but `screen.area_close` hangs and `screen.area_move` has no effect in `-b`.
- Simulated events don't update `event.mouse_prev_x`: modal operators track the previous mouse position themselves. `Region.active_panel_category` is read-only (headless and GUI), so a sidebar tab can't be preselected; GUI tests switch tabs with Ctrl+wheel over the tab strip.
- Keymap items that must win over a same-event item in the same keymap go in front (`_add(..., first=True)`) and must return PASS_THROUGH when they don't apply; list them in `maya_patches.PASS_THROUGH_FIRST`.
- Git Bash gotcha: `$PWD` is `/c/...`, which Blender's Python can't resolve — pass Windows paths (`cygpath -w`) in `BLENDER_USER_*` when launching Blender by hand.
- Headless gotcha: in `-b` the default keyconfig is not populated (research/blender/industry_compatible_vs_maya.md:14); build keyconfigs from data, don't read `keyconfigs.default`.
- UI: verify with a GUI screenshot. Interaction feel: add to `docs/manual_checks.md`.
- Maya menu items: map them in `ui/menu_map.py` (label path → operator / v3d / tool / menu); unmapped items draw greyed. `TOPBAR_HT_upper_bar.draw_left/right` are swapped by `ui/status_line.py` and must be restored on unregister (`tests/kit.py` snapshots them).
- GUI typing: hover the field (MOUSEMOVE) before clicking, then `ev('TEXTINPUT', 'PRESS', unicode=ch)`. The top bar/status bar are global areas (not in `screen.areas`): hover them to redraw. With `--factory-startup`, loading the MayaKit template reloads factory prefs, so re-activate the Maya keymap in GUI tests.
- Marking menus: data in `marking/menus.py` (Maya radial positions, checked against research JSON by `tests/test_step8_marking_menus.py`); pies are generated from it. Menu/pie items must not invoke operators that open their own popup (e.g. `transform.select_orientation`): use `wm.context_set_enum`/exec-style ops.
- Marking menu engine/hotbox: logic in `marking/engine.py` (no bpy, test it headless), GPU drawing in `marking/draw.py` (one handler per editor, draws only the region in `draw.ACTIVE`), modals in `marking/modal.py`. Pass the press position as `origin` when invoking `maya_kit.mm_engine` from another operator: a nested invoke's event is the window's latest state.
- Concepts (step 10): the Maya pivot is the object origin and `delta_location` holds the Maya pivot offset (Freeze → channels 0/0/1, pivot kept). Setting `matrix_basis`/`matrix_world` keeps deltas. Parent the Maya way with `operators/parenting.set_parent_maya` (parent inverse identity unless shear). Menu items Maya builds at run time go in `menu_map.EXTRA`.
- Sidebar dock (step 11): CB/LE and AE share the "Channel Box" sidebar tab; `WindowManager.maya_kit_dock` picks which panels poll. Outliner rows are a WM collection rebuilt from handlers (never write ID data in `draw`). To test "is this object in the view layer", use `select_set`'s RuntimeError — `view_layer.objects.get` misses objects linked since the last sync.
- Shelf (step 12): Status Line + Shelf live in the "Maya strip", an Image Editor whose `space.mask` is the Mask `.MayaKitStrip`; `ui/shelf.py` swaps `IMAGE_HT_header/tool_header.draw` (restored on unregister, snapshotted by `tests/kit.py`). Layout changes go in `tools/make_startup.py` (rerun it). A HORIZONTAL `area_split` gives the new area the top part.
- Release (step 13): a background `install-file --enable` must not persist first-start flags (keymap choice isn't saved there); a template installed into a fresh config needs `bpy.utils.refresh_script_paths()` before it can import. `LICENSE` exists twice (root and `src/maya_kit/`), kept identical by `tests/test_step13_release.py`.
- Smooth preview (step 15): 1/2/3 own only the modifiers `display.is_preview()` names ("Maya Smooth Preview" Subsurf, last in the stack, plus a Set Shade Smooth nodes modifier right before it). They are display only: Delete History keeps them, Channel Box INPUTS / AE tabs hide them. `ObjectModifiers.move` doesn't exist in 4.5: use `object.modifier_move_to_index` under `temp_override(object=ob)`.
- Global Maya keys (step 16): bind them in "Screen" (like IC's Ctrl+Z) and remove same-event items from editor keymaps, which run first (z was 3D View/View2D/Image/Node Editor zoom border). Object visibility = `maya_kit.visibility`: Blender deselects on `hide_set`, so "hidden but selected" is the `maya_kit_kept` ID property.
- Framing (step 17): F/A/Shift+F/Shift+A/Ctrl+Shift+F use `operators/framing.fit` (bpy-free) on the visible part of the region (`view.visible_bounds`: overlapping sidebar/toolbar/headers excluded). `RegionView3D.update()` doesn't exist in 4.5, so build the view matrix yourself after changing distance. Operator props that keymap items set only partly need `options={'SKIP_SAVE'}`, or Blender reuses the last call's value.
- Mesh keys (step 18): `mesh.select_mode(use_expand=True)` clears the selection in 4.5 and plain switching keeps only contained elements, so Maya's convert (touching) is `maya_kit.convert_selection` (bmesh; read the selection before switching the mode, which re-flushes it). D in edit mode = `maya_kit.hold(component_pivot)`: 3D cursor pivot + cursor tool while held.
- Timeline (step 20): `ui/time_slider.py` swaps `bl_ui.space_time.TIME_HT_editor_buttons.draw_header` (a plain class, not in bpy.types; restored on unregister, snapshotted by `tests/kit.py`). Maya animation range = frame_start/end, playback range = preview range. Timelines refit with `anim.scene_range_frame` from a msgbus subscription (re-made in load_post; file load clears msgbus) via a timer.
- GUI traps (step 9): `screen.screenshot` shows the previous frame (take shots one tick later); setting `SpaceView3D.show_region_toolbar` inside an operator doesn't stick — set it from a `bpy.app.timers` callback.
- Units (step 21, decision 8): a Maya length of 1 = one scene display unit; anything that creates geometry or places objects multiplies Maya numbers by `operators/units.maya_unit()` (0.01 in the MayaKit template, 1 with Maya Units or a factory m scene). Template view values live in `tools/make_startup.py` `maya_views()` (Maya persp/clip in cm); `units.apply_file(rescale_views=True)` keeps them for new files.
- Gizmo keys (step 22): the C transform gizmo starts its tweak on LMB **PRESS** from the gizmo map handler (keymaps `Generic Gizmo Maybe Drag` / `Drag`, ahead of region keymaps), whatever the keymap item's value says; to act before it, put a PRESS item first in those keymaps that returns PASS_THROUGH (`maya_kit.manip_duplicate`). `MAYA_KIT_GUI_ARGS="--debug-handlers" python tests/gui/run.py -k ...` shows which keymap item matched.
- Grid (step 25): with a unit system, user-perspective views skip grid steps below 1 m and divide by `scale_length`, so a cm scene needs `overlay.grid_scale` = metres per display unit (`units.grid_scale()`, 0.01) or the grid is invisible and X-hold GRID snap jumps by metres.
- Smart Extrude / cleanup (step 26): an operator run from a gizmo keymap sees `context.gizmo_group` (the C group, e.g. `VIEW3D_GGT_xform_gizmo`), and `Window.modal_operators` tells when the gizmo's transform ends. Nested op calls push no undo step: if the transform confirmed without moving, one `ed.undo` restores the state before the press; if it was cancelled there is no step, so revert by hand.
- Active handle (step 28): which C-gizmo handle was dragged is read afterwards from the registered transform (`wm.operators[-1]` `constraint_axis` / `orient_type` / `orient_axis`). In event simulation a transform modal started by a nested invoke on a mouse press doesn't see moves queued in the same tick: GUI tests send press, moves and release in separate steps.
- Materials (step 29): assignment goes through `operators/material.assign` (face select mode + selected faces = those faces, else the whole object = one slot). Marking-menu items run with `rmb=True` act on `WindowManager.maya_kit_mm_target` when nothing is selected. In click mode the engine runs the picked item on the button's release: an item that opens a popup would otherwise get that release and pick the popup's first row.
- Selection feel (step 30): edit-mode box/lasso skips occluded elements unless the view's X-ray **flag** is set (alpha doesn't matter): `maya_kit.select_through` sits first in the select tool keymaps, sets the flag + alpha 1.0 and returns PASS_THROUGH; a timer restores it when the select modal ends. Pre-selection = a Python gizmo group with `GIZMO_GT_mesh_preselect_elem_3d` (keep Blender's default gizmo keymap: an empty one stops hover; it ignores the select mode, so vertex mode + select tools only). Gizmo groups aren't in `bpy.types`; check `"bl_rna" in cls.__dict__`. `prefs_preset.GROUPS` holds navigation and undo (`edit.undo_steps` 256 = Blender's max).
- Menu bounds (step 33): `engine.fit_ring` keeps a marking menu inside `view.visible_bounds` without moving its centre (the press point gesture directions are measured from): radial boxes slide in, the list goes under / above / beside the ring. List submenus move their centre (`Session._inside_bounds`); hotbox rows that hit the top edge go under the centre box.
- Menu children (step 34): submenus Maya builds at run time (Windows > ... Editors, Display > Heads Up Display) get their items from `menu_map.CHILDREN` (`menu_sets.sub_items`); actions still go in MAP. Editors open in a new window via `maya_kit.open_editor(ui_type)` (area_dupli, like `maya_kit.script_editor`).
- Key batch (step 35): F2–F6 = menu sets in "Screen" (IC 3D View F2–F5 view keys removed; F1 / Ctrl+F1–F3 kept, editors' own F keys shadow them); Y = `maya_kit.last_tool` from `operators/tool_keys.LAST` (a persistent 0.25 s timer remembers the last non-QWERT tool per mode); Ctrl+Alt+LMB = `maya_kit.box_zoom` (draws its own box, then `view3d.zoom_border` exec, right-to-left = zoom out).
- Symmetry (step 36): Maya's global symmetry state is `Scene.maya_kit_symmetry` (`operators/symmetry.py`); Blender's mirror is per mesh (`use_mirror_x/y/z`, `use_mirror_topology`, local axes through the origin), so a depsgraph handler applies the state to meshes entering edit mode and pulls Blender's header mirror buttons back. `transform.*` exec needs `mirror=True` to read the flags (invoke/gizmo reads them itself); with both sides selected the +side drives and the −side mirrors.
- Panel menus (step 37): the 3D View header's Maya View/Shading/Lighting/Show/Renderer/Panels come from overriding `VIEW3D_MT_editor_menus.draw_collapsible` (an inherited classmethod: set it on the class, `del` it on unregister; `tests/kit.py` snapshots it), not from replacing `VIEW3D_HT_header.draw`. Panel menu operators run in this view's main WINDOW region (`panel_menus.main_region`) because header-menu context has no `region_data`. GUI tests: after ESC closes a header menu, move the cursor off the header before clicking the next one.
- Channel Box entry (step 38): value fields are text proxies (`<key>_text` on `Scene.maya_kit_cb`; custom/SHAPES/INPUTS rows in `Scene.maya_kit_cb.rows`, rebuilt from handlers when `rows_sig` differs) so Maya `+=5`/`*=2` entry works (`ui/cb_entry.py`, numbers in display units via `bpy.utils.units.to_value`). Keep editable proxies on the Scene, not the WindowManager: UI edits of WM properties push no undo step. Kit-made materials carry `maya_kit_type` (AE label/sections via `attribute_editor.material_type`).
- Pick-walk / axis lock (step 39): edit-mode arrows = `maya_kit.pick_walk_component` (bmesh; edges walk loop L/R and ring U/D like Maya's pickWalk*.mel, vertices/faces pick the neighbour closest to the arrow on screen via `region_3d.perspective_matrix`, front (x, z) headless). Alt+Shift+LMB/MMB = `maya_kit.view_axis_lock` (own modal: turntable maths of view3d_navigate_rotate, `view_rotation` = inverse of C `viewquat`).
- Maya look (step 40): Maya reference = factory prefs measured in a running Maya 2022 (`research/maya/colors.json`, `screens/`), not the user's Maya prefs. Lead (last selected = Blender active) is green #43ffa3, other selected white; factory viewport is flat #5c5c5c (no gradient). Theme `axis_x/y/z` also colours the grid axis lines.
