"""Graph Editor tools in a real UI (Maya Workflow Kit layout, the big view switched to the Graph Editor), driven by
simulated mouse events:

- Region Keys tool: a marquee leaves its region as a box; dragging the box's right side scales the keys inside about
  the region's left side (a single key has no box of its own), and the box follows the keys.
- Prefer Selected Curves: with a key of curve Y selected, a click nearer to a key of curve X than to one of Y picks the
  Y key; with the option off the same click picks the X key.
- Pre-Select Highlight: the curve under the mouse is the hovered one, none away from the curves.
"""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, screenshot, view3d, win, load_maya_layout, graph_value  # noqa: E402,E501

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
# location X keys and location Y keys (linear)
X_KEYS = ((1, 0.0), (10, 5.0), (20, 0.0))
Y_KEYS = ((1, 1.0), (10, 4.85), (20, 2.0))


def region():
    return next(r for r in C["area"].regions if r.type == 'WINDOW')


def curve(index):
    ob = bpy.data.objects["keys"]
    return next(fc for fc in import_module(MODULE + ".compat").id_fcurves(ob)
                if fc.data_path == "location" and fc.array_index == index)


def view_px(frame, shown):
    """Region pixel of a point of the view (frame, value as the value axis shows it)."""
    return tuple(int(round(v)) for v in region().view2d.view_to_region(frame, shown, clip=False))


def to_px(frame, value):
    """Region pixel of a stored location value at ``frame``."""
    return view_px(frame, graph_value(curve(0), value))


def win_xy(rx, ry):
    r = region()
    return int(r.x + rx), int(r.y + ry)


def times(index):
    return [round(kp.co.x, 3) for kp in curve(index).keyframe_points]


def selected(index):
    return [round(kp.co.x, 3) for kp in curve(index).keyframe_points if kp.select_control_point]


def select_only(index, frames):
    for i in (0, 1):
        fc = curve(i)
        fc.select = i == index
        for kp in fc.keyframe_points:
            kp.select_control_point = i == index and any(abs(kp.co.x - f) < 1e-3 for f in frames)
            kp.select_left_handle = kp.select_right_handle = False


def prefs():
    return import_module(MODULE + ".preferences").get()


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, _reg = view3d()
    bpy.ops.object.empty_add()
    ob = bpy.context.active_object
    ob.name = "keys"
    for index, keys in ((0, X_KEYS), (1, Y_KEYS)):
        for t, v in keys:
            ob.location[index] = v
            ob.keyframe_insert("location", index=index, frame=t)
    for i in (0, 1):
        for kp in curve(i).keyframe_points:
            kp.interpolation = 'LINEAR'
    bpy.context.scene.frame_set(1)
    bpy.context.scene.tool_settings.use_snap_anim = True
    bpy.context.scene.allset_auto_key = False
    p = prefs()
    p.snap_time_to_selection = False
    p.graph_auto_frame = False
    p.graph_auto_frame_time = False
    C["area"] = area
    area.ui_type = 'FCURVES'


@step
def s_view():
    a = C["area"]
    sp = a.spaces.active
    sp.use_normalization = False
    sp.dopesheet.show_only_selected = True
    with bpy.context.temp_override(window=win(), area=a, region=region()):
        bpy.ops.graph.view_all()


def _idle(n=3):
    for _ in range(n):
        step(lambda: None)


def _move(x, y):
    ev('MOUSEMOVE', 'NOTHING', x=win_xy(x, y)[0], y=win_xy(x, y)[1])


def _drag(start, end, n=6):
    """A left drag from region point ``start`` to ``end`` (one event per step)."""
    step(lambda: _move(*start()))
    step(lambda: ev('LEFTMOUSE', 'PRESS', x=win_xy(*start())[0], y=win_xy(*start())[1]))
    for i in range(1, n + 1):
        def mv(i=i):
            (x0, y0), (x1, y1) = C["drag"]
            _move(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n)
        step(mv)
    step(lambda: ev('LEFTMOUSE', 'RELEASE'))
    _idle(4)


def _set_drag(start, end):
    def fn():
        C["drag"] = (start(), end())
    return fn


# --- Region Keys tool ---------------------------------------------------------------------------------------------

@step
def s_region_tool():
    select_only(0, ())
    C["before"] = (times(0), times(1))
    _move(region().width // 2, region().height // 2)
    bpy.context.window_manager.allset_graph_key_tool = 'REGION'
    bpy.ops.ed.undo_push(message="region start")


def _marquee():
    return to_px(2, 0.2), to_px(12, 5.15)


step(_set_drag(lambda: _marquee()[0], lambda: _marquee()[1]))
_drag(lambda: C["drag"][0], lambda: C["drag"][1])


@step
def s_region_check():
    gr = import_module(MODULE + ".operators.graph_region")
    a = C["area"]
    with bpy.context.temp_override(window=win(), area=a, region=region(), space_data=a.spaces.active):
        view = gr.region_of(bpy.context)
        sb = import_module(MODULE + ".operators.graph_scale_box")
        boxes = sb.current_boxes(bpy.context)
    check(f"the marquee selected the keys at 10 ({selected(0)} / {selected(1)})",
          selected(0) == [10] and selected(1) == [10])
    check(f"the Region Keys box is the marquee's region ({view})",
          view is not None and abs(view[0] - 2) < 0.3 and abs(view[2] - 12) < 0.3)
    check("the box drawn is that region", boxes is not None and boxes[1] == view)
    C["region"] = view
    if SHOTS:
        screenshot(os.path.join(SHOTS, "graph_region_box.png"))


def _right_side():
    v = C["region"] or (2, 0, 12, 1)
    return view_px(v[2], (v[1] + v[3]) / 2)


def _right_side_to():
    v = C["region"] or (2, 0, 12, 1)
    return view_px(v[0] + 1.5 * (v[2] - v[0]), (v[1] + v[3]) / 2)


step(_set_drag(_right_side, _right_side_to))
_drag(lambda: C["drag"][0], lambda: C["drag"][1])


@step
def s_region_scaled():
    # time x1.5 about the region's left side (frame 2): 10 -> 14 (one key alone has no box of its own)
    check(f"the right side scaled the key about the region's left side ({times(0)} / {times(1)})",
          times(0) == [1, 14, 20] and times(1) == [1, 14, 20])
    gr = import_module(MODULE + ".operators.graph_region")
    a = C["area"]
    with bpy.context.temp_override(window=win(), area=a, region=region(), space_data=a.spaces.active):
        view = gr.region_of(bpy.context)
    check(f"the region followed the keys ({view})", view is not None and abs(view[2] - 17) < 0.6)
    if SHOTS:
        screenshot(os.path.join(SHOTS, "graph_region_scaled.png"))


@step
def s_region_undo():
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


_idle(3)


@step
def s_region_undo_check():
    check(f"one undo puts the keys back ({times(0)})", (times(0), times(1)) == C["before"])
    bpy.context.window_manager.allset_graph_key_tool = 'MOVE'


# --- Prefer Selected Curves ---------------------------------------------------------------------------------------

def _prefer_case(name, on):
    def before():
        prefs().graph_prefer_selected = on
        select_only(1, (1,))            # Y has a selected key: Y is the preferred curve
        curve(0).select, curve(1).select = True, False      # X is the selected channel (Blender's own pick)
        # Y's key at 10 sits 6 px below X's key (both within Blender's 10 px pick distance)
        ppv = to_px(10, 1.0)[1] - to_px(10, 0.0)[1]
        kp = next(k for k in curve(1).keyframe_points if abs(k.co.x - 10) < 1e-3)
        d = (5.0 - 6.0 / ppv) - kp.co.y
        kp.co.y += d
        kp.handle_left.y += d
        kp.handle_right.y += d
        curve(1).update()
        x, yx = to_px(10, 5.0)
        _x, yy = to_px(10, kp.co.y)
        # 2 px from X's key toward Y's: X's key is the nearer one (and X is the first curve)
        C["click"] = (x, yx + (2 if yy > yx else -2))
        C["gap"] = abs(yx - yy)
        _move(*C["click"])
    step(before)
    step(lambda: ev('LEFTMOUSE', 'PRESS', x=win_xy(*C["click"])[0], y=win_xy(*C["click"])[1]))
    step(lambda: ev('LEFTMOUSE', 'RELEASE'))
    _idle(3)

    def verify():
        gap = C["gap"]
        if on:
            check(f"{name}: the click took Y's key at 10 ({selected(0)} / {selected(1)}, keys {gap} px apart)",
                  selected(1) == [10] and selected(0) == [])
        else:
            check(f"{name}: without the option the nearer X key is picked ({selected(0)} / {selected(1)})",
                  selected(0) == [10] and selected(1) == [])
    step(verify)


_prefer_case("prefer_on", True)
_prefer_case("prefer_off", False)


# --- Pre-Select Highlight -----------------------------------------------------------------------------------------

def _hover_case(name, point, want):
    def go():
        prefs().graph_preselect = True
        select_only(0, ())
        _move(*point())
    step(go)
    _idle(2)

    def verify():
        gh = import_module(MODULE + ".operators.graph_hover")
        a = C["area"]
        with bpy.context.temp_override(window=win(), area=a, region=region(), space_data=a.spaces.active):
            got = gh.hovered(bpy.context)
        exp = want()
        check(f"{name}: hovered curve {got} (want {exp})", got == exp)
        if SHOTS and exp is not None:
            screenshot(os.path.join(SHOTS, f"graph_{name}.png"))
    step(verify)


# X at frame 5 = 2.222 (0 -> 5 over 1..10); Y at frame 15 halfway between its keys at 10 and 20
_hover_case("hover_x", lambda: to_px(5, 5.0 * 4 / 9), lambda: curve(0).as_pointer())
_hover_case("hover_y", lambda: to_px(15, curve(1).evaluate(15)), lambda: curve(1).as_pointer())
_hover_case("hover_none", lambda: to_px(15, 0.2), lambda: None)


@step
def s_hover_off():
    prefs().graph_preselect = False
    _move(*to_px(5, 5.0 * 4 / 9))


_idle(2)


@step
def s_hover_off_check():
    gh = import_module(MODULE + ".operators.graph_hover")
    a = C["area"]
    with bpy.context.temp_override(window=win(), area=a, region=region(), space_data=a.spaces.active):
        got = gh.hovered(bpy.context)
    check(f"with the option off nothing is highlighted ({got})", got is None)
    prefs().graph_prefer_selected = False


run()
