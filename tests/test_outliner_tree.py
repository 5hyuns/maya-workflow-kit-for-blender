"""#348: the kit-drawn Maya Outliner tree — the row model (Maya order, joints as rows under their parent joint, objects
parented to a joint under it, Shapes / Children / search / Sort Alphabetically / Show filters, sets after the DAG),
the cached rebuild, Outliner switching (Blender's rows hidden in a Maya Outliner, back before saving and on disable)
and row selection. GUI: tests/gui/gui_outliner_tree.py."""

import os
import tempfile
import time
from importlib import import_module
from mathutils import Vector

import bpy

import kit

tree = import_module(kit.MODULE + ".ui.outliner_tree")
maya_outliner = import_module(kit.MODULE + ".ui.maya_outliner")
outliner = import_module(kit.MODULE + ".ui.outliner")
joints = import_module(kit.MODULE + ".operators.joints")
sets = import_module(kit.MODULE + ".operators.sets")
order = import_module(kit.MODULE + ".ui.outliner_order")


def _on():
    tree.ENABLED = True
    tree.EXPANDED.clear()


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for data in (bpy.data.armatures, bpy.data.meshes, bpy.data.cameras, bpy.data.lights):
        for d in list(data):
            data.remove(d)
    for c in list(bpy.data.collections):
        if sets.is_set(c):
            bpy.data.collections.remove(c)


def _mesh(name, parent=None, bone=""):
    base = name.rstrip("0123456789")
    ob = bpy.data.objects.new(name, bpy.data.meshes.new(base + "Shape" + name[len(base):]))
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
        if bone:
            ob.parent_type, ob.parent_bone = 'BONE', bone
    order.number_new(list(bpy.context.scene.objects))
    return ob


def _skeleton(chain):
    """A kit skeleton: ``chain`` = [(parent index or None, (x, y, z))]; returns (object, joint names)."""
    ob = joints.new_skeleton(bpy.context)
    names = []
    for parent, p in chain:
        names.append(joints.add_joint(ob, Vector(p), names[parent] if parent is not None else None, length=0.5))
    bpy.ops.object.mode_set(mode='OBJECT')
    order.number_new(list(bpy.context.scene.objects))
    return ob, names


def _rows(**kw):
    bpy.context.view_layer.update()       # objects linked since the last sync
    return tree.build(bpy.context.scene, bpy.context.view_layer, tree.default_options(**kw))


def _shown(rows):
    return [(r.kind, r.label, r.depth) for r in rows]


def _open(*rows_or_keys):
    for r in rows_or_keys:
        tree.EXPANDED.add(r.key if hasattr(r, "key") else r)


def _row(rows, label, kind=None):
    return next(r for r in rows if r.label == label and (kind is None or r.kind == kind))


def _rig():
    """pCube1, skeleton joint1 > (joint2 > joint3, joint4), pCylinder1 on joint2, pSphere1 under the skeleton object."""
    _clear()
    cube = _mesh("pCube1")
    sk, names = _skeleton([(None, (0, 0, 0)), (0, (0, 0, 1)), (1, (0, 0, 2)), (0, (1, 0, 1))])
    cyl = _mesh("pCylinder1", sk, names[1])
    sph = _mesh("pSphere1", sk)
    return cube, sk, names, cyl, sph


def test_maya_order_cameras_first_then_dag():
    _on()
    _clear()
    a = _mesh("pCube1")
    b = _mesh("pSphere1")
    c = _mesh("pCone1", a)
    rows = _rows()
    assert _shown(rows) == [('CAMERA', "persp", 0), ('CAMERA', "top", 0), ('CAMERA', "front", 0),
                            ('CAMERA', "side", 0), ('OBJECT', "pCube1", 0), ('OBJECT', "pSphere1", 0)], _shown(rows)
    assert _row(rows, "pCube1").kids and not _row(rows, "pCube1").open
    _open(_row(rows, "pCube1"))
    rows = _rows()
    assert [r.label for r in rows][4:] == ["pCube1", "pCone1", "pSphere1"], _shown(rows)
    assert _row(rows, "pCone1").depth == 1
    # creation order, not link order or name: a duplicate-like renumber puts pCube1 last
    a["allset_dag_order"] = 99
    rows = _rows()
    assert [r.label for r in rows if r.kind == 'OBJECT' and r.depth == 0] == ["pSphere1", "pCube1"]
    rows = _rows(sort_alpha=True)
    assert [r.label for r in rows if r.kind == 'OBJECT' and r.depth == 0] == ["pCube1", "pSphere1"]


def test_joints_are_rows_under_their_parent_joint():
    _on()
    cube, sk, names, cyl, sph = _rig()
    j1, j2, j3, j4 = names
    rows = [r for r in _rows() if r.kind != 'CAMERA']
    assert _shown(rows) == [('OBJECT', "pCube1", 0), ('JOINT', j1, 0)], \
        f"no skeleton row: the root joint is the top node ({_shown(rows)})"
    _open(_row(rows, j1))
    rows = [r for r in _rows() if r.kind != 'CAMERA']
    assert _shown(rows)[1:] == [('JOINT', j1, 0), ('JOINT', j2, 1), ('JOINT', j4, 1), ('OBJECT', "pSphere1", 1)], \
        _shown(rows)
    _open(_row(rows, j2))
    rows = [r for r in _rows() if r.kind != 'CAMERA']
    assert _shown(rows)[1:] == [('JOINT', j1, 0), ('JOINT', j2, 1), ('JOINT', j3, 2), ('OBJECT', "pCylinder1", 2),
                                ('JOINT', j4, 1), ('OBJECT', "pSphere1", 1)], _shown(rows)
    assert not _row(rows, j3).kids and _row(rows, j2).open
    assert _row(rows, j3).ob == sk.name and _row(rows, j3).sub == j3


def test_named_armature_keeps_its_row():
    _on()
    _clear()
    sk, names = _skeleton([(None, (0, 0, 0)), (0, (0, 0, 1))])
    sk.name = "rig"
    rows = [r for r in _rows() if r.kind != 'CAMERA']
    assert _shown(rows) == [('OBJECT', "rig", 0)]
    _open(_row(rows, "rig"))
    rows = [r for r in _rows() if r.kind != 'CAMERA']
    assert _shown(rows) == [('OBJECT', "rig", 0), ('JOINT', names[0], 1)], _shown(rows)


def test_several_root_joints_each_a_row():
    _on()
    _clear()
    sk, names = _skeleton([(None, (0, 0, 0)), (None, (2, 0, 0))])
    rows = [r for r in _rows() if r.kind != 'CAMERA']
    assert _shown(rows) == [('JOINT', names[0], 0), ('JOINT', names[1], 0)], _shown(rows)


def test_shapes_children_search_and_show_filters():
    _on()
    cube, sk, names, cyl, sph = _rig()
    j1, j2, j3, j4 = names
    # Display > Shapes: the shape row under its transform
    rows = [r for r in _rows(shapes=True) if r.kind != 'CAMERA']
    assert _row(rows, "pCube1").kids
    _open(_row(rows, "pCube1"))
    rows = [r for r in _rows(shapes=True) if r.kind != 'CAMERA']
    assert _shown(rows)[:2] == [('OBJECT', "pCube1", 0), ('SHAPE', cube.data.name, 1)], _shown(rows)
    assert not any(r.kind == 'SHAPE' and r.ob == sk.name for r in rows), "joints have no shape row"
    tree.EXPANDED.clear()
    # Children off: every node, flat
    rows = [r for r in _rows(children=False) if r.kind != 'CAMERA']
    assert _shown(rows) == [('OBJECT', "pCube1", 0), ('JOINT', j1, 0), ('JOINT', j2, 0), ('JOINT', j3, 0),
                            ('OBJECT', "pCylinder1", 0), ('JOINT', j4, 0), ('OBJECT', "pSphere1", 0)], _shown(rows)
    assert not any(r.kids for r in rows)
    # search: the matches and the rows above them
    rows = _rows(search="Cylinder")
    assert _shown(rows) == [('JOINT', j1, 0), ('JOINT', j2, 1), ('OBJECT', "pCylinder1", 2)], _shown(rows)
    assert _shown(_rows(search="cylinder", case=True)) == []
    assert _shown(_rows(search="pCube", complete=True)) == []
    assert [r.label for r in _rows(search="pCube1", complete=True)] == ["pCube1"]
    # Show > Joints off: no joint rows, what hangs on them moves up
    types = tree.ALL_TYPES - {'ARMATURE'}
    rows = [r for r in _rows(types=types) if r.kind != 'CAMERA']
    assert _shown(rows) == [('OBJECT', "pCube1", 0), ('OBJECT', "pCylinder1", 0), ('OBJECT', "pSphere1", 0)], \
        _shown(rows)
    rows = _rows(types=tree.ALL_TYPES - {'CAMERA'})
    assert not any(r.kind == 'CAMERA' for r in rows), "Show > Cameras off hides the startup camera rows"


def test_sets_follow_the_dag():
    _on()
    _clear()
    a, b = _mesh("pCube1"), _mesh("pCube2")
    coll = sets.create("set1", [a, b])
    rows = tree.tail_rows(bpy.context.scene, tree.default_options())
    assert _shown(rows) == [('DEFAULT_SET', "defaultLightSet", 0), ('DEFAULT_SET', "defaultObjectSet", 0),
                            ('SET', "set1", 0)], _shown(rows)
    assert rows[-1].kids and not rows[-1].open
    tree.set_expanded([rows[-1].key], True)
    assert coll.allset_expanded
    rows = tree.tail_rows(bpy.context.scene, tree.default_options())
    assert _shown(rows)[2:] == [('SET', "set1", 0), ('MEMBER', "pCube1", 1), ('MEMBER', "pCube2", 1)], _shown(rows)


def _outliner():
    area = next(a for a in bpy.data.screens["Layout"].areas if a.type == 'OUTLINER')
    return area, area.spaces.active


def test_switching_hides_blender_rows_and_brings_them_back():
    _on()
    area, sp = _outliner()
    saved = (sp.display_mode, sp.use_filter_collection, sp.use_filter_object_content, sp.show_mode_column,
             sp.show_restrict_column_render, sp.use_filter_object)
    try:
        assert not tree.is_tree(sp) and sp.use_filter_object, "a factory Outliner is Blender's"
        assert tree.hide_all() == 0 and sp.use_filter_object, "a plain Blender Outliner keeps its rows"
        maya_outliner.setup(sp)
        assert tree.is_tree(sp) and not sp.use_filter_object, "a Maya Outliner shows the kit tree"
        assert maya_outliner.is_maya_outliner(sp)
        assert not maya_outliner.shows_dag_only(sp) and not maya_outliner.shapes_shown(sp), \
            "the old row painters and the Shapes reveal leave a kit tree alone"
        tree._on_save_pre()
        assert sp.use_filter_object, "a saved file shows Blender's rows without the kit"
        tree._on_save_post()
        assert not sp.use_filter_object and tree.is_tree(sp)
        # Display > Shapes stays a kit tree
        sp.use_filter_object_content = True
        assert tree.is_tree(sp)
        sp.use_filter_object_content = False
        # disabled tree (or the kit off): Blender's rows
        tree.ENABLED = False
        assert tree.show_all() == 1 and sp.use_filter_object
        maya_outliner.setup(sp)
        assert sp.use_filter_object, "setup leaves Blender's rows while the kit tree is off"
        tree.ENABLED = True
        assert tree.hide_all() == 1 and tree.is_tree(sp)
        # a file saved with the kit tree opens with Blender's rows
        path = os.path.join(tempfile.mkdtemp(), "tree348.blend")
        bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
        assert not sp.use_filter_object, "hidden again after saving"
        assert tree.show_all() == 1
    finally:
        (sp.display_mode, sp.use_filter_collection, sp.use_filter_object_content, sp.show_mode_column,
         sp.show_restrict_column_render, sp.use_filter_object) = saved


def test_saved_file_has_blender_rows():
    _on()
    area, sp = _outliner()
    saved = (sp.display_mode, sp.use_filter_collection, sp.show_mode_column, sp.use_filter_object)
    path = os.path.join(tempfile.mkdtemp(), "tree348b.blend")
    seen = []

    def record(*_a):
        seen.append(sp.use_filter_object)
    try:
        maya_outliner.setup(sp)
        assert not sp.use_filter_object
        bpy.app.handlers.save_pre.append(record)       # runs after the kit's save_pre, before the file is written
        bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
        assert seen == [True], f"Blender's rows are on in the written file ({seen})"
        assert not sp.use_filter_object, "and hidden again after saving"
    finally:
        if record in bpy.app.handlers.save_pre:
            bpy.app.handlers.save_pre.remove(record)
        (sp.display_mode, sp.use_filter_collection, sp.show_mode_column, sp.use_filter_object) = saved


def test_cache_rebuilds_only_on_structure_change():
    _on()
    _clear()
    _mesh("pCube1")
    area, sp = _outliner()
    saved = (sp.display_mode, sp.use_filter_collection, sp.show_mode_column, sp.use_filter_object)
    try:
        maya_outliner.setup(sp)
        ctx = bpy.context
        tree._cache.clear()
        n0 = tree.STATS["builds"]
        tree.rows_for(ctx, sp)
        tree.rows_for(ctx, sp)
        assert tree.STATS["builds"] == n0 + 1, "the same structure reuses the rows"
        bpy.data.objects["pCube1"].select_set(True)
        tree.rows_for(ctx, sp)
        assert tree.STATS["builds"] == n0 + 1, "a selection change draws from the cached rows"
        outliner._bump()
        tree.rows_for(ctx, sp)
        assert tree.STATS["builds"] == n0 + 2, "a structure change rebuilds"
    finally:
        (sp.display_mode, sp.use_filter_collection, sp.show_mode_column, sp.use_filter_object) = saved


def test_rebuild_1000_objects_is_fast():
    _on()
    _clear()
    me = bpy.data.meshes.new("pCubeShape")
    coll = bpy.context.scene.collection
    for i in range(1000):
        ob = bpy.data.objects.new(f"pCube{i + 1}", me)
        coll.objects.link(ob)
    ts = []
    for _ in range(3):
        t0 = time.perf_counter()
        rows = _rows()
        ts.append((time.perf_counter() - t0) * 1000.0)
    print("TREE348 build 1000 objects ms", [round(t, 2) for t in ts])
    assert len(rows) == 1004
    assert min(ts) < 60.0, ts


def test_select_rows_like_maya():
    _on()
    cube, sk, names, cyl, sph = _rig()
    j1, j2, j3, j4 = names
    _open(('B', sk.session_uid, j1), ('B', sk.session_uid, j2))
    rows = _rows()
    i = rows.index(_row(rows, "pCube1"))
    tree.select_row(bpy.context, rows, i, 'REPLACE')
    assert [o.name for o in bpy.context.selected_objects] == ["pCube1"] and bpy.context.active_object == cube
    k = rows.index(_row(rows, j3))
    tree.select_row(bpy.context, rows, k, 'REPLACE')
    assert sk.mode in ('POSE', 'EDIT') and bpy.context.active_object == sk, sk.mode
    assert not cube.select_get(), "a joint pick replaces the selection"
    picked = _picked(sk)
    assert picked == {j3}, picked
    m = rows.index(_row(rows, j4))
    tree.select_row(bpy.context, rows, m, 'TOGGLE')
    assert _picked(sk) == {j3, j4}, _picked(sk)
    s, a, hidden, live = tree.row_state(bpy.context, rows[m], set())
    assert s and a, (s, a)
    # a range of joints from the active joint
    j = rows.index(_row(rows, j2))
    tree.select_row(bpy.context, rows, j, 'REPLACE')
    tree.select_row(bpy.context, rows, k, 'RANGE', anchor=tree.active_row(bpy.context, rows))
    assert _picked(sk) == {j2, j3}, f"range rows j2, j3 pick the joints ({_picked(sk)})"
    # a range that also holds an object row picks objects (the skeleton stands for its joints)
    tree.select_row(bpy.context, rows, m, 'RANGE', anchor=k)
    picked = {o.name for o in bpy.context.selected_objects}
    assert sk.mode == 'OBJECT' and picked == {sk.name, "pCylinder1"}, (sk.mode, picked)
    # back to objects: the skeleton leaves Pose / Edit Mode
    tree.select_row(bpy.context, rows, i, 'REPLACE')
    assert sk.mode == 'OBJECT' and [o.name for o in bpy.context.selected_objects] == ["pCube1"]
    tree.select_row(bpy.context, rows, rows.index(_row(rows, "pCylinder1")), 'TOGGLE')
    assert {o.name for o in bpy.context.selected_objects} == {"pCube1", "pCylinder1"}
    tree.deselect_all(bpy.context)
    assert not bpy.context.selected_objects


def _picked(sk):
    if sk.mode == 'EDIT':
        return {eb.name for eb in sk.data.edit_bones if eb.select_head and not (eb.parent and eb.parent.select
                                                                                 and eb.parent.select_head)}
    return {pb.name for pb in sk.pose.bones if pb.select}


def test_disabled_tree_draws_nothing():
    tree.ENABLED = False
    area, sp = _outliner()
    assert not tree.wants_tree(sp) and not tree.is_tree(sp)


def test_tree_picks_set_the_lead():
    """#338: the last row picked in the tree is the lead (Match Transformations, Channel Box, selection wire)."""
    _on()
    _clear()
    a, b, c = _mesh("pA1"), _mesh("pB1"), _mesh("pC1")
    pick_order = import_module(kit.MODULE + ".operators.pick_order")
    rows = _rows()
    i = {r.label: k for k, r in enumerate(rows)}
    tree.select_row(bpy.context, rows, i["pA1"], 'REPLACE')
    tree.select_row(bpy.context, rows, i["pB1"], 'TOGGLE')
    assert [o.name for o in pick_order.ordered(bpy.context)] == ["pA1", "pB1"]
    assert pick_order.last(bpy.context) == b and bpy.context.view_layer.objects.active == b, "Ctrl-pick B: B leads"
    tree.select_row(bpy.context, rows, i["pA1"], 'TOGGLE')
    tree.select_row(bpy.context, rows, i["pA1"], 'TOGGLE')
    assert pick_order.last(bpy.context) == a, "A picked again last: A leads"
    tree.select_row(bpy.context, rows, i["pC1"], 'REPLACE')
    tree.select_row(bpy.context, rows, i["pA1"], 'RANGE', anchor=tree.active_row(bpy.context, rows))
    assert pick_order.last(bpy.context) == a and {o.name for o in bpy.context.selected_objects} == {"pA1", "pB1", "pC1"}
