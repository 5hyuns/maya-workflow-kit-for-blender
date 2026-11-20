"""#409 in a real UI (Maya Workflow Kit layout, a view that looks through a camera with an image plane):

- a right-click on the panel toolbar's Image Plane button opens its menu (Import Image..., Display Mode, Delete:
  imagePlane1); its Import Image... opens the file browser and leaves the camera's image plane shown;
- View > Image Plane opens Import Image..., Import Movie..., Image Plane Attributes; its Import Movie... opens the
  file browser. Shots with ``--shots``."""

import os
import sys
import tempfile
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, button_under_mouse, check, ev, load_maya_layout, run, screenshot, setup, step, tap, view3d, win  # noqa: E402

GUI_TIMEOUT = 240
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
FOLDER = tempfile.mkdtemp(prefix="gui409_")
C = {}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def header():
    area, _r = view3d()
    return area, next(r for r in area.regions if r.type == 'TOOL_HEADER')


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def again(fn, cond, limit=40):
    n = C.setdefault("wait_" + fn.__name__, 0)
    if not cond() and n < limit:
        C["wait_" + fn.__name__] = n + 1
        sim._steps.insert(0, fn)
        return True
    return False


def file_browser():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == 'FILE_BROWSER' and a.spaces.active.params is not None \
                    and a.spaces.active.active_operator is not None:
                return w, a
    return None, None


def close_browser():
    w, a = file_browser()
    if a is None:
        return
    r = next(r for r in a.regions if r.type == 'WINDOW')
    x, y = r.x + r.width // 2, r.y + r.height // 2
    w.event_simulate(type='MOUSEMOVE', value='NOTHING', x=x, y=y)
    w.event_simulate(type='ESC', value='PRESS', x=x, y=y)
    w.event_simulate(type='ESC', value='RELEASE', x=x, y=y)


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    png = os.path.join(FOLDER, "ref409.png")
    img = bpy.data.images.new("ref409.png", 200, 100)
    img.filepath_raw = png
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CAMERA')
        C["cam"] = bpy.context.view_layer.objects.active.name
        bpy.ops.allset.panel_look_through(camera=C["cam"])
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.image_plane('EXEC_DEFAULT', filepath=png)
    C["plane"] = next(ob.name for ob in bpy.data.objects if ob.type == 'EMPTY' and ob.parent is not None
                      and ob.parent.name == C["cam"])
    C["n"] = len(bpy.data.objects)
    redraw()


@step
def s_settle():
    redraw()


def sweep():
    """Left to right along the tool header's middle, 3 px a tick: the x of the Image Plane button."""
    state = {}

    def look():
        area, region = header()
        if not state:
            state["x"] = region.x + 2
        else:
            _path, cmd = button_under_mouse(area, region)
            if "image_plane" in cmd and "btn" not in C:
                C["btn"] = (state["x"] + 4, region.y + region.height // 2)
            state["x"] += 3
            if "btn" in C or state["x"] > region.x + region.width // 2:
                return
        ev('MOUSEMOVE', 'NOTHING', x=state["x"], y=region.y + region.height // 2)
        sim._steps.insert(0, look)
    return look


step(sweep())


@step
def s_found():
    check(f"found the Image Plane button {C.get('btn')} in the panel toolbar", "btn" in C)
    if "btn" in C:
        x, y = C["btn"]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('MOUSEMOVE', 'NOTHING', x=x + 1, y=y)


@step
def s_rmb():
    ptr = win().as_pointer()
    pt = mod("ui.panel_toolbar")
    check(f"over Image Plane the right-click is watched ({pt._over_camera.get(ptr)})",
          pt._over_camera.get(ptr) == "ALLSET_MT_pt_image_plane" and ptr in pt._watching)
    ev('RIGHTMOUSE', 'PRESS')
    ev('RIGHTMOUSE', 'RELEASE')


@step
def s_rmb_open():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue409_button_menu.png"))
    tap('I')            # the menu's underlined letter of its first row, Import Image...


@step
def s_rmb_import():
    if again(s_rmb_import, lambda: file_browser()[0] is not None):
        return
    ob = bpy.data.objects.get(C["plane"])
    check("the right-click menu's Import Image... opens the file browser", file_browser()[0] is not None)
    check("... and the camera's image plane stays shown", ob is not None and not ob.hide_get())
    close_browser()


@step
def s_view_menu():
    if again(s_view_menu, lambda: file_browser()[0] is None):
        return
    check("cancelling makes nothing", len(bpy.data.objects) == C["n"])
    _a, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.call_menu(name="ALLSET_MT_panel_image_plane")


@step
def s_view_open():
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue409_view_menu.png"))
    tap('M')            # Import Movie...


@step
def s_movie_browser():
    if again(s_movie_browser, lambda: file_browser()[0] is not None):
        return
    w, a = file_browser()
    op = a.spaces.active.active_operator if a is not None else None
    check(f"View > Image Plane > Import Movie... opens the file browser for movies "
          f"({getattr(op, 'filter_movie', None)})", op is not None and op.filter_movie and not op.filter_image)
    close_browser()


@step
def s_done():
    if again(s_done, lambda: file_browser()[0] is None):
        return
    check("nothing made, the image plane still shown",
          len(bpy.data.objects) == C["n"] and not bpy.data.objects[C["plane"]].hide_get())


run()
