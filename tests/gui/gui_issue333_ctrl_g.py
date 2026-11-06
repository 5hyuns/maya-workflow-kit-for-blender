"""#333, real key events: Ctrl+G groups the selection and G repeats that grouping (Maya: G = Repeat Last,
Ctrl+G = Group). Each G puts the newest group under the next one, and Edit > Repeat names the command."""
import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win  # noqa: E402

rep = import_module(MODULE + '.operators.repeat_maya')


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def hover():
    area, region = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 2)


def ctrl_g():
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    ev('G', 'PRESS', ctrl=True)
    ev('G', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


def groups():
    return sorted(o.name for o in bpy.context.scene.objects if o.type == 'EMPTY' and o.name.startswith('group'))


def parent_of(name):
    ob = bpy.data.objects.get(name)
    return ob.parent.name if ob is not None and ob.parent is not None else None


@step
def prepare():
    setup()
    with override():
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        bpy.ops.allset.menu_item(item='Create/Polygon Primitives/Cube', clicked=True)
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    hover()
    ctrl_g()


@step
def after_ctrl_g():
    check('Ctrl+G groups the cube under group1', groups() == ['group1'] and parent_of('pCube1') == 'group1')
    check('Edit > Repeat reads Repeat "Group"', rep.label(bpy.context) == 'Repeat "Group"')
    hover()
    tap('G')


@step
def after_g():
    check('G repeats the grouping: group1 goes under group2',
          groups() == ['group1', 'group2'] and parent_of('group1') == 'group2' and parent_of('pCube1') == 'group1')
    check('the new group is the selection', bpy.context.active_object is not None
          and bpy.context.active_object.name == 'group2')
    hover()
    tap('G')


@step
def after_second_g():
    check('G again: group2 under group3', groups() == ['group1', 'group2', 'group3'] and parent_of('group2') == 'group3')


run()
