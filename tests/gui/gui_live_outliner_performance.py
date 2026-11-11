"""Twenty live rows in the kit's Outliner tree: drawn green, and a redraw stays cheap (no row scan)."""
import os
import statistics
import sys
import time
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, view3d, win

C = {}


def outliner():
    area = next(a for a in win().screen.areas if a.type == 'OUTLINER')
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def redraw(iterations):
    area, region = outliner()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        start = time.perf_counter()
        bpy.ops.wm.redraw_timer(type='DRAW', iterations=iterations)
        return (time.perf_counter()-start)*1000/iterations


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_references():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        for i in range(20):
            bpy.ops.mesh.primitive_cube_add(size=.1, location=(i*.2, 0, 0))
            bpy.context.object.name = f'Reference{i:02}'
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = None
    C['names'] = {ob.name for ob in bpy.context.scene.objects}


@step
def s_baseline():
    redraw(2)
    C['baseline'] = statistics.median(redraw(6) for _ in range(3))
    import_module(MODULE+'.operators.live').set_objects(bpy.context.scene, list(bpy.context.scene.objects))


@step
def s_measure():
    tree = import_module(MODULE+'.ui.outliner_tree')
    live = import_module(MODULE+'.operators.live')
    cold = []
    for _ in range(3):
        tree._cache.clear()
        cold.append(redraw(1))
    warm = statistics.median(redraw(6) for _ in range(3))
    area, region = outliner()
    lives = set(live.objects(bpy.context.scene))
    with bpy.context.temp_override(window=win(), area=area, region=region):
        rows = tree.rows_for(bpy.context, area.spaces.active)
    names = {row.ob for row in rows if row.kind == 'OBJECT' and tree.row_state(bpy.context, row, lives)[3]}
    check('all twenty similar live rows are drawn live', names == C['names'])
    check(f'live rows redraw cheaply ({warm:.2f}ms, baseline {C["baseline"]:.2f}ms)',
          warm < max(20, C['baseline']*8))
    check(f'a redraw that rebuilds the rows stays cheap ({statistics.median(cold):.2f}ms)',
          statistics.median(cold) < max(150, C['baseline']*25))


run()
