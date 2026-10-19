# Step 116 — Maya docking model: every panel its own window, tear off by the ::::: handle

User instruction (2026-10-19): in Maya every panel (Outliner, Channel Box / Layer Editor, Attribute Editor, Tool
Settings, Modeling Toolkit, ...) is its own dockable window; the dotted handle tears it off into a floating window and
it can be docked again; menus tear off by their dotted line. The viewport and the Attribute Editor (and every panel)
are separate windows — a panel over the viewport or inside the 3D View sidebar is not Maya.

## 계획 (delegated)

### Evidence

- Maya: every element is a `workspaceControl` (Qt dock widget) made by `createUIComponentDockControl`
  (research/maya/ui_layout.md:39-42); Tool Settings left, CB/LE + AE + MTK one right tab stack, Outliner left
  (ui_layout.md:45-63, 117-129); every menu has a tear-off line `-to true` (ui_layout.md:184). Maya 2022 shot
  `research/maya/screens/10_attribute_editor.png`: right column = one stack with side tabs, Outliner title tab.
- Kit before this step: Outliner = own area (left), Tool Settings = own area (Properties Tool tab, step 106), Status
  Line / Shelf = own areas, Time / Range Slider = Dope Sheet area — but **CB/LE, AE and MTK were the main 3D View's
  sidebar** (three sidebar tabs, step 99), i.e. part of the viewport.
- Measured in a GUI Blender 4.5 (`tmp/probe116/g1.py`, factory startup):
  - `screen.area_split(direction='VERTICAL', factor=0.8)` on the viewport puts the new area on the **right**
    (width 0.2).
  - A Properties editor on its Tool tab draws Python `VIEW_3D` / `UI` panels of category "Tool" (the step 106
    mechanism) — with Blender's own Tool-tab panels (Active Tool, Options, Workspace) around it.
  - `screen.area_dupli('INVOKE_DEFAULT')` on that area opens a new OS window at the area's place and size holding a
    copy whose `context`, `show_properties_*` flags and hidden header **are copied**; the kit panel draws there.
    (Without INVOKE it is an "invalid operator call".)
  - `wm.window_close` under a window override closes the floating window; `screen.area_close` on a docked area gives
    the neighbour its width back (GUI only, hangs in `-b`).
  - `SpaceProperties.pin_id` takes only one ID type per space (it became Text) — not usable as a marker.

### Choice

1. **(a) Separate areas, no overlap.** The right tab stack is its own area: a Properties editor on the Tool tab,
   header and tab column hidden (like the Tool Settings dock), right of the viewport. The 3D View sidebar no longer
   hosts any Maya panel (`maya_dock_only` and the sidebar-tab sync go). The area's role is stored in the space itself
   so it survives save / load and `area_dupli`: the hidden tab-visibility flags `show_properties_*` (invisible while
   the tab column is hidden) — Tool tab + one role flag:
   STACK `world`, CHANNEL_BOX `physics`, ATTRIBUTE_EDITOR `effects`, MODELING_TOOLKIT `particles`, MENU `texture`;
   the Tool Settings dock stays "Tool tab only". One kit panel (`ALLSET_PT_maya_dock`, VIEW_3D / UI / "Tool",
   polls only in such areas) draws handle + tabs + the content; Blender's Tool-tab panels are hidden there by
   `dock_tabs` (already wrapped for the Tool Settings dock).
2. **Tabs.** The stack shows a tab row (Channel Box / Layer Editor | Attribute Editor | Modeling Toolkit) at its
   top; `WindowManager.allset_dock` stays the selected tab (Ctrl+A, Windows menu, RMB "<object>..." keep working).
   Maya's side tabs can't be drawn inside a Properties region (documented divergence).
3. **(b) Handle.** Every Maya panel starts with a dotted handle row (`::::::::`, emboss off). Click on a docked panel
   = **tear off**: a floating window with only that panel (`area_dupli` of its area + the copy's role set to that
   panel; a torn-off tab leaves the stack's tab row; Tool Settings / Outliner areas close their docked copy).
   Click on a floating panel's handle = menu **Dock / Close**: Dock closes the window and puts the panel back (stack
   tab selected; Tool Settings / Outliner: re-split the viewport's left side). Closing the floating window by the OS
   button also docks the tab again (the stack hides only kinds that have a floating window). Dragging a panel onto a
   dock target is not possible from Python (no cross-window drag and drop) — the click replaces the drag.
4. **(c) Windows menu.** Windows > General Editors > Attribute Editor / Channel Box / Modeling Toolkit / Tool
   Settings and Windows > Outliner raise the docked panel (stack tab) or, when the current layout has no place for it,
   open it as a floating window (Maya opens panels that aren't in the workspace as floating windows).
5. **Menu tear-off.** Kit Maya menus get Maya's dotted first line; clicking it opens a floating window (role MENU)
   whose panel draws that menu's items as buttons. The menu path is kept per window in memory (not in the file):
   a MENU window restored from a saved file has nothing to show and closes itself.
6. **Template / switch.** `tools/make_startup.py` splits the stack off the viewport's right side (Maya narrow panel
   260 px) and hides the viewport sidebar; regenerated in a GUI Blender. Switching to Blender closes floating windows
   whose only area is a Maya role (they would show Blender's Tool tab).

### Blind spots checked / accepted

- Operators run from the dock (MTK buttons, CB menus) now run in a Properties context, not a 3D View sidebar: kit
  menu actions already run from the top bar (no 3D View context) through `allset.menu_item` overrides; checked by the
  GUI tests that click MTK / CB buttons.
- Panel code that assumed a VIEW_3D sidebar region (`fill_pane` region height, `_sync_tick` categories,
  `_show_sidebar_later`) is replaced or made region-agnostic.
- `tool_settings.in_dock` was "any Properties space": now "Properties Tool tab and not a Maya content role".
- A user's own Properties editor on the Tool tab is never marked (role flags are only set by the kit), so nothing
  changes there.
- Not possible: real OS-level docking (drag a floating window into a dock slot), Maya's side tabs, tearing off
  toolbars (Shelf / Status Line / Time Slider keep their rows; documented as left).

## 한 것

- `ui/maya_dock.py` (new): roles in the space's hidden tab flags (`role` / `set_role` / `set_role_later`), tab stack
  (`stack_tabs`, `current_tab` skip floating kinds), `open_stack` (split right of the viewport, 260 px), `tear_off`
  (stack tab → floating window with that panel; an emptied stack closes; Tool Settings / Outliner → floating copy +
  `area_close` of the docked one), `dock` (close the window from a timer, then stack tab / `tool_dock.open_dock` /
  left split for the Outliner), `show` / `toggle` (Maya raise / toggleUIComponentVisibility), menu tear-off
  (`tear_menu`, MENU windows from a file close themselves), `close_floating` (switch to Blender).
  Operators `allset.dock_handle` (click: tear off; on a floating panel: Dock / Close menu), `allset.dock_back`,
  `allset.dock_tab`, `allset.panel_show`, `allset.menu_tear_off`; panel `ALLSET_PT_maya_dock` (VIEW_3D / UI / "Tool",
  polls only in role areas): handle row, tab row, Channel Box (+ fill + Layer Editor), Attribute Editor, Modeling
  Toolkit, or the torn-off menu's items.
- The sidebar dock is gone: `ALLSET_PT_channel_box` / `_dock_attribute_editor` / `_dock_modeling_toolkit` /
  `layer_editor.ALLSET_PT_layer_editor` are no longer registered (their draw code is called by the dock panel),
  `outliner.ALLSET_PT_outliner` removed, preference "Channel Box Dock Only" removed, the sidebar-tab sync timer
  removed (`allset_dock` now only redraws), `dock_tabs` wraps Blender's Tool panels only in Properties Tool tabs (the
  viewport sidebar is Blender's again). `tool_dock.is_dock` / `tool_settings.in_dock` exclude role areas; the Tool
  Settings panel and the Maya Outliner header start with the handle.
- Raising: Ctrl+A, Windows > General Editors (AE / CB / MTK), RMB "<object>...", material "Attributes", Status Line
  editor toggles → `maya_dock.show` / `toggle` (tab of the stack, or a floating window when the layout has none);
  Windows > Outliner = `allset.panel_show` (docked = shown, else a floating Maya Outliner).
- Kit Maya menus start with Maya's dotted tear-off line (`menu_sets._menu_class` → `maya_dock.draw_tear_line`).
- Template (`tools/make_startup.py`, regenerated in a GUI Blender): tab stack area 277 px right of the viewport
  (`make_stack`: Tool tab, `STACK_FLAG`, header + tab column hidden), viewport sidebar off.
- Switch to Blender closes floating Maya-panel windows (`switch.set_mode`).
- Found while migrating the GUI tests: the dock's Channel Box tab first lacked the Layer Editor / Set Driven Key pane
  (added: `layer_editor.ALLSET_PT_layer_editor.draw` under the Channel Box); `dock_show` in the tick that made the
  stack opened a floating Channel Box (the stack's role was still pending: `find_stack` counts `_pending`); Ctrl+A
  with no stack opened a window per press (now one floating dock window switches between AE and CB).
- The handle row = Maya's title / tab row: grip `::::::::` + the tabs in one row (Channel Box's empty title row gone).
- Tests: `tests/test_step116_dock.py` (6) and `tests/gui/gui_step116_dock.py` (20 checks: layout without overlap,
  handle click → floating CB alone, Dock, AE window closed → docks back, Tool Settings / Outliner tear off + dock,
  menu tear-off + Close, no stack → Windows > AE floating, CB toggle hides / shows the stack). Old tests follow the
  new model (steps 5, 7, 11, 34, 49, 63 headless; 5, 6, 11, 21, 29, 38, 49, 55, 58, 62, 63, 65, 91, 99, 112 GUI):
  `sim.dock_area` / `dock_region` and `sim.find_button` (sweeps for a button by data path / command and returns its
  centre; hover in one tick, press in the next) replace sidebar pixel offsets. `tools/release_shots.py` /
  `dogfood_session.py` use the stack.

## 검증

- 헤드리스 **869/869** (new `test_step116_dock.py` 6).
- GUI 전체 (once, before the commit): **1119/1121**; the two failures re-run alone after fixing the tests: menus now open
  with Maya's tear-off line under the mouse, so `gui_step54` walks three rows to Trax Editor (and rests with a small
  move so the tooltip shows) — 5/5; `gui_step106`: closing the Tool Settings dock gave its width back while the Tool
  Box column had been fitted meanwhile (viewport wider, layout back) — 12/12. `gui_step116_dock` 20/20.
- Screenshots looked at (`tmp/shots116/`): layout with the stack beside the viewport (no overlap, viewport sidebar
  closed), torn-off Channel Box alone in its window while the stack shows AE / MTK, floating Outliner, Tool Settings
  and torn-off File menu (narrow, left column of items).
- `tools/release_check.py` all PASS (20).

## 남은 것

- Not possible from Python (documented): dragging a floating panel back onto a dock slot (OS-level docking; Dock is a
  click), Maya's side tabs (tabs are a row at the top of the stack), left-aligned item text in torn-off menus (Blender
  centres button text).
- Toolbars (Status Line, Shelf, Time / Range Slider) keep their rows: no tear-off for them yet (Maya allows it).
- `ui/outliner.py` still builds `allset_outliner_rows` / `ALLSET_UL_outliner` although the sidebar list that showed
  them is gone (kept: headless tests use the rows; candidate for cleanup).
- `docs/manual_checks.md` step 116 items (real mouse: dragging floating windows, two monitors, save / reopen).
- Next: step 117 (listing package; upload by the user).
- `tools/release_shots.py`: the AE screenshots (05 / 06) now select the Attribute Editor tab (they showed the Channel Box since step 99); release_check re-run: all PASS.
