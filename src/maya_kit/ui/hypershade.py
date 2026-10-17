# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Hypershade = a Shader Editor window with a "Hypershade" sidebar tab.

Maya's Hypershade (, shot render_01_win1) is a floating window: Browser
(material swatches), Create (material types), the node graph and the Property Editor. Blender's Shader Editor
is the graph; the kit adds the rest as a sidebar tab of every Shader Editor:

- Browser: the scene's materials with their previews; a click makes one the Hypershade's current material
  (the active object's slot when it has it, else this Shader Editor is pinned to it);
- Create: Maya material types, created unassigned like Maya's Create bar (fake user, so saving keeps them);
- Assign Material To Selection (Maya's swatch RMB item, ``maya_kit.assign_material``);
- Property Editor: the Attribute Editor's material sections with their map buttons.

``maya_kit.hypershade`` opens the window: Windows > Rendering Editors > Hypershade, the Status Line icon and the
hotbox's Windows menu all run it. The hotbox's Hypershade layouts keep the Shading workspace (render.md).
"""

import bpy
from bpy.props import EnumProperty, StringProperty

from ..operators import material as material_ops
from ..operators import menu_extras
from . import ae_layout

CATEGORY = "Hypershade"
NOTICE = "Hypershade: Blender Shader Editor + kit material list. Add nodes with Shift+A (Tab edits groups)."
# Maya Hypershade Create > Maya > Surface order (render_01_win1): Blinn, Lambert, Phong, Standard Surface, Surface Shader
CREATE = ('BLINN', 'LAMBERT', 'PHONG', 'STANDARD_SURFACE', 'AI_STANDARD_SURFACE', 'SURFACE')
COLUMNS = 3


def materials():
    return sorted((m for m in bpy.data.materials if not m.is_grease_pencil), key=lambda m: m.name.lower())


def current(context):
    """The Hypershade's current material: the picked one, else the active object's active material."""
    mat = bpy.data.materials.get(context.window_manager.maya_kit_hs_material)
    if mat is None and context.active_object is not None:
        mat = context.active_object.active_material
    return mat


def show(context, mat, space=None):
    """Make ``mat`` current and show it in the Shader Editor ``space``: the active object's slot when it has
    the material (the editor follows the object, unpinned), else pin the editor to it."""
    context.window_manager.maya_kit_hs_material = mat.name
    ob = context.active_object
    index = next((i for i, s in enumerate(ob.material_slots) if s.material == mat), None) if ob else None
    if space is None or space.type != 'NODE_EDITOR':
        if index is not None:
            ob.active_material_index = index
        return
    if index is not None:
        ob.active_material_index = index
        space.pin = False
    elif mat.node_tree is not None:
        space.pin = True
        space.node_tree = mat.node_tree


def _hypershade_area(context):
    return max(context.window.screen.areas, key=lambda a: a.width * a.height, default=None)


class MAYAKIT_OT_hypershade(bpy.types.Operator):
    """Hypershade: a Shader Editor window with the material browser, Create and Property Editor (sidebar tab)"""
    bl_idname = "maya_kit.hypershade"
    bl_label = "Hypershade"

    def execute(self, context):
        if context.window is None:
            return {'CANCELLED'}
        area = _hypershade_area(context)
        if area is None:
            return {'CANCELLED'}
        window = menu_extras.open_window(context, area)
        if window is None:
            self.report({'ERROR'}, "Could not open a new window")
            return {'CANCELLED'}
        target = window.screen.areas[0]
        target.ui_type = 'ShaderNodeTree'
        mat = current(context)
        if mat is not None:
            show(context, mat, target.spaces.active)
        menu_extras.sidebar_tab_later(window, CATEGORY)
        return {'FINISHED'}


class MAYAKIT_OT_hs_pick(bpy.types.Operator):
    """Show this material in the graph and the Property Editor (Maya Hypershade swatch click)"""
    bl_idname = "maya_kit.hs_pick"
    bl_label = "Pick Material"

    material: StringProperty(name="Material", options={'SKIP_SAVE'})

    def execute(self, context):
        mat = bpy.data.materials.get(self.material)
        if mat is None:
            return {'CANCELLED'}
        show(context, mat, context.space_data)
        for area in context.screen.areas if context.screen else ():
            area.tag_redraw()
        return {'FINISHED'}


class MAYAKIT_OT_hs_create(bpy.types.Operator):
    """Create a material of this type without assigning it (Maya Hypershade Create)"""
    bl_idname = "maya_kit.hs_create"
    bl_label = "Create Material"
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(items=material_ops.KIND_ITEMS, name="Material")

    def execute(self, context):
        mat = material_ops.new_material(self.kind)
        mat.use_fake_user = True    # no user yet: Blender would drop it on save, Maya keeps it
        show(context, mat, context.space_data)
        return {'FINISHED'}


def draw_browser(layout, context):
    mats = materials()
    if not mats:
        layout.label(text="No materials in the scene")
        return
    cur = current(context)
    grid = layout.grid_flow(row_major=True, columns=COLUMNS, even_columns=True, align=False)
    for mat in mats:
        col = grid.column(align=True)
        col.template_icon(icon_value=layout.icon(mat), scale=3.0)
        op = col.operator("maya_kit.hs_pick", text=mat.name, depress=(mat == cur))
        op.material = mat.name


def draw_create(layout, context):
    col = layout.column(align=True)
    for kind in CREATE:
        col.operator("maya_kit.hs_create", text=material_ops.MATERIALS[kind][1], icon='MATERIAL').kind = kind


def draw_property_editor(layout, context):
    from . import attribute_editor
    mat = current(context)
    if mat is None:
        layout.label(text="Pick a material")
        return
    head = layout.row(align=True)
    head.label(text=f"{attribute_editor.material_type(mat)}:")
    head.prop(mat, "name", text="")
    name = attribute_editor.material_type(mat)
    sections = ae_layout.BY_KIND[name][0]
    attribute_editor.draw_sections(layout, context, None, mat, sections, f"hs_{name}")


class _Panel:
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = CATEGORY

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and getattr(space, "tree_type", "") == 'ShaderNodeTree'


class MAYAKIT_PT_hs_browser(_Panel, bpy.types.Panel):
    bl_label = "Browser"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        from . import chrome
        chrome.paragraph(layout, context, NOTICE)
        draw_browser(layout, context)
        cur = current(context)
        row = layout.row()
        row.enabled = cur is not None
        op = row.operator("maya_kit.assign_material", text="Assign Material To Selection", icon='MATERIAL')
        op.material = cur.name if cur is not None else ""


class MAYAKIT_PT_hs_create(_Panel, bpy.types.Panel):
    bl_label = "Create"
    bl_order = 1

    def draw(self, context):
        draw_create(self.layout, context)


class MAYAKIT_PT_hs_property_editor(_Panel, bpy.types.Panel):
    bl_label = "Property Editor"
    bl_order = 2

    def draw(self, context):
        draw_property_editor(self.layout, context)


classes = (MAYAKIT_OT_hypershade, MAYAKIT_OT_hs_pick, MAYAKIT_OT_hs_create,
           MAYAKIT_PT_hs_browser, MAYAKIT_PT_hs_create, MAYAKIT_PT_hs_property_editor)


def register():
    bpy.types.WindowManager.maya_kit_hs_material = StringProperty(
        name="Hypershade Material", options={'SKIP_SAVE'})
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.maya_kit_hs_material
