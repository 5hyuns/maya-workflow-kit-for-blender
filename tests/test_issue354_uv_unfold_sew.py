"""#354: UV Editor Unfold froze Blender for minutes on a dense shell (each UV was compared with every UV of its shell
to find the shell's UV mean, twice per Unfold), and UV > Sew UV Edges / Merge UVs / Cut UV Edges did nothing for edges
picked in the 3D View while UV Sync Selection was off (they read only the UV Editor's own selection).

Like Maya (one component selection for the viewport and the UV Editor): outside the UV Editor and the kit's UV
component mode, with no UV picked, these commands take what the 3D View shows selected. In the UV Editor and in UV
mode they keep reading the UV selection."""

import time
from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

import kit

uvt = import_module(kit.MODULE + ".operators.uv_tools")


def _clear():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _bm(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.ensure_lookup_table()
    return bm, bm.loops.layers.uv.active


def _shells(ob):
    bm, uv = _bm(ob)
    return len(uvt.islands(bm, uv))


def _top(bm):
    return max(bm.faces, key=lambda f: f.calc_center_median().z)


def _cube_apart(sync, gap=0.3):
    """A cube with its top face cut out of the UVs and moved ``gap`` along U; one top border edge picked in the
    3D View (mesh selection only, no UV picked), edge select mode. Returns (object, that edge's index)."""
    _clear()
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = sync
    ts.mesh_select_mode = (False, True, False)
    bm, uv = _bm(ob)
    top = _top(bm)

    def joined(e):           # the top face and its neighbour across ``e`` share both UVs (the cross's fold)
        other = next(f for f in e.link_faces if f is not top)
        return all((uvt._uv_at(top, v, uv) - uvt._uv_at(other, v, uv)).length < 1e-6 for v in e.verts)
    edge = next(e for e in sorted(top.edges, key=lambda e: e.index) if joined(e))
    for e in top.edges:
        e.seam = True
    for lp in top.loops:
        lp[uv].uv.x += gap
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for f in bm.faces:
        for lp in f.loops:
            lp.uv_select_vert = lp.uv_select_edge = False
        f.uv_select = False
    edge.select = True
    for v in edge.verts:
        v.select = True
    bmesh.update_edit_mesh(ob.data)
    return ob, edge.index


# --- Unfold on a dense shell -------------------------------------------------------------------------------------

def _grid(cuts):
    """One flat grid of ``cuts`` x ``cuts`` quads: a single UV shell."""
    _clear()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=cuts, y_subdivisions=cuts, size=2)
    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.mesh.select_all(action='DESELECT')
    return ob


def test_point_mean_counts_each_uv_once():
    """The shell's UV mean: every UV (vertex + coordinate) once, also where a vertex has several UVs."""
    ob, _e = _cube_apart(True)
    bm, uv = _bm(ob)
    faces = list(bm.faces)
    pts = []
    for f in faces:
        for lp in f.loops:
            p = lp[uv].uv.copy()
            if not any(v is lp.vert and (q - p).length < 1e-6 for v, q in pts):
                pts.append((lp.vert, p))
    want = sum((q for _v, q in pts), Vector((0.0, 0.0))) / len(pts)
    got = uvt._point_mean(faces, uv)
    assert (got - want).length < 1e-9, (got, want)
    assert len(pts) > len(bm.verts)       # the cube's UV cross has several UVs on some vertices


def test_unfold_dense_shell_stays_interactive():
    """A 14 400-face shell: Unfold took minutes (the whole UI froze, which reads as a crash); now a few seconds."""
    ob = _grid(120)
    bm, uv = _bm(ob)
    faces = list(bm.faces)
    mean0 = uvt._point_mean(faces, uv)
    area0 = sum(uvt._uv_area(f, uv) for f in faces)
    t = time.perf_counter()
    assert bpy.ops.allset.uv_unfold() == {'FINISHED'}
    dt = time.perf_counter() - t
    assert dt < 8.0, f"Unfold on 14 400 faces took {dt:.1f} s"
    bm, uv = _bm(ob)
    faces = list(bm.faces)
    assert _shells(ob) == 1
    assert (uvt._point_mean(faces, uv) - mean0).length < 1e-4          # the shell stays where it was
    area = sum(uvt._uv_area(f, uv) for f in faces)
    assert abs(area - area0) / area0 < 1e-3, (area, area0)            # and keeps its UV area


def test_unfold_with_picks_in_two_meshes_keeps_their_shells():
    """Two meshes in edit mode, one face picked in each: Unfold works on each picked shell, whole. Blender's unwrap
    works on every mesh in edit mode, so the other mesh's lone picked face was unwrapped on its own and torn off
    its shell (1 -> 2 shells in both meshes)."""
    _clear()
    obs = []
    for x in (0.0, 3.0):
        bpy.ops.mesh.primitive_uv_sphere_add(location=(x, 0.0, 0.0))
        obs.append(bpy.context.object)
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    means = []
    for ob in obs:
        bm, uv = _bm(ob)
        for el in (*bm.verts, *bm.edges, *bm.faces):
            el.select = False
        bm.faces[10].select_set(True)
        means.append(uvt._point_mean(list(bm.faces), uv).copy())
        bmesh.update_edit_mesh(ob.data)
    assert [_shells(ob) for ob in obs] == [1, 1]
    assert bpy.ops.allset.uv_unfold() == {'FINISHED'}
    assert [_shells(ob) for ob in obs] == [1, 1]
    for ob, mean in zip(obs, means):
        bm, uv = _bm(ob)
        assert (uvt._point_mean(list(bm.faces), uv) - mean).length < 1e-4, ob.name
        assert [f.index for f in bm.faces if f.select] == [10]           # each mesh keeps its own pick


# --- Sew / Merge / Cut on a 3D View selection with UV Sync Selection off -----------------------------------------

def test_sew_takes_the_3d_view_edges_with_sync_off():
    for sync in (False, True):
        ob, idx = _cube_apart(sync)
        assert _shells(ob) == 2
        assert bpy.ops.allset.uv_sew() == {'FINISHED'}, sync
        bm, _uv = _bm(ob)
        assert _shells(ob) == 1, sync
        assert not bm.edges[idx].seam
        assert sum(e.seam for e in bm.edges) == 3          # only the picked edge was sewn


def test_main_menu_sew_merge_cut_with_sync_off():
    ob, idx = _cube_apart(False)
    assert bpy.ops.allset.menu_item(item="UV/Sew UV Edges") == {'FINISHED'}
    assert _shells(ob) == 1
    # Merge UVs: the picked edge's UVs on the two sides lie 0.005 apart (inside the 0.01 threshold)
    ob, idx = _cube_apart(False, gap=0.005)
    assert _shells(ob) == 2
    assert bpy.ops.allset.menu_item(item="UV/Merge UVs") == {'FINISHED'}
    assert _shells(ob) == 1
    # Cut UV Edges: an edge inside a shell gets its seam and splits off
    ob, idx = _cube_apart(False)
    bm, _uv = _bm(ob)
    inner = next(e for e in bm.edges if not e.seam and all(f is not _top(bm) for f in e.link_faces))
    for el in (*bm.verts, *bm.edges):
        el.select = False
    inner.select = True
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.menu_item(item="UV/Cut UV Edges") == {'FINISHED'}
    bm, _uv = _bm(ob)
    assert bm.edges[inner.index].seam


def test_a_uv_pick_still_wins_with_sync_off():
    """With a UV picked (UV Editor selection), the commands read only that, not the other mesh-selected edges."""
    ob, idx = _cube_apart(False)
    bm, uv = _bm(ob)
    top = _top(bm)
    for f in bm.faces:
        f.select_set(True)                   # the faces shown in the UV Editor (sync off): every edge selected too
    other = next(e for e in top.edges if e.index != idx)
    lp = next(lp for lp in top.loops if lp.edge is other)
    lp.uv_select_edge = True                  # one UV edge picked: the top's other border edge
    lp.uv_select_vert = lp.link_loop_next.uv_select_vert = True
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.uv_sew() == {'FINISHED'}
    bm, _uv = _bm(ob)
    assert not bm.edges[other.index].seam
    assert sum(e.seam for e in bm.edges) == 3      # the picked UV edge only, not every selected mesh edge


def test_uv_mode_keeps_the_uv_selection():
    """In the kit's UV component mode the 3D View shows UVs: with no UV picked the commands still do nothing."""
    ob, _idx = _cube_apart(True)
    assert bpy.ops.allset.uv_component(mode='UV_EDGE') == {'FINISHED'}
    assert uvt.in_uv_mode(bpy.context.scene)
    bpy.ops.uv.select_all(action='DESELECT')
    seams = sum(e.seam for e in _bm(ob)[0].edges)
    assert bpy.ops.allset.uv_sew() == {'CANCELLED'}
    assert sum(e.seam for e in _bm(ob)[0].edges) == seams
    assert _shells(ob) == 2
    bpy.ops.allset.uv_component(mode='EDGE')


# --- the other main UV menu commands that read a selection: Delete UVs, Split UVs, Auto Seams --------------------

def _pick_top_face(ob):
    bm, _uv = _bm(ob)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm.select_mode = {'FACE'}
    _top(bm).select_set(True)
    bmesh.update_edit_mesh(ob.data)
    return _top(bm).index


def test_main_menu_delete_and_split_with_sync_off():
    for sync in (True, False):
        # Delete UVs: the face picked in the 3D View loses its UVs (they collapse to 0, 0)
        ob, _idx = _cube_apart(sync)
        top = _pick_top_face(ob)
        assert bpy.ops.allset.menu_item(item="UV/Delete UVs") == {'FINISHED'}
        bm, uv = _bm(ob)
        assert all(lp[uv].uv.length < 1e-9 for lp in bm.faces[top].loops), sync
        assert sum(all(lp[uv].uv.length < 1e-9 for lp in f.loops) for f in bm.faces) == 1, sync
        # Split UVs: the edge picked in the 3D View (inside a shell) is cut there
        ob, _idx = _cube_apart(sync)
        bm, _uv = _bm(ob)
        inner = next(e for e in bm.edges if not e.seam and all(f is not _top(bm) for f in e.link_faces))
        for el in (*bm.verts, *bm.edges):
            el.select = False
        inner.select = True
        for v in inner.verts:
            v.select = True
        bm.select_mode = {'EDGE'}
        bmesh.update_edit_mesh(ob.data)
        assert bpy.ops.allset.menu_item(item="UV/Split UVs") == {'FINISHED'}
        bm, _uv = _bm(ob)
        assert bm.edges[inner.index].seam, sync
        assert sum(e.seam for e in bm.edges) == 5, sync        # the top face's 4 + the picked one


def _two_closed_cubes(sync):
    """One mesh, two cubes with one closed UV shell each (a UV per vertex); every face of the first cube picked in
    the 3D View, face select mode."""
    _clear()
    from mathutils import Matrix
    me = bpy.data.meshes.new("two")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((3.0, 0.0, 0.0)))
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            co = lp.vert.co
            lp[uv].uv = (co.x * 0.1 + co.z * 0.03, co.y * 0.1 + co.z * 0.05)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("two", me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = sync
    ts.mesh_select_mode = (False, False, True)
    bm, _uv = _bm(ob)
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for f in bm.faces:
        for lp in f.loops:
            lp.uv_select_vert = lp.uv_select_edge = False
        if f.calc_center_median().x < 1.5:
            f.select_set(True)
    bmesh.update_edit_mesh(ob.data)
    return ob


def test_main_menu_auto_seams_takes_the_3d_view_faces_with_sync_off():
    """Auto Seams on the cube picked in the 3D View: seams on that cube only, with UV Sync on or off."""
    for sync in (True, False):
        ob = _two_closed_cubes(sync)
        assert _shells(ob) == 2
        assert bpy.ops.allset.menu_item(item="UV/Auto Seams") == {'FINISHED'}
        bm, _uv = _bm(ob)
        seams = [e for e in bm.edges if e.seam]
        assert seams, sync
        assert all(max(v.co.x for v in e.verts) < 1.5 for e in seams), sync     # none on the second cube
