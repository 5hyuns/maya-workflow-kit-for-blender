"""Maya Outliner Ctrl+D = Edit > Duplicate: the Outliner's Ctrl+D runs allset.duplicate (IC: drivers_add_selected),
and a selected group copies with everything below it."""

import bpy

import kit


def _tree():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    coll = bpy.context.scene.collection
    fix = bpy.data.objects.new("fix", None)
    sub = bpy.data.objects.new("group1", None)
    a = bpy.data.objects.new("geometry_4", bpy.data.meshes.new("m4"))
    b = bpy.data.objects.new("geometry_12", bpy.data.meshes.new("m12"))
    for ob in (fix, sub, a, b):
        coll.objects.link(ob)
    sub.parent = fix
    a.parent = fix
    b.parent = sub
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    fix.select_set(True)
    bpy.context.view_layer.objects.active = fix
    return fix


def _shape(ob):
    return (ob.type, sorted(_shape(c) for c in ob.children))


def test_outliner_ctrl_d_keymap_item():
    km = kit.maya_kc().keymaps["Outliner"]
    items = [k for k in km.keymap_items if k.active and k.type == 'D' and k.value == 'PRESS'
             and k.ctrl and not (k.shift or k.alt)]
    assert [k.idname for k in items] == ["allset.duplicate"], [k.idname for k in items]


def test_group_duplicates_with_children():
    fix = _tree()
    before = set(bpy.data.objects)
    assert bpy.ops.allset.duplicate() == {'FINISHED'}
    new = [o for o in bpy.data.objects if o not in before]
    assert len(new) == 4, [o.name for o in new]
    top = [o for o in new if o.parent is None]
    assert len(top) == 1 and _shape(top[0]) == _shape(fix), [o.name for o in new]
    assert list(bpy.context.selected_objects) == top          # Maya selects the copy
    assert _shape(fix) == ('EMPTY', sorted([('EMPTY', [('MESH', [])]), ('MESH', [])]))   # original untouched
