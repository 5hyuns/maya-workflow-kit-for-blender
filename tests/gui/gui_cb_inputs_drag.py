"""Channel Box INPUTS in a real UI (#230, #222): a kit cube's polyCube1 expanded -> a left drag across its Subdivisions
Height value steps it by whole numbers and rebuilds the cube; a click on the attribute name selects it and a
middle drag in the viewport then changes it (Maya's virtual slider); a Subdivision modifier's Levels value drags the
same way. Screenshots with ALLSET_GUI_SHOTS (or --shots)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import (MODULE, check, dock_area, dock_region, ev, find_button, run, screenshot, scroll_channel_box,  # noqa: E402
                 setup, step, view3d, win)

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
GUI_TIMEOUT = 300


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def dock():
    return dock_area(), dock_region()


def cb():
    return import_module(MODULE + ".ui.channel_box")


def ph():
    return import_module(MODULE + ".operators.prim_history")


def cube():
    return bpy.data.objects[C["cube"]]


def subdiv_height():
    return ph().attrs(ph().node_of(cube())[0])["subdivisionsHeight"]


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
        bpy.ops.allset.create(kind='CUBE')
    ob = bpy.context.view_layer.objects.active
    C["cube"] = ob.name
    _owner, node = ph().node_of(ob)
    cb().set_open(ob, cb().history_node(node["name"]))
    cb().set_selected_channels([])
    dock_area('CHANNEL_BOX')


@step
def s_wait():
    # a new lead starts with every node collapsed (Maya): expand polyCube1 once the lead has settled
    _owner, node = ph().node_of(cube())
    cb().set_open(cube(), cb().history_node(node["name"]))
    cb().rebuild_rows()
    redraw()


@step
def s_wait2():
    scroll_channel_box()       # the expanded node's rows are below the Channel Box part's fixed height
    redraw()


step(find_button(dock, lambda p, _c: p.endswith("allset_creation.subdivisionsHeight_text"), C, "sh", x_frac=0.7,
                 step_px=4))
step(find_button(dock, lambda p, _c: p.endswith("allset_creation.subdivisionsHeight_sel"), C, "sh_name",
                 x_frac=0.25, step_px=4))


@step
def s_found():
    shot("gui_cb_inputs_found.png")
    check(f"Subdivisions Height value / name found ({C.get('sh')}, {C.get('sh_name')})",
          C.get("sh") and C.get("sh_name"))
    if not C.get("sh"):
        raise RuntimeError("field not found")
    C["start"] = subdiv_height()
    C["verts"] = len(cube().data.vertices)


def drag(tag, key, dx, moves=10, button='LEFTMOUSE', at=None):
    def hover():
        x, y = at() if at else C[key]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    hover.__name__ = f"s_{tag}_hover"
    step(hover)

    def press():
        x, y = at() if at else C[key]
        ev(button, 'PRESS', x=x, y=y)
    press.__name__ = f"s_{tag}_press"
    step(press)
    for i in range(1, moves + 1):
        def move(i=i):
            x, y = at() if at else C[key]
            ev('MOUSEMOVE', 'NOTHING', x=x + round(dx * i / moves), y=y)
        move.__name__ = f"s_{tag}_move{i}"
        step(move)

    def release():
        ev(button, 'RELEASE')
    release.__name__ = f"s_{tag}_release"
    step(release)
    for i in range(8):
        def settle():
            redraw()
        settle.__name__ = f"s_{tag}_settle{i}"
        step(settle)


drag("value", "sh", 20)           # an integer value: 10 px per step -> 2 subdivisions more


@step
def s_value_dragged():
    v = subdiv_height()
    check(f"a left drag across Subdivisions Height steps it by whole numbers ({C['start']} -> {v})",
          v == C["start"] + 2)
    check(f"the cube was rebuilt ({C['verts']} -> {len(cube().data.vertices)} vertices)",
          len(cube().data.vertices) > C["verts"])
    shot("gui_cb_inputs_drag_value.png")
    C["mid"] = v


@step
def s_click_name():
    x, y = C["sh_name"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_click_name_press():
    x, y = C["sh_name"]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_selected():
    key = cb().HISTORY_PREFIX + "subdivisionsHeight"
    check(f"a click on the attribute name selects it ({cb().selected_channels()})",
          cb().selected_channels() == [key])


def viewport_point():
    area, region = view3d()
    return region.x + region.width // 3, region.y + region.height // 3


drag("slider", None, -100, button='MIDDLEMOUSE', at=viewport_point)     # -1 subdivision


@step
def s_slider():
    v = subdiv_height()
    check(f"a middle drag in the viewport changes the selected history attribute ({C['mid']} -> {v})",
          v == C["mid"] - 1)
    cb().set_selected_channels([])
    ob = cube()
    ob.modifiers.new("subdiv", 'SUBSURF').levels = 1
    redraw()


@step
def s_rows():
    ob = cube()
    cb().set_open(ob, cb().mod_node(ob.modifiers["subdiv"]))
    cb().rebuild_rows()
    redraw()


@step
def s_rows2():
    cb().reveal(cb().mod_node(cube().modifiers["subdiv"]))    # scroll the node's first rows into view
    redraw()


step(find_button(dock, lambda p, _c: ".rows[" in p and p.endswith("].text") and _levels_row(p), C, "lv",
                 x_frac=0.7, step_px=4))


def _levels_row(path):
    import re
    m = re.search(r"rows\[(\d+)\]", path)
    rows = bpy.context.scene.allset_cb.rows
    return bool(m) and int(m.group(1)) < len(rows) and rows[int(m.group(1))].kind == "INPUT" \
        and rows[int(m.group(1))].name == "levels"


drag("levels", "lv", 10)          # 10 px = one level


@step
def s_levels():
    check(f"Levels value found ({C.get('lv')})", C.get("lv"))
    lv = cube().modifiers["subdiv"].levels
    check(f"a Subdivision modifier's Levels value drags by whole numbers (1 -> {lv})", lv == 2)
    cb().set_selected_channels([cb().row_key(next(r for r in bpy.context.scene.allset_cb.rows if r.name == "levels"))])
    shot("gui_cb_inputs_drag_levels.png")


run()
