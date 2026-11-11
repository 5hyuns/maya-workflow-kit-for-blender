"""Maya object sets — Create > Sets > Set / Quick Select Set, members, select, add / remove, delete, rename,
save / reload, the Outliner tree's SET rows, menu mapping."""

import os
import tempfile
from importlib import import_module

import bpy

import kit

sets = import_module(kit.MODULE + ".operators.sets")
tree = import_module(kit.MODULE + ".ui.outliner_tree")
tree_edit = import_module(kit.MODULE + ".ui.outliner_tree_edit")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
notices = import_module(kit.MODULE + ".ui.notices")


def _scene(n=3):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for c in list(bpy.data.collections):
        if sets.is_set(c):
            bpy.data.collections.remove(c)
    obs = []
    for i in range(n):
        me = bpy.data.meshes.new(f"pCubeShape{i + 1}")
        ob = bpy.data.objects.new(f"pCube{i + 1}", me)
        bpy.context.scene.collection.objects.link(ob)
        obs.append(ob)
    _select(obs[:2])
    return obs


def _select(obs):
    for o in bpy.context.scene.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = obs[-1] if obs else None


def _selected():
    return {o.name for o in bpy.context.selected_objects}


def test_create_set_like_maya():
    a, b, c = _scene()
    assert bpy.ops.allset.create_set() == {'FINISHED'}
    s1 = bpy.data.collections["set1"]
    assert sets.is_set(s1) and {o.name for o in s1.objects} == {"pCube1", "pCube2"}
    assert _selected() == {"pCube1", "pCube2"}, "Maya keeps the selection"
    assert s1.use_fake_user and not any(s1 in sc.collection.children_recursive for sc in bpy.data.scenes)
    assert a.users_collection and bpy.context.scene.collection in a.users_collection, "object stays in the scene"
    _select([a])
    bpy.ops.allset.create_set()
    _select([])
    bpy.ops.allset.create_set()
    assert [s.name for s in sets.all_sets()] == ["set1", "set2", "set3"], "names and creation order (S2)"
    assert len(bpy.data.collections["set3"].objects) == 0, "nothing selected = empty set"
    sets.delete(bpy.data.collections["set1"])
    assert sets.next_name() == "set4", "one past the highest, no gap filling"
    bpy.ops.allset.create_set(name="propSet")
    assert sets.all_sets()[-1].name == "propSet"


def test_select_members_modes():
    a, b, c = _scene()
    coll = sets.create("", [a, b])
    _select([c])
    bpy.ops.allset.select_set_members(name=coll.name)
    assert _selected() == {"pCube1", "pCube2"}, "select <set> = members (S4)"
    assert bpy.context.view_layer.objects.active in (a, b)
    _select([c])
    bpy.ops.allset.select_set_members(name=coll.name, mode='ADD')
    assert _selected() == {"pCube1", "pCube2", "pCube3"}
    _select([a, c])
    bpy.ops.allset.select_set_members(name=coll.name, mode='TOGGLE')
    assert _selected() == {"pCube2", "pCube3"}
    # a member outside the view layer is skipped
    bpy.context.scene.collection.objects.unlink(b)
    _select([c])
    sets.select_members(bpy.context, coll)
    assert _selected() == {"pCube1"}


def test_edit_add_remove_rename_delete():
    a, b, c = _scene()
    coll = sets.create("", [a])
    _select([b, c])
    bpy.ops.allset.set_edit(name=coll.name, action='ADD')
    assert {o.name for o in coll.objects} == {"pCube1", "pCube2", "pCube3"}
    _select([c])
    bpy.ops.allset.set_edit(name=coll.name, action='REMOVE')
    assert {o.name for o in coll.objects} == {"pCube1", "pCube2"}
    bpy.ops.allset.set_edit(name=coll.name, member="pCube1", action='REMOVE_MEMBER')
    assert {o.name for o in coll.objects} == {"pCube2"}
    bpy.ops.allset.set_edit(name=coll.name, action='EXPAND')
    assert coll.allset_expanded
    bpy.ops.allset.set_edit('EXEC_DEFAULT', name=coll.name, action='RENAME', new_name="hero")
    assert sets.get("hero") is coll
    bpy.data.objects.remove(b)
    assert len(coll.objects) == 0, "deleting a member removes it from the set (S5)"
    bpy.ops.allset.set_edit(name="hero", action='DELETE')
    assert sets.get("hero") is None and "pCube1" in bpy.data.objects


def test_quick_select_set_and_menu():
    a, b, c = _scene()
    bpy.ops.allset.create_quick_select_set('EXEC_DEFAULT', name="mySel")
    q = sets.get("mySel")
    assert q is not None and q.get(sets.TEXT) == sets.QUICK and {o.name for o in q.objects} == {"pCube1", "pCube2"}
    sets.create("", [c])
    assert [s.name for s in sets.quick_sets()] == ["mySel"], "only text gCharacterSet sets in the menu (S7)"
    assert menu_map.MAP["Select/Quick Select Sets"] == ("menu", "ALLSET_MT_quick_select_sets")
    assert hasattr(bpy.types, "ALLSET_MT_quick_select_sets")


def test_menu_mapping():
    assert menu_map.MAP["Create/Sets/Set"] == "allset.create_set"
    assert menu_map.MAP["Create/Sets/Quick Select Set..."] == "allset.create_quick_select_set"
    assert "Create/Sets/Quick Select Set..." not in notices.NOTICES and "Select/Quick Select Sets" not in notices.NOTICES
    assert "Create/Sets/Partition" in notices.NOTICES
    assert "option_box" in bpy.ops.allset.create_set.get_rna_type().properties


def test_save_and_reload_keeps_sets():
    a, b, c = _scene()
    s1 = sets.create("", [a, b])
    q = sets.create("quick1", [c], text=sets.QUICK)
    s1.allset_expanded = True
    path = os.path.join(tempfile.mkdtemp(), "sets96.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    bpy.ops.wm.read_homefile(use_empty=True)
    assert not sets.all_sets()
    bpy.ops.wm.open_mainfile(filepath=path)
    got = sets.all_sets()
    assert [s.name for s in got] == ["set1", "quick1"]
    assert {o.name for o in got[0].objects} == {"pCube1", "pCube2"} and got[0].allset_expanded
    assert got[1].get(sets.TEXT) == sets.QUICK
    assert all(o.name in bpy.context.scene.objects for o in got[0].objects)


def test_outliner_set_rows():
    a, b, c = _scene()
    coll = sets.create("", [a, b])
    bpy.context.view_layer.update()
    head = tree.build(bpy.context.scene, bpy.context.view_layer, tree.default_options())
    rows = head + tree.tail_rows(bpy.context.scene, tree.default_options())
    kinds = [(r.kind, r.label) for r in rows]
    assert kinds[-1] == ('SET', "set1") and kinds[-3:-1] == [('DEFAULT_SET', "defaultLightSet"),
                                                          ('DEFAULT_SET', "defaultObjectSet")], kinds
    assert all(k in ('CAMERA', 'OBJECT') for k, _n in kinds[:-3]), "sets after the DAG rows"
    _select([c])
    tree.select_row(bpy.context, rows, len(rows) - 1, 'REPLACE')
    assert _selected() == {"pCube1", "pCube2"}
    assert tree_edit.rename(('SET', "set1", ""), "renamed") == "renamed"
    assert sets.get("renamed") is coll


def test_set_rows_expand():
    a, b, c = _scene()
    s1 = sets.create("", [a, b])
    sets.create("", [])
    opts = tree.default_options()
    assert [(r.kind, r.label) for r in tree.tail_rows(bpy.context.scene, opts)][2:] == [('SET', "set1"),
                                                                                       ('SET', "set2")]
    tree.set_expanded([('S', "set1")], True)
    assert s1.allset_expanded
    assert [(r.kind, r.ob, r.sub) for r in tree.tail_rows(bpy.context.scene, opts)][2:] == [
        ('SET', "set1", ""), ('MEMBER', "pCube1", "set1"), ('MEMBER', "pCube2", "set1"), ('SET', "set2", "")]


def test_keymap_items_first_in_outliner():
    kc = kit.maya_kc()
    km = kc.keymaps.get("Outliner")
    if km is None:
        return
    ids = [it.idname for it in km.keymap_items]
    assert "allset.outliner_tree_click" in ids and "allset.outliner_tree_menu" in ids
    lmb = [it.idname for it in km.keymap_items if it.type == 'LEFTMOUSE' and it.value == 'PRESS']
    assert lmb[0] == "allset.outliner_tree_click", lmb
    rmb = [it.idname for it in km.keymap_items if it.type == 'RIGHTMOUSE']
    assert rmb[0] == "allset.outliner_tree_menu", rmb
