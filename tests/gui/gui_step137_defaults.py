"""Issue #71, in the Maya Workflow Kit layout: Assign New Material > Blinn shows Maya's Blinn values in the
Attribute Editor (Color 0.5, Incandescence black, Eccentricity 0.3, Specular Roll Off 0.7); a new point light shows
Intensity 1 / Decay Rate No Decay. Screenshots for a visual check."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, screenshot, setup, step, view3d, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def shot(name):
    path = os.path.join(SHOTS or os.path.join(os.environ.get("TEMP", "."), "gui137"), name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    screenshot(path)
    return path


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_blinn():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
        res = bpy.ops.allset.shelf_material(kind='BLINN')
        check(f"Assign New Material > Blinn ({res})", res == {'FINISHED'})
        bpy.ops.allset.material_attributes()
    mat = bpy.context.active_object.active_material
    C["mat"] = mat.name
    check(f"the new material is blinn1 ({mat.name})", mat.name == "blinn1")
    check(f"AE Eccentricity = 0.3 ({mat.allset_eccentricity:.4f})", abs(mat.allset_eccentricity - 0.3) < 1e-4)
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_wait():
    pass


@step
def s_shot_blinn():
    path = shot("gui_step137_blinn_ae.png")
    check(f"Blinn AE screenshot {path}", os.path.exists(path))


@step
def s_light():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='POINT_LIGHT')
    attribute_editor = import_module(MODULE + ".ui.attribute_editor")
    light = bpy.context.active_object.data
    check(f"point light: Intensity 1, No Decay ({light.allset_intensity:.4f}, {light.allset_decay})",
          abs(light.allset_intensity - 1.0) < 1e-4 and light.allset_decay == 'NO_DECAY')
    attribute_editor.show_dock(bpy.context, 'ATTRIBUTE_EDITOR')
    attribute_editor.set_tab(bpy.context, "S")          # pointLightShape1
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_wait2():
    pass


@step
def s_shot_light():
    path = shot("gui_step137_light_ae.png")
    check(f"light AE screenshot {path}", os.path.exists(path))


run()
