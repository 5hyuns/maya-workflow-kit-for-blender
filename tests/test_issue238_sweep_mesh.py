"""Create > Sweep Mesh as a live sweepMeshCreator node (#238): the mesh follows the curve and its profile /
interpolation / taper / twist / caps stay editable from the Channel Box INPUTS and the Attribute Editor."""

from importlib import import_module

import bpy
from mathutils import Vector

import kit

sweep = import_module(kit.MODULE + ".operators.sweep_mesh")
deformers = import_module(kit.MODULE + ".operators.deformers")
history = import_module(kit.MODULE + ".operators.history")
cb = import_module(kit.MODULE + ".ui.channel_box")
ae = import_module(kit.MODULE + ".ui.attribute_editor")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.curves):
        for d in list(coll):
            coll.remove(d)


def _select(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _curve(cvs=((0, 0, 0), (3, 0, 0), (6, 0, 0), (9, 0, 0)), name="curve1"):
    """A cubic clamped NURBS curve (one span for 4 CVs), like a kit CV curve."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('NURBS')
    sp.points.add(len(cvs) - 1)
    for p, c in zip(sp.points, cvs):
        p.co = (*c, 1.0)
    sp.order_u = 4
    sp.use_endpoint_u = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    _select(ob)
    return ob


def _sweep(curve):
    _select(curve)
    assert bpy.ops.allset.sweep_mesh() == {'FINISHED'}
    return bpy.context.active_object


def _mesh(ob):
    bpy.context.view_layer.update()
    return ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data


def _counts(ob):
    me = _mesh(ob)
    return len(me.vertices), len(me.polygons)


def test_default_sweep_is_a_live_node():
    _clear()
    curve = _curve()
    ob = _sweep(curve)
    assert ob.name == "sweep1" and ob.data.name == "sweepShape1" and ob.type == 'MESH'
    assert "curve1" in bpy.data.objects                               # the curve is kept
    assert [m.name for m in ob.modifiers] == ["sweepMeshCreator1"]
    md = ob.modifiers[0]
    assert sweep.is_sweep(md) and sweep.get(md, "Curve") == curve
    # 8 sides, EP to EP 5 steps on a one-span curve = 6 rings; no caps
    assert _counts(ob) == (48, 40), _counts(ob)
    assert ob.data.materials[0] is not None                           # lambert1 like every new shape
    # a second sweep numbers on
    ob2 = _sweep(_curve(name="curve2"))
    assert ob2.name == "sweep2" and ob2.modifiers[0].name == "sweepMeshCreator2"


def test_tube_surrounds_the_curve():
    _clear()
    ob = _sweep(_curve())
    me = _mesh(ob)
    for v in me.vertices:
        r = Vector((0.0, v.co.y, v.co.z)).length
        assert abs(r - 1.0) < 1e-4, (tuple(v.co), r)                  # radius 1 Maya unit round the X axis
    xs = sorted({round(v.co.x, 4) for v in me.vertices})
    assert xs[0] == 0.0 and xs[-1] == 9.0 and len(xs) == 6, xs
    # outward normals
    for p in me.polygons:
        c = p.center
        assert p.normal.dot(Vector((0.0, c.y, c.z))) > 0, tuple(p.normal)


def test_interpolation_and_profile_change_topology():
    _clear()
    ob = _sweep(_curve(cvs=((0, 0, 0), (3, 0, 0), (6, 2, 0), (9, 0, 0), (12, 0, 0))))   # 2 spans
    md = ob.modifiers[0]
    assert _counts(ob)[0] == 8 * (2 * 5 + 1)
    sweep.set_(md, "Interpolation Steps", 2)
    assert _counts(ob)[0] == 8 * (2 * 2 + 1)
    sweep.set_(md, "Interpolation Mode", 0)                         # Start to End: steps over the whole curve
    sweep.set_(md, "Interpolation Steps", 7)
    assert _counts(ob)[0] == 8 * 8
    sweep.set_(md, "Poly Sides", 5)
    assert _counts(ob)[0] == 5 * 8
    sweep.set_(md, "Poly Type", 1)                                  # star: inner points between the outer ones
    assert _counts(ob)[0] == 10 * 8
    sweep.set_(md, "Interpolation Mode", 3)                         # Precision 75 -> 9 segments per span
    assert _counts(ob)[0] == 10 * (2 * 9 + 1)
    sweep.set_(md, "Interpolation Mode", 2)                         # Distance: rings closer together = more rings
    sweep.set_(md, "Interpolation Distance", 1.0)
    a = _counts(ob)[0]
    sweep.set_(md, "Interpolation Distance", 0.5)
    assert _counts(ob)[0] > a
    sweep.set_(md, "Interpolation Mode", 1)
    sweep.set_(md, "Interpolation Steps", 5)
    sweep.set_(md, "Poly Type", 0)
    sweep.set_(md, "Poly Sides", 8)
    sweep.set_(md, "Profile Type", 1)                               # rectangle: 4 corners
    assert _counts(ob)[0] == 4 * 11
    sweep.set_(md, "Corner Radius", 0.25)
    sweep.set_(md, "Corner Segments", 3)
    assert _counts(ob)[0] == 4 * 4 * 11
    sweep.set_(md, "Profile Type", 2)                               # line: an open ribbon
    assert _counts(ob) == (2 * 11, 10)
    sweep.set_(md, "Profile Type", 3)                               # arc of 8 segments
    assert _counts(ob)[0] == 9 * 11
    sweep.set_(md, "Profile Type", 4)                               # wave of 16 segments
    assert _counts(ob)[0] == 17 * 11
    sweep.set_(md, "Profile Type", 0)
    sweep.set_(md, "Caps", True)
    assert _counts(ob) == (88, 80 + 2)


def test_scale_taper_twist():
    _clear()
    ob = _sweep(_curve())
    md = ob.modifiers[0]

    def radii(x):
        return [Vector((0.0, v.co.y, v.co.z)).length for v in _mesh(ob).vertices if abs(v.co.x - x) < 1e-4]
    sweep.set_(md, "Scale Profile", 2.0)
    assert all(abs(r - 2.0) < 1e-4 for r in radii(0.0))
    sweep.set_(md, "Taper", 0.5)
    assert all(abs(r - 2.0) < 1e-4 for r in radii(0.0)) and all(abs(r - 1.0) < 1e-4 for r in radii(9.0))
    sweep.set_(md, "Taper", 1.0)
    first = sorted((round(v.co.y, 4), round(v.co.z, 4)) for v in _mesh(ob).vertices if abs(v.co.x - 9.0) < 1e-4)
    sweep.set_(md, "Twist", 45.0 / 2)                               # half a step of the octagon at the end
    turned = sorted((round(v.co.y, 4), round(v.co.z, 4)) for v in _mesh(ob).vertices if abs(v.co.x - 9.0) < 1e-4)
    assert turned != first
    start = sorted((round(v.co.y, 4), round(v.co.z, 4)) for v in _mesh(ob).vertices if abs(v.co.x) < 1e-4)
    sweep.set_(md, "Twist", 0.0)
    assert start == sorted((round(v.co.y, 4), round(v.co.z, 4)) for v in _mesh(ob).vertices if abs(v.co.x) < 1e-4)


def test_curve_edit_updates_the_mesh():
    _clear()
    curve = _curve()
    ob = _sweep(curve)
    curve.data.splines[0].points[3].co = (9.0, 0.0, 4.0, 1.0)
    curve.data.update_tag()
    zs = [v.co.z for v in _mesh(ob).vertices]
    assert max(zs) > 3.0, max(zs)
    curve.location.y = 5.0                                           # moving the curve moves the sweep
    ys = [v.co.y for v in _mesh(ob).vertices]
    assert min(ys) > 3.0, min(ys)


def test_channel_box_inputs_and_attribute_editor():
    _clear()
    ob = _sweep(_curve())
    md = ob.modifiers[0]
    assert deformers.base_of(md) == "sweepMeshCreator" and deformers.node_type(md) == "sweepMeshCreator"
    assert ae.modifier_node(ob, md) == ("sweepMeshCreator1", "sweepMeshCreator")
    assert not history.is_deformer(md)                              # history, not a deformer
    rows = cb._modifier_props(md)
    assert rows == ["maya:" + k for k, *_r in sweep.ATTR_ROWS], rows
    assert cb.input_label(md, "maya:profilePolySides") == "Profile Poly Sides"
    a = deformers.attr(md, "maya:profilePolySides")
    assert a.get(md) == 8
    a.set(md, 6)
    assert sweep.get(md, "Poly Sides") == 6 and _counts(ob)[0] == 36
    deformers.attr(md, "maya:capsEnable").set(md, True)
    assert sweep.get(md, "Caps") is True

    class Layout:
        def __init__(self):
            self.texts = []

        def row(self, **_k):
            return self

        def label(self, text="", **_k):
            self.texts.append(text)

        def separator(self, **_k):
            pass

        def prop(self, _owner, _name, text="", **_k):
            self.texts.append(text)

        def operator(self, _op, text="", **_k):
            self.texts.append(text)

            class Op:
                pass
            return Op()
    lay = Layout()
    assert sweep.draw_ae(lay, md)
    for t in ("Profile Type", "Poly", "Wave", "Profile Poly Sides", "Scale Profile", "Rotate Profile", "Twist",
              "Taper", "Steps", "Caps"):
        assert t in lay.texts, (t, lay.texts)
    assert not sweep.draw_ae(Layout(), ob.modifiers.new("Bevel", 'BEVEL'))


def test_delete_history_and_curve_delete_bake():
    _clear()
    curve = _curve()
    ob = _sweep(curve)
    n = _counts(ob)
    history.delete_history(bpy.context, [ob])
    assert not ob.modifiers and (len(ob.data.vertices), len(ob.data.polygons)) == n
    ob2 = _sweep(curve)
    _select(curve)
    assert bpy.ops.allset.delete() == {'FINISHED'}
    assert "curve1" not in bpy.data.objects
    ob2 = bpy.data.objects["sweep2"]
    assert not ob2.modifiers and len(ob2.data.vertices) == n[0]


def test_construction_history_off_bakes():
    _clear()
    wm = bpy.context.window_manager
    old = wm.allset_construction_history
    wm.allset_construction_history = False
    try:
        ob = _sweep(_curve())
        assert not ob.modifiers and len(ob.data.vertices) == 48
    finally:
        wm.allset_construction_history = old


def test_one_undo_step():
    _clear()
    curve = _curve()
    _select(curve)
    bpy.ops.ed.undo_push(message="before")
    assert bpy.ops.allset.sweep_mesh('EXEC_DEFAULT', True) == {'FINISHED'}
    assert "sweep1" in bpy.data.objects
    bpy.ops.ed.undo()
    assert "sweep1" not in bpy.data.objects and "curve1" in bpy.data.objects


def test_disable_is_clean():
    assert "sweepMeshCreator" in deformers.BASES
    kit.disable()
    try:
        d = import_module(kit.MODULE + ".operators.deformers")
        assert "sweepMeshCreator" not in d.BASES and "sweepMeshCreator" not in d.ATTRS
    finally:
        kit.enable()
    assert "sweepMeshCreator" in import_module(kit.MODULE + ".operators.deformers").BASES
