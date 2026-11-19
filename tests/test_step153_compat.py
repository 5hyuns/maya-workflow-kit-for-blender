"""Blender 5.x pass — unified paint settings (#90), menus that stay open (5.0), radial submenus open from their own
box or sector."""

import math
from importlib import import_module

import bpy

import kit

compat = import_module(kit.MODULE + ".compat")
engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")


def test_unified_paint_settings_radius_round_trip():
    ts = bpy.context.scene.tool_settings
    ups = compat.unified_paint_settings(ts, "weight_paint")
    assert isinstance(ups, bpy.types.UnifiedPaintSettings)
    compat.set_unprojected_radius(ups, 0.35)
    assert abs(compat.unprojected_radius(ups) - 0.35) < 1e-6
    assert abs(ups.unprojected_size - 0.7) < 1e-6                 # 5.x stores the diameter
    ups.weight = 0.25
    assert abs(compat.unified_paint_settings(ts).weight - 0.25) < 1e-6


def test_menus_close_on_leave():
    view = bpy.context.preferences.view
    want = view.menu_close_leave
    assert compat.menus_close_on_leave(bpy.context.preferences) == want


def _measure(text):
    return 7.0 * len(text)


def _wide_north_box_point(s, p):
    """A point of the N box (Symmetry, a submenu) past the ring and in the NE sector: Maya's wide N box reaches into
    the diagonal sector there (Maya ring geometry)."""
    n = s.stack[0][0].radial["N"]
    assert n.sub is not None
    x0, y0, x1, y1 = n.rect
    for yy in range(int(y0) + 1, int(y1)):
        for xx in range(int(x1) - 1, 0, -1):
            if math.hypot(xx, yy) >= p.radius and engine.direction(xx, yy, p.dead) == "NE":
                return n, (xx, yy)
    raise AssertionError(f"N box {n.rect} doesn't reach the NE sector")


def test_diagonal_rest_on_a_wide_north_box_opens_the_box_item():
    # Move Options: N = Symmetry (a submenu), NE = Component (a command). Where the N box reaches into the NE sector
    # the box is what the pointer is on: it is hovered and a rest there opens Symmetry, not anything of NE.
    p = engine.Params()
    origin = (500.0, 400.0)
    s = engine.Session(mm.OPT_MOVE, origin, 0.0, _measure, p)
    n, pt = _wide_north_box_point(s, p)
    t = p.show_delay + 0.05
    s.move(origin[0] + pt[0] / 2, origin[1] + pt[1] / 2, t)
    s.move(origin[0] + pt[0], origin[1] + pt[1], t + 0.02)
    assert s.hover[0] is n, s.hover
    s.tick(t + 0.02 + p.open_dwell + 0.01)
    assert len(s.stack) == 2 and s.via[1] is n, "a rest on the N box's NE part opens the N submenu"
    want = sorted(label for label, _a in n.sub.radial.values() if label)
    got = sorted(it.label for it in s.layout.items if it.kind == "radial")
    assert got == want, (got, want)


def test_diagonal_rest_off_the_box_belongs_to_its_own_sector():
    # A NE stroke through the N box's NE part and on, past the ring in the NE sector off the N box: NE (Component)
    # is hovered, a rest there opens nothing (N's submenu only opens from its box or its own sector) and the
    # release runs Component.
    p = engine.Params()
    origin = (500.0, 400.0)
    s = engine.Session(mm.OPT_MOVE, origin, 0.0, _measure, p)
    n, pt = _wide_north_box_point(s, p)
    far = max(pt) * 2
    t = p.show_delay + 0.05
    s.move(origin[0] + pt[0], origin[1] + pt[1], t)
    assert s.hover[0] is n, s.hover
    s.move(origin[0] + far, origin[1] + far, t + 0.02)
    assert s.hover[0] is not n and s.hover[0].label == "Component", s.hover
    s.tick(t + 0.02 + p.open_dwell + 0.5)
    assert len(s.stack) == 1, "a rest in the NE sector off the N box opened a submenu"
    res = s.release(origin[0] + far, origin[1] + far, t + 0.6)
    assert res and res[0] == "RUN" and res[1].label == "Component", res


def test_straight_stroke_still_opens_the_radial_submenu():
    p = engine.Params()
    origin = (500.0, 400.0)
    s = engine.Session(mm.OPT_MOVE, origin, 0.0, _measure, p)
    s.move(origin[0], origin[1] + p.radius + 15, 0.2)
    s.tick(0.2 + p.open_dwell + 0.01)                   # a rest on it opens it (Maya)
    assert len(s.stack) == 2
