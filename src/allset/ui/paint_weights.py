# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Paint Skin Weights tool settings: the Influences list and paint operation, in the dock while weight painting.

 (Tool Settings: Influences list, lock, Add / Replace / Smooth / Scale, Value,
Flood), :74 (kit before: the list was only in Properties > Data), design  「계획」 3. Influences =
the vertex groups named after the skeleton's joints (operators/skin.influences); clicking one = the joint painted.
"""

import bpy

# Maya paint operation -> Blender brush blend (Smooth = the Blur tool)
OPERATIONS = (("MIX", "Replace"), ("ADD", "Add"), ("MUL", "Scale"))
# The Flood button: Blender's fill + Maya Interactive normalization (operators/skin.py, step 129)
FLOOD_OP = "allset.flood_weights"


class ALLSET_UL_influences(bpy.types.UIList):
    """Maya Paint Skin Weights influence list: joints, with their lock"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0):
        row = layout.row(align=True)
        row.label(text=item.name, icon='BONE_DATA')
        row.prop(item, "lock_weight", text="", emboss=False,
                 icon='LOCKED' if item.lock_weight else 'UNLOCKED')

    def filter_items(self, context, data, propname):
        return influence_filter(data, self.bitflag_filter_item)


def influence_filter(mesh, flag):
    """UIList (flags, order): only the joints' groups, sorted by name."""
    from ..operators import skin
    keep = {vg.name for vg in skin.influences(mesh)}
    groups = mesh.vertex_groups
    flags = [flag if vg.name in keep else 0 for vg in groups]
    order = sorted(range(len(groups)), key=lambda i: groups[i].name)
    return flags, [order.index(i) for i in range(len(groups))]


def active(context):
    ob = context.active_object
    return context.mode == 'PAINT_WEIGHT' and ob is not None and ob.type == 'MESH'


def draw(layout, context):
    """Maya Paint Skin Weights tool settings, at the top of the dock while weight painting (a separate header-less
    sidebar panel would sort below the Channel Box / Layer Editor, step 50)."""
    ob = context.active_object
    box = layout.box()
    box.label(text="Paint Skin Weights Tool")
    box.label(text="Influences")
    box.template_list("ALLSET_UL_influences", "", ob, "vertex_groups", ob.vertex_groups, "active_index", rows=6)
    brush = context.tool_settings.weight_paint.brush
    box.label(text="Paint operation")
    row = box.row(align=True)
    if brush is not None:
        for blend, label in OPERATIONS:
            row.prop_enum(brush, "blend", blend, text=label)
    row.operator("wm.tool_set_by_id", text="Smooth").name = "builtin_brush.Blur"
    if brush is not None:
        from bl_ui.properties_paint_common import UnifiedPaintPanel
        col = box.column(align=True)
        UnifiedPaintPanel.prop_unified(col, context, brush, "weight", unified_name="use_unified_weight",
                                       text="Value", slider=True)
        UnifiedPaintPanel.prop_unified(col, context, brush, "strength", unified_name="use_unified_strength",
                                       text="Opacity", slider=True)
    box.prop(context.tool_settings, "use_auto_normalize", text="Normalize Weights (Interactive)")
    box.operator(FLOOD_OP, text="Flood")
    note = box.row()
    note.active = False
    note.label(text="Ctrl+LMB a joint to paint it")


classes = (ALLSET_UL_influences,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
