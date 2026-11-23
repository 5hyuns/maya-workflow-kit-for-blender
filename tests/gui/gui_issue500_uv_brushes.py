"""In a real UI (#500): an 8 x 8 grid -> UV > UV Editor -> UV Editor > Tools > Pin makes the Pin brush the active UV
Editor tool; an LMB drag pins the UVs under the brush only; B + LMB drag right makes the brush bigger; Tools > Smear
and a drag pushes UVs; Tools > Cut and a drag along a row of edges cuts them; Tools > Optimize and a drag relaxes the smeared UVs; Tools >
Lattice and a drag of its corner point bends the UVs; RMB opens the brush marking menu;
W leaves the brush for the Move tool (screenshot of the brush circle)."""

import os
import sys
from importlib import import_module

import bmesh
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


@step
def s_pin_tool():
    w, a, r = uv_window()
    check(f"UV > UV Editor: a UV Editor window, grid in edit mode ({a is not None}, {grid().mode})",
          a is not None and grid().mode == 'EDIT')
    if a is None:
        return
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
    menu_item("UV Editor/Tools/Pin")
    check(f"Tools > Pin makes the Pin brush the UV Editor tool ({tool_id()})", tool_id() == "allset.uv_brush_pin")
    bpy.context.scene.allset_uv_brush.pin_size = 0.1
    C["uvpos"] = uv_px(0.5, 0.5)
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.3, 0.5))
    redraw_all()


@step
def s_pin_drag():
    C["before"] = uv_state()
    drag([uv_px(0.3, 0.5), uv_px(0.4, 0.5), uv_px(0.5, 0.5)])


@step
def s_pin_shot():
    shot("issue500_pin_circle.png")
    release()


@step
def s_pin_checked():
    st = uv_state()
    pinned = {k for k, (_uv, p) in st.items() if p}
    near = {k for k, (uv, _p) in st.items() if 0.2 <= uv[0] <= 0.6 and abs(uv[1] - 0.5) < 0.05}
    far = {k for k, (uv, _p) in st.items() if uv[0] > 0.8 or abs(uv[1] - 0.5) > 0.3}
    check(f"the drag pinned the UVs under the stroke ({len(pinned & near)} of {len(near)})",
          near and near <= pinned)
    check(f"UVs away from the brush stay unpinned ({len(pinned & far)})", not (pinned & far))
    C["pinned"] = len(pinned)


@step
def s_size_press():
    C["size0"] = bpy.context.scene.allset_uv_brush.pin_size
    x, y = uv_px(0.5, 0.5)
    uv_ev('MOUSEMOVE', 'NOTHING', x, y)
    uv_ev('B', 'PRESS', x, y)


@step
def s_size_drag():
    x, y = uv_px(0.5, 0.5)
    uv_ev('LEFTMOUSE', 'PRESS', x, y)
    for k in range(1, 6):
        uv_ev('MOUSEMOVE', 'NOTHING', x + 20 * k, y)


@step
def s_size_release():
    uv_ev('LEFTMOUSE', 'RELEASE')
    uv_ev('B', 'RELEASE')
    redraw_all()


@step
def s_size_checked():
    s = bpy.context.scene.allset_uv_brush
    check(f"B + LMB drag 100 px right doubles the brush size ({C['size0']:.3f} -> {s.pin_size:.3f})",
          abs(s.pin_size - 2 * C["size0"]) < 0.01 * C["size0"] + 1e-6)
    pinned = sum(p for _uv, p in uv_state().values())
    check(f"the size drag pinned nothing ({C['pinned']} -> {pinned})", pinned == C["pinned"])
    shot("issue500_pin_big_circle.png")


@step
def s_smear():
    menu_item("UV Editor/Tools/Smear")
    check(f"Tools > Smear makes the Smear brush the tool ({tool_id()})", tool_id() == "allset.uv_brush_smear")
    C["before"] = uv_state()
    drag([uv_px(0.5, 0.2), uv_px(0.55, 0.2), uv_px(0.6, 0.2), uv_px(0.65, 0.2)])


@step
def s_smear_release():
    release()


@step
def s_smear_checked():
    st = uv_state()
    moved = [k for k in st if abs(st[k][0][0] - C["before"][k][0][0]) > 1e-4]
    far = [k for k in moved if abs(C["before"][k][0][1] - 0.2) > 0.2]
    check(f"the Smear drag moved UVs along the stroke ({len(moved)}), none far from it ({len(far)})",
          moved and not far)


@step
def s_cut():
    menu_item("UV Editor/Tools/Cut")
    check(f"Tools > Cut makes the Cut brush the tool ({tool_id()})", tool_id() == "allset.uv_brush_cut")
    C["seams"] = seams()
    v = 0.75 + 0.004
    drag([uv_px(0.02 + 0.03 * k, v) for k in range(33)])


@step
def s_cut_release():
    release()


@step
def s_cut_checked():
    check(f"the Cut drag along a row of edges cut them ({C['seams']} -> {seams()} seams)", seams() - C["seams"] >= N)


@step
def s_optimize():
    menu_item("UV Editor/Tools/Optimize")
    check(f"Tools > Optimize makes the Optimize brush the tool ({tool_id()})", tool_id() == "allset.uv_brush_optimize")
    C["before"] = uv_state()
    drag([uv_px(0.55, 0.2), uv_px(0.6, 0.2), uv_px(0.65, 0.2)])


@step
def s_optimize_release():
    release()


@step
def s_optimize_checked():
    st = uv_state()
    moved = [k for k in st if max(abs(st[k][0][i] - C["before"][k][0][i]) for i in (0, 1)) > 1e-5]
    far = [k for k in moved if abs(C["before"][k][0][1] - 0.2) > 0.25]
    check(f"the Optimize drag relaxed the smeared UVs ({len(moved)}), none far from the brush ({len(far)})",
          moved and not far)


@step
def s_lattice():
    w, a, r = uv_window()
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.mesh.select_all(action='SELECT')
    menu_item("UV Editor/Tools/Lattice")
    check(f"Tools > Lattice makes the Lattice tool active ({tool_id()})", tool_id() == "allset.uv_lattice")
    C["before"] = uv_state()
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.9, 0.9))
    redraw_all()


@step
def s_lattice_drag():
    drag([uv_px(1.0, 1.0), uv_px(1.05, 1.02), uv_px(1.1, 1.05)])


@step
def s_lattice_shot():
    shot("issue500_lattice.png")
    release()


@step
def s_lattice_checked():
    st = uv_state()
    corner = [k for k, (uv, _p) in C["before"].items() if uv[0] > 0.95 and uv[1] > 0.95]
    low = [k for k, (uv, _p) in C["before"].items() if uv[0] < 0.6 or uv[1] < 0.6]
    moved_corner = all(st[k][0][0] > C["before"][k][0][0] + 0.05 for k in corner)
    moved_low = [k for k in low if abs(st[k][0][0] - C["before"][k][0][0]) > 1e-6]
    check(f"dragging the lattice corner moved the corner UVs ({moved_corner}), not the UVs outside its cells "
          f"({len(moved_low)})", corner and moved_corner and not moved_low)
    menu_item("UV Editor/Tools/Pin")


@step
def s_rmb():
    x, y = uv_px(0.5, 0.5)
    uv_ev('MOUSEMOVE', 'NOTHING', x, y)
    uv_ev('RIGHTMOUSE', 'PRESS', x, y)


@step
def s_rmb_open():
    s = mod(".marking.draw").ACTIVE.get("session")
    name = getattr(s.stack[0][0].sub, "name", None) if s is not None else None
    check(f"RMB with a brush tool opens the brush marking menu ({name})", name == "UV_BRUSH")
    shot("issue500_brush_menu.png")
    uv_ev('ESC', 'PRESS')
    uv_ev('ESC', 'RELEASE')
    uv_ev('RIGHTMOUSE', 'RELEASE')


@step
def s_w():
    x, y = uv_px(0.5, 0.5)
    uv_ev('W', 'PRESS', x, y)
    uv_ev('W', 'RELEASE', x, y)


@step
def s_w_checked():
    check(f"W leaves the brush for the Move tool ({tool_id()})", tool_id() == "builtin.move")


run()
