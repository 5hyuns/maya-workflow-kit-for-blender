"""A selected group still highlights its contents with Show > Locators (Empties) off."""
from importlib import import_module

import bpy

import kit

wire = import_module(kit.MODULE + '.ui.selection_wire')
tree = import_module(kit.MODULE + '.ui.outliner_tree')


def test_group_hidden_by_view_type_still_highlights_visible_descendants():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    group = bpy.data.objects.new('fix', None)
    nested = bpy.data.objects.new('nested', None)
    mesh = bpy.data.meshes.new('body')
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    child = bpy.data.objects.new('body', mesh)
    other = bpy.data.objects.new('other', mesh)
    hidden = bpy.data.objects.new('hidden', mesh)
    for ob in (group, nested, child, other, hidden):
        bpy.context.scene.collection.objects.link(ob)
    nested.parent = group
    child.parent = hidden.parent = nested
    bpy.context.view_layer.update()
    hidden.hide_set(True)
    area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    space = area.spaces.active
    old = space.show_object_viewport_empty
    try:
        with bpy.context.temp_override(area=area, region=region):
            rows = tree.build(bpy.context.scene, bpy.context.view_layer, tree.default_options())
            index = next(i for i, r in enumerate(rows) if r.ob == group.name)
            tree.select_row(bpy.context, rows, index, 'REPLACE')
            for show in (True, False):
                space.show_object_viewport_empty = show
                assert group.select_get() and bpy.context.active_object == group
                assert list(bpy.context.view_layer.objects.selected) == [group]
                if not show:
                    assert bpy.context.selected_objects == [], 'Blender filters the group out of the view context'
                for fast in (False, True):
                    assert wire.highlighted(bpy.context, roots_shown=fast) == [(child, True)]
            # A separately picked child keeps its own white colour under the green lead group.
            child.select_set(True)
            assert dict(wire.highlighted(bpy.context, roots_shown=True)) == {child: False}
            child.select_set(False)
            wire.set_highlighting(bpy.context, False)
            try:
                assert wire.highlighted(bpy.context, roots_shown=True) == []
            finally:
                wire.set_highlighting(bpy.context, True)
            space.show_object_viewport_mesh = False
            try:
                assert wire.highlighted(bpy.context, roots_shown=True) == []
            finally:
                space.show_object_viewport_mesh = True
            group.select_set(False)
            assert wire.highlighted(bpy.context, roots_shown=True) == []
    finally:
        space.show_object_viewport_empty = old
