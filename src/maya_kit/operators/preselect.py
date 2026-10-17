# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya pre-selection highlight in mesh edit mode.

Maya highlights the component under the mouse before you click
(``preSelectHilite true``, , defaults.json:96).
Blender 4.5 only has this inside a few tools (Poly Build, Loop Cut); its C gizmo
type ``GIZMO_GT_mesh_preselect_elem_3d`` (element nearest to the mouse) can be
used from a Python gizmo group:

- The group keeps Blender's default gizmo keymap: with an empty custom keymap
  the gizmo is never hovered (checked). Clicks still reach the select tool
  (the gizmo has no tweak of its own; GUI test).
- Only while a select tool is active: 3D gizmos tested by ``test_select`` win
  the hover over the transform manipulator's handles, so with Move/Rotate/Scale
  the arrows near a vertex would stop working (delegated).
- Only in vertex select mode: the gizmo ignores the select mode and still
  lights the nearest vertex in edge/face mode (GUI test), which would point at
  the wrong component (delegated; edge/face highlight =  남은 것).
"""

import bpy

MODES = {'EDIT_MESH'}
GIZMO = "GIZMO_GT_mesh_preselect_elem_3d"

_last = []   # the live group (tests read its gizmo)


def _enabled(context):
    from .. import preferences
    try:
        if not preferences.get().preselect_highlight:
            return False
    except KeyError:
        return False
    if context.mode not in MODES or tuple(context.tool_settings.mesh_select_mode) != (True, False, False):
        return False
    tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
    # Target Weld (step 64): Maya lights the vertex you are about to drag
    return tool is not None and (tool.idname.startswith("builtin.select") or tool.idname == "maya_kit.target_weld_tool")


def gizmo():
    """The pre-selection gizmo of the last set-up group, or None."""
    try:
        return _last[0].gz if _last else None
    except ReferenceError:
        return None


class MAYAKIT_GGT_preselect(bpy.types.GizmoGroup):
    bl_idname = "MAYAKIT_GGT_preselect"
    bl_label = "Maya Pre-selection Highlight"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SELECT'}

    @classmethod
    def poll(cls, context):
        return _enabled(context)

    def setup(self, context):
        self.gz = self.gizmos.new(GIZMO)
        # Maya preSelectHilite = red ( viewport.preselect_hilite_component)
        self.gz.color = self.gz.color_highlight = (1.0, 0.0, 0.0)
        self.gz.alpha = self.gz.alpha_highlight = 1.0
        _last[:] = [self]


classes = (MAYAKIT_GGT_preselect,)


def clear():
    _last.clear()
