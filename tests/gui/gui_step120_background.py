"""Step 120 in a real UI: Maya's Alt+B (cycleBackgroundColor) with the Maya theme on, read back from screen pixels and
compared with a running Maya 2022 (research/maya/screens/bg120/_bg120.json): factory flat #5c5c5c -> #a1a1a1 ->
gradient #889db3 (top) .. #0d0d0d (bottom) -> black -> #5c5c5c, in every 3D View. Also the Color Settings dialog
(Windows > Settings/Preferences > Color Settings) on screen."""

import json
import os
import sys
from importlib import import_module

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from sim import MODULE, check, ev, run, step, setup, screenshot, view3d, win  # noqa: E402
from look_compare import de2000  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
MAYA = os.path.join(ROOT, "research", "maya", "screens", "bg120", "_bg120.json")
C = {"n": 0}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def rgb(c):
    return "#%02x%02x%02x" % tuple(round(v * 255) for v in c[:3])


def grab(tag):
    C["n"] += 1
    path = os.path.join(SHOTS or bpy.app.tempdir, f"step120_{C['n']}_{tag}.png")
    screenshot(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = img.pixels[:]
    bpy.data.images.remove(img)

    def at(x, y):
        i = (y * w + x) * 4
        return tuple(px[i:i + 3])
    return at


def samples(at):
    """Background pixels at the left edge of the main view: top, bottom and every 10 % from the top."""
    _area, r = view3d()
    x = r.x + 12
    col = {}
    for k in range(11):
        t = k / 10
        y = r.y + round((1 - t) * (r.height - 1))
        y = min(max(y, r.y + 2), r.y + r.height - 3)
        col[t] = at(x, y)
    return col


def maya_column(label):
    """Maya's pixel column for a state, keyed by the fraction from the top (0 .. 1)."""
    if not os.path.exists(MAYA):
        return {}
    data = json.load(open(MAYA))
    st = next(s for s in data["states"] if s["label"] == label)
    h = st["size"][1]
    return {y / (h - 1): hexrgb(c) for y, c in st["column_x_mid"]}


def nearest(col, t):
    return col[min(col, key=lambda k: abs(k - t))]


def alt_b():
    area, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    ev('B', 'PRESS', alt=True)
    ev('B', 'RELEASE', alt=True)


@step
def s_setup():
    setup()
    mod("theme").apply()   # Make Blender feel like Maya turns the Maya theme on (switch.set_mode)
    for area in win().screen.areas:
        if area.type == 'VIEW_3D':
            sp = area.spaces.active
            sp.overlay.show_overlays = False     # no grid / text over the background samples
            sp.show_gizmo = False
            area.tag_redraw()
    bpy.ops.object.select_all(action='DESELECT')


@step
def s_wait():
    pass


def flat_check(tag, maya_label, expect_hex):
    at = grab(tag)
    col = samples(at)
    ref = hexrgb(expect_hex)
    worst = max(de2000(c, ref) for c in col.values())
    check(f"{tag}: background {rgb(col[0.5])} = Maya {expect_hex} (max ΔE00 {worst:.2f} ≤ 2 over the view)",
          worst <= 2.0)
    m = maya_column(maya_label)
    if m:
        check(f"{tag}: Maya's own pixel {rgb(nearest(m, 0.5))} = {expect_hex}", de2000(nearest(m, 0.5), ref) <= 1.0)


@step
def s_factory():
    flat_check("factory", "factory", "#5c5c5c")
    state = mod("operators.key_batch3").background_state(view3d()[0].spaces.active.shading,
                                                         mod("operators.key_batch3").theme_gradients())
    check(f"the view starts in Maya's factory state (GREY, got {state})", state == "GREY")
    alt_b()


@step
def s_light_wait():
    pass


@step
def s_light():
    flat_check("light", "press1", "#a1a1a1")
    alt_b()


@step
def s_gradient_wait():
    pass


@step
def s_gradient():
    at = grab("gradient")
    col = samples(at)
    top, bottom = hexrgb("#889db3"), hexrgb("#0d0d0d")
    check(f"gradient top {rgb(col[0.0])} = Maya #889db3 (ΔE00 {de2000(col[0.0], top):.2f} ≤ 2)",
          de2000(col[0.0], top) <= 2.0)
    check(f"gradient bottom {rgb(col[1.0])} = Maya #0d0d0d (ΔE00 {de2000(col[1.0], bottom):.2f} ≤ 2)",
          de2000(col[1.0], bottom) <= 2.0)
    m = maya_column("press2")
    if m:
        des = {t: de2000(c, nearest(m, t)) for t, c in col.items()}
        C["gradient_de"] = des
        print("GUI gradient profile:", ", ".join(f"{t:.1f} {rgb(col[t])}/{rgb(nearest(m, t))} {d:.1f}"
                                                for t, d in sorted(des.items())))
        # Blender mixes the two theme colours in scene-linear light, Maya in between (step_120.md): recorded,
        # bounded so a wrong direction (top / bottom swapped) or a missing gradient still fails
        check(f"gradient follows Maya down the view (max ΔE00 {max(des.values()):.1f} < 12)",
              max(des.values()) < 12)
    gr = mod("operators.key_batch3").theme_gradients()
    check("the Maya theme carries the gradient (LINEAR)", gr.background_type == 'LINEAR')
    alt_b()


@step
def s_black_wait():
    pass


@step
def s_black():
    flat_check("black", "press3", "#000000")
    gr = mod("operators.key_batch3").theme_gradients()
    check("gradient off again, the theme's flat colour is Maya's 0.36",
          gr.background_type == 'SINGLE_COLOR' and abs(gr.high_gradient[0] - 0.36) < 1e-3)
    alt_b()


@step
def s_grey_wait():
    pass


@step
def s_grey():
    flat_check("grey again", "press4", "#5c5c5c")
    area, r = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=r):
        bpy.ops.allset.color_settings('INVOKE_DEFAULT')


@step
def s_dialog_wait():
    pass


@step
def s_dialog():
    grab("color_settings")     # the dialog is looked at by hand (docs/steps/step_120.md)
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')
    mod("theme").restore()


run()
