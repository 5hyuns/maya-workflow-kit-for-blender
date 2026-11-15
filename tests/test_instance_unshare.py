"""Duplicate Special > Instance: the Outliner marks instances (and the groups above them), and Freeze
Transformations / Delete History turn an instance into a plain object that no longer follows the original."""

import importlib

import bpy

import kit


def _mod(name):
    return importlib.import_module(kit.MODULE + "." + name)


def _instance_pair():
    """group1 (pCube1, pSphere1) and its instance copy; returns (group1, kids, copy)."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    coll = bpy.context.scene.collection
    grp = bpy.data.objects.new("group1", None)
    coll.objects.link(grp)
    kids = []
    for name in ("pCube1", "pSphere1"):
        me = bpy.data.meshes.new(name + "Shape")
        me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        ob.parent = grp
        kids.append(ob)
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    grp.select_set(True)
    bpy.context.view_layer.objects.active = grp
    assert bpy.ops.allset.duplicate_special(geometry_type='INSTANCE') == {'FINISHED'}
    copy = bpy.context.view_layer.objects.active
    assert copy is not grp and {c.data for c in copy.children} == {k.data for k in kids}
    return grp, kids, copy


def _key(ob):
    return ('O', ob.session_uid)


def test_outliner_marks_only_the_instance_copies():
    grp, kids, copy = _instance_pair()
    lone = bpy.data.objects.new("plain", bpy.data.meshes.new("plainShape"))
    bpy.context.scene.collection.objects.link(lone)
    fix = bpy.data.objects.new("fix", None)      # a group above both: unmarked
    bpy.context.scene.collection.objects.link(fix)
    grp.parent = copy.parent = fix
    keys = _mod("ui.outliner_tree").instance_keys(bpy.context)
    for ob in (copy, *copy.children):
        assert _key(ob) in keys, ob.name
    for ob in (grp, *kids, fix, lone):            # the originals share the mesh but aren't instances
        assert _key(ob) not in keys, ob.name


def test_plain_copy_of_an_instance_is_unmarked():
    grp, kids, copy = _instance_pair()
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    copy.select_set(True)
    bpy.context.view_layer.objects.active = copy
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    plain = bpy.context.view_layer.objects.active
    assert not any(ob.get("allset_instance") for ob in (plain, *plain.children))


def _check_plain(grp, kids, copy):
    for c in copy.children:
        assert c.data not in {k.data for k in kids}, c.name
    kids[0].data.vertices[0].co.z = 3.0               # an edit on the original no longer shows on the copy
    assert all(c.data.vertices[0].co.z == 0.0 for c in copy.children)
    keys = _mod("ui.outliner_tree").instance_keys(bpy.context)
    assert not {_key(ob) for ob in (grp, copy, *kids, *copy.children)} & keys


def test_freeze_on_instance_group_makes_plain_objects():
    grp, kids, copy = _instance_pair()                # copy in place: Freeze has nothing to bake
    assert bpy.ops.allset.freeze_transform() == {'FINISHED'}
    _check_plain(grp, kids, copy)


def test_delete_history_on_instance_group_makes_plain_objects():
    grp, kids, copy = _instance_pair()
    assert bpy.ops.allset.delete_history() == {'FINISHED'}
    _check_plain(grp, kids, copy)


def test_delete_history_bakes_the_copy_only():
    grp, kids, copy = _instance_pair()
    c = copy.children[0]
    c.modifiers.new("solid", 'SOLIDIFY')
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    c.select_set(True)
    bpy.context.view_layer.objects.active = c
    before = {k.name: len(k.data.vertices) for k in kids}
    assert bpy.ops.allset.delete_history() == {'FINISHED'}
    assert not c.modifiers and len(c.data.vertices) == 6         # solidify baked into the copy's own mesh
    assert {k.name: len(k.data.vertices) for k in kids} == before  # the original's mesh untouched


def test_unshare_keeps_original_data_on_the_last_sharer():
    grp, kids, copy = _instance_pair()
    data = kids[0].data
    assert _mod("operators.duplicate").unshare([grp, copy]) == 2
    owners = [ob for ob in bpy.data.objects if ob.data is data]
    assert len(owners) == 1, [o.name for o in owners]
