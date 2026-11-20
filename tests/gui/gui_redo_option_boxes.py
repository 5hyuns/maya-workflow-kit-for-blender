"""A click on the option box ❒ of a menu item whose settings are the command's own (Blender's Adjust Last Operation)
shows those settings at once, like a Maya option box: Edit Mesh > Add Divisions ❒ and Mesh Display > Reverse ❒ in
component mode (real simulated clicks on the Maya menu bar and the menu row's ❒). The command ran once, is the last registered operation, and its settings popup is drawn under the pointer."""

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
# (menu set, path, row in its menu: 0 = the tear-off line; no separator above these rows)
CASES = (("modelingMenuSet", "Edit Mesh/Add Divisions", 1), ("modelingMenuSet", "Mesh Display/Reverse", 3))


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
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
    mod(".ui.status_line").redraw_top_bars()
    ms = mod(".ui.menu_sets")
    _spy(ms.ALLSET_OT_menu_option_box, "box")
    _spy(ms.ALLSET_OT_menu_item, "item")
    C["mid"] = (r.x + r.width // 2, r.y + r.height // 2)


def click_case(menu_set, path, k):
    top = path.split("/")[0]
    tag = path.replace("/", "_").replace(" ", "_")

    def s_open():
        bpy.context.preferences.addons[MODULE].preferences.menu_set = menu_set
        mod(".ui.status_line").redraw_top_bars()
        C["calls"].clear()
        ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])

    def s_bar():
        shot(f"redo_box_before_{tag}")             # menus closed: the popup is what differs afterwards
        x, y = button_point(top)
        C["bar"] = (x, y)
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    def s_click_bar():
        press_release(*C["bar"])

    def s_target():
        z = zone(path)
        C["zone"] = z
        y = row_y(k)
        C["target"] = (int(z[0] + oc().ZONE_LEFT_UNITS * unit()), y)
        ev('MOUSEMOVE', 'NOTHING', x=int(z[2] + 2 * unit()), y=y)     # enter the row from the left

    def s_hover():
        ev('MOUSEMOVE', 'NOTHING', x=C["target"][0], y=C["target"][1])

    def s_press():
        C["ops_before"] = len(bpy.context.window_manager.operators)
        press_release(*C["target"])

    def s_result():
        import numpy as np
        shot(f"redo_box_after_{tag}")
        a, b = pixels(f"redo_box_before_{tag}"), pixels(f"redo_box_after_{tag}")
        x, y = C["target"]
        h, w = a.shape[:2]
        # the settings popup opens at the pointer, over the place the menu was (the menu itself closed)
        box = (slice(max(0, y - 250), min(h, y + 20)), slice(max(0, x - 200), min(w, x + 300)))
        changed = float((np.abs(a[box] - b[box]).max(axis=2) > 8 / 255).mean())
        want = mod(".ui.menu_map").spec(path)[1]
        ops = [o.bl_idname.lower().replace("_ot_", ".") for o in bpy.context.window_manager.operators]
        check(f"{path}: the click reached the option box ({C['calls']})",
              C["calls"][:2] == [("item", path), ("box", path)])
        check(f"{path}: the command is the last registered operation ({ops[-2:]}, want {want})",
              bool(ops) and ops[-1] == want)
        check(f"{path}: its settings popup is drawn (changed {changed:.2f})", changed > 0.15)

    def s_close():
        tap('ESC')
        ev('MOUSEMOVE', 'NOTHING', x=C["mid"][0], y=C["mid"][1])

    for f in (s_open, s_bar, lambda: None, s_click_bar, lambda: None, lambda: None, s_target, s_hover,
              lambda: None, lambda: None, s_press, lambda: None, lambda: None, s_result, s_close, lambda: None):
        step(f)


for _set, _path, _k in CASES:
    click_case(_set, _path, _k)


@step
def s_restore():
    for cls, orig in C.get("restore", ()):
        cls.execute = orig


run()
