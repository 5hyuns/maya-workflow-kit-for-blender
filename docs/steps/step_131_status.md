# Step 131 — lane STATUS: Status Line, menu bar and panel toolbar icons (#23)

User report #23: the kit icons look too unlike Maya's, so menus and buttons are hard to tell apart. This lane redraws
the Status Line glyphs (`src/allset/ui/status_icons.py` `GLYPHS`) and the viewport panel toolbar glyphs
(`src/allset/ui/panel_toolbar.py` `g_*`, registered as `status_icons.EXTRA["pt_<name>"]`). Shelf, Tool Box, Layer
Editor, Outliner and Hypershade icons are other lanes.

References (looked at only, never copied or traced — decision 6): `research/maya/re/icons131.md` (vocabulary and
per-icon descriptions), the Maya 2022 install icons at 1x/2x via `tmp/maya_icons131/` (tmp only, untracked).

## What was done

- **Canvas with pixel hinting.** `Canvas(size)` keeps the glyph code in unit coordinates but snaps rectangle / frame /
  polygon edges to the pixel grid of `size`, rounds stroke widths to whole pixels (minimum 1), puts odd-width strokes
  and odd-diameter discs on pixel centres and even ones on pixel boundaries; axis-aligned lines become pixel-exact
  bars with square caps. Supersampling is at least 128 samples across (`ss = max(4, ceil(128 / size))`).
- **`image(name, size=32)`** → `(size, size, 4)` float32, top row first, straight alpha, for any size (16, 20, 24,
  32, 48 tested), with Maya's dark outline (`outlined`: alpha grown one pixel, `OUTLINE` at 0.9) added at the final
  size; the Status Line chrome (`CHROME` = bar, open, closed) is drawn without it.
- **Maya colours.** `GREY` = #bcbcbc, `TEAL` = #48a9b4 (+ `TEAL_DARK` / `TEAL_LIGHT` shading tones, `LIGHT` for the
  pointer and highlights); the names other modules import (`GREY`, `DIM`, `DARK`, `TEAL`, `BLUE`, `ORANGE`, `Canvas`,
  `render`, `gear`, `arrow_cursor`, `GLYPHS`, `EXTRA`) still exist.
- **Glyphs redrawn after Maya's silhouette / main colour / composition** (descriptions in the code docstrings):
  selection masks teal (handle plus, joint chain, S curve with CV squares, NURBS quilt, lattice, particles, teal
  clapper with ball, question mark); component modes = point square, diagonal edge, L of faces; snap toggles = one
  grey horseshoe magnet with teal pole tips, differing only by the teal target at the lower right (grid hash, curve,
  dot, centre target, plane, Make Live ground line); render buttons = one striped clapperboard with eye / IPR / gear /
  layer stack; history = clock + list; editor toggles = cube + hammer, T-pose figure, slider rows, list + hammer,
  layer stack. Panel toolbar: camera, camera + teal padlock, camera + teal gear, ribbon, teal plane on a floor,
  four-way arrow + teal magnifier, pencil, grid plate, film strip gate, gates with teal dot / dark disc / teal dotted
  cross / teal picture / teal T, wire cube, teal shaded cube, shaded cube + wire, half-checker ball, checker ball,
  bulb with rays, teal ball + hatched shadow, ball in teal occlusion pool, ghost-trail balls, half-smooth / half-stepped
  ring, checker + solid teal squares, teal dashed box + pointer, three X-ray tiles (see-through overlap, outline back +
  points, joint), iris, half disc + bracket, OFF disc.
- **New glyph `color_mgmt_on`**: Maya swaps the colour management icon with its state; the toolbar now draws a teal ON
  disc while colour management is on and Maya's grey OFF disc while it is off (`delegated`).
- **Icon size follows the UI scale.** `icon(name)` returns the preview `"<name>@<px>"` with
  `px = round(16 × preferences.system.ui_scale)` (16 / 20 / 24 at 1.0 / 1.25 / 1.5). `make_all()` (the register
  timer) builds every glyph at that size and remembers it in `_size`. When a draw finds no preview of the current
  size but one of the previous size, it returns the old one as a stand-in and schedules `make_all` from a 0 s timer,
  which makes the new size and tags every area plus the top bars for redraw — so previews are not created inside a
  header draw except for the very first draw before the register timer ran (as before). New previews get new names
  instead of rewriting pixels of existing previews (no reliance on Blender invalidating a cached icon texture).
  Everything lives in one `bpy.utils.previews` collection, removed on unregister.

## Decisions (delegated)

- **1x, not 2x, previews** (`delegated`, measured): GUI shots at UI scale 1.25 with previews of the drawn size (20 px)
  vs twice it (40 px, Blender resamples): edge energy (mean absolute neighbour difference over the panel toolbar /
  Status Line strip) 18.97 / 22.15 for 1x vs 16.47 / 20.11 for 2x — the 1x hinted pixels are 10–15 % crisper, so the
  preview is made at exactly the drawn size.
- **Dark outline** on every button glyph (`delegated`): Maya's #3a3a3a outline (icons131.md:20, 27) is close to
  Blender's header colour, so the kit uses #212121 at 0.9 alpha, which separates the glyph from both Maya's #444 and
  Blender's darker header.
- **Cursor colour**: the select-mode pointers are light grey (`LIGHT`) with the outline, as in Maya's pickObjByType;
  teal goes to the hierarchy elbow / object square / first component square (`delegated`).
- **Make Live**: Maya draws the magnet alone; the kit adds a short grey ground line so it differs from the other
  snap toggles by more than a few pixels (`delegated`).
- **X-ray tiles**: Maya's three X-ray icons sit on a dark tile; the kit keeps the tile and makes the three contents
  clearly different (overlap / outline + teal points / joint) (`delegated`).
- **Chrome** (`bar`, `open`, `closed`) left as it was (score 1 against Maya's openBar / closeBar): changing it is a
  Status Line layout change (Maya's handle sits at the group start), not an icon change — left for the layout lane.

## Scores (0–3, recognisable as the Maya icon; before = `tmp/maya_icons131/index.json`, after = own sheets)

Status Line:

| glyph | before | after | glyph | before | after |
|---|---|---|---|---|---|
| new | 2 | 3 | snap_GRID | 2 | 3 |
| open_scene | 2 | 3 | snap_CURVE | 2 | 2 |
| save | 2 | 3 | snap_POINT | 2 | 3 |
| undo | 2 | 2 | snap_PROJECTED | 2 | 2 |
| redo | 2 | 2 | snap_PLANE | 2 | 2 |
| sel_hierarchy | 2 | 2 | snap_LIVE | 2 | 2 |
| sel_object | 2 | 3 | history | 1 | 3 |
| sel_component | 2 | 3 | render_view | 2 | 3 |
| mask_HANDLES | 2 | 3 | render | 3 | 3 |
| mask_JOINTS | 1 | 2 | ipr | 3 | 2 |
| mask_CURVES | 1 | 2 | render_settings | 3 | 3 |
| mask_SURFACES | 0 | 2 | hypershade | 2 | 2 |
| mask_DEFORMERS | 1 | 2 | render_setup | 1 | 2 |
| mask_DYNAMICS | 2 | 3 | light_editor | 2 | 2 |
| mask_RENDERING | 0 | 2 | pause | 3 | 3 |
| mask_MISC | 2 | 3 | ed_MODELING_TOOLKIT | 2 | 2 |
| vertex | 1 | 3 | ed_CHARACTER | 2 | 2 |
| edge | 1 | 3 | ed_ATTRIBUTE | 2 | 2 |
| face | 1 | 2 | ed_TOOL_SETTINGS | 2 | 3 |
| open / closed (chrome) | 1 | 1 | ed_CHANNEL_BOX | 2 | 2 |

Panel toolbar:

| glyph | before | after | glyph | before | after |
|---|---|---|---|---|---|
| cam_select | 2 | 3 | default_mat | 1 | 2 |
| cam_lock | 3 | 3 | wire_on_shaded | 1 | 3 |
| cam_attr | 1 | 3 | textured | 2 | 3 |
| bookmark | 3 | 3 | all_lights | 2 | 3 |
| image_plane | 1 | 2 | shadows | 2 | 2 |
| pan_zoom | 0 | 3 | ssao | 0 | 2 |
| grease | 2 | 2 | motion_blur | 2 | 3 |
| grid | 2 | 3 | aa | 0 | 2 |
| film_gate | 1 | 2 | dof | 1 | 3 |
| res_gate | 3 | 3 | isolate | 1 | 2 |
| gate_mask | 2 | 3 | xray | 0 | 2 |
| field_chart | 1 | 3 | xray_comp | 0 | 2 |
| safe_action | 1 | 3 | xray_joints | 1 | 2 |
| safe_title | 1 | 3 | exposure | 1 | 3 |
| wire | 1 | 3 | gamma | 1 | 2 |
| smooth | 1 | 3 | color_mgmt | 0 | 2 |

Still below 2: only the chrome `open` / `closed` (see Decisions). `ipr` dropped 3 → 2 because the block letters are
cramped at 16 px (still readable at 20 / 24).

## Verification

- `ALLSET_SANDBOX=status131 python tests/run.py -k step131_icons,step113,enable_disable,step51`: test_step131_icons
  `test_status_line_unique`, `test_panel_toolbar_unique`, `test_status_icon_sizes` PASS (the two shelf tests fail —
  shelf lane); test_step51_shelf_menus 7/7 PASS; test_enable_disable 4/4 PASS.
- `python tests/gui/run.py -k step113,step75` (UI scale 1.25): 16/16 PASS; `-k step113 --ui-scale 0.8` (effective
  1.0): 10/10 PASS. A temporary GUI script (not committed) checked that the previews are made at 20 px at 1.25 and,
  after the view scale changed to 1.5 effective, at 24 px with `_size == [24]` (2/2 PASS).
- Sheets (tmp only): `tmp/status131/sheet_status.png`, `sheet_panel.png` (Maya 64 | kit 64 | Maya native ×3 | kit
  20 or 16 ×3 | kit 16 ×3); GUI crops `tmp/status131/c125_status.png`, `c125_panel.png`, `c100_top.png`,
  `c100_panel.png`, `c150_top.png`; full shots `tmp/status131/gui125/`, `gui100/`, `gui_scale/`, 2x experiment
  `gui125_2x/`.

## Left

- Status Line chrome (group handle / collapse arrows) after Maya's openBar / closeBar — layout lane.
- `docs/manual_checks.md`: glance at the Status Line and panel toolbar at the user's own UI scale after changing it
  in Preferences (icons switch size one tick later).
