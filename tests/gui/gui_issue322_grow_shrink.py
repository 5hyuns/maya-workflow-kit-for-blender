"""#322: in Edit Mode > and < grow / shrink the component selection: Shift+. / Shift+, on a US keyboard, and on a
keyboard with its own < > key, Shift+< > grows and < > shrinks."""

import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

C = {}


def main_view():
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D']
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def selected_faces():
    ob = bpy.data.objects["Plane"]
    ob.update_from_editmode()
    return sum(1 for p in ob.data.polygons if p.select)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=9, y_subdivisions=9, size=4)
    bpy.context.object.name = "Plane"
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    for f in bm.faces:
        f.select_set(False)
    bm.faces.ensure_lookup_table()
    centre = min(bm.faces, key=lambda f: f.calc_center_median().length)
    centre.select_set(True)
    bmesh.update_edit_mesh(bpy.context.object.data)
    _area, region = main_view()
    C["xy"] = (region.x + region.width // 2, region.y + region.height // 2)
    ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])


def key(label, type, shift, expect):
    def before():
        C["n0"] = selected_faces()

    def press():
        x, y = C["xy"]
        if shift:
            ev('LEFT_SHIFT', 'PRESS', shift=True, x=x, y=y)
        ev(type, 'PRESS', shift=shift, x=x, y=y)
        ev(type, 'RELEASE', shift=shift, x=x, y=y)
        if shift:
            ev('LEFT_SHIFT', 'RELEASE', x=x, y=y)

    def verify():
        n = selected_faces()
        grew = n > C["n0"] if expect == "grow" else n < C["n0"]
        check(f"{label}: {expect} ({C['n0']} -> {n} faces)", grew)

    for fn in (before, press, verify):
        step(fn)


key("Shift+.", 'PERIOD', True, "grow")
key("Shift+< > key", 'GRLESS', True, "grow")
key("Shift+,", 'COMMA', True, "shrink")
key("< > key", 'GRLESS', False, "shrink")

run()
