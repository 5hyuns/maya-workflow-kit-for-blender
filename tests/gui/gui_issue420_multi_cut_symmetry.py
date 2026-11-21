"""In a real UI (GitHub #420): with Symmetry Object X on, a Multi-Cut made by clicks on one half of a cube (split in
the middle) is cut on the other half too, and a Ctrl+click edge loop gets its mirrored loop."""

import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win  # noqa: E402

C = {}


def mc():
    return import_module(MODULE + ".operators.multi_cut")


def cube():
    return bpy.data.objects["Cube"]


def bm():
    b = bmesh.from_edit_mesh(cube().data)
    for seq in (b.verts, b.edges, b.faces):
        seq.ensure_lookup_table()
    return b


def counts():
    b = bm()
    return len(b.verts), len(b.edges), len(b.faces)


def depth(co):
    area, _region = view3d()
    return -(area.spaces.active.region_3d.view_matrix @ (cube().matrix_world @ co)).z


def to_window(co):
    area, region = view3d()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, cube().matrix_world @ co)
    return region.x + round(p.x), region.y + round(p.y)


def tool_id():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        t = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False)
    return t.idname if t else None


def has(co):
    return any((v.co - Vector(co)).length < 1e-3 for v in bm().verts)


def at(k, t):
    a, b = C["edges"][k]
    return to_window(a.lerp(b, t))


def click(x, y, **mods):
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y, **mods)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y, **mods)


def release(**mods):
    ev('LEFTMOUSE', 'RELEASE', **mods)


def undo():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_setup():
    C["x"], C["y"] = setup()
    check("Maya keymap active", sys.modules["sim"].maya_keys())
    me = cube().data                                  # a middle edge loop at x = 0: the cube has two halves
    b = bmesh.new()
    b.from_mesh(me)
    geom = b.verts[:] + b.edges[:] + b.faces[:]
    bmesh.ops.bisect_plane(b, geom=geom, plane_co=(0, 0, 0), plane_no=(1, 0, 0))
    b.to_mesh(me)
    b.free()
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    sym = import_module(MODULE + ".operators.symmetry")
    sym.set_mode(bpy.context.scene.allset_symmetry, "OBJECT_X")
    view3d()[0].spaces.active.region_3d.view_distance = 5.0      # closer: the half faces are large on screen
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('X', 'PRESS', ctrl=True, shift=True)
    ev('X', 'RELEASE', ctrl=True, shift=True)


@step
def s_tool():
    check(f"Ctrl+Shift+X = edit mode + the kit Multi-Cut tool ({bpy.context.mode}, {tool_id()})",
          bpy.context.mode == 'EDIT_MESH' and tool_id() == "allset.multi_cut_tool")
    b = bm()
    face = min((f for f in b.faces if f.calc_center_median().x > 0.1),
               key=lambda f: sum(depth(v.co) for v in f.verts))
    # its two edges along X (not the middle one, not the outer one): a cut between them stays on this half
    along = [e for e in face.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > 0.5]
    C["edges"] = [(e.verts[0].co.copy(), e.verts[1].co.copy()) for e in along]
    C["n0"] = counts()
    click(*at(0, 0.5))


@step
def s_first_release():
    release()


@step
def s_second():
    check(f"one cut point ({mc().STATE['points']})", len(mc().STATE["points"]) == 1)
    # the opposite edge at the same X
    a, b = C["edges"][0]
    x = a.lerp(b, 0.5).x
    c, d = C["edges"][1]
    C["t1"] = (x - c.x) / (d.x - c.x)
    C["x_cut"] = x
    click(*at(1, C["t1"]))


@step
def s_second_release():
    release()


@step
def s_enter():
    tap('RET')


@step
def s_cut():
    n0, n = C["n0"], counts()
    x = C["x_cut"]
    check(f"Enter cuts this half and the mirrored half ({n0} -> {n}: +4 v / +6 e / +2 f)",
          n == (n0[0] + 4, n0[1] + 6, n0[2] + 2))
    mirrored = [Vector((-v.co.x, v.co.y, v.co.z)) for v in bm().verts if abs(v.co.x - x) < 1e-3]
    check(f"the new vertices have mirrored partners at x = {-x:.3f}", mirrored and all(has(m) for m in mirrored))
    undo()


@step
def s_ctrl_click():
    check(f"Ctrl+Z undoes both cuts in one step ({counts()})", counts() == C["n0"])
    x, y = at(0, 0.3)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y + 1, ctrl=True)
    C["x_loop"] = C["edges"][0][0].lerp(C["edges"][0][1], 0.3).x
    click(x, y, ctrl=True)


@step
def s_ctrl_release():
    release(ctrl=True)


@step
def s_loop():
    n0, n = C["n0"], counts()
    x = C["x_loop"]
    check(f"Ctrl+click = an edge loop and its mirrored loop ({n0} -> {n}: +8 v)", n[0] == n0[0] + 8)
    xs = sorted(round(v.co.x, 2) for v in bm().verts if abs(abs(v.co.x) - abs(x)) < 0.05)
    check(f"the loops sit at x = {x:.2f} and {-x:.2f} ({xs})", any(abs(v - x) < 0.05 for v in xs)
          and any(abs(v + x) < 0.05 for v in xs))
    undo()
    import_module(MODULE + ".operators.symmetry").set_mode(bpy.context.scene.allset_symmetry, "OFF")


run()
