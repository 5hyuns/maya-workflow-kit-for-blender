# SPDX-License-Identifier: GPL-3.0-or-later
"""Quad Draw, Create Polygon and Append to Polygon as kit tools.

The tools run the modals of operators/quad_draw.py and operators/poly_draw.py; their Maya Tool Settings (fields and
factory values: ) are drawn here, in Blender's tool header / Tool tab and in the kit's
Tool Settings dock (ui/tool_settings.py kinds QUAD_DRAW / CREATE_POLYGON / APPEND_POLYGON).
"""

import bpy

from . import notices
from ..operators import poly_draw, quad_draw

GREY = {
    "Quad Draw/Live Constraint": (
        "Make Live", "The kit draws on the live surface, else on every other visible mesh; no colour options"),
}

QUAD_DRAW_SHORTCUTS = (
    ("Click", "place a dot on the live surface"),
    ("Drag a dot / vertex / edge / face", "move it along the surface (Auto-weld when let go near a vertex)"),
    ("Shift+click", "fill a quad (or triangle) between the dots / border vertices around the mouse"),
    ("Shift+drag", "relax the vertices under the brush"),
    ("Ctrl+click an edge", "insert an edge loop"),
    ("Ctrl+Shift+click", "delete a dot, vertex, edge or face"),
    ("Tab+drag a border edge", "extend it by a row of quads"),
    ("Tab+drag in empty space", "draw a strip of quads"),
    ("Middle-drag", "move a vertex, edge or face"),
    ("Esc", "leave the tool"),
)
CREATE_SHORTCUTS = (
    ("Click", "place a point (drag to move it)"),
    ("Middle-drag", "move the last point"),
    ("Backspace / Delete", "remove the last point"),
    ("Enter", "complete the polygon (the tool stays)"),
    ("Esc", "drop the points; with none, leave the tool"),
)
APPEND_SHORTCUTS = (
    ("Click a border edge", "start the new face there"),
    ("Click", "place a point / add another border edge"),
    ("Backspace / Delete", "remove the last point"),
    ("Enter", "add the face (the tool stays)"),
    ("Esc", "drop the points; with none, leave the tool"),
)


def _row(layout, label):
    split = layout.split(factor=0.42, align=True)
    left = split.row()
    left.alignment = 'RIGHT'
    left.label(text=label)
    return split.row(align=True)


def _grey(layout, key, text):
    row = layout.row()
    row.enabled = False
    row.operator("allset.menu_unavailable", text=text, emboss=False).item = key


def draw_quad_draw(layout, context, header=False):
    s = poly_draw.settings(context)
    if header:
        layout.prop(s, "qd_auto_weld", text="Auto-weld")
        layout.prop(s, "qd_relax", text="")
        layout.prop(s, "qd_extend", text="")
        return
    row = _row(layout, "Auto-weld:")
    row.prop(s, "qd_auto_weld", text="")
    sub = row.row(align=True)
    sub.active = s.qd_auto_weld
    sub.prop(s, "qd_weld_px", text="")
    _row(layout, "Relax:").prop(s, "qd_relax", text="")
    _row(layout, "Extend:").prop(s, "qd_extend", text="")
    _row(layout, "Quad Strip Width:").prop(s, "qd_strip_width", text="")
    _row(layout, "").operator("allset.quad_draw_clear_dots", text="Clear Dots")


def draw_live(layout, context):
    live = getattr(context.scene, "allset_live", None)
    _row(layout, "Live surface:").label(text=live.name if live is not None else "None (other visible meshes)")
    _grey(layout, "Quad Draw/Live Constraint", "Wireframe Overlay, Mesh Color / Alpha ...")


def draw_create(layout, context, header=False):
    s = poly_draw.settings(context)
    if header:
        layout.prop(s, "cp_divisions")
        layout.prop(s, "cp_limit_points")
        return
    _row(layout, "Divisions:").prop(s, "cp_divisions", text="")
    _row(layout, "Limit points:").prop(s, "cp_limit_points", text="")
    _row(layout, "").prop(s, "cp_keep_planar")
    _row(layout, "Texture:").prop(s, "cp_texture", expand=True)


def draw_append(layout, context, header=False):
    s = poly_draw.settings(context)
    if header:
        layout.prop(s, "ap_divisions")
        layout.prop(s, "ap_limit_points")
        return
    _row(layout, "Divisions:").prop(s, "ap_divisions", text="")
    _row(layout, "Rotation angle:").prop(s, "ap_rotation_angle", text="")
    _row(layout, "Limit points:").prop(s, "ap_limit_points", text="")
    _row(layout, "").prop(s, "ap_keep_planar")
    _row(layout, "Texture:").prop(s, "ap_texture", expand=True)


def draw_shortcuts(layout, rows):
    col = layout.column(align=True)
    for key, what in rows:
        split = col.split(factor=0.42)
        split.label(text=key)
        split.label(text=what)


def _hover_items():
    items = [("allset.quad_draw_hover", {"type": 'MOUSEMOVE', "value": 'ANY', "any": True}, None)]
    for key in ('LEFT_CTRL', 'RIGHT_CTRL', 'LEFT_SHIFT', 'RIGHT_SHIFT'):
        for value in ('PRESS', 'RELEASE'):
            items.append(("allset.quad_draw_hover", {"type": key, "value": value, "any": True}, None))
    return tuple(items)


class ALLSET_TL_quad_draw(bpy.types.WorkSpaceTool):
    """Maya Quad Draw: dots on the live surface, Shift = fill / relax, Ctrl = loop,
    Ctrl+Shift = delete, Tab+drag = extend / strip. No select fallback: Maya's Quad Draw LMB doesn't select."""
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_MESH'
    bl_idname = quad_draw.TOOL
    bl_label = "Quad Draw"
    bl_description = ("Click on the live surface to place dots, Shift+click between them to fill a quad. "
                      "Drag = move, Shift+drag = relax, Ctrl+click = edge loop, Ctrl+Shift+click = delete, "
                      "Tab+drag = extend a border / quad strip (Maya Quad Draw)")
    bl_icon = "ops.mesh.polybuild_hover"
    bl_widget = None
    bl_keymap = (
        ("allset.quad_draw", {"type": 'LEFTMOUSE', "value": 'PRESS', "any": True}, None),
        ("allset.quad_draw", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, {"properties": [("middle", True)]}),
        ("allset.quad_draw_tab", {"type": 'TAB', "value": 'PRESS'}, None),
        ("allset.quad_draw_exit", {"type": 'ESC', "value": 'PRESS'}, None),
        *_hover_items(),
    )

    @staticmethod
    def draw_settings(context, layout, tool):
        draw_quad_draw(layout, context, header=context.region.type == 'TOOL_HEADER')


def _create_keymap():
    return (
        ("allset.create_polygon", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("allset.poly_tool_exit", {"type": 'ESC', "value": 'PRESS'}, None),
    )


class ALLSET_TL_create_polygon(bpy.types.WorkSpaceTool):
    """Maya Create Polygon (object mode)."""
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_idname = poly_draw.CREATE_TOOL
    bl_label = "Create Polygon"
    bl_description = ("Click to place points, Enter to make a new polygon object. Backspace removes the last point, "
                      "middle-drag moves it (Maya Create Polygon)")
    bl_icon = "ops.mesh.polybuild_hover"
    bl_widget = None
    bl_keymap = _create_keymap()

    @staticmethod
    def draw_settings(context, layout, tool):
        draw_create(layout, context, header=context.region.type == 'TOOL_HEADER')


class ALLSET_TL_create_polygon_edit(bpy.types.WorkSpaceTool):
    """Maya Create Polygon (component mode: the polygon is still a new object)."""
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_MESH'
    bl_idname = poly_draw.CREATE_TOOL
    bl_label = "Create Polygon"
    bl_description = ALLSET_TL_create_polygon.bl_description
    bl_icon = "ops.mesh.polybuild_hover"
    bl_widget = None
    bl_keymap = _create_keymap()

    @staticmethod
    def draw_settings(context, layout, tool):
        draw_create(layout, context, header=context.region.type == 'TOOL_HEADER')


class ALLSET_TL_append_polygon(bpy.types.WorkSpaceTool):
    """Maya Append to Polygon."""
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_MESH'
    bl_idname = poly_draw.APPEND_TOOL
    bl_label = "Append to Polygon"
    bl_description = ("Click a border edge of the mesh, then place points or click another border edge; Enter adds "
                      "the face (Maya Append to Polygon)")
    bl_icon = "ops.mesh.polybuild_hover"
    bl_widget = None
    bl_keymap = (
        ("allset.append_polygon", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("allset.poly_tool_exit", {"type": 'ESC', "value": 'PRESS'}, None),
    )

    @staticmethod
    def draw_settings(context, layout, tool):
        draw_append(layout, context, header=context.region.type == 'TOOL_HEADER')


TOOLS = (ALLSET_TL_quad_draw, ALLSET_TL_create_polygon, ALLSET_TL_create_polygon_edit, ALLSET_TL_append_polygon)


def register():
    notices.PANEL_NOTICES.update(GREY)
    for tool in TOOLS:
        after = {"builtin.poly_build"} if tool.bl_context_mode == 'EDIT_MESH' else None
        bpy.utils.register_tool(tool, after=after)


def unregister():
    for tool in reversed(TOOLS):
        bpy.utils.unregister_tool(tool)
    for key in GREY:
        notices.PANEL_NOTICES.pop(key, None)
