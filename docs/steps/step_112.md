# Step 112 — User bug: see-through Channel Box dock, empty Tool Box strip

User report 2026-10-19 (real GUI, Blender 4.5.4, Maya layout; screenshot
`hermes/autodrive_bmk/user_bug_1019_transparent.png`):

1. Right dock (Channel Box / Layer Editor / Attribute Editor = 3D View sidebar tabs): only the value fields were opaque,
   the viewport grid and axis lines showed through the rest.
2. Far-left strip (~50 px, left of the Outliner, only a `<` / `>` arrow): no tool icons, viewport showing through; the
   Tool Box icons were drawn inside the main viewport instead (x ≈ 305–345).

## 원인 (재현)

Reproduced with the user's path in a clean sandbox: extension installed, Maya mode on (`switch.enter_layout`), Blender's
own theme (the Maya theme is a separate opt-in, `maya_theme`), effective UI scale 1.25 —
`tests/gui/gui_step112_opaque.py`, before picture `step_112/before_125.png`.

1. **Dock**: Blender's Region Overlap (`preferences.system.use_region_overlap`, on by default) draws 3D View sidebars
   over the viewport with the theme's region background alpha — `view_3d.space.button` alpha is **0** in Blender's
   theme (measured `(0.188, 0.188, 0.188, 0.0)`), and the Channel Box panel has no header, so no panel background is
   drawn either. The Maya theme (`studio_grey.xml`, `button="#444444ff"`) hides it, but only when the user turned that
   option on. Same for every overlapping region: Image / UV Editor sidebar and toolbar, the main view's toolbar.
2. **Tool Box**: the template column was exactly one toolbar column at UI scale 1.0 (57 px). Area sizes are pixels
   (scaled with the window, not with the UI scale); at 1.25 the toolbar needs 70 px, and Blender doesn't draw a region
   wider than its area at all (`RGN_FLAG_TOO_SMALL`). `toolbox.fit_columns` widens it through `screen.area_move`,
   which only polls with the mouse in an area gap, so it warps the cursor there (`ALLSET_OT_fit_columns`, at most 3
   times per load, stops when the user moves the mouse). When that fails, the fallback shows the main view's toolbar
   and the column stays an empty strip — the user's picture (reproduced with the cursor fit off: column 56 px, no TOOLS
   region, main view toolbar on).
   The user's strip also showed the grid X axis: its overlays were on, and `is_toolbox` required overlays off, so the
   column wasn't even recognised any more.

## 계획 (delegated)

- Dock: theme alpha only fixes it for users of the Maya theme, and writing into the user's own theme without that
  option would change their colours behind an opt-in they didn't take. Region overlap off is Maya's own arrangement — the viewport area ends where
  the dock starts (`research/maya/ui_layout.md:96`) — and it is one Blender preference: new `prefs_preset` group
  `panels` ("Solid Side Panels", `use_maya_panels`, default on like the navigation group; backup / restore when the
  option, Maya mode or the add-on goes off; in `switch.FOOTPRINT`). Per-region overlap doesn't exist in 4.5, and a
  Python handler can't draw behind panels (UI regions call only POST_PIXEL). Fixes Image / UV sidebars too (Graph
  Editor / Dope Sheet sidebars never overlap).
- Tool Box: template column with room for one toolbar column up to scale 1.6 (`tools/make_startup.py`
  `TOOLBOX_ROOM`, 90 px at 1600 px: 1.25 fits even in a 1280 px window); the cursor fit still narrows it to one column
  when it can. The spare width must not look like a viewport: `toolbox.settle` gives the column a flat background in
  the toolbar's theme colour (`View3DShading.background_type = 'VIEWPORT'`) and turns its overlays off again from the
  fit timer. `is_toolbox` keys on "every object type hidden" (`show_object_viewport_mesh` off) instead of overlays off.
- The leftover strip is kept (not removed): it is Maya's Tool Box column (`ui_layout.md:224`), now always showing its
  tools; the main view's duplicate toolbar only appears in the old fallback (column narrower than the toolbar).

## 한 것

- `prefs_preset.PANELS_PRESET` (`system.use_region_overlap` False), group `panels`; `preferences.use_maya_panels`
  "Solid Side Panels" + `panels_backup`, shown under Maya Navigation in the add-on preferences; `switch.FOOTPRINT`.
- `ui/toolbox.py`: `is_toolbox` (overlays no longer part of the identity), `settle(space)` (overlays off, flat
  background = `view_3d.space.button` converted sRGB → linear: the viewport colour is scene linear — written as is,
  sRGB 48 showed as 119, measured), called from `fit_columns` every tick.
- `tools/make_startup.py`: `TOOLBOX_ROOM = 1.6`, `is_toolbox_space` in sync; `startup.blend` regenerated (column 90 px,
  Outliner 260, view 1244 at 1600 px).
- Tests: `tests/gui/gui_step112_opaque.py` (user's path, cursor fit off, 9 checks: overlap off, dock beside the view,
  column draws its toolbar unfitted, no main-view toolbar, screen pixels — dock margin = region colour ≠ viewport,
  spare column = toolbar colour — overlays turned on get settled, Blender mode gives overlap back);
  `tests/test_step112_panels.py` (5: enable / option / disable restore, identity ignores overlays, framing);
  `tests/test_step49_layout.py` identity sync test follows the new flag.
- Side effects of a view beside the dock (the 3D View WINDOW region is now narrower than its area):
  - `operators/framing.fit` rewritten as a distance search on the centred box (`centred(d)`: Newton pan steps on
    the measured response, halved while the error grows). The old "refit distance, then one linear pan" rounds
    oscillated for a box much wider than deep in a narrower perspective view: Ctrl+Shift+F / A with a far child left
    the box 1.2–1.5× the view (`gui_step17_framing`, reproduced headless with the GUI's matrices).
  - The persp view now spans only the visible part, as Maya's panel does (Maya's 54.4° fits the panel width, not
    the width under the dock): objects look smaller than with the old overlapped region.
  - Tests that assumed overlap: `tests/gui/sim.py` starts sessions with overlap off (region rects only follow a
    preference change at the next screen refresh, so positions computed in the enable tick were stale;
    `ALLSET_GUI_KEEP_OVERLAP=1` keeps Blender's value for the step 112 test); `gui_step4_view` (top-left quad
    region = leftmost, right of the toolbar), `gui_step17_framing` (sidebar beside the region), `gui_step49_layout`
    (unfitted column with its toolbar drawn), sweep M76-1 (9 px or the circle's centre), M78-4 (0.15 cm = about two
    pixels), M79 (cube framed before the strokes).
- Pictures: `docs/steps/step_112/before_125.png` (old code, user's case), `after_125.png`, `after_100.png`.

## 검증

- GUI `gui_step112_opaque` 9/9 at 1.25 and at `--ui-scale 0.8` (effective 1.0); screenshots looked at: dock solid grey
  beside the viewport (navigation gizmo moves left of it), Tool Box icons in the left column, no tools in the viewport.
- Headless 851/851 (846 + 5: `test_step112_panels`, incl. the framing case).
- GUI full suite 1083/1083 (1074 + 9). The first full run had 20 failures from the layout change (stale rects in
  the enable tick, framing oscillation, overlap-shaped test geometry): fixed as listed above, then rerun.

## 남은 것

- Users who keep their own theme get Blender's region colour (#303030) for the dock, not Maya's #444444 (that is the
  Maya theme option).
- With the cursor fit failing the column keeps its spare width (up to 34 px at scale 1.0) — solid, but wider than
  Maya's 40 px Tool Box.
- `docs/manual_checks.md` step 112: real-mouse check in the user's own setup.
