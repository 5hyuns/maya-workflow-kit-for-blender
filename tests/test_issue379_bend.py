"""Issue #379: Deform > Nonlinear > Bend like Maya.

A plane made flat and bent: the handle is made at the plane's centre, standing upright with a scale of half the
plane's longest side, so it bends nothing until it is turned to lie along the plane (no spin); turned that way,
Curvature 180 (degrees, typed in the Channel Box) rolls the plane into a closed circle whose length is the plane's.
The bend follows Maya's rule in the handle's space (bounds, envelope, weights, a moved / turned / scaled handle),
the bounds take values beyond the object (Low Bound up to 0, High Bound from 0), the handle draws its straight line,
its bent line and the line towards the bend, Delete History takes the handle with the node, and a lattice gets a
Simple Deform that bends the same way."""

import math
from importlib import import_module

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

import kit

cb = import_module(kit.MODULE + ".ui.channel_box")
deformers = import_module(kit.MODULE + ".operators.deformers")
bend = import_module(kit.MODULE + ".operators.bend_deformer")
handles = import_module(kit.MODULE + ".ui.bend_handles")
history = import_module(kit.MODULE + ".operators.history")
ow = import_module(kit.MODULE + ".operators.option_windows")


def _fresh():
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.lattices, bpy.data.actions):
        for d in list(coll):
            coll.remove(d)
    cb.reset_open()
    cb.set_selected_channels([])
    bpy.context.scene.frame_set(1)


def _select(*obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _plane(size_x=4.0, size_y=4.0, cuts=31):
    """A flat plane on the ground (Blender XY) with many points along X."""
    me = bpy.data.meshes.new("pPlaneShape1")
    bm = bmesh.new()
    n = cuts + 1
    vs = [[bm.verts.new((-size_x / 2 + size_x * i / n, -size_y / 2 + size_y * j, 0.0)) for j in (0, 1)]
          for i in range(n + 1)]
    for i in range(n):
        bm.faces.new((vs[i][0], vs[i + 1][0], vs[i + 1][1], vs[i][1]))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("pPlane1", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    _select(ob)
    return ob


def _column(height=4.0, cuts=40):
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = bpy.context.active_object
    ob.name = "pCube1"
    ob.data.transform(Matrix.Diagonal((0.2, 0.2, height, 1.0)))
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    vertical = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-6]
    bmesh.ops.subdivide_edges(bm, edges=vertical, cuts=cuts - 1)
    bm.to_mesh(ob.data)
    bm.free()
    bpy.context.view_layer.update()
    _select(ob)
    return ob


def _points(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    return co.reshape(-1, 3) @ np.array(ob.matrix_world)[:3, :3].T + np.array(ob.matrix_world)[:3, 3]


def _rest(ob):
    co = np.empty(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3) @ np.array(ob.matrix_world)[:3, :3].T + np.array(ob.matrix_world)[:3, 3]


def _make(ob):
    """Deform > Nonlinear > Bend on ``ob``: (handle, modifier)."""
    _select(ob)
    assert bpy.ops.allset.deformer(kind='BEND') == {'FINISHED'}
    handle = bpy.context.view_layer.objects.active
    md = ob.modifiers["bend1"]
    return handle, md


def _type(lead, md, attr, text):
    """Type ``text`` in the Channel Box row ``attr`` of the bend node (expanded in INPUTS of ``lead``)."""
    _select(lead)
    cb.set_open(lead, cb.mod_node(md))
    bpy.context.scene.allset_cb.rows_sig = ""
    cb.rebuild_rows(bpy.context)
    rows = [r for r in bpy.context.scene.allset_cb.rows if r.kind == "INPUT" and r.name == deformers.PREFIX + attr]
    assert rows, (attr, [(r.kind, r.name) for r in bpy.context.scene.allset_cb.rows])
    rows[0].text = text
    bpy.context.view_layer.update()
    return rows[0]


def _rows(lead, md):
    _select(lead)
    cb.set_open(lead, cb.mod_node(md))
    bpy.context.scene.allset_cb.rows_sig = ""
    cb.rebuild_rows(bpy.context)
    return [(cb.input_label(md, r.name), r.text) for r in bpy.context.scene.allset_cb.rows
            if r.kind == "INPUT" and r.name.startswith(deformers.PREFIX)]


def _expected(rest, handle, curvature, low, high, envelope=1.0, weights=None):
    """The bend rule applied by hand in the handle's space (Maya Y = the handle's local Z)."""
    m = handle.matrix_world
    mi = m.inverted()
    out = []
    for i, p in enumerate(rest):
        q = mi @ Vector(p)
        x2, y2 = bend.bent(q.x, q.z, curvature, low, high)
        w = envelope * (1.0 if weights is None else weights[i])
        b = m @ Vector((x2, q.y, y2))
        out.append(Vector(p) + w * (b - Vector(p)))
    return np.array(out)


# --- the reporter's plane ------------------------------------------------------------------------------------

def test_flat_plane_handle_stands_upright_and_bends_nothing():
    _fresh()
    plane = _plane(4.0, 2.0)
    handle, md = _make(plane)
    assert md.type == 'NODES' and bend.is_bend(md) and bend.get(md, "Handle") == handle
    assert handle.name == "bend1Handle" and bpy.context.active_object == handle          # Maya: the handle selected
    assert (handle.location - Vector((0, 0, 0))).length < 1e-6
    # half the longest side (the plane's 4), not its zero height: the handle is not squashed to nothing
    assert all(abs(s - 2.0) < 1e-6 for s in handle.scale), tuple(handle.scale)
    assert handle.rotation_euler.to_matrix() == Matrix.Identity(3)
    _type(handle, md, "curvature", "180")
    assert abs(bend.get(md, "Curvature") - math.pi) < 1e-6, "Curvature is typed in degrees"
    # every point sits at the handle's height 0: nothing bends, nothing spins
    assert np.abs(_points(plane) - _rest(plane)).max() < 1e-6


def test_curvature_180_rolls_the_plane_into_a_closed_circle():
    _fresh()
    plane = _plane(4.0, 4.0)
    handle, md = _make(plane)
    handle.rotation_euler = Euler((0.0, math.radians(90.0), 0.0))     # the handle's length along the plane's X
    _type(handle, md, "curvature", "180")
    pts = _points(plane)
    rest = _rest(plane)
    ends = [i for i, p in enumerate(rest) if abs(p[0] + 2.0) < 1e-6], [i for i, p in enumerate(rest) if abs(p[0] - 2.0)
                                                                         < 1e-6]
    assert ends[0] and ends[1]
    for a, b in zip(sorted(ends[0], key=lambda i: rest[i][1]), sorted(ends[1], key=lambda i: rest[i][1])):
        assert np.linalg.norm(pts[a] - pts[b]) < 1e-4, ("the two ends meet", pts[a], pts[b])
    # a circle of the plane's length: radius 4 / 2pi around a centre on the handle's X side
    r = 4.0 / (2 * math.pi)
    side = handle.matrix_world.to_3x3() @ Vector((1, 0, 0))
    centre = handle.matrix_world.translation + side.normalized() * r
    for p, q in zip(pts, rest):
        d = Vector(p) - centre
        d.y = 0.0
        assert abs(d.length - r) < 1e-4, (q, p, d.length, r)
    # Curvature 90: half the circle
    _type(handle, md, "curvature", "90")
    pts = _points(plane)
    span = max(p[0] for p in pts) - min(p[0] for p in pts)
    assert abs(span - 2 * 4.0 / math.pi) < 1e-3, span
    # a positive Curvature bends towards the handle's +X (here world -Z), a negative one away
    assert min(p[2] for p in pts) < -1.0 and max(p[2] for p in pts) < 1e-6
    _type(handle, md, "curvature", "-90")
    pts = _points(plane)
    assert max(p[2] for p in pts) > 1.0 and min(p[2] for p in pts) > -1e-6


def test_the_bend_follows_its_rule_for_any_handle_bounds_envelope_and_weights():
    _fresh()
    col = _column()
    col.location = (0.5, -0.3, 1.0)
    bpy.context.view_layer.update()
    handle, md = _make(col)
    assert all(abs(s - 2.0) < 1e-6 for s in handle.scale)                 # half the column's 4
    rest = _rest(col)
    for curv, low, high, env in ((90.0, -1.0, 1.0, 1.0), (90.0, -0.5, 0.3, 1.0), (-60.0, -2.0, 2.0, 1.0),
                                 (360.0, -1.0, 1.0, 0.5), (45.0, 0.0, 0.8, 1.0)):
        _type(handle, md, "curvature", str(curv))
        _type(handle, md, "lowBound", str(low))
        _type(handle, md, "highBound", str(high))
        _type(handle, md, "envelope", str(env))
        want = _expected(rest, handle, math.radians(curv), low, high, env)
        got = _points(col)
        assert np.abs(got - want).max() < 1e-4, (curv, low, high, env, np.abs(got - want).max())
    # the handle moved, turned and scaled unevenly afterwards
    handle.location = (0.2, 0.1, 0.5)
    handle.rotation_euler = Euler((0.3, -0.2, 0.7))
    handle.scale = (1.0, 0.5, 3.0)
    _type(handle, md, "envelope", "1")
    _type(handle, md, "curvature", "75")
    want = _expected(rest, handle, math.radians(75.0), 0.0, 0.8)
    assert np.abs(_points(col) - want).max() < 1e-4
    # painted weights blend the bend per point (the node's vertex group)
    vg = col.vertex_groups["bend1"]
    w = [0.25 if p[2] > 1.0 else 1.0 for p in rest]
    for i, x in enumerate(w):
        vg.add([i], x, 'REPLACE')
    col.data.update()
    want = _expected(rest, handle, math.radians(75.0), 0.0, 0.8, 1.0, w)
    assert np.abs(_points(col) - want).max() < 1e-4
    assert deformers.paint_group(col, "nonLinear") == "bend1"


def test_channel_box_rows_and_limits_like_maya():
    _fresh()
    col = _column()
    handle, md = _make(col)
    assert _rows(handle, md) == [("Envelope", "1"), ("Curvature", "0"), ("Low Bound", "-1"), ("High Bound", "1")], \
        _rows(handle, md)
    _type(handle, md, "lowBound", "-3")          # beyond the object: kept (no fraction of the object's extent)
    assert abs(bend.get(md, "Low Bound") + 3.0) < 1e-6
    _type(handle, md, "lowBound", "0.5")         # Maya: Low Bound is at most 0
    assert bend.get(md, "Low Bound") == 0.0
    _type(handle, md, "highBound", "-1")         # High Bound at least 0
    assert bend.get(md, "High Bound") == 0.0
    _type(handle, md, "envelope", "3")           # Envelope -2 .. 2
    assert bend.get(md, "Envelope") == 2.0
    _type(handle, md, "curvature", "720")        # Curvature has no limit
    assert abs(bend.get(md, "Curvature") - 4 * math.pi) < 1e-5
    rows = dict(_rows(col, md))                  # the mesh's INPUTS show the same node
    assert rows["Curvature"] == "720" and rows["High Bound"] == "0", rows


def test_option_window_curvature_in_degrees():
    _fresh()
    col = _column()
    w = ow._BY_KEY["deform_bend"]
    f = next(x for x in w.fields if x.name == "curvature")
    assert (f.lo, f.hi) == (-180.0, 180.0), (f.lo, f.hi)
    res = ow.run(w, bpy.context, {"curvature": 90.0, "low": -0.5, "high": 1.0})
    assert not isinstance(res, str), res
    md = col.modifiers["bend1"]
    assert abs(bend.get(md, "Curvature") - math.pi / 2) < 1e-6 and abs(bend.get(md, "Low Bound") + 0.5) < 1e-6


# --- the handle's drawing ----------------------------------------------------------------------------------

def test_handle_draws_its_line_bent_line_and_bend_side():
    _fresh()
    col = _column()
    handle, md = _make(col)
    _type(handle, md, "curvature", "90")
    _type(handle, md, "lowBound", "-0.5")
    _type(handle, md, "highBound", "0.3")
    segs = handles.segments(bpy.context.view_layer)
    assert segs, "the handle draws"
    m = handle.matrix_world
    straight = segs[0]
    assert (straight[0] - m @ Vector((0, 0, -0.5))).length < 1e-6 and (straight[1] - m @ Vector((0, 0, 0.3))).length \
        < 1e-6, "the straight line runs from Low Bound to High Bound along the handle"
    assert straight[2] == handles.LEAD, "the lead handle draws green"
    tick = segs[-1]
    c = math.pi / 2
    assert (tick[0] - m.translation).length < 1e-6
    assert (tick[1] - m @ Vector((0.2 * c, 0, 0))).length < 1e-6, "towards the bend's side, 0.2 per radian"
    arc = segs[1:-1]
    assert (arc[0][0] - m @ bend.to_kit(*bend.bent(0.0, -0.5, c, -0.5, 0.3))).length < 1e-6
    assert (arc[-1][1] - m @ bend.to_kit(*bend.bent(0.0, 0.3, c, -0.5, 0.3))).length < 1e-6
    # the bent line is where the handle's own axis goes when bent
    for a, b, _c in arc:
        q = m.inverted() @ a
        assert abs(q.y) < 1e-6
    _select(col)
    assert handles.segments(bpy.context.view_layer)[0][2] == handles.DORMANT, "dark blue when not selected"
    # Curvature 0: just the straight line (the bent line on it), no side line
    _type(handle, md, "curvature", "0")
    _select(col)
    segs = handles.segments(bpy.context.view_layer)
    assert all(abs((m.inverted() @ p).x) < 1e-9 for s in segs for p in s[:2])
    handle.hide_set(True)
    assert not handles.segments(bpy.context.view_layer), "a hidden handle draws nothing"


# --- history, other objects, older bends ---------------------------------------------------------------------

def test_delete_history_takes_the_handle():
    _fresh()
    col = _column()
    handle, md = _make(col)
    _type(handle, md, "curvature", "90")
    assert history.is_deformer(md)
    _select(col)
    assert bpy.ops.allset.delete_history() == {'FINISHED'}
    assert "bend1" not in col.modifiers and "bend1Handle" not in bpy.data.objects
    _fresh()
    a, b = _column(), _column()
    a.name, b.name = "pCube1", "pCube2"
    _select(a, b)
    assert bpy.ops.allset.deformer(kind='BEND') == {'FINISHED'}
    assert bend.is_bend(a.modifiers["bend1"]) and bend.is_bend(b.modifiers["bend1"])
    _select(a)
    assert bpy.ops.allset.delete_history() == {'FINISHED'}
    assert "bend1Handle" in bpy.data.objects, "kept while another object's bend still uses it"
    assert deformers.driven_modifiers(bpy.data.objects["bend1Handle"]) == [b.modifiers["bend1"]]


def _lattice_points(lat, evaluated=True):
    dg = bpy.context.evaluated_depsgraph_get()
    src = lat.evaluated_get(dg) if evaluated else lat
    return np.array([tuple(lat.matrix_world @ p.co_deform) for p in src.data.points])


def test_lattice_bend_follows_its_handle_like_maya():
    """A lattice can't take Geometry Nodes: its bend is a Simple Deform whose angle / limits follow the Maya values kept
    on the handle and the handle itself — moved, turned, scaled, keyed — like Maya's bend on lattice points."""
    _fresh()
    bpy.ops.object.add(type='LATTICE')
    lat = bpy.context.active_object
    lat.data.points_w = 9
    lat.scale = (1.0, 1.0, 4.0)
    bpy.context.view_layer.update()
    _select(lat)
    assert bpy.ops.allset.deformer(kind='BEND') == {'FINISHED'}
    handle = bpy.context.view_layer.objects.active
    md = lat.modifiers["bend1"]
    assert md.type == 'SIMPLE_DEFORM' and md.deform_axis == 'Y'
    rest = _lattice_points(lat, evaluated=False)
    _type(handle, md, "curvature", "90")
    assert abs(deformers.sd_bend_values(md)[0] - math.pi / 2) < 1e-6
    assert np.abs(_lattice_points(lat) - _expected(rest, handle, math.pi / 2, -1.0, 1.0)).max() < 1e-4
    assert _rows(handle, md) == [("Curvature", "90"), ("Low Bound", "-1"), ("High Bound", "1")], _rows(handle, md)
    # the handle moved / turned / scaled after the bend was made: the bend follows it (the bounds stay in handle units)
    for loc, rot, scale in (((0.0, 0.0, 0.6), (0.0, 0.0, 0.0), (2.0, 2.0, 2.0)),
                            ((0.1, -0.2, 0.3), (0.2, 0.35, 0.5), (1.5, 1.5, 1.5)),
                            ((0.0, 0.0, -0.4), (0.0, 0.0, 0.0), (1.0, 1.0, 3.0))):
        handle.location, handle.rotation_euler, handle.scale = loc, Euler(rot), scale
        bpy.context.view_layer.update()
        want = _expected(rest, handle, math.pi / 2, -1.0, 1.0)
        assert np.abs(_lattice_points(lat) - want).max() < 1e-4, (loc, rot, scale)
    _type(handle, md, "lowBound", "-0.3")
    _type(handle, md, "highBound", "2.5")          # past the lattice's end: the same as its end
    want = _expected(rest, handle, math.pi / 2, -0.3, 2.5)
    assert np.abs(_lattice_points(lat) - want).max() < 1e-4
    assert dict(_rows(handle, md))["High Bound"] == "2.5"
    # the lattice moved: the bend stays in the handle's space
    lat.location = (0.3, 0.0, 0.2)
    bpy.context.view_layer.update()
    rest = _lattice_points(lat, evaluated=False)
    assert np.abs(_lattice_points(lat) - _expected(rest, handle, math.pi / 2, -0.3, 2.5)).max() < 1e-4
    # keyed Curvature (on the handle, like the node's own attribute) and a keyed handle play back
    sc = bpy.context.scene
    row = _type(handle, md, "curvature", "0")
    key = cb.row_key(row)
    for frame, text in ((1, "0"), (10, "120")):
        sc.frame_set(frame)
        _type(handle, md, "curvature", text)
        cb.set_selected_channels([key])
        assert bpy.ops.allset.cb_key_selected() == {'FINISHED'}
    cb.set_selected_channels([])
    fc = cb.fcurve(handle, key)
    assert fc is not None and fc.id_data == handle.animation_data.action, "keyed on the handle"
    handle.rotation_euler = Euler((0.0, 0.0, 0.0))
    handle.keyframe_insert("rotation_euler", index=1, frame=1)
    handle.rotation_euler = Euler((0.0, 0.6, 0.0))
    handle.keyframe_insert("rotation_euler", index=1, frame=10)
    for frame in (10, 4, 1, 7):
        sc.frame_set(frame)
        c = fc.evaluate(frame)
        assert abs(deformers.sd_bend_values(md)[0] - c) < 1e-5
        want = _expected(rest, handle, c, -0.3, 2.5)
        assert np.abs(_lattice_points(lat) - want).max() < 1e-4, frame
        assert cb.channel_state(handle, key) == ('KEYED' if frame in (1, 10) else 'ANIMATED'), frame
    # the handle draws Maya's lines from the values it keeps
    sc.frame_set(10)
    segs = handles.segments(bpy.context.view_layer)
    tick = segs[-1]
    assert (tick[1] - handle.matrix_world @ Vector((0.2 * math.radians(120.0), 0, 0))).length < 1e-5


def test_surface_bend_follows_its_handle():
    """A NURBS surface: also a Simple Deform kept in step with the handle (angle = Curvature x the bounded length of the
    surface along the handle, limits = the bounds on the surface's extent)."""
    _fresh()
    bpy.ops.surface.primitive_nurbs_surface_surface_add()
    surf = bpy.context.active_object
    surf.scale = (1.0, 1.0, 1.0)
    surf.rotation_euler = Euler((math.radians(90.0), 0.0, 0.0))     # standing: its extent along Z
    bpy.context.view_layer.update()
    _select(surf)
    assert bpy.ops.allset.deformer(kind='BEND') == {'FINISHED'}
    handle = bpy.context.view_layer.objects.active
    md = surf.modifiers["bend1"]
    assert md.type == 'SIMPLE_DEFORM' and md.deform_axis == 'Y'
    _type(handle, md, "curvature", "60")

    def want():
        m = handle.matrix_world.inverted() @ surf.matrix_world
        zs = [(m @ p.co.xyz).z for sp in surf.data.splines for p in sp.points]
        e0, e1 = min(zs), max(zs)
        a, b = max(-1.0, e0), min(1.0, e1)
        return ((a - e0) / (e1 - e0), (b - e0) / (e1 - e0)), math.radians(60.0) * (b - a)

    for loc in ((0.0, 0.0, 0.0), (0.0, 0.0, 0.7), (0.2, 0.0, -0.5)):
        handle.location = loc
        bpy.context.view_layer.update()
        limits, angle = want()
        assert abs(md.angle - angle) < 1e-5 and all(abs(x - y) < 1e-5 for x, y in zip(md.limits, limits)), loc
    # an angle typed in Blender's modifier panel is kept: it becomes the Curvature, and the bend still follows the handle
    a, b = (lambda r: (r[2], r[3]))(deformers._sd_range(md))
    md.angle = 1.0
    bpy.context.view_layer.update()
    assert abs(md.angle - 1.0) < 1e-6
    assert abs(deformers.sd_bend_values(md)[0] - 1.0 / (b - a)) < 1e-5
    curv = deformers.sd_bend_values(md)[0]
    handle.location = (0.0, 0.0, 0.3)
    bpy.context.view_layer.update()
    m = handle.matrix_world.inverted() @ surf.matrix_world
    zs = [(m @ p.co.xyz).z for sp in surf.data.splines for p in sp.points]
    assert abs(md.angle - curv * (min(1.0, max(zs)) - max(-1.0, min(zs)))) < 1e-5


def _curve_points(cu, evaluated=True):
    if evaluated:
        dg = bpy.context.evaluated_depsgraph_get()
        geo = cu.evaluated_get(dg).evaluated_geometry()
        pos = geo.curves.attributes["position"]
        co = [tuple(cu.matrix_world @ Vector(d.vector)) for d in pos.data]
    else:
        co = [tuple(cu.matrix_world @ p.co.xyz) for sp in cu.data.splines for p in sp.points]
    return np.array(co)


def test_curve_bend_moves_its_control_points_like_maya():
    """A curve takes the same Geometry Nodes bend as a mesh: its control points bend by Maya's rule, also after the
    handle moved and turned."""
    _fresh()
    cu_data = bpy.data.curves.new("curveShape1", 'CURVE')
    cu_data.dimensions = '3D'
    sp = cu_data.splines.new('NURBS')
    sp.points.add(8)
    for i, p in enumerate(sp.points):
        p.co = (0.2, 0.1, i * 0.5 - 2.0, 1.0)
    sp.order_u = 4
    cu = bpy.data.objects.new("curve1", cu_data)
    bpy.context.scene.collection.objects.link(cu)
    bpy.context.view_layer.update()
    _select(cu)
    assert bpy.ops.allset.deformer(kind='BEND') == {'FINISHED'}
    handle = bpy.context.view_layer.objects.active
    md = cu.modifiers["bend1"]
    assert bend.is_bend(md) and bend.get(md, "Handle") == handle
    rest = _curve_points(cu, evaluated=False)
    _type(handle, md, "curvature", "90")
    assert np.abs(_curve_points(cu) - _expected(rest, handle, math.pi / 2, -1.0, 1.0)).max() < 1e-4
    handle.location = (-0.1, 0.0, 0.4)
    handle.rotation_euler = Euler((0.0, math.radians(25.0), 0.0))
    bpy.context.view_layer.update()
    assert np.abs(_curve_points(cu) - _expected(rest, handle, math.pi / 2, -1.0, 1.0)).max() < 1e-4


def test_bend_of_earlier_versions_keeps_its_rows():
    _fresh()
    col = _column()
    handle = bpy.data.objects.new("bend1Handle", None)
    bpy.context.scene.collection.objects.link(handle)
    md = col.modifiers.new("bend1", 'SIMPLE_DEFORM')
    md.deform_method, md.deform_axis, md.origin, md.angle = 'BEND', 'Z', handle, 1.2
    assert deformers.base_of(md) == "bend" and deformers.drives(md, handle)
    assert [a.key for a in deformers.attrs(md)] == ["curvature", "lowBound", "highBound"]
    assert abs(deformers.attr(md, deformers.PREFIX + "curvature").get(md) - 1.2) < 1e-6
    assert not handles.segments(bpy.context.view_layer), "no Maya lines for Blender's own angle"


def test_attribute_editor_tab_shows_the_maya_attributes():
    """The bend1 tab of the Attribute Editor draws Envelope, Curvature (degrees), Low Bound and High Bound, not the
    Geometry Nodes modifier's own settings."""
    _fresh()
    col = _column()
    _handle, md = _make(col)

    class Layout:
        def __init__(self):
            self.rows = []

        def prop(self, data, prop, text=""):
            self.rows.append((text, data.bl_rna.properties[prop].subtype if prop in data.bl_rna.properties else None))

    lay = Layout()
    assert bend.draw_ae(lay, md)
    assert [t for t, _s in lay.rows] == ["Envelope", "Curvature", "Low Bound", "High Bound"], lay.rows
    assert dict(lay.rows)["Curvature"] == 'ANGLE', lay.rows
    assert not bend.draw_ae(Layout(), col.modifiers.new("Bevel", 'BEVEL'))


def test_lattice_bend_says_when_it_writes_during_an_update():
    """The handler that keeps a lattice bend in step with its handle writes the Simple Deform's angle / limits during
    a depsgraph update (also on a frame change, while playing): it tells the kit's shared update round first, so the
    kit handlers after it see the lattice change as if each walked the update itself, and a frame change with such a
    bend in the file counts as one where a handler writes. With no lattice / surface bend it writes nothing."""
    us = import_module(kit.MODULE + ".update_summary")
    wire = import_module(kit.MODULE + ".ui.selection_wire")
    key = "operators.bend_deformer:_on_update"
    assert key in us.REPORTERS
    _fresh()
    sc = bpy.context.scene
    sc.frame_set(2)
    assert wire._idle_writer(key, sc, []), "no bend: the frame change handler writes nothing"
    bpy.ops.object.add(type='LATTICE')
    lat = bpy.context.active_object
    lat.data.points_w = 9
    lat.scale = (1.0, 1.0, 4.0)
    bpy.context.view_layer.update()
    _select(lat)
    assert bpy.ops.allset.deformer(kind='BEND') == {'FINISHED'}
    handle = bpy.context.view_layer.objects.active
    md = lat.modifiers["bend1"]
    _type(handle, md, "curvature", "90")
    us.MISMATCHES.clear()
    us.CHECK = True
    try:
        for z in (0.6, -0.4, 0.2):
            limits = tuple(md.limits)
            handle.location.z = z
            bpy.context.view_layer.update()
            assert tuple(md.limits) != limits, (z, "the handle moved: the bend wrote new limits")
        assert not us.MISMATCHES, us.MISMATCHES[:2]
    finally:
        us.CHECK = False
    sc.frame_set(3)
    assert not wire._idle_writer(key, sc, []), "a lattice bend may write on a frame change"
    for ob in (lat, handle):
        bpy.data.objects.remove(ob)
    bpy.context.view_layer.update()
    sc.frame_set(4)
    assert wire._idle_writer(key, sc, []), "the bend is gone: nothing to write"
