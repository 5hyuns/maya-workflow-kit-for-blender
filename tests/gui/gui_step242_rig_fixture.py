"""Step 242 (Issue #159) in a real UI, chain ③: a skeleton built from Maya 2026 numbers (tests/maya2026_rig.py,
JOINT_MATH move_joint_156 start = Maya world j1 (0,0,0) j2 (3,1,0) j3 (6,0,-1) j4 (8,1,1)) behaves like a kit skeleton
in the Maya layout: it sits at Maya's positions in Maya units, a click on j2 picks it the Maya way (kit pick), its
axes are Maya's, and save + open keeps it — so steps 243-252 can start their GUI checks from measured skeletons."""

import os
import sys
import tempfile
from importlib import import_module

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step  # noqa: E402
import maya2026_rig as rig  # noqa: E402
import maya2026_rig_data as data  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
CASE = data.JOINT_MATH["move_joint_156"]["start"]
PARENTS = {"j1": None, "j2": "j1", "j3": "j2", "j4": "j3"}


def mod(name):
    return import_module(MODULE + name)


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, f"gui_step242_{name}.png"))


def main_view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in bpy.context.window_manager.windows[0].screen.areas
             if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def ov():
    area, region = main_view()
    return bpy.context.temp_override(window=bpy.context.window_manager.windows[0], area=area, region=region)


def screen_of(world):
    _a, r = main_view()
    p = view3d_utils.location_3d_to_region_2d(r, r.data, world)
    return int(r.x + p.x), int(r.y + p.y)


def skel():
    return {n: dict(rec, parent=PARENTS[n], w=CASE["world"][n]) for n, rec in CASE["attrs"].items()}


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_build():
    for ob in list(bpy.data.objects):
        if ob.type in {'MESH', 'ARMATURE'}:
            bpy.data.objects.remove(ob)
    C["unit"] = mod(".operators.units").maya_unit()
    ob = rig.build_skeleton(skel(), unit=C["unit"], name="skeleton1")
    ob.data.show_axes = True
    ob.show_in_front = True
    C["rig"] = ob.name
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    with ov():
        bpy.ops.view3d.view_selected()
    bpy.ops.ed.undo_push(message="build")


@step
def s_built():
    ob = bpy.data.objects[C["rig"]]
    worst = max((rig.joint_world(ob, n, C["unit"])[0] - Vector(CASE["world"][n])).length for n in PARENTS)
    check(f"skeleton at Maya's measured world positions in Maya units (unit {C['unit']}, worst {worst:.1e})",
          worst < 2e-3)
    shot("01_built")


@step
def s_pose():
    bpy.ops.object.mode_set(mode='POSE')


@step
def s_click_j2():
    ob = bpy.data.objects[C["rig"]]
    x, y = screen_of(ob.matrix_world @ ob.data.bones["j2"].head_local)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_picked():
    ob = bpy.data.objects[C["rig"]]
    cb = mod(".ui.channel_box")
    sel = sorted(b.name for b in ob.pose.bones if cb.bone_selected(b))
    check(f"click on j2 picks j2 (kit joint pick works on fixture skeletons) ({sel})", "j2" in sel)
    shot("02_picked_j2")


@step
def s_save_open():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    path = os.path.join(tempfile.mkdtemp(prefix="allset242_"), "fixture.blend")
    C["path"] = path
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    bpy.ops.wm.open_mainfile(filepath=path, load_ui=False)


@step
def s_reopened():
    ob = bpy.data.objects.get(C["rig"])
    check("save + open keeps the skeleton", ob is not None)
    if ob is None:
        return
    worlds = rig.world_matrices(skel())
    worst = 0.0
    for n in PARENTS:
        _p, axes = rig.joint_world(ob, n, C["unit"])
        want = worlds[n].to_3x3().normalized()
        worst = max(worst, (axes.col[0] - want.col[0]).length, (axes.col[1] - want.col[1]).length)
    check(f"after open the joints keep Maya's X / Y axes (worst {worst:.1e})", worst < 1e-5)
    shot("03_reopened")


run()
