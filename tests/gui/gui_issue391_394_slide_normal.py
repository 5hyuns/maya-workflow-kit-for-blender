"""#391 / #394 in a real UI, Move tool in mesh edit mode: Ctrl+Shift+drag on a manipulator handle slides the
selected edge along the mesh (its vertices stay on the cube's edges), like Maya; Ctrl+middle-drag anywhere moves
the selection along its normal (a top face straight up, a corner vertex along its own normal)."""
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
    """A cube vertex slid along one of its edges keeps two of its three coordinates at +-1."""
    return sum(abs(abs(c) - 1.0) < 1e-4 for c in co) >= 2


def running(names):
    return any(op.bl_idname in names for op in win().modal_operators)


def select(kind, pick):
    """Select the cube's components of ``kind`` ('VERT' / 'EDGE' / 'FACE') for which ``pick(element)`` is true."""
    with override():
        bpy.ops.mesh.select_mode(type=kind)
        bpy.ops.mesh.select_all(action='DESELECT')
        b = bm()
        seq = {'VERT': b.verts, 'EDGE': b.edges, 'FACE': b.faces}[kind]
        for e in seq:
            if pick(e):
                e.select_set(True)
        b.select_flush_mode()
        bmesh.update_edit_mesh(bpy.context.edit_object.data)
    C['before'] = coords()


def reset():
    with override():
        b = bm()
        b.verts.ensure_lookup_table()
        for v, co in zip(b.verts, C['start']):
            v.co = co
        bmesh.update_edit_mesh(bpy.context.edit_object.data)


def screen(world):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, world)
    return Vector((region.x + p.x, region.y + p.y))


def z_arrow():
    """Window point on the Move manipulator's Z arrow (half way) of the current selection."""
    with override():
        centre, frame, _otype = mod('ui.manipulator').pivot_frame(bpy.context, 'TRANSLATE')
        _area, region = view3d()
        rv3d = region.data
        size = rv3d.view_distance * 0.02
        p0, p1 = screen(centre), screen(centre + frame.col[2].normalized() * size)
        n = mod('ui.manipulator').ARROW_PX * bpy.context.preferences.view.gizmo_size / 75.0 * \
            bpy.context.preferences.system.ui_scale
    return p0 + (p1 - p0).normalized() * n * 0.6


def drag(prefix, button, mods, start, delta, ops):
    """Steps: hover, modifier keys + press, moves, release + keys up."""
    keys = {"ctrl": "LEFT_CTRL", "shift": "LEFT_SHIFT"}
    kw = {m: True for m in mods}

    def hover():
        C['a'] = start()
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x), y=int(C['a'].y))
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x) + 1, y=int(C['a'].y))

    def press():
        held = {}
        for m in mods:
            held[m] = True
            ev(keys[m], 'PRESS', **held)
        ev(button, 'PRESS', x=int(C['a'].x), y=int(C['a'].y), **kw)

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
        ev(button, 'RELEASE', x=int(q.x), y=int(q.y), **kw)
        for m in reversed(mods):
            ev(keys[m], 'RELEASE')
    for f in (hover, press, move1, move2, release):
        f.__name__ = f"s_{prefix}_{f.__name__}"
        step(f)


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
    # the top edge at +X +Y... any top edge along Y at x = +1
    select('EDGE', lambda e: all(abs(v.co.x - 1) < 1e-4 and abs(v.co.z - 1) < 1e-4 for v in e.verts))


drag('slide', 'LEFTMOUSE', ('ctrl', 'shift'), z_arrow, Vector((0, -40)),
     ('TRANSFORM_OT_edge_slide', 'TRANSFORM_OT_vert_slide'))


@step
def s_slide_check():
    after = coords()
    moved = [i for i, (a, b) in enumerate(zip(C['before'], after)) if (a - b).length > 1e-4]
    check(f"Ctrl+Shift+drag on the Z arrow runs a slide ({C.get('slide_running')})", C.get('slide_running'))
    check(f"the edge's two vertices moved and stay on cube edges ({[tuple(round(c, 3) for c in after[i]) for i in moved]})",
          len(moved) == 2 and all(on_an_edge(after[i]) for i in moved))
    reset()
    select('FACE', lambda f: f.normal.z > 0.9)


def empty_spot():
    _a, r = view3d()
    return Vector((r.x + r.width * 0.25, r.y + r.height * 0.3))


drag('face', 'MIDDLEMOUSE', ('ctrl',), empty_spot, Vector((30, 60)), ('TRANSFORM_OT_shrink_fatten',))


@step
def s_face_check():
    after = coords()
    moved = [i for i, (a, b) in enumerate(zip(C['before'], after)) if (a - b).length > 1e-4]
    ds = [after[i] - C['before'][i] for i in moved]
    check(f"Ctrl+MMB runs a move along normals ({C.get('face_running')})", C.get('face_running'))
    check(f"the top face moved straight along its normal ({[tuple(round(c, 3) for c in d) for d in ds]})",
          len(moved) == 4 and all(abs(d.x) < 1e-4 and abs(d.y) < 1e-4 for d in ds)
          and all(abs(d.z - ds[0].z) < 1e-4 for d in ds))
    reset()
    select('VERT', lambda v: v.co.x > 0.9 and v.co.y > 0.9 and v.co.z > 0.9)


drag('vert', 'MIDDLEMOUSE', ('ctrl',), empty_spot, Vector((30, 60)), ('TRANSFORM_OT_shrink_fatten',))


@step
def s_vert_check():
    after = coords()
    moved = [i for i, (a, b) in enumerate(zip(C['before'], after)) if (a - b).length > 1e-4]
    d = after[moved[0]] - C['before'][moved[0]] if moved else Vector()
    along = d.normalized().dot(Vector((1, 1, 1)).normalized()) if d.length > 1e-6 else 0.0
    check(f"a corner vertex moves along its own normal ({tuple(round(c, 3) for c in d)}, {along:.4f})",
          len(moved) == 1 and abs(along) > 0.99)
    reset()


run()
