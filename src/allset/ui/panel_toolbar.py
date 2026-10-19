# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya viewport panel bar in the Allset layout: the panel menu bar alone, and the panel toolbar under it.

Maya 2022 (, _top113.json "panel"): every model panel has a 19 px menu bar
(View Shading Lighting Show Renderer Panels) and under it a toolbar of 16 px icons on a 19 px pitch in groups —
camera, gates and grid, shading modes and lights, effects, isolate / X-ray — then exposure and gamma fields and the
colour management view. Blender's 3D View header mixed Maya's menus with its own editor-type button, mode selector,
transform orientation, pivot, snapping, proportional editing, overlays and shading (user report 2026-10-19,
).

In 3D Views of the Allset layout (a screen with the Maya strip) the class's own draw of ``VIEW3D_HT_header`` is
replaced by the Maya menu bar and the tool header's by the Maya panel toolbar (like ``editor_chrome``: only the
class's own draw function, so UI appended by others still draws; restored on unregister). Other layouts keep
Blender's header with the Maya menus (``panel_menus``). Icons are kit-drawn (``status_icons``), no Maya assets.
"""

import math

import bpy

from . import panel_menus, status_icons
from .status_icons import BLUE, DARK, DIM, GREY, TEAL

GREY_OP = "allset.menu_unavailable"


# --- glyphs (16 px buttons; drawn on the 32 px status_icons canvas) -----------------------------------

def _camera(cv):
    cv.rect(0.10, 0.34, 0.66, 0.78, GREY)
    cv.poly([(0.66, 0.48), (0.92, 0.32), (0.92, 0.80), (0.66, 0.64)], GREY)


def g_cam_select(cv):
    _camera(cv)
    status_icons.arrow_cursor(cv, 0.40, 0.08, 0.42, TEAL)


def g_cam_lock(cv):
    _camera(cv)
    cv.ring(0.36, 0.30, 0.13, 0.07, TEAL, 0, 180)
    cv.rect(0.22, 0.30, 0.50, 0.52, TEAL)


def g_cam_attr(cv):
    _camera(cv)
    for y in (0.48, 0.62):
        cv.line(0.18, y, 0.56, y, 0.05, DARK)


def g_bookmark(cv):
    cv.poly([(0.26, 0.10), (0.74, 0.10), (0.74, 0.90), (0.50, 0.70), (0.26, 0.90)], GREY)


def g_image_plane(cv):
    cv.frame(0.12, 0.18, 0.88, 0.82, 0.06, GREY)
    cv.poly([(0.20, 0.74), (0.42, 0.44), (0.58, 0.62), (0.68, 0.50), (0.82, 0.74)], TEAL)


def g_pan_zoom(cv):
    cv.frame(0.12, 0.12, 0.88, 0.88, 0.06, GREY)
    cv.line(0.5, 0.25, 0.5, 0.75, 0.08, GREY)
    cv.line(0.25, 0.5, 0.75, 0.5, 0.08, GREY)


def g_grease(cv):
    cv.line(0.20, 0.82, 0.78, 0.22, 0.16, GREY)
    cv.poly([(0.13, 0.92), (0.16, 0.76), (0.28, 0.86)], TEAL)


def g_grid(cv):
    for k in (0.15, 0.38, 0.62, 0.85):
        cv.line(k, 0.12, k, 0.88, 0.05, GREY)
        cv.line(0.12, k, 0.88, k, 0.05, GREY)


def _gate(cv):
    cv.frame(0.08, 0.20, 0.92, 0.80, 0.06, GREY)


def g_film_gate(cv):
    _gate(cv)
    cv.frame(0.24, 0.32, 0.76, 0.68, 0.05, DIM)


def g_res_gate(cv):
    _gate(cv)
    cv.rect(0.24, 0.32, 0.76, 0.68, DIM)


def g_gate_mask(cv):
    cv.rect(0.08, 0.20, 0.92, 0.80, DIM)
    cv.rect(0.26, 0.32, 0.74, 0.68, DARK)


def g_field_chart(cv):
    _gate(cv)
    for r in (0.12, 0.22):
        cv.ring(0.5, 0.5, r, 0.04, DIM)


def g_safe_action(cv):
    _gate(cv)
    cv.frame(0.18, 0.28, 0.82, 0.72, 0.04, TEAL)


def g_safe_title(cv):
    _gate(cv)
    cv.frame(0.26, 0.34, 0.74, 0.66, 0.04, TEAL)


def _ball(cv, colour, wire=False):
    if wire:
        cv.ring(0.5, 0.5, 0.36, 0.06, colour)
        cv.ring(0.5, 0.5, 0.36, 0.05, colour)
        for k in (-0.18, 0.0, 0.18):
            cv.line(0.16, 0.5 + k, 0.84, 0.5 + k, 0.04, colour)
        cv.line(0.5, 0.14, 0.5, 0.86, 0.04, colour)
    else:
        cv.circle(0.5, 0.5, 0.36, colour)


def g_wire(cv):
    _ball(cv, GREY, wire=True)


def g_smooth(cv):
    _ball(cv, GREY)
    cv.circle(0.40, 0.38, 0.10, (0.95, 0.95, 0.95))


def g_default_mat(cv):
    _ball(cv, DIM)


def g_wire_on_shaded(cv):
    _ball(cv, DIM)
    _ball(cv, GREY, wire=True)


def g_textured(cv):
    cv.circle(0.5, 0.5, 0.36, GREY)
    for i in range(3):
        for j in range(3):
            if (i + j) % 2:
                cv.fill(((cv.x - 0.5) ** 2 + (cv.y - 0.5) ** 2 <= 0.36 ** 2)
                        & (cv.x >= 0.14 + i * 0.24) & (cv.x < 0.38 + i * 0.24)
                        & (cv.y >= 0.14 + j * 0.24) & (cv.y < 0.38 + j * 0.24), DARK)


def g_all_lights(cv):
    cv.circle(0.5, 0.42, 0.24, (0.95, 0.85, 0.40))
    cv.rect(0.40, 0.66, 0.60, 0.86, GREY)


def g_shadows(cv):
    cv.poly([(0.10, 0.86), (0.60, 0.86), (0.90, 0.62), (0.40, 0.62)], DIM)
    cv.circle(0.40, 0.38, 0.22, GREY)


def g_ssao(cv):
    cv.rect(0.12, 0.12, 0.88, 0.88, GREY)
    cv.poly([(0.12, 0.88), (0.88, 0.12), (0.88, 0.88)], DIM)
    cv.frame(0.12, 0.12, 0.88, 0.88, 0.04, DARK)


def g_motion_blur(cv):
    cv.circle(0.66, 0.5, 0.22, GREY)
    for k, y in enumerate((0.36, 0.5, 0.64)):
        cv.line(0.10 + k * 0.04, y, 0.42, y, 0.06, DIM)


def g_aa(cv):
    cv.poly([(0.14, 0.84), (0.50, 0.14), (0.86, 0.84)], GREY)
    cv.poly([(0.30, 0.84), (0.50, 0.44), (0.70, 0.84)], DARK)


def g_dof(cv):
    cv.circle(0.32, 0.50, 0.14, GREY)
    cv.circle(0.68, 0.50, 0.20, DIM)


def g_isolate(cv):
    cv.frame(0.10, 0.10, 0.90, 0.90, 0.05, DIM)
    cv.poly([(0.30, 0.38), (0.50, 0.26), (0.70, 0.38), (0.70, 0.62), (0.50, 0.74), (0.30, 0.62)], TEAL)


def g_xray(cv):
    cv.circle(0.5, 0.5, 0.36, GREY)
    cv.circle(0.5, 0.5, 0.26, DIM)
    cv.ring(0.5, 0.5, 0.36, 0.05, GREY)


def g_xray_comp(cv):
    g_xray(cv)
    for x, y in ((0.30, 0.30), (0.70, 0.30), (0.30, 0.70), (0.70, 0.70)):
        cv.circle(x, y, 0.08, TEAL)


def g_xray_joints(cv):
    g_xray(cv)
    cv.ring(0.36, 0.64, 0.09, 0.05, TEAL)
    cv.line(0.42, 0.58, 0.66, 0.34, 0.07, TEAL)


def g_exposure(cv):
    cv.circle(0.5, 0.5, 0.36, GREY)
    cv.poly([(0.5, 0.14), (0.86, 0.5), (0.5, 0.86)], DARK)


def g_gamma(cv):
    pts = [(0.14 + 0.72 * t, 0.86 - 0.72 * (t ** 0.45)) for t in [i / 20 for i in range(21)]]
    cv.polyline(pts, 0.09, GREY)


def g_color_mgmt(cv):
    for k, c in enumerate(((0.85, 0.35, 0.35), (0.40, 0.75, 0.40), BLUE)):
        a = k * 2 * math.pi / 3 - math.pi / 2
        cv.circle(0.5 + 0.17 * math.cos(a), 0.5 + 0.17 * math.sin(a), 0.22, c)


GLYPHS = {name[2:]: fn for name, fn in globals().items() if name.startswith("g_")}


# --- the toolbar (Maya 2022 order,  panel icons x 328-1068) -----

# (glyph, kind, data, label): kind "set" = panel_menus.ALLSET_OT_panel_set key, "prop" = (owner, prop) on the view,
# "run" = (operator, props) run in the view, "grey" = no Blender equivalent (the label explains it).
TOOLBAR = (
    (("cam_select", "set", "SELECT_CAMERA", "Select Camera"),
     ("cam_lock", "prop", ("space", "lock_camera"), "Lock Camera (the view moves its camera)"),
     ("cam_attr", "grey", None, "Camera Attributes"),
     ("bookmark", "grey", None, "Bookmarks"),
     ("image_plane", "run", ("allset.create", {"kind": 'IMAGE_PLANE'}), "Image Plane"),
     ("pan_zoom", "grey", None, "2D Pan/Zoom"),
     ("grease", "grey", None, "Grease Pencil")),
    (("grid", "set", "GRID", "Grid"),
     ("film_gate", "grey", None, "Film Gate"),
     ("res_gate", "grey", None, "Resolution Gate"),
     ("gate_mask", "grey", None, "Gate Mask"),
     ("field_chart", "grey", None, "Field Chart"),
     ("safe_action", "grey", None, "Safe Action"),
     ("safe_title", "grey", None, "Safe Title")),
    (("wire", "set", "SHADE_WIRE", "Wireframe"),
     ("smooth", "set", "SHADE_SMOOTH", "Smooth Shade All"),
     ("default_mat", "set", "DEFAULT_MATERIAL", "Use Default Material"),
     ("wire_on_shaded", "prop", ("overlay", "show_wireframes"), "Wireframe on Shaded"),
     ("textured", "set", "HW_TEXTURE", "Textured"),
     ("all_lights", "set", "LIGHT_ALL", "Use All Lights"),
     ("shadows", "prop", ("shading", "show_shadows"), "Shadows")),
    (("ssao", "prop", ("shading", "show_cavity"), "Screen Space Ambient Occlusion (Blender: cavity)"),
     ("motion_blur", "grey", None, "Motion Blur"),
     ("aa", "grey", None, "Multisample Anti-aliasing"),
     ("dof", "prop", ("shading", "use_dof"), "Depth of Field")),
    (("isolate", "run", ("view3d.localview", {"frame_selected": False}), "Isolate Select"),
     ("xray", "prop", ("shading", "show_xray"), "X-Ray"),
     ("xray_comp", "grey", None, "X-Ray Active Components"),
     ("xray_joints", "prop", ("overlay", "show_xray_bone"), "X-Ray Joints")),
)


def _flat(layout, on):
    sub = layout.row(align=True)
    if not on:
        sub.emboss = 'NONE'
    return sub


def _icon(name):
    return status_icons.icon("pt_" + name)


def draw_toolbar(layout, context):
    space = context.space_data
    for group in TOOLBAR:
        bar = layout.row(align=True)
        bar.ui_units_x = 0.5
        bar.label(text="", icon_value=status_icons.icon("bar"))
        row = layout.row(align=True)
        for glyph, kind, data, label in group:
            if kind == "set":
                on = bool(panel_menus.state(context, data))
                _flat(row, on).operator(panel_menus.ALLSET_OT_panel_set.bl_idname, text="", icon_value=_icon(glyph),
                                        depress=on).key = data
            elif kind == "prop":
                owner = panel_menus._owner(space, context, data[0])
                on = bool(getattr(owner, data[1]))
                _flat(row, on).prop(owner, data[1], text="", icon_value=_icon(glyph), toggle=True)
            elif kind == "run":
                op = _flat(row, False).operator(panel_menus.ALLSET_OT_panel_run.bl_idname, text="",
                                                icon_value=_icon(glyph))
                op.op = data[0]
                import json
                op.props = json.dumps(data[1])
            else:
                _flat(row, False).operator(GREY_OP, text="", icon_value=_icon(glyph)).item = f"Panel toolbar/{label}"
    # exposure / gamma fields and the view transform (Maya's colour management controls)
    vs = context.scene.view_settings
    bar = layout.row(align=True)
    bar.ui_units_x = 0.5
    bar.label(text="", icon_value=status_icons.icon("bar"))
    row = layout.row(align=True)
    row.label(text="", icon_value=_icon("exposure"))
    sub = row.row(align=True)
    sub.ui_units_x = 2.2
    sub.prop(vs, "exposure", text="")
    row.label(text="", icon_value=_icon("gamma"))
    sub = row.row(align=True)
    sub.ui_units_x = 2.2
    sub.prop(vs, "gamma", text="")
    row.label(text="", icon_value=_icon("color_mgmt"))
    sub = row.row(align=True)
    sub.ui_units_x = 6
    sub.prop(vs, "view_transform", text="")


# --- header patch ---------------------------------------------------------------------------------------

def maya_layout(context):
    """A 3D View of the Allset layout (its screen has the Maya strip)."""
    from .shelf import strip_area
    area = context.area
    return (area is not None and area.type == 'VIEW_3D' and context.screen is not None
            and strip_area(context.screen) is not None and panel_menus._enabled(context))


def _header(self, context):
    if not maya_layout(context):
        return _orig["header"](self, context)
    layout = self.layout
    row = layout.row(align=True)
    for label, idname in panel_menus.BAR:
        row.menu(idname, text=label)
    return None


def _tool_header(self, context):
    if not maya_layout(context):
        return _orig["tool_header"](self, context)
    draw_toolbar(self.layout, context)
    return None


HEADERS = (("header", "VIEW3D_HT_header", _header), ("tool_header", "VIEW3D_HT_tool_header", _tool_header))
_orig = {}


def _own_index(cls_name, funcs):
    """Index of the class's own draw among its draw functions (something may have been prepended)."""
    for i, f in enumerate(funcs):
        if getattr(f, "__qualname__", "") == f"{cls_name}.draw":
            return i
    return 0


def patch_headers():
    for key, name, fn in HEADERS:
        funcs = getattr(bpy.types, name)._dyn_ui_initialize()
        i = _own_index(name, funcs)
        if key not in _orig:
            _orig[key] = funcs[i]
        funcs[i] = fn


def unpatch_headers():
    for key, name, fn in HEADERS:
        if key in _orig:
            funcs = getattr(bpy.types, name)._dyn_ui_initialize()
            funcs[funcs.index(fn)] = _orig.pop(key)


def register():
    for name, fn in GLYPHS.items():
        status_icons.EXTRA["pt_" + name] = fn
    patch_headers()


def unregister():
    unpatch_headers()
    for name in GLYPHS:
        status_icons.EXTRA.pop("pt_" + name, None)
