# Changelog

All notable changes to Maya Workflow Kit (called Allset for Maya Users in steps 111–124 and Maya Kit before step 111). Format: [Keep a Changelog](https://keepachangelog.com/), versions follow
[Semantic Versioning](https://semver.org/). Step documents: <n>.md`.

## [Unreleased]

### Changed
- Quad Draw, Create Polygon and Append to Polygon are Maya-style kit tools with Maya's clicks, modifier keys and Tool
  Settings instead of Blender's Poly Build (#30).
- Insert Edge Loop inserts where you click (one click), Offset Edge Loop drags two loops, Slide Edge slides with the
  middle mouse button; Maya Tool Settings and the Offset Edge Loop window (#31).
- The Deform menu creates Maya-like deformers (Lattice fitted around the selection, Delta Mush, Wrap, ShrinkWrap,
  Nonlinear with handles, Cluster, Soft Modification, Texture, Curve Warp) with Maya option windows, Channel Box INPUTS
  attributes and Paint Weights on the deformer's own weights (#34).

## [0.3.0] — 2026-10-24

The Maya parity release after the eighth audit (steps 133–143). Blender 4.5 LTS through 5.2.x. Quad Draw, the
edge-loop tools and the Deform menu move to 0.4.0 (#30 #31 #34).

### Changed
- **Viewport looks like Maya without a theme** (#58 #59 #61 #75 #76): kit-drawn lead green / white selection,
  Maya component colours, Maya grid, no 3D cursor in the Maya layout, Maya Move / Scale manipulator axis colours and
  dark-blue dormant wireframe; no redo panel after display / mode keys; Smooth Mesh Preview shades smooth.
- **Dock and Channel Box** (#55 #60 #78): INPUTS collapsed until clicked, Layer Editor always visible, wheel scroll;
  Maya's vertical tab strip with a dock as narrow as Maya's (Channel Box) that widens for the Attribute Editor.
- **Marking menus** (#56 #62 #74): stay inside the window, 128 → 73 greyed entries (the rest explain why), Ctrl+RMB
  convert menu on meshes.
- **Animation / render** (#66 #67 #71): Graph Editor values in centimetres, Render Current Frame through the view
  camera or Maya's persp, Maya Blinn / Phong / light decay and render size defaults.
- **Scenes and files** (#57 #63 #64 #69): Save / Don't Save / Cancel on New Scene, the Maya layout after Open, tool
  settings kept across New / Open, FBX / OBJ / Alembic / USD round trips with Maya's axes, scale and names.
- **Edit Mesh / UV** (#16 #68 #70): Connect, Merge, Symmetrize and Smooth give Maya's results; Ctrl+B and Ctrl+E on
  edges / vertices act at once and stay editable; UV Automatic / Contour Stretch from object mode.
- **Maya option windows** (#32 #33 #35): 26 more windows with Maya 2022's fields and factory defaults (Create Joints,
  IK Handle, Bind / Unbind / Copy / Paint Skin Weights, Blend Shape, Parent, Cut / Copy / Paste / Delete / Snap / Scale
  Keys, Connect, Circularize, Make Hole, Insert Edge Loop, Aim / Pole Vector / Scale constraints, Duplicate Special);
  Aim aims +X with world up Y like Maya; Key > Scale Keys is new.
- **Keys and selection** (#65 #72 #73): Ctrl+A switches Attribute Editor / Channel Box in every mode, UV Editor
  Alt+RMB dolly, 13 Select / Ctrl+RMB conversions (Grow / Shrink Along Loop, perimeters, To Face Path, To UVs ...),
  joint names restart at joint1, Gravity / Newton fields with Maya magnitudes; an undo-depth hint (Blender keeps 32
  steps unless you raise it).
- **UI fit and icons** (#54 #77): the menu bar folds into » at 150 % UI scale, Set Driven Key fits, 485 more Maya menu
  icons.
- Store media, marketing images and clips retaken in Blender's own theme (#41).

### Fixed — reported by users
- Maya mode failed to switch on when another add-on's Render panel module had a non-list `classes` (#79).
- Double-click edge loop select raised an error in Blender 5.1 / 5.2 (#84).
- After extruding, Q / W / E / R bring the Move manipulator back; F12 no longer leaves UV sync on for F9–F11 (#80).

### Known issues
- Menu option boxes (❒) open on press-and-hold → Option Box, not on a click (#82, 0.4.0).
- Narrow dock truncates a few labels at 125 % (#85); Channel Box spacing at 150 % (#83); redo panel over the shelf
  after Create Joints (#86); Channel Box channel-name RMB shows Blender's menu (#87).

## [0.2.1] — 2026-10-21

A bug-fix and store-compliance release (steps 125–132). Blender 4.5 LTS through 5.2.x.

**Thank you** to everyone who used the kit in real work and reported what felt wrong — most fixes below come from
those reports (labelled `user-report` on GitHub).

### Changed — store review (extensions.blender.org, #40)
- **Nothing outside the extension changes any more** (#40, #42, #43, #46): no theme is shipped or applied, Blender
  preferences and your active keymap are never written (Maya keys are add-on keymap items that disappear when Maya mode
  or the extension is off), no app template is copied into your scripts folder, no `exec` / `eval` or import hooks
  (scripts run as Text blocks through Blender's Run Script). Disabling or removing the extension is a plain unregister.
  Recommended theme / navigation settings are listed in the README instead.
- Alt+RMB dolly works without Blender's zoom preference (#51); Maya menu items that used to write preferences open
  Blender's Preferences instead (#43).
- Store tags: User Interface only.
- **Renamed to Maya Workflow Kit** (step 125,  —  revision): store / display
  name "Maya Workflow Kit" (no "Blender" in the store name), repository "Maya Workflow Kit for Blender"
  (`maya-workflow-kit-for-blender`), release zip `maya-workflow-kit-<version>.zip`, default project folder
  `Documents/Maya Workflow Kit/projects/default`. Unchanged: extension id `allset` (updates keep working), package
  `src/allset`, `allset.` / `ALLSET_` prefixes, tagline. README rewritten for GitHub.

### Fixed — reported by users
- Soft Select: middle-mouse drag changes the falloff radius, soft select is off by default (#1); vertices are coloured
  by influence (#2).
- Tool Box: double-clicking a tool opens its Tool Settings (#3).
- Torn-off panels open at a size that fits their content (#4).
- Marking menus no longer close while dragging or over the Time Slider (#5).
- Channel Box: drag over value fields to select channels; one typed value goes into all of them (#6).
- Layer Editor rows, V / P boxes, toolbar icons and tabs follow Maya (#7).
- Quick Layout: Single Perspective shows the perspective view; Four View back to persp works (#8).
- F frames with the camera you look through (#9).
- Viewport panel toolbar buttons toggle on and off and all do something (#10).
- Primitives show their creation INPUTS in the Channel Box (#11) and use Maya's topology (cap fans, Subdivisions
  Caps) (#12).
- UV Editor checker toggles off again (#13).
- Material colour changes show in shaded mode (#14).
- Double-click loop selection and "pick two, select the run between" for edges / vertices / faces (#22).
- **Icons**: every shelf button, Status Line / panel toolbar glyph, Tool Box tool, Layer Editor button and Outliner
  set / camera row is redrawn after Maya 2022's icons (kit-drawn, one picture per button, sharp at 100 / 125 / 150 %);
  190 Maya menu items show icons (#23).
- **Hypershade** opens as its own window in Maya's layout: Browser, Create, Material Viewer, Graph with Maya's toolbar,
  Property Editor (#25).
- Multi-Cut works like Maya's (click / drag points, Shift snap %, Ctrl loop cut, Backspace, RMB finish) (#27); tools
  have Maya Tool Settings (#28).
- Auto Key button (#37) and key ticks on the Time Slider (#38).
- Crash when closing an editor window opened from a Maya menu within 2 s (#36).

### Fixed — found by our own audit
- Soft Select shared between object and component mode (#15); Ctrl+D in component mode duplicates the object (#17);
  Delete History works in component mode (#18); Edit menu items work in component mode (#39).
- Switching Maya → Blender leaves no empty Maya strips (#19).
- Paint Skin Weights normalizes like Maya (#20).
- Torn-off Display menu: Hide / Show work (#21).
- Status Line IPR off restores the previous shading (#24).
- One Maya visibility: h, Channel Box Visibility and display layer V agree (#26).
- Select / Lasso / Paint Selection Tool Settings have Maya's sections (#29).
- Viewport background / selection colours without the kit theme (#45), Hypershade opening (#47), top-bar test and
  dogfood session after the store changes (#48, #49, #50).
- Blender 4.5 crashed on quit with the new Tool Box vector icons (fixed before release, step 131).
- Ctrl+N (New Scene) opens a new scene in the Maya layout again, like File > New Scene (#44).
- At 125 % UI scale, opening and closing Tool Settings no longer narrows the viewport (#53).
- The viewport panel toolbar folds the groups that don't fit into a Maya-style » menu, so every button is reachable at 125 % / 150 % (#52).

## [0.2.0] — 2026-10-19

The first version prepared for extensions.blender.org (steps 14–117). Blender 4.5 LTS (4.5.x).

### Added
- **Navigate & Select**: framing in the visible part of the view (17), Maya mesh keys and convert selection (18), edit-mode
  selection through occluded elements and pre-selection (30, 74), selection priority (76), component pick-walk and
  axis lock (39), Move / Scale manipulator with Maya pivot editing (59, 77, 94), soft select and symmetry (36, 63),
  selection masks (93), snap holds (95).
- **Hotbox & Marking Menus**: menus kept inside the view (33), whole-window drawing and RMB fidelity (52), more
  marking menus (78, 94).
- **Channel Box & Attribute Editor**: text entry with `+=` / `*=` (38), joints and pose bones (55), constraints, Set
  Driven Key (62), extrusion history tab (65, 106), default material and shading groups (100), Maya docking model with
  tear-off panels and floating windows (116).
- **Menu Sets & Shelves**: every factory shelf button in its Maya slot (109), menu hotkeys in the labels (108), honest
  greyed items with notes (54, 101), Graph Editor / Dope Sheet / UV Editor / Hypershade / Render Settings / Script
  Editor menus (104, 105), Time Slider and Range Slider (20, 56, 73), Modeling Toolkit (63), Tool Settings (106), Maya
  top area (113), tear-off menus (116).
- **Maya concepts**: Maya length units (21), Smooth Mesh Preview (15), visibility (16), Combine / Separate / Mirror /
  Boolean (63), editable extrude history (65), UV tools (66, 79), render and look-dev (67), FX scale (68), projects and
  references (69), playblast (70), sets (96), file import / export (102), rigging (57, 58, 110).
- **Option windows** with Maya 2022's factory values, Save / Reset Settings and Apply (103).
- **Listing package** (117): `docs/distribution/listing.md` (form fields, long description, media captions, technical
  disclosure), `docs/distribution/media/` (icon, featured image, six workflow screenshots; `tools/make_listing_media.py`).

### Changed
- **Opt-in**: enabling changes nothing until you choose Maya; no automatic preference saves; the layout template holds
  no code and is removed on disable (115). Maya | Blender switch (60).
- Supported Blender is now **4.5.x** (was 4.2.0 – 5.2.x): Blender 4.2.23 fails 25 of 869 headless tests and 5.0.1
  fails 19 (layered actions, layout template dock), so the manifest offers 4.5.0 – 4.5.x only until a 5.x update (117).
- Permission reason: "Layout template, settings backup, shelves, Maya project folders"; tag Rigging added (117).
- Extension guidelines: no `sys.modules` entries, CC0 assets, no `bl_info` in the extension build (114); the
  moderation ruff command passes on the extension source (117).
- **Renamed to Allset for Maya Users** (step 111, ): extension id `allset`, tagline "The whole Maya
  workflow in Blender, in one install", Python package `src/allset`, operator / class prefixes `allset.` /
  `ALLSET_`, app template `Allset` (an old `MayaKit` template install is removed), keymap "Maya-style", theme
  "Studio Grey (Maya-inspired)", Help > Blender Extensions; trademark notice in the README and the preferences.

## [0.1.0] — 2026-10-16

First release (Blender 4.2+, built and tested on Blender 4.5.4 LTS).

### Added
- **Packaging** (step 1, 13): Blender extension `maya_kit` plus a legacy add-on zip from the same source
  (`tools/build.py`); `blender --command extension validate` passes; GPL-3.0-or-later `LICENSE`;
  `tools/release_check.py` (build → validate → clean-config install + enable → screenshot set).
- **Maya keymap** (step 2): "Maya" keyconfig generated from Industry Compatible data with Maya patches, Maya selection
  modifiers, 4/5/6/7 display modes, Ctrl+G group, keymap mapping document ().
- **Hold / tap keys** (step 3): X/C/V/J snapping while held, D/Insert pivot editing, B soft select, A tap, arrow pick-walk.
- **Camera and view feel** (step 4): Maya navigation preferences preset with backup/restore, ortho tumble lock,
  Shift+F/Shift+A framing in all views, view undo, Space four views, 1/2/3 smooth preview, F7–F11 component modes.
- **Layout and theme** (step 5): Maya General layout application template, Maya grey theme.
- **Channel Box and Layer Editor** (step 6): multi-object editing, viewport MMB virtual slider, Channels menu,
  display layers on collections.
- **Top UI** (step 7): Maya menu bar and menu sets, Status Line, Python command line with a `cmds` shim, Help Line.
- **Marking menus** (step 8) and **hotbox / marking menu engine** (step 9): Maya radial layouts, gestures, click mode,
  in-place submenus, option boxes; Space-hold hotbox.
- **Scene concepts** (step 10): Freeze Transformations (pivot kept), Reset Transformations, Center Pivot, Delete History
  and Delete (All) by Type, Maya-style parenting (P / Shift+P), Duplicate Special / with Transform, Maya creation names
  and defaults, optional Maya units.
- **Outliner and Attribute Editor** (step 11): sidebar Outliner (DAG, shapes, rename), Attribute Editor node tabs with
  Maya template sections, Ctrl+A dock toggle, Ctrl+Shift+A / Alt+D selection keys.
- **Shelf** (step 12): Status Line + Shelf strip, Maya factory shelves as Blender operators, user Python shelves.

### Fixed (found by the clean-install release check, step 13)
- Installing and enabling from the command line left the first GUI start on the Blender keymap.
- Installing the layout in a brand-new config did not run the template's script until a restart, so loading the layout
  dropped the Maya keymap.

### Known limitations
- Things Blender only allows in C++ (Y-up, MMB-drag on fields, gizmo extension, new region types, Outliner tree drawing,
  timeline drawing, separate pivots, MEL) — see README "Limits".
