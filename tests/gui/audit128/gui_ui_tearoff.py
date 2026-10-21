"""Audit 128 (UI lane), GitHub issue #4: a torn-off panel / menu window should be sized to its content (Maya: a
floating workspaceControl / torn-off menu is as tall as what it shows). Tears off the Channel Box stack tab, the
Tool Settings dock (Move tool), the Outliner and two Maya menus (File = long, a short one) and records each
floating window's size against the main window. PASSES when short content gives a short window.
Screenshots: audit128_tear_*.png."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import MODULE, check, run, setup, step, win  # noqa: E402

GUI_TIMEOUT = 240
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {"sizes": {}}


def mod(name):
    return import_module(MODULE + name)


def dock():
    return mod(".ui.maya_dock")


def floating():
    return [w for w in bpy.context.window_manager.windows if dock().is_floating(w)]


def shot(name, window=None):
    if SHOTS:
        with bpy.context.temp_override(window=window or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def region(area, kind='WINDOW'):
    return next(r for r in area.regions if r.type == kind)


def in_area(window, area, fn, **kw):
    with bpy.context.temp_override(window=window, screen=window.screen, area=area, region=region(area)):
        return fn(**kw)


def record(key):
    fl = floating()
    if not fl:
        check(f"{key}: a floating window opened", False)
        return None
    w = fl[-1]
    C["sizes"][key] = (w.width, w.height)
    print("AUDIT128 SIZE", key, w.width, w.height, "main", win().width, win().height)
    return w


def close_all():
    for w in floating():
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


def menu_id(label):
    for name in dir(bpy.types):
        if name.startswith("ALLSET_MT_") and "proxy" not in name:
            cls = getattr(bpy.types, name)
            if getattr(cls, "bl_label", "") == label and name.count("_") <= 3:
                return name
    return None


@step
def s_setup():
    setup()
    bpy.ops.allset.make_maya(open_layout=False)
    bpy.ops.allset.layout_install()
    bpy.ops.wm.read_homefile(app_template="Maya_Workflow_Kit")


@step
def s_cb():
    bpy.ops.allset.keymap_activate()
    bpy.context.window_manager.allset_dock = 'CHANNEL_BOX'
    in_area(win(), dock().find_stack(win().screen), bpy.ops.allset.dock_handle)


@step
def s_cb_rec():
    w = record("channel_box")
    if w:
        shot("audit128_tear_cb.png", w)
    close_all()


@step
def s_tool():
    bpy.ops.allset.editor_toggle(editor='TOOL_SETTINGS')


@step
def s_tool2():
    td = mod(".ui.tool_dock")
    area = td.find(win().screen)
    if area is not None:
        in_area(win(), area, bpy.ops.allset.dock_handle)


@step
def s_tool_rec():
    w = record("tool_settings")
    if w:
        shot("audit128_tear_tool.png", w)
    close_all()


@step
def s_menu_long():
    C["file"] = menu_id("File")
    print("AUDIT128 menus", C["file"], [(n, getattr(bpy.types, n).bl_label) for n in dir(bpy.types)
                                       if n.startswith("ALLSET_MT_") and n.count("_") <= 3][:60])
    with bpy.context.temp_override(window=win()):
        dock().tear_menu(bpy.context, C["file"], "File")


@step
def s_menu_long_rec():
    w = record("menu_file")
    if w:
        shot("audit128_tear_menu_file.png", w)
    close_all()


@step
def s_menu_short():
    # Maya's Help-like short menus: pick the first label that exists
    for label in ("Cache", "Help", "Arnold", "Lighting/Shading"):
        C["short"] = menu_id(label)
        if C["short"]:
            C["short_label"] = label
            break
    with bpy.context.temp_override(window=win()):
        dock().tear_menu(bpy.context, C["short"], C["short_label"])


@step
def s_menu_short_rec():
    w = record("menu_short")
    if w:
        shot("audit128_tear_menu_short.png", w)


@step
def s_checks():
    s = C["sizes"]
    main_h = win().height
    print("AUDIT128 SIZES", s, "main", win().width, main_h)
    if "menu_short" in s and "menu_file" in s:
        check(f"a short torn-off menu ({C.get('short_label')}) gets a shorter window than the long File menu "
              f"({s['menu_short']} vs {s['menu_file']})", s['menu_short'][1] < s['menu_file'][1] - 50)
    if "menu_short" in s:
        check(f"a short torn-off menu window is not near full window height ({s['menu_short'][1]} of {main_h})",
              s['menu_short'][1] < 0.5 * main_h)
    if "tool_settings" in s:
        check(f"floating Tool Settings (Move) is sized to its content, not the full dock height "
              f"({s['tool_settings'][1]} of {main_h})", s['tool_settings'][1] < 0.6 * main_h)
    close_all()


run()
