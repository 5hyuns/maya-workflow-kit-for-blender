"""In a real UI (#513): an 8 x 8 grid in the UV Editor, Cut tool with Cut Open Ratio 0.5 and Display All Shell Borders:
a drag along the middle row of edges cuts the grid in two and opens a gap of half an edge between the split UVs, both
shells' borders are drawn; with Steady Stroke (Distance 0.2) the same drag on another row stops short of the mouse
(screenshots)."""
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
def s_cut():
    w, a, r = uv_window()
    check(f"UV Editor open ({a is not None})", a is not None)
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
    menu_item("UV Editor/Tools/Cut")
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.5, 0.3))


@step
def s_cut_drag():
    s = bpy.context.scene.allset_uv_brush
    s.cut_open_ratio, s.cut_steady, s.show_shell_borders = 0.5, False, True
    C["seams"] = seams()
    v = 0.5 + 0.004
    drag([uv_px(0.02 + 0.03 * k, v) for k in range(33)])


@step
def s_cut_release():
    release()


@step
def s_cut_checked():
    check(f"the Cut drag along a row of edges cut them ({C['seams']} -> {seams()} seams)", seams() - C["seams"] >= N)
    bm = bmesh.from_edit_mesh(grid().data)
    uv = bm.loops.layers.uv.active
    mid = sorted({round(l[uv].uv.y, 5) for v in bm.verts if abs(v.co.x) < 1e-6 and abs(v.co.y) < 1e-6
                  for l in v.link_loops})
    gap = mid[-1] - mid[0] if mid else 0.0
    check(f"Cut Open Ratio 0.5 opens a gap of half an edge (1/16) between the split UVs ({gap:.4f})",
          abs(gap - 0.5 / N) < 1e-3)
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.5, 0.3))
    redraw_all()


@step
def s_borders_hover():
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.52, 0.32))
    redraw_all()


@step
def s_borders_shot():
    b = mod(".operators.uv_brush")._borders
    check(f"Display All Shell Borders: the borders of both shells are drawn ({len(b['segments'])} segments)",
          len(b["segments"]) >= 4 * N + 2 * N)
    shot("issue513_shell_borders.png")


@step
def s_steady():
    s = bpy.context.scene.allset_uv_brush
    s.cut_steady, s.cut_steady_distance, s.show_shell_borders = True, 0.2, False
    C["seams"] = seams()
    v = 0.25 + 0.004
    drag([uv_px(0.02 + 0.03 * k, v) for k in range(33)])


@step
def s_steady_shot():
    shot("issue513_steady.png")
    release()


@step
def s_steady_checked():
    cut = seams() - C["seams"]
    check(f"Steady Stroke 0.2: the stroke stops 0.2 short of the mouse, fewer edges cut ({cut} of {N})",
          0 < cut < N)
    bpy.context.scene.allset_uv_brush.cut_steady = False


run()
