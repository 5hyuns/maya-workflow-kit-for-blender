"""The Maya Outliner's cached rows and Python's garbage collector: the cache keeps only the rows of the current scene
structure (an edit used to leave the old rows behind, up to 17 copies of every row), and a rebuild after an edit
keeps the rows that did not change (the same objects), so it adds new long-lived objects only for what changed. A
full collection walks every long-lived object, and new ones are what start it. The rows are the same as a fresh
build's."""

import gc
import types
from importlib import import_module

import bpy

import kit

tree = import_module(kit.MODULE + ".ui.outliner_tree")
outliner = import_module(kit.MODULE + ".ui.outliner")
maya_outliner = import_module(kit.MODULE + ".ui.maya_outliner")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for data in (bpy.data.armatures, bpy.data.meshes, bpy.data.lights, bpy.data.cameras):
        for d in list(data):
            data.remove(d)


def _link(name, data=None, parent=None):
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob


def _scene(n):
    """``n`` meshes (every tenth one parented to the one before it), a rig with two joints and an object under the
    rig."""
    me = bpy.data.meshes.new("pCubeShape")
    prev = None
    for i in range(n):
        prev = _link(f"pCube{i + 1}", me, parent=prev if i % 10 == 9 else None)
    arm = bpy.data.armatures.new("rig")
    rig = _link("rig", arm)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    b1 = arm.edit_bones.new("joint1")
    b1.head, b1.tail = (0, 0, 0), (0, 0, 1)
    b2 = arm.edit_bones.new("joint2")
    b2.head, b2.tail = (0, 0, 1), (0, 0, 2)
    b2.parent = b1
    bpy.ops.object.mode_set(mode='OBJECT')
    _link("rigChild", me, parent=rig)
    bpy.context.view_layer.update()


def _outliner():
    area = next(a for a in bpy.data.screens["Layout"].areas if a.type == 'OUTLINER')
    return area.spaces.active


def _tracked_under(root):
    """Garbage-collector-tracked objects reachable from ``root`` (``root`` included), classes and modules left out
    (an instance of a Python class refers to its class)."""
    seen, stack = set(), [root]
    while stack:
        o = stack.pop()
        if id(o) in seen or not gc.is_tracked(o) or isinstance(o, (type, types.ModuleType)):
            continue
        seen.add(id(o))
        stack.extend(gc.get_referents(o))
    return len(seen)


def _fresh(sp):
    """The rows a new build gives now (no cache, no reuse)."""
    return tree.build(bpy.context.scene, bpy.context.view_layer, tree.options(sp)) + \
        tree.tail_rows(bpy.context.scene, tree.options(sp))


def test_the_cache_keeps_only_the_current_rows():
    """Six structure edits in a row: the cache still holds one set of rows (it held all seven), so the objects the
    garbage collector walks for it stay about one per row."""
    _clear()
    _scene(300)
    sp = _outliner()
    saved = (sp.display_mode, sp.use_filter_collection, sp.show_mode_column, sp.use_filter_object)
    tree.EXPANDED.clear()
    try:
        maya_outliner.setup(sp)
        tree._cache.clear()
        rows = tree.rows_for(bpy.context, sp)
        for _ in range(6):
            outliner._bump()
            rows = tree.rows_for(bpy.context, sp)
        assert rows == _fresh(sp), "the rows are a fresh build's"
        gc.collect()
        assert len(tree._cache) == 1, len(tree._cache)
        n = _tracked_under(tree._cache)
        assert n <= len(rows) + 10, (n, len(rows))
    finally:
        tree._cache.clear()
        (sp.display_mode, sp.use_filter_collection, sp.show_mode_column, sp.use_filter_object) = saved
        _clear()


def test_a_rebuild_keeps_the_rows_that_did_not_change():
    """A rename rebuilds the rows: every row but the renamed object's is the row object built before (the rows that
    live on are what the garbage collector counts towards its next full pass), and the rows equal a fresh build's —
    after a rename, an expand, a re-parent and a removal too."""
    _clear()
    _scene(300)
    sp = _outliner()
    saved = (sp.display_mode, sp.use_filter_collection, sp.show_mode_column, sp.use_filter_object)
    tree.EXPANDED.clear()
    try:
        maya_outliner.setup(sp)
        tree._cache.clear()
        before = tree.rows_for(bpy.context, sp)
        old = {id(r) for r in before}
        bpy.data.objects["pCube5"].name = "renamed5"
        outliner._bump()
        after = tree.rows_for(bpy.context, sp)
        assert after == _fresh(sp)
        made = [r for r in after if id(r) not in old]
        assert [r.ob for r in made if r.kind != 'DEFAULT_SET'] == ["renamed5"], made
        assert len(after) == len(before)

        rig = bpy.data.objects["rig"]
        tree.set_expanded([('O', rig.session_uid)], True)
        assert tree.rows_for(bpy.context, sp) == _fresh(sp), "expanded"
        bpy.data.objects["pCube3"].parent = bpy.data.objects["pCube1"]
        tree.set_expanded([('O', bpy.data.objects["pCube1"].session_uid)], True)
        outliner._bump()
        assert tree.rows_for(bpy.context, sp) == _fresh(sp), "re-parented"
        bpy.data.objects.remove(bpy.data.objects["pCube7"])
        bpy.context.view_layer.update()
        outliner._bump()
        assert tree.rows_for(bpy.context, sp) == _fresh(sp), "removed"
    finally:
        tree._cache.clear()
        tree.EXPANDED.clear()
        (sp.display_mode, sp.use_filter_collection, sp.show_mode_column, sp.use_filter_object) = saved
        _clear()


def test_reuse_gives_the_same_rows_for_every_filter():
    """``build`` with the rows of an earlier build to reuse gives rows equal to a build without, for Shapes,
    Children off, Show filters and a search."""
    _clear()
    _scene(40)
    sc, vl = bpy.context.scene, bpy.context.view_layer
    for o in bpy.data.objects:
        tree.EXPANDED.add(('O', o.session_uid))
    try:
        earlier = tree.build(sc, vl, tree.default_options())
        bpy.data.objects["pCube2"].name = "other2"
        pool = {r: r for r in earlier}
        for types in (tree.ALL_TYPES, frozenset({'MESH'}), frozenset({'ARMATURE'})):
            for children in (True, False):
                for shapes in (False, True):
                    for search in ("", "Cube1"):
                        opts = tree.default_options(children=children, shapes=shapes, types=types, search=search)
                        assert tree.build(sc, vl, opts, reuse=dict(pool)) == tree.build(sc, vl, opts), \
                            (types, children, shapes, search)
    finally:
        tree.EXPANDED.clear()
        _clear()
