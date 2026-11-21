"""#437: hiding the Tool Box (Windows > UI Elements > Tool Box, the Preferences UI Elements page, the hotbox) closes
the Maya layout's Tool Box column instead of leaving Blender's toolbar in it; showing it docks the column back left
of the Outliner. The main viewport's own toolbar stays hidden both ways. In Blender's own layouts (no column) the
toggle shows / hides the main viewport's toolbar."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, win  # noqa: E402


C = {}


def mod(name):
    return import_module(MODULE + name)


def column():
    return mod(".ui.toolbox_layouts").toolbox_area(win().screen)


def main_toolbar():
    view, _r = mod(".ui.status_line").main_view3d(win().screen)
    return view.spaces.active.show_region_toolbar


def outliner():
    return next((a for a in win().screen.areas if a.type == 'OUTLINER'), None)


def toggle():
    with bpy.context.temp_override(window=win()):
        return bpy.ops.allset.toolbox_toggle()


def shown():
    return mod(".ui.toolbox_layouts").toolbox_shown(win().screen)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_layout():
    check("the Maya layout has the Tool Box column", column() is not None and shown())
    check("the main viewport's own toolbar is hidden", not main_toolbar())
    C["outliner_x"] = outliner().x
    check("Preferences UI Elements row reads on", mod(".ui.maya_prefs").OP_STATES["allset.toolbox_toggle"](bpy.context))
    toggle()





@step
def s_hidden():
    check("Tool Box off: the column is closed", column() is None and not shown())
    check("Tool Box off: no Blender toolbar in the main viewport instead", not main_toolbar())
    out = outliner()
    check(f"the Outliner took the column's place (x {out.x} <= {C['outliner_x']})", out.x < C["outliner_x"])
    check("Preferences UI Elements row reads off",
          not mod(".ui.maya_prefs").OP_STATES["allset.toolbox_toggle"](bpy.context))
    toggle()


@step
def s_back():
    col = column()
    check("Tool Box on: the column is back", col is not None and shown())
    out = outliner()
    check(f"it sits left of the Outliner ({col.x}+{col.width} vs {out.x})", abs(col.x + col.width - out.x) <= 8)
    want = mod(".ui.toolbox_column").column_width(bpy.context)
    check(f"it is at least one toolbar column wide ({col.width} >= {want})", col.width >= want)
    region = next(r for r in col.regions if r.type == 'TOOLS')
    check(f"its toolbar shows ({region.width} px)", region.width > 0)
    check("the main viewport's own toolbar is still hidden", not main_toolbar())
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.hb_ui(element='TOOLBOX')        # hotbox East zone: UI Elements > Tool Box


@step
def s_hotbox():
    check("the hotbox Tool Box item closes the column too", column() is None)
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.quick_layout(layout='FOUR')


@step
def s_four_wait():
    pass


@step
def s_four():
    check("four view: still no column", column() is None)
    toggle()


@step
def s_four_wait2():
    pass


@step
def s_four_wait3():
    pass


@step
def s_four_back():
    col = column()
    check("four view: the column comes back", col is not None)
    views = [a for a in win().screen.areas if a.type == 'VIEW_3D' and a != col]
    check(f"four view: still four panels ({len(views)})", len(views) == 4)
    toggle()


@step
def s_four_wait4():
    pass


@step
def s_four_hidden():
    check("four view: the column closes again", column() is None)
    views = [a for a in win().screen.areas if a.type == 'VIEW_3D']
    check(f"four view: four panels stay ({len(views)})", len(views) == 4)


@step
def s_blender_layout():
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.maya_workspace(name="Modeling - Expert")


@step
def s_blender_toggle():
    check("Blender layout: no column, not a kit layout",
          column() is None and not mod(".ui.toolbox_layouts").kit_layout(win().screen))
    C["before"] = main_toolbar()
    toggle()


@step
def s_blender_after():
    check(f"Blender layout: the main viewport's toolbar flips ({C['before']} -> {main_toolbar()})",
          main_toolbar() != C["before"])
    check("Blender layout: no column was added", column() is None)


run()
