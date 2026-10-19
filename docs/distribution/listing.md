# extensions.blender.org listing — Allset for Maya Users

Step 115 wrote the technical disclosure below ("no surprises", Terms of Service 3.1 / 3.9). Step 116 adds the listing
texts (name, tagline, short / long description, tags, screenshots) on top of it; the English paragraphs marked
**[listing]** go into the long description as they are.

## What happens when you enable it — nothing until you choose Maya

**[listing]** Installing and enabling Allset does not change your keymap, preferences, theme or layout. It adds a
small Maya | Blender switch at the right of the top bar, an Edit menu entry, the shortcut Ctrl+Alt+Shift+M and, once,
a welcome dialog. Only when you click **Make Blender feel like Maya** (in the welcome dialog or in the add-on
preferences) or switch to Maya does Allset turn on its Maya-style keymap, Maya layout, menus, theme and Maya-like
preferences (navigation, undo steps, solid side panels, auto key, density, font, wireframes, splash). Before that, a
copy of everything it will change is written to the extension's user folder; switching back to Blender, disabling or
removing the extension puts your values back. Allset never saves your preferences by itself: Blender's own
Auto-Save Preferences (or you) do.

**[listing]** The Maya layout is an application template (File > New > Allset). Allset copies it to your
`scripts/startup/bl_app_templates_user/Allset` folder only when you choose Maya or click Install Maya Layout. It holds
only data (`startup.blend`, splash images, a marker file) — no code — and is deleted when you disable or remove the
extension (folders without Allset's marker are never touched).

Implementation: `src/allset/welcome.py`, `switch.py` (snapshot / restore), `first_start.py`, `app_template/__init__.py`,
tests `tests/test_step115_opt_in.py`, `tests/test_enable_disable.py`, `tests/test_step60_switch.py`.

## Changes to Blender's own UI classes

Most kit UI is its own panels, menus, gizmos and draw handlers, or is added with Blender's `append` / `prepend`
(about 20 places: the top bar switch, the Edit menu item, the Graph Editor toolbar, the Channel Box button context
menu, the Status Line at the start of the 3D View tool header, the Tool Box filter around the toolbar draw, ...).
Where Allset has to draw *instead of* Blender in its Maya areas, it uses one of the mechanisms below. All of them are
active only in Maya mode and are undone when you switch to Blender, disable or remove the extension;
`tests/test_enable_disable.py` (via `tests/kit.py` `snapshot`) fails if any of them is left behind, and
`tests/test_step115_opt_in.py` checks that other add-ons' `append`ed UI survives both directions.

### 1. Own draw swapped inside Blender's draw list (`ui/own_draw.py` and the per-editor modules)

Blender keeps a class's draw functions in a list once anything is appended (`bpy_types._GenericUI`). Allset replaces
only Blender's *own* entry in that list with a function that draws the Maya version in Allset's areas and calls
Blender's original everywhere else. Other add-ons' appended / prepended functions keep drawing, and the restore puts
Blender's function back in place even if others extended the class after Allset.

| Class | Module | Maya areas (elsewhere Blender's own draw) |
|---|---|---|
| `STATUSBAR_HT_header` | `command_line/__init__.py` | Help Line + Command Line row (Blender's when both are off) |
| `TOPBAR_HT_upper_bar` | `ui/status_line.py` | Maya menu bar / Status Line (pref "Maya Menu Bar"); `draw_left` / `draw_right` untouched |
| `OUTLINER_HT_header` | `ui/maya_outliner.py` | Outliner in View Layer mode: Maya Display / Show / Help menus |
| `IMAGE_HT_header`, `IMAGE_HT_tool_header` | `ui/shelf.py` | the Status Line / Shelf rows of the Allset layout, Maya UV Editor menus, Render View buttons |
| `GRAPH_HT_header`, `DOPESHEET_HT_header` | `ui/editor_chrome.py` | Maya Graph Editor / Dope Sheet menu bars (Timeline mode stays Blender's) |
| `VIEW3D_HT_header`, `VIEW3D_HT_tool_header` | `ui/panel_toolbar.py` | Maya panel menus / panel toolbar in Allset-layout 3D Views |
| `PROPERTIES_HT_header` | `ui/render_settings.py` | the Render Settings window only |
| `INFO_HT_header`, `TEXT_HT_header` | `ui/script_editor.py` | the Script Editor window only |

Why not `append` / `prepend`: those can only add after / before Blender's content; these areas must not show
Blender's header items next to the Maya ones (Maya menus replace them, the Status Line / Shelf rows are a whole Maya
widget).

### 2. Helpers that are not draw functions (class attribute set while in Maya mode, original put back)

No `append` API exists for these: they are methods Blender's own draw calls.

| Attribute | Module | Why |
|---|---|---|
| `TIME_HT_editor_buttons.draw_header`, `TIME_MT_editor_menus.draw_collapsible` (5.x: the Dope Sheet's) | `ui/time_slider.py` | Maya Time Slider / Range Slider layout of the Timeline header; Blender's Timeline header draw calls these helpers |
| `VIEW3D_MT_editor_menus.draw_collapsible` | `ui/panel_menus.py` | Maya panel menus (View, Shading, Lighting, Show, Renderer, Panels) in 3D View headers; an inherited classmethod, set on the class and `del`eted on restore |
| `NODE_MT_editor_menus.draw_collapsible` | `ui/hypershade.py` | Hypershade menus in Shader Editors (same mechanism) |
| `VIEW3D_PT_tools_active.tools_from_context` | `ui/toolbox.py` | the Maya Tool Box tool list, only while the toolbar draws (flag set by a `prepend` / `append` pair) |
| Move / Scale ToolDefs' `widget` in `VIEW3D_PT_tools_active._tools` | `ui/manipulator.py` | the Maya manipulator gizmo group for Blender's Move / Scale tools |

### 3. Blender panels re-registered with a wrapped `poll`

Blender has no API to hide a panel. `ui/dock_tabs.py` (3D View sidebar: only the Maya dock tabs, pref "Channel Box
Dock Only") and `ui/render_settings.py` (Render properties in the Render Settings window) re-register Blender's own
panel classes with a `poll` that also asks Allset; restoring re-registers them with their original `poll`, in
Blender's registration order (`registration_key`), and never re-registers a class its add-on already unregistered.

## Other system access

- **Keyboard state (Windows only).** `operators/keystate.py` reads `user32.GetAsyncKeyState` through `ctypes`
  (read-only, no hook) to end Maya "hold" keys whose release Blender's transform modal swallowed. On other systems, or
  if the call fails, it answers "unknown" and the hold ends on Blender's own release event (callers act only on an
  explicit "not held"; `tests/test_step115_opt_in.py`).
- **Files.** Writes only to the extension's user folder (`bpy.utils.extension_path_user`: preference snapshot, theme
  backup, shelves) and, on request, the layout template folder above and the user's chosen project folders.
- **No network**, no `sys.path` / `sys.modules` changes (step 114), no auto-updater, Python only.
