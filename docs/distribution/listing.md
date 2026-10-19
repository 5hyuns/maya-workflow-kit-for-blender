# extensions.blender.org listing — Allset for Maya Users

The submission package (step 117). The user uploads it at https://extensions.blender.org/submit/ — nothing here was
uploaded. Part A = the form fields, part B = the long description (paste as it is, Markdown), part C = the media,
part D = the technical disclosure for the reviewers (step 115; the paragraphs marked **[listing]** are also in part B).
Rules followed: `docs/distribution/extensions_audit.md` (final status of every requirement there).

## A. Form fields (most come from `src/allset/blender_manifest.toml` in the zip)

| Field | Value |
|---|---|
| File | `dist/allset-0.2.0.zip` (`python tools/build.py`; `blender --command extension validate` passes) |
| Name | Allset for Maya Users |
| Tagline (≤ 64, no end punctuation) | The whole Maya workflow in Blender, in one install (50) |
| Short description (the first paragraph of B) | Not just a Maya keymap: Allset brings the whole Maya workflow to Blender — hotbox and marking menus, Channel Box and Attribute Editor, menu sets and shelves, option windows and Maya's scene concepts — and changes nothing until you choose Maya. |
| Type | Add-on |
| Tags (platform list) | User Interface, 3D View, Modeling, Animation, Rigging |
| License | GPL-3.0-or-later (code); CC0-1.0 (the kit-made images and data files, `ASSETS_LICENSE.txt`) |
| Copyright | 2026 ohnsk |
| Supported Blender | 4.5 LTS and 5.0 – 5.2 (4.5.x – 5.2.x; tested on 4.5.4, 5.0.1, 5.1.2, 5.2.2) — manifest `blender_version_min` / `max` (see part D "Versions") |
| Permissions | `files`: "Layout template, settings backup, shelves, Maya project folders" (63, no end punctuation). No `network`, no `clipboard`, no `camera` / `microphone` |
| Platforms | all (pure Python, no `platforms` entry) |
| Website / support URL | none yet (no public page or issue tracker — decision 11); add the tracker URL on the platform after the upload |
| Icon | `docs/distribution/media/icon.png` (256 × 256) |
| Featured image | `docs/distribution/media/featured.png` (1920 × 1080) |
| Preview images | 10 gallery items in part C order: `docs/distribution/marketing/clips/00_trailer.mp4` + `01–07_*.mp4` (1920 × 1080 H.264) + two stills from `docs/distribution/media/` |

## B. Long description

**Not just a Maya keymap: Allset brings the whole Maya workflow to Blender** — hotbox and marking menus, Channel Box
and Attribute Editor, menu sets and shelves, option windows and Maya's scene concepts — and changes nothing until you
choose Maya.

Moving from Maya to Blender is rarely about keys alone. It is the hotbox under the space bar, the right-click marking
menu over an object, the Channel Box where you type `+=5`, the menu sets and shelves, the option box next to a menu
item, and objects that behave like Maya transforms — Freeze, History, Center Pivot, groups, centimetres, `pCube1`.
Allset rebuilds those, one workflow at a time, on top of Blender's own tools.

### Navigate & Select

- Alt + LMB / MMB / RMB tumble, track and dolly; F / A / Shift+F frame selected / all in the visible part of the view;
  Space taps to four views; view undo.
- Q W E R T Y tools, Maya's selection modifiers (Shift toggles, Ctrl deselects, Ctrl+Shift adds), F8 object / component
  toggle and F9–F12 component modes, pre-selection highlight, edit-mode box select through occluded elements like Maya, selection priority.
- Hold keys as in Maya: X / C / V snap while held, D / Insert edit the pivot, B soft select, J step snap; arrow-key
  pick-walk; Maya selection colours (lead green, others white) and the Move / Scale manipulator.

### Hotbox & Marking Menus

- Space-hold hotbox with every menu of the current menu set, Recent Commands and the marking menu zones.
- Right-click, Shift+right-click, Ctrl+right-click marking menus over objects and components, in Maya's radial
  positions, with gestures, click mode, submenus and option boxes; Shift+Q / Alt+Q / Shift+S hold menus.

### Channel Box & Attribute Editor

- Channel Box / Layer Editor: Translate / Rotate / Scale / Visibility of every selected object, SHAPES and INPUTS
  (history nodes), keyed / locked / driven colours, `+=5` `*=2` entry, the viewport middle-drag
  virtual slider for selected channels, Channels menu and
  right-click menu, display layers.
- Attribute Editor with Maya's node tabs and sections (transform, shape, history, material, shading group), Notes.
- Maya's docking: Channel Box / Attribute Editor / Modeling Toolkit share one tab stack next to the viewport and tear
  off into floating windows by their ::::: handle (Ctrl+A toggles); Outliner and Tool Settings dock left.

### Menu Sets & Shelves

- Maya's menu bar with the Modeling / Rigging / Animation / FX / Rendering menu sets (F2–F6), Maya's menu order and
  names, Maya hotkeys shown in the menus, dotted tear-off lines.
- Status Line, Shelf with the factory shelves (Polygons, Rigging, Animation, Rendering, FX ...) and your own Python
  shelves, Time Slider and Range Slider, Help Line and a Python Command Line with a small `maya.cmds` look-alike.
- Maya editors where Blender has a counterpart: Graph Editor and Dope Sheet menus, UV Editor, Hypershade, Render
  Settings, Script Editor, Modeling Toolkit.
- Every Maya menu item Blender cannot do is shown greyed with a one-line note saying why and what to use instead.

### Maya concepts

- Freeze Transformations (channels back to 0 / 0 / 1, pivot kept), Reset Transformations, Center Pivot, Delete History
  and Delete by Type, Maya-style parenting (P / Shift+P keep the Channel Box values), Ctrl+G groups, Duplicate
  Special.
- Centimetres: the Allset layout uses Maya's cm display and Maya sizes for everything it creates; an optional "Maya
  Units" preference sets 1 Blender unit = 1 cm.
- Maya names (`pCube1`, `pCubeShape1`, `group1`, `polySmooth1`, `joint1`, `lambert1`), the default material, Maya's
  extrude history you can edit afterwards, Smooth Mesh Preview (1 / 2 / 3), Maya projects with Set Project.

### Option windows

- The option box (❒) on a menu item opens Maya's option window with Maya 2022's factory values: Save Settings, Reset
  Settings, Apply and the command button, and a plain click then uses your saved values. Polygon primitives,
  Duplicate Special, Freeze, Extrude, Bevel, Bind Skin, constraints, Set Key, UV projections and more.

### What happens when you enable it — nothing until you choose Maya

Installing and enabling Allset does not change your keymap, preferences, theme or layout. It adds a small
Maya | Blender switch at the right of the top bar, an Edit menu entry, the shortcut Ctrl+Alt+Shift+M and, once, a
welcome dialog. Only when you click **Make Blender feel like Maya** (in the welcome dialog or in the add-on
preferences) or switch to Maya does Allset turn on its Maya-style keymap, Maya layout, menus, theme
("Studio Grey (Maya-inspired)") and Maya-like preferences (navigation, undo steps, solid side panels, auto key,
density, font, wireframes, splash). Before that, a copy of everything it will change is written to the extension's
user folder.

### How to go back

- Click **Blender** in the Maya | Blender switch (or Ctrl+Alt+Shift+M): Blender's keymap, theme, layout and every
  preference Allset changed come back; switch again whenever you like.
- **Revert Maya Look** in the add-on preferences removes the theme, splash and layout template only.
- Disabling or removing the extension puts your values back the same way and deletes the layout template. Allset never
  saves your preferences by itself: Blender's own Auto-Save Preferences (or you) do.

### Files it writes outside the extension

- `scripts/startup/bl_app_templates_user/Allset/` — the Maya layout (File > New > Allset): only data
  (`startup.blend`, splash images, a marker file), copied when you choose Maya or click Install Maya Layout, deleted
  when you disable or remove Allset (folders without Allset's marker are never touched).
- The extension's user folder (Blender's `extension_path_user`): preference snapshot, theme backup, your shelves.
- Maya projects: the file dialogs open in the current project like Maya's. With no project set, the default project
  `Documents/allset/projects/default` is made the first time a project-aware dialog opens; Set Project / Project
  Window make folders only where you choose.
- Playblast writes its movie to Blender's temporary folder; exports and saves go where you choose.

### Technical notes

- **Python `exec`**: only text you type or write yourself — the Python Command Line, your Python shelf buttons and the
  Script Editor run it in their own namespace (with the `maya.cmds` look-alike), exactly like Blender's Python
  console. Allset never downloads or generates code.
- **`bpy.utils.execfile`**: the Maya-style keymap is built from Blender's own bundled Industry Compatible keymap data
  (`presets/keyconfig/keymap_data/industry_compatible_data.py` of the running Blender), loaded the way Blender's
  keymap preset loads it, then patched. No keymap data is copied into the extension.
- **`ctypes` (Windows only)**: one read-only `user32.GetAsyncKeyState` call, to end Maya hold keys (D, X, C, V, B ...)
  whose key release Blender's transform tool swallows. No hook, nothing written; elsewhere Blender's own key-release
  event is used.
- **Blender UI classes**: most of Allset's UI is its own panels, menus and gizmos, or `append` / `prepend`. In Maya
  areas it draws instead of a few Blender headers and re-registers some panels with a wrapped `poll` — only in Maya
  mode, put back when you switch to Blender, disable or remove it; other add-ons' additions keep drawing.
- No network access, no auto-updater, no `sys.path` / `sys.modules` changes. Help menu items open Blender manual
  pages in your web browser when you click them.

### Limits

Blender is Z-up and has one pivot per object; dragging over a field with the middle mouse, Maya's MEL, side tabs and
OS-level docking of panels need Blender's C++ code and are not imitated. Each greyed menu item says what to use
instead.

### Trademarks

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc., and/or its subsidiaries and/or affiliates
in the USA and/or other countries. This project is an independent, free and open-source (GPL) extension for Blender.
It is not affiliated with, endorsed by, sponsored by, or otherwise approved by Autodesk, Inc. or the Blender
Foundation. It contains no Autodesk code, icons, MEL scripts or other Autodesk assets; references to Maya are solely to
describe compatibility and the intended audience.

## C. Media (`docs/distribution/media/`: Blender screenshots taken with Allset, no Maya or Blender logo, no Maya capture)

Store rules (step 121, sources in `docs/distribution/marketing/references.md` §1): icon 256 × 256 PNG; featured
image JPEG / PNG / WebP ≥ 1920 × 1080, 16:9 (also the social card); previews 16:9, each **a JPEG / PNG / WebP image
or an MP4 video** (no GIF, no WebM), ≥ 1 required, no count or size cap in the site code, caption ≤ 255 characters;
a video's poster is its first frame. GIFs can only be linked in the description, which the moderation guideline
discourages ("no heavy image (.gif images in particular)").

Regenerate with `python tools/make_listing_media.py` (= `tools/marketing/make_marketing.py`: a GUI Blender in a clean
sandbox with the built zip, Maya theme and Maya's factory background, a scene of CC0 models from Poly Haven, Kenney
and Quaternius — `docs/distribution/marketing/CREDITS.md` — then Pillow captions in the visual system of
`docs/distribution/marketing/style.md`, copy from `copy.md`). The icon and featured image are kit-made; the scenes use
the CC0 models credited at the end of part B (add the copy.md "Credits line" there when pasting).

Gallery (step 123, references.md §5 — `delegated`: seven feature clips instead of six because the step 123 request
names seven topics; the "switch" still `10` is replaced by clip 7, so the gallery stays at 10 items with two stills).
Paths below are under `docs/distribution/`. Clips: `python tools/marketing/make_clips.py`; the MP4s carry English
caption bands, key chips and a drawn cursor; no audio. **GIFs (`marketing/gif/`) are never uploaded here** — they are
for the GitHub README and social posts (`marketing/README.md`).

| # | File | Kind | Caption (≤ 255 characters) |
|---|---|---|---|
| – | `media/icon.png` | icon 256 × 256 | — |
| – | `media/featured.png` | featured image 1920 × 1080 | — (key visual: name + tagline + two real screens) |
| 1 | `marketing/clips/00_trailer.mp4` | MP4 38.8 s (poster = key visual title card) | Allset in 40 seconds: hotbox, marking menus, Channel Box keys, Maya navigation, pivot snapping, rigging, and the one-click switch back to plain Blender. |
| 2 | `marketing/clips/01_hotbox.mp4` | MP4 6–9 s | Tap Space to toggle one view and four views; hold Space for the hotbox with every menu of every menu set. Here: Select > All, straight from the hotbox. |
| 3 | `marketing/clips/02_marking_menu.mp4` | MP4 6–9 s | Right-click over an object for its marking menu in Maya's positions: drag to Vertex for component mode, right-click again for Object Mode. |
| 4 | `marketing/clips/03_channel_box_keys.mp4` | MP4 6–9 s | S keys every channel and the Channel Box turns red; type +=90 into Rotate Z, right-click > Key Selected keys only that channel, then scrub the Time Slider. |
| 5 | `marketing/clips/04_navigation.mp4` | MP4 6–9 s | Alt + left drag tumbles, Alt + middle drag tracks, Alt + right drag dollies; click an object and press F to frame it, A to frame everything. |
| 6 | `marketing/clips/05_pivot_snap.mp4` | MP4 6–9 s | Insert edits the pivot; hold V while dragging and it snaps to a vertex of the drill. Insert again, and the drill rotates around its new pivot. |
| 7 | `marketing/clips/06_rigging.mp4` | MP4 6–9 s | From the Rigging shelf: Create Joints by clicking, an IK Handle from shoulder to wrist, Bind Skin, pull the handle, then Paint Skin Weights. |
| 8 | `marketing/clips/07_switch.mp4` | MP4 6–9 s | One click on Blender in the top-bar switch gives plain Blender back with the same scene; one click on Maya brings the Maya layout, keys and colors back. |
| 9 | `media/03_channel_box_ae.png` | still 1920 × 1080 | Channel Box and Attribute Editor: keyed channels in red, +=5 and *=2 entry, Maya node tabs, docked next to the viewport. |
| 10 | `media/04_menus_shelves.png` | still 1920 × 1080 | Rigging menu set (F3) with option boxes that open Maya option windows with Maya 2022's factory values, and the Rigging shelf. |

The other step 122 stills (`01`, `02`, `05`–`10`) stay in `docs/distribution/media/` for other uses (press, README).

## D. Technical disclosure for the reviewers

### Versions

`blender_version_min = "4.5.0"`, `blender_version_max = "5.3.0"` (exclusive): 4.5.x – 5.2.x. Target 4.5 LTS
(decision 4); step 118 made 5.0 – 5.2 work and measured every minor version's latest release (4.5.4, 5.0.1, 5.1.2,
5.2.2): the full headless suite, the GUI suite and the clean install → enable → disable → remove round trip pass on each
(`docs/compat_5x.md`, version differences in one module, `compat.py`). Blender 4.2.23 LTS fails 25 of 869 tests (the
layout template is saved by 4.5, brush assets are 4.3+, file I/O options differ), so 4.2 – 4.4 are not offered the
extension, and a Blender after 5.2 is not offered it until it is measured the same way.

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
