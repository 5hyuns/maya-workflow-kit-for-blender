"""#429 in a real UI, mesh edit mode: Ctrl+Shift+drag on a Rotate ring / a Scale axis handle, and Ctrl+Shift+middle-
drag with the Rotate / Scale tool, rotate / scale the selected top face of a cube with every vertex kept on one of
the cube's edges, like Maya. The rule itself: tests/test_issue429_edge_constraint.py."""
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
EDGE_OPS = ('ALLSET_OT_edge_rotate', 'ALLSET_OT_manip_scale')


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
    """A cube vertex on one of the cube's edges keeps two of its three coordinates at +-1."""
    return sum(abs(abs(c) - 1.0) < 1e-4 for c in co) >= 2


def running(names):
    return any(op.bl_idname in names for op in win().modal_operators)


def reset():
    with override():
        b = bm()
        b.verts.ensure_lookup_table()
        for v, co in zip(b.verts, C['start']):
            v.co = co
        b.normal_update()
        bmesh.update_edit_mesh(bpy.context.edit_object.data)
    C['before'] = coords()


def screen(world):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, world)
    return Vector((region.x + p.x, region.y + p.y))


def _frame(kind):
    with override():
        centre, frame, _otype = mod('ui.manipulator').pivot_frame(bpy.context, kind)
        prefs = bpy.context.preferences
        px = prefs.view.gizmo_size / 75.0 * prefs.system.ui_scale
    _area, region = view3d()
    wpp = mod('operators.manip_scale').world_per_pixel(region, region.data, centre)
    return centre, frame, px, wpp


def x_ring():
    """Window point on the front of the Rotate manipulator's X ring, and the ring's screen tangent there."""
    m = mod('ui.manipulator')
    centre, frame, px, wpp = _frame('ROTATE')
    r = m.ARROW_PX * m.ROTATE_RING_R * px * wpp
    rv3d = view3d()[1].data
    view_z = rv3d.view_matrix.inverted_safe().col[2].xyz.normalized()
    x = frame.col[0].normalized()
    best = None
    for u in (frame.col[1], frame.col[2], -frame.col[1], -frame.col[2]):
        u = u.normalized()
        if u.dot(view_z) < 0.05:
            continue
        a, b = screen(centre), screen(centre + u * r)
        if best is None or (b - a).length > best[0]:
            best = ((b - a).length, centre + u * r, x.cross(u))
    _l, p, tangent = best
    a, b = screen(p), screen(p + tangent * r * 0.2)
    C['tangent'] = (b - a).normalized()
    return a


def x_arrow():
    """Window point on the Scale manipulator's X handle (60 % out)."""
    m = mod('ui.manipulator')
    centre, frame, px, wpp = _frame('RESIZE')
    p0, p1 = screen(centre), screen(centre + frame.col[0].normalized() * wpp * 10)
    C['axis_dir'] = (p1 - p0).normalized()
    return p0 + C['axis_dir'] * m.ARROW_PX * px * 0.6


def drag(prefix, button, start, delta):
    """Steps: hover, Ctrl+Shift + press, moves, release + keys up. ``delta()`` = the whole move (window px)."""
    def hover():
        C['a'] = start()
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x), y=int(C['a'].y))
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x) + 1, y=int(C['a'].y))

    def press():
        ev('LEFT_CTRL', 'PRESS', ctrl=True)
        ev('LEFT_SHIFT', 'PRESS', ctrl=True, shift=True)
        ev(button, 'PRESS', x=int(C['a'].x), y=int(C['a'].y), ctrl=True, shift=True)

    def move1():
        q = C['a'] + delta() * 0.25
        ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), ctrl=True, shift=True)

    def move2():
        C[prefix + '_running'] = running(EDGE_OPS)
        for f in (0.5, 0.75, 1.0):
            q = C['a'] + delta() * f
            ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), ctrl=True, shift=True)

    def release():
        q = C['a'] + delta()
        ev(button, 'RELEASE', x=int(q.x), y=int(q.y), ctrl=True, shift=True)
        ev('LEFT_SHIFT', 'RELEASE', ctrl=True)
        ev('LEFT_CTRL', 'RELEASE')
    for f in (hover, press, move1, move2, release):
        f.__name__ = f"s_{prefix}_{f.__name__}"
        step(f)


def result(prefix, label):
    def check_it():
        after = coords()
        moved = [i for i, (a, b) in enumerate(zip(C['before'], after)) if (a - b).length > 1e-4]
        check(f"{label}: an edge-constrained drag runs ({C.get(prefix + '_running')})", C.get(prefix + '_running'))
        check(f"{label}: the top face's vertices moved and stay on the cube's edges "
              f"({[tuple(round(c, 3) for c in after[i]) for i in moved]})",
              moved and set(moved) <= C['top'] and all(on_an_edge(after[i]) for i in moved))
        reset()
    check_it.__name__ = f"s_{prefix}_check"
    step(check_it)


def tool(name):
    def set_tool():
        with override():
            bpy.ops.wm.tool_set_by_id(name=name)
    set_tool.__name__ = "s_tool_" + name.split('.')[-1]
    step(set_tool)


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
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        b = bm()
        for f in b.faces:
            f.select_set(f.normal.z > 0.9)
        b.select_flush_mode()
        bmesh.update_edit_mesh(ob.data)
        C['top'] = {v.index for v in b.verts if v.select}
        region = view3d()[1]
        region.data.view_rotation = Quaternion((0.82, 0.42, 0.17, 0.34))
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = 9
    C['start'] = coords()
    C['before'] = coords()


tool('builtin.rotate')
drag('ring', 'LEFTMOUSE', x_ring, lambda: C['tangent'] * 60)
result('ring', "Ctrl+Shift+drag on the X ring")
drag('rmmb', 'MIDDLEMOUSE', lambda: Vector(C['mouse']), lambda: Vector((50, 0)))
result('rmmb', "Ctrl+Shift+middle-drag with the Rotate tool")
tool('builtin.scale')
drag('arrow', 'LEFTMOUSE', x_arrow, lambda: C['axis_dir'] * 40)
result('arrow', "Ctrl+Shift+drag on the X scale handle")
drag('smmb', 'MIDDLEMOUSE', lambda: Vector(C['mouse']), lambda: Vector((40, 0)))
result('smmb', "Ctrl+Shift+middle-drag with the Scale tool")

run()
