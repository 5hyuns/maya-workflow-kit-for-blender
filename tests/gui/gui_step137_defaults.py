"""In the Maya Workflow Kit layout: the shelf's material button makes Blender's new material (Principled BSDF,
named Material) whose Attribute Editor shows the Principled inputs by Blender's names; a new point light has
Blender's power, shown in the Power row. Screenshots for a visual check."""

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
        res = bpy.ops.allset.shelf_material()
        check(f"New Material ({res})", res == {'FINISHED'})
        bpy.ops.allset.material_attributes()
    mat = bpy.context.active_object.active_material
    C["mat"] = mat.name
    check(f"the new material is Blender's Material ({mat.name})", mat.name.startswith("Material"))
    ae = import_module(MODULE + ".ui.attribute_editor")
    tab = next(t for t in ae.tabs(bpy.context.active_object) if t[0] == "MAT:0")
    check(f"AE material tab is a Principled BSDF ({tab})", tab[2] == "Principled BSDF")
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
    ob = bpy.context.active_object
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.light_add(type='POINT')          # Blender's Add > Light > Point
    ref = bpy.context.active_object
    want = ref.data.energy
    bpy.data.objects.remove(ref)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    check(f"point light: Blender's power ({light.energy:.4f} W, Blender {want:.4f})", abs(light.energy - want) < 1e-6)
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
