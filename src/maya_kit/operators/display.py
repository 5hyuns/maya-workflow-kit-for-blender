# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya 4/5/6/7 viewport display modes.

research/maya/interaction.md:174-177 (RTC DisplayWireframe, DisplayShaded,
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
        # scene lights is the closest real-time look (docs/steps/step_2.md).
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


classes = (MAYAKIT_OT_display_mode,)
