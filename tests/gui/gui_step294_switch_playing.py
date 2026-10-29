"""Switching Maya / Blender while the animation plays (#218): playback stops, and W / E / R / Q pick the Maya tools
afterwards. The Maya button while Maya mode is already on opens the Maya layout."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d, win  # noqa: E402

C = {}


def switch():
    return import_module(MODULE + ".switch")


def playing():
    return any(w.screen.is_animation_playing for w in bpy.context.window_manager.windows)


def tool():
    return bpy.context.workspace.tools.from_space_view3d_mode('OBJECT', create=False).idname


def play():
    with bpy.context.temp_override(window=win(), screen=win().screen):
        bpy.ops.screen.animation_play()


def key(k):
    _area, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    ev(k, 'PRESS')
    ev(k, 'RELEASE')


@step
def s_setup():
    C["xy"] = setup()
    bpy.context.scene.frame_end = 100000
    switch().request(False)


@step
def s_wait0():
    pass


@step
def s_blender_play():
    check("Blender mode", not switch().is_on())
    play()


@step
def s_switch_while_playing():
    check("playing in Blender mode", playing())
    switch().request(True, layout=False)


@step
def s_wait():
    pass


@step
def s_after():
    check("switching to Maya mode stopped playback", not playing())
    key('W')


@step
def s_w():
    check(f"W picks the Move tool after the switch ({tool()})", tool() == "builtin.move")
    key('E')


@step
def s_e():
    check(f"E picks the Rotate tool ({tool()})", tool() == "builtin.rotate")
    play()


@step
def s_back_while_playing():
    check("playing in Maya mode", playing())
    switch().request(False)


@step
def s_wait2():
    pass


@step
def s_back():
    check("switching to Blender mode stopped playback", not playing())
    switch().request(True, layout=False)


@step
def s_wait3():
    pass


@step
def s_maya_again():
    C["ws"] = win().workspace.name
    switch().request(True)          # the Maya button while Maya mode is on


@step
def s_wait4():
    pass


@step
def s_layout():
    sw = switch()
    check(f"the Maya button with Maya mode on opens the Maya layout ({C['ws']} -> {win().workspace.name})",
          sw.is_maya_workspace(win().workspace))


run()
