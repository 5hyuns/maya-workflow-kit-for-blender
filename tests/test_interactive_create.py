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


def test_maya_rules_for_more_primitives():
    m = ic()
    assert 'DISC' not in m.STEPS, "Maya draws no disc: Create > Disc makes it at the origin"
    assert m.STEPS['HELIX'] == ("width", "height", "coils", "radius")
    assert m.radius('PYRAMID', 3, -4) == 4, "pyramid: corner distance = the larger offset"
    assert close(m.first_values('PYRAMID', 2.0, 4)["sideLength"], 2 * math.sqrt(2))
    assert m.height_value('PIPE', 1.5) == 3.0 and m.height_value('CONE', 1.5) == 1.5, "pipe Height = 2 x drawn"
    assert close(m.px_value("thickness", 0.5, 200), 20.5), "pipe thickness has no upper limit"
    assert m.px_value("thickness", 0.5, -100) == 0.01
    assert close(m.px_value("coils", 3, 37), 6.7) and m.px_value("coils", 3, -60) == 0.5
    assert close(m.px_value("radius", 0.4, 7), 1.1) and m.px_value("radius", 0.4, -60) == 0.01
    assert m.step_attr('HELIX', "radius") == "radius"
    assert {'PLATONIC', 'SOCCER_BALL'} <= m.SHIFT_LIFT and 'HELIX' in m.SHIFT_HEIGHT


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
    assert prefs.interactive_creation is False and prefs.exit_on_completion is True, "defaults off / on, like Maya"


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


def _object_tools():
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as TOOLBAR

    def flat(items):
        for item in items:
            if type(item) is tuple:
                yield from (i for i in item if i is not None)
            elif item is not None:
                yield item
    return {t.idname for t in flat(TOOLBAR._tools['OBJECT'])}


def test_a_tool_in_object_mode():
    """Picking a primitive makes a tool current (Esc keeps a tool): LMB presses (plain / Shift / Ctrl / both) start a
    primitive, nothing is bound to Esc or Alt, and it isn't a Select / Move / Rotate / Scale tool, so Y (last tool)
    comes back to it."""
    m = ic()
    assert m.TOOL in _object_tools()
    items = import_module(kit.MODULE + ".ui.interactive_tool").ALLSET_TL_interactive_create.bl_keymap
    presses = {(kw.get("shift", False), kw.get("ctrl", False)) for op, kw, _p in items
               if op == "allset.interactive_create" and kw["type"] == 'LEFTMOUSE' and kw["value"] == 'PRESS'}
    assert presses == {(False, False), (True, False), (False, True), (True, True)}, presses
    assert not any(kw["type"] == 'ESC' or kw.get("alt") for _op, kw, _p in items), "Esc keeps the tool, Alt navigates"
    tool_keys = import_module(kit.MODULE + ".operators.tool_keys")
    assert not tool_keys.is_sacred(m.TOOL)
    tool_keys.remember('OBJECT', m.TOOL)
    assert tool_keys.LAST['OBJECT'] == m.TOOL
    command_line = import_module(kit.MODULE + ".command_line")
    assert command_line.help_for_tool(m.TOOL).startswith("Interactive Creation"), "Help Line while the tool waits"


def test_pick_remembers_the_primitive():
    m = ic()
    n = m.CURRENT["pick"]
    m.pick('CYLINDER', {"subdivisionsAxis": 8})
    assert m.CURRENT["kind"] == 'CYLINDER' and m.CURRENT["values"] == {"subdivisionsAxis": 8}
    assert m.CURRENT["pick"] == n + 1, "a new pick leaves a primitive being drawn"
    # start() makes the tool current (False = the caller creates at the origin instead)
    assert m.start(bpy.context, 'CUBE') is True and m.tool_active(bpy.context)
    assert m.CURRENT["kind"] == 'CUBE' and m.CURRENT["values"] == {}
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box", space_type='VIEW_3D')      # Q
    assert not m.tool_active(bpy.context)


def test_disable_removes_the_tool():
    tool = ic().TOOL
    kit.disable()
    try:
        assert tool not in _object_tools(), "disabling unregisters the tool"
    finally:
        kit.enable()
    assert tool in _object_tools()
