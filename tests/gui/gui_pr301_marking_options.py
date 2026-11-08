"""#301 marking menu options in a real UI (add-on preferences, off by default).
Submenu Return Ring on: Shift+RMB on edges, drag onto Merge/Collapse Edges (its submenu opens in place, linked to the
press point), rest near the press point beside the submenu's south box: after a moment the edge menu is there again
without a mouse move. Quick Gestures on: RMB on the cube and one quick stroke east onto UV opens its submenu hidden
(the route with its menu names is drawn instead); Esc closes it. Off again: the same stroke shows the
submenu. The new drawings run without errors."""

import os
import sys
import traceback
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, view3d, win  # noqa: E402

C = {"calls": {}, "errors": []}


def draw():
    return import_module(MODULE + ".marking.draw")


def prefs():
    return import_module(MODULE + ".preferences").get()


def session():
    return draw().ACTIVE.get("session")


def box_center(s, key, level=-1):
    lay, (cx, cy) = s.stack[level]
    it = lay.radial[key]
    ox, oy = draw().ACTIVE["origin"]
    return (ox + round(cx + (it.rect[0] + it.rect[2]) / 2), oy + round(cy + (it.rect[1] + it.rect[3]) / 2))


def window_point(s, xy):
    ox, oy = draw().ACTIVE["origin"]
    return ox + round(xy[0]), oy + round(xy[1])


def watch(name):
    """Count the calls of a drawing function of marking/draw.py and keep any error it raises."""
    original = getattr(draw(), name)

    def wrapped(*args, **kw):
        C["calls"][name] = C["calls"].get(name, 0) + 1
        try:
            return original(*args, **kw)
        except Exception:
            C["errors"].append(traceback.format_exc())
            raise
    setattr(draw(), name, wrapped)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


@step
def s_setup():
    C["x"], C["y"] = setup()
    p = prefs()
    check("both options are off after install", not p.mm_quick_gestures and not p.mm_submenu_guides)
    p.mm_submenu_guides = True
    for name in ("_draw_anchors", "_draw_route", "_near_centre"):
        watch(name)
    cube = bpy.data.objects["Cube"]
    bpy.context.view_layer.objects.active = cube
    cube.select_set(True)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, True, False)
    bm = bmesh.from_edit_mesh(cube.data)
    for e in bm.edges:
        e.select_set(False)
    bm.edges.ensure_lookup_table()
    bm.edges[0].select_set(True)
    bmesh.update_edit_mesh(cube.data)
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    redraw()


@step
def s_shift_rmb():
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"], shift=True)


@step
def s_onto_merge():
    s = session()
    check("Shift+RMB on edges opens the edge marking menu", s is not None and s.layout.radial.get("N") is not None)
    if s is not None:
        x, y = box_center(s, "N")
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y + 40, shift=True)


@step
def s_rest():
    s = session()
    ok = s is not None and len(s.stack) == 2 and "Target Weld Tool" in [it.label for it in s.layout.items]
    check("dragging past Merge/Collapse Edges opens its submenu in place", ok)
    if ok:
        check("Submenu Return Ring: the submenu is linked to the press point", s.anchors() == [(s.stack[0][1],
                                                                                              s.stack[1][1])])
        x, y = window_point(s, (s.stack[0][1][0] + 12, s.stack[0][1][1] - 6))
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y, shift=True)


@step
def s_resting():
    s = session()
    check(f"resting near the press point (off the south box): the ring fills ({s and s.dwell_progress(s.time + 0.2)})",
          s is not None and len(s.stack) == 2 and s._dwell is not None)


@step
def s_back():
    s = session()
    check("after a moment without a mouse move the edge menu is there again, still held",
          s is not None and len(s.stack) == 1 and s.mode == "PRESS")
    check(f"the ring and the near-centre line drew without errors ({C['calls']})",
          C["calls"].get("_draw_anchors", 0) > 0 and C["calls"].get("_near_centre", 0) > 0 and not C["errors"])
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"], y=C["y"])


@step
def s_quick_setup():
    check("Esc closes the menu", not draw().ACTIVE)
    p = prefs()
    p.mm_submenu_guides = False
    p.mm_quick_gestures = True
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set(mode='OBJECT')
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])


def close():
    """Esc closes the submenu, Esc again the menu; then the held button goes up (nothing runs)."""
    for _ in range(2):
        ev('ESC', 'PRESS')
        ev('ESC', 'RELEASE')
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"] + 90, y=C["y"])


def quick_east():
    """RMB on the cube and one quick stroke east past the UV box (all in one tick)."""
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"])
    for k in range(1, 11):
        ev('MOUSEMOVE', 'NOTHING', x=C["x"] + 9 * k, y=C["y"])


step(quick_east)


@step
def s_quick_hidden():
    s = session()
    ok = s is not None and len(s.stack) == 2
    check("Quick Gestures: a quick stroke onto UV opens its submenu", ok)
    if ok:
        check(f"... hidden, with the route's menu names ({[n for _p, n in s.route]})",
              not s.visible(s.time + 1.0) and [n for _p, n in s.route][1:] == ["UV"])
        check(f"the route drew without errors ({C['calls'].get('_draw_route', 0)})",
              C["calls"].get("_draw_route", 0) > 0 and not C["errors"])
    close()


@step
def s_quick_off():
    check("Esc twice closes it", not draw().ACTIVE)
    prefs().mm_quick_gestures = False
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])


step(quick_east)


@step
def s_default_shown():
    s = session()
    check("options off: the same stroke opens the submenu and shows it",
          s is not None and len(s.stack) == 2 and s.visible(s.time))
    close()
    if C["errors"]:
        print(C["errors"][0])


run()
