"""#381 follow-up in a real UI: the Maya Ctrl+Z (Undo) unticked in Preferences > Keymap (the user keymap item's
checkbox) while Blender's own Ctrl+Z is switched off by the Maya keys. In Blender mode Ctrl+Z over the viewport still
undoes (Blender's own key); back in Maya mode the user's untick is kept: Ctrl+Z does nothing, z undoes."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 200
C = {}


def kcs():
    return bpy.context.window_manager.keyconfigs


def screen():
    return kcs().user.keymaps["Screen"]


def kit_ctrl_z():
    addon = kcs().addon.keymaps["Screen"]
    base = next(k for k in addon.keymap_items if k.idname == "ed.undo" and k.type == 'Z' and k.ctrl and not k.shift)
    return screen().keymap_items.find_match(addon, base)


def ctrl_z_items():
    return [(bool(k.active), bool(k.is_user_modified)) for k in screen().keymap_items
            if k.idname == "ed.undo" and k.type == 'Z' and k.ctrl and not k.shift and not k.alt]


def v3d_override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def to_viewport():
    _area, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


def move_cube():
    """An undo step that moves the cube by 2 (returns the x before)."""
    obj = bpy.data.objects[C["cube"]]
    x0 = obj.location.x
    obj.location.x += 2.0
    with v3d_override():
        bpy.ops.ed.undo_push(message="Move")
    return x0


def cube_x():
    obj = bpy.data.objects.get(C["cube"])
    return obj.location.x if obj is not None else float("nan")      # gone: undone past its creation


def switch(on):
    import_module(MODULE + ".switch").set_mode(on, layout=False)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    with v3d_override():
        bpy.ops.allset.create(kind='CUBE')
        bpy.ops.ed.undo_push(message="Cube")      # an undo below the moves keeps the cube
    C["cube"] = bpy.context.active_object.name
    to_viewport()


@step
def s_untick():
    item = kit_ctrl_z()
    check(f"Maya mode: the Maya Ctrl+Z is on, Blender's own is off ({ctrl_z_items()})",
          item is not None and item.active and ctrl_z_items().count((True, False)) == 1)
    if item is not None:
        item.active = False                  # the Preferences > Keymap checkbox of that item
    kcs().update()


@step
def s_blender_mode():
    check(f"the unticked Maya Ctrl+Z does nothing in Maya mode ({ctrl_z_items()})",
          True not in [a for a, _m in ctrl_z_items()])
    switch(False)


@step
def s_blender_ctrl_z():
    check(f"Blender mode: Blender's own Ctrl+Z is on and unedited ({ctrl_z_items()})",
          ctrl_z_items() == [(True, False)])
    to_viewport()
    C["x0"] = move_cube()
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_blender_ctrl_z_done():
    check(f"Blender mode: Ctrl+Z over the viewport undoes (x {C['x0']} -> {cube_x()})", abs(cube_x() - C["x0"]) < 1e-4)
    switch(True)


@step
def s_maya_again():
    to_viewport()
    C["x1"] = move_cube()
    ev('Z', 'PRESS', ctrl=True)
    ev('Z', 'RELEASE', ctrl=True)


@step
def s_maya_ctrl_z_done():
    check(f"Maya mode again: the user's untick is kept, Ctrl+Z does nothing (x {C['x1']} + 2 -> {cube_x()})",
          abs(cube_x() - (C["x1"] + 2.0)) < 1e-4)
    ev('Z', 'PRESS')
    ev('Z', 'RELEASE')


@step
def s_maya_z_done():
    check(f"Maya mode again: z undoes (x -> {cube_x()})", abs(cube_x() - C["x1"]) < 1e-4)
    screen().restore_to_default()
    kcs().update()


run()
