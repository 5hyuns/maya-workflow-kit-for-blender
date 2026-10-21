# Step 129 — lane T: timers keep pointers, not UI objects (#36)

A `bpy.types.Window` (and the Screen / Area / Region / Space reached from it) kept across timer ticks is not invalidated
when its window closes. Reading it later dereferences freed memory, and Blender crashes (EXCEPTION_ACCESS_VIOLATION in
`BKE_workspace_active_screen_get` via `Window.screen`, issue #36, `tests/gui/audit128/gui_props_window_close_crash.py`).
The hotfix's `_window_alive` is now `src/allset/live_refs.py`: `pointer(ref)`, `window(ptr)`, `find_area(ptr, win)` /
`area(...)`, `region(area, ptr)`, `find_space(ptr, win)`. Deferred callbacks keep `as_pointer()` values and look the live
object up again on each tick, and stop when it is gone. Comparing pointers never dereferences anything.

## All 46 `bpy.app.timers.register` sites (line numbers before the change)

| file:line | holds UI refs across ticks? | change |
|---|---|---|
| first_start.py:53 `_open_layout` | no (`_window()` fresh) | — |
| first_start.py:130 `_open_layout` | no | — |
| first_start.py:158 `_disarm` | no | — |
| keymap/\_\_init\_\_.py:99 `_reactivate` | no (keyconfigs) | — |
| marking/modal.py:468 `toggle` (hb_ui TOOLBOX) | **yes: Space** | area pointer → `live_refs.find_area`, set under `temp_override(window, area)` |
| marking/\_\_init\_\_.py:344 `_tool_later` | no (walks windows fresh) | — |
| operators/graph_keys.py:530 `_snap_tick` | no | — |
| operators/hold.py:319 `_component_tick` | **yes: `COMPONENT.area`** (read via `_alive` → `area.type`) | `area_ptr`; `_tool_set` looks it up, falls back to the largest 3D View |
| operators/manip.py:225 `watch.tick` | **yes: Window, Area, Region** | pointers; window / area / region looked up each tick |
| operators/marquee.py:55 `_watch` | **yes: Space + Window in `_active`** | entries hold space / window pointers; `_running` / `_restore` look them up |
| operators/menu_extras.py:82 `sidebar_tab_later` | was yes (hotfix: pointer) | uses `live_refs.window` |
| operators/menu_extras.py:109 `properties_tab_later` | was yes (hotfix: pointer) | uses `live_refs.window` |
| operators/menu_items.py:503 `_retry_brush` | no (`windows[0]` fresh each tick) | — |
| operators/mesh_tools.py:637 `_fix_snap_points` | **yes: Window in `_snap_fixes`** | window pointer; `_knife_running` looks it up |
| operators/option_windows.py:366 `later` (new scene) | no | — |
| operators/outliner_drag.py:435 `convert_drop` | no | — |
| operators/pivot.py:296 `_tick` | no (walks windows fresh) | — |
| operators/project.py:307 `browse_from_later` | no (walks windows fresh) | — |
| operators/tool_keys.py:188 `_watch` | no | — |
| operators/view.py:483 `poll_views` | no (`_histories` keyed by pointer, values = captured numbers) | — |
| prefs_preset.py:207 `_apply_late` | no | — |
| switch.py:394 `_delete_later` | pointer already | now uses `live_refs.window` |
| switch.py:527 `_apply_pending` | no | — |
| switch.py:572 restore lambda | no | — |
| ui/attribute_editor.py:1193 AE copy tab | **yes: Area of the new window** | window + area pointers, `live_refs.area` each tick |
| ui/channel_box.py:1420 `_first_rebuild` | no | — |
| ui/editor_chrome.py:715 `prepare_later` | **yes: Window** | window pointer, looked up each tick |
| ui/manipulator.py:704 `_ensure_timer` | no (workspaces' tools) | — |
| ui/maya_dock.py:108 `set_role_later` | **yes: Area + Window** | area / window pointers, `live_refs.find_area` |
| ui/maya_dock.py:235 `close_window_later` | **yes: Window** (`in windows` compare was safe, the later use was not when the pointer was reused) | window pointer |
| ui/maya_dock.py:359 `dock.back` (stack) | **yes: main Window** | main window pointer |
| ui/maya_dock.py:381 `dock.back` (Tool Settings / Outliner) | **yes: main Window** | main window pointer |
| ui/maya_dock.py:529 menu tear-off `later` | no (`bpy.context` fresh) | — |
| ui/maya_dock.py:637 `_close_stale_menus` | no (walks windows fresh) | — |
| ui/notices.py:550 `_expire` | **yes: status bar Area** (via `_redraw_status`) | stored as (window pointer, area); the area is touched only while its window is open (global areas aren't in `screen.areas` and live as long as their window, like `status_line._top_bars`) |
| ui/notices.py:574 `_redraw_status` | same as above | same |
| ui/outliner.py:442 `_first_rebuild` | no | — |
| ui/status_icons.py:471 `make_all` | no | — |
| ui/time_slider.py:627 `_deferred_fit` | no (walks windows fresh) | — |
| ui/toolbox.py:303 `_fit_tick` (load) | no (`fit_columns` walks windows fresh; `_warps` / `_fallback` keyed by screen name) | — |
| ui/toolbox.py:373 `_fit_tick` | no | — |
| ui/tool_dock.py:110 `open_dock.later` | **yes: Area + Window** | area / window pointers, `live_refs.find_area` |
| ui/view_furniture.py:357 `_strip_later` | no (area pointer, walks windows) | — |
| ui/view_message.py:125 `_tick` | no (pointers since step 72) | — |
| welcome.py:133 `opt_in` lambda | no | — |
| welcome.py:159 `_show_welcome` | no | — |

Changed: 17 sites. 14 newly fixed in 10 files, the hotfix's 2 moved to `live_refs`, and `switch._delete_later` (already
pointer-based) now uses the shared helper. `command_line.draw_help_line` passes its window to
`notices.remember_status_area`. The other 29 sites were checked: they only use `bpy.context` / `bpy.data` fresh on each tick.

## Other deferred callbacks checked

- msgbus: `time_slider._subscribe` (no args, `_schedule` reads fresh) — fine.
- Draw-time stores: `status_line._top_bars` (window pointer → global area, tagged only for open windows), `marking/draw.ACTIVE`
  (pointers), `light_editor._SPACES` / `maya_dock._torn_menus` / `view_furniture._HIDDEN` / `_PENDING` (pointer keys, never dereferenced) — fine.
- Modal operators (`toolbox.ALLSET_OT_fit_columns._window`, taphold, marking) run inside their window's handlers and end with it — fine.

## Verification

- GUI regression `tests/gui/gui_step129_timers.py`: opens Hypershade, Light Editor, Graph Editor, a torn-off Channel Box and a
  torn-off File menu, closes each window in the same step (before the timer's first tick), and waits 3 s. Result: 14/14 PASS.
- `tests/gui/audit128/gui_props_window_close_crash.py`: 2/2 PASS.
- GUI files touching the changed modules (step 22, 26, 28, 30, 54, 64, 67, 77, 94, 104, 106, 116, 129): 134 passed, 0 failed.
- Headless `tests/run.py`: 889 passed, 5 failed. The 5 failures read `research/` (untracked, absent from the lane
  worktree): test_keymap_maya, test_step107_keys, test_step108_menu_hotkeys, test_step120_background x2. Unrelated to this lane.
  `test_step30_selection` now resolves its fake marquee entries through the `_lookup_space` / `_lookup_window` hooks.
