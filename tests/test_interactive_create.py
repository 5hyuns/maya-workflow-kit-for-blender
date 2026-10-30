"""Create > Polygon Primitives > Interactive Creation (#225): drawing maths, menu items and the plain create path."""

import math
from importlib import import_module

import bpy
from mathutils import Vector

import kit


def ic():
    return import_module(kit.MODULE + ".operators.interactive_create")


def close(a, b, eps=1e-6):
    return abs(a - b) < eps


def test_plane_hit_and_coords():
    P = ic().Plane((0, 0, 0), (0, 0, 1), (1, 0, 0))
    p = P.hit((2, 3, 10), (0, 0, -1))
    assert p is not None and (p - Vector((2, 3, 0))).length < 1e-9, p
    assert P.hit((0, 0, 10), (1, 0, 0)) is None, "a ray parallel to the plane misses"
    assert P.hit((0, 0, 10), (0, 0, 1)) is None, "behind the eye"
    assert P.coords(p) == (2.0, 3.0)
    # front view plane: normal towards the viewer (-Y), u = +X, v = n x u = +Z
    F = ic().Plane((0, 0, 0), (0, -1, 0), (1, 0, 0))
    assert (F.v - Vector((0, 0, 1))).length < 1e-9, F.v
    rot = F.rotation().to_3x3()
    assert (rot @ Vector((0, 0, 1)) - Vector((0, -1, 0))).length < 1e-9, "local Z = the plane normal"


def test_axis_param():
    # line through the origin along +Z, ray from (5, 0, 2) towards -X: closest point at z = 2
    t = ic().axis_param((0, 0, 0), (0, 0, 1), (5, 0, 2), (-1, 0, 0))
    assert close(t, 2.0), t
    assert ic().axis_param((0, 0, 0), (0, 0, 1), (5, 0, 2), (0, 0, -1)) is None, "parallel ray"


def test_rect_rules():
    rect = ic().rect
    assert rect(0, 0, 4, 2) == (2, 1, 4, 2), "corner to corner"
    assert rect(0, 0, -4, 2) == (-2, 1, 4, 2)
    assert rect(1, 1, 4, 2, centred=True) == (1, 1, 6, 2), "Ctrl: centred on the press, 2|da| x 2|db|"
    assert rect(0, 0, 4, -1, square=True) == (0, 0, 8, 8), "Shift: equal sides 2 x max, centred on the press"


def test_sizes():
    m = ic()
    assert m.first_values('CUBE', (2, 3)) == {"width": 2, "depth": 3}
    assert m.first_values('CUBE', (2, 3), width_along_a=False) == {"width": 3, "depth": 2}
    assert m.first_values('PLANE', (2, 3)) == {"width": 2, "height": 3}
    assert m.first_values('SPHERE', 1.5) == {"radius": 1.5}
    assert m.first_values('HELIX', 1.5) == {"width": 3.0}
    assert close(m.first_values('PRISM', 1.0, 3)["sideLength"], math.sqrt(3)), "triangle side for circumradius 1"
    assert m.radius('SPHERE', 3, -4) == 4, "sphere: the larger offset"
    assert m.radius('CYLINDER', 3, -4) == 5, "cylinder: the distance"
    assert close(m.section_radius(0.5, 30), 3.5) and m.section_radius(0.5, -100) == 0.01, "torus section per px"


def test_view_axes():
    m = ic()
    assert m.maya_axis((0, 0, 1)) == (0, 1, 0), "ground: Maya Y"
    assert m.maya_axis((0, -1, 0)) == (0, 0, 1), "front view (towards the viewer): Maya +Z"
    assert m.maya_axis((1, 0, 0)) == (1, 0, 0), "side view: Maya +X"
    assert tuple(m.world_axis(Vector((0.1, -0.9, 0.2)))) == (0, -1, 0)


def test_placement():
    pl = ic().placement
    n = (0, 0, 1)
    assert (pl((1, 2, 0), n, -0.5, 0.5, "base") - Vector((1, 2, 0.5))).length < 1e-9, "bottom on the plane"
    assert (pl((1, 2, 0), n, -0.5, 0.5, "top") - Vector((1, 2, -0.5))).length < 1e-9, "hangs below"
    assert (pl((1, 2, 0), n, -0.5, 0.5, "centre") - Vector((1, 2, 0))).length < 1e-9
    assert (pl((1, 2, 0), n, -0.5, 0.5, "lift", 0.5) - Vector((1, 2, 0.5))).length < 1e-9, "torus Shift lift"


def test_every_step_kind_is_a_primitive():
    prim_history = import_module(kit.MODULE + ".operators.prim_history")
    prim_shapes = import_module(kit.MODULE + ".operators.prim_shapes")
    m = ic()
    for kind, steps in m.STEPS.items():
        node = prim_history.KIND_NODES[kind][0]
        attrs = prim_shapes.defaults(node)
        firsts = m.first_values(kind, (1.0, 1.0) if steps[0] == "rect" else 1.0, 4)
        for name in firsts:
            assert name in attrs, (kind, name)
        for later in steps[1:]:
            assert m.step_attr(kind, later) in attrs, (kind, later)


def test_menu_items_are_checks():
    menu_map = import_module(kit.MODULE + ".ui.menu_map")
    notices = import_module(kit.MODULE + ".ui.notices")
    for label, pref in (("Interactive Creation", "interactive_creation"), ("Exit On Completion", "exit_on_completion")):
        action = menu_map.MAP[f"Create/Polygon Primitives/{label}"]
        assert action[0] == "prop" and action[1] == f"addon_prefs.{pref}", action
    assert "Create/Polygon Primitives" not in notices.CATEGORIES, "nothing in that menu is greyed any more"
    prefs = import_module(kit.MODULE + ".preferences").get()
    assert prefs.interactive_creation is False and prefs.exit_on_completion is True, "Maya defaults off / on"


def test_plain_create_without_a_window():
    """Interactive Creation on, but no window (background, scripts): the primitive is created at the origin."""
    prefs = import_module(kit.MODULE + ".preferences").get()
    prefs.interactive_creation = True
    try:
        assert not ic().wanted(bpy.context, 'CUBE')
        before = set(bpy.data.objects)
        bpy.ops.allset.create(kind='CUBE')
        new = [o for o in bpy.data.objects if o not in before]
        assert len(new) == 1 and new[0].name.startswith("pCube"), new
    finally:
        prefs.interactive_creation = False
