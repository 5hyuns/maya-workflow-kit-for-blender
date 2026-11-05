"""Graph Editor tangent handles like Maya (#296) in a real UI (Maya Workflow Kit layout, the big view switched to the
Graph Editor): the kit draws the handles (Blender's are off), a non-weighted handle sits at a fixed length on screen;
a click selects it, a left drag only turns it (its time length stays), Esc puts it back, one undo takes a drag back;
a weighted handle follows the mouse; a middle drag moves a selected handle; a marquee picks a handle end; a click on a
key still selects the key; View > Tangents > Never hides the handles; Maya mode off gives Show Handles back."""

import math
import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, screenshot, view3d, win, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 300
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
FRAMES = ((1, 0.0), (13, 0.05), (25, 0.0))


def mod(name):
    return import_module(MODULE + name)


def region():
    return next(r for r in C["area"].regions if r.type == 'WINDOW')


def space():
    return C["area"].spaces.active


def curve():
    return mod(".compat").id_fcurve_collection(bpy.data.objects["pCube1"]).find("location", index=0)


def handles():
    with bpy.context.temp_override(window=win(), area=C["area"], region=region()):
        return mod(".ui.graph_handles").current(bpy.context)


def end_px(key, side):
    h = handles()
    r = next(i for i in range(len(h)) if h.fcurves[int(h.curves[i])] == curve() and h.keys[i] == key
             and h.sides[i] == side)
    return tuple(float(v) for v in h.end_px[r]), tuple(float(v) for v in h.key_px[r])


def win_xy(rx, ry):
    r = region()
    return int(round(r.x + rx)), int(round(r.y + ry))


def move_to(rx, ry):
    x, y = win_xy(rx, ry)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


def arm(side, i=1):
    kp = curve().keyframe_points[i]
    h = kp.handle_left if side == 0 else kp.handle_right
    return h[0] - kp.co[0], h[1] - kp.co[1]


def pick_handle(side=1):
    deselect()
    kp = curve().keyframe_points[1]
    if side == 0:
        kp.select_left_handle = True
    else:
        kp.select_right_handle = True


def deselect():
    for fc in mod(".compat").id_fcurves(bpy.data.objects["pCube1"]):
        fc.select = fc == curve()
        for kp in fc.keyframe_points:
            kp.select_control_point = kp.select_left_handle = kp.select_right_handle = False


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, reg = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=reg):
        bpy.ops.allset.create(kind='CUBE')
    ob = bpy.data.objects["pCube1"]
    scene = bpy.context.scene
    for f, v in FRAMES:
        scene.frame_set(f)
        ob.location.x = v
        with bpy.context.temp_override(window=win(), area=area, region=reg):
            bpy.ops.allset.set_key()
    scene.frame_set(1)
    p = mod(".preferences").get()
    p.snap_time_to_selection = False
    p.graph_auto_frame = False
    p.graph_auto_frame_time = False
    bpy.context.window_manager.allset_graph_key_tool = 'MOVE'
    C["area"] = area
    area.ui_type = 'FCURVES'
    space().show_handles = True


@step
def s_frame():
    a = C["area"]
    a.spaces.active.use_normalization = False
    fc = curve()
    kp = fc.keyframe_points[1]                  # the middle key: an aligned tangent at a slope
    kp.handle_left_type = kp.handle_right_type = 'ALIGNED'
    kp.handle_left = (kp.co[0] - 4.0, kp.co[1] - 0.02)
    kp.handle_right = (kp.co[0] + 4.0, kp.co[1] + 0.02)
    fc.update()
    weights = mod(".operators.graph_weights")
    weights.set_weighted(fc, False)
    weights.third_arms(fc)
    deselect()
    fc.keyframe_points[1].select_control_point = True     # On Active Keys: its tangents show
    with bpy.context.temp_override(window=win(), area=a, region=region()):
        bpy.ops.graph.view_all()
    move_to(region().width // 2, 20)


for _ in range(3):
    step(lambda: None)


@step
def s_takeover():
    gh = mod(".ui.graph_handles")
    check("the kit draws this Graph Editor's handles (Blender's are off)", gh.owns(space()) and not space().show_handles)
    check("the kit's Show Handles value is the editor's own (on)", gh.shows_handles(space()))
    check("tangents on active keys (Maya View > Tangents)", space().use_only_selected_keyframe_handles)
    (ex, ey), (kx, ky) = end_px(1, 1)
    length = math.hypot(ex - kx, ey - ky)
    ui = bpy.context.preferences.system.ui_scale or 1.0
    check(f"non-weighted handle drawn {length:.1f} px from its key (fixed {gh.FIXED_PX * ui:.0f})",
          abs(length - gh.FIXED_PX * ui) < 0.5)
    real = region().view2d.view_to_region(*curve().keyframe_points[1].handle_right, clip=False)
    check(f"... not at the real handle ({math.hypot(real[0] - kx, real[1] - ky):.0f} px away)",
          abs(math.hypot(real[0] - kx, real[1] - ky) - length) > 5)
    C["arm0"] = arm(1)
    C["third"] = mod(".operators.graph_weights").third(curve(), 1, 1)
    move_to(ex, ey)


@step
def s_click():
    ev('LEFTMOUSE', 'PRESS')
    ev('LEFTMOUSE', 'RELEASE')


step(lambda: None)


@step
def s_click_check():
    kps = curve().keyframe_points
    check("a click on the handle end selects that handle", kps[1].select_right_handle)
    check("... not its key, nor any other key",
          not any(kp.select_control_point for kp in kps) and not kps[1].select_left_handle)
    check("handles unchanged by a click", arm(1) == C["arm0"])
    if SHOTS:
        screenshot(os.path.join(SHOTS, "issue296_selected.png"))


def drag(button, dx, dy, n=6, cancel=False):
    def press():
        ev(button, 'PRESS')
    step(press)
    for i in range(1, n + 1):
        def mv(i=i):
            x, y = C["press"]
            move_to(x + dx * i / n, y + dy * i / n)
        step(mv)
    if cancel:
        step(lambda: ev('ESC', 'PRESS'))
        step(lambda: ev('ESC', 'RELEASE'))
        step(lambda: ev(button, 'RELEASE'))
    else:
        step(lambda: ev(button, 'RELEASE'))
    step(lambda: None)


def at_end(key=1, side=1, push=None):
    def go():
        (ex, ey), _k = end_px(key, side)
        C["press"] = (ex, ey)
        C["before"] = (arm(0), arm(1))
        if push:
            bpy.ops.ed.undo_push(message=push)
        move_to(ex, ey)
    step(go)


# a left drag up: a non-weighted tangent only turns
at_end(push="before turn")
drag('LEFTMOUSE', 0, 40)


@step
def s_turn_check():
    ax, ay = arm(1)
    lx, ly = arm(0)
    third = C["third"]
    check(f"drag keeps the time length a third of the way ({ax:.4f} ~ {third:.4f})", abs(ax - third) < 1e-4)
    check(f"... and turns the tangent up ({C['before'][1][1]:.5f} -> {ay:.5f})", ay > C["before"][1][1] + 1e-4)
    check(f"... the aligned left side turns along ({lx:.4f}, {ly:.5f})",
          abs(lx + third) < 1e-4 and abs(ly / lx - ay / ax) < 1e-3)
    (ex, ey), (kx, ky) = end_px(1, 1)
    gh = mod(".ui.graph_handles")
    ui = bpy.context.preferences.system.ui_scale or 1.0
    check("... still drawn at the fixed length", abs(math.hypot(ex - kx, ey - ky) - gh.FIXED_PX * ui) < 0.5)
    want = math.atan2(C["press"][1] + 40 - ky, C["press"][0] - kx)
    check(f"... pointing at the mouse ({math.degrees(math.atan2(ey - ky, ex - kx)):.1f} ~ {math.degrees(want):.1f} deg)",
          abs(math.atan2(ey - ky, ex - kx) - want) < math.radians(1.5))
    if SHOTS:
        screenshot(os.path.join(SHOTS, "issue296_turned.png"))
    C["turned"] = (arm(0), arm(1))


@step
def s_undo():
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


step(lambda: None)


@step
def s_undo_check():
    got = (arm(0), arm(1))
    check(f"one undo takes the drag back ({got[1]} ~ {C['before'][1]})",
          all(abs(a - b) < 1e-5 for p, q in zip(got, C["before"]) for a, b in zip(p, q)))


# Esc during a drag puts the tangent back
at_end()
drag('LEFTMOUSE', 0, -40, cancel=True)


@step
def s_cancel_check():
    got = (arm(0), arm(1))
    check("Esc puts the tangent back",
          all(abs(a - b) < 1e-6 for p, q in zip(got, C["before"]) for a, b in zip(p, q)))


# middle drag with a selected handle and no selected key (Move Keys tool)
@step
def s_mmb_prep():
    pick_handle()
    C["before"] = (arm(0), arm(1))
    C["press"] = (region().width * 0.3, region().height * 0.3)
    move_to(*C["press"])


drag('MIDDLEMOUSE', 0, -30)


@step
def s_mmb_check():
    ax, ay = arm(1)
    check(f"middle drag turns the selected handle down ({C['before'][1][1]:.5f} -> {ay:.5f})",
          ay < C["before"][1][1] - 1e-4 and abs(ax - C["third"]) < 1e-4)


# weighted: the handle end follows the mouse
@step
def s_weighted():
    with bpy.context.temp_override(window=win(), area=C["area"], region=region()):
        fc = curve()
        mod(".operators.graph_weights").set_weighted(fc, True)
    pick_handle()


at_end()
drag('LEFTMOUSE', 30, 20)


@step
def s_weighted_check():
    kp = curve().keyframe_points[1]
    got = region().view2d.view_to_region(*kp.handle_right, clip=False)
    want = (C["press"][0] + 30, C["press"][1] + 20)
    check(f"weighted handle end follows the mouse ({got[0]:.1f}, {got[1]:.1f}) ~ {want}",
          abs(got[0] - want[0]) < 1.5 and abs(got[1] - want[1]) < 1.5)


# a marquee from empty space around a handle end picks it
@step
def s_box_prep():
    mod(".operators.graph_weights").set_weighted(curve(), False)
    pick_handle()
    (ex, ey), (kx, ky) = end_px(1, 0)
    C["box"] = (ex, ey)
    C["press"] = (ex - 25, ey + 25 if ey < ky else ey - 25)     # away from the curve
    move_to(*C["press"])


@step
def s_box_press():
    ev('LEFTMOUSE', 'PRESS')


for k in range(1, 7):
    def box_move(k=k):
        x0, y0 = C["press"]
        x1, y1 = C["box"][0] + 10, C["box"][1] + (10 if C["box"][1] > y0 else -10)
        move_to(x0 + (x1 - x0) * k / 6, y0 + (y1 - y0) * k / 6)
    step(box_move)
step(lambda: ev('LEFTMOUSE', 'RELEASE'))
for _ in range(3):
    step(lambda: None)


@step
def s_box_check():
    kps = curve().keyframe_points
    check("a marquee around a handle end selects that handle", kps[1].select_left_handle)
    check("... and no key", not any(kp.select_control_point for kp in kps))
    check("... the handle outside it is deselected", not kps[1].select_right_handle)
    if SHOTS:
        screenshot(os.path.join(SHOTS, "issue296_box.png"))


# a click on a key still selects the key (Blender's click)
@step
def s_key_click():
    _e, (kx, ky) = end_px(1, 1)
    deselect()
    move_to(kx, ky)
    ev('LEFTMOUSE', 'PRESS')
    ev('LEFTMOUSE', 'RELEASE')


step(lambda: None)


@step
def s_key_check():
    check("a click on the key selects the key", curve().keyframe_points[1].select_control_point)


@step
def s_never():
    with bpy.context.temp_override(window=win(), area=C["area"], region=region()):
        bpy.context.window_manager.allset_graph_tangents = 'NEVER'
        n = len(mod(".ui.graph_handles").current(bpy.context))
        check(f"View > Tangents > Never hides the handles ({n})", n == 0)
        bpy.context.window_manager.allset_graph_tangents = 'ALWAYS'
        n = len(mod(".ui.graph_handles").current(bpy.context))
        check(f"... Always shows them again ({n})", n > 0)


@step
def s_maya_off():
    mod(".switch").set_mode(False, layout=False)
    check("Maya mode off: the Graph Editor shows its own handles again", space().show_handles)


run()
