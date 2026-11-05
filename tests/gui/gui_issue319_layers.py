"""In a real UI: the display layer row's RMB menu (Maya: Add Selected Objects / Remove Selected Objects / Select
Objects / Delete Layer on a layer row).

Maya Workflow Kit layout, pCube1 in layer1 (Create Layer from Selected), pCube2 selected. RMB on layer1's V box
in the Layer Editor opens the menu (Blender's own items first, then the layer items); the menu opens with
Add Selected Objects under the mouse, Enter runs it -> pCube2 joins layer1.
Shot ``gui_issue319_layer_menu.png`` with ``--shots``."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import (MODULE, check, dock_area, dock_region, ev, find_button, load_maya_layout, run,  # noqa: E402
                 setup, step, view3d, win)

GUI_TIMEOUT = 200
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def le():
    return import_module(f"{MODULE}.ui.layer_editor")


def dock():
    return dock_area(), dock_region()


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, reg = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=reg, space_data=area.spaces.active):
        bpy.ops.allset.create(kind='CUBE')
        bpy.ops.allset.create(kind='CUBE')
    sc = bpy.context.scene
    a, b = bpy.data.objects["pCube1"], bpy.data.objects["pCube2"]
    for o in sc.objects:
        o.select_set(o == a)
    bpy.context.view_layer.objects.active = a
    bpy.context.window_manager.allset_le_tab = 'DISPLAY'
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.layer_new(selected=True)
    a.select_set(False)
    b.select_set(True)
    bpy.context.view_layer.objects.active = b
    C["layer"] = le().layer_of(a, sc)
    check(f"layer made with pCube1 ({C['layer']})", C["layer"] is not None)
    redraw()


@step
def s_wait():
    redraw()


step(find_button(dock, lambda _p, c: "layer_toggle" in c, C, "row", x_frac=0.1, step_px=4, start_frac=0.3))


@step
def s_hover():
    check(f"layer row V box found ({C.get('row')})", C.get("row") is not None)
    if C.get("row"):
        ev('MOUSEMOVE', 'NOTHING', x=C["row"][0], y=C["row"][1])


@step
def s_rmb():
    if C.get("row"):
        ev('RIGHTMOUSE', 'PRESS')


@step
def s_rmb_up():
    if C.get("row"):
        ev('RIGHTMOUSE', 'RELEASE')


@step
def s_menu_shot():
    if SHOTS:
        with bpy.context.temp_override(window=win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "gui_issue319_layer_menu.png"))


@step
def s_enter():
    if C.get("row"):
        ev('RET', 'PRESS')
        ev('RET', 'RELEASE')


@step
def s_check():
    b = bpy.data.objects["pCube2"]
    layer = le().layer_of(b, bpy.context.scene)
    name = layer.name if layer is not None else None
    want = C["layer"].name if C.get("layer") is not None else "?"
    check(f"RMB on the layer row > Add Selected Objects puts pCube2 in {want} (got {name})", name == want)


run()
