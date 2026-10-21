# Step 129 — lane CB: Channel Box multi-channel entry (#6), Layer Editor look (#7), one visibility (#26)

## 계획

### Evidence
- Maya 2022 capture (factory prefs, 1600x900, widget grabs only): `research/scripts/maya_le129/le129.py` →
  `research/maya/screens/le129/` (`le02_dock.png`, `le03_layer_editor.png`, `_le129.json`).
  - Channel Box with Translate X/Y/Z + Rotate X selected: the **name cell** is drawn blue (#5285a6) over the whole
    label width; value fields stay dark. Selection = names, not fields.
  - Layer Editor: tab bar 18 px high, tabs left-aligned (Display 67 px, Anim 56 px); menu bar Layers / Options / Help;
    four 22x23 icon buttons right-aligned under it (move up, move down, new empty layer, new layer from selected);
    then a dark list (#2b2b2b) filling the pane. Rows 20 px: three 20x14 boxes V, P, type (blank / T / R) with 3 px
    gaps, a 16x14 colour swatch (diagonal line = no colour), then the name as plain text. Newest layer on top.
- Blender (probe `tmp/probe129/gui_probe.py`, GUI, 4.5): a "Property Editor" keymap item on MOUSEMOVE runs over the
  dock's buttons and sees the hovered button in `context.property` ((Scene, "allset_cb.tx_text", -1)); a window
  modal handler gets LEFTMOUSE PRESS before the UI and can eat it (the field then does not start editing); while it
  runs, hover keeps updating while LMB is held. An embossed text field starts editing on PRESS, so a drag that starts
  on a field can't be seen by any keymap item.

### #26 Visibility model (decision)
Maya has one `visibility` attribute per node, keyable, written by h / Display > Hide / Show / Channel Box; a display
layer's V is a separate override that never writes the node's attribute.
- **Maya visibility = `Object.hide_viewport`** (per object, keyable, independent of view layers — like Maya's
  attribute; the Channel Box row and its keys already use it). `hide_set` (view-layer base flag) is not keyable and
  would make Channel Box keys impossible.
- h / Ctrl+H / Alt+H / Shift+H / Ctrl+Shift+H (`operators/visibility.py`) write `hide_viewport`; the "kept"
  selection markers stay. New action `SHOW_ALL`; Display > Hide = `HIDE`, Display > Show = `SHOW_ALL`
  (`menu_map.py`), so the Maya menus no longer call Blender's view-layer `hide_view_set/clear`.
- **Display layer V and P = the view-layer flag `hide_set`** (the free second flag; Blender ORs it with
  `hide_viewport` for drawing, so a layer never shows an object whose own Visibility is off, and the layer never
  touches `hide_viewport`).
- Template / Reference: Blender has no per-collection draw override, so the layer remembers the member's own
  `display_type` / `hide_select` in ID properties (`allset_layer_own`) the first time it overrides them and puts
  them back on Normal, on leaving the layer and on layer delete (a Bounds object stays Bounds).
- Repro `tests/gui/audit128/gui_scene_concepts.py` called Blender's `object.hide_view_clear` as "Display > Show >
  All"; it now runs the Maya menu item (`allset.menu_item(item="Display/Show")`) — that is what the menu runs.
  (delegated)

### #6 Channel selection by drag (decision)
- Name cells become toggle buttons of per-channel bool proxies (`<key>_sel` on `Scene.allset_cb`, `sel` on custom
  rows): pressed = selected = theme selection blue (Maya's blue name cell). Their setter toggles, so Blender's own
  drag-toggle already selects a range if nothing else runs.
- `allset.cb_hover` ("Property Editor" MOUSEMOVE, first, PASS_THROUGH) remembers the hovered channel cell and starts
  `allset.cb_channel_drag`, a window modal that lives while the mouse is in that dock region and passes every event
  through except the LMB presses it handles:
  - press on a name: eaten; click = only this channel, Ctrl = toggle, Shift = range from the anchor; dragging
    selects the rows from the anchor to the row under the mouse (Ctrl+drag adds).
  - press on a value field: also eaten (first plan: let it start the text edit and end that edit when the mouse
    leaves the row — measured in the GUI: while a field edits, the UI takes every mouse event, so the drag was never
    seen, and the click elsewhere applied the old text). Click = that channel becomes the selection (unless it is one
    of several selected — then they stay) and the field is edited in a popover over it, text active at once
    (`wm.call_panel(keep_open=False)` like Blender's F2 rename: Enter applies and closes); drag = rows from the
    anchor to the row under the mouse.
  - Enter writes the typed text into every selected channel of every selected object (step 38 `apply_entry`,
    relative `+=` per channel).

### #7 Layer Editor (decision)
- Tabs: two slim tab buttons on the left (not a full-width expanded enum).
- Toolbar: right-aligned icon row in Maya's order (move up, move down, new empty, new from selected), one row with
  the menu bar like Maya; Blender has no Maya icons, nearest Blender icons; assign / remove / select / delete stay
  in the Layers menu and the row RMB menu.
- Rows: a `UIList` with three narrow fixed-width toggles (V, P, type letter), a colour swatch, then the name as
  plain text (double-click renames — Blender UIList rename), newest first; list rows fill the pane, no resize grip /
  filter strip. RMB on a row: Maya's layer menu (Add / Remove Selected Objects, Select Objects, Set type, Empty the
  Layer, Delete Layer). Move up / down reorder layers (collection order).

### Tests (TDD)
- headless `tests/test_step129_cb.py`: visibility model (h → Channel Box off; CB 0 → Display > Show shows it;
  layer V off/on keeps own visibility; Template → Normal keeps Bounds; delete restores), channel range selection
  helpers, entry to several channels, `_sel` proxies, unchanged text ignored, layer order / move.
- GUI `tests/gui/gui_step129_channel_box.py`: drag over the names Translate X → Scale Z, then over the value fields;
  click a highlighted field, type one value, Enter → every selected channel on both selected cubes; screenshots of
  the Channel Box and Layer Editor next to the Maya capture.

## 한 일

- #26: `operators/visibility.py` writes `hide_viewport` (h / Ctrl+H / Alt+H / Shift+H / Ctrl+Shift+H, new
  `SHOW_ALL`); `menu_map` Display > Hide / Show = `allset.visibility` HIDE / SHOW_ALL. `ui/layer_editor.py`: V / P =
  view-layer `hide_set` (`_layer_hide`), Template / Reference keep the member's own `display_type` / `hide_select`
  in the ID property `allset_layer_own` and put them back (Normal, removal, delete).
- #6: `ui/channel_box.py` — `<key>_sel` / `rows[i].sel` toggles as name cells, `drawn_keys` / `channel_range` /
  `select_range` / `cell_key`, `allset.cb_hover` (keymap "Property Editor" MOUSEMOVE, first, `maya_patches`) +
  `allset.cb_channel_drag` (window modal), `ALLSET_PT_cb_field` popover editor (`edit_field`).
- #7: Layer Editor tabs (slim, left), Maya toolbar order (move up / down = `allset.layer_move`, new empty, new from
  selected), rows = V / P / type boxes (`allset.layer_toggle`, `layer_cycle_type`) + swatch + name, newest first
  (`allset_layer.order`, `display_order`, `move_layer`), list fills the dock pane (`list_rows` counts the dock's
  WINDOW region), RMB on a row's boxes = Maya's layer menu on top of the button context menu, Layers menu gets
  Set Normal / Template / Reference, Empty the Layer.
- Repro `tests/gui/audit128/gui_scene_concepts.py` runs the Maya menu item for Display > Show (delegated, see
  「계획」).

## 검증

- headless `ALLSET_SANDBOX=lane_cb python tests/run.py`: 913 passed, 0 failed (109 files; new
  `tests/test_step129_cb.py` 19 tests; step 6 / 16 tests follow the visibility model).
- GUI `ALLSET_SANDBOX=lane_cb_gui python tests/gui/run.py -k step129,step16_,step55,step62,step38,step11_,step116,step6_`:
  85 passed, 0 failed. New `tests/gui/gui_step129_channel_box.py` (11 checks): drag over names Translate X → Scale Z,
  drag over fields Translate X → Rotate Z, values unchanged by the drag, one typed `2` → Translate / Rotate X/Y/Z of
  both cubes, Scale untouched.
- Audit repro `--dir tests/gui/audit128 -k gui_scene_concepts`: the four visibility / layer checks PASS (16/17; the
  remaining FAIL is "Create JOINT: joint1" — another lane's issue).
- Look: kit `tmp/shots129/gui_step129_layer_editor.png`, `gui_step129_cb_names_drag.png`, `gui_step129_cb_typing.png`
  vs Maya `research/maya/screens/le129/le02_dock.png`.

## 남은 것

- Blender's UIList always draws its bottom strip (filter triangle + resize grip): no Python switch hides it.
- Channel names stay centred in their cell (Blender toggle text); Maya right-aligns them.
- The layer RMB menu acts on the selected (active) layer, not the row under the mouse when that row isn't selected.
- Layer colour = Blender's collection colour tag (Maya's free RGB colour / quick-edit window: not done).
- Interaction feel to check by hand: `docs/manual_checks.md` (step 129 rows).
