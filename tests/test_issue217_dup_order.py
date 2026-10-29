"""#217: a duplicated object carries its original's creation-order number (an ID property copy). The Outliner order
sync then saw two objects with the same number, linked them one way, read them back the other way and relinked
every 0.25 s for ever: the rows swapped, the selection flickered and the Move manipulator could not be dragged.
A copy now counts as a new node (Maya: a duplicate goes last among its siblings) and the sync settles."""

from importlib import import_module

import bpy

import kit


def m(name):
    return import_module(f"{kit.MODULE}.{name}")


def _scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    sc = bpy.context.scene
    coll = bpy.data.collections.new("Collection")
    sc.collection.children.link(coll)
    m("operators.startup_cameras").ensure(sc, bpy.context.view_layer)
    return sc, coll


def _cube(name, coll):
    me = bpy.data.meshes.new(name + "Shape")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _dup(ob, coll, name):
    """What Blender's duplicate does to the ID: a copy with the same ID properties, linked at the end."""
    new = ob.copy()
    new.name = name
    coll.objects.link(new)
    return new


def _shown(coll):
    oo = m("ui.outliner_order")
    return oo.display_order([o.name for o in coll.objects if o.parent is None], True)


def test_duplicate_gets_its_own_number_and_goes_last():
    sc, coll = _scene()
    oo = m("ui.outliner_order")
    vl = bpy.context.view_layer
    a = _cube("pCube1", coll)
    b = _cube("pCube2", coll)
    oo.sync(sc, vl, rotate=True)
    c = _dup(a, coll, "pCube3")
    assert c.get(oo.ORDER) == a.get(oo.ORDER), "the copy starts with the original's number (Blender copies it)"
    oo.sync(sc, vl, rotate=True)
    numbers = [o.get(oo.ORDER) for o in sc.objects]
    assert len(set(numbers)) == len(numbers), numbers
    assert c[oo.ORDER] > b[oo.ORDER] > a[oo.ORDER]
    assert _shown(coll) == ["persp", "top", "front", "side", "pCube1", "pCube2", "pCube3"], _shown(coll)


def test_sync_settles_after_a_duplicate():
    sc, coll = _scene()
    oo = m("ui.outliner_order")
    vl = bpy.context.view_layer
    a = _cube("pCube1", coll)
    oo.sync(sc, vl, rotate=True)
    b = _dup(a, coll, "pCube2")
    for o in sc.objects:
        o.select_set(o is b)
    vl.objects.active = b
    oo.sync(sc, vl, rotate=True)
    relinks = [oo.sync(sc, vl, rotate=True) for _i in range(8)]
    assert not any(relinks), f"the 0.25 s sync keeps relinking: {relinks}"
    assert _shown(coll)[-2:] == ["pCube1", "pCube2"], _shown(coll)
    assert b.select_get() and not a.select_get() and vl.objects.active == b


def test_several_copies_and_a_saved_tie_settle():
    """Copies of copies, and a file saved with two equal numbers (an earlier version): every number unique, the
    first in link order keeps its number."""
    sc, coll = _scene()
    oo = m("ui.outliner_order")
    vl = bpy.context.view_layer
    a = _cube("pCube1", coll)
    oo.sync(sc, vl, rotate=True)
    b = _dup(a, coll, "pCube2")
    c = _dup(b, coll, "pCube3")
    d = _dup(a, coll, "pCube4")
    keep = a[oo.ORDER]
    oo.sync(sc, vl, rotate=True)
    assert a[oo.ORDER] == keep
    assert a[oo.ORDER] < b[oo.ORDER] < c[oo.ORDER] < d[oo.ORDER]
    assert not any(oo.sync(sc, vl, rotate=True) for _i in range(6))
    assert _shown(coll)[4:] == ["pCube1", "pCube2", "pCube3", "pCube4"], _shown(coll)


def test_tie_rule_is_pure():
    oo = m("ui.outliner_order")

    class Ob(dict):
        def __init__(self, name, n, uid):
            super().__init__()
            self.name, self.session_uid = name, uid
            if n is not None:
                self[oo.ORDER] = n

    a, b, c, d = Ob("a", 0, 5), Ob("b", 0, 9), Ob("c", None, 7), Ob("d", 1, 6)
    oo.number_new([b, a, c, d])
    assert a[oo.ORDER] == 0 and d[oo.ORDER] == 1, "the older ID keeps the shared number"
    assert b[oo.ORDER] == 2 and c[oo.ORDER] == 3, "copies and new objects go last, in creation order"
