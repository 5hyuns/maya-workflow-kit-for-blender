"""#430 in a real UI, mesh edit mode: Ctrl+middle-drag with the Rotate tool turns each selected component group about
its own normal around the group's centre; with the Scale tool it scales the group across its normal. Only the
horizontal part of the drag counts; Esc puts the components back; in object mode the drag is the plain middle drag."""
import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, view3d, win, MODULE  # noqa: E402

C = {}
OP = 'ALLSET_OT_component_local'


def rate(name):
    """The kit's drag rate ``name`` ('DEG_PER_PX' or 'PX_PER_SCALE')."""
    return getattr(import_module(MODULE + '.operators.component_local'), name)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def bm():
    return bmesh.from_edit_mesh(bpy.context.edit_object.data)


def coords():
    b = bm()
    b.verts.ensure_lookup_table()
    return [v.co.copy() for v in b.verts]


def running():
    return any(op.bl_idname == OP for op in win().modal_operators)


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
    C['before'] = coords()


def reset():
    with override():
        b = bm()
        b.verts.ensure_lookup_table()
        for v, co in zip(b.verts, C['start']):
            v.co = co
        b.normal_update()
        bmesh.update_edit_mesh(bpy.context.edit_object.data)


def tool(name):
    with override():
        bpy.ops.wm.tool_set_by_id(name=name)


def empty_spot():
    _a, r = view3d()
    return Vector((r.x + r.width * 0.25, r.y + r.height * 0.3))


def drag(prefix, delta, cancel=False, ctrl=True):
    """Ctrl+MMB drag in an empty spot: hover, Ctrl + press, moves, release (or Esc) + Ctrl up (plain MMB: ctrl=False)."""
    def hover():
        C['a'] = empty_spot()
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x), y=int(C['a'].y))

    def press():
        if ctrl:
            ev('LEFT_CTRL', 'PRESS', ctrl=True)
        ev('MIDDLEMOUSE', 'PRESS', x=int(C['a'].x), y=int(C['a'].y), ctrl=ctrl)

    def move1():
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x) + int(delta.x * 0.5), y=int(C['a'].y) + int(delta.y * 0.5),
           ctrl=ctrl)

    def move2():
        C[prefix + '_running'] = running()
        ev('MOUSEMOVE', 'NOTHING', x=int(C['a'].x) + int(delta.x), y=int(C['a'].y) + int(delta.y), ctrl=ctrl)

    def release():
        x, y = int(C['a'].x) + int(delta.x), int(C['a'].y) + int(delta.y)
        if cancel:
            ev('ESC', 'PRESS', ctrl=True)
            ev('ESC', 'RELEASE', ctrl=True)
        ev('MIDDLEMOUSE', 'RELEASE', x=x, y=y, ctrl=ctrl)
        if ctrl:
            ev('LEFT_CTRL', 'RELEASE')
    for f in (hover, press, move1, move2, release):
        f.__name__ = f"s_{prefix}_{f.__name__}"
        step(f)


def moved(after):
    return [i for i, (a, b) in enumerate(zip(C['before'], after)) if (a - b).length > 1e-4]


def expect(mode, amount, centre, normal, idx):
    out = {}
    for i in idx:
        r = C['before'][i] - centre
        if mode == 'ROTATE':
            out[i] = centre + Matrix.Rotation(amount, 3, normal) @ r
        else:
            along = normal * r.dot(normal)
            out[i] = centre + along + (r - along) * amount
    return out


def close(after, want):
    return all((after[i] - p).length < 1e-3 for i, p in want.items())


def fmt(after, idx):
    return [tuple(round(c, 3) for c in after[i]) for i in idx]


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
        region = view3d()[1]
        region.data.view_rotation = Quaternion((0.82, 0.42, 0.17, 0.34))
        region.data.view_location = (0, 0, 0)
        region.data.view_distance = 9
    tool('builtin.rotate')
    C['start'] = coords()
    select('FACE', lambda f: f.normal.z > 0.9)


drag('rot', Vector((90, 0)))


@step
def s_rot_check():
    after = coords()
    top = [i for i, co in enumerate(C['before']) if co.z > 0.9]
    want = expect('ROTATE', -math.radians(90 * rate('DEG_PER_PX')), Vector((0, 0, 1)), Vector((0, 0, 1)), top)
    check(f"Rotate tool: Ctrl+MMB runs the local rotate ({C.get('rot_running')})", C.get('rot_running'))
    check(f"the top face turned about its normal around its centre ({fmt(after, top)})",
          sorted(moved(after)) == sorted(top) and close(after, want))
    ops = bpy.context.window_manager.operators
    check(f"the drag is one registered (undoable) step ({ops[-1].bl_idname if ops else None})",
          bool(ops) and ops[-1].bl_idname == OP)
    reset()
    select('FACE', lambda f: f.normal.z > 0.9)


drag('vert', Vector((0, 80)))


@step
def s_vert_check():
    after = coords()
    check(f"a vertical drag turns nothing ({moved(after)})", not moved(after))
    reset()
    # two separate faces: each one turns about its own normal and centre
    select('FACE', lambda f: abs(f.normal.z) > 0.9)


drag('two', Vector((60, 0)))


@step
def s_two_check():
    after = coords()
    a = -math.radians(60 * rate('DEG_PER_PX'))
    top = [i for i, co in enumerate(C['before']) if co.z > 0.9]
    bottom = [i for i, co in enumerate(C['before']) if co.z < -0.9]
    want = expect('ROTATE', a, Vector((0, 0, 1)), Vector((0, 0, 1)), top)
    want.update(expect('ROTATE', a, Vector((0, 0, -1)), Vector((0, 0, -1)), bottom))
    check(f"top and bottom faces each turn about their own normal ({fmt(after, top + bottom)})",
          close(after, want) and all(after[i].z > 0.9 for i in top) and all(after[i].z < -0.9 for i in bottom))
    reset()
    tool('builtin.scale')
    select('FACE', lambda f: f.normal.z > 0.9)


drag('scale', Vector((90, 0)))


@step
def s_scale_check():
    after = coords()
    top = [i for i, co in enumerate(C['before']) if co.z > 0.9]
    want = expect('SCALE', 1 + 90 / rate('PX_PER_SCALE'), Vector((0, 0, 1)), Vector((0, 0, 1)), top)
    check(f"Scale tool: Ctrl+MMB runs the local scale ({C.get('scale_running')})", C.get('scale_running'))
    check(f"the top face grew across its normal, staying in its plane ({fmt(after, top)})",
          sorted(moved(after)) == sorted(top) and close(after, want))
    reset()
    # an edge: its normal is the mean of its faces' normals, so it scales along its own length
    select('EDGE', lambda e: all(abs(v.co.x - 1) < 1e-4 and abs(v.co.z - 1) < 1e-4 for v in e.verts))


drag('edge', Vector((-40, 0)))


@step
def s_edge_check():
    after = coords()
    idx = moved(after)
    f = 1 - 40 / rate('PX_PER_SCALE')
    want = {i: Vector((1, C['before'][i].y * f, 1)) for i in idx}
    check(f"an edge scales along its own length to the left ({fmt(after, idx)})", len(idx) == 2 and close(after, want))
    reset()
    select('FACE', lambda f: f.normal.z > 0.9)


drag('esc', Vector((90, 0)), cancel=True)


@step
def s_esc_check():
    after = coords()
    check(f"Esc puts the face back ({moved(after)})", not moved(after))
    with override():
        bpy.ops.object.mode_set(mode='OBJECT')
    C['before_ob'] = bpy.data.objects['Cube'].matrix_world.copy()


drag('object', Vector((90, 0)))


@step
def s_object_check():
    ob = bpy.data.objects['Cube']
    check(f"object mode: Ctrl+MMB with the Scale tool does not run the local scale ({C.get('object_running')})",
          not C.get('object_running'))
    C['ctrl_ob'] = ob.matrix_world.copy()
    check(f"... it scales the object like a plain middle drag ({tuple(round(c, 3) for c in ob.scale)})",
          C['ctrl_ob'] != C['before_ob'])
    ob.matrix_world = C['before_ob']


drag('plain', Vector((90, 0)), ctrl=False)


@step
def s_plain_check():
    ob = bpy.data.objects['Cube']
    diff = max(abs(a - b) for ra, rb in zip(ob.matrix_world, C['ctrl_ob']) for a, b in zip(ra, rb))
    check(f"the same plain middle drag gives the same object ({diff:.5f})", diff < 1e-4)
    ob.matrix_world = C['before_ob']


run()
