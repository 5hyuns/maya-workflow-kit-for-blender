"""Issues #457 / #461: Deform > Nonlinear > Twist, Squash, Flare, Sine and Wave work like Maya in the handle's space.

A column of points along the handle (handle at the origin, unit scale): Twist turns from Start Angle at Low Bound to
End Angle at High Bound, Flare scales from the start values to the end values, Squash stretches the length between
the bounds and narrows the sides most at Max Expand Pos, and bounds beyond -1 / 1 spread the effect over a longer
range. Sine moves the points sideways along a sine wave of the length, Wave moves them along the handle in rings
around it. Envelope blends the result in; the Channel Box rows set the node's inputs; a lattice keeps a Simple Deform.
"""

import math
from importlib import import_module

import bpy

import kit

deformers = import_module(kit.MODULE + ".operators.deformers")
nl = import_module(kit.MODULE + ".operators.nonlinear_nodes")
history = import_module(kit.MODULE + ".operators.history")

# Maya-space points (x, y, z): y along the handle
PTS = [(0.5, y / 4.0, 0.3) for y in range(-16, 17)] + [(r / 4.0, 0.0, 0.0) for r in range(0, 9)]


def _fresh():
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.lattices):
        for d in list(coll):
            coll.remove(d)


def _make(kind, **values):
    """``kind`` on the column with the handle at the origin, unit scale; ``values`` = {Maya attribute: value}
    (angles in degrees, like the Channel Box)."""
    _fresh()
    me = bpy.data.meshes.new("pCubeShape1")
    me.from_pydata([(x, -z, y) for x, y, z in PTS], [], [])
    ob = bpy.data.objects.new("pCube1", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    assert bpy.ops.allset.deformer(kind=kind.upper()) == {'FINISHED'}
    md = ob.modifiers[f"{kind}1"]
    assert md.type == 'NODES' and nl.kind_of(md) == kind, (md.type, kind)
    h = deformers.handle_of(md)
    assert h is not None and h.name == f"{kind}1Handle"
    h.location, h.rotation_euler, h.scale = (0, 0, 0), (0, 0, 0), (1, 1, 1)
    for key, v in values.items():
        a = deformers.attr(md, "maya:" + key)
        assert a is not None, key
        a.set(md, math.radians(v) if a.kind == "ROTATION" else v)
    return ob, md


def _result(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    return [(v.co.x, v.co.z, -v.co.y) for v in ev.vertices]


def _close(a, b, what, tol=1e-4):
    assert all(abs(p - q) < tol for p, q in zip(a, b)), (what, a, b)


def _turn(p, deg):
    a = math.radians(deg)
    x, y, z = p
    return (x * math.cos(a) - z * math.sin(a), y, x * math.sin(a) + z * math.cos(a))


def test_twist_from_low_to_high():
    ob, md = _make("twist", endAngle=90.0)
    out = _result(ob)
    for p, q in zip(PTS[:33], out):
        t = min(max(p[1], -1.0), 1.0)
        _close(q, _turn(p, 90.0 * (t + 1.0) / 2.0), p)
    _close(out[0], PTS[0], "below Low Bound: still")
    _close(out[32], _turn(PTS[32], 90.0), "above High Bound: End Angle")
    ob, md = _make("twist", startAngle=30.0, endAngle=90.0, highBound=5.0)
    out = _result(ob)
    for p, q in zip(PTS[:33], out):
        _close(q, _turn(p, 30.0 + 60.0 * (max(p[1], -1.0) + 1.0) / 6.0), p)
    assert abs(deformers.attr(md, "maya:highBound").get(md) - 5.0) < 1e-6
    deformers.attr(md, "maya:lowBound").set(md, 2.0)
    assert deformers.attr(md, "maya:lowBound").get(md) == 0.0, "Low Bound stays at 0 or below"


def test_flare_from_start_to_end():
    ob, md = _make("flare", endFlareX=2.0, endFlareZ=3.0)
    out = _result(ob)
    for p, q in zip(PTS[:33], out):
        u = (min(max(p[1], -1.0), 1.0) + 1.0) / 2.0
        _close(q, (p[0] * (1 + u), p[1], p[2] * (1 + 2 * u)), p)
    _close(out[0], PTS[0], "the bottom keeps its size")
    ob, md = _make("flare", curve=0.5)
    out = _result(ob)
    mid = PTS.index((0.5, 0.0, 0.3))
    _close(out[mid], (0.75, 0.0, 0.45), "Curve widens the middle")


def test_squash_stretches_between_the_bounds():
    ob, md = _make("squash", factor=0.5)
    out = _result(ob)
    for p, q in zip(PTS[:33], out):
        t = min(max(p[1], -1.0), 1.0)
        assert abs(q[1] - (p[1] + 0.5 * t)) < 1e-4, (p, q)          # 1.5 times as long, the ends move with it
    mid = PTS.index((0.5, 0.0, 0.3))
    side = out[mid][0] / 0.5
    assert abs(side - 1.0 / (1.0 + 2.0 * (math.sqrt(1.5) - 1.0))) < 1e-4, side
    assert abs(out[0][0] - 0.5) < 1e-6 and abs(out[32][0] - 0.5) < 1e-6, "beyond the bounds: no narrowing"
    ob, md = _make("squash", factor=-0.5, maxExpandPos=0.25)
    out = _result(ob)
    widths = [q[0] for q in out[12:21]]           # y from -1 to 1
    assert widths.index(max(widths)) == 2, widths  # widest at a quarter of the way up (y = -0.5)
    assert abs(out[16][1] - 0.0) < 1e-6 and abs(out[20][1] - 1.0 / 1.5) < 1e-4, "squashed to 1 / 1.5"
    ob, md = _make("squash", factor=0.5, envelope=2.0)
    _close(_result(ob)[20], (0.5, 1.5, 0.3), "Envelope works up to 1")


def test_sine_moves_points_sideways():
    ob, md = _make("sine", amplitude=0.3)
    out = _result(ob)
    for p, q in zip(PTS[:33], out):
        t = min(max(p[1], -1.0), 1.0)
        _close(q, (p[0] + 0.3 * math.sin(math.pi * t), p[1], p[2]), p)
    ob, md = _make("sine", amplitude=0.3, wavelength=1.0, offset=0.25, dropoff=1.0, highBound=3.0)
    out = _result(ob)
    for p, q in zip(PTS[:33], out):
        t = min(max(p[1], -1.0), 3.0)
        k = 1.0 - abs(t) / 3.0
        _close(q, (p[0] + 0.3 * k * math.sin(2 * math.pi * (t + 0.25)), p[1], p[2]), p)


def test_wave_moves_points_in_rings():
    ob, md = _make("wave", amplitude=0.2)
    out = _result(ob)
    for p, q in zip(PTS[33:], out[33:]):
        r = min(p[0], 1.0)
        _close(q, (p[0], 0.2 * math.cos(2 * math.pi * r), 0.0), p)
    ob, md = _make("wave", amplitude=0.2, wavelength=0.5, minRadius=0.25, maxRadius=1.5, dropoff=0.5)
    out = _result(ob)
    for p, q in zip(PTS[33:], out[33:]):
        r = min(max(p[0], 0.25), 1.5)
        k = 1.0 - 0.5 * (r - 0.25) / 1.25
        _close(q, (p[0], 0.2 * k * math.cos(2 * math.pi * (r - 0.25) / 0.5), 0.0), p)


def test_envelope_weights_and_delete_history():
    ob, md = _make("twist", endAngle=90.0, envelope=0.5)
    out = _result(ob)
    full = _turn(PTS[32], 90.0)
    _close(out[32], tuple((a + b) / 2 for a, b in zip(PTS[32], full)), "half the way")
    vg = ob.vertex_groups["twist1"]
    vg.add([32], 0.0, 'REPLACE')
    ob.data.update()
    _close(_result(ob)[32], PTS[32], "weight 0: still")
    rows = [a.key for a in deformers.attrs(md)]
    assert rows == ["envelope", "startAngle", "endAngle", "lowBound", "highBound"], rows
    assert history.is_deformer(md), "Delete Non-Deformer History keeps it"
    assert deformers.drives(md, deformers.handle_of(md))


def test_option_window_values_and_lattice():
    _fresh()
    me = bpy.data.meshes.new("pCubeShape1")
    me.from_pydata([(x, -z, y) for x, y, z in PTS], [], [])
    ob = bpy.data.objects.new("pCube1", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    deformers.create(bpy.context, 'TWIST', {"end_angle": 45.0, "low": -2.0, "high": 3.0})
    md = ob.modifiers["twist1"]
    assert abs(deformers.attr(md, "maya:endAngle").get(md) - math.radians(45.0)) < 1e-6
    assert deformers.attr(md, "maya:lowBound").get(md) == -2.0 and deformers.attr(md, "maya:highBound").get(md) == 3.0
    # a lattice: no Geometry Nodes there, a Simple Deform with the old rows
    _fresh()
    lat = bpy.data.objects.new("ffd1Lattice", bpy.data.lattices.new("ffd1LatticeShape"))
    bpy.context.scene.collection.objects.link(lat)
    lat.select_set(True)
    bpy.context.view_layer.objects.active = lat
    assert bpy.ops.allset.deformer(kind='SQUASH') == {'FINISHED'}
    md = lat.modifiers["squash1"]
    assert md.type == 'SIMPLE_DEFORM' and deformers.base_of(md) == "squash"
    assert [a.key for a in deformers.attrs(md)] == ["factor", "lowBound", "highBound"]
