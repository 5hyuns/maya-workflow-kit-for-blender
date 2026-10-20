"""Shared data + image helpers for tools/look_shots.py (GUI) and tools/look_compare.py (headless).

Coordinates are screenshot pixels, origin top-left, in the 1600x900 window both apps use
(Maya: research/maya/screens/_maya_ui_dump.json widgets are relative to MayaWindow, which is
the grabbed rectangle, so they are screenshot coordinates too).

Kit points/rects are given relative to a kit *anchor* (an area/region found at shot time, see
``look_shots.anchor_rects``) so the tables survive layout changes. Offsets: dx/dy >= 0 count from
the anchor's left/top edge, < 0 from its right/bottom edge.
"""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAYA = ROOT / "research" / "maya"
SCREENS = MAYA / "screens"
# ALLSET_LOOK_TAG (step 118): another Blender version writes into compare_<tag> and tmp/look_env_<tag>
COMPARE = SCREENS / ("compare_" + os.environ["ALLSET_LOOK_TAG"] if os.environ.get("ALLSET_LOOK_TAG") else "compare")

# ---------------------------------------------------------------- camera (docs/steps/step_41.md)
# Maya persp: 35 mm lens, 1.417 in (36 mm) horizontal aperture, Fill fit = horizontal on the
# wide viewport -> horizontal FOV 2*atan(18/35) = 54.43 deg (Maya 2022 camera defaults [K];
# checked against the cube size in the Maya shots, step 41). Eye (28, 21, 28) Y-up
# (research/maya/defaults.json) = Blender (28, -28, 21) cm.
MAYA_FOCAL_MM, MAYA_APERTURE_MM = 35.0, 36.0
MAYA_EYE_BLENDER = (28.0, -28.0, 21.0)
# Maya's GL view inside modelPanel4 (dump [315,133,1001,651]) minus panel menu bar + icon bar (39 px).
MAYA_VIEW_RECT = (315, 172, 1001, 612)


def maya_f_px():
    """Maya persp focal length in screen pixels (pixels per unit of tan)."""
    return (MAYA_VIEW_RECT[2] / 2) / (MAYA_APERTURE_MM / 2 / MAYA_FOCAL_MM)


# Shots whose kit camera is fitted to the Maya cube: shot -> (Maya wire colour that outlines
# pCube1 in that shot, what Maya did). The kit view then uses Maya's pixel focal length and the
# distance that gives pCube1 the same on-screen height.
CUBE_FITS = {
    "02_cube_selected_move": ("#43ffa3", "viewFit pCube1 fitFactor 0.35 (lead wire, green)"),
    "04_wire_selected_lead": ("#43ffa3", "viewFit all fitFactor 0.8 (pCube1 lead wire, green)"),
    "07_faces_selected": ("#64dcff", "same camera as 04 (component-mode wire, light blue)"),
}

# ---------------------------------------------------------------- pixel samples
# Maya sample name (research/maya/colors.json "ui_samples") -> kit point:
#   (shot, anchor, dx, dy, radius, note)  or  (None, note) = the kit has no such element.
# Offsets were read off the kit shots of step 41 (layout of tools/make_startup.py at that time);
# a layout change moves the anchors, not these numbers. "press" = where Space / RMB went down.
KIT_POINTS = {
    "menu_bar_bg": ("02_cube_selected_move", "topbar", -200, 16, 2, "top bar, left of the workspace menu"),
    "status_line_bg": ("02_cube_selected_move", "strip.HEADER", -20, 16, 2, "Status Line row, right end"),
    "shelf_tab_bar_bg": ("02_cube_selected_move", "shelf.HEADER", -20, 13, 2, "shelf tab row, right end"),
    "shelf_tab_active": ("02_cube_selected_move", "shelf.HEADER", 152, 7, 1, "current tab (Poly Modeling), left padding"),
    "shelf_tab_inactive": ("02_cube_selected_move", "shelf.HEADER", 395, 5, 1, "Rigging tab, above the text"),
    "shelf_icon_row_bg": ("02_cube_selected_move", "shelf.WINDOW", -20, 19, 2, "shelf icon row, right end"),
    "toolbox_bg": ("02_cube_selected_move", "toolbox.TOOLS", 28, -40, 2, "Tool Box column, bottom"),
    "toolbox_active_tool": ("02_cube_selected_move", "toolbox.TOOLS", 27, 132, 1, "Move tool button (step 99: re-picked)"),
    "outliner_header_bg": (None, "no Outliner dock title"),
    "outliner_menu_bg": ("02_cube_selected_move", "outliner.HEADER", 3, 16, 1, "Outliner header padding"),
    "outliner_search_field": ("02_cube_selected_move", "outliner.HEADER", 207, 16, 0,
                              "Outliner search field (step 119: the 1-2 px of fill left of the icon in 4.5 and 5.x)"),
    "outliner_list_bg": ("02_cube_selected_move", "outliner.WINDOW", 130, -60, 2, "Outliner list"),
    "outliner_row_selected": ("11_channel_box", "outliner.WINDOW", 200, 14, 2, "selected row pCube1"),
    "outliner_row_selected_component_mode": ("08_verts_selected", "outliner.WINDOW", 200, 14, 2,
                                             "pCube1 row in edit mode"),
    "panel_menu_bar_bg": ("02_cube_selected_move", "view3d.HEADER", 4, 16, 1, "3D View header padding"),
    "panel_toolbar_bg": (None, "no panel icon bar (the tool settings row is hidden, step 49)"),
    "viewport_bg": ("02_cube_selected_move", "view3d.WINDOW", 380, 90, 2, "persp background, upper area"),
    "viewport_border": ("02_cube_selected_move", "window", 264, 500, 0, "editor border Outliner | view"),
    "cb_bg": ("11_channel_box", "view3d.UI", 24, 213, 2, "Channel Box panel background"),
    "cb_field": ("11_channel_box", "view3d.UI", 172, 92, 2, "Translate X value field"),
    "cb_shape_row": ("11_channel_box", "view3d.UI", 172, 280, 2, "SHAPES row pCubeShape1"),
    "cb_input_row": (None, "no INPUTS row for a cube without modifiers (Maya: polyCube1 history)"),
    "layer_editor_list": ("11_channel_box", "view3d.UI", 130, 450, 2, "Layer Editor list"),
    "layer_tab_active": ("02_cube_selected_move", "view3d.UI", 37, 341, 1, "Display tab (active: Blender's blue, step 99)"),
    "dock_side_tab_strip": ("11_channel_box", "view3d.UI", -14, -150, 2, "sidebar tab strip"),
    "time_slider_bg": ("11_channel_box", "timeline.WINDOW", 705, 15, 2, "timeline ruler between labels"),
    "time_field": ("11_channel_box", "timeline.UI", 60, 18, 2, "current frame field (Time Slider row)"),
    "range_slider_field": ("11_channel_box", "timeline.HEADER", 90, 13, 2, "start frame field"),
    "range_slider_bar": ("02_cube_selected_move", "timeline.HEADER", 350, 13, 2, "Range Slider bar (ui/range_bar.py, step 73)"),
    "range_slider_handle": ("02_cube_selected_move", "timeline.HEADER", 244, 13, 1, "Range Slider start handle"),
    "bottom_bars_bg": ("11_channel_box", "timeline.HEADER", 850, 16, 2, "timeline header background"),
    "command_line_field": ("11_channel_box", "statusbar.command", 160, 14, 2, "Python command field"),
    "command_result_field": (None, "no result field"),
    "help_line_bg": ("11_channel_box", "statusbar.help", 600, 14, 2, "Help Line background"),
    "menu_popup_bg": ("12_create_menu", "topbar", 390, 330, 2, "Create menu body, right margin"),
    "marking_menu_box": ("14_marking_menu_object", "press", -16, -81, 1, "radial box Edge, padding"),
    "marking_menu_list_bg": ("14_marking_menu_object", "press", -31, 205, 1, "list body right of Select Hierarchy"),
    "hotbox_row_bg": ("13_hotbox", "press", -253, 36, 1, "hotbox row Mesh, left padding (over the view background)"),
}

# ---------------------------------------------------------------- viewport pixels (step 43)
# Rendered viewport elements. (label, shot, Maya colour or None, kit point key, radius, mode, Maya region)
#   mode "best": the pixel closest to the Maya colour, in the Maya view and in a box of +-radius
#                around each kit point (geometry.json "points": edge midpoints, vertices, origin);
#                robust to 1 px line offsets and anti-aliasing.
#   mode "tint": selected-face fill only. Maya stipples selected faces; the kit's fill alpha is
#                measured (kit shot vs the base shot, same view, (2r+1)x(r+1) box at the kit point),
#                laid over Maya's base shading of the region and compared with Maya's mean there.
#                Region = (Maya base shot, Maya [x, y, w, h], kit base shot).
#   mode "best" with a shot name as region: the kit pixels come from that kit shot (step 47: Maya has no
#                shaded shot with two objects selected; its white wire pixel is taken from 04). The kit base is 03 (same
#                view, no manipulator): at the Maya density the Move arrow's tip covers the box in 02
#                (step 44).
VIEW_SAMPLES = (
    ("lead wire (pCube1, green)", "04_wire_selected_lead", "#43ffa3", "pCube1.edges", 3, "best", None),
    ("other selected wire (pCube2, white)", "04_wire_selected_lead", "#ffffff", "pCube2.edges", 3, "best", None),
    ("dormant wire (pCube3, dark blue)", "04_wire_selected_lead", "#000460", "pCube3.edges", 3, "best", None),
    # step 47: selection wire over shading. "best" + a kit shot name in the last field = kit pixels from that shot.
    ("lead wire over shading (pCube1)", "02_cube_selected_move", "#43ffa3", "pCube1.edges", 3, "best", None),
    ("other selected wire over shading (pCube2)", "04_wire_selected_lead", "#ffffff", "pCube2.edges", 3, "best",
     "02b_two_selected_shaded"),
    ("component-mode wire (light blue)", "07_faces_selected", "#64dcff", "pCube1.edges", 3, "best", None),
    ("selected face, top (fill)", "07_faces_selected", None, "pCube1.top_face", 6, "tint",
     ("02_cube_selected_move", (830, 400, 20, 12), "03_cube_unselected")),
    ("selected vertex (pale yellow)", "08_verts_selected", "#fdff88", "pCube1.sel_verts", 4, "best", None),
    ("unselected vertex (purple)", "08_verts_selected", "#c800c8", "pCube1.verts", 4, "best", None),
    ("manipulator X (red)", "02_cube_selected_move", "#e60000", "pCube1.origin", 120, "best", None),
    ("manipulator Y (green)", "02_cube_selected_move", "#00e600", "pCube1.origin", 120, "best", None),
    ("manipulator Z (blue)", "02_cube_selected_move", "#0000ff", "pCube1.origin", 120, "best", None),
)


def best_pixel(img, hex_colour, rect, keep=1):
    """(x, y, rgb) of the pixel in rect [x, y, w, h] closest (RGB distance) to the colour; with
    keep > 1 a list of the ``keep`` closest (callers pick by CIEDE2000)."""
    import numpy as np
    h = hex_colour.lstrip("#")
    ref = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
    H, W, _ = img.shape
    x0, y0 = max(0, int(rect[0])), max(0, int(rect[1]))
    x1, y1 = min(W, int(rect[0] + rect[2])), min(H, int(rect[1] + rect[3]))
    sub = img[y0:y1, x0:x1]
    if sub.size == 0:
        return None
    d = np.sum((sub - ref) ** 2, axis=2)
    order = np.argsort(d, axis=None)[:keep]
    out = []
    for flat in order:
        yy, xx = np.unravel_index(flat, d.shape)
        out.append((x0 + int(xx), y0 + int(yy), tuple(float(v) for v in sub[yy, xx])))
    return out[0] if keep == 1 else out


def mean_colour(img, rect):
    import numpy as np
    x, y, w, h = (int(round(v)) for v in rect)
    return tuple(float(v) for v in img[y:y + h, x:x + w].reshape(-1, 3).mean(axis=0))


# ---------------------------------------------------------------- rectangles
# Maya widget (dump "widgets") -> kit anchor. Kit-only anchors are listed in KIT_ONLY.
RECTS = (
    ("menuBar", "topbar", "main menu bar"),
    ("StatusLine", "strip.HEADER", "Status Line"),
    ("Shelf", "shelf", "Shelf (kit: tab row = header, icon row = WINDOW)"),
    ("ToolBox", "toolbox", "Tool Box"),
    ("Outliner", "outliner", "Outliner"),
    ("MainPane", "view3d.pane", "viewport pane (kit: 3D View without the sidebar dock)"),
    ("modelPanel4", "view3d.pane", "persp panel (Maya: incl. panel menu + icon bar; kit: incl. header)"),
    ("ChannelBoxLayerEditor", "view3d.UI", "Channel Box / Layer Editor dock"),
    ("TimeSlider", "timeline.WINDOW", "Time Slider"),
    ("RangeSlider", "timeline.HEADER", "Range Slider (kit: timeline header, under the Time Slider)"),
    ("HelpLine", "statusbar.help", "Help Line (kit: status bar row, left)"),
    ("CommandLine", "statusbar.command", "Command Line (kit: status bar row, right)"),
)
KIT_ONLY = ("outliner_right", "properties", "view3d.TOOLS", "view3d.TOOL_HEADER")
RECT_TOL = 10

# ---------------------------------------------------------------- crops
# name -> (shot, Maya widget in the dump, kit anchor, stack): side = side by side, over = Maya above kit
CROPS = (
    ("status_line", "11_channel_box", "StatusLine", "strip.HEADER", "over"),
    ("shelf", "11_channel_box", "Shelf", "shelf", "over"),
    ("channel_box", "11_channel_box", "ChannelBoxLayerEditor", "view3d.UI", "side"),
    ("outliner", "11_channel_box", "Outliner", "outliner", "side"),
    ("time_slider", "11_channel_box", "TimeSlider", "timeline.WINDOW", "over"),
    ("range_slider", "11_channel_box", "RangeSlider", "timeline.HEADER", "over"),
)


def maya_dump():
    return json.loads((SCREENS / "_maya_ui_dump.json").read_text())


def maya_colors():
    return json.loads((MAYA / "colors.json").read_text())


# Used when the KIT_POINTS anchor is missing: Blender 5.x never opens the Timeline sidebar, so the Maya Workflow Kit timeline is
# one row and the Time Slider buttons sit at the right end of the header (step 118, 119).
KIT_POINTS_ALT = {
    "time_field": ("11_channel_box", "timeline.HEADER", -230, 13, 2, "current frame field (5.x: header right end)"),
}


def resolve(rects, anchor, dx=0, dy=0):
    """Point (x, y) from an anchor rect [x, y, w, h] and offsets (negative = from right/bottom)."""
    x, y, w, h = rects[anchor]
    return (x + dx if dx >= 0 else x + w + dx), (y + dy if dy >= 0 else y + h + dy)


# ---------------------------------------------------------------- images (bpy + numpy)
def load_rgb(path):
    """PNG -> numpy float array [row (top first), col, rgb] in 0..1 (stored sRGB values)."""
    import bpy
    import numpy as np
    im = bpy.data.images.load(str(path), check_existing=False)
    try:
        w, h = im.size
        a = np.empty(w * h * 4, dtype=np.float32)
        im.pixels.foreach_get(a)
    finally:
        bpy.data.images.remove(im)
    return a.reshape(h, w, 4)[::-1, :, :3].copy()


def sample(img, x, y, r=2):
    """Median colour of the (2r+1)^2 box at (x, y)."""
    import numpy as np
    h, w, _ = img.shape
    x0, x1 = max(0, x - r), min(w, x + r + 1)
    y0, y1 = max(0, y - r), min(h, y + r + 1)
    return tuple(float(v) for v in np.median(img[y0:y1, x0:x1].reshape(-1, 3), axis=0))


def colour_bbox(img, hex_colour, rect, tol=30):
    """Bounding box [x0, y0, x1, y1] of pixels within ``tol`` (0..255, per channel) of a colour."""
    import numpy as np
    h = hex_colour.lstrip("#")
    ref = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
    x, y, w, hh = rect
    sub = img[y:y + hh, x:x + w] * 255.0
    mask = np.all(np.abs(sub - ref) <= tol, axis=2)
    ys, xs = np.nonzero(mask)
    if len(xs) < 4:
        return None
    return [int(xs.min()) + x, int(ys.min()) + y, int(xs.max()) + x, int(ys.max()) + y]


def maya_cube_bbox(shot):
    colour, _note = CUBE_FITS[shot]
    return colour_bbox(load_rgb(SCREENS / f"{shot}.png"), colour, MAYA_VIEW_RECT)


# ---------------------------------------------------------------- density (step 44)
# Maya 2022 at Qt dpr 1.0 (research/maya/colors.json metrics): menu bar 27 px, menu items 20 px,
# Channel Box rows 16 px. (name, target px, tolerance px)
DENSITY = (
    ("menu bar height", 27, 2),
    ("menu item pitch", 20, 1),
    ("Channel Box row pitch", 16, 1),
    # step 51: the Create menu opens right under the menu bar; Maya's 64 px shelf with 32 px icons
    ("menu top - menu bar bottom", 0, 4),
    ("shelf height", 64, 2),
    ("shelf icon", 32, 2),
)
# Menu popup background: Maya #525252 (colors.json ui notes), kit theme wcol_menu_back #535353.
MENU_BG = {"maya": "#525252", "kit": "#535353"}
MENU_SEARCH = (10, 20, 690, 680)  # where the Create menu opens under the menu bar, [x, y, w, h]; from x 10: the
# 1 px editor outline at the window edge (x 2 in 5.x, the same #535353 as the menu) is no menu (step 119)


def colour_area(img, hex_colour, rect, tol=2, min_run=60):
    """[x, y, w, h] spanned by rows and columns holding at least ``min_run`` pixels of a flat colour."""
    import numpy as np
    h = hex_colour.lstrip("#")
    ref = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
    x, y, w, hh = rect
    mask = np.all(np.abs(img[y:y + hh, x:x + w] * 255.0 - ref) <= tol, axis=2)
    cols = np.nonzero(mask.sum(axis=0) >= min_run)[0]
    rows = np.nonzero(mask.sum(axis=1) >= min_run // 2)[0]
    if len(cols) < 2 or len(rows) < 2:
        return None
    return [int(cols.min()) + x, int(rows.min()) + y, int(cols.max() - cols.min() + 1),
            int(rows.max() - rows.min() + 1)]


def line_pitch(img, rect, contrast=0.15):
    """Most common distance (px) between the centres of consecutive text lines inside ``rect``.

    A row is a text row when at least 2 of its pixels are ``contrast`` brighter than the rect's median
    (light text on Maya's and the kit's dark greys). Returns (pitch, lines, rows at that pitch ±1).
    """
    import numpy as np
    x, y, w, h = (int(round(v)) for v in rect)
    sub = img[max(0, y):y + h, max(0, x):x + w]
    lum = sub.mean(axis=2)
    bright = (lum > np.median(lum) + contrast).sum(axis=1) >= 2
    centres, start = [], None
    for i, b in enumerate(list(bright) + [False]):
        if b and start is None:
            start = i
        elif not b and start is not None:
            if i - start >= 3:             # ignore 1-2 px lines (separators, field edges)
                centres.append((start + i - 1) / 2)
            start = None
    diffs = [round(b - a) for a, b in zip(centres, centres[1:])]
    if not diffs:
        return None, len(centres), 0
    counts = {d: sum(abs(v - d) <= 1 for v in diffs) for d in set(diffs) if d >= 8}
    if not counts:
        return None, len(centres), 0
    pitch = max(counts, key=lambda d: (counts[d], -d))
    near = [v for v in diffs if abs(v - pitch) <= 1]
    return round(sum(near) / len(near), 1), len(centres), counts[pitch]


# ---------------------------------------------------------------- view furniture (step 46)
# Found the same way in both shots inside search boxes at the view's corners (offsets from the view rect:
# Maya MAYA_VIEW_RECT, kit "view3d.visible"): ViewCube = pixels brighter than 130 (white faces at 0.5),
# label = brighter than 180, triad = saturated (max - min channel > 80).
# (name, corner, search box [dx, dy, w, h] from that corner, test)
FURNITURE = (
    ("ViewCube", "top-right", (-160, 0, 160, 130), "bright130"),
    ("camera label", "bottom-centre", (-120, -30, 240, 30), "bright180"),
    ("axis triad", "bottom-left", (0, -90, 90, 90), "saturated"),
)
FURNITURE_TOL = 10
TEXT_INFO_BOX = (5, 5, 320, 50)    # top-left of the view, where Blender's text info draws


def _test(img, name):
    lum = img.mean(axis=2) * 255
    if name == "bright130":
        return lum > 130
    if name == "bright180":
        return lum > 180
    return (img.max(axis=2) - img.min(axis=2)) * 255 > 80


def furniture_box(img, view, corner, box, test):
    """Bounding box [x, y, w, h] (screenshot px) of the furniture element, or None."""
    import numpy as np
    vx, vy, vw, vh = view
    ox = {"top-right": vx + vw, "bottom-centre": vx + vw / 2, "bottom-left": vx}[corner]
    oy = vy if corner == "top-right" else vy + vh
    x, y = int(round(ox + box[0])), int(round(oy + box[1]))
    sub = img[max(0, y):y + box[3], max(0, x):x + box[2]]
    ys, xs = np.nonzero(_test(sub, test))
    if len(xs) == 0:
        return None
    return [int(xs.min()) + x, int(ys.min()) + y, int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)]


def corner_offsets(rect, view, corner):
    """Element rect relative to the view corner it belongs to: (dx, dy) of its outer edges, (w, h)."""
    x, y, w, h = rect
    vx, vy, vw, vh = view
    if corner == "top-right":
        return (vx + vw) - (x + w), y - vy, w, h
    if corner == "bottom-centre":
        return (x + w / 2) - (vx + vw / 2), (vy + vh) - (y + h), w, h
    return x - vx, (vy + vh) - (y + h), w, h


def triad_origin(img, rect):
    """Pixel where the red, green and blue axis lines meet inside ``rect`` [x, y, w, h] (both shots: the
    point whose farthest nearest-colour pixel is closest), or None."""
    import numpy as np
    x, y, w, h = (int(round(v)) for v in rect)
    sub = img[y:y + h, x:x + w] * 255
    groups = []
    for c in range(3):
        others = [o for o in range(3) if o != c]
        m = (sub[:, :, c] > 150) & (sub[:, :, others[0]] < 110) & (sub[:, :, others[1]] < 110)
        ys, xs = np.nonzero(m)
        if len(xs) == 0:
            return None
        groups.append(np.stack([xs, ys], axis=1).astype(float))
    gy, gx = np.mgrid[0:h, 0:w]
    grid = np.stack([gx.ravel(), gy.ravel()], axis=1).astype(float)
    worst = np.zeros(len(grid))
    for g in groups:
        d = np.sqrt(((grid[:, None, :] - g[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
        worst = np.maximum(worst, d)
    i = int(worst.argmin())
    return [x + grid[i][0], y + grid[i][1]]
