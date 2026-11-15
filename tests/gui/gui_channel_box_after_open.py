# SPDX-License-Identifier: GPL-3.0-or-later
"""The Channel Box keeps following the lead's values after File > Open and after a new scene in the Maya layout: its
value poll (the timer that redraws the dock when the lead's translate / rotate / scale change, also while a move
runs) still runs in the newly loaded file, so a lead moved there is seen within a few ticks."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

OTHER = os.path.join(bpy.app.tempdir or os.environ.get("TEMP", "."), "gui_channel_box_after_open.blend")


def cb():
    return import_module(MODULE + ".ui.channel_box")


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def lead(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        me = bpy.data.meshes.new(name)
        me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [], [(0, 1, 2)])
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
    for other in bpy.context.view_layer.objects:
        other.select_set(other == ob)
    bpy.context.view_layer.objects.active = ob
    return ob


def followed(label, ob, where):
    snap = cb()._transform_snapshot
    registered = bpy.app.timers.is_registered(cb()._poll_transform_values)
    seen = snap is not None and snap[0] == ob.as_pointer() and snap[1] == tuple(where)
    check(f"{label}: the Channel Box value poll runs (registered {registered}) and saw the lead move to {where} "
          f"(saw {snap[1] if snap else None})", registered and seen)


def idle():
    """One step for the poll: it runs at least once between the step before and the step after this one."""


@step
def s_setup():
    setup()
    with override():
        bpy.ops.wm.save_as_mainfile(filepath=OTHER, copy=True)
    lead("Cube").location = (0.5, 0.5, 0.5)


step(idle)


@step
def s_before():
    followed("before any file load", bpy.data.objects["Cube"], (0.5, 0.5, 0.5))


@step
def s_open():
    with override():
        bpy.ops.wm.open_mainfile(filepath=OTHER)


@step
def s_move_after_open():
    lead("Cube").location = (1.5, 2.5, 0.5)


step(idle)


@step
def s_after_open():
    followed("after File > Open", bpy.data.objects["Cube"], (1.5, 2.5, 0.5))


@step
def s_new_scene():
    load_maya_layout()


@step
def s_move_in_new_scene():
    lead("pCube1").location = (0.25, 0.75, 1.25)


step(idle)


@step
def s_after_new_scene():
    followed("after a new scene in the Maya layout", bpy.data.objects["pCube1"], (0.25, 0.75, 1.25))
    try:
        os.remove(OTHER)
    except OSError:
        pass


run()
