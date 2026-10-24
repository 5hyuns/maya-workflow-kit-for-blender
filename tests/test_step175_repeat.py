"""Step 175: Maya G repeats menu / shelf / marking-menu commands too (operators/repeat_maya.py), Edit > Repeat label,
Recent Commands, one undo step per G. Maya rules: research/maya/re/repeat_175.md (GUI-measured)."""

from importlib import import_module

import bpy

import kit

modal = import_module(kit.MODULE + ".marking.modal")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
rep = import_module(kit.MODULE + ".operators.repeat_maya")
option_windows = import_module(kit.MODULE + ".operators.option_windows")

CUBE = "Create/Polygon Primitives/Cube"


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    rep.HISTORY.clear()


def _object_mode():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _meshes():
    return sorted(o.name for o in bpy.context.scene.objects if o.type == 'MESH')


def _select(*names):
    for o in bpy.context.scene.objects:
        o.select_set(o.name in names)
    bpy.context.view_layer.objects.active = bpy.data.objects[names[-1]] if names else None


def _menu(path):
    res = modal.run_action(bpy.context, menu_map.MAP[path], path=path)
    _object_mode()
    return res


def test_menu_command_is_what_g_repeats():
    """Maya: Create > Polygon Primitives > Cube from the menu, then G = the next cube (pCube2)."""
    _clear()
    assert _menu(CUBE) == {'FINISHED'}
    assert _meshes() == ["pCube1"]
    assert rep.last(bpy.context)[0] == "kit"
    assert bpy.ops.allset.repeat_last() == {'FINISHED'}
    _object_mode()
    assert _meshes() == ["pCube1", "pCube2"], _meshes()
    assert rep.label(bpy.context) == 'Repeat "Cube"'


def test_combine_then_g_combines_the_new_selection():
    _clear()
    for _ in range(4):
        _menu(CUBE)
    _select("pCube1", "pCube2")
    assert _menu("Mesh/Combine") == {'FINISHED'}
    first = _meshes()
    assert len(first) == 3, first
    _select("pCube3", "pCube4")
    assert bpy.ops.allset.repeat_last() == {'FINISHED'}
    assert len(_meshes()) == 2, _meshes()                 # the second pair combined too
    assert rep.label(bpy.context) == 'Repeat "Combine"'


def test_key_operator_after_a_menu_command_wins_selection_does_not():
    """A registered (key) operator after the menu command is newer (Ctrl+E / Ctrl+D style); selecting is not."""
    _clear()
    _menu(CUBE)
    bpy.ops.object.select_all('EXEC_DEFAULT', True, action='DESELECT')   # registered, but Maya doesn't repeat it
    assert rep.last(bpy.context)[0] == "kit"
    bpy.ops.mesh.primitive_uv_sphere_add('EXEC_DEFAULT', True)           # a key command: registered
    what = rep.last(bpy.context)
    assert what[0] == "blender", what
    n = len(_meshes())
    assert bpy.ops.allset.repeat_last() == {'FINISHED'}
    assert len(_meshes()) == n + 1 and sum(o.name.startswith("Sphere") for o in bpy.context.scene.objects) == 2
    # the next menu command is newer again
    _menu(CUBE)
    assert rep.last(bpy.context)[0] == "kit"


def test_one_undo_step_per_g():
    _clear()
    bpy.ops.ed.undo_push(message="start")
    _menu(CUBE)
    assert bpy.ops.allset.repeat_last() == {'FINISHED'}
    _object_mode()
    assert _meshes() == ["pCube1", "pCube2"]
    bpy.ops.ed.undo()
    assert _meshes() == ["pCube1"], _meshes()               # one Ctrl+Z takes back exactly the repeated cube


def test_option_window_command_is_recorded_with_its_values():
    _clear()
    w = option_windows.find_path(CUBE)
    assert w is not None
    mod, name = w.idname.split(".")
    getattr(getattr(bpy.ops, mod), name)('EXEC_DEFAULT')       # the window's Create (Maya Apply / command)
    _object_mode()
    assert rep.HISTORY and rep.HISTORY[-1]["path"] == CUBE
    assert bpy.ops.allset.repeat_last() == {'FINISHED'}
    _object_mode()
    assert len(_meshes()) == 2, _meshes()


def test_marking_menu_item_and_recent_commands():
    _clear()
    res = modal.run_action(bpy.context, ("item", CUBE))         # a marking-menu entry that runs a menu item
    _object_mode()
    assert res == {'FINISHED'} and rep.HISTORY[-1]["action"] == ("item", CUBE)
    _select("pCube1")
    bpy.ops.mesh.primitive_uv_sphere_add('EXEC_DEFAULT', True)
    rows = rep.recent(bpy.context)
    labels = [r[2] for r in rows]
    assert labels[0] != "Cube" and "Cube" in labels, labels       # newest first: the sphere, then the cube
    kind, key, _l = next(r for r in rows if r[2] == "Cube")
    assert bpy.ops.allset.repeat_item(kind=kind, index=key) == {'FINISHED'}
    _object_mode()
    assert "pCube2" in _meshes()
    assert "ALLSET_MT_recent_commands" in dir(bpy.types)


def test_nothing_to_repeat_and_no_record_items():
    _clear()
    wm = bpy.context.window_manager
    for i in range(len(wm.operators)):
        pass
    rep.record("Repeat", "allset.repeat_last", "Edit/Repeat")
    assert not rep.HISTORY                                        # Edit > Repeat itself is never a command to repeat
    assert rep.repeatable("MESH_OT_extrude_region") and rep.repeatable("ALLSET_OT_extrude")
    for idname in ("VIEW3D_OT_select", "OBJECT_OT_select_all", "TRANSFORM_OT_translate", "ED_OT_undo",
                   "VIEW3D_OT_view_all", "SCREEN_OT_repeat_last", "ALLSET_OT_repeat_last"):
        assert not rep.repeatable(idname), idname


def test_keys_and_menus_point_at_the_kit_repeat():
    km = kit.maya_kc().keymaps["Screen"]
    g = [k for k in km.keymap_items if k.type == 'G' and k.value == 'PRESS' and k.active and not (k.shift or k.ctrl or k.alt)]
    assert [k.idname for k in g] == ["allset.repeat_last"], [k.idname for k in g]
    assert menu_map.MAP["Edit/Repeat"] == "allset.repeat_last"
    assert menu_map.MAP["Edit/Recent Commands List"] == ("menu", "ALLSET_MT_recent_commands")
    assert menu_sets._dynamic_label("Edit/Repeat", "Repeat").startswith("Repeat")
