"""Pick actual Smart Extrude rotation rings/scale boxes; verify angular drag and momentary J."""
import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win

C = {}


def mod(name):
    return import_module(MODULE+'.'+name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def bm():
    return bmesh.from_edit_mesh(bpy.context.edit_object.data)


def handle_point(kind, axis, point):
    gz = next(g for g, k, a in C['group'].handles if (k, a) == (kind, axis))
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, gz.matrix_world @ Vector(point))
    return round(region.x+p.x), round(region.y+p.y)


def move(point):
    ev('MOUSEMOVE', 'NOTHING', x=point[0], y=point[1])


@step
def s_setup():
    mouse = setup()
    ui = mod('ui.smart_extrude')
    original = ui.ALLSET_GGT_smart_extrude.draw_prepare
    def spy(self, context):
        C['group'] = self
        original(self, context)
    ui.ALLSET_GGT_smart_extrude.draw_prepare = spy
    with override():
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects['Cube']
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.context.scene.unit_settings.system = 'NONE'
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        max(bm().faces, key=lambda f: f.calc_center_median().z).select_set(True)
        bmesh.update_edit_mesh(ob.data)
        bpy.ops.allset.smart_extrude(translation=(0, 0, 1))
        bpy.ops.wm.tool_set_by_id(name=mod('operators.smart_extrude').TOOL)
        area, region = view3d()
        region.data.view_rotation = Quaternion((1, 0, 0, 0))
        region.data.view_location = (0, 0, 1)
        region.data.view_distance = 8
        C['before'] = mod('operators.smart_extrude').signature(bm())
        C['snap'] = mod('operators.hold').GROUPS['snap'].capture(bpy.context.tool_settings)
    move(mouse)


@step
def s_wait_draw():
    view3d()[0].tag_redraw()


@step
def s_ring_hover():
    C['start'] = handle_point('ROTATE', 'Z', (math.cos(.6), math.sin(.6), 0))
    C['end'] = handle_point('ROTATE', 'Z', (math.cos(1.1), math.sin(1.1), 0))
    move(C['start'])


@step
def s_ring_press():
    ev('LEFTMOUSE', 'PRESS', x=C['start'][0], y=C['start'][1])


@step
def s_ring_drag():
    for i in range(1, 9):
        move((round(C['start'][0]+(C['end'][0]-C['start'][0])*i/8),
              round(C['start'][1]+(C['end'][1]-C['start'][1])*i/8)))


@step
def s_ring_preview():
    drag = mod('operators.smart_extrude').DRAG
    check('actual Z ring starts the rotate operator', drag is not None and drag.kind == 'ROTATE' and drag.axis == 2)
    check('ring drag measures the angular mouse movement', drag is not None and abs(drag.rotation[2]-.5) < .035)
    C['free_angle'] = drag.rotation[2]
    ev('J', 'PRESS')


@step
def s_ring_snap():
    drag = mod('operators.smart_extrude').DRAG
    increment = bpy.context.tool_settings.snap_angle_increment_3d
    check('J during a ring drag snaps to the configured angular increment', abs(drag.rotation[2]/increment-round(drag.rotation[2]/increment)) < 1e-5)
    with override():
        centre, axes = mod('ui.smart_extrude').widget_frame(bpy.context)
        for gz, kind, axis in C['group'].handles:
            if kind == 'TRANSLATE':
                check('live '+axis+' arrow follows the rotated frame', gz.matrix_basis.to_3x3().col[2].dot(axes.col['XYZ'.index(axis)]) > .9999)
    ev('J', 'RELEASE')


@step
def s_ring_unsnap():
    drag = mod('operators.smart_extrude').DRAG
    check('releasing J returns to free rotation immediately', abs(drag.rotation[2]-C['free_angle']) < 1e-5)
    tap('ESC')
    ev('LEFTMOUSE', 'RELEASE')


@step
def s_scale_hover():
    check('ring cancel restores exact geometry and component selection', mod('operators.smart_extrude').signature(bm()) == C['before'])
    C['start'] = handle_point('SCALE', 'X', (0, 0, 1))
    C['end'] = (C['start'][0]+30, C['start'][1])
    move(C['start'])


@step
def s_scale_press():
    ev('LEFTMOUSE', 'PRESS', x=C['start'][0], y=C['start'][1])


@step
def s_scale_drag():
    for i in range(1, 9):
        move((round(C['start'][0]+30*i/8), C['start'][1]))


@step
def s_scale_check():
    drag = mod('operators.smart_extrude').DRAG
    check('actual scale box invokes scaling rather than translation', drag is not None and drag.kind == 'SCALE' and drag.axis == 0)
    check('scale box edits the existing cap volume', bm().calc_volume() > 12.1 and max(v.co.x for v in bm().verts) > 1.2)
    tap('ESC')
    ev('LEFTMOUSE', 'RELEASE')


@step
def s_done():
    check('scale cancel restores the exact pre-drag result', mod('operators.smart_extrude').signature(bm()) == C['before'])
    check('Smart Extrude keeps the original snap preferences', mod('operators.hold').GROUPS['snap'].capture(bpy.context.tool_settings) == C['snap'])


run()
