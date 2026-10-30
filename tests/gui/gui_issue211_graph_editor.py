"""Graph Editor controls (#211) in a real UI (Maya Workflow Kit layout, the big view switched to the Graph Editor):
a plain middle drag counts from the press, Shift+LMB drag on an already selected key moves it along one axis (a
Shift+click still toggles it off), r / e / w pick the Scale / Rotate / Move key tool for middle drags, Unconstrained
drag off locks a plain middle drag to its first axis, and l turns the value lines on."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, screenshot, view3d, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def region():
    return next(r for r in C["area"].regions if r.type == 'WINDOW')


def curve():
    return import_module(MODULE + ".compat").id_fcurve_collection(bpy.data.objects["pCube1"]).find("location", index=0)


def key10():
    return min(curve().keyframe_points, key=lambda kp: abs(kp.co.x - C.get("kx", 10.0)))


def win_xy(rx, ry):
    r = region()
    return int(r.x + rx), int(r.y + ry)


def px_per_frame():
    v2d = region().view2d
    return v2d.view_to_region(11, 0, clip=False)[0] - v2d.view_to_region(10, 0, clip=False)[0]


def prefs():
    return import_module(MODULE + ".preferences").get()


def reset_key(x=10.0, y=0.05, handles='AUTO_CLAMPED'):
    for kp in curve().keyframe_points:
        kp.select_control_point = kp.select_left_handle = kp.select_right_handle = False
    C["kx"] = 10.0
    kp = key10()
    kp.handle_left_type = kp.handle_right_type = handles
    kp.co = (x, y)
    kp.select_control_point = True
    curve().update()
    C["kx"] = x


def shift(value):
    ev('LEFT_SHIFT', value, shift=(value == 'PRESS'))


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
    for f, v in ((1, 0.0), (10, 0.05), (20, 0.0)):
        ob.location.x = v
        ob.keyframe_insert("location", index=0, frame=f)
    p = prefs()
    p.snap_time_to_selection = False
    p.graph_auto_frame = False
    p.graph_unconstrained_drag = True
    p.graph_value_lines = False
    bpy.context.window_manager.allset_graph_key_tool = 'MOVE'
    C["area"] = area
    area.ui_type = 'FCURVES'


@step
def s_frame():
    a = C["area"]
    a.spaces.active.use_normalization = False
    with bpy.context.temp_override(window=win(), area=a, region=region()):
        bpy.ops.graph.view_all()
    reset_key()
    r = region()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 3)


@step
def s_view_scale():
    r = region()
    C["ppf"] = ppf = px_per_frame()
    C["mid"] = (r.width // 2, r.height // 3)
    C["n2"] = int(round(2.3 * ppf))
    print("GUI ppf", ppf, "region", r.width, r.height, flush=True)
    check(f"Graph Editor view is wide enough for the drags ({ppf:.1f} px / frame)", ppf >= 8)


def _case(name, button, moves_fn, press_fn, expect_fn, mods=False, prep=None, snap=True):
    st = {}
    for _ in range(12):                 # no double-click with the previous case's press
        step(lambda: None)

    def before():
        bpy.context.scene.tool_settings.use_snap_anim = snap
        reset_key()
        if prep:
            prep()
        st["press"] = press_fn()
        st["moves"] = moves_fn()
        kp = key10()
        st["start"] = (tuple(kp.co), tuple(kp.handle_right))

    step(before)
    step(lambda: None)
    if mods:
        step(lambda: shift('PRESS'))

    def hover():
        x, y = win_xy(*st["press"])
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y, shift=mods)
    step(hover)

    def down():
        x, y = win_xy(*st["press"])
        ev(button, 'PRESS', x=x, y=y, shift=mods)
    step(down)
    for i in range(6):
        def mv(i=i):
            moves = st["moves"]
            if i < len(moves):
                p = st["press"]
                x, y = win_xy(p[0] + moves[i][0], p[1] + moves[i][1])
                ev('MOUSEMOVE', 'NOTHING', x=x, y=y, shift=mods)
        step(mv)
    step(lambda: ev(button, 'RELEASE', shift=mods))
    if mods:
        step(lambda: shift('RELEASE'))
    step(lambda: None)
    step(lambda: None)

    def verify():
        kp = key10()
        ok, text = expect_fn(st["start"], kp)
        check(f"{name}: {text} (key {st['start'][0][0]:.3f}, {st['start'][0][1]:.4f} -> "
              f"{kp.co.x:.3f}, {kp.co.y:.4f})", ok)
        if SHOTS:
            screenshot(os.path.join(SHOTS, f"issue211_{name}.png"))
    step(verify)


def _mid():
    return C["mid"]


def _key_px():
    kp = key10()
    return tuple(int(round(v)) for v in region().view2d.view_to_region(kp.co.x, kp.co.y, clip=False))


# 1. a plain middle drag counts from the press: one move of 2 frames' pixels moves the key by exactly that
def _two_frames():
    n = int(round(2 * C["ppf"]))
    v2d = region().view2d
    x, y = C["mid"]
    C["dt"] = v2d.region_to_view(x + n, y)[0] - v2d.region_to_view(x, y)[0]     # the whole move, in frames
    return [(n, 0)]


_case("mmb_from_press", 'MIDDLEMOUSE', _two_frames, _mid,
      lambda s, kp: (abs(kp.co.x - (s[0][0] + C["dt"])) < 1e-3 and abs(kp.co.y - s[0][1]) < 1e-6,
                     f"one move moves the key the whole distance from the press ({C.get('dt', 0):.3f} frames)"),
      snap=False)

# 2. Shift+LMB drag that starts on the selected key: time only, and the key stays selected
_case("shift_lmb_selected", 'LEFTMOUSE', lambda: [(6, 1), (6 + C["n2"], 1), (6 + C["n2"], -1)], _key_px,
      lambda s, kp: (kp.co.x == s[0][0] + 2 and abs(kp.co.y - s[0][1]) < 1e-6 and kp.select_control_point,
                     "time only +2, still selected"), mods=True)

# 3. a Shift+click on the selected key still toggles it off
_case("shift_click_toggles", 'LEFTMOUSE', lambda: [], _key_px,
      lambda s, kp: (not kp.select_control_point and tuple(kp.co) == s[0], "deselected, not moved"), mods=True)


# 4. r = Scale Keys tool: a middle drag 50 px right of a press at frame 2 scales time by 1.5 around frame 2
@step
def s_r():
    x, y = win_xy(*C["mid"])
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('R', 'PRESS')
    ev('R', 'RELEASE')


@step
def s_r_check():
    check("r over the Graph Editor picks the Scale Keys tool",
          bpy.context.window_manager.allset_graph_key_tool == 'SCALE')


def _at_frame2():
    x, _y = region().view2d.view_to_region(2.0, 0.0, clip=False)
    return (int(round(x)), C["mid"][1])


def _scale_moves():
    gm = import_module(MODULE + ".operators.graph_move")
    return [(int(gm.SCALE_PX // 2), 0)]


_case("scale_tool", 'MIDDLEMOUSE', _scale_moves, _at_frame2,
      lambda s, kp: (abs(kp.co.x - 14.0) < 1e-6 and abs(kp.co.y - s[0][1]) < 1e-3,
                     "time scaled 1.5 around frame 2: 10 -> 14"),
      prep=lambda: None)


# 5. e = turn the tangents
@step
def s_e():
    ev('E', 'PRESS')
    ev('E', 'RELEASE')


@step
def s_e_check():
    check("e over the Graph Editor picks the Rotate tool", bpy.context.window_manager.allset_graph_key_tool == 'ROTATE')


_case("rotate_tool", 'MIDDLEMOUSE', lambda: [(0, 40), (0, 80)], _mid,
      lambda s, kp: (tuple(kp.co) == s[0] and kp.handle_right_type == 'ALIGNED'
                     and kp.handle_right.y > s[1][1] + 1e-4, "key stays, its out tangent turned up"))


# 6. w = back to moving; Unconstrained drag off = the first move picks the axis
@step
def s_w():
    ev('W', 'PRESS')
    ev('W', 'RELEASE')
    prefs().graph_unconstrained_drag = False


@step
def s_w_check():
    check("w over the Graph Editor picks the Move Keys tool", bpy.context.window_manager.allset_graph_key_tool == 'MOVE')


_case("constrained_mmb", 'MIDDLEMOUSE', lambda: [(5, 1), (5 + C["n2"], 1), (5 + C["n2"], 40)], _mid,
      lambda s, kp: (kp.co.x == s[0][0] + 2 and abs(kp.co.y - s[0][1]) < 1e-6, "time only +2"))


@step
def s_unconstrained_back():
    prefs().graph_unconstrained_drag = True


# 7. l = value lines
@step
def s_l():
    x, y = win_xy(*C["mid"])
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('L', 'PRESS')
    ev('L', 'RELEASE')


@step
def s_l_check():
    gv = import_module(MODULE + ".ui.graph_view")
    a = C["area"]
    with bpy.context.temp_override(window=win(), area=a, region=region(), space_data=a.spaces.active):
        lines = gv.value_lines(bpy.context)
    # the selected key's curve runs from 0 to 0.05: zero line, lowest 0, highest 0.05
    check(f"l turns the value lines on: zero / lowest / highest ({[round(v, 3) for v, _c in lines]})",
          prefs().graph_value_lines and [round(v, 3) for v, _c in lines] == [0.0, 0.0, 0.05])
    if SHOTS:
        screenshot(os.path.join(SHOTS, "issue211_value_lines.png"))
    prefs().graph_value_lines = False


run()
