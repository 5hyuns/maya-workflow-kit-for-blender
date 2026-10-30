"""Joints drawn like Maya's in the Maya layout (cm scene): Blender's bones are off in the layout's views, the kit draws
dark violet wire spheres and bones; selecting the root joint turns the whole chain green (the lead's colour passed down);
turning the view's Bones overlay back on shows Blender's bones and no kit joints. Selection follows Maya: a click hits a
joint's wire (its centre cross in a front view selects it, the inside of its circle away from the lines selects
nothing), a marquee touching a joint's lines picks it but keeps one joint per skeleton (the one nearest the root), and
joints win over a mesh in the same marquee."""

import os
import sys
from importlib import import_module

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
VIOLET = np.array([0x26, 0x00, 0x43]) / 255.0
LEAD = np.array([0x43, 0xff, 0xa3]) / 255.0
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_maya_joints_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[..., :3]


def to_window(world):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    p = location_3d_to_region_2d(region, area.spaces.active.region_3d, world)
    return None if p is None else Vector((p.x + region.x, p.y + region.y))


def count(px, world, colour, half=40):
    p = to_window(world)
    x, y = int(round(p.x)), int(round(p.y))
    patch = px[y - half:y + half, x - half:x + half]
    return int((np.abs(patch - colour).max(axis=-1) < 0.08).sum())


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def heads():
    arm = bpy.data.objects[C["arm"]]
    return [arm.matrix_world @ arm.data.bones[n].head_local for n in C["names"]]


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    joints = mod(".operators.joints")
    k = mod(".operators.units").maya_unit()
    arm = joints.new_skeleton(bpy.context)
    names, parent = [], None
    for x in (-8.0, 0.0, 8.0):
        parent = joints.add_joint(arm, Vector((x, 0.0, 4.0)) * k, parent, length=1.0 * k)
        names.append(parent)
    joints.finish(bpy.context, arm, names)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for n in names:
        arm.data.bones[n][joints.RADIUS] = 4.0          # drawn radius 2 units: big enough to sample
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    C["arm"], C["names"] = arm.name, names
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_location = (0.0, 0.0, 4.0 * k)
    rv3d.view_distance = 40.0 * k
    redraw()


@step
def s_settled():
    toolbox = mod(".ui.toolbox")
    views = [a.spaces.active for a in win().screen.areas
             if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    check(f"Blender's bones are off in the layout's views ({[s.overlay.show_bones for s in views]})",
          views and not any(s.overlay.show_bones for s in views))
    redraw()


@step
def s_unselected():
    px = shot("unselected")
    n = [count(px, h, VIOLET) for h in heads()]
    check(f"every joint draws dark violet ({n} px)", all(c > 20 for c in n))
    check("nothing green yet", all(count(px, h, LEAD) == 0 for h in heads()))
    arm = bpy.data.objects[C["arm"]]
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    cb = mod(".ui.channel_box")
    for pb in arm.pose.bones:
        cb.set_bone_selected(pb, pb.name == C["names"][0])
    arm.data.bones.active = arm.data.bones[C["names"][0]]
    redraw()


@step
def s_root_selected():
    px = shot("root_selected")
    n = [count(px, h, LEAD) for h in heads()]
    check(f"the root is the lead and its chain draws green ({n} px)", all(c > 20 for c in n))
    check("no violet left on the chain", all(count(px, h, VIOLET) == 0 for h in heads()))
    area, _r = view3d()
    area.spaces.active.overlay.show_bones = True
    redraw()


@step
def s_bones_back_on():
    px = shot("blender_bones")
    check("with the Bones overlay on again the kit draws no joints",
          all(count(px, h, LEAD) == 0 and count(px, h, VIOLET) == 0 for h in heads()))
    area, _r = view3d()
    area.spaces.active.overlay.show_bones = False
    bpy.ops.object.mode_set(mode='OBJECT')
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    # front orthographic view: each joint shows a circle with a cross
    from mathutils import Euler
    k = mod(".operators.units").maya_unit()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = Euler((1.5707963, 0.0, 0.0)).to_quaternion()
    rv3d.view_location = (0.0, 0.0, 4.0 * k)
    rv3d.view_distance = 30.0 * k
    area_, region = view3d()
    with bpy.context.temp_override(window=win(), area=area_, region=region):
        bpy.ops.allset.create(kind='CUBE')
    cube = bpy.context.view_layer.objects.active
    cube.location = (8.0 * k, 0.0, -4.0 * k)
    cube.scale = (3.0, 3.0, 3.0)
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    C["cube"] = cube.name
    redraw()


def selected_joints():
    arm = bpy.data.objects[C["arm"]]
    if arm.mode != 'POSE':
        return []
    cb = mod(".ui.channel_box")
    return [pb.name for pb in arm.pose.bones if cb.bone_selected(pb)]


def click(name, world_fn):
    def press():
        p = world_fn()
        ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))
        ev('LEFTMOUSE', 'PRESS', x=int(p.x), y=int(p.y))

    def release():
        p = world_fn()
        ev('LEFTMOUSE', 'RELEASE', x=int(p.x), y=int(p.y))
    press.__name__, release.__name__ = f"s_{name}_press", f"s_{name}_release"
    step(press)
    step(release)


def box(name, a_fn, b_fn):
    def press():
        a = a_fn()
        ev('MOUSEMOVE', 'NOTHING', x=int(a.x), y=int(a.y))
        ev('LEFTMOUSE', 'PRESS', x=int(a.x), y=int(a.y))

    def move1():
        a, b = a_fn(), b_fn()
        ev('MOUSEMOVE', 'NOTHING', x=int((a.x + b.x) / 2), y=int((a.y + b.y) / 2))

    def move2():
        b = b_fn()
        ev('MOUSEMOVE', 'NOTHING', x=int(b.x), y=int(b.y))

    def release():
        b = b_fn()
        ev('LEFTMOUSE', 'RELEASE', x=int(b.x), y=int(b.y))

    def settle():
        pass                       # the joint rules run from a timer after the box ends
    for i, fn in enumerate((press, move1, move2, release, settle, settle)):
        f = (lambda fn: lambda: fn())(fn)
        f.__name__ = f"s_{name}_{i}"
        step(f)


def head(i):
    return lambda: to_window(heads()[i])


def r_px():
    """Drawn joint radius in window px (front ortho)."""
    k = mod(".operators.units").maya_unit()
    a, b = to_window(heads()[1]), to_window(heads()[1] + Vector((2.0 * k, 0, 0)))
    return (b - a).length


click("centre", head(1))


@step
def s_centre_done():
    check(f"a click on a joint's centre cross selects that joint ({selected_joints()})",
          selected_joints() == [C["names"][1]])


click("inside", lambda: to_window(heads()[1]) + Vector((0.45, 0.45)) * r_px())


@step
def s_inside_done():
    check(f"a click inside the circle away from its lines selects nothing ({selected_joints()})",
          selected_joints() == [])


box("chain", lambda: to_window(heads()[0]) + Vector((-3, -1.5)) * r_px(),
    lambda: to_window(heads()[2]) + Vector((3, 1.5)) * r_px())


@step
def s_chain_done():
    check(f"a box around the whole chain selects its top joint only ({selected_joints()})",
          selected_joints() == [C["names"][0]])


box("tip", lambda: to_window(heads()[2]) + Vector((-0.2, -0.2)) * r_px(),
    lambda: to_window(heads()[2]) + Vector((0.2, 0.2)) * r_px())


@step
def s_tip_done():
    check(f"a small box on the last joint's centre selects it ({selected_joints()})",
          selected_joints() == [C["names"][2]])


box("mixed", lambda: to_window(heads()[2]) + Vector((-0.2, -8.0)) * r_px(),
    lambda: to_window(heads()[2]) + Vector((0.2, 0.2)) * r_px())


@step
def s_mixed_done():
    cube = bpy.data.objects[C["cube"]]
    check(f"joints win over a mesh in the same box ({selected_joints()}, cube {cube.select_get()})",
          selected_joints() == [C["names"][2]] and not cube.select_get())


box("cube_only", lambda: to_window(heads()[2]) + Vector((-0.5, -4.5)) * r_px(),
    lambda: to_window(heads()[2]) + Vector((0.5, -3.5)) * r_px())


@step
def s_cube_only_done():
    cube = bpy.data.objects[C["cube"]]
    check(f"a box over the cube alone selects the cube ({cube.select_get()}, joints {selected_joints()})",
          cube.select_get() and selected_joints() == [])


run()
