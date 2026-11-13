"""#348: editing in the kit-drawn Maya Outliner tree — rename with the Channel Box name rules (joints, shapes, sets),
reveal (rows above the selection open), middle-mouse drops (objects onto a joint, joints onto a joint of their
skeleton, a root joint = the skeleton, between rows, to the world), Hide In Outliner, the dim highlight of rows
with a selected node below them, the visibility column and Delete. GUI: tests/gui/gui_outliner_tree.py."""

from importlib import import_module

import bpy
from mathutils import Vector

import kit

tree = import_module(kit.MODULE + ".ui.outliner_tree")
edit = import_module(kit.MODULE + ".ui.outliner_tree_edit")
joints = import_module(kit.MODULE + ".operators.joints")
sets = import_module(kit.MODULE + ".operators.sets")
order = import_module(kit.MODULE + ".ui.outliner_order")


def _clear():
    tree.ENABLED = True
    tree.EXPANDED.clear()
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for data in (bpy.data.armatures, bpy.data.meshes):
        for d in list(data):
            data.remove(d)
    for c in list(bpy.data.collections):
        if sets.is_set(c):
            bpy.data.collections.remove(c)


def _mesh(name, parent=None, location=(0, 0, 0)):
    base = name.rstrip("0123456789")
    ob = bpy.data.objects.new(name, bpy.data.meshes.new(base + "Shape" + name[len(base):]))
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    if parent is not None:
        ob.parent = parent
    order.number_new(list(bpy.context.scene.objects))
    bpy.context.view_layer.update()
    return ob


def _rig():
    _clear()
    cube = _mesh("pCube1", location=(4, 0, 0))
    ob = joints.new_skeleton(bpy.context)
    names = []
    for parent, p in ((None, (0, 0, 0)), (0, (0, 0, 1)), (1, (0, 0, 2)), (0, (1, 0, 1))):
        names.append(joints.add_joint(ob, Vector(p), names[parent] if parent is not None else None, length=0.5))
    bpy.ops.object.mode_set(mode='OBJECT')
    order.number_new(list(bpy.context.scene.objects))
    bpy.context.view_layer.update()
    return cube, ob, names


def _rows(**kw):
    bpy.context.view_layer.update()
    return tree.build(bpy.context.scene, bpy.context.view_layer, tree.default_options(**kw)) + \
        tree.tail_rows(bpy.context.scene, tree.default_options(**kw))


def _row(rows, label, kind=None):
    return next(r for r in rows if r.label == label and (kind is None or r.kind == kind))


def _select(*obs):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.view_layer.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = obs[-1] if obs else None


def test_rename_rows_with_maya_names():
    cube, sk, names = _rig()
    assert edit.rename(('OBJECT', "pCube1", ""), "box") == "box"
    assert cube.name == "box" and cube.data.name == "boxShape", (cube.name, cube.data.name)
    assert edit.rename(('OBJECT', "box", ""), "my box") == "my_box", "spaces become _ (Maya)"
    assert edit.rename(('OBJECT', "my_box", ""), "1bad") is None and cube.name == "my_box"
    tree.EXPANDED.add(('B', sk.session_uid, names[1]))
    assert edit.rename(('JOINT', sk.name, names[1]), "spine") == "spine"
    assert "spine" in sk.data.bones and ('B', sk.session_uid, "spine") in tree.EXPANDED, \
        "a renamed joint keeps its open row"
    assert edit.rename(('SHAPE', "my_box", "boxShape"), "boxGeo") == "boxGeo" and cube.data.name == "boxGeo"
    coll = sets.create("set1", [cube])
    assert edit.rename(('SET', "set1", ""), "props") == "props" and coll.name == "props"
    assert edit.rename_target(('CAMERA', "persp", "")) is None, "drawn rows have nothing to rename"


def test_reveal_opens_the_rows_above():
    cube, sk, names = _rig()
    j1, j2, j3, j4 = names
    cyl = _mesh("pCylinder1", sk)
    cyl.parent_type, cyl.parent_bone = 'BONE', j3
    keys = edit.ancestor_keys(cyl)
    assert keys == [('B', sk.session_uid, j3), ('B', sk.session_uid, j2), ('B', sk.session_uid, j1)], keys
    assert edit.ancestor_keys(sk, j3) == [('B', sk.session_uid, j2), ('B', sk.session_uid, j1)]
    tree.set_expanded(keys, True)
    rows = [r for r in _rows() if r.kind not in ('CAMERA', 'DEFAULT_SET')]
    assert [(r.label, r.depth) for r in rows] == [("pCube1", 0), (j1, 0), (j2, 1), (j3, 2), ("pCylinder1", 3),
                                                  (j4, 1)], [(r.label, r.depth) for r in rows]


def test_dim_highlight_above_the_selection():
    cube, sk, names = _rig()
    j1, j2, j3, j4 = names
    _select(sk)
    bpy.ops.object.mode_set(mode='POSE')
    for pb in sk.pose.bones:
        pb.select = pb.name == j3
    sk.data.bones.active = sk.data.bones[j3]
    above = tree.selected_ancestors(bpy.context)
    assert above == {('B', sk.session_uid, j2), ('B', sk.session_uid, j1)}, above
    bpy.ops.object.mode_set(mode='OBJECT')


def test_drop_object_onto_a_joint_keeps_it_in_place():
    cube, sk, names = _rig()
    j1, j2, j3, j4 = names
    world = cube.matrix_world.copy()
    rows = _rows()
    tree.set_expanded([('B', sk.session_uid, j1)], True)
    rows = _rows()
    changed, msg = edit.drop(bpy.context, [('OBJECT', "pCube1", "")], _row(rows, j2), 'ON')
    bpy.context.view_layer.update()
    assert changed == 1 and not msg, (changed, msg)
    assert cube.parent == sk and cube.parent_type == 'BONE' and cube.parent_bone == j2
    assert (cube.matrix_world.translation - world.translation).length < 1e-4, (cube.matrix_world, world)
    tree.set_expanded([('B', sk.session_uid, j2)], True)
    rows = _rows()
    assert [(r.label, r.depth) for r in rows if r.label in (j2, j3, "pCube1")] == [(j2, 1), (j3, 2), ("pCube1", 2)]
    # to the world (empty space)
    changed, _m = edit.drop(bpy.context, [('OBJECT', "pCube1", "")], None, 'ON')
    bpy.context.view_layer.update()
    assert changed == 1 and cube.parent is None
    assert (cube.matrix_world.translation - world.translation).length < 1e-4


def test_drop_joints_within_their_skeleton():
    cube, sk, names = _rig()
    j1, j2, j3, j4 = names
    rows = [r for r in _rows(children=False)]
    changed, msg = edit.drop(bpy.context, [('JOINT', sk.name, j4)], _row(rows, j3), 'ON')
    assert changed == 1 and not msg, (changed, msg)
    assert sk.data.bones[j4].parent.name == j3
    changed, msg = edit.drop(bpy.context, [('JOINT', sk.name, j4)], None, 'ON')
    assert changed == 1 and sk.data.bones[j4].parent is None, "to the world = a root joint"
    rows = [r for r in _rows() if r.kind == 'JOINT' and r.depth == 0]
    assert [r.label for r in rows] == [j1, j4], [r.label for r in rows]
    assert sk.mode == 'OBJECT'


def test_root_joint_dropped_on_an_object_moves_the_skeleton():
    cube, sk, names = _rig()
    rows = _rows()
    changed, msg = edit.drop(bpy.context, [('JOINT', sk.name, names[0])], _row(rows, "pCube1"), 'ON')
    assert changed == 1 and sk.parent == cube, (changed, msg, sk.parent)
    rows = _rows()
    assert not any(r.label == names[0] and r.depth == 0 for r in rows), "the skeleton went under pCube1"
    changed, msg = edit.drop(bpy.context, [('JOINT', sk.name, names[2])], _row(rows, "pCube1"), 'ON')
    assert msg, "a joint inside a chain can't go under an object"


def test_hide_in_outliner_and_eye_column():
    cube, sk, names = _rig()
    _select(cube)
    assert bpy.ops.allset.outliner_tree_hide(hide=True) == {'FINISHED'}
    assert not any(r.label == "pCube1" for r in _rows())
    assert bpy.ops.allset.outliner_tree_hide(hide=False) == {'FINISHED'}
    assert any(r.label == "pCube1" for r in _rows())
    rows = _rows()
    row = _row(rows, "pCube1")
    assert edit.eye_state(row) is True
    assert edit.toggle_eye(bpy.context, row) and cube.hide_viewport and edit.eye_state(row) is False
    edit.toggle_eye(bpy.context, row)
    assert not cube.hide_viewport
    root = _row(rows, names[0])
    assert edit.eye_state(root) is True
    edit.toggle_eye(bpy.context, root)
    assert sk.pose.bones[names[0]].hide and edit.eye_state(root) is False
    assert all(sk.pose.bones[n].hide for n in names), "the joints below go with it (Maya)"
    edit.toggle_eye(bpy.context, root)
    assert not any(sk.pose.bones[n].hide for n in names)
    assert edit.eye_state(_row(rows, "persp")) is None


def test_select_and_render_columns():
    cube, sk, names = _rig()
    rows = _rows()
    row, root = _row(rows, "pCube1"), _row(rows, names[0])
    for col, prop in (('SELECT', "hide_select"), ('RENDER', "hide_render")):
        assert tree.column_state(row, col) is True
        assert edit.toggle_column(bpy.context, row, col) and getattr(cube, prop)
        assert tree.column_state(row, col) is False
        edit.toggle_column(bpy.context, row, col)
        assert not getattr(cube, prop)
    assert tree.column_state(root, 'SELECT') is True
    assert edit.toggle_column(bpy.context, root, 'SELECT') and sk.data.bones[names[0]].hide_select
    assert tree.column_state(root, 'SELECT') is False
    edit.toggle_column(bpy.context, root, 'SELECT')
    assert tree.column_state(root, 'RENDER') is None, "a joint has no render column"
    assert not edit.toggle_column(bpy.context, root, 'RENDER')
    assert tree.column_state(_row(rows, "persp"), 'SELECT') is None
    shape = tree.Row('SHAPE', "pCube1", cube.data.name, 1, False, False, cube.data.name, 'SHAPE', None)
    assert tree.column_state(shape, 'RENDER') is None
    icons = import_module(kit.MODULE + ".ui.blender_restrict_icons").CELLS
    heights = {k[0] for k in icons}
    assert 20 in heights and len(icons) == 6 * len(heights), "Blender's 3 icons x on/off at every captured height"


def test_delete_objects_and_joints():
    cube, sk, names = _rig()
    child = _mesh("pSphere1", cube)
    _select(cube)
    assert edit.delete_selected(bpy.context) == 1
    assert "pCube1" not in bpy.data.objects and "pSphere1" not in bpy.data.objects, "Maya Delete takes the children"
    on3 = _mesh("pCone1", sk)
    on3.parent_type, on3.parent_bone = 'BONE', names[2]
    _select(sk)
    bpy.ops.object.mode_set(mode='POSE')
    for pb in sk.pose.bones:
        pb.select = pb.name == names[1]
    sk.data.bones.active = sk.data.bones[names[1]]
    assert edit.delete_selected(bpy.context) == 2, "joint2 and joint3 below it"
    assert sorted(b.name for b in sk.data.bones) == sorted([names[0], names[3]])
    assert "pCone1" not in bpy.data.objects, "an object on a deleted joint goes with it (Maya)"
    assert sk.mode == 'POSE'
    bpy.ops.object.mode_set(mode='OBJECT')


def test_drop_between_rows_reorders():
    _clear()
    a, b = _mesh("pCube1"), _mesh("pSphere1")
    rows = _rows()
    assert [r.label for r in rows if r.kind == 'OBJECT'] == ["pCube1", "pSphere1"]
    sp = _outliner_space()
    saved = sp.use_sort_alpha
    sp.use_sort_alpha = False                 # Maya order (a factory Outliner sorts by name)
    try:
        tree._cache.clear()
        before = tree.rows_for(bpy.context, sp)
        changed, _m = edit.drop(bpy.context, [('OBJECT', "pSphere1", "")], _row(rows, "pCube1"), 'BEFORE')
        assert changed, "placed"
        rows = _rows()
        assert [r.label for r in rows if r.kind == 'OBJECT'] == ["pSphere1", "pCube1"], [r.label for r in rows]
        after = tree.rows_for(bpy.context, sp)
        assert [r.label for r in after if r.kind == 'OBJECT'] == ["pSphere1", "pCube1"], \
            "the cached rows follow the new order (an ID property write tags nothing)"
        assert [r.label for r in before if r.kind == 'OBJECT'] == ["pCube1", "pSphere1"]
    finally:
        sp.use_sort_alpha = saved


def _outliner_space():
    area = next(a for a in bpy.data.screens["Layout"].areas if a.type == 'OUTLINER')
    return area.spaces.active


def test_drop_onto_a_set_adds_to_it():
    _clear()
    a, b = _mesh("pCube1"), _mesh("pSphere1")
    coll = sets.create("set1", [a])
    rows = _rows()
    changed, _m = edit.drop(bpy.context, [('OBJECT', "pSphere1", "")], _row(rows, "set1"), 'ON')
    assert changed == 1 and {o.name for o in coll.objects} == {"pCube1", "pSphere1"}, "Maya: dropped onto a set"
    assert b.parent is None
    assert edit.drop(bpy.context, [('OBJECT', "pSphere1", "")], _row(rows, "defaultLightSet"), 'ON')[0] == 0


def test_a_hidden_row_picked_in_the_outliner_comes_back_with_h():
    _clear()
    a, b = _mesh("pA1"), _mesh("pA2")
    a.hide_viewport = True
    bpy.context.view_layer.update()
    rows = _rows()
    _select(b)
    tree.select_row(bpy.context, rows, rows.index(_row(rows, "pA1")), 'REPLACE')
    assert not bpy.context.selected_objects, "the visible selection is replaced"
    assert tree.row_state(bpy.context, _row(rows, "pA1"), set())[0], "the hidden row shows picked"
    assert bpy.context.view_layer.objects.active == a
    assert bpy.ops.allset.visibility(action='TOGGLE') == {'FINISHED'}
    assert not a.hide_viewport, "h on the hidden row picked in the Outliner shows it (Maya)"
    # a visible pick drops the hidden pick
    a.hide_viewport = True
    bpy.context.view_layer.update()
    tree.select_row(bpy.context, rows, rows.index(_row(rows, "pA1")), 'REPLACE')
    tree.select_row(bpy.context, rows, rows.index(_row(rows, "pA2")), 'REPLACE')
    assert not tree.row_state(bpy.context, _row(rows, "pA1"), set())[0]
    tree.select_row(bpy.context, rows, rows.index(_row(rows, "pA1")), 'TOGGLE')
    assert tree.row_state(bpy.context, _row(rows, "pA1"), set())[0] and b.select_get(), "Ctrl adds the hidden row"
    tree.deselect_all(bpy.context)
    assert not tree.row_state(bpy.context, _row(rows, "pA1"), set())[0] and not b.select_get()


def test_a_selection_locked_row_stays_picked():
    """A live surface (hide_select) can't be selected in Blender: its Outliner row is still picked, and Delete in
    the Outliner takes it (Maya deletes a picked node)."""
    _clear()
    a, b = _mesh("pLive1"), _mesh("pB1")
    a.hide_select = True
    bpy.context.view_layer.update()
    rows = _rows()
    tree.select_row(bpy.context, rows, rows.index(_row(rows, "pLive1")), 'REPLACE')
    assert not a.select_get() and tree.picked_unselectable(bpy.context) == [a]
    assert tree.row_state(bpy.context, _row(rows, "pLive1"), set())[0]
    tree.select_row(bpy.context, rows, rows.index(_row(rows, "pB1")), 'TOGGLE')
    assert b.select_get() and tree.picked_unselectable(bpy.context) == [a], "Ctrl adds, the locked pick stays"
    tree.select_row(bpy.context, rows, rows.index(_row(rows, "pB1")), 'REPLACE')
    assert tree.picked_unselectable(bpy.context) == [], "a plain click elsewhere drops it"
    tree.select_row(bpy.context, rows, rows.index(_row(rows, "pLive1")), 'REPLACE')
    assert edit.delete_selected(bpy.context) == 1 and "pLive1" not in bpy.data.objects
