"""#572: in Multi-Component mode (F7) the pre-selection highlight picks the vertex, edge or face under the mouse,
like Maya (it showed vertices only)."""
import os
import sys
from importlib import import_module

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win

C = {}


@step
def s_setup():
    setup()
    cube = bpy.data.objects["Cube"]
    for o in bpy.context.view_layer.objects:
        o.select_set(o is cube)
    bpy.context.view_layer.objects.active = cube
    tap('F7')


@step
def s_probe():
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    pre = import_module(MODULE + '.operators.preselect')
    out = {}
    with bpy.context.temp_override(window=win(), area=area, region=region):
        for name, p in (("vertex", (1, -1, 1)), ("edge mid", (0, -1, 1)), ("face centre", (0, 0, 1))):
            xy = location_3d_to_region_2d(region, rv3d, Vector(p))
            t = pre.pick(bpy.context, region, rv3d, (round(xy.x), round(xy.y)))
            out[name] = None if t is None else t[1]

    check(f"multi preselect {out}", out == {"vertex": 'VERT', "edge mid": 'EDGE', "face centre": 'FACE'})


run()
