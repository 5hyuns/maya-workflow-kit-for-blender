"""#414 in a real UI: a quick RMB click in the centre keeps the marking menu open (click mode) also when the press
and the release both come in during a slow viewport frame. A draw handler makes one frame take a while and, during
that frame, queues the press and the release, the way the window system's events wait while Blender draws; the next
steps read the marking menu. A frame of 0 s (both queued from a timer step) is the control."""

import os
import sys
import time
from importlib import import_module

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, view3d, win  # noqa: E402

FRAMES = (0.0, 0.10, 0.20, 0.30, 0.40, 0.60)
C = {"slow": None, "handler": None}


def draw():
    return import_module(MODULE + ".marking.draw")


def _slow_frame():
    t = C["slow"]
    if t is None:
        return
    C["slow"] = None
    time.sleep(t)
    x, y = C["xy"]
    w = win()
    w.event_simulate(type='RIGHTMOUSE', value='PRESS', x=x, y=y)
    w.event_simulate(type='RIGHTMOUSE', value='RELEASE', x=x, y=y)


@step
def s_setup():
    setup()
    cube = bpy.data.objects["Cube"]
    _area, region = view3d()
    p = location_3d_to_region_2d(region, region.data, cube.location)
    C["xy"] = (region.x + int(p.x), region.y + int(p.y))
    C["handler"] = bpy.types.SpaceView3D.draw_handler_add(_slow_frame, (), 'WINDOW', 'POST_PIXEL')
    ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])


def _trial(frame):
    def click():
        if frame == 0.0:
            x, y = C["xy"]
            ev('RIGHTMOUSE', 'PRESS', x=x, y=y)
            ev('RIGHTMOUSE', 'RELEASE', x=x, y=y)
        else:
            C["slow"] = frame
            for a in win().screen.areas:
                a.tag_redraw()

    def wait():
        pass

    def read():
        s = draw().ACTIVE.get("session")
        check(f"a quick click during a {frame:.2f} s frame keeps the menu open (click mode)",
              s is not None and s.mode == "CLICK")
        if s is not None:
            ev('ESC', 'PRESS', x=C["xy"][0], y=C["xy"][1])
            ev('ESC', 'RELEASE', x=C["xy"][0], y=C["xy"][1])

    step(click)
    step(wait)
    step(wait)
    step(read)
    step(wait)


for _f in FRAMES:
    _trial(_f)


@step
def s_done():
    if C["handler"] is not None:
        bpy.types.SpaceView3D.draw_handler_remove(C["handler"], 'WINDOW')
        C["handler"] = None


run()
