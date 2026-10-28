"""Step 141 lane SELECT (quant gap 3): Select menu / Ctrl+RMB (CTRL_CONVERT) conversions — Grow / Shrink Along Loop,
perimeters, To Face Path, To Shell Border, To UV Shell Border, To UVs, To UV Perimeter, To UV Edge Loop
(operators/select_convert.py). Every expected selection is Maya 2022 measured with mayapy on meshes numbered like
Maya's (research/maya/re/select_convert_141.md, research/scripts/select_convert_141_mayapy*.py).
Step doc: docs/steps/step_141_select.md; GUI: tests/gui/gui_step141_select.py."""

from importlib import import_module

import bmesh
import bpy

import kit

mm = import_module(kit.MODULE + ".marking.menus")
modal = import_module(kit.MODULE + ".marking.modal")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
notices = import_module(kit.MODULE + ".ui.notices")
sc = import_module(kit.MODULE + ".operators.select_convert")
compat = import_module(kit.MODULE + ".compat")

# Maya polyCube: vertex positions, edges, faces (vertex order) and per-corner UV numbers (map index, UV) — mayapy.
CUBE_V = [(-.5, -.5, .5), (.5, -.5, .5), (-.5, .5, .5), (.5, .5, .5), (-.5, .5, -.5), (.5, .5, -.5), (-.5, -.5, -.5),
          (.5, -.5, -.5)]
CUBE_E = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 7), (6, 0), (7, 1)]
CUBE_F = [[(0, 0), (1, 1), (3, 3), (2, 2)], [(2, 2), (3, 3), (5, 5), (4, 4)], [(4, 4), (5, 5), (7, 7), (6, 6)],
          [(6, 6), (7, 7), (1, 9), (0, 8)], [(1, 1), (7, 10), (5, 11), (3, 3)], [(6, 12), (0, 0), (2, 2), (4, 13)]]
CUBE_UV = [(.33, 0), (.6633, 0), (.33, .25), (.6633, .25), (.33, .5), (.6633, .5), (.33, .75), (.6633, .75),
           (.33, 1), (.6633, 1), (1, 0), (1, .25), (0, 0), (0, .25)]

BLOCK = [5, 6, 9, 10]                 # 2 x 2 faces in the middle of the 4 x 4 plane
CORNER = [0, 1, 4, 5]                 # 2 x 2 faces in its corner
VBLOCK = [6, 7, 8, 11, 12, 13, 16, 17, 18]
BLOCK6 = [r * 6 + c for r in (1, 2, 3) for c in (1, 2, 3)]
CORNER6 = [r * 6 + c for r in (0, 1, 2) for c in (0, 1, 2)]
BORDER_V = [0, 1, 2, 3, 4, 5, 9, 10, 14, 15, 19, 20, 21, 22, 23, 24]
BORDER_E = [0, 1, 2, 4, 6, 8, 10, 17, 19, 26, 28, 35, 36, 37, 38, 39]
BORDER_F = [0, 1, 2, 3, 4, 7, 8, 11, 12, 13, 14, 15]
ALL_UV = list(range(14))

# (case, mesh, input kind, input indices, conversion, expected kind, expected indices) — Maya's results
CASES = [
    ("grow_loop_face1", "plane", 'FACE', [5], 'GROW_LOOP', 'FACE', [1, 4, 5, 6, 9]),
    ("grow_loop_face2h", "plane", 'FACE', [5, 6], 'GROW_LOOP', 'FACE', [4, 5, 6, 7]),
    ("grow_loop_face2v", "plane", 'FACE', [5, 9], 'GROW_LOOP', 'FACE', [1, 5, 9, 13]),
    ("grow_loop_face_block", "plane", 'FACE', BLOCK, 'GROW_LOOP', 'FACE', [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14]),
    ("grow_loop_face_L", "plane6", 'FACE', [14, 15, 21], 'GROW_LOOP', 'FACE', [9, 13, 14, 15, 16, 21, 27]),
    ("grow_loop_edge1", "plane", 'EDGE', [13], 'GROW_LOOP', 'EDGE', [11, 13, 15]),
    ("grow_loop_edge2", "plane", 'EDGE', [12, 13], 'GROW_LOOP', 'EDGE', [3, 11, 12, 13, 15, 21]),
    ("grow_loop_edge_chain2", "plane", 'EDGE', [11, 13], 'GROW_LOOP', 'EDGE', [9, 11, 13, 15]),
    ("grow_loop_border_edge", "plane", 'EDGE', [2], 'GROW_LOOP', 'EDGE', [0, 2, 4]),
    ("grow_loop_corner_edge", "plane", 'EDGE', [0], 'GROW_LOOP', 'EDGE', [0, 2]),
    ("grow_loop_vtx1", "plane", 'VERT', [12], 'GROW_LOOP', 'VERT', [7, 11, 12, 13, 17]),
    ("grow_loop_vtx2", "plane", 'VERT', [12, 13], 'GROW_LOOP', 'VERT', [11, 12, 13, 14]),
    ("grow_loop_vtx_block", "plane", 'VERT', [6, 7, 11, 12], 'GROW_LOOP', 'VERT',
     [1, 2, 5, 6, 7, 8, 10, 11, 12, 13, 16, 17]),
    ("grow_loop_border_vtx2", "plane", 'VERT', [1, 2], 'GROW_LOOP', 'VERT', [0, 1, 2, 3]),
    ("shrink_loop_face4h", "plane", 'FACE', [4, 5, 6, 7], 'SHRINK_LOOP', 'FACE', [5, 6]),
    ("shrink_loop_face1", "plane", 'FACE', [5], 'SHRINK_LOOP', 'FACE', []),
    ("shrink_loop_face_row_border", "plane", 'FACE', [0, 1, 2, 3], 'SHRINK_LOOP', 'FACE', [1, 2]),
    ("shrink_loop_face3h", "plane6", 'FACE', [13, 14, 15], 'SHRINK_LOOP', 'FACE', [14]),
    ("shrink_loop_face_block", "plane6", 'FACE', BLOCK6, 'SHRINK_LOOP', 'FACE', [14]),
    ("shrink_loop_face_L", "plane6", 'FACE', [13, 14, 15, 21, 27], 'SHRINK_LOOP', 'FACE', [14, 21]),
    ("shrink_loop_face_plus", "plane6", 'FACE', [8, 13, 14, 15, 20], 'SHRINK_LOOP', 'FACE', [14]),
    ("shrink_loop_edge3", "plane", 'EDGE', [12, 13, 14], 'SHRINK_LOOP', 'EDGE', []),
    ("shrink_loop_edge_row", "plane", 'EDGE', [9, 11, 13, 15], 'SHRINK_LOOP', 'EDGE', [11, 13]),
    ("shrink_loop_edge_chain3", "plane", 'EDGE', [9, 11, 13], 'SHRINK_LOOP', 'EDGE', [11]),
    ("shrink_loop_edge_chain2", "plane", 'EDGE', [11, 13], 'SHRINK_LOOP', 'EDGE', []),
    ("shrink_loop_border_edges", "plane", 'EDGE', [0, 2, 4, 6], 'SHRINK_LOOP', 'EDGE', [2, 4]),
    ("shrink_loop_vtx3", "plane", 'VERT', [11, 12, 13], 'SHRINK_LOOP', 'VERT', []),
    ("shrink_loop_vtx_row5", "plane", 'VERT', [10, 11, 12, 13, 14], 'SHRINK_LOOP', 'VERT', [11, 12, 13]),
    ("shrink_loop_vtx_block", "plane", 'VERT', VBLOCK, 'SHRINK_LOOP', 'VERT', []),
    ("shrink_loop_vtx_block4", "plane", 'VERT', VBLOCK + [2, 22, 10, 14], 'SHRINK_LOOP', 'VERT', [7, 11, 12, 13, 17]),
    ("vtx_perimeter_faces", "plane", 'FACE', BLOCK, 'VERTEX_PERIMETER', 'VERT', [6, 7, 8, 11, 13, 16, 17, 18]),
    ("vtx_perimeter_vtx", "plane", 'VERT', VBLOCK, 'VERTEX_PERIMETER', 'VERT', [6, 7, 8, 11, 13, 16, 17, 18]),
    ("vtx_perimeter_edges", "plane", 'EDGE', [13], 'VERTEX_PERIMETER', 'VERT', [2, 3, 7, 8, 12, 13]),
    ("vtx_perimeter_corner", "plane", 'FACE', CORNER, 'VERTEX_PERIMETER', 'VERT', [0, 1, 2, 5, 7, 10, 11, 12]),
    ("vtx_perimeter_vtx1", "plane", 'VERT', [12], 'VERTEX_PERIMETER', 'VERT', [6, 7, 8, 11, 13, 16, 17, 18]),
    ("vtx_perimeter_vtx_row", "plane", 'VERT', [11, 12, 13], 'VERTEX_PERIMETER', 'VERT',
     [5, 6, 7, 8, 9, 10, 14, 15, 16, 17, 18, 19]),
    ("vtx_perimeter_edges_loop", "plane", 'EDGE', [11, 13], 'VERTEX_PERIMETER', 'VERT', [1, 2, 3, 6, 8, 11, 12, 13]),
    ("vtx_perimeter_edges_square", "plane", 'EDGE', [11, 12, 14, 20], 'VERTEX_PERIMETER', 'VERT', [6, 7, 11, 12]),
    ("vtx_perimeter_vtx_partial", "plane", 'VERT', [6, 7, 11, 12, 13], 'VERTEX_PERIMETER', 'VERT', [6, 7, 11, 12]),
    ("vtx_perimeter_cube_all", "cube", 'FACE', [0, 1, 2, 3, 4, 5], 'VERTEX_PERIMETER', 'VERT', []),
    ("edge_perimeter_faces", "plane", 'FACE', BLOCK, 'EDGE_PERIMETER', 'EDGE', [11, 12, 13, 16, 21, 25, 29, 31]),
    ("edge_perimeter_corner", "plane", 'FACE', CORNER, 'EDGE_PERIMETER', 'EDGE', [0, 1, 2, 5, 10, 14, 18, 20]),
    ("edge_perimeter_vtx", "plane", 'VERT', VBLOCK, 'EDGE_PERIMETER', 'EDGE', [11, 12, 13, 16, 21, 25, 29, 31]),
    ("edge_perimeter_edges", "plane", 'EDGE', [13], 'EDGE_PERIMETER', 'EDGE', [4, 5, 7, 14, 16, 22]),
    ("edge_perimeter_vtx1", "plane", 'VERT', [12], 'EDGE_PERIMETER', 'EDGE', [11, 12, 13, 16, 21, 25, 29, 31]),
    ("face_perimeter_faces", "plane6", 'FACE', BLOCK6, 'FACE_PERIMETER', 'FACE', [7, 8, 9, 13, 15, 19, 20, 21]),
    ("face_perimeter_corner", "plane6", 'FACE', CORNER6, 'FACE_PERIMETER', 'FACE', [0, 1, 2, 6, 8, 12, 13, 14]),
    ("face_perimeter_vtx", "plane", 'VERT', [12], 'FACE_PERIMETER', 'VERT', [12]),          # kept: no face inside
    ("face_perimeter_edge", "plane", 'EDGE', [13], 'FACE_PERIMETER', 'EDGE', [13]),
    ("face_perimeter_vtx_block", "plane", 'VERT', VBLOCK, 'FACE_PERIMETER', 'FACE', [5, 6, 9, 10]),
    ("face_path_edge1", "plane", 'EDGE', [13], 'FACE_PATH', 'FACE', [2, 6, 10, 14]),
    ("face_path_edge_h", "plane", 'EDGE', [12], 'FACE_PATH', 'FACE', [4, 5, 6, 7]),
    ("face_path_edge2", "plane", 'EDGE', [13, 14], 'FACE_PATH', 'FACE', [2, 4, 5, 6, 7, 10, 14]),
    ("face_path_cube", "cube", 'EDGE', [0], 'FACE_PATH', 'FACE', [0, 1, 2, 3]),
    ("face_path_cube_e4", "cube", 'EDGE', [4], 'FACE_PATH', 'FACE', [0, 2, 4, 5]),
    ("face_path_face", "plane", 'FACE', [5], 'FACE_PATH', 'FACE', [1, 4, 5, 6, 7, 9, 13]),
    ("face_path_vtx", "plane", 'VERT', [12], 'FACE_PATH', 'FACE', [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14]),
    ("shell_border_plane_face", "plane", 'FACE', [5], 'SHELL_BORDER', 'FACE', []),
    ("shell_border_plane_vtx", "plane", 'VERT', [12], 'SHELL_BORDER', 'VERT', []),
    ("shell_border_cube_face", "cube", 'FACE', [0], 'SHELL_BORDER', 'FACE', []),
    ("shell_border_open_cube_face", "open_cube", 'FACE', [0], 'SHELL_BORDER', 'FACE', [0, 1, 3, 4]),
    ("shell_border_open_cube_vtx", "open_cube", 'VERT', [0], 'SHELL_BORDER', 'VERT', []),
    ("shell_border_plane_border_face", "plane", 'FACE', [0], 'SHELL_BORDER', 'FACE', BORDER_F),
    ("shell_border_plane_border_vtx", "plane", 'VERT', [0], 'SHELL_BORDER', 'VERT', BORDER_V),
    ("shell_border_plane_border_edge", "plane", 'EDGE', [0], 'SHELL_BORDER', 'EDGE', BORDER_E),
    ("uv_shell_border_plane", "plane", 'FACE', [5], 'UV_SHELL_BORDER', 'FACE', BORDER_F),
    ("uv_shell_border_plane_vtx", "plane", 'VERT', [12], 'UV_SHELL_BORDER', 'VERT', BORDER_V),
    ("uv_shell_border_plane_edge", "plane", 'EDGE', [13], 'UV_SHELL_BORDER', 'EDGE', BORDER_E),
    ("uv_shell_border_cube", "cube", 'FACE', [0], 'UV_SHELL_BORDER', 'FACE', []),
    ("uv_shell_border_cube_edge", "cube", 'EDGE', [0], 'UV_SHELL_BORDER', 'EDGE', []),
    ("uv_shell_border_open_cube_face", "open_cube", 'FACE', [0], 'UV_SHELL_BORDER', 'FACE', [0, 1, 3, 4]),
    ("to_uvs_face", "plane", 'FACE', [5], 'UVS', 'UV', [6, 7, 11, 12]),
    ("to_uvs_plane_vtx", "plane", 'VERT', [12], 'UVS', 'UV', [12]),
    ("to_uvs_cube_face", "cube", 'FACE', [0], 'UVS', 'UV', [0, 1, 2, 3]),
    ("to_uvs_cube_f1", "cube", 'FACE', [1], 'UVS', 'UV', [2, 3, 4, 5]),
    ("to_uvs_cube_vtx", "cube", 'VERT', [0], 'UVS', 'UV', [0, 8]),
    ("to_uvs_cube_vtx2", "cube", 'VERT', [2], 'UVS', 'UV', [2]),
    ("to_uvs_cube_edge", "cube", 'EDGE', [0], 'UVS', 'UV', [0, 1, 8, 9]),
    ("to_uvs_cube_e4", "cube", 'EDGE', [4], 'UVS', 'UV', [0, 2]),
    ("uv_perimeter_faces", "plane", 'FACE', BLOCK, 'UV_PERIMETER', 'UV', [6, 7, 8, 11, 13, 16, 17, 18]),
    ("uv_perimeter_vtx1", "plane", 'VERT', [12], 'UV_PERIMETER', 'UV', [6, 7, 8, 11, 13, 16, 17, 18]),
    ("uv_perimeter_edge", "plane", 'EDGE', [13], 'UV_PERIMETER', 'UV', [2, 3, 7, 8, 12, 13]),
    ("uv_perimeter_cube_face", "cube", 'FACE', [0, 1], 'UV_PERIMETER', 'UV', [0, 1, 2, 3, 4, 5, 8, 9, 11, 13]),
    ("uv_perimeter_cube_f0", "cube", 'FACE', [0], 'UV_PERIMETER', 'UV', [0, 1, 2, 3, 8, 9]),
    ("uv_perimeter_cube_vtx0", "cube", 'VERT', [0], 'UV_PERIMETER', 'UV', [1, 2, 3, 4, 6, 7, 9, 10, 12, 13]),
    ("uv_edge_loop_plane", "plane", 'EDGE', [13], 'UV_EDGE_LOOP', 'EDGE', [9, 11, 13, 15]),
    ("uv_edge_loop_plane_v", "plane", 'EDGE', [12], 'UV_EDGE_LOOP', 'EDGE', [3, 12, 21, 30]),
    *[(f"uv_edge_loop_cube_e{i}", "cube", 'EDGE', [i], 'UV_EDGE_LOOP', 'EDGE', [i]) for i in range(12)],
]
# With UV Sync Selection off (the kit's Maya UV component) To UV Shell Border reads the selected UVs.
UV_CASES = [
    ("uv_shell_border_plane_map12", "plane", [12], BORDER_V),
    ("uv_shell_border_cube_map0", "cube", [0], ALL_UV),
    ("uv_shell_border_cube_map6", "cube", [6], ALL_UV),
]

PATHS = {   # Select menu path -> (operator, kind) the step maps
    "Select/Grow Along Loop": 'GROW_LOOP', "Select/Shrink Along Loop": 'SHRINK_LOOP',
    "Select/Convert Selection/To Vertex Perimeter": 'VERTEX_PERIMETER',
    "Select/Convert Selection/To Edge Perimeter": 'EDGE_PERIMETER',
    "Select/Convert Selection/To Face Perimeter": 'FACE_PERIMETER',
    "Select/Convert Selection/To Face Path": 'FACE_PATH', "Select/Convert Selection/To Shell Border": 'SHELL_BORDER',
    "Select/Convert Selection/To UV Shell Border": 'UV_SHELL_BORDER', "Select/Convert Selection/To UVs": 'UVS',
    "Select/Convert Selection/To UV Perimeter": 'UV_PERIMETER',
    "Select/Convert Selection/To UV Edge Loop": 'UV_EDGE_LOOP',
}


# --- meshes numbered like Maya's ------------------------------------------------------------------------

def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def _plane_bm(n):
    """Maya polyPlane -sx n -sy n numbering: vertex r * (n+1) + c, edges per vertex (right, then down), face r * n + c;
    one UV per vertex (map index = vertex index)."""
    bm = bmesh.new()
    vs = [bm.verts.new((c, -r, 0.0)) for r in range(n + 1) for c in range(n + 1)]
    for i, v in enumerate(vs):
        r, c = divmod(i, n + 1)
        if c < n:
            bm.edges.new((v, vs[i + 1]))
        if r < n:
            bm.edges.new((v, vs[i + n + 1]))
    uv = bm.loops.layers.uv.new("map1")
    for r in range(n):
        for c in range(n):
            i = r * (n + 1) + c
            f = bm.faces.new((vs[i], vs[i + 1], vs[i + n + 2], vs[i + n + 1]))
            for lp in f.loops:
                k = lp.vert.index
                lp[uv].uv = ((k % (n + 1)) / n, 1.0 - (k // (n + 1)) / n)
    return bm


def _cube_bm(open_face=None):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in CUBE_V]
    for a, b in CUBE_E:
        bm.edges.new((vs[a], vs[b]))
    uv = bm.loops.layers.uv.new("map1")
    for i, corners in enumerate(CUBE_F):
        if i == open_face:
            continue
        f = bm.faces.new([vs[v] for v, _m in corners])
        for lp, (_v, m) in zip(f.loops, corners):
            lp[uv].uv = CUBE_UV[m]
    return bm


def _make(kind):
    _clear()
    bm = {"plane": lambda: _plane_bm(4), "plane6": lambda: _plane_bm(6), "cube": _cube_bm,
          "open_cube": lambda: _cube_bm(open_face=1)}[kind]()
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.index_update()
    me = bpy.data.meshes.new("pShape1")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("p1", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    return ob


def _bm(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.ensure_lookup_table()
    return bm


def _seq(bm, kind):
    return {'VERT': bm.verts, 'EDGE': bm.edges, 'FACE': bm.faces}[kind]


def _select(ob, kind, idx):
    ts = bpy.context.scene.tool_settings
    ts.mesh_select_mode = (kind == 'VERT', kind == 'EDGE', kind == 'FACE')
    bm = _bm(ob)
    for seq in (bm.verts, bm.edges, bm.faces):
        for x in seq:
            x.select_set(False)
    for i in idx:
        _seq(bm, kind)[i].select_set(True)
    bmesh.update_edit_mesh(ob.data)


def _map_index(mesh_kind, lp, uv):
    if mesh_kind.startswith("plane"):
        return lp.vert.index
    p = lp[uv].uv
    return next(i for i, q in enumerate(CUBE_UV) if abs(p.x - q[0]) < 1e-4 and abs(p.y - q[1]) < 1e-4)


def _result(ob, mesh_kind, kind):
    bm = _bm(ob)
    if kind == 'UV':
        uv = bm.loops.layers.uv.active
        return sorted({_map_index(mesh_kind, lp, uv) for f in bm.faces if f.select for lp in f.loops
                       if compat.uv_vert_selected(lp, uv)})
    return sorted(x.index for x in _seq(bm, kind) if x.select)


def _mode_kind():
    return sc.mode_kind(bpy.context.scene.tool_settings.mesh_select_mode)


# --- tests ----------------------------------------------------------------------------------------------

def test_conversions_match_maya():
    bad = []
    for name, mesh_kind, kind_in, idx, what, kind_out, expected in CASES:
        ob = _make(mesh_kind)
        _select(ob, kind_in, idx)
        res = bpy.ops.allset.select_convert(kind=what)
        assert res == {'FINISHED'}, (name, res)
        ts = bpy.context.scene.tool_settings
        got = _result(ob, mesh_kind, kind_out)
        if kind_out == 'UV':
            ok = not ts.use_uv_select_sync and got == expected
        else:
            ok = ts.use_uv_select_sync and _mode_kind() == kind_out and got == expected
        if not ok:
            bad.append((name, kind_out, _mode_kind(), got, expected))
    print(f"{len(CASES) - len(bad)} / {len(CASES)} conversions = Maya")
    assert not bad, "\n".join(map(str, bad))


def test_uv_component_source():
    """Sync off = Maya UV component: To UV Shell Border reads the selected UVs and selects UVs."""
    for name, mesh_kind, maps, expected in UV_CASES:
        ob = _make(mesh_kind)
        ts = bpy.context.scene.tool_settings
        ts.use_uv_select_sync = False
        bm = _bm(ob)
        uv = bm.loops.layers.uv.active
        for f in bm.faces:
            f.select_set(True)
            for lp in f.loops:
                compat.set_uv_vert_selected(lp, uv, _map_index(mesh_kind, lp, uv) in maps)
        bmesh.update_edit_mesh(ob.data)
        assert bpy.ops.allset.select_convert(kind='UV_SHELL_BORDER') == {'FINISHED'}
        got = _result(ob, mesh_kind, 'UV')
        assert not ts.use_uv_select_sync and got == expected, (name, got, expected)
    # a mesh-component conversion from UVs: their vertices, back to Maya's vertex component (sync on)
    ob = _make("plane")
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    bm = _bm(ob)
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        f.select_set(True)
        for lp in f.loops:
            compat.set_uv_vert_selected(lp, uv, lp.vert.index == 12)
    bmesh.update_edit_mesh(ob.data)
    assert bpy.ops.allset.select_convert(kind='EDGE_PERIMETER') == {'FINISHED'}
    assert ts.use_uv_select_sync and _mode_kind() == 'EDGE'
    assert _result(ob, "plane", 'EDGE') == [11, 12, 13, 16, 21, 25, 29, 31]
    # Blender's factory state (sync off, a mesh selection): the mesh selection converts, sync stays off
    ob = _make("plane")
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    _select(ob, 'VERT', [12])
    assert bpy.ops.allset.select_convert(kind='GROW_LOOP') == {'FINISHED'}
    assert not ts.use_uv_select_sync and _mode_kind() == 'VERT'
    assert _result(ob, "plane", 'VERT') == [7, 11, 12, 13, 17]


def test_menu_paths_mapped():
    for path, kind in PATHS.items():
        assert menu_map.MAP.get(path) == ("allset.select_convert", {"kind": kind}), path
    for path, comp in (("Select/Components/UV", 'UV'), ("Select/Components/UV Shell", 'SHELL')):
        assert menu_map.MAP.get(path) == ("allset.uv_component", {"mode": comp}), path
    for label, t in (("To Vertices", 'VERT'), ("To Edges", 'EDGE'), ("To Faces", 'FACE')):
        assert menu_map.MAP["Select/Convert Selection/" + label] == ("allset.convert_selection", {"type": t})
    # what stays greyed has a notice (step 101)
    for path in ("Select/Components/Vertex Face", "Select/Convert Selection/To Vertex Faces"):
        assert path not in menu_map.MAP and notices.greyed_notice(path), path
    # the UV Editor's Select menu runs the same conversions
    for label in ("Grow Along Loop", "Convert Selection/To Face Path", "Convert Selection/To UV Perimeter"):
        assert menu_map.MAP["UV Editor/Select/" + label][0] == "allset.select_convert", label


def test_marking_menu_entries():
    entries = {p: a for p, _l, a in mm.label_walk(mm.MENUS["CTRL_CONVERT"], "CTRL_CONVERT")}
    greyed = [p for p, a in entries.items() if mm.is_greyed(a)]
    assert not greyed, greyed
    for p in ("CTRL_CONVERT/Grow Selection/Grow Along Loop",
              "CTRL_CONVERT/Shrink Selection/Shrink Selection Along Loop", "CTRL_CONVERT/To UVs/To UV Perimeter",
              "CTRL_CONVERT/To UVs/To UVs", "CTRL_CONVERT/To Face Path", "CTRL_CONVERT/To Shell Border",
              "CTRL_CONVERT/To Vertices/To Vertex Perimeter", "CTRL_CONVERT/To Faces/To Face Perimeter",
              "CTRL_CONVERT/To Edges/To Edge Perimeter"):
        a = entries[p]
        assert isinstance(a, tuple) and a[0] == "item" and a[1] in menu_map.MAP, (p, a)
        assert p not in notices.MARKING, p
    ob = _make("plane")
    _select(ob, 'FACE', [5, 6])
    for p, a in entries.items():
        if isinstance(a, tuple) and a[0] == "item":
            assert modal.poll_action(a), p
    # run through the marking-menu path: allset.menu_item -> the Select menu's operator
    modal.run_action(bpy.context, entries["CTRL_CONVERT/Grow Selection/Grow Along Loop"])
    assert _result(ob, "plane", 'FACE') == [4, 5, 6, 7]
    modal.run_action(bpy.context, entries["CTRL_CONVERT/To Vertices/To Vertex Perimeter"])
    assert _mode_kind() == 'VERT' and _result(ob, "plane", 'VERT') == [5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    modal.run_action(bpy.context, entries["CTRL_CONVERT/To Edges/To Edges"])
    assert _mode_kind() == 'EDGE' and len(_result(ob, "plane", 'EDGE')) == 23, _result(ob, "plane", 'EDGE')


def test_menu_item_runs():
    ob = _make("plane")
    _select(ob, 'EDGE', [13])
    assert bpy.ops.allset.menu_item(item="Select/Convert Selection/To Face Path") == {'FINISHED'}
    assert _mode_kind() == 'FACE' and _result(ob, "plane", 'FACE') == [2, 6, 10, 14]
    # To Edges from vertices = the edges they touch (Maya ConvertSelectionToEdges), not a cleared selection
    _select(ob, 'VERT', [12])
    assert bpy.ops.allset.menu_item(item="Select/Convert Selection/To Edges") == {'FINISHED'}
    assert _mode_kind() == 'EDGE' and _result(ob, "plane", 'EDGE') == [14, 20, 22, 23]
    bpy.ops.object.mode_set(mode='OBJECT')


def test_kit_cube_isolated_vertex():
    """The kit's Maya cube (operators/create.py): an isolated vertex grows along its loops to its 3 neighbours."""
    _clear()
    bpy.ops.allset.create(kind='CUBE')
    ob = bpy.context.active_object
    if bpy.context.mode != 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='EDIT')
    _select(ob, 'VERT', [0])
    bm = _bm(ob)
    want = sorted({0} | {e.other_vert(bm.verts[0]).index for e in bm.verts[0].link_edges})
    print("kit cube", len(bm.verts), [len(v.link_edges) for v in bm.verts], list(ob.modifiers))
    assert bpy.ops.allset.menu_item(item="Select/Grow Along Loop") == {'FINISHED'}
    assert _result(ob, "cube", 'VERT') == want, (_result(ob, "cube", 'VERT'), want)
    bpy.ops.object.mode_set(mode='OBJECT')
