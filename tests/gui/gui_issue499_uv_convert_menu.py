"""In a real UI (#499): a 4 x 4 grid -> UV > UV Editor -> UV component, four UVs selected -> Ctrl+RMB opens the UV
Editor's selection conversion marking menu (ring To Faces / To Edges / To UVs / To Vertices / Grow / Shrink /
To UV Shell / To UV Shell Border) -> release on Inverse Selection in its list -> the other UVs are selected
(screenshot)."""

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


@step
def s_opened():
    w, a, r = uv_window()
    check(f"UV > UV Editor: a UV Editor window, grid in edit mode ({C['open']}, {a is not None}, {grid().mode})",
          a is not None and grid().mode == 'EDIT')
    if a is None:
        return
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
    pick_uvs()
    check("UV component: UV Sync Selection off", not bpy.context.scene.tool_settings.use_uv_select_sync)
    C["uvpos"] = centre()
    uv_ev('MOUSEMOVE', 'NOTHING', *centre())
    redraw_all()


@step
def s_press():
    x, y = C["c"] = centre()
    uv_ev('MOUSEMOVE', 'NOTHING', x, y)
    uv_ev('LEFT_CTRL', 'PRESS', x, y)
    uv_ev('RIGHTMOUSE', 'PRESS', x, y, ctrl=True)


@step
def s_menu_open():
    name = open_menu_name()
    check(f"Ctrl+RMB in the UV Editor opens the conversion menu (got {name})", name == "UV_CONVERT")
    s = session()
    if s is None:
        return
    ring = {k: it.label for k, it in s.layout.radial.items()}
    check(f"ring: S To Faces, N To Edges, E To UVs, W To Vertices, NE Grow, NW Shrink, SE To UV Shell, "
          f"SW To UV Shell Border ({ring})",
          ring == {"S": "To Faces", "N": "To Edges", "E": "To UVs", "W": "To Vertices", "NE": "Grow Selection",
                   "NW": "Shrink Selection", "SE": "To UV Shell", "SW": "To UV Shell Border"})
    labels = [it.label for it in s.layout.items if it.label and it.label not in ring.values()]
    check(f"the list starts with Select All / Clear Selection / Inverse Selection ({labels[:3]})",
          labels[:3] == ["Select All", "Clear Selection", "Inverse Selection"])
    w, _a, _r = uv_window()
    shot("gui_issue499_uv_convert_menu.png", w)
    item = next((it for it in s.layout.items if it.label == "Inverse Selection"), None)
    if item is None:
        return
    box = item.rect
    x = C["c"][0] + int(s.center[0] - s.press[0] + (box[0] + box[2]) / 2)
    y = C["c"][1] + int(s.center[1] - s.press[1] + (box[1] + box[3]) / 2)
    C["release"] = (x, y)
    uv_ev('MOUSEMOVE', 'NOTHING', x, y, ctrl=True)


@step
def s_release():
    x, y = C["release"]
    uv_ev('RIGHTMOUSE', 'RELEASE', x, y, ctrl=True)
    uv_ev('LEFT_CTRL', 'RELEASE', x, y)
    redraw_all()


@step
def s_inverted():
    b = bmesh.from_edit_mesh(grid().data)
    uv = b.loops.layers.uv.active
    compat = mod(".compat")
    on = {lp.vert.index for f in b.faces for lp in f.loops if compat.uv_vert_selected(lp, uv)}
    check(f"Inverse Selection ran in the UV Editor: 25 - 4 UVs selected ({len(on)})", len(on) == (N + 1) ** 2 - 4)
    check("menu closed", not mod(".marking.draw").ACTIVE)


@step
def s_end():
    check("menu closed at the end", not mod(".marking.draw").ACTIVE)


run()
