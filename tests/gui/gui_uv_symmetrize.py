"""In a real UI: an 8 x 8 grid in the UV Editor. Modify > Symmetrize makes the kit's Symmetrize brush the tool; the first
click on a middle up-down edge picks the symmetry line (no UV changes, Mirror Axis U); then a drag on the left half gives
the moved left UVs under the brush the mirror of their right counterparts again, UVs outside the brush stay; Ctrl+click
changes nothing; leaving the tool forgets the line (screenshot)."""
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



def near(st, u, v, tol=1e-4):
    return [k for k, (uv, _p) in st.items() if abs(uv[0] - u) < tol and abs(uv[1] - v) < tol]



def jitter_left():
    bm = bmesh.from_edit_mesh(grid().data)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        for l in f.loops:
            u, v = l[uv].uv
            if u < 0.49:
                l[uv].uv = (u + 0.02, v + 0.01)
    bmesh.update_edit_mesh(grid().data)


@step
def s_tool():
    w, a, r = uv_window()
    check(f"UV Editor open ({a is not None})", a is not None)
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
    menu_item("UV Editor/Modify/Symmetrize")
    check(f"Modify > Symmetrize makes the Symmetrize brush the tool ({tool_id()})",
          tool_id() == "allset.uv_brush_symmetrize")
    s = bpy.context.scene.allset_uv_brush
    s.sym_size, s.sym_axis = 0.2, 'V'
    jitter_left()
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.5, 0.0625))


@step
def s_pick():
    C["before"] = uv_state()
    drag([uv_px(0.5, 0.0625)])


@step
def s_pick_release():
    release()


@step
def s_picked():
    sym = mod(".operators.uv_symmetrize")
    check("the pick changes no UV", uv_state() == C["before"])
    check(f"the pick remembers the line ({len(sym.segments())} segments)", len(sym.segments()) == 8)
    check(f"an up-down edge sets Mirror Axis U ({bpy.context.scene.allset_uv_brush.sym_axis})",
          bpy.context.scene.allset_uv_brush.sym_axis == 'U')
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.25, 0.5))


@step
def s_ctrl():
    C["before"] = uv_state()
    drag([uv_px(0.25, 0.5), uv_px(0.26, 0.5)], ctrl=True)


@step
def s_ctrl_release():
    uv_ev('LEFTMOUSE', 'RELEASE', ctrl=True)
    redraw_all()


@step
def s_ctrl_checked():
    check("Ctrl+click changes nothing", uv_state() == C["before"])
    drag([uv_px(0.27, 0.5), uv_px(0.25, 0.5), uv_px(0.23, 0.5)])


@step
def s_paint_shot():
    shot("uv_symmetrize.png")
    release()


@step
def s_painted():
    st = uv_state()
    b = C["before"]
    under = near(b, 0.27, 0.51)          # grid UV (0.25, 0.5) moved by (0.02, 0.01)
    outside = near(b, 0.02, 0.01)        # grid UV (0, 0), far from the brush
    right = near(b, 0.75, 0.5)
    ok_under = under and all(abs(st[k][0][0] - 0.25) < 1e-5 and abs(st[k][0][1] - 0.5) < 1e-5 for k in under)
    check(f"a moved left UV under the brush gets the mirror of its right counterpart ({under and st[under[0]][0]})",
          ok_under)
    check("a left UV outside the brush stays", outside and st[outside[0]][0] == b[outside[0]][0])
    check("the right half stays", right and st[right[0]][0] == b[right[0]][0])
    menu_item("UV Editor/Tools/Pinch")
    redraw_all()


@step
def s_left():
    sym = mod(".operators.uv_symmetrize")
    check(f"leaving the tool forgets the line ({len(sym.segments())})", not sym.segments())


run()
