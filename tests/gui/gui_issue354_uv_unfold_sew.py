"""#354 in a real UI: with UV Sync Selection off, an edge clicked in the 3D View, then UV > Sew UV Edges / Merge UVs
from the main menu, sews / merges it (it did nothing: the commands read only the UV Editor's selection). Then a dense
mesh (15 600 faces, one UV shell per cube side) in a UV Editor: Ctrl+U (Unfold) finishes in seconds (it froze the UI
for minutes), Ctrl+Z puts the UVs back, Ctrl+Shift+Z redoes it, and Blender keeps running."""

import os
import sys
import time
from importlib import import_module

import bmesh
import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 300
C = {}


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def cube():
    return bpy.data.objects["Cube"]


def bm():
    b = bmesh.from_edit_mesh(cube().data)
    C["bm"] = b        # keep the wrapper alive: its elements die with it
    for seq in (b.verts, b.edges, b.faces):
        seq.ensure_lookup_table()
    return b


def shells():
    b = bm()
    return len(mod(".operators.uv_tools").islands(b, b.loops.layers.uv.active))


def top_face(b):
    return max(b.faces, key=lambda f: f.calc_center_median().z)


def fold_edge(b):
    """The top face's edge whose neighbour shares its UVs (the fold of the cube's UV cross)."""
    uvt = mod(".operators.uv_tools")
    uv = b.loops.layers.uv.active
    top = top_face(b)
    for e in sorted(top.edges, key=lambda e: e.index):
        other = next(f for f in e.link_faces if f is not top)
        if all((uvt._uv_at(top, v, uv) - uvt._uv_at(other, v, uv)).length < 1e-6 for v in e.verts):
            return e
    return None


def apart(gap):
    """Top face cut out of the UV cross and moved ``gap`` along U; nothing selected."""
    b = bm()
    uv = b.loops.layers.uv.active
    for f in b.faces:
        for lp in f.loops:
            lp[uv].uv = C["orig"][lp.index].copy()
    for e in b.edges:
        e.seam = False
    top = top_face(b)
    for e in top.edges:
        e.seam = True
    for lp in top.loops:
        lp[uv].uv.x += gap
    for el in (*b.verts, *b.edges, *b.faces):
        el.select = False
    for f in b.faces:
        for lp in f.loops:
            lp.uv_select_vert = lp.uv_select_edge = False
        f.uv_select = False
    bmesh.update_edit_mesh(cube().data)


def click_fold_edge():
    b = bm()
    e = b.edges[C["fold"]]
    area, region = view3d()
    rv3d = area.spaces.active.region_3d
    mid = cube().matrix_world @ ((e.verts[0].co + e.verts[1].co) / 2)
    p = location_3d_to_region_2d(region, rv3d, mid)
    x, y = region.x + int(p.x), region.y + int(p.y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


def main_menu(item):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return bpy.ops.allset.menu_item(item=item)


@step
def s_setup():
    setup()
    o = cube()
    for x in bpy.context.scene.objects:
        x.select_set(x is o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT')
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    ts.mesh_select_mode = (False, True, False)
    b = bm()
    uv = b.loops.layers.uv.active
    C["orig"] = {lp.index: lp[uv].uv.copy() for f in b.faces for lp in f.loops}
    C["fold"] = fold_edge(b).index
    apart(0.3)
    C["n0"] = shells()


@step
def s_click_sew():
    click_fold_edge()


@step
def s_sew():
    b = bm()
    picked = [e.index for e in b.edges if e.select]
    C["sew"] = main_menu("UV/Sew UV Edges")
    check(f"3D View click picks the edge ({picked}); UV > Sew UV Edges with UV Sync off sews it: "
          f"shells {C['n0']} -> {shells()}, seam gone {not bm().edges[C['fold']].seam}",
          picked == [C["fold"]] and shells() == C["n0"] - 1 and not bm().edges[C["fold"]].seam)
    apart(0.005)


@step
def s_click_merge():
    click_fold_edge()


@step
def s_merge():
    main_menu("UV/Merge UVs")
    check(f"UV > Merge UVs with UV Sync off merges the clicked edge's UVs (0.005 apart): shells {C['n0']} -> {shells()}",
          shells() == C["n0"] - 1)
    # a dense mesh for Unfold: every quad cut 50 times
    b = bm()
    bmesh.ops.subdivide_edges(b, edges=list(b.edges), cuts=50, use_grid_fill=True)
    for el in (*b.verts, *b.edges, *b.faces):
        el.select = False
    bmesh.update_edit_mesh(cube().data)
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.ed.undo_push(message="dense mesh")      # Ctrl+Z below goes back to here, not before the subdivision
    area.ui_type = 'UV'
    C["area"] = area


@step
def s_unfold_key():
    b = bm()
    uv = b.loops.layers.uv.active
    C["faces"] = len(b.faces)
    C["before"] = [lp[uv].uv.copy() for f in b.faces for lp in f.loops]
    r = next(r for r in C["area"].regions if r.type == 'WINDOW')
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    C["t"] = time.perf_counter()
    ev('U', 'PRESS', ctrl=True)
    ev('U', 'RELEASE', ctrl=True)


@step
def s_unfolded():
    dt = time.perf_counter() - C["t"]
    b = bm()
    uv = b.loops.layers.uv.active
    now = [lp[uv].uv.copy() for f in b.faces for lp in f.loops]
    moved = sum((p - q).length > 1e-6 for p, q in zip(now, C["before"]))
    check(f"Ctrl+U on {C['faces']} faces: Unfold ran ({moved} UVs moved) in {dt:.1f} s (under 10 s)",
          moved > 0 and dt < 10.0)
    C["after"] = now
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_undone():
    b = bm()
    uv = b.loops.layers.uv.active
    now = [lp[uv].uv.copy() for f in b.faces for lp in f.loops]
    worst = max((p - q).length for p, q in zip(now, C["before"]))
    check(f"Ctrl+Z puts the UVs back in one step (worst {worst:.2e})", len(now) == len(C["before"]) and worst < 1e-6)
    ev('Z', 'PRESS', ctrl=True, shift=True)
    ev('Z', 'RELEASE', ctrl=True, shift=True)


@step
def s_redone():
    b = bm()
    uv = b.loops.layers.uv.active
    now = [lp[uv].uv.copy() for f in b.faces for lp in f.loops]
    worst = max((p - q).length for p, q in zip(now, C["after"]))
    check(f"Ctrl+Shift+Z redoes the Unfold (worst {worst:.2e}); Blender still in edit mode",
          worst < 1e-6 and cube().mode == 'EDIT')


run()
