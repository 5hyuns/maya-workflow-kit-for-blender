# Step 145 부록 — 재점검 9차 수치 감사 (lane B, paper)

Step 133 부록 (`docs/steps/step_133_quant.md`) 의 수치를 오늘 master 에서 같은 방법으로 다시 센 결과. 칭찬 없이 차이만.
Read-only audit, 2026-10-24, HEAD de5feb7 (0.3.0 + step 144). Scripts and raw data outside the repository in
`tmp/audit145b_work/` (`leaves.py`, `leaves_now.json`, `option_kinds_now.json`); the step-133 baseline was recomputed from
`git archive 1ac4b77` with the same scripts (`tmp/audit133_quant/menus_per.py`, `marking_cmp.py`, `probe_quant.py`).

Method (unchanged from step 133):

- Menus: `python tools/menu_count.py` + the per-top-menu script on `menu_count.leaves()`. "Working" = path in `menu_map.MAP`;
  "greyed + notice" = `notices.greyed_notice(path)`.
- Option boxes: `python tools/menu_count.py --options` = `tests/test_step140_option_count.py` (sandbox `option_count`, run with
  `--no-build` on `dist/maya-workflow-kit-0.3.0.zip`, built after HEAD). Kinds from `ui/menu_sets.option_kind`.
- Shelves / distinct option windows: `probe_quant.py` in a headless Blender 4.5.4 (own sandbox, created first, `--factory-startup`).
- Hotkeys: `python tools/gen_keymap_mapping.py` (exit 0, `docs/keymap_mapping.md` unchanged — nothing to restore).
- Marking menus: `marking/menus.py` imported as a plain module at 1ac4b77 and now. Since step 136 an entry can be
  `("item", "<Maya menu path>")` — counted as working when the path is in `menu_map.MAP` (all 70 are).

## 0. Headline (step 133 → now)

| Metric | Step 133 (1ac4b77, 0.2.1) | Now (de5feb7, 0.3.0 + 144) |
|---|---|---|
| Unique kit menu leaves (main menu sets) | 1318 | 1318 (no leaf added or removed) |
| ... working (mapped, incl. with notice) | 587 (44.5 %) | **596 (45.2 %)** = 504 + 92 with a notice |
| ... of which only open a Blender editor / Preferences / web page | – | 52 (30 editor, 4 Preferences, 18 URL) |
| ... greyed with a notice / without | 731 / 0 | 722 / **0** |
| Leaves counted per set | 1486, working 662 | 1486, working 663 (44.6 %) |
| `menu_map.MAP` / `notices.NOTICES` / `CATEGORIES` | 1082 / 128 / 183 | 1102 / 138 / 181 |
| Editor menu bars (Graph, Dope Sheet, UV, UV Toolkit, Hypershade, Render Settings, Script Editor) | 914 leaves, 495 working | 914 leaves, **506 working (55 %)** — UV Editor 84 → 95; of the 506, 52 open a web page and 39 Blender Preferences |
| Option-box paths (`OPTION_BOXES`) | 507 | 507 |
| ... kit Maya option window | 29 paths (29 specs) | **75 paths (65 specs)** |
| ... operator dialog | 19 | 22 |
| ... distinct real windows / dialogs | 38 | **80** |
| ... tool + Tool Settings | 14 | 10 (4 Mesh Tools boxes now open Maya tool windows / dialogs instead, steps 140 / 144) |
| ... run + Adjust Last Operation | 151 | **123** |
| ... "Blender has no settings" (`option_generic`) | 62 | **43** |
| ... opens a Blender menu | 0 | 1 (`Mesh/Cleanup...`) |
| ... dead (box on a greyed item) | 231 (46 %) | **233 (46 %)** (+2: step 144 greyed Deform > Solidify, Paint Weights > Tension / Wire / Jiggle) |
| Shelves (8 tabs, 203 buttons) | 151 working, 52 greyed + notice | **unchanged** 151 / 52 / 0 |
| Hotkeys (468 rows) implemented / IC / n/a / unreviewed / macOS | 199 / 30 / 171 / 0 / 68 | **unchanged** 199 / 30 / 171 / 0 / 68 |
| Marking menus (26 menus, 464 → 472 entries) | 298 working, **128 greyed** (112 none + 16 empty submenus), 38 submenus | **363 working** (293 + 70 `item` entries), **69 greyed** (59 + 10), 40 submenus |
| ... greyed that work from a main menu (#74) | 25 | **0** |
| Live Maya top-level items missing from kit menus | 11 | 11 (no leaf change) |
| AE dedicated layouts (`ae_layout.BY_KIND`) | 21 kinds | 21 kinds (+ history tabs `polyExtrudeEdge` / `polyExtrudeVertex` / `polyBevel` records, step 139) |
| Manual checks (items / ticked / open) | 499 / 70 / 429 | before this audit 580 / 70 / 510 → after cleanup **548 / 78 / 470** (§6) |

Read: since 0.2.1 the work went into depth (Maya tools, results, option windows, marking menus), not breadth — the
main menus gained 9 working leaves (Select conversions, Scale Keys) and lost 4 (Deform, honesty greying in step 144).

## 1. Menus per menu set

| Set | Leaves | Working 133 → now | Greyed + notice 133 → now | Greyed, no notice |
|---|---|---|---|---|
| Common | 449 | 56 % → **59 %** (263) | 198 → 186 | 0 |
| Modeling | 349 | 47 % → **46 %** (160) | 185 → 189 | 0 |
| Rigging | 190 | 39 % → **37 %** (71) | 115 → 119 | 0 |
| Animation | 180 | 49 % → **48 %** (86) | 91 → 94 | 0 |
| FX | 205 | 18 % → 18 % (37) | 168 → 168 | 0 |
| Rendering | 63 | 24 % → 24 % (15) | 48 → 48 | 0 |
| (always visible) Cache + Help | 50 | 62 % → 62 % (31) | 19 → 19 | 0 |

Modeling / Rigging / Animation went down because the shared Deform menu (counted in each of them) lost 4 working leaves.

### 1a. Per top menu (Deform and Constrain shared, listed once)

| Set | Menu | Leaves | % working 133 → now | Working (+ notice) | Greyed + notice | Option boxes |
|---|---|---|---|---|---|---|
| Common | File | 30 | 80 % → 80 % | 15 + 9 | 6 | 12 |
| Common | Edit | 68 | 65 % → **66 %** | 44 + 1 | 23 | 19 |
| Common | Create | 70 | 53 % → 53 % | 29 + 8 | 33 | 44 |
| Common | Select | 81 | 48 % → **62 %** | 50 + 0 | 31 | 3 |
| Common | Modify | 90 | 41 % → 41 % | 33 + 4 | 53 | 31 |
| Common | Display | 36 | 64 % → 64 % | 20 + 3 | 13 | 2 |
| Common | Windows | 74 | 64 % → 64 % | 38 + 9 | 27 | 1 |
| Modeling | Mesh | 26 | 81 % → 81 % | 21 + 0 | 5 | 20 |
| Modeling | Edit Mesh | 28 | 89 % → 89 % | 25 + 0 | 3 | 18 |
| Modeling | Mesh Tools | 36 | 81 % → 81 % | 20 + 9 | 7 | 35 |
| Modeling | Mesh Display | 39 | 38 % → 38 % | 15 + 0 | 24 | 10 |
| Modeling | Curves | 36 | 44 % → 44 % | 14 + 2 | 20 | 24 |
| Modeling | Surfaces | 41 | 20 % → 20 % | 4 + 4 | 33 | 37 |
| Modeling | Deform | 74 | 43 % → **38 %** | 14 + 14 | 46 | 47 |
| Modeling | UV | 19 | 84 % → 84 % | 16 + 0 | 3 | 11 |
| Modeling | Generate | 50 | 4 % → 4 % | 2 + 0 | 48 | 8 |
| Rigging | Skeleton | 54 | 24 % → 24 % | 10 + 3 | 41 | 8 |
| Rigging | Skin | 28 | 64 % → 64 % | 18 + 0 | 10 | 13 |
| Rigging | Constrain | 20 | 55 % → 55 % | 8 + 3 | 9 | 17 |
| Rigging | Control | 14 | 7 % → 7 % | 0 + 1 | 13 | 3 |
| Animation | Key | 41 | 49 % → **51 %** | 21 + 0 | 20 | 12 |
| Animation | Playback | 26 | 73 % → 73 % | 18 + 1 | 7 | 1 |
| Animation | Audio | 9 | 56 % → 56 % | 4 + 1 | 4 | 0 |
| Animation | Visualize | 10 | 20 % → 20 % | 2 + 0 | 8 | 4 |
| FX | nParticles | 25 | 28 % → 28 % | 5 + 2 | 18 | 15 |
| FX | Fluids | 25 | 16 % → 16 % | 2 + 2 | 21 | 20 |
| FX | nCloth | 13 | 38 % → 38 % | 2 + 3 | 8 | 3 |
| FX | nHair | 54 | 4 % → 4 % | 1 + 1 | 52 | 13 |
| FX | nConstraint | 19 | 0 % → 0 % | 0 + 0 | 19 | 11 |
| FX | nCache | 20 | 15 % → 15 % | 3 + 0 | 17 | 12 |
| FX | Fields/Solvers | 38 | 37 % → 37 % | 13 + 1 | 24 | 19 |
| FX | Effects | 11 | 18 % → 18 % | 2 + 0 | 9 | 8 |
| Rendering | Lighting/Shading | 14 | 36 % → 36 % | 5 + 0 | 9 | 0 |
| Rendering | Texturing | 8 | 12 % → 12 % | 1 + 0 | 7 | 2 |
| Rendering | Render | 15 | 47 % → 47 % | 6 + 1 | 8 | 6 |
| Rendering | Toon | 20 | 5 % → 5 % | 0 + 1 | 19 | 1 |
| Rendering | Stereo | 6 | 17 % → 17 % | 0 + 1 | 5 | 0 |
| (always visible) | Cache | 24 | 46 % → 46 % | 5 + 6 | 13 | 15 |
| (always visible) | Help | 26 | 77 % → 77 % | 18 + 2 | 6 | 1 |

Changes (exact path diff 1ac4b77 → de5feb7): **+13 working** — Edit/Keys/Scale Keys, Key/Scale Keys, Select/Components/UV, UV Shell,
Grow / Shrink Along Loop, Convert Selection/To Face Path, To Shell Border, To UV Edge Loop, To UV Perimeter, To UV Shell Border, To UVs,
To Vertex Perimeter; **−4 working** — Deform/Solidify, Deform/Paint Weights/Jiggle, Tension, Wire (greyed with a notice in step 144:
no Blender deformer with Maya's meaning, `docs/steps/step_144_deform.md:36`).

Menus that did not move since **step 98** (two audits): Control 7 %, Visualize 20 %, nConstraint 0 %, nCache 15 %, Fields/Solvers 37 %,
Effects 18 %, Texturing 12 %, Render 47 %. Since step 133 every menu except Edit / Select / Key / Deform stayed exactly as it was.

### 1b. Weakest menus by Maya-user impact (daily use × greyed share)

| Menu | % working | Daily-use items still greyed (Maya user hits them) |
|---|---|---|
| **Curves** | 44 % | Rebuild, Fillet, Edit Curve Tool, Cut, Intersect, Straighten / Bend / Curl, Duplicate Surface Curves, Move Seam; `Create/Curve Tools/EP Curve Tool`, Three / Two Point Circular Arc |
| **Skeleton** | 24 % | 35 Joint Labelling items (Mirror Skin Weights by label), Enable / Disable Selected IK Handles, Enable IK/FK Control, IK Handle Snap |
| **Skin** | 64 % | Export / Import Weight Maps, Interactive Bind Skin (+ Tool), Move Weights to Influences, Post Normalization, Reset Default Weights, Bake Deformation to Skin Weights |
| **Render** | 47 % | Batch Render (+ Cancel / Show), Test Resolution, Render Diagnostics |
| **Surfaces** | 20 % | 33 greyed (Rebuild, Trim / Untrim, Intersect, Attach / Detach Surfaces, Extend, Birail …); 29 of 37 option boxes dead |
| **Mesh Display** | 38 % | Set Vertex Normal, Apply Color, colour-set editing (Assign / Edit / Rename Set), Color Material Channel / Material Blend 13 |
| **Visualize** | 20 % | Ghost Selected / Unghost / Ghosting Editor, Create / Update Animation Snapshot |
| **Key** | 51 % | IK/FK Keys 4, Set Blend Shape Target Weight Keys, Key > Attribute Editor (!), 10 Character Set items |
| **Modify** | 41 % | Align Tool, Snap Align > Position Along Curve, Default Object Manipulator 5, Evaluate Nodes 14 (Maya evaluation toggles) |
| Generate / nHair / nConstraint / Toon | 0–5 % | whole systems Blender has no counterpart for (Paint Effects, XGen, Nucleus hair / constraints, Toon) — notices only |

### 1c. Editor menu bars (step 104 / 105)

| Editor | Leaves | Working 133 → now | Greyed + notice | Most-greyed menus now |
|---|---|---|---|---|
| Graph Editor | 229 | 137 → 137 (60 %) | 92 | View 25 / 40, Show 21 / 34, Curves 16 / 39, Select 6 / 8, List 6 / 8 |
| Dope Sheet | 181 | 117 → 117 (65 %) | 64 | Show 21 / 34, Curves 17 / 34, List 6 / 7 |
| UV Editor | 172 | 84 → **95 (55 %)** | 77 | Modify 17 / 31, Select 13 / 39, View 13 / 20, Tools 9 / 19, Image 9 / 14 |
| UV Toolkit | 3 | 1 → 1 | 2 | Maya's whole UV Toolkit panel is still 3 menu leaves |
| Hypershade | 249 | 114 → 114 (46 %) | 135 | Create 91 / 160, Edit 21 / 30, Tabs 6 / 6, Options 6 / 6, Graph 5 / 9 |
| Render Settings | 21 | 10 → 10 | 11 | Presets 9 / 10 |
| Script Editor | 59 | 32 → 32 | 27 | **History 13 / 13** (Echo All Commands …) |

Honesty note: of the 506 "working" editor-bar leaves, 52 open a Blender web page (`wm.url_open`: every Help menu, MEL / Node
reference) and 39 open Blender Preferences (`screen.userpref_show`; e.g. all 34 Graph Editor / Dope Sheet `Tangents/Default In / Out
Tangent/*` radio items open Preferences > Animation instead of setting anything) — real actions are 410 / 914 (45 %).
The UV Editor greyed list still has the daily UV tools: `Tools/Unfold`, `Move UV Shell`, `Cut`, `Sew`, `Pin`, `Modify/Stack Shells`,
`Snap Together`, `Distribute Shells`, `Orient Shells to Edges`, `Straighten Border`, `Map Border`, `Cut/Sew/Auto Seams`, `Create UV Shell`,
`View/Toggle Shell Borders`, `View/Isolate Select/*`, `Edit/Delete`.

## 2. Option boxes per top menu (507 paths)

window = kit Maya option window, dialog = operator / file dialog, tool = tool + Tool Settings, redo = run + Adjust Last Operation,
generic = "Blender has no settings for this" window, dead = box on a greyed item. Step 133 values in brackets where they changed.

| Menu | window | dialog | tool | redo | generic | dead |
|---|---|---|---|---|---|---|
| File | 2 | 6 | – | 1 | 1 | 2 |
| Edit | **12** [3] | – | – | **3** [7] | **0** [4] | **4** [5] |
| Create | 6 | 1 | – | 19 | 1 | 17 |
| Select | – | – | – | 2 | – | 1 |
| Modify | 2 | – | 4 | 7 | 1 | 17 |
| Display | – | – | – | 1 | 1 (Grid) | 1 |
| Mesh | 2 | 1 | 1 | 11 | – | 4 (+1 menu) |
| Edit Mesh | **6** [4] | – | 1 | 9 | **0** [2] | 2 |
| Mesh Tools | **4** [0] | **3** [0] | **4** [8] | **17** [18] | **0** [2] | 7 |
| Mesh Display | – | 1 | – | 5 | 1 | 3 |
| Curves | – | – | – | 4 | 5 | 15 |
| Surfaces | – | – | – | 3 | 5 | **29** |
| Deform | **16** [0] | – | – | **2** [16] | **9** [15] | **20** [16] |
| UV | 3 | – | – | **3** [4] | **3** [2] | 2 |
| Generate | – | – | – | – | – | 8 |
| Skeleton | **3** [0] | – | – | 3 | **2** [5] | – |
| Skin | **4** [1] | – | – | 3 | **1** [4] | 5 |
| Constrain | **6** [3] | – | – | **4** [6] | **0** [1] | 7 |
| Control | – | – | – | – | 1 | 2 |
| Key | **9** [3] | – | – | **0** [4] | **0** [1] | **3** [4] |
| Playback / Windows | – | 1 / 1 | – | – | – | – |
| Visualize | – | – | – | 1 | – | 3 |
| nParticles / Fluids / nCloth / nHair / nConstraint / nCache | – | – | – | 2 / 3 / – / 2 / – / 3 | 5 / 1 / 2 / – / – / – | 8 / 16 / 1 / 11 / 11 / 9 |
| Fields/Solvers / Effects | – | – | – | 13 / 2 | – | 6 / 6 |
| Render / Texturing / Toon | – | – | – | **0** [2] / – / – | **3** [1] / 1 / – | 3 / 1 / 1 |
| Cache | – | 8 | – | – | – | 7 |
| Help | – | – | – | – | – | 1 |

The 43 boxes that still open the generic "no settings" window, by Maya-user impact:

- Daily: `Render/Render Current Frame`, `Render/Render Sequence`, `Render/IPR Render Current Frame` (Maya: camera, frame range,
  output — the Render Sequence box is how a Maya user renders a range), `Display/Grid` (Maya Grid Options: length, spacing,
  subdivisions — see blindspot BS3), `Curves/Attach`, `Detach`, `Smooth` (×2), `Reverse Direction`, `UV/Merge UVs`,
  `UV/Contour Stretch`, `UV/3D Cut and Sew UV Tool`, `Skeleton/Set` / `Assume Preferred Angle`, `Skin/Edit Influences/Add Influence`.
- Weekly: 9 `Deform/Paint Weights/*` (Maya opens the paint tool's Tool Settings), `Surfaces/Loft`, `Extrude`, `Planar`, `Bevel Plus`,
  `Reverse Direction`, `nCloth/Create nCloth`, `Create Passive Collider`, `nParticles/Create Emitter` (×2), `Emit from Object` (×2),
  `Make Collide` (nParticles, Fluids), `Modify/Bake Pivot`, `Mesh Display/Paint Vertex Color Tool`, `Texturing/3D Paint Tool`,
  `Create/Curve Tools/Pencil Curve Tool`, `File/Archive Scene`, `Control/Create Character Set`.

**How a box opens is a bigger gap than what it opens** (GitHub #82, user report): a plain click on the ❒ runs the command; the window
only opens with press-and-hold → "Option Box". So the 75 + 22 real windows above are effectively hidden from a Maya user who clicks
the box (every menu, not just File).

## 3. Shelves (`ui/shelf.all_buttons`)

Unchanged since step 133 (per-button diff empty): 203 buttons, **151 working (74 %)**, 52 greyed with a notice, 0 without.

| Shelf | Buttons | Working | Greyed (+ notice) |
|---|---|---|---|
| Curves / Surfaces | 38 | 24 | 14: Three Point Circular Arc, Rebuild Curve, Curve Editing Tool, Birail 1, Project Curve on Surface, Intersect / Trim / Untrim / Attach / Detach / Extend / Rebuild Surfaces, Sculpt Geometry Tool, Surface Editing Tool |
| Poly Modeling | 43 | 41 | 2: Super Shape, 3D Grab UV Tool |
| Sculpting | 26 | 19 | 7: Imprint, Convert To Frozen, Pose Editor, Smooth / Clone / Mask / Erase Target |
| Rigging | 18 | 17 | 1: Human IK |
| Animation | 14 | 14 | 0 |
| Rendering | 25 | 19 | 6: Ambient Light, Volume Light, Shading Map, Render Diagnostics, Cancel / Show Batch Render |
| FX | 29 | 13 | 16: 2D Fluid Container with Emitter, Make Selected Curves Dynamic, 14 nHair state buttons |
| FX Caching | 10 | 4 | 6: Set / Clear Initial State, Enable / Disable All Caches On Selected, Merge Caches, Replace Cache Frame |

## 4. Hotkeys (`docs/keymap_mapping.md`, 468 rows)

Status counts unchanged since step 133: 구현 199, IC 일치 30, 해당 없음 171, 미검토 0, macOS 전용 68. Step 141 changed bindings
(Ctrl+A in every 3D mode + UV, UV Alt+RMB dolly, Ctrl+Shift+A / Alt+D per mode) inside rows that were already 구현, so the doc only
gained notes. The 171 n/a rows still include daily Maya keys whose editor has no Blender counterpart: UV Editor 4 / 6 / 8 / 9 display,
Ctrl+1 isolate, Delete (Delete UVs); Hypershade / Node Editor 1–5, arrows, `,` `.` `/`, Shift+! / @ / # (25 + 32 rows); Time Editor
32 rows; Graph Editor `l` value lines.

Kit menus show the Maya key beside the label only for **57 main-menu items** (`ui/menu_hotkeys.py`: Edit 13, Key 8, File 7, Playback 7,
Select 7, Edit Mesh 5, …); **0 editor-menu-bar items** have hotkey text (step 108 「남은 것」, still open).

## 5. Marking menus / hotbox (`marking/menus.py`)

| | Step 133 | Now |
|---|---|---|
| Entries (26 menus) | 464 | 472 |
| Working | 298 | **363** (293 direct + 70 `("item", path)` main-menu items) |
| Greyed | 128 (112 no action + 16 empty submenus) | **69** (59 + 10) |
| Submenus | 38 | 40 |

The 69 greyed entries (each has a `notices.MARKING` notice, step 136):

- 25 = Shift+Q `doSelectComponentMM` non-mesh pick masks (CVs, lattice points, pivots, handles …) + All Components off + Save to shelf.
- RMB object (`dagMenuProc` / `_curve`): Vertex Face, DG Traversal, Inputs, Outputs, Metadata, Time Editor (×2), curve Curve Point / Hull /
  Edit Point.
- Shift+RMB: Reorder Vertices, Merge Edge Tool, Assign Invisible Faces, Pipe, Helix, Gear.
- w / e / r: Snap > Face Center, Keep Spacing, Live Object Axis (×2), Custom (×2), Reset.
- a: Enable / Select / Disable All Outputs, Select All Inputs.
- Hotbox: Persp/Relationship Editor, **Time Slider, Range Slider** (toggles), Hierarchy, Dynamics Mask.
- UV Editor: Create UV Shell, Delete UVs, Auto Seams (×2), Texture Borders (×2).
- `buildObjectMenuItemsNow`: Complete Tool, Show Orientation Handle.

## 6. Manual checks (`docs/manual_checks.md`)

| | Items | Ticked | Open |
|---|---|---|---|
| Step 133 count | 499 | 70 | 429 |
| Today before this audit (steps 133–144 added 81) | 580 | 70 | 510 |
| After this audit's cleanup | **548** | **78** | **470** |

- Deleted (32 items, obsolete since step 130 / 116 — the feature or setting no longer exists): old lines 33, 34 (Activate Maya Keymap /
  Quick Setup keymap), 61 (Maya Navigation Preferences), 65–68 (Install / Remove Maya Layout, Apply Maya Theme, template re-enable), 73
  (sidebar Channel Box tab), 82, 139, 140 (File > New > Allset template, keymap after Quick Setup), 285 (Revert Maya Look), 290–294
  (Maya density, Segoe UI, flat widgets), 324 (sidebar dock / Channel Box Dock Only), 348 (Maya Font), 418 (Restore Blender Settings),
  731–732 (Allset name / MayaKit template), 736 (Solid Side Panels), 749, 802 (`bl_app_templates_user/Allset`), 769, 773–777, 781 (Maya
  theme on 5.x / Alt+B with the Maya theme) — and the now-empty section headers Step 44, 111, 112, 119.
- Ticked (8, the GUI test asserts every clause): Step 138 Ctrl+N prompt untitled / saved (`gui_step138_prompt`), Maya layout on
  File > Open + option off (`gui_step138_open`), Step 139 Connect / Merge / Smooth / Symmetrize (`gui_step139_edit`), UV > Automatic +
  Best Plane / Contour Stretch enabled (`gui_step139_uv`).
- Still partly stale (kept, need a rewrite, not deleted): 141 (navigation part), 282 / 284 (theme / File > New template part), 323 / 654
  (Maya Density wording), 352 / 353 (navigation / Maya theme colours on 5.x), 413 (theme in the switch list), 656 (Blender Item tab,
  gone since step 116), 747 / 801 (template / File > New entry).
