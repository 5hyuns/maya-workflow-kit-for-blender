# Step 215 — Maya Preferences window and Hotkey Editor (Issue #121)

Source: `docs/steps/step_210_remaining.md` §8 #3 (carried over six audits): Windows > Settings/Preferences >
Preferences / Hotkey Editor opened Blender's Preferences. The kit doesn't write Blender's preferences
(`docs/user_decisions.md` decisions 13 / 14). Maya spec: `research/maya/re/prefs_215.md` — GUI Maya 2022 capture
(`research/scripts/maya_prefs215/`, data + shots `research/maya/screens/prefs215/`).

## 계획 (delegated)

- Lanes (two foreground agents, then main): (A) GUI Maya capture of the Preferences window (38 categories, every
  control), Hotkey Editor, Marking Menu / Shelf Editor ∥ (B) kit Hotkey Editor window; then (C, main) the kit
  Preferences window from A's capture. Sequential only: C needs A's category tree and labels.
- Both windows are `ui/marked_window.py` kinds (Properties Tool tab in its own window, step 213): HOTKEY_EDITOR =
  bone + bone_constraints flags, PREFERENCES = scene + output flags.
- Preferences rows: kit add-on preference / scene value (editable) / Blender preference (read-only + Recommended
  setup + "Blender Preferences" button opening that section) / Maya control with no counterpart (greyed + reason).
- Hotkey bindings are changed on `keyconfigs.user` (the merged keymap Blender's own keymap editor edits); Blender's
  Save Preferences / auto-save keeps them — the kit writes no file.

## 한 것

- **Maya capture** (`research/maya/re/prefs_215.md`): Preferences = 817 x 531, Edit (Revert to Saved, Restore Default
  Settings) / Help menu bar, a 130 px "Categories" list (38 rows: Interface, Display, Settings, Security, Modules,
  Applications + children), page "<Category>: <description>", Save / Cancel; closing by the OS button saves. Factory
  values per page (UI Elements all on, Time Slider 24 fps / playback 1–120 / animation 1–200 / Play every frame /
  Continuous, Undo infinite, Selection Preselection Highlight on ...). Hotkey Editor = Hotkey Set (Maya Default,
  locked — editing makes "Maya Default Duplicate"), Edit Hotkeys For (Menu items / Editors / Other items / Custom
  Scripts), tree Application Command | Runtime Command | Hotkey, Search By Application / Runtime Command / Hotkey,
  Keyboard and Runtime Command Editor tabs, Save / Save and Close.
- **Preferences window** (`ui/maya_prefs.py`, data `ui/maya_prefs_data.py` bpy-free): Maya's 38 categories in a
  scrolling list (children indented), each page = Maya's title and sections with the kit's rows — 37 kit settings
  (menu set, menu bar / panel menus, marking menu / hotbox styles, Status Line / Command Line / Help Line / Tool Box,
  ViewCube, In-View Messages, view axis / selection wire / component colours, tangents, Graph Editor auto frame,
  project, smart extrude / duplicate, Maya names, preselection / select-through / priority, Channel Box sync, test
  resolution ...), scene values (linear / angular unit, Auto Key, framerate, playback / animation range, playback
  speed, colour management, default light: 12), 12 Blender preferences shown read-only (Undo Steps, Resolution Scale,
  Gizmo Size, Tooltips, Auto-Save, Recent Files ...) and greyed Maya controls with the reason. Save keeps the changes
  and closes; Cancel / Edit > Revert to Saved write back the values of the window's opening; Edit > Restore Default
  Settings = kit defaults + Maya factory scene values (24 fps, 1–200 / 1–120, cm / degrees, Play every frame).
  Windows > Settings/Preferences > Preferences opens it.
- **Hotkey Editor** (`ui/hotkey_editor.py`, rows `keymap/hotkey_rows.py`, Maya data `keymap/hotkey_data.py` from
  `tools/gen_hotkey_data.py` — keys / contexts / command names only): 400 Maya factory hotkeys (68 macOS-only Cmd rows
  hidden) with columns Command | Maya Hotkey | Kit Hotkey | Status, search by name or hotkey (case / space
  insensitive), Maya categories, details (Maya key, context, category, the kit operator + keymap). Assign New
  Hotkey... = next key press (Esc / mouse cancels); a clash is warned ("Also used by ..."); Restore / Restore All Maya
  Hotkeys = Blender's `restore_item_to_default`. Measured [O]: the user keyconfig carries the add-on items, an edit
  there changes what fires (GUI: Ctrl+F6 toggles the selection mode, F8 no longer does), survives Maya mode off / on,
  marks preferences dirty and writes nothing (sandbox config folder unchanged). The kit's mapping notes (partly
  Korean dev notes) are not shown in the window.

## 검증

- Headless: `test_step215_prefs` 7 (Maya tree, every row resolves, Cancel round trip, Maya factory defaults, no
  Blender preference written, menu + unique flag pair, disable removes props) + `test_step215_hotkeys` 8 (rows,
  search, rebind / restore, conflicts, lifecycle, step 130 scans) — 15 / 15. Full headless **2101 / 2101** (4.5.4).
- GUI: `gui_step215_prefs` 4 / 4 (menu opens the kit window, Cancel restores framerate 30 → 24 and closes),
  `gui_step215_hotkeys` 14 / 14; with related files + smoke (`-k step215,step213_editors,step209_reference,
  step116_dock,step60_switch,step49_layout,step129_switch`) **87 / 87**. Shots checked by eye:
  `tmp/shots215p/gui_step215_prefs_interface.png` (Interface page: menu set, menubar checks, marking menus, Interface
  Scaling / Devices as Blender rows with the Preferences button), `gui_step215_prefs_time_slider.png` (Time Slider
  page, list scrolled to the selected row, Save / Cancel), `tmp/shots215/gui_step215_hotkey_editor.png` /
  `gui_step215_hotkey_search.png`.
- Menu count unchanged (both items were already mapped to Blender's Preferences): unique 806 / 1319.

## 남은 것

- Hotkey Editor: no keyboard picture, no Runtime Command Editor tab, no Hotkey Set duplicate / import / export
  (Blender: Preferences > Keymap > Export), Maya's "Editors" category; macOS Cmd rows hidden.
- Preferences: Maya pages with no counterpart are greyed (Kinematics, NURBS, Subdivs, Assets, Cached Playback, Dynamics,
  GPU Cache, XGen, MEL, Modules ...); Time Display (Frames / Timecode), Key ticks, Looping, Up axis, camera clip
  defaults are greyed rows. Marking Menu Editor / Shelf Editor / Panel Editor stay greyed with their notices.
- Not run on Blender 5.x.
