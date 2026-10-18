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
# 3 = smooth mesh preview; per selected shape, geometry unchanged. Blender form:
# the kit's own preview Subsurf (never the user's Subsurf, step 15) plus a
# "Set Shade Smooth" geometry-nodes modifier right before it, so the preview looks
# smooth without touching the mesh's sharp_face data. The Subsurf stays last in the
# stack, which keeps Blender's GPU subdivision. Both are display only: not history
# (operators/history.py keeps them), hidden from INPUTS. 

PREVIEW_MOD_NAME = "Maya Smooth Preview"
PREVIEW_SHADE_NAME = "Maya Smooth Preview Shading"
SHADE_GROUP_NAME = ".MayaKit Smooth Preview Shading"  # leading dot: hidden in node menus
PREVIEW_NAMES = (PREVIEW_MOD_NAME, PREVIEW_SHADE_NAME)
_WIRE_FLAG = "maya_kit_preview_wire"  # object custom prop: we turned show_wire on


def is_preview(mod):
    """True for the kit's smooth-preview modifiers (display only, not Maya history)."""
    return mod.name in PREVIEW_NAMES


def _shade_group():
    ng = bpy.data.node_groups.get(SHADE_GROUP_NAME)
    if ng is not None and ng.bl_idname == 'GeometryNodeTree':
        return ng
    ng = bpy.data.node_groups.new(SHADE_GROUP_NAME, 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gin, gout = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
    smooth = ng.nodes.new("GeometryNodeSetShadeSmooth")   # domain FACE, Shade Smooth = True
    smooth.inputs["Shade Smooth"].default_value = True
    gin.location, smooth.location, gout.location = (-250, 0), (0, 0), (250, 0)
    ng.links.new(gin.outputs[0], smooth.inputs["Geometry"])
    ng.links.new(smooth.outputs[0], gout.inputs[0])
    return ng


def _ensure_shade_modifier(ob, sub):
    """The shading modifier, placed directly before the preview Subsurf ``sub``."""
    shade = ob.modifiers.get(PREVIEW_SHADE_NAME)
    if shade is None:
        shade = ob.modifiers.new(PREVIEW_SHADE_NAME, 'NODES')
        shade.node_group = _shade_group()
        shade.show_render = False
        shade.show_in_editmode = True
        shade.show_on_cage = False
        shade.show_expanded = False
    want = list(ob.modifiers).index(sub)
    if list(ob.modifiers).index(shade) != want - 1:
        # ObjectModifiers has no move() in 4.5; the operator only needs the object.
        with bpy.context.temp_override(object=ob):
            bpy.ops.object.modifier_move_to_index(modifier=shade.name, index=want)
    return shade


def preview_modifier(ob, create):
    """The object's preview Subsurf (never a user Subsurf), or a new one if ``create``."""
    mod = ob.modifiers.get(PREVIEW_MOD_NAME)
    if mod is not None and mod.type == 'SUBSURF':
        if create:
            _ensure_shade_modifier(ob, mod)
        return mod
    if not create:
        return None
    mod = ob.modifiers.new(PREVIEW_MOD_NAME, 'SUBSURF')
    mod.levels = 2          # Maya smooth preview divisions default 
    mod.render_levels = 2
    mod.show_render = False  # preview only: renders unchanged
    mod.show_in_editmode = True
    mod.show_on_cage = False
    _ensure_shade_modifier(ob, mod)
    return mod


def set_smooth_preview(ob, level):
    mod = preview_modifier(ob, create=level > 1)
    if mod is not None:
        mod.show_viewport = level > 1
        shade = ob.modifiers.get(PREVIEW_SHADE_NAME)
        if shade is not None:
            shade.show_viewport = level > 1
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


SMOOTH_LEVELS = (0, 4)   # preview Subsurf levels kept in this range [delegated]


def change_smoothing_level(ob, delta):
    """Maya PgUp / PgDn (changeSmoothingLevel, Maya-679): the smooth preview's
    division level. An object without a preview gets a hidden one that keeps the level
    (Maya's smoothLevel shows only in 3 mode too). Returns the new level."""
    mod = preview_modifier(ob, create=False)
    if mod is None:
        mod = preview_modifier(ob, create=True)
        set_smooth_preview(ob, 1)      # hidden until 3
    lo, hi = SMOOTH_LEVELS
    mod.levels = max(lo, min(hi, mod.levels + delta))
    return mod.levels


class MAYAKIT_OT_smooth_level(bpy.types.Operator):
    """Raise or lower the smooth preview level of the selection (Maya PgUp / PgDn)"""
    bl_idname = "maya_kit.smooth_level"
    bl_label = "Smoothing Level"
    bl_options = {'REGISTER', 'UNDO'}

    delta: bpy.props.IntProperty(name="Delta", default=1, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return MAYAKIT_OT_smooth_preview.poll(context)

    def execute(self, context):
        levels = [change_smoothing_level(ob, self.delta)
                  for ob in MAYAKIT_OT_smooth_preview._targets(context) if ob.type == 'MESH']
        self.report({'INFO'}, f"Smooth preview level {', '.join(map(str, sorted(set(levels))))}")
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


# Shift+Q marking menu check boxes (doSelectComponentMM, Maya-160): Maya pick-mask
# types that Blender has = the mesh select modes.
MASK_KINDS = (("VERT", "Poly Vertices", ""), ("EDGE", "Poly Edges", ""), ("FACE", "Faces", ""),
              ("ALL", "All Components On", ""))
_MASK_INDEX = {"VERT": 0, "EDGE": 1, "FACE": 2}


def toggled_mask(mask, kind):
    """Mesh select mode after toggling ``kind`` (Maya check box); Blender needs at least one mode on."""
    if kind == "ALL":
        return (True, True, True)
    new = list(mask)
    i = _MASK_INDEX[kind]
    new[i] = not new[i]
    return tuple(new) if any(new) else tuple(mask)


class MAYAKIT_OT_component_mask(bpy.types.Operator):
    """Toggle a component type in the pick mask (Maya Shift+Q marking menu)"""
    bl_idname = "maya_kit.component_mask"
    bl_label = "Component Pick Mask"
    bl_options = {'REGISTER', 'UNDO'}

    kind: bpy.props.EnumProperty(items=MASK_KINDS, name="Kind")

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and ob.type == 'MESH'

    def execute(self, context):
        ts = context.scene.tool_settings
        if context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')
        ts.mesh_select_mode = toggled_mask(tuple(ts.mesh_select_mode), self.kind)
        return {'FINISHED'}


classes = (MAYAKIT_OT_display_mode, MAYAKIT_OT_smooth_preview, MAYAKIT_OT_smooth_level,
           MAYAKIT_OT_component_mode, MAYAKIT_OT_component_mask)
