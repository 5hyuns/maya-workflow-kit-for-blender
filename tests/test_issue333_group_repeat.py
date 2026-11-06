"""#333: G is Repeat Last and Ctrl+G is Group, like Maya. G after Ctrl+G groups again (the new group goes under
the next one), G after Edit > Group does the same, and a selection made in between is not the command G repeats."""

from importlib import import_module

import bpy

import kit

rep = import_module(kit.MODULE + ".operators.repeat_maya")
modal = import_module(kit.MODULE + ".marking.modal")
menu_map = import_module(kit.MODULE + ".ui.menu_map")


def _items(km, key, **mods):
    kc = kit.maya_kc()
    want = {m: mods.get(m, False) for m in ("shift", "ctrl", "alt")}
    return [k for k in kc.keymaps[km].keymap_items if k.active and k.type == key and k.value == 'PRESS'
            and all(getattr(k, m) == v for m, v in want.items())]


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    rep.HISTORY.clear()


def _cube(name):
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    ob.name = name
    return ob


def _select(*obs):
    for ob in bpy.context.scene.objects:
        ob.select_set(ob in obs)
    bpy.context.view_layer.objects.active = obs[-1] if obs else None


def _groups():
    return sorted(o.name for o in bpy.context.scene.objects if o.type == 'EMPTY' and o.name.startswith("group"))


def test_g_keys_follow_maya():
    assert [k.idname for k in _items("Screen", "G")] == ["allset.repeat_last"]
    for km in ("Object Mode", "Outliner"):
        assert "allset.group" in [k.idname for k in _items(km, "G", ctrl=True)], km
    assert [k.idname for k in _items("3D View", "G", shift=True)] == ["allset.repeat_at_mouse"]
    # over the Graph Editor and the Dope Sheet, G frames the playback range (Maya); Repeat Last is the viewport's G
    assert [k.idname for k in _items("Graph Editor", "G")] == ["anim.scene_range_frame"]
    assert [k.idname for k in _items("Dopesheet", "G")] == ["allset.dope_sheet_key"]


def test_g_after_ctrl_g_groups_again():
    _clear()
    cube = _cube("pCube1")
    _select(cube)
    # Ctrl+G: a key command, registered like any operator run from a key
    assert bpy.ops.allset.group('EXEC_DEFAULT', True) == {'FINISHED'}
    g1 = bpy.context.active_object
    assert g1.name == "group1" and cube.parent == g1, _groups()
    what = rep.last(bpy.context)
    assert what[0] == "blender", what
    assert bpy.context.window_manager.operators[what[1]].bl_idname == "ALLSET_OT_group"
    assert rep.label(bpy.context) == 'Repeat "Group"'
    assert bpy.ops.allset.repeat_last() == {'FINISHED'}
    g2 = bpy.context.active_object
    assert g2.name == "group2" and g1.parent == g2 and cube.parent == g1, _groups()
    # and again
    assert bpy.ops.allset.repeat_last() == {'FINISHED'}
    assert _groups() == ["group1", "group2", "group3"] and g2.parent.name == "group3"


def test_g_after_edit_group_menu():
    _clear()
    cube = _cube("pCube1")
    _select(cube)
    assert modal.run_action(bpy.context, menu_map.MAP["Edit/Group"], path="Edit/Group") == {'FINISHED'}
    assert cube.parent is not None and cube.parent.name == "group1"
    assert rep.label(bpy.context) == 'Repeat "Group"'
    assert bpy.ops.allset.repeat_last() == {'FINISHED'}
    assert bpy.data.objects["group1"].parent == bpy.data.objects["group2"], _groups()


def test_selecting_in_between_is_not_the_last_command():
    _clear()
    a, b = _cube("pCube1"), _cube("pCube2")
    _select(a)
    assert bpy.ops.allset.group('EXEC_DEFAULT', True) == {'FINISHED'}
    # pick the other cube: a registered selection operator plus a click-style selection
    bpy.ops.object.select_all('EXEC_DEFAULT', True, action='DESELECT')
    _select(b)
    assert rep.label(bpy.context) == 'Repeat "Group"'
    assert bpy.ops.allset.repeat_last() == {'FINISHED'}
    assert b.parent is not None and b.parent.name == "group2", _groups()
    assert a.parent.name == "group1"
