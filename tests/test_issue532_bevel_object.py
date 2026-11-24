"""Issue #532: Bevel on an object selection and on a mesh scaled differently per axis, like Maya.

- Ctrl+B with objects selected (object mode) bevels every edge of each selected mesh and stays in object mode; so do
  Edit Mesh > Bevel and its option window. The new polyBevel node shows in the In-View Editor right away.
- World Space (on): Fraction, Offset and the profile work on the mesh as it stands in the world, so a cube scaled
  (1, 1, 6) gets the same width on every edge instead of ends six times wider; off: on the object-space mesh.
"""

from importlib import import_module

import bmesh
import bpy
from mathutils import Matrix, Vector

import kit

bev = import_module(kit.MODULE + ".operators.bevel_maya")
extrude = import_module(kit.MODULE + ".operators.extrude")
in_view_target = import_module(kit.MODULE + ".ui.in_view_target")
option_windows_basic = import_module(kit.MODULE + ".operators.option_windows_basic")

TOL = 1e-4


def _fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    extrude.clear()
    scene = bpy.context.scene
    for k in [k for k in scene.keys() if k.startswith("allset_poly")]:
        del scene[k]


def _cube(scale=(1.0, 1.0, 6.0), rotation=(0.0, 0.0, 0.0)):
    """A kit cube with an object scale; returns (object, side length in object space)."""
    assert bpy.ops.allset.create(kind='CUBE') == {'FINISHED'}
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    ob = bpy.context.view_layer.objects.active
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    ob.scale = scale
    ob.rotation_euler = rotation
    bpy.context.view_layer.update()
    xs = [v.co.x for v in ob.data.vertices]
    return ob, max(xs) - min(xs)


def _insets(ob, side):
    """World distance of the bevel's points from the box faces, per object axis: the set of distances seen."""
    half = side / 2.0
    scale = [abs(s) for s in ob.scale]
    out = []
    for a in range(3):
        out.append(sorted({round(scale[a] * (half - abs(v.co[a])), 5) for v in ob.data.vertices}))
    return out


def _check_even(ob, side, width):
    insets = _insets(ob, side)
    for a, values in enumerate(insets):
        # each point lies on the box face or one width in from it
        assert all(abs(d) < TOL or abs(d - width) < TOL for d in values), (a, insets, width)
        assert any(abs(d - width) < TOL for d in values), (a, insets, width)


def test_ctrl_b_in_object_mode_runs_the_bevel():
    km = kit.maya_kc().keymaps["Object Mode"]
    items = [k.idname for k in km.keymap_items if k.active and k.type == 'B' and k.value == 'PRESS' and k.ctrl
             and not (k.shift or k.alt or k.oskey)]
    assert items == ["allset.bevel"], items


def test_object_mode_bevel_is_even_on_a_scaled_cube_and_shows_the_in_view_editor():
    _fresh()
    ob, side = _cube()
    assert bpy.ops.allset.bevel() == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT' and ob.select_get()
    assert len(ob.data.vertices) == 24 and len(ob.data.polygons) == 26, (len(ob.data.vertices), len(ob.data.polygons))
    # Fraction 0.5 of the shortest world edge (the side), halved as both of its ends are bevelled
    _check_even(ob, side, side * 0.25 * bev.FIT)
    shown, node = in_view_target.object_shown(bpy.context)
    assert shown == ob and node is not None and node.name == "polyBevel1", (shown, node)
    # every face still faces out
    centre = sum((v.co for v in ob.data.vertices), Vector()) / len(ob.data.vertices)
    assert all(p.normal.dot(p.center - centre) > 0.0 for p in ob.data.polygons)


def test_edit_mode_bevel_on_a_scaled_cube_is_even_too():
    _fresh()
    ob, side = _cube(scale=(2.0, 1.0, 0.5))
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    assert bpy.ops.allset.bevel() == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    _check_even(ob, side, side * 0.5 * 0.25 * bev.FIT)       # the shortest world edge is half the side


def test_rotated_scaled_and_mirrored_cubes():
    for scale, rotation in (((1.0, 1.0, 6.0), (0.5, 0.7, 0.0)), ((-1.0, 1.0, 6.0), (0.0, 0.0, 0.0))):
        _fresh()
        ob, side = _cube(scale, rotation)
        assert bpy.ops.allset.bevel() == {'FINISHED'}
        _check_even(ob, side, side * 0.25 * bev.FIT)
        centre = sum((v.co for v in ob.data.vertices), Vector()) / len(ob.data.vertices)
        assert all(p.normal.dot(p.center - centre) > 0.0 for p in ob.data.polygons), scale


def test_offset_is_in_world_units_on_every_axis():
    _fresh()
    ob, side = _cube()
    offset = 0.2 * side
    unit = side          # the kit cube's side is one Maya length
    assert bpy.ops.allset.bevel(offset_as_fraction=False, offset=offset / unit) == {'FINISHED'}
    _check_even(ob, side, offset * bev.FIT)


def test_segments_keep_a_round_profile_in_the_world():
    _fresh()
    ob, side = _cube()
    assert bpy.ops.allset.bevel(segments=3) == {'FINISHED'}
    insets = _insets(ob, side)
    assert len(insets[0]) == 4 and all(len(i) == 4 for i in insets), insets
    for a in (1, 2):
        assert all(abs(p - q) < TOL for p, q in zip(insets[0], insets[a])), insets


def test_world_space_off_works_in_object_space():
    _fresh()
    ob, side = _cube()
    assert bpy.ops.allset.bevel(world_space=False) == {'FINISHED'}
    half = side / 2.0
    for a in range(3):
        values = sorted({round(half - abs(v.co[a]), 5) for v in ob.data.vertices})
        assert len(values) == 2 and abs(values[-1] - side * 0.25 * bev.FIT) < TOL, (a, values)


def test_editing_the_node_keeps_the_world_widths():
    _fresh()
    ob, side = _cube()
    assert bpy.ops.allset.bevel() == {'FINISHED'}
    assert extrude.set_params(bpy.context, fraction=0.3) == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    _check_even(ob, side, side * 0.3 * 0.5 * bev.FIT)


def test_menu_item_and_option_window_from_object_mode():
    _fresh()
    ob, side = _cube()
    assert bpy.ops.allset.menu_item(item="Edit Mesh/Bevel") == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    _check_even(ob, side, side * 0.25 * bev.FIT)
    assert in_view_target.object_shown(bpy.context)[0] == ob
    _fresh()
    ob, side = _cube()
    v = {"offset_type": "Fractional", "width": 0.4, "segments": 1, "depth": 1.0}
    assert option_windows_basic._run_bevel(bpy.context, v) == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    _check_even(ob, side, side * 0.4 * 0.5 * bev.FIT)
    assert in_view_target.object_shown(bpy.context)[0] == ob


def test_shape_matrix_leaves_rigid_and_uniform_transforms_alone():
    class Ob:
        def __init__(self, m):
            self.matrix_world = m
    assert bev.shape_matrix(None) is None
    assert bev.shape_matrix(Ob(Matrix.Identity(4))) is None
    assert bev.shape_matrix(Ob(Matrix.Rotation(0.6, 4, 'X') @ Matrix.Diagonal((3.0, 3.0, 3.0, 1.0)))) is None
    assert bev.shape_matrix(Ob(Matrix.Diagonal((-2.0, 2.0, 2.0, 1.0)))) is None
    m = bev.shape_matrix(Ob(Matrix.Diagonal((-1.0, 1.0, 6.0, 1.0))))
    assert m is not None and m.determinant() > 0.0
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    before = [v.co.copy() for v in bm.verts]
    with bev.world_shape(bm, Ob(Matrix.Diagonal((1.0, 1.0, 6.0, 1.0)))) as shaped:
        assert shaped and max(abs(v.co.z) for v in bm.verts) > 2.9
    assert all((v.co - p).length < 1e-6 for v, p in zip(bm.verts, before))
    bm.free()
