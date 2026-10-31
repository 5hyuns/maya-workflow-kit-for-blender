"""Viewport extras in a real UI (#224, #216): the ViewCube's hover controls (roll arrows on a face-aligned view,
Home), its labels drawn in Blender's UI font, the Alt+B gradient behind a selected cube with its wire, the gradient
kept per view through a save and reopen. Screenshots with ALLSET_GUI_SHOTS (or --shots)."""

import os
import sys
from importlib import import_module

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
GUI_TIMEOUT = 240


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def area3d():
    return max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)


def region():
    return next(r for r in area3d().regions if r.type == 'WINDOW')


def vf():
    return import_module(MODULE + ".ui.view_furniture")


def kb3():
    return import_module(MODULE + ".operators.key_batch3")


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def cube_geometry():
    m = vf()
    area, r = area3d(), region()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        b = m._bounds(bpy.context)
        s = m._scale()
        size = m.cube_size(r.width, r.height, s)
        centre, _l, _t = m.layout(b, s, size)
        controls = m.control_layout(bpy.context, centre, size)
    return r, centre, size, controls


def view_dir():
    return region().data.view_rotation @ Vector((0.0, 0.0, -1.0))


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    bpy.ops.allset.create(kind='CUBE')
    ob = bpy.context.active_object
    ob.scale = (6, 6, 6)
    ob.location = (0, 0, 0.03)
    area, r = area3d(), region()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        bpy.ops.view3d.view_axis(type='FRONT')
    redraw()


@step
def s_hover_cube():
    r, centre, size, _c = cube_geometry()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + round(centre[0]), y=r.y + round(centre[1]))


@step
def s_hover_cube2():
    r, centre, size, _c = cube_geometry()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + round(centre[0]) + 1, y=r.y + round(centre[1]))
    redraw()


@step
def s_front_shot():
    shot("gui_step293_viewcube_front.png")
    r, centre, size, controls = cube_geometry()
    x, y, rad = controls["ROLL_LEFT"]
    inside = r.width - rad > x > rad and r.height - rad > y > rad
    check(f"roll arrows of a face-aligned view stay inside the view ({x:.0f}, {y:.0f}, r {rad:.0f})", inside)
    C["dir"] = view_dir().copy()
    C["roll_xy"] = (r.x + round(x), r.y + round(y))
    ev('MOUSEMOVE', 'NOTHING', x=C["roll_xy"][0], y=C["roll_xy"][1])


@step
def s_roll_hover():
    ev('MOUSEMOVE', 'NOTHING', x=C["roll_xy"][0] + 1, y=C["roll_xy"][1])


@step
def s_roll_press():
    ev('LEFTMOUSE', 'PRESS', x=C["roll_xy"][0] + 1, y=C["roll_xy"][1])
    ev('LEFTMOUSE', 'RELEASE', x=C["roll_xy"][0] + 1, y=C["roll_xy"][1])


@step
def s_roll_wait():
    pass


@step
def s_roll():
    d = view_dir()
    up = region().data.view_rotation @ Vector((0.0, 1.0, 0.0))
    check(f"a click on the roll arrow rolls the front view 90° (looks along {tuple(round(v, 2) for v in d)}, "
          f"up {tuple(round(v, 2) for v in up)})", (d - C["dir"]).length < 1e-3 and abs(up.z) < 1e-3)
    shot("gui_step293_viewcube_rolled.png")
    r, centre, size, controls = cube_geometry()
    x, y, _rad = controls["HOME"]
    C["home_xy"] = (r.x + round(x), r.y + round(y))
    region().data.view_location = (0.05, 0.0, 0.02)     # panned away: Home brings the view back to the origin
    ev('MOUSEMOVE', 'NOTHING', x=r.x + round(centre[0]), y=r.y + round(centre[1]))


@step
def s_home_hover():
    ev('MOUSEMOVE', 'NOTHING', x=C["home_xy"][0], y=C["home_xy"][1])


@step
def s_home_hover2():
    ev('MOUSEMOVE', 'NOTHING', x=C["home_xy"][0] + 1, y=C["home_xy"][1])


@step
def s_home_press():
    ev('LEFTMOUSE', 'PRESS', x=C["home_xy"][0] + 1, y=C["home_xy"][1])
    ev('LEFTMOUSE', 'RELEASE', x=C["home_xy"][0] + 1, y=C["home_xy"][1])


@step
def s_home_wait():
    pass


@step
def s_home():
    loc = region().data.view_location
    check(f"the Home control runs the kit's Home (view back at the origin: {tuple(round(v, 3) for v in loc)})",
          loc.length < 1e-6)
    ev('MOUSEMOVE', 'NOTHING', x=region().x + region().width // 3, y=region().y + region().height // 3)
    for _i in range(2):   # grey -> light -> gradient
        ev('B', 'PRESS', alt=True)
        ev('B', 'RELEASE', alt=True)


@step
def s_gradient_wait():
    bpy.context.view_layer.objects.active.select_set(True)
    redraw()


@step
def s_gradient():
    sh = area3d().spaces.active.shading
    check(f"two Alt+B from grey give the gradient ({kb3().background_state(sh)})", kb3().is_gradient(sh))
    shot("gui_step293_gradient_wire.png")
    path = os.path.join(bpy.app.tempdir, "s293_gradient.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    C["path"] = path


@step
def s_reopen():
    bpy.ops.wm.open_mainfile(filepath=C["path"])


@step
def s_reopen_wait():
    redraw()


@step
def s_reopened():
    sh = area3d().spaces.active.shading
    check("the gradient is a per-view setting kept by save and open", kb3().is_gradient(sh))
    shot("gui_step293_gradient_reopened.png")


run()
