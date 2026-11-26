"""#571 in the UV Editor: a B tap turns soft select on (and the next tap off), and B held + a left-mouse drag to the
right makes the falloff radius larger; the 3D View follows the same state."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d, win  # noqa: E402

C = {}


def mod(name):
    return import_module(MODULE + name)


def cube():
    return bpy.data.objects["Cube"]


def uv_centre():
    area = C["uv_area"]
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return region.x + region.width // 2, region.y + region.height // 2


def soft_on():
    return mod(".operators.soft_select").is_on()


@step
def s_setup():
    C["x"], C["y"] = setup()
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set('EXEC_DEFAULT', True, mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
    uv = max((a for a in win().screen.areas if a.type == 'PROPERTIES'), key=lambda a: a.height)
    uv.type = 'IMAGE_EDITOR'
    uv.ui_type = 'UV'
    C["uv_area"] = uv
    mod(".operators.soft_select").set_on(False)
    bpy.context.scene.tool_settings.proportional_size = 0.1


@step
def s_tap():
    x, y = uv_centre()
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('B', 'PRESS', x=x, y=y)
    ev('B', 'RELEASE', x=x, y=y)


@step
def s_tap_check():
    check("B tap in the UV Editor turns soft select on", soft_on()
          and bpy.context.scene.tool_settings.use_proportional_edit)
    x, y = uv_centre()
    ev('B', 'PRESS', x=x, y=y)


@step
def s_hold_press():
    x, y = uv_centre()
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


@step
def s_hold_drag():
    x, y = uv_centre()
    ev('MOUSEMOVE', 'NOTHING', x=x + 50, y=y)


@step
def s_hold_drag2():
    x, y = uv_centre()
    ev('MOUSEMOVE', 'NOTHING', x=x + 100, y=y)


@step
def s_hold_release():
    x, y = uv_centre()
    ev('LEFTMOUSE', 'RELEASE', x=x + 100, y=y)
    ev('B', 'RELEASE', x=x + 100, y=y)


@step
def s_hold_check():
    size = bpy.context.scene.tool_settings.proportional_size
    check(f"B + left-mouse drag to the right makes the radius larger ({size:.4f})", size > 0.15)
    check("a B drag leaves soft select on", soft_on())
    x, y = uv_centre()
    ev('B', 'PRESS', x=x, y=y)
    ev('B', 'RELEASE', x=x, y=y)


@step
def s_off_check():
    check("the next B tap turns it off", not soft_on()
          and not bpy.context.scene.tool_settings.use_proportional_edit)


run()
