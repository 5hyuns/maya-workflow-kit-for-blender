# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya 4/5/6/7 viewport display modes.

 (RTC DisplayWireframe, DisplayShaded,
DisplayShadedAndTextured, DisplayLight). Maya applies them to the panel under
the pointer (interaction.md:33); bound in the "3D View" keymap, Blender gives
us that area as ``context.space_data``.
"""

import bpy

MODES = (
    ("WIREFRAME", "Wireframe", "Maya 4: wireframe"),
    ("SHADED", "Shaded", "Maya 5: smooth shaded, no textures"),
    ("TEXTURED", "Shaded + Textured", "Maya 6: shaded and textured"),
    ("LIGHTS", "All Lights", "Maya 7: lit by the scene's lights (Material Preview)"),
)


def apply_display_mode(shading, mode):
    """Set a View3DShading to the Blender look closest to a Maya display mode."""
    if mode == "WIREFRAME":
        shading.type = 'WIREFRAME'
    elif mode == "SHADED":
        shading.type = 'SOLID'
        shading.color_type = 'MATERIAL'
    elif mode == "TEXTURED":
        shading.type = 'SOLID'
        shading.color_type = 'TEXTURE'
    elif mode == "LIGHTS":
        # Maya "Use All Lights": no exact Blender twin. Material Preview with
        # scene lights is the closest real-time look.
        shading.type = 'MATERIAL'
        shading.use_scene_lights = True
        shading.use_scene_world = False
    else:
        raise ValueError(mode)


class MAYAKIT_OT_display_mode(bpy.types.Operator):
    """Switch the 3D view's display like Maya's 4/5/6/7 keys"""
    bl_idname = "maya_kit.display_mode"
    bl_label = "Maya Display Mode"
    bl_options = {'REGISTER'}

    mode: bpy.props.EnumProperty(items=MODES, name="Mode", default="SHADED")

    @classmethod
    def poll(cls, context):
        return context.space_data is not None and context.space_data.type == 'VIEW_3D'

    def execute(self, context):
        apply_display_mode(context.space_data.shading, self.mode)
        return {'FINISHED'}


# --- 1/2/3 smooth mesh preview ------------------------------------------------
#  1 = no smoothing, 2 = cage + smooth,
# 3 = smooth mesh preview; per selected shape, geometry unchanged.
# Blender form: a Subsurf modifier's viewport visibility.

PREVIEW_MOD_NAME = "Maya Smooth Preview"
_WIRE_FLAG = "maya_kit_preview_wire"  # object custom prop: we turned show_wire on


def preview_modifier(ob, create):
    """The object's first Subsurf modifier, or a new preview one if ``create``."""
    for mod in ob.modifiers:
        if mod.type == 'SUBSURF':
            return mod
    if not create:
        return None
    mod = ob.modifiers.new(PREVIEW_MOD_NAME, 'SUBSURF')
    mod.levels = 2          # Maya smooth preview divisions default 
    mod.render_levels = 2
    mod.show_render = False  # preview only: renders unchanged
    mod.show_in_editmode = True
    mod.show_on_cage = False
    return mod


def set_smooth_preview(ob, level):
    mod = preview_modifier(ob, create=level > 1)
    if mod is not None:
        mod.show_viewport = level > 1
    if level == 2:
        if not ob.show_wire:
            ob.show_wire = True
            ob[_WIRE_FLAG] = True
    elif ob.get(_WIRE_FLAG):
        ob.show_wire = False
        del ob[_WIRE_FLAG]


class MAYAKIT_OT_smooth_preview(bpy.types.Operator):
    """Maya 1/2/3: smooth mesh preview off / cage + smooth / smooth"""
    bl_idname = "maya_kit.smooth_preview"
    bl_label = "Smooth Mesh Preview"
    bl_options = {'REGISTER', 'UNDO'}

    level: bpy.props.IntProperty(name="Level", min=1, max=3, default=3)

    @classmethod
    def poll(cls, context):
        return any(ob.type == 'MESH' for ob in cls._targets(context))

    @staticmethod
    def _targets(context):
        if context.mode == 'EDIT_MESH':
            return list(context.objects_in_mode)
        return list(context.selected_objects)

    def execute(self, context):
        for ob in self._targets(context):
            if ob.type == 'MESH':
                set_smooth_preview(ob, self.level)
        return {'FINISHED'}


# --- F7/F9/F10/F11 component modes ----------------------------------------------
#  (F9 vertex, F10 edge, F11 face, F7 multi).

COMPONENTS = (
    ("VERT", "Vertex", "Maya F9"),
    ("EDGE", "Edge", "Maya F10"),
    ("FACE", "Face", "Maya F11"),
    ("MULTI", "Multi-Component", "Maya F7: vertices, edges and faces together"),
)
_SELECT_MODE = {"VERT": (True, False, False), "EDGE": (False, True, False),
                "FACE": (False, False, True), "MULTI": (True, True, True)}


class MAYAKIT_OT_component_mode(bpy.types.Operator):
    """Enter a mesh component mode (Maya F7/F9/F10/F11)"""
    bl_idname = "maya_kit.component_mode"
    bl_label = "Component Mode"
    bl_options = {'REGISTER', 'UNDO'}

    type: bpy.props.EnumProperty(items=COMPONENTS, name="Component")

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and ob.type == 'MESH'

    def execute(self, context):
        if context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')
        context.scene.tool_settings.mesh_select_mode = _SELECT_MODE[self.type]
        return {'FINISHED'}


classes = (MAYAKIT_OT_display_mode, MAYAKIT_OT_smooth_preview, MAYAKIT_OT_component_mode)
