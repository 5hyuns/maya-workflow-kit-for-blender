"""In a real UI: cube -> UV > UV Editor -> every UV selected -> UV Editor > Image > Measure Pixel Distance opens the
Pixel Distance window (map sizes 4096 down to 128 with U Distance, V Distance and Distance in pixels; screenshot)."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def cube():
    return bpy.data.objects["Cube"]


def uv_window():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.ui_type == 'UV':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


@step
def s_setup():
    C["x"], C["y"] = setup()
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    area, region = view3d()
    menu_map = mod(".ui.menu_map")
    modal = mod(".marking.modal")
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["open"] = modal.run_action(bpy.context, menu_map.MAP["UV/UV Editor"])


@step
def s_wait_uv_window():
    import sim
    C.setdefault("wait_uv", 0)
    if uv_window()[1] is None and C["wait_uv"] < 15:
        C["wait_uv"] += 1
        sim._steps.insert(0, s_wait_uv_window)


@step
def s_measure():
    w, a, r = uv_window()
    check(f"a UV Editor window opens ({C['open']})", a is not None)
    if a is None:
        return
    b = bmesh.from_edit_mesh(cube().data)
    for el in (*b.verts, *b.edges, *b.faces):
        el.select = True
    bmesh.update_edit_mesh(cube().data)
    C["box"] = mod(".operators.uv_toolkit_ops").selected_box(bpy.context)
    menu_map = mod(".ui.menu_map")
    modal = mod(".marking.modal")
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
        C["run"] = modal.run_action(bpy.context, menu_map.MAP["UV Editor/Image/Measure Pixel Distance"])


@step
def s_shot():
    w, _a, _r = uv_window()
    if SHOTS and w is not None:
        with bpy.context.temp_override(window=w):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "gui_uv_measure_pixel_distance.png"))
    box = C.get("box")
    check(f"the menu item runs the Pixel Distance window on the selected UVs' box ({C.get('run')}, {box})",
          C.get("run") is not False and box is not None and box[0] > 0 and box[1] > 0)


run()
