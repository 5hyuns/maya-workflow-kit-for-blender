"""Issue #407: a skinned mesh's components sit on the posed mesh in component mode whatever its Normalize Weights
(Disable / Enable / Enable Post), like Maya: the kit's component drawing and preselection read the posed cage, and
Blender's own edit cage is the same posed mesh."""

from importlib import import_module
from math import radians

import bmesh
import bpy
import numpy as np
from mathutils import Vector

import kit

joints = import_module(kit.MODULE + ".operators.joints")
skin = import_module(kit.MODULE + ".operators.skin")
cc = import_module(kit.MODULE + ".ui.component_colors")
preselect = import_module(kit.MODULE + ".operators.preselect")

MODES = ("NONE", "INTERACTIVE", "POST")


def _scene():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    arm = joints.new_skeleton(bpy.context)
    parent = None
    for z in (0.0, 1.0, 2.0):
        parent = joints.add_joint(arm, Vector((0, 0, z)), parent, length=0.5)
    joints.finish(bpy.context, arm, ["joint1", "joint2", "joint3"])
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=2.0, location=(0, 0, 1.0), vertices=12)
    cyl = bpy.context.active_object
    for ob in (arm, cyl):
        ob.select_set(True)
    bpy.context.view_layer.objects.active = cyl
    assert bpy.ops.allset.bind_skin() == {'FINISHED'}
    return arm, cyl


def _posed_in_edit_mode(mode):
    arm, cyl = _scene()
    bpy.ops.object.select_all(action='DESELECT')
    cyl.select_set(True)
    bpy.context.view_layer.objects.active = cyl
    assert bpy.ops.allset.skin_normalize_mode(mode=mode) == {'FINISHED'}
    pb = arm.pose.bones["joint2"]
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (radians(90), 0, 0)
    bpy.context.view_layer.update()
    posed = np.array([v.co for v in cyl.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices])
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.view_layer.update()
    return cyl, posed


def test_component_colours_on_the_posed_mesh_for_every_normalize_mode():
    bad = {}
    for mode in MODES:
        cyl, posed = _posed_in_edit_mode(mode)
        bm = bmesh.from_edit_mesh(cyl.data)
        co = cc._coordinates(cyl, bpy.context.evaluated_depsgraph_get(), bm, len(bm.verts))
        off = float(np.abs(np.asarray(co, float) - posed).max()) if co is not None else None
        if off is None or off > 1e-4:
            bad[mode] = off
        bpy.ops.object.mode_set(mode='OBJECT')
    assert not bad, bad


def test_preselection_on_the_posed_mesh_for_every_normalize_mode():
    bad = {}
    for mode in MODES:
        cyl, posed = _posed_in_edit_mode(mode)
        co = preselect._deformed_cage(cyl, len(cyl.data.vertices))
        off = float(np.abs(co - posed).max()) if co is not None else None
        if off is None or off > 1e-4:
            bad[mode] = off
        bpy.ops.object.mode_set(mode='OBJECT')
    assert not bad, bad


def test_the_edit_cage_is_the_posed_mesh_for_every_normalize_mode():
    """Blender selects and moves components on the edit cage: every skin modifier shown in edit mode is on it."""
    bad = {}
    for mode in MODES:
        cyl, _posed = _posed_in_edit_mode(mode)
        mods = [(m.name, m.show_in_editmode, m.show_on_cage) for m in cyl.modifiers
                if m.show_viewport and m.show_in_editmode and not m.show_on_cage]
        if mods or not cc.use_evaluated(cyl.modifiers):
            bad[mode] = mods
        bpy.ops.object.mode_set(mode='OBJECT')
    assert not bad, bad
