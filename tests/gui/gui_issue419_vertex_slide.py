"""#419 in a real UI, Move tool in vertex mode: Ctrl+Shift+drag on a manipulator handle slides the selected vertices
along their edges, like Maya (one corner vertex, then two vertices of the top face); a plain drag on the same handle
still moves along the handle's axis."""
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, view3d, win, MODULE  # noqa: E402

C = {}
SLIDES = ('TRANSFORM_OT_vert_slide', 'TRANSFORM_OT_edge_slide')


def mod(name):
    return import_module(MODULE + '.' + name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def bm():
    return bmesh.from_edit_mesh(bpy.context.edit_object.data)


def coords():
    b = bm()
    b.verts.ensure_lookup_table()
    return [v.co.copy() for v in b.verts]


def on_an_edge(co):
    """A cube vertex slid along one of its edges keeps two of its three coordinates at +-1 and stays in the cube."""
    return sum(abs(abs(c) - 1.0) < 1e-4 for c in co) >= 2 and all(abs(c) <= 1.0 + 1e-4 for c in co)


def running(names):
    return any(op.bl_idname in names for op in win().modal_operators)


def moved_points():
    after = coords()
    return [(i, after[i]) for i, (a, b) in enumerate(zip(C['before'], after)) if (a - b).length > 1e-3]


def select_verts(pick):
    with override():
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')
        b = bm()
        for v in b.verts:
            if pick(v.co):
                v.select_set(True)
        b.select_flush_mode()
        bmesh.update_edit_mesh(bpy.context.edit_object.data)
    C['before'] = coords()


def reset():
    with override():
        b = bm()
        b.verts.ensure_lookup_table()
        for v, co in zip(b.verts, C['start']):
            v.co = co
        b.normal_update()
        bmesh.update_edit_mesh(bpy.context.edit_object.data)


def screen(world):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, world)
    return Vector((region.x + p.x, region.y + p.y))


def z_arrow():
    """Window point on the Move manipulator's Z arrow (a little past half way) of the current selection."""
    with override():
        centre, frame, _otype = mod('ui.manipulator').pivot_frame(bpy.context, 'TRANSLATE')
        _area, region = view3d()
        size = region.data.view_distance * 0.02
        p0, p1 = screen(centre), screen(centre + frame.col[2].normalized() * size)
        n = mod('ui.manipulator').ARROW_PX * bpy.context.preferences.view.gizmo_size / 75.0 * \
            bpy.context.preferences.system.ui_scale
    return p0 + (p1 - p0).normalized() * n * 0.6


def drag(prefix, mods, delta, ops):
    """Steps: hover the Z arrow, modifier keys + LMB press, moves, release + keys up."""
    keys = {"ctrl": "LEFT_CTRL", "shift": "LEFT_SHIFT"}
    kw = {m: True for m in mods}

    def hover():
        C['a'] = z_arrow()
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x), y=int(C['a'].y))
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x) + 1, y=int(C['a'].y))

    def press():
        held = {}
        for m in mods:
            held[m] = True
            ev(keys[m], 'PRESS', **held)
        ev('LEFTMOUSE', 'PRESS', x=int(C['a'].x), y=int(C['a'].y), **kw)

    def move1():
        q = C['a'] + delta * 0.25
        ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), **kw)

    def move2():
        C[prefix + '_running'] = running(ops)
        for f in (0.5, 0.75, 1.0):
            q = C['a'] + delta * f
            ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), **kw)

    def release():
        q = C['a'] + delta
        ev('LEFTMOUSE', 'RELEASE', x=int(q.x), y=int(q.y), **kw)
        for m in reversed(mods):
            ev(keys[m], 'RELEASE')
    for f in (hover, press, move1, move2, release):
        f.__name__ = f"s_{prefix}_{f.__name__}"
        step(f)


def corner(co):
    return co.x > 0.9 and co.y > 0.9 and co.z > 0.9


def top_pair(co):
    return co.x > 0.9 and co.z > 0.9


@step
def s_setup():
    C['mouse'] = setup()
    with override():
        ob = bpy.data.objects['Cube']
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.context.tool_settings.use_snap = False
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.tool_set_by_id(name='builtin.move')
        region = view3d()[1]
        region.data.view_rotation = Quaternion((0.82, 0.42, 0.17, 0.34))
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = 9
        mod('preferences').get(bpy.context).transform_constraint = 'NONE'
    C['start'] = coords()
    select_verts(corner)


# a sideways drag: the Z arrow alone would hardly move the vertex, a slide moves it along one of its edges
drag('one', ('ctrl', 'shift'), Vector((-60, -10)), SLIDES)


@step
def s_one_check():
    moved = moved_points()
    check(f"Ctrl+Shift+drag on the Z arrow runs a slide in vertex mode ({C.get('one_running')})",
          C.get('one_running'))
    check(f"the corner vertex moved along one of its edges ({[tuple(round(c, 3) for c in co) for _i, co in moved]})",
          len(moved) == 1 and on_an_edge(moved[0][1]))
    reset()
    select_verts(top_pair)


drag('two', ('ctrl', 'shift'), Vector((-60, -10)), SLIDES)


@step
def s_two_check():
    moved = moved_points()
    check(f"Ctrl+Shift+drag slides two selected vertices too ({C.get('two_running')})", C.get('two_running'))
    check(f"both vertices moved and stay on cube edges ({[tuple(round(c, 3) for c in co) for _i, co in moved]})",
          len(moved) == 2 and all(on_an_edge(co) for _i, co in moved))
    reset()
    select_verts(corner)


# the plain drag on the same handle (straight down the arrow) is a move along Z, not a slide
drag('plain', (), Vector((0, -40)), SLIDES)


@step
def s_plain_check():
    moved = moved_points()
    d = moved[0][1] - C['before'][moved[0][0]] if moved else Vector()
    check(f"a plain drag on the Z arrow runs no slide ({C.get('plain_running')})", not C.get('plain_running'))
    check(f"... and moves the vertex along Z only ({tuple(round(c, 3) for c in d)})",
          len(moved) == 1 and abs(d.x) < 1e-4 and abs(d.y) < 1e-4 and abs(d.z) > 1e-3)
    reset()


run()
