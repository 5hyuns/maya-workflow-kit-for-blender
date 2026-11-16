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


def test_lattice_bend_bends_the_same_way():
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
    _type(handle, md, "curvature", "90")
    assert abs(deformers.sd_bend_values(md)[0] - math.pi / 2) < 1e-6
    dg = bpy.context.evaluated_depsgraph_get()
    ev = lat.evaluated_get(dg)
    got = np.array([tuple(lat.matrix_world @ p.co_deform) for p in ev.data.points])
    rest = np.array([tuple(lat.matrix_world @ p.co_deform) for p in lat.data.points])
    want = _expected(rest, handle, math.pi / 2, -1.0, 1.0)
    assert np.abs(got - want).max() < 1e-4, np.abs(got - want).max()
    assert _rows(handle, md) == [("Curvature", "90"), ("Low Bound", "-1"), ("High Bound", "1")], _rows(handle, md)


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
