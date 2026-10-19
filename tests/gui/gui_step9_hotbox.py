"""Step 9 in a real UI: marking menu engine (drag, click mode, flick, in-place submenu)
and the hotbox (menu rows, centre zone menu, Space tap); screenshots."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, step, setup, screenshot, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
D = 110  # px: past the ring (radius 80 x UI scale)


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def ts():
    return bpy.context.scene.tool_settings


def mode():
    return bpy.context.mode


def obj_mode():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def drag_to(dx, dy):
    x, y = C["x"], C["y"]
    ev('MOUSEMOVE', 'NOTHING', x=x + dx // 3, y=y + dy // 3)
    ev('MOUSEMOVE', 'NOTHING', x=x + 2 * dx // 3, y=y + 2 * dy // 3)
    ev('MOUSEMOVE', 'NOTHING', x=x + dx, y=y + dy)


@step
def s_setup():
    C["x"], C["y"] = setup()
    C["draw"] = import_module(MODULE + ".marking.draw")
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"])


@step
def s_drag_shown():
    check("RMB press opens the engine (not a pie)", "session" in C["draw"].ACTIVE)
    # Held still past the 0.15 s delay: the menu is drawn without a mouse move (a
    # screenshot shows the previous frame, so it is taken one tick later).


@step
def s_drag_shown2():
    shot("gui_step9_rmb_engine.png")
    drag_to(0, D)


@step
def s_drag_release():
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"], y=C["y"] + D)


@step
def s_drag_done():
    check("drag north + release = Edge mode",
          mode() == 'EDIT_MESH' and tuple(ts().mesh_select_mode) == (False, True, False))
    check("engine closed and nothing left drawing", not C["draw"].ACTIVE)
    obj_mode()
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"], y=C["y"])  # quick click


@step
def s_click_mode():
    check("quick RMB click keeps the menu open (click mode)",
          "session" in C["draw"].ACTIVE and C["draw"].ACTIVE["session"].mode == "CLICK")
    drag_to(-D, 0)
    shot("gui_step9_click_mode.png")
    ev('LEFTMOUSE', 'PRESS', x=C["x"] - D, y=C["y"])
    ev('LEFTMOUSE', 'RELEASE', x=C["x"] - D, y=C["y"])


@step
def s_click_done():
    check("click mode: click West = Vertex mode",
          mode() == 'EDIT_MESH' and tuple(ts().mesh_select_mode) == (True, False, False))
    obj_mode()
    # Flick: press, move and release within one tick (well under the 0.15 s draw delay).
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"])
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"] - 30)
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"] - 60)
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"], y=C["y"] - 60)


@step
def s_flick_done():
    check("quick flick south = Face mode (menu never drawn)",
          mode() == 'EDIT_MESH' and tuple(ts().mesh_select_mode) == (False, False, True))
    # In-place submenu: Ctrl+RMB (convert), W "To Vertices >" then W "To Vertices".
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"], ctrl=True)


@step
def s_sub_open():
    drag_to(-D, 0)


@step
def s_sub_shown():
    s = C["draw"].ACTIVE.get("session")
    check("dragging onto 'To Vertices' opens its submenu in place", s is not None and len(s.stack) == 2)
    x0 = C["x"] - D
    ev('MOUSEMOVE', 'NOTHING', x=x0 - 40, y=C["y"])
    ev('MOUSEMOVE', 'NOTHING', x=x0 - 80, y=C["y"])
    shot("gui_step9_submenu.png")


@step
def s_sub_release():
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"] - D - 80, y=C["y"], ctrl=True)


@step
def s_sub_done():
    check("submenu W = To Vertices (vertex select mode)", tuple(ts().mesh_select_mode) == (True, False, False))
    obj_mode()
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('SPACE', 'PRESS')


@step
def s_hotbox():
    hb = C["draw"].ACTIVE.get("hotbox")
    check("Space hold shows the hotbox", hb is not None)
    shot("gui_step9_hotbox.png")
    _area, r = view3d()
    rect = next(rc for rc, key, label in hb.labels if label == "Mesh")
    x, y = r.x + int((rect[0] + rect[2]) / 2), r.y + int((rect[1] + rect[3]) / 2)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_hotbox_menu():
    shot("gui_step9_hotbox_mesh_menu.png")
    check("clicking a menu name closes the hotbox", not C["draw"].ACTIVE)
    tap('ESC')
    ev('SPACE', 'RELEASE')


@step
def s_zone():
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('SPACE', 'PRESS')


@step
def s_zone_click():
    ev('LEFTMOUSE', 'PRESS', x=C["x"], y=C["y"])  # centre zone


@step
def s_zone_menu():
    drag_to(-D, 0)
    shot("gui_step9_hotbox_center.png")


@step
def s_zone_release():
    ev('LEFTMOUSE', 'RELEASE', x=C["x"] - D, y=C["y"])
    ev('SPACE', 'RELEASE')


@step
def s_zone_done():
    area, _r = view3d()
    rv3d = area.spaces.active.region_3d
    check(f"hotbox centre zone, drag W = Top View (got {rv3d.view_perspective})",
          rv3d.view_perspective == 'ORTHO')
    with bpy.context.temp_override(window=win(), area=area):
        bpy.ops.allset.hb_view(view='PERSP')
    check("Perspective View restores the perspective camera", rv3d.view_perspective == 'PERSP')
    C["tb"] = area.spaces.active.show_region_toolbar
    with bpy.context.temp_override(window=win(), area=area):
        bpy.ops.allset.hb_ui(element='TOOLBOX')


@step
def s_toolbox():
    area, _r = view3d()
    check("East zone Tool Box toggles the toolbar", area.spaces.active.show_region_toolbar != C["tb"])
    area.spaces.active.show_region_toolbar = C["tb"]
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    tap('SPACE')


@step
def s_tap():
    area, _r = view3d()
    check("Space tap = four views", len(area.spaces.active.region_quadviews) > 0)
    check("no hotbox left after a tap", not C["draw"].ACTIVE)
    tap('SPACE')  # back to one view


@step
def s_option_boxes():
    # Shift+RMB in face mode, click mode: option boxes [] on Maya's items.
    bpy.ops.object.mode_set(mode='EDIT')
    ts().mesh_select_mode = (False, False, True)
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"], shift=True)
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"], y=C["y"], shift=True)


@step
def s_option_shot():
    s = C["draw"].ACTIVE.get("session")
    check("face tools menu has option boxes", s is not None and any(it.opt_rect for it in s.layout.items))
    shot("gui_step9_option_boxes.png")
    tap('ESC')


run()
