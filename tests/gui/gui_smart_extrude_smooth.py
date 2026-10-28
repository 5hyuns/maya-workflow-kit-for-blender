"""Gizmo follows each mouse event even while an expensive Boolean preview is deferred."""
import os
import sys
import time
from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d, win

C = {}


def mod(name):
    return import_module(MODULE+'.'+name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def bm():
    return bmesh.from_edit_mesh(bpy.context.edit_object.data)


@step
def s_setup():
    mouse = setup()
    with override():
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects['Cube']
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.context.scene.unit_settings.system = 'NONE'
        bpy.context.tool_settings.use_snap = False
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        max(bm().faces, key=lambda f: f.calc_center_median().z).select_set(True)
        bmesh.update_edit_mesh(ob.data)
        bpy.ops.wm.tool_set_by_id(name=mod('operators.smart_extrude').TOOL)
    ev('MOUSEMOVE', 'NOTHING', x=mouse[0], y=mouse[1])


@step
def s_invoke():
    with override():
        bpy.ops.allset.smart_extrude_drag('INVOKE_DEFAULT', kind='TRANSLATE', axis=2)
    drag = mod('operators.smart_extrude').DRAG
    check('preview timer no longer imposes a 10 Hz floor', drag._timer.time_step <= 1/60+1e-5)
    check('free drag has no increment snap enabled', not drag._step_held and not drag._baseline_step)
    # Hold mesh evaluation back deliberately. This must never hold the handles.
    drag._interval, drag._last_time = 1000., time.monotonic()
    C['before'] = bm().calc_volume()


for i in range(1, 5):
    @step
    def move(i=i):
        drag = mod('operators.smart_extrude').DRAG
        _area, region = view3d()
        C['end'] = (region.x+round(drag._mouse[0]+drag._screen_axis.x*8*i),
                    region.y+round(drag._mouse[1]+drag._screen_axis.y*8*i))
        ev('MOUSEMOVE', 'NOTHING', x=C['end'][0], y=C['end'][1])

    @step
    def inspect(i=i):
        drag = mod('operators.smart_extrude').DRAG
        check(f'move {i}: geometry evaluation is still deferred', drag._pending and bm().calc_volume() == C['before'])
        with override():
            centre, _axes = mod('ui.smart_extrude').widget_frame(bpy.context)
            expected = drag._session.centre + drag._session.axes @ (Vector(drag.translation)*drag._session.unit)
            check(f'move {i}: gizmo follows this mouse event instead of the last Boolean tick',
                  (centre-expected).length < 1e-6 and centre.z > C.get('previous_z', 1.))
            C['previous_z'] = centre.z
        check(f'move {i}: free translation keeps fractional precision', abs(drag.translation[2]-round(drag.translation[2])) > 1e-4)


@step
def s_release():
    ev('LEFTMOUSE', 'RELEASE', x=C['end'][0], y=C['end'][1])


@step
def s_done():
    check('release evaluates and commits the final exact transform', mod('operators.smart_extrude').DRAG is None
          and bm().calc_volume() > C['before']+.01 and all(e.is_manifold for e in bm().edges))


run()
