"""#556: UV Editor commands take only the UV components drawn as selected. Two faces share a mesh edge but are two UV
shells; a click on the UV edge of that mesh edge in one shell (UV Edge component, UV Sync Selection off), after the other
shell's edge was picked before, and UV Toolkit Align Max V moves only the clicked edge's two UVs. With UV Sync Selection
on (the Edge component) the click picks the mesh edge, which both shells draw as selected, and Align moves the UVs of
both: what is drawn as selected is what the command moves."""

import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, load_maya_layout, run, setup, step, tap, view3d, win  # noqa: E402

GUI_TIMEOUT = 240
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
S = {}
# face A on the left of the UV square, face B on the right; they share the mesh edge v1-v2
A = [(0.1, 0.1), (0.4, 0.15), (0.4, 0.45), (0.1, 0.4)]
B = [(0.6, 0.5), (0.9, 0.5), (0.9, 0.8), (0.6, 0.8)]


def ob():
    return bpy.data.objects["two"]


def uv_win():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == 'IMAGE_EDITOR' and a.ui_type == 'UV':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


def uv_ctx():
    w, a, r = uv_win()
    return bpy.context.temp_override(window=w, area=a, region=r)


def uv_px(u, v):
    _w, _a, r = uv_win()
    x, y = r.view2d.view_to_region(u, v, clip=False)
    return r.x + x, r.y + y


def click(u, v, shift=False):
    w = uv_win()[0]
    x, y = uv_px(u, v)
    w.event_simulate(type='MOUSEMOVE', value='NOTHING', x=x, y=y)
    w.event_simulate(type='LEFTMOUSE', value='PRESS', x=x, y=y, shift=shift)
    w.event_simulate(type='LEFTMOUSE', value='RELEASE', x=x, y=y, shift=shift)


def flags():
    bm = bmesh.from_edit_mesh(ob().data)
    uv = bm.loops.layers.uv.active
    return [(f.index, lp.vert.index, tuple(round(c, 3) for c in lp[uv].uv), lp.uv_select_vert, lp.uv_select_edge)
            for f in bm.faces for lp in f.loops]


def uvs():
    bm = bmesh.from_edit_mesh(ob().data)
    uv = bm.loops.layers.uv.active
    return {(f.index, lp.vert.index): tuple(round(c, 5) for c in lp[uv].uv) for f in bm.faces for lp in f.loops}


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_mesh():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    me = bpy.data.meshes.new("two")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (2, 0, 0), (2, 1, 0)], [],
                   [(0, 1, 2, 3), (1, 4, 5, 2)])
    me.uv_layers.new(name="map1")
    for poly, corners in zip(me.polygons, (A, B)):
        for li, c in zip(poly.loop_indices, corners):
            me.uv_layers[0].data[li].uv = c
    o = bpy.data.objects.new("two", me)
    bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    area, r = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    tap('F12')


step(lambda: None)


@step
def s_edge_mode():
    w, a, r = uv_win()
    check("F12 opened the UV Editor", w is not None)
    with uv_ctx():
        bpy.ops.image.view_all(fit_view=True)
        bpy.ops.allset.uv_component(mode='UV_EDGE')
        bpy.ops.uv.select_all(action='DESELECT')


@step
def s_click_b():
    click(0.6, 0.65)          # face B's left edge (mesh edge v1-v2, the shared one)


step(lambda: None)


@step
def s_click_a():
    print("GUI INFO after B click", [x for x in flags() if x[3] or x[4]], flush=True)
    click(0.4, 0.3)           # face A's right edge: the same mesh edge v1-v2


step(lambda: None)


@step
def s_align():
    S["flags"] = flags()
    print("GUI INFO after A click", [x for x in S["flags"] if x[3] or x[4]], flush=True)
    drawn = {(f, v) for f, v, _uv, _vs, es in S["flags"] if es}
    check(f"only face A's edge is a selected UV edge ({sorted(drawn)})", {f for f, _v in drawn} == {0})
    if SHOTS:
        with uv_ctx():
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "gui_issue556_before.png"))
    S["before"] = uvs()
    with uv_ctx():
        S["res"] = bpy.ops.allset.uv_align_to(axis='V', where='MAX')


@step
def s_check():
    after = uvs()
    moved = sorted(k for k in after if after[k] != S["before"][k])
    print("GUI INFO moved", moved, flush=True)
    check(f"Align Max V moves only the clicked edge's UVs ({S['res']}, moved {moved})",
          all(f == 0 for f, _v in moved))
    if SHOTS:
        with uv_ctx():
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "gui_issue556_after.png"))


# the same with UV Sync Selection on (the Edge component): the click selects the mesh edge, which face B's shell has
# too, so the UV Editor draws that edge as selected in both shells


@step
def s_sync_edge_mode():
    bm = bmesh.from_edit_mesh(ob().data)
    uv = bm.loops.layers.uv.active
    for f, corners in zip(bm.faces, (A, B)):
        for lp, c in zip(f.loops, corners):
            lp[uv].uv = c
    bmesh.update_edit_mesh(ob().data)
    with uv_ctx():
        bpy.ops.allset.uv_component(mode='EDGE')
        bpy.ops.uv.select_all(action='DESELECT')
    ts = bpy.context.scene.tool_settings
    check(f"Edge component: UV Sync Selection on ({ts.use_uv_select_sync}, {tuple(ts.mesh_select_mode)})",
          ts.use_uv_select_sync and ts.mesh_select_mode[1])
    check(f"Edge component: a pick shows on every UV of the mesh element ({ts.uv_sticky_select_mode})",
          ts.uv_sticky_select_mode == 'SHARED_VERTEX')


@step
def s_sync_click_a():
    click(0.4, 0.3)


step(lambda: None)


@step
def s_sync_align():
    fl = flags()
    bm = bmesh.from_edit_mesh(ob().data)
    print("GUI INFO sync after A click", [x for x in fl if x[3] or x[4]], "sync valid",
          getattr(bm, "uv_select_sync_valid", None), "mesh edges", [e.index for e in bm.edges if e.select],
          flush=True)
    shared = next(e for e in bm.edges if {v.index for v in e.verts} == {1, 2})
    picked = [e.index for e in bm.edges if e.select]
    check(f"the click picked the shared mesh edge ({picked})", picked == [shared.index])
    # Blender draws the mesh selection when the UV selection isn't kept apart from it; when it is kept, the UV edge
    # of face B must be selected too
    kept = getattr(bm, "uv_select_sync_valid", False)
    b_edge = [x for x in fl if x[0] == 1 and x[1] in (1, 2) and x[4]]
    check(f"face B's UV edge is drawn as selected too (kept apart {kept}, B flags {b_edge})", not kept or b_edge)
    if SHOTS:
        with uv_ctx():
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "gui_issue556_sync_before.png"))
    S["before2"] = uvs()
    with uv_ctx():
        S["res2"] = bpy.ops.allset.uv_align_to(axis='V', where='MAX')


@step
def s_sync_check():
    after = uvs()
    moved = sorted(k for k in after if after[k] != S["before2"][k])
    print("GUI INFO sync moved", moved, flush=True)
    check(f"UV Sync on: Align Max V moves the selected edge's UVs in both shells ({S['res2']}, moved {moved})",
          {f for f, _v in moved} == {0, 1} and all(v in (1, 2) for _f, v in moved))
    if SHOTS:
        with uv_ctx():
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "gui_issue556_sync_after.png"))


run()
