"""#375 in a real UI, the value editor like Maya's Channel Box: after a drag down over the values Rotate X -> Rotate Z
the editor shows the last value (Rotate Z) ready to be replaced; Esc writes nothing, a click away writes only a
changed text, Enter writes the text into every selected channel of both selected cubes (also when it is unchanged).
A single click on one value and then a click away changes nothing either."""

import math
import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, dock_area, dock_region, ev, find_button, run, setup, step, view3d, win  # noqa: E402

C = {}
GUI_TIMEOUT = 360
LEAD = (10.0, 20.0, 30.0)
OTHER = (1.0, 2.0, 3.0)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def dock():
    return dock_area(), dock_region()


def cb():
    return import_module(MODULE + ".ui.channel_box")


def cubes():
    return bpy.data.objects["Cube"], bpy.data.objects["Cube2"]


def degrees(ob):
    return tuple(round(math.degrees(v), 3) for v in ob.rotation_euler)


def reset():
    a, b = cubes()
    a.rotation_euler = [math.radians(v) for v in LEAD]
    b.rotation_euler = [math.radians(v) for v in OTHER]
    for o in bpy.context.view_layer.objects:
        o.select_set(o in (a, b))
    bpy.context.view_layer.objects.active = a
    cb().set_selected_channels([])
    redraw()


@step
def s_setup():
    setup()
    a = bpy.data.objects["Cube"]
    b = a.copy()
    b.name = "Cube2"
    bpy.context.scene.collection.objects.link(b)
    reset()
    dock_area('CHANNEL_BOX')
    redraw()


@step
def s_wait():
    redraw()


for _k in ("rx", "ry", "rz"):
    step(find_button(dock, lambda p, _c, k=_k: p.endswith(f"allset_cb.{k}_text"), C, _k, x_frac=0.7, step_px=4))


@step
def s_found():
    found = {k: C.get(k) for k in ("rx", "ry", "rz")}
    check(f"Rotate X / Y / Z fields found ({found})", all(found.values()))
    if not all(found.values()):
        raise RuntimeError("fields not found")
    C["rz_text"] = bpy.context.scene.allset_cb.rz_text
    C["ry_text"] = bpy.context.scene.allset_cb.ry_text
    _area, r = view3d()
    C["away"] = (r.x + 60, r.y + 60)


def value_drag(tag):
    def hover():
        x, y = C["rx"]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    hover.__name__ = f"s_{tag}_hover"
    step(hover)

    def hover2():
        x, y = C["rx"]
        ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)
    hover2.__name__ = f"s_{tag}_hover2"
    step(hover2)

    def press():
        x, y = C["rx"]
        ev('LEFTMOUSE', 'PRESS', x=x + 1, y=y)
    press.__name__ = f"s_{tag}_press"
    step(press)
    for i in range(1, 7):
        def move(i=i):
            x0, y0 = C["rx"]
            _x1, y1 = C["rz"]
            ev('MOUSEMOVE', 'NOTHING', x=x0 + 1, y=round(y0 + (y1 - y0) * i / 6))
        move.__name__ = f"s_{tag}_move{i}"
        step(move)

    def release():
        ev('LEFTMOUSE', 'RELEASE')
        redraw()
    release.__name__ = f"s_{tag}_release"
    step(release)


def click_away(tag):
    """A click in the viewport, press and release in separate ticks like a hand click; then the cubes are selected
    again (the click deselects them)."""
    def move():
        ev('MOUSEMOVE', 'NOTHING', x=C["away"][0], y=C["away"][1])
    move.__name__ = f"s_{tag}_away_move"
    step(move)

    def press():
        ev('LEFTMOUSE', 'PRESS', x=C["away"][0], y=C["away"][1])
    press.__name__ = f"s_{tag}_away_press"
    step(press)

    def release():
        ev('LEFTMOUSE', 'RELEASE', x=C["away"][0], y=C["away"][1])
    release.__name__ = f"s_{tag}_away_release"
    step(release)


def values_are(label, lead, other):
    a, b = cubes()
    ok = all(abs(x - y) < 1e-3 for x, y in zip(degrees(a) + degrees(b), lead + other))
    check(f"{label} (Cube {degrees(a)}, Cube2 {degrees(b)})", ok)


def reselect():
    a, b = cubes()
    for o in bpy.context.view_layer.objects:
        o.select_set(o in (a, b))
    bpy.context.view_layer.objects.active = a
    redraw()


# 1. the editor shows the last value; a click away writes nothing
value_drag("away")


@step
def s_prefilled():
    text = bpy.context.scene.allset_cb.entry_text
    check(f"after the drag the editor shows Rotate Z's value ({text!r}, field {C['rz_text']!r})", text == C["rz_text"])


click_away("away")


@step
def s_away_check():
    values_are("a click away from the unchanged editor changes no value", LEAD, OTHER)
    reselect()


# 2. Esc writes nothing
value_drag("esc")


@step
def s_esc():
    ev('ESC', 'PRESS')


@step
def s_esc_release():
    ev('ESC', 'RELEASE')


@step
def s_esc_check():
    values_are("Esc in the editor changes no value", LEAD, OTHER)


# 3. Enter writes the shown value into every selected channel of both cubes
value_drag("enter")


@step
def s_enter():
    ev('RET', 'PRESS')


@step
def s_enter_release():
    ev('RET', 'RELEASE')


@step
def s_enter_check():
    values_are("Enter on the unchanged editor writes Rotate Z's value into Rotate X / Y / Z of both cubes",
               (30.0, 30.0, 30.0), (30.0, 30.0, 30.0))
    reset()


# 4. a typed value and a click away: written
value_drag("typed")


@step
def s_type():
    ev('A', 'PRESS', ctrl=True)
    ev('A', 'RELEASE', ctrl=True)
    ev('TEXTINPUT', 'PRESS', unicode="4")
    ev('TEXTINPUT', 'PRESS', unicode="5")


click_away("typed")


@step
def s_typed_check():
    values_are("a typed 45 and a click away writes 45 into Rotate X / Y / Z of both cubes",
               (45.0, 45.0, 45.0), (45.0, 45.0, 45.0))
    reset()


# 5. one click on a value, then a click away: nothing changes (also not the other cube's value)
@step
def s_one_hover():
    x, y = C["ry"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_one_hover2():
    x, y = C["ry"]
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


@step
def s_one_press():
    x, y = C["ry"]
    ev('LEFTMOUSE', 'PRESS', x=x + 1, y=y)


@step
def s_one_release():
    x, y = C["ry"]
    ev('LEFTMOUSE', 'RELEASE', x=x + 1, y=y)


@step
def s_one_prefilled():
    text = bpy.context.scene.allset_cb.entry_text
    check(f"a click on Rotate Y edits its value ({text!r}, field {C['ry_text']!r})", text == C["ry_text"])


click_away("one")


@step
def s_one_check():
    values_are("a click on one value and a click away changes no value", LEAD, OTHER)


run()
