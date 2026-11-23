"""In a real UI (#501): a 4 x 4 grid -> UV > UV Editor -> the UV Move tool -> Ctrl+Shift+RMB opens its option marking
menu (ring Symmetry / Step Snap / Keep Spacing / Select) -> release on Step Snap -> UV increment snapping is on; with a
select tool Ctrl+Shift+RMB opens the select option menu, whose Drag/Marquee picks the Drag tool (screenshots)."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, run, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
N = 4


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def grid():
    return bpy.data.objects[C["grid"]]


def uv_window():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.ui_type == 'UV':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


def shot(name, window=None):
    if SHOTS:
        with bpy.context.temp_override(window=window or win()):
            bpy.ops.screen.screenshot(filepath=os.path.join(SHOTS, name))


def uv_ev(type, value, x=None, y=None, **kw):
    """sim.ev for the UV Editor window (keeps sim's simulated key state: the menu engine reads it)."""
    down = sys.modules["sim"]._down
    if value == 'PRESS':
        down.add(type)
    elif value == 'RELEASE':
        down.discard(type)
    w, _a, _r = uv_window()
    if x is None:
        x, y = C["uvpos"]
    C["uvpos"] = (x, y)
    w.event_simulate(type=type, value=value, x=x, y=y, **kw)


def centre():
    _w, _a, r = uv_window()
    return r.x + r.width // 2, r.y + r.height // 2


def redraw_all():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            a.tag_redraw()


def session():
    return mod(".marking.draw").ACTIVE.get("session")


def open_menu_name():
    s = session()
    return getattr(s.stack[0][0].sub, "name", None) if s is not None else None




@step
def s_setup():
    C["x"], C["y"] = setup()
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for ob in list(bpy.data.objects):
            ob.select_set(False)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=N, y_subdivisions=N, size=2.0)
        C["grid"] = bpy.context.active_object.name
        C["open"] = mod(".marking.modal").run_action(bpy.context, mod(".ui.menu_map").MAP["UV/UV Editor"])


@step
def s_wait_uv_window():
    import sim
    C.setdefault("wait_uv", 0)
    if uv_window()[1] is None and C["wait_uv"] < 15:
        C["wait_uv"] += 1
        sim._steps.insert(0, s_wait_uv_window)


@step
def s_opened():
    w, a, r = uv_window()
    check(f"UV > UV Editor: a UV Editor window, grid in edit mode ({C['open']}, {a is not None}, {grid().mode})",
          a is not None and grid().mode == 'EDIT')
    if a is None:
        return
    ts = bpy.context.scene.tool_settings
    ts.use_snap_uv = False
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
        bpy.ops.wm.tool_set_by_id(name="builtin.move", space_type='IMAGE_EDITOR')
    C["uvpos"] = centre()
    uv_ev('MOUSEMOVE', 'NOTHING', *centre())
    redraw_all()


def press():
    x, y = C["c"] = centre()
    uv_ev('MOUSEMOVE', 'NOTHING', x, y)
    uv_ev('LEFT_CTRL', 'PRESS', x, y)
    uv_ev('LEFT_SHIFT', 'PRESS', x, y)
    uv_ev('RIGHTMOUSE', 'PRESS', x, y, ctrl=True, shift=True)


def release(x, y):
    uv_ev('RIGHTMOUSE', 'RELEASE', x, y, ctrl=True, shift=True)
    uv_ev('LEFT_SHIFT', 'RELEASE', x, y)
    uv_ev('LEFT_CTRL', 'RELEASE', x, y)
    redraw_all()


@step
def s_press():
    press()


@step
def s_menu_open():
    name = open_menu_name()
    check(f"Ctrl+Shift+RMB with the UV Move tool opens its option menu (got {name})", name == "UV_OPT_MOVE")
    s = session()
    if s is None:
        return
    ring = {k: it.label for k, it in s.layout.radial.items()}
    check(f"ring: N Symmetry, E Step Snap, SE Keep Spacing, S Select ({ring})",
          ring == {"N": "Symmetry", "E": "Step Snap", "SE": "Keep Spacing", "S": "Select"})
    w, _a, _r = uv_window()
    shot("gui_issue501_uv_move_options.png", w)
    box = s.layout.radial["E"].rect
    x = C["c"][0] + int(s.center[0] - s.press[0] + (box[0] + box[2]) / 2)
    y = C["c"][1] + int(s.center[1] - s.press[1] + (box[1] + box[3]) / 2)
    C["release"] = (x, y)
    uv_ev('MOUSEMOVE', 'NOTHING', x, y, ctrl=True, shift=True)


@step
def s_release():
    release(*C["release"])


@step
def s_step_snap_on():
    ts = bpy.context.scene.tool_settings
    check(f"Step Snap turned the UV increment snap on ({ts.use_snap_uv}, {set(ts.snap_uv_element)})",
          ts.use_snap_uv and 'INCREMENT' in ts.snap_uv_element)
    check("menu closed", not mod(".marking.draw").ACTIVE)
    w, a, r = uv_window()
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box", space_type='IMAGE_EDITOR')
    redraw_all()


@step
def s_select_press():
    press()


@step
def s_select_menu():
    name = open_menu_name()
    check(f"with a select tool the select option menu opens (got {name})", name == "UV_OPT_SELECT")
    w, _a, _r = uv_window()
    shot("gui_issue501_uv_select_options.png", w)
    s = session()
    if s is None:
        return
    box = s.layout.radial["NE"].rect
    x = C["c"][0] + int(s.center[0] - s.press[0] + (box[0] + box[2]) / 2)
    y = C["c"][1] + int(s.center[1] - s.press[1] + (box[1] + box[3]) / 2)
    C["release"] = (x, y)
    uv_ev('MOUSEMOVE', 'NOTHING', x, y, ctrl=True, shift=True)


@step
def s_select_release():
    release(*C["release"])


@step
def s_drag_tool():
    tool = bpy.context.workspace.tools.from_space_image_mode('UV', create=False)
    check(f"Drag/Marquee picks the UV Editor's Drag tool, like the UV Toolkit ({tool and tool.idname})",
          tool is not None and tool.idname == "builtin.select_circle")


@step
def s_end():
    check("menu closed at the end", not mod(".marking.draw").ACTIVE)
    bpy.context.scene.tool_settings.use_snap_uv = False


run()
