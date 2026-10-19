# Changelog

All notable changes to Allset for Maya Users (called Maya Kit before step 111). Format: [Keep a Changelog](https://keepachangelog.com/), versions follow
[Semantic Versioning](https://semver.org/). Step documents: <n>.md`.

## [Unreleased]

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
