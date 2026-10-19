"""Step 17 in a real UI: F / A / Ctrl+Shift+F / Shift+F fit 0.95 of the part of the view
not under the sidebar; hotbox rows stay inside the window (docs/steps/step_17.md, step 52)."""

import os
import sys
from importlib import import_module

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def view_mod():
    return import_module(MODULE + ".operators.view")


def corners(obs):
    """Maya fits the axis-aligned bounding box of everything framed (fitPanel)."""
    pts = []
    for ob in obs:
        if ob.type == 'MESH':
            pts += [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        else:
            pts.append(ob.matrix_world.translation.copy())
    return import_module(MODULE + ".operators.framing").box_corners(pts)


def fit_ratio(area, region, obs):
    """(inside, ratio) of the projected bounding box against the visible rect."""
    rv3d = region.data
    rect = view_mod().visible_bounds(area, region)
    pp = [location_3d_to_region_2d(region, rv3d, p) for p in corners(obs)]
    if any(p is None for p in pp):
        return False, 0.0
    xs, ys = [p.x for p in pp], [p.y for p in pp]
    inside = min(xs) >= rect[0] - 2 and max(xs) <= rect[2] + 2 and min(ys) >= rect[1] - 2 and max(ys) <= rect[3] + 2
    ratio = max((max(xs) - min(xs)) / (rect[2] - rect[0]), (max(ys) - min(ys)) / (rect[3] - rect[1]))
    return inside, ratio


def only(*names):
    for o in bpy.context.view_layer.objects:
        o.select_set(o.name in names)
    bpy.context.view_layer.objects.active = bpy.data.objects[names[0]]


@step
def s_setup():
    C["x"], C["y"] = setup()
    area, region = view3d()
    area.spaces.active.show_region_ui = True     # sidebar open, overlapping (factory)
    child = bpy.data.objects.new("far_child", None)
    bpy.context.scene.collection.objects.link(child)
    child.parent = bpy.data.objects["Cube"]
    child.location = (12.0, 0.0, 0.0)
    only("Cube")


@step
def s_press_f():
    area, region = view3d()
    C["x"] = region.x + int(view_mod().visible_bounds(area, region)[2] * 0.5)
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    tap('F')


@step
def s_f_drawn():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_f():
    area, region = view3d()
    rect = view_mod().visible_bounds(area, region)
    check(f"sidebar excluded from the visible rect ({rect[2]:.0f} of {region.width} px)", rect[2] < region.width)
    inside, ratio = fit_ratio(area, region, [bpy.data.objects["Cube"]])
    check(f"F: cube inside the visible part, fills 0.95 (ratio {ratio:.3f})", inside and abs(ratio - 0.95) < 0.03)
    shot("step17_f.png")
    ev('F', 'PRESS', ctrl=True, shift=True)
    ev('F', 'RELEASE', ctrl=True, shift=True)


@step
def s_ctrl_shift_f_drawn():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_ctrl_shift_f():
    area, region = view3d()
    obs = [bpy.data.objects["Cube"], bpy.data.objects["far_child"]]
    inside, ratio = fit_ratio(area, region, obs)
    check(f"Ctrl+Shift+F: cube + child fit (ratio {ratio:.3f})", inside and abs(ratio - 0.95) < 0.03)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    tap('A')


@step
def s_a_drawn():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_a():
    area, region = view3d()
    obs = [o for o in bpy.context.view_layer.objects if o.visible_get()]
    inside, ratio = fit_ratio(area, region, obs)
    check(f"A tap: everything fits (ratio {ratio:.3f})", inside and abs(ratio - 0.95) < 0.03)
    shot("step17_a.png")
    only("Cube")
    tap('SPACE')   # four views


@step
def s_quad():
    ev('F', 'PRESS', shift=True)
    ev('F', 'RELEASE', shift=True)


@step
def s_quad_drawn():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_quad_check():
    area = view3d()[0]
    regs = [r for r in area.regions if r.type == 'WINDOW']
    res = [fit_ratio(area, r, [bpy.data.objects["Cube"]]) for r in regs]
    check(f"Shift+F frames the cube in all {len(regs)} views (ratios {[round(x[1], 3) for x in res]})",
          len(regs) == 4 and all(i and abs(r - 0.95) < 0.03 for i, r in res))
    shot("step17_quad.png")
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    tap('SPACE')   # back to one view


@step
def s_hotbox():
    area, region = view3d()
    rect = view_mod().visible_bounds(area, region)
    C["hx"] = region.x + int(rect[2]) - 30          # near the sidebar's left edge
    ev('MOUSEMOVE', 'NOTHING', x=C["hx"], y=C["y"])
    ev('SPACE', 'PRESS')


@step
def s_hotbox_wait():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_hotbox_check():
    draw = import_module(MODULE + ".marking.draw")
    area, region = view3d()
    # step 52: Maya's hotbox floats over the whole window, sidebar included: rows stay in the window
    rect = draw.window_bounds(win(), region)
    lay = draw.ACTIVE.get("hotbox")
    xs = [r[2] for r, _k, _l in lay.labels] if lay else []
    check(f"hotbox rows end inside the window (max x {max(xs) if xs else None:.0f} <= {rect[2]:.0f})",
          bool(xs) and max(xs) <= rect[2] + 1)
    shot("step17_hotbox.png")
    ev('SPACE', 'RELEASE')
    tap('ESC')


run()
