"""#447: Status Line off (Windows > UI Elements, the hotbox, Preferences > UI Elements) closes the Maya layout's Status
Line row above the shelf; the shelf row stays, keeps its height and the viewports below get the room. On puts the row
back over the shelf. Also in the four view, and the Shelf toggle with the Status Line off shows the shelf only."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, win  # noqa: E402


C = {}


def mod(name):
    return import_module(MODULE + name)


def prefs():
    return mod(".preferences").get(bpy.context)


def strip():
    return mod(".ui.shelf_strip").strip_area(win().screen)


def row():
    return mod(".ui.shelf_strip").shelf_row_area(win().screen)


def main_view():
    return mod(".ui.status_line").main_view3d(win().screen)[0]


def kit_screen():
    with bpy.context.temp_override(window=win(), screen=win().screen):
        return mod(".ui.panel_toolbar").maya_screen(bpy.context)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_layout():
    st, rw = strip(), row()
    check("the Maya layout has the Status Line row and the shelf row", st is not None and rw is not None)
    check("the Status Line row sits on the shelf row", abs(st.y - (rw.y + rw.height)) <= 4)
    C.update(row_h=rw.height, row_top=rw.y + rw.height, strip_top=st.y + st.height, view_h=main_view().height)
    prefs().show_status_line = False           # Windows > UI Elements > Status Line


@step
def s_wait():
    pass


@step
def s_off():
    rw = row()
    check("Status Line off: the Status Line row is closed", strip() is None)
    check("Status Line off: the shelf row stays", rw is not None)
    check(f"the shelf row keeps its height ({rw.height} vs {C['row_h']})", abs(rw.height - C["row_h"]) <= 4)
    check(f"the shelf row moved up to the top ({rw.y + rw.height} vs {C['strip_top']})",
          abs(rw.y + rw.height - C["strip_top"]) <= 4)
    check(f"the viewport got the room ({main_view().height} > {C['view_h']})", main_view().height > C["view_h"])
    check("still the kit layout (panel menus stay)", kit_screen())
    with bpy.context.temp_override(window=win(), screen=win().screen):
        check("Status Line drawn nowhere", not mod(".ui.status_line").status_line_shown(bpy.context))
    prefs().show_status_line = True


@step
def s_wait2():
    pass


@step
def s_on():
    st, rw = strip(), row()
    check("Status Line on: the row is back", st is not None and rw is not None)
    check("it sits on the shelf row", abs(st.y - (rw.y + rw.height)) <= 4)
    check(f"at the top again ({st.y + st.height} vs {C['strip_top']})", abs(st.y + st.height - C["strip_top"]) <= 4)
    header = next(r for r in st.regions if r.type == 'HEADER')
    check(f"one header high ({st.height} vs header {header.height})", st.height - header.height <= 4)
    check(f"the shelf row keeps its height ({rw.height} vs {C['row_h']})", abs(rw.height - C["row_h"]) <= 4)
    check(f"the viewport as before ({main_view().height} vs {C['view_h']})", abs(main_view().height - C["view_h"]) <= 6)
    check("the shelf row draws no header (tabs in its icon row)", not rw.spaces.active.show_region_header)
    check("the Status Line row has no tool header", not st.spaces.active.show_region_tool_header)
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.hb_ui(element='STATUS_LINE')     # hotbox: UI Elements > Status Line


@step
def s_wait3():
    pass


@step
def s_hotbox():
    check("the hotbox item turns it off too", not prefs().show_status_line and strip() is None and row() is not None)
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.quick_layout(layout='FOUR')


@step
def s_four_wait():
    pass


@step
def s_four():
    check("four view: still no Status Line row", strip() is None and row() is not None)
    C["four_row_h"] = row().height
    prefs().show_status_line = True


@step
def s_four_wait2():
    pass


@step
def s_four_on():
    st, rw = strip(), row()
    check("four view: the row comes back over the shelf", st is not None and rw is not None
          and abs(st.y - (rw.y + rw.height)) <= 4)
    views = [a for a in win().screen.areas if a.type == 'VIEW_3D' and a.spaces.active.show_region_header]
    check(f"four view: four panels stay ({len(views)})", len(views) == 4)
    prefs().show_status_line = False


@step
def s_four_wait3():
    pass


@step
def s_shelf_off():
    check("four view: Status Line off again", strip() is None and row() is not None)
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.shelf_strip_toggle()          # Windows > UI Elements > Shelf (off)


@step
def s_shelf_wait():
    pass


@step
def s_shelf_gone():
    check("Shelf off: the shelf row goes", row() is None and strip() is None)
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.quick_layout(layout='SINGLE')


@step
def s_single_wait():
    pass


@step
def s_shelf_on():
    with bpy.context.temp_override(window=win()):
        bpy.ops.allset.shelf_strip_toggle()          # Shelf on while the Status Line is off


@step
def s_shelf_wait2():
    pass


@step
def s_shelf_back():
    st = strip()
    check("Shelf on: a shelf strip", st is not None)
    check("Status Line off: its Status Line header is hidden", not st.spaces.active.show_region_header)
    check("the shelf shows", st.spaces.active.show_region_tool_header)
    with bpy.context.temp_override(window=win(), screen=win().screen):
        check("Status Line drawn nowhere", not mod(".ui.status_line").status_line_shown(bpy.context))
    prefs().show_status_line = True


@step
def s_shelf_wait3():
    pass


@step
def s_shelf_status_on():
    st = strip()
    check("Status Line on: the strip's Status Line header shows again", st is not None
          and st.spaces.active.show_region_header)


run()
