"""Issue #329 (Auto Key) in a real UI: pCube1 parent-constrains pCube2 (one target), its weight pCube1W0 keyed 1 at
frame 1 and 0 at frame 10, the constraint node open in the Channel Box INPUTS. A click on the Time Slider's Auto Key
button turns Auto Key on; a click on the Time Slider at frame 20, a click in the weight's value field, typing 1 and
Enter keys the weight at 20 (1 is also what the weight showed when Auto Key was turned on); one Ctrl+Z takes back the
weight and its key, Shift+Z brings both back; frame 30, type 0 -> key 0 at 30; frame 40, a drag on the value field ->
key at 40 with the dragged weight; then a scrub of the Time Slider: the weight follows its keys and pCube2 follows
Maya's one-target rule (on pCube1 for any weight above 0, its own place at 0). Screenshots with ALLSET_GUI_SHOTS
(or --shots)."""

import os
import re
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import (MODULE, check, dock_area, dock_region, ev, find_button, run, screenshot, scroll_channel_box,  # noqa: E402
                 setup, step, tap, view3d, win)

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
GUI_TIMEOUT = 300
KEY = "cw:CHILD_OF:0:influence"
FOLLOW = 5.0        # pCube1 at y 5: pCube2 on its target = y 5, on its own place = y 0


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def dock():
    return dock_area(), dock_region()


def cb():
    return import_module(MODULE + ".ui.channel_box")


def child():
    return bpy.data.objects[C["child"]]


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def timeline(kind='WINDOW'):
    for area in win().screen.areas:
        if area.type == 'DOPESHEET_EDITOR' and area.spaces.active.mode == 'TIMELINE':
            return area, next(r for r in area.regions if r.type == kind)
    raise LookupError("no Time Slider")


def tx(frame):
    _area, r = timeline()
    x = r.view2d.view_to_region(frame, 0, clip=False)[0]
    return r.x + int(x), r.y + r.height // 2


def keys():
    fc = cb().fcurve(child(), KEY)
    return [(round(k.co.x), round(k.co.y, 4)) for k in fc.keyframe_points] if fc is not None else None


def weight():
    return cb().get_value(child(), KEY)


def weight_y():
    dg = bpy.context.evaluated_depsgraph_get()
    return child().evaluated_get(dg).matrix_world.translation.y


def on_target(w):
    return FOLLOW if w > 1e-9 else 0.0


def idle(n=3):
    for _i in range(n):
        step(lambda: None)


@step
def s_setup():
    setup()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.mesh.primitive_cube_add()
        parent = bpy.context.view_layer.objects.active
        parent.name = "pCube1"
        bpy.ops.mesh.primitive_cube_add(location=(3.0, 0.0, 0.0))
    ob = bpy.context.view_layer.objects.active
    ob.name = "pCube2"
    con = ob.constraints.new('CHILD_OF')
    con.target = parent
    parent.select_set(False)
    C["child"] = ob.name
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 48
    sc.use_preview_range = False
    sc.allset_auto_key = False
    cb().set_selected_channels([])
    dock_area('CHANNEL_BOX')


@step
def s_open():
    # a new lead starts with every node collapsed (Maya): expand the constraint node once the lead has settled
    ob = child()
    # the constraint took pCube2's offset with pCube1 at the origin: pCube1 at y 5 now = pCube2 at y 5 while on
    bpy.data.objects["pCube1"].location = (0.0, FOLLOW, 0.0)
    cb().set_open(ob, cb().con_node(ob, ob.constraints[0]))
    cb().rebuild_rows()
    area, r = timeline()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        bpy.ops.anim.scene_range_frame()
    redraw()


@step
def s_scroll():
    scroll_channel_box()       # the expanded node's rows may sit below the Channel Box part's fixed height
    redraw()


@step
def s_keyed():
    """The weight keyed 1 at frame 1 and 0 at frame 10 (S keys it there, the earlier #329 test), back at frame 1."""
    ob, sc = child(), bpy.context.scene
    sc.frame_set(1)
    cb().set_value(ob, KEY, 1.0)
    cb().keyframe(ob, KEY)
    sc.frame_set(10)
    cb().set_value(ob, KEY, 0.0)
    cb().keyframe(ob, KEY)
    sc.frame_set(1)
    bpy.ops.ed.undo_push(message="Keys")
    check(f"the weight is keyed 1 at frame 1 and 0 at frame 10 ({keys()})", keys() == [(1, 1.0), (10, 0.0)])
    redraw()


def _is_weight_value(path, _c=None):
    m = re.search(r"allset_cb\.rows\[(\d+)\]\.text$", path or "")
    rows = bpy.context.scene.allset_cb.rows
    return m is not None and int(m.group(1)) < len(rows) and rows[int(m.group(1))].kind == "CONSTRAINT"


step(find_button(dock, _is_weight_value, C, "value", x_frac=0.72, step_px=4))
step(find_button(lambda: timeline('HEADER'), lambda path, cmd: "allset_auto_key" in path, C, "auto", step_px=5))


@step
def s_found():
    check(f"the weight's value field is found ({C.get('value')})", C.get("value") is not None)
    check(f"the Time Slider shows the Auto Key button ({C.get('auto')})", C.get("auto") is not None)
    if not C.get("value") or not C.get("auto"):
        raise RuntimeError("a button was not found")
    x, y = C["auto"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_auto_click():
    ev('LEFTMOUSE', 'PRESS')
    ev('LEFTMOUSE', 'RELEASE')


idle()


@step
def s_auto_on():
    sc = bpy.context.scene
    check(f"a click on the Auto Key button turns Auto Key on at frame 1 ({sc.allset_auto_key}, weight {weight()})",
          sc.allset_auto_key and sc.frame_current == 1 and weight() == 1.0)


def goto(frame):
    def s_hover():
        C["t"] = tx(frame)
        ev('MOUSEMOVE', 'NOTHING', x=C["t"][0], y=C["t"][1])

    def s_click():
        x, y = C["t"]
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)

    def s_at():
        sc = bpy.context.scene
        check(f"a click on the Time Slider goes to frame {frame} ({sc.frame_current})", sc.frame_current == frame)
        redraw()

    for fn in (s_hover, s_click, s_at):
        step(fn)
    idle(2)


def type_weight(text):
    def s_hover():
        x, y = C["value"]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    def s_click():
        x, y = C["value"]
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)

    def s_type():
        ev('A', 'PRESS', ctrl=True)     # select the whole text, then type over it
        ev('A', 'RELEASE', ctrl=True)
        for ch in text:
            ev('TEXTINPUT', 'PRESS', unicode=ch)

    def s_enter():
        tap('RET')

    for fn in (s_hover, s_click, s_type, s_enter):
        step(fn)
    idle(3)          # the Auto Key timer has run


def hover_view():
    _a, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


# --- frame 20: type 1 -------------------------------------------------------------------------------------------------
goto(20)


@step
def s_at20():
    check(f"frame 20 shows the held key 0 (weight {weight()}, pCube2 y {weight_y():.3f})",
          weight() == 0.0 and abs(weight_y()) < 1e-4)


type_weight("1")


@step
def s_typed20():
    shot("gui_issue329_autokey_20.png")
    check(f"typing 1 at frame 20 with Auto Key on keys the weight there ({keys()})",
          keys() == [(1, 1.0), (10, 0.0), (20, 1.0)])
    check(f"... and pCube2 goes onto pCube1 (weight {weight()}, y {weight_y():.3f})",
          weight() == 1.0 and abs(weight_y() - FOLLOW) < 1e-4)
    hover_view()


@step
def s_undo():
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


idle(4)


@step
def s_undone():
    check(f"one Ctrl+Z takes back the typed weight and its key ({keys()}, weight {weight()})",
          keys() == [(1, 1.0), (10, 0.0)] and weight() == 0.0 and bpy.context.scene.frame_current == 20)
    hover_view()


@step
def s_redo():
    ev('Z', 'PRESS', shift=True)
    ev('Z', 'RELEASE', shift=True)
    ev('LEFT_SHIFT', 'RELEASE')


idle(4)


@step
def s_redone():
    check(f"one Shift+Z brings both back ({keys()}, weight {weight()})",
          keys() == [(1, 1.0), (10, 0.0), (20, 1.0)] and weight() == 1.0)


# --- frame 30: type 0 -------------------------------------------------------------------------------------------------
goto(30)
type_weight("0")


@step
def s_typed30():
    check(f"typing 0 at frame 30 keys 0 there ({keys()})", keys() == [(1, 1.0), (10, 0.0), (20, 1.0), (30, 0.0)])
    check(f"... and pCube2 goes back to its own place (y {weight_y():.3f})", abs(weight_y()) < 1e-4)


# --- frame 40: drag the value field -----------------------------------------------------------------------------------
goto(40)


@step
def s_drag_hover():
    x, y = C["value"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_drag_press():
    x, y = C["value"]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


for _i in range(1, 11):
    def _move(i=_i):
        x, y = C["value"]
        ev('MOUSEMOVE', 'NOTHING', x=x + 6 * i, y=y)
    step(_move)


@step
def s_drag_release():
    ev('LEFTMOUSE', 'RELEASE')


idle(3)


@step
def s_dragged():
    w = weight()
    C["w40"] = w
    k = keys() or []
    key40 = next((v for f, v in k if f == 40), None)
    shot("gui_issue329_autokey_drag.png")
    check(f"a drag on the weight's field at frame 40 raises it ({w:.3f}) and keys it there ({k})",
          w > 0.05 and key40 is not None and abs(key40 - round(w, 4)) < 1e-3
          and [f for f, _v in k] == [1, 10, 20, 30, 40])
    check(f"... pCube2 is on pCube1 again (y {weight_y():.3f})", abs(weight_y() - FOLLOW) < 1e-4)


# --- scrub ------------------------------------------------------------------------------------------------------------
SCRUB = (1, 5, 10, 15, 20, 25, 30, 35, 40, 44, 12, 1)


@step
def s_scrub_start():
    C["scrub"] = [tx(f) for f in SCRUB]
    x, y = C["scrub"][0]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_scrub_press():
    x, y = C["scrub"][0]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


def scrub_to(i, frame):
    def s_move():
        x, y = C["scrub"][i]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        redraw()

    def s_check():
        sc = bpy.context.scene
        fc = cb().fcurve(child(), KEY)
        want = fc.evaluate(sc.frame_current) if fc is not None else None
        w = weight()
        row = next(r for r in sc.allset_cb.rows if r.kind == "CONSTRAINT")
        y = weight_y()
        check(f"scrubbing to frame {frame} ({sc.frame_current}): the weight follows its keys (weight {w:.3f}, "
              f"Channel Box {row.text}, curve {want if want is None else round(want, 3)})",
              sc.frame_current == frame and want is not None and abs(w - want) < 1e-5
              and abs(float(row.text) - want) < 1e-3)
        check(f"... and pCube2 follows the one-target rule (y {y:.3f}, want {on_target(want or 0.0):.3f})",
              want is not None and abs(y - on_target(want)) < 1e-4)

    step(s_move)
    step(s_check)


for _i, _f in enumerate(SCRUB):
    if _i:
        scrub_to(_i, _f)


@step
def s_scrub_release():
    x, y = C["scrub"][-1]
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
    redraw()


@step
def s_scrub_done():
    sc = bpy.context.scene
    check(f"the scrub keys nothing ({keys()})", [f for f, _v in keys()] == [1, 10, 20, 30, 40])
    check(f"the scrub ends at frame 1 with weight 1 ({sc.frame_current}, {weight()})",
          sc.frame_current == 1 and weight() == 1.0)
    sc.allset_auto_key = False


run()
