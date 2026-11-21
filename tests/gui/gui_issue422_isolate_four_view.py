"""#422 with Maya's panel layouts: Isolate Select belongs to one panel. Ctrl+1 in the single perspective view, Space
to the four view and back, Ctrl+1 inside the four view: in every step the isolated panel shows only the isolated
cubes, a click and a marquee there pick only them, and the other panels still show and pick every cube."""

import math
import os
import sys
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {"u": 1.0}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def fv():
    return import_module(f"{MODULE}.ui.four_view")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def persp():
    """The perspective panel: the four view's persp place, else the main 3D View."""
    roles = fv().roles(win().screen)
    return roles["persp"] if roles else view3d()[0]


def region_of(area):
    return next(r for r in area.regions if r.type == 'WINDOW')


def screen_xy(area, co):
    region = region_of(area)
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, Vector(co) * C["u"])
    return region.x + int(round(p.x)), region.y + int(round(p.y))


def rel(area, fx, fy):
    r = region_of(area)
    return r.x + int(r.width * fx), r.y + int(r.height * fy)


def key(k, **mods):
    ev(k, 'PRESS', **mods)
    ev(k, 'RELEASE', **mods)


def ctrl_one(area):
    x, y = rel(area, 0.5, 0.9)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFT_CTRL', 'PRESS')
    key('ONE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


def click(xy, **mods):
    ev('MOUSEMOVE', 'NOTHING', x=xy[0], y=xy[1])
    ev('LEFTMOUSE', 'PRESS', x=xy[0], y=xy[1], **mods)
    ev('LEFTMOUSE', 'RELEASE', x=xy[0], y=xy[1], **mods)


def drag(a, b):
    ev('MOUSEMOVE', 'NOTHING', x=a[0], y=a[1])
    ev('LEFTMOUSE', 'PRESS', x=a[0], y=a[1])
    n = 8
    for i in range(1, n + 1):
        ev('MOUSEMOVE', 'NOTHING', x=a[0] + (b[0] - a[0]) * i // n, y=a[1] + (b[1] - a[1]) * i // n)
    ev('LEFTMOUSE', 'RELEASE', x=b[0], y=b[1])


def selected():
    return sorted(o.name for o in bpy.context.scene.objects if o.select_get() and o.type == 'MESH')


def select(*names):
    for o in bpy.context.scene.objects:
        o.select_set(o.name in names)
    bpy.context.view_layer.objects.active = bpy.data.objects[names[-1]] if names else None


def isolated(area):
    return area.spaces.active.local_view is not None


def shown(area):
    """Mesh names drawn in ``area`` (Isolate Select = local view of that panel)."""
    space = area.spaces.active
    if space.local_view is None:
        return sorted(o.name for o in bpy.context.scene.objects if o.type == 'MESH')
    return sorted(o.name for o in bpy.context.scene.objects if o.type == 'MESH' and o.local_view_get(space))


def space_tap(get):
    """Space over the area ``get()`` returns: move in one tick, key in the next, two redraw ticks after."""
    def move():
        r = region_of(get())
        C["xy"] = (r.x + r.width // 2, r.y + int(r.height * 0.9))
        ev('MOUSEMOVE', 'NOTHING', x=C["xy"][0], y=C["xy"][1])

    def tap():
        x, y = C["xy"]
        ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)
        ev('SPACE', 'PRESS', x=x, y=y)
        ev('SPACE', 'RELEASE', x=x, y=y)
    step(move)
    step(tap)
    step(redraw)
    step(redraw)


CUBES = {"pCube1": (-3, 0, 1), "pCube2": (0, 0, 1), "pCube3": (3, 0, 1)}


def pick_checks(label, get, expect_marquee, target="pCube2", hidden=None):
    """A click on ``target`` picks it, one on ``hidden`` (a cube the panel doesn't show) picks nothing; a marquee
    over the panel picks ``expect_marquee``."""
    @step
    def clear():
        select()
        click(rel(get(), 0.1, 0.1))         # a click on empty space first: no double click below

    step(redraw)
    step(redraw)

    @step
    def do_click():
        click(screen_xy(get(), CUBES[target]))

    step(redraw)

    @step
    def clicked():
        check(f"{label}: a click on {target} picks it ({selected()})", selected() == [target])
        select()

    if hidden:
        step(redraw)
        step(redraw)

        @step
        def do_hidden():
            click(screen_xy(get(), CUBES[hidden]))

        step(redraw)

        @step
        def hidden_clicked():
            check(f"{label}: a click where {hidden} is hidden picks nothing ({selected()})", selected() == [])

    step(redraw)
    step(redraw)

    @step
    def do_marquee():
        drag(rel(get(), 0.03, 0.97), rel(get(), 0.97, 0.03))

    step(redraw)

    @step
    def marqueed():
        check(f"{label}: a marquee over the panel picks {expect_marquee} ({selected()})",
              selected() == expect_marquee)


@step
def s_setup():
    setup()
    load_maya_layout()


for _i in range(4):
    step(redraw)


@step
def s_scene():
    sc = bpy.context.scene
    C["u"] = u = import_module(MODULE + ".operators.units").maya_unit(sc)
    for name, x in (("pCube1", -3.0), ("pCube2", 0.0), ("pCube3", 3.0)):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2.0 * u)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        ob.location.x = x * u
        sc.collection.objects.link(ob)
    rv3d = view3d()[0].spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_rotation = Euler((math.radians(70), 0, math.radians(20))).to_quaternion()
    rv3d.view_location = (0, 0, 0)
    rv3d.view_distance = 16.0 * u
    select("pCube1", "pCube2")
    redraw()


step(redraw)


@step
def s_iso_single():
    ctrl_one(persp())


step(redraw)


@step
def s_iso_single_on():
    check(f"Ctrl+1 in the single view isolates pCube1 and pCube2 ({shown(persp())})",
          shown(persp()) == ["pCube1", "pCube2"])
    shot("gui_issue422_4v_single.png")


pick_checks("single view isolated", persp, ["pCube1", "pCube2"], hidden="pCube3")
space_tap(persp)


@step
def s_four():
    screen = win().screen
    check(f"Space: the four view ({len(fv().panes(screen))} panels)", fv().is_four(screen))
    roles = fv().roles(screen)
    check(f"... the persp panel stays isolated ({shown(persp())})", shown(persp()) == ["pCube1", "pCube2"])
    others = {r: shown(a) for r, a in roles.items() if r != "persp"}
    check(f"... the other panels show every cube ({others})",
          all(v == ["pCube1", "pCube2", "pCube3"] for v in others.values()))
    shot("gui_issue422_4v_four.png")


pick_checks("four view, persp panel isolated", persp, ["pCube1", "pCube2"], hidden="pCube3")
pick_checks("four view, front panel", lambda: fv().roles(win().screen)["front"], ["pCube1", "pCube2", "pCube3"])


@step
def s_iso_off_in_four():
    ctrl_one(persp())


step(redraw)


@step
def s_iso_off_four():
    space = persp().spaces.active
    check(f"Ctrl+1 again in the persp panel ends Isolate Select ({space.local_view is None})",
          space.local_view is None)
    select("pCube2", "pCube3")
    ctrl_one(persp())


step(redraw)


@step
def s_iso_in_four():
    check(f"Ctrl+1 inside the four view isolates pCube2 and pCube3 ({shown(persp())})",
          shown(persp()) == ["pCube2", "pCube3"])


pick_checks("isolated inside the four view", persp, ["pCube2", "pCube3"])
space_tap(persp)


@step
def s_single_again():
    screen = win().screen
    area = persp()
    check(f"Space: back to one panel ({len(fv().panes(screen))})", len(fv().panes(screen)) == 1)
    check(f"... it stays isolated ({shown(area)})", shown(area) == ["pCube2", "pCube3"])
    shot("gui_issue422_4v_single_again.png")


pick_checks("single view again", persp, ["pCube2", "pCube3"])


@step
def s_before_four_again():
    select("pCube3")


space_tap(persp)


def front():
    return fv().roles(win().screen)["front"]


@step
def s_four_again():
    roles = fv().roles(win().screen)
    check(f"Space: the four view again, persp still isolated ({shown(persp())})",
          bool(roles) and shown(persp()) == ["pCube2", "pCube3"])
    check(f"... the front panel is not ({isolated(front())})", bool(roles) and not isolated(front()))
    check(f"... the selection is kept ({selected()})", selected() == ["pCube3"])
    select("pCube1")
    ctrl_one(front())


step(redraw)


@step
def s_front_iso():
    check(f"Ctrl+1 in the front panel isolates pCube1 there ({shown(front())})", shown(front()) == ["pCube1"])
    check(f"... the persp panel keeps its own ({shown(persp())})", shown(persp()) == ["pCube2", "pCube3"])


pick_checks("front panel isolated", front, ["pCube1"], target="pCube1", hidden="pCube2")
space_tap(persp)


@step
def s_single_third():
    check(f"Space over persp: one panel, still isolated ({shown(persp())})",
          len(fv().panes(win().screen)) == 1 and shown(persp()) == ["pCube2", "pCube3"])


space_tap(persp)


@step
def s_four_third():
    roles = fv().roles(win().screen)
    check(f"Space: the four view, the front panel isolates pCube1 again ({bool(roles) and shown(front())})",
          bool(roles) and shown(front()) == ["pCube1"])
    check(f"... persp keeps pCube2 and pCube3 ({shown(persp())})", shown(persp()) == ["pCube2", "pCube3"])
    shot("gui_issue422_4v_four_third.png")


pick_checks("front panel isolated again", front, ["pCube1"], target="pCube1", hidden="pCube2")


run()
