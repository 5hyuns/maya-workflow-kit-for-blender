"""With the 3D View's Show > Locators off, a selected group is missing from Blender's selected objects; Duplicate,
Duplicate Special, Duplicate with Transform, Freeze Transformations and Delete History still take it."""
from contextlib import contextmanager

import bpy


@contextmanager
def hidden_group():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    root = bpy.data.objects.new("group1", None)
    mesh = bpy.data.meshes.new("pCubeShape1")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    child = bpy.data.objects.new("pCube1", mesh)
    for ob in (root, child):
        bpy.context.scene.collection.objects.link(ob)
    child.parent = root
    root.location = (2, 0, 0)
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.context.view_layer.update()
    area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    space = area.spaces.active
    old = space.show_object_viewport_empty
    try:
        with bpy.context.temp_override(area=area, region=region):
            space.show_object_viewport_empty = False
            assert bpy.context.selected_objects == []
            yield bpy.context, root
    finally:
        space.show_object_viewport_empty = old


def _groups():
    return sorted(ob.name for ob in bpy.data.objects if ob.type == 'EMPTY')


def test_duplicate_takes_the_hidden_group():
    with hidden_group() as (ctx, root):
        assert bpy.ops.allset.duplicate() == {'FINISHED'}
        assert _groups() == ["group1", "group2"], _groups()
        new = bpy.data.objects["group2"]
        assert [c.type for c in new.children] == ['MESH']
        assert list(ctx.view_layer.objects.selected) == [new]       # the hidden original is no longer selected


def test_duplicate_special_and_with_transform_take_the_hidden_group():
    with hidden_group() as (ctx, root):
        assert bpy.ops.allset.duplicate_special() == {'FINISHED'}
        assert len(_groups()) == 2, _groups()
    with hidden_group() as (ctx, root):
        assert bpy.ops.allset.duplicate_with_transform() == {'FINISHED'}
        assert len(_groups()) == 2, _groups()


def test_freeze_takes_the_hidden_group():
    with hidden_group() as (ctx, root):
        assert bpy.ops.allset.freeze_transform() == {'FINISHED'}
        assert tuple(root.location) == (0.0, 0.0, 0.0)
