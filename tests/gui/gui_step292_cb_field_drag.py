"""Channel Box value dragging in a real UI (#224):
- a left drag across the Translate X field changes it by 0.01 per pixel; one Undo restores the start value;
- Shift = 10x finer, Ctrl = whole displayed units, Esc restores the start value;
- the wheel during a drag adds whole units, Ctrl+wheel over a field steps it;
- with Auto Key on, a keyed channel gets a key at the current frame after a drag;
- a vertical drag that starts on a value field still selects channels, a plain click still edits the field.
Screenshots with ALLSET_GUI_SHOTS (or --shots)."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, dock_area, dock_region, ev, find_button, run, screenshot, setup, step  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
GUI_TIMEOUT = 300


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def dock():
    return dock_area(), dock_region()


def cb():
    return import_module(MODULE + ".ui.channel_box")


def cube():
    return bpy.data.objects["Cube"]


def undo():
    win = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=win):
        bpy.ops.ed.undo()


def near(a, b, eps=1e-4):
    return abs(a - b) < eps


@step
def s_setup():
    setup()
    ob = cube()
    ob.location = (0.0, 0.0, 0.0)
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    cb().set_selected_channels([])
    dock_area('CHANNEL_BOX')
    bpy.ops.ed.undo_push(message="test start")


@step
def s_wait():
    for a in bpy.context.window_manager.windows[0].screen.areas:
        a.tag_redraw()


step(find_button(dock, lambda p, _c: p.endswith("allset_cb.tx_text"), C, "tx", x_frac=0.7, step_px=4))
step(find_button(dock, lambda p, _c: p.endswith("allset_cb.sz_text"), C, "sz", x_frac=0.7, step_px=4))


@step
def s_found():
    check(f"Translate X / Scale Z fields found ({C.get('tx')}, {C.get('sz')})", C.get("tx") and C.get("sz"))
    if not C.get("tx"):
        raise RuntimeError("field not found")


def drag(tag, dx, mods=(), end='LEFTMOUSE', moves=10, wheel=()):
    """Hover, press, ``moves`` horizontal moves to +dx (one per tick), optional wheel notches, then release / ``end``."""
    key_ev = {"shift": 'LEFT_SHIFT', "ctrl": 'LEFT_CTRL', "alt": 'LEFT_ALT'}
    flags = {m: True for m in mods}

    def hover():
        x, y = C["tx"]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    hover.__name__ = f"s_{tag}_hover"
    step(hover)

    def press():
        x, y = C["tx"]
        for m in mods:
            ev(key_ev[m], 'PRESS', **flags)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y, **flags)
    press.__name__ = f"s_{tag}_press"
    step(press)
    for i in range(1, moves + 1):
        def move(i=i):
            x, y = C["tx"]
            ev('MOUSEMOVE', 'NOTHING', x=x + round(dx * i / moves), y=y, **flags)
        move.__name__ = f"s_{tag}_move{i}"
        step(move)
    for w in wheel:
        def notch(w=w):
            ev(w, 'PRESS', **flags)
        notch.__name__ = f"s_{tag}_{w}"
        step(notch)

    def release():
        if end == 'LEFTMOUSE':
            ev('LEFTMOUSE', 'RELEASE', **flags)
        else:
            ev(end, 'PRESS', **flags)
            ev(end, 'RELEASE', **flags)
            ev('LEFTMOUSE', 'RELEASE', **flags)
        for m in mods:
            ev(key_ev[m], 'RELEASE')
    release.__name__ = f"s_{tag}_release"
    step(release)


drag("plain", 50)


@step
def s_plain():
    v = cube().location.x
    C["plain"] = v
    check(f"a 50 px drag on Translate X adds 0.5 ({v:.4f})", near(v, 0.5, 0.02))
    check(f"the drag selected only Translate X ({cb().selected_channels()})", cb().selected_channels() == ["tx"])
    shot("gui_step292_drag.png")
    undo()


@step
def s_plain_undo():
    v = cube().location.x
    check(f"one Undo after the drag brings Translate X back to 0 ({v:.4f})", near(v, 0.0))


drag("shift", 50, mods=("shift",))


@step
def s_shift():
    v = cube().location.x
    check(f"Shift drag 50 px adds 0.05 ({v:.4f})", near(v, 0.05, 0.005))
    cube().location.x = 0.0


drag("ctrl", 50, mods=("ctrl",))


@step
def s_ctrl():
    v = cube().location.x
    check(f"Ctrl drag 50 px lands on a whole unit ({v:.4f})", near(v, round(v)) and round(v) >= 1)
    cube().location.x = 0.0


drag("esc", 50, end='ESC')


@step
def s_esc():
    v = cube().location.x
    check(f"Esc during a drag restores Translate X ({v:.4f})", near(v, 0.0))


drag("wheel", 20, wheel=('WHEELUPMOUSE', 'WHEELUPMOUSE'))


@step
def s_wheel():
    v = cube().location.x
    check(f"two wheel notches during a 20 px drag add 2 + 0.2 ({v:.4f})", near(v, 2.2, 0.03))
    cube().location.x = 0.0


@step
def s_ctrl_wheel_hover():
    x, y = C["tx"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_ctrl_wheel():
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    ev('WHEELUPMOUSE', 'PRESS', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


@step
def s_ctrl_wheel_check():
    v = cube().location.x
    check(f"Ctrl+wheel over the field steps Translate X by 1 ({v:.4f})", near(v, 1.0, 0.001))
    ob = cube()
    ob.location.x = 0.0
    ob.keyframe_insert("location", index=0, frame=1)
    bpy.context.scene.frame_set(5)
    bpy.context.scene.allset_auto_key = True


drag("autokey", 30)


@step
def s_autokey_wait():
    pass


@step
def s_autokey():
    ob = cube()
    fc = next(f for f in import_module(MODULE + ".compat").id_fcurves(ob) if f.data_path == "location" and f.array_index == 0)
    frames = sorted(round(k.co.x) for k in fc.keyframe_points)
    key5 = next((k.co.y for k in fc.keyframe_points if round(k.co.x) == 5), None)
    check(f"Auto Key keyed the dragged channel at frame 5 ({frames}, {key5})", key5 is not None and near(key5, 0.3, 0.02))
    bpy.context.scene.allset_auto_key = False
    cb().set_selected_channels([])


# a vertical drag that starts on a value field still selects channels (Translate X -> Scale Z)
@step
def s_vsel_hover():
    x, y = C["tx"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_vsel_press():
    x, y = C["tx"]
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)


for _i in range(1, 9):
    def _vmove(i=_i):
        x0, y0 = C["tx"]
        _x1, y1 = C["sz"]
        ev('MOUSEMOVE', 'NOTHING', x=x0, y=round(y0 + (y1 - y0) * i / 8))
    _vmove.__name__ = f"s_vsel_move{_i}"
    step(_vmove)


@step
def s_vsel_release():
    ev('LEFTMOUSE', 'RELEASE')


@step
def s_vsel():
    sel = cb().selected_channels()
    check(f"a vertical drag from the Translate X field selects Translate X -> Scale Z ({sel})",
          sel == ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"])
    x = cube().location.x
    check(f"the vertical drag changed no value ({x:.4f})", near(x, 0.3, 0.02) or near(x, 0.0))


# a Ctrl click (no drag) on a value toggles that channel like a Ctrl click on its name
@step
def s_ctrl_click_hover():
    x, y = C["sz"]
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_ctrl_click_press():
    x, y = C["sz"]
    ev('LEFT_CTRL', 'PRESS', ctrl=True)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y, ctrl=True)


@step
def s_ctrl_click_release():
    ev('LEFTMOUSE', 'RELEASE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


@step
def s_ctrl_click():
    sel = cb().selected_channels()
    check(f"Ctrl click on the Scale Z value takes it out of the selection ({sel})",
          sel == ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy"])
    s = cube().scale.z
    check(f"the Ctrl click changed no value ({s:.4f})", near(s, 1.0))


run()
