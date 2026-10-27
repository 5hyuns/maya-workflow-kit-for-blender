"""Step 228 lane B: Flow Path Object (operators/flow_path_228.py) and Loft > Output geometry Polygons
(operators/surfaces_maya.py) against mayapy 2026 (research/maya/re/curve_rigs_228.json keys ``flow`` / ``loft``,
setups research/scripts/maya_curves228/measure.py). Maya (x, y, z) -> Blender (x, -z, y) x maya_unit."""

import json
import math
import os
from importlib import import_module

import bpy
from mathutils import Vector

import kit

smaya = import_module(kit.MODULE + ".operators.surfaces_maya")
sm = import_module(kit.MODULE + ".operators.surfaces_math")
cmaya = import_module(kit.MODULE + ".operators.curves_maya")
flowmod = import_module(kit.MODULE + ".operators.flow_path_228")
units = import_module(kit.MODULE + ".operators.units")

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "research", "maya", "re", "curve_rigs_228.json")
with open(DATA, encoding="utf-8") as _fh:
    D = json.load(_fh)


def k():
    return units.maya_unit(bpy.context.scene)


def b(p):
    return Vector((p[0], -p[2], p[1])) * k()


def _fresh():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for coll in (bpy.data.curves, bpy.data.meshes, bpy.data.lattices):
        for d in list(coll):
            coll.remove(d)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 120
    sc.frame_set(1)


def _select(obs):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[-1]


def _curve(name, pts):
    """Maya ``cmds.curve(d=3, p=pts)`` (clamped uniform cubic) as a Blender curve object."""
    n = len(pts)
    knots = [0.0] * 3 + [float(i) for i in range(1, n - 3)] + [float(n - 3)] * 3
    mc = cmaya.MCurve([tuple(b(p)) for p in pts], knots, 3, None, False)
    data_ = bpy.data.curves.new(name, 'CURVE')
    data_.dimensions = '3D'
    cmaya.write_spline(data_, mc)
    ob = bpy.data.objects.new(name, data_)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# --- Flow Path Object ----------------------------------------------------------------------------------------

def _snake():
    """Maya ``polyCylinder(h=4, ax=(1, 0, 0), sh=10)`` vertices (20 sides, 11 rings along X) in Maya's order."""
    vs = []
    for r in range(11):
        for i in range(20):
            a = math.radians(-162 + 18 * i)
            vs.append(b((-2 + 0.4 * r, math.cos(a), math.sin(a))))
    for vid, rest in zip(D["flow"]["vids"], D["flow"]["rest"]):
        assert (vs[vid] - b(rest)).length < 1e-5, vid
    me = bpy.data.meshes.new("snakeShape")
    me.from_pydata(vs, [], [])
    ob = bpy.data.objects.new("snake", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _motion_path(ob, path):
    """Lane A's Attach to Motion Path result: Follow Path, fixed location, offset_factor keyed 1 -> 0, 120 -> 1 with
    Maya's flat auto tangents (mp_default u values)."""
    path.data.use_path = True
    path.data.splines[0].resolution_u = 64
    con = ob.constraints.new('FOLLOW_PATH')
    con.target = path
    con.use_fixed_location = True
    con.use_curve_follow = True
    con.forward_axis = 'FORWARD_X'
    con.up_axis = 'UP_Z'
    con.offset_factor = 0.0
    con.keyframe_insert("offset_factor", frame=1)
    con.offset_factor = 1.0
    con.keyframe_insert("offset_factor", frame=120)
    fc = kit.fcurves(ob)[0]
    k0, k1 = fc.keyframe_points
    for kp in (k0, k1):
        kp.handle_left_type = kp.handle_right_type = 'FREE'
    k0.handle_right = (1 + 119 / 3, 0.0)
    k1.handle_left = (120 - 119 / 3, 1.0)
    fc.update()
    return con


def _flow_scene():
    _fresh()
    path = _curve("path", D["path_points"])
    ob = _snake()
    con = _motion_path(ob, path)
    bpy.context.view_layer.update()
    return path, ob, con


def _world_verts(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    try:
        return [oe.matrix_world @ v.co for v in me.vertices]
    finally:
        oe.to_mesh_clear()


def test_flow_needs_motion_path():
    _fresh()
    ob = _snake()
    _select([ob])
    assert bpy.ops.allset.flow_path() == {'CANCELLED'}
    assert not bpy.data.lattices


def test_flow_nodes():
    path, ob, con = _flow_scene()
    _select([ob])
    assert bpy.ops.allset.flow_path() == {'FINISHED'}
    lob = bpy.data.objects["ffd1Lattice"]
    assert ob.modifiers["ffd1"].type == 'LATTICE' and ob.modifiers["ffd1"].object == lob
    assert ob.modifiers["ffd1Base"].type == 'HOOK'
    assert lob.modifiers["flow1"].type == 'CURVE' and lob.modifiers["flow1"].object == path
    lat = lob.data
    assert (lat.points_u, lat.points_v, lat.points_w) == (5, 2, 2)      # Front 5 along X, Up / Side 2
    assert con.mute
    rec = json.loads(lob[flowmod.KEY])
    assert rec["object"] == "snake" and rec["path"] == "path" and rec["flow"] == "flow1"
    assert bpy.context.active_object == lob


def test_flow_vertices_vs_mayapy():
    path, ob, con = _flow_scene()
    _select([ob])
    bpy.ops.allset.flow_path()
    vids = D["flow"]["vids"]
    ends = [i for i, v in enumerate(vids) if v < 20 or v >= 200]       # vertices on the lattice's end planes
    worst, worst_end, report = 0.0, 0.0, []
    for f, rows in D["flow"]["rows"]:
        bpy.context.scene.frame_set(f)
        got = _world_verts(ob)
        errs = [(got[v] - b(want)).length / k() for v, want in zip(vids, rows)]
        report.append((f, round(max(errs), 4)))
        worst = max(worst, max(errs))
        if f in (30, 60, 90):            # inside the path: the lattice points sit where Maya's flow puts them
            worst_end = max(worst_end, max(errs[i] for i in ends))
    print("flow max deviation per frame (Maya units):", report, "end planes 30/60/90:", round(worst_end, 6))
    assert worst_end < 1e-3, worst_end
    # Maya's ffd (Local off) is a Bernstein volume, Blender's lattice Linear: approximation, recorded in step_228.md
    assert worst < 0.1, report
    bpy.context.scene.frame_set(1)


def test_flow_undo():
    path, ob, con = _flow_scene()
    _select([ob])
    bpy.ops.ed.undo_push(message="before flow")
    assert bpy.ops.allset.flow_path('EXEC_DEFAULT', True) == {'FINISHED'}
    assert "ffd1Lattice" in bpy.data.objects
    bpy.ops.ed.undo()
    assert "ffd1Lattice" not in bpy.data.objects
    ob = bpy.data.objects["snake"]
    assert not ob.modifiers and not ob.constraints[0].mute


# --- Loft > Polygons -----------------------------------------------------------------------------------------

A = [(0, 0, 0), (1, 0, 1), (2, 0, 0), (3, 0, 1)]
B = [(0, 2, 0), (1, 2, 1), (2, 2, 0), (3, 2, 1)]


def _loft_polygons():
    _fresh()
    a, c = _curve("curve1", A), _curve("curve2", B)
    _select([a, c])
    assert bpy.ops.allset.loft(output='POLYGONS') == {'FINISHED'}
    return a, c, bpy.context.active_object


def test_loft_polygons_counts_and_name():
    a, c, m = _loft_polygons()
    L = D["loft"]
    assert m.type == 'MESH' and m.name == "loftedSurface1", m.name
    me = m.data
    uv = me.uv_layers.active
    nuv = len({(round(d.uv[0], 6), round(d.uv[1], 6)) for d in uv.data})
    print("loft counts kit / Maya: verts %d / %d, faces %d / %d, uvs %d / %d"
          % (len(me.vertices), L["verts"], len(me.polygons), L["faces"], nuv, L["uvs"]))
    assert (len(me.vertices), len(me.polygons), nuv) == (L["verts"], L["faces"], L["uvs"])
    assert not [o for o in bpy.data.objects if o.type == 'SURFACE']       # Maya -po 1: no NURBS surface node
    assert smaya.loft_record(m)["curves"] == ["curve1", "curve2"]


def test_loft_polygons_points_at_maya_uvs():
    """The kit's surface at each Maya vertex's UV = that Maya vertex (surface + UV mapping exact, though the
    tessellations differ), and every kit vertex's UV maps back to its own position."""
    a, c, m = _loft_polygons()
    s = smaya._loft_surf([a, c], json.loads(m[smaya.LOFT_KEY])["opts"])
    u0, u1 = s.domain_u()
    v0, v1 = s.domain_v()

    def at(uv):
        return Vector(s.point(u0 + uv[1] * (u1 - u0), v0 + uv[0] * (v1 - v0)))

    worst = max((at(uv) - b(p)).length / k() for uv, p in zip(D["loft"]["uv"], D["loft"]["points"]))
    print("loft: kit surface at Maya UVs vs Maya vertices, max", worst)
    assert worst < 1e-4, worst
    me = m.data
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            assert (at(uv[li].uv) - m.matrix_world @ me.vertices[vi].co).length < 1e-4


def test_loft_polygons_history():
    a, c, m = _loft_polygons()
    smaya._pending.clear()
    sp = c.data.splines[0]
    p = sp.points[1]
    p.co = (*(Vector(p.co[:3]) + b((0, 0, 1))), 1.0)       # Maya: move curve2.cv[1] by (0, 0, 1)
    c.data.update_tag()
    bpy.context.view_layer.update()
    assert "curve2" in smaya._pending, smaya._pending      # the depsgraph handler noticed the input curve
    smaya._tick()
    s = smaya._loft_surf([a, c], json.loads(m[smaya.LOFT_KEY])["opts"])
    verts, tris, uvs = smaya.tessellate(s)
    me = m.data
    assert max((Vector(v) - me.vertices[i].co).length for i, v in enumerate(verts)) < 1e-6
    # Maya's vertex 5 after the move lies on the unchanged curve1 (its tessellation moved along it): the kit's
    # surface still passes through it
    after = b(D["loft"]["after_cv_move_v5"])
    best = min((Vector(s.point(u0, s.domain_v()[0])) - after).length
               for u0 in [s.domain_u()[0] + (s.domain_u()[1] - s.domain_u()[0]) * i / 2000 for i in range(2001)])
    assert best < 2e-3, best
    # an edit away from the kit's result breaks the history (Maya: the mesh no longer follows)
    me.vertices[0].co.z += 0.5
    p.co = (*(Vector(p.co[:3]) + b((0, 0, 1))), 1.0)
    smaya.refresh_lofts(bpy.context.scene, {"curve2"})
    assert smaya.LOFT_KEY not in m
    assert abs(me.vertices[0].co.z - 0.5) < 1e-6


def test_loft_option_window():
    ow = import_module(kit.MODULE + ".operators.option_windows")
    w = next(w for w in ow.WINDOWS if w.key == "loft")
    assert any(f.name == "output" and f.items == ("NURBS", "Polygons") for f in w.fields)
    fw = next(w for w in ow.WINDOWS if w.key == "flow_path")
    assert [f.default for f in fw.fields] == [5, 2, 2]
    mm = import_module(kit.MODULE + ".ui.menu_map")
    assert mm.MAP["Constrain/Motion Paths/Flow Path Object"] == "allset.flow_path"
