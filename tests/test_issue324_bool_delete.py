"""#324: deleting a Boolean result whose construction history keeps hidden input objects deletes those inputs
too, like Maya; undo brings everything back; an input another result still uses stays."""

from importlib import import_module

import bpy

import kit

mesh_maya = import_module(kit.MODULE + ".operators.mesh_maya")
dag = import_module(kit.MODULE + ".operators.dag")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def _select(*obs, active=None):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or obs[-1]


def _create(x=0.0, y=0.0):
    bpy.ops.allset.create(kind='CUBE')
    ob = bpy.context.active_object
    ob.location.x, ob.location.y = x, y
    return ob


def _meshes():
    return sorted(o.name for o in bpy.data.objects if o.type == 'MESH')


def _boolean_of_three():
    """A minus (B + C) with history on: A keeps B, B keeps C (both hidden)."""
    bpy.context.window_manager.allset_construction_history = True
    _clear()
    a, b, c = _create(), _create(0.5), _create(0.0, 0.5)
    _select(a, b, c, active=c)
    assert bpy.ops.allset.boolean(operation='DIFFERENCE') == {'FINISHED'}
    assert mesh_maya.bool_inputs(a) == [b] and mesh_maya.bool_inputs(b) == [c]
    assert not b.visible_get() and not c.visible_get()
    return a, b, c


def test_delete_result_takes_hidden_inputs():
    a, b, c = _boolean_of_three()
    names = _meshes()
    _select(a)
    bpy.ops.ed.undo_push(message="before")
    assert bpy.ops.allset.delete('EXEC_DEFAULT', True) == {'FINISHED'}
    assert _meshes() == [], _meshes()
    assert not bpy.data.meshes, [m.name for m in bpy.data.meshes]
    bpy.ops.ed.undo()
    assert _meshes() == names, (_meshes(), names)
    res = [o for o in bpy.data.objects if mesh_maya.bool_inputs(o) and o.visible_get()]
    assert len(res) == 1, [o.name for o in res]          # the result is back with its live Boolean
    hidden = sorted(o.name for o in bpy.data.objects if o.get(mesh_maya.BOOL_INPUT) and not o.visible_get())
    assert len(hidden) == 2, hidden                       # and both inputs, still hidden


def test_delete_input_alone_keeps_result():
    a, b, c = _boolean_of_three()
    c.hide_set(False)                    # shown again (Outliner / Show) and picked
    _select(c)
    an, bn, cn = a.name, b.name, c.name
    assert bpy.ops.allset.delete() == {'FINISHED'}
    assert _meshes() == sorted((an, bn)), _meshes()
    assert not bpy.data.objects[bn].visible_get(), "the other input stays a hidden input"


def test_shared_input_stays():
    """An input another object's Boolean still uses is kept when one result goes."""
    a, b, c = _boolean_of_three()
    d = _create(3.0)
    md = d.modifiers.new("Boolean", 'BOOLEAN')
    md.object = b
    _select(a)
    an, bn, cn, dn = a.name, b.name, c.name, d.name
    assert bpy.ops.allset.delete() == {'FINISHED'}
    assert _meshes() == sorted((bn, cn, dn)), _meshes()


def test_history_off_and_plain_delete_unchanged():
    bpy.context.window_manager.allset_construction_history = False
    _clear()
    a, b = _create(), _create(0.5)
    _select(a, b, active=b)
    assert bpy.ops.allset.boolean(operation='DIFFERENCE') == {'FINISHED'}
    e = _create(4.0)
    _select(a)
    assert bpy.ops.allset.delete() == {'FINISHED'}
    assert _meshes() == [e.name], _meshes()
    bpy.context.window_manager.allset_construction_history = True


def test_command_line_delete_takes_inputs():
    """The script delete (cmds.delete) uses the same rule."""
    a, b, c = _boolean_of_three()
    assert dag.delete_hierarchy(bpy.context, [a]) == 1
    assert _meshes() == [], _meshes()


def test_outliner_delete_keys():
    km = kit.maya_kc().keymaps["Outliner"]
    for key in ("DEL", "BACK_SPACE"):
        got = [k.idname for k in km.keymap_items if k.active and k.type == key and k.value == 'PRESS'
               and not (k.shift or k.ctrl or k.alt or k.oskey)]
        assert got[:1] == ["allset.outliner_delete"] or "allset.outliner_delete" in got, (key, got)
        assert "outliner.delete" not in got, (key, got)
