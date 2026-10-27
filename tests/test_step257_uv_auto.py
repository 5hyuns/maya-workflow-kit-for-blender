"""Step 257 (Issue #150): UV > Automatic packs the shells with Maya's "Into square" layout and shows an editable
polyAutoProj node in the Channel Box INPUTS.

Maya truth for the #150 mesh (step-239 chain: cylinder, cap extruded Local Translate Z 1, cap rim bevelled, history
deleted, UV > Automatic with factory options) =  B2 table (Maya 2026).
Which face goes to which plane / shell (): tests/maya257_uv_faces_data.py
(Maya 2026, 11 meshes incl. self-overlapping helicoids, jittered meshes and partial selections)."""

from importlib import import_module

import bmesh
import bpy

import kit

ex = import_module(kit.MODULE + ".operators.extrude")
bev = import_module(kit.MODULE + ".operators.bevel_maya")
create = import_module(kit.MODULE + ".operators.create")
units = import_module(kit.MODULE + ".operators.units")
uvt = import_module(kit.MODULE + ".operators.uv_tools")
al = import_module(kit.MODULE + ".operators.autoproj_layout")
in_view = import_module(kit.MODULE + ".ui.in_view")
extrude = import_module(kit.MODULE + ".operators.extrude")

# (u0, v0, u1, v1) of Maya's six shells
MAYA_SHELLS = [
    (0.001992, 0.001856, 0.300239, 0.554836),
    (0.308172, 0.001856, 0.606419, 0.554836),
    (0.406530, 0.558827, 0.775184, 0.927481),
    (0.102148, 0.558827, 0.400395, 0.927481),
    (0.614158, 0.001856, 0.830847, 0.463817),
    (0.781319, 0.467808, 0.998008, 0.929769),
]


def chain():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    ob = create.create(bpy.context, 'CYLINDER')
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    k = units.maya_unit(bpy.context.scene)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    cap = [f for f in bm.faces if f.calc_center_median().z > 0.99 * k]
    ex.extrude(bm, cap, local_translate_z=1.0 * k)
    top = {f for f in bm.faces if f.calc_center_median().z > 1.99 * k}
    border = [e for e in bm.edges if sum(1 for f in e.link_faces if f in top) == 1]
    bev.bevel_edges(bm, border, unit=k)
    bm.to_mesh(ob.data)
    bm.free()
    ex.RECORDS.pop(ob.name, None)
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    return ob


def shells(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    out = []
    for s in uvt.islands(bm, uv):
        pts = [lp[uv].uv for f in s for lp in f.loops]
        out.append((min(p.x for p in pts), min(p.y for p in pts), max(p.x for p in pts), max(p.y for p in pts)))
    bm.free()
    return sorted(out)


def test_chain_layout_like_maya():
    """The kit-built #150 chain (Maya-numbered since step 257, #149): every face whose normal is clear of Maya's
    0.5 candidate threshold gets Maya's planes. Four bevel faces (42 / 47 / 52 / 57) have a normal component of
    exactly 0.5 in exact arithmetic; Maya's own float32 vertices put them at 0.4999999 / -0.5 / -0.5000001 / 0.5,
    so only face 52 turns into an X- candidate there. The kit's vertices are 2e-6 from Maya's, so those four faces
    follow float noise and the final layout differs (see test_maya_chain_mesh_through_kit for the same mesh with
    Maya's floats: Maya's bboxes within 5e-7)."""
    from maya257_uv_faces_data import CASES
    case = CASES["chain150"]
    ob = chain()
    assert bpy.ops.allset.menu_item(item="UV/Automatic") == {'FINISHED'}
    k = units.maya_unit(bpy.context.scene)
    pts = [(v.co.x / k, v.co.z / k, -v.co.y / k) for v in ob.data.vertices]          # Blender -> Maya (x, z, -y)
    faces = [list(p.vertices) for p in ob.data.polygons]
    # face ids and their vertices like Maya (#149; the first corner of a face may differ)
    assert [sorted(f) for f in faces] == [sorted(f) for f in case["faces"]], "chain not numbered like Maya (#149)"
    kit_n = al.face_normals(pts, faces)
    maya_n = al.face_normals(case["verts"], case["faces"])
    edge = set()
    for i, (a, m) in enumerate(zip(kit_n, maya_n)):
        for c in range(3):
            assert abs(float(a[c]) - float(m[c])) < 1e-5, (i, a, m)
            if abs(abs(float(m[c])) - 0.5) < 1e-5:
                edge.add(i)
    assert edge == {42, 47, 52, 57}, sorted(edge)

    def masks(normals):
        out = []
        for x, y, z in normals:
            dots = (-x, x, -y, y, -z, z)
            out.append(sum(1 << j for j, d in enumerate(dots) if d > al.THRESHOLD6))
        return out
    km, mm = masks(kit_n), masks(maya_n)
    differ = [i for i in range(len(faces)) if km[i] != mm[i] and i not in edge]
    assert not differ, differ
    got = shells(ob)
    assert len(got) == 6, got
    assert all(0.0 <= x <= 1.0 for s in got for x in s), got


def _same_partition(a, b):
    """Two face labelings put the same faces together (shell ids themselves differ)."""
    fw, bw = {}, {}
    return all(fw.setdefault(x, y) == y and bw.setdefault(y, x) == x for x, y in zip(a, b))


def test_plane_assignment_like_maya():
    """bpy-free rule vs Maya: every projected face in the same shell as Maya's, on each case."""
    from maya257_uv_faces_data import CASES
    bad, faces = [], 0
    for name, case in CASES.items():
        act = case["active"] if case["active"] is not None else list(range(len(case["faces"])))
        shells = al.assign_planes(case["verts"], [case["faces"][i] for i in act])
        got = [-1] * len(case["faces"])
        for i, (_plane, group) in enumerate(shells):
            for f in group:
                got[act[f]] = i
        faces += len(act)
        if not _same_partition([got[i] for i in act], [case["shell"][i] for i in act]) or                 len(shells) != len({case["shell"][i] for i in act}):
            bad.append(name)
    print("cases", len(CASES), "faces", faces, "differ", bad)
    assert not bad, bad


def test_maya_chain_mesh_through_kit():
    """Maya's own #150 chain points (bit-exact, scene unit 1 = Maya unit) through the kit's UV > Automatic code:
    the six shells land on Maya's bboxes. Blender (x, y, z) = Maya (x, -z, y) keeps every float."""
    from maya257_uv_faces_data import CASES
    case = CASES["chain150"]
    bm = bmesh.new()
    verts = [bm.verts.new((x, -z, y)) for x, y, z in case["verts"]]
    for f in case["faces"]:
        bm.faces.new([verts[i] for i in f])
    bm.faces.index_update()
    uv = bm.loops.layers.uv.verify()
    assert uvt.auto_project(bm, uv, list(bm.faces), 6, 0.2, 1.0) == 6
    got = []
    for s in uvt.islands(bm, uv):
        pts = [lp[uv].uv for f in s for lp in f.loops]
        got.append((min(p.x for p in pts), min(p.y for p in pts), max(p.x for p in pts), max(p.y for p in pts)))
    bm.free()
    got, want = sorted(got), sorted(MAYA_SHELLS)
    worst = max(abs(a - b) for g, w in zip(got, want) for a, b in zip(g, w))
    print("Maya mesh: worst shell bbox difference", worst)
    assert len(got) == 6 and worst < 2e-5, (got, want)


# --- polyAutoProj history node (Channel Box INPUTS) -------------------------------------------------------------

def _cube():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene["allset_polyAutoProj"] = 0
    ob = create.create(bpy.context, 'CUBE')
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    return ob


def _bounds(ob):
    import numpy as np
    layer = ob.data.uv_layers.active
    a = np.empty(len(layer.data) * 2)
    layer.data.foreach_get("uv", a)
    a = a.reshape(-1, 2)
    return float(a[:, 0].min()), float(a[:, 1].min()), float(a[:, 0].max()), float(a[:, 1].max())


def test_object_mode_automatic_leaves_an_editable_poly_auto_proj_node():
    """Maya: UV > Automatic in object mode -> Channel Box INPUTS polyAutoProj1 (060_modeling_anim.md B2), its values
    can be typed there and change the UVs; Delete History removes it."""
    ob = _cube()
    assert bpy.ops.allset.menu_item(item="UV/Automatic") == {'FINISHED'}
    assert bpy.context.mode == 'OBJECT'
    rec = in_view.cb_record(bpy.context, ob)
    assert rec is not None and rec.name == "polyAutoProj1", rec
    assert rec.spec.fields == ("planes", "optimize", "percentage_space")
    hist = bpy.context.window_manager.allset_history
    assert hist.planes_text == "6" and float(hist.percentage_space_text) == 0.2, (hist.planes_text,
                                                                                 hist.percentage_space_text)
    # no In-View Editor / extrude manipulator for a projection
    assert not rec.spec.in_view
    b0 = _bounds(ob)
    assert min(b0[:2]) > 0.001, b0
    hist.percentage_space_text = "0"                     # typed in the Channel Box
    rec = in_view.cb_record(bpy.context, ob)
    assert rec is not None and rec.params["percentage_space"] == 0.0, rec and rec.params
    b1 = _bounds(ob)
    assert abs(min(b1[:2])) < 1e-6 and abs(max(b1[2:]) - 1.0) < 1e-6, b1      # no border at 0 % (Maya ps 0)
    assert bpy.context.mode == 'OBJECT' and ob.select_get()
    # a second Automatic is polyAutoProj2 (Maya numbers per scene)
    assert bpy.ops.allset.menu_item(item="UV/Automatic") == {'FINISHED'}
    assert in_view.cb_record(bpy.context, ob).name == "polyAutoProj2"
    # Delete History: the node goes, the UVs stay
    b2 = _bounds(ob)
    assert bpy.ops.allset.delete_history() == {'FINISHED'}
    assert in_view.cb_record(bpy.context, ob) is None
    assert _bounds(ob) == b2


def test_node_hides_when_the_uvs_change_and_works_in_edit_mode():
    ob = _cube()
    assert bpy.ops.allset.menu_item(item="UV/Automatic") == {'FINISHED'}
    assert in_view.cb_record(bpy.context, ob) is not None
    layer = ob.data.uv_layers.active
    layer.data[0].uv = (0.5, 0.5)                         # another UV edit: no longer this node's result
    assert in_view.cb_record(bpy.context, ob) is None
    # edit mode: selected faces, the node is the last kit operation like extrude / bevel
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='SELECT')
    assert bpy.ops.allset.menu_item(item="UV/Automatic") == {'FINISHED'}
    rec = in_view.cb_record(bpy.context, ob)
    assert rec is not None and rec.spec.node == "polyAutoProj", rec
    assert extrude.set_params(bpy.context, planes=3) == {'FINISHED'}
    rec = in_view.cb_record(bpy.context, ob)
    assert rec is not None and rec.params["planes"] == 3
    assert not in_view.manip_visible(bpy.context)
    bpy.ops.object.mode_set(mode='OBJECT')


def test_optimize_zero_is_less_distortion():
    """Optimize 0 (Less distortion): one best plane per face (autoproj_layout.assign_planes, checked both ways)."""
    ob = _cube()
    assert bpy.ops.allset.menu_item(item="UV/Automatic") == {'FINISHED'}
    hist = bpy.context.window_manager.allset_history
    hist.optimize_text = "0"
    rec = in_view.cb_record(bpy.context, ob)
    assert rec is not None and rec.params["optimize"] == 0.0
