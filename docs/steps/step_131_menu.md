# Step 131 — lane MENU: kit-drawn icons on Maya menu items (#23)

User request (issue #23, "menu items with icons"): Maya-recognisable kit-drawn icons; Maya main-menu items that
show an icon in Maya 2022 should show the kit-drawn icon of the same command in the kit's Maya menus. Only kit
drawings are reused (`shelf_icons` / `status_icons` / `kit_icons`); items without a kit drawing get no icon.

## 계획

- Facts: Maya 2022 shows an icon on 1772 main-menu entries (look-only capture `tmp/maya_icons131/menu_icons.json`,
  menu path -> icon file; 1263 distinct paths, of them 895 labelled items — the rest are the hidden option-box
  actions Qt lists after an item). 679 of the labelled items exist in the kit's menus (the others are plug-in menus
  — MASH, Muscle, XGen, Bifrost — or Maya run-time items the kit doesn't build).
- Link a menu item to a kit drawing in a generator (`tools/gen_menu_icons.py` -> `src/allset/ui/menu_icon_data.py`,
  `ICONS = {menu path: picture}`):
  1. same picture: the item's Maya icon file is a factory shelf button's (`research/maya/shelves.json` image1) ->
     that button's kit drawing (`("shelf", shelf, label, index)`);
  2. same command: the item's runTimeCommand (`research/maya/menus.json`) is a shelf button's, or `shelf_map.MENU`
     names the item as the button's menu item;
  3. a short hand table (`GLYPHS`) for items whose Maya icon is the picture of a Status Line button (Windows >
     editors, Select > Components > Vertex / Edge / Face) or a Tool Box tool (Modify > Transformation Tools > Move /
     Rotate / Scale) the kit already draws.
  Only Maya icon *file names* are compared; none is written to `src/` (decision 6).
- `src/allset/ui/menu_icons.py`: `picture(pic, n)` renders any of the three kinds at `n` px (the drawings hint
  their edges to that grid); previews (`bpy.utils.previews`) at 16 px x UI scale are made by a persistent timer,
  20 ms of drawing per tick, never while a menu draws. Until a size is complete `icon_value` returns 0 for every
  item (after a UI scale change the previous size stands in), so a menu never mixes rows with and without icons.
  Registered / unregistered by `menu_sets` (no edit of `ui/__init__.py`).
- `menu_sets._draw_items` passes `menu_icons.icon_value(path)` to `draw_item` / `_draw_boxed` / submenu
  `layout.menu` (`icon_value`); `draw_spec` takes `icon_value` beside its `icon`. Marking menus / hotbox lists are
  GPU-drawn (`marking/draw.py`) and are left unchanged; editor menu bars (Graph Editor, Hypershade ...) have no
  Maya menu-icon data and stay without icons.

## Measurement: text alignment with icons (GUI, `tests/gui/gui_step131_menu_icons.py`)

- Blender's popup menus reserve the icon column on every row, also in a menu where no item has an icon: in the
  control shot (Create > Measure Tools, no kit icon) item text starts 24 px right of the menu title; in Edit Mesh
  (icons on Bevel, Bridge, Circularize ...) it starts 24 px right of the title as well, on icon and icon-less rows
  alike (crops `tmp/menu131_shots/cmp_align.png`, UI scale 1.0). So the icon fills the already reserved column:
  labels don't move, the step 108 right-aligned Maya hotkeys (measured with blf on the label text only) and the
  step 103 ❒ marks stay on one column (Edit Mesh: Ctrl+B / Ctrl+E / Ctrl+Del end on one x, every ❒ on one x;
  Mesh Tools at 1.25: Ctrl+Shift+X / Ctrl+Shift+Q beside the icons of Multi-Cut / Quad Draw). No blank icons needed.
- Greyed (unmapped) items with an icon (Create > Polygon Primitives > Super Ellipse ...) get Blender's disabled
  dimming of the icon, matching Maya's greyed icon.
- The 16 / 20 / 24 px renders of all 183 distinct pictures were checked on a contact sheet over the menu colour:
  they read at 16 px (letters-on-disc icons such as the nCloth / nHair caches are the roughest but still
  distinct); no small variant was needed, `shelf_icons.py` is unchanged.

## Decisions (delegated)

1. **Link by picture first.** Maya uses the shelf picture of the same command in its menus; the picture file is the
   most reliable link (176 items). Commands from `menus.json` add nothing beyond it (most menu items are built at
   run time without a recorded command); `shelf_map.MENU` adds one (Windows > Content Browser).
2. **Status Line / Tool Box pictures** are reused for 13 items whose Maya menu icon is that same picture (Windows >
   Attribute Editor / Channel Box / Tool Settings / Modeling Toolkit / Hypershade / Render View / Light Editor,
   Select > Components > Vertex / Edge / Face, Move / Rotate / Scale Tool). Render Setup is not a kit menu item.
3. **No icon** for Maya icon items without a kit drawing (489 of 679: Deform deformers, Mesh Display, Effects,
   Fields, most of Mesh Tools / Edit Mesh ...). Drawing new pictures for them is outside this lane (the user asked
   to reuse kit drawings).
4. **Same picture twice in one menu** only where Maya does it too (nCache > Merge Caches > Maya Fluid / nObject,
   nHair > Convert Selection > To Hair Constraints / To Hair Systems); `test_step131_menu_icons` allows exactly
   those.
5. **Previews from a persistent timer**: a non-persistent timer was dropped by the file load that opens the Maya
   layout right after Maya mode turns on (measured: the first menu then had no icons until a redraw).
6. Menu icon size = `max(16, round(16 x ui_scale))` like `status_icons.icon_px`; previews of other sizes stay in the
   collection until unregister (a few hundred small images).

## Done

- `tools/gen_menu_icons.py`, `src/allset/ui/menu_icon_data.py` (190 items), `src/allset/ui/menu_icons.py`,
  `src/allset/ui/menu_sets.py` (icon_value through draw_item / draw_spec / _draw_boxed / submenus; register).
- Tests: `tests/test_step131_menu_icons.py` (paths are kit menu items, every picture is a kit drawing, 16/20/24 px
  sizes, distinct per menu, preview = picture at the icon size, menus hand Blender the icon with hotkeys and boxes
  kept, unregister frees previews and timer); `tests/gui/gui_step131_menu_icons.py` (icons made before the first
  menu opens; shots of Create > Polygon / NURBS Primitives, Mesh, Edit Mesh, Mesh Tools, Deform, Constrain, Key,
  Windows > General Editors and the control menu).

## Verification

- `ALLSET_SANDBOX=menu131 python tests/run.py -k step131,step108,step101,step103,step54,enable_disable,step130,step114`:
  77 passed, 1 failed — `test_step108_menu_hotkeys::test_generated_table_is_current` reads
  `research/maya/menus.json`, which is not in a git worktree (research/ is untracked); unrelated to this lane.
- `ALLSET_SANDBOX=menu131 python tests/gui/run.py -k step108,step101,step103,step51,step116,step131_menu`: 49 passed,
  0 failed. `gui_step131_menu_icons` also passes at `--ui-scale 0.8` (13/13). Every GUI log ends with a quit-time
  `EXCEPTION_ACCESS_VIOLATION` in tbbmalloc ("C-style MEM_freeN on a pointer created with MEM_new"), also in lane
  TOOLBOX's `gui_step131_toolbox_icons` log without this lane's code: results are written before it.

Screenshots: `tmp/menu131_shots/s100/` (UI scale 1.0) and
`tmp/menu131_shots/s125/` (1.25).

## Left

- Maya icon items without a kit drawing (489) — new drawings would be a follow-up (biggest groups: Deform, Mesh
  Display, Effects / Fields, Edit Mesh / Mesh Tools tools that have no shelf button).
- Editor menu bars (Graph Editor, Dope Sheet, UV Editor, Hypershade ...): no Maya menu-icon capture for them yet.
- Marking menus / hotbox lists: no icons (GPU-drawn engine; Maya's marking menus show icons only on some items).
