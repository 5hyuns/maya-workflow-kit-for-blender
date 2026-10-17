"""Shared data + image helpers for tools/look_shots.py (GUI) and tools/look_compare.py (headless).

Coordinates are screenshot pixels, origin top-left, in the 1600x900 window both apps use
(Maya: research/maya/screens/_maya_ui_dump.json widgets are relative to MayaWindow, which is
the grabbed rectangle, so they are screenshot coordinates too).

Kit points/rects are given relative to a kit *anchor* (an area/region found at shot time, see
``look_shots.anchor_rects``) so the tables survive layout changes. Offsets: dx/dy >= 0 count from
the anchor's left/top edge, < 0 from its right/bottom edge.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAYA = ROOT / "research" / "maya"
SCREENS = MAYA / "screens"
COMPARE = SCREENS / "compare"

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
    "shelf_tab_bar_bg": (None, "no shelf tab row (shelf set = dropdown)"),
    "shelf_tab_active": (None, "no shelf tabs"),
    "shelf_tab_inactive": (None, "no shelf tabs"),
    "shelf_icon_row_bg": ("02_cube_selected_move", "strip.TOOL_HEADER", -20, 16, 2, "shelf row, right end"),
    "toolbox_bg": ("02_cube_selected_move", "view3d.TOOLS", 35, -40, 2, "toolbar column (drawn over the view)"),
    "toolbox_active_tool": ("02_cube_selected_move", "view3d.TOOLS", 16, 108, 1, "Move tool button padding"),
    "outliner_header_bg": (None, "no Outliner dock title"),
    "outliner_menu_bg": ("02_cube_selected_move", "outliner.HEADER", 3, 16, 1, "Outliner header padding"),
    "outliner_search_field": ("02_cube_selected_move", "outliner.HEADER", 210, 16, 2, "Outliner search field"),
    "outliner_list_bg": ("02_cube_selected_move", "outliner.WINDOW", 130, -60, 2, "Outliner list"),
    "outliner_row_selected": ("11_channel_box", "outliner.WINDOW", 200, 14, 2, "selected row pCube1"),
    "outliner_row_selected_component_mode": ("08_verts_selected", "outliner.WINDOW", 200, 14, 2,
                                             "pCube1 row in edit mode"),
    "panel_menu_bar_bg": ("02_cube_selected_move", "view3d.HEADER", 4, 16, 1, "3D View header padding"),
    "panel_toolbar_bg": ("02_cube_selected_move", "view3d.TOOL_HEADER", -200, 16, 2, "tool header row"),
    "viewport_bg": ("02_cube_selected_move", "view3d.WINDOW", 380, 90, 2, "persp background, upper area"),
    "viewport_border": ("02_cube_selected_move", "window", 264, 500, 0, "editor border Outliner | view"),
    "cb_bg": ("11_channel_box", "view3d.UI", 24, 213, 2, "Channel Box panel background"),
    "cb_field": ("11_channel_box", "view3d.UI", 229, 133, 2, "Translate X value field"),
    "cb_shape_row": ("11_channel_box", "view3d.UI", 229, 430, 2, "SHAPES row pCubeShape1"),
    "cb_input_row": (None, "no INPUTS row for a cube without modifiers (Maya: polyCube1 history)"),
    "layer_editor_list": ("11_channel_box", "view3d.UI", 229, 545, 2, "Layer Editor body"),
    "layer_tab_active": (None, "no Display/Anim tabs"),
    "dock_side_tab_strip": ("11_channel_box", "view3d.UI", -14, -150, 2, "sidebar tab strip"),
    "time_slider_bg": ("11_channel_box", "timeline.WINDOW", 705, 15, 2, "timeline ruler between labels"),
    "time_field": ("11_channel_box", "timeline.HEADER", 715, 16, 2, "current frame field"),
    "range_slider_field": ("11_channel_box", "timeline.HEADER", 940, 16, 2, "start frame field"),
    "range_slider_bar": (None, "no range bar"),
    "range_slider_handle": (None, "no range bar"),
    "bottom_bars_bg": ("11_channel_box", "timeline.HEADER", 850, 16, 2, "timeline header background"),
    "command_line_field": ("11_channel_box", "statusbar", 300, 14, 2, "Python command field"),
    "command_result_field": (None, "no result field"),
    "help_line_bg": ("11_channel_box", "statusbar", 800, 14, 2, "status bar background"),
    "menu_popup_bg": ("12_create_menu", "topbar", 390, 330, 2, "Create menu body, right margin"),
    "marking_menu_box": ("14_marking_menu_object", "press", -24, -99, 1, "radial box Edge, padding"),
    "marking_menu_list_bg": ("14_marking_menu_object", "press", -198, -77, 1, "list row Select Hierarchy"),
    "hotbox_row_bg": ("13_hotbox", "press", -257, -124, 1, "hotbox box File, padding"),
}

# ---------------------------------------------------------------- viewport pixels (step 43)
# Rendered viewport elements. (label, shot, Maya colour or None, kit point key, radius, mode, Maya region)
#   mode "best": the pixel closest to the Maya colour, in the Maya view and in a box of +-radius
#                around each kit point (geometry.json "points": edge midpoints, vertices, origin);
#                robust to 1 px line offsets and anti-aliasing.
#   mode "tint": selected-face fill only. Maya stipples selected faces; the kit's fill alpha is
#                measured (kit shot vs the base shot, same view, (2r+1)x(r+1) box at the kit point),
#                laid over Maya's base shading of the region and compared with Maya's mean there.
#                Region = (Maya base shot, Maya [x, y, w, h], kit base shot). The kit base is 03 (same
#                view, no manipulator): at the Maya density the Move arrow's tip covers the box in 02
#                (step 44).
VIEW_SAMPLES = (
    ("lead wire (pCube1, green)", "04_wire_selected_lead", "#43ffa3", "pCube1.edges", 3, "best", None),
    ("other selected wire (pCube2, white)", "04_wire_selected_lead", "#ffffff", "pCube2.edges", 3, "best", None),
    ("dormant wire (pCube3, dark blue)", "04_wire_selected_lead", "#000460", "pCube3.edges", 3, "best", None),
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
    ("Shelf", "strip.TOOL_HEADER", "Shelf"),
    ("ToolBox", "view3d.TOOLS", "Tool Box"),
    ("Outliner", "outliner", "Outliner"),
    ("MainPane", "view3d", "viewport pane"),
    ("modelPanel4", "view3d.WINDOW", "persp panel (Maya: incl. panel menu + icon bar)"),
    ("ChannelBoxLayerEditor", "view3d.UI", "Channel Box / Layer Editor dock"),
    ("TimeSlider", "timeline.WINDOW", "Time Slider"),
    ("RangeSlider", "timeline.HEADER", "Range Slider (kit: timeline header)"),
    ("HelpLine", "statusbar", "Help Line (kit: status bar)"),
    ("CommandLine", "statusbar", "Command Line (kit: status bar)"),
)
KIT_ONLY = ("outliner_right", "properties")
RECT_TOL = 10

# ---------------------------------------------------------------- crops
# name -> (shot, Maya widget in the dump, kit anchor, stack): side = side by side, over = Maya above kit
CROPS = (
    ("status_line", "11_channel_box", "StatusLine", "strip.HEADER", "over"),
    ("shelf", "11_channel_box", "Shelf", "strip.TOOL_HEADER", "over"),
    ("channel_box", "11_channel_box", "ChannelBoxLayerEditor", "view3d.UI", "side"),
    ("outliner", "11_channel_box", "Outliner", "outliner", "side"),
    ("time_slider", "11_channel_box", "TimeSlider", "timeline.WINDOW", "over"),
    ("range_slider", "11_channel_box", "RangeSlider", "timeline.HEADER", "over"),
)


def maya_dump():
    return json.loads((SCREENS / "_maya_ui_dump.json").read_text())


def maya_colors():
    return json.loads((MAYA / "colors.json").read_text())


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
)
# Menu popup background: Maya #525252 (colors.json ui notes), kit theme wcol_menu_back #535353.
MENU_BG = {"maya": "#525252", "kit": "#535353"}
MENU_SEARCH = (0, 20, 700, 680)   # where the Create menu opens under the menu bar, [x, y, w, h]


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
