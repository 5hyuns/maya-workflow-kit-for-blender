"""#563: switching between Blender mode and Maya mode changes no object: a cube made in Blender mode and a pCube1
made in Maya mode keep their sizes both ways. Each mode shows its own 3D View, framed for its own lengths (Maya mode:
centimetres, like Maya's new-scene camera; Blender mode: Blender's own view), which is why the same objects look
far bigger or smaller after a switch. Screenshots with ALLSET_GUI_SHOTS."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def sw():
    return import_module(MODULE + ".switch")


def dims():
    return {o.name: tuple(round(v, 6) for v in o.dimensions) for o in bpy.data.objects if o.type == 'MESH'}


def view_distance():
    area, _r = view3d()
    return round(area.spaces.active.region_3d.view_distance, 4)


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def switch(mode):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.switch_mode(mode=mode)


def wait_for(on, name):
    def s_wait():
        import sim
        C.setdefault(name, 0)
        if (sw().is_on() != on or (on and not sw().is_maya_workspace(win().workspace))) and C[name] < 40:
            C[name] += 1
            sim._steps.insert(0, s_wait)
    s_wait.__name__ = name
    step(s_wait)


@step
def s_setup():
    setup()
    load_maya_layout()          # a new Maya scene: lengths shown in cm, one Maya unit = 1 cm


wait_for(True, "w_maya0")


@step
def s_to_blender():
    switch('BLENDER')


wait_for(False, "w_blender0")


@step
def s_add_cube():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.mesh.primitive_cube_add()       # Blender's Add > Mesh > Cube: 2 m


wait_for(False, "w_blender")


@step
def s_blender_cube():
    check("Blender mode", not sw().is_on())
    C["units"] = tuple(getattr(bpy.context.scene.unit_settings, k) for k in ("system", "length_unit", "scale_length"))
    C["dims"] = dims()
    C["blender_view"] = view_distance()
    check(f"Blender's cube is 2 m ({C['dims']})", C["dims"].get("Cube") == (2.0, 2.0, 2.0))
    shot("gui_issue563_1_blender.png")
    switch('MAYA')


wait_for(True, "w_maya")


@step
def s_maya():
    check(f"switching to Maya mode changes no object ({dims()})", dims() == C["dims"])
    units = tuple(getattr(bpy.context.scene.unit_settings, k) for k in ("system", "length_unit", "scale_length"))
    check(f"nor the scene units ({units})", units == C["units"])
    C["maya_view"] = view_distance()
    print("GUI INFO view distance: Blender", C["blender_view"], "Maya", C["maya_view"], flush=True)
    shot("gui_issue563_2_maya.png")
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    C["dims2"] = dims()
    k = import_module(MODULE + ".operators.units").maya_unit(bpy.context.scene)
    check(f"Maya mode's pCube1 is 1 Maya unit ({C['dims2'].get('pCube1')}, unit {k} BU)",
          C["dims2"].get("pCube1") == (round(k, 6),) * 3)


@step
def s_maya_shot():
    shot("gui_issue563_3_maya_pcube.png")
    switch('BLENDER')


wait_for(False, "w_blender2")


@step
def s_blender_again():
    check(f"back in Blender mode: both cubes keep their sizes ({dims()})", dims() == C["dims2"])
    print("GUI INFO view distance back in Blender:", view_distance(), flush=True)
    shot("gui_issue563_4_blender_again.png")


run()
