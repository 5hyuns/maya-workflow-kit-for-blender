# SPDX-License-Identifier: GPL-3.0-or-later
"""#351 follow-up: a component pivot edit (D latch / Insert) or a placed component pivot belongs to the file it was
made in. After File > Open / New / Revert the next file has no pivot edit running and no placed pivot following its
components; the Maya tool settings the kit carries from file to file (pivot point, select mode) are the user's, not
the ones the pivot edit had set for a while."""

import os
from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix

import kit

hold = import_module(kit.MODULE + ".operators.hold")
manip = import_module(kit.MODULE + ".operators.manip")
manipulator = import_module(kit.MODULE + ".ui.manipulator")
pivot_follow = import_module(kit.MODULE + ".operators.pivot_follow")

TMP = bpy.app.tempdir or os.environ.get("TEMP", ".")
OTHER = os.path.join(TMP, "issue351_other.blend")
THIS = os.path.join(TMP, "issue351_this.blend")


def _tool(name):
    bpy.ops.wm.tool_set_by_id(name=name, space_type='VIEW_3D')


def _cube_scene(pivot_point='BOUNDING_BOX_CENTER', select_mode=(False, False, True)):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    ts = bpy.context.scene.tool_settings
    ts.transform_pivot_point = pivot_point
    ts.mesh_select_mode = select_mode
    bpy.context.scene.cursor.matrix = Matrix.Identity(4)
    bpy.context.window_manager.allset_pin_pivot = False
    return ob


def _edit_select_top(ob):
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        v.select = v.co.z > 0
    bm.select_flush(True)
    bmesh.update_edit_mesh(ob.data)


def _save_other(pivot_point='MEDIAN_POINT', select_mode=(True, False, False)):
    """The next file: its own pivot point and select mode."""
    _cube_scene(pivot_point, select_mode)
    bpy.ops.wm.save_as_mainfile(filepath=OTHER, copy=True)


def _edit_on_in_this_file(save=False):
    """Face mode, top face, Move tool, Insert = a pivot edit running in this file."""
    ob = _cube_scene()
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=THIS)
    _edit_select_top(ob)
    _tool("builtin.move")
    assert bpy.ops.allset.pivot_toggle() == {'FINISHED'}
    assert hold.COMPONENT.on


def _custom_in_this_file(save=False):
    """A placed component pivot (Insert, move it, Insert) in this file."""
    ob = _cube_scene()
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=THIS)
    _edit_select_top(ob)
    _tool("builtin.move")
    bpy.ops.allset.pivot_toggle()
    bpy.context.scene.cursor.location = (3.0, 0.0, 1.0)
    bpy.ops.allset.pivot_toggle()
    assert hold.COMPONENT.custom and not hold.COMPONENT.on


def _edit_in_next_file():
    ob = bpy.context.scene.objects[0]
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    _edit_select_top(ob)
    _tool("builtin.move")
    return ob


LOADERS = {
    "open": lambda: bpy.ops.wm.open_mainfile(filepath=OTHER),
    "new": lambda: bpy.ops.wm.read_homefile(),
    "revert": lambda: bpy.ops.wm.revert_mainfile(),
}


def _load(how):
    LOADERS[how]()
    if not any(ob.type == 'MESH' for ob in bpy.context.scene.objects):
        bpy.ops.mesh.primitive_cube_add()


def test_a_running_pivot_edit_ends_with_its_file():
    for how in LOADERS:
        hold.unregister_cleanup()
        _save_other()
        _edit_on_in_this_file(save=(how == "revert"))
        _load(how)
        assert not hold.COMPONENT.on, f"{how}: the pivot edit of the previous file is still on"
        _edit_in_next_file()
        assert not manip.component_pivot_edit(bpy.context), how
        assert not manipulator.pivot_edit(bpy.context), f"{how}: the manipulator would show pivot handles"
    hold.unregister_cleanup()


def test_the_next_file_gets_the_users_settings():
    """The pivot edit sets the pivot point to the 3D cursor and every select mode for a while; the next file gets the
    user's pivot point and select mode (carried like Maya's tool settings), and Insert twice there starts and ends a
    pivot edit of its own."""
    for how in LOADERS:
        hold.unregister_cleanup()
        _save_other('MEDIAN_POINT', (True, False, False))
        _edit_on_in_this_file(save=(how == "revert"))      # face mode, Bounding Box Center, then the pivot edit
        ts = bpy.context.scene.tool_settings
        assert ts.transform_pivot_point == 'CURSOR' and tuple(ts.mesh_select_mode) == (True, True, True)
        _load(how)
        ts = bpy.context.scene.tool_settings
        assert ts.transform_pivot_point == 'BOUNDING_BOX_CENTER', (how, ts.transform_pivot_point)
        assert tuple(ts.mesh_select_mode) == (False, False, True), (how, tuple(ts.mesh_select_mode))
        _edit_in_next_file()
        mode, point = tuple(ts.mesh_select_mode), ts.transform_pivot_point
        assert bpy.ops.allset.pivot_toggle() == {'FINISHED'}
        assert hold.COMPONENT.on, f"{how}: Insert starts a pivot edit in this file"
        bpy.ops.allset.pivot_toggle()
        assert not hold.COMPONENT.on
        assert (tuple(ts.mesh_select_mode), ts.transform_pivot_point) == (mode, point), how
    hold.unregister_cleanup()


def test_a_placed_pivot_hands_the_users_pivot_point_on():
    """A placed pivot is the 3D cursor pivot for a while: the next file gets the pivot point the user had."""
    for how in LOADERS:
        hold.unregister_cleanup()
        _save_other('MEDIAN_POINT')
        _custom_in_this_file(save=(how == "revert"))       # Bounding Box Center, then the placed pivot
        assert bpy.context.scene.tool_settings.transform_pivot_point == 'CURSOR'
        _load(how)
        assert bpy.context.scene.tool_settings.transform_pivot_point == 'BOUNDING_BOX_CENTER', how
    hold.unregister_cleanup()
    hold.unregister_cleanup()


def test_a_placed_pivot_stays_with_its_file():
    for how in LOADERS:
        hold.unregister_cleanup()
        _save_other('CURSOR')                 # the user's own file: Pivot Point = 3D Cursor
        _custom_in_this_file(save=(how == "revert"))
        _load(how)
        bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'
        _edit_in_next_file()
        assert not hold.COMPONENT.custom and hold.COMPONENT.outside is None, how
        assert not pivot_follow.active(bpy.context), f"{how}: the kit follow would drive the user's 3D cursor"
    hold.unregister_cleanup()


def test_the_users_cursor_pivot_never_follows():
    """The next file's own 3D cursor pivot: a Move of the components (after an Undo) leaves the cursor alone."""
    hold.unregister_cleanup()
    _save_other('CURSOR')
    _custom_in_this_file()
    bpy.ops.wm.open_mainfile(filepath=OTHER)
    ob = _edit_in_next_file()
    sc = bpy.context.scene
    sc.tool_settings.transform_pivot_point = 'CURSOR'      # the user's own 3D cursor pivot in this file
    sc.cursor.location = (5.0, 5.0, 5.0)
    pivot_follow._step(bpy.context, True)            # what an Undo in component mode runs
    bm = bmesh.from_edit_mesh(ob.data)
    for v in bm.verts:
        if v.select:
            v.co.z += 1.0
    bmesh.update_edit_mesh(ob.data)
    assert pivot_follow.update(bpy.context, "TRANSFORM_OT_translate") is None
    assert tuple(sc.cursor.location) == (5.0, 5.0, 5.0), tuple(sc.cursor.location)
    hold.unregister_cleanup()
