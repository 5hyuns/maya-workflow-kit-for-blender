# Changelog

All notable changes to Allset for Maya Users (called Maya Kit before step 111). Format: [Keep a Changelog](https://keepachangelog.com/), versions follow
[Semantic Versioning](https://semver.org/). Step documents: `docs/steps/step_<n>.md`.

## [Unreleased]

### Changed
- **Renamed to Allset for Maya Users** (step 111, decision 12): extension id `allset`, tagline "The whole Maya
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
  modifiers, 4/5/6/7 display modes, Ctrl+G group, keymap mapping document (`docs/keymap_mapping.md`).
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
