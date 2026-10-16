"""Step 5 in a real UI: Maya layout template + Maya theme, area placement, screenshots."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, step, setup, screenshot, win  # noqa: E402

SHOTS = os.environ.get("MAYA_KIT_GUI_SHOTS", "")


def areas(t):
    return [a for a in win().screen.areas if a.type == t]


@step
def s_setup():
    setup()
    check("install layout", bpy.ops.maya_kit.layout_install() == {'FINISHED'})
    check("apply theme", bpy.ops.maya_kit.theme_apply() == {'FINISHED'})
    bpy.ops.wm.read_homefile(app_template="MayaKit")


@step
def s_wait():
    pass


@step
def s_layout():
    check("workspace General", win().workspace.name == "General")
    v3d = areas('VIEW_3D')[0]
    outl = sorted(areas('OUTLINER'), key=lambda a: a.x)
    props = areas('PROPERTIES')[0]
    time = areas('DOPESHEET_EDITOR')[0]
    left, layer = outl[0], outl[-1]
    check("Outliner left of the viewport", left.x + left.width <= v3d.x + 2)
    check("Properties (AE) right of the viewport", props.x >= v3d.x + v3d.width - 2)
    check("Layer Editor above Properties, same column",
          abs(layer.x - props.x) <= 2 and layer.y > props.y)
    check("Layer Editor shows collections only", not layer.spaces.active.use_filter_object)
    check("timeline across the bottom", time.y < v3d.y and time.width >= v3d.width)
    check("Outliner about 16% of the width", 0.10 < left.width / win().width < 0.22)
    check("viewport sidebar shown (Channel Box host)", v3d.spaces.active.show_region_ui)
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_step5_layout.png"))
    bpy.ops.mesh.primitive_cube_add()


@step
def s_object():
    props = areas('PROPERTIES')[0]
    check("Properties switches to the Object tab with an object", props.spaces.active.context == 'OBJECT')
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_step5_object.png"))
    bpy.ops.maya_kit.theme_restore()
    bpy.ops.maya_kit.layout_remove()


run()
