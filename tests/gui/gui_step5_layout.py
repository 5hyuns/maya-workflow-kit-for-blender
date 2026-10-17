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
    # Maya General (step 49): Tool Box | Outliner | view (+ sidebar dock), full-width strip and timeline
    check("workspace General", win().workspace.name == "General")
    views = sorted(areas('VIEW_3D'), key=lambda a: -a.width * a.height)
    v3d, column = views[0], views[-1]
    outl = areas('OUTLINER')[0]
    time = areas('DOPESHEET_EDITOR')[0]
    check("Tool Box column, then Outliner, left of the viewport",
          len(views) == 2 and column.x < outl.x and outl.x + outl.width <= v3d.x + 2)
    check("no Properties column (AE = the sidebar dock)", not areas('PROPERTIES'))
    check("timeline across the bottom", time.y < v3d.y and time.width >= win().width - 4)   # 5.x: 2 px edge
    check("Outliner about 16% of the width", 0.10 < outl.width / win().width < 0.22)
    check("viewport sidebar shown (Channel Box host)", v3d.spaces.active.show_region_ui)
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_step5_layout.png"))
    bpy.ops.mesh.primitive_cube_add()


@step
def s_object():
    v3d = max(areas('VIEW_3D'), key=lambda a: a.width * a.height)
    ui = next(r for r in v3d.regions if r.type == 'UI')
    check("sidebar dock on the Channel Box tab with an object", ui.active_panel_category == "Channel Box")
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_step5_object.png"))
    bpy.ops.maya_kit.theme_restore()
    bpy.ops.maya_kit.layout_remove()


run()
