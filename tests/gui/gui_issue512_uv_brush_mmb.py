"""In a real UI (#512, #518, #516): an 8 x 8 grid in the UV Editor. Pin tool: an MMB drag right grows the brush size
by the drag in UV units, an MMB drag down lowers the strength, nothing gets pinned; Unfold: an MMB drag up changes
nothing; RMB names the Last Tool; Smudge with Middle mouse initiates: a left drag does nothing, a middle drag smudges
the selected UVs, and with the option off a middle drag smudges nothing (screenshots)."""
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



def mmb(points):
    uv_ev('MOUSEMOVE', 'NOTHING', *points[0])
    uv_ev('MIDDLEMOUSE', 'PRESS', *points[0])
    for p in points[1:]:
        uv_ev('MOUSEMOVE', 'NOTHING', *p)


def mmb_release():
    uv_ev('MIDDLEMOUSE', 'RELEASE')
    redraw_all()


def du(px):
    """UV units of ``px`` pixels in the UV Editor."""
    _w, _a, r = uv_window()
    return r.view2d.region_to_view(px, 0)[0] - r.view2d.region_to_view(0, 0)[0]


@step
def s_tools():
    w, a, r = uv_window()
    check(f"UV Editor open ({a is not None})", a is not None)
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
    menu_item("UV Editor/Tools/Unfold")
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.5, 0.5))
    menu_item("UV Editor/Tools/Pin")
    s = bpy.context.scene.allset_uv_brush
    s.pin_size, s.pin_strength = 0.1, 100.0
    uv_ev('MOUSEMOVE', 'NOTHING', *uv_px(0.5, 0.5))
    C["state"] = uv_state()


@step
def s_mmb_right():
    x, y = uv_px(0.5, 0.5)
    mmb([(x, y)] + [(x + 20 * k, y + 2 * k) for k in range(1, 6)])


@step
def s_mmb_right_shot():
    shot("issue512_mmb_size.png")
    mmb_release()


@step
def s_mmb_right_checked():
    s = bpy.context.scene.allset_uv_brush
    want = 0.1 + du(100)
    check(f"Pin: MMB drag 100 px right grows the size by 100 px in UV units ({s.pin_size:.4f}, {want:.4f})",
          abs(s.pin_size - want) < 2e-3)
    check(f"... the strength stays ({s.pin_strength})", s.pin_strength == 100.0)
    check("... no UV pinned or moved", uv_state() == C["state"])


@step
def s_mmb_down():
    x, y = uv_px(0.5, 0.5)
    mmb([(x, y)] + [(x + 1, y - 20 * k) for k in range(1, 6)])


@step
def s_mmb_down_checked():
    mmb_release()
    s = bpy.context.scene.allset_uv_brush
    want = 100.0 - du(100) * 100
    check(f"Pin: MMB drag 100 px down lowers the strength ({s.pin_strength:.2f}, {want:.2f})",
          abs(s.pin_strength - want) < 0.3)


@step
def s_unfold_up():
    menu_item("UV Editor/Tools/Unfold")
    s = bpy.context.scene.allset_uv_brush
    C["relax"] = (s.relax_size, s.relax_strength)
    x, y = uv_px(0.5, 0.5)
    mmb([(x, y)] + [(x, y + 20 * k) for k in range(1, 6)])


@step
def s_unfold_up_checked():
    mmb_release()
    s = bpy.context.scene.allset_uv_brush
    check(f"Unfold: MMB drag up changes nothing ({C['relax']} -> {(s.relax_size, s.relax_strength)})",
          (s.relax_size, s.relax_strength) == C["relax"])


@step
def s_rmb_label():
    x, y = uv_px(0.5, 0.5)
    uv_ev('MOUSEMOVE', 'NOTHING', x, y)
    uv_ev('RIGHTMOUSE', 'PRESS', x, y)


@step
def s_rmb_label_open():
    s = mod(".marking.draw").ACTIVE.get("session")
    sub = s.stack[0][0].sub if s is not None else None
    label = sub.radial.get("E", ("",))[0] if sub is not None else None
    check(f"#516: the brush marking menu names the last tool ({label})", label == "Last Tool: Pin")
    shot("issue516_last_tool.png")
    uv_ev('ESC', 'PRESS')
    uv_ev('ESC', 'RELEASE')
    uv_ev('RIGHTMOUSE', 'RELEASE')


def _select_middle():
    bm = bmesh.from_edit_mesh(grid().data)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        for l in f.loops:
            c = l[uv].uv
            on = abs(c.x - 0.5) < 0.2 and abs(c.y - 0.5) < 0.2
            l.uv_select_vert = on
            l.uv_select_edge = on
    bmesh.update_edit_mesh(grid().data)


@step
def s_smudge_left_with_middle():
    w, a, r = uv_window()
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.context.scene.tool_settings.use_uv_select_sync = False
        bpy.ops.allset.uv_component(mode='UV')
    menu_item("UV Editor/Tools/Smudge")
    _select_middle()
    s = bpy.context.scene.allset_uv_brush
    s.smudge_middle = True
    C["state"] = uv_state()
    drag([uv_px(0.5, 0.5), uv_px(0.53, 0.5), uv_px(0.56, 0.5)])


@step
def s_smudge_left_checked():
    release()
    check("#518 Middle mouse initiates on: a left drag smudges nothing", uv_state() == C["state"])
    mmb([uv_px(0.5, 0.5), uv_px(0.53, 0.5), uv_px(0.56, 0.5)])


@step
def s_smudge_middle_checked():
    mmb_release()
    moved = [k for k, (uv, _p) in uv_state().items() if abs(uv[0] - C["state"][k][0][0]) > 1e-4]
    check(f"#518 ... a middle drag smudges the selected UVs ({len(moved)} moved)", len(moved) > 0)
    bpy.context.scene.allset_uv_brush.smudge_middle = False
    C["state"] = uv_state()
    mmb([uv_px(0.5, 0.5), uv_px(0.53, 0.5), uv_px(0.56, 0.5)])


@step
def s_smudge_off_checked():
    mmb_release()
    check("#518 option off: a middle drag smudges nothing", uv_state() == C["state"])


run()
