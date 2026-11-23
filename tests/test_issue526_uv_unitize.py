"""#526: UV Editor Modify > Unitize (``allset.uv_unitize``) puts each selected face on the 0-1 square's edge and
makes every face its own UV shell, like Maya: no UV of one face stays joined to a UV of another face (Blender's
island / sticky selection and the kit's shells), so moving one face moves nothing else."""

from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit

um = import_module(kit.MODULE + ".operators.uv_modify")
uvt = import_module(kit.MODULE + ".operators.uv_tools")
compat = import_module(kit.MODULE + ".compat")
emm = import_module(kit.MODULE + ".ui.editor_menu_map")

LIMIT = 1e-4         # Blender joins two UVs of one vertex closer than this on both axes
SLACK = 3e-4         # a split UV may sit this far from its exact place


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _uv_area():
    scr = bpy.context.window.screen
    a = next(a for a in scr.areas if a.type in ('VIEW_3D', 'IMAGE_EDITOR'))
    a.ui_type = 'UV'
    return a, next(r for r in a.regions if r.type == 'WINDOW')


def _edit(ob, synced=True):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = synced
    ts.mesh_select_mode = (False, False, True)
    return ob


def _cube():
    _clear()
    bpy.ops.mesh.primitive_cube_add()
    return _edit(bpy.context.active_object)


def _grid(n=3):
    _clear()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=n, y_subdivisions=n, size=2)
    return _edit(bpy.context.active_object)


def _bm(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    return bm, bm.loops.layers.uv.active


def _select_faces(ob, idx):
    bm, _uv = _bm(ob)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for i in idx:
        bm.faces[i].select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(ob.data)


def _joined_pairs(bm, uv, faces=None):
    """Pairs of loops of one vertex in two different faces whose UVs Blender treats as one."""
    out = []
    for v in bm.verts:
        ls = list(v.link_loops)
        for i, a in enumerate(ls):
            for b in ls[i + 1:]:
                if a.face is not b.face and (faces is None or a.face in faces or b.face in faces):
                    pa, pb = a[uv].uv, b[uv].uv
                    if abs(pa.x - pb.x) <= LIMIT and abs(pa.y - pb.y) <= LIMIT:
                        out.append((a.face.index, b.face.index, v.index))
    return out


def _check_face(face, uv):
    want = um.unitize_points(len(face.loops))
    for loop, p in zip(face.loops, want):
        got = loop[uv].uv
        assert (got - p).length <= SLACK, (face.index, tuple(got), tuple(p))
        assert -1e-9 <= got.x <= 1 + 1e-9 and -1e-9 <= got.y <= 1 + 1e-9, tuple(got)


def test_points_on_the_square_edge():
    def pts(n):
        return [tuple(round(c, 4) for c in p) for p in um.unitize_points(n)]
    assert pts(3) == [(0, 0), (1, 0), (1, 1)]
    assert pts(4) == [(0, 0), (1, 0), (1, 1), (0, 1)]
    assert pts(5) == [(0, 0), (1, 0), (1, 0.5), (1, 1), (0, 1)]
    assert pts(6) == [(0, 0), (1, 0), (1, 0.5), (1, 1), (0.5, 1), (0, 1)]
    assert pts(7) == [(0, 0), (0.5, 0), (1, 0), (1, 0.5), (1, 1), (0.5, 1), (0, 1)]
    assert pts(8) == [(0, 0), (0.5, 0), (1, 0), (1, 0.5), (1, 1), (0.5, 1), (0, 1), (0, 0.5)]
    assert pts(9) == [(0, 0), (0.5, 0), (1, 0), (1, 0.3333), (1, 0.6667), (1, 1), (0.5, 1), (0, 1), (0, 0.5)]
    assert pts(12) == [(0, 0), (0.3333, 0), (0.6667, 0), (1, 0), (1, 0.3333), (1, 0.6667), (1, 1), (0.6667, 1),
                       (0.3333, 1), (0, 1), (0, 0.6667), (0, 0.3333)]


def test_menu_runs_the_kit_unitize():
    assert emm.MAP["UV Editor/Modify/Unitize"] == "allset.uv_unitize"


def test_cube_every_face_its_own_shell():
    ob = _cube()
    bpy.ops.mesh.select_all(action='SELECT')
    assert bpy.ops.allset.uv_unitize() == {'FINISHED'}
    bm, uv = _bm(ob)
    for f in bm.faces:
        _check_face(f, uv)
    assert not _joined_pairs(bm, uv), _joined_pairs(bm, uv)
    assert sorted(len(i) for i in uvt.islands(bm, uv)) == [1] * 6
    assert all(e.seam for e in bm.edges), "every edge of the unitized faces is cut"


def test_grid_and_one_face():
    ob = _grid(3)
    bm, uv = _bm(ob)
    before = {l.index: l[uv].uv.copy() for f in bm.faces for l in f.loops}
    _select_faces(ob, [4])                       # the middle face
    assert bpy.ops.allset.uv_unitize() == {'FINISHED'}
    bm, uv = _bm(ob)
    _check_face(bm.faces[4], uv)
    for f in bm.faces:
        if f.index != 4:
            assert all((l[uv].uv - before[l.index]).length < 1e-7 for l in f.loops), "other faces stay"
    assert not _joined_pairs(bm, uv, {bm.faces[4]})
    assert [len(i) for i in uvt.islands(bm, uv) if bm.faces[4] in i] == [1]
    assert sum(e.seam for e in bm.edges) == 4


def test_uv_sync_off_maps_the_picked_uv_faces():
    ob = _grid(2)
    bpy.context.scene.tool_settings.use_uv_select_sync = False
    bm, uv = _bm(ob)
    for f in bm.faces:
        f.select_set(True)
        compat.set_uv_face_selected(f, uv, f.index in (0, 3))
    bmesh.update_edit_mesh(ob.data)
    before = {l.index: l[uv].uv.copy() for f in bm.faces for l in f.loops}
    assert bpy.ops.allset.uv_unitize() == {'FINISHED'}
    bm, uv = _bm(ob)
    for f in bm.faces:
        if f.index in (0, 3):
            _check_face(f, uv)
        else:
            assert all((l[uv].uv - before[l.index]).length < 1e-7 for l in f.loops)
    assert not _joined_pairs(bm, uv, {bm.faces[0], bm.faces[3]})


def test_nothing_selected_changes_nothing():
    ob = _cube()
    bpy.ops.mesh.select_all(action='DESELECT')
    bm, uv = _bm(ob)
    before = [l[uv].uv.copy() for f in bm.faces for l in f.loops]
    assert bpy.ops.allset.uv_unitize() == {'CANCELLED'}
    bm, uv = _bm(ob)
    assert [l[uv].uv.copy() for f in bm.faces for l in f.loops] == before


def test_ngons_and_triangles():
    _clear()
    me = bpy.data.meshes.new("mix")
    verts = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 1, 0), (1.5, 1.6, 0), (1, 1, 0), (0, 1, 0), (0.5, 2, 0)]
    me.from_pydata(verts, [], [(0, 1, 5, 6), (1, 2, 3, 4, 5), (6, 5, 7)])
    me.uv_layers.new(name="UVMap")
    ob = bpy.data.objects.new("mix", me)
    bpy.context.collection.objects.link(ob)
    _edit(ob)
    bpy.ops.mesh.select_all(action='SELECT')
    assert bpy.ops.allset.uv_unitize() == {'FINISHED'}
    bm, uv = _bm(ob)
    for f in bm.faces:
        _check_face(f, uv)
    assert not _joined_pairs(bm, uv)


def test_blender_moves_one_face_alone():
    """After Unitize, Blender's own island pick and a move of one face's UVs leave every other face in place."""
    ob = _cube()
    bpy.ops.mesh.select_all(action='SELECT')
    assert bpy.ops.allset.uv_unitize() == {'FINISHED'}
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    bm, uv = _bm(ob)
    for f in bm.faces:
        compat.set_uv_face_selected(f, uv, f.index == 1)
    bmesh.update_edit_mesh(ob.data)
    a, r = _uv_area()
    with bpy.context.temp_override(area=a, region=r):
        bpy.ops.uv.select_linked()
        bm, uv = _bm(ob)
        picked = sorted({l.face.index for f in bm.faces for l in f.loops if compat.uv_vert_selected(l, uv)})
        assert picked == [1], picked
        before = {l.index: l[uv].uv.copy() for f in bm.faces for l in f.loops}
        bpy.ops.transform.translate(value=(0.3, 0.2, 0.0))
    bm, uv = _bm(ob)
    moved = sorted({f.index for f in bm.faces for l in f.loops if (l[uv].uv - before[l.index]).length > 1e-6})
    assert moved == [1], moved
