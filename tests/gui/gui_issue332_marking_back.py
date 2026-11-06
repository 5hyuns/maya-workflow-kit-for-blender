"""#332: a radial submenu of a marking menu gives the menu it opened from back. RMB held on the cube, drag onto
UV (its submenu opens in place), drag back toward the press point: the object menu is there again, drag west =
Vertex. Click mode: RMB click, onto UV (submenu), back inside the ring, click Face. Esc with the submenu open
closes only the submenu; Esc at the top menu closes it."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap  # noqa: E402

C = {}


def draw():
    return import_module(MODULE + ".marking.draw")


def session():
    return draw().ACTIVE.get("session")


def box_center(s, key, level=-1):
    """Window point in the middle of the radial box ``key`` of the menu at stack ``level``."""
    lay, (cx, cy) = s.stack[level]
    it = lay.radial[key]
    ox, oy = draw().ACTIVE["origin"]
    return (ox + round(cx + (it.rect[0] + it.rect[2]) / 2), oy + round(cy + (it.rect[1] + it.rect[3]) / 2))


def label(s):
    it = s.hover[0] if s is not None else None
    return it.label if it is not None else None


def path(a, b, n):
    return [(round(a[0] + (b[0] - a[0]) * k / n), round(a[1] + (b[1] - a[1]) * k / n)) for k in range(1, n + 1)]


def mover(key):
    """One MOUSEMOVE per tick along C[key]."""
    def fn():
        pts = C.get(key) or []
        if not pts:
            return
        x, y = pts.pop(0)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        if pts:
            import sim
            sim._steps.insert(0, fn)
    return fn


def to_object_mode():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def press_point():
    return C["x"], C["y"]


# --- press mode ----------------------------------------------------------------------------------------------

@step
def s_setup():
    C["x"], C["y"] = setup()
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = None
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"])     # over the cube (factory scene, centred)


@step
def s_plan_east():
    s = session()
    check("press: RMB on the cube opens the object marking menu", s is not None)
    C["east"] = path(press_point(), box_center(s, "E"), 4) if s is not None else []


step(mover("east"))


@step
def s_sub_open():
    s = session()
    ok = s is not None and len(s.stack) == 2
    check("press: dragging onto UV opens its submenu in place", ok)
    if ok:
        labels = sorted(it.label for it in s.layout.items)
        check(f"press: the submenu shows UV / UV Shell ({labels})", labels == ["UV", "UV Shell"])
    start = C["east"][-1] if C.get("east") else press_point()
    C["back"] = path(start, (C["x"] + 25, C["y"]), 5)


step(mover("back"))


@step
def s_back():
    s = session()
    check("press: dragging back inside the ring closes the submenu and the object menu stays open",
          s is not None and len(s.stack) == 1)
    check(f"press: its UV box is hovered again ({label(s)})", label(s) == "UV")
    C["west"] = path((C["x"] + 25, C["y"]), (C["x"] - 120, C["y"]), 4)


step(mover("west"))


@step
def s_west():
    s = session()
    check(f"press: dragging on west hovers Vertex ({label(s)})", label(s) == "Vertex")
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"] - 120, y=C["y"])


@step
def s_vertex():
    ts = bpy.context.scene.tool_settings
    check("press: release runs Vertex (component mode, vertices) and the menu closes",
          bpy.context.mode == 'EDIT_MESH' and tuple(ts.mesh_select_mode) == (True, False, False)
          and not draw().ACTIVE)
    to_object_mode()
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])


# --- click mode ----------------------------------------------------------------------------------------------

@step
def s_click():
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"], y=C["y"])     # a quick click (same tick): the menu stays open


@step
def s_click_plan():
    s = session()
    check("click: an RMB click keeps the object menu open", s is not None and s.mode == "CLICK")
    C["ceast"] = path(press_point(), box_center(s, "E"), 3) if s is not None else []


step(mover("ceast"))


@step
def s_click_sub():
    s = session()
    check("click: moving onto UV opens its submenu", s is not None and len(s.stack) == 2)
    start = C["ceast"][-1] if C.get("ceast") else press_point()
    C["cback"] = path(start, (C["x"] + 25, C["y"]), 4)


step(mover("cback"))


@step
def s_click_back():
    s = session()
    check("click: moving back inside the ring shows the object menu again, still open",
          s is not None and len(s.stack) == 1)
    C["south"] = path((C["x"] + 25, C["y"]), box_center(s, "S"), 3) if s is not None else []


step(mover("south"))


@step
def s_click_face():
    s = session()
    check(f"click: Face is hovered ({label(s)})", label(s) == "Face")
    ev('LEFTMOUSE', 'PRESS')


@step
def s_click_face_release():
    ev('LEFTMOUSE', 'RELEASE')


@step
def s_face():
    ts = bpy.context.scene.tool_settings
    check("click: clicking Face runs it (component mode, faces) and closes the menu",
          bpy.context.mode == 'EDIT_MESH' and tuple(ts.mesh_select_mode) == (False, False, True)
          and not draw().ACTIVE)
    to_object_mode()
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])


# --- Esc -----------------------------------------------------------------------------------------------------

@step
def s_esc_press():
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"])


@step
def s_esc_plan():
    s = session()
    C["eeast"] = path(press_point(), box_center(s, "E"), 3) if s is not None else []


step(mover("eeast"))


@step
def s_esc():
    s = session()
    check("esc: the UV submenu is open", s is not None and len(s.stack) == 2)
    tap('ESC')


@step
def s_esc_once():
    s = session()
    check("esc: Esc closes only the submenu, the object menu stays open", s is not None and len(s.stack) == 1)
    tap('ESC')


@step
def s_esc_twice():
    check("esc: Esc at the top menu closes it", not draw().ACTIVE)
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"], y=C["y"])


run()
