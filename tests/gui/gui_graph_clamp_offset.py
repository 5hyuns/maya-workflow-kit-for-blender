"""Graph Editor Curves > Clamp Curves / Offset Curves run from the Maya menu in a real Graph Editor, and their option
box opens the settings (Adjust Last Operation)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, step, setup, view3d, win, load_maya_layout  # noqa: E402

C = {}


def region():
    return next(r for r in C["area"].regions if r.type == 'WINDOW')


def curve():
    return import_module(MODULE + ".compat").id_fcurve_collection(bpy.data.objects["pCube1"]).find("location", index=0)


def menu(item):
    with bpy.context.temp_override(window=win(), area=C["area"], region=region()):
        return bpy.ops.allset.menu_item(item=item)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    area, reg = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=reg):
        bpy.ops.allset.create(kind='CUBE')
    ob = bpy.data.objects["pCube1"]
    for f, v in ((1, -2.0), (10, 3.0), (20, 5.0)):
        ob.location.x = v
        ob.keyframe_insert("location", index=0, frame=f)
    C["area"] = area
    area.ui_type = 'FCURVES'


@step
def s_wait():
    pass


@step
def s_clamp():
    for kp in curve().keyframe_points:
        kp.select_control_point = kp.co.x > 5
    r = menu("Graph Editor/Curves/Clamp Curves")
    vals = [round(kp.co.y, 3) for kp in curve().keyframe_points]
    check(f"Clamp Curves from the menu ({r}): selected keys above 0 become 0 ({vals})", vals == [-2.0, 0.0, 0.0])


@step
def s_offset():
    r = menu("Graph Editor/Curves/Offset Curves")
    times = [round(kp.co.x, 3) for kp in curve().keyframe_points]
    check(f"Offset Curves from the menu ({r}): selected keys one frame later ({times})", times == [1.0, 11.0, 21.0])
    bpy.ops.ed.undo()


@step
def s_undo():
    times = [round(kp.co.x, 3) for kp in curve().keyframe_points]
    check(f"one undo puts the offset back ({times})", times == [1.0, 10.0, 20.0])


run()
