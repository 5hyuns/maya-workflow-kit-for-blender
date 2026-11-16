"""#370 follow-up in a real UI (Maya Workflow Kit layout): a measurement made with Create > Measure Tools > Distance
Tool stays. Two clicks -> locator1, locator2 and distanceDimension1 in the Outliner and drawn in the view; then the
Select Tool, the Distance Tool again (the menu item), Select again: after each switch the three objects are still there,
listed in the Outliner and the distance is still drawn; a second measurement with the tool picked again adds
distanceDimension2 next to the first."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
NAMES = ("locator1", "locator2", "distanceDimension1")


def mod(name):
    return import_module(MODULE + "." + name)


def main_view():
    toolbox = mod("ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def world(x, y):
    u = mod("operators.units").maya_unit(bpy.context.scene)
    return Vector((x * u, y * u, 0.0))


def to_window(p):
    _area, region = main_view()
    xy = view3d_utils.location_3d_to_region_2d(region, region.data, Vector(p))
    return int(round(region.x + xy.x)), int(round(region.y + xy.y))


def click(p):
    ev('MOUSEMOVE', 'NOTHING', x=p[0], y=p[1])
    ev('LEFTMOUSE', 'PRESS', x=p[0], y=p[1])
    ev('LEFTMOUSE', 'RELEASE', x=p[0], y=p[1])


def drawn():
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        got = mod("ui.distance_dimensions").screen_items(bpy.context, region, region.data, area.spaces.active)
    return sorted(ob.name for ob, *_rest in got)


def outliner_labels():
    area = next(a for a in win().screen.areas if a.type == 'OUTLINER')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return [r.label for r in mod("ui.outliner_tree").rows_for(bpy.context, area.spaces.active)]


def active_tool():
    tool = bpy.context.workspace.tools.from_space_view3d_mode('OBJECT', create=False)
    return tool.idname if tool else None


def pick_menu_tool():
    """Create > Measure Tools > Distance Tool, as the menu item runs it."""
    kind, idname, _x = mod("ui.menu_map").MAP["Create/Measure Tools/Distance Tool"]
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.tool_set_by_id(name=idname)
    return kind, idname


def select_tool():
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def still_there(tag, names=NAMES):
    have = [n for n in names if bpy.data.objects.get(n) is not None]
    check(f"{tag}: {', '.join(names)} still exist ({have})", len(have) == len(names))
    labels = outliner_labels()
    check(f"{tag}: the Outliner lists them ({[n for n in names if n in labels]})", all(n in labels for n in names))
    dims = [n for n in names if n.startswith("distanceDimension")]
    got = drawn()
    check(f"{tag}: the view draws {dims} ({got})", all(n in got for n in dims))


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_tool():
    for o in list(bpy.context.view_layer.objects):
        o.select_set(False)
    got = pick_menu_tool()
    check(f"Create > Measure Tools > Distance Tool picks the kit's tool ({got}, active {active_tool()})",
          got == ("tool", "allset.distance_tool") and active_tool() == "allset.distance_tool")


@step
def s_click1():
    click(to_window(world(-4, -2)))


@step
def s_click2():
    click(to_window(world(2, 3)))


@step
def s_made():
    redraw()


@step
def s_made_check():
    still_there("after two clicks")
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue370_tool_again_made.png"))
    select_tool()
    redraw()


@step
def s_select_check():
    check(f"the Select Tool is on ({active_tool()})", active_tool() == "builtin.select_box")
    still_there("Select Tool")
    pick_menu_tool()
    redraw()


@step
def s_again_check():
    check(f"the Distance Tool is on again ({active_tool()})", active_tool() == "allset.distance_tool")
    still_there("Distance Tool picked again")
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue370_tool_again.png"))


@step
def s_second1():
    click(to_window(world(4, -3)))


@step
def s_second2():
    click(to_window(world(6, 2)))


@step
def s_second_made():
    redraw()


@step
def s_second_check():
    still_there("a second measurement", NAMES + ("distanceDimension2",))
    select_tool()
    redraw()


@step
def s_final_check():
    still_there("Select Tool again", NAMES + ("distanceDimension2",))


run()
