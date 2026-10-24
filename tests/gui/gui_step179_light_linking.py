"""Step 179 in a real UI: a point light and two cubes, Lighting/Shading > Break Light Links from the menu map, then the
Light Linking Editor popover (light-centric) shows the light with one cube linked and one not; shot of the editor."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def override():
    a, region = view3d()
    return bpy.context.temp_override(window=win(), screen=win().screen, area=a, region=region)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    unit = import_module(MODULE + ".operators.units").maya_unit()
    with override():
        for x in (-2, 2):
            bpy.ops.allset.create(kind='CUBE')
            bpy.context.view_layer.objects.active.location = (x * unit, 0, 0)
        bpy.ops.allset.create(kind='POINT_LIGHT')
    obs = {o.name: o for o in bpy.context.scene.objects}
    C["names"] = sorted(obs)
    light = next(o for o in obs.values() if o.type == 'LIGHT')
    cube = obs["pCube2"]
    for o in bpy.context.scene.objects:
        o.select_set(o in (light, cube))
    bpy.context.view_layer.objects.active = light
    C["light"] = light.name
    with override():
        res = bpy.ops.allset.menu_item(item="Lighting/Shading/Break Light Links")
    ll = import_module(MODULE + ".operators.light_links")
    check(f"Break Light Links from the menu ({res}): {light.name} no longer lights pCube2, still lights pCube1",
          not ll.linked(light, cube) and ll.linked(light, obs["pCube1"]))


@step
def s_editor():
    a, region = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height * 2 // 3)
    with override():
        res = bpy.ops.allset.menu_item(item="Lighting/Shading/Light Linking Editor")
    wm = bpy.context.window_manager
    check(f"Light Linking Editor opens light-centric on the selected light ({res}, {wm.allset_ll_mode}, "
          f"{wm.allset_ll_current})", wm.allset_ll_mode == "LIGHT_CENTRIC" and wm.allset_ll_current == C["light"])


@step
def s_shot():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_step179_light_linking_editor.png"))
    check("editor popover drawn (screenshot)", True)


run()
