"""Issue #397: a skinned mesh's components sit on the posed mesh like Maya: Bind Skin and Paint Skin Weights keep the
skin shown in edit mode on the edit cage, and the kit's component drawing reads that posed cage. Paint Skin Weights
turns its wireframe on the first time on a mesh, like Maya.
GUI: tests/gui/gui_issue397_paint_component.py."""

from importlib import import_module

import bpy
from mathutils import Vector

import kit

joints = import_module(kit.MODULE + ".operators.joints")
skin = import_module(kit.MODULE + ".operators.skin")
cc = import_module(kit.MODULE + ".ui.component_colors")
psw = import_module(kit.MODULE + ".operators.paint_skin_weights")


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
    return arm, cyl


def _bind(arm, cyl, **kw):
    for ob in (arm, cyl):
        ob.select_set(True)
    bpy.context.view_layer.objects.active = cyl
    assert bpy.ops.allset.bind_skin(**kw) == {'FINISHED'}


def test_bind_skin_shows_the_pose_in_component_mode():
    for method in ("CLASSIC_LINEAR", "WEIGHT_BLENDED"):
        arm, cyl = _scene()
        _bind(arm, cyl, skinning=method)
        mods = [m for m in cyl.modifiers if m.type == 'ARMATURE']
        assert mods and all(m.show_in_editmode and m.show_on_cage for m in mods), (method, mods)
        assert cc.use_evaluated(cyl.modifiers), method


def test_cage_rule():
    arm, cyl = _scene()
    _bind(arm, cyl)
    md = skin.armature_modifier(cyl)
    md.show_on_cage = False                     # shown in edit mode but off the cage: the cage is the BMesh
    assert not cc.use_evaluated(cyl.modifiers)
    md.show_on_cage = True
    sub = cyl.modifiers.new("sub", 'SUBSURF')
    sub.show_in_editmode = True
    assert not cc.use_evaluated(cyl.modifiers)
    sub.show_in_editmode = False
    assert cc.use_evaluated(cyl.modifiers)


def test_paint_skin_weights_on_an_older_skin():
    arm, cyl = _scene()
    _bind(arm, cyl)
    md = skin.armature_modifier(cyl)
    md.show_in_editmode = md.show_on_cage = False       # a skin bound before
    cyl.pop(psw.PAINT_WIRE, None)
    bpy.ops.object.select_all(action='DESELECT')
    cyl.select_set(True)
    bpy.context.view_layer.objects.active = cyl
    try:
        bpy.ops.allset.paint_skin_weights()
    except RuntimeError:
        pass                                            # background: no tool system for the brush tool
    assert cyl.mode == 'WEIGHT_PAINT'
    assert md.show_in_editmode and md.show_on_cage
    assert cyl.get(psw.PAINT_WIRE)
    bpy.ops.object.mode_set(mode='OBJECT')


def test_component_mode_shows_the_pose_of_any_skin():
    """A skin bound before (or by Blender's own tools) shows its pose as soon as it goes into component mode."""
    from math import radians
    arm, cyl = _scene()
    _bind(arm, cyl)
    md = skin.armature_modifier(cyl)
    md.show_in_editmode = md.show_on_cage = False
    other = cyl.modifiers.new("Armature", 'ARMATURE')      # a second skin, as Blender's Ctrl+P makes
    other.object = arm
    other.show_in_editmode = other.show_on_cage = False
    pb = arm.pose.bones["joint2"]
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (radians(90), 0, 0)
    bpy.ops.object.select_all(action='DESELECT')
    cyl.select_set(True)
    bpy.context.view_layer.objects.active = cyl
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.view_layer.update()
    assert all(m.show_in_editmode and m.show_on_cage for m in (md, other)), [(m.show_in_editmode, m.show_on_cage)
                                                                             for m in (md, other)]
    assert cc.use_evaluated(cyl.modifiers)
    bpy.ops.object.mode_set(mode='OBJECT')
