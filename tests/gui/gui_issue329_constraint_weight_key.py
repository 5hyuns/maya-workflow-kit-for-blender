"""Issue #329 in a real UI: pCube1 parent-constrains pCube2, the constraint node expanded in the Channel Box INPUTS ->
RMB on the target weight's name (pCube1W0) selects that channel and opens the Channels menu; Key Selected (K) keys
the constraint's influence on pCube2, and the row then shows the keyed state. Then the follow-up report: type 0 in
the weight and press S, go to frame 10 on the Time Slider, type 1 and press S, and scrub the Time Slider — the
weight and pCube2's evaluated position follow the keys. Screenshots with ALLSET_GUI_SHOTS (or --shots)."""

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
    bpy.context.scene.frame_set(5)
    cb().set_selected_channels([])
    dock_area('CHANNEL_BOX')


@step
def s_wait():
    # a new lead starts with every node collapsed (Maya): expand the constraint node once the lead has settled
    ob = child()
    cb().set_open(ob, cb().con_node(ob, ob.constraints[0]))
    cb().rebuild_rows()
    redraw()


@step
def s_wait2():
    scroll_channel_box()       # the expanded node's rows may sit below the Channel Box part's fixed height
    redraw()


def _is_weight(path, _c=None):
    m = re.search(r"allset_cb\.rows\[(\d+)\]\.sel$", path or "")
    rows = bpy.context.scene.allset_cb.rows
    return m is not None and int(m.group(1)) < len(rows) and rows[int(m.group(1))].kind == "CONSTRAINT"


step(find_button(dock, _is_weight, C, "weight", x_frac=0.25, step_px=4))


@step
def s_hover():
    shot("gui_issue329_found.png")
    check(f"the pCube1W0 weight's name is a channel button ({C.get('weight')})", C.get("weight") is not None)
    if not C.get("weight"):
        raise RuntimeError("weight row not found")
    x, y = C["weight"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_hover2():
    x, y = C["weight"]
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


@step
def s_rmb():
    ev('RIGHTMOUSE', 'PRESS')
    ev('RIGHTMOUSE', 'RELEASE')


@step
def s_menu():
    shot("gui_issue329_menu.png")
    sel = cb().selected_channels()
    check(f"RMB on the weight selects its channel ({sel})", sel == [KEY])
    check(f"the channel is labelled after the target ({cb().channel_label(KEY)})", cb().channel_label(KEY) == "pCube1W0")


@step
def s_pick():
    tap('K')      # Key Selected by its underlined letter (the menu may slide up)


@step
def s_picked():
    redraw()
    ob = child()
    curves = list(import_module(MODULE + ".compat").id_fcurves(ob)) if ob.animation_data else []
    keyed = [(fc.data_path, [round(k.co.x) for k in fc.keyframe_points]) for fc in curves]
    check(f"Channels > Key Selected keys the target weight at the current frame ({keyed})",
          keyed == [(f'constraints["{ob.constraints[0].name}"].influence', [5])])
    state = cb().channel_state(ob, KEY)
    check(f"the weight row reads keyed ({state})", state == 'KEYED')
    parent = bpy.data.objects["pCube1"]
    check("the target object stays unkeyed", parent.animation_data is None)


@step
def s_shot():
    shot("gui_issue329_keyed.png")


@step
def s_delete():
    """Channels > Delete Selected removes the weight's curve (the row reads plain again)."""
    bpy.ops.allset.cb_delete_keys()
    redraw()


@step
def s_deleted():
    ob = child()
    state = cb().channel_state(ob, KEY)
    check(f"Delete Selected clears the weight's animation ({state})", state is None and cb().fcurve(ob, KEY) is None)
    # the follow-up report: type the weight, S, another frame, type, S, scrub
    bpy.data.objects["pCube1"].location = (0.0, FOLLOW, 0.0)       # weight 1 = pCube2 at y 5, weight 0 = y 0
    cb().set_selected_channels([])
    bpy.context.scene.frame_set(1)
    redraw()


# --- type, S, frame, type, S, scrub ------------------------------------------------------------------------------

FOLLOW = 5.0


def timeline():
    for area in win().screen.areas:
        if area.type == 'DOPESHEET_EDITOR' and area.spaces.active.mode == 'TIMELINE':
            return area, next(r for r in area.regions if r.type == 'WINDOW')
    raise LookupError("no timeline")


def tx(frame):
    _area, r = timeline()
    x = r.view2d.view_to_region(frame, 0, clip=False)[0]
    return r.x + int(x), r.y + r.height // 2


def hover_view():
    _a, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


def type_text(text):
    ev('A', 'PRESS', ctrl=True)     # select the whole text, then type over it
    ev('A', 'RELEASE', ctrl=True)
    for ch in text:
        ev('TEXTINPUT', 'PRESS', unicode=ch)


def weight_y():
    dg = bpy.context.evaluated_depsgraph_get()
    return child().evaluated_get(dg).matrix_world.translation.y


def weight_row():
    return next(r for r in bpy.context.scene.allset_cb.rows if r.kind == "CONSTRAINT")


def _is_weight_value(path, _c=None):
    m = re.search(r"allset_cb\.rows\[(\d+)\]\.text$", path or "")
    rows = bpy.context.scene.allset_cb.rows
    return m is not None and int(m.group(1)) < len(rows) and rows[int(m.group(1))].kind == "CONSTRAINT"


@step
def s_range():
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 24
    sc.use_preview_range = False
    area, r = timeline()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        bpy.ops.anim.scene_range_frame()
    redraw()


step(find_button(dock, _is_weight_value, C, "value", x_frac=0.72, step_px=4))


def type_weight(text, frame):
    """Steps: click the weight's value field, type ``text``, Enter, then S over the viewport."""
    def s_click():
        check(f"the weight's value field is found ({C.get('value')})", C.get("value") is not None)
        if not C.get("value"):
            raise RuntimeError("weight value field not found")
        x, y = C["value"]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    def s_press():
        x, y = C["value"]
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)

    def s_type():
        type_text(text)

    def s_enter():
        tap('RET')

    def s_typed():
        con = child().constraints[0]
        check(f"typing {text} at frame {frame} sets the weight ({con.influence:.3f})",
              abs(con.influence - float(text)) < 1e-6)
        hover_view()

    def s_key():
        tap('S')

    def s_keyed():
        fc = cb().fcurve(child(), KEY)
        keys = [(round(k.co.x), round(k.co.y, 6)) for k in fc.keyframe_points] if fc is not None else None
        check(f"S keys the open constraint node's weight at frame {frame} ({keys})",
              keys is not None and (frame, float(text)) in keys)
        redraw()

    for fn in (s_click, s_press, s_type, s_enter, s_typed, s_key, s_keyed):
        step(fn)


type_weight("0", 1)


@step
def s_goto10():
    C["t10"] = tx(10)
    ev('MOUSEMOVE', 'NOTHING', x=C["t10"][0], y=C["t10"][1])


@step
def s_click10():
    x, y = C["t10"]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_at10():
    sc = bpy.context.scene
    check(f"a click on the Time Slider goes to frame 10 ({sc.frame_current})", sc.frame_current == 10)
    redraw()


type_weight("1", 10)


@step
def s_scrub_start():
    fc = cb().fcurve(child(), KEY)
    keys = [(round(k.co.x), round(k.co.y, 6)) for k in fc.keyframe_points] if fc is not None else None
    check(f"the weight's curve holds both keys ({keys})", keys == [(1, 0.0), (10, 1.0)])
    C["scrub"] = [tx(f) for f in (1, 5, 10, 3)]
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
        w = child().constraints[0].influence
        text = weight_row().text
        y = weight_y()
        shot(f"gui_issue329_scrub_{frame}.png")
        check(f"scrubbing to frame {frame} ({sc.frame_current}): the weight follows its keys (influence {w:.3f}, "
              f"Channel Box {text}, curve {want if want is None else round(want, 3)})",
              sc.frame_current == frame and want is not None and abs(w - want) < 1e-5
              and abs(float(text) - want) < 1e-3)
        check(f"... and pCube2 moves with it (y {y:.3f}, want {FOLLOW * (want or 0):.3f})",
              want is not None and abs(y - FOLLOW * want) < 1e-4)
        redraw()

    step(s_move)
    step(s_check)


scrub_to(1, 5)
scrub_to(2, 10)
scrub_to(3, 3)


@step
def s_scrub_release():
    x, y = C["scrub"][3]
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
    redraw()


@step
def s_scrub_done():
    sc = bpy.context.scene
    check(f"the scrub ends at frame 3 ({sc.frame_current}) with the weight between the keys",
          sc.frame_current == 3 and 0.05 < child().constraints[0].influence < 0.95)


run()
