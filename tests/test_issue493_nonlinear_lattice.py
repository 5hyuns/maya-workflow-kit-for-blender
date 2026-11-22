"""Issue #493: Twist, Squash, Flare, Sine and Wave on a lattice or a NURBS surface take Maya's shapes.

A lattice and a mesh with the same points get one node (one handle): with the same values the lattice points end up
where the mesh points do. The shape follows the handle (moved, keyed), Envelope and the node's weights blend it in,
several nodes deform one after the other, and removing the node (also Delete by Type > Nonlinears) takes its shape
away.
"""

import math
from importlib import import_module

import bpy
from mathutils import Vector

import kit

deformers = import_module(kit.MODULE + ".operators.deformers")
nl = import_module(kit.MODULE + ".operators.nonlinear_nodes")
nm = import_module(kit.MODULE + ".operators.nonlinear_math")
history = import_module(kit.MODULE + ".operators.history")


def _fresh():
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.lattices, bpy.data.curves, bpy.data.actions):
        for d in list(coll):
            coll.remove(d)
    bpy.context.scene.frame_set(1)


def _select(*obs):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _pair():
    """A 3 x 5 x 3 lattice (scaled up along Z) and a mesh with the lattice's points, both selected."""
    lat = bpy.data.objects.new("ffd1Lattice", bpy.data.lattices.new("ffd1LatticeShape"))
    lat.data.points_u, lat.data.points_v, lat.data.points_w = 3, 3, 5
    lat.scale = (1.0, 0.8, 3.0)
    lat.location = (0.2, -0.1, 0.4)
    lat.rotation_euler = (0.1, 0.0, 0.3)
    bpy.context.scene.collection.objects.link(lat)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new("pCubeShape1")
    me.from_pydata([tuple(lat.matrix_world @ p.co) for p in lat.data.points], [], [])
    ob = bpy.data.objects.new("pCube1", me)
    bpy.context.scene.collection.objects.link(ob)
    _select(ob, lat)
    return lat, ob


def _lattice(lat):
    bpy.context.view_layer.update()
    ev = lat.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [lat.matrix_world @ p.co_deform for p in ev.data.points]


def _mesh(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [ob.matrix_world @ v.co for v in ev.data.vertices]


def _close(a, b, what, tol=1e-4):
    worst = max((p - q).length for p, q in zip(a, b))
    assert worst < tol, (what, worst)


def _set(md, values):
    for key, v in values.items():
        a = deformers.attr(md, "maya:" + key)
        assert a is not None, (md.name, key)
        a.set(md, math.radians(v) if a.kind == "ROTATION" else v)


CASES = {
    "twist": {"startAngle": -30.0, "endAngle": 120.0, "lowBound": -0.7, "highBound": 1.6},
    "squash": {"factor": 0.6, "expand": 1.4, "maxExpandPos": 0.3, "startSmoothness": 0.4, "endSmoothness": 0.8,
               "highBound": 0.8},
    "flare": {"startFlareX": 0.5, "endFlareX": 1.8, "startFlareZ": 1.2, "endFlareZ": 0.7, "curve": 0.6},
    "sine": {"amplitude": 0.3, "wavelength": 1.3, "offset": 0.2, "dropoff": -0.4, "lowBound": -2.0},
    "wave": {"amplitude": 0.25, "wavelength": 0.7, "offset": 0.1, "dropoff": 0.5, "dropoffPosition": 0.3,
             "maxRadius": 1.5},
}


def test_lattice_points_go_where_mesh_points_go():
    for kind, values in CASES.items():
        _fresh()
        lat, ob = _pair()
        assert bpy.ops.allset.deformer(kind=kind.upper()) == {'FINISHED'}
        name = f"{kind}1"
        lmd, mmd = lat.modifiers[name], ob.modifiers[name]
        assert mmd.type == 'NODES' and nm.kind_of(lmd) == kind, (kind, lmd.type)
        assert deformers.handle_of(lmd) == deformers.handle_of(mmd)
        rows = [a.key for a in deformers.attrs(lmd)]
        assert rows == [a.key for a in deformers.attrs(mmd)], (kind, rows)
        _set(lmd, values)
        _set(mmd, values)
        _close(_lattice(lat), _mesh(ob), kind)
        assert lat.data.shape_keys.key_blocks[name].value == 1.0
        # the handle moved and turned: the shape stays in its space
        h = deformers.handle_of(lmd)
        h.location += Vector((0.3, -0.2, 0.5))
        h.rotation_euler = (0.4, -0.2, 0.7)
        h.scale = (1.3, 1.3, 1.3)
        _close(_lattice(lat), _mesh(ob), kind + " moved handle")
        # Envelope
        _set(lmd, {"envelope": 0.5})
        _set(mmd, {"envelope": 0.5})
        _close(_lattice(lat), _mesh(ob), kind + " envelope")


def test_weights_keys_and_order():
    _fresh()
    lat, ob = _pair()
    bpy.ops.allset.deformer(kind='TWIST')
    _select(ob, lat)
    bpy.ops.allset.deformer(kind='FLARE')
    t, f = lat.modifiers["twist1"], lat.modifiers["flare1"]
    tm, fm = ob.modifiers["twist1"], ob.modifiers["flare1"]
    for a, b, vals in ((t, tm, {"endAngle": 90.0}), (f, fm, {"endFlareX": 2.0, "curve": 0.5})):
        _set(a, vals)
        _set(b, vals)
    _close(_lattice(lat), _mesh(ob), "twist, then flare")
    # weights: the node's vertex group
    vg = lat.vertex_groups["twist1"]
    vg.add([0, 1, 2, 3], 0.25, 'REPLACE')
    ob.vertex_groups["twist1"].add([0, 1, 2, 3], 0.25, 'REPLACE')
    _close(_lattice(lat), _mesh(ob), "weights")
    # a keyed value follows the frame
    h = deformers.handle_of(t)
    _set(t, {"endAngle": 0.0})
    a = deformers.attr(t, "maya:endAngle")
    path = a.paths[0][0]
    assert path == f'origin["{nm.prop("End Angle")}"]', path
    h.keyframe_insert(f'["{nm.prop("End Angle")}"]', frame=1)          # keyed on the handle, like bend's rows
    _set(t, {"endAngle": 180.0})
    h.keyframe_insert(f'["{nm.prop("End Angle")}"]', frame=11)
    sc = bpy.context.scene
    for frame, deg in ((1, 0.0), (11, 180.0)):
        sc.frame_set(frame)
        assert abs(nm.values(t)["End Angle"] - math.radians(deg)) < 1e-5, frame
        _set(tm, {"endAngle": deg})
        _close(_lattice(lat), _mesh(ob), f"keyed frame {frame}")
    assert h is not None


def test_removing_the_node_takes_its_shape():
    _fresh()
    lat, _ob = _pair()
    _select(lat)
    rest = _lattice(lat)
    bpy.ops.allset.deformer(kind='SQUASH')
    _set(lat.modifiers["squash1"], {"factor": 0.8})
    assert max((p - q).length for p, q in zip(_lattice(lat), rest)) > 0.05
    lat.modifiers.remove(lat.modifiers["squash1"])
    _close(_lattice(lat), rest, "node removed")
    assert lat.data.shape_keys is None, "the kit's Basis goes with the last node"
    _select(lat)
    bpy.ops.allset.deformer(kind='SINE')
    _set(lat.modifiers["sine1"], {"amplitude": 0.4})
    history.delete_by_type(bpy.context, 'NONLINEARS', [lat])
    _close(_lattice(lat), rest, "Delete by Type > Nonlinears")
    assert "sine1" not in lat.modifiers and lat.data.shape_keys is None


def test_nurbs_surface():
    _fresh()
    bpy.ops.surface.primitive_nurbs_surface_cylinder_add()
    srf = bpy.context.active_object
    srf.scale = (1.0, 1.0, 2.0)
    bpy.context.view_layer.update()
    rest = [Vector(p.co.xyz) for sp in srf.data.splines for p in sp.points]
    _select(srf)
    assert bpy.ops.allset.deformer(kind='TWIST') == {'FINISHED'}
    md = srf.modifiers["twist1"]
    assert nm.kind_of(md) == "twist"
    _set(md, {"endAngle": 90.0})
    bpy.context.view_layer.update()
    h = deformers.handle_of(md)
    to_h = h.matrix_world.inverted() @ srf.matrix_world
    kb = srf.data.shape_keys.key_blocks["twist1"]
    for p, k in zip(rest, kb.data):
        q = to_h @ p
        x, y, z = nm.deform("twist", nm.values(md), q.x, q.z, -q.y)
        want = to_h.inverted() @ Vector((x, -z, y))
        assert (Vector(k.co) - want).length < 1e-5, (p, k.co, want)


def test_python_shapes_match_the_node_groups():
    """The Python shapes are the node groups' shapes: a mesh column through every kind with random values."""
    import random
    rnd = random.Random(493)
    pts = [(rnd.uniform(-1.5, 1.5), rnd.uniform(-2.5, 2.5), rnd.uniform(-1.5, 1.5)) for _ in range(60)]
    for kind in nl.KINDS:
        for _round in range(4):
            _fresh()
            me = bpy.data.meshes.new("m")
            me.from_pydata([(x, -z, y) for x, y, z in pts], [], [])
            ob = bpy.data.objects.new("pCube1", me)
            bpy.context.scene.collection.objects.link(ob)
            _select(ob)
            bpy.ops.allset.deformer(kind=kind.upper())
            md = ob.modifiers[f"{kind}1"]
            h = deformers.handle_of(md)
            h.location, h.rotation_euler, h.scale = (0, 0, 0), (0, 0, 0), (1, 1, 1)
            vals = nm.defaults(kind)
            for n in vals:
                lo, hi = nl.LIMITS.get(n, (None, None))
                lo = -2.0 if lo is None else lo
                hi = 2.0 if hi is None else hi
                if n == "Envelope":
                    lo, hi = 1.0, 1.0
                vals[n] = rnd.uniform(lo, hi) if n not in ("Max Radius", "Wavelength") else rnd.uniform(0.3, 2.0)
                a = deformers.attr(md, "maya:" + nm.prop(n)[len(nm.PREFIX):])
                a.set(md, vals[n])
            vals = {n: nl.limited(kind, n, v) for n, v in vals.items()}
            ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
            for (x, y, z), v in zip(pts, ev.vertices):
                want = nm.deform(kind, vals, x, y, z)
                got = (v.co.x, v.co.z, -v.co.y)
                assert all(abs(a - b) < 1e-4 for a, b in zip(want, got)), (kind, vals, (x, y, z), want, got)
