# Step 131 — lane SHELF: the 203 factory shelf icons (issue #23)

Main step doc: `docs/steps/step_131.md`. Maya references (descriptions only, no pixels):
`research/maya/re/icons131.md` "Maya's shared visual vocabulary" and "Shelf"; the exported Maya icons in
`tmp/maya_icons131/` were only looked at (decision 6: nothing copied, traced or tracked).

## 계획

1. Replace the keyword → glyph table + two-letter badge + letter-tile fallback of `ui/shelf_icons.py` with one
   drawing per factory button (`ICONS["<shelf>/<label>"]`), following each Maya icon's subject, main colour,
   composition and size (icons131.md per-icon lines).
2. Shared Maya vocabulary as parts: dark #3a3a3a outline round every shape (alpha post pass at the target
   size + `ol=True` for parts drawn over the subject), per-kind hues (NURBS blue, poly orange, UV green, editor
   teal, rig lavender, key orange-red, render yellow, FX salmon), grey #bcbcbc tool parts, the action mark
   small in a corner (plus, X, check, no-sign, eye, chain link, key bar, target, checker badge).
3. Hinting: draw in icon units (0..32, y down); edges, line widths and axis-aligned line centres snap to the
   1x pixel grid, so a 1-unit line is one crisp pixel at 32 and two at 64, and the 64 px picture scaled down
   equals the 32 px one. 4x / 3x supersampling for curves.
4. `ui/shelf.py` picks the 64 px texture when the drawn icon is wider than 32 px.
5. Compare sheets kit-new vs Maya per shelf in `tmp/shelf131/`, score 0-3, redraw weakest first; a uniqueness
   check (the main lane's `test_step131_icons.py` rule: ≥ 4 % of pixels differ by > 0.25) on every shelf.

## Decisions (delegated)

- **delegated**: one hue per *kind*, not per shelf (Maya does the same: UV tools are green on Poly Modeling,
  constraints keep their lavender link on Animation, Content Browser is teal). `SHELF_COLOURS` keeps the shelf →
  hue table with the measured values (#57a4cb, #da9355, #ad9cd8, #df6e41, #bfb23a, #d6806d); `LIGHT` = #bcbcbc.
- **delegated**: a factory label draws the same picture on any shelf (Set Key on Rigging and Animation, the six
  constraints), like a Maya icon belongs to its command. A user shelf button whose label is a factory label gets
  that picture; any other user label gets Maya's generic script button with the label's initials (the only
  place letters remain, as Maya writes a custom button's icon label on it).
- **delegated**: Maya buttons that share a label (FX "From Current" start / rest, FX Caching "Delete Cache"
  fluid / nCloth) are told apart by `index` (button position): `draw(..., index=)` / `texture(..., index=)`,
  keys `"<shelf>/<label>#<index>"`; without an index the first one is drawn.
- **delegated**: letters are used only where Maya's icon is text (hair states C / S / R, "svg", "T", "0,0,0",
  the cluster "C", "1" of Set Initial State), drawn with the 5x7 pixel font at two units per cell (bold) so
  they stay crisp.
- **delegated**: material balls differ by tone *and* highlight (Standard Surface black with hard highlight and
  bright rim, Blinn broad soft highlight, Lambert light matte, Phong small sharp dot, Phong E dark with a soft
  elongated highlight) — Maya's own Phong / Phong E / Blinn icons are nearly the same picture, which the
  uniqueness rule does not allow.
- **delegated**: the 2x texture is chosen from the drawn size (`texture_size(size)`: 64 above 32 px). In the
  template the shelf row height limits the icon to 28 px at UI scale 1.25 (gui_step51 "icons 28"), so the 2x
  picture shows only when the row is taller (larger UI scales); the row layout is not this lane's scope.

## Done

- `src/allset/ui/shelf_icons.py` rewritten: `Canvas(size)` with hinting (`snap`, `lw`, `centre`, grid = 1x
  pixel), masks (rect, circle, ellipse, rings, arcs, polygons, lines, capsule rings), parts (cube, cylinder,
  cone, torus, sphere shading, film strip / frame, clapper, stacks, shirt, hair, brush, pencil, blade, window,
  human, link, key bar, checker, target, snowflake, arrows), 203 button drawings in `ICONS`, `icon_for`,
  `draw(label, shelf=None, greyed=False, size=32, index=None)` → (size, size, 4) float32 top-down straight
  alpha, `texture(label, shelf, greyed, size, index)`, `texture_size`, `clear`. Pure numpy, no files, no bpy at
  import. Greyed buttons: grey, alpha × `GREYED_ALPHA`.
- `src/allset/ui/shelf.py` `draw_row`: 64 px texture when the icon is drawn wider than 32 px; passes the
  button index for factory shelves.
- Tests updated to the new design: `tests/test_step109_shelves.py` (measured hues, every Sculpting brush its own
  picture, dark outline, UV green), `tests/test_step51_shelf_menus.py` (no letter tiles for factory buttons,
  user-label fallback, a command's picture is the same on every shelf, same-label buttons differ by index).

## Scores (0 unrelated, 1 same idea, 2 recognisable, 3 close; counts 0/1/2/3, mean)

| shelf | before (icons131.md) | after (this lane, sheets `tmp/shelf131/sheet_<Shelf>.png`) |
|---|---|---|
| Curves / Surfaces (38) | 9/20/4/5, 1.13 | 0/0/21/17, 2.45 |
| Poly Modeling (43) | 11/17/14/1, 1.12 | 0/0/23/20, 2.47 |
| Sculpting (26) | 6/20/0/0, 0.77 | 0/0/11/15, 2.58 |
| Rigging (18) | 5/11/1/1, 0.89 | 0/0/5/13, 2.72 |
| Animation (14) | 3/10/1/0, 0.86 | 0/0/2/12, 2.86 |
| Rendering (25) | 5/16/2/2, 1.04 | 0/0/10/15, 2.60 |
| FX (29) | 17/9/3/0, 0.52 | 0/0/16/13, 2.45 |
| FX Caching (10) | 3/7/0/0, 0.70 | 0/0/2/8, 2.80 |

Every button ≥ 2. Weakest remaining (2): the hair-state letter icons (pixel-font letters vs Maya's smooth
ones), Phong / Phong E / Blinn / Lambert (Maya's balls are near-identical; ours differ on purpose), Sweep Mesh
(a coil, Maya a twisted ribbon), Bridge, Untrim, Birail.

## Verification

- `ALLSET_SANDBOX=shelf131 python tests/run.py -k step131_icons,step109,step51`:
  `test_shelf_buttons_unique` PASS, `test_shelf_icons_sizes` PASS, step109 / step51 all PASS; the three
  status / panel tests of `test_step131_icons` fail in this worktree (`status_icons.image` belongs to another
  lane).
- Uniqueness margin (sheet script): no pair of a shelf below 4 %; closest pairs ~4.7-8 % (hair states, material
  balls, NURBS Cube / Bevel Plus).
- 32 vs 64: the 64 px picture scaled down differs from the 32 px one in ≤ 1.6 % of pixels (Ambient Light), most
  icons 0 %.
- GUI: `python tests/gui/run.py -k step109,step51,step113` at the default effective scale 1.25 (25 passed) and
  with `--ui-scale 0.8` = effective 1.0 (26 passed); shelf row crops in `tmp/shelf131/gui_shelf_*.png`.

## Left

- The template shelf row draws icons at 28 px at UI scale 1.25 (row height bound), so the 2x texture is not
  visible there; a taller row is a layout decision for the main lane.
