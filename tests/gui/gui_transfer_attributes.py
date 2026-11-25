"""In a real UI: a sphere and a hard-edged cube selected (cube last) -> Mesh > Transfer Attributes option box opens the
Transfer Attributes Options window (screenshot); the menu item with Vertex normal On gives the cube the sphere's
normals through a live Data Transfer modifier (#554)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


@step
def s_setup():
    C["x"], C["y"] = setup()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, 0))
        bpy.ops.object.shade_smooth()
    src = bpy.context.active_object
    cube = bpy.data.objects["Cube"]
    cube.scale = (0.7, 0.7, 0.7)
    for ob in bpy.context.view_layer.objects:
        ob.select_set(ob in (src, cube))
    bpy.context.view_layer.objects.active = cube
    C["src"], C["cube"] = src.name, cube.name


@step
def s_option_box():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["box"] = bpy.ops.allset.menu_option_box('INVOKE_DEFAULT', item="Mesh/Transfer Attributes")


@step
def s_shot():
    if SHOTS:
        with bpy.context.temp_override(window=win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "gui_transfer_attributes_options.png"))
    check(f"the option box opens the options window ({C.get('box')})", C.get("box") in ({'FINISHED'},
                                                                                      {'RUNNING_MODAL'}))


@step
def s_close_and_run():
    import sim
    sim.tap('ESC')
    cube = bpy.data.objects[C["cube"]]
    cube.modifiers.clear()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["run"] = bpy.ops.allset.transfer_attributes(normals='ON', uv_sets='OFF', color_sets='OFF')


@step
def s_check():
    cube = bpy.data.objects[C["cube"]]
    mods = [(m.type, getattr(m, "object", None) and m.object.name) for m in cube.modifiers]
    me = cube.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    per_vertex = {}
    for loop, n in zip(me.loops, me.corner_normals):
        per_vertex.setdefault(loop.vertex_index, []).append(n.vector.copy())
    smooth = all(n.angle(ns[0]) < 1e-3 for ns in per_vertex.values() for n in ns)
    check(f"Transfer Attributes adds a live Data Transfer from the sphere ({C.get('run')}, {mods})",
          mods == [('DATA_TRANSFER', C["src"])])
    check("the cube takes one normal per vertex (smooth like the sphere)", smooth)
    if SHOTS:
        with bpy.context.temp_override(window=win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, "gui_transfer_attributes_result.png"))


run()
