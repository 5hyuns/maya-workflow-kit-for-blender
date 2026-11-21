"""#418: Taper / Twist of the face extrusion and the Extrude option box's Curve settings, like Maya: Taper and Twist
shape an extrusion that follows a curve (Curve: Selected = the first selected curve, Curve: Generated = a straight
curve the kit makes along the faces' normal); without a curve they change nothing; the faces taper / twist as one
piece about the centre of all of them, also with Keep Faces Together off."""

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
    """A mesh of flat quads at z = 0 (``faces_xy`` = [(x0, x1, y0, y1)]), every face selected, in edit mode."""
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


def _edit(ob, curves=()):
    for c in curves:
        c.select_set(True)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select_set(True)
    bmesh.update_edit_mesh(ob.data)


def _curve(name, points):
    c = cmaya.make_cv_curve(bpy.context, points, 1)
    c.name = name
    c.select_set(False)
    return c


def _rings(ob):
    """{height: sorted (x, y) of the vertices at that height}."""
    bm = bmesh.from_edit_mesh(ob.data)
    out = {}
    for v in bm.verts:
        out.setdefault(round(v.co.z, 4) + 0.0, []).append((round(v.co.x, 4) + 0.0, round(v.co.y, 4) + 0.0))
    return {z: sorted(set(p)) for z, p in out.items()}


def test_generated_path_maths():
    pts = [Vector((x, y, 1.0)) for x in (-1.0, 1.0) for y in (-1.0, 1.0)]
    cvs = ec.generated_points(pts, [Vector((0, 0, 1))])
    assert (cvs[0] - Vector((0, 0, 1))).length < 1e-5, cvs[0]
    assert abs((cvs[3] - cvs[0]).length - 0.9 * math.sqrt(8.0)) < 1e-5
    assert all(abs(c.x) < 1e-5 and abs(c.y) < 1e-5 for c in cvs)
    assert abs((cvs[1] - cvs[0]).length - (cvs[3] - cvs[0]).length / 3.0) < 1e-5
    # normals that cancel out: along world X
    cvs = ec.generated_points(pts, [Vector((0, 0, 1)), Vector((0, 0, -1))])
    assert (cvs[3] - cvs[0]).normalized().dot(Vector((1, 0, 0))) > 0.9999


def test_generated_curve_taper_and_twist():
    _reset()
    ob = _mesh([(-1, 1, -1, 1)])
    _edit(ob)
    assert bpy.ops.allset.extrude(curve='GENERATED', divisions=2, taper=0.5) == {'FINISHED'}
    path = bpy.data.objects.get("polyExtrudeFace1Curve")
    assert path is not None and path.type == 'CURVE', [o.name for o in bpy.data.objects]
    assert path.data.name == "polyExtrudeFace1CurveShape"
    assert bpy.context.view_layer.objects.active is ob and ob.mode == 'EDIT'
    rec = extrude.current(ob)
    assert rec is not None and rec.spec is ec.SPEC and rec.params["curve"] == path.name
    top = 0.9 * math.sqrt(8.0)
    rings = _rings(ob)
    assert sorted(rings) == [0.0, round(top / 2, 4), round(top, 4)], sorted(rings)
    assert rings[round(top / 2, 4)] == [(-0.75, -0.75), (-0.75, 0.75), (0.75, -0.75), (0.75, 0.75)]
    assert rings[round(top, 4)] == [(-0.5, -0.5), (-0.5, 0.5), (0.5, -0.5), (0.5, 0.5)]
    # Twist turns the steps evenly, right-handed about the path (here +Z)
    assert extrude.set_params(bpy.context, taper=1.0, twist=90.0) == {'FINISHED'}
    mid = _rings(ob)[round(top / 2, 4)]
    r = round(math.sqrt(2.0), 4)
    assert mid == sorted([(0.0, -r), (0.0, r), (-r, 0.0), (r, 0.0)]), mid
    bm = bmesh.from_edit_mesh(ob.data)
    assert len([f for f in bm.faces if f.select]) == 1


def test_generated_curve_reused_by_the_same_node():
    _reset()
    ob = _mesh([(-1, 1, -1, 1)])
    _edit(ob)
    assert bpy.ops.allset.extrude(curve='GENERATED') == {'FINISHED'}
    assert bpy.ops.allset.extrude(curve='GENERATED') == {'FINISHED'}
    names = sorted(o.name for o in bpy.data.objects if o.type == 'CURVE')
    assert names == ["polyExtrudeFace1Curve", "polyExtrudeFace2Curve"], names


def test_no_curve_means_no_taper():
    # like Maya: without a curve Taper / Twist change nothing (the plain extrusion)
    _reset()
    ob = _mesh([(-1, 1, -1, 1)])
    _edit(ob)
    assert bpy.ops.allset.extrude(divisions=2, taper=0.5, twist=90.0, local_translate_z=1.0) == {'FINISHED'}
    rec = extrude.current(ob)
    assert rec.spec is extrude.FACE
    rings = _rings(ob)
    assert rings[1.0] == [(-1.0, -1.0), (-1.0, 1.0), (1.0, -1.0), (1.0, 1.0)], rings


def test_curve_none_ignores_a_selected_curve():
    _reset()
    crv = _curve("crvA", [(0, 0, 0), (0, 0, 4)])
    ob = _mesh([(-1, 1, -1, 1)])
    _edit(ob, [crv])
    assert bpy.ops.allset.extrude(curve='NONE', taper=0.5) == {'FINISHED'}
    assert extrude.current(ob).spec is extrude.FACE


def test_two_curves_take_the_first_selected():
    # Maya extrudes along the first selected curve only (the kit's pick order)
    order = import_module(kit.MODULE + ".operators.pick_order")
    for first, second in (("crvB", "crvA"), ("crvA", "crvB")):
        _reset()
        crvs = {"crvB": _curve("crvB", [(0, 0, 0), (3, 0, 0)]), "crvA": _curve("crvA", [(0, 0, 0), (0, 0, 4)])}
        ob = _mesh([(-0.5, 0.5, -0.5, 0.5)])
        vl = bpy.context.view_layer
        for o in bpy.context.scene.objects:
            o.select_set(False)
        order._sync(bpy.context.scene, vl)
        for name in (first, second):
            crvs[name].select_set(True)
            order._sync(bpy.context.scene, vl)
        _edit(ob)
        assert bpy.ops.allset.extrude() == {'FINISHED'}
        rec = extrude.current(ob)
        assert rec.spec is ec.SPEC and rec.params["curve"] == first, (first, rec.params)


def test_keep_faces_apart_taper_about_all_faces():
    # Keep Faces Together off along a curve: the faces still taper about the centre of all of them (only their
    # vertices are apart)
    for together in (True, False):
        _reset()
        crv = _curve("crv", [(0, 0, 0), (0, 0, 4)])
        ob = _mesh([(-1, 0, -1, 1), (0, 1, -1, 1)])
        _edit(ob, [crv])
        assert bpy.ops.allset.extrude(divisions=2, taper=0.5, keep_faces_together=together) == {'FINISHED'}
        rings = _rings(ob)
        assert rings[4.0] == [(-0.5, -0.5), (-0.5, 0.5), (0.0, -0.5), (0.0, 0.5), (0.5, -0.5), (0.5, 0.5)], \
            (together, rings[4.0])
        assert rings[2.0] == [(-0.75, -0.75), (-0.75, 0.75), (0.0, -0.75), (0.0, 0.75), (0.75, -0.75), (0.75, 0.75)]
        bm = bmesh.from_edit_mesh(ob.data)
        assert len([v for v in bm.verts if abs(v.co.z - 4.0) < 1e-6]) == (6 if together else 8)


def test_option_box_curve_rows():
    window = ow._BY_KEY["extrude"]
    names = [f.name for f in window.fields]
    assert names == ["divisions", "offset", "thickness", "curve", "taper", "twist"], names
    d = window.defaults()
    assert (d["curve"], d["taper"], d["twist"], d["divisions"]) == ("Selected", 1.0, 0.0, 1)
    curve = next(f for f in window.fields if f.name == "curve")
    assert tuple(curve.items) == ("None", "Selected", "Generated")
    assert window.enabled(dict(d, curve="None"), "taper") is False
    assert window.enabled(dict(d, curve="None"), "twist") is False
    assert window.enabled(dict(d, curve="None"), "divisions") is True
    assert window.enabled(dict(d, curve="Generated"), "taper") is True
    assert "Curve" not in window.missing and "Taper" not in window.missing


def test_option_box_runs_the_generated_curve():
    _reset()
    ob = _mesh([(-1, 1, -1, 1)])
    _edit(ob)
    res = ow.run(ow._BY_KEY["extrude"], bpy.context, {"curve": "Generated", "taper": 0.5, "divisions": 2})
    assert res == {'FINISHED'}, res
    rec = extrude.current(ob)
    assert rec.spec is ec.SPEC and rec.params["taper"] == 0.5 and rec.params["divisions"] == 2, rec.params


def test_channel_box_order():
    # Maya's order of the node's attributes
    assert ec.SPEC.fields == ("local_translate_z", "offset", "keep_faces_together", "divisions", "twist",
                              "taper", "thickness")
    assert set(ec.SPEC.view_fields) == set(ec.SPEC.fields)


def test_twist_is_right_handed_about_the_path():
    _reset()
    ob = _mesh([(-1, 1, -0.5, 0.5)])
    _edit(ob)
    assert bpy.ops.allset.extrude(curve='GENERATED', twist=45.0) == {'FINISHED'}
    c, s = math.cos(math.radians(45.0)), math.sin(math.radians(45.0))
    want = sorted((round(x * c - y * s, 4) + 0.0, round(x * s + y * c, 4) + 0.0)
                  for x in (-1.0, 1.0) for y in (-0.5, 0.5))
    top = max(_rings(ob))
    assert _rings(ob)[top] == want, (_rings(ob)[top], want)
