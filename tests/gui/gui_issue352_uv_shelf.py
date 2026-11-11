"""#352 in a real UI: the UV Editing shelf's UV Editor button opens the UV Editor in its own window, like
Windows > UV Editor, and the shelf row stays a shelf. A shelf row an older version switched to the UV Editor no longer
counts as the UV Editor (Windows > UV Editor opens a window) and shows the shelf again after a file load; the
hotbox's panel switch leaves the Status Line / Shelf strips alone."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, scale, step, setup, screenshot, win, load_maya_layout  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
shelf = import_module(MODULE + ".ui.shelf")
uv_tools = import_module(MODULE + ".operators.uv_tools")


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def row():
    return shelf.shelf_row_area(win().screen)


def row_space():
    return row().spaces.active


def icon_centre(slot):
    area = row()
    r = next(r for r in area.regions if r.type == 'WINDOW')
    x, y, size = shelf.icon_rect(r, slot, scale())
    return round(r.x + x + size / 2), round(r.y + y + size / 2)


def windows():
    return list(bpy.context.window_manager.windows)


def uv_areas(window):
    return [a for a in window.screen.areas if a.ui_type == 'UV']


def close_extra_windows():
    for w in windows()[1:]:
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    bpy.ops.allset.keymap_activate()
    bpy.ops.allset.make_maya(open_layout=False)
    bpy.ops.allset.create(kind='CUBE')
    bpy.ops.allset.shelf_select(shelf="UVEditing")
    redraw()


@step
def s_hover():
    C["mode0"] = row_space().mode
    C["n0"] = len(windows())
    _cur, buttons = shelf.icon_buttons(bpy.context)
    C["slot"] = next(k for k, b in enumerate(buttons) if b[1].startswith("UV Editor"))
    x, y = icon_centre(C["slot"])
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    redraw()


@step
def s_click():
    ev('LEFTMOUSE', 'PRESS')
    ev('LEFTMOUSE', 'RELEASE')


for _k in range(4):         # the window opens on a later tick
    step(lambda: None)


@step
def s_click_check():
    check(f"the shelf row is still a shelf ({C['mode0']} -> {row_space().mode}, ui_type {row().ui_type})",
          C["mode0"] == 'VIEW' and row_space().mode == 'VIEW' and shelf.is_shelf_row(row_space()))
    check("the main window has no UV Editor area", not uv_areas(win()))
    new = windows()[C["n0"]:]
    check(f"the shelf button opened one new window ({C['n0']} -> {len(windows())})", len(new) == 1)
    check("the new window shows the UV Editor", bool(new) and bool(uv_areas(new[0])))
    w, a = uv_tools.find_uv_editor(bpy.context)
    check("the kit finds the UV Editor in the new window", bool(new) and w == new[0] and a is not None)
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue352_after_click.png"))
    close_extra_windows()


@step
def s_old_broken_row():
    # what the old button did: the shelf row (an Image Editor) switched to the UV Editor
    row_space().mode = 'UV'
    C["n1"] = len(windows())
    w, a = uv_tools.find_uv_editor(bpy.context)
    check("a shelf row in UV mode is not taken for the UV Editor", w is None and a is None)
    bpy.ops.allset.open_editor(ui_type='UV')


for _k in range(4):
    step(lambda: None)


@step
def s_old_broken_check():
    new = windows()[C["n1"]:]
    check(f"Windows > UV Editor opens its own window, not the shelf ({C['n1']} -> {len(windows())})",
          len(new) == 1 and bool(uv_areas(new[0])))
    close_extra_windows()
    shelf.settle_rows()            # runs after a file load / when the kit starts
    check(f"the shelf row shows the shelf again ({row_space().mode})", row_space().mode == 'VIEW')
    strip = shelf.strip_area(win().screen)
    strip.spaces.active.mode = 'UV'
    shelf.settle_rows()
    check(f"the Status Line strip too ({strip.spaces.active.mode})", strip.spaces.active.mode == 'VIEW')


@step
def s_hotbox_pane_on_row():
    area = row()
    with bpy.context.temp_override(window=win(), area=area,
                                   region=next(r for r in area.regions if r.type == 'WINDOW')):
        res = bpy.ops.allset.hb_pane(ui_type='UV')
    check(f"the hotbox panel switch leaves the shelf row alone ({res}, {row_space().mode})",
          res == {'CANCELLED'} and row_space().mode == 'VIEW' and row().ui_type != 'UV')
    from sim import view3d
    v3d, r = view3d()
    with bpy.context.temp_override(window=win(), area=v3d, region=r):
        res = bpy.ops.allset.hb_pane(ui_type='UV')
    check(f"on a viewport panel it still switches the panel ({res})", res == {'FINISHED'} and v3d.ui_type == 'UV')
    v3d.ui_type = 'VIEW_3D'


run()
