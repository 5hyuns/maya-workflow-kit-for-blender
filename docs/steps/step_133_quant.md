# Step 133 부록 — 재점검 8차 수치 감사 (QUANT 레인)

step 98 부록 (`docs/steps/step_98_quant.md`) 의 수치를 오늘 master 에서 다시 센 결과. 칭찬 없이 차이만. 계산 스크립트와 원자료는 저장소 밖
`tmp/audit133_quant/` (`menus_per.py`, `live_vs_kit.py`, `marking_cmp.py`, `probe_quant.py` + `run_probe.sh`, `probe.json`, `menus_detail.json`).

Read-only audit, 2026-10-22, HEAD 1ac4b77 (0.2.1). Method:

- Menus: `python tools/menu_count.py --greyed` (the step 98 rules, now a tool) plus `menus_per.py`, which uses the same
  `menu_count.leaves()` per top menu. "Working" = path in `menu_map.MAP`; "greyed + notice" = `notices.greyed_notice(path)`
  (exact NOTICES or a CATEGORIES prefix, step 101).
- Option boxes, shelves: `probe_quant.py` run by `tests/_bootstrap.py` in a headless Blender 4.5 (`--factory-startup`,
  `BLENDER_USER_*` = `tmp/audit133_quant/sandbox/`, created first) with `dist/maya-workflow-kit-0.2.1.zip` installed
  (built after HEAD; `diff -rq` against `src/allset` = identical). Kinds from `ui/menu_sets.option_kind`; shelves from
  `ui/shelf.all_buttons` + `button_notice`.
- Hotkeys: `python tools/gen_keymap_mapping.py` (exit 0, `docs/keymap_mapping.md` unchanged, nothing to restore).
- Live Maya top-level items: `research/maya/screens/audit7/maya/_audit7.json` (the step 98 Qt capture) vs the first level
  of `ui/menu_data.MENUS` + `menu_map.EXTRA` (labels normalised: `...`, `(R)`, case).
- Marking menus: `marking/menus.py` at 8936c73 (step 98) and now, both imported as plain modules (the file has no imports).

## 0. Headline (step 98 → now)

| Metric | Step 98 (8936c73) | Now (1ac4b77) |
|---|---|---|
| Unique kit menu leaves (main menu sets) | 1251 | **1318** |
| ... working (mapped, incl. with notice) | 370 (29.6 %) | **587 (44.5 %)** = 495 + 92 with a notice |
| ... greyed with a notice | 15 | **731** |
| ... greyed without a notice | **866** | **0** |
| Leaves counted per set (shared Deform / Constrain per set) | 1417 | 1486, working 662 (44.5 %) |
| `menu_map.MAP` / `notices.NOTICES` (+ `CATEGORIES`) | 370 / 41 | 1082 (incl. editor menu bars) / 128 + 183 prefix rules |
| Editor menu bars (Graph Editor, Dope Sheet, UV, Hypershade, Render Settings, Script Editor) | none | 914 leaves, 495 working (54 %), 419 greyed + notice, 0 without |
| Kit option-box paths (`menu_data.OPTION_BOXES`) | 500 | 507 |
| ... real options window / dialog | **6** | **48 paths** (29 kit option windows + 19 operator dialogs), **38 distinct** |
| ... tool + Tool Settings | 11 | 14 |
| ... run + Adjust Last Operation | 156 | 151 |
| ... "Blender has no settings" window (`option_generic`) | – | 62 |
| ... dead (box on a greyed item) | **323** | **231** (46 %) |
| ... box icon on a submenu, no box | 3 | 0 (`Mesh/Cleanup...` opens a Blender menu) |
| Shelves (8 factory tabs, 203 buttons) | 98 drawn, 105 left out without a trace | **151 working (74 %), 52 greyed with a notice, 0 without** (every button keeps its Maya slot) |
| Hotkeys (468 rows): implemented / IC match / n/a / unreviewed / macOS | 155 / 15 / 11 / **219** / 68 | **199 / 30 / 171 / 0 / 68** |
| Windows menu (leaves) | 68: 34 work (9 notice), 3 greyed + notice, **31 greyed without** | 74: **47 work (9 notice), 27 greyed + notice, 0 without** |
| Live Maya top-level items missing from kit menus | 64 (incl. MASH 4, Audio 7, Generate 17, Stereo 4) | **11** (MASH 4, nCloth / nConstraint texture↔vertex map 2 + 2, 3 run-time labels) |
| Marking menus (26 kit menus) | 298 working / 112 greyed / 54 submenus | **unchanged** (only the Multi-Cut target changed, step 129) |
| Maya hotkey marking menus (11) | 8 bound | 8 bound (`n` traversal, `u` paint ops, `o` poly brush = n/a) |
| AE dedicated layouts (`ae_layout.BY_KIND`) | 16 kinds | 21 kinds + 18 creation-node tabs (`prim_history`) + `polyExtrudeFace` + shadingEngine tab + 28 modifier types named as 21 Maya node types |

Notes on the counts:

- `option_kind` reports Skeleton/Orient Joint and Mirror Joints as "redo" (no `option_box` prop, no `option_windows` spec),
  although both always open `invoke_props_dialog` (step 57). Step 98 counted them as real dialogs, so the comparable
  real-dialog figure is 50 paths / 40 distinct.
- The leaf count grew (1251 → 1318) because step 101 restored run-time items (Audio 0 → 9, Generate 33 → 50, Cache 13 → 24,
  Stereo 0 → 6, Modify > Naming, Playback Speed, Help). Step 98's lost Modify > Prefix Hierarchy Names / Search and Replace
  Names are now present and working.

## 1. Menus per menu set

| Set | Leaves 98 → now | Working 98 → now | Greyed + notice 98 → now | Greyed, no notice 98 → now |
|---|---|---|---|---|
| Common | 435 → 449 | 44 % → **56 %** | 5 → 198 | 237 → 0 |
| Modeling | 331 → 349 | 22 % → **47 %** | 1 → 185 | 256 → 0 |
| Rigging | 189 → 190 | 21 % → **39 %** | 1 → 115 | 149 → 0 |
| Animation | 164 → 180 | 32 % → **49 %** | 3 → 91 | 108 → 0 |
| FX | 205 → 205 | 14 % → **18 %** | 2 → 168 | 174 → 0 |
| Rendering | 57 → 63 | 21 % → **24 %** | 3 → 48 | 42 → 0 |
| (always visible) Cache + Help | 36 → 50 | 0 % → **62 %** | 0 → 19 | 36 → 0 |

### 1a. Per top menu

"Working" = mapped + mapped with a notice. Deform and Constrain are shared and listed once.

| Set | Menu | Leaves 98 → now | % working 98 → now | Working (+ notice) | Greyed + notice | Greyed, no notice | Option boxes |
|---|---|---|---|---|---|---|---|
| Common | File | 27 → 30 | 63 % → 80 % | 15 + 9 | 6 | 0 | 12 |
| Common | Edit | 68 → 68 | 62 % → 65 % | 43 + 1 | 24 | 0 | 19 |
| Common | Create | 68 → 70 | 44 % → 53 % | 29 + 8 | 33 | 0 | 44 |
| Common | Select | 80 → 81 | 39 % → 48 % | 39 + 0 | 42 | 0 | 3 |
| Common | Modify | 88 → 90 | 32 % → 41 % | 33 + 4 | 53 | 0 | 31 |
| Common | Display | 36 → 36 | 31 % → 64 % | 20 + 3 | 13 | 0 | 2 |
| Common | Windows | 68 → 74 | 50 % → 64 % | 38 + 9 | 27 | 0 | 1 |
| Modeling | Mesh | 26 → 26 | 54 % → 81 % | 21 + 0 | 5 | 0 | 20 |
| Modeling | Edit Mesh | 28 → 28 | 64 % → 89 % | 25 + 0 | 3 | 0 | 18 |
| Modeling | Mesh Tools | 36 → 36 | 25 % → 81 % | 20 + 9 | 7 | 0 | 35 |
| Modeling | Mesh Display | 39 → 39 | 18 % → 38 % | 15 + 0 | 24 | 0 | 10 |
| Modeling | Curves | 36 → 36 | 11 % → 44 % | 14 + 2 | 20 | 0 | 24 |
| Modeling | Surfaces | 41 → 41 | 0 % → 20 % | 4 + 4 | 33 | 0 | 37 |
| Modeling | Deform | 73 → 74 | 15 % → 43 % | 18 + 14 | 42 | 0 | 47 |
| Modeling | UV | 19 → 19 | 58 % → 84 % | 16 + 0 | 3 | 0 | 11 |
| Modeling | Generate | 33 → 50 | 0 % → 4 % | 2 + 0 | 48 | 0 | 8 |
| Rigging | Skeleton | 54 → 54 | 13 % → 24 % | 10 + 3 | 41 | 0 | 8 |
| Rigging | Skin | 28 → 28 | 43 % → 64 % | 18 + 0 | 10 | 0 | 13 |
| Rigging | Constrain | 20 → 20 | 40 % → 55 % | 8 + 3 | 9 | 0 | 17 |
| Rigging | Control | 14 → 14 | 7 % → 7 % | 0 + 1 | 13 | 0 | 3 |
| Animation | Key | 41 → 41 | 41 % → 49 % | 20 + 0 | 21 | 0 | 12 |
| Animation | Playback | 25 → 26 | 64 % → 73 % | 18 + 1 | 7 | 0 | 1 |
| Animation | Audio | 0 → 9 | 0 % → 56 % | 4 + 1 | 4 | 0 | 0 |
| Animation | Visualize | 5 → 10 | 20 % → 20 % | 2 + 0 | 8 | 0 | 4 |
| FX | nParticles | 25 → 25 | 16 % → 28 % | 5 + 2 | 18 | 0 | 15 |
| FX | Fluids | 25 → 25 | 8 % → 16 % | 2 + 2 | 21 | 0 | 20 |
| FX | nCloth | 13 → 13 | 23 % → 38 % | 2 + 3 | 8 | 0 | 3 |
| FX | nHair | 54 → 54 | 2 % → 4 % | 1 + 1 | 52 | 0 | 13 |
| FX | nConstraint | 19 → 19 | 0 % → 0 % | 0 + 0 | 19 | 0 | 11 |
| FX | nCache | 20 → 20 | 15 % → 15 % | 3 + 0 | 17 | 0 | 12 |
| FX | Fields/Solvers | 38 → 38 | 37 % → 37 % | 13 + 1 | 24 | 0 | 19 |
| FX | Effects | 11 → 11 | 18 % → 18 % | 2 + 0 | 9 | 0 | 8 |
| Rendering | Lighting/Shading | 14 → 14 | 29 % → 36 % | 5 + 0 | 9 | 0 | 0 |
| Rendering | Texturing | 8 → 8 | 12 % → 12 % | 1 + 0 | 7 | 0 | 2 |
| Rendering | Render | 15 → 15 | 47 % → 47 % | 6 + 1 | 8 | 0 | 6 |
| Rendering | Toon | 20 → 20 | 0 % → 5 % | 0 + 1 | 19 | 0 | 1 |
| Rendering | Stereo | 0 → 6 | 0 % → 17 % | 0 + 1 | 5 | 0 | 0 |
| (always visible) | Cache | 13 → 24 | 0 % → 46 % | 5 + 6 | 13 | 0 | 15 |
| (always visible) | Help | 23 → 26 | 0 % → 77 % | 18 + 2 | 6 | 0 | 1 |

These menus did **not** move since step 98 (same % working): Control 7 %, Visualize 20 % (5 new leaves, 1 new working),
nConstraint 0 %, nCache 15 %, Fields/Solvers 37 %, Effects 18 %, Texturing 12 %, Render 47 %.

Under 25 % working: Generate 4 %, nHair 4 %, Toon 5 %, Control 7 %, Texturing 12 %, nCache 15 %, Fluids 16 %, Stereo 17 %,
Effects 18 %, Surfaces 20 %, Visualize 20 %, Skeleton 24 %.

### 1b. Editor menu bars (steps 104 / 105, not present at step 98)

| Editor | Leaves | Working | Greyed + notice | Most-greyed menus |
|---|---|---|---|---|
| Graph Editor | 229 | 137 (60 %) | 92 | View 25 / 40, Show 21 / 34, Curves 16 / 39 |
| Dope Sheet | 181 | 117 (65 %) | 64 | Show 21 / 34, Curves 17 / 34 |
| UV Editor | 172 | 84 (49 %) | 88 | Select 22 / 39, Modify 17 / 31, View 13 / 20, Tools 9 / 19 |
| UV Toolkit | 3 | 1 | 2 | Maya's whole UV Toolkit panel is 3 menu leaves here |
| Hypershade | 249 | 114 (46 %) | 135 | Create 91 / 160, Edit 21 / 30, Tabs 6 / 6, Options 6 / 6, Graph 5 / 9 |
| Render Settings | 21 | 10 (48 %) | 11 | Presets 9 / 10 |
| Script Editor | 59 | 32 (54 %) | 27 | History 13 / 13 |

## 2. Option boxes per top menu (507 paths)

window = kit Maya option window (`option_windows`), dialog = the operator's own options or file dialog, tool = tool + Tool
Settings, redo = run + Adjust Last Operation, generic = "Blender has no settings for this" window, dead = box on a greyed item.

| Menu | window | dialog | tool | redo | generic | dead |
|---|---|---|---|---|---|---|
| File | 2 | 6 | – | 1 | 1 | 2 |
| Edit | 3 | – | – | 7 | 4 | 5 |
| Create | 6 | 1 | – | 19 | 1 | 17 |
| Select | – | – | – | 2 | – | 1 |
| Modify | 2 | – | 4 | 7 | 1 | 17 |
| Display | – | – | – | 1 | 1 | 1 |
| Mesh | 2 | 1 | 1 | 11 | – | 4 (+1 menu) |
| Edit Mesh | 4 | – | 1 | 9 | 2 | 2 |
| Mesh Tools | – | – | 8 | 18 | 2 | 7 |
| Mesh Display | – | 1 | – | 5 | 1 | 3 |
| Curves | – | – | – | 4 | 5 | 15 |
| Surfaces | – | – | – | 3 | 5 | **29** |
| Deform | – | – | – | 16 | **15** | 16 |
| UV | 3 | – | – | 4 | 2 | 2 |
| Generate | – | – | – | – | – | 8 |
| Skeleton | – | – | – | 3 | 5 | – |
| Skin | 1 | – | – | 3 | 4 | 5 |
| Constrain | 3 | – | – | 6 | 1 | 7 |
| Control | – | – | – | – | 1 | 2 |
| Key | 3 | – | – | 4 | 1 | 4 |
| Playback / Windows | – | 1 / 1 | – | – | – | – |
| Visualize | – | – | – | 1 | – | 3 |
| nParticles / Fluids / nCloth / nHair / nConstraint / nCache | – | – | – | 2 / 3 / – / 2 / – / 3 | 5 / 1 / 2 / – / – / – | 8 / 16 / 1 / 11 / 11 / 9 |
| Fields/Solvers / Effects | – | – | – | 13 / 2 | – | 6 / 6 |
| Render / Texturing / Toon | – | – | – | 2 / – / – | 1 / 1 / – | 3 / 1 / 1 |
| Cache | – | 8 | – | – | – | 7 |
| Help | – | – | – | – | – | 1 |

Daily-use boxes that open only the generic "no settings" window, although the Maya box holds settings a Maya user changes:
Skeleton/Create Joints (Joint Tool orientation), Skin/Paint Skin Weights (tool settings), Skeleton/Create IK Handle,
Create IK Spline Handle, Set / Assume Preferred Angle, Edit/Parent (Preserve Position), Unparent, Ungroup, Key/Delete Keys,
Edit/Keys/Delete Keys, Deform/Blend Shape, Deform/Cluster, Mesh Tools/Connect, Edit Mesh/Connect, Edit Mesh/Circularize,
Mesh Tools/Make Hole, Skin/Copy Skin Weights, Skin/Unbind Skin, Constrain/Pole Vector, UV/Merge UVs, nCloth/Create nCloth,
Curves/Attach / Detach, Surfaces/Loft / Extrude / Planar / Bevel Plus, 12 Deform/Paint Weights entries.

## 3. Shelves (`ui/shelf.all_buttons`)

| Shelf | Buttons | Step 98 drawn | Now working | Greyed + notice | Greyed, no notice |
|---|---|---|---|---|---|
| Curves / Surfaces | 38 | 10 | 24 | 14 | 0 |
| Poly Modeling | 43 | 35 | 41 | 2 | 0 |
| Sculpting | 26 | 1 | 19 | 7 | 0 |
| Rigging | 18 | 15 | 17 | 1 | 0 |
| Animation | 14 | 13 | 14 | 0 | 0 |
| Rendering | 25 | 13 | 19 | 6 | 0 |
| FX | 29 | 7 | 13 | **16** | 0 |
| FX Caching | 10 | 4 | 4 | 6 | 0 |
| **Total** | 203 | 98 (48 %) | **151 (74 %)** | 52 | 0 |

Greyed buttons:

- Curves / Surfaces: Three Point Circular Arc, Rebuild Curve, Curve Editing Tool, Birail 1, Project Curve on Surface, Intersect / Trim / Untrim / Attach / Detach / Extend / Rebuild Surfaces, Sculpt Geometry Tool, Surface Editing Tool.
- Poly Modeling: Super Shape, 3D Grab UV Tool.
- Sculpting: Imprint, Convert To Frozen, Pose Editor, Smooth / Clone / Mask / Erase Target.
- Rigging: Human IK.
- Rendering: Ambient Light, Volume Light, Shading Map, Render Diagnostics, Cancel / Show Batch Render.
- FX: 2D Fluid Container with Emitter, Make Selected Curves Dynamic and 14 nHair state buttons.
- FX Caching: 6 of 10.

The plug-in tabs (Arnold, Bifrost, MASH, Motion Graphics, XGen) are still absent, by design.

## 4. Hotkeys (`docs/keymap_mapping.md`, 468 rows)

| Status | Step 98 | Now |
|---|---|---|
| 구현 (implemented) | 155 | **199** |
| IC 일치 | 15 | 30 |
| 해당 없음 (n/a, reviewed) | 11 | **171** |
| 미검토 (unreviewed) | **219** | **0** |
| macOS 전용 | 68 | 68 |

n/a rows by context (n/a / all rows in that context):

- hyperShadePanel 25 / 25, nodeEditorPanel 32 / 40, timeEditorPanel 32 / 42
- xgmIGBrush 9, polyTexturePlacementPanel (UV Editor) 7 / 27, global 48 / 262
- profiler 4, shapePanel 3, others 1–2

"n/a" here often means "Blender has no such display", not "Maya users don't press it":

- UV Editor: 4 / 6 / 8 / 9 (wireframe / texture / shell border / texture border display), Ctrl+1 isolate, Delete (Delete UVs).
- Hypershade / Node Editor: 1–5 attribute display, arrow pick-walk, `,` `.` `/` up/downstream, Shift+! / @ / # solo.
- Graph Editor `l` (value lines), `n` traversal marking menu, global Ctrl+Up / Down (checker density).

## 5. Windows menu (74 leaves)

- **47 open something.** 9 of them have a notice: Hypergraph Hierarchy / Connections, Time / Trax Editor, Quick Rig, Hypershade, Light Editor, Animation Layers, Node Editor.
  - New since step 98: Component Editor, Connection Editor, File Path Editor, Command Shell, Shape Editor, Render Layer Editor, Light Linking, Render Layers, Sets, Display Layers, Hotkey Editor, Color Settings, Plug-in Manager, Content Browser, Workspaces, UI Elements, Switch to Blender.
- **27 are greyed with a notice:** Home, Asset Editor, Channel Control, Namespace Editor, Profiler, Evaluation Toolkit, Paint Effects, XGen Editor, Crease Sets, HumanIK, Pose Editor, Motion Library, Rendering Flags, Hardware Render Buffer, Camera Sets, Character Sets, Deformer Sets, Dynamic Relationships, Partitions, Render Pass Sets, UV Linking, **Marking Menu Editor, Shelf Editor, Panel Editor**, Minimize Application, Raise Main Window, Raise Application Windows.
- **0 are greyed without a notice** (step 98: 31).

## 6. Live Maya top-level items missing from kit menus (Qt capture vs menu_data)

746 live top-level items were compared; 11 are missing (step 98: 64):

- MASH menu (4): a plug-in, not drawn by design.
- nCloth and nConstraint: Convert Texture to Vertex Map and Convert Vertex to Texture Map (2 + 2). The generator still drops them.
- 3 others:
  - Edit: `Undo "<last command>"`, a run-time label.
  - Mesh Tools: Hide Modeling Toolkit. The kit shows the Show/Hide toggle in its other state.
  - Help: Autodesk App Store.

## 7. Marking menus / hotbox (`marking/menus.py` vs `research/maya/marking_menus.json`)

No change since step 98 (the diff is the Multi-Cut target only). 26 kit menus: 298 working entries, 112 greyed, 54 submenus.
Radial positions are still enforced by `tests/test_step8_marking_menus.py`.

| Menu | Working | Greyed | Greyed entries |
|---|---|---|---|
| RMB object (dagMenuProc / _curve) | 21 / 17 | 2 / 4 | Vertex Face, Make Live, DG Traversal, Inputs, Outputs, Metadata, Actions, UV / Color Sets, Time Editor (curve: Curve Point, Hull, Edit Point) |
| Shift+RMB object | 16 | 8 | Fill Holes, Append to Polygon Tool, Toggle Soft Edge Display, Extrude, Quadrangulate, Union, Difference, Intersection |
| Shift+RMB vertex | 13 | 6 | Vertex Normal Edit Tool, Toggle Vertex Normal Display, Paint Select, Detach Components, Circularize, Reorder Vertices |
| Shift+RMB edge | 21 | 6 | Merge Edge Tool, Soften/Harden, Toggle Soft Edge Display, Paint Select, Circularize, Edit Edge Flow |
| Shift+RMB face | 15 | 6 | Reverse Propagate, Toggle Face Normal Display, Wedge Face, Paint Select, Assign Invisible Faces, Circularize |
| Shift+RMB nothing selected | 11 | 5 | Create Polygon Tool, Pipe, Helix, Gear, Quad Draw Tool |
| Ctrl+RMB convert | 14 | 12 | Grow / Shrink Along Loop, To UVs, To UV Shell / Perimeter, To Edge Loop and Delete / Duplicate, To Edge Ring and Split / Collapse, To Vertex Perimeter, To Face Path, To Shell Border |
| w / e / r / q options | 20 / 17 / 20 / 5 | 4 / 2 / 1 / 1 | Face Center, Keep Spacing, Live Object Axis, Custom, Reset, Camera-Based Selection |
| a (select all) | 3 | 4 | Enable / Select / Disable All Outputs, Select All Inputs |
| Hotbox N / S / E / W / C | 6 / 6 / 8 / 7 / 10 | 2 / 2 / 3 / 2 / 0 | Toggle Outliner, Persp/Relationship Editor, Set Editor, Hypergraph, Time Slider, Range Slider, Shelf, Hierarchy, Dynamics Mask |
| UV Editor RMB / Shift+RMB UV / shell | 12 / 11 / 12 | 0 / 8 / 6 | Best Plane, Contour Stretch, 3D Grab UV Tool, Create UV Shell, Delete UVs, Auto Seams, Texture Borders, UV Set Editor |
| Shift+S tangents | 16 | 0 | |
| Shift+Q component mask / Alt+Q | 5 / 4 | 25 / 0 | every non-mesh component type |

**25 greyed marking-menu entries have a working main-menu item with the same Maya command.** The marking menus were not
revisited after steps 63, 101 and 110 mapped those commands:

- Shift+RMB object: Fill Holes, Extrude, Quadrangulate, Union, Difference, Intersection.
- Shift+RMB components: Vertex Normal Edit Tool, Detach Components, Circularize (×3), Soften/Harden, Edit Edge Flow, Wedge Face, Reverse (face normals), Quad Draw Tool.
- Ctrl+RMB convert: To UV Shell.
- UV Editor marking menus: Best Plane (×2), Contour Stretch (×2), UV Set Editor (×2).
- RMB object: Make Live (×2).

## 8. Channel Box / Attribute Editor node types

- Dedicated AE layouts (`ae_layout.BY_KIND`): transform, joint, mesh, camera, pointLight, directionalLight, spotLight, areaLight,
  standardSurface, aiStandardSurface, lambert, blinn, phong, surfaceShader, phongE, anisotropic, rampShader, layeredShader,
  useBackground, nucleus + generic material. Step 98 had 16; the 5 step-105 shaders are new.
- History tabs:
  - 18 creation nodes (polyCube … polyPrism, makeNurbSphere … makeNurbCube; `prim_history.KIND_NODES`, step 129, new).
  - polyExtrudeFace (kit record).
  - shadingEngine (`SG:i`, step 100).
  - Modifiers named as 21 Maya node types (`attribute_editor.MODIFIER_NODES`: polySmoothFace, polyBevel3, skinCluster, ffd, nonLinear, deltaMush, …), shown as a generic property dump.
  - Constraints.
- Header-only types (`NODE_TYPE`, generic layout): nurbsCurve, nurbsSurface, lattice, type, metaball, locator.
- No AE presence (by code reading, not GUI-checked): file / place2dTexture / bump2d texture nodes, animCurve, ikHandle (an empty
  object), blendShape (shape keys), the deformer node behind cluster / softMod handles, ambientLight / volumeLight (not creatable).
- The 10 research AE templates (`ae_templates.json`) are all covered.

## 9. Largest remaining gaps (grade · F daily frequency · S severity · score = F × S)

Grades as in step 98: 외형 (look) / 조작 (operation) / 기능 (function) / 없음 (missing).

| # | Gap | Grade | F | S | Score |
|---|---|---|---|---|---|
| 1 | **Marking menus unchanged since step 98**: 112 of 410 entries greyed. 25 of them (Shift+RMB Extrude, Fill Holes, Booleans, Circularize, Detach, Soften/Harden, Edit Edge Flow, Wedge, Quad Draw, UV Best Plane / Contour Stretch / UV Set Editor) work from the main menus but stay greyed in the menus Maya modelers actually use | 기능 | 5 | 3 | **15** |
| 2 | **Option boxes**: 231 of 507 are dead (46 %) and 62 open a generic "no settings" window, including daily ones (Create Joints, Paint Skin Weights, Create IK Handle, Parent, Delete Keys, Blend Shape, Connect, Circularize). Only 48 paths (38 distinct) open a real options window | 기능 | 4 | 3 | **12** |
| 3 | **Ctrl+RMB convert / Select menu**: 12 of 26 convert entries greyed. Select has 42 greyed (Grow / Shrink Along Loop, Components UV / UV Shell / Vertex Face, To UVs, To Vertex / UV Perimeter, To Face Path, To Shell Border) | 기능 | 3 | 3 | **9** |
| 4 | **UV Editor**: 88 of 172 menu leaves greyed. Modify: Stack, Snap Together, Distribute, Straighten Border, Layout Along, Orient Shells. Tools: Unfold, Move UV Shell, Cut, Sew, Pin. The whole UV Toolkit panel is 3 leaves. Keys n/a: display 4 / 6 / 8 / 9, Ctrl+1 isolate, Delete UVs | 기능 | 3 | 3 | **9** |
| 5 | **Curves (44 %) / Surfaces (20 %)**: Rebuild Curve, Fillet, Offset, Curve Editing Tool greyed in the menu and on the shelf; 29 of 37 Surfaces boxes dead; 14 Curves / Surfaces shelf buttons greyed | 없음 | 3 | 3 | **9** |
| 6 | **Key / animation editing**: Scale Keys greyed (Key and Edit > Keys). Graph Editor View 25 / 40 and Show 21 / 34 greyed (buffer curves, curve names, auto frame, show results). Visualize still at 20 % (Ghosting, Animation Snapshot) | 기능 | 3 | 3 | **9** |
| 7 | **AE node coverage**: no tab for texture nodes (file / place2dTexture), animCurve, ikHandle, blendShape, cluster; modifiers get a generic Blender property dump under a Maya node name | 기능 | 3 | 3 | **9** |
| 8 | **Weights in / out**: Skin Export / Import Weight Maps, Deform Export / Import Weights, Interactive Bind Skin and Move Weights to Influences are greyed. Riggers move weights between rigs every week | 없음 | 2 | 4 | **8** |
| 9 | **Hypershade graph work**: Graph menu Clear / Add Selected / Remove Selected / Rearrange greyed; Tabs and Options 0 / 12; Create 91 / 160 greyed; all 25 hyperShadePanel keys n/a (1–5 display, pick-walk, up / downstream, solo) | 조작 | 3 | 2 | **6** |
| 10 | **Skeleton 24 %**: 35 Joint Labelling items greyed (needed for label-based Mirror Skin Weights), plus Enable / Disable IK Handles and IK/FK control; Control 7 % and HumanIK stay greyed | 없음 | 2 | 3 | **6** |

Below the cut:

| Gap | F | S | Score |
|---|---|---|---|
| Hotbox greyed toggles (Toggle Outliner, Time / Range Slider, Shelf) | 3 | 2 | 6 |
| Windows > Shelf / Marking Menu / Panel Editor greyed (customisation) | 2 | 3 | 6 |
| Render > Batch Render / Test Resolution greyed | 2 | 3 | 6 |
| FX menus at 18 %: nHair 4 %, nConstraint 0 %; also Generate 4 %, Toon 5 % | 1 | 4 | 4 |
| FX shelf: 16 greyed nHair buttons | 1 | 3 | 3 |
| nCloth / nConstraint paint-map conversions missing from the menus | 1 | 1 | 1 |
