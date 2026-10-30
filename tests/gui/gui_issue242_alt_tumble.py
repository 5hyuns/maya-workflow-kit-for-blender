"""Issue #242: Alt+LMB drag tumbles the view in the Maya layout with the Alt key really held (a keyboard Alt press
before the mouse, as a hand does), in object mode and edit mode, with Select, Move and Rotate tools, and with
the drag starting over an object or over empty space."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

C = {}


def main_view():
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D']
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.object.select_all(action='DESELECT')
    if "Cube" not in bpy.data.objects:
        bpy.ops.mesh.primitive_cube_add()
    area, region = main_view()
    rv = region.data
    rv.view_perspective = 'PERSP'
    C["region"] = region


CASES = [
    ("object, empty space, Select", 'OBJECT', "builtin.select_box", (0.15, 0.8)),
    ("object, over the cube, Select", 'OBJECT', "builtin.select_box", (0.5, 0.5)),
    ("object, Move tool", 'OBJECT', "builtin.move", (0.15, 0.8)),
    ("object, Rotate tool", 'OBJECT', "builtin.rotate", (0.5, 0.5)),
    ("edit, Select", 'EDIT', "builtin.select_box", (0.5, 0.5)),
    ("edit, Move tool", 'EDIT', "builtin.move", (0.15, 0.8)),
]


def add_case(label, mode, tool, frac):
    def prepare():
        cube = bpy.data.objects["Cube"]
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = cube
        cube.select_set(True)
        if mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        area, region = main_view()
        with bpy.context.temp_override(window=win(), area=area, region=region):
            bpy.ops.wm.tool_set_by_id(name=tool)
        C["rot0"] = region.data.view_rotation.copy()
        x = region.x + int(region.width * frac[0])
        y = region.y + int(region.height * frac[1])
        C["xy"] = (x, y)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    def press():
        x, y = C["xy"]
        ev('LEFT_ALT', 'PRESS', alt=True, x=x, y=y)

    def drag1():
        x, y = C["xy"]
        ev('LEFTMOUSE', 'PRESS', alt=True, x=x, y=y)

    def drag2():
        x, y = C["xy"]
        ev('MOUSEMOVE', 'NOTHING', alt=True, x=x + 60, y=y + 20)

    def drag3():
        x, y = C["xy"]
        ev('MOUSEMOVE', 'NOTHING', alt=True, x=x + 120, y=y + 40)

    def release():
        x, y = C["xy"]
        ev('LEFTMOUSE', 'RELEASE', alt=True, x=x + 120, y=y + 40)
        ev('LEFT_ALT', 'RELEASE', x=x + 120, y=y + 40)

    def verify():
        _a, region = main_view()
        diff = C["rot0"].rotation_difference(region.data.view_rotation).angle
        check(f"Alt+LMB tumbles: {label} (turned {diff:.3f} rad)", diff > 0.05)

    for fn in (prepare, press, drag1, drag2, drag3, release, verify):
        step(fn)


for case in CASES:
    add_case(*case)

run()
