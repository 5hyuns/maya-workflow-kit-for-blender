"""In a real UI (#517): an 8 x 8 grid in the UV Editor. Tools > Grab makes the kit's Grab brush the tool and a drag
moves the UV under the brush centre 80 % of the way (outside the brush nothing moves); Tools > Pinch (size 0.2) and a stroke
pull the UVs on both sides toward it; RMB shows Last Tool: Grab (screenshot)."""
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


@step
def s_grab():
    w, a, r = uv_window()
    check(f"UV Editor open ({a is not None})", a is not None)
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
    menu_item("UV Editor/Tools/Grab")
    check(f"Tools > Grab makes the kit's Grab brush the tool ({tool_id()})", tool_id() == "allset.uv_brush_grab")
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.5, 0.5))


@step
def s_grab_drag():
    C["before"] = uv_state()
    drag([uv_px(0.5, 0.5), uv_px(0.55, 0.5), uv_px(0.6, 0.5)])


@step
def s_grab_shot():
    shot("issue517_grab.png")
    release()


@step
def s_grab_checked():
    st = uv_state()
    k = near(C["before"], 0.5, 0.5)
    du = st[k[0]][0][0] - 0.5 if k else 0
    far = near(C["before"], 0.875, 0.5)
    check(f"Grab: the UV under the brush centre follows 80 % of a 0.1 drag ({du:.4f})", abs(du - 0.08) < 0.004)
    check("Grab: a UV outside the brush stays", far and st[far[0]][0] == C["before"][far[0]][0])
    menu_item("UV Editor/Tools/Pinch")
    check(f"Tools > Pinch makes the kit's Pinch brush the tool ({tool_id()})", tool_id() == "allset.uv_brush_pinch")
    bpy.context.scene.allset_uv_brush.pinch_size = 0.2
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.25, 0.25))


@step
def s_pinch_drag():
    C["before"] = uv_state()
    drag([uv_px(0.25, 0.25 + 0.01 * k) for k in range(0, 26)])


@step
def s_pinch_release():
    release()


@step
def s_pinch_checked():
    st = uv_state()
    left = near(C["before"], 0.125, 0.375)
    right = near(C["before"], 0.375, 0.375)
    ok = left and right and st[left[0]][0][0] > C["before"][left[0]][0][0] and         st[right[0]][0][0] < C["before"][right[0]][0][0]
    check("Pinch: the UVs on both sides of the stroke move toward it", ok)
    x, y = uv_px(0.5, 0.5)
    uv_ev('MOUSEMOVE', 'NOTHING', x, y)
    uv_ev('RIGHTMOUSE', 'PRESS', x, y)


@step
def s_rmb_open():
    s = mod(".marking.draw").ACTIVE.get("session")
    sub = s.stack[0][0].sub if s is not None else None
    label = sub.radial.get("E", ("",))[0] if sub is not None else None
    check(f"the brush marking menu's Last Tool names Grab ({label})", label == "Last Tool: Grab")
    uv_ev('ESC', 'PRESS')
    uv_ev('ESC', 'RELEASE')
    uv_ev('RIGHTMOUSE', 'RELEASE')


run()
