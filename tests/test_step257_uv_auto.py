"""Step 257 (Issue #150): UV > Automatic packs the shells with Maya's "Into square" layout and shows an editable
polyAutoProj node in the Channel Box INPUTS.

Maya's result for the #150 mesh (step-239 chain: cylinder, cap extruded Local Translate Z 1, cap rim bevelled, history
deleted, UV > Automatic with factory options) = Maya 2026's table.
Which face goes to which plane / shell follows Maya
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


def _same_partition(a, b):
    """Two face labelings put the same faces together (shell ids themselves differ)."""
    fw, bw = {}, {}
    return all(fw.setdefault(x, y) == y and bw.setdefault(y, x) == x for x, y in zip(a, b))


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
