# SPDX-License-Identifier: GPL-3.0-or-later
"""Display > Polygons, the two items that are not check boxes (step 291).

Maya sets polygon display on the selected meshes (polyOptions); Blender keeps it on each 3D View's overlays, drawn on
the meshes in edit mode. Both act on the 3D View the menu reads (``ui/status_line.view3d_space``).

- Normals Size...: Maya's small window with the normal length slider (polyOptions -sizeNormal) = the overlay's
  Normal Size (``View3DOverlay.normals_length``, Blender units).
- Reset Display: Maya puts the polygon display options back to their defaults = the overlays this menu sets, back to
  Blender's factory values (measured in Blender 5.2's factory startup).
"""

import bpy
from bpy.props import FloatProperty

from .. import results

# Blender 5.2 factory startup, Layout 3D View: (overlay or shading, property, value)
FACTORY = (
    ("overlay", "show_face_normals", False),
    ("overlay", "show_vertex_normals", False),
    ("overlay", "show_split_normals", False),
    ("overlay", "normals_length", 0.1),
    ("overlay", "show_edge_sharp", True),
    ("overlay", "show_edge_crease", True),
    ("overlay", "show_edge_seams", True),
    ("overlay", "show_face_center", False),
    ("shading", "show_backface_culling", False),
)


def _space(op, context):
    from ..ui.status_line import view3d_space
    space = view3d_space(context)
    if space is None:
        op.report({'WARNING'}, "No 3D View to display polygons in")
    return space


class ALLSET_OT_normals_size(bpy.types.Operator):
    """Maya Display > Polygons > Normals Size: the length of the face and vertex normals drawn in the 3D View"""
    bl_idname = "allset.normals_size"
    bl_label = "Normals Size"

    size: FloatProperty(name="Normals Size", default=0.1, min=0.00001, max=2.0, step=1, precision=3)

    def invoke(self, context, event):
        space = _space(self, context)
        if space is None:
            return {'CANCELLED'}
        self.size = space.overlay.normals_length
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        self.layout.prop(self, "size")
        self.layout.label(text="Blender draws normals on meshes in edit mode.")

    def execute(self, context):
        space = _space(self, context)
        if space is None:
            return {'CANCELLED'}
        space.overlay.normals_length = self.size
        results.result(self, f"Normals Size {self.size:g}")
        return {'FINISHED'}


class ALLSET_OT_poly_display_reset(bpy.types.Operator):
    """Maya Display > Polygons > Reset Display: normals, edge and face display back to their defaults"""
    bl_idname = "allset.poly_display_reset"
    bl_label = "Reset Display"

    def execute(self, context):
        space = _space(self, context)
        if space is None:
            return {'CANCELLED'}
        for owner, prop, value in FACTORY:
            setattr(getattr(space, owner), prop, value)
        results.result(self, "Polygon display reset")
        return {'FINISHED'}


classes = (ALLSET_OT_normals_size, ALLSET_OT_poly_display_reset)
