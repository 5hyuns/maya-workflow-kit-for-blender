# Step 98 부록 — 재점검 7차 수치 감사 (메뉴 · 셸프 · 키맵 · Windows)

읽기 전용 서브에이전트가 `research/maya/menus.json` · `shelves.json` · `docs/keymap_mapping.md` 와 `src/maya_kit/ui/menu_data.py` · `menu_map.py` · `notices.py` · `shelf_*.py` 를 대조한 결과. 계산 스크립트는 저장소 밖 `tmp/audit7/`. 주장은 본문(step_98.md)에서 grep 으로 표본 재확인함 (Modify > Naming 없음, project.py:420 문구, Alt+R = scale_clear).


Read-only audit, 2026-10-19, HEAD 8936c73. The numbers come from scripts in `tmp/audit7/`:

- `menus_audit.py` imports the generated `menu_data`, `menu_map` and `notices` with bpy stubbed. It re-implements the path rules of `ui/menu_sets.children` and `sub_items`, so CHILDREN, EXTRA and `#2` paths count exactly as drawn.
- `shelves_audit.py` and `keymap_audit.py`.
- Two headless Blender probes, `io_probe.py` and `selmode_probe.py`. Both ran with `--factory-startup` and `BLENDER_USER_*` set to `tmp/audit7/`.

Raw output is in `menus_audit.json` (per menu) and `menus_detail.json` (one row per kit leaf: set, path, class, option box, action).

**Terms**

- **Mapped**: the path is in `menu_map.MAP`, so it draws as a working operator. The operator's context poll can still grey it.
- **Greyed**: not in MAP, so it draws through `maya_kit.menu_unavailable` (poll is always False).
- **Notice**: the path is in `notices.NOTICES` (a "not in Blender" note in the tooltip and the Help Line).

Option boxes are classified from `menu_sets._draw_items` and `marking/modal.run_action` (`src/maya_kit/marking/modal.py:54-80`):

- **Real dialog**: the operator has an `option_box` prop (`maya_kit.mirror`, `maya_kit.playblast`, `maya_kit.create_set`), or always opens `invoke_props_dialog` (`maya_kit.orient_joint`, `maya_kit.mirror_joints`).
- **Tool+settings**: sets the tool and opens Tool Settings.
- **Redo panel**: runs the command, then `screen.redo_last` (Blender's Adjust Last Operation).
- **Dead**: the box icon sits on a greyed item.
- **Submenu**: mapped to a Blender menu. The box icon is drawn, but there is no box.

## 0. Headline numbers

| Metric | Value |
|---|---|
| Maya menus in menus.json | 42. The MASH, Bifrost and Boss plug-in menus are listed in the sets but have no data and are not drawn. |
| Unique kit leaf items (all menus, shared Deform/Constrain counted once) | **1251** |
| Mapped (working) | 344, plus 26 with a notice = **370 (29.6%)** |
| Greyed | **881 (70.4%)**: 15 with a notice, **866 with no explanation** |
| Maya option boxes (menus.json raw, shared menus counted per menu) | 625 |
| Kit option-box paths (`menu_data.OPTION_BOXES`) | 500 (499 on leaves) |
| ... real Maya-style options dialog | **6** (Mesh/Mirror, Windows/Playblast, Playback/Playblast, Create/Sets/Set, Skeleton/Orient Joint, Skeleton/Mirror Joints) |
| ... tool + Tool Settings | 11 |
| ... run + Adjust Last Operation | 156 |
| ... dead (greyed) | **323** |
| ... submenu with a box icon but no box (Import, Export All, Export Selection) | 3 |
| `menu_map.MAP` entries / `notices.NOTICES` entries | 370 / 41 |
| Dead MAP keys / dead NOTICES keys / OPTION_BOXES paths that don't exist | 0 / 0 / 0 |
| menu_data matches a fresh regeneration from menus.json | yes (0 menus differ) |
| Shelves (8 factory tabs) | 203 Maya buttons, **98 drawn (48%)**, 105 left out without a trace |
| Hotkeys (docs/keymap_mapping.md) | 468 rows: 155 implemented, 15 match IC, 11 n/a, **219 unreviewed**, 68 macOS only |

## 1. Menus per menu set

| Set | Menu | Maya leaves (menus.json raw) | Maya opt boxes (raw) | Kit leaves | Mapped | Mapped + notice | Greyed + notice | Greyed, no notice | % working | Kit opt boxes: real dialog / tool+settings / redo panel / dead / submenu |
|---|---|---|---|---|---|---|---|---|---|---|
| Common | File | 27 | 12 | 27 | 13 | 4 | 0 | 10 | 63% | 0 / 0 / 6 / 3 / 3 |
| Common | Edit | 69 | 19 | 68 | 42 | 0 | 0 | 26 | 62% | 0 / 0 / 13 / 6 / 0 |
| Common | Create | 68 | 44 | 68 | 27 | 3 | 1 | 37 | 44% | 1 / 0 / 22 / 21 / 0 |
| Common | Select | 80 | 3 | 80 | 31 | 0 | 0 | 49 | 39% | 0 / 0 / 2 / 1 / 0 |
| Common | Modify | 90 | 40 | 88 | 26 | 2 | 1 | 59 | 32% | 0 / 4 / 5 / 21 / 0 |
| Common | Display | 31 | 2 | 36 | 11 | 0 | 0 | 25 | 31% | 0 / 0 / 1 / 1 / 0 |
| Common | Windows | 17 | 1 | 68 | 25 | 9 | 3 | 31 | 50% | 1 / 0 / 0 / 0 / 0 |
| Modeling | Mesh | 26 | 20 | 26 | 14 | 0 | 0 | 12 | 54% | 1 / 0 / 10 / 9 / 0 |
| Modeling | Edit Mesh | 28 | 18 | 28 | 18 | 0 | 0 | 10 | 64% | 0 / 0 / 11 / 7 / 0 |
| Modeling | Mesh Tools | 36 | 35 | 36 | 8 | 1 | 0 | 27 | 25% | 0 / 7 / 1 / 27 / 0 |
| Modeling | Mesh Display | 39 | 10 | 39 | 7 | 0 | 0 | 32 | 18% | 0 / 0 / 4 / 6 / 0 |
| Modeling | Curves | 36 | 24 | 36 | 4 | 0 | 0 | 32 | 11% | 0 / 0 / 4 / 20 / 0 |
| Modeling | Surfaces | 41 | 37 | 41 | 0 | 0 | 0 | 41 | 0% | 0 / 0 / 0 / 37 / 0 |
| Modeling | Deform | 74 | 47 | 73 | 11 | 0 | 0 | 62 | 15% | 0 / 0 / 11 / 36 / 0 |
| Modeling | UV | 19 | 11 | 19 | 11 | 0 | 1 | 7 | 58% | 0 / 0 / 8 / 3 / 0 |
| Modeling | Generate | 33 | 8 | 33 | 0 | 0 | 0 | 33 | 0% | 0 / 0 / 0 / 8 / 0 |
| Rigging | Skeleton | 54 | 8 | 54 | 6 | 1 | 1 | 46 | 13% | 2 / 0 / 2 / 4 / 0 |
| Rigging | Skin | 28 | 13 | 28 | 12 | 0 | 0 | 16 | 43% | 0 / 0 / 7 / 6 / 0 |
| Rigging | Deform | 74 | 47 | 73 | 11 | 0 | 0 | 62 | 15% | 0 / 0 / 11 / 36 / 0 |
| Rigging | Constrain | 20 | 17 | 20 | 8 | 0 | 0 | 12 | 40% | 0 / 0 / 8 / 9 / 0 |
| Rigging | Control | 14 | 3 | 14 | 0 | 1 | 0 | 13 | 7% | 0 / 0 / 1 / 2 / 0 |
| Animation | Key | 41 | 12 | 41 | 17 | 0 | 1 | 23 | 41% | 0 / 0 / 8 / 4 / 0 |
| Animation | Playback | 27 | 1 | 25 | 16 | 0 | 2 | 7 | 64% | 1 / 0 / 0 / 0 / 0 |
| Animation | Audio | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0% | 0 / 0 / 0 / 0 / 0 |
| Animation | Visualize | 5 | 4 | 5 | 1 | 0 | 0 | 4 | 20% | 0 / 0 / 1 / 3 / 0 |
| Animation | Deform | 74 | 47 | 73 | 11 | 0 | 0 | 62 | 15% | 0 / 0 / 11 / 36 / 0 |
| Animation | Constrain | 20 | 17 | 20 | 8 | 0 | 0 | 12 | 40% | 0 / 0 / 8 / 9 / 0 |
| FX | nParticles | 25 | 15 | 25 | 2 | 2 | 0 | 21 | 16% | 0 / 0 / 4 / 11 / 0 |
| FX | Fluids | 25 | 20 | 25 | 2 | 0 | 0 | 23 | 8% | 0 / 0 / 2 / 18 / 0 |
| FX | nCloth | 16 | 5 | 13 | 2 | 1 | 0 | 10 | 23% | 0 / 0 / 2 / 1 / 0 |
| FX | nHair | 54 | 13 | 54 | 1 | 0 | 0 | 53 | 2% | 0 / 0 / 1 / 12 / 0 |
| FX | nConstraint | 21 | 13 | 19 | 0 | 0 | 0 | 19 | 0% | 0 / 0 / 0 / 11 / 0 |
| FX | nCache | 20 | 12 | 20 | 3 | 0 | 2 | 15 | 15% | 0 / 0 / 3 / 9 / 0 |
| FX | Fields/Solvers | 38 | 19 | 38 | 13 | 1 | 0 | 24 | 37% | 0 / 0 / 13 / 6 / 0 |
| FX | Effects | 11 | 8 | 11 | 2 | 0 | 0 | 9 | 18% | 0 / 0 / 2 / 6 / 0 |
| Rendering | Lighting/Shading | 14 | 0 | 14 | 4 | 0 | 0 | 10 | 29% | 0 / 0 / 0 / 0 / 0 |
| Rendering | Texturing | 8 | 2 | 8 | 1 | 0 | 0 | 7 | 12% | 0 / 0 / 1 / 1 / 0 |
| Rendering | Render | 14 | 6 | 15 | 6 | 1 | 3 | 5 | 47% | 0 / 0 / 3 / 3 / 0 |
| Rendering | Toon | 20 | 1 | 20 | 0 | 0 | 0 | 20 | 0% | 0 / 0 / 0 / 1 / 0 |
| Rendering | Stereo | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0% | 0 / 0 / 0 / 0 / 0 |
| (always visible) | Cache | 13 | 9 | 13 | 0 | 0 | 0 | 13 | 0% | 0 / 0 / 0 / 9 / 0 |
| (always visible) | Help | 28 | 1 | 23 | 0 | 0 | 0 | 23 | 0% | 0 / 0 / 0 / 1 / 0 |

| Set (incl. shared Deform/Constrain) | Leaves | Working (mapped incl. notice) | Greyed + notice | Greyed, no notice | % working |
|---|---|---|---|---|---|
| Common | 435 | 193 | 5 | 237 | 44% |
| Modeling | 331 | 74 | 1 | 256 | 22% |
| Rigging | 189 | 39 | 1 | 149 | 21% |
| Animation | 164 | 53 | 3 | 108 | 32% |
| FX | 205 | 29 | 2 | 174 | 14% |
| Rendering | 57 | 12 | 3 | 42 | 21% |
| (always visible) | 36 | 0 | 0 | 36 | 0% |

**Notes**

- Modeling, Rigging and Animation all show one shared **Deform** menu: 73 leaves, 11 working, 0 notices. Rigging and Animation share one **Constrain** menu: 20 leaves, 8 working. Both are counted in each set's row above.
- These menus have **0 working items**:
  - Surfaces (41)
  - Generate (33)
  - Toon (20)
  - Cache (13; the always-visible Maya 2022 Cache menu)
  - Help (23)
  - nConstraint (19)
  - Control (14; its 1 working item is a substitute with a notice)
- **Audio** and **Stereo** have no data at all: the static parse of `buildSoundPopupMenu` and `RenStereoMenu` found no items, so both draw as empty menus.
- Windows has 68 kit leaves against 17 in menus.json. The other 51 come from `menu_map.CHILDREN`, because Maya builds the editor submenus at run time (`src/maya_kit/ui/menu_map.py:479-517`).

### 1a. Names and order (menus.json vs menu_data)

- menu_data is a faithful regeneration: nothing is reordered and nothing is added.
- The generator drops labels that are run-time `<dynamic:...>` in the static parse. Some are restored by the kit; some are lost:
  - **Modify > Naming section (2 items): lost.** Prefix Hierarchy Names and Search and Replace Names (`research/maya/menus.md:340-342`) are missing entirely, not even greyed. Riggers use them daily.
  - Modify > Match Transformations (5) and Snap Align Objects (4): restored by CHILDREN.
  - Modify > Pivot (2): restored by EXTRA.
  - Modify > Attributes (3): restored by EXTRA.
  - Deform > Pose Space Deformation > Pose Editor title: lost.
  - nCloth and nConstraint paint-attribute lists (3 + 3): lost.
  - Playback > Playback Speed: "Play Every Frame, Free" and "Max Real-time" are lost. Only "Real-time" is left.
  - nCloth > Convert nCloth Output Space (2): lost.
  - Help (5): About, Maya Home, Learning Channel and others are lost.
- **Windows > Settings/Preferences** is a submenu in Maya (Preferences, Hotkey Editor, Color Settings, Shelf Editor, Plug-in Manager, ...). The kit makes it one leaf that opens Blender Preferences (`screen.userpref_show`), so Hotkey Editor, Shelf Editor and Plug-in Manager have no entry.
- The **Help** menu label is `'Help '`, with a trailing space left over from the parse.
- **Playback > Playback Looping > Continuous** is greyed, but Continuous is exactly what Blender does. Only Once and Oscillate carry the notice "Blender playback always loops", so the one correct item looks broken.
- Two code paths for one feature: the menu items `Select/Convert Selection/To Edges` and `To Faces` run `mesh.select_mode(use_expand=True)` (`src/maya_kit/ui/menu_map.py:200-205`), while the Ctrl+F9–F11 hotkeys use `maya_kit.convert_selection` (`src/maya_kit/keymap/mapping.py:176-179`). A headless probe (the 4 vertices of one face selected) gave Maya's result, 8 edges and 5 faces. So this case is not a bug, but the menu and the hotkeys can drift apart.

### 1b. Greyed items without a notice that a Maya user is most likely to hit daily

The ranking is my judgement. Every item listed is greyed in menus_detail.json.

| # | Maya path | Why it hurts | Closest Blender feature |
|---|---|---|---|
| 1 | Mesh Display/Soften/Harden Edges, Set Vertex Normal, Lock/Unlock Normals, Vertex Normal Edit Tool | normals matter on every model | Mark Sharp, Shade Auto Smooth, Normals menu |
| 2 | Edit Mesh/Detach, Flip, Circularize, Edit Edge Flow, Wedge, Transform | core polygon editing | Rip/Split, Mirror, To Sphere, Spin |
| 3 | Mesh Tools/Connect, Make Hole, Append to Polygon, plus the 21 Sculpting Tools (only 8 of 36 Mesh Tools items work) | everyday tools | Knife / vertex connect, Fill, every sculpt brush |
| 4 | Select/Shortest Edge Path Tool, Grow/Shrink Along Loop, Components/UV, UV Shell, Convert Selection/To UVs, To UV Shell | selection | `mesh.shortest_path_pick`, select more/less, UV sync selection |
| 5 | Modify/Transformation Tools/Soft Modification Tool, Proportional Modification Tool, Default Object Manipulator | soft selection as a tool | proportional editing |
| 6 | Modify/Naming: Prefix Hierarchy Names, Search and Replace Names (missing, not even greyed) | renaming | `wm.batch_rename` |
| 7 | Display/Toggle Show/Hide, Wireframe Color..., Object Display/Template, Transform Display/Rotate Pivots | display | hide toggle, object colour, `hide_select` |
| 8 | Display/Polygons, NURBS, Animation, Rendering: whole display-option submenus drawn as single greyed leaves | backface culling, normals display, joint size | viewport overlays |
| 9 | UV/Split UVs, Best Plane, Contour Stretch, Assign Checker Shader, UV Set Editor | UV workflow | seams + split, Follow Active Quads, UV Grid image, UV Maps panel |
| 10 | Skeleton/Insert Joints, Reroot Skeleton, Set/Assume Preferred Angle, Create IK Spline Handle, Joint Labelling (39 items) | rigging | subdivide bone, Spline IK, bone names |
| 11 | Skin/Edit Influences (Add, Remove, Remove Unused), Hammer Skin Weights, Interactive Bind Skin, Normalize toggles, Export/Import Weight Maps | skinning | vertex group ops |
| 12 | Deform/Cluster, Wire, Nonlinear (Bend, Flare, Sine, Squash), Soft Modification, Jiggle, Paint Weights (11 items) | deformers | Hook, Curve, SimpleDeform, Wave modifiers; weight paint |
| 13 | Key/Insert Key on Translate/Rotate/Scale, Key/Scale Keys, Playback/Select Next/Previous Key | animation | `keyframe_insert_by_name`, Graph Editor scale |
| 14 | Visualize/Create Animation Snapshot, Create Turntable... | animation review | onion skinning, motion paths |
| 15 | Constrain/Closest Point, Point On Poly, Normal, Tangent, Rivet, UV Pin, Proximity Pin | constraints | Shrinkwrap, vertex parent |
| 16 | Create/Polygon Primitives/Pipe, Helix, Gear, Soccer Ball; Curve Tools/EP Curve Tool, Pencil Curve Tool; Lights/Ambient Light; NURBS Primitives/Cube, Cone | creation | Extra Objects add-on, Draw curve tool |
| 17 | Cache menu, all 13 items (Create New Cache, Import Cache..., Export Cache, ...) | Alembic pipeline | Alembic/USD import and export, Mesh Sequence Cache modifier |
| 18 | Curves/Rebuild, Attach, Detach, Offset, Extend, Fillet; all 41 Surfaces items | NURBS work | some curve operators |
| 19 | File/Archive Scene, View Image..., View Sequence..., Recent Increments, ATOM Export/Import | file handling | Pack Resources, Image Editor, `render.play_rendered_anim` |
| 20 | Windows: Component Editor, Connection Editor, Shape Editor, Pose Editor, Render Layer Editor, Light Linking, Sets | editors | Spreadsheet, Drivers, Shape Keys panel, View Layers, Light Linking (Blender 4.x), kit sets |
| 21 | Render/Test Resolution | render | resolution % |
| 22 | Mesh/Cleanup..., Retopologize, Conform | modeling | Clean Up menu, QuadriFlow remesh, Shrinkwrap |

## 2. File menu, item by item

| Maya item | Maya option box | Kit action | Kit option-box behaviour |
|---|---|---|---|
| New Scene | yes | `wm.read_homefile` (the template's start scene) | redo panel (read_homefile has no options, so none in practice) |
| Open Scene... | yes | `maya_kit.open_scene` (file browser in the project's scenes folder) | redo panel (none) |
| Save Scene | yes | `maya_kit.save_scene` | redo panel |
| Save Scene As... | yes | `maya_kit.save_scene_as` (starts in the project's scenes folder) | redo panel |
| Increment and Save | - | `maya_kit.increment_save` (Maya naming) | - |
| Archive Scene | yes | **greyed, no notice.** Blender has File > External Data > Pack Resources. | dead |
| Save Preferences | - | `wm.save_userpref` | - |
| Optimize Scene Size | yes | `outliner.orphans_purge` | redo panel |
| Import... | yes | Blender's `TOPBAR_MT_file_import` submenu. You pick the format first; Maya uses one dialog that detects the type. It does not start in the project folder. | box icon, no box |
| Export All... | yes | Blender's `TOPBAR_MT_file_export` submenu | box icon, no box |
| Export Selection... | yes | `MAYAKIT_MT_export_selection`: FBX, OBJ, glTF, USD and Alembic, each with its "selected only" option preset (`src/maya_kit/operators/menu_extras.py:196-227`) | box icon, no box. Each format's options are in the file browser's side panel. |
| Adobe After Effects Live Link | - | greyed, no notice | - |
| Export to Offline File... / Assign Offline File... | yes | greyed, no notice | dead |
| ATOM > Export Animation / Import Animation / Create ATOM Template | - | greyed, no notice | - |
| Create Reference... | yes | `maya_kit.create_reference` (.blend link + library override, `ns:` names), with notice | redo panel |
| Reference Editor | - | Outliner in Blender File mode, in a new window, with notice | - |
| View Image... / View Sequence... | - | greyed, no notice | - |
| Project Window / Set Project... | - | kit project operators, with notice | - |
| Recent Files | - | `TOPBAR_MT_file_open_recent` | - |
| Recent Increments | - | greyed, no notice | - |
| Recent Projects | - | `MAYAKIT_MT_recent_projects` | - |
| Exit | - | `wm.quit_blender` | - |

**File menu totals.** 27 leaves:

- 17 work (4 of them with a notice).
- 10 are greyed, all without a notice.
- 12 have a Maya option box, and none opens a real Maya-style options window: 6 open the redo panel, 3 are dead, 3 show the icon only.

**Formats.** A headless probe of Blender 4.5 with `--factory-startup` found every operator below present. All of them are reachable through Import and Export All:

| Format | Import operator | Export operator | Where the kit offers it |
|---|---|---|---|
| FBX | `import_scene.fbx` | `export_scene.fbx` | Import, Export All, Export Selection |
| OBJ | `wm.obj_import` | `wm.obj_export` | all three |
| Alembic | `wm.alembic_import` | `wm.alembic_export` | all three. Maya's own route, the Cache menu, is greyed (0 of 13). |
| USD | `wm.usd_import` | `wm.usd_export` | all three |
| glTF | `import_scene.gltf` | `export_scene.gltf` | all three |
| Collada, PLY, STL, BVH, SVG | present | present | Import and Export All only |
| **.ma / .mb** | none | none | **Not possible.** Yet `src/maya_kit/operators/project.py:420` tells the user to "use File > Import for .ma / .fbx / .obj", which is misleading. |

The kit sets no Maya-friendly FBX or Alembic export defaults (axes, scale). A grep finds no FBX settings anywhere in `src/`.

## 3. Shelves (research/maya/shelves.json factory shelves vs ui/shelf_data.py + ui/shelf_map.py)

Unmapped buttons are **not drawn at all** (`src/maya_kit/ui/shelf.py:100-110`). So kit shelves are shorter than Maya's, and gaps open in Maya's button order. Double-click or Ctrl+click on a button opens the redo panel (`shelf.py:17-23`).

| Shelf file | Tab | Maya buttons (json) | kit data | drawn (mapped) | not drawn | dbl-click opts in Maya |
|---|---|---|---|---|---|---|
| CurvesSurfaces | Curves / Surfaces | 38 | 38 | 10 | 28 | 36 |
| Polygons | Poly Modeling | 43 | 43 | 35 | 8 | 28 |
| Sculpting | Sculpting | 26 | 26 | 1 | 25 | 23 |
| Rigging | Rigging | 18 | 18 | 15 | 3 | 15 |
| Animation | Animation | 14 | 14 | 13 | 1 | 13 |
| Rendering | Rendering | 25 | 25 | 13 | 12 | 9 |
| FX | FX | 29 | 29 | 7 | 22 | 8 |
| FXCaching | FX Caching | 10 | 10 | 4 | 6 | 2 |
| **Total** | | 203 | 203 | 98 | 105 | |
json shelves not in kit: ['Curves', 'Dynamics', 'Fluids', 'Fur', 'General', 'Hair', 'MotionGraphics', 'Muscle', 'NCloth', 'PaintEffects', 'Shelf1', 'Shelf2', 'Surfaces', 'Toon', 'TURTLE']
- **Curves / Surfaces** not drawn (28): NURBS Square, Pencil Curve Tool, Three Point Circular Arc, Attach Curves, Detach Curves, Extend Curve, Offset Curve, Rebuild Curve, Add Points Tool, Curve Editing Tool, NURBS Cube, NURBS Cone, Loft, Planar, Extrude, Birail 1 Tool, Bevel Plus, Project Curve on Surface, Intersect Surfaces, Trim Tool, Untrim Surfaces, Attach Surfaces, Detach Surfaces, Insert Isoparms, Extend Surfaces, Rebuild Surfaces, Sculpt Geometry Tool, Surface Editing Tool
- **Poly Modeling** not drawn (8): Super Shape, Sweep Mesh, SVG, Content Browser, Retopologize, Circularize, Contour Stretch, 3D Grab UV Tool
- **Sculpting** not drawn (25): Smooth Tool, Relax Tool, Grab Tool, Pinch Tool, Flatten Tool, Foamy Tool, Spray Tool, Repeat Tool, Imprint Tool, Wax Tool, Scrape Tool, Fill Tool, Knife Tool, Smear Tool, Bulge Tool, Amplify Tool, Freeze Tool, Convert To Frozen, Base Meshes, Shape Editor, Pose Editor, Smooth Target Tool, Clone Target Tool, Mask Target Tool, Erase Target Tool
- **Rigging** not drawn (3): Human IK, Create Cluster, Pole Vector Constraint
- **Animation** not drawn (1): Pole Vector Constraint
- **Rendering** not drawn (12): Ambient Light, Volume Light, Edit Material Attributes, Anisotropic Material, Phong E Material, Layered Material, Ramp Material, Shading Map, Use Background, Render Diagnostics, Cancel Batch Render, Show Batch Render
- **FX** not drawn (22): 3D Fluid Container with Emitter, 2D Fluid Container with Emitter, Emit Fluid from Object, Make Collide, Paint Hair Tool Options, Make Selected Curves Dynamic, Current Position, Start Position, Rest Position, To Hair Systems, To Follicles, To Start Curves, To Rest Curves, Scale Hair Tool, To Start Curve End CVs, To Rest Curve End CVs, From Current, Current and Start, From Current, Current and Rest, Display Input Mesh, Display Current Mesh
- **FX Caching** not drawn (6): Set Initial State, Clear Initial State, Enable All Caches On Selected, Disable All Caches On Selected, Merge Caches, Replace Cache Frame

**Notes**

- The legacy shelf files in shelves.json (Curves, Surfaces, General, Dynamics, ...) are not Maya 2022 default tabs, so leaving them out is correct.
- The Maya 2022 plug-in tabs (Arnold, Bifrost, MASH, Motion Graphics, XGen) are missing too.
- **Sculpting draws 1 of 26 buttons**: only Sculpt Tool, which enters Sculpt Mode. Blender has about 15 equivalent brushes (Smooth, Relax, Grab, Pinch, Flatten, Scrape, Fill, Smear, Inflate, Mask, ...).
- **Curves / Surfaces draws 10 of 38**, and **FX draws 7 of 29**.

## 4. Keymap (docs/keymap_mapping.md, 468 Maya factory hotkeys)

| Status | Count |
|---|---|
| 구현 (implemented) | 155 |
| IC 일치 (Industry Compatible already matches) | 15 |
| 해당 없음 (n/a) | 11 |
| **미검토 (unreviewed)** | **219** |
| macOS 전용 (macOS only) | 68 |

Unreviewed rows by Maya context:

| Context | Unreviewed |
|---|---|
| global | 62 |
| timeEditorPanel | 36 |
| nodeEditorPanel | 36 |
| hyperShadePanel | 25 |
| polyTexturePlacementPanel (UV Editor) | 17 |
| sculptMeshCache | 15 |
| xgmIGBrush | 9 |
| profilerPanel | 4 |
| graphEditor | 3 |
| shapePanel | 3 |
| texSculptCacheContext | 2 |
| Unfold3DBrush | 2 |
| hyperGraphPanel | 2 |
| posePanel | 1 |
| SymmetrizeUVBrush | 1 |
| texCutContext | 1 |

### Highest-priority unreviewed rows (keys used daily)

"Line" is the line number in docs/keymap_mapping.md.

| Line | Maya key | Context | Maya command | Current binding in the kit's Maya keyconfig |
|---|---|---|---|---|
| L217 | Esc | global | AbortCurrentTool | Frames `screen.animation_cancel`; nothing aborts a 3D View tool |
| L254 | Ctrl+I | global | SelectNextIntermediatObject | **`select_all(INVERT)`**, a different action |
| L255 | F1 | global | Help | **3D View `view_axis(FRONT)`** |
| L171 | Ctrl+M | global | ToggleMainMenubar | none |
| L172 | Shift+M | global | TogglePanelMenubar | none |
| L173 | Ctrl+Shift+M | global | ToggleModelEditorBars | none |
| L170 | Alt+M | global | FullHotboxDisplay | none |
| L435 | Alt+B | global | CycleBackgroundColor | none |
| L465 | Ctrl+F | global | SearchEngine | none (Blender's search is F3) |
| L393 | Alt+R | global | ToggleReflection | **`object.scale_clear`**: clears scale by surprise |
| L231-232 | Ctrl+PgUp / Ctrl+PgDn | global | PickWalkIn / PickWalkOut | **`screen.workspace_cycle`** |
| L131-132 | Shift+{ / Shift+} | global | Previous/NextViewArrangement | `select_hierarchy` (extend) |
| L267 | u (hold) | global, paint | PaintOperationMarkingMenu | none |
| L269 | Shift+B (hold) | global, paint | ModifyLowerRadius | none |
| L271 | n (hold) | global, paint | ModifyPaintValue | none |
| L273 | Alt+F | global, paint | FloodSurfaces | none |
| L276-277 | Ctrl+Alt+C / Ctrl+Alt+V | global | Copy/PasteVertexSkinWeights | none, although the menu items Skin > Copy/Paste Vertex Weights work |
| L274 | Alt+C | global | ToggleColorFeedback | **Mesh loop-cut tool** |
| L278-279 | Ctrl+. / Ctrl+, | global | Next/PrevSkinPaintMode | none / **`screen.userpref_show`** |
| L280 | o (hold) | global | PolyBrushMarkingMenu | none |
| L281 | m (hold) | global | ModifyDisplacement | **Measure tool** |
| L324 | Delete | UV Editor | DeleteUVs | none |
| L338 | Ctrl+1 | UV Editor | ToggleUVIsolateViewSelected | **`mesh.select_mode(VERT)`**, wrong |
| L332-337 | 4 / 5 / 6 / 7 / 8 / 9 | UV Editor | UV wireframe / shaded / texture / distortion / shell border / texture border display | 4 = island select mode; the rest are unbound |
| L341-344, L339-340, L325-326 | Q/W/E/R, F/A, Ctrl+C/V | UV Editor | UV tools, frame, copy/paste UVs | Blender equivalents are already bound (`tool_set_by_id`, `view_selected` / `view_all`, `uv.copy` / `uv.paste`); only the status needs updating |
| L397-405 | Ctrl+1 … Ctrl+9 | sculpt | SetMesh*Tool (Sculpt, Smooth, Relax, Grab, Pinch, Flatten, Foamy, Spray, Repeat) | none |
| L407-408 | b / m (hold) | sculpt | brush size / strength drag | none (Blender uses F / Shift+F) |
| L84-86 | h / j / l | Graph Editor | Lock channel / Unlock channel / value lines | none |
| L478-485 | Alt+T, Alt+Shift+T, ', ;, Shift+\|, Shift+", Shift+: | global | Time Slider bookmarks | none (Blender has markers) |
| L359-383 | 1–5, arrow keys, `,` `.` `/` | Hypershade | attribute display, pick-walk, upstream/downstream | none in the kit Hypershade (Shader Editor) |
| L38-39 | Ctrl+Up / Ctrl+Down | global | Increase/DecreaseCheckerDensity | none |

## 5. Windows > editors

| Maya editor | What the kit opens | Notice |
|---|---|---|
| Outliner | Blender Outliner in a new window (`open_editor OUTLINER`). It is separate from the kit Outliner docked in the layout. | - |
| Attribute Editor, Channel Box, Layer Editor, Display Layer Editor, Display Layers | dock panel in the 3D View sidebar (`dock_show`). All layer entries open the Channel Box dock. | - |
| Tool Settings | `editor_toggle TOOL_SETTINGS` | - |
| Graph Editor | Graph Editor window (FCURVES) with the kit toolbar | - |
| Dope Sheet | Dope Sheet window | - |
| Time Editor, Trax Editor, Animation Layers | NLA Editor | yes |
| Camera Sequencer | Video Sequencer | - |
| Expression Editor | Drivers editor | - |
| Hypershade | `maya_kit.hypershade`: Shader Editor plus a sidebar tab with Browser / Create / Property Editor | yes |
| Node Editor | Shader Editor (`ShaderNodeTree`) | yes |
| Hypergraph: Hierarchy / Hypergraph: Connections | Outliner / Drivers editor | yes |
| UV Editor | UV Editor window | - |
| Modeling Toolkit | kit Modeling Toolkit dock | - |
| Render Settings | `maya_kit.render_settings` | - |
| Render View | `render.view_show` | - |
| Light Editor | kit light editor window | yes |
| Shading Group Attributes | material Attribute Editor | - |
| Script Editor | `maya_kit.script_editor` | - |
| Attribute Spread Sheet | Spreadsheet | - |
| Reference Editor (File menu) | Outliner in Blender File mode | yes |
| Playblast | `maya_kit.playblast`, with a real options dialog | - |
| Output Window | `wm.console_toggle` (works on Windows only) | - |
| Quick Rig | `maya_kit.quick_rig` | yes |
| Namespace Editor, HumanIK, Character Sets | greyed | yes |
| Component Editor, Connection Editor, Channel Control, Asset Editor, File Path Editor, Command Shell, Profiler, Evaluation Toolkit | greyed | **no** |
| Paint Effects, XGen Editor, Crease Sets | greyed | no |
| Shape Editor, Pose Editor, Motion Library | greyed | no, though Blender has the Shape Keys panel |
| Render Layer Editor, Rendering Flags, Hardware Render Buffer | greyed | no, though Blender has View Layers |
| Camera Sets, Deformer Sets, Dynamic Relationships, Light Linking, Partitions, Render Layers, Render Pass Sets, Sets, UV Linking | greyed | no, though Blender 4.x has Light Linking and the kit has had sets since step 96 |
| Content Browser, Home, Minimize Application, Raise Main Window, Raise Application Windows | greyed | no |
| Settings/Preferences (a submenu in Maya) | Blender Preferences only | - |

**Windows menu totals.** 68 leaves:

- 34 work (9 of them with a notice).
- 3 are greyed with a notice.
- **31 are greyed without a notice.**
