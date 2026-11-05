"""In a real UI (#316): a click on a Channel Box name shows the selection highlight at once, while the mouse
stays over that row; a click on the next row moves the highlight there; quick clicks on two rows both select.
Checked on screenshots (the highlight is the theme's pressed-button colour)."""

import os
import sys
import tempfile
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, dock_area, dock_region, ev, find_button, run, screenshot, setup, step, win  # noqa: E402

C = {}
GUI_TIMEOUT = 200
TMP = tempfile.mkdtemp(prefix="allset316_")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def dock():
    return dock_area(), dock_region()


def cb():
    return import_module(MODULE + ".ui.channel_box")


def pressed_colour():
    th = bpy.context.preferences.themes[0].user_interface.wcol_toggle.inner_sel
    return tuple(th[:3])


def cell_colour(path, key):
    """Mean colour of a 6 x 4 px patch left of the name cell's centre (away from the text)."""
    x, y = C[key]
    x = x - 30
    im = bpy.data.images.load(path, check_existing=False)
    w, _h = im.size
    px = im.pixels[:]
    bpy.data.images.remove(im)
    acc = [0.0, 0.0, 0.0]
    n = 0
    for yy in range(y - 2, y + 2):
        for xx in range(x - 3, x + 3):
            i = (yy * w + xx) * 4
            for c in range(3):
                acc[c] += px[i + c]
            n += 1
    return tuple(v / n for v in acc)


def is_pressed(col):
    """The pressed colour's hue (the button under the mouse is drawn a little lighter): blue well above red, like the
    theme's pressed colour, where an unselected cell is grey."""
    want = pressed_colour()
    return (col[2] - col[0]) > 0.5 * (want[2] - want[0])


def shot_and_read(name, keys):
    path = os.path.join(TMP, name)
    screenshot(path)
    return {k: cell_colour(path, k) for k in keys}


@step
def s_setup():
    setup()
    for o in bpy.context.view_layer.objects:
        o.select_set(o.name == "Cube")
    bpy.context.view_layer.objects.active = bpy.data.objects["Cube"]
    cb().set_selected_channels([])
    dock_area('CHANNEL_BOX')
    redraw()


@step
def s_wait():
    redraw()


step(find_button(dock, lambda p, _c: p.endswith("allset_cb.tx_text"), C, "tx_field", x_frac=0.7, step_px=4))
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.ty_text"), C, "ty_field", x_frac=0.7, step_px=4))
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.tx_sel"), C, "tx_name", y_from="tx_field", step_px=8))
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.ty_sel"), C, "ty_name", y_from="ty_field", step_px=8))


@step
def s_found():
    ok = all(C.get(k) for k in ("tx_name", "ty_name"))
    check(f"name cells found ({C})", ok)
    if not ok:
        raise RuntimeError("cells not found")
    x, y = C["tx_name"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_hover():
    x, y = C["tx_name"]
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


@step
def s_click_tx():
    x, y = C["tx_name"]
    ev('LEFTMOUSE', 'PRESS', x=x + 1, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x + 1, y=y)


@step
def s_settle():
    pass


@step
def s_tx_highlight():
    cols = shot_and_read("tx.png", ("tx_name", "ty_name"))
    check(f"selected {cb().selected_channels()}", cb().selected_channels() == ["tx"])
    check(f"Translate X highlighted while the mouse stays on it ({cols['tx_name']} vs {pressed_colour()})",
          is_pressed(cols["tx_name"]))
    check(f"Translate Y not highlighted ({cols['ty_name']})", not is_pressed(cols["ty_name"]))
    x, y = C["ty_name"]
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


@step
def s_hover_ty():
    x, y = C["ty_name"]
    ev('MOUSEMOVE', 'NOTHING', x=x + 2, y=y)


@step
def s_click_ty():
    x, y = C["ty_name"]
    ev('LEFTMOUSE', 'PRESS', x=x + 2, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x + 2, y=y)


@step
def s_settle2():
    pass


@step
def s_ty_highlight():
    cols = shot_and_read("ty.png", ("tx_name", "ty_name"))
    check(f"selected {cb().selected_channels()}", cb().selected_channels() == ["ty"])
    check(f"Translate Y highlighted while the mouse stays on it ({cols['ty_name']})", is_pressed(cols["ty_name"]))
    check(f"Translate X no longer highlighted ({cols['tx_name']})", not is_pressed(cols["tx_name"]))


@step
def s_quick():
    # Maya: quick clicks, each selects; the second one comes within the double-click time
    x, y = C["tx_name"]
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


@step
def s_quick2():
    x, y = C["tx_name"]
    ev('LEFTMOUSE', 'PRESS', x=x + 1, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x + 1, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x + 1, y=y, ctrl=True)
    ev('LEFTMOUSE', 'RELEASE', x=x + 1, y=y, ctrl=True)


@step
def s_quick_result():
    sel = cb().selected_channels()
    check(f"a quick second Ctrl+click on the same name toggles it off ({sel})", sel == [])


run()
