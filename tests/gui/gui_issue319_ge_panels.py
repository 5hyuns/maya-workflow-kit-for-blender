"""#319: Maya's modular editor windows in a real UI. Windows > Animation Editors > Graph Editor opens a floating
window (its header shows the kit's handle, no Panels menu); Dock Bottom closes it and puts a Graph Editor of the
window's height under the main viewport with the window's settings; the pane's Panels > Tear Off... opens it in a
window again and leaves a 3D View in the pane; Dock Left docks it at the left; Panels > Tear Off Copy... opens a
second window and keeps the pane; Panels > Panel > Outliner turns the pane into an Outliner."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, win  # noqa: E402

GUI_TIMEOUT = 240
C = {}
TOL = 6          # px: split borders


def mod(name):
    return import_module(MODULE + name)


def others():
    return [w for w in bpy.context.window_manager.windows if w != win()]


def areas(ui_type):
    return [a for a in win().screen.areas if a.ui_type == ui_type]


def v3d():
    area = max((a for a in win().screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def rect(a):
    return (a.x, a.y, a.width, a.height)


def region(area, kind):
    return next(r for r in area.regions if r.type == kind)


def in_window(w, fn, **kw):
    a = w.screen.areas[0]
    with bpy.context.temp_override(window=w, screen=w.screen, area=a, region=region(a, 'WINDOW')):
        return fn(**kw)


def close_others():
    for w in others():
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_open_window():
    C["n_view"] = len(areas('VIEW_3D'))
    area, reg = v3d()
    with bpy.context.temp_override(window=win(), area=area, region=reg):
        C["open"] = bpy.ops.allset.open_editor(ui_type='FCURVES')


@step
def s_window_is_floating_editor():
    new = others()
    check(f"Graph Editor window opened ({C['open']}, {len(new)} new)", len(new) == 1)
    if not new:
        return
    w = new[0]
    C["w"] = w
    a = w.screen.areas[0]
    check(f"... showing the Graph Editor ({a.ui_type})", a.ui_type == 'FCURVES')
    ep = mod(".ui.editor_panels")
    with bpy.context.temp_override(window=w, screen=w.screen, area=a):
        check("the window is a floating editor (handle, no Panels menu)",
              ep.floating_editor(bpy.context) == "Graph Editor" and not ep.is_pane(bpy.context))
    a.spaces.active.show_cursor = False          # a setting the dock must carry over
    a.spaces.active.dopesheet.show_hidden = True
    C["h"], C["wd"] = w.height, w.width
    C["target"] = rect(v3d()[0])


@step
def s_dock_bottom():
    w = C.get("w")
    if w is None:
        return
    C["res"] = in_window(w, bpy.ops.allset.editor_dock, side='BOTTOM')
    check(f"Dock Bottom ran ({C['res']})", C["res"] == {'FINISHED'})


@step
def s_docked_bottom():
    check(f"the window closed ({len(others())} other windows)", not others())
    ge = areas('FCURVES')
    check(f"one Graph Editor pane in the main window ({len(ge)})", len(ge) == 1)
    if not ge:
        return
    a = ge[0]
    tx, ty, tw, th = C["target"]
    want = min(0.45 * th, max(0.1 * th, C["h"]))
    check(f"... at the bottom of the viewport's place (y {a.y} == {ty}, x {a.x} == {tx})",
          abs(a.y - ty) <= TOL and abs(a.x - tx) <= TOL)
    check(f"... as wide as the viewport ({a.width} ~ {tw})", abs(a.width - tw) <= TOL)
    check(f"... about the window's height ({a.height} ~ {want:.0f}, window {C['h']})", abs(a.height - want) <= 0.1 * th)
    sp = a.spaces.active
    check("... with the window's settings (cursor off, hidden shown)",
          sp.show_cursor is False and sp.dopesheet.show_hidden is True)
    v, r = v3d()
    check(f"the viewport sits above it (view y {v.y} >= {a.y + a.height - TOL})", v.y >= a.y + a.height - TOL)


@step
def s_tear_off():
    ge = areas('FCURVES')
    if not ge:
        return
    a = ge[0]
    C["pane"] = rect(a)
    C["n_view2"] = len(areas('VIEW_3D'))
    with bpy.context.temp_override(window=win(), screen=win().screen, area=a, region=region(a, 'HEADER')):
        C["tear"] = bpy.ops.allset.panel_run(op="allset.panel_tear_off", props='{"copy": false}')


@step
def s_torn_off():
    new = others()
    check(f"Tear Off... opened a window ({C.get('tear')}, {len(new)} new)", len(new) == 1)
    check(f"... the pane is a 3D View now ({len(areas('FCURVES'))} Graph Editors, {len(areas('VIEW_3D'))} views)",
          not areas('FCURVES') and len(areas('VIEW_3D')) == C.get("n_view2", 0) + 1)
    if new:
        w = new[0]
        a = w.screen.areas[0]
        check(f"... showing the Graph Editor with its settings ({a.ui_type})",
              a.ui_type == 'FCURVES' and a.spaces.active.show_cursor is False)
        px, py, pw, ph = C["pane"]
        check(f"... about the pane's size ({w.width}x{w.height} ~ {pw}x{ph})",
              abs(w.width - pw) <= 40 and abs(w.height - ph) <= 60)
        wp = mod(".ui.window_places")
        check("... remembered as the Graph Editor window's place", wp.place("editor:FCURVES") is not None)
        C["w2"] = w


@step
def s_dock_left():
    w = C.get("w2")
    if w is None:
        return
    C["wd2"] = w.width
    C["target2"] = rect(v3d()[0])
    C["res2"] = in_window(w, bpy.ops.allset.editor_dock, side='LEFT')


@step
def s_docked_left():
    if "target2" not in C:
        return
    check(f"Dock Left closed the window ({C.get('res2')}, {len(others())} others)", not others())
    ge = areas('FCURVES')
    check(f"one Graph Editor pane again ({len(ge)})", len(ge) == 1)
    if not ge:
        return
    a = ge[0]
    tx, ty, tw, th = C["target2"]
    want = min(0.45 * tw, max(0.1 * tw, C["wd2"]))
    check(f"... at the left of the viewport's place (x {a.x} == {tx}, y {a.y} == {ty})",
          abs(a.x - tx) <= TOL and abs(a.y - ty) <= TOL)
    check(f"... about the window's width ({a.width} ~ {want:.0f})", abs(a.width - want) <= 0.1 * tw)


@step
def s_tear_off_copy():
    ge = areas('FCURVES')
    if not ge:
        return
    a = ge[0]
    with bpy.context.temp_override(window=win(), screen=win().screen, area=a, region=region(a, 'HEADER')):
        C["copy"] = bpy.ops.allset.panel_run(op="allset.panel_tear_off", props='{}')


@step
def s_copied():
    if "copy" not in C:
        return
    new = others()
    check(f"Tear Off Copy... opened a window ({C.get('copy')}, {len(new)} new)", len(new) == 1)
    check(f"... and the pane keeps its Graph Editor ({len(areas('FCURVES'))})", len(areas('FCURVES')) == 1)
    if new:
        check("... the window shows a Graph Editor", new[0].screen.areas[0].ui_type == 'FCURVES')
    close_others()


@step
def s_panel_submenu():
    ge = areas('FCURVES')
    if not ge:
        return
    a = ge[0]
    with bpy.context.temp_override(window=win(), screen=win().screen, area=a, region=region(a, 'HEADER')):
        res = bpy.ops.allset.hb_pane(ui_type='OUTLINER')
    check(f"Panels > Panel > Outliner turns the pane into an Outliner ({res}, {a.ui_type})",
          res == {'FINISHED'} and a.ui_type == 'OUTLINER')


run()
