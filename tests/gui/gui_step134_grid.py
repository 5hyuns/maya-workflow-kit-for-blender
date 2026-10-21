"""Step 134 lane GRID in a real UI (#59, docs/steps/step_134_grid.md): the Maya layout's first screen shows Maya's grid
as strongly as Maya 2022 does and no 3D cursor; the D / Insert component pivot still shows the cursor.

Measured from screenshots the way the Maya reference is measured (research/maya/screens/01_layout_empty.png):
- grid line colour = the most common clearly-darker pixel inside the grid = Maya #404040 (ΔE00),
- contrast = standard deviation of the grey value inside the grid (shrunk to 85 % around its centre), against the
  same number from the Maya shot,
- axis lines thicker than minor lines (dark-pixel run across the projected line, median),
- no 3D-cursor red near the origin; during Insert the cursor is drawn again and hidden after."""

import os
import sys
from importlib import import_module

import bpy
import numpy as np
from bpy_extras import view3d_utils
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from sim import MODULE, check, ev, load_maya_layout, run, screenshot, setup, step, tap, view3d, win  # noqa: E402
from look_compare import de2000  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MAIN_ROOT = os.environ.get("ALLSET_MAIN_ROOT", "")
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
MAYA_SHOT = "research/maya/screens/01_layout_empty.png"
# Maya's grid corners in that shot (image px, y down; compare_audit133_s100/grid.md: kit projection = Maya grid)
MAYA_QUAD = ((453.5, 493.0), (820.5, 751.4), (1187.5, 493.0), (820.5, 364.2))
MAYA_LINE = (64 / 255,) * 3
STD_TOLERANCE = 0.25      # relative: kit std within 25 % of Maya's
C = {"n": 0}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def load(path):
    """Image as an (h, w, 3) array, row 0 = bottom (window coordinates)."""
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[:, :, :3]


def grab(tag):
    C["n"] += 1
    scale = round(bpy.context.preferences.system.ui_scale * 100)
    path = os.path.join(SHOTS or bpy.app.tempdir, f"step134_{C['n']}_{tag}_{scale}.png")
    screenshot(path)
    return load(path)


def quad_mask(shape, quad, shrink=0.85):
    """Pixels inside the convex quad (x, y window px) shrunk around its centre."""
    h, w = shape[:2]
    cx = sum(p[0] for p in quad) / 4
    cy = sum(p[1] for p in quad) / 4
    q = [(cx + shrink * (x - cx), cy + shrink * (y - cy)) for x, y in quad]
    ys, xs = np.mgrid[0:h, 0:w]
    inside = np.ones((h, w), bool)
    for i in range(4):
        (x0, y0), (x1, y1) = q[i], q[(i + 1) % 4]
        cross = (x1 - x0) * (ys - y0) - (y1 - y0) * (xs - x0)
        s = np.sign((x1 - x0) * (cy - y0) - (y1 - y0) * (cx - x0))   # the centre's side of this edge
        inside &= cross * s >= 0
    return inside


def grid_stats(img, quad):
    """(std of grey 0-255, line colour (most common darker pixel), background grey) inside the grid."""
    m = quad_mask(img.shape, quad)
    px = img[m]
    grey = px.mean(axis=1) * 255
    bg = float(np.median(grey))
    dark = px[grey < bg - 8]
    if len(dark):
        keys, counts = np.unique(np.round(dark * 255).astype(int), axis=0, return_counts=True)
        line = tuple(keys[counts.argmax()] / 255)
    else:
        line = None
    return float(grey.std()), line, bg


def maya_stats():
    path = next((os.path.join(r, MAYA_SHOT) for r in (ROOT, MAIN_ROOT, os.path.join(ROOT, "..", "..", ".."))
                 if r and os.path.exists(os.path.join(r, MAYA_SHOT))), None)
    if path is None:
        return None
    img = load(path)
    h = img.shape[0]
    quad = [(x, h - 1 - y) for x, y in MAYA_QUAD]
    return grid_stats(img, quad)


def project(co):
    area, region = view3d()
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, co)
    return None if p is None else (region.x + p.x, region.y + p.y)


def kit_quad():
    unit = mod("operators.units").maya_unit(bpy.context.scene)
    return [project(Vector(c)) for c in mod("ui.maya_grid").corners("FLOOR", unit)]


def ink_width(img, a, b, samples=24):
    """Median run of dark pixels across the projected segment a-b (window px)."""
    a, b = np.array(a), np.array(b)
    d = b - a
    n = np.array((-d[1], d[0])) / max(np.linalg.norm(d), 1e-9)
    grey = img.mean(axis=2) * 255
    h, w = grey.shape
    widths = []
    for t in np.linspace(0.2, 0.8, samples):
        if abs(t - 0.5) < 0.06:      # skip the crossing with the other axis
            continue
        p = a + t * d
        run_ = 0
        for k in np.arange(-4, 4.01, 0.5):
            x, y = (p + k * n).round().astype(int)
            if 0 <= x < w and 0 <= y < h and grey[y, x] < 80:
                run_ += 1
        widths.append(run_ * 0.5)
    return float(np.median(widths)) if widths else 0.0


def red_near(img, xy, r=30):
    """Pixels near ``xy`` that are the 3D cursor's red (Maya's grid is grey)."""
    x, y = int(xy[0]), int(xy[1])
    sub = img[max(0, y - r):y + r, max(0, x - r):x + r]
    return int(((sub[:, :, 0] - sub[:, :, 1] > 0.25) & (sub[:, :, 0] > 0.5)).sum())


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def main_space():
    return view3d()[0].spaces.active


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_keys():
    bpy.ops.allset.keymap_activate()
    area, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + 5, y=r.y + r.height - 5)    # mouse out of the grid
    redraw()


@step
def s_wait():
    redraw()


@step
def s_first_screen():
    sp = main_space()
    ov = sp.overlay
    check(f"Maya layout view hides the 3D cursor (show_cursor {ov.show_cursor})", not ov.show_cursor)
    check("no Blender floor / axis lines under the Maya grid",
          not ov.show_floor and not ov.show_ortho_grid and not ov.show_axis_x and not ov.show_axis_y)
    check("the Maya grid is on in the main view", mod("ui.maya_grid").is_on(sp))
    img = grab("first_screen")
    quad = kit_quad()
    std, line, bg = grid_stats(img, quad)
    maya = maya_stats()
    ms, mline, mbg = maya if maya else (None, MAYA_LINE, None)
    de = de2000(line, MAYA_LINE) if line else 99.0
    print(f"GRID134 kit std {std:.2f} line {line and '#%02x%02x%02x' % tuple(round(v * 255) for v in line)} "
          f"bg {bg:.1f} | maya std {ms} line #404040 bg {mbg}")
    check(f"grid line colour = Maya #404040 (ΔE00 {de:.2f} ≤ 3)", de <= 3.0)
    if ms is not None:
        check(f"grid contrast (std of grey inside the grid) {std:.2f} within {STD_TOLERANCE:.0%} of Maya's {ms:.2f}",
              abs(std - ms) <= STD_TOLERANCE * ms)
    unit = mod("operators.units").maya_unit(bpy.context.scene)
    s = 12 * unit
    axis = ink_width(img, project(Vector((-s, 0, 0))), project(Vector((s, 0, 0))))
    minor = ink_width(img, project(Vector((-s, 3 * unit, 0))), project(Vector((s, 3 * unit, 0))))
    check(f"axis line thicker than a minor line (dark run {axis} px vs {minor} px)", axis > minor and minor > 0)
    o = project(Vector((0, 0, 0)))
    red = red_near(img, o)
    check(f"no 3D cursor at the origin ({red} cursor-red px)", red == 0)
    C["first"] = (std, line, ms)


@step
def s_cube():
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.create(kind='CUBE')
    r = region
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    tap('F9')


@step
def s_insert():
    check(f"F9: component mode ({bpy.context.mode})", bpy.context.mode == 'EDIT_MESH')
    tap('INSERT')
    redraw()


@step
def s_insert_wait():
    redraw()


@step
def s_insert_check():
    on = mod("operators.hold").COMPONENT.on
    check(f"Insert: component pivot edit on ({on})", on)
    check(f"the cursor (= component pivot) shows while editing it ({main_space().overlay.show_cursor})",
          main_space().overlay.show_cursor)
    img = grab("insert")
    red = red_near(img, project(bpy.context.scene.cursor.location))
    check(f"the cursor is drawn ({red} cursor-red px)", red > 0)
    tap('INSERT')
    redraw()


@step
def s_insert_off():
    redraw()


@step
def s_insert_off_check():
    on = mod("operators.hold").COMPONENT.on
    check(f"Insert again: pivot edit off ({on}), cursor hidden again ({main_space().overlay.show_cursor})",
          not on and not main_space().overlay.show_cursor)


run()
