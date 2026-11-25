"""#570: a Smart Duplicate whose drag was cancelled is taken back even before the scene has updated.

A cancelled transform puts the copy's channels back at once; its world matrix follows only at the next scene update.
Whether the copy moved is read from the channels, so the check right after the cancel sees it unmoved.
"""

from importlib import import_module

import bpy

import kit

manip = import_module(kit.MODULE + ".operators.manip")


def _fresh():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add()
    return bpy.context.view_layer.objects.active


def test_cancelled_copy_counts_as_unmoved_before_the_scene_update():
    ob = _fresh()
    state = manip.start_duplicate(bpy.context)
    copy = bpy.data.objects[state["copies"][0]]
    assert copy is not ob

    # the drag moves the copy and the scene updates (the world matrix follows)
    copy.location.x = 1.785
    bpy.context.view_layer.update()
    assert manip.moved(state), "a moved copy is kept"

    # cancel: the channels go back, the world matrix is still the moved one until the next update
    copy.location.x = 0.0
    assert abs(copy.matrix_world.translation.x - 1.785) < 1e-6, "world matrix not updated yet"
    assert not manip.moved(state), "the cancelled copy is seen as unmoved and taken back"

    manip.revert(state)
    assert state["copies"][0] not in bpy.data.objects
    assert ob.select_get() and bpy.context.view_layer.objects.active is ob


def test_rotated_or_scaled_copy_is_kept():
    _fresh()
    state = manip.start_duplicate(bpy.context)
    copy = bpy.data.objects[state["copies"][0]]
    copy.rotation_euler.z = 0.5
    assert manip.moved(state)
    copy.rotation_euler.z = 0.0
    copy.scale.y = 2.0
    assert manip.moved(state)
