"""D + V + MMB drag snaps a group's pivot onto a vertex of one of its children (step 312)."""
import os
import sys
from importlib import import_module

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win

C = {}


def mod(name):
    return import_module(MODULE+'.'+name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def screen(point):
    area, region = view3d()
    xy = location_3d_to_region_2d(region, area.spaces.active.region_3d, point)
    return region.x+round(xy.x), region.y+round(xy.y)


def move(point):
    ev('MOUSEMOVE', 'NOTHING', x=point[0], y=point[1])


def children_world():
    return {ob.name: ob.matrix_world.copy() for ob in bpy.data.objects if ob.parent is not None}


@step
def s_setup():
    setup()
    for ob in list(bpy.data.objects):
        if ob.name != 'Cube':
            bpy.data.objects.remove(ob)
    a = bpy.data.objects['Cube']
    a.location = (3, 0, 0)
    b = a.copy()
    b.data = a.data.copy()
    b.name = 'Cube2'
    b.location = (-3, 0, 1)
    bpy.context.collection.objects.link(b)
    for ob in (a, b):
        ob.select_set(True)
    bpy.context.view_layer.objects.active = a
    with override():
        bpy.ops.allset.group()
    C['group'] = bpy.context.view_layer.objects.active
    with override():
        bpy.ops.wm.tool_set_by_id(name='builtin.move')
    ts = bpy.context.tool_settings
    ts.use_snap = False
    C['snap'] = mod('operators.hold').GROUPS['snap'].capture(ts)
    area, _region = view3d()
    rv = area.spaces.active.region_3d
    rv.view_perspective, rv.view_distance = 'ORTHO', 14
    rv.view_rotation = Matrix.Rotation(.6, 3, 'X').to_quaternion()
    rv.view_location = (0, 0, 0)
    bpy.context.view_layer.update()
    # the target: a corner of the child Cube (not on the grid, not at the group's pivot)
    C['vertex'] = a.matrix_world @ a.data.vertices[0].co
    C['children'] = children_world()


@step
def s_pivot_mode():
    check('the group is an Empty with two children', C['group'].type == 'EMPTY' and len(C['group'].children) == 2)
    tap('D')


@step
def s_hold_v():
    check('D turns on pivot editing', bpy.context.tool_settings.use_transform_data_origin)
    C['start'] = screen(C['group'].matrix_world.translation + Vector((0, -.5, 0)))
    move(C['start'])
    ev('V', 'PRESS')


@step
def s_mmb_press():
    check('V holds a point snap', bpy.context.tool_settings.use_snap
          and 'VERTEX' in bpy.context.tool_settings.snap_elements)
    ev('MIDDLEMOUSE', 'PRESS')


@step
def s_drag():
    end = screen(C['vertex'])
    for i in range(1, 11):
        move((C['start'][0]+round((end[0]-C['start'][0])*i/10), C['start'][1]+round((end[1]-C['start'][1])*i/10)))


@step
def s_hover_end():
    move(screen(C['vertex']))


@step
def s_release():
    ev('MIDDLEMOUSE', 'RELEASE')


@step
def s_release_v():
    ev('V', 'RELEASE')


@step
def s_check():
    pivot = C['group'].matrix_world.translation
    check("the group's pivot snaps onto the child's vertex", (pivot - C['vertex']).length < 1e-4)
    now = children_world()
    check('the children stay in place', all(
        all(abs(now[k][i][j] - m[i][j]) < 1e-5 for i in range(4) for j in range(4)) for k, m in C['children'].items()))
    check("the group's channels stay (Maya: moving a pivot changes no channel)",
          Vector(C['group'].location).length < 1e-6)
    check('pivot editing is still on after the drag', bpy.context.tool_settings.use_transform_data_origin)
    check('the snap settings come back after V',
          mod('operators.hold').GROUPS['snap'].capture(bpy.context.tool_settings) == C['snap'])


run()
