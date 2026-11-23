# SPDX-License-Identifier: GPL-3.0-or-later
"""UV Editor > Tools > Unfold, Optimize, Cut, Sew, Pin, Smear and Smudge as UV Editor tools, like Maya's UV brushes,
and Tools > Lattice (operators/uv_lattice.py).

Each is a Blender tool of the UV Editor (edit mode): LMB drag = the brush stroke (operators/uv_brush.py), Ctrl+drag =
its other way (Pin unpins, Sew cuts; the Cut tool does nothing with Ctrl or Shift), B + LMB drag = brush size, M + LMB drag = strength,
MMB drag left / right = size and up / down = strength (operators/uv_brush.ALLSET_OT_uv_brush_mmb); the circle follows
the mouse. The Tools menu items make them active; Q / W / E / R leave them. Their settings show in the tool
header and the sidebar's Tool tab, with Maya's labels and start values.
"""

import bpy

from ..operators import uv_brush
from ..keymap.ic_data import platform_tool


def _keymap(mode):
    shift = ((("allset.uv_brush_stroke", {"type": 'LEFTMOUSE', "value": 'PRESS', "shift": True},
               {"properties": [("mode", mode), ("invert", True)]}),) if mode == "CUT" else ())  # does nothing
    # Smudge's Middle mouse initiates: the stroke starts on the middle mouse (otherwise it passes the press on)
    middle = ((("allset.uv_brush_stroke", {"type": 'MIDDLEMOUSE', "value": 'PRESS'},
                {"properties": [("mode", mode), ("middle", True)]}),) if mode == "SMUDGE" else ())
    return (
        ("allset.uv_brush_stroke", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": [("mode", mode)]}),
        ("allset.uv_brush_stroke", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True},
         {"properties": [("mode", mode), ("invert", True)]}),
        *shift,
        *middle,
        ("allset.uv_brush_mmb", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),
        ("allset.tap_hold", {"type": 'B', "value": 'PRESS'}, {"properties": [("binding", "uv_brush_size")]}),
        ("allset.tap_hold", {"type": 'M', "value": 'PRESS'}, {"properties": [("binding", "uv_brush_strength")]}),
        ("allset.uv_brush_hover", {"type": 'MOUSEMOVE', "value": 'ANY', "any": True}, None),
    )


def _relax_settings(layout, s, mode, header):
    layout.prop(s, "relax_size", slider=not header)
    layout.prop(s, "relax_strength", slider=not header)
    row = layout.row()
    row.enabled = mode == "OPTIMIZE"         # Maya greys Surface Angle in Unfold mode
    row.prop(s, "surfangle", slider=not header)


def _sculpt_settings(layout, s, size, strength, header):
    layout.prop(s, size, slider=not header)
    layout.prop(s, strength, slider=not header)
    if not header:
        layout.prop(s, "show_ring")


class _UVBrushTool(bpy.types.WorkSpaceTool):
    bl_space_type = 'IMAGE_EDITOR'
    bl_context_mode = 'UV'
    bl_widget = None
    mode = ""

    @classmethod
    def settings_for(cls, context, layout, header):
        s = uv_brush.settings(context)
        m = cls.mode
        if m in {"UNFOLD", "OPTIMIZE"}:
            _relax_settings(layout, s, m, header)
        elif m in {"CUT", "SEW"}:
            if m == "CUT":
                layout.prop(s, "cut_sensitivity", slider=not header)
            else:
                layout.prop(s, "sew_size", slider=not header)
        elif m == "PIN":
            _sculpt_settings(layout, s, "pin_size", "pin_strength", header)
            if not header:
                row = layout.row(align=True)
                row.operator("allset.uv_unpin_all", text="Unpin All")
                row.operator("allset.uv_invert_pin", text="Invert Pin")
        elif m == "SMEAR":
            _sculpt_settings(layout, s, "smear_size", "smear_strength", header)
        elif m == "SMUDGE":
            layout.prop(s, "smudge_effect", text="" if header else None)
            layout.prop(s, "smudge_falloff", text="" if header else None)
            layout.prop(s, "smudge_size", slider=not header)
            row = layout.row()
            row.enabled = s.smudge_effect == 'SMUDGE'     # Maya greys Pressure for the Fixed effect
            row.prop(s, "smudge_pressure", slider=not header)
            layout.prop(s, "smudge_middle")


def _tool(mode, label, icon, description):
    def draw_settings(context, layout, tool):
        cls.settings_for(context, layout, context.region.type == 'TOOL_HEADER')

    cls = type(f"ALLSET_TL_uv_brush_{mode.lower()}", (_UVBrushTool,), {
        "bl_idname": uv_brush.TOOL_IDS[mode], "bl_label": label, "bl_icon": icon, "bl_description": description,
        "bl_keymap": _keymap(mode), "mode": mode, "draw_settings": staticmethod(draw_settings)})
    return cls


TOOLS = (
    _tool("OPTIMIZE", "Optimize", "ops.mesh.vertices_smooth",
          "Drag to untangle and relax the spacing between the UVs under the brush (Maya Optimize UV Tool). "
          "b + drag = size, m + drag = strength"),
    _tool("UNFOLD", "Unfold", "brush.uv_sculpt.relax",
          "Drag to unwrap the UVs under the brush against the surface (Maya Unfold UV Tool). "
          "b + drag = size, m + drag = strength"),
    _tool("CUT", "Cut", "ops.mesh.rip_edge",
          "Drag along edges to split the UVs there (Maya Cut UV Tool)"),
    _tool("PIN", "Pin", "ops.generic.select_paint",
          "Drag to pin the UVs under the brush so other UV tools leave them (Maya Pin UV Tool). Ctrl+drag unpins. "
          "b + drag = size"),
    _tool("SEW", "Sew", "ops.transform.edge_slide",
          "Drag along shell borders to weld the UVs together (Maya Sew UV Tool). Ctrl+drag cuts. b + drag = size"),
    _tool("SMEAR", "Smear", "ops.gpencil.sculpt_smear",
          "Drag to push the UVs under the brush along the stroke (Maya Smear UV Tool). "
          "b + drag = size, m + drag = strength"),
    _tool("SMUDGE", "Smudge", "brush.paint_texture.smear",
          "Drag to pull the selected UVs in the direction of the stroke (Maya Smudge UV Tool). "
          "b + drag = size"),
)


class ALLSET_TL_uv_lattice(bpy.types.WorkSpaceTool):
    """Maya Lattice UV Tool: a lattice around the selected UVs; drag its points to bend them."""
    bl_space_type = 'IMAGE_EDITOR'
    bl_context_mode = 'UV'
    bl_idname = "allset.uv_lattice"
    bl_label = "Lattice"
    bl_description = ("Drag the points of the lattice around the selected UVs to bend them (Maya Lattice UV Tool). "
                      "Columns / Rows set the lattice")
    bl_icon = "ops.transform.shear"
    bl_widget = None
    bl_keymap = (
        ("allset.uv_lattice_drag", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("allset.uv_lattice_hover", {"type": 'MOUSEMOVE', "value": 'ANY', "any": True}, None),
    )

    @staticmethod
    def draw_settings(context, layout, tool):
        s = uv_brush.settings(context)
        header = context.region.type == 'TOOL_HEADER'
        layout.prop(s, "lattice_columns", slider=not header)
        layout.prop(s, "lattice_rows", slider=not header)


TOOLS = (*TOOLS, ALLSET_TL_uv_lattice)


def register():
    for k, tool in enumerate(TOOLS):        # at the end of the UV Editor toolbar, after a separator
        bpy.utils.register_tool(platform_tool(tool), separator=k == 0)


def unregister():
    for tool in reversed(TOOLS):
        bpy.utils.unregister_tool(tool)
