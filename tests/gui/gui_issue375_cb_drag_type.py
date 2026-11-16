"""#375 in a real UI: Maya Channel Box, drag down over the value fields Scale X -> Scale Z, release, then just type
a value and Enter (no second click): the value goes into every selected channel of both selected cubes. The selection
shows where it was made, like Maya: after the drag over the values their cells are blue and the names are not. A drag
over the names only selects (no field editor opens); then the names are blue and the values stay text fields."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, dock_area, dock_region, ev, find_button, run, screenshot, setup, step, tap, win  # noqa: E402

C = {}
GUI_TIMEOUT = 240


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def dock():
    return dock_area(), dock_region()


def cb():
    return import_module(MODULE + ".ui.channel_box")


def cubes():
    return bpy.data.objects["Cube"], bpy.data.objects["Cube2"]


@step
def s_setup():
    setup()
    a = bpy.data.objects["Cube"]
    b = a.copy()
    b.name = "Cube2"
    bpy.context.scene.collection.objects.link(b)
    for o in bpy.context.view_layer.objects:
        o.select_set(o in (a, b))
    bpy.context.view_layer.objects.active = a
    cb().set_selected_channels([])
    dock_area('CHANNEL_BOX')
    redraw()


@step
def s_wait():
    redraw()


step(find_button(dock, lambda p, _c: p.endswith("allset_cb.sx_text"), C, "sx_field", x_frac=0.7, step_px=4))
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.sz_text"), C, "sz_field", x_frac=0.7, step_px=4))
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.tx_text"), C, "tx_field", x_frac=0.7, step_px=4))
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.tz_text"), C, "tz_field", x_frac=0.7, step_px=4))
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.tx_sel"), C, "tx_name", y_from="tx_field", step_px=8))
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.tz_sel"), C, "tz_name", y_from="tz_field", step_px=8))


@step
def s_found():
    found = {k: C.get(k) for k in ("sx_field", "sz_field", "tx_name", "tz_name")}
    check(f"Scale X / Scale Z fields found ({found})", all(found.values()))
    if not all(found.values()):
        raise RuntimeError("cells not found")
    x, y = C["sx_field"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_hover():
    x, y = C["sx_field"]
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


@step
def s_press():
    x, y = C["sx_field"]
    ev('LEFTMOUSE', 'PRESS', x=x + 1, y=y)


def _drag(key_from, key_to, tag, n=6):
    for i in range(1, n + 1):
        def move(i=i):
            x0, y0 = C[key_from]
            x1, y1 = C[key_to]
            ev('MOUSEMOVE', 'NOTHING', x=x0 + 1, y=round(y0 + (y1 - y0) * i / n))
        move.__name__ = f"s_drag_{tag}_{i}"
        step(move)


_drag("sx_field", "sz_field", "fields")


@step
def s_release():
    ev('LEFTMOUSE', 'RELEASE')
    redraw()


@step
def s_selected():
    sel = cb().selected_channels()
    check(f"drag over the value fields Scale X -> Scale Z selects them ({sel})", sel == ["sx", "sy", "sz"])


@step
def s_type():
    ev('A', 'PRESS', ctrl=True)
    ev('A', 'RELEASE', ctrl=True)
    ev('TEXTINPUT', 'PRESS', unicode="3")
    redraw()


@step
def s_enter():
    tap('RET')


@step
def s_applied():
    for ob in cubes():
        check(f"{ob.name}: typing 3 right after the drag set Scale X/Y/Z ({tuple(ob.scale)})",
              tuple(ob.scale) == (3.0, 3.0, 3.0))
        check(f"{ob.name}: unselected Translate stays ({tuple(ob.location)})", tuple(ob.location) == (0.0, 0.0, 0.0))
    x, y = C["tx_name"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


# Maya: the cells of a drag over the values are blue (a pressed toggle of the twin ``<key>_text_on``), their names not
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.sy_text_on"), C, "sy_blue", x_frac=0.7, step_px=4))
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.sy_sel"), C, "sy_name", y_from="sy_blue", step_px=8))


@step
def s_value_cells_blue():
    check(f"after a drag over the values, a selected value cell is blue (Scale Y: {C.get('sy_blue')})",
          C.get("sy_blue") is not None)
    check(f"after a drag over the values, the selected channel's name is not pressed (Scale Y: {C.get('sy_name')})",
          C.get("sy_name") is not None)
    shots = os.environ.get("ALLSET_GUI_SHOTS", "")
    if shots:
        screenshot(os.path.join(shots, "gui_issue375_blue_values.png"))
    x, y = C["tx_name"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_name_hover():
    x, y = C["tx_name"]
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


@step
def s_name_press():
    x, y = C["tx_name"]
    ev('LEFTMOUSE', 'PRESS', x=x + 1, y=y)


_drag("tx_name", "tz_name", "names")


@step
def s_name_release():
    ev('LEFTMOUSE', 'RELEASE')
    redraw()


@step
def s_name_type():
    ev('TEXTINPUT', 'PRESS', unicode="7")
    tap('RET')


@step
def s_name_only_selects():
    sel = cb().selected_channels()
    check(f"a drag over the names Translate X -> Z selects them ({sel})", sel == ["tx", "ty", "tz"])
    a, _b = cubes()
    check(f"after a name drag, typing opens no field (Translate {tuple(a.location)})",
          tuple(a.location) == (0.0, 0.0, 0.0))



# Maya: after a drag over the names, the names are blue and the value cells stay text fields
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.ty_text"), C, "ty_plain", x_frac=0.7, step_px=4))
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.ty_sel_on"), C, "ty_name_on", y_from="ty_plain",
                 step_px=8))


@step
def s_name_cells_blue():
    check(f"after a drag over the names, a selected name is pressed (Translate Y: {C.get('ty_name_on')})",
          C.get("ty_name_on") is not None)
    check(f"after a drag over the names, its value cell stays a text field (Translate Y: {C.get('ty_plain')})",
          C.get("ty_plain") is not None)
    shots = os.environ.get("ALLSET_GUI_SHOTS", "")
    if shots:
        screenshot(os.path.join(shots, "gui_issue375_blue_names.png"))


run()
