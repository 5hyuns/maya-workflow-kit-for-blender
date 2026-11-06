"""In a real UI (#315): RMB on a Channel Box channel opens the Channels menu left of the dock, so the channel names
and values stay visible; Ctrl+RMB (the Edit menu) too. Checked on screenshots: the name / value cells look the same
with the menu open, the viewport just left of the dock is covered by the menu."""

import os
import sys
import tempfile
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, dock_area, dock_region, ev, find_button, run, screenshot, setup, step, tap, win  # noqa: E402

C = {}
GUI_TIMEOUT = 200
TMP = tempfile.mkdtemp(prefix="allset315_")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def dock():
    return dock_area(), dock_region()


def cb():
    return import_module(MODULE + ".ui.channel_box")


def patch(path, x, y):
    im = bpy.data.images.load(path, check_existing=False)
    w, _h = im.size
    px = im.pixels[:]
    bpy.data.images.remove(im)
    out = []
    for yy in range(y - 3, y + 3):
        for xx in range(x - 3, x + 3):
            i = (yy * w + xx) * 4
            out.append(tuple(round(v, 3) for v in px[i:i + 3]))
    return out


def points():
    r = dock_region()
    tx_name, tx_field = C["tx_name"], C["tx_field"]
    return {"name": (tx_name[0] - 30, tx_name[1]), "field": tx_field,
            "left": (r.x - 40, tx_name[1])}


def grab(name):
    path = os.path.join(TMP, name)
    screenshot(path)
    return {k: patch(path, *p) for k, p in points().items()}


@step
def s_setup():
    setup()
    for o in bpy.context.view_layer.objects:
        o.select_set(o.name == "Cube")
    bpy.context.view_layer.objects.active = bpy.data.objects["Cube"]
    cb().set_selected_channels(["tx"])
    dock_area('CHANNEL_BOX')
    redraw()


@step
def s_wait():
    redraw()


step(find_button(dock, lambda p, _c: p.endswith("allset_cb.tx_text"), C, "tx_field", x_frac=0.7, step_px=4))
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.tx_sel_on"), C, "tx_name", y_from="tx_field", step_px=8))


@step
def s_found():
    ok = all(C.get(k) for k in ("tx_name", "tx_field"))
    check(f"cells found ({C})", ok)
    if not ok:
        raise RuntimeError("cells not found")
    # the before shot with the mouse where the menu puts it: nothing in the dock hovered
    r = dock_region()
    ev('MOUSEMOVE', 'NOTHING', x=r.x - 60, y=C["tx_field"][1])


@step
def s_before():
    C["before"] = grab("before.png")
    x, y = C["tx_field"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_hover():
    x, y = C["tx_field"]
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


def menu_steps(tag, ctrl):
    def press():
        x, y = C["tx_field"]
        ev('RIGHTMOUSE', 'PRESS', x=x + 1, y=y, ctrl=ctrl)
        ev('RIGHTMOUSE', 'RELEASE', x=x + 1, y=y, ctrl=ctrl)
    press.__name__ = f"s_{tag}_press"
    step(press)

    def settle():
        redraw()
    settle.__name__ = f"s_{tag}_settle"
    step(settle)

    def look():
        after = grab(f"{tag}.png")
        before = C["before"]
        check(f"{tag}: the channel name cell is not covered", after["name"] == before["name"])
        # the field under the click may keep its hover tint; a menu over it would be far darker
        diff = sum(abs(a - b) for pa, pb in zip(after["field"], before["field"]) for a, b in zip(pa, pb))
        diff /= 3 * len(before["field"])
        check(f"{tag}: the value field is not covered (mean difference {diff:.3f})", diff < 0.05)
        check(f"{tag}: the menu is drawn left of the dock", after["left"] != before["left"])
        tap('ESC')
    look.__name__ = f"s_{tag}_look"
    step(look)

    def back():
        x, y = C["tx_field"]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    back.__name__ = f"s_{tag}_back"
    step(back)

    def back2():
        x, y = C["tx_field"]
        ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)
    back2.__name__ = f"s_{tag}_back2"
    step(back2)


menu_steps("channels", False)
menu_steps("edit", True)


@step
def s_kept():
    check(f"the selection is kept ({cb().selected_channels()})", cb().selected_channels() == ["tx"])


run()
