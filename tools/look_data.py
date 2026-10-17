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
