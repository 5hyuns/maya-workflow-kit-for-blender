"""#387: in a real UI, Ctrl+RMB on a vertex (Convert Selection) and a stroke straight down that keeps moving goes
over "To Faces" (a radial submenu) to the list row "To Shell" under it; the release converts the vertex to its
shell. A rest on "To Faces" opens its submenu, and a quick stroke released on "To Faces" closes the menu and runs
nothing, like Maya."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap  # noqa: E402

C = {}


def draw():
    return import_module(MODULE + ".marking.draw")


def session():
    return draw().ACTIVE.get("session")


def center_of(rect, s, level=0):
    _lay, (cx, cy) = s.stack[level]
    ox, oy = draw().ACTIVE["origin"]
    return (ox + round(cx + (rect[0] + rect[2]) / 2), oy + round(cy + (rect[1] + rect[3]) / 2))


def label(s):
    it = s.hover[0] if s is not None else None
    return it.label if it is not None else None


def selected_verts():
    ob = bpy.context.edit_object
    bm = bmesh.from_edit_mesh(ob.data)
    return sum(1 for v in bm.verts if v.select)


def one_vertex():
    ob = bpy.context.edit_object
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.select = False
    bm.select_flush(False)
    bm.verts.ensure_lookup_table()
    bm.verts[0].select = True
    bm.select_flush(True)
    bmesh.update_edit_mesh(ob.data)


@step
def s_setup():
    C["x"], C["y"] = setup()
    cube = bpy.data.objects["Cube"]
    for o in bpy.context.view_layer.objects:
        o.select_set(o == cube)
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(4.0, 0.0, 0.0))     # a second shell in the same mesh
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    one_vertex()
    C["total"] = len(bmesh.from_edit_mesh(bpy.context.edit_object.data).verts)
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])


@step
def s_press():
    check(f"one vertex selected ({selected_verts()} of {C['total']})", selected_verts() == 1)
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"], ctrl=True)


@step
def s_stroke():
    s = session()
    check("Ctrl+RMB opens the Convert Selection marking menu", s is not None and s.stack[0][0].sub.label
          == "Convert Selection")
    if s is None:
        return
    lay = s.stack[0][0]
    shell = next(it for it in lay.items if it.label == "To Shell")
    C["shell"] = center_of(shell.rect, s)
    # one stroke within one tick: no rest on the way
    x0, y0 = C["x"], C["y"]
    x1, y1 = C["shell"]
    n = 12
    for k in range(1, n + 1):
        ev('MOUSEMOVE', 'NOTHING', x=round(x0 + (x1 - x0) * k / n), y=round(y0 + (y1 - y0) * k / n), ctrl=True)


@step
def s_over_list():
    s = session()
    ok = s is not None
    check(f"the stroke went over To Faces: no submenu opened ({len(s.stack) if ok else None} level(s))",
          ok and len(s.stack) == 1)
    check(f"To Shell is hovered ({label(s)})", label(s) == "To Shell")
    ev('RIGHTMOUSE', 'RELEASE', x=C["shell"][0], y=C["shell"][1], ctrl=True)


@step
def s_shell():
    n = selected_verts()
    check(f"the release runs To Shell: the vertex's whole shell is selected ({n} of {C['total']})",
          n == C["total"] // 2 and not draw().ACTIVE)
    one_vertex()
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"], ctrl=True)


@step
def s_to_faces():
    s = session()
    if s is None:
        check("Ctrl+RMB opens the menu again", False)
        return
    it = s.stack[0][0].radial["S"]
    C["faces"] = center_of(it.rect, s)
    ev('MOUSEMOVE', 'NOTHING', x=(C["x"] + C["faces"][0]) // 2, y=(C["y"] + C["faces"][1]) // 2, ctrl=True)
    ev('MOUSEMOVE', 'NOTHING', x=C["faces"][0], y=C["faces"][1], ctrl=True)


@step
def s_rested():
    s = session()
    ok = s is not None and len(s.stack) == 2
    check("a rest on To Faces opens its submenu", ok)
    if ok:
        labels = sorted(it.label for it in s.layout.items)
        check(f"the submenu: To Faces / To Contained Faces / To Face Perimeter ({labels})",
              labels == ["To Contained Faces", "To Face Perimeter", "To Faces"])
    tap('ESC')
    tap('ESC')
    ev('RIGHTMOUSE', 'RELEASE', ctrl=True)


@step
def s_closed():
    check("Esc closes the menu", not draw().ACTIVE)
    one_vertex()
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"], ctrl=True)


@step
def s_quick_to_faces():
    s = session()
    if s is None:
        check("Ctrl+RMB opens the menu a third time", False)
        return
    it = s.stack[0][0].radial["S"]
    fx, fy = center_of(it.rect, s)
    # a quick stroke onto To Faces and the release, within one tick: no rest on it
    for k in range(1, 7):
        ev('MOUSEMOVE', 'NOTHING', x=round(C["x"] + (fx - C["x"]) * k / 6), y=round(C["y"] + (fy - C["y"]) * k / 6),
           ctrl=True)
    ev('RIGHTMOUSE', 'RELEASE', x=fx, y=fy, ctrl=True)


@step
def s_quick_closed():
    check("a quick stroke released on To Faces closes the menu (no click mode)", not draw().ACTIVE)
    n = selected_verts()
    check(f"... and runs nothing: still one vertex ({n} of {C['total']})", n == 1)
    if draw().ACTIVE:
        tap('ESC')
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


run()
