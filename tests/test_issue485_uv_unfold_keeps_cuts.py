"""#485: Unfold keeps every UV cut, also a cut inside one shell (the cylinder side's vertical cut): the side unfolds
flat instead of as a closed tube."""

from importlib import import_module

import bmesh
import bpy

import kit

uvt = import_module(kit.MODULE + ".operators.uv_tools")


def _cylinder():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=1, depth=2)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='SELECT')
    return ob


def _bm(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.ensure_lookup_table()
    return bm, bm.loops.layers.uv.active


def _cuts_inside_a_shell(bm, uv):
    groups = uvt.islands(bm, uv)
    where = {f: i for i, isl in enumerate(groups) for f in isl}
    out = []
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        a, b = e.link_faces
        if where[a] == where[b] and not all(uvt._same(uvt._uv_at(a, v, uv), uvt._uv_at(b, v, uv)) for v in e.verts):
            out.append(e.index)
    return out


def _stretch(bm, uv, ob):
    """Largest ratio between a side face's UV area per world area and the side's mean (1 = even)."""
    side = [f for f in bm.faces if len(f.verts) == 4]
    ratios = [uvt._uv_area(f, uv) / uvt._world_area(f, ob.matrix_world) for f in side]
    mean = sum(ratios) / len(ratios)
    return max(max(r / mean, mean / r) for r in ratios if r > 0)


def test_unfold_keeps_the_cut_inside_the_cylinder_side():
    ob = _cylinder()
    bm, uv = _bm(ob)
    cuts = _cuts_inside_a_shell(bm, uv)
    assert cuts, "the cylinder side has a vertical cut inside its shell"
    assert bpy.ops.allset.uv_unfold() == {'FINISHED'}
    bm, uv = _bm(ob)
    for i in cuts:
        e = bm.edges[i]
        a, b = e.link_faces
        assert not all(uvt._same(uvt._uv_at(a, v, uv), uvt._uv_at(b, v, uv)) for v in e.verts), \
            f"edge {i}: the cut got closed"
    assert _stretch(bm, uv, ob) < 1.2, "the side unfolds flat, its faces evenly sized"
