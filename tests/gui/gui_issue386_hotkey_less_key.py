"""#386: in a real UI the kit Hotkey Editor's Assign New Hotkey takes the "<" key of German / Nordic keyboards
(Blender's GRLESS) and the "+" key (PLUS), like Blender's own keymap editor: SnapToPointPress (the v hold) gets "<",
its Shift+V row gets "+"; then "<" over the viewport starts the point snap hold."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, view3d, win  # noqa: E402

GUI_TIMEOUT = 150
C = {}


def mod(name):
    return import_module(MODULE + name)


def hk():
    """(window, area, WINDOW region) of the Hotkey Editor, else (None, None, None)."""
    mw = mod(".ui.marked_window")
    w = mw.find_window(bpy.context, "HOTKEY_EDITOR")
    if w is None:
        return None, None, None
    area = next(a for a in w.screen.areas if mw.kind_of(a) == "HOTKEY_EDITOR")
    return w, area, next(r for r in area.regions if r.type == 'WINDOW')


def ev2(type, value, **kw):
    """An event into the Hotkey Editor window (sim.ev always goes to the main window)."""
    w, _a, region = hk()
    kw.setdefault("x", region.x + region.width // 2)
    kw.setdefault("y", region.y + region.height // 2)
    w.event_simulate(type=type, value=value, **kw)


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def snap_rows():
    he = mod(".ui.hotkey_editor")
    return sorted((r for r in he.rows() if r["command"] == "SnapToPointPress"), key=lambda r: r["number"])


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_open():
    bpy.ops.allset.keymap_activate()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        C["open"] = bpy.ops.allset.menu_item(item="Windows/Settings/Preferences/Hotkey Editor")


@step
def s_opened():
    redraw()


@step
def s_search():
    w, _area, _region = hk()
    check(f"the Hotkey Editor is open ({C['open']})", w is not None)
    wm = bpy.context.window_manager
    wm.allset_hk_search = "SnapToPointPress"
    shown = [r.command for r in wm.allset_hk_rows]
    check(f"the search shows SnapToPointPress's two rows ({shown})",
          shown == ["SnapToPointPress", "SnapToPointPress (2nd hotkey)"])
    C["n"] = 0
    redraw()


def _capture(n):
    w, area, region = hk()
    if w is None:
        return
    bpy.context.window_manager.allset_hk_active = n
    ev2('MOUSEMOVE', 'NOTHING')
    with bpy.context.temp_override(window=w, area=area, region=region):
        C["capture"] = bpy.ops.allset.hotkey_assign('INVOKE_DEFAULT')
    redraw()


@step
def s_capture_less():
    _capture(0)


@step
def s_press_less():
    wm = bpy.context.window_manager
    check(f"Assign New Hotkey waits for a key ({C.get('capture')}, capturing={wm.allset_hk_capture})",
          wm.allset_hk_capture)
    if hk()[0] is not None:
        ev2('GRLESS', 'PRESS')
        ev2('GRLESS', 'RELEASE')


@step
def s_less_done():
    he = mod(".ui.hotkey_editor")
    wm = bpy.context.window_manager
    text = he.kit_text(bpy.context, snap_rows()[0])
    check(f'the pressed "<" is the new key ({text!r}, capturing={wm.allset_hk_capture})',
          text == "< *" and not wm.allset_hk_capture)
    if wm.allset_hk_capture:            # end the capture so the next step starts clean
        ev2('ESC', 'PRESS')
        ev2('ESC', 'RELEASE')


@step
def s_capture_plus():
    _capture(1)


@step
def s_press_plus():
    if hk()[0] is not None:
        ev2('PLUS', 'PRESS')
        ev2('PLUS', 'RELEASE')


@step
def s_plus_done():
    he = mod(".ui.hotkey_editor")
    wm = bpy.context.window_manager
    text = he.kit_text(bpy.context, snap_rows()[1])
    check(f'the pressed "+" is the new key ({text!r}, capturing={wm.allset_hk_capture})',
          text == "+ *" and not wm.allset_hk_capture)
    if wm.allset_hk_capture:
        ev2('ESC', 'PRESS')
        ev2('ESC', 'RELEASE')
    w = hk()[0]
    if w is not None:
        with bpy.context.temp_override(window=w):
            bpy.ops.wm.window_close()


@step
def s_viewport():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    ev('MOUSEMOVE', 'NOTHING', x=region.x + region.width // 2, y=region.y + region.height // 2)


@step
def s_hold_less():
    ev('GRLESS', 'PRESS')


@step
def s_holding():
    hold = mod(".operators.hold")
    running = [op.bl_idname for op in win().modal_operators]
    snap = bpy.context.scene.tool_settings
    check(f'"<" over the viewport starts the point snap hold (modal: {running}, snap: {snap.use_snap}, '
          f'{sorted(snap.snap_elements)})', "ALLSET_OT_hold" in running and snap.use_snap
          and "VERTEX" in snap.snap_elements)
    C["hold"] = hold
    ev('GRLESS', 'RELEASE')


@step
def s_released():
    running = [op.bl_idname for op in win().modal_operators]
    check(f'releasing "<" ends the hold ({running})', "ALLSET_OT_hold" not in running)


run()
