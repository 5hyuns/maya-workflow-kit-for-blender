"""#428 in a real UI, more ways in: an edge loop picked with the double-click (the kit's loop pick at the mouse), the
Move tool from the W key, Ctrl+Shift+drag on a handle slides the whole loop along the side edges like Maya. Like Maya,
Ctrl+Shift pressed after a plain handle drag has started keeps moving (no slide), and letting go of Ctrl+Shift during a
slide keeps sliding."""
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
MOVES = ('TRANSFORM_OT_translate', 'ALLSET_OT_live_translate')


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
    """A middle-loop vertex slid along a side edge keeps x and y at +-1 and stays in the cube."""
    return all(abs(abs(c) - 1.0) < 1e-4 for c in co[:2]) and abs(co[2]) <= 1.0 + 1e-4


def running(names):
    return [op.bl_idname for op in win().modal_operators if op.bl_idname in names]


def moved_points():
    after = coords()
    return [(i, after[i]) for i, (a, b) in enumerate(zip(C['before'], after)) if (a - b).length > 1e-3]


def reset():
    with override():
        b = bm()
        b.verts.ensure_lookup_table()
        for v, co in zip(b.verts, C['start']):
            v.co = co
        b.normal_update()
        bmesh.update_edit_mesh(bpy.context.edit_object.data)
    view3d()[0].tag_redraw()


def mid_loop(e):
    return all(abs(v.co.z) < 1e-4 for v in e.verts)


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


def drag(prefix, start, delta, button='LEFTMOUSE', keys_first=False, mods='press'):
    """Steps: mouse onto ``start()``, press, moves, release. ``mods``: 'press' = Ctrl+Shift down at the press (before
    the mouse comes onto the handle when ``keys_first``); 'mid' = a plain press, Ctrl+Shift down after the first move;
    'letgo' = Ctrl+Shift at the press, let go after the first move."""
    on = {"ctrl": True, "shift": True}
    kw = dict(on) if mods != 'mid' else {}

    def keys():
        ev('LEFT_CTRL', 'PRESS', ctrl=True)
        ev('LEFT_SHIFT', 'PRESS', ctrl=True, shift=True)

    def hover():
        C['a'] = start()
        if keys_first:
            keys()
        held = kw if keys_first else {}
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x), y=int(C['a'].y), **held)
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x) + 1, y=int(C['a'].y), **held)

    def press():
        if not keys_first and mods != 'mid':
            keys()
        ev(button, 'PRESS', x=int(C['a'].x), y=int(C['a'].y), **kw)

    def move1():
        q = C['a'] + delta * 0.25
        ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), **kw)
        if mods == 'mid':
            keys()
            kw.update(on)
        elif mods == 'letgo':
            ev('LEFT_SHIFT', 'RELEASE', ctrl=True)
            ev('LEFT_CTRL', 'RELEASE')
            kw.clear()

    def move2():
        C[prefix] = running(SLIDES)
        C[prefix + '_moving'] = running(MOVES)
        for f in (0.5, 0.75, 1.0):
            q = C['a'] + delta * f
            ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), **kw)

    def release():
        q = C['a'] + delta
        ev(button, 'RELEASE', x=int(q.x), y=int(q.y), **kw)
        if kw:
            ev('LEFT_SHIFT', 'RELEASE', ctrl=True)
            ev('LEFT_CTRL', 'RELEASE')
    for f in (hover, press, move1, move2, release):
        f.__name__ = f"s_{prefix}_{f.__name__}"
        step(f)




def loop_selected():
    return sorted(e.index for e in bm().edges if e.select)


def case(prefix, what, start, delta, slide, **kw):
    """Pick the middle loop again, drag, then check: ``slide`` = the edge slide ran and every loop vertex stayed on
    a side edge; else no slide ran and the loop kept its height."""
    def s_select():
        reset()
        with override():
            bpy.ops.mesh.select_all(action='DESELECT')
        hover_loop_edge()
        pick_loop()
        C['before'] = coords()
    s_select.__name__ = f"s_{prefix}_select"
    step(s_select)
    drag(prefix, start, delta, **kw)

    def s_check():
        moved = moved_points()
        ran = C.get(prefix) or ()
        if slide:
            check(f"{what}: runs the edge slide ({ran})", 'TRANSFORM_OT_edge_slide' in ran)
            check(f"{what}: the 4 loop vertices slid along the side edges "
                  f"({[tuple(round(c, 3) for c in co) for _i, co in moved]})",
                  len(moved) == 4 and all(on_an_edge(co) for _i, co in moved))
        else:
            check(f"{what}: no slide runs ({ran})", not ran)
            check(f"{what}: the move goes on ({C.get(prefix + '_moving')})", bool(C.get(prefix + '_moving')))
            loop = [co for co in coords() if abs(co.z) < 0.9]
            check(f"{what}: the loop stays at the middle height, nothing slid up or down a side edge "
                  f"({[tuple(round(c, 3) for c in co) for co in loop]})",
                  len(loop) == 4 and all(abs(co.z) < 1e-4 for co in loop))
    s_check.__name__ = f"s_{prefix}_check"
    step(s_check)


def hover_loop_edge():
    """Mouse on the middle-loop edge nearest the viewer."""
    region = view3d()[1]
    eye = region.data.view_matrix.inverted().translation
    edges = [e for e in bm().edges if mid_loop(e)]
    e = min(edges, key=lambda e: ((e.verts[0].co + e.verts[1].co) / 2 - eye).length)
    p = screen((e.verts[0].co + e.verts[1].co) / 2)
    ev('MOUSEMOVE', 'NOTHING', x=int(p.x), y=int(p.y))


def pick_loop():
    # event simulation can't send DOUBLE_CLICK: the double-click's operator runs at the simulated mouse
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C['pick'] = bpy.ops.allset.loop_pick('INVOKE_DEFAULT', between=False)


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
        b = bm()
        sides = [e for e in b.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1.0]
        bmesh.ops.subdivide_edges(b, edges=sides, cuts=1, use_grid_fill=True)
        bmesh.update_edit_mesh(bpy.context.edit_object.data)
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.wm.tool_set_by_id(name='builtin.select_box')
        region = view3d()[1]
        region.data.view_rotation = Quaternion((0.82, 0.42, 0.17, 0.34))
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = 9
        mod('preferences').get(bpy.context).transform_constraint = 'NONE'
    C['start'] = coords()


@step
def s_hover():
    hover_loop_edge()


@step
def s_double_click():
    pick_loop()


@step
def s_loop_check():
    n = len(loop_selected())
    check(f"the double-click on a middle edge picks its loop ({C.get('pick')}, {n} edges, the loop = 4)", n == 4)


@step
def s_w_key():
    ev('MOUSEMOVE', 'NOTHING', x=C['mouse'][0], y=C['mouse'][1])
    tap('W')


@step
def s_w_check():
    tool = bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH')
    check(f"the W key picks the Move tool ({tool.idname if tool else None})",
          tool is not None and tool.idname == 'builtin.move')


DOWN = Vector((0, -40))
case('loop_z', "double-clicked loop, Z arrow, Ctrl+Shift+drag", lambda: handle_point('AXIS', 'Z'), DOWN, True)
case('loop_centre', "double-clicked loop, centre handle, Ctrl+Shift+drag", lambda: handle_point('CENTER'), DOWN,
     True)
case('loop_mmb', "double-clicked loop, Ctrl+Shift+middle-drag away from the manipulator", empty_point,
     Vector((0, -40)), True, button='MIDDLEMOUSE')
case('loop_letgo', "Ctrl+Shift let go during the slide: it goes on", lambda: handle_point('AXIS', 'Z'), DOWN, True,
     mods='letgo')
case('loop_mid', "Ctrl+Shift pressed after a plain X arrow drag started: it keeps moving (no slide)",
     lambda: handle_point('AXIS', 'X'), Vector((-60, -10)), False, mods='mid')


run()
