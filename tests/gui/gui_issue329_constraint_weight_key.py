"""Issue #329 in a real UI: pCube1 parent-constrains pCube2, the constraint node expanded in the Channel Box INPUTS ->
RMB on the target weight's name (pCube1W0) selects that channel and opens the Channels menu; Key Selected (K) keys
the constraint's influence on pCube2, and the row then shows the keyed state. Screenshots with ALLSET_GUI_SHOTS
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
GUI_TIMEOUT = 240
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


run()
