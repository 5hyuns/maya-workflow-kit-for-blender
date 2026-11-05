"""Graph Editor Sculpting Tools with real mouse drags: Grab moves the keys under the brush by the drag with a smooth
falloff and one undo takes the stroke back; Smear spreads a diagonal drag along its path; Smooth pulls a spike toward
its neighbours; Key Reducer deletes keys on a straight line; only selected keys change when some are selected."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d, win, load_maya_layout, screenshot  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
BASE = "Graph Editor/Edit/Transformation Tools/Sculpting Tools/"


def gs():
    return import_module(MODULE + ".operators.graph_sculpt")


def region():
    return next(r for r in C["area"].regions if r.type == 'WINDOW')


def curve(index=0):
    col = import_module(MODULE + ".compat").id_fcurve_collection(bpy.data.objects["pCube1"])
    return col.find("location", index=index)


def vals(index=0):
    return {round(kp.co.x): round(kp.co.y, 4) for kp in curve(index).keyframe_points}


def at(t, v):
    r = region()
    x, y = r.view2d.view_to_region(t, v, clip=False)
    return r.x + x, r.y + y


def menu(item):
    with bpy.context.temp_override(window=win(), area=C["area"], region=region()):
        return bpy.ops.allset.menu_item(item=BASE + item)


def drag(a, b, n=8):
    ev('MOUSEMOVE', 'NOTHING', x=int(a[0]), y=int(a[1]))
    ev('LEFTMOUSE', 'PRESS', x=int(a[0]), y=int(a[1]))
    for i in range(1, n + 1):
        ev('MOUSEMOVE', 'NOTHING', x=int(a[0] + (b[0] - a[0]) * i / n), y=int(a[1] + (b[1] - a[1]) * i / n))
    ev('LEFTMOUSE', 'RELEASE', x=int(b[0]), y=int(b[1]))


def tool_running():
    return any(op.bl_idname == "ALLSET_OT_graph_sculpt" for op in win().modal_operators)


def reset(spike=False):
    for idx, fn in ((0, lambda f: -4.0 if (spike and f == 20) else 0.0), (1, lambda f: -15.0 + f * 0.25)):
        fc = curve(idx)
        for kp in list(fc.keyframe_points):
            pass
        while len(fc.keyframe_points):
            fc.keyframe_points.remove(fc.keyframe_points[0])
        for f in range(0, 41):
            kp = fc.keyframe_points.insert(f, fn(f))
            kp.select_control_point = False
        fc.update()
    bpy.ops.ed.undo_push(message="reset")


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    area, reg = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=reg):
        bpy.ops.allset.create(kind='CUBE')
    ob = bpy.data.objects["pCube1"]
    for f in (0, 40):
        ob.location = (0.0, -15.0 + f * 0.25, 0.0)
        ob.keyframe_insert("location", index=0, frame=f)
        ob.keyframe_insert("location", index=1, frame=f)
    C["area"] = area
    area.ui_type = 'FCURVES'
    reset()


@step
def s_view():
    sp = C["area"].spaces.active
    sp.use_normalization = False
    sp.show_region_ui = False
    r = region()
    r.view2d.view_to_region(0, 0)
    with bpy.context.temp_override(window=win(), area=C["area"], region=r):
        bpy.ops.graph.view_all()


@step
def s_view2():
    r = region()
    x0, _ = r.view2d.view_to_region(0, 0, clip=False)
    x1, _ = r.view2d.view_to_region(1, 0, clip=False)
    C["ppf"] = x1 - x0
    check(f"a frame is wide enough on screen ({C['ppf']:.1f} px)", C["ppf"] > 8)
    check(f"Grab Tool from the menu ({menu('Grab Tool')})", tool_running())


@step
def s_grab():
    a = at(20, 0.0)
    drag(a, (a[0], a[1] - 40))


@step
def s_grab_check():
    v = vals()
    r = region()
    dv = r.view2d.region_to_view(0, 100 - 40)[1] - r.view2d.region_to_view(0, 100)[1]
    rad = bpy.context.window_manager.allset_sculpt_keys_radius
    w1 = gs().falloff(C["ppf"] / rad)
    check(f"Grab: the key under the brush follows the drag ({v[20]} vs {dv:.4f})", abs(v[20] - dv) < 0.02 * abs(dv))
    check(f"Grab: its neighbours move by the falloff ({v[19]} {v[21]} vs {dv * w1:.4f})",
          abs(v[19] - dv * w1) < 0.03 * abs(dv) and abs(v[21] - dv * w1) < 0.03 * abs(dv))
    far = [f for f in v if abs(f - 20) * C["ppf"] > rad + 2 and v[f] != 0.0]
    check(f"Grab: keys outside the brush stay ({far})", not far)
    check(f"Grab: times stay ({sorted(v) == list(range(41))})", sorted(v) == list(range(41)))
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_graph_sculpt_grab.png"))
    bpy.ops.ed.undo()


@step
def s_grab_undo():
    check(f"one undo takes the stroke back ({[vals()[f] for f in (19, 20, 21)]})",
          all(v == 0.0 for v in vals().values()))
    for kp in curve(0).keyframe_points:
        kp.select_control_point = kp.co.x >= 20
    a = at(20, 0.0)
    drag(a, (a[0], a[1] - 40))


@step
def s_selected_only():
    v = vals()
    check(f"with keys selected only they change ({v[19]}, {v[20]}, {v[21]})", v[19] == 0.0 and v[20] != 0 and v[21] != 0)
    bpy.ops.ed.undo()
    for kp in curve(0).keyframe_points:
        kp.select_control_point = False
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')


@step
def s_smear():
    check(f"Esc ends the tool ({tool_running()})", not tool_running())
    menu("Smear Tool")
    a, b = at(16, 0.0), at(24, 0.0)
    drag(a, (b[0], b[1] - 40), n=16)


@step
def s_smear_check():
    v = vals()
    moved = [f for f in v if abs(v[f]) > 1e-3]
    check(f"Smear: a diagonal drag spreads along its path ({moved})", min(moved) <= 15 and max(moved) >= 24)
    reset(spike=True)
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')


@step
def s_smooth():
    menu("Smooth Tool")
    a = at(20, -4.0)
    drag(a, (a[0] + 1, a[1]), n=1)


@step
def s_smooth_check():
    v = vals()
    check(f"Smooth: the spike comes toward its neighbours ({v[20]})", -2.6 < v[20] < -1.4 and v[19] == 0.0)
    check(f"Smooth: the keys stay at their frames ({sorted(v) == list(range(41))})", sorted(v) == list(range(41)))
    reset()
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')


@step
def s_reduce():
    menu("Key Reducer Tool")
    a, b = at(14, -11.5), at(26, -8.5)
    C["n1"] = len(curve(1).keyframe_points)
    drag(a, b, n=24)


@step
def s_reduce_check():
    times = [round(kp.co.x) for kp in curve(1).keyframe_points]
    check(f"Key Reducer: keys on the straight line are gone ({len(times)} of {C['n1']})", len(times) < C["n1"] - 5)
    check(f"Key Reducer: first and last keys stay ({times[0]}, {times[-1]})", times[0] == 0 and times[-1] == 40)
    check(f"Key Reducer: the flat curve far away is untouched ({len(curve(0).keyframe_points)})",
          len(curve(0).keyframe_points) == 41)
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')


run()
