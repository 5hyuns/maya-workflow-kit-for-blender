"""#478: Edit > Ungroup lists the freed children last among their new siblings, in the order they had in the group,
like Maya (and like Unparent)."""

from importlib import import_module

import bpy

import kit

rows_mod = import_module(kit.MODULE + ".ui.outliner_tree_rows")
order_mod = import_module(kit.MODULE + ".ui.outliner_order")


def _base():
    bpy.ops.wm.read_homefile(use_empty=True)
    for k in ('CUBE', 'SPHERE', 'LOCATOR'):
        bpy.ops.allset.create(kind=k)


def _sel(*names):
    for ob in bpy.context.view_layer.objects:
        ob.select_set(ob.name in names)
    bpy.context.view_layer.objects.active = bpy.data.objects[names[-1]]


def _rows():
    scene, vl = bpy.context.scene, bpy.context.view_layer
    order_mod.sync(scene, vl)
    return [(r.depth, r.label) for r in rows_mod.build(scene, vl, rows_mod.default_options())]


def _group_name():
    return next(o.name for o in bpy.data.objects if o.type == 'EMPTY' and o.children)


def test_ungroup_puts_children_last():
    _base()
    _sel("pCube1", "pSphere1")
    assert bpy.ops.allset.group() == {'FINISHED'}
    _sel(_group_name())
    assert bpy.ops.allset.ungroup() == {'FINISHED'}
    top = [label for depth, label in _rows() if depth == 0]
    assert top[-3:] == ["locator1", "pCube1", "pSphere1"], top


def test_ungroup_under_parent_puts_children_last():
    _base()
    _sel("pCube1", "pSphere1")
    bpy.ops.allset.group()
    inner = _group_name()
    _sel(inner, "locator1")
    assert bpy.ops.allset.parent() == {'FINISHED'}      # locator1 > inner group > pCube1, pSphere1
    _sel(inner)
    assert bpy.ops.allset.ungroup() == {'FINISHED'}
    loc = bpy.data.objects["locator1"]
    assert sorted(c.name for c in loc.children) == ["pCube1", "pSphere1"]
    sib = order_mod.sibling_lists(list(bpy.context.scene.objects), key=lambda o: o.get(order_mod.ORDER, 0))
    assert [o.name for o in sib["locator1"]] == ["pCube1", "pSphere1"], sib
