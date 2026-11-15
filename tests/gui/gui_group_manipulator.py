"""Real group Move, Rotate and Scale handle drags with Show > Locators off."""
import math
import os
import sys
from importlib import import_module

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, view3d, win

C = {}


def root():
    return bpy.data.objects['fix']


def mp():
    return import_module(MODULE + '.ui.manipulator')


def tool(name):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.tool_set_by_id(name=name)
    area.tag_redraw()


def screen():
    _, region = view3d()
    p = location_3d_to_region_2d(region, region.data, root().matrix_world.translation)
    return p + Vector((region.x, region.y))


def length():
    return mp().ARROW_PX * bpy.context.preferences.view.gizmo_size / 75 * bpy.context.preferences.system.ui_scale


def drag(points, cancel=False):
    @step
    def hover():
        C['points'] = points()
        p = C['points'][0]
        ev('MOUSEMOVE', 'NOTHING', x=round(p.x), y=round(p.y))

    @step
    def press():
        p = C['points'][0]
        ev('LEFTMOUSE', 'PRESS', x=round(p.x), y=round(p.y))

    @step
    def start():
        p = C['points'][0].lerp(C['points'][1], .15)
        ev('MOUSEMOVE', 'NOTHING', x=round(p.x), y=round(p.y))

    @step
    def move():
        a, b = C['points']
        for i in range(2, 11):
            p = a.lerp(b, i / 10)
            ev('MOUSEMOVE', 'NOTHING', x=round(p.x), y=round(p.y))

    @step
    def release():
        p = C['points'][1]
        if cancel:
            ev('ESC', 'PRESS', x=round(p.x), y=round(p.y))
            ev('ESC', 'RELEASE', x=round(p.x), y=round(p.y))
        ev('LEFTMOUSE', 'RELEASE', x=round(p.x), y=round(p.y))


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_group():
    bpy.ops.allset.keymap_activate()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.mesh.primitive_cube_add(size=.02)
        bpy.context.active_object.name = 'body'
        bpy.ops.allset.group()
        bpy.context.active_object.name = 'fix'
        bpy.ops.view3d.view_axis(type='FRONT')
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = .15
        area.spaces.active.show_object_viewport_empty = False
        bpy.ops.ed.undo_push(message='Group fixture')
    tool('builtin.move')


@step
def s_poll():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        check('Move handles exist at the hidden group pivot', mp().ALLSET_GGT_xform.poll(bpy.context)
              and mp().pivot_frame(bpy.context, 'TRANSLATE')[0].length < 1e-6)
        check('only group selected, locator axes hidden', bpy.context.selected_objects == []
              and list(bpy.context.view_layer.objects.selected) == [root()])


drag(lambda: (screen() + Vector((length() * .6, 0)), screen() + Vector((length() * .6 + 60, 0))))


@step
def s_move_check():
    child = bpy.data.objects['body']
    check(f'Move arrow transforms group and child once ({root().location.x:.5f})', root().location.x > .001
          and abs(root().location.y) < 1e-6 and abs(root().location.z) < 1e-6
          and (child.matrix_world.translation - root().matrix_world.translation).length < 1e-6)
    C['moved'] = root().location.copy()
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_undo_check():
    check('one Undo restores the group move', root().location.length < 1e-6)
    ev('Z', 'PRESS', ctrl=True, shift=True)
    ev('Z', 'RELEASE', ctrl=True, shift=True)


@step
def s_redo_check():
    check('one Redo reapplies the group move', (root().location - C['moved']).length < 1e-6)
    tool('builtin.rotate')


def rotate_points():
    radius = length() * mp().ROTATE_RING_R * mp().VIEW_RING
    return tuple(screen() + radius * Vector((math.cos(a), math.sin(a))) for a in (.6, 1.6))


drag(rotate_points)


@step
def s_rotate_check():
    check('Rotate ring transforms the group', root().rotation_euler.to_quaternion().angle > .1)
    tool('builtin.scale')


drag(lambda: (screen(), screen() + Vector((45, 0))), cancel=True)


@step
def s_cancel_check():
    check('Escape restores group scale after a drag', (root().scale - Vector((1, 1, 1))).length < 1e-6)


drag(lambda: (screen(), screen() + Vector((45, 0))))


@step
def s_scale_check():
    check(f'Scale centre changes group uniformly ({tuple(root().scale)})', min(root().scale) > 1.1
          and max(root().scale) - min(root().scale) < 1e-5)
    check('children remain unselected and axes stay hidden', not bpy.data.objects['body'].select_get()
          and not view3d()[0].spaces.active.show_object_viewport_empty)
    tool('builtin.select_box')


@step
def s_select_check():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        check('Select tool does not show the transform manipulator', not mp().ALLSET_GGT_xform.poll(bpy.context))


run()
