"""Ctrl+G with a joint selected (pose mode), in the viewport and in the Outliner: the skeleton goes under group1 and
its skin moves with the group, like grouping a root joint in Maya. Headless: tests/test_group_joints.py."""

import os
import sys
from importlib import import_module

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, view3d, win  # noqa: E402

joints = import_module(MODULE + ".operators.joints")
skin = import_module(MODULE + ".operators.skin")
cb = import_module(MODULE + ".ui.channel_box")


def outliner():
    area = next(a for a in win().screen.areas if a.type == 'OUTLINER')
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def hover(area_region):
    _a, r = area_region
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


def ctrl_g():
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    ev('G', 'PRESS', ctrl=True)
    ev('G', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


def skinned(x):
    """A skeleton (3 joints up Z at x) and a box bound to it."""
    arm = joints.new_skeleton(bpy.context)
    parent, names = None, []
    for z in (0.0, 1.0, 2.0):
        parent = joints.add_joint(arm, Vector((x, 0, z)), parent, length=0.5)
        names.append(parent)
    joints.finish(bpy.context, arm, names)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0, 1.0), scale=(0.3, 0.3, 1.2))
    box = bpy.context.active_object
    skin.bind_skin(bpy.context, arm, [box])
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    return arm, box, names[0]


def pick_root(arm, root):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, pb.name == root)
    arm.data.bones.active = arm.data.bones[root]


def skin_center(box):
    dg = bpy.context.evaluated_depsgraph_get()
    ev_ob = box.evaluated_get(dg)
    me = ev_ob.to_mesh()
    c = sum((box.matrix_world @ v.co for v in me.vertices), Vector()) / len(me.vertices)
    ev_ob.to_mesh_clear()
    return c


S = {}


@step
def s_setup():
    setup()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        S["a"] = skinned(0.0)
        S["b"] = skinned(3.0)
        pick_root(S["a"][0], S["a"][2])
    check(f"setup: pose mode, {S['a'][2]} picked ({bpy.context.mode})", bpy.context.mode == 'POSE')
    hover(view3d())


@step
def s_view_ctrl_g():
    ctrl_g()


@step
def s_view_check():
    arm, box, _root = S["a"]
    grp = bpy.data.objects.get("group1")
    check(f"viewport Ctrl+G on a root joint makes group1 ({grp})", grp is not None)
    check(f"the skeleton is under group1 ({arm.parent})", grp is not None and arm.parent == grp)
    check(f"object mode, group1 selected ({bpy.context.mode})",
          bpy.context.mode == 'OBJECT' and grp is not None and grp.select_get())
    if grp is not None:
        before = skin_center(box)
        grp.location = (0.0, 2.0, 0.0)
        bpy.context.view_layer.update()
        moved = skin_center(box) - before
        check(f"moving group1 moves the skin with it ({tuple(round(v, 4) for v in moved)})",
              (moved - Vector((0, 2, 0))).length < 1e-4)
    arm_b, _box_b, root_b = S["b"]
    pick_root(arm_b, root_b)
    hover(outliner())


@step
def s_outliner_ctrl_g():
    ctrl_g()


@step
def s_outliner_check():
    arm_b, box_b, _root = S["b"]
    grp = bpy.data.objects.get("group2")
    check(f"Outliner Ctrl+G on a root joint makes group2 ({grp})", grp is not None and arm_b.parent == grp)
    S.clear()       # no Blender data kept past the session


run()
