"""In a real UI: in Pose Mode, Key > Pose Breakdowner, Relax Pose to Breakdown and Push Pose from Breakdown (the items
right below Set Breakdown Key) run Blender's pose in-between tools in the 3D View; Enter keeps the result."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, load_maya_layout, win  # noqa: E402

S = {}


def main_view():
    return max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)


def park():
    r = next(r for r in main_view().regions if r.type == 'WINDOW')
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


def bone():
    return S["ob"].pose.bones[0]


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_rig():
    bpy.ops.object.armature_add()
    ob = bpy.context.view_layer.objects.active
    S["ob"] = ob
    with bpy.context.temp_override(window=win(), area=main_view()):
        bpy.ops.object.mode_set(mode='POSE')
    pb = ob.pose.bones[0]
    if hasattr(pb, "select"):
        pb.select = True
    else:
        pb.bone.select = True
    for f, z in ((1, 0.0), (11, 1.0)):
        pb.location.z = z
        pb.keyframe_insert("location", frame=f)
    bpy.context.scene.frame_set(6)


@step
def s_places():
    menu_map = import_module(MODULE + ".ui.menu_map")
    menu_sets = import_module(MODULE + ".ui.menu_sets")
    menu_data = import_module(MODULE + ".ui.menu_data")
    paths = [p for p, _it in menu_sets.children(menu_data.MENUS['mainKeysMenu'][3], "Key") if p]
    i = paths.index("Key/Set Breakdown Key")
    check("Key menu: the three pose in-between items follow Set Breakdown Key",
          paths[i + 1:i + 4] == ["Key/Pose Breakdowner", "Key/Relax Pose to Breakdown", "Key/Push Pose from Breakdown"])
    check("they run Blender's pose.breakdown / pose.relax / pose.push in the 3D View",
          [menu_map.MAP[p] for p in paths[i + 1:i + 4]]
          == [("v3d", "pose.breakdown", {}), ("v3d", "pose.relax", {}), ("v3d", "pose.push", {})])


for item, op in (("Key/Pose Breakdowner", "pose.breakdown"), ("Key/Relax Pose to Breakdown", "pose.relax"),
                 ("Key/Push Pose from Breakdown", "pose.push")):
    def s_off(item=item):
        bone().location.z = 5.0      # an unkeyed pose far from the keys
        bpy.context.view_layer.update()
        park()

    def s_run(item=item, op=op):
        with bpy.context.temp_override(window=win()):
            S["ret"] = bpy.ops.allset.menu_run('EXEC_DEFAULT', op=op, item=item)

    def s_enter():
        ev('RET', 'PRESS')
        ev('RET', 'RELEASE')

    def s_check(item=item):
        z = bone().location.z
        check(f"{item}: runs and Enter keeps a pose other than the unkeyed 5.0 (z = {z:.3f}, {S['ret']})",
              S["ret"] == {'FINISHED'} and abs(z - 5.0) > 1e-3)

    for fn in (s_off, s_run, lambda: None, s_enter, lambda: None, s_check):
        step(fn)


run()
