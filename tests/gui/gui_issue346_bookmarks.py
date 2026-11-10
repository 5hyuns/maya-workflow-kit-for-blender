"""#346: the viewport panel toolbar's Bookmarks and 2D Pan/Zoom buttons in a real UI (Maya Workflow Kit layout, a view
that looks through a camera).

\\ + LMB drag pans the camera view and lights the 2D Pan/Zoom button; a click on the button shows the whole camera
frame (the camera stays), a second click brings the pan back. A click on Bookmarks makes cameraView1 on the camera;
after the camera moved, a right-click on Bookmarks opens the camera's bookmarks and picking cameraView1 puts the
camera back. A right-click on 2D Pan/Zoom opens the 2D bookmarks menu. Shots with ``--shots``."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, button_under_mouse, check, ev, load_maya_layout, run, screenshot, setup, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def header():
    area, _r = view3d()
    return area, next(r for r in area.regions if r.type == 'TOOL_HEADER')


def rv3d():
    return view3d()[1].data


def cam():
    return bpy.data.objects[C["cam"]]


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


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
        bpy.ops.allset.panel_look_through(camera=C["cam"])
    redraw()


@step
def s_settle():
    redraw()


def sweep():
    """Left to right along the tool header's middle, 3 px a tick: the x of the Bookmarks and 2D Pan/Zoom buttons."""
    state = {}

    def look():
        area, region = header()
        if not state:
            state["x"] = region.x + 2
        else:
            _path, cmd = button_under_mouse(area, region)
            for key, name in (("bm_btn", "key='BOOKMARK'"), ("pz_btn", "key='PAN_ZOOM'")):
                if name in cmd and key not in C:
                    C[key] = (state["x"] + 4, region.y + region.height // 2)    # a little inside the button
            state["x"] += 3
            if "pz_btn" in C or state["x"] > region.x + region.width // 2:
                return
        ev('MOUSEMOVE', 'NOTHING', x=state["x"], y=region.y + region.height // 2)
        sim._steps.insert(0, look)
    return look


step(sweep())


@step
def s_found():
    check(f"found Bookmarks {C.get('bm_btn')} and 2D Pan/Zoom {C.get('pz_btn')} in the panel toolbar",
          "bm_btn" in C and "pz_btn" in C)
    check("the 2D Pan/Zoom button starts off", not mod("ui.camera_bookmarks").pan_zoom_on(rv3d()))
    _a, r = view3d()
    C["mid"] = (r.x + r.width // 2, r.y + r.height // 2)
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])


@step
def s_pan_start():
    C["off0"] = tuple(rv3d().view_camera_offset)
    C["loc0"] = tuple(cam().location)
    ev('BACK_SLASH', 'PRESS')
    ev('LEFTMOUSE', 'PRESS', x=C["mid"][0], y=C["mid"][1])


@step
def s_pan_move():
    for i in range(1, 5):
        ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0] + 20 * i, y=C["mid"][1])


@step
def s_pan_end():
    ev('LEFTMOUSE', 'RELEASE', x=C["mid"][0] + 80, y=C["mid"][1])
    ev('BACK_SLASH', 'RELEASE')


@step
def s_pan_check():
    C["off1"] = tuple(rv3d().view_camera_offset)
    check(f"\\ + LMB drag pans the camera view ({C['off0']} -> {C['off1']})", abs(C["off1"][0] - C["off0"][0]) > 1e-4)
    check("... and lights the 2D Pan/Zoom button", mod("ui.camera_bookmarks").pan_zoom_on(rv3d()))
    redraw()
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue346_pan_on.png"))


def click(key):
    def press():
        x, y = C[key]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)

    def release():
        x, y = C[key]
        ev('LEFTMOUSE', 'PRESS', x=x + 1, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x + 1, y=y)
    return press, release


for _f in click("pz_btn"):
    step(_f)


@step
def s_off_check():
    off = tuple(rv3d().view_camera_offset)
    check(f"2D Pan/Zoom off: the whole frame, no pan ({off})", abs(off[0]) < 1e-6 and abs(off[1]) < 1e-6)
    check("... the button is off and the camera stays",
          not mod("ui.camera_bookmarks").pan_zoom_on(rv3d()) and tuple(cam().location) == C["loc0"])
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue346_pan_off.png"))


for _f in click("pz_btn"):
    step(_f)


@step
def s_on_check():
    off = tuple(rv3d().view_camera_offset)
    check(f"2D Pan/Zoom on again: the pan comes back ({off} == {C['off1']})",
          abs(off[0] - C["off1"][0]) < 1e-5 and abs(off[1] - C["off1"][1]) < 1e-5)
    check("... and the button is on", mod("ui.camera_bookmarks").pan_zoom_on(rv3d()))


for _f in click("bm_btn"):
    step(_f)


@step
def s_bookmark_check():
    names = [b.name for b in mod("ui.camera_bookmarks").bookmarks(cam())]
    check(f"a click on Bookmarks bookmarks the camera ({names})", names == ["cameraView1"])
    C["mw"] = [tuple(r) for r in cam().matrix_world]
    cam().location.x += 3.0
    bpy.context.view_layer.update()
    x, y = C["bm_btn"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


@step
def s_rmb_bookmarks():
    ptr = win().as_pointer()
    pt = mod("ui.panel_toolbar")
    check(f"over Bookmarks the right-click is watched ({pt._over_camera.get(ptr)})",
          pt._over_camera.get(ptr) == "ALLSET_MT_pt_bookmarks" and ptr in pt._watching)
    ev('RIGHTMOUSE', 'PRESS')
    ev('RIGHTMOUSE', 'RELEASE')


@step
def s_menu_open():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue346_bookmarks_menu.png"))
    tap('C')            # the menu's underlined letter of its first row, cameraView1


@step
def s_picked():
    mw = [tuple(r) for r in cam().matrix_world]
    same = all(abs(a - b) < 1e-5 for ra, rb in zip(mw, C["mw"]) for a, b in zip(ra, rb))
    check(f"picking cameraView1 in the right-click menu puts the camera back ({cam().location.x:.3f})", same)
    x, y = C["pz_btn"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


@step
def s_rmb_pan_zoom():
    ptr = win().as_pointer()
    pt = mod("ui.panel_toolbar")
    check(f"over 2D Pan/Zoom the right-click opens the 2D bookmarks ({pt._over_camera.get(ptr)})",
          pt._over_camera.get(ptr) == "ALLSET_MT_pt_pan_zoom")
    ev('RIGHTMOUSE', 'PRESS')
    ev('RIGHTMOUSE', 'RELEASE')


@step
def s_menu2_open():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue346_pan_zoom_menu.png"))
    tap('C')            # Create 2D Bookmark (the only row starting with C)


@step
def s_2d_check():
    marks = mod("ui.camera_bookmarks").bookmarks(cam(), True)
    check(f"Create 2D Bookmark in that menu keeps the 2D pan ({[b.name for b in marks]})",
          len(marks) == 1 and abs(marks[0].offset[0] - C["off1"][0]) < 1e-5)
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])


@step
def s_editor():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["editor"] = bpy.ops.allset.camera_bookmark_editor('INVOKE_DEFAULT')
    redraw()


@step
def s_editor_shown():
    check(f"Edit Bookmarks opens the Bookmark Editor ({C['editor']})", C["editor"] == {'FINISHED'})
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue346_bookmark_editor.png"))
    tap('ESC')


run()
