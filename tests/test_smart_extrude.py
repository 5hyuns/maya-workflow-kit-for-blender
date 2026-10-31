"""Operator/session contracts of modern Maya Smart Extrude."""
import math
from importlib import import_module

import bmesh
import bpy
from mathutils import Vector
from kit import MODULE


def smart():
    return import_module(MODULE + '.operators.smart_extrude')


def setup(mode='FACE', inset=False):
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    smart().clear()
    bpy.context.scene.unit_settings.system = 'NONE'
    bpy.context.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
    for slot in bpy.context.scene.transform_orientation_slots:
        slot.type = 'GLOBAL'
    bpy.ops.mesh.primitive_cube_add(size=2)
    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type=mode)
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(ob.data)
    top = max(bm.faces, key=lambda f: f.calc_center_median().z)
    if inset:
        bmesh.ops.inset_region(bm, faces=[top], thickness=.5, depth=0, use_even_offset=True)
        top = min((f for f in bm.faces if f.calc_center_median().z > .99), key=lambda f: f.calc_center_median().xy.length)
    if mode == 'FACE':
        top.select_set(True)
    elif mode == 'EDGE':
        top.edges[0].select_set(True)
    else:
        top.verts[0].select_set(True)
    bm.select_flush_mode()
    bm.faces.active = top
    bmesh.update_edit_mesh(ob.data)
    return ob


def volume(ob):
    return bmesh.from_edit_mesh(ob.data).calc_volume()


def test_operator_outward_pocket_through_and_selection():
    ob = setup(inset=True)
    assert bpy.ops.allset.smart_extrude(translation=(0, 0, -3)) == {'FINISHED'}
    assert abs(volume(ob)-6) < 1e-5
    bm = bmesh.from_edit_mesh(ob.data)
    assert all(e.is_manifold for e in bm.edges)
    assert any(f.select for f in bm.faces), 'through-hole leaves its cut walls selected'
    assert not any(o.name.startswith('.allset_smart') for o in bpy.data.objects)
    assert not any(m.name.startswith('.allset_smart') for m in bpy.data.meshes)


def test_repeat_uses_new_selection():
    ob = setup()
    bpy.ops.allset.smart_extrude(translation=(0, 0, 1))
    assert abs(volume(ob)-12) < 1e-5
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(False)
    face = max(bm.faces, key=lambda f: f.calc_center_median().x)
    face.select_set(True)
    bmesh.update_edit_mesh(ob.data)
    # Replaying the recorded properties captures the NEW face's component normal.
    repeat = import_module(MODULE + '.operators.repeat_maya')
    entry = repeat.HISTORY[-1]
    op_props = entry['action'][2]
    bpy.ops.allset.smart_extrude(**op_props)
    assert volume(ob) > 12.1, volume(ob)
    assert max(v.co.x for v in bmesh.from_edit_mesh(ob.data).verts) > 1.99


def test_rotated_scaled_object_and_custom_pivot_snapshot():
    ob = setup()
    ob.rotation_euler = (.2, -.4, .7)
    ob.scale = (2, 3, .5)
    bpy.context.view_layer.update()
    before = ob.matrix_world.copy()
    session = smart().Session(bpy.context, 'WORLD')
    try:
        result = session.result(bpy.context, (0, 0, .3), (0, 0, 0), (1, 1, 1))
        assert all(e.is_manifold for e in result.edges)
        result.free()
        assert ob.matrix_world == before
        bpy.context.tool_settings.transform_pivot_point = 'CURSOR'
        bpy.context.scene.cursor.location = (3, 4, 5)
    finally:
        session.free()
    session = smart().Session(bpy.context, 'CUSTOM')
    try:
        assert session.centre == Vector((3, 4, 5))
        frozen = session.centre.copy()
        bpy.context.scene.cursor.location = (0, 0, 0)
        assert session.centre == frozen
    finally:
        session.free()


def test_rotate_scale_full_transform_keeps_cap_and_volume():
    ob = setup()
    session = smart().Session(bpy.context)
    try:
        result = session.result(bpy.context, (0, 0, 1), (math.radians(25), 0, 0), (.6, .6, 1))
        assert result.calc_volume() > 8
        assert all(e.is_manifold and e.is_contiguous for e in result.edges)
        assert any(f.select for f in result.faces)
        expected = session.transform((0, 0, 1), (math.radians(25), 0, 0), (.6, .6, 1))
        top = max(session.pre.faces, key=lambda f: f.calc_center_median().z)
        for v in top.verts:
            assert min((expected @ v.co - p.co).length for p in result.verts) < 1e-5
        result.free()
    finally:
        session.free()


def test_rotation_without_translation_grows_and_carves():
    ob = setup()
    session = smart().Session(bpy.context)
    try:
        result = session.result(bpy.context, (0, 0, 0), (math.radians(20), 0, 0), (1, 1, 1))
        zs = [v.co.z for v in result.verts]
        assert max(zs) > 1.2 and any(.6 < z < .9 for z in zs), zs
        assert all(e.is_manifold for e in result.edges)
        result.free()
    finally:
        session.free()


def test_component_conversion_and_individual_faces():
    for mode, count in (('VERT', 3), ('EDGE', 2)):
        setup(mode)
        session = smart().Session(bpy.context, together=False)
        try:
            assert len(session.faces) == count, session.faces
            result = session.result(bpy.context, (0, 0, .2), (0, 0, 0), (1, 1, 1))
            assert result.calc_volume() > 8
            assert all(e.is_manifold for e in result.edges)
            result.free()
        finally:
            session.free()


def test_uv_and_materials_on_unaffected_faces():
    ob = setup()
    ob.data.materials.clear()
    material = bpy.data.materials.new('Smart untouched')
    other = bpy.data.materials.new('Smart cap')
    ob.data.materials.append(material)
    ob.data.materials.append(other)
    bm = bmesh.from_edit_mesh(ob.data)
    layer = bm.loops.layers.uv.new('ArtistUV')
    bottom = min(bm.faces, key=lambda f: f.calc_center_median().z)
    expected = {}
    for i, lp in enumerate(bottom.loops):
        uv = (.12+i*.1, .23+i*.05)
        lp[layer].uv = uv
        expected[tuple(lp.vert.co)] = uv
    bottom.material_index = 0
    max(bm.faces, key=lambda f: f.calc_center_median().z).material_index = 1
    bmesh.update_edit_mesh(ob.data)
    bpy.ops.allset.smart_extrude(translation=(0, 0, 1))
    bm = bmesh.from_edit_mesh(ob.data)
    layer = bm.loops.layers.uv.get('ArtistUV')
    bottom = min(bm.faces, key=lambda f: f.calc_center_median().z)
    assert layer is not None and bottom.material_index == 0
    for lp in bottom.loops:
        assert (Vector(lp[layer].uv)-Vector(expected[tuple(lp.vert.co)])).length < 1e-6
    assert ob.data.materials[0] == material
    assert ob.data.materials[1] == other
    assert all(f.material_index == 1 for f in bm.faces if f.select)


def test_failed_operation_is_atomic_and_no_datablock_leaks():
    ob = setup()
    signature = smart().signature(bmesh.from_edit_mesh(ob.data))
    before = (len(bpy.data.objects), len(bpy.data.meshes))
    for _ in range(3):
        assert bpy.ops.allset.smart_extrude(translation=(0, 0, -4)) == {'CANCELLED'}
    assert smart().signature(bmesh.from_edit_mesh(ob.data)) == signature
    assert (len(bpy.data.objects), len(bpy.data.meshes)) == before


def test_coplanar_adjustment_keeps_selection_for_later_depth():
    ob = setup()
    bpy.ops.allset.smart_extrude(scale=(.5, .5, 1))
    assert abs(volume(ob)-8) < 1e-5
    assert any(f.select for f in bmesh.from_edit_mesh(ob.data).faces)
    rec, params = smart().current(bpy.context)
    session = rec['session']
    result = session.result(bpy.context, (0, 0, 1), params['rotation'], params['scale'])
    try:
        assert 8 < result.calc_volume() < 12
    finally:
        result.free()


def test_cancel_restores_active_component_and_custom_pivot():
    ob = setup()
    hold = import_module(MODULE+'.operators.hold')
    bpy.context.tool_settings.transform_pivot_point = 'CURSOR'
    bpy.context.scene.cursor.location = (3, 4, 5)
    hold.COMPONENT.custom = True
    hold.COMPONENT.sel_sig = hold.selection_signature(bpy.context)
    bm = bmesh.from_edit_mesh(ob.data)
    bm.select_history.add(bm.faces.active)
    before = smart().selection_state(bm)
    session = smart().Session(bpy.context)
    try:
        session.show(bpy.context, (0, 0, 1), (0, 0, 0), (1, 1, 1))
        hold.COMPONENT.tick(bpy.context)
        session.restore(bpy.context)
        assert smart().selection_state(bmesh.from_edit_mesh(ob.data)) == before
        assert bpy.context.tool_settings.transform_pivot_point == 'CURSOR'
        assert hold.COMPONENT.custom
        assert bpy.context.scene.cursor.location == Vector((3, 4, 5))
    finally:
        session.free()
        hold.COMPONENT.custom = False
        hold.COMPONENT.sel_sig = None


def test_open_input_rejected_without_changing_mesh():
    ob = setup()
    bm = bmesh.from_edit_mesh(ob.data)
    bottom = min(bm.faces, key=lambda f: f.calc_center_median().z)
    bmesh.ops.delete(bm, geom=[bottom], context='FACES_ONLY')
    bmesh.update_edit_mesh(ob.data)
    before = smart().signature(bm)
    assert bpy.ops.allset.smart_extrude(translation=(0, 0, 1)) == {'CANCELLED'}
    assert smart().signature(bmesh.from_edit_mesh(ob.data)) == before
