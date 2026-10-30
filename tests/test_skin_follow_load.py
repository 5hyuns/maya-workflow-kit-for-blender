"""A skin moves with its skeleton object like a Maya skin. Files whose skins were bound before the kit gave them a
follow get it when they open (nothing moves on load, it follows from then on); meshes parented under their skeleton
and skins the kit didn't bind are left alone. A moved skeleton's skin goes out in an FBX where it shows."""

import os
from importlib import import_module

import bpy
from mathutils import Vector

import kit

joints = import_module(kit.MODULE + ".operators.joints")
skin = import_module(kit.MODULE + ".operators.skin")
follow = import_module(kit.MODULE + ".operators.skin_follow")
command_line = import_module(kit.MODULE + ".command_line")

OUT = os.path.join(os.environ.get("ALLSET_TEST_OUT", bpy.app.tempdir), "skin_follow_load")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions):
        for d in list(coll):
            coll.remove(d)


def _skinned():
    _clear()
    arm = joints.new_skeleton(bpy.context)
    parent = None
    names = []
    for z in (0.0, 1.0, 2.0):
        parent = joints.add_joint(arm, Vector((0, 0, z)), parent, length=0.5)
        names.append(parent)
    joints.finish(bpy.context, arm, names)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.0), scale=(0.3, 0.3, 1.2))
    box = bpy.context.active_object
    box.name = "pCube1"
    skin.bind_skin(bpy.context, arm, [box])
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    return arm, box


def _points(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    e = ob.evaluated_get(dg)
    return [e.matrix_world @ v.co for v in e.data.vertices]


def _worst(a, b):
    return max((p - q).length for p, q in zip(a, b))


def _old_file(name, arm, box):
    """Save the scene as a file bound before the follow existed: the skin has no follow."""
    for con in follow.follows(box):
        box.constraints.remove(con)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    return path


def test_old_file_gets_follow_on_load_without_moving():
    arm, box = _skinned()
    arm.location = (2.0, 0.0, 0.0)               # the skeleton object was moved after the bind, before the follow
    bpy.context.view_layer.update()
    before = _points(box)
    path = _old_file("old_moved.blend", arm, box)
    command_line.show_result("")
    bpy.ops.wm.open_mainfile(filepath=path)
    box, arm = bpy.data.objects["pCube1"], next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    assert len(follow.follows(box)) == 1, [c.name for c in box.constraints]
    assert _worst(before, _points(box)) < 1e-5, "nothing moves on load"
    assert "move with their skeleton" in command_line._result["text"], command_line._result
    p0 = _points(box)
    arm.location.x += 1.5
    bpy.context.view_layer.update()
    moved = [p - q for p, q in zip(_points(box), p0)]
    assert all((d - Vector((1.5, 0, 0))).length < 1e-5 for d in moved), "the skin follows from now on"
    assert follow.repair_file() == 0, "a second pass adds nothing"


def test_mesh_under_its_skeleton_and_foreign_skins_are_left_alone():
    arm, box = _skinned()
    for con in follow.follows(box):
        box.constraints.remove(con)
    box.parent = arm                              # Blender's parent already carries it
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3, 0, 1))
    other = bpy.context.active_object             # an Armature modifier the kit's Bind Skin didn't make
    other.modifiers.new("Armature", 'ARMATURE').object = arm
    assert follow.repair_file() == 0
    assert not follow.follows(box) and not follow.follows(other)
    follow.ensure(arm)                            # grouping the skeleton doesn't double the parented mesh either
    assert not follow.follows(box)


def test_fbx_of_a_moved_skeleton_keeps_the_skin_where_it_shows():
    arm, box = _skinned()
    arm.location = (2.0, 1.0, 0.0)
    arm.rotation_euler = (0.0, 0.0, 0.5)
    bpy.context.view_layer.update()
    before = sorted(tuple(round(c, 4) for c in p) for p in _points(box))
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "moved_skin.fbx")
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    assert bpy.ops.allset.file_export_all('EXEC_DEFAULT', filepath=path, export_type='FBX') == {'FINISHED'}
    _clear()
    assert bpy.ops.allset.file_import('EXEC_DEFAULT', filepath=path) == {'FINISHED'}
    mesh = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    after = sorted(tuple(round(c, 4) for c in p) for p in _points(mesh))
    assert len(after) == len(before)
    worst = max((Vector(a) - Vector(b)).length for a, b in zip(after, before))
    assert worst < 1e-3, ("skin moved in the FBX round trip", worst, before[:2], after[:2])
