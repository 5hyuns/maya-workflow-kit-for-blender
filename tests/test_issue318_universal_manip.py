"""Universal Manipulator (#318): Ctrl+T in Object Mode picks the kit's box tool (mesh component modes too, see
test_issue318_component_um.py),
Modify > Transformation Tools > Universal Manipulator too; a corner drag scales one box axis with the opposite face
fixed (Ctrl: about the centre, Shift: evenly with the opposite corner fixed), an edge drag rotates about the edge's
direction, a typed length scales that axis about the box centre. The GUI test tests/gui/gui_issue318_universal_manip.py
drags the handles."""

import math
from importlib import import_module

import bpy
from mathutils import Vector

import kit

um = import_module(kit.MODULE + ".operators.universal_manip")
ui_um = import_module(kit.MODULE + ".ui.universal_manip")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")


def _close(a, b, eps=1e-4):
    return all(abs(x - y) <= eps for x, y in zip(a, b))


def _tall_box():
    """A 1 x 4 x 1 box standing on the ground (pivot at its foot), the only selected object."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    ob = bpy.context.active_object
    for v in ob.data.vertices:
        v.co.y += 0.5            # the mesh's foot on its origin
    ob.data.update()
    ob.scale = (1.0, 4.0, 1.0)
    bpy.context.view_layer.update()
    um.settings(bpy.context).property_unset("space")
    um.settings(bpy.context).property_unset("rotate_around")
    return ob


def _box():
    bpy.context.view_layer.update()
    _frame, lo, hi = um.box_of(bpy.context)
    return tuple(lo), tuple(hi)


# --- maths ---------------------------------------------------------------------------------------------------

def test_corners_and_edges():
    assert um.corner_signs(0) == (-1, -1, -1) and um.corner_signs(7) == (1, 1, 1) and um.corner_signs(5) == (1, -1, 1)
    for c in range(8):
        edges = um.edges_at_corner(c)
        assert len(set(edges)) == 3 and sorted(um.edge_spec(e)[0] for e in edges) == [0, 1, 2]
        s = um.corner_signs(c)
        for e in edges:                       # each edge at the corner has the corner's signs on its other axes
            axis, sides = um.edge_spec(e)
            assert all(s[a] == sgn for a, sgn in sides.items()), (c, e)
    lo, hi = Vector((-0.5, 0, -0.5)), Vector((0.5, 4, 0.5))
    assert _close(um.edge_mid(lo, hi, um.edges_at_corner(7)[0]), (0, 4, 0.5))
    assert _close(um.corner_point(lo, hi, 7), (0.5, 4, 0.5))


def test_pick_axis_follows_the_drag():
    axes = [(100, 0), (0, 80), (-40, -40)]
    assert um.pick_axis((30, 2), axes) == 0
    assert um.pick_axis((-1, -20), axes) == 1
    assert um.pick_axis((20, 20), axes) == 2          # against the axis counts too (the corner moves inward)
    assert um.pick_axis((10, 0), [(0, 0), (0, 50), None]) == 1   # end-on axes never win
    assert um.pick_axis((0, 0), axes) is None
    assert um.along((50, 0), (100, 0)) == 0.5 and um.along((0, -40), (0, 80)) == -0.5


def test_corner_scale_plans():
    lo, hi = Vector((-0.5, 0, -0.5)), Vector((0.5, 4, 0.5))
    # plain: only that axis, the opposite face stays (corner +X+Y+Z, Z pulled in by 0.68)
    f, fixed = um.scale_plan(lo, hi, 7, 'FACE', axis=2, offset=-0.68)
    assert _close(f, (1, 1, 0.32)) and abs(fixed[2] - -0.5) < 1e-9
    f, fixed = um.scale_plan(lo, hi, 0, 'FACE', axis=1, offset=2.0)       # min corner: the top stays
    assert _close(f, (1, 1.5, 1)) and abs(fixed[1] - 4.0) < 1e-9
    # Ctrl: that axis about the box centre
    f, fixed = um.scale_plan(lo, hi, 7, 'CENTER', axis=2, offset=-0.45)
    assert _close(f, (1, 1, 0.1)) and _close(fixed, (0, 2, 0))
    # Shift: evenly, the opposite corner stays
    f, fixed = um.scale_plan(lo, hi, 7, 'UNIFORM', factor=1.108)
    assert _close(f, (1.108,) * 3) and _close(fixed, (-0.5, 0, -0.5))
    f, fixed = um.scale_plan(lo, hi, 7, 'UNIFORM_CENTER', factor=2.0)
    assert _close(fixed, (0, 2, 0))
    assert um.uniform_factor((150, 100), (100, 100), (0, 100)) == 1.5
    assert um.uniform_factor((100, 100), (100, 100), (0, 100)) == 1.0
    assert um.size_factor(4.0, 2.0) == 0.5 and um.size_factor(0.0, 2.0) == 1.0


def test_rotate_maths():
    assert abs(um.rotate_angle((50, 0), (10, 0)) - math.radians(10.0)) < 1e-9       # 0.2 degrees per px
    assert abs(um.rotate_angle((0, 50), (10, 0))) < 1e-12                           # across the arrows: nothing
    assert abs(um.rotate_angle((-30, 0), (0, 0)) - math.radians(-6.0)) < 1e-9       # end-on: horizontal drag
    t = um.tangent(Vector((1, 0, 0)), Vector((0, 4, 0.5)), Vector((0, 0, 0)))
    assert _close(t, Vector((0, -0.5, 4)).normalized())


# --- registration ------------------------------------------------------------------------------------------------

def _maya_items(km_name, etype, ctrl=False):
    km = kit.maya_kc().keymaps[km_name]
    return [(k.idname, k.properties.name if k.properties and "name" in k.properties.keys() else None)
            for k in km.keymap_items if k.active and k.type == etype and k.value == 'PRESS' and k.ctrl == ctrl
            and not k.shift and not k.alt]


def test_ctrl_t_menu_and_tool():
    assert ("wm.tool_set_by_id", um.TOOL) in _maya_items("Object Mode", 'T', ctrl=True)
    assert ("wm.tool_set_by_id", um.TOOL) in _maya_items("Mesh", 'T', ctrl=True)      # components too (#318)
    assert menu_map.spec("Modify/Transformation Tools/Universal Manipulator")[:2] == ("tool", um.TOOL)
    assert um.TOOL not in menu_sets.COMPONENT_TWIN
    from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active
    ids = [item.idname for item, _i in ToolSelectPanelHelper._tools_flatten_with_tool_index(
        VIEW3D_PT_tools_active.tools_from_context(bpy.context, mode='OBJECT')) if item is not None]
    assert um.TOOL in ids
    assert hasattr(bpy.types.Scene, "allset_universal_manip")
    assert "ALLSET_GGT_universal_manip" in {c.bl_idname for c in ui_um.classes}


def test_disable_removes_everything():
    kit.disable()
    try:
        assert not hasattr(bpy.types.Scene, "allset_universal_manip")
        assert not hasattr(bpy.types, "ALLSET_OT_um_scale")
    finally:
        kit.enable()
    assert hasattr(bpy.types.Scene, "allset_universal_manip")


# --- what the drags do (Blender's transforms with the box frame and fixed point) -------------------------------

def _scale(corner, mode, axis=None, offset=0.0, factor=None):
    frame, lo, hi = um.box_of(bpy.context)
    f, fixed = um.scale_plan(lo, hi, corner, mode, axis, offset, factor)
    um.apply_scale(f, frame, frame @ fixed, final=True)


def test_corner_scale_keeps_the_opposite_face():
    ob = _tall_box()
    assert _box() == ((-0.5, 0.0, -0.5), (0.5, 4.0, 0.5))
    _scale(7, 'FACE', axis=2, offset=-0.68)
    lo, hi = _box()
    assert _close(ob.scale, (1, 4, 0.32)), ob.scale[:]
    assert abs(lo[2] - -0.5) < 1e-4 and abs(hi[2] - -0.18) < 1e-4, (lo, hi)
    assert abs(lo[1]) < 1e-4 and abs(hi[1] - 4.0) < 1e-4


def test_ctrl_scale_about_the_centre():
    ob = _tall_box()
    _scale(7, 'CENTER', axis=2, offset=-0.45)
    lo, hi = _box()
    assert _close(ob.scale, (1, 4, 0.1)) and _close((lo[2], hi[2]), (-0.05, 0.05)), (ob.scale[:], lo, hi)


def test_shift_scale_keeps_the_opposite_corner():
    ob = _tall_box()
    _scale(7, 'UNIFORM', factor=1.108)
    lo, hi = _box()
    assert _close(ob.scale, (1.108, 4 * 1.108, 1.108)) and _close(lo, (-0.5, 0, -0.5)), (ob.scale[:], lo)


def test_edge_rotate_turns_about_the_edge_direction():
    ob = _tall_box()
    frame, lo, hi = um.box_of(bpy.context)
    pivot = um.rotate_pivot(bpy.context, frame, lo, hi)
    assert _close(pivot, (0, 0, 0))                                    # Rotate around Pivot: the object's pivot
    mid = frame @ um.edge_mid(lo, hi, 3)                              # X edge at +Y +Z: (0, 4, 0.5)
    assert _close(mid, (0, 4, 0.5))
    t = um.tangent(frame.col[0], mid, pivot)
    um.apply_rotate(0, math.radians(10), frame, pivot, final=True)
    assert abs(ob.rotation_euler.x - math.radians(10)) < 1e-4, ob.rotation_euler[:]
    moved = ob.matrix_world @ Vector((0, 1.0, 0.5))                  # where that edge middle went
    assert (moved - mid).dot(t) > 0, (moved, mid, t)                 # a positive turn moves it along the arrows
    um.settings(bpy.context).rotate_around = 'CENTER'
    frame, lo, hi = um.box_of(bpy.context)
    assert _close(um.rotate_pivot(bpy.context, frame, lo, hi), frame @ um.centre(lo, hi))


def test_typed_length_scales_about_the_box_centre():
    ob = _tall_box()
    assert bpy.ops.allset.um_size(axis='Y', length=2.0) == {'FINISHED'}
    lo, hi = _box()
    assert _close(ob.scale, (1, 2, 1)) and _close((lo[1], hi[1]), (1.0, 3.0)), (ob.scale[:], lo, hi)


def test_local_space_box_follows_the_object():
    ob = _tall_box()
    ob.rotation_euler = (0, 0, math.radians(30))
    bpy.context.view_layer.update()
    um.settings(bpy.context).space = 'LOCAL'
    frame, lo, hi = um.box_of(bpy.context)
    assert _close(hi - lo, (1, 4, 1))
    bpy.ops.allset.um_size(axis='X', length=3.0)
    assert _close(ob.scale, (3, 4, 1)) and abs(ob.rotation_euler.z - math.radians(30)) < 1e-4, ob.scale[:]
    um.settings(bpy.context).space = 'WORLD'
    _frame, lo, hi = um.box_of(bpy.context)
    assert (hi - lo).x > 3.0                                          # the world box of the turned object is wider
    bpy.ops.allset.um_reset()
    assert um.settings(bpy.context).space == 'WORLD' and um.settings(bpy.context).rotate_around == 'PIVOT'


def test_length_field_typing():
    text, fresh = "4.000", True
    text, fresh = um.edit_text(text, fresh, 'TWO', "2")           # the first key replaces the shown length
    assert (text, fresh) == ("2", False)
    for t, ch in (('PERIOD', "."), ('FIVE', "5"), ('A', "a")):    # letters are ignored
        text, fresh = um.edit_text(text, fresh, t, ch)
    assert text == "2.5"
    text, _f = um.edit_text(text, fresh, 'BACK_SPACE', "")
    assert text == "2." and um.typed_value(text) == 2.0
    assert um.edit_text("4.000", True, 'BACK_SPACE', "") == ("", False)
    assert um.typed_value("1,5") == 1.5 and um.typed_value("") is None and um.typed_value("-") is None


def test_label_sits_across_its_edge():
    # a horizontal edge below the box centre: the number goes straight down from its middle
    x, y = ui_um.label_xy((100, 50), (100, 100), (60, 50), (140, 50), 14)
    assert abs(x - 100) < 1e-9 and abs(y - 36) < 1e-9
    # an edge seen end-on: straight away from the centre
    x, y = ui_um.label_xy((130, 100), (100, 100), (130, 100), (131, 100), 10)
    assert abs(x - 140) < 1e-9 and abs(y - 100) < 1e-9
    x, y = ui_um.label_xy((100, 50), (100, 100), (60, 50), (140, 50), 14, (20, 6))     # clear of its own text
    assert abs(y - 30) < 1e-9
