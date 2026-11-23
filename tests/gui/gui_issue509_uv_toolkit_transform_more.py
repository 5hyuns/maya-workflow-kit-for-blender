"""In a real UI (#509): a 4 x 4 grid in the UV Editor, four UVs selected; the UV Toolkit's Transform section shows the
preset buttons, the Step Snap rows, Retain Component Spacing and Distribute U / V (screenshot); Move Step Snap on with a
step of 0.25 sets the UV grid to 4; a Rotate 45 item turns the selection; Distribute along V runs."""
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
    shot("gui_issue509_uv_toolkit_transform.png", w)



@step
def s_step_snap():
    w, a, r = uv_window()
    tk = bpy.context.scene.allset_uv_toolkit
    ts = bpy.context.scene.tool_settings
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.allset.uv_step_snap(kind='TRANSLATE')
        tk.move_snap_value = 0.25
    ed = a.spaces.active.uv_editor
    check(f"Move Step Snap on, step 0.25 = a UV grid of 4 ({ed.grid_shape_source}, "
          f"{tuple(ed.custom_grid_subdivisions)})", mod(".operators.snap_align").uv_step_snap_on(ts, 'TRANSLATE')
          and ed.grid_shape_source == 'FIXED' and tuple(ed.custom_grid_subdivisions) == (4, 4))
    redraw_all()


@step
def s_step_snap_shot():
    shot("gui_issue509_step_snap.png", uv_window()[0])
    w, a, r = uv_window()
    b0 = picked_box()
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.allset.uv_rotate_step(angle=45.0)
    b1 = picked_box()
    check(f"a Rotate button's 45 item turns the selection ({b0} -> {b1})", b0 != b1)
    tk = bpy.context.scene.allset_uv_toolkit
    tk.distribute_axis = 'V'
    with bpy.context.temp_override(window=w, area=a, region=r):
        res = bpy.ops.allset.uv_distribute_toolkit()
    check(f"Distribute along V runs ({res})", res == {'FINISHED'})
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.allset.uv_step_snap(kind='TRANSLATE')


run()
