"""#484: Move and Sew on an open border inside one UV shell sews it like Sew UV Edges (its UVs meet half-way)."""

from importlib import import_module

import bmesh
import bpy

import kit

uvt = import_module(kit.MODULE + ".operators.uv_tools")


def _cube():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.mesh.primitive_cube_add(size=2)
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    return ob


def _bm(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.ensure_lookup_table()
    return bm, bm.loops.layers.uv.active


def _inside_border(bm, uv):
    """An edge whose two faces are in the same shell but whose UVs differ there (an open border of the shell)."""
    assert len(uvt.islands(bm, uv)) == 1, "the cube's UVs are one shell"
    for e in bm.edges:
        a, b = e.link_faces
        if not all(uvt._same(uvt._uv_at(a, v, uv), uvt._uv_at(b, v, uv)) for v in e.verts):
            return e
    raise AssertionError("no open border")


def _pick(ob, index):
    bm, _uv = _bm(ob)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    e = bm.edges[index]
    e.select = True
    for v in e.verts:
        v.select = True
    bmesh.update_edit_mesh(ob.data)


def test_move_and_sew_sews_a_border_inside_one_shell():
    ob = _cube()
    bm, uv = _bm(ob)
    e = _inside_border(bm, uv)
    idx = e.index
    a, b = e.link_faces
    want = {v.index: (uvt._uv_at(a, v, uv) + uvt._uv_at(b, v, uv)) / 2 for v in e.verts}
    far = {(f.index, l.vert.index): l[uv].uv.copy() for f in bm.faces for l in f.loops if l.vert.index not in want}
    e.seam = True
    bmesh.update_edit_mesh(ob.data)
    _pick(ob, idx)
    assert bpy.ops.allset.uv_move_sew() == {'FINISHED'}
    bm, uv = _bm(ob)
    e = bm.edges[idx]
    assert not e.seam
    for f in e.link_faces:
        for v in e.verts:
            assert (uvt._uv_at(f, v, uv) - want[v.index]).length < 1e-5, (f.index, v.index)
    for f in bm.faces:
        for l in f.loops:
            if l.vert.index in want:
                continue
            assert (l[uv].uv - far[(f.index, l.vert.index)]).length < 1e-6, "the rest of the shell stays"


def test_move_and_sew_still_warns_on_an_edge_with_nothing_to_sew():
    ob = _cube()
    bm, uv = _bm(ob)
    inner = next(e for e in bm.edges
                 if all(uvt._same(uvt._uv_at(e.link_faces[0], v, uv), uvt._uv_at(e.link_faces[1], v, uv))
                        for v in e.verts))
    _pick(ob, inner.index)
    assert bpy.ops.allset.uv_move_sew() == {'CANCELLED'}
