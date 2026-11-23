"""In a real UI (#494): a 4 x 4 grid -> UV > UV Editor -> UV component, four UVs selected -> the UV Toolkit's
Transform section (Pivot / Move / Rotate / Scale) and Align and Snap's Snap grid are drawn, the Move U / V fields show
the selection's centre; Move, Pivot and Scale buttons act in the UV Editor (screenshots)."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
N = 4


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


def shot(name, window=None):
    if SHOTS:
        with bpy.context.temp_override(window=window or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def uv_ev(type, value, x=None, y=None, **kw):
    """sim.ev for the UV Editor window (keeps sim's simulated key state: the menu engine reads it)."""
    down = sys.modules["sim"]._down
    if value == 'PRESS':
        down.add(type)
    elif value == 'RELEASE':
        down.discard(type)
    w, _a, _r = uv_window()
    if x is None:
        x, y = C["uvpos"]
    C["uvpos"] = (x, y)
    w.event_simulate(type=type, value=value, x=x, y=y, **kw)


def centre():
    _w, _a, r = uv_window()
    return r.x + r.width // 2, r.y + r.height // 2


def redraw_all():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def session():
    return mod(".marking.draw").ACTIVE.get("session")


def open_menu_name():
    s = session()
    return getattr(s.stack[0][0].sub, "name", None) if s is not None else None




@step
def s_setup():
    C["x"], C["y"] = setup()
    tk = mod(".ui.uv_toolkit")
    original = tk._section

    def opened(layout, idname, label, default_closed=True):     # Transform and Align and Snap shown open
        return original(layout, idname, label, default_closed=default_closed and idname not in (
            "ALLSET_uvtk_transform", "ALLSET_uvtk_align") and idname != "ALLSET_uvtk_cut")
    tk._section = opened
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


def pick_uvs():
    """UV component, the UVs of the bottom-left face selected."""
    w, a, r = uv_window()
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.allset.uv_component(mode='UV')
    b = bmesh.from_edit_mesh(grid().data)
    uv = b.loops.layers.uv.active
    lo = min(v.co.x for v in b.verts)
    corner = {(0, 0), (1, 0), (0, 1), (1, 1)}
    step_ = 2.0 / N

    def on(v):
        return (round((v.co.x - lo) / step_), round((v.co.y - lo) / step_)) in corner
    compat = mod(".compat")
    for f in b.faces:
        for lp in f.loops:
            compat.set_uv_vert_selected(lp, uv, on(lp.vert))
            compat.set_uv_edge_selected(lp, uv, on(lp.vert) and on(lp.link_loop_next.vert))
    bmesh.update_edit_mesh(grid().data)


def picked_box():
    b = bmesh.from_edit_mesh(grid().data)
    uv = b.loops.layers.uv.active
    compat = mod(".compat")
    pts = [tuple(lp[uv].uv) for f in b.faces for lp in f.loops if compat.uv_vert_selected(lp, uv)]
    return (round(min(p[0] for p in pts), 4), round(min(p[1] for p in pts), 4),
            round(max(p[0] for p in pts), 4), round(max(p[1] for p in pts), 4))


@step
def s_opened():
    w, a, r = uv_window()
    check(f"UV > UV Editor: a UV Editor window, grid in edit mode ({C['open']}, {a is not None}, {grid().mode})",
          a is not None and grid().mode == 'EDIT')
    if a is None:
        return
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
    a.spaces.active.show_region_ui = True
    pick_uvs()
    C["box0"] = picked_box()
    redraw_all()


@step
def s_toolkit_drawn():
    w, a, r = uv_window()
    tk = bpy.context.scene.allset_uv_toolkit
    with bpy.context.temp_override(window=w, area=a, region=r):
        mod(".ui.uv_hud")._invalidate()
        u, v = tk.position_u, tk.position_v
    b = C["box0"]
    check(f"the Move U / V fields show the selection's centre ({u:.4f}, {v:.4f})",
          abs(u - (b[0] + b[2]) / 2) < 1e-4 and abs(v - (b[1] + b[3]) / 2) < 1e-4)
    shot("gui_issue494_uv_toolkit_transform.png", w)


@step
def s_run_buttons():
    w, a, r = uv_window()
    b = C["box0"]
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.allset.uv_nudge(direction='UP_RIGHT')
        moved = picked_box()
        bpy.ops.allset.uv_pivot(position='BOTTOM_LEFT')
        piv = mod(".operators.uv_transform").cursor_uv(a.spaces.active)
        bpy.ops.allset.uv_scale_step()
        scaled = picked_box()
        bpy.ops.allset.uv_pivot_reset()
    check(f"Move up right by 0.1 ({b} -> {moved})",
          all(abs(m - (o + 0.1)) < 1e-4 for m, o in zip(moved, b)))
    check(f"the pivot on the selection's bottom left ({piv})",
          abs(piv[0] - moved[0]) < 1e-4 and abs(piv[1] - moved[1]) < 1e-4)
    w0, h0 = moved[2] - moved[0], moved[3] - moved[1]
    check(f"Scale x2 about that pivot ({scaled})", abs(scaled[0] - moved[0]) < 1e-4
          and abs(scaled[2] - (moved[0] + 2 * w0)) < 1e-4 and abs(scaled[3] - (moved[1] + 2 * h0)) < 1e-4)
    redraw_all()


@step
def s_end():
    shot("gui_issue494_uv_toolkit_after.png", uv_window()[0])
    check("UV Editor still open", uv_window()[1] is not None)


run()
