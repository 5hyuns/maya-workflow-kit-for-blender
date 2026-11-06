"""#321: Edit Mesh > Extrude with faces and a curve selected extrudes the faces along the curve, like Maya: step k of
Divisions N puts the faces' centre on the curve point at parameter k / N (even in parameter, not in length), at the
curve's place in the world; each step faces along the chord from the previous centre; Taper and Twist grow
linearly with k / N; the node stays editable (polyExtrudeFace in Channel Box INPUTS)."""

import math
from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit

extrude = import_module(kit.MODULE + ".operators.extrude")
ec = import_module(kit.MODULE + ".operators.extrude_curve")
cmaya = import_module(kit.MODULE + ".operators.curves_maya")


def _scene(curve_points, degree=1):
    """A 1 x 1 plane at the origin (normal +Z) in edit mode, its face selected, and a selected curve."""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    extrude.clear()
    for k in [k for k in bpy.context.scene.keys() if k.startswith("allset_poly")]:
        del bpy.context.scene[k]
    curve = cmaya.make_cv_curve(bpy.context, curve_points, degree)
    bpy.ops.mesh.primitive_plane_add(size=1)
    plane = bpy.context.active_object
    curve.select_set(True)
    plane.select_set(True)
    bpy.context.view_layer.objects.active = plane
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(plane.data)
    for f in bm.faces:
        f.select_set(True)
    bmesh.update_edit_mesh(plane.data)
    return plane, curve


def _cap(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    faces = [f for f in bm.faces if f.select]
    assert len(faces) == 1, len(faces)
    f = faces[0]
    return f.calc_center_median(), f.normal.copy(), [v.co.copy() for v in f.verts]


def _level_centres(ob):
    """Centres of the vertex rings by height (the side rings of a straight extrusion along Z)."""
    bm = bmesh.from_edit_mesh(ob.data)
    by_z = {}
    for v in bm.verts:
        by_z.setdefault(round(v.co.z, 4), []).append(v.co.copy())
    return sorted(by_z)


def test_parameter_uniform_steps():
    plane, _curve = _scene([(0, 0, 0), (0, 0, 1), (0, 0, 4)])
    assert bpy.ops.allset.extrude(divisions=5) == {'FINISHED'}
    assert _level_centres(plane) == [0.0, 0.4, 0.8, 1.6, 2.8, 4.0], _level_centres(plane)
    bm = bmesh.from_edit_mesh(plane.data)
    assert len(bm.verts) == 24
    rec = extrude.current(plane)
    assert rec is not None and rec.spec is ec.SPEC and rec.name == "polyExtrudeFace1"
    assert extrude.caps_selected(plane, rec)


def test_default_one_division_goes_to_the_curve_end_facing_the_chord():
    plane, _curve = _scene([(3, 0, 0), (3, 0, 4)])
    assert bpy.ops.allset.extrude() == {'FINISHED'}
    centre, normal, _vs = _cap(plane)
    assert (centre - Vector((3, 0, 4))).length < 1e-5, centre
    assert (normal - Vector((0.6, 0, 0.8))).length < 1e-5, normal


def test_arc_tilts_the_face():
    plane, _curve = _scene([(0, 0, 0), (2, 0, 2)])
    assert bpy.ops.allset.extrude() == {'FINISHED'}
    centre, normal, _vs = _cap(plane)
    assert (centre - Vector((2, 0, 2))).length < 1e-5
    assert (normal - Vector((1, 0, 1)).normalized()).length < 1e-5


def test_taper_and_twist_are_linear_in_k():
    plane, _curve = _scene([(0, 0, 0), (0, 0, 5)])
    assert bpy.ops.allset.extrude(divisions=5) == {'FINISHED'}
    assert extrude.set_params(bpy.context, taper=0.5) == {'FINISHED'}
    _c, _n, vs = _cap(plane)
    assert all(abs(abs(v.x) - 0.25) < 1e-5 and abs(abs(v.y) - 0.25) < 1e-5 for v in vs), vs
    assert extrude.set_params(bpy.context, taper=1.0, twist=90.0) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(plane.data)
    ring = [v.co for v in bm.verts if abs(v.co.z - 1.0) < 1e-5]
    a = math.radians(18.0)
    want = Vector((-0.5 * math.cos(a) - -0.5 * math.sin(a), -0.5 * math.sin(a) + -0.5 * math.cos(a), 1.0))
    assert any((v - want).length < 1e-4 for v in ring), (want, ring)
    assert extrude.current(plane).params["twist"] == 90.0


def test_place_maths():
    """The placement rule alone: k / N of taper and twist, the turn onto the chord."""
    members = [(1, "a", Vector((0.5, 0.5, 0))), (2, "b", Vector((0.5, 0.5, 0)))]
    out = ec.place([(Vector(), Vector((0, 0, 1)), members)], [Vector((0, 0, 1)), Vector((0, 0, 2))], 2, taper=0.0)
    assert (out["a"] - Vector((0.25, 0.25, 1))).length < 1e-9
    assert (out["b"] - Vector((0, 0, 2))).length < 1e-9


def test_without_a_curve_it_is_the_usual_extrusion():
    plane, curve = _scene([(0, 0, 0), (0, 0, 4)])
    curve.select_set(False)
    assert bpy.ops.allset.extrude() == {'FINISHED'}
    assert extrude.current(plane).spec is extrude.FACE


def test_one_face_plane_keeps_its_bottom():
    # like Maya: a lone face extruded along a curve becomes a closed box (bottom, sides, end)
    plane, _curve = _scene([(0, 0, 0), (0, 0, 1), (0, 0, 4)])
    assert bpy.ops.allset.extrude() == {'FINISHED'}
    bm = bmesh.from_edit_mesh(plane.data)
    assert (len(bm.verts), len(bm.edges), len(bm.faces)) == (8, 12, 6), (len(bm.verts), len(bm.edges), len(bm.faces))
    bottom = [f for f in bm.faces if abs(f.calc_center_median().z) < 1e-6]
    assert len(bottom) == 1 and bottom[0].normal.z < -0.99, [tuple(f.normal) for f in bottom]
    assert all(e.is_manifold for e in bm.edges)
    plane, _curve = _scene([(0, 0, 0), (0, 0, 1), (0, 0, 4)])
    assert bpy.ops.allset.extrude(divisions=5) == {'FINISHED'}
    bm = bmesh.from_edit_mesh(plane.data)
    assert (len(bm.verts), len(bm.edges), len(bm.faces)) == (24, 44, 22)
