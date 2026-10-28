"""Live lists/locks/history, evaluated target queries and restricted Move/Quad Draw."""
import os
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import bmesh
import bpy
from mathutils import Vector

import kit

live = import_module(kit.MODULE+'.operators.live')
qd = import_module(kit.MODULE+'.operators.quad_draw')
move = import_module(kit.MODULE+'.operators.live_translate')


def fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for scene in bpy.data.scenes:
        live.set_objects(scene, [])
        scene.allset_live_history.clear()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    ts = bpy.context.tool_settings
    ts.use_snap = False
    ts.snap_elements = {'INCREMENT'}
    ts.use_proportional_edit = False
    ts.transform_pivot_point = 'MEDIAN_POINT'
    bpy.context.scene.cursor.location = (0, 0, 0)
    return bpy.context.scene


def cube(name='Reference', position=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=position)
    ob = bpy.context.object
    ob.name = name
    return ob


def select(*objects):
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[-1] if objects else None


def test_make_live_locks_reference_without_changing_transform_or_snap_settings():
    scene = fresh()
    ob = cube()
    before = ob.matrix_world.copy(), [v.co.copy() for v in ob.data.vertices]
    ts = scene.tool_settings
    ts.use_snap, ts.snap_elements = True, {'GRID', 'VERTEX'}
    snap = import_module(kit.MODULE+'.operators.hold').GROUPS['snap'].capture(ts)
    assert bpy.ops.allset.make_live() == {'FINISHED'}
    assert live.objects(scene) == [ob] and ob.hide_select and not ob.select_get()
    assert bpy.context.active_object is None
    assert ob.matrix_world == before[0] and all(v.co == p for v, p in zip(ob.data.vertices, before[1]))
    assert not any(ob.lock_location) and not any(ob.lock_rotation) and not any(ob.lock_scale)
    assert import_module(kit.MODULE+'.operators.hold').GROUPS['snap'].capture(ts) == snap
    bpy.ops.allset.make_live()
    assert not live.objects(scene) and not ob.hide_select and live.LOCK not in ob
    assert import_module(kit.MODULE+'.operators.hold').GROUPS['snap'].capture(ts) == snap


def test_multiple_targets_history_rename_and_recent_toggle():
    scene = fresh()
    a, b = cube('A'), cube('B', (4, 0, 0))
    select(a, b)
    bpy.ops.allset.make_live()
    assert set(live.objects(scene)) == {a, b} and live.text(scene).startswith('<')
    assert a.hide_select and b.hide_select
    a.name = 'Renamed reference'
    bpy.ops.allset.live_list(action='CLEAR')
    assert not a.hide_select and not b.hide_select
    bpy.ops.allset.live_list(action='RECENT')
    assert set(live.objects(scene)) == {a, b}
    assert 'Renamed reference' in live.text(scene)
    bpy.ops.allset.live_list(action='RECENT')
    assert not live.objects(scene)


def test_history_add_remove_and_original_restrictions_are_preserved():
    scene = fresh()
    a, b = cube('A'), cube('B')
    a.hide_select = True
    live.set_objects(scene, [a])
    select(b)
    bpy.ops.allset.live_list(action='ADD')
    assert set(live.objects(scene)) == {a, b}
    # A history-menu entry removes a restricted reference without unlocking it.
    bpy.ops.allset.live_list(action='REMOVE', object_name=a.name)
    assert live.objects(scene) == [b] and a.hide_select
    live.set_objects(scene, [])
    assert a.hide_select and not b.hide_select


def test_invalid_selection_is_atomic_and_does_not_clear_live_list():
    scene = fresh()
    a = cube()
    live.set_objects(scene, [a])
    bpy.ops.object.empty_add()
    assert bpy.ops.allset.make_live() == {'CANCELLED'}
    assert live.objects(scene) == [a] and a.hide_select


def test_history_is_bounded_and_duplicate_groups_are_not_accumulated():
    scene = fresh()
    nodes = [cube('Ref'+str(i)) for i in range(live.LIMIT+2)]
    for ob in nodes:
        live.set_objects(scene, [ob])
    assert len(scene.allset_live_history) == live.LIMIT
    live.set_objects(scene, [nodes[-1]])
    assert len(scene.allset_live_history) == live.LIMIT


def test_shared_object_stays_restricted_until_last_scene_releases_it():
    scene = fresh()
    ob = cube()
    other = bpy.data.scenes.new('Other Live Scene')
    other.collection.objects.link(ob)
    try:
        live.set_objects(scene, [ob])
        live.set_objects(other, [ob])
        live.set_objects(scene, [])
        assert ob.hide_select
        live.set_objects(other, [])
        assert not ob.hide_select
    finally:
        bpy.data.scenes.remove(other)


def test_legacy_pointer_and_deleting_first_target_keep_list_consistent():
    scene = fresh()
    a, b = cube('A'), cube('B')
    scene.allset_live = a
    assert live.objects(scene) == [a] and a.hide_select
    live.set_objects(scene, [a, b])
    bpy.data.objects.remove(a, do_unlink=True)
    live.sync()
    assert live.objects(scene) == [b] and scene.allset_live == b
    scene.allset_live = None
    assert not live.objects(scene) and not b.hide_select


def test_queries_ignore_unrelated_front_surface_and_support_hidden_target():
    scene = fresh()
    reference = cube('Live')
    cube('Distractor', (0, 0, 3))
    live.set_objects(scene, [reference])
    hit = live.ray_hit(bpy.context, Vector((0, 0, 8)), Vector((0, 0, -1)))
    assert hit[2] == reference and abs(hit[0].z-1) < 1e-5
    reference.hide_set(True)
    bpy.context.view_layer.update()
    assert qd.reference_objects(bpy.context) == [reference]
    hit = live.ray_hit(bpy.context, Vector((0, 0, 8)), Vector((0, 0, -1)))
    assert hit and hit[2] == reference


def test_evaluated_modifier_and_geometry_transform_cache_invalidation():
    scene = fresh()
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    ob = bpy.context.object
    mod = ob.modifiers.new('Reference shell', 'SOLIDIFY')
    mod.thickness, mod.offset = 2, 1
    live.set_objects(scene, [ob])
    bpy.context.view_layer.update()
    origin, ray = Vector((0, 0, 10)), Vector((0, 0, -1))
    assert abs(live.ray_hit(bpy.context, origin, ray)[0].z-2) < 1e-5
    mod.thickness = 3
    bpy.context.view_layer.update()
    assert abs(live.ray_hit(bpy.context, origin, ray)[0].z-3) < 1e-5
    ob.location.z = 2
    bpy.context.view_layer.update()
    assert abs(live.ray_hit(bpy.context, origin, ray)[0].z-5) < 1e-5
    assert ob.modifiers[0] == mod and len(ob.data.vertices) == 4


def test_nearest_queries_use_world_distance_under_nonuniform_scale():
    scene = fresh()
    bpy.ops.mesh.primitive_plane_add(size=20, location=(1, 2, 3))
    ob = bpy.context.object
    ob.scale, ob.rotation_euler = (3, .4, 2), (.3, .2, .6)
    bpy.context.view_layer.update()
    live.set_objects(scene, [ob])
    normal = ob.matrix_world.to_3x3().inverted().transposed() @ Vector((0, 0, 1))
    normal.normalize()
    point = ob.matrix_world.translation+normal*4
    nearest = live.nearest(bpy.context, point)
    assert (nearest[0]-ob.matrix_world.translation).length < 2e-5


def test_quad_draw_never_edits_any_live_reference():
    scene = fresh()
    a, b = cube('A'), cube('B', (4, 0, 0))
    live.set_objects(scene, [a, b])
    select(b)
    assert qd.pick_target(bpy.context) is None
    assert set(qd.reference_objects(bpy.context)) == {a, b}
    assert (qd.project_point(bpy.context, Vector((4, 0, 3)))-Vector((4, 0, 1))).length < 1e-5


def test_live_wire_color_and_panel_visibility_rules():
    scene = fresh()
    ob = cube()
    live.set_objects(scene, [ob])
    wire = import_module(kit.MODULE+'.ui.selection_wire')
    ctx = SimpleNamespace(scene=scene, space_data=SimpleNamespace(shading=SimpleNamespace(type='SOLID'),
                          overlay=SimpleNamespace(show_wireframes=False)))
    assert live.COLOR == (0, .6, 84/255)
    assert not wire.live_wire_objects(ctx)
    ctx.space_data.overlay.show_wireframes = True
    assert wire.live_wire_objects(ctx) == [ob]
    ctx.space_data.overlay.show_wireframes = False
    ctx.space_data.shading.type = 'WIREFRAME'
    assert wire.live_wire_objects(ctx) == [ob]
    labels = import_module(kit.MODULE+'.ui.outliner_joints')
    assert labels.label(ob) == ob.name
    live.set_objects(scene, [])
    assert labels.label(ob) is None


def test_move_object_projects_only_to_live_and_preserves_reference():
    scene = fresh()
    reference = cube('Live')
    cube('Distractor', (0, 0, 3))
    live.set_objects(scene, [reference])
    source = cube('Mover', (0, 0, 7))
    before = reference.matrix_world.copy()
    assert bpy.ops.allset.live_translate(value=(0, 0, -3)) == {'FINISHED'}
    assert abs(source.location.z-1) < 1e-5
    assert reference.matrix_world == before and reference.hide_select


def test_move_components_uses_native_uv_and_selected_geometry():
    scene = fresh()
    reference = cube('Live')
    live.set_objects(scene, [reference])
    source = cube('Mover', (0, 0, 5))
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    before = source.matrix_world.copy()
    assert bpy.ops.allset.live_translate(value=(0, 0, -3)) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(source.data)
    centre = sum((source.matrix_world @ v.co for v in bm.verts), Vector())/len(bm.verts)
    assert abs(centre.z-1) < 1e-5 and source.matrix_world == before


def test_live_state_and_history_survive_blend_roundtrip():
    scene = fresh()
    a, b = cube('Saved A'), cube('Saved B', (4, 0, 0))
    live.set_objects(scene, [a, b])
    path = Path(os.environ['BLENDER_USER_CONFIG']).parent/'live_roundtrip.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    assert [o.name for o in live.objects(scene)] == ['Saved A', 'Saved B']
    assert all(o.hide_select for o in live.objects(scene))
    bpy.ops.allset.live_list(action='CLEAR')
    assert not any(bpy.data.objects[n].hide_select for n in ('Saved A', 'Saved B'))
    bpy.ops.allset.live_list(action='RECENT')
    assert len(live.objects(scene)) == 2


def test_disable_reenable_restores_flags_without_losing_live_identity():
    scene = fresh()
    ob = cube()
    live.set_objects(scene, [ob])
    switch = import_module(kit.MODULE+'.switch')
    switch.set_mode(False, layout=False)
    assert not ob.hide_select and live.LOCK not in ob
    switch.set_mode(True, layout=False)
    assert live.objects(scene) == [ob] and ob.hide_select
    live.set_objects(scene, [])


def test_component_commands_cannot_edit_an_outliner_active_live_reference():
    scene = fresh()
    ob = cube()
    live.set_objects(scene, [ob])
    bpy.context.view_layer.objects.active = ob
    for kind in ('VERT', 'EDGE', 'FACE', 'MULTI'):
        assert bpy.ops.allset.component_mode(type=kind) == {'CANCELLED'}
        assert bpy.context.mode == 'OBJECT'
    assert bpy.ops.allset.toggle_sel_mode() == {'CANCELLED'}
    bpy.ops.allset.component_mask(kind='ALL')
    assert bpy.context.mode == 'OBJECT'


def test_status_line_magnet_and_dropdown_are_bound_to_live_operators():
    from test_step7_top_ui import FakeLayout, _ctx
    fresh()
    status = import_module(kit.MODULE+'.ui.status_line')
    status._collapsed.discard('SNAP')
    layout = FakeLayout()
    status.draw_status_line(layout, _ctx(), compact=True)
    calls = [e for e in layout.log if e[0] == 'op']
    assert any(e[1] == 'allset.make_live' for e in calls)
    assert len([e for e in calls if e[1] == 'allset.live_history']) >= 2
    assert not any(e[1] == 'allset.snap_toggle' and getattr(e[3], 'snap', None) == 'LIVE' for e in calls)
