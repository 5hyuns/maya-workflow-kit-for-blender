"""Groups retain their tool handles and transform selection with locator axes hidden."""
from contextlib import contextmanager
from importlib import import_module
import math

import bpy
from mathutils import Vector

import kit

group = import_module(kit.MODULE + '.operators.group')
mp = import_module(kit.MODULE + '.ui.manipulator')
scale = import_module(kit.MODULE + '.operators.manip_scale')


@contextmanager
def fixture():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    root = bpy.data.objects.new('fix', None)
    mesh = bpy.data.meshes.new('body')
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    child = bpy.data.objects.new('body', mesh)
    for ob in (root, child):
        bpy.context.scene.collection.objects.link(ob)
    child.parent = root
    child.location = (1, 0, 0)
    root.location = (2, 3, 4)
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
            yield bpy.context, root, child
    finally:
        space.show_object_viewport_empty = old


def test_group_has_move_rotate_scale_handles_at_its_pivot():
    with fixture() as (ctx, root, child):
        ctx.scene.tool_settings.transform_pivot_point = 'ACTIVE_ELEMENT'
        assert ctx.selected_objects == []
        for tool, kind in mp.TOOLS.items():
            bpy.ops.wm.tool_set_by_id(name=tool)
            assert mp.tool_kind(ctx) == kind
            assert mp.ALLSET_GGT_xform.poll(ctx), tool
            center, _, _ = mp.pivot_frame(ctx, kind)
            assert (center - root.matrix_world.translation).length < 1e-6
        bpy.ops.wm.tool_set_by_id(name='builtin.select_box')
        assert not mp.ALLSET_GGT_xform.poll(ctx)
        assert list(ctx.view_layer.objects.selected) == [root] and not child.select_get()


def test_hidden_group_transform_moves_children_once_and_scale_restores():
    with fixture() as (ctx, root, child):
        baseline = child.matrix_world.translation.copy()
        with group.selection_context(ctx):
            assert ctx.selected_objects == [root]
            assert ctx.selected_editable_objects == [root]
            assert bpy.ops.transform.translate(value=(1, 0, 0)) == {'FINISHED'}
        ctx.view_layer.update()
        assert (child.matrix_world.translation - baseline - Vector((1, 0, 0))).length < 1e-6
        assert ctx.selected_objects == [] and not ctx.space_data.show_object_viewport_empty
        with group.selection_context(ctx):
            state = scale.save_state(ctx)
            assert scale.supported(ctx)
            assert scale.apply(ctx, 2.0) == {'FINISHED'}
            assert all(abs(v - 2) < 1e-6 for v in root.scale)
            scale.restore(state)
            assert all(abs(v - 1) < 1e-6 for v in root.scale)
            assert bpy.ops.transform.rotate(value=math.pi / 2, orient_type='GLOBAL',
                                            orient_axis='Z', constraint_axis=(False, False, True)) == {'FINISHED'}
        assert abs(root.rotation_euler.z - math.pi / 2) < 1e-6, tuple(root.rotation_euler)
        assert list(ctx.view_layer.objects.selected) == [root] and not child.select_get()


def test_locked_group_is_not_added_to_editable_selection():
    with fixture() as (ctx, root, _child):
        root.hide_select = True
        before = root.matrix_world.copy()
        with group.selection_context(ctx):
            assert root not in ctx.selected_editable_objects
            assert bpy.ops.transform.translate(value=(1, 0, 0)) == {'CANCELLED'}
        assert root.matrix_world == before
