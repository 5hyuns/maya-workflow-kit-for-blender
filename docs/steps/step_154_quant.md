# Step 154 부록 — 재점검 10차 수치 감사 (lane B, paper + look_compare)

Step 145 부록 (`docs/steps/step_145_quant.md`) 의 수치를 오늘 master 에서 같은 방법으로 다시 센 결과. 칭찬 없이 차이만.
Read-only audit, 2026-10-24, HEAD e26b969 (0.3.0 + steps 145–153), `dist/maya-workflow-kit-0.3.0.zip` (HEAD 빌드, `--no-build`).
Scripts and raw data outside the repository in `tmp/audit154b/`; the step-145 baseline is `git archive de5feb7` in `tmp/audit154b/old/`
plus step 145's raw files (`tmp/audit145b_work/leaves_now.json`, `option_kinds_now.json`).

Method (unchanged from step 145):

- Menus: `python tools/menu_count.py` + `tmp/audit154b/menus_per.py` (per top menu, `menu_count.leaves()`); "working" = path in
  `menu_map.MAP`, "greyed + notice" = `notices.greyed_notice(path)`. Exact path diffs: `leaves.py` (main menus) / `ed_diff.py`
  (editor menu bars, run on de5feb7 and HEAD).
- Option boxes: `ALLSET_SANDBOX=option_count154 python tests/run.py --no-build -k step140_option_count` (menu_count `--options`
  hard-codes sandbox `option_count`, so the test was run directly) → `tmp/option_count154/results/option_kinds.json`; 1 passed.
- Shelves / distinct option windows: `tmp/audit154b/probe_quant.py` (= step 133's probe) in a headless Blender 4.5 sandbox
  `tmp/audit154b/sandbox` (created first, `--factory-startup`).
- Hotkeys: `python tools/gen_keymap_mapping.py` (exit 0; `docs/keymap_mapping.md` unchanged in git — nothing to restore).
- Marking menus: `src/allset/marking/menus.py` imported as a plain module at de5feb7 and HEAD.
- look_compare: `ALLSET_GUI_UI_SCALE=0.8 ALLSET_LOOK_TAG=audit154_s100` through `tmp/audit154b/look_nobuild.py` (the same
  `look_compare.main`, only `build.main` patched to return the existing zip so another lane's `dist/` is not rewritten) →
  `research/maya/screens/compare_audit154_s100/`, diffed against step 145's `compare_audit145_s100/`.

## 0. Headline (step 145 → now)

| Metric | Step 145 (de5feb7, 0.3.0 + 144) | Now (e26b969, 0.3.0 + 153) |
|---|---|---|
| Unique kit menu leaves (main menu sets) | 1318 | 1318 (no leaf added or removed) |
| ... working (mapped, incl. with notice) | 596 (45.2 %) | **600 (45.5 %)** = 507 + 93 with a notice |
| ... greyed with a notice / without | 722 / 0 | 718 / 0 |
| Leaves counted per set | 1486, working 663 (44.6 %) | 1486, working 667 (44.9 %) |
| `menu_map.MAP` / `notices.NOTICES` / `CATEGORIES` | 1102 / 138 / 181 | 1117 / 162 / 179 |
| Editor menu bars (7 editors, 914 leaves) | 506 working (55 %) | **517 (57 %)** — Graph Editor 137 → 145, Dope Sheet 117 → 120; of the 517, 52 open a web page and 39 Blender Preferences → real actions **426 / 914 (47 %)** |
| Option-box paths (`OPTION_BOXES`) | 507 | 507 |
| ... kit Maya option window | 75 paths (65 specs) | **78 paths (68 specs)** |
| ... operator dialog | 22 | 22 |
| ... distinct real windows / dialogs | 80 | **83** |
| ... tool + Tool Settings | 10 | 10 |
| ... run + Adjust Last Operation | 123 | **121** |
| ... "Blender has no settings" (`option_generic`) | 43 | 43 (−2 Grid / Render Sequence, +2 regressions, §2) |
| ... opens a Blender menu | 1 | 1 |
| ... dead (box on a greyed item) | 233 (46 %) | **232 (46 %)** |
| How a box opens (#82) | click = command; window only by press-hold-drag to "Option Box" | click = command still; window by a **0.2 s press and release** (no drag, step 146) |
| Shelves (8 tabs, 203 buttons) | 151 working, 52 greyed + notice | **153 / 50 / 0** (Rendering: Cancel / Show Batch Render) |
| Hotkeys (468 rows) implemented / IC / n/a / unreviewed / macOS | 199 / 30 / 171 / 0 / 68 | **202 / 27** / 171 / 0 / 68 (Shift+W/E/R IC → kit `allset.set_key`, step 151) |
| Main-menu items with Maya hotkey text | 57 | 57; editor menu bars still 0 |
| Marking menus (26 menus) | 472 entries: 363 working, 69 greyed (59 + 10 empty submenus), 40 submenus | **474: 364 working** (294 + 70 `item`), **69 greyed** (59 + 10), 41 submenus |
| Manual checks (unticked / ticked) | 470 / 78 | 503 / 79 (steps 146–153 added 33 open items) |
| look_compare viewport (ΔE00 < 5) | 11/12 | 11/12 (same element fails: face stipple) |
| look_compare kit-drawn pixels | 6/6 | **5/6** — `marking_menu_box` 0.3 → 13.0, a stale sample point (§5), not a colour change |
| look_compare rects / density / scene / grid / furniture / checks | 5/12 · 5/6 · 3/3 · ok · 2/3 · 9/9 | identical (md files diff-equal except the one pixel row) |

Read: steps 146–153 again went into depth (option box opening, undo, Channel Box, Graph Editor, ring geometry, render windows, 5.x).
Breadth moved by **4 main-menu leaves** (all Render), 11 editor-bar leaves (Graph / Dope Sheet View / Show), 3 option windows,
2 shelf buttons, 3 hotkeys, 1 marking entry.

## 1. Menus per menu set

| Set | Leaves | Working 145 → now | Greyed + notice | Greyed, no notice |
|---|---|---|---|---|
| Common | 449 | 59 % → 59 % (263) | 186 | 0 |
| Modeling | 349 | 46 % → 46 % (160) | 189 | 0 |
| Rigging | 190 | 37 % → 37 % (71) | 119 | 0 |
| Animation | 180 | 48 % → 48 % (86) | 94 | 0 |
| FX | 205 | 18 % → 18 % (37) | 168 | 0 |
| Rendering | 63 | 24 % → **30 %** (19) | 48 → 44 | 0 |
| (always visible) Cache + Help | 50 | 62 % → 62 % (31) | 19 | 0 |

### 1a. Per top menu (Deform and Constrain shared, listed once)

| Set | Menu | Leaves | % working 145 → now | Working (+ notice) | Greyed + notice | Option boxes |
|---|---|---|---|---|---|---|
| Common | File | 30 | 80 % | 15 + 9 | 6 | 12 |
| Common | Edit | 68 | 66 % | 44 + 1 | 23 | 19 |
| Common | Create | 70 | 53 % | 29 + 8 | 33 | 44 |
| Common | Select | 81 | 62 % | 50 + 0 | 31 | 3 |
| Common | Modify | 90 | 41 % | 33 + 4 | 53 | 31 |
| Common | Display | 36 | 64 % | 20 + 3 | 13 | 2 |
| Common | Windows | 74 | 64 % | 38 + 9 | 27 | 1 |
| Modeling | Mesh | 26 | 81 % | 21 + 0 | 5 | 20 |
| Modeling | Edit Mesh | 28 | 89 % | 25 + 0 | 3 | 18 |
| Modeling | Mesh Tools | 36 | 81 % | 20 + 9 | 7 | 35 |
| Modeling | Mesh Display | 39 | 38 % | 15 + 0 | 24 | 10 |
| Modeling | Curves | 36 | 44 % | 14 + 2 | 20 | 24 |
| Modeling | Surfaces | 41 | 20 % | 4 + 4 | 33 | 37 |
| Modeling | Deform | 74 | 38 % | 14 + 14 | 46 | 47 |
| Modeling | UV | 19 | 84 % | 16 + 0 | 3 | 11 |
| Modeling | Generate | 50 | 4 % | 2 + 0 | 48 | 8 |
| Rigging | Skeleton | 54 | 24 % | 10 + 3 | 41 | 8 |
| Rigging | Skin | 28 | 64 % | 18 + 0 | 10 | 13 |
| Rigging | Constrain | 20 | 55 % | 8 + 3 | 9 | 17 |
| Rigging | Control | 14 | 7 % | 0 + 1 | 13 | 3 |
| Animation | Key | 41 | 51 % | 21 + 0 | 20 | 12 |
| Animation | Playback | 26 | 73 % | 18 + 1 | 7 | 1 |
| Animation | Audio | 9 | 56 % | 4 + 1 | 4 | 0 |
| Animation | Visualize | 10 | 20 % | 2 + 0 | 8 | 4 |
| FX | nParticles | 25 | 28 % | 5 + 2 | 18 | 15 |
| FX | Fluids | 25 | 16 % | 2 + 2 | 21 | 20 |
| FX | nCloth | 13 | 38 % | 2 + 3 | 8 | 3 |
| FX | nHair | 54 | 4 % | 1 + 1 | 52 | 13 |
| FX | nConstraint | 19 | 0 % | 0 + 0 | 19 | 11 |
| FX | nCache | 20 | 15 % | 3 + 0 | 17 | 12 |
| FX | Fields/Solvers | 38 | 37 % | 13 + 1 | 24 | 19 |
| FX | Effects | 11 | 18 % | 2 + 0 | 9 | 8 |
| Rendering | Lighting/Shading | 14 | 36 % | 5 + 0 | 9 | 0 |
| Rendering | Texturing | 8 | 12 % | 1 + 0 | 7 | 2 |
| Rendering | Render | 15 | 47 % → **73 %** | 9 + 2 | 4 | 6 |
| Rendering | Toon | 20 | 5 % | 0 + 1 | 19 | 1 |
| Rendering | Stereo | 6 | 17 % | 0 + 1 | 5 | 0 |
| (always visible) | Cache | 24 | 46 % | 5 + 6 | 13 | 15 |
| (always visible) | Help | 26 | 77 % | 18 + 2 | 6 | 1 |

Changes (exact path diff de5feb7 → e26b969): **+4 working** — `Render/Batch Render`, `Cancel Batch Render`, `Show Batch Render`,
`Test Resolution` (step 152). Nothing lost. Every other main menu is exactly as at step 145.

Menus that did not move since **step 98** (three audits): Control 7 %, Visualize 20 %, nConstraint 0 %, nCache 15 %, Fields/Solvers 37 %,
Effects 18 %, Texturing 12 %. Since step 133 (two audits): Curves, Surfaces, Skeleton, Skin, Mesh Display, Modify, Create, Windows.

### 1b. Weakest menus by Maya-user impact (daily use × greyed share)

| Menu | % working | Daily-use items still greyed (Maya user hits them) |
|---|---|---|
| **Curves** | 44 % | Rebuild, Fillet, Edit Curve Tool, Cut, Intersect, Straighten / Bend / Curl, Duplicate Surface Curves, Move Seam; `Create/Curve Tools/EP Curve Tool`, Three / Two Point Circular Arc. Unchanged for two audits. |
| **Skeleton** | 24 % | 35 Joint Labelling items (Mirror Skin Weights by label), Enable / Disable Selected IK Handles, Enable IK/FK Control, IK Handle Snap |
| **Skin** | 64 % | Export / Import Weight Maps, Interactive Bind Skin (+ Tool), Move Weights to Influences, Post Normalization, Reset Default Weights, Bake Deformation to Skin Weights |
| **Surfaces** | 20 % | 33 greyed (Rebuild, Trim / Untrim, Intersect, Attach / Detach, Extend, Birail …); 29 of 37 option boxes dead |
| **Mesh Display** | 38 % | Set Vertex Normal, Apply Color, colour-set editing, Color Material Channel / Material Blend 13 |
| **Modify** | 41 % | Align Tool, Snap Align > Position Along Curve, Default Object Manipulator 5, Evaluate Nodes 14 |
| **Visualize** | 20 % | Ghost Selected / Unghost / Ghosting Editor, Create / Update Animation Snapshot |
| **Key** | 51 % | IK/FK Keys 4, Set Blend Shape Target Weight Keys, Key > Attribute Editor, 10 Character Set items |
| Generate / nHair / nConstraint / Toon | 0–5 % | whole systems with no Blender counterpart (Paint Effects, XGen, Nucleus hair / constraints, Toon) — notices only |

Render left this list (73 %); its remaining greyed items are Set NURBS Tessellation, Run Render Diagnostics, Export Pre-Compositing, Create Backburner Job.

### 1c. Editor menu bars (step 104 / 105)

| Editor | Leaves | Working 145 → now | Greyed + notice | Most-greyed menus now |
|---|---|---|---|---|
| Graph Editor | 229 | 137 → **145 (63 %)** | 84 | View 20 / 40, Show 18 / 34, Curves 16 / 39, Select 6 / 8, List 6 / 8 |
| Dope Sheet | 181 | 117 → **120 (66 %)** | 61 | Show 18 / 34, Curves 17 / 34, List 6 / 7 |
| UV Editor | 172 | 95 → 95 (55 %) | 77 | Modify 17 / 31, Select 13 / 39, View 13 / 20, Tools 9 / 19, Image 9 / 14 |
| UV Toolkit | 3 | 1 → 1 | 2 | Maya's whole UV Toolkit panel is still 3 menu leaves |
| Hypershade | 249 | 114 → 114 (46 %) | 135 | Create 91 / 160, Edit 21 / 30, Tabs 6 / 6, Options 6 / 6 |
| Render Settings | 21 | 10 → 10 | 11 | Presets 9 / 10 |
| Script Editor | 59 | 32 → 32 | 27 | **History 13 / 13** |

New working (step 150): Graph Editor `View/Auto Frame`, `Auto Frame Time`, `Curve Name/Always / Active Only / Never`; Graph Editor and
Dope Sheet `Show/Objects/Clear Below`, `Show/Attributes/Clear Below`, `Show/Objects/Subdiv Objects`.
Honesty note unchanged: 52 web-page items and 39 Preferences items (all 34 `Tangents/Default In / Out Tangent/*` radio items still open
Preferences > Animation) → real actions 426 / 914. The UV Editor greyed list still holds the daily UV tools listed in step 145
(Unfold, Move UV Shell, Cut, Sew, Pin, Stack / Distribute / Orient Shells, Straighten Border, Map Border, Auto Seams, Create UV Shell,
Toggle Shell Borders, Isolate Select, Edit/Delete) — no change since step 145.

## 2. Option boxes per top menu (507 paths)

window = kit Maya option window, dialog = operator / file dialog, tool = tool + Tool Settings, redo = run + Adjust Last Operation,
generic = "Blender has no settings for this" window, dead = box on a greyed item. Step 145 values in brackets where they changed.

| Menu | window | dialog | tool | redo | generic | dead |
|---|---|---|---|---|---|---|
| File | 2 | 6 | – | 1 | 1 | 2 |
| Edit | 12 | – | – | **2** [3] | **1** [0] | 4 |
| Create | 6 | 1 | – | 19 | 1 | 17 |
| Select | – | – | – | 2 | – | 1 |
| Modify | 2 | – | 4 | 7 | 1 | 17 |
| Display | **1** [0] | – | – | **0** [1] | 1 | 1 |
| Mesh | 2 | 1 | 1 | 11 | – | 4 (+1 menu) |
| Edit Mesh | 6 | – | 1 | 9 | – | 2 |
| Mesh Tools | 4 | 3 | 4 | 17 | – | 7 |
| Mesh Display | – | 1 | – | 5 | 1 | 3 |
| Curves | – | – | – | 4 | 5 | 15 |
| Surfaces | – | – | – | 3 | 5 | 29 |
| Deform | 16 | – | – | 2 | 9 | 20 |
| UV | 3 | – | – | 3 | 3 | 2 |
| Generate | – | – | – | – | – | 8 |
| Skeleton | 3 | – | – | 3 | 2 | – |
| Skin | 4 | – | – | 3 | 1 | 5 |
| Constrain | 6 | – | – | 4 | – | 7 |
| Control | – | – | – | – | 1 | 2 |
| Key | 9 | – | – | – | – | 3 |
| Playback / Windows | – | 1 / 1 | – | – | – | – |
| Visualize | – | – | – | 1 | – | 3 |
| nParticles / Fluids / nCloth / nHair / nConstraint / nCache | – | – | – | 2 / 3 / – / 2 / – / 3 | 5 / 1 / 2 / – / – / – | 8 / 16 / 1 / 11 / 11 / 9 |
| Fields/Solvers / Effects | – | – | – | 13 / 2 | – | 6 / 6 |
| Render / Texturing / Toon | **2** [0] / – / – | – | – | – | **2** [3] / 1 / – | **2** [3] / 1 / 1 |
| Cache | – | 8 | – | – | – | 7 |
| Help | – | – | – | – | – | 1 |

Path diff: `Display/Grid` generic → window (Grid Options), `Render/Render Sequence` generic → window, `Render/Batch Render` dead → window
(step 152). **Two regressions redo → generic**: `Display/Toggle Show/Hide` and `Edit/Delete by Type/Non-Deformer History` now open the
"Blender has no settings" window instead of running with Adjust Last Operation (consistent with step 147's "no redo panel" for
display / key commands, but in Maya both boxes are real option windows, so the box got less useful).
`Render/Render Current Frame` / `IPR Render Current Frame` stay `generic` in the count, though since step 152 they show Maya's own
'Renderer "<name>" does not provide render options.' warning — Maya-exact, but the classifier does not separate it.

The 43 generic boxes, by Maya-user impact: daily — `Curves/Attach`, `Detach`, `Smooth` (×2), `Reverse Direction`, `UV/Merge UVs`,
`UV/Contour Stretch`, `UV/3D Cut and Sew UV Tool`, `Skeleton/Set` / `Assume Preferred Angle`, `Skin/Edit Influences/Add Influence`,
`Edit/Delete by Type/Non-Deformer History`; weekly — 9 `Deform/Paint Weights/*`, `Surfaces/Loft / Extrude / Planar / Bevel Plus /
Reverse Direction`, `nCloth/Create nCloth / Create Passive Collider`, `nParticles/Create Emitter` (×2) / `Emit from Object` (×2) /
`Make Collide`, `Fluids/Make Collide`, `Modify/Bake Pivot`, `Mesh Display/Paint Vertex Color Tool`, `Texturing/3D Paint Tool`,
`Create/Curve Tools/Pencil Curve Tool`, `File/Archive Scene`, `Control/Create Character Set`, `Display/Toggle Show/Hide`.

How a box opens: a plain click on a box item still runs the command with saved / default values (Blender can't tell the ❒ part from
the label, `docs/steps/step_146.md` 계획 1); the window opens on a 0.2 s press and release. A Maya user who clicks the ❒ like in Maya
still gets the command, not the window. On Blender 5.x the Maya menu stays open under the window (step 153).

## 3. Shelves (`ui/shelf.all_buttons`)

203 buttons, **153 working (75 %)**, 50 greyed with a notice, 0 without. Only change: Rendering 19 → 21 (Cancel / Show Batch Render).

| Shelf | Buttons | Working | Greyed (+ notice) |
|---|---|---|---|
| Curves / Surfaces | 38 | 24 | 14 (unchanged list: circular arc, rebuild / intersect / trim / attach / detach / extend surfaces …) |
| Poly Modeling | 43 | 41 | 2: Super Shape, 3D Grab UV Tool |
| Sculpting | 26 | 19 | 7: Imprint, Convert To Frozen, Pose Editor, Smooth / Clone / Mask / Erase Target |
| Rigging | 18 | 17 | 1: Human IK |
| Animation | 14 | 14 | 0 |
| Rendering | 25 | **21** | 4: Ambient Light, Volume Light, Shading Map, Render Diagnostics |
| FX | 29 | 13 | 16: 2D Fluid Container with Emitter, Make Selected Curves Dynamic, 14 nHair buttons |
| FX Caching | 10 | 4 | 6: Set / Clear Initial State, Enable / Disable All Caches, Merge Caches, Replace Cache Frame |

## 4. Hotkeys / marking menus

Hotkeys (`docs/keymap_mapping.md`, 468 rows): 구현 **202**, IC 일치 **27**, 해당 없음 171, 미검토 0, macOS 전용 68 — the 3 moved rows are
SetKeyTranslate / Rotate / Scale (Shift+W / E / R, step 151). The 171 n/a rows still include the daily keys of editors with no Blender
counterpart (UV Editor 4/6/8/9, Ctrl+1 isolate, Delete UVs; Hypershade / Node Editor 57 rows; Time Editor 32; Graph Editor `l`).
Menu hotkey text: 57 main-menu items, 0 editor-bar items (unchanged).

Marking menus: 474 entries, 364 working, 69 greyed (each with a `notices.MARKING` notice), 41 submenus. Only change: RMB object `UV`
became a submenu (`UV` + `UV Shell`, step 151, like Maya 2022). The 69 greyed entries are the same list as step 145 §5 (Shift+Q non-mesh
masks 25, RMB Vertex Face / DG Traversal / Inputs / Outputs / Metadata / Time Editor, Shift+RMB Reorder Vertices / Merge Edge Tool /
Pipe / Helix / Gear, w/e/r Live Object Axis / Custom / Reset, a-key outputs, hotbox Time Slider / Range Slider toggles, UV Create UV
Shell / Delete UVs / Auto Seams / Texture Borders, Complete Tool, Show Orientation Handle).

## 5. look_compare at effective UI scale 1.0

`research/maya/screens/compare_audit154_s100/` (15 side-by-side images, 6 crops). Summary lines:

- checks 9/9; pixels kit-drawn **5/6** (theme 30, 19 > 5 not counted, 2 no kit element); viewport **11/12**; rects **5/12**; scene 3/3;
  density 5/6 (menu top − bar bottom −6 px); grid ok (ΔE00 0.7, corners 4/4); furniture 2/3 (axis triad outline only).
- Only change vs step 145: `marking_menu_box` ΔE00 0.3 → 13.0. Not a colour regression: since step 151 the ring is Maya-sized (R 55,
  21 px boxes), so the fixed kit point (797, 414) in `14_marking_menu_object` now lands on the cube's top face (#747577) above the
  Edge box. `tools/look_data.py` KIT_POINTS needs re-picking for that sample.

Visible differences in the images (differences only):

1. **Theme colours** (decided, #45): Blender dark menu bar / popup menus #181818 vs Maya #444444 / #525252, editor gaps #161616 vs Maya's
   #5c5c5c (Maya panes join with no dark seams), frame fields #545454 vs #2b2b2b, Outliner selected row #334d80 vs #5285a6, Tool Box
   active tool #4772b3 vs #5285a6.
2. **Selected faces** (`07`): the kit fills selected faces nearly opaque orange (raw mean #ad8e6e); Maya stipples #e3ac79 at ~25 % over
   the shading (mean #918477). The one failing viewport element, unchanged since step 134.
3. **Four view** (`16`): the kit's quad view has one panel menu + toolbar for all four panes (Blender Quad View); Maya has a header per
   pane. The kit ortho panes are zoomed far in (cubes ~5× larger than Maya's), labels `top -Z` / `front +Y` vs Maya `top -Y` / `front -Z`
   (Y-up, decided C), and the view cube shows only in the front pane (Maya: TOP in the top pane).
4. **Create menu** (`12`): the popup overlaps the menu bar by 6 px, starts with the tear-off row instead of Maya's "Objects" section
   label, shows Blender's underlined mnemonic letters, and lists a `Subdiv Primitives` row that the Maya 2022 shot does not have.
5. **Outliner**: no "Outliner" dock title bar (Maya has one); row order pCube1–3 first, then persp / top / front / side (Maya: cameras
   first); in edit mode the kit adds dot markers before mesh rows (`07`).
6. **RMB marking menu** (`14`): ring now matches Maya; the list below wraps into a second column (Paint, Metadata, Actions, UV Sets,
   Color Sets, Time Editor, Material Attributes, Assign … Material) to the right, where Maya keeps one tall column that runs off the
   window bottom; the kit draws a ring cursor at the centre.
7. **Move manipulator** (`02`): kit arrows + centre box only at this size; Maya's red / green / blue plane squares are clearly visible
   between the axes, the kit's are not.
8. **Bottom rows**: Time Slider ruler 1300 px wide (frame field + transport in a separate area right), Maya 1596 (rect Δw −296, Δy +24);
   Command Line language label `Python` (Maya `MEL`); a Maya / Blender switch at the right end of the top bar that Maya doesn't have.
9. **Hotbox** (`13`): centre box reads "Maya Workflow Kit" (Maya: "Maya"); MASH rows absent (plug-in; expected).
10. Layout rects: Tool Box / Outliner / viewport / dock 37 px taller and start 10 px higher than Maya's (Maya's Outliner starts 17 px lower, under its title bar), dock 27 px wider (Channel Box tab 287 vs 260).

## 6. Not measured

- Live Maya side-by-side scenario (file I/O, modeling, UV, animation, rigging, FX, render runs): this lane only re-ran the counted
  measurements and look_compare; no new Maya capture (Maya images are the existing `research/maya/screens/*`).
- look_compare at effective 1.25: not run (step 145 also measured 1.0 only).
- Distinct-option-window count uses the step 133 probe (83); it does not check that each window's fields match Maya.
