# Step 131 — lane TOOLBOX: Maya-recognisable kit icons for the Tool Box, Layer Editor and kit Outliner rows (#23)

User request (issue #23): the kit's icons look too unlike Maya's, so menus and buttons are hard to tell apart.
Re-draw them as kit-made glyphs (no Maya icon files copied or traced; the installed Maya 2022 icons are only
looked at) that follow each Maya icon's silhouette, main colour, composition and size; list every icon with its
Maya command; score recognisability on side-by-side sheets (tmp only) and redraw the weakest first, pixel-hinted
at 32 / 24 / 16 px with sizes for 125 % / 150 % displays; neighbours must stay distinct.

This lane: the Tool Box column (tools + quick layouts), the Layer Editor toolbar, the Outliner rows the kit draws,
kit menus. Reference descriptions: `research/maya/re/icons131.md` (items 8, 10; Tool Box / Layer Editor / Outliner
sections).

## 계획

- One module `src/allset/ui/kit_icons.py`: glyph functions written once against a small drawing API, rendered two
  ways:
  - `Pen` (raster, numpy via `status_icons.Canvas`): rectangles, frames and axis-aligned strokes snapped to whole
    pixels of the target size, a one-pixel dark rim like Maya's icons (#3a3a3a). Shown through
    `bpy.utils.previews` (`icon_value`) or as a GPU texture, always at the exact pixel size it is displayed at
    (16 / 20 / 24 px = UI scale 1.0 / 1.25 / 1.5), so nothing is resampled.
  - `Geo` (vector): the same calls recorded as coloured triangles for `bpy.app.icons.new_triangles` — Blender's
    own toolbar icons are triangle icons (`datafiles/icons/*.dat`) and only those are drawn at the toolbar's big
    tool size; a preview icon in a toolbar button is drawn at the normal 16 px x UI scale (measured, see below).
- Palette from the Maya icons (measured on the installed PNGs, not copied): light grey #bdbdbd line art, teal
  #48aab5 accents, rim #3a3a3a.
- Tool Box tools: `toolbox._tools_from_context` already hands Blender's toolbar the Maya tool list while the
  toolbar draws; in the Tool Box column (`is_toolbox`) each Maya tool's ToolDef is now a `_replace(icon=...)` copy
  whose icon name `allset.tool:<idname>` is put into `bl_ui.space_toolsystem_common._icon_cache` (Blender reads
  that dict before looking for a .dat file). Only the drawn copy changes — tool switching, `operator_menu_hold`,
  the step 129 double click (`activate_by_id` wrapper) and tooltips look tools up by idname and are untouched.
  Unregister pops the kit keys from the cache and releases the vector icons.
- Quick layouts, Layer Editor toolbar: `kit_icons.button(layout, op, glyph, fallback)` — the kit glyph's
  `icon_value`, Blender's old icon until the preview exists (previews are made from a 0 s timer, not while a
  region draws, like `status_icons`).
- Outliner rows the kit draws (`outliner_sets`: default cameras, default sets, kit sets): `kit_icons.draw_texture`
  replaces the old GPU line drawings (two blue rings / a box + triangle).

## Decisions (delegated)

1. **Tool Box only in the column** (as asked): the main view's fallback toolbar (shown while the column is too
   narrow, `toolbox._fallback`) and every other 3D View toolbar keep Blender's icons, even when they list the Maya
   tools.
2. **Tool icons are vector icons, not bitmaps.** Measured in the GUI: a preview (`icon_value` of a
   `bpy.utils.previews` image) in a toolbar tool button is drawn at 16 px x UI scale — half the size of Blender's
   own tool icons and of Maya's 32 px Tool Box icons, and blurred from the 32 px bitmap. Blender's vector icons are
   rasterised by Blender at the tool size, so the tool glyphs are handed over as triangles. Consequence: no
   kit pixel hinting for the 6 tool icons (Blender rasterises them at 32 px x scale with its own anti-aliasing),
   and no dark rim (a vector rim would need polygon offsets; Blender's own tool icons have none either; on the
   pressed blue tool button the light grey glyph still reads).
3. **"2x for 125 % / 150 %" = exact size.** Instead of one 2x bitmap scaled down by Blender, every raster glyph is
   made at the pixel size of the running UI scale (`size_for`: 16 x scale; 32 x scale for the tool sheets) with
   edges snapped to that size's pixels — a separate hinted bitmap per scale, created on demand.
4. **Outliner object-type rows stay Blender's.** The Maya Workflow Kit Outliner is Blender's C tree; Python cannot
   change its icons, and the kit cannot overlay them reliably: the tree's expanded state (TreeStore) is not exposed
   to Python, so a draw handler cannot know which object a row shows (search filter, sort, type filters, children
   of filtered parents). A wrong icon is worse than Blender's. This leaves the 13 rows the reference scores 0
   (group / locator / IK handle / cluster = Blender's one empty icon, six light types = one light icon, mesh,
   image plane, text, field) as they are. `outliner.ALLSET_UL_outliner.icon_for` (the step 11 UIList outliner) is
   not drawn anywhere since step 116, so it is not changed either. Follow-up idea (not done): reconstruct rows from
   the pixel indent of each row's icon + the DFS order of the hierarchy, abort on any mismatch.
5. **Kit menus keep no icons.** Kit Maya menus draw no icon on any item (`menu_sets` draws every item through
   `allset.menu_item`); Maya shows one on ~1770 items (`tmp/maya_icons131/menu_icons.json`). Adding them needs
   `menu_sets.py` (not this lane's file) and a glyph per command — the shelf lane draws those glyphs
   (`shelf_icons`), so menu icons should reuse them once both lanes are merged (one glyph per Maya command). Left
   for a follow-up; no menu item lost its icon.
6. **Last-tool slot keeps Blender's icon.** Maya shows the last used tool's own icon there; the kit's last tool is a
   Blender tool (Multi-Cut, Quad Draw, ...) whose icon is Blender's everywhere else too.
7. **Greyed camera rows**: Maya greys hidden startup cameras' names; the kit draws their camera glyph greyed too
   (luminance x 0.85, alpha 0.6), as the old line drawing was.
8. Outliner textures are drawn with the plain builtin `IMAGE` shader and display (sRGB) values: measured in 4.5,
   the Outliner region shows the shader's values as they are (scene-linear values, as the shelf's image editor
   needs, came out far too dark).

9. **Tool icon colours are pre-compensated for Blender's Icon Saturation.** Blender desaturates toolbar vector
   icons by the theme's Icon Saturation (measured: teal #48aab5 shown as #6a9ba1 at the default 0.5, = s·c +
   (1 − s)·luma with luma 0.3/0.59/0.11). The kit only reads the theme value (no preference write) and makes the
   vector icon with `compensate(colour, s)` so the toolbar shows Maya's teal; one icon per saturation value.
10. **Shared Canvas.** `Pen` asks `status_icons.Canvas` for `hint=False` when that parameter exists (the STATUS lane
    added canvas-side hinting and per-size supersampling `ss`): the Pen does its own snapping, so the glyphs are the
    same on both versions of `status_icons` (checked by rendering the sheets against master's `status_icons.py`).

## Inventory (area, kit item, Maya command / icon, recognisability score 0-3 before / after)

Before = `tmp/maya_icons131/index.json` scores (ref lane); after = this lane's judgement on the sheets
(`tmp/toolbox131_sheets/v7_*.png`, kit 16 / 20 / 24 px + zoom vs Maya PNG) and GUI shots.

| Area | Kit item | Maya command (icon) | Before | After |
|---|---|---|---|---|
| Tool Box | `builtin.select_box` | Select Tool (aselect) | 1 | 3 |
| Tool Box | `builtin.select_lasso` | Lasso Tool (lassoSelect) | 2 | 3 |
| Tool Box | `builtin.select_circle` | Paint Selection Tool (artSelect) | 1 | 3 |
| Tool Box | `builtin.move` | Move Tool (move_M) | 2 | 3 |
| Tool Box | `builtin.rotate` | Rotate Tool (rotate_M) | 2 | 3 |
| Tool Box | `builtin.scale` | Scale Tool (scale_M) | 1 | 3 |
| Tool Box | last tool slot | last used tool (that tool's icon) | – | – (Blender's, decision 6) |
| Tool Box | quick layout SINGLE | Single Perspective View (singlePerspLayout) | 0 | 3 |
| Tool Box | quick layout FOUR | Four View (fourViewLayout) | 0 | 3 |
| Tool Box | quick layout FRONT_PERSP (greyed) | Front/Persp (twoViewVerticalLayout) | 1 | 3 |
| Tool Box | Outliner button | Show/hide Outliner (outliner) | 1 | 3 |
| Layer Editor | move up | Move selection up in list (moveLayerUp) | 1 | 3 |
| Layer Editor | move down | Move selection down in list (moveLayerDown) | 1 | 3 |
| Layer Editor | create empty layer | Create Empty Layer (newLayerEmpty) | 1 | 3 |
| Layer Editor | create layer from selected | Create Layer and assign selected (newLayerSelected) | 0 | 3 |
| Outliner (kit rows) | kit set rows | objectSet (out_objectSet) | 0 | 3 |
| Outliner (kit rows) | defaultLightSet / defaultObjectSet | default sets (out_objectSet) | 0 | 3 |
| Outliner (kit rows) | persp / top / front / side | startup cameras (out_camera) | 2 | 3 |
| Outliner (C rows) | mesh, curve, surface, group, locator, IK, cluster, joint, lattice, camera, 6 lights, image plane, text, field | out_* | 0-2 | unchanged (decision 4) |
| Menus | Maya menu items | ~1770 items with icons | none drawn | unchanged (decision 5) |

## Verification

- `tests/test_step131_toolbox_icons.py` (headless): inventory = the Maya tool list / layout / layer / outliner items,
  sizes per UI scale (16/20/24, tools 32/40/48), coverage, pixel hinting (opaque frame edge, no half-tone edge next
  to the move square), every pair in an area differs in >= 5 % of the pixels, Maya palette present, previews made
  at the right size, the toolbar cache key resolves through `ToolSelectPanelHelper._icon_value_from_icon_handle`,
  disable removes the cache keys / previews / vector icons.
- `tests/gui/gui_step131_toolbox_icons.py`: Maya layout; Blender's toolbar cache holds the kit names; the Move tool
  shows teal arrows spanning more than 20 px x scale (tool size); quick layout icons in Maya grey; Outliner set row
  shows the teal flag in the right colour; Layer Editor toolbar teal; a Tool Box click still sets Rotate.
  Screens: `tmp/toolbox131_sheets/gui/step131_{window,toolbox,outliner,stack}_{1.00,1.25}.png`.
- Commands / results: see the end of this file.

## Results

- `ALLSET_SANDBOX=toolbox131 python tests/run.py -k step131_toolbox,enable_disable,toolbox,outliner,layer` —
  34 passed, 0 failed (4 files).
- `ALLSET_SANDBOX=toolbox131 python tests/gui/run.py -k toolbox,outliner,layer` (effective UI scale 1.25) —
  32 passed, 0 failed (gui_step11_outliner_ae, gui_step82_outliner_drag, gui_step131_toolbox_icons).
- `... tests/gui/run.py -k step131_toolbox --ui-scale 0.8` (effective 1.0) — 7 passed, 0 failed.
- Looked at: sheets `tmp/toolbox131_sheets/v8_*.png` (+ `v7_geom.png` for the vector tools, `vm_*.png` rendered
  with master's `status_icons`), GUI crops `tmp/toolbox131_sheets/gui/step131_{toolbox,outliner,stack,window}_{1.00,1.25}.png`.
  The sandbox folder is `tmp/toolbox131` (wiped by each run), so sheets live in `tmp/toolbox131_sheets`.

## Left

- Outliner C-tree object-type icons (decision 4) and kit menu icons (decision 5): follow-ups.
- Tool icons have no dark rim and no kit pixel hinting (decision 2).
