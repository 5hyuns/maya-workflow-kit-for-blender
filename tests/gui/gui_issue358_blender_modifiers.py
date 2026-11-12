"""#358: Attribute Editor > Blender Modifiers... opens a floating window with Blender's Properties editor on the
Modifiers tab, pinned to the selected object (its whole modifier stack, Add Modifier included)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

C = {}


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_cube():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.mesh.primitive_cube_add()
        ob = bpy.context.active_object
        ob.modifiers.new("Bevel", 'BEVEL')
        C["ob"] = ob.name
        C["windows"] = len(bpy.context.window_manager.windows)
        C["result"] = bpy.ops.allset.ae_blender_modifiers()


def _idle():
    pass


for _i in range(4):
    step(_idle)


@step
def s_check():
    wm = bpy.context.window_manager
    check(f"the button ran ({C['result']})", C["result"] == {'FINISHED'})
    new = [w for w in wm.windows][C["windows"]:]
    spaces = [a.spaces.active for w in new for a in w.screen.areas if a.type == 'PROPERTIES']
    got = [(sp.context, getattr(sp.pin_id, "name", None), sp.use_pin_id) for sp in spaces]
    check(f"a new window shows the Modifiers tab pinned to the object ({got})",
          (('MODIFIER', C["ob"], True) in got))
    for w in new:
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


run()
