"""The option box ❒ of a component command picked in object mode (Edit Mesh > Add Divisions ❒ with a cube selected,
real simulated clicks on the Maya menu bar and the row's ❒): the command runs on the whole mesh, Blender stays in
object mode, and its settings popup (Adjust Last Operation) shows the command's own settings at once; the command is
one undo step, so one Ctrl+Z takes it back and Blender is still in object mode."""

import os
import sys
import tempfile
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, tap, win  # noqa: E402

GUI_TIMEOUT = 300
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {"calls": []}
PATH, ROW = "Edit Mesh/Add Divisions", 1


def mod(name):
    return import_module(MODULE + name)


def oc():
    return mod(".ui.option_click")


def shot_path(name):
    return os.path.join(SHOTS or tempfile.gettempdir(), name + ".png")


def shot(name):
    with bpy.context.temp_override(window=win()):
        bpy.ops.screen.screenshot(filepath=shot_path(name))


def pixels(name):
    import numpy as np
    img = bpy.data.images.load(shot_path(name))
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[:, :, :3]


def unit():
    return mod(".ui.toolbar_fit").unit(bpy.context.preferences.system.ui_scale,
                                       bpy.context.preferences.system.pixel_size)


def top_region():
    area = mod(".ui.status_line")._top_bars.get(win().as_pointer())
    return next(r for r in area.regions if r.type == 'HEADER')


def button_point(label):
    sl = mod(".ui.status_line")
    ms = mod(".ui.menu_sets")
    names, _n = sl.shown_menus(win())
    labels = [getattr(bpy.types, ms.menu_idname(nm)).bl_label for nm in names]
    with bpy.context.temp_override(window=win()):
        widths, _f, _m = sl.menu_bar_widths(bpy.context, list(names), False)
    i = labels.index(label)
    r = top_region()
    left = r.x + int(oc().LEAD_UNITS * unit()) + sum(widths[:i])
    return left + widths[i] // 2, r.y + r.height // 2


def row_y(k):
    return top_region().y - int(0.48 * unit()) - k * unit()


def zone(path):
    with bpy.context.temp_override(window=win(), area=None, region=None):
        return oc().box_zone(bpy.context, path)


def _spy(cls, tag):
    orig = cls.execute

    def execute(self, context):
        C["calls"].append((tag, getattr(self, "item", "")))
        return orig(self, context)
    cls.execute = execute
    C.setdefault("restore", []).append((cls, orig))


def press_release(x, y):
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


def view():
    toolbox = mod(".ui.toolbox")
    areas = [a for a in win().screen.areas if a.type == 'VIEW_3D' and not toolbox.is_toolbox(a.spaces.active)]
    area = max(areas, key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_ready():
    bpy.ops.allset.keymap_activate()
    bpy.context.preferences.view.show_tooltips = False
    area, r = view()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        bpy.ops.allset.create(kind='CUBE')
    C["ob"] = bpy.context.active_object.name      # by name: an undo frees the object it held
    bpy.ops.ed.undo_push(message="Cube")           # a Python call pushes no step: the state Ctrl+Z goes back to
    mod(".ui.status_line").redraw_top_bars()
    ms = mod(".ui.menu_sets")
    _spy(ms.ALLSET_OT_menu_option_box, "box")
    _spy(ms.ALLSET_OT_menu_item, "item")
    C["mid"] = (r.x + r.width // 2, r.y + r.height // 2)


def faces():
    return len(bpy.data.objects[C["ob"]].data.polygons)


@step
def s_open():
    bpy.context.preferences.addons[MODULE].preferences.menu_set = "modelingMenuSet"
    mod(".ui.status_line").redraw_top_bars()
    C["calls"].clear()
    C["faces0"] = faces()
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])


@step
def s_bar():
    shot("objmode_box_before")
    x, y = button_point("Edit Mesh")
    C["bar"] = (x, y)
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)


@step
def s_wait1():
    pass


@step
def s_click_bar():
    press_release(*C["bar"])


@step
def s_wait2():
    pass


@step
def s_wait3():
    pass


@step
def s_target():
    z = zone(PATH)
    y = row_y(ROW)
    C["target"] = (int(z[0] + oc().ZONE_LEFT_UNITS * unit()), y)
    ev('MOUSEMOVE', 'NOTHING', x=int(z[2] + 2 * unit()), y=y)     # enter the row from the left


@step
def s_hover():
    ev('MOUSEMOVE', 'NOTHING', x=C["target"][0], y=C["target"][1])


@step
def s_wait4():
    pass


@step
def s_wait5():
    pass


@step
def s_press():
    press_release(*C["target"])


@step
def s_wait6():
    pass


@step
def s_wait7():
    pass


@step
def s_result():
    import numpy as np
    shot("objmode_box_after")
    a, b = pixels("objmode_box_before"), pixels("objmode_box_after")
    x, y = C["target"]
    h, w = a.shape[:2]
    box = (slice(max(0, y - 250), min(h, y + 20)), slice(max(0, x - 200), min(w, x + 300)))
    changed = float((np.abs(a[box] - b[box]).max(axis=2) > 8 / 255).mean())
    want = mod(".ui.menu_item_ops").WHOLE_MESH_OPTIONS[PATH]
    ops = [o.bl_idname.lower().replace("_ot_", ".") for o in bpy.context.window_manager.operators]
    check(f"the click reached the option box ({C['calls']})", C["calls"][:2] == [("item", PATH), ("box", PATH)])
    check(f"Blender stays in object mode ({bpy.context.mode})", bpy.context.mode == 'OBJECT')
    check(f"the whole cube got its divisions ({C['faces0']} -> {faces()} faces)", faces() == 4 * C["faces0"])
    last = bpy.context.window_manager.operators[-1] if ops else None
    check(f"the whole-mesh command is the last registered operation ({ops[-2:]}, want {want})",
          bool(ops) and ops[-1] == want)
    check(f"its settings are the command's own ({last and last.bl_label}, Divisions {last and last.divisions})",
          last is not None and last.bl_label == "Add Divisions" and last.divisions == 1)
    check(f"its settings popup is drawn (changed {changed:.2f})", changed > 0.15)
    C["faces1"] = faces()


@step
def s_undo():
    tap('ESC')                          # close the settings popup
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])


@step
def s_undo2():
    ev('Z', 'PRESS', x=C["mid"][0], y=C["mid"][1], ctrl=True)
    ev('Z', 'RELEASE', x=C["mid"][0], y=C["mid"][1], ctrl=True)


@step
def s_undo_wait():
    pass


@step
def s_undo_result():
    # Adjust Last Operation undoes the command's one step and runs it again with the new settings
    check(f"one Ctrl+Z takes the whole command back ({C['faces1']} -> {faces()} faces)", faces() == C["faces0"])
    check(f"... still in object mode ({bpy.context.mode})", bpy.context.mode == 'OBJECT')


@step
def s_close():
    tap('ESC')
    ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])


@step
def s_restore():
    for cls, orig in C.get("restore", ()):
        cls.execute = orig


run()
