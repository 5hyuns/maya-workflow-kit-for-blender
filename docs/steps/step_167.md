# Step 167 — Shelf double-click and overflow

Backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_164.json` item 4 (audit 11: `step_163_remaining.md`
§4 BS2, step 162 remaining).

## 계획

Lanes: one (delegated) — the Maya capture decides the overflow design and both parts change `ui/shelf.py`; two agents
would edit the same file.

1. Measure Maya first (GUI Maya, `research/scripts/maya_shelf167/`): narrow window, shelf widgets, wheel, double-click.
   Result `research/maya/re/shelf_overflow_167.md`: buttons wrap into rows, one row shown, a 12 px vertical scroll bar
   with ▲ / ▼, a wheel notch = one row.
2. Double-click / second click within Blender's double-click time = the button's option box through its Maya menu
   item (`allset.menu_option_box`, the menu's Shift / Ctrl+click path); the first click ran the command once. A
   "redo" option box runs the command again with its settings, so it undoes the first run first.
3. Overflow: `row_layout` flows the slots into rows, `_row[shelf]` = the row shown, icons on other rows are not drawn
   or picked; scroll bar drawn at the right; wheel = keymap items first in "Image" (pass through elsewhere), arrows =
   picking gizmos.

## 한 것

- Maya measured (`research/maya/re/shelf_overflow_167.md`, screens `research/maya/screens/shelf167/`): Poly Modeling's
  51 cells wrap into a second row already at 1600 px; the scroll bar's page = one 35 px row; wheel down / up moves one
  row and stops at the ends; Cube = CreatePolygonCube / doubleClickCommand CreatePolygonCubeOptions.
- `ui/shelf.py`:
  - `ALLSET_OT_shelf_button.invoke`: DOUBLE_CLICK or a second press within `preferences.inputs.mouse_double_click_time`
    → `option_box(...)` (was `screen.redo_last`, which shows nothing since step 147: shelf runs aren't registered);
    Ctrl+click = the box without running first; script buttons have no double-click command (nothing more runs).
  - `menu_path_of` (shelf_map.MENU, else the main menu item mapped to the same action: Cube →
    Create > Polygon Primitives > Cube), `option_box` → `allset.menu_option_box`, `take_back_run` (undo the first
    click for "redo" boxes).
  - `row_layout` / `rows_of` / `scroll_shelf` / `icon_rect` (other rows off-screen), `scroll_rects` /
    `_draw_scroll_bar` (Maya ▲ / ▼, the arrow at its end dimmed), `ALLSET_GT_shelf_scroll` gizmos,
    `allset.shelf_scroll`; the bar sits 16 px from the right edge (`SCROLL_RIGHT_PX`).
  - Two Blender things were in the way (measured with `--debug-handlers`): the Image Editor's navigation gizmo (not
    drawn under the kit's row, still picked) took the clicks at the row's right end, and the Sample tool keymap takes
    plain clicks before "Image". Shelf rows now have `show_gizmo_navigate` off (`tools/make_startup.py`, template
    regenerated; `settle_rows` from load_post / a timer for older files) and the arrows are gizmos.
- `keymap/maya_patches.patch_shelf_scroll`: WHEELUP / WHEELDOWN first in "Image" (shadows Image / View2D, both pass
  through; listed in `PASS_THROUGH_FIRST`).

## 검증

- Headless `tests/test_step167_shelf.py` 6/6: two clicks on Polygon Cube = **one cube + `menu_option_box` on
  Create/Polygon Primitives/Cube** (no undo, no redo_last), DOUBLE_CLICK event and Ctrl+click = the box only, "redo"
  boxes take the first run back, two far-apart clicks = two cubes, Maya flow rows (1600 px UI 1.0 one row, UI 1.25 two
  rows, 1000 px two rows), scroll clamps / last button reachable / keymap items. Headless full **1554 / 1554**.
- GUI `tests/gui/gui_step167_shelf.py` 9/9 (1600 px window, UI 1.25): Poly Modeling 2 rows, the last button (3D Cut and
  Sew UV Tool) off the shown row, scroll bar drawn; the wheel over the icons shows row 1 and the last button is
  on screen and highlights; the ▲ arrow shows row 0 again; a double-click on Polygon Cube makes one cube and opens
  Polygon Cube Options (screenshot `tmp/shots167/gui_step167_dclick_125.png`). Related GUI `-k
  step12_shelf,step109_shelves,step162_shelf_add,step113,step51` 40/40. Full GUI suite not run (release prep only).

## 남은 것

- Maya's tab-strip scroll arrows (20 x 18, a narrow window) are not drawn: the kit tab row still cuts off.
- The scroll bar has no draggable thumb (one row shown: the thumb is the whole track in Maya too).
- The double-click run in Maya could not be replayed by a synthesised Qt double click (documented by the button's
  `doubleClickCommand` instead).
