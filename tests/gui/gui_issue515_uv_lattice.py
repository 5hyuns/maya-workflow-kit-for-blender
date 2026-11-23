"""In a real UI (#515): an 8 x 8 grid in the UV Editor, Lattice tool. Falloff 0.5: a corner drag moves the corner UV
half way; the picked point shows a move handle whose V arrow moves it along V only; dragging a lattice line moves both
its points; with Use bounding rectangle off a drag on empty space draws the lattice (no UV moves) and dragging its
corner bends only the UVs inside it (screenshots)."""
import os
import sys
from importlib import import_module

import bmesh
import numpy as np
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
N = 8


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def grid():
    return bpy.data.objects[C["grid"]]


def uv_window():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.ui_type == 'UV':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


def shot(name):
    if SHOTS:
        w, _a, _r = uv_window()
        with bpy.context.temp_override(window=w or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def uv_ev(type, value, x=None, y=None, **kw):
    """sim.ev for the UV Editor window (keeps sim's simulated key state: tap / hold keys read it)."""
    down = sys.modules["sim"]._down
    if value == 'PRESS':
        down.add(type)
    elif value == 'RELEASE':
        down.discard(type)
    w, _a, _r = uv_window()
    if x is None:
        x, y = C["uvpos"]
    C["uvpos"] = (int(x), int(y))
    w.event_simulate(type=type, value=value, x=int(x), y=int(y), **kw)


def uv_px(u, v):
    _w, _a, r = uv_window()
    x, y = r.view2d.view_to_region(u, v, clip=False)
    return r.x + x, r.y + y


def redraw_all():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def tool_id():
    w, a, r = uv_window()
    with bpy.context.temp_override(window=w, area=a, region=r):
        t = bpy.context.workspace.tools.from_space_image_mode('UV', create=False)
    return t.idname if t else ""


def menu_item(path):
    w, a, r = uv_window()
    with bpy.context.temp_override(window=w, area=a, region=r):
        return mod(".marking.modal").run_action(bpy.context, mod(".ui.menu_map").MAP[path])


def uv_state():
    bm = bmesh.from_edit_mesh(grid().data)
    uv = bm.loops.layers.uv.active
    return {l.index: (tuple(l[uv].uv), l[uv].pin_uv) for f in bm.faces for l in f.loops}


def seams():
    bm = bmesh.from_edit_mesh(grid().data)
    return sum(e.seam for e in bm.edges)


def drag(points, ctrl=False):
    uv_ev('MOUSEMOVE', 'NOTHING', *points[0])
    uv_ev('LEFTMOUSE', 'PRESS', *points[0], ctrl=ctrl)
    for p in points[1:]:
        uv_ev('MOUSEMOVE', 'NOTHING', *p, ctrl=ctrl)


def release():
    uv_ev('LEFTMOUSE', 'RELEASE')
    redraw_all()


@step
def s_setup():
    C["x"], C["y"] = setup()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for ob in list(bpy.data.objects):
            ob.select_set(False)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=N, y_subdivisions=N, size=2.0)
        C["grid"] = bpy.context.active_object.name
        C["open"] = mod(".marking.modal").run_action(bpy.context, mod(".ui.menu_map").MAP["UV/UV Editor"])


@step
def s_wait_uv_window():
    import sim
    C.setdefault("wait_uv", 0)
    if uv_window()[1] is None and C["wait_uv"] < 15:
        C["wait_uv"] += 1
        sim._steps.insert(0, s_wait_uv_window)



def uvs_near(st, u, v, tol=1e-4):
    return [k for k, (uv, _p) in st.items() if abs(uv[0] - u) < tol and abs(uv[1] - v) < tol]


def uv_of(k):
    return uv_state()[k][0]


@step
def s_lattice():
    w, a, r = uv_window()
    check(f"UV Editor open ({a is not None})", a is not None)
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
        bpy.ops.mesh.select_all(action='SELECT')
    menu_item("UV Editor/Tools/Lattice")
    s = bpy.context.scene.allset_uv_brush
    s.lattice_falloff, s.lattice_bounding_rect, s.lattice_move_manipulator = 0.5, True, True
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.9, 0.9))
    redraw_all()


@step
def s_falloff_drag():
    C["before"] = uv_state()
    C["corner"] = uvs_near(C["before"], 1.0, 1.0)[0]
    drag([uv_px(1.0, 1.0), uv_px(1.05, 1.0), uv_px(1.1, 1.0)])


@step
def s_falloff_checked():
    release()
    moved = uv_of(C["corner"])[0] - C["before"][C["corner"]][0][0]
    check(f"Falloff 0.5: the corner UV follows its lattice point half way ({moved:.4f} of 0.1)", abs(moved - 0.05) < 4e-3)
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.5, 0.5))
    redraw_all()


@step
def s_pick_centre():
    lat = mod(".operators.uv_lattice")._state["lattice"]
    p = tuple(lat.pts[1, 1])
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(*p))
    uv_ev('LEFTMOUSE', 'PRESS', *uv_px(*p))
    uv_ev('LEFTMOUSE', 'RELEASE', *uv_px(*p))
    redraw_all()


@step
def s_manip_shot():
    shot("issue515_lattice_manipulator.png")
    s = bpy.context.scene.allset_uv_brush
    s.lattice_falloff = 1.0
    lat = mod(".operators.uv_lattice")._state["lattice"]
    check(f"the picked point carries the move handle ({lat.picked if lat else None})",
          lat is not None and lat.picked == (1, 1))
    # drag the V arrow of the handle: the point moves only along V
    _w, _a, r = uv_window()
    hx, hy = mod(".operators.uv_lattice")._manip_handles(r, lat, bpy.context.preferences.system.ui_scale)["V"]
    C["p0"] = tuple(lat.pts[1, 1])
    drag([(r.x + hx, r.y + hy), (r.x + hx + 30, r.y + hy + 20), (r.x + hx + 60, r.y + hy + 40)])


@step
def s_manip_checked():
    release()
    lat = mod(".operators.uv_lattice")._state["lattice"]
    p = tuple(lat.pts[1, 1]) if lat is not None else (0, 0)
    check(f"the V arrow moves the point along V only ({C['p0']} -> {p})",
          abs(p[0] - C["p0"][0]) < 1e-6 and p[1] > C["p0"][1] + 0.01)


@step
def s_line_drag():
    lat = mod(".operators.uv_lattice")._state["lattice"]
    C["pts0"] = lat.pts.copy()
    a, b = lat.pts[0, 0], lat.pts[0, 1]            # the bottom line between the first two points
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    drag([uv_px(*m), uv_px(m[0], m[1] - 0.03), uv_px(m[0], m[1] - 0.06)])


@step
def s_line_checked():
    release()
    lat = mod(".operators.uv_lattice")._state["lattice"]
    d = lat.pts - C["pts0"]
    moved = [tuple(int(x) for x in ij) for ij in np.argwhere(np.abs(d).max(axis=2) > 1e-6)]
    check(f"dragging a lattice line moves both its points ({moved})", sorted(moved) == [(0, 0), (0, 1)])


@step
def s_draw_rect():
    w, a, r = uv_window()
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.ed.undo()
    s = bpy.context.scene.allset_uv_brush
    s.lattice_bounding_rect = False
    C["before"] = uv_state()
    drag([uv_px(0.05, 0.05), uv_px(0.2, 0.2), uv_px(0.51, 0.51)])


@step
def s_draw_rect_shot():
    shot("issue515_lattice_draw.png")
    release()


@step
def s_draw_rect_checked():
    lat = mod(".operators.uv_lattice")._state["lattice"]
    check(f"Use bounding rectangle off: the drag draws the lattice ({lat.rect if lat else None})",
          lat is not None and lat.drawn and abs(lat.rect[2] - 0.51) < 0.01)
    check("drawing the lattice moves no UV", uv_state() == C["before"])
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.6, 0.6))


@step
def s_drawn_drag():
    lat = mod(".operators.uv_lattice")._state["lattice"]
    C["rect"] = lat.rect
    drag([uv_px(lat.rect[2], lat.rect[3]), uv_px(lat.rect[2] + 0.05, lat.rect[3]),
          uv_px(lat.rect[2] + 0.1, lat.rect[3])])


@step
def s_drawn_checked():
    release()
    st = uv_state()
    r = C["rect"]
    outside = [k for k, (uv, _p) in C["before"].items() if uv[0] > r[2] + 1e-3 or uv[1] > r[3] + 1e-3]
    inside = [k for k, (uv, _p) in C["before"].items() if 0.3 < uv[0] < r[2] - 0.01 and 0.3 < uv[1] < r[3] - 0.01]
    moved_out = [k for k in outside if st[k][0] != C["before"][k][0]]
    moved_in = [k for k in inside if st[k][0][0] > C["before"][k][0][0] + 1e-4]
    check(f"the drawn lattice bends the UVs inside it ({len(moved_in)} of {len(inside)}), not those outside "
          f"({len(moved_out)})", inside and len(moved_in) == len(inside) and not moved_out)
    bpy.context.scene.allset_uv_brush.lattice_bounding_rect = True


run()
