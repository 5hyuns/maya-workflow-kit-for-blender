# SPDX-License-Identifier: GPL-3.0-or-later
"""#351: component pivot editing keeps the Move / Rotate / Scale tool and its manipulator (D / Insert), and a placed
component pivot moves with the components like Maya's (Pin Component Pivot off). GUI:
tests/gui/gui_issue351_component_pivot.py."""

from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix, Vector

import kit

hold = import_module(kit.MODULE + ".operators.hold")
pivot = import_module(kit.MODULE + ".operators.pivot")
manipulator = import_module(kit.MODULE + ".ui.manipulator")

TOOLS = ("builtin.move", "builtin.rotate", "builtin.scale")


def follow():
    return import_module(kit.MODULE + ".operators.pivot_follow")


def _tool(name):
    bpy.ops.wm.tool_set_by_id(name=name, space_type='VIEW_3D')


def _tool_id():
    tool = bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH', create=False)
    return tool.idname if tool is not None else None


def _edit_cube(tool="builtin.move", select=lambda co: co.z > 0):
    """A 2 x 2 x 2 cube in edit mode with the top face selected (centre (0, 0, 1)), ``tool`` active."""
    hold.unregister_cleanup()
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    sc = bpy.context.scene
    ts = sc.tool_settings
    ts.transform_pivot_point = 'BOUNDING_BOX_CENTER'
    ts.use_proportional_edit = False
    ts.mesh_select_mode = (False, False, True)
    sc.cursor.matrix = Matrix.Identity(4)
    sc.transform_orientation_slots[pivot.MOVE_SLOT].type = 'GLOBAL'
    wm = bpy.context.window_manager
    wm.allset_pin_pivot = False
    bpy.ops.object.mode_set(mode='EDIT')
    _select(ob, select)
    _tool(tool)
    return ob


def _select(ob, pred):
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select = False
    for e in bm.edges:
        e.select = False
    for v in bm.verts:
        v.select = pred(v.co)
    bm.select_flush(True)
    bmesh.update_edit_mesh(ob.data)


def _verts(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return [ob.matrix_world @ v.co for v in bm.verts]


def _same(a, b, eps=1e-5):
    return all((p - q).length < eps for p, q in zip(a, b))


def _place_pivot(at=(3.0, 0.0, 1.0)):
    """Insert, move the pivot, Insert: a custom component pivot at ``at``."""
    assert bpy.ops.allset.pivot_toggle() == {'FINISHED'}
    assert hold.COMPONENT.on
    bpy.context.scene.cursor.location = at
    bpy.ops.allset.pivot_toggle()
    assert hold.COMPONENT.custom and not hold.COMPONENT.on
    assert bpy.context.scene.tool_settings.transform_pivot_point == 'CURSOR'


# --- the tool and its manipulator stay -------------------------------------------------------------------------

def test_pivot_edit_keeps_the_transform_tool():
    for tool in TOOLS:
        _edit_cube(tool)
        assert bpy.ops.allset.pivot_toggle() == {'FINISHED'}
        assert hold.COMPONENT.on, tool
        assert _tool_id() == tool, f"{tool}: the tool stays during the pivot edit ({_tool_id()})"
        assert bpy.context.scene.tool_settings.transform_pivot_point == 'CURSOR'
        bpy.ops.allset.pivot_toggle()
        assert not hold.COMPONENT.on and _tool_id() == tool


def test_select_tool_d_and_insert_do_nothing():
    """Like Maya: the pivot is edited with the Move / Rotate / Scale tools only."""
    ob = _edit_cube("builtin.select_box")
    before = _verts(ob)
    assert bpy.ops.allset.pivot_toggle() == {'FINISHED'}
    assert not hold.COMPONENT.on, "Select tool: no pivot edit"
    assert _tool_id() == "builtin.select_box"
    assert bpy.context.scene.tool_settings.transform_pivot_point == 'BOUNDING_BOX_CENTER'
    assert hold.pivot_tool(bpy.context) is False
    _tool("builtin.move")
    assert hold.pivot_tool(bpy.context) is True
    assert _same(before, _verts(ob))


def test_manipulator_shows_the_pivot_handles_in_component_mode():
    _edit_cube()
    assert not manipulator.pivot_edit(bpy.context)
    bpy.ops.allset.pivot_toggle()
    assert manipulator.pivot_edit(bpy.context), "component pivot edit = the manipulator's pivot look"
    cursor = bpy.context.scene.cursor
    cursor.matrix = Matrix.Translation((0.5, 0.0, 1.0)) @ Matrix.Rotation(0.4, 4, 'X')
    axes = manipulator.pivot_axes(bpy.context)
    assert not hold.turned(axes, cursor.matrix.to_3x3()), "the handles use the pivot's own axes"
    centre, frame, _otype = manipulator.pivot_frame(bpy.context, 'TRANSLATE')
    assert (centre - Vector((0.5, 0.0, 1.0))).length < 1e-6
    assert not hold.turned(frame, cursor.matrix.to_3x3())
    bpy.ops.allset.pivot_toggle()
    assert not manipulator.pivot_edit(bpy.context)


def test_rotate_and_scale_tools_show_the_pivot_handles():
    for tool in TOOLS:
        _edit_cube(tool)
        manipulator.ensure_tools()
        bpy.ops.allset.pivot_toggle()
        assert manipulator.tool_kind(bpy.context) == 'TRANSLATE', (tool, manipulator.tool_kind(bpy.context))
        bpy.ops.allset.pivot_toggle()
        assert manipulator.tool_kind(bpy.context) == manipulator.TOOLS[tool], tool


def test_a_ring_turns_the_component_pivot_only():
    ob = _edit_cube()
    before = _verts(ob)
    bpy.ops.allset.pivot_toggle()
    cursor = bpy.context.scene.cursor
    assert bpy.ops.allset.pivot_rotate(axis='X', angle=0.5) == {'FINISHED'}
    want = Matrix.Rotation(0.5, 3, 'X')
    assert not hold.turned(want, cursor.matrix.to_3x3()), cursor.matrix
    assert (cursor.location - Vector((0, 0, 1))).length < 1e-6, "the pivot stays where it is"
    assert _same(before, _verts(ob)), "the components stay"
    bpy.ops.allset.pivot_toggle()
    slot = bpy.context.scene.transform_orientation_slots[pivot.MOVE_SLOT]
    assert slot.type == pivot.ORIENT_NAME, "a turned pivot gives the Move axes"


# --- the placed pivot moves with the components -------------------------------------------------------------

def test_a_move_takes_the_pivot_along():
    ob = _edit_cube()
    _place_pivot((3.0, 0.0, 1.0))
    bpy.ops.transform.translate(value=(0.0, 0.5, 1.0))
    d = follow().update(bpy.context, "TRANSFORM_OT_translate")
    assert d is not None and (d - Vector((0.0, 0.5, 1.0))).length < 1e-5, d
    assert (bpy.context.scene.cursor.location - Vector((3.0, 0.5, 2.0))).length < 1e-5
    # a single vertex keeps its offset too
    _select(ob, lambda co: co.x > 0 and co.y > 0 and co.z > 0)
    hold.COMPONENT.tick(bpy.context)          # Pin off: a new selection drops the placed pivot
    assert not hold.COMPONENT.custom
    _place_pivot((2.0, 1.0, 2.0))
    bpy.ops.transform.translate(value=(1.0, 0.0, 0.0))
    follow().update(bpy.context, "TRANSFORM_OT_translate")
    assert (bpy.context.scene.cursor.location - Vector((3.0, 1.0, 2.0))).length < 1e-5


def test_soft_selection_moves_take_the_pivot_along():
    _edit_cube()
    _place_pivot((3.0, 0.0, 1.0))
    bpy.ops.transform.translate(value=(0.0, 0.0, 0.7), use_proportional_edit=True, proportional_size=3.0)
    follow().update(bpy.context, "TRANSFORM_OT_translate")
    assert (bpy.context.scene.cursor.location - Vector((3.0, 0.0, 1.7))).length < 1e-5


def test_rotate_scale_and_typed_moves_leave_the_pivot():
    ob = _edit_cube()
    _place_pivot((3.0, 0.0, 1.0))
    cursor = bpy.context.scene.cursor
    bpy.ops.transform.rotate(value=0.5, orient_axis='Z')
    assert follow().update(bpy.context, "TRANSFORM_OT_rotate") is None
    bpy.ops.transform.resize(value=(1.5, 1.5, 1.5))
    assert follow().update(bpy.context, "TRANSFORM_OT_resize") is None
    assert (cursor.location - Vector((3.0, 0.0, 1.0))).length < 1e-6
    # a single vertex turned about the pivot moves like a translation: told apart by the operator
    _select(ob, lambda co: co.x > 0 and co.y > 0 and co.z > 0)
    hold.COMPONENT.tick(bpy.context)
    _place_pivot((3.0, 0.0, 1.0))
    bpy.ops.transform.rotate(value=0.5, orient_axis='Z')
    assert follow().update(bpy.context, "TRANSFORM_OT_rotate") is None
    # a typed / scripted change (no registered move): the pivot stays and the next move counts from there
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        if v.select:
            v.co.x += 2.0
    bmesh.update_edit_mesh(ob.data)
    assert follow().update(bpy.context, None) is None
    bpy.ops.transform.translate(value=(0.0, 0.0, 1.0))
    follow().update(bpy.context, "TRANSFORM_OT_translate")
    assert (cursor.location - Vector((3.0, 0.0, 2.0))).length < 1e-5, cursor.location


def test_pin_keeps_the_pivot_in_place():
    _edit_cube()
    bpy.context.window_manager.allset_pin_pivot = True
    try:
        _place_pivot((3.0, 0.0, 1.0))
        bpy.ops.transform.translate(value=(0.0, 0.0, 1.0))
        assert follow().update(bpy.context, "TRANSFORM_OT_translate") is None
        assert (bpy.context.scene.cursor.location - Vector((3.0, 0.0, 1.0))).length < 1e-6
    finally:
        bpy.context.window_manager.allset_pin_pivot = False


def test_offset_while_a_move_runs_is_the_components_offset():
    ob = _edit_cube()
    _place_pivot((3.0, 0.0, 1.0))
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        if v.select:
            v.co.y += 0.25
    bmesh.update_edit_mesh(ob.data)
    d = follow().pending(bpy.context, "TRANSFORM_OT_translate")
    assert d is not None and (d - Vector((0.0, 0.25, 0.0))).length < 1e-6, d
    assert follow().pending(bpy.context, "TRANSFORM_OT_rotate") is None
    assert (bpy.context.scene.cursor.location - Vector((3.0, 0.0, 1.0))).length < 1e-6, "display only"


def test_undo_and_redo_take_the_pivot_with_the_move():
    _edit_cube()
    _place_pivot((3.0, 0.0, 1.0))
    cursor = bpy.context.scene.cursor
    bpy.ops.ed.undo_push(message="placed")
    bpy.ops.transform.translate(value=(0.0, 0.0, 1.0))
    bpy.ops.ed.undo_push(message="moved")
    follow().update(bpy.context, "TRANSFORM_OT_translate")
    assert (cursor.location - Vector((3.0, 0.0, 2.0))).length < 1e-5
    bpy.ops.ed.undo()
    assert (bpy.context.scene.cursor.location - Vector((3.0, 0.0, 1.0))).length < 1e-5, "undo: back with the move"
    bpy.ops.ed.redo()
    assert (bpy.context.scene.cursor.location - Vector((3.0, 0.0, 2.0))).length < 1e-5, "redo: forward again"


def test_leaving_edit_mode_forgets_the_moves():
    _edit_cube()
    _place_pivot()
    bpy.ops.transform.translate(value=(0.0, 0.0, 1.0))
    follow().update(bpy.context, "TRANSFORM_OT_translate")
    assert follow().journal_size() == 1
    bpy.ops.object.mode_set(mode='OBJECT')
    hold.COMPONENT.tick(bpy.context)
    assert not hold.COMPONENT.custom
    follow().update(bpy.context, None)
    assert follow().journal_size() == 0
