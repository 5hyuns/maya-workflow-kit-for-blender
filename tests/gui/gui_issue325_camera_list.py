"""#325: in the Maya Workflow Kit layout a right-click on the camera icon at the left of the viewport panel toolbar
lists the scene's cameras (like Maya); picking one looks through it in that view. A right-click on another toolbar
button keeps Blender's own button menu (the camera list stays closed)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, button_under_mouse, check, ev, run, screenshot, setup, step, tap, view3d, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def header():
    area, _r = view3d()
    return area, next(r for r in area.regions if r.type == 'TOOL_HEADER')


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CAMERA')
        C["cam"] = bpy.context.view_layer.objects.active.name
    area.spaces.active.region_3d.view_perspective = 'PERSP'
    for a in win().screen.areas:
        a.tag_redraw()


def sweep():
    """Left to right along the tool header's middle, 3 px a tick, until Lock Camera: the x of the camera icon and
    of Lock Camera (the first buttons of the toolbar)."""
    state = {}

    def look():
        area, region = header()
        if not state:
            state["x"] = region.x + 2
        else:
            _path, cmd = button_under_mouse(area, region)
            for key, name in (("cam_btn", "SELECT_CAMERA"), ("lock_btn", "CAMERA_LOCK")):
                if name in cmd and key not in C:
                    C[key] = (state["x"] + 3, region.y + region.height // 2)    # a little inside the button
            state["x"] += 3
            if "lock_btn" in C or state["x"] > region.x + region.width // 2:
                return
        ev('MOUSEMOVE', 'NOTHING', x=state["x"], y=region.y + region.height // 2)
        sim._steps.insert(0, look)
    return look


step(sweep())


@step
def s_rmb_other():
    check(f"found the camera icon {C.get('cam_btn')} and Lock Camera {C.get('lock_btn')}",
          "cam_btn" in C and "lock_btn" in C)
    x, y = C["lock_btn"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


@step
def s_rmb_other_press():
    ptr = win().as_pointer()
    check("over Lock Camera the camera watch is off", not mod("ui.panel_toolbar")._over_camera.get(ptr))
    ev('RIGHTMOUSE', 'PRESS')
    ev('RIGHTMOUSE', 'RELEASE')


@step
def s_close_other():
    tap('ESC')
    x, y = C["cam_btn"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


@step
def s_rmb_camera():
    ptr = win().as_pointer()
    pt = mod("ui.panel_toolbar")
    check("over the camera icon the right-click is watched", pt._over_camera.get(ptr) and ptr in pt._watching)
    ev('RIGHTMOUSE', 'PRESS')
    ev('RIGHTMOUSE', 'RELEASE')


@step
def s_menu_open():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue325_camera_list.png"))
    tap(C["cam"][0].upper())        # the menu's underlined letter of the camera's row (persp p, top t, front f, side s)


@step
def s_picked():
    area, _r = view3d()
    space = area.spaces.active
    check(f"picking {C['cam']} in the list looks through it ({space.region_3d.view_perspective}, "
          f"{space.camera.name if space.camera else None})",
          space.region_3d.view_perspective == 'CAMERA' and space.camera is not None
          and space.camera.name == C["cam"])


run()
