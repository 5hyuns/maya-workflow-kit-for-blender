"""Mesh > Transfer Attributes (#554), like Maya: the last selected mesh takes vertex normals / positions / UV sets /
color sets from the other selected mesh, live. Start values: Vertex position Off, Vertex normal Off, UV Sets All,
Color Sets All, World, Closest to point. With Vertex normal On a hard-edged cube takes the smooth normals of a sphere
around it: one normal per vertex, the sphere's normal at the closest point."""

import bpy
from mathutils import Vector


def _scene():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=20, radius=1.0)
    src = bpy.context.active_object
    src.name = "src"
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_cube_add(size=1.4)
    dst = bpy.context.active_object
    dst.name = "dst"
    bpy.ops.object.shade_flat()
    src.select_set(True)
    dst.select_set(True)
    bpy.context.view_layer.objects.active = dst
    return src, dst


def _corner_normals(ob):
    me = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    out = {}
    for loop, n in zip(me.loops, me.corner_normals):
        out.setdefault(loop.vertex_index, []).append(Vector(n.vector))
    return out, me


def test_menu_item_runs_kit_operator():
    from bl_ext.user_default.allset.ui import menu_map
    assert menu_map.MAP["Mesh/Transfer Attributes"] == "allset.transfer_attributes"


def test_start_values_transfer_uvs_and_colors_not_normals():
    src, dst = _scene()
    assert bpy.ops.allset.transfer_attributes() == {'FINISHED'}
    mods = [m for m in dst.modifiers]
    assert len(mods) == 1 and mods[0].type == 'DATA_TRANSFER', [m.type for m in mods]
    dt = mods[0]
    assert dt.object is src and dt.use_object_transform
    assert set(dt.data_types_loops) == {'UV', 'COLOR_CORNER'}, dt.data_types_loops
    assert dt.loop_mapping == 'POLYINTERP_NEAREST'
    assert dt.layers_uv_select_src == 'ALL'
    assert not src.modifiers
    # the selection stays as it was
    assert src.select_get() and dst.select_get() and bpy.context.view_layer.objects.active is dst


def test_normals_on_gives_smooth_vertex_normals():
    for method in ('CLOSEST_POINT', 'ALONG_NORMAL'):
        src, dst = _scene()
        before, _ = _corner_normals(dst)
        assert any(a.angle(b) > 1.0 for ns in before.values() for a in ns for b in ns)   # hard edges first
        assert bpy.ops.allset.transfer_attributes(normals='ON', uv_sets='OFF', color_sets='OFF',
                                                  search_method=method) == {'FINISHED'}
        after, me = _corner_normals(dst)
        for vi, ns in after.items():
            for n in ns:
                assert n.angle(ns[0]) < 1e-3, (method, vi, ns)      # one normal per vertex
            corner = me.vertices[vi].co.normalized()
            assert ns[0].angle(corner) < 0.06, (method, vi, ns[0], corner)   # the sphere's normal there


def test_positions_on_moves_points_onto_the_source():
    src, dst = _scene()
    assert bpy.ops.allset.transfer_attributes(positions='ON', uv_sets='OFF', color_sets='OFF') == {'FINISHED'}
    me = dst.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    for v in me.vertices:
        assert 0.95 < v.co.length <= 1.0 + 1e-4, v.co


def test_live_follows_the_source():
    src, dst = _scene()
    bpy.ops.allset.transfer_attributes(positions='ON', uv_sets='OFF', color_sets='OFF')
    src.location.x = 3.0
    bpy.context.view_layer.update()
    me = dst.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    assert all(v.co.x > 0.5 for v in me.vertices), [tuple(v.co) for v in me.vertices]


def test_one_mesh_selected_is_refused():
    src, dst = _scene()
    src.select_set(False)
    try:
        bpy.ops.allset.transfer_attributes(normals='ON')
    except RuntimeError as ex:
        assert "Select at least one source" in str(ex), ex
    else:
        raise AssertionError("ran with one mesh")
    assert not dst.modifiers
