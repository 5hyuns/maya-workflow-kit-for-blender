"""#428 in a real UI, the way a Maya user works: a new scene in the Maya layout, a polygon cube made by the kit, W
picks the Move tool in object mode, F10 / F7 / F11 go to the component modes, then Ctrl+Shift+drag on the Move
manipulator's Z arrow slides the selected edges (or faces) along the mesh, like Maya."""
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, load_maya_layout, run, setup, step, tap, view3d, win, MODULE  # noqa: E402

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
    """A cube vertex slid along one of its edges keeps two of its coordinates on the cube's sides."""
    h = C['half']
    return sum(abs(abs(c) - h) < 1e-4 * h for c in co) >= 2 and all(abs(c) <= h * (1 + 1e-4) for c in co)


def top_edge(e):
    h = C['half']
    return all(abs(v.co.x - h) < 1e-4 and abs(v.co.y - h) < 1e-4 for v in e.verts)


def top_face(f):
    h = C['half']
    return all(abs(v.co.y - h) < 1e-4 for v in f.verts)


def select(seq_name, pick):
    with override():
        b = bm()
        for e in list(b.verts) + list(b.edges) + list(b.faces):
            e.select_set(False)
        for e in getattr(b, seq_name):
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


def moved_points():
    after = coords()
    return [(i, after[i]) for i, (a, b) in enumerate(zip(C['before'], after)) if (a - b).length > 1e-4 * C['half']]


def screen(world):
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, world)
    return Vector((region.x + p.x, region.y + p.y))


def z_arrow():
    gz = next(g for g, r, d in C['group'].handles if r == 'AXIS' and d == 'Z')
    return screen(gz.matrix_world @ Vector((0, 0, 0.6)))


def drag(prefix, delta):
    kw = {"ctrl": True, "shift": True}

    def hover():
        C['a'] = z_arrow()
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x), y=int(C['a'].y))
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x) + 1, y=int(C['a'].y))

    def press():
        ev('LEFT_CTRL', 'PRESS', ctrl=True)
        ev('LEFT_SHIFT', 'PRESS', ctrl=True, shift=True)
        ev('LEFTMOUSE', 'PRESS', x=int(C['a'].x), y=int(C['a'].y), **kw)

    def move1():
        q = C['a'] + delta * 0.25
        ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), **kw)

    def move2():
        C[prefix] = [op.bl_idname for op in win().modal_operators if op.bl_idname in SLIDES]
        for f in (0.5, 0.75, 1.0):
            q = C['a'] + delta * f
            ev('MOUSEMOVE', 'NOTHING', x=int(q.x), y=int(q.y), **kw)

    def release():
        q = C['a'] + delta
        ev('LEFTMOUSE', 'RELEASE', x=int(q.x), y=int(q.y), **kw)
        ev('LEFT_SHIFT', 'RELEASE', ctrl=True)
        ev('LEFT_CTRL', 'RELEASE')
    for f in (hover, press, move1, move2, release):
        f.__name__ = f"s_{prefix}_{f.__name__}"
        step(f)


def verdict(prefix, what, count):
    def s():
        moved = moved_points()
        check(f"{what}: Ctrl+Shift+drag on the Z arrow runs Edge Slide ({C.get(prefix)})",
              'TRANSFORM_OT_edge_slide' in (C.get(prefix) or ()))
        check(f"{what}: {count} vertices slid along the cube's edges "
              f"({[tuple(round(c, 3) for c in co) for _i, co in moved]})",
              len(moved) == count and all(on_an_edge(co) for _i, co in moved))
        reset()
    s.__name__ = f"s_{prefix}_check"
    step(s)


@step
def s_setup():
    C['mouse'] = setup()
    load_maya_layout()


@step
def s_cube():
    ui = mod('ui.manipulator')
    original = ui.ALLSET_GGT_xform.draw_prepare

    def spy(self, context):
        original(self, context)
        C['group'] = self
    ui.ALLSET_GGT_xform.draw_prepare = spy
    with override():
        bpy.ops.allset.create(kind='CUBE')
        bpy.context.tool_settings.use_snap = False
        region = view3d()[1]
        region.data.view_rotation = Quaternion((0.82, 0.42, 0.17, 0.34))
        region.data.view_location = bpy.context.active_object.location.copy()
        region.data.view_distance = 9 * max(bpy.context.active_object.dimensions) / 2
    ev('MOUSEMOVE', 'NOTHING', x=C['mouse'][0], y=C['mouse'][1])
    tap('W')


@step
def s_f10():
    tool = bpy.context.workspace.tools.from_space_view3d_mode('OBJECT')
    C['object_tool'] = tool.idname if tool else None
    tap('F10')


@step
def s_edge_mode():
    tool = bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH')
    check(f"W in object mode, then F10: edge mode with the Move tool ({bpy.context.mode}, "
          f"{tuple(bpy.context.tool_settings.mesh_select_mode)}, {C.get('object_tool')}, "
          f"{tool.idname if tool else None})",
          bpy.context.mode == 'EDIT_MESH' and tuple(bpy.context.tool_settings.mesh_select_mode) == (False, True, False)
          and tool is not None and tool.idname == 'builtin.move')
    with override():
        C['start'] = coords()
    C['half'] = max(abs(c) for co in C['start'] for c in co)
    # the cube's local up is Y in the kit's Maya scene (Y-up), so a "top" edge here has y = +half
    select('edges', top_edge)


drag('edge', Vector((-60, -10)))
verdict('edge', "edge mode (F10)", 2)


@step
def s_f7():
    ev('MOUSEMOVE', 'NOTHING', x=C['mouse'][0], y=C['mouse'][1])
    tap('F7')


@step
def s_multi():
    check(f"F7: multi-component mode ({tuple(bpy.context.tool_settings.mesh_select_mode)})",
          tuple(bpy.context.tool_settings.mesh_select_mode) == (True, True, True))
    select('edges', top_edge)


drag('multi', Vector((-60, -10)))
verdict('multi', "multi-component mode (F7), one edge", 2)


@step
def s_f11():
    ev('MOUSEMOVE', 'NOTHING', x=C['mouse'][0], y=C['mouse'][1])
    tap('F11')


@step
def s_face_mode():
    select('faces', top_face)


drag('face', Vector((-60, -10)))
verdict('face', "face mode (F11)", 4)


run()
