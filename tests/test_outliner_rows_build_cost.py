"""The Maya Outliner's rows in a big file: the steps of a move / rotate / scale don't make the structure check read
the update. The structure check decides as before."""

from importlib import import_module

import bpy

import kit

outliner = import_module(kit.MODULE + ".ui.outliner")
depsgraph_filter = import_module(kit.MODULE + ".depsgraph_filter")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for data in (bpy.data.armatures, bpy.data.meshes, bpy.data.lights, bpy.data.cameras, bpy.data.curves):
        for d in list(data):
            data.remove(d)


def _link(name, data=None, parent=None):
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob


class _CountedLook(depsgraph_filter.Look):
    made = 0

    def __init__(self, depsgraph):
        type(self).made += 1
        super().__init__(depsgraph)


def test_move_steps_skip_the_structure_checks_pass_over_the_update():
    """During a move / rotate / scale the structure can't change, so each step's update is not read for the
    structure check (one pass over every ID of the update); outside a transform the check decides as before."""
    _clear()
    me = bpy.data.meshes.new("pCubeShape")
    ob = _link("pCube1", me)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    real_posing, real_look = outliner._posing, depsgraph_filter.Look
    depsgraph_filter.Look = _CountedLook
    try:
        outliner._posing = lambda: True
        _CountedLook.made = 0
        v = outliner.structure_version()
        for _step in range(5):
            outliner._on_depsgraph(sc, dg)
        assert outliner.structure_version() == v, "a transform step keeps the structure"
        assert _CountedLook.made == 0, f"5 transform steps read the update {_CountedLook.made} times"
        # not transforming: an update with nothing in it changes the structure (as before)
        outliner._posing = lambda: False
        outliner._on_depsgraph(sc, dg)
        assert outliner.structure_version() == v + 1
        assert _CountedLook.made == 1

        def broken():
            raise ReferenceError("gone")
        outliner._posing = broken
        outliner._on_depsgraph(sc, dg)
        assert outliner.structure_version() == v + 2, "an unreadable transform state still counts the update"
        outliner._on_depsgraph(sc, None)
        assert outliner.structure_version() == v + 3
    finally:
        outliner._posing, depsgraph_filter.Look = real_posing, real_look
    ob.name = "renamed"
    _clear()
