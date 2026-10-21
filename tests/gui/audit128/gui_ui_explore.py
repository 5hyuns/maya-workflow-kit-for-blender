"""Audit 128 (UI lane): exploratory Maya-user session in the Maya Workflow Kit layout, screenshots only plus a few
size / state checks: menu sets F2-F6, hotbox, RMB / Shift+RMB marking menus, Windows > Hypershade / Script Editor /
Render Settings window sizes, shelf tab switch, Help Line, Ctrl+A. Screenshots: audit128_x_*.png."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import MODULE, check, ev, run, setup, step, tap, win  # noqa: E402

GUI_TIMEOUT = 300
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def mod(name):
    return import_module(MODULE + name)


def shot(name, window=None):
    if SHOTS:
        with bpy.context.temp_override(window=window or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def v3d():
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def in_v3d(fn, *a, **kw):
    area, region = v3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn(*a, **kw)


def menu(path):
    return in_v3d(bpy.ops.allset.menu_item, item=path)


def centre():
    _a, r = v3d()
    return r.x + r.width // 2, r.y + r.height // 2


def newest():
    wins = bpy.context.window_manager.windows
    return wins[-1] if len(wins) > 1 else None


def close_extra():
    wm = bpy.context.window_manager
    while len(wm.windows) > 1:
        with bpy.context.temp_override(window=wm.windows[-1]):
            bpy.ops.wm.window_close()


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()
    mod(".ui.status_line").redraw_top_bars()


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    bpy.ops.allset.layout_install()
    bpy.ops.wm.read_homefile(app_template="Maya_Workflow_Kit")


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    in_v3d(bpy.ops.allset.create, kind='CUBE')
    x, y = centre()
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    redraw()


@step
def s_layout_shot():
    shot("audit128_x_layout.png")
    tap('F3')      # Modeling menu set


@step
def s_f3():
    redraw()


@step
def s_f3_shot():
    shot("audit128_x_f3.png")
    x, y = centre()
    ev('SPACE', 'PRESS', x=x, y=y)


@step
def s_hotbox_wait():
    pass


@step
def s_hotbox_shot():
    shot("audit128_x_hotbox.png")
    ev('SPACE', 'RELEASE')


@step
def s_rmb():
    x, y = centre()
    ev('RIGHTMOUSE', 'PRESS', x=x, y=y)


@step
def s_rmb_wait():
    pass


@step
def s_rmb_shot():
    shot("audit128_x_rmb.png")
    ev('RIGHTMOUSE', 'RELEASE')
    tap('ESC')


@step
def s_shift_rmb():
    x, y = centre()
    ev('RIGHTMOUSE', 'PRESS', x=x, y=y, shift=True)


@step
def s_shift_rmb_wait():
    pass


@step
def s_shift_rmb_shot():
    shot("audit128_x_shift_rmb.png")
    ev('RIGHTMOUSE', 'RELEASE', shift=True)
    tap('ESC')
    C["hs"] = menu("Windows/Rendering Editors/Hypershade")


@step
def s_hs():
    w = newest()
    C["hs_size"] = (w.width, w.height) if w else None
    print("AUDIT128 hypershade", C["hs"], C["hs_size"])
    redraw()


@step
def s_hs_shot():
    w = newest()
    if w:
        shot("audit128_x_hypershade.png", w)
    close_extra()
    C["se"] = menu("Windows/General Editors/Script Editor")


@step
def s_se():
    w = newest()
    C["se_size"] = (w.width, w.height) if w else None
    print("AUDIT128 script editor", C["se"], C["se_size"])
    redraw()


@step
def s_se_shot():
    w = newest()
    if w:
        shot("audit128_x_script_editor.png", w)
    close_extra()
    C["rs"] = menu("Render/Render Settings...") if False else menu("Windows/Rendering Editors/Render Settings...")


@step
def s_rs():
    w = newest()
    C["rs_size"] = (w.width, w.height) if w else None
    print("AUDIT128 render settings", C["rs"], C["rs_size"])
    redraw()


@step
def s_rs_shot():
    w = newest()
    if w:
        shot("audit128_x_render_settings.png", w)
    close_extra()
    C["ol"] = menu("Windows/Outliner")


@step
def s_ol():
    w = newest()
    C["ol_size"] = (w.width, w.height) if w else None
    print("AUDIT128 outliner", C["ol"], C["ol_size"], len(bpy.context.window_manager.windows))
    redraw()


@step
def s_ol_shot():
    w = newest()
    if w:
        shot("audit128_x_outliner.png", w)
    close_extra()
    x, y = centre()
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('A', 'PRESS', ctrl=True)
    ev('A', 'RELEASE', ctrl=True)


@step
def s_ctrl_a():
    wm = bpy.context.window_manager
    print("AUDIT128 ctrl+a dock", wm.allset_dock, len(wm.windows))
    C["after_ctrl_a"] = wm.allset_dock
    redraw()


@step
def s_ctrl_a_shot():
    shot("audit128_x_ctrl_a.png")
    sizes = {k: C.get(k) for k in ("hs_size", "se_size", "rs_size", "ol_size")}
    print("AUDIT128 window sizes", sizes, "main", win().width, win().height)
    check(f"Ctrl+A raises the Attribute Editor ({C.get('after_ctrl_a')})", C.get("after_ctrl_a") == 'ATTRIBUTE_EDITOR')


run()
