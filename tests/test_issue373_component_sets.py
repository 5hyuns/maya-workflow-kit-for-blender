"""Issue #373: Create > Sets > Set and Quick Select Set hold vertices, edges and faces like Maya (``pCube1.vtx[0:3]``,
``pCube1.e[0:2]``, ``pCube2.f[1]``), next to whole objects; selecting the set selects those components (Edit Mode in
the matching component mode); Add / Remove, save / reload, rename, a move of the points, the Outliner rows and the
command line ``sets`` keep them; object sets work as before."""

import os
import tempfile
from importlib import import_module

import bmesh
import bpy

import kit

sets = import_module(kit.MODULE + ".operators.sets")
tree = import_module(kit.MODULE + ".ui.outliner_tree")
cmds = import_module(kit.MODULE + ".command_line.cmds_shim")


def _object_mode():
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _scene():
    """pCube1 at the origin, pCube2 at x = 3 (8 vertices, 12 edges, 6 faces each), nothing selected."""
    _object_mode()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for c in list(bpy.data.collections):
        if sets.is_set(c) or c.get(sets.PARTS):
            bpy.data.collections.remove(c)
    obs = []
    for i in range(2):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.0 * i, 0.0, 0.0))
        ob = bpy.context.active_object
        ob.name, ob.data.name = f"pCube{i + 1}", f"pCubeShape{i + 1}"
        obs.append(ob)
    _select([])
    return obs


def _select(obs):
    for o in bpy.context.scene.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = obs[-1] if obs else None


def _edit(obs, mode, picks):
    """Edit Mode on ``obs`` in component ``mode`` ('VERT' / 'EDGE' / 'FACE') with ``picks`` ({object: indices})
    selected."""
    _object_mode()
    _select(obs)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (mode == 'VERT', mode == 'EDGE', mode == 'FACE')
    for ob in obs:
        bm = bmesh.from_edit_mesh(ob.data)
        bm.select_mode = {mode}
        for seq in (bm.faces, bm.edges, bm.verts):
            for e in seq:
                e.select_set(False)
        seq = {'VERT': bm.verts, 'EDGE': bm.edges, 'FACE': bm.faces}[mode]
        seq.ensure_lookup_table()
        for i in picks.get(ob, ()):
            seq[i].select_set(True)
        bm.select_flush_mode()
        bmesh.update_edit_mesh(ob.data)


def _picked(ob):
    """{'v': selected vertex ids, 'e': edge ids, 'f': face ids} of ``ob`` in Edit Mode."""
    bm = bmesh.from_edit_mesh(ob.data)
    return {"v": {v.index for v in bm.verts if v.select}, "e": {e.index for e in bm.edges if e.select},
            "f": {f.index for f in bm.faces if f.select}}


def _editing():
    return {o.name for o in bpy.context.objects_in_mode} if bpy.context.mode == 'EDIT_MESH' else set()


def _selected():
    return {o.name for o in bpy.context.selected_objects}


def _members(coll):
    return [o.name for o in sets.members(coll)] + [n for o in sets.part_objects(coll)
                                                   for n in sets.component_names(coll, o)]


def test_create_set_from_vertices_edges_faces():
    a, b = _scene()
    _edit([a], 'VERT', {a: [0, 1, 2, 3]})
    assert bpy.ops.allset.create_set() == {'FINISHED'}
    s1 = sets.get("set1")
    assert _members(s1) == ["pCube1.vtx[0:3]"], _members(s1)
    assert not sets.members(s1), "the mesh itself is not a member"
    assert bpy.context.mode == 'EDIT_MESH' and _picked(a)["v"] == {0, 1, 2, 3}, "Maya keeps the selection"
    _edit([a], 'EDGE', {a: [0, 1, 2]})
    bpy.ops.allset.create_set()
    assert _members(sets.get("set2")) == ["pCube1.e[0:2]"]
    _edit([b], 'FACE', {b: [1, 3]})
    bpy.ops.allset.create_set()
    assert _members(sets.get("set3")) == ["pCube2.f[1]", "pCube2.f[3]"], "one name per run of indices, like Maya"
    # both meshes in Edit Mode: each one's components
    _edit([a, b], 'VERT', {a: [7], b: [5, 6]})
    bpy.ops.allset.create_set()
    assert sorted(_members(sets.get("set4"))) == ["pCube1.vtx[7]", "pCube2.vtx[5:6]"], _members(sets.get("set4"))
    # nothing picked in Edit Mode: an empty set
    _edit([a], 'VERT', {})
    bpy.ops.allset.create_set()
    assert _members(sets.get("set5")) == []


def test_select_component_set():
    a, b = _scene()
    _edit([a], 'VERT', {a: [0, 1, 2, 3]})
    v_set = sets.create("vset", parts=sets.gather(bpy.context)[1])
    _edit([a], 'EDGE', {a: [4, 5]})
    e_set = sets.create("eset", parts=sets.gather(bpy.context)[1])
    _edit([b], 'FACE', {b: [1, 3]})
    f_set = sets.create("fset", parts=sets.gather(bpy.context)[1])
    _object_mode()
    _select([])
    bpy.ops.allset.select_set_members(name=v_set.name)
    assert bpy.context.mode == 'EDIT_MESH' and _editing() == {"pCube1"}
    assert tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (True, False, False), "vertex mode"
    assert _picked(a)["v"] == {0, 1, 2, 3}
    # from Edit Mode on another mesh: replaced (that mesh leaves Edit Mode)
    bpy.ops.allset.select_set_members(name=f_set.name)
    assert _editing() == {"pCube2"} and tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, False, True)
    assert _picked(b)["f"] == {1, 3}
    bpy.ops.allset.select_set_members(name=e_set.name)
    assert _editing() == {"pCube1"} and tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, True, False)
    assert _picked(a)["e"] == {4, 5}, "the old vertex picks of pCube1 are gone"
    # Add keeps what is picked (components of the other mesh too)
    bpy.ops.allset.select_set_members(name=f_set.name, mode='ADD')
    assert _editing() == {"pCube1", "pCube2"}
    assert _picked(a)["e"] == {4, 5} and _picked(b)["f"] == {1, 3}
    # Toggle takes picked members out
    bpy.ops.allset.select_set_members(name=f_set.name, mode='TOGGLE')
    assert not _picked(b)["f"] and _picked(a)["e"] == {4, 5}
    # Quick Select Sets: the same select
    _edit([b], 'VERT', {b: [4, 5]})
    bpy.ops.allset.create_quick_select_set('EXEC_DEFAULT', name="qs")
    q = sets.get("qs")
    assert q.get(sets.TEXT) == sets.QUICK and _members(q) == ["pCube2.vtx[4:5]"]
    _object_mode()
    _select([a])
    bpy.ops.allset.select_set_members(name="qs")
    assert _editing() == {"pCube2"} and _picked(b)["v"] == {4, 5} and "pCube1" not in _selected()


def test_mixed_objects_and_components():
    a, b = _scene()
    _edit([a], 'FACE', {a: [0]})
    b.select_set(True)                       # pCube2 picked as an object next to pCube1's face
    bpy.ops.allset.create_set()
    s1 = sets.get("set1")
    assert _members(s1) == ["pCube2", "pCube1.f[0]"], _members(s1)
    assert cmds.sets("set1", q=True) == ["pCube2", "pCube1.f[0]"], "sets -q lists objects and components"
    _object_mode()
    _select([])
    bpy.ops.allset.select_set_members(name="set1")
    assert _editing() == {"pCube1"} and _picked(a)["f"] == {0}
    assert _selected() == {"pCube1", "pCube2"}, "the whole member is picked too (outside Edit Mode)"
    assert b.mode == 'OBJECT'
    bpy.ops.allset.select_set_members(name="set1", mode='TOGGLE')
    assert not _picked(a)["f"] and not b.select_get(), "Toggle takes both kinds of member out"


def test_add_remove_components_and_delete():
    a, b = _scene()
    _edit([a], 'VERT', {a: [0, 1, 2, 3]})
    bpy.ops.allset.create_set()
    s1 = sets.get("set1")
    _edit([a], 'VERT', {a: [6]})
    bpy.ops.allset.set_edit(name="set1", action='ADD')
    assert _members(s1) == ["pCube1.vtx[0:3]", "pCube1.vtx[6]"]
    _edit([a], 'VERT', {a: [1]})
    bpy.ops.allset.set_edit(name="set1", action='REMOVE')
    assert _members(s1) == ["pCube1.vtx[0]", "pCube1.vtx[2:3]", "pCube1.vtx[6]"]
    _object_mode()
    _select([b])
    bpy.ops.allset.set_edit(name="set1", action='ADD')
    assert _members(s1) == ["pCube2", "pCube1.vtx[0]", "pCube1.vtx[2:3]", "pCube1.vtx[6]"]
    bpy.ops.allset.set_edit(name="set1", member="pCube1", action='REMOVE_MEMBER')
    assert _members(s1) == ["pCube2"], "Remove From Current Set takes the mesh's components out"
    assert not [at.name for at in a.data.attributes if at.name.startswith(".allset_set_")], "no attribute left"
    _edit([a], 'EDGE', {a: [3]})
    bpy.ops.allset.create_set()
    s2 = sets.get("set2")
    assert [at.name for at in a.data.attributes if at.name.startswith(".allset_set_")]
    bpy.ops.allset.set_edit(name="set2", action='DELETE')
    _object_mode()
    assert sets.get("set2") is None and "pCube1" in bpy.data.objects
    assert not [at.name for at in a.data.attributes if at.name.startswith(".allset_set_")], "Delete Set cleans up"
    assert not [c for c in bpy.data.collections if c.get(sets.PARTS) and not c.users]


def test_save_reload_rename_and_move():
    a, b = _scene()
    _edit([a], 'VERT', {a: [0, 1, 2, 3]})
    bpy.ops.allset.create_set()
    _edit([b], 'FACE', {b: [2]})
    bpy.ops.allset.create_quick_select_set('EXEC_DEFAULT', name="faces")
    _object_mode()
    path = os.path.join(tempfile.mkdtemp(), "sets373.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=path)
    assert _members(sets.get("set1")) == ["pCube1.vtx[0:3]"]
    assert _members(sets.get("faces")) == ["pCube2.f[2]"]
    a = bpy.data.objects["pCube1"]
    sets.get("set1").name = "corners"
    assert _members(sets.get("corners")) == ["pCube1.vtx[0:3]"], "a rename keeps the components"
    # moving points (same topology) keeps the members
    _edit([a], 'VERT', {a: [0, 5]})
    bm = bmesh.from_edit_mesh(a.data)
    bmesh.ops.translate(bm, vec=(0.0, 0.0, 0.5), verts=[v for v in bm.verts if v.select])
    bmesh.update_edit_mesh(a.data)
    _object_mode()
    assert _members(sets.get("corners")) == ["pCube1.vtx[0:3]"]
    _select([])
    bpy.ops.allset.select_set_members(name="corners")
    assert _picked(a)["v"] == {0, 1, 2, 3}


def test_outliner_component_rows():
    a, b = _scene()
    _edit([a], 'VERT', {a: [0, 1, 2, 3]})
    bpy.ops.allset.create_set()
    _object_mode()
    s1 = sets.get("set1")
    opts = tree.default_options()
    rows = tree.tail_rows(bpy.context.scene, opts)
    row = next(r for r in rows if r.kind == 'SET' and r.ob == "set1")
    assert row.kids, "the set row has members to show"
    s1.allset_expanded = True
    rows = tree.tail_rows(bpy.context.scene, opts)
    got = [(r.kind, r.ob, r.label) for r in rows if r.kind in ('SET', 'MEMBER')]
    assert got == [('SET', "set1", "set1"), ('MEMBER', "pCube1", "pCube1.vtx[0:3]")], got
    _select([b])
    tree.select_row(bpy.context, rows, len(rows) - 1, 'REPLACE')
    assert _editing() == {"pCube1"} and _picked(a)["v"] == {0, 1, 2, 3}, "the row picks its components"
    _object_mode()
    _select([b])
    tree.select_row(bpy.context, rows, len(rows) - 2, 'REPLACE')
    assert _editing() == {"pCube1"} and _picked(a)["v"] == {0, 1, 2, 3}, "the set row picks them too"


def test_object_sets_unchanged():
    a, b = _scene()
    _select([a, b])
    bpy.ops.allset.create_set()
    s1 = sets.get("set1")
    assert _members(s1) == ["pCube1", "pCube2"] and not sets.part_objects(s1)
    _select([])
    bpy.ops.allset.select_set_members(name="set1")
    assert bpy.context.mode == 'OBJECT' and _selected() == {"pCube1", "pCube2"}
    # from Edit Mode an object set leaves Edit Mode, as before
    _edit([a], 'VERT', {a: [0]})
    bpy.ops.allset.select_set_members(name="set1")
    assert bpy.context.mode == 'OBJECT' and _selected() == {"pCube1", "pCube2"}
