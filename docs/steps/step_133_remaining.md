# Step 133 lane DOCS — what is done, what is left, blindspots (audit 8)

User request (2026-10-22, items 2–3): "research/README.md 대응표·docs/PLAN.md·docs/steps/*.md 「남은 것」·docs/manual_checks.md를 모아
끝난 것 지우고 남은 것 정리 (know-your-unknowns blindspot으로 놓친 것 보완) 3) docs/PLAN.md에 「재점검 7차」 절(구현률: 대응표 항목 중
완료/부분/불가, 남은 것 우선순위) 작성".

Read-only lane: sources = `research/README.md` mapping table (33 rows), `docs/PLAN.md` 「재점검 6차」 / 「재점검 7차(정밀 비판)」,
every 「남은 것」 / "Left" section of `docs/steps/step_98*.md` … `step_132*.md`, `docs/manual_checks.md`, `docs/keymap_mapping.md`,
`docs/user_decisions.md` 14, open GitHub issues (`gh issue list --state open`, 2026-10-22). Every verdict below was re-checked
against today's `src/allset` (HEAD 1ac4b77 + uncommitted step 133 docs) by grep; "[I]" = read from code, not run. Verdicts are
delegated. Step 130 (store compliance, decision 14) removed the theme, Blender preference presets, app-template install and the
active-keyconfig switch, so rows that relied on them were judged again.

## 1. Implementation rate — research/README.md mapping table (33 rows)

| Group | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | 12 | 1 — selection modifiers outside the 3D View | 0 | 0 |
| UI (9) | 8 | 1 — theme (Maya grey) | 0 | 0 |
| 개념 (11) | 9 | 0 | 0 | 2 — separate rotate/scale pivots, Y-up |
| **Total (33)** | **29 (88 %)** | **2 (6 %)** | **0** | **2 (6 %)** |

Audits 1 → 8: 21/8/2/2 → 23/8/0/2 → 25/6/0/2 → 27/4/0/2 → 28/3/0/2 → 29/2/0/2 (audit 6) → 30/1/0/2 (after step 96) →
audit 7 (step 98) had no rate table → **29/2/0/2 now: one regression, the theme row (Done → Partial) by step 130**. If store policy
is counted as a wall, the theme row is "not possible": 29/1/0/3.

Partial rows (evidence):

- **Selection modifiers outside the 3D View** (unchanged since audit 6): `src/allset/keymap/maya_patches.py:59-62` — UV / Outliner /
  Graph / Dope Sheet / NLA box select have no XOR mode, so Shift-marquee adds instead of toggling (`:79-87`); Node Editor has no
  Ctrl-marquee deselect (`:68` `_NODE_BOX`).
- **Theme (Maya grey)**: the kit ships no theme (`tests/test_step5_layout.py:24`, `tests/test_step130_package_scan.py:199`). What is
  still Maya: the Maya layout's 3D views have their own flat #5c5c5c background (`tools/make_startup.py:344`,
  `operators/key_batch3.py:71`), and kit-drawn surfaces keep Maya colours (marking menus / hotbox, Graph Editor outliner panel,
  Range Slider, In-View Editor, in-view messages, soft-select colours; `docs/steps/step_130_theme.md:21-24`). What is now Blender's
  (user theme): lead / selected colours (orange instead of green #43ffa3 / white), widgets (rounded), menu background #181818
  instead of #525252, menu bar / Status Line / shelf header #303030 instead of #444444, Outliner selection, Dope Sheet key colours,
  out-of-range shading, Alt+B gradient step (`step_130_theme.md:48-62`).

Rows re-judged after step 130 and kept Done:

- **Alt+L/M/R tumble / track / dolly** — the navigation preset is gone, but Blender 4.5 factory values already match Maya (Turntable,
  orbit about the view centre = COI, no zoom-to-mouse) except the zoom axis; Alt+RMB in the 3D View is the kit's own `allset.dolly`
  (horizontal drag, `operators/view.py:50-97`, `maya_patches.py:228-231`, #51). Caveat: 2D editors — blindspot B2.
- **Layout (App Template)** — now `switch.enter_layout` (append the bundled workspace) + `allset.new_maya_scene`
  (`first_start.py:28-35`) + "Start in Maya Layout" (`preferences.py:46`). Lost: File > New entry. Caveat: blindspot B3.
- **Command line** — `bpy.ops.text.run_script` instead of exec (step 130 lane E); behaviour differences listed in
  `step_130_exec.md:42-55`.

Other counters (vs audit 7): keymap rows (468) implemented 155 → **199**, IC 15 → **30**, n/a 11 → **171**, unreviewed 219 → **0**,
macOS 68 (`docs/keymap_mapping.md:9-14`). Manual checks: see §3.

## 2. Open items (deduplicated, grouped; source = where the item was written)

### 2.0 Closed since audit 7 (checked by grep / step docs — delete from the backlog)

| Item | Source | Closed by |
|---|---|---|
| Audit-7 backlog 1–12 (first screen, lambert1, menu honesty, file I/O, option boxes, editor chrome, Hypershade / Render Settings / Script Editor, Tool Settings + AE, keymap 219 unreviewed, menu hotkeys, shelves, modeling / rigging gaps) | PLAN 「재점검 7차」 | steps 99–110 (each has a step doc; keymap unreviewed = 0) |
| AE creation-node tab (polyCube1) | step_106 | step 129 (`ui/attribute_editor.py:145-147`, `prim_history`) |
| Hypershade Maya layout (Browser / Create / Material Viewer) | step_100, step_105 | step 131 (`ui/hypershade_layout.py`) |
| Skin Edit Influences / Hammer, Pencil Curve | step_101 candidates | step 110 (`ui/menu_map.py:836-839`), `menu_map.py:808` |
| Welcome text clipped at 125 %, "persp" drawn twice | step_122, step_123 | step 124 (HANDOFF) |
| Key visual stretched | step_125 | step 126 |
| 5.x compat, version bump | step_117, step_118 | steps 118, 132 (0.2.1) |
| #53 relayout at 1.25, #52 toolbar overflow, #44 Ctrl+N | step_129, step_130 | step 132 |
| Icons #23, Hypershade #25 | step_129 | step 131 (follow-up #54) |
| Item tab can't be hidden, kit Outliner default rows in the sidebar | step_99 | obsolete: dock left the sidebar (step 116) |
| `user_disabling` on 5.x, template removal, `reinstall_if_wanted` | step_115 | obsolete: removed in step 130 |
| 5.x theme files, Outliner outline key, Alt+B gradient ΔE | step_119, step_120 | obsolete: theme removed in step 130 |
| Audit-6 later list: UV checker, Straighten, Spline IK, Make Live, Component Editor, 0.8 scale / 5.x GUI runs, template copy refresh | PLAN 「재점검 6차」 9 | `menu_map.py:674`, `editor_menu_map.py:250-251`, step 110, `menu_map.py:232`, `:600`, steps 98 / 118, step 130 |

### 2.1 Maya option windows and tools (GitHub milestone 0.3.0)

- #16 Ctrl+B bevel = mouse modal, Esc leaves nothing (Maya bevels at once).
- #30 Quad Draw / Create Polygon / Append = Blender Poly Build; #31 Insert Edge Loop / Slide / Offset Edge Loop = Blender tools.
- #32 rigging tools (Joint, IK Handle, IK Spline, Paint Skin Weights, Unbind / Copy Skin Weights) open "no settings".
- #33 modeling option boxes: Blender redo fields instead of Maya windows (28 windows) — includes step_103 "144 boxes are still Adjust
  Last Operation" and the missing fields Taper / Twist / Smoothing angle (`operators/option_windows.py:423`, `:435`), Cone height
  divisions.
- #34 Deform menu without Maya creation options; Paint Weights doesn't pick the deformer.
- #35 Key menu / constraints options; Scale Keys missing.
- Same family, not in an issue: Make Hole merge modes, Circularize options, Soft Mod falloff surface / mask, Cluster weight paint,
  Nonlinear bounds in the CB (step_110); Multi-Cut Ctrl-loop while placing points, Ctrl-drag loop slide, Edge Flow, slice range
  (step_129_multicut); Tool Settings inventory for the remaining tools of #28 (step_129_multicut); Paint Selection Add default only
  after Reset Tool (step_129_tool_settings); Maya Snap Step % 10 constant to confirm (step_129_tool_settings).

### 2.2 Release / store (user actions)

- Upload `dist/maya-workflow-kit-0.2.1.zip`, post `docs/distribution/review_reply.md`, publish the v0.2.1 draft (step_130, step_132).
- #41 store media / marketing generators still show the removed theme (step_130, step_132).
- Reviewer risk: the kit switches active-keyconfig items off in memory; no good alternative if rejected (step_130_keymap 「남은 것」).
- Placeholders: trailer / download links, Reddit sidebar, README trailer link (step_123), site store links, Pages after the repo is
  public (step_127), first-upload size limits (step_121).

### 2.3 Icons (#54)

- 489 Maya menu items with an icon in Maya and none in the kit; editor menu bars (Graph Editor, Hypershade …) not captured; Blender's
  C Outliner type icons can't change (step_131, step_131_menu, step_131_toolbox).
- Status Line group handle open / closed position (step_131_status); tool icons without dark rim / hinting (step_131_toolbox).
- Shelf icons 28 px at UI scale 1.25 (row height) — layout decision (step_113, step_131_shelf).

### 2.4 Editors

- Graph Editor kit channel list doesn't follow Blender's channel scroll, no marquee multi-select, no pose-bone / shape-key curves
  under the object row; Dope Sheet keeps Blender's list (step_104).
- Editor menu bars have no Maya hotkey text (step_108): `ui/menu_hotkeys.py` has only main-menu paths (File / Edit / … / Playback),
  0 `Graph Editor/…` keys.
- Script Editor: History menu (Echo All Commands) and Source Script unmapped (`ui/editor_menu_data.py:987`, `:1012`) (step_105).
- Render Settings: new scene still 1920 × 1080 (Maya HD 540) — no resolution in `tools/make_startup.py`; Maya's render frame range
  separate from the Time Slider (step_105).
- Hypershade: one graph tab, Bins / Tabs / Asset Nodes / Bake Sets greyed, Material Viewer = still preview image (step_131_hypershade).
- Maya workspaces (Modeling / Animation / Rigging / UV Editing / Rendering) not built: the Maya layout has only "General"
  (`tools/make_startup.py:294`); Windows > Workspaces = Blender's menu (`ui/menu_map.py:253`) (PLAN 「재점검 6차」 9,
  research/maya/ui_layout.md:139-158).
- Time Slider: selected-key / hover ticks (`ui/time_slider.py:560-569` draws all keys alike); UV Alt+arrow nudge (no binding);
  Rotate tool Ctrl plane (not found) (PLAN 「재점검 6차」 9).

### 2.5 Modeling / rigging fidelity

- Edit Edge Flow and IK Spline curve fit exact Maya rules (REA provider not installed); Flip needs GUI Maya measurement (step_110).
- Skin: Move Weights to Influences, Post Normalization, Joint Labelling (notice only) (step_110).
- Primitives: polyDisc Circle interior points approximated, platonic / disc UVs not Maya's, non-+Y NURBS start angle, hard-edge rule
  approximated, vertex edits hide the history node (Maya keeps tweaks), Pipe / Helix / Gear / Soccer Ball / Super Ellipse /
  Spherical Harmonics / Ultra Shape = notice (step_129_prims).
- lambert1 diffuse 0.8 / Ambient Color rows absent (render albedo 0.5 vs Maya 0.4) (step_100).
- Menu candidates still greyed: Select > Grow / Shrink Along Loop, Visualize > Animation Snapshot, Curves > Rebuild, EP Curve Tool
  (step_101; no `menu_map` entry).
- Component-mode Select > Similar / All by Type, Copy / Paste, Center Pivot, Shift+D not re-checked (step_129_audit_p1 Left).

### 2.6 Channel Box / Layer Editor / layout

- CB channel names centred (Maya right-aligns), UIList bottom strip can't hide, layer RMB acts on the selected layer not the row
  under the mouse, layer colour = collection colour tag (no free RGB / quick-edit) (step_129_cb).
- Layer Editor Display / Anim tab colour and list background (step_99; theme now the user's).
- Layout geometry: rects 9/12 not reachable (Blender header / status bar heights), Tool Settings dock between Outliner and view, not
  full-height left; no tear-off for Status Line / Shelf / Time Slider rows (step_99, step_106, step_116).
- `ui/outliner.py` still builds `allset_outliner_rows` for a list nobody draws (cleanup candidate) (step_116; still at
  `ui/outliner.py:9`, `:132-136`).

### 2.7 Keys

- b / m / n hold-drag = Blender radial control (press, release, move, click), not Maya's hold-while-dragging (step_107).
- Editor keys classified NO (Time Editor 36, Node Editor / Hypershade 57) to be revisited when those editors become Maya-like
  (step_107).

### 2.8 Verification debt

- `[K]` behaviours never compared with a running Maya (PLAN 「재점검 6차」 9); Maya B-drag soft-select rate unmeasured (×2 / 100 px
  kept; step_129_softsel, step_129).
- Areas audit 128 did not cover: C / V / J hold keys measured live, Graph Editor detail, UV Toolkit toggles, every shelf button run,
  File / Windows / Render menu sweep (step_128).
- 5.1.2 manual sweep stalls at check 79 (Win32 1407) — cause unknown (step_118); #52 width rule measured on 4.5 only (step_132).
- ruff: 40 findings in tests/ and tools/ (step_117); `fetch_assets.py` re-extracts Inter and can collide (step_124); pivot_snap clip
  re-record unstable (step_125).
- Manual checks: 429 open (§3), ~31 obsolete since step 130.

### 2.9 Step 130 losses with no open item (decision 14 lists them as lost; nothing tracks a remedy)

- Lead / selected colours, flat widgets, Maya menu / bar greys — theme removed; the only route left is a separate theme extension
  (decision 2 of step 130: "나중에 별도 테마 확장으로 낼 수 있음") or the listing's recommended-theme text.
- Undo depth: Blender's default 32 steps vs Maya infinite (research/maya/interaction.md:222); `docs/manual_checks.md:220` still
  expects 256.
- Region Overlap left on: 3D View toolbar / sidebar / headers can overlap the view in the Maya layout (Maya's panel bars are opaque) —
  needs a GUI look (UI lane).
- Splash on every start, Maya density / Segoe UI / aliased wire, File > New > Maya Workflow Kit entry.

## 3. Manual checks (`docs/manual_checks.md`, counted 2026-10-22)

| Range | Items | Ticked (auto, step 88 / 97) | Open | Open, obsolete since step 130 | Open, needs a human (heuristic) | Open, possibly automatable (heuristic) |
|---|---|---|---|---|---|---|
| Steps 2–49 | 175 | 0 | 175 | 12 | 30 | 133 |
| Steps 50–98 | 194 | 70 (steps 59–79) | 124 | 4 | 21 | 99 |
| Steps 99–132 (+ "Step 131 — icons") | 130 | 0 | 130 | 15 | 54 | 61 |
| **Total** | **499** | **70** | **429** | **31** | **105** | **293** |

- Audit 6: 348 / 13 ticked; step 97: 369 / 70; now 499 / 70 — 130 items added since step 97, none ticked.
- "Needs a human" = the item asks for feel, a side-by-side Maya look, a real install / store / browser / monitor / restart / tablet,
  DOUBLE_CLICK or a 5.x build (keyword match). "Possibly automatable" = none of those words; step 88 / 97 found that most of these
  still need judgement, so the realistic sweep target is the 99–132 batch (61) plus the never-swept 2–49 batch.
- Obsolete (rewrite or delete): lines 34, 65–67, 82, 140, 220, 282, 285, 290–294, 323, 340, 348, 413, 418, 654, 731–732, 736, 747,
  749, 769, 774–777, 781, 783, 802 — they test the theme, Install Maya Layout, Revert Maya Look, Restore Blender Settings, Solid Side
  Panels, the user template folder, Maya Density / Segoe UI or 256 undo steps.
- Sections with the most open human checks: Step 129 Multi-Cut (8), Step 131 Hypershade (7), Step 49 layout (7), Step 56 Time Slider
  (7), Step 107 keys (6), Step 101 menus (6).

## 4. Blindspots (not implemented and not listed as left out / not possible)

Each was re-checked by grep in `src/allset` and the docs before listing.

| # | Maya behaviour (research) | Kit today (grep proof) | Grade · score (freq × sev) |
|---|---|---|---|
| B1 | **Tool settings are global and persist across File > New / Open** (`rememberCtxSettings`, research/maya/interaction.md:31; symmetry is a global setting, :159) | Blender keeps them in `scene.tool_settings` / `transform_orientation_slots` (research/blender/concepts.md:21 "per scene"). `allset.new_maya_scene` reloads the bundled startup.blend (`src/allset/first_start.py:28-35`), so Move axis, step snap, soft-select radius / falloff, symmetry (`Scene.allset_symmetry`) reset on every New Scene and follow each opened file. Only selection masks are carried over a load (`ui/status_line.py:749`, step 93); grep `load_pre` / `load_post` shows no tool-setting carry. No doc lists it. | operation · 3 × 3 = 9 |
| B2 | **Ctrl+A = Attribute Editor / Channel Box swap in every mode** (global hotkey, research/maya/interaction.md:252, HK:230) | Bound only in "Object Mode" (`keymap/maya_patches.py:378`); in edit mode / pose mode IC's Ctrl+A select-all stays (`keymap/ic_4_5.py:3014` `mesh.select_all`, `:2184` `pose.select_all`). `docs/keymap_mapping.md` marks the row 구현 with "Mesh: mesh.select_all" in the binding column, no note. | operation · 3 × 3 = 9 |
| B3 | **The UI does not come from the scene file**: opening any scene keeps the Maya panels (research/maya/ui_layout.md:15-77, workspaces are separate files) | Blender loads the file's own screens. The Maya layout is entered only at start (`first_start.py:122-132`, armed once), by Make Maya / switch (`switch.py:256-266`) or "Maya Layout in This File" (`first_start.py:103-113`); no `load_post` re-enters it and nothing passes `load_ui=False` (grep `load_ui`: only `first_start.py:33,35`). A Maya user who opens a downloaded .blend in Maya mode gets its Blender layout (Maya menus stay; Shelf, Tool Box, CB dock, Time Slider header go). [I] confirm in GUI. | look/operation · 3 × 4 = 12 |
| B4 | **Alt+RMB drag left / right = zoom in 2D editors** (Maya dolly in UV Editor, research/maya/interaction.md:43) | The kit replaced Alt+RMB only in the 3D View (`maya_patches.py:228-231`, #51). The UV / Image editor keeps IC `image.view_zoom` (`keymap/ic_4_5.py:791`), which reads Blender's Zoom Axis preference (factory Vertical) — the preference step 4 used to set to Horizontal (`docs/steps/step_4.md:19`) and step 130 removed. [I] measure in GUI (Graph Editor `view2d.zoom` `:107`, `:144` zooms per axis and is probably fine). | operation · 2 × 2 = 4 |
| B5 | **Channel Box field colours by state**: keyed red, connected / driven yellow, expression purple, constraint blue, muted brown, locked grey (research/maya/channel_box.md:138-139) | Every animated state draws the same alert red plus a Blender decorator icon column (`ui/channel_box.py:1353`, `:1385-1388`); only constraint (pressed button, `:1376-1382`) and lock (disabled) differ. Not in any 「남은 것」. | look · 3 × 1 = 3 |
| B6 | **Undo is infinite** (research/maya/interaction.md:222, defaults.json:132) | Blender factory 32 steps since step 130; listed only as a loss in decision 14 (`docs/user_decisions.md:129`), no open item or user hint; `docs/manual_checks.md:220` still checks 256. | function · 2 × 3 = 6 |

Not blindspots (checked, already listed or done): Space tap = maximize (`marking/modal.py:234-238`), CB slider speeds / hyperbolic
(`ui/channel_box.py:64`, `:698-724`), Channel Names Long / Short (greyed, `channel_box.py:1249`), New Scene asks to save
(`first_start.py:91-93`), backtick tweak, Ctrl+Space, Home, Alt+5, Alt+A, PgUp / PgDn, Ctrl+Y, Ctrl+Alt+H (all 구현 in
`docs/keymap_mapping.md`), orbit around COI (Blender default = Maya factory).

## 5. Proposed priority (daily frequency × severity, then cost)

1. **Store 0.2.1 + #41 media** (user upload, retake media without the theme) — release-blocking for the listing.
2. **#16 Ctrl+B instant bevel** — daily modeling key behaves differently (milestone 0.3.0).
3. **Maya layout survives File > Open** (B3) — every opened .blend loses the Maya panels; decide: re-enter the layout on load_post in
   Maya mode (append when the file has no Maya workspace) vs keep the file's UI.
4. **Global tool settings** (B1) — carry Move / Rotate / Scale axis, step snap, soft-select, symmetry over New / Open like the masks
   (step 93 pattern).
5. **#30–#33 Maya tools and option windows** (Quad Draw, Insert Edge Loop, modeling option boxes, rigging tools) — the largest
   remaining parity block.
6. **Ctrl+A in component / pose mode** (B2) + Image Editor Alt+RMB zoom axis (B4) — small keymap batch.
7. **Theme gap** — a separate Maya theme extension (allowed by the store as a theme package) or a one-click "open Themes with the
   recommended values" text; track the lost lead-green / white selection as an issue.
8. **#34 / #35 Deform and Key / constraint options**.
9. **Editor polish**: Graph Editor list scroll / marquee / bone curves, editor menu-bar hotkeys, Render Settings HD 540 default,
   Script Editor History / Source Script, Maya workspaces (Animation / Rigging / UV Editing).
10. **#54 icons** (489 menu items, editor menu bars).
11. **Manual-check cleanup**: delete / rewrite the 31 obsolete items, sweep the 61 step 99–132 items with `gui_manual_sweep.py`,
    tick or re-file the rest.
12. Later: CB name alignment / state colours (B5), layer RGB colour, undo-depth hint (B6), primitives fidelity, Edge Flow / IK Spline
    rules (needs REA provider), ruff cleanup, `ui/outliner.py` unused rows.

Kept as not possible / out of scope: Y-up, separate pivots, MMB on fields, MEL, history beyond the kit records, playback Once /
Oscillate, 2D pan / zoom in user views, Blender C panels / Outliner icons, a full Maya theme inside this extension (store policy).
