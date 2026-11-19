"""In a real UI: #392 a cylinder in object mode -> UV > Camera-based maps the whole object from the 3D View (it
only warned), Ctrl+Z puts the UVs back; #393 a wavy cylinder side shell in a UV Editor window with one UV edge loop
selected -> UV Editor > Modify > Straighten Shell (the UV Toolkit button) makes the shell a straight strip at once
(no dialog, no "active face" error), Ctrl+Z puts it back."""

import math
import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, setup, step, view3d, win  # noqa: E402

C = {}
N, H, RING = 20, 4, 2


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def uv_window():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.ui_type == 'UV':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


def obj_uvs(ob):
    return [tuple(round(c, 5) for c in d.uv) for d in ob.data.uv_layers.active.data]


def edit_uvs(ob):
    b = bmesh.from_edit_mesh(ob.data)
    uv = b.loops.layers.uv.active
    return [tuple(round(c, 5) for c in lp[uv].uv) for f in b.faces for lp in f.loops]


# --- #392 -----------------------------------------------------------------------------------------

@step
def s_setup():
    C["x"], C["y"] = setup()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.ops.mesh.primitive_cylinder_add(vertices=20)
        C["cyl"] = bpy.context.active_object.name
        bpy.ops.ed.undo_push(message="cylinder")
    C["uv0"] = obj_uvs(bpy.data.objects[C["cyl"]])


@step
def s_camera_based():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["res"] = bpy.ops.allset.menu_item('INVOKE_DEFAULT', True, item="UV/Camera-based")
    ob = bpy.data.objects[C["cyl"]]
    uvs = obj_uvs(ob)
    check(f"UV > Camera-based in object mode maps the whole cylinder ({C['res']}, changed {uvs != C['uv0']}, "
          f"mode {ob.mode})", C["res"] == {'FINISHED'} and uvs != C["uv0"] and ob.mode == 'OBJECT')
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])


@step
def s_undo_press():
    ev('LEFT_CTRL', 'PRESS')
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


@step
def s_undone():
    ob = bpy.data.objects[C["cyl"]]
    check("Ctrl+Z puts the cylinder's UVs back", obj_uvs(ob) == C["uv0"])


# --- #393 -----------------------------------------------------------------------------------------

def side_uv(i, j):
    return (0.3 + 0.1 * j + 0.03 * math.sin(i * 0.7) + 0.004 * i, 0.05 + 0.065 * i + 0.01 * math.sin(j * 1.3))


@step
def s_ribbon():
    """A cylinder side cut along one edge line, laid out as a wavy upright ribbon (one shell)."""
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    me = bpy.data.meshes.new("ribbon")
    b = bmesh.new()
    uv = b.loops.layers.uv.new("map1")
    ring = [[b.verts.new((math.cos(2 * math.pi * i / N), math.sin(2 * math.pi * i / N), 0.5 * j))
             for i in range(N)] for j in range(H + 1)]
    corners_of = {}
    for j in range(H):
        for i in range(N):
            corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            f = b.faces.new([ring[jj][ii % N] for ii, jj in corners])
            corners_of[f] = corners
            for lp, (ii, jj) in zip(f.loops, corners):
                lp[uv].uv = side_uv(ii, jj)
    b.faces.index_update()
    C["where"] = {f.index: c for f, c in corners_of.items()}
    b.to_mesh(me)
    b.free()
    ob = bpy.data.objects.new("ribbon", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    C["rib"] = ob.name
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["open"] = mod(".marking.modal").run_action(bpy.context, mod(".ui.menu_map").MAP["UV/UV Editor"])


@step
def s_wait_uv_window():
    C.setdefault("wait", 0)
    if uv_window()[1] is None and C["wait"] < 15:
        C["wait"] += 1
        sys.modules["sim"]._steps.insert(0, s_wait_uv_window)


@step
def s_select_loop():
    w, a, r = uv_window()
    ob = bpy.data.objects[C["rib"]]
    check(f"UV > UV Editor opens a UV Editor window, ribbon in edit mode ({a is not None}, {ob.mode})",
          a is not None and ob.mode == 'EDIT')
    if a is None:
        return
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    b = bmesh.from_edit_mesh(ob.data)
    uv = b.loops.layers.uv.active
    b.faces.ensure_lookup_table()
    on = set()
    for fi, corners in C["where"].items():
        for k, lp in enumerate(b.faces[fi].loops):
            if corners[k][1] == RING and corners[(k + 1) % 4][1] == RING:
                on.add(lp.edge)
    ring_verts = {v for e in on for v in e.verts}
    for f in b.faces:
        f.select = True
        for lp in f.loops:
            lp.uv_select_vert = lp.vert in ring_verts
            lp.uv_select_edge = lp.edge in on
    bmesh.update_edit_mesh(ob.data)
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
        bpy.ops.ed.undo_push(message="loop")
    C["uv1"] = edit_uvs(ob)


@step
def s_straighten():
    w, a, r = uv_window()
    if a is None:
        return
    with bpy.context.temp_override(window=w, area=a, region=r):
        C["res"] = bpy.ops.allset.menu_item('INVOKE_DEFAULT', True, item="UV Editor/Modify/Straighten Shell")
    ob = bpy.data.objects[C["rib"]]
    b = bmesh.from_edit_mesh(ob.data)
    uv = b.loops.layers.uv.active
    b.faces.ensure_lookup_table()
    grid = {}
    for fi, corners in C["where"].items():
        for lp, ij in zip(b.faces[fi].loops, corners):
            grid[ij] = lp[uv].uv.copy()
    width = max(p.x for p in grid.values()) - min(p.x for p in grid.values())
    height = max(p.y for p in grid.values()) - min(p.y for p in grid.values())
    rings = max(max(grid[i, j].x for i in range(N + 1)) - min(grid[i, j].x for i in range(N + 1))
                for j in range(H + 1))
    check(f"Straighten Shell: a straight upright strip at once ({C['res']}, width {width:.3f}, height {height:.3f}, "
          f"ring bend {rings:.6f})", C["res"] == {'FINISHED'} and height > 2 * width and rings < 1e-4 * height)
    x, y = r.x + r.width // 2, r.y + r.height // 2
    C["uvpos"] = (x, y)
    w.event_simulate(type='MOUSEMOVE', value='NOTHING', x=x, y=y)


@step
def s_uv_undo():
    w, _a, _r = uv_window()
    x, y = C["uvpos"]
    w.event_simulate(type='LEFT_CTRL', value='PRESS', x=x, y=y)
    w.event_simulate(type='Z', value='PRESS', x=x, y=y, ctrl=True)
    w.event_simulate(type='Z', value='RELEASE', x=x, y=y, ctrl=True)
    w.event_simulate(type='LEFT_CTRL', value='RELEASE', x=x, y=y)


@step
def s_uv_undone():
    ob = bpy.data.objects[C["rib"]]
    check("Ctrl+Z in the UV Editor puts the wavy shell back", ob.mode == 'EDIT' and edit_uvs(ob) == C["uv1"])


run()
