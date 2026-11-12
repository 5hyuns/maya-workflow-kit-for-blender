"""#357: Visualize > Blue Pencil in the Maya layout — drawn frames get Maya's light blue marks on the Time Slider,
Alt+< / Alt+> jump between them, the nearest frames' drawings show as ghosts, and Tool Settings offers Pencil / Line /
Eraser."""

import os
import sys
from importlib import import_module

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def bp():
    return import_module(MODULE + ".ui.blue_pencil")


def view():
    return import_module(MODULE + ".ui.status_line").main_view3d(win().screen)


def timeline():
    area = next(a for a in win().screen.areas if a.type == 'DOPESHEET_EDITOR' and a.ui_type == 'TIMELINE')
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def at(fx, fy):
    _a, r = view()
    return int(r.x + r.width * fx), int(r.y + r.height * fy)


def shot(name):
    path = os.path.join(SHOTS or bpy.app.tempdir, f"gui_issue357_{name}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)          # bottom line first


def stroke(fx0, fy0, fx1, fy1):
    steps = []

    def press():
        x, y = at(fx0, fy0)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    steps.append(press)
    for i in range(1, 9):
        def mv(i=i):
            x = at(fx0 + (fx1 - fx0) * i / 8, 0)[0]
            y = at(0, fy0 + (fy1 - fy0) * i / 8)[1]
            ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        steps.append(mv)

    def release():
        x, y = at(fx1, fy1)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
    steps.append(release)
    return steps


def redraw():
    for area in win().screen.areas:
        area.tag_redraw()


def idle():
    pass


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_tool():
    bpy.ops.allset.keymap_activate()
    bpy.context.scene.frame_set(1)
    area, region = view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.menu_item(item="Visualize/Blue Pencil")


for _f in stroke(0.35, 0.40, 0.55, 0.40):
    step(_f)


@step
def s_frame10():
    bpy.context.scene.frame_set(10)


for _f in stroke(0.35, 0.65, 0.55, 0.65):
    step(_f)


@step
def s_frames():
    frames = bp().frame_numbers(bpy.context.scene)
    check(f"two Blue Pencil frames drawn ({frames})", frames == [1, 10])
    bpy.context.scene.frame_set(5)
    redraw()


step(idle)


@step
def s_marks_and_ghost_on():
    px = shot("ghost_on_f5")
    area, region = timeline()
    ts = import_module(MODULE + ".ui.time_slider")
    s = bpy.context.preferences.system.ui_scale
    y0 = ts._rows("tick", region.height, ts.ROWS, s)[0]
    k = min(region.height / ts.MAYA_RULER_H, s)
    want = np.array(bp().FRAME_RGB[:3])
    ok = []
    for f in (1, 10):
        tri = ts.blue_pencil_marks(region, [f], y0, k)
        if not tri:
            ok.append(False)
            continue
        cx = sum(p[0] for p in tri) / 3
        cy = sum(p[1] for p in tri) / 3
        got = px[region.y + int(cy), region.x + int(cx), :3]
        ok.append(bool(np.abs(got - want).max() < 0.06))
        C[f"mark{f}"] = tuple(round(float(c), 3) for c in got)
    check(f"Time Slider marks frames 1 and 10 in Maya's light blue ({C})", all(ok))
    _a, r = view()
    x0, x1 = at(0.36, 0)[0], at(0.54, 0)[0]
    y = at(0, 0.65)[1]
    C["ghost_on"] = px[y - 3:y + 4, x0:x1, :3].copy()
    prefs = import_module(MODULE + ".preferences").get()
    prefs.bp_ghost_next = False
    redraw()


step(idle)


@step
def s_ghost_off():
    px = shot("ghost_off_f5")
    x0, x1 = at(0.36, 0)[0], at(0.54, 0)[0]
    y = at(0, 0.65)[1]
    off = px[y - 3:y + 4, x0:x1, :3]
    diff = float(np.abs(C["ghost_on"] - off).max())
    check(f"Ghost Next shows frame 10's drawing at frame 5 (max difference on / off {diff:.3f})", diff > 0.05)
    import_module(MODULE + ".preferences").get().bp_ghost_next = True


@step
def s_alt_lt():
    x, y = at(0.8, 0.8)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFT_ALT', 'PRESS', x=x, y=y, alt=True)
    ev('LEFT_SHIFT', 'PRESS', x=x, y=y, alt=True, shift=True)
    ev('COMMA', 'PRESS', x=x, y=y, alt=True, shift=True)
    ev('COMMA', 'RELEASE', x=x, y=y, alt=True, shift=True)


@step
def s_alt_lt_done():
    x, y = at(0.8, 0.8)
    ev('LEFT_SHIFT', 'RELEASE', x=x, y=y, alt=True)
    ev('LEFT_ALT', 'RELEASE', x=x, y=y)
    check(f"Alt+< from frame 5 goes to frame 1 ({bpy.context.scene.frame_current})",
          bpy.context.scene.frame_current == 1)
    ev('LEFT_ALT', 'PRESS', x=x, y=y, alt=True)
    ev('LEFT_SHIFT', 'PRESS', x=x, y=y, alt=True, shift=True)
    ev('COMMA', 'PRESS', x=x, y=y, alt=True, shift=True)
    ev('COMMA', 'RELEASE', x=x, y=y, alt=True, shift=True)


@step
def s_alt_wrap():
    x, y = at(0.8, 0.8)
    ev('LEFT_SHIFT', 'RELEASE', x=x, y=y, alt=True)
    ev('LEFT_ALT', 'RELEASE', x=x, y=y)
    check(f"Alt+< on the first frame wraps to the last ({bpy.context.scene.frame_current})",
          bpy.context.scene.frame_current == 10)
    ev('LEFT_ALT', 'PRESS', x=x, y=y, alt=True)
    ev('LEFT_SHIFT', 'PRESS', x=x, y=y, alt=True, shift=True)
    ev('PERIOD', 'PRESS', x=x, y=y, alt=True, shift=True)
    ev('PERIOD', 'RELEASE', x=x, y=y, alt=True, shift=True)


@step
def s_alt_gt():
    x, y = at(0.8, 0.8)
    ev('LEFT_SHIFT', 'RELEASE', x=x, y=y, alt=True)
    ev('LEFT_ALT', 'RELEASE', x=x, y=y)
    check(f"Alt+> on the last frame wraps to the first ({bpy.context.scene.frame_current})",
          bpy.context.scene.frame_current == 1)
    area, region = view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.menu_item(item="Windows/General Editors/Tool Settings")


step(idle)
step(idle)


@step
def s_tool_settings():
    shot("tool_settings")
    area, region = view()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.wm.tool_set_by_id(name="builtin.annotate_eraser", space_type='VIEW_3D')
        tool = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False)
    check(f"the Eraser tool is an annotate tool with the Blue Pencil section ({tool.idname})",
          tool.idname in bp().TOOL_IDS)


run()
