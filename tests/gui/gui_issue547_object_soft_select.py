"""#547: with soft select on, moving a new primitive in object mode moves only that object (soft select's Volume /
Surface falloff acts on components, not on whole objects); soft select stays on for component mode."""
import os
import sys
from importlib import import_module

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win  # noqa: E402

C = {}


def mod(name):
    return import_module(MODULE + '.' + name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def screen(point):
    area, region = view3d()
    xy = location_3d_to_region_2d(region, area.spaces.active.region_3d, point)
    return region.x + round(xy.x), region.y + round(xy.y)


def move(point):
    ev('MOUSEMOVE', 'NOTHING', x=point[0], y=point[1])


@step
def s_setup():
    setup()
    for ob in list(bpy.data.objects):
        if ob.name != 'Cube':
            bpy.data.objects.remove(ob)
    old = bpy.data.objects['Cube']
    old.location = (2, 0, 0)
    C['old'] = old.name
    with override():
        bpy.ops.allset.create(kind='SPHERE')
    C['new'] = bpy.context.view_layer.objects.active.name
    ts = bpy.context.tool_settings
    ts.use_snap = False
    area, _region = view3d()
    rv = area.spaces.active.region_3d
    rv.view_perspective, rv.view_distance = 'ORTHO', 14
    rv.view_rotation = Matrix.Rotation(.6, 3, 'X').to_quaternion()
    rv.view_location = (0, 0, 0)
    bpy.context.view_layer.update()
    C['old_m'] = old.matrix_world.copy()
    C['start'] = screen(Vector((0, -3, 0)))
    move(C['start'])
    tap('W')


@step
def s_soft_on():
    check('only the new primitive is selected',
          [o.name for o in bpy.context.selected_objects] == [C['new']])
    tap('B')


@step
def s_press():
    check('B turns soft select on', mod('operators.soft_select').is_on())
    ev('MIDDLEMOUSE', 'PRESS')


@step
def s_drag():
    for i in range(1, 11):
        move((C['start'][0] - 12 * i, C['start'][1]))


@step
def s_release():
    ev('MIDDLEMOUSE', 'RELEASE')


@step
def s_check():
    new = bpy.data.objects[C['new']]
    old = bpy.data.objects[C['old']]
    check('the new primitive moved', new.matrix_world.translation.length > 0.2)
    check('the other object stays where it was',
          all(abs(old.matrix_world[i][j] - C['old_m'][i][j]) < 1e-6 for i in range(4) for j in range(4)))
    check('soft select is still on', mod('operators.soft_select').is_on()
          and bpy.context.tool_settings.use_proportional_edit)
    tap('B')


run()
