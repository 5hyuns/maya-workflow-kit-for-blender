# Step 115 — Distribution prep 3: no surprises (opt-in, cleanup, fewer monkeypatches)

Audit `docs/distribution/extensions_audit.md` 「위험」 items (Terms of Service 3.1 "no surprises", 3.9 "don't touch
Blender internals / other add-ons"; add-on guidelines). All decisions below are `delegated`.

## 계획 (delegated)

Measured first (`tmp/probe115/`, Blender 4.5, sandbox config):

- A GUI `wm.read_homefile(app_template="Allset")` does **not** reload the saved preferences (an unsaved
  `ui_line_width` change survives, the add-on stays registered, `maya_mode` stays) — only the active keyconfig falls
  back to "Blender" (stored name too). With `-b` nothing changes at all. So the template `__init__.py` only ever had one
  real job: re-activate the Maya keymap after the switch.
- Quitting unregisters add-ons through `bpy.utils._on_exit` → `addon_utils.disable_all` → `disable`; a user disable
  (Preferences checkbox, extension Remove / Disable) calls `addon_utils.disable` directly. The call stack tells them
  apart; nothing else does (`disable` drops the `preferences.addons` entry only after `unregister`).
- `bl_app_template_utils.activate` imports a template with `ignore_not_found=True`: a template folder without
  `__init__.py` is supported ("modules that don't contain scripts").

1. **Opt-in.** `maya_mode` defaults to **off**. Enabling registers only CORE (preferences, switch, welcome): the
   Maya | Blender switch at the right of the top bar (append), an Edit menu item (append), Ctrl+Alt+Shift+M in the add-on
   keyconfig, and once, in a GUI session, the welcome dialog. Keymap, preference presets, theme, layout, UI
   replacements and handlers come only from a user action: the welcome dialog's "Make Blender feel like Maya", the
   same button in the add-on preferences, or the switch. "Make Blender feel like Maya" = Maya mode on + Make Blender
   Maya (template, theme, splash, density, start option); the open file gets the layout workspace appended (switch
   `enter_layout`, data kept) or, when it is an untouched new file, is replaced by the template file.
2. **No automatic `save_userpref`.** `first_start.make` only marks the preferences dirty (the template switch doesn't
   reload them — measured). `switch.finish_interrupted` no longer saves from a timer: the restore is idempotent
   (only values still in their Maya state are put back), so the snapshot is kept, the preferences marked dirty, and
   the snapshot deleted at the first start that finds nothing left to restore. The only `save_userpref` left is
   Maya's File > Save Preferences menu item (a user action).
3. **App template = data only.** Keep the template (decisions 3 / 9: File > New > Allset and "Start in Maya Layout"
   open the template *file* — cm units, Maya views, empty scene — which a workspace append can't give a new file; the
   switch already appends only the workspace into the open file). Ship it **without `__init__.py`**: no code outside the
   extension. The keymap re-activation moves into the keymap module (load_post: in the Allset template, Blender's
   default keyconfig → Maya, as the old template code did). Install / remove set the hidden add-on pref
   `layout_installed`; a **user disable / remove deletes the marker-carrying template** (legacy `MayaKit` too), quit
   and script reload keep it (stack check); `register` reinstalls it when `layout_installed` is still set (e.g. the
   stack check failed in another Blender version), so the preference survives either way.
4. **Draw swaps.** Every place that replaced a Blender UI method was classified:
   - only *adds* to Blender's draw → `prepend` / `append` (Tool Box filter flag on `VIEW3D_PT_tools_active`);
   - replaces Blender's content in kit areas only → swap **only the class's own draw function** in its draw list
     (`ui/own_draw.py`, the mechanism `append` uses), so other add-ons' `append` / `prepend` keep drawing and survive
     our unregister: STATUSBAR, TOPBAR upper bar (instead of `draw_left/right`), OUTLINER, IMAGE header and tool
     header (others already did this: Graph / Dope Sheet, VIEW3D headers, Properties / Info / Text headers);
   - helpers that are not draw functions (TIME `draw_header`, `*_MT_editor_menus.draw_collapsible`, toolbar
     `tools_from_context`) and panel `poll` wrappers have no append API: listed with reason and restore guarantee in
     `docs/distribution/listing.md`.
5. **ctypes**: `keystate.is_down` returns None (unknown) off Windows and if the call fails; callers only act on an
   explicit False, so they fall back to Blender's RELEASE events. Documented in listing.md.
6. Tests: `tests/kit.enable()` = enable + Maya mode (as before step 115, no theme); new `test_step115_opt_in.py`;
   GUI `sim.setup()` turns Maya mode on after enabling; tools that drive a first start use the welcome action.

## 한 것

- **Opt-in** (`preferences.maya_mode` default off): enabling registers CORE = `preferences`, `switch`, new
  `welcome.py`. `welcome.py`: the dialog (moved from `first_start`, shown once in a GUI session while Maya mode is off;
  text says nothing has changed yet) and `opt_in()` = `switch.set_mode(True)` + `first_start.make()` + the layout
  (template file for an untouched new file, else `switch.enter_layout` into the open file). The add-on preferences in
  Blender mode show "Make Blender feel like Maya" (the same dialog), "Maya Mode Only" and "Restore Blender Settings".
- **No automatic saves**: `first_start.make` marks the preferences dirty instead of `save_userpref`;
  `switch._save_and_forget` removed — `finish_interrupted` restores without saving and drops the snapshot once nothing
  is left. Stale snapshots: register finishes an interrupted switch only when the preferences still show Maya mode
  (`switch.maya_state_left`: stored keyconfig "Maya-style" or the Maya theme), else forgets the file (found by the full
  run: a snapshot from an earlier test file overwrote `ui_scale`). A user disable drops snapshot and theme backup.
- **Template**: `app_template/Allset/__init__.py` deleted (template = `startup.blend` + splash images + marker);
  `install()` deletes a stale `__init__.py` of an older copy, no `refresh_script_paths`. Hidden pref
  `layout_installed`; `__init__.unregister` → `app_template.remove_on_disable()` when `switch.user_disabling()` (the
  `addon_utils.disable` frame has `default_set=True`); `register` → `reinstall_if_wanted()`. Keymap after a template
  switch: `keymap._keep_keyconfig` (load_post) + the same check from a persistent 0 s timer
  (`_reactivate`, rule `wants_maya`): the GUI probe showed the switch resets the keyconfig *after* load_post and runs
  no load_pre, so a load_pre memory never saw "Maya-style" and a non-persistent timer was dropped by the load.
- **Draws**: `ui/own_draw.py` (`swap` / `original` / `restore` of the class's own entry in its draw list) now used by
  `command_line` (STATUSBAR; the hand-made loop over other add-ons' functions is gone), `ui/maya_outliner.py`,
  `ui/shelf.py` (IMAGE header + tool header), `ui/status_line.py` (TOPBAR own draw `draw_upper_bar`; Blender's
  `draw_left` / `draw_right` untouched). `ui/toolbox.py`: `prepend(_draw_begin)` / `append(_draw_end)` instead of a
  replaced `draw`. The rest (helpers, poll wrappers) listed with reasons in `docs/distribution/listing.md`.
- **ctypes**: `keystate.is_down` also returns None when the call raises; callers checked (only `is False`, and
  `manip.py` treats None as "not held" = no wait).
- Tests / tools: `tests/kit.py` (`enable(maya=True)`, draw-list snapshot `_draw_funcs`), `tests/gui/sim.py` setup opts
  in, `tests/test_step115_opt_in.py` (new), step 5 / 7 / 12 / 49 / 50 / 60 tests follow the new mechanisms,
  `rt60_session.py` without `run_timers`; `tools/release_probe.py` / `installer/blender_helper.py` "make" =
  `welcome.opt_in`, `release_shots.py` / `dogfood_session.py` / `repo_check.py` check "unchanged until the opt-in".
- Docs: `docs/distribution/listing.md` (new: opt-in text for the listing, UI class changes table, system access),
  `docs/manual_checks.md` (step 115), CLAUDE.md.

## 검증

- 헤드리스 **864/864** (`tests/test_step115_opt_in.py` 10 new: enable alone changes no user setting / handler /
  keyconfig and disable leaves nothing; opt-in → Maya + template, disable restores and deletes the template; quit-style
  disable keeps it, reinstall when wanted; template has no code; only Maya's Save Preferences item saves; keymap rule
  after a template switch; other add-ons' appended UI survives enable and disable on all six classes; keystate None
  off Windows / on failure; stale snapshot dropped, user disable drops the snapshot).
- GUI **1093/1093** (`gui_step53_editors` now shows its own material: since Maya mode is switched on outside Blender's
  restricted register context, the default-material handler baselines and gives the test's new cube lambert1 — the
  kit behaviour step 100 wants; `gui_step7` / `gui_step35` / sweep M72-1 hook the kit's top bar draw).
- Welcome dialog GUI shot in a clean sandbox (`tmp/probe115/w/`): enabling = keymap "Blender", Default theme, Region
  Overlap on; Return in the dialog → Maya-style keymap (also after the template switch), Studio Grey theme, Allset
  template, solid panels.
- `tools/release_check.py` all PASS (validate, clean install, user setup kept / restored), `tools/repo_check.py`
  11/11, `tools/installer_check.py` 9/9.

## 남은 것

- `docs/manual_checks.md` step 115 (real Get Extensions install, Auto-Save Preferences off, template removal on a real
  Remove, File > New > Allset keymap).
- `switch.user_disabling` reads Blender's `addon_utils.disable` frame (4.5 measured; 5.x not re-measured — if it
  fails the template stays on disable and `reinstall_if_wanted` covers the opposite case).
- Step 116: listing texts / tags / screenshots on top of `docs/distribution/listing.md` (upload by the user).
