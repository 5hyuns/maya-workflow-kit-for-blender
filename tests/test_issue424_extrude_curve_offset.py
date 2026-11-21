"""#424: Offset of the extrusion along a curve, like Maya: step k of Divisions N moves the faces' border edges
Offset x k / N into the faces (a negative Offset grows them), after Taper scales the step; the move stays in the
faces' first plane (Twist and the turn onto the path don't turn it). Keep Faces Together on insets only the border of
the selection, off every face on its own. The Extrude option box's Offset goes along a curve too, and the node shows
Offset in the Channel Box and the In-View Editor."""

import math
from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit

extrude = import_module(kit.MODULE + ".operators.extrude")
ec = import_module(kit.MODULE + ".operators.extrude_curve")
cmaya = import_module(kit.MODULE + ".operators.curves_maya")
ow = import_module(kit.MODULE + ".operators.option_windows")


def _reset():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for cu in list(bpy.data.curves):
        bpy.data.curves.remove(cu)
    extrude.clear()
    for k in [k for k in bpy.context.scene.keys() if k.startswith("allset_poly")]:
        del bpy.context.scene[k]


def _mesh(faces_xy):
    """Flat quads at z = 0 (``faces_xy`` = [(x0, x1, y0, y1)])."""
    me = bpy.data.meshes.new("m")
    bm = bmesh.new()
    verts = {}

    def v(x, y):
        if (x, y) not in verts:
            verts[(x, y)] = bm.verts.new((x, y, 0.0))
        return verts[(x, y)]
    for x0, x1, y0, y1 in faces_xy:
        bm.faces.new((v(x0, y0), v(x1, y0), v(x1, y1), v(x0, y1)))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("mesh", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _curve(points):
    c = cmaya.make_cv_curve(bpy.context, points, 1)
    c.name = "crv"
    c.select_set(True)
    return c


def _edit(ob):
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(True)
    bmesh.update_edit_mesh(ob.data)


def _scene(faces_xy=((-1, 1, -1, 1),), path=((0, 0, 0), (0, 0, 4))):
    _reset()
    _curve(list(path))
    ob = _mesh(list(faces_xy))
    _edit(ob)
    return ob


def _rings(ob):
    """{height: sorted (x, y) of the vertices at that height}."""
    bm = bmesh.from_edit_mesh(ob.data)
    out = {}
    for v in bm.verts:
        out.setdefault(round(v.co.z, 4) + 0.0, []).append((round(v.co.x, 4) + 0.0, round(v.co.y, 4) + 0.0))
    return {z: sorted(set(p)) for z, p in out.items()}


def _square(h):
    return sorted((round(x, 4) + 0.0, round(y, 4) + 0.0) for x in (-h, h) for y in (-h, h))


def _coords(ob):
    return [v.co.copy() for v in bmesh.from_edit_mesh(ob.data).verts]


def test_offset_steps_along_the_curve():
    ob = _scene()
    assert bpy.ops.allset.extrude(divisions=4, offset=0.2) == {'FINISHED'}
    rec = extrude.current(ob)
    assert rec.spec is ec.SPEC and abs(rec.params["offset"] - 0.2) < 1e-6, rec.params
    rings = _rings(ob)
    for k in range(1, 5):
        assert rings[float(k)] == _square(1.0 - 0.2 * k / 4), (k, rings[float(k)])
    # a negative Offset grows the faces
    assert extrude.set_params(bpy.context, offset=-0.3, divisions=2) == {'FINISHED'}
    rings = _rings(ob)
    assert rings[2.0] == _square(1.15) and rings[4.0] == _square(1.3), rings


def test_offset_after_the_taper():
    ob = _scene()
    assert bpy.ops.allset.extrude(divisions=2, taper=0.5, offset=0.2) == {'FINISHED'}
    rings = _rings(ob)
    assert rings[2.0] == _square(0.75 - 0.1), rings[2.0]
    assert rings[4.0] == _square(0.5 - 0.2), rings[4.0]


def _offset_moves(ob, **values):
    """Each vertex's move when Offset goes from 0 to 0.2 on the last extrusion (same topology)."""
    assert extrude.set_params(bpy.context, offset=0.0, **values) == {'FINISHED'}
    before = _coords(ob)
    assert extrude.set_params(bpy.context, offset=0.2, **values) == {'FINISHED'}
    return [b - a for a, b in zip(before, _coords(ob))], _coords(ob)


def _check_first_plane(ob, moves, after):
    """Every move lies in the faces' first plane (z = 0) and points from the vertex's step centre inwards."""
    for d, co in zip(moves, after):
        assert abs(d.z) < 1e-6, d
        if d.length > 1e-9:
            assert abs(abs(d.x) - abs(d.y)) < 1e-6, d       # a square's corner moves along its diagonal


def test_offset_is_not_twisted():
    ob = _scene()
    assert bpy.ops.allset.extrude(divisions=2) == {'FINISHED'}
    moves, after = _offset_moves(ob, twist=90.0)
    _check_first_plane(ob, moves, after)
    # the end corner of (-1, -1) turns to (1, -1) and moves by its own inward offset (+0.2, +0.2)
    want = Vector((1.2, -0.8, 4.0))
    assert any((co - want).length < 1e-4 for co in after), after
    assert max(d.length for d in moves) - math.sqrt(2.0) * 0.2 < 1e-6


def test_offset_is_not_turned_with_the_path():
    ob = _scene(path=((0, 0, 0), (0, 0, 2), (2, 0, 2)))
    assert bpy.ops.allset.extrude(divisions=2) == {'FINISHED'}
    moves, after = _offset_moves(ob)
    _check_first_plane(ob, moves, after)
    # the end step faces +X; its corners still move inside the first (XY) plane
    end = [co for co, d in zip(after, moves) if abs(co.x - 2.0) < 1.0 and d.length > 1e-9]
    assert end, after


def test_keep_faces_together_insets_the_border_only():
    for together, middle in ((True, (0.0, 0.0)), (False, (0.1, 0.2))):
        ob = _scene(faces_xy=((-1, 0, -1, 1), (0, 1, -1, 1)))
        assert bpy.ops.allset.extrude(divisions=2, offset=0.2, keep_faces_together=together) == {'FINISHED'}
        rings = _rings(ob)
        for z, m, o in ((2.0, middle[0], 0.1), (4.0, middle[1], 0.2)):
            xs = sorted({x for x, _y in rings[z]})
            ys = sorted({y for _x, y in rings[z]})
            want_x = sorted({round(-1.0 + o, 4), round(1.0 - o, 4), round(-m, 4) + 0.0, round(m, 4) + 0.0})
            assert xs == want_x, (together, z, xs, want_x)
            assert ys == [round(-1.0 + o, 4), round(1.0 - o, 4)], (together, z, ys)


def test_option_box_passes_offset_along_a_curve():
    for curve in ("Selected", "Generated"):
        ob = _scene()
        res = ow.run(ow._BY_KEY["extrude"], bpy.context, {"curve": curve, "offset": 0.2, "divisions": 2})
        assert res == {'FINISHED'}, res
        rec = extrude.current(ob)
        assert rec.spec is ec.SPEC and abs(rec.params["offset"] - 0.2) < 1e-6, (curve, rec.params)


def test_offset_rows():
    # Channel Box in the order of the node's attributes, In-View after Local Translate Z like the plain extrusion
    assert ec.SPEC.fields.index("offset") == ec.SPEC.fields.index("local_translate_z") + 1
    assert ec.SPEC.fields.index("offset") < ec.SPEC.fields.index("keep_faces_together")
    assert ec.SPEC.view_fields[:3] == ("thickness", "local_translate_z", "offset"), ec.SPEC.view_fields
    assert ec.SPEC.labels["offset"] == "Offset" and ec.SPEC.defaults["offset"] == 0.0
    props = bpy.ops.allset.extrude_curve_edit.get_rna_type().properties
    assert "offset" in props.keys()
