# Step 145 lane B — what is done, what is left, blindspots (audit 9)

User request (2026-10-24, items 2 and 5): "research/README.md 대응표·docs/PLAN.md·docs/steps/*.md 「남은 것」·docs/manual_checks.md를
모아 끝난 것 지우고 남은 것 정리 (know-your-unknowns blindspot으로 놓친 것 보완) … 비판 기준: '기본 Maya에 Blender 기능이 붙은 모습'
… 칭찬 말고 차이만 … 메뉴 전수 대비 …".

Paper lane, no GUI. Sources: `research/README.md` mapping table (33 rows), `docs/PLAN.md` 「재점검 8차」, `docs/steps/step_133_remaining.md`
(the audit-8 consolidated list of steps 98–132), every 「남은 것」 of `docs/steps/step_134*.md` … `step_144*.md`, `docs/manual_checks.md`,
`docs/compat_5x.md`, open GitHub issues (`gh issue list --state open`, 2026-10-24: **#81 #82 #83 #85 #86 #87 #88 #89**; #1–#80 and #84 are
closed). Every verdict re-checked against `src/allset` at HEAD de5feb7 by grep / script ("[I]" = read from code, not run). Counts:
`docs/steps/step_145_quant.md`. Verdicts are delegated.

## 1. Implementation rate — research/README.md mapping table (33 rows)

| Group | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | 12 | 1 — selection modifiers outside the 3D View | 0 | 0 |
| UI (9) | 8 | 1 — theme (Maya grey) | 0 | 0 |
| 개념 (11) | 9 | 0 | 0 | 2 — separate rotate / scale pivots, Y-up |
| **Total (33)** | **29 (88 %)** | **2 (6 %)** | **0** | **2 (6 %)** |

Audits 1 → 9: 21/8/2/2 → 23/8/0/2 → 25/6/0/2 → 27/4/0/2 → 28/3/0/2 → 29/2/0/2 (6) → 30/1/0/2 (step 96) → – (7) → 29/2/0/2 (8, theme
regression by step 130) → **29/2/0/2 now (no row moved; both partial rows narrowed)**.

Row by row (evidence = step / file):

| Row | Verdict | Evidence |
|---|---|---|
| Alt+L/M/R tumble / track / dolly | Done | Blender factory turntable / COI; Alt+RMB = `allset.dolly` (3D, `operators/view.py`), `allset.dolly_2d` (Image / UV, step 141); Graph Editor / Node Editor Alt+RMB not kit (Node = IC link cut, step 141 「남은 것」) |
| QWERT, MMB drag | Done | IC + kit tools (steps 2, 59) |
| Shift / Ctrl / Ctrl+Shift click | Done | `keymap/maya_patches.py` `SELECT_RULES` (3D, UV click, Node exact) |
| 4/5/6/7 | Done | step 2, HUD fix step 134 |
| 1/2/3 smooth preview | Done | step 15, smooth shading step 134 (#61) |
| Ctrl+G group | Done | step 2 |
| D / Insert pivot | Done | steps 59, 77, 94 |
| X/C/V hold snap | Done | step 3, `operators/hold.py` |
| Arrow pick-walk | Done | steps 3, 39, 57 |
| Shift+drag manipulator = duplicate / extrude | Done | steps 22, 26, 143 (move after extrude) |
| `[` `]` view undo | Done | step 4 |
| Space hotbox | Done | steps 9, 52, 136 |
| RMB / Shift / Ctrl+RMB marking menus | Done | steps 8, 9, 136 (greyed 128 → 69, quant §5) |
| **Selection modifiers in other editors** | **Partial** (unchanged since audit 6) | `maya_patches.py:59-62`: uv / outliner / graph / action / nla `select_box` have no XOR, Shift-marquee adds instead of toggling; Outliner / Graph click: Ctrl and Ctrl+Shift fall back to toggle (`:50-57`); Node Ctrl-marquee = Blender link cut (`:64-68`) |
| Layout | Done | `switch.enter_layout`, `allset.new_maya_scene`, Maya layout on File > Open (step 138) |
| Channel Box (+ MMB) | Done | steps 6, 38, 129, 135 |
| Attribute Editor | Done | steps 11, 91, 106, 116 |
| Maya Outliner | Done | steps 82, 96, 99 |
| Status Line / Shelf | Done | steps 12, 113, 131 |
| Time / Range Slider | Done | steps 20, 56, 73, 84 |
| Command line | Done | step 7, run_script since step 130 |
| Menu sets | Done | step 7 |
| **Theme (Maya grey)** | **Partial** (narrowed) | No theme may ship (decision 13 / 14). Kit-drawn now: lead #43ffa3 / white selection wire (`ui/selection_wire.py`, step 134), component colours (`ui/component_colors.py`), grid #404040 (`ui/maya_grid.py`), viewport #5c5c5c, Move / Scale manipulator axis colours + dormant wire #000460 (step 142). Still the user's Blender theme: every widget, menu / panel background, Outliner selection, Dope Sheet / Graph key colours, Rotate gizmo, edit-mode element edges under the kit colours (step_134.md 「남은 것」) |
| Transform / Shape | Done | kit Outliner / AE / CB SHAPES |
| Construction history | Done | steps 15, 65, 129, 139 records + Delete History |
| Freeze Transforms | Done | step 10 |
| Center Pivot | Done | step 10 |
| Separate rotate / scale pivots | Not possible | decision (README) |
| Group | Done | step 2 |
| Display Layer | Done | steps 6, 129 (#26) |
| Parent keeps world | Done | decision 4, `operators/parenting.py` |
| Y-up | Not possible | decision 5; I/O axis conversion only (step 138) |
| cm units | Done | decision 8, step 21 |
| Naming pCube1 / pCubeShape1 / polyCube1 | Done | steps 10, 129 |

## 2. Done since audit 8 — delete from the backlog

| Item (source) | Closed by (evidence) |
|---|---|
| Audit-8 backlog 1–8 (PLAN 「재점검 8차」): viewport look, dock / CB, marking menus, animation / render basics, scenes and files, Edit Mesh / UV results, option windows, keymap / selection batch — issues #55–#75 | steps 134–141; all closed on GitHub |
| #16 instant bevel, #30 Quad Draw / Create Polygon / Append, #31 Insert / Offset Edge Loop / Slide Edge, #32 #33 #35 option windows, #34 Deform | steps 139, 140, 144 (closed) |
| #76 manipulator / dormant wire colours, #77 menu bar overflow at 1.5, #78 dock width, #54 icons, #41 store media without a theme | step 142 (closed) |
| #79 Maya mode on 5.2.3, #80 move after extrude, #84 double-click loop on 5.1+ | step 143 (closed) |
| Audit-8 blindspots B1 tool settings carry, B2 Ctrl+A in edit / pose, B3 layout on Open, B4 UV Alt+RMB, B6 undo depth | B1 / B3 step 138 (`ui/scene_carry.py`, `gui_step138_open`); B2 / B4 / B6 step 141 (`maya_patches.CTRL_A_MODES`, `allset.dolly_2d`, `preferences.undo_hint`) |
| Render Settings HD 540 default | step 137 (template 960 × 540) |
| Select > Grow / Shrink Along Loop, Convert to UVs / Face Path / Shell Border | step 141 (`operators/select_convert.py`) |
| Marking menu Merge / Connect / Bevel / Automatic using raw Blender ops (step_139_edit / _shape / _uv 「남은 것」) | done: `marking/menus.py:322,332,346,374,386`, `ui/shelf_map.py:68-69,130` go through `("item", "Edit Mesh/…")` |
| Graph Editor metres in the cm scene | step 137 (`ui/graph_units.py`; mouse-off-curves limit stays, below) |
| Key > Scale Keys | step 140 |
| 25 marking-menu entries greyed but working from the menus (#74) | step 136 (0 left, quant §5) |
| Obsolete (feature removed, not done): theme files / 5.x theme keys / `_rna_xml` / Alt+B Maya-theme gradient / app-template install / Maya density / Segoe UI / `user_disabling` items | step 130 store rules — `docs/compat_5x.md` 「테마 차이」 and 「남은 것」 bullets 2 and 4 are stale text, not work |

## 3. Remaining work, one list (Maya-user impact first)

Score = daily frequency F (1–5) × severity S (1–4), grades 외형 / 조작 / 기능 / 없음 as in step 98. "src" = where the item was written.

| # | Item | Grade | F×S | Sources |
|---|---|---|---|---|
| 1 | **Option boxes open only by press-and-hold** → "Option Box"; a plain click on ❒ runs the command (Maya: click the box). All 75 Maya windows + 22 dialogs are hidden from a Maya user | 조작 | 5×3 = **15** | #82 (user), step_143.md, CLAUDE.md step 51 / 103 |
| 2 | **Undo: Mesh Tools items that enter edit mode push no undo step** — the first Ctrl+Z leaves component mode | 기능 | 4×3 = **12** | #88, step_144.md |
| 3 | **Channel Box RMB on a channel name** shows Blender's button menu (no Key Selected / Mute / Break Connections …) | 기능 | 4×3 = **12** | #87, step_142.md |
| 4 | **Narrow dock truncates** labels / values at UI 1.25 (this PC's default): "Chann…", AE Scale "1." | 외형 | 5×2 = **10** | #85, step_142.md |
| 5 | **Rendering a Maya scene**: no default light (a lightless scene renders dark; Maya Software has one), Render Current Frame / Sequence / IPR boxes = "no settings", Batch Render / Test Resolution / Render Diagnostics greyed, Render Setup greyed (Status Line) | 기능 | 3×3 = **9** | step_137.md, step_137_render.md, quant §1b / §2 |
| 6 | **Curves / NURBS modelling**: EP Curve Tool, Rebuild, Fillet, Edit Curve Tool, Cut, Intersect, Straighten greyed; Curves 44 %, Surfaces 20 % (29 / 37 boxes dead); 14 Curves / Surfaces shelf buttons greyed | 없음 | 3×3 = **9** | quant §1b / §3, step_133_quant §9 #5 (unchanged) |
| 7 | **UV Editor tools**: Tools > Unfold / Move UV Shell / Cut / Sew / Pin, Modify > Stack / Snap Together / Distribute / Orient / Straighten / Map Border, Auto Seams, Delete UVs, Toggle Shell Borders, Isolate Select; UV Toolkit = 3 leaves; keys 4 / 6 / 8 / 9, Ctrl+1, Delete n/a | 기능 | 3×3 = **9** | quant §1c / §4, step_133_quant §9 #4 |
| 8 | **Graph Editor depth**: View / Show 46 greyed (Show Buffer Curves greyed although buffer curves = ghost curves work, curve names, auto frame); kit channel list has no pose-bone / shape-key curves, no scroll / marquee (step_104); Key commands in the Graph Editor act on Channel Box nodes, not selected keys (step_140 「남은 것」); value labels revert to metres off the curve area (step_137_graph); editor menu bars show no Maya hotkeys (0 entries, step_108); Default In / Out Tangent items only open Preferences | 기능 | 3×3 = **9** | step_104, step_108, step_137_graph, step_140, quant §1c |
| 9 | **Maya workspaces / Reset UI**: no way back to the default Maya layout but a restart (#81); Windows > Workspaces = Blender's menu (`ui/menu_map.py` `TOPBAR_MT_workspace_menu`); only the "General" workspace exists (`tools/make_startup.py:300`; Maya has Modeling / Rigging / Animation / UV Editing / Rendering …) | 조작 | 3×3 = **9** | #81 (user), step_133_remaining 2.4, research/maya/ui_layout.md:139-158 |
| 10 | **Weights and rig utilities**: Skin Export / Import Weight Maps, Deform Export / Import Weights, Move Weights to Influences, Interactive Bind Skin, Post Normalization, 35 Joint Labelling items, Enable / Disable IK Handles, IK/FK control | 없음 | 2×4 = **8** | quant §1b, step_110 「남은 것」 |
| 11 | **Shelf Create Joints**: Adjust Last Operation panel over the shelf eats the next click | 조작 | 3×2 = 6 | #86 |
| 12 | **2D editors**: Ctrl+A = select-all in Graph / Dope Sheet / Outliner / Node (Maya global AE toggle); Node Editor Alt+RMB = IC link cut (no Hypershade dolly); box XOR missing outside the 3D View (README partial row) | 조작 | 3×2 = 6 | step_141 「남은 것」, README row |
| 13 | **Channel Box look**: every animated state one alert red + icon (Maya: keyed red, driven / connected yellow, expression purple, muted brown — research/maya/channel_box.md:138-139; `ui/channel_box.py:1502`); light SHAPES rows show Blender Power, not Maya Intensity (step_137_defaults); lambert1 diffuse 0.8 missing → renders 1.25× brighter (step_100, step_137) | 외형 | 3×2 = 6 | audit-8 B5, step_137_defaults.md |
| 14 | **Grid options**: the Maya grid is fixed ±12 units, spacing 5, divisions 5 (`ui/maya_grid.py:27`), Display > Grid ❒ = "no settings" (blindspot BS3) | 기능 | 3×2 = 6 | this audit |
| 15 | **Visualize** 20 % since step 98: Ghost Selected / Ghosting Editor, Create / Update Animation Snapshot | 없음 | 2×2 = 4 | quant §1a |
| 16 | Script Editor History menu 0 / 13 (Echo All Commands — how Maya users learn commands; Blender's Info editor already shows the operators) | 기능 | 2×2 = 4 | step_105, quant §1c |
| 17 | Quad Draw leftovers (overlay colours, Tab+MMB strip, Ctrl+Shift+RMB menu), Insert Edge Loop Auto complete / Fix Quads, Lattice local mode, nonlinear shapes approximated | 기능 | 2×2 = 4 | #89, step_144.md |
| 18 | Hypershade graph: Create 91 / 160 greyed, Tabs / Options 0 / 12, Graph Clear / Add / Remove / Rearrange greyed, 25 keys n/a | 조작 | 2×2 = 4 | step_133_quant §9 #9 (unchanged) |
| 19 | Mesh / Edit Mesh fidelity: Connect ≥ 4 points (Maya edge order, M11), Automatic "Less distortion" shell sizes, Contour Stretch ≠ Maya 4-corner, Bevel Chamfer off / Mitering / Smoothing Angle, primitives approximations (step_129_prims) | 기능 | 2×2 = 4 | step_139*.md |
| 20 | Open: Blender's "Save changes before closing?" wording; second window gets the file layout; tool settings not kept across sessions (Maya prefs) | 외형 | 2×1 = 2 | step_138*.md |
| 21 | UI 1.5: two empty rows above the Layer Editor | 외형 | 1×1 = 1 | #83 |
| 22 | FX / Generate / Toon / nHair / nConstraint (0–18 %): whole systems without a Blender counterpart — notices only | 없음 | 1×4 = 4 | quant §1a |
| 23 | **Blender 5.x: Paint Skin Weights ❒ window raises** (`ToolSettings.unified_paint_settings` gone in 5.0) | 기능 | 2×3 = 6 | **#90** (this audit, §5) |

Verification / housekeeping debt (not Maya-user facing):

- **5.x full runs**: before this audit the whole suite last ran on 5.x in step 118 (877 tests); steps 119–144 ran only subsets
  (`-k step137,enable_disable`, `-k step143,step105,step118,enable_disable`, release_check 5.2.2). This audit's 5.2.2 headless run found
  #90 (§5); 5.0.1 / 5.1.2 headless and every 5.x GUI run are still owed.
- `docs/compat_5x.md` result table and theme sections describe the step-118 / theme era (stale).
- `docs/manual_checks.md`: 470 open after this audit's cleanup (§6); 11 items partly stale (list in quant §6).
- Code cleanup carried: `ui/outliner.py:9,132-169` still rebuilds `allset_outliner_rows` for a list nobody draws (step_116);
  `marking/rmb_items.py:207-208,321` keeps the old VERTEX_PERIMETER / SHELL_BORDER rules only for a test (step_141); ruff findings in
  tests / tools (step_117).
- `[K]` behaviours never compared with a running Maya (Quad Draw click rules step_144_poly, Symmetrize click side step_139_edit, B-drag
  soft-select rate step_129).
- User actions (Hermes): publish the v0.3.0 draft release, upload `maya-workflow-kit-0.3.0.zip` to the store (step_143.md).

## 4. Blindspots (not in any step 「남은 것」, issue or test — checked by grep)

| # | Maya behaviour | Kit today (evidence) | F×S |
|---|---|---|---|
| BS1 | **Preferences window** (Windows > Settings/Preferences > Preferences): Maya's Settings page is where a Maya user sets working units (cm / m / in), time (fps), up axis, undo queue, default tangents, manipulator size | opens Blender Preferences (`ui/menu_map.py` `screen.userpref_show`); the Maya-meaning options are spread over the add-on preferences (`preferences.py`: Maya Units, CB speed, parent mode …); grep "Working Units" in `src/allset` = 0. Units / fps are only reachable through Blender's Scene properties or the Time Slider fps menu (`ui/time_slider.py:148`) | 2×3 = 6 |
| BS2 | **Hotkey Editor**: a Maya user rebinds keys there and the change persists | opens Blender Preferences > Keymap. The Maya keys are add-on keyconfig items regenerated on every `keymap.activate()` (`keymap/__init__.py:237-246`, 1 s `_watch`). Whether a user edit of a Maya key survives a restart / Maya ⇄ Blender switch is untested: `tests/test_step130_keymap_lifecycle.py:67` only asserts that the kit itself makes no user keymap edit. [I] | 2×3 = 6 |
| BS3 | **Grid Options** (Display > Grid ❒: length and width, grid lines every, subdivisions, colours) — Maya users enlarge the grid for big scenes | the kit grid is constants `SIZE 12 / SPACING 5 / DIVISIONS 5` (`ui/maya_grid.py:4-36`); the box opens `allset.option_generic` ("no settings", quant §2). A 20 m (2000-unit) set has a 24-unit grid patch in the middle | 3×2 = 6 |
| BS4 | **Reference Editor**: reload / unload / replace / import objects from a reference, namespaces | File > Reference Editor opens the Outliner in Blender File mode (`menu_map.py` `('allset.open_editor', {'ui_type': 'OUTLINER', 'display_mode': 'LIBRARIES'})`); the kit has only Create Reference (step 69); Namespace Editor greyed (`ui/notices.py:63`) | 2×3 = 6 |
| BS5 | **Render Setup / render layers** (Maya 2022's default layer system: collections + overrides) | Status Line Render Setup greyed (`ui/status_line.py:543`), Windows > Render Layers / Render Layer Editor = Properties View Layer tab, Hypershade Create > Render Layer = `scene.view_layer_add` | 2×3 = 6 |
| BS6 | **Outliner Shift+click = range select** [K] (Maya Outliner: Ctrl toggles, Shift selects the run) | Outliner Shift / Ctrl / Ctrl+Shift click all = extend (toggle) (`maya_patches.py:52-55`); the step-2 manual check "Outliner Ctrl / Shift rule to confirm against Maya" (`docs/manual_checks.md`, Step 2) is still open after 143 steps | 3×2 = 6 |
| BS7 | **"Working" menu items that only open Blender's own window**: 52 main-menu leaves (30 editors, 4 Preferences, 18 web pages) and 91 editor-bar leaves (52 web pages, 39 Preferences) are counted as working | `menu_map.MAP` values `allset.open_editor` / `screen.userpref_show` / `wm.url_open` (quant §0, §1c). The headline "45 % working" overstates what a Maya user can do from the menus by ~4 points (main) / ~10 points (editor bars) | 2×2 = 4 |
| BS8 | **5.x after step 118** | see §3 debt; the bmesh-heavy steps 139–144 (edge loops, Quad Draw, deformers, select conversions) have never run on 5.x as a whole suite before this audit | 2×3 = 6 (risk) |

Not blindspots (checked, listed elsewhere): Script Editor MEL (decision, not possible), Playblast options (`Playback/Playblast` ❒ =
dialog, step 70), scene units (decision 8 + Maya Units preference), multi-window layout (step_138 「남은 것」), Undo queue (step 141 hint),
playback Once / Oscillate (not possible), Marking Menu / Shelf / Panel Editor (greyed with a notice since step 101).

## 5. Blender 5.2.2 headless run (this audit)

`ALLSET_SANDBOX=audit145b python tests/run.py --no-build --blender <portable 5.2.2>` on `dist/maya-workflow-kit-0.3.0.zip` (HEAD
de5feb7): **157 files, 1305 / 1308 pass, 3 fail** — the first whole-suite 5.x run since step 118.

- Kit bug, filed **#90**: Skin > Paint Skin Weights ❒ (the step-140 Paint Skin Weights Tool window) raises on Blender 5.0+ —
  `operators/skin.py:494` reads `ToolSettings.unified_paint_settings`, which 5.0 moved to `tool_settings.weight_paint.unified_paint_settings`
  (probe on 5.0.1 and 5.2.2); no `compat.py` shim. The mesh is left in Weight Paint without the Maya settings. Plain click unaffected.
  Test: `test_step140_rig::test_paint_skin_weights_tool_settings`.
- Test-only (same API): `test_step129_audit_p1::test_paint_skin_weights_normalizes_interactively`,
  `::test_flood_keeps_blender_choice_without_normalization` write `ts.unified_paint_settings.weight` directly (#90 notes it).
- Expected drift (no action): every file logs "1 keymap patch doesn't apply to 5.2.2: Node Editor: no item node.viewer_border Z"
  (`patch.DRIFT` outside 4.5).
- Not run: GUI suite on 5.x (Lane A owns the GUI session; one Blender at a time here).

## 6. Manual checks cleanup (`docs/manual_checks.md`)

- Before: 580 items, 70 ticked, 510 open (81 added by steps 133–144). After: **548 items, 78 ticked, 470 open**.
- **Deleted 32 obsolete items** (+ 4 empty section headers Step 44 / 111 / 112 / 119) — the feature or setting no longer exists since
  step 130 (store rules) or step 116 (dock left the sidebar): Activate Maya Keymap / Quick Setup keymap (step 2 ×2, step 7, step 13 ×2),
  Maya Navigation Preferences (step 4), Install / Remove Maya Layout, New File with Maya Layout, Apply Maya Theme, template re-enable
  (step 5 ×4), sidebar Channel Box tab (step 6), Revert Maya Look (step 42), Maya density / Segoe UI / flat widgets (step 44 ×5),
  sidebar dock / Channel Box Dock Only (step 49), Maya Font (step 52), Restore Blender Settings (step 60), Allset name + MayaKit template
  (step 111 ×2), Solid Side Panels (step 112), user template removal (step 115, step 125), 5.x Maya theme (step 118, step 119 ×5), Alt+B
  with the Maya theme (step 120). Old line numbers: quant §6.
- **Ticked 8** whose every clause a GUI test asserts: Step 138 Ctrl+N untitled / saved prompt (`gui_step138_prompt`), Maya layout on
  File > Open + option off (`gui_step138_open`), Step 139 Connect / Merge / Smooth / Symmetrize (`gui_step139_edit`), UV > Automatic +
  UV Editor Best Plane / Contour Stretch (`gui_step139_uv`). Not ticked although a GUI test exists, because the item also asks for
  something the test doesn't check: Step 138 tool settings (soft-select radius not asserted), Step 137 render (Outliner persp row),
  Step 137 defaults (Color / Incandescence / Roll Off, Cycles light), Step 135 dock (1.0 / 1.5 scales), Step 144 tools (visual feedback).
- Still to rewrite (partly stale, kept): Step 13 disable item (navigation), Step 42 install / restart items (theme, File > New entry),
  Step 49 / 99 Maya Density wording, Step 53 (navigation, 5.x Maya theme colours), Step 60 switch (theme), Step 99 dock tabs (Blender
  Item tab — gone), Step 115 / 125 install items (template / File > New entry).
