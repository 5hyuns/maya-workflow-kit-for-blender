# SPDX-License-Identifier: GPL-3.0-or-later
"""Target Weld and Crease Tool as Blender tools, and Maya's Multi-Cut Tool Settings (docs/steps/step_64.md 「계획」).

- Target Weld (Maya Mesh Tools > Target Weld, research/maya/workflows/shots/modeling_08_win1.png): LMB press on a
  vertex / edge starts ``allset.target_weld``; a press away from them falls back to the select tool.
- Crease Tool (Mesh Tools > Crease Tool): MMB drag = ``allset.crease_drag``; LMB selects (fallback).
- Multi-Cut stays Blender's knife (``builtin.knife``); its Ctrl / Shift keys are keymap patches
  (keymap/maya_patches.py patch_multi_cut). Its Maya settings (shots/modeling_06_win1.png) are drawn in the
  Tool Settings panel in front of Blender's knife settings.
Settings live in ``Scene.allset_mesh_tools`` (operators/mesh_tools.py).
"""

import bpy

from . import notices
from ..operators import cut_sew, mesh_tools

# Greyed Maya settings: (notice key, label) -> (substitute, one line)
GREY = {
    "Multi-Cut/Smoothing Angle": (
        "Mark Sharp", "Blender's cuts don't harden edges by angle: mark them with Mesh Display > Harden Edge."),
    "Multi-Cut/Edge Flow": (
        "Edge Slide", "Blender has no edge flow for new loops: slide them with G G (Edge Slide)."),
    "Multi-Cut/Subdivisions": (
        "Subdivide", "New edges have no extra divisions: Edit Mesh > Add Divisions afterwards."),
    "Multi-Cut/Slice Tool": (
        "Bisect tool", "Blender slices with the Bisect tool (Knife group in the toolbar), not inside the knife."),
    "Crease Tool/Extend to creased components": (
        "Select Similar", "Select the creased edges with Select > Select Similar > Crease first."),
}


def _grey(layout, key, text):
    row = layout.row()
    row.enabled = False
    row.operator("allset.menu_unavailable", text=text, emboss=False).item = key


class ALLSET_TL_target_weld(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_MESH'
    bl_idname = mesh_tools.TARGET_WELD_TOOL
    bl_label = "Target Weld"
    bl_description = ("Drag a vertex or edge onto the target to merge them (Maya Target Weld). "
                      "A selected vertex takes every selected vertex with it")
    bl_icon = "ops.transform.vert_slide"
    bl_widget = None
    bl_options = {'KEYMAP_FALLBACK'}
    bl_keymap = (("allset.target_weld", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),)

    @staticmethod
    def draw_settings(context, layout, tool):
        s = mesh_tools.settings(context)
        layout.prop(s, "weld_merge_to", expand=True)
        layout.prop(s, "weld_preserve_uvs")


class ALLSET_TL_crease(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_MESH'
    bl_idname = mesh_tools.CREASE_TOOL
    bl_label = "Crease Tool"
    bl_description = ("Crease the selected edges (vertices in vertex mode): middle-drag left = less, "
                      "right = more (Maya Crease Tool)")
    bl_icon = "ops.transform.shrink_fatten"
    bl_widget = None
    bl_options = {'KEYMAP_FALLBACK'}
    bl_keymap = (("allset.crease_drag", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),)

    @staticmethod
    def draw_settings(context, layout, tool):
        layout.prop(mesh_tools.settings(context), "crease_mode", expand=True)
        if context.region.type != 'TOOL_HEADER':
            _grey(layout, "Crease Tool/Extend to creased components", "Extend to creased components")


class ALLSET_TL_cut_sew(bpy.types.WorkSpaceTool):
    """Maya 3D Cut and Sew UV Tool (docs/steps/step_79.md): drag = cut, Ctrl+drag = sew, Shift+drag = select;
    x / s / d = Cut / Sew / Unfold + Layout (hotkeySetup.mel:539-541, tool context polyCutUV)."""
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_MESH'
    bl_idname = cut_sew.TOOL
    bl_label = "3D Cut and Sew UV Tool"
    bl_description = ("Drag along edges to cut the UVs there, Ctrl+drag to sew them, Shift+drag to select edges. "
                      "x = Cut, s = Sew, d = Unfold and Layout (Maya 3D Cut and Sew UV Tool)")
    bl_icon = "ops.mesh.knife_tool"
    bl_widget = None
    bl_options = {'KEYMAP_FALLBACK'}
    bl_keymap = (
        ("allset.cut_sew_stroke", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": [("action", 'CUT')]}),
        ("allset.cut_sew_stroke", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True},
         {"properties": [("action", 'SEW')]}),
        ("allset.cut_sew_stroke", {"type": 'LEFTMOUSE', "value": 'PRESS', "shift": True},
         {"properties": [("action", 'SELECT')]}),
        ("allset.uv_cut", {"type": 'X', "value": 'PRESS'}, {"properties": [("mesh_select", True)]}),
        ("allset.uv_sew", {"type": 'S', "value": 'PRESS'}, {"properties": [("mesh_select", True)]}),
        ("allset.uv_unfold_layout", {"type": 'D', "value": 'PRESS'}, None),
    )

    @staticmethod
    def draw_settings(context, layout, tool):
        layout.label(text="Drag: Cut  ·  Ctrl+drag: Sew  ·  Shift+drag: Select", icon='INFO')
        row = layout.row(align=True)
        row.operator("allset.uv_cut", text="Cut (x)").mesh_select = True
        row.operator("allset.uv_sew", text="Sew (s)").mesh_select = True
        row.operator("allset.uv_unfold_layout", text="Unfold + Layout (d)")


TOOLS = (ALLSET_TL_target_weld, ALLSET_TL_crease, ALLSET_TL_cut_sew)


def active_tool_id(context):
    try:
        tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
    except (AttributeError, TypeError, RuntimeError):
        return ""
    return tool.idname if tool is not None else ""


def draw_multicut_settings(self, context):
    """Maya's Multi-Cut Tool Settings (shots/modeling_06_win1.png) above Blender's knife settings."""
    if active_tool_id(context) != mesh_tools.MULTI_CUT_TOOL:
        return
    layout = self.layout
    layout.separator()
    layout.label(text="Multi-Cut")
    layout.prop(mesh_tools.settings(context), "snap_step", slider=True)
    layout.label(text="Shift: snap the cut to the step, Ctrl+click: edge loop", icon='INFO')
    box = layout.box()
    box.label(text="Cut / Insert Edge Loop Tool")
    for name in ("Smoothing Angle", "Edge Flow", "Subdivisions"):
        _grey(box, f"Multi-Cut/{name}", name)
    _grey(layout, "Multi-Cut/Slice Tool", "Slice Tool")


def register():
    notices.PANEL_NOTICES.update(GREY)
    for tool in TOOLS:
        bpy.utils.register_tool(tool, after={"builtin.knife"})
    bpy.types.VIEW3D_PT_active_tool.append(draw_multicut_settings)


def unregister():
    bpy.types.VIEW3D_PT_active_tool.remove(draw_multicut_settings)
    for tool in reversed(TOOLS):
        bpy.utils.unregister_tool(tool)
    for key in GREY:
        notices.PANEL_NOTICES.pop(key, None)
