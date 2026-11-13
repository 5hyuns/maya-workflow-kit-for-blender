"""The Maya Outliner's rows in a big file: a rebuild of the rows (after a load, an undo, an added, removed, renamed or
re-parented object) asks each object for what it needs only (an icon kind is worked out once per object type; only an
empty reads the locator flag), a redraw finds a local object's row without counting the file's objects (only a linked
object's row checks the count), and the steps of a move / rotate / scale don't make the structure check read the
update. The rows, icons and objects found are the same as before."""

import os
import tempfile
from importlib import import_module

import bpy

import kit

tree = import_module(kit.MODULE + ".ui.outliner_tree")
outliner = import_module(kit.MODULE + ".ui.outliner")
layout = import_module(kit.MODULE + ".ui.hypergraph_layout")
create = import_module(kit.MODULE + ".operators.create")
depsgraph_filter = import_module(kit.MODULE + ".depsgraph_filter")


class _Count:
    """Counts the calls of a module attribute (function or class) while installed."""

    def __init__(self, module, name):
        self.module, self.name, self.calls = module, name, 0
        self.real = getattr(module, name)

    def __enter__(self):
        real = self.real

        def counted(*a, **k):
            self.calls += 1
            return real(*a, **k)
        setattr(self.module, self.name, counted)
        return self

    def __exit__(self, *exc):
        setattr(self.module, self.name, self.real)


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


def _mixed():
    """Objects of every row kind: meshes, empties (a locator among them), a light, a camera, a curve, a lattice, a
    named rig with joints and children, an object hidden in the Outliner."""
    me = bpy.data.meshes.new("pCubeShape")
    a = _link("pCube1", me)
    _link("pCube2", me, parent=a)
    loc = _link("locator1")
    loc[create.LOCATOR_PROP] = True
    grp = _link("group1")
    _link("inGroup", me, parent=grp)
    _link("light1", bpy.data.lights.new("light1", 'POINT'))
    _link("camera1", bpy.data.cameras.new("camera1"))
    _link("curve1", bpy.data.curves.new("curve1", 'CURVE'))
    _link("lattice1", bpy.data.lattices.new("lattice1"))
    hidden = _link("hidden1", me)
    hidden["allset_hidden_in_outliner"] = True
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
    prop = _link("prop", me, parent=rig)
    prop.parent_type = 'BONE'
    prop.parent_bone = "joint2"
    _link("rigChild", me, parent=rig)
    for i in range(30):
        _link(f"leaf{i}", me)
    bpy.context.view_layer.update()


def test_rows_show_each_objects_own_icon_and_filters():
    """Every object row carries the icon of its own object (``icon_kind``) and is kept or dropped by its own type
    group (Show filters), with Display > Shapes, Children off and a search too."""
    _clear()
    _mixed()
    sc, vl = bpy.context.scene, bpy.context.view_layer
    for o in bpy.data.objects:
        tree.EXPANDED.add(('O', o.session_uid))
    for types in (tree.ALL_TYPES, frozenset({'MESH'}), frozenset({'EMPTY', 'LIGHT'}), frozenset()):
        for children in (True, False):
            for shapes in (False, True):
                for search in ("", "1"):
                    opts = tree.default_options(children=children, shapes=shapes, types=types, search=search)
                    rows = tree.build(sc, vl, opts)
                    for r in rows:
                        if r.kind not in ('OBJECT', 'SHAPE'):
                            continue
                        ob = bpy.data.objects[r.ob]
                        assert r.icon == tree.icon_kind(ob), (r, tree.icon_kind(ob))
                        assert r.kind == 'SHAPE' or tree.type_group(ob) in types, (r, types)
                        assert r.kind == 'OBJECT' or (shapes and r.label == ob.data.name), r
                    shown = {r.ob for r in rows if r.kind == 'OBJECT'}
                    for ob in bpy.data.objects:
                        top_leaf = not ob.children and ob.type != 'ARMATURE' and ob.parent is None
                        if (top_leaf and tree.type_group(ob) in types and not ob.get("allset_hidden_in_outliner")
                                and (not search or search in ob.name)):
                            assert ob.name in shown, (ob.name, types, children, shapes, search)
                        if ob.get("allset_hidden_in_outliner"):
                            assert ob.name not in shown, ob.name
    tree.EXPANDED.clear()
    _clear()


def test_a_rows_build_works_out_an_icon_kind_once_per_type():
    """A rows build of 3,000 meshes worked out each row's icon kind (``node_kind``) and read its locator flag one
    object at a time: now once per object type, and only an empty reads the flag."""
    _clear()
    me = bpy.data.meshes.new("pCubeShape")
    for i in range(3000):
        _link(f"pCube{i + 1}", me)
    for i in range(5):
        _link(f"null{i + 1}")
    bpy.context.view_layer.update()
    sc, vl = bpy.context.scene, bpy.context.view_layer
    with _Count(layout, "node_kind") as kinds:
        rows = tree.build(sc, vl, tree.default_options())
    assert len([r for r in rows if r.kind == 'OBJECT']) == 3005
    assert {r.icon for r in rows if r.ob.startswith("pCube")} == {'MESH'}
    assert {r.icon for r in rows if r.ob.startswith("null")} == {'GROUP'}
    assert kinds.calls <= 10, f"the icon kind was worked out {kinds.calls} times for 3,005 rows"
    _clear()


class _CountedObjects:
    """``bpy.data.objects`` that counts how often its length is read."""

    def __init__(self, real, counts):
        self._real, self._counts = real, counts

    def __len__(self):
        self._counts["len"] += 1
        return len(self._real)

    def __getattr__(self, name):
        return getattr(self._real, name)


class _CountedBpy:
    def __init__(self, counts):
        self.data = _CountedData(counts)

    def __getattr__(self, name):
        return getattr(bpy, name)


class _CountedData:
    def __init__(self, counts):
        self._counts = counts

    @property
    def objects(self):
        return _CountedObjects(bpy.data.objects, self._counts)

    def __getattr__(self, name):
        return getattr(bpy.data, name)


def _linked_file():
    """A library file with objects ``shared`` and ``onlyLinked``; links both in. Returns the linked objects."""
    me = bpy.data.meshes.new("libShape")
    a = bpy.data.objects.new("shared", me)
    b = bpy.data.objects.new("onlyLinked", me)
    path = os.path.join(tempfile.gettempdir(), "allset_outliner_names_lib.blend")
    bpy.data.libraries.write(path, {a, b}, fake_user=True)
    bpy.data.objects.remove(a)
    bpy.data.objects.remove(b)
    with bpy.data.libraries.load(path, link=True) as (src, dst):
        dst.objects = ["shared", "onlyLinked"]
    return dst.objects


def test_rows_find_local_and_linked_objects_like_get():
    """With a linked library a local and a linked object can share a name: a row finds what ``bpy.data.objects.get``
    finds (the local one) after objects are added, renamed and removed with no update in between, and a redraw of
    local rows doesn't count the file's objects (it counted them on every redraw of a file with a library)."""
    _clear()
    me = bpy.data.meshes.new("pCubeShape")
    locals_ = [_link(f"pCube{i + 1}", me) for i in range(50)]
    linked = _linked_file()
    assert all(o.library is not None for o in linked) and len(bpy.data.libraries)
    names = [o.name for o in locals_] + ["shared", "onlyLinked", "nothing"]
    tree._by_name["key"] = None
    for n in names:
        assert tree.object_named(n) == bpy.data.objects.get(n), n
    # a local object takes a linked object's name (no update, so the kept names stay): get finds the local one
    clash = _link("shared", me)
    assert clash.name == "shared" and clash.library is None
    for n in names:
        assert tree.object_named(n) == bpy.data.objects.get(n), n
    assert tree.object_named("shared") == clash
    clash.name = "notShared"
    locals_[3].name = "onlyLinked"
    bpy.context.view_layer.update()                  # a rename updates the scene before the next redraw
    for n in names + ["notShared", "pCube4"]:
        assert tree.object_named(n) == bpy.data.objects.get(n), n
    bpy.data.objects.remove(locals_[3])
    for n in names + ["notShared", "pCube4"]:
        assert tree.object_named(n) == bpy.data.objects.get(n), n
    # redraws of local rows: no object count
    bpy.context.view_layer.update()
    tree.object_names()
    counts = {"len": 0}
    real = tree.bpy
    tree.bpy = _CountedBpy(counts)
    try:
        for _redraw in range(10):
            mapped = tree.object_names()
            for o in locals_[10:30]:
                assert tree.object_named(o.name, mapped) == o
    finally:
        tree.bpy = real
    assert counts["len"] == 0, f"10 redraws of local rows counted the objects {counts['len']} times"
    # a linked row counts at most once per redraw
    counts["len"] = 0
    tree.bpy = _CountedBpy(counts)
    try:
        for _redraw in range(3):
            mapped = tree.object_names()
            for _row in range(4):
                assert tree.object_named("onlyLinked", mapped) == bpy.data.objects.get("onlyLinked")
    finally:
        tree.bpy = real
    assert counts["len"] <= 3, counts
    _clear()
    for lib in list(bpy.data.libraries):
        bpy.data.libraries.remove(lib)


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
