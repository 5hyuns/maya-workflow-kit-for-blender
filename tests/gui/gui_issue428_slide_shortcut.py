"""#428 in a real UI: the Move tool picked with the W key in mesh edit mode, Ctrl+Shift+drag slides the selection
along the mesh like Maya: edges and faces on the Z, X and Y arrows, a plane handle and the centre, with Ctrl+Shift
pressed before the mouse comes onto the handle or after; Ctrl+Shift+middle-drag anywhere slides too. The same with
the Industry Compatible keymap active."""
import os
import sys
from importlib import import_module

import bmesh
import bpy
from mathutils import Quaternion, Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, tap, view3d, win, MODULE  # noqa: E402

C = {}
SLIDES = ('TRANSFORM_OT_edge_slide', 'TRANSFORM_OT_vert_slide')


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
    return [op.bl_idname for op in win().modal_operators if op.bl_idname in names]


def moved_points():
    after = coords()
    return [(i, after[i]) for i, (a, b) in enumerate(zip(C['before'], after)) if (a - b).length > 1e-3]


def select(kind, pick):
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
    view3d()[0].tag_redraw()
    C['before'] = coords()


def reset():
    with override():
        b = bm()
        b.verts.ensure_lookup_table()
        for v, co in zip(b.verts, C['start']):
            v.co = co
        b.normal_update()
        bmesh.update_edit_mesh(bpy.context.edit_object.data)
    view3d()[0].tag_redraw()


def top_edge(e):
    return all(abs(v.co.x - 1) < 1e-4 and abs(v.co.z - 1) < 1e-4 for v in e.verts)


def top_face(f):
    return all(abs(v.co.z - 1) < 1e-4 for v in f.verts)


def screen(world):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, world)
    return Vector((region.x + p.x, region.y + p.y))


def handle(role, data=None):
    return next(g for g, r, d in C['group'].handles if r == role and (data is None or d == data))


def handle_point(role, data=None):
    """Window point on a Move manipulator handle of the current selection."""
    gz = handle(role, data)
    at = mod('ui.manipulator').PLANE_AT
    local = {'AXIS': Vector((0, 0, 0.6)), 'PLANE': Vector((at, at, 0)), 'CENTER': Vector()}[role]
    return screen(gz.matrix_world @ local)


def empty_point():
    """A viewport point well away from the manipulator and the cube."""
    _area, region = view3d()
    return Vector((region.x + region.width * 0.15, region.y + region.height * 0.2))


def drag(prefix, start, delta, button='LEFTMOUSE', keys_first=False):
    """Steps: (Ctrl+Shift down first when ``keys_first``) mouse onto ``start()``, (else Ctrl+Shift down there),
    press, moves, release + keys up."""
    kw = {"ctrl": True, "shift": True}

    def keys():
        ev('LEFT_CTRL', 'PRESS', ctrl=True)
        ev('LEFT_SHIFT', 'PRESS', ctrl=True, shift=True)

    def hover():
        C['a'] = start()
        if keys_first:
            keys()
        mods = kw if keys_first else {}
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x), y=int(C['a'].y), **mods)
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x) + 1, y=int(C['a'].y), **mods)

    def press():
        if not keys_first:
            keys()
        ev(button, 'PRESS', x=int(C['a'].x), y=int(C['a'].y), **kw)

    def move1():
        q = C['a'] + delta * 0.25
        ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), **kw)

    def move2():
        C[prefix] = running(SLIDES)
        for f in (0.5, 0.75, 1.0):
            q = C['a'] + delta * f
            ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), **kw)

    def release():
        q = C['a'] + delta
        ev(button, 'RELEASE', x=int(q.x), y=int(q.y), **kw)
        ev('LEFT_SHIFT', 'RELEASE', ctrl=True)
        ev('LEFT_CTRL', 'RELEASE')
    for f in (hover, press, move1, move2, release):
        f.__name__ = f"s_{prefix}_{f.__name__}"
        step(f)


def verdict(prefix, what, op, count):
    """Check that ``prefix``'s drag ran ``op`` and left ``count`` moved vertices, each on a cube edge."""
    def s():
        moved = moved_points()
        check(f"{what}: runs {op} ({C.get(prefix)})", op in (C.get(prefix) or ()))
        check(f"{what}: {count} vertices slid along cube edges "
              f"({[tuple(round(c, 3) for c in co) for _i, co in moved]})",
              len(moved) == count and all(on_an_edge(co) for _i, co in moved))
        reset()
    s.__name__ = f"s_{prefix}_check"
    step(s)


def case(prefix, what, kind, pick, start, delta, op, count, **kw):
    def s():
        select(kind, pick)
    s.__name__ = f"s_{prefix}_select"
    step(s)
    drag(prefix, start, delta, **kw)
    verdict(prefix, what, op, count)


@step
def s_setup():
    C['mouse'] = setup()
    ui = mod('ui.manipulator')
    original = ui.ALLSET_GGT_xform.draw_prepare

    def spy(self, context):
        original(self, context)
        C['group'] = self
    ui.ALLSET_GGT_xform.draw_prepare = spy
    with override():
        ob = bpy.data.objects['Cube']
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.context.tool_settings.use_snap = False
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.tool_set_by_id(name='builtin.select_box')
        region = view3d()[1]
        region.data.view_rotation = Quaternion((0.82, 0.42, 0.17, 0.34))
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = 9
        mod('preferences').get(bpy.context).transform_constraint = 'NONE'
    C['start'] = coords()


@step
def s_w_key():
    # the W key picks the Move tool (a tap), with the mouse in the viewport
    ev('MOUSEMOVE', 'NOTHING', x=C['mouse'][0], y=C['mouse'][1])
    tap('W')


@step
def s_w_check():
    tool = bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH')
    check(f"the W key picks the Move tool ({tool.idname if tool else None})",
          tool is not None and tool.idname == 'builtin.move')
    select('EDGE', top_edge)


EDGE_SLIDE = 'TRANSFORM_OT_edge_slide'
SIDE = Vector((-60, -10))

case('edge_z_keys_first', "edge, Z arrow, Ctrl+Shift held before the mouse comes onto it", 'EDGE', top_edge,
     lambda: handle_point('AXIS', 'Z'), SIDE, EDGE_SLIDE, 2, keys_first=True)
case('edge_z', "edge, Z arrow, Ctrl+Shift pressed on it", 'EDGE', top_edge,
     lambda: handle_point('AXIS', 'Z'), Vector((0, -40)), EDGE_SLIDE, 2)
case('edge_x', "edge, X arrow", 'EDGE', top_edge, lambda: handle_point('AXIS', 'X'), SIDE, EDGE_SLIDE, 2)
case('edge_y', "edge, Y arrow", 'EDGE', top_edge, lambda: handle_point('AXIS', 'Y'), SIDE, EDGE_SLIDE, 2)
case('edge_plane', "edge, XY plane handle", 'EDGE', top_edge, lambda: handle_point('PLANE', 'XY'), SIDE,
     EDGE_SLIDE, 2)
case('edge_centre', "edge, centre handle", 'EDGE', top_edge, lambda: handle_point('CENTER'), SIDE, EDGE_SLIDE, 2)
case('face_z', "face, Z arrow", 'FACE', top_face, lambda: handle_point('AXIS', 'Z'), Vector((0, -40)),
     EDGE_SLIDE, 4)
case('vert_x', "vertex, X arrow", 'VERT', lambda v: v.co.x > 0.9 and v.co.y > 0.9 and v.co.z > 0.9,
     lambda: handle_point('AXIS', 'X'), SIDE, 'TRANSFORM_OT_vert_slide', 1)
case('edge_mmb', "edge, Ctrl+Shift+middle-drag away from the manipulator", 'EDGE', top_edge, empty_point,
     Vector((-60, -40)), EDGE_SLIDE, 2, button='MIDDLEMOUSE')


@step
def s_ic_keymap():
    # the Industry Compatible keymap active (a test config): the same Ctrl+Shift drags slide
    path = os.path.join(bpy.utils.system_resource('SCRIPTS'), "presets", "keyconfig", "Industry_Compatible.py")
    with override():
        bpy.ops.preferences.keyconfig_activate(filepath=path)
    C['ic'] = bpy.context.window_manager.keyconfigs.active.name


@step
def s_ic_check():
    check(f"Industry Compatible keymap active ({C.get('ic')})", C.get('ic') == "Industry_Compatible")


case('ic_edge_z', "Industry Compatible: edge, Z arrow", 'EDGE', top_edge, lambda: handle_point('AXIS', 'Z'),
     Vector((0, -40)), EDGE_SLIDE, 2)
case('ic_edge_mmb', "Industry Compatible: edge, Ctrl+Shift+middle-drag", 'EDGE', top_edge, empty_point,
     Vector((-60, -40)), EDGE_SLIDE, 2, button='MIDDLEMOUSE')


run()
