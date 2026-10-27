"""Step 244 (Issue #161) in a real UI, chain ③ (research/maya/re/joint_rig_2026_joint_tool.md §3, GUI Maya 2026 front
clicks (0,0,0) (4,3,0) (8,0,0) (11,2,0)): Joint Tool in the front view, 4 clicks, Enter -> every joint's frame = Maya's
(aos: joint1 / joint2 Y = (0,0,-1), joint3 Y = (0,0,1), joint4 = joint3's frame), new joints SSC on, Maya radius ->
the AE shows Maya's jointOrient -> Skeleton > Orient Joint with auto orient off (option box values) re-orients ->
Ctrl+Z puts it back -> save + open keeps the frames."""

import math
import os
import sys
import tempfile
from importlib import import_module

import bpy
from bpy_extras import view3d_utils
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402
import maya2026_rig as rig  # noqa: E402
import maya2026_rig_data as data  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
FC = data.JOINT_TOOL["front_chain"]
MAYA = ("joint1", "joint2", "joint3", "joint4")
CLICKS = [(0, 0, 0), (4, 3, 0), (8, 0, 0), (11, 2, 0)]


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, f"gui_step244_{name}.png"))


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def ov():
    area, region = main_view()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def screen_of(world):
    _a, r = main_view()
    p = view3d_utils.location_3d_to_region_2d(r, r.data, world)
    return int(round(r.x + p.x)), int(round(r.y + p.y))


def rig_ob():
    return bpy.data.objects[C["rig"]]


def frames():
    ob = rig_ob()
    return {n: rig.joint_world(ob, n, C["unit"])[1] for n in C["names"]}


def err(a, b):
    return max((a.col[i] - b.col[i]).length for i in range(3))


def maya_axes(mn):
    x, y, z = FC[mn]["axes"]
    m = rig.Matrix.Identity(3)
    m.col[0], m.col[1], m.col[2] = Vector(x), Vector(y), Vector(z)
    return m


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_front():
    for ob in list(bpy.data.objects):
        if ob.type in {'MESH', 'ARMATURE'}:
            bpy.data.objects.remove(ob)
    C["unit"] = mod(".operators.units").maya_unit()
    _a, r = main_view()
    rv3d = r.data
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = Euler((math.radians(90), 0, 0)).to_quaternion()     # Maya front = Blender front (-Y)
    rv3d.view_location = rig.to_blender((5.5, 1.5, 0), C["unit"])
    rv3d.view_distance = 16 * C["unit"]
    with ov():
        bpy.ops.allset.joint_tool('INVOKE_DEFAULT')


def click(i):
    @step
    def s_click():
        x, y = screen_of(rig.to_blender(CLICKS[i], C["unit"]))
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
    s_click.__name__ = f"s_click{i + 1}"


for _i in range(4):
    click(_i)


@step
def s_enter():
    _a, r = main_view()
    ev('RET', 'PRESS', x=r.x + 20, y=r.y + 20)
    ev('RET', 'RELEASE', x=r.x + 20, y=r.y + 20)


@step
def s_created():
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    check(f"Joint Tool made one skeleton ({len(arms)})", len(arms) == 1)
    C["rig"] = arms[0].name
    ob = rig_ob()
    C["names"] = [b.name for b in ob.data.bones]
    check(f"4 joints ({C['names']})", len(C["names"]) == 4)
    f = frames()
    worst = max(err(f[n], maya_axes(mn)) for n, mn in zip(C["names"], MAYA))
    # clicks land on whole pixels: directions are off by ~1e-3 at this zoom
    check(f"every joint's frame = Maya's GUI front chain (aos: joint3 flips, end = parent) ({worst:.1e})", worst < 0.02)
    signs = [round(f[n].col[1].z) for n in C["names"]]                 # Maya Y's Maya-Z sign
    check(f"Maya Y signs -1, -1, +1, +1 like Maya ({signs})", signs == [-1, -1, 1, 1])
    check("new joints: Segment Scale Compensate on", all(b.inherit_scale == 'NONE' for b in ob.data.bones))
    radii = [round(b.get("allset_radius", 0), 3) for b in ob.data.bones]
    check(f"Maya joint radius 0.707 / 0.707 / 0.634 / 0.634 ({radii})",
          all(abs(a - b) < 0.01 for a, b in zip(radii, (0.707, 0.707, 0.634, 0.634))))
    ae = mod(".ui.attribute_editor")
    jo = [math.degrees(v) for v in ae.joint_orient(ob.pose.bones[C["names"][2]])]
    want = Euler([math.radians(v) for v in FC["joint3"]["jo"]], 'XYZ').to_matrix()
    got = Euler([math.radians(v) for v in jo], 'XYZ').to_matrix()
    check(f"AE Joint Orient of joint3 = Maya (180, -70.76, 0) ({[round(v, 2) for v in jo]})", err(got, want) < 0.02)
    ob.data.show_axes = True
    C["f0"] = f


@step
def s_shot_created():
    shot("01_front_chain")


@step
def s_orient_menu():
    ob = rig_ob()
    with ov():
        if bpy.context.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')
        cb = mod(".ui.channel_box")
        for pb in ob.pose.bones:
            cb.set_bone_selected(pb, pb.name == C["names"][0])
        ob.data.bones.active = ob.data.bones[C["names"][0]]
        # the option box values: auto orient secondary axis off (projected world up), then Orient
        bpy.ops.allset.orient_joint('EXEC_DEFAULT', True, auto_secondary=False)


@step
def s_reoriented():
    f = frames()
    y = f[C["names"]][1] if False else f[C["names"][0]].col[1]
    check(f"Orient Joint without aos: joint1 Y = world up projected ({tuple(round(c, 3) for c in y)})",
          abs(y.y) > 0.5 and abs(y.z) < 1e-5)
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_undone():
    e = max(err(a, C["f0"][n]) for n, a in frames().items())
    check(f"Ctrl+Z: Maya's aos frames back ({e:.1e})", e < 1e-5)
    path = os.path.join(tempfile.mkdtemp(prefix="allset244_"), "orient.blend")
    with ov():
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    bpy.ops.wm.open_mainfile(filepath=path, load_ui=False)


@step
def s_reopened():
    e = max(err(a, C["f0"][n]) for n, a in frames().items())
    check(f"save + open keeps the frames ({e:.1e})", e < 1e-5)
    shot("02_reopened")


run()
