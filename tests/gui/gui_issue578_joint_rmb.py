"""#578 in a real UI: a scene with only joints (pose mode). Right-click on a joint opens Maya's joint marking menu
(W Set Preferred Angle, E Assume Preferred Angle, N Edit Joints), right-click on empty space with no joint selected
Maya's Select All / Complete Tool menu, never Blender's Pose context menu."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def radial_labels():
    s = mod(".marking.draw").ACTIVE.get("session")
    if s is None:
        return None
    return {k: it.label for k, it in s.layout.radial.items() if it is not None}


def joint_px(name):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    area, region = view3d()
    ob = bpy.data.objects["joint1"]
    p = location_3d_to_region_2d(region, region.data, ob.matrix_world @ ob.pose.bones[name].head)
    return int(region.x + p.x), int(region.y + p.y)


@step
def s_setup():
    setup()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    arm = bpy.data.armatures.new("skeleton")
    ob = bpy.data.objects.new("joint1", arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='EDIT')
        parent = None
        for i in range(3):
            b = arm.edit_bones.new(f"joint{i + 1}")
            b.head, b.tail = (i * 3.0, 0, 0), (i * 3.0 + 3.0, 0, 0)
            if parent is not None:
                b.parent, b.use_connect = parent, True
            parent = b
        bpy.ops.object.mode_set(mode='POSE')
        for pb in ob.pose.bones:
            pb.select = False
        bpy.ops.view3d.view_axis(type='FRONT')
        bpy.ops.view3d.view_all(center=False)


@step
def s_wait():
    pass


@step
def s_rmb_joint():
    check(f"pose mode, nothing selected ({bpy.context.mode})", bpy.context.mode == 'POSE')
    C["j"] = joint_px("joint2")
    ev('MOUSEMOVE', 'NOTHING', x=C["j"][0], y=C["j"][1])
    ev('RIGHTMOUSE', 'PRESS', x=C["j"][0], y=C["j"][1])


@step
def s_rmb_joint_check():
    got = radial_labels()
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue578_joint_rmb.png"))
    check(f"RMB on a joint opens the joint marking menu ({got})",
          got == {"W": "Set Preferred Angle", "E": "Assume Preferred Angle", "N": "Edit Joints"})
    check(f"the menu knows the joint ({bpy.context.window_manager.allset_mm_joint})",
          bpy.context.window_manager.allset_mm_joint == "joint2")
    tap('ESC')
    ev('RIGHTMOUSE', 'RELEASE', x=C["j"][0], y=C["j"][1])


@step
def s_rmb_empty():
    _area, region = view3d()
    C["e"] = (region.x + 40, region.y + region.height - 120)
    ev('MOUSEMOVE', 'NOTHING', x=C["e"][0], y=C["e"][1])
    ev('RIGHTMOUSE', 'PRESS', x=C["e"][0], y=C["e"][1])


@step
def s_rmb_empty_check():
    got = radial_labels()
    check(f"RMB on empty space, no joint selected: Select All / Complete Tool ({got})",
          got == {"S": "Select All", "N": "Complete Tool"})
    tap('ESC')
    ev('RIGHTMOUSE', 'RELEASE', x=C["e"][0], y=C["e"][1])


run()
