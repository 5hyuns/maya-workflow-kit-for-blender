"""#487: UV > Planar projects along the scene's axis and fits the selection's box in the scene (the object's turn and
scale count), and clicking UV > Planar gives the option window's default result (X axis, bounding box)."""

import math

import bmesh
import bpy

from bl_ext.user_default.allset.operators import option_windows, option_windows_basic as owb


def _turned_box():
    """A unit cube scaled 3 x 1 x 1 and turned 90 degrees about Z: in the scene it is 1 (X) x 3 (Y) x 1 (Z)."""
    bpy.ops.wm.read_homefile(use_empty=True)
    me = bpy.data.meshes.new("box")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("box", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (4, 5, 6)
    ob.scale = (3, 1, 1)
    ob.rotation_euler = (0, 0, math.pi / 2)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.context.view_layer.update()
    return ob


def _uvs(ob):
    """{scene position of the vertex: its UVs}."""
    me = ob.data
    layer = me.uv_layers.active.data
    out = {}
    for lp in me.loops:
        co = tuple(round(c, 3) for c in ob.matrix_world @ me.vertices[lp.vertex_index].co)
        out.setdefault(co, set()).add(tuple(round(c, 3) for c in layer[lp.index].uv))
    return out


def test_planar_x_follows_the_scene_on_a_turned_scaled_object():
    ob = _turned_box()
    assert bpy.ops.allset.uv_planar(axis='X') == {'FINISHED'}
    for co, uvs in _uvs(ob).items():
        assert len(uvs) == 1, (co, uvs)
        u, v = next(iter(uvs))
        # sees scene Y (3) x Z (1): U along +Y spans 0-1, V along +Z centred
        assert abs(u - (co[1] - 3.5) / 3) < 1e-3, (co, u)
        assert abs(v - ((co[2] - 5.5) / 3 + 1 / 3)) < 1e-3, (co, v)


def test_planar_menu_click_matches_the_option_window_defaults():
    ob = _turned_box()
    window = option_windows.find_path("UV/Planar")
    assert window is not None
    owb._run_uv_planar(bpy.context, window.defaults())
    by_window = _uvs(ob)
    ob = _turned_box()
    assert bpy.ops.allset.menu_item(item="UV/Planar") == {'FINISHED'}
    assert _uvs(ob) == by_window


def test_normal_based_uses_the_scene_normal():
    """A plane turned to face scene X: Normal-Based sees it flat (not edge-on), filling 0-1."""
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.mesh.primitive_plane_add(size=2)
    ob = bpy.context.active_object
    ob.rotation_euler = (0, math.pi / 2, 0)
    ob.scale = (1, 2, 1)
    bpy.context.view_layer.update()
    assert bpy.ops.allset.menu_item(item="UV/Normal-Based") == {'FINISHED'}
    us = [u for s in _uvs(ob).values() for u, _v in s]
    vs = [v for s in _uvs(ob).values() for _u, v in s]
    spans = sorted((round(max(us) - min(us), 3), round(max(vs) - min(vs), 3)))
    assert spans == [0.5, 1.0], spans
