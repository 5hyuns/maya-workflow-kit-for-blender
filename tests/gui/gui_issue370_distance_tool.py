"""#370 in a real UI (Maya Workflow Kit layout): Create > Measure Tools > Distance Tool. Two clicks on the ground ->
locator1, locator2 and distanceDimension1 (the distance in Maya units, drawn in the view); the tool stays on: a click on
locator2 then a free click -> distanceDimension2 from locator2; Ctrl+Z takes that measurement back in one step; moving
locator1 changes the drawn number; a click on a dimension line with the Select Tool selects the dimension; Esc after
one click keeps that locator."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, tap, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + "." + name)


def main_view():
    toolbox = mod("ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def running():
    return "ALLSET_OT_distance_click" in [op.bl_idname for op in win().modal_operators]


def u():
    return mod("operators.units").maya_unit(bpy.context.scene)


def world(x, y):
    return Vector((x * u(), y * u(), 0.0))


def to_window(p):
    _area, region = main_view()
    xy = view3d_utils.location_3d_to_region_2d(region, region.data, Vector(p))
    return int(round(region.x + xy.x)), int(round(region.y + xy.y))


def click(p):
    """A left click at window pixel ``p`` (press and release in this tick)."""
    ev('MOUSEMOVE', 'NOTHING', x=p[0], y=p[1])
    ev('LEFTMOUSE', 'PRESS', x=p[0], y=p[1])
    ev('LEFTMOUSE', 'RELEASE', x=p[0], y=p[1])


def obj(name):
    return bpy.data.objects.get(name)


def selected():
    return sorted(o.name for o in bpy.context.view_layer.objects if o.select_get())


def items():
    """(name, text, dimension line ends in window pixels) the main view draws."""
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        got = mod("ui.distance_dimensions").screen_items(bpy.context, region, region.data, area.spaces.active)
    off = Vector((region.x, region.y))
    return [(ob.name, text, a2 + off, b2 + off) for ob, _a, _b, a2, b2, text in got]


def set_tool(idname):
    area, region = main_view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.tool_set_by_id(name=idname)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_tool():
    for o in list(bpy.context.view_layer.objects):
        o.select_set(False)
    _area, region = main_view()
    C["p1"], C["p2"], C["p3"] = world(-4, -2), world(2, 3), world(5, -3)
    for name in ("p1", "p2", "p3"):
        x, y = to_window(C[name])
        check(f"{name} is in the main view ({x}, {y})", region.x + 20 < x < region.x + region.width - 20
              and region.y + 20 < y < region.y + region.height - 20)
    item = mod("ui.menu_map").MAP["Create/Measure Tools/Distance Tool"]
    check(f"the menu item picks the kit's Distance Tool ({item})", item == ("tool", "allset.distance_tool", False))
    set_tool("allset.distance_tool")
    tool = bpy.context.workspace.tools.from_space_view3d_mode('OBJECT', create=False)
    check(f"Distance Tool is the active tool ({tool.idname if tool else None})",
          tool is not None and tool.idname == "allset.distance_tool")


@step
def s_click1():
    click(to_window(C["p1"]))


@step
def s_check1():
    loc = obj("locator1")
    check("first click: locator1 on the ground at the click", loc is not None and (loc.location - C["p1"]).length
          < 0.05 * u())
    check("the tool waits for the second point", running())
    check(f"locator1 selected ({selected()})", selected() == ["locator1"])


@step
def s_click2():
    click(to_window(C["p2"]))


@step
def s_check2():
    dt = mod("operators.distance_tool")
    loc, dd = obj("locator2"), obj("distanceDimension1")
    check("second click: locator2 and distanceDimension1", loc is not None and dd is not None)
    if dd is None:
        return
    want = (C["p2"] - C["p1"]).length / u()
    got = dt.distance(dd)
    check(f"distanceDimension1 measures locator1 -> locator2 ({got:.4f}, about {want:.4f})",
          [o.name for o in dt.ends(dd)] == ["locator1", "locator2"] and abs(got - want) < 0.1)
    check(f"locator2 and the dimension selected, the dimension the lead ({selected()})",
          selected() == ["distanceDimension1", "locator2"] and bpy.context.view_layer.objects.active == dd)
    check("the measurement is done (no click waiting)", not running())
    drawn = items()
    check(f"the main view draws the distance ({[(n, t) for n, t, _a, _b in drawn]})",
          [(n, t) for n, t, _a, _b in drawn] == [("distanceDimension1", dt.label(got))])
    tool = bpy.context.workspace.tools.from_space_view3d_mode('OBJECT', create=False)
    check("the Distance Tool stays on", tool is not None and tool.idname == "allset.distance_tool")


@step
def s_shot():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue370_distance.png"))


@step
def s_reuse_click():
    click(to_window(obj("locator2").matrix_world.translation))


@step
def s_reuse_check():
    n = len([o for o in bpy.data.objects if o.name.startswith("locator")])
    check(f"a click on locator2 uses it (no new locator: {n})", n == 2 and running())
    click(to_window(C["p3"]))


@step
def s_reuse_done():
    dt = mod("operators.distance_tool")
    dd = obj("distanceDimension2")
    check("distanceDimension2 measures from locator2 to locator3",
          dd is not None and [o.name for o in dt.ends(dd)] == ["locator2", "locator3"])
    _area, region = main_view()
    x, y = region.x + region.width // 2, region.y + region.height // 2
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('Z', 'PRESS', x=x, y=y, ctrl=True)
    ev('Z', 'RELEASE', x=x, y=y, ctrl=True)


@step
def s_undo_check():
    names = sorted(o.name for o in bpy.data.objects if o.name.startswith(("locator", "distanceDimension")))
    check(f"Ctrl+Z takes the whole second measurement back ({names})",
          names == ["distanceDimension1", "locator1", "locator2"])
    loc = obj("locator1")
    loc.location = loc.location + Vector((0.0, -3.0 * u(), 0.0))
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_moved_check():
    dt = mod("operators.distance_tool")
    dd = obj("distanceDimension1")
    want = (obj("locator2").location - obj("locator1").location).length / u()
    drawn = items()
    check(f"moving locator1 changes the drawn distance ({[t for _n, t, _a, _b in drawn]}, {want:.4f})",
          [t for _n, t, _a, _b in drawn] == [dt.label(want)] and abs(dt.distance(dd) - want) < 1e-5)
    C["line"] = drawn[0][2:] if drawn else None
    set_tool("builtin.select_box")
    for o in list(bpy.context.view_layer.objects):
        o.select_set(False)


@step
def s_pick_line():
    a2, b2 = C["line"]
    p = a2 + (b2 - a2) * 0.25
    click((int(round(p.x)), int(round(p.y))))


@step
def s_pick_check():
    check(f"a click on the dimension line selects distanceDimension1 ({selected()})",
          selected() == ["distanceDimension1"] and bpy.context.view_layer.objects.active == obj("distanceDimension1"))
    set_tool("allset.distance_tool")


@step
def s_esc_click():
    click(to_window(world(-6, 4)))


@step
def s_esc():
    check("one click: the tool waits", running() and obj("locator3") is not None)
    tap('ESC')


@step
def s_esc_check():
    check("Esc stops the measurement and keeps the locator", not running() and obj("locator3") is not None
          and obj("distanceDimension2") is None)


run()
