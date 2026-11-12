"""#350: the option box ❒ of a Maya menu opened from the Space hotbox.

1. Geometry: Maya menus opened by a click on their hotbox name (released at the pointer): the model's menu left / right
   edges (``ui/option_click.box_zone``) against the menu back colour in a screenshot, and the ❒ glyph inside the
   model's zone. Blender places such a popup with the pointer at 0.8 of its width (``option_click.POPUP_AT``).
2. Clicks in a menu opened from the hotbox: Edit Mesh > Bevel and Create > Polygon Primitives > Cube - a click on the
   ❒ = ``allset.menu_option_box``, a click on the label = the command alone, Shift+click on the label = the option box.
3. Press and hold Edit Mesh > Bevel in a menu opened from the hotbox = the option box (the hold menu's row).
Runs at the session's UI scale (e.g. 1.25; ``ALLSET_GUI_UI_SCALE=0.8`` = 1.0).
"""

import os
import sys
import tempfile
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win  # noqa: E402

GUI_TIMEOUT = 420
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {"calls": []}
# (hotbox name, where the hotbox is opened: fraction of the viewport width / height)
GEOMETRY = [("Edit Mesh", 0.5, 0.5), ("Create", 0.5, 0.5), ("Modify", 0.5, 0.5), ("Display", 0.5, 0.5),
            ("File", 0.5, 0.5), ("Key", 0.5, 0.5), ("Edit Mesh", 0.12, 0.5), ("Modify", 0.9, 0.5)]
BACK_TOL = 0.02
ROW0 = 2.04      # popup top edge -> centre of its tear-off line (row 0), in units: a menu called at the pointer has a title row


def mod(name):
    return import_module(MODULE + name)


def oc():
    return mod(".ui.option_click")


def ms():
    return mod(".ui.menu_sets")


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


def zone(path):
    with bpy.context.temp_override(window=win(), area=None, region=None):
        return oc().box_zone(bpy.context, path)


def wait(n):
    for _ in range(n):
        step(lambda: None)


def _spy(cls, tag):
    orig = cls.execute

    def execute(self, context):
        C["calls"].append((tag + ("_hold" if getattr(self, "from_hold", False) else ""), getattr(self, "item", "")))
        return orig(self, context)
    cls.execute = execute
    C.setdefault("restore", []).append((cls, orig))


def label_point(name):
    hb = mod(".marking.draw").ACTIVE.get("hotbox")
    _a, r = view3d()
    rect = next(rc for rc, key, label in hb.labels if label == name)
    return r.x + int((rect[0] + rect[2]) / 2), r.y + int((rect[1] + rect[3]) / 2)


def measure(a, mx, my):
    """(left, right, top) of the popup menu under the pointer from a screenshot: the menu back colour = the most
    common colour on a strip under the pointer; a column is inside the menu when most rows of a band are that colour."""
    import numpy as np
    u = unit()
    h, w = a.shape[:2]
    ys = [y for y in range(int(my - 1.5 * u), int(my - 7 * u), -1) if 0 <= y < h]
    strip = np.round(a[ys, mx] * 255).astype(int)
    keys, counts = np.unique(strip, axis=0, return_counts=True)
    back = keys[counts.argmax()] / 255.0
    band = a[ys]                                            # rows x columns x rgb
    isb = (np.abs(band - back).max(axis=2) < BACK_TOL)
    frac = isb.mean(axis=0)
    inside = frac > 0.3
    x = mx
    while x > 0 and inside[x - 1]:
        x -= 1
    left = x
    x = mx
    while x < w - 1 and inside[x + 1]:
        x += 1
    right = x
    # the top edge: up from just above the row under the pointer (that row is highlighted) while the rows are the
    # back colour (a separator line or the title's rule is a gap of a few rows)
    cols = slice(left + 4, right - 4)
    top, gap = int(my + 0.75 * u), 0
    for y in range(int(my + 0.75 * u), h):
        if (np.abs(a[y, cols] - back).max(axis=1) < BACK_TOL).mean() > 0.5:
            top, gap = y, 0
        else:
            gap += 1
            if gap > 4:
                break
    return left, right, top, back


def box_x(path, left):
    """Window x of the middle of the ❒ glyph of ``path``'s row in a menu whose left edge is ``left`` (the row texts
    the kit draws, right-aligned: same text model as the menu bar)."""
    u = unit()
    size = ms().font_size()
    got = oc().rows(path.rsplit("/", 1)[0])
    text = got[1][path]
    glyph = ms().text_width(ms().BOX_MARK.strip(), size)
    return int(left + oc().TEXT_UNITS * u + ms().text_width(text, size) - glyph / 2)


def open_from_hotbox(name, fx, fy, tag):
    """Steps: Space down at (fx, fy) of the viewport, click ``name`` (press, release) = the menu opens at the pointer."""
    def s_space():
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        _a, r = view3d()
        C["hb"] = (r.x + int(r.width * fx), r.y + int(r.height * fy))
        ev('MOUSEMOVE', 'NOTHING', x=C["hb"][0], y=C["hb"][1])
        ev('SPACE', 'PRESS')

    def s_move():
        C["open"] = label_point(name)
        ev('MOUSEMOVE', 'NOTHING', x=C["open"][0], y=C["open"][1])

    def s_press():
        ev('LEFTMOUSE', 'PRESS', x=C["open"][0], y=C["open"][1])

    def s_release():
        ev('LEFTMOUSE', 'RELEASE', x=C["open"][0], y=C["open"][1])

    def s_measure():
        shot(tag)
        a = pixels(tag)
        C["menu"] = measure(a, *C["open"])
        C["a"] = a
    for f in (s_space, lambda: None, s_move, s_press, lambda: None, s_release, lambda: None, lambda: None, s_measure):
        step(f)


def close_all():
    def s_close():
        tap('ESC')
        tap('ESC')
        ev('SPACE', 'RELEASE')
        _a, r = view3d()
        ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    step(s_close)
    wait(2)


@step
def s_setup():
    setup()
    bpy.ops.allset.keymap_activate()
    bpy.context.preferences.view.show_tooltips = False
    if not any(o.type == 'MESH' for o in bpy.context.scene.objects):
        bpy.ops.mesh.primitive_cube_add()
    for o in bpy.context.scene.objects:
        o.select_set(o.type == 'MESH')
    _spy(ms().ALLSET_OT_menu_option_box, "box")
    _spy(ms().ALLSET_OT_menu_item, "item")


# --- 1. geometry ----------------------------------------------------------------------------------------------

def geometry_case(label, fx, fy, n):
    tag = f"350_hotbox_{label.replace(' ', '_')}_{n}"
    open_from_hotbox(label, fx, fy, tag)

    def s_check():
        import numpy as np
        left, right, top, _back = C["menu"]
        rows = oc().rows(label)[1]
        boxed = [p for p, t in rows.items() if t.endswith("❒")]
        z = zone(boxed[0]) if boxed else None
        u = unit()
        print("GUI350 geometry", label, "open", C["open"], "screen", (left, right, top),
              "model", None if z is None else tuple(round(v) for v in z),
              "pulldown width", oc().width(label, u), "u", u, flush=True)
        check(f"{label} from the hotbox at {C['open']}: the model places the menu ({boxed[:1]} zone {z})",
              z is not None)
        if z is None:
            return
        x0, x1, mleft, mright = z
        check(f"{label}: menu left model {mleft:.0f} / screen {left} (tol 4 px)", abs(mleft - left) <= 4)
        check(f"{label}: menu right model {mright:.0f} / screen {right} (tol 6 px)", abs(mright - right) <= 6)
        a = C["a"]
        glyph = ms().text_width("❒", ms().font_size())
        gx0 = int(x0 + oc().ZONE_LEFT_UNITS * u)
        band = slice(max(0, int(top - 40 * u)), int(top))
        cell = a[band, gx0:int(gx0 + glyph)].mean(axis=2)
        bright_in = int((cell > 0.6).sum())
        check(f"{label}: ❒ glyphs in the model's cell x {gx0}..{gx0 + glyph:.0f} (bright px {bright_in})",
              bright_in > 20)
        del np
    step(s_check)
    close_all()


for _n, (_label, _fx, _fy) in enumerate(GEOMETRY):
    geometry_case(_label, _fx, _fy, _n)


# --- 2. clicks in a menu opened from the hotbox ------------------------------------------------------------------

def click_case(path, row_k, how, sub_k=None):
    """Open the path's top menu from the hotbox, (hover the submenu row ``sub_k``), click row ``row_k``:
    ``how`` = "box" (the ❒), "label", "shift" (Shift held, the label)."""
    top = path.split("/")[0]
    tag = f"350_click_{path.split('/')[-1]}_{how}"
    open_from_hotbox(top, 0.5, 0.5, tag + "_menu")

    def s_sub():
        del C["calls"][:]
        left, right, mtop, _b = C["menu"]
        u = unit()
        C["top"] = mtop
        C["left"] = left
        if sub_k is None:
            return
        y = int(mtop - ROW0 * u - sub_k * u)
        C["sub_row"] = (int(left + 4 * u), y)
        ev('MOUSEMOVE', 'NOTHING', x=C["sub_row"][0] - 3, y=y)

    def s_sub2():
        if sub_k is not None:
            ev('MOUSEMOVE', 'NOTHING', x=C["sub_row"][0], y=C["sub_row"][1])

    def s_sub_measure():
        if sub_k is None:
            return
        shot(tag + "_sub")
        a = pixels(tag + "_sub")
        # the submenu opens right of the parent: measure it from a point just right of the parent's right edge
        u = unit()
        right = C["menu"][1]
        px_ = int(right + 3 * u)
        left, r2, stop, _b = measure(a, px_, C["sub_row"][1] + int(2 * u))
        C["left"] = left
        print("GUI350 submenu", path, "screen", (left, r2, stop), flush=True)

    def s_target():
        u = unit()
        # a submenu's tear-off line is level with its row in the parent menu
        y = int(C["sub_row"][1] - row_k * u) if sub_k is not None else int(C["top"] - ROW0 * u - row_k * u)
        if how == "box":
            x = box_x(path, C["left"])
        else:
            x = int(C["left"] + 3 * u)
        C["target"] = (x, y)
        ev('MOUSEMOVE', 'NOTHING', x=int(C["left"] + 2 * u), y=y)     # enter the row from the left

    def s_hover():
        ev('MOUSEMOVE', 'NOTHING', x=C["target"][0], y=C["target"][1])

    def s_press():
        shot(tag + "_before")
        if how == "shift":
            sim._down.add('LEFT_SHIFT')
        ev('LEFTMOUSE', 'PRESS', x=C["target"][0], y=C["target"][1])
        ev('LEFTMOUSE', 'RELEASE', x=C["target"][0], y=C["target"][1])

    def s_result():
        sim._down.discard('LEFT_SHIFT')
        shot(tag + "_after")
        want = [("item", path)] if how == "label" else [("item", path), ("box", path)]
        z = zone(path)
        print("GUI350 click", path, how, "target", C["target"], "zone", z, "calls", C["calls"], flush=True)
        check(f"hotbox {path}: click {how} at {C['target']} -> {C['calls']}", C["calls"] == want)
    for f in (s_sub, lambda: None, s_sub2, lambda: None, lambda: None, s_sub_measure, s_target, s_hover,
              lambda: None, lambda: None, s_press, lambda: None, lambda: None, s_result):
        step(f)
    close_all()

    @step
    def s_clean():
        for ob in list(bpy.context.scene.objects):
            if ob.type == 'MESH' and ob.name.startswith("pCube") and len(bpy.context.scene.objects) > 1:
                bpy.data.objects.remove(ob)
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for o in bpy.context.scene.objects:
            o.select_set(o.type == 'MESH')
    wait(1)


click_case("Edit Mesh/Bevel", 2, "box")
click_case("Edit Mesh/Bevel", 2, "label")
click_case("Edit Mesh/Bevel", 2, "shift")
click_case("Create/Polygon Primitives/Cube", 2, "box", sub_k=2)


# --- 3. press and hold the item in a menu opened from the hotbox --------------------------------------------------

def hold_case(path, row_k):
    top = path.split("/")[0]
    tag = f"350_hold_{path.split('/')[-1]}"
    open_from_hotbox(top, 0.5, 0.5, tag + "_menu")

    def s_row():
        del C["calls"][:]
        del ms().LAST_WARP[:]
        u = unit()
        left, _right, mtop, _b = C["menu"]
        C["row"] = (int(left + 5 * u), int(mtop - ROW0 * u - row_k * u))
        ev('MOUSEMOVE', 'NOTHING', x=C["row"][0] - 4, y=C["row"][1])

    def s_row2():
        ev('MOUSEMOVE', 'NOTHING', x=C["row"][0], y=C["row"][1])

    def s_press():
        ev('LEFTMOUSE', 'PRESS', x=C["row"][0], y=C["row"][1])

    def s_release():
        shot(tag + "_held")
        warp = [w[1:] for w in ms().LAST_WARP if w[0] == 'HOLD_ROW']
        C["warp"] = list(warp[0]) if warp else []
        x, y = C["warp"] if warp else C["row"]
        ms().AWAY_TICK = 0.3
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
        if ms().compat.menus_close_on_leave(bpy.context.preferences):
            ev('MOUSEMOVE', 'NOTHING', x=2 if x > win().width // 2 else win().width - 3, y=y)

    def s_back():
        moves = {m[0]: m[1:] for m in ms().LAST_WARP}
        if 'BACK' in moves:
            ev('MOUSEMOVE', 'NOTHING', x=moves['BACK'][0], y=moves['BACK'][1])

    def s_result():
        shot(tag + "_option_box")
        ms().AWAY_TICK = 0.05
        print("GUI350 hold", path, "warp", C["warp"], "calls", C["calls"], flush=True)
        check(f"hotbox {path}: press and hold the item, let go = the option box ({C['calls']})",
              C["calls"] == [("box_hold", path), ("box", path)])
    for f in (s_row, s_row2, lambda: None, s_press, lambda: None, s_release, lambda: None, s_back, lambda: None,
              s_result):
        step(f)
    close_all()


hold_case("Edit Mesh/Bevel", 2)


@step
def s_restore():
    for cls, orig in C.get("restore", ()):
        cls.execute = orig
    check("done", True)


run()
