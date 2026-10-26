# Step 219 — Menus follow Maya 2026 (Issue #130)

## 한 것
- `tools/gen_menu_data.py` now builds `ui/menu_data.py` from the Maya 2026 GUI dump
  (`research/maya/re/maya2026_menus_dump.json`, menus after postMenuCommand, plug-in items included); menu sets
  still from `research/maya/menus.json`. Edit > Undo "<last command>" → "Undo"; Autodesk App Store keeps the step 111
  rename. Submenus the kit fills from the scene (`("menu", ...)` actions: recent files, character sets, workspaces,
  materials, Render Using / Test Resolution, Quick Select Sets) stay kit-filled (`kit_filled`); the hand-written
  `menu_map.CHILDREN` lists for Windows > ... Editors / Modify > Match / Snap Align / Display > HUD were dropped — the
  dump has them (only Windows > Settings/Preferences stays). Commands are the runTimeCommand MEL (dump
  `runTimeCommands`), so menu hotkeys match more items (57 → 75).
- Result: 42 menus, 2210 items, 619 option boxes (Maya 2022 static parse: 2283 / 638 with run-time padding).
  Removed (Maya 2026 has no such item): Create > Subdiv Primitives / Type, Edit > Fur, Display > Subdiv Surfaces,
  Deform > Paint Weights > Set Membership, Visualize > Create Editable Motion Trail / Open Ghosting Editor, nHair >
  Classic Hair, several Help items, Windows > Render Layer Editor / Render Layers.
- Kit mappings kept under the new labels: Polygon Disc, Polygon Type, Paint Membership, Hide Modeling Toolkit,
  Booleans > Difference (A - B), Motion Trail Editor, Ghosting Editor (also in Windows > Animation Editors), HUD Select
  Details / ViewCube, Render Setup (= View Layers), Assign New Material > New Material..., Create > Cameras > Stereo
  Camera notice.
- New items mapped (Blender engine in Maya's place): Booleans > Difference (B - A) (`allset.boolean` DIFFERENCE_BA,
  tested), Mesh > Unsmooth = Blender Un-Subdivide, Edit Mesh > Smart Extrude = kit Extrude, Modify > Zero Pivot
  (`xform -ztp`) = `allset.reset_pivot` (delegated: also resets the pivot orientation), Playback Speed > Play Every
  Frame, Free / Max Real-time = Blender Play Every Frame, Visualize > Blue Pencil = Blender Annotate tool, Windows >
  LookdevX Graph Editor = Hypershade (Shader Editor), Bifrost Graph Editor = Geometry Nodes editor, UV > 3D Grab UV
  Tool = UV Editor Grab (twin). The rest (ML Deformer, Slice / Hole Punch / Cut Out / Split Edges, Reorder Rotation,
  Bifrost / USD / MaterialX / XGen, new HUD items, Help additions) are greyed with notices (category rules) — not
  re-implemented (product principle). Dead rules removed (UV, Create/Subdiv Primitives); new notice for the bake-set
  placeholder.
- `tools/gen_menu_icons.py` `RENAMED_2026` carries the Maya 2022 icon capture over to renamed items.

## 검증 (속도 우선 규칙: 바뀐 기능만 -k)
- `tools/menu_consistency.py` 0; `tools/menu_count.py`: greyed without notice 0 (unique 1552 leaves, 808 working).
- Headless `-k step219,step101,step166,step51,step54,step108,step131,step142,step63,step136,step7,step34,step177,
  step104,step183,step162,step116,step29,step52,step190,step185,step171,step59`: 250 / 250 after fixes
  (`test_step219_menus`: structure = rebuilt from the dump, 2026 items present / 2022 items gone, no stale mapping,
  Difference (B - A) geometry).
- GUI `gui_step131_menu_icons` (+ Visualize shot) 14 / 14; shots of Deform / Visualize / Mesh checked by eye.

## 남은 것
- Full headless / GUI suites, 5.x, look_compare: Release prep (228).
- `research/maya/menus.json` still gives the menu sets; Maya 2026's own set list is not in the dump.
