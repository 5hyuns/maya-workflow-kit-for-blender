"""Issue #208 in a real UI (Maya Workflow Kit layout): snapping in the EP Curve Tool. curve1 = an EP curve on the
ground; EP Curve Tool again: hold C + click beside curve1 -> the point is on curve1, C + drag slides along it; hold V +
click near curve1's end -> the point = its end CV; a plain click stays free on the ground; middle-drag moves the last
point (with C: onto curve1); Ctrl+click inverts Blender's scene snapping (Vertex); Enter -> curve2 starts on curve1."""

import os
import sys
from importlib import import_module

import bpy
import numpy as np
from bpy_extras import view3d_utils
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, tap, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + ".operators." + name)


def main_view():
    toolbox = import_module(MODULE + ".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def running():
    return "ALLSET_OT_ep_curve_tool" in [op.bl_idname for op in win().modal_operators]


def to_window(p):
    """Window pixel of world point ``p`` in the main view."""
    _area, region = main_view()
    xy = view3d_utils.location_3d_to_region_2d(region, region.data, Vector(p))
    return int(round(region.x + xy.x)), int(round(region.y + xy.y))


def curve_samples(n=4000):
    cm = mod("curves_math")
    cvs, knots, degree, weights = C["curve"]
    return np.asarray([cm.evaluate(cvs, knots, degree, knots[0] + (knots[-1] - knots[0]) * i / (n - 1), weights)
                       for i in range(n)])


def dist_to_curve(p):
    s = C["samples"]
    a, b = s[:-1], s[1:]
    d = b - a
    t = np.clip(((np.asarray(p) - a) * d).sum(1) / np.maximum((d * d).sum(1), 1e-30), 0, 1)
    q = a + d * t[:, None]
    return float(np.min(np.linalg.norm(q - np.asarray(p), axis=1)))


def pts():
    return mod("curve_draw").STATE["points"]


def u():
    return mod("units").maya_unit(bpy.context.scene)


def world(x, y):
    return Vector((x * u(), y * u(), 0.0))


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_curve1():
    ctx = bpy.context
    with ctx.temp_override(window=win()):
        ob = mod("curves_maya").make_ep_curve(ctx, [world(-6, -2), world(-2, 3), world(2, -1), world(6, 2)], 3)
    mod("naming").apply_maya_name(ob, "curve")
    C["ob"] = ob
    mc = mod("curves_maya").read_spline(ob.data.splines[0], ob.matrix_world)
    C["curve"] = mc.math()
    C["samples"] = curve_samples()
    C["end_cv"] = Vector(mc.cvs[-1])
    check(f"curve1 made ({ob.name})", ob.name == "curve1")
    ts = ctx.scene.tool_settings
    ts.use_snap = False
    ts.snap_elements = {'VERTEX'}
    for o in list(ctx.view_layer.objects):
        o.select_set(False)
    area, region = main_view()
    _area, region = main_view()
    cm = mod("curves_math")
    cvs, knots, degree, weights = C["curve"]
    C["on_a"] = Vector(cm.evaluate(cvs, knots, degree, 0.7, weights))
    C["on_b"] = Vector(cm.evaluate(cvs, knots, degree, 1.6, weights))
    for name in ("on_a", "on_b"):
        x, y = to_window(C[name])
        check(f"{name} is in the main view ({x}, {y})", region.x < x < region.x + region.width
              and region.y < y < region.y + region.height)
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 2)
    with ctx.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.ep_curve_tool('INVOKE_DEFAULT')
    check("EP Curve Tool runs", running())


# --- C hold + click beside the curve: the point is on curve1 -------------------------------------

@step
def s_c_hold():
    x, y = to_window(C["on_a"])
    C["xy"] = (x + 4, y - 3)
    ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])


@step
def s_c_press_key():
    ev('C', 'PRESS', x=C["xy"][0], y=C["xy"][1])


@step
def s_c_click():
    ev('LEFTMOUSE', 'PRESS', x=C["xy"][0], y=C["xy"][1])


@step
def s_c_on_curve():
    p = pts()[-1] if pts() else None
    d = dist_to_curve(p) if p is not None else 1e9
    check(f"C + click: the new point is on curve1 (distance {d / u():.2e} units)", d < 2e-3 * u())
    check(f"C + click: the point is near the cursor's curve point ({(p - C['on_a']).length / u():.3f} units)",
          p is not None and (p - C["on_a"]).length < 0.5 * u())
    xb, yb = to_window(C["on_b"])
    xa, ya = C["xy"]
    C["path"] = [(int(xa + (xb + 3 - xa) * k / 6), int(ya + (yb + 2 - ya) * k / 6)) for k in range(1, 7)]


def _drag_move():
    x, y = C["path"].pop(0)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    C["xy"] = (x, y)


for _ in range(6):          # one move per tick (snap holds)
    step(_drag_move)


@step
def s_c_drag_release():
    ev('LEFTMOUSE', 'RELEASE', x=C["xy"][0], y=C["xy"][1])


@step
def s_c_slid():
    p = pts()[-1]
    d = dist_to_curve(p)
    check(f"C + drag: the point slid along curve1 (distance {d / u():.2e}, to on_b {(p - C['on_b']).length / u():.3f})",
          d < 2e-3 * u() and (p - C["on_b"]).length < 0.5 * u())
    check(f"one point placed ({len(pts())})", len(pts()) == 1)
    ev('C', 'RELEASE', x=C["xy"][0], y=C["xy"][1])


# --- V hold + click near the end: the point = curve1's end CV --------------------------------------

@step
def s_v_move():
    x, y = to_window(C["end_cv"])
    C["xy"] = (x - 7, y + 6)            # V: the nearest point on screen
    ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])


@step
def s_v_key():
    ev('V', 'PRESS', x=C["xy"][0], y=C["xy"][1])


@step
def s_v_press():
    ev('LEFTMOUSE', 'PRESS', x=C["xy"][0], y=C["xy"][1])


@step
def s_v_release():
    ev('LEFTMOUSE', 'RELEASE', x=C["xy"][0], y=C["xy"][1])


@step
def s_v_check():
    p = pts()[-1]
    check(f"V + click: the point = curve1's end CV ({(p - C['end_cv']).length / u():.2e} units)",
          len(pts()) == 2 and (p - C["end_cv"]).length < 1e-4 * u())
    ev('V', 'RELEASE', x=C["xy"][0], y=C["xy"][1])


# --- a plain click: free on the ground --------------------------------------------------------------

@step
def s_free_move():
    C["free"] = world(0, 7)
    C["xy"] = to_window(C["free"])
    ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])


@step
def s_free_press():
    ev('LEFTMOUSE', 'PRESS', x=C["xy"][0], y=C["xy"][1])


@step
def s_free_release():
    ev('LEFTMOUSE', 'RELEASE', x=C["xy"][0], y=C["xy"][1])


@step
def s_free_check():
    p = pts()[-1]
    check(f"plain click: the point is free on the ground (z {p.z:.2e}, off {(p - C['free']).length / u():.3f})",
          len(pts()) == 3 and abs(p.z) < 1e-6 and (p - C["free"]).length < 0.1 * u())


# --- MMB drag moves the last point; with C it lands on curve1 ---------------------------------------

@step
def s_mmb_press():
    ev('MIDDLEMOUSE', 'PRESS', x=C["xy"][0], y=C["xy"][1])


@step
def s_mmb_move():
    C["mmb_to"] = world(3, 6)
    C["xy"] = to_window(C["mmb_to"])
    ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])


@step
def s_mmb_release():
    ev('MIDDLEMOUSE', 'RELEASE', x=C["xy"][0], y=C["xy"][1])


@step
def s_mmb_check():
    p = pts()[-1]
    check(f"middle-drag moves the last point ({(p - C['mmb_to']).length / u():.3f} units off, {len(pts())} points)",
          len(pts()) == 3 and (p - C["mmb_to"]).length < 0.1 * u())
    x, y = to_window(C["on_b"])
    C["xy"] = (x - 3, y + 4)
    ev('C', 'PRESS', x=C["xy"][0], y=C["xy"][1])


@step
def s_mmb_c_press():
    ev('MIDDLEMOUSE', 'PRESS', x=C["xy"][0], y=C["xy"][1])


@step
def s_mmb_c_release():
    ev('MIDDLEMOUSE', 'RELEASE', x=C["xy"][0], y=C["xy"][1])


@step
def s_mmb_c_check():
    p = pts()[-1]
    d = dist_to_curve(p)
    check(f"C + middle-drag: the last point moves onto curve1 (distance {d / u():.2e})",
          len(pts()) == 3 and d < 2e-3 * u())
    ev('C', 'RELEASE', x=C["xy"][0], y=C["xy"][1])


# --- Ctrl+click inverts Blender's scene snapping (Vertex, off) ----------------------------------------

@step
def s_ctrl_move():
    x, y = to_window(C["end_cv"])
    C["xy"] = (x + 8, y - 6)
    ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])


@step
def s_ctrl_key():
    ev('LEFT_CTRL', 'PRESS', ctrl=True)


@step
def s_ctrl_press():
    ev('LEFTMOUSE', 'PRESS', x=C["xy"][0], y=C["xy"][1], ctrl=True)


@step
def s_ctrl_release():
    ev('LEFTMOUSE', 'RELEASE', x=C["xy"][0], y=C["xy"][1], ctrl=True)


@step
def s_ctrl_check():
    ev('LEFT_CTRL', 'RELEASE')
    p = pts()[-1]
    check(f"Ctrl+click with Blender snapping off (Vertex): snaps to curve1's end CV "
          f"({(p - C['end_cv']).length / u():.2e}, {len(pts())} points)",
          len(pts()) == 4 and (p - C["end_cv"]).length < 1e-4 * u())
    bpy.context.scene.tool_settings.use_snap = True


@step
def s_snap_on_press():
    ev('LEFTMOUSE', 'PRESS', x=C["xy"][0], y=C["xy"][1])


@step
def s_snap_on_release():
    ev('LEFTMOUSE', 'RELEASE', x=C["xy"][0], y=C["xy"][1])


@step
def s_snap_on_check():
    p = pts()[-1]
    check(f"plain click with Blender snapping on (Vertex): snaps ({(p - C['end_cv']).length / u():.2e})",
          len(pts()) == 5 and (p - C["end_cv"]).length < 1e-4 * u())


@step
def s_ctrl2_key():
    ev('LEFT_CTRL', 'PRESS', ctrl=True)


@step
def s_ctrl2_press():
    ev('LEFTMOUSE', 'PRESS', x=C["xy"][0], y=C["xy"][1], ctrl=True)


@step
def s_ctrl2_release():
    ev('LEFTMOUSE', 'RELEASE', x=C["xy"][0], y=C["xy"][1], ctrl=True)


@step
def s_ctrl2_check():
    ev('LEFT_CTRL', 'RELEASE')
    p = pts()[-1]
    check(f"Ctrl+click with Blender snapping on: no snap, free on the ground "
          f"({(p - C['end_cv']).length / u():.3f} units from the CV, z {p.z:.1e})",
          len(pts()) == 6 and (p - C["end_cv"]).length > 0.05 * u() and abs(p.z) < 1e-6)
    bpy.context.scene.tool_settings.use_snap = False
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_shot():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue208_drawing.png"))
    tap('RET')


@step
def s_done():
    check("Enter ends the EP Curve Tool", not running())
    ob = bpy.data.objects.get("curve2")
    check(f"curve2 made ({sorted(o.name for o in bpy.data.objects if o.type == 'CURVE')})", ob is not None)
    last = mod("curve_draw").LAST["points"]
    check(f"curve2's first edit point is on curve1 ({dist_to_curve(last[0]) / u():.2e})",
          bool(last) and dist_to_curve(last[0]) < 2e-3 * u())
    if ob is not None:
        sp = ob.data.splines[0]
        first = ob.matrix_world @ (sp.points[0].co.xyz if sp.type != 'BEZIER' else sp.bezier_points[0].co)
        check(f"curve2 starts on curve1 ({dist_to_curve(first) / u():.2e})", dist_to_curve(first) < 2e-3 * u())


run()
