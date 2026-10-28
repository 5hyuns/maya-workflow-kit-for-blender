"""Twenty live labels stay identifiable without the former ~265ms redraw scan."""
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
    labels = import_module(MODULE+'.ui.outliner_joints')
    cold = []
    for _ in range(3):
        labels._rows.clear()
        cold.append(redraw(1))
    warm = statistics.median(redraw(6) for _ in range(3))
    _, region = outliner()
    names = {name for name, _label in labels.SEEN.get(region.as_pointer(), ())}
    check('all twenty similar live names remain correctly identified', names == C['names'])
    check(f'unchanged live labels redraw without the full search ({warm:.2f}ms, baseline {C["baseline"]:.2f}ms)',
          warm < max(20, C['baseline']*8))
    check(f'uncached row matching avoids the old 265ms stall ({statistics.median(cold):.2f}ms)',
          statistics.median(cold) < max(75, C['baseline']*25))


run()
