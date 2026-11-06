"""#323: a marquee over a rig's controls (bones with a custom shape, like Auto Rig Pro's) picks every control in
it, not only the one closest to the root; a marquee around a whole kit joint chain still picks its top joint."""

import os
import sys
from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

C = {}
CONTROLS = ("c_global", "c_root", "c_spine", "c_chest", "c_hand")


def mod(name):
    return import_module(MODULE + name)


def to_window(world):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    p = location_3d_to_region_2d(region, area.spaces.active.region_3d, world)
    return Vector((p.x + region.x, p.y + region.y))


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def picked(name):
    a = bpy.data.objects[name]
    if a.mode != 'POSE':
        return []
    cb = mod(".ui.channel_box")
    return sorted(pb.name for pb in a.pose.bones if cb.bone_selected(pb))


def circle(name, k):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, segments=12, radius=1.0 * k)
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new(name, me)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    k = mod(".operators.units").maya_unit()
    shapes = bpy.data.collections.new("cs_grp")             # control shapes live in a hidden collection
    bpy.context.scene.collection.children.link(shapes)
    shapes.hide_viewport = True
    arm = bpy.data.armatures.new("rig")
    rig = bpy.data.objects.new("rig", arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    heads = {"c_global": (-10, 0, 0), "c_root": (-10, 0, 2), "c_spine": (-10, 0, 4), "c_chest": (-10, 0, 6),
             "c_hand": (-7, 0, 6)}
    parent = {"c_root": "c_global", "c_spine": "c_root", "c_chest": "c_spine", "c_hand": "c_chest"}
    for n in CONTROLS:
        eb = arm.edit_bones.new(n)
        eb.head = Vector(heads[n]) * k
        eb.tail = (Vector(heads[n]) + Vector((0, 0, 1))) * k
        if n in parent:
            eb.parent = arm.edit_bones[parent[n]]
    bpy.ops.object.mode_set(mode='OBJECT')
    for n in CONTROLS:
        cs = circle("cs_" + n, k)
        shapes.objects.link(cs)
        pb = rig.pose.bones[n]
        pb.custom_shape = cs
        pb.use_custom_shape_bone_size = False
    joints = mod(".operators.joints")
    rig.select_set(False)
    a = joints.new_skeleton(bpy.context)
    names, par = [], None
    for x in (6.0, 9.0, 12.0):
        par = joints.add_joint(a, Vector((x, 0.0, 4.0)) * k, par, length=1.0 * k)
        names.append(par)
    joints.finish(bpy.context, a, names)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    C["k"], C["skel"], C["joints"] = k, a.name, names
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = (0.7071068, 0.7071068, 0.0, 0.0)      # front view
    rv3d.view_location = (0.0, 0.0, 3.0 * k)
    rv3d.view_distance = 40.0 * k
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.pose.select_all(action='DESELECT')
    redraw()


def box(name, lo, hi):
    """Drag from world point ``lo`` to ``hi`` (both scaled by the scene unit at run time)."""
    def corner(w):
        return to_window(Vector(w) * C["k"])

    def press():
        p = corner(lo)
        ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))
        ev('LEFTMOUSE', 'PRESS', x=int(p.x), y=int(p.y))

    def move1():
        p = (corner(lo) + corner(hi)) / 2
        ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))

    def move2():
        p = corner(hi)
        ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))

    def release():
        p = corner(hi)
        ev('LEFTMOUSE', 'RELEASE', x=int(p.x), y=int(p.y))

    def settle():
        pass                       # the joint rules run from a timer after the box ends
    for i, fn in enumerate((press, move1, move2, release, settle, settle, settle)):
        f = (lambda fn: lambda: fn())(fn)
        f.__name__ = f"s_{name}_{i}"
        step(f)


@step
def s_ready():
    check(f"Pose mode on the rig, nothing selected ({bpy.context.mode}, {picked('rig')})",
          bpy.context.mode == 'POSE' and picked("rig") == [])


box("controls", (-13.5, 0, -2), (-4, 0, 8.5))


@step
def s_controls():
    check(f"a box over the controls picks all of them ({picked('rig')})", picked("rig") == sorted(CONTROLS))


box("chain", (3, 0, 1), (14, 0, 7))


@step
def s_chain():
    skel = C["skel"]
    check(f"a box around a whole joint chain still picks its top joint ({picked(skel)})",
          picked(skel) == [C["joints"][0]])


run()
