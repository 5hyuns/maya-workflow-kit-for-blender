"""Outliner selection in the Maya layout (#230): Shift+click = range, real Ctrl+click toggles, like Maya's
Outliner (the factory-screen version is in gui_step170_select_mods)."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

C = {}
KEYS = {"ctrl": "LEFT_CTRL", "shift": "LEFT_SHIFT"}


def area():
    return C["area"]


def region():
    return next(r for r in area().regions if r.type == 'WINDOW')


def wait(n=12):
    for _ in range(n):
        step(lambda: None)


def click(xy, *mods):
    wait()

    def s1():
        ev('MOUSEMOVE', 'NOTHING', x=xy()[0], y=xy()[1])
        for m in mods:
            ev(KEYS[m], 'PRESS', x=xy()[0], y=xy()[1], **{m: True})

    def s2():
        x, y = xy()
        kw = {m: True for m in mods}
        ev('LEFTMOUSE', 'PRESS', x=x, y=y, **kw)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y, **kw)

    def s3():
        for m in mods:
            ev(KEYS[m], 'RELEASE', x=xy()[0], y=xy()[1])
    step(s1)
    step(s2)
    step(s3)
    wait(2)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_outliner():
    for name in ("pA1", "pA2", "pA3", "pA4"):
        ob = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.children[0].objects.link(ob) if len(bpy.context.scene.collection.children)             else bpy.context.scene.collection.objects.link(ob)
    for o in bpy.context.view_layer.objects:
        if o is not None:
            o.select_set(False)
    C["area"] = max((a for a in win().screen.areas if a.type == 'OUTLINER'), key=lambda a: a.height)


@step
def s_rows():
    r = region()
    s = bpy.context.preferences.system.ui_scale
    C["row"] = round(20 * s)
    C["rows"] = {}
    C["probe"] = [r.y + r.height - int(C["row"] * (i + 0.5)) for i in range(16)]


def probe(i):
    def s_click():
        r = region()
        y = C["probe"][i]
        ev('MOUSEMOVE', 'NOTHING', x=r.x + int(r.width * 0.35), y=y)
        ev('LEFTMOUSE', 'PRESS', x=r.x + int(r.width * 0.35), y=y)
        ev('LEFTMOUSE', 'RELEASE', x=r.x + int(r.width * 0.35), y=y)

    def s_look():
        sel = [o.name for o in bpy.context.view_layer.objects if o is not None and o.select_get()]
        if len(sel) == 1 and sel[0] not in C["rows"]:
            C["rows"][sel[0]] = C["probe"][i]
    step(s_click)
    step(s_look)


for _i in range(16):
    probe(_i)


def row(name):
    def xy():
        r = region()
        return r.x + int(r.width * 0.35), C["rows"].get(name, r.y)
    return xy


def selected():
    return sorted(o.name for o in bpy.context.view_layer.objects if o is not None and o.select_get())


@step
def s_rows_found():
    check(f"Outliner rows found ({sorted(C['rows'])})", all(n in C["rows"] for n in ("pA1", "pA2", "pA3", "pA4")))


click(row("pA1"))
click(row("pA3"), "shift")


@step
def s_range():
    check(f"Shift+click = range pA1..pA3 (Maya Outliner) ({selected()})", selected() == ["pA1", "pA2", "pA3"])



click(row("pA2"), "ctrl")


@step
def s_toggle():
    check(f"Ctrl+click toggles pA2 off ({selected()})", selected() == ["pA1", "pA3"])


click(row("pA4"), "ctrl")


@step
def s_toggle_on():
    check(f"Ctrl+click adds pA4 ({selected()})", selected() == ["pA1", "pA3", "pA4"])


run()
