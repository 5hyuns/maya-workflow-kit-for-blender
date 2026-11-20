"""Issue #402: Skin > Mirror Skin Weights' option box opens Maya's Mirror Skin Weights Options window (Mirror across,
Direction: Positive to negative, Influence association, Normalize, Mirror / Apply / Close) without mirroring first,
and the Direction option mirrors either way. GUI: tests/gui/gui_issue402_mirror_options.py."""

from importlib import import_module

import bpy
from mathutils import Vector

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")
joints = import_module(kit.MODULE + ".operators.joints")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")

PATH = "Skin/Mirror Skin Weights"


def _scene():
    """A grid across X skinned to joint1 (centre) > jointL (+X) / jointR (-X); +X vertices fully on jointL, -X
    vertices fully on joint1 (an unmirrored skin)."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    arm = joints.new_skeleton(bpy.context)
    root = joints.add_joint(arm, Vector((0, 0, 0)), None, length=0.5)
    left = joints.add_joint(arm, Vector((1, 0, 0)), root, length=0.5)
    right = joints.add_joint(arm, Vector((-1, 0, 0)), root, length=0.5)
    eb = arm.data.edit_bones
    eb[left].name, eb[right].name = "jointL", "jointR"
    eb[root].name = "joint1"
    joints.finish(bpy.context, arm, ["joint1", "jointL", "jointR"])
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=8, y_subdivisions=2, size=3.0)
    grid = bpy.context.active_object
    for ob in (arm, grid):
        ob.select_set(True)
    bpy.context.view_layer.objects.active = grid
    assert bpy.ops.allset.bind_skin() == {'FINISHED'}
    names = [vg.name for vg in grid.vertex_groups]
    assert {"joint1", "jointL", "jointR"} <= set(names), names
    for v in grid.data.vertices:
        for vg in grid.vertex_groups:
            vg.remove([v.index])
        if v.co.x > 1e-6:
            grid.vertex_groups["jointL"].add([v.index], 1.0, 'REPLACE')
        else:
            grid.vertex_groups["joint1"].add([v.index], 1.0, 'REPLACE')
    return arm, grid


def _weight(grid, v, name):
    idx = grid.vertex_groups[name].index
    return next((g.weight for g in v.groups if g.group == idx), 0.0)


def _side(grid, sign):
    return [v for v in grid.data.vertices if v.co.x * sign > 1e-6]


def test_option_box_is_the_maya_window():
    assert menu_sets.option_kind(PATH) == "window", "the option box only runs the command, then Adjust Last Operation"
    w = ow.find_path(PATH)
    assert (w.title, w.action) == ("Mirror Skin Weights Options", "Mirror")
    fields = {f.name: f for f in w.fields}
    assert fields["mirror_across"].default == "YZ" and list(fields["mirror_across"].items) == ["XY", "YZ", "XZ"]
    assert fields["positive_to_negative"].default is True
    assert fields["normalize"].default is False
    assert fields["influence1"].default == "Closest joint"


def test_window_direction_negative_to_positive():
    _arm, grid = _scene()
    res = ow.run(ow.find_path(PATH), bpy.context, {"positive_to_negative": False})
    assert not isinstance(res, str) and 'FINISHED' in res, res
    # -X (all on joint1, which mirrors onto itself) is copied onto +X; -X keeps its weights
    for v in _side(grid, 1):
        assert abs(_weight(grid, v, "joint1") - 1.0) < 1e-4 and _weight(grid, v, "jointL") < 1e-4, v.index
    for v in _side(grid, -1):
        assert abs(_weight(grid, v, "joint1") - 1.0) < 1e-4 and _weight(grid, v, "jointR") < 1e-4, v.index


def test_window_default_positive_to_negative():
    _arm, grid = _scene()
    res = ow.run(ow.find_path(PATH), bpy.context, {})
    assert not isinstance(res, str) and 'FINISHED' in res, res
    # +X jointL is copied onto -X as its mirror partner jointR
    for v in _side(grid, -1):
        assert abs(_weight(grid, v, "jointR") - 1.0) < 1e-4 and _weight(grid, v, "joint1") < 1e-4, v.index
    for v in _side(grid, 1):
        assert abs(_weight(grid, v, "jointL") - 1.0) < 1e-4, v.index
