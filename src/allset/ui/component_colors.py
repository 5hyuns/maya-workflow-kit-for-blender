# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya component colours in mesh edit mode.

Maya 2022 draws a mesh in component mode with its own colours ( viewport, pixels of
, 08_verts_selected.png, 09_edges_selected.png at UI scale 1.0):
every visible edge 1 px hilite #64dcff; vertex mode: unselected vertices 3 px #c800c8 (hiliteComponent), selected
vertices 4 px #fdff88 (the screen value of polyVertex); edge mode: selected edges #e3ac79 (polyEdge); face mode:
selected faces a 1-in-4 pixel stipple #e3ac79 (polyFace), no fill.

Blender draws edit meshes with the user's theme (orange / black). The kit ships no theme (step 130, ),
so this POST_VIEW handler draws the Maya colours on top of Blender's own edit-mesh drawing (which stays under it).

Reading the edit mesh (probe tmp/p134, 101 124 vertices): the evaluated object's ``to_mesh()`` is the current
BMesh with ``.select_vert/edge/poly`` in ~4 ms; BMesh Python loops cost ~0.4 s. With a modifier shown in edit mode
the evaluated mesh is not the cage, so the cage is read from the BMesh, only up to ``BMESH_LIMIT`` vertices
(bigger meshes keep Blender's drawing). Arrays and GPU batches are cached per object and re-read when a
depsgraph update names the object or its mesh.
"""

import bpy
import numpy as np

HILITE = "#64dcff"          # displayColor.hilite (18): the object being edited, every edge
VERT = "#c800c8"            # displayColor.hiliteComponent (9): unselected vertices
VERT_SEL = "#fdff88"        # selected vertices as Maya draws them (08_verts_selected.png; polyVertex 17 = #ffff00)
EDGE_SEL = "#e3ac79"        # selected edges (09_edges_selected.png; polyEdge 21 = #e4ac79)
FACE_SEL = "#e3ac79"        # selected face stipple (07_faces_selected.png; polyFace 21)
VERT_PX = 3.0               # Maya pixel sizes at UI scale 1.0 (08_verts_selected.png)
VERT_SEL_PX = 4.0
LINE_PX = 2.0               # Maya's lines are 1 px, but Blender's own edit edges under them are ~2 px anti-aliased
                            # (x UI scale): 1 px left Blender's colours on both sides (GUI shot, )
BMESH_LIMIT = 50000         # cage read from the BMesh (modifiers shown in edit mode) only up to this many vertices
DEPTH_BIAS = 0.0005         # relative pull toward the camera (soft_overlay uses 0.001 and draws over this)
POINT_BIAS = 0.003          # vertices: Blender's own edit vertices write depth well in front of the surface

_handle = []
_shader = {}
_cache = {}                 # (object pointer, mesh pointer) -> _State
_dirty = set()              # object / mesh names a depsgraph update touched since the last read
_times = []


# --- pure helpers (tests/test_step134_selection.py) -----------------------------------------------

def srgb(hex_str):
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


class MeshArrays:
    """Edit cage arrays: co (n, 3) float32 object space, edges (e, 2) int32, per element select / hide bools,
    polygons as loop_start / loop_total into corner_vert."""
    __slots__ = ("co", "edges", "vsel", "vhide", "esel", "ehide", "fsel", "fhide", "loop_start", "loop_total",
                 "corner_vert")

    def __init__(self, co, edges, vsel=None, vhide=None, esel=None, ehide=None, fsel=None, fhide=None,
                 loop_start=None, loop_total=None, corner_vert=None):
        self.co = np.asarray(co, dtype=np.float32).reshape(-1, 3)
        self.edges = np.asarray(edges, dtype=np.int32).reshape(-1, 2)
        n, e = len(self.co), len(self.edges)
        f = 0 if loop_start is None else len(loop_start)

        def flags(a, k):
            return np.zeros(k, bool) if a is None else np.asarray(a, dtype=bool).reshape(-1)
        self.vsel, self.vhide = flags(vsel, n), flags(vhide, n)
        self.esel, self.ehide = flags(esel, e), flags(ehide, e)
        self.fsel, self.fhide = flags(fsel, f), flags(fhide, f)
        self.loop_start = np.zeros(0, np.int32) if loop_start is None else np.asarray(loop_start, np.int32)
        self.loop_total = np.zeros(0, np.int32) if loop_total is None else np.asarray(loop_total, np.int32)
        self.corner_vert = np.zeros(0, np.int32) if corner_vert is None else np.asarray(corner_vert, np.int32)


def fan_triangles(loop_start, loop_total, corner_vert, mask):
    """Vertex index triangles (t, 3) of the polygons in ``mask``, fanned from each polygon's first corner."""
    start = np.asarray(loop_start, np.int64)[mask]
    total = np.asarray(loop_total, np.int64)[mask]
    ntri = np.maximum(total - 2, 0)
    if not len(ntri) or ntri.sum() == 0:
        return np.zeros((0, 3), np.int32)
    first = np.repeat(start, ntri)
    # i = 1 .. total-2 within each polygon
    offs = np.arange(ntri.sum()) - np.repeat(np.cumsum(ntri) - ntri, ntri) + 1
    cv = np.asarray(corner_vert, np.int64)
    return np.stack([cv[first], cv[first + offs], cv[first + offs + 1]], axis=1).astype(np.int32)


def layers(m, select_mode):
    """What to draw for the Maya component look: dict of index arrays into ``m.co``.

    edges: every visible edge (hilite); verts / verts_sel (vertex mode); edges_sel (edge mode); tris (face mode,
    selected visible faces). Hidden elements are never drawn."""
    vert_mode, edge_mode, face_mode = (bool(x) for x in select_mode)
    vis_e = ~m.ehide
    out = {"edges": m.edges[vis_e]}
    if vert_mode:
        vis = ~m.vhide
        out["verts"] = np.flatnonzero(vis & ~m.vsel).astype(np.int32)
        out["verts_sel"] = np.flatnonzero(vis & m.vsel).astype(np.int32)
    if edge_mode:
        out["edges_sel"] = m.edges[vis_e & m.esel]
    if face_mode:
        out["tris"] = fan_triangles(m.loop_start, m.loop_total, m.corner_vert, m.fsel & ~m.fhide)
    return out


def use_evaluated(modifiers):
    """True when the evaluated edit mesh is the cage: no modifier is shown in edit mode."""
    return not any(md.show_viewport and md.show_in_editmode for md in modifiers)


def readable(n_verts, evaluated):
    """Whether the kit draws this mesh: the evaluated read is always fast, the BMesh read only up to BMESH_LIMIT."""
    return evaluated or n_verts <= BMESH_LIMIT


# --- reading the edit mesh -------------------------------------------------------------------------

def _attr(me, name, count):
    a = me.attributes.get(name)
    out = np.zeros(count, bool)
    if a is not None and count:
        a.data.foreach_get("value", out)
    return out


def read_evaluated(ob, depsgraph, faces=True):
    """MeshArrays of the evaluated edit mesh (no edit-mode modifiers: this is the cage); polygons only with
    ``faces`` (face select mode)."""
    ev = ob.evaluated_get(depsgraph)
    me = ev.to_mesh()
    try:
        n, e = len(me.vertices), len(me.edges)
        f, l = (len(me.polygons), len(me.loops)) if faces else (0, 0)
        co = np.empty(n * 3, np.float32)
        me.vertices.foreach_get("co", co)
        ed = np.empty(e * 2, np.int32)
        me.edges.foreach_get("vertices", ed)
        ls = np.empty(f, np.int32)
        me.polygons.foreach_get("loop_start", ls)
        lt = np.empty(f, np.int32)
        me.polygons.foreach_get("loop_total", lt)
        cv = np.empty(l, np.int32)
        me.loops.foreach_get("vertex_index", cv)
        return MeshArrays(co, ed, _attr(me, ".select_vert", n), _attr(me, ".hide_vert", n),
                          _attr(me, ".select_edge", e), _attr(me, ".hide_edge", e),
                          _attr(me, ".select_poly", f), _attr(me, ".hide_poly", f), ls, lt, cv)
    finally:
        ev.to_mesh_clear()


def read_bmesh(bm):
    """MeshArrays of the BMesh cage (Python loops: small meshes only)."""
    from itertools import chain
    bm.verts.index_update()
    n, e = len(bm.verts), len(bm.edges)
    co = np.fromiter(chain.from_iterable(v.co for v in bm.verts), np.float32, 3 * n)
    ed = np.fromiter(chain.from_iterable((x.verts[0].index, x.verts[1].index) for x in bm.edges), np.int32, 2 * e)
    lt = np.fromiter((len(f.verts) for f in bm.faces), np.int32, len(bm.faces))
    ls = (np.cumsum(lt) - lt).astype(np.int32)
    cv = np.fromiter(chain.from_iterable((v.index for v in f.verts) for f in bm.faces), np.int32, int(lt.sum()))
    return MeshArrays(co, ed,
                      np.fromiter((v.select for v in bm.verts), bool, n), np.fromiter((v.hide for v in bm.verts), bool, n),
                      np.fromiter((x.select for x in bm.edges), bool, e), np.fromiter((x.hide for x in bm.edges), bool, e),
                      np.fromiter((f.select for f in bm.faces), bool, len(bm.faces)),
                      np.fromiter((f.hide for f in bm.faces), bool, len(bm.faces)), ls, lt, cv)


class _State:
    __slots__ = ("arrays", "faces", "batches", "bkey", "name", "me_name")

    def __init__(self, ob):
        self.arrays = None
        self.faces = False          # arrays hold the polygons (read only in face select mode)
        self.batches = None
        self.bkey = None
        self.name = ob.name
        self.me_name = ob.data.name


# --- drawing ---------------------------------------------------------------------------------------

def _enabled():
    from .. import preferences
    try:
        return preferences.get().maya_component_colors
    except (KeyError, AttributeError):
        return False


def _builtin(name):
    if name not in _shader:
        import gpu
        _shader[name] = gpu.shader.from_builtin(name)
    return _shader[name]


def _stipple():
    if "stipple" not in _shader:
        import gpu
        info = gpu.types.GPUShaderCreateInfo()
        info.push_constant('MAT4', 'ModelViewProjectionMatrix')
        info.push_constant('VEC4', 'color')
        info.vertex_in(0, 'VEC3', 'pos')
        info.fragment_out(0, 'VEC4', 'fragColor')
        info.vertex_source("void main() { gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0); }")
        # Maya's face stipple: one pixel in every 2 x 2 block (07_faces_selected.png)
        info.fragment_source("void main() { ivec2 p = ivec2(gl_FragCoord.xy);"
                             " if (((p.x | p.y) & 1) != 0) { discard; } fragColor = color; }")
        _shader["stipple"] = gpu.shader.create_from_info(info)
    return _shader["stipple"]


def _linear(hex_str):
    from mathutils import Color
    c = Color(srgb(hex_str)).from_srgb_to_scene_linear()
    return (c.r, c.g, c.b, 1.0)


def _batches(st, select_mode):
    key = tuple(bool(x) for x in select_mode)
    if st.batches is not None and st.bkey == key:
        return st.batches
    from gpu_extras.batch import batch_for_shader
    m = st.arrays
    lay = layers(m, select_mode)
    flat = _builtin('UNIFORM_COLOR')
    poly = _builtin('POLYLINE_UNIFORM_COLOR')
    out = []

    def lines(idx, color, width):
        if len(idx):
            out.append(('LINES', poly, batch_for_shader(poly, 'LINES', {"pos": m.co[idx.reshape(-1)]}), color, width))

    def points(idx, color, size):
        if len(idx):
            out.append(('POINTS', flat, batch_for_shader(flat, 'POINTS', {"pos": m.co[idx]}), color, size))
    if "tris" in lay and len(lay["tris"]):
        sh = _stipple()
        out.append(('TRIS', sh, batch_for_shader(sh, 'TRIS', {"pos": m.co}, indices=lay["tris"]),
                    _linear(FACE_SEL), 0.0))
    lines(lay["edges"], srgb(HILITE) + (1.0,), LINE_PX)
    if "edges_sel" in lay:
        lines(lay["edges_sel"], srgb(EDGE_SEL) + (1.0,), LINE_PX)
    if "verts" in lay:
        points(lay["verts"], srgb(VERT) + (1.0,), VERT_PX)
        points(lay["verts_sel"], srgb(VERT_SEL) + (1.0,), VERT_SEL_PX)
    st.batches, st.bkey = out, key
    return out


def _biased_projection(rv3d, bias):
    import gpu
    from mathutils import Matrix
    p = Matrix(gpu.matrix.get_projection_matrix())
    if rv3d is not None and rv3d.is_perspective:
        p[2][3] -= bias * abs(p[2][3])
    else:
        p[2][3] -= bias * 0.1
    return p


def _xray(space):
    sh = space.shading
    return sh.show_xray_wireframe if sh.type == 'WIREFRAME' else sh.show_xray


def edit_objects(context):
    return [ob for ob in (context.objects_in_mode_unique_data or ()) if ob is not None and ob.type == 'MESH'
            and ob.visible_get()]


def state(ob, depsgraph, faces=True):
    """Up-to-date cached arrays of ``ob`` (None when the kit leaves this mesh to Blender's drawing); ``faces``:
    the polygons are needed too (face select mode)."""
    import bmesh
    key = (ob.as_pointer(), ob.data.as_pointer())
    st = _cache.get(key)
    if st is None or st.name != ob.name or st.me_name != ob.data.name:
        st = _cache[key] = _State(ob)
        st.arrays = None
    if st.arrays is not None and ob.name not in _dirty and ob.data.name not in _dirty and (st.faces or not faces):
        return st
    bm = bmesh.from_edit_mesh(ob.data)
    evaluated = use_evaluated(ob.modifiers)
    if not readable(len(bm.verts), evaluated):
        st.arrays = None
        return None
    arrays = read_evaluated(ob, depsgraph, faces) if evaluated else None
    if arrays is None or len(arrays.co) != len(bm.verts) or len(arrays.edges) != len(bm.edges):
        if len(bm.verts) > BMESH_LIMIT:
            return None
        arrays, faces = read_bmesh(bm), True
    st.arrays, st.faces, st.batches, st.bkey = arrays, faces, None, None
    return st


def _draw():
    context = bpy.context
    if context.mode != 'EDIT_MESH' or not _enabled():
        return
    space, rv3d, region = context.space_data, context.region_data, context.region
    if rv3d is None or space is None or region is None or not space.overlay.show_overlays:
        return
    from . import toolbox
    if toolbox.is_toolbox(space):
        return
    obs = edit_objects(context)
    if not obs:
        return
    import time
    import gpu
    t0 = time.perf_counter()
    depsgraph = context.view_layer.depsgraph
    select_mode = tuple(context.tool_settings.mesh_select_mode)
    states = []
    for ob in obs:
        st = state(ob, depsgraph, select_mode[2])
        if st is not None:
            states.append((ob, st))
    _dirty.difference_update({ob.name for ob in obs} | {ob.data.name for ob in obs})
    live = {(ob.as_pointer(), ob.data.as_pointer()) for ob in obs}
    for k in [k for k in _cache if k not in live]:
        del _cache[k]
    if not states:
        return
    scale = context.preferences.system.ui_scale or 1.0
    gpu.state.depth_test_set('NONE' if _xray(space) else 'LESS_EQUAL')
    gpu.state.depth_mask_set(False)
    proj = {False: _biased_projection(rv3d, DEPTH_BIAS), True: _biased_projection(rv3d, POINT_BIAS)}
    gpu.matrix.push_projection()
    try:
        for ob, st in states:
            with gpu.matrix.push_pop():
                gpu.matrix.multiply_matrix(ob.matrix_world)
                for kind, sh, batch, color, size in _batches(st, select_mode):
                    gpu.matrix.load_projection_matrix(proj[kind == 'POINTS'])
                    sh.bind()
                    sh.uniform_float("color", color)
                    if kind == 'POINTS':
                        gpu.state.point_size_set(max(1.0, round(size * scale)))
                    elif kind == 'LINES':
                        sh.uniform_float("viewportSize", (region.width, region.height))
                        sh.uniform_float("lineWidth", size * scale)
                    batch.draw(sh)
        gpu.state.point_size_set(1.0)
    finally:
        gpu.matrix.pop_projection()
        gpu.state.depth_test_set('NONE')
    _times.append(time.perf_counter() - t0)
    if len(_times) > 120:
        del _times[0]


def frame_ms():
    return sum(_times) / len(_times) * 1000.0 if _times else 0.0


def _callback():
    try:
        _draw()
    except Exception:  # never let a draw error repeat every frame
        import traceback
        traceback.print_exc()
        _remove_handler()


def _remove_handler():
    while _handle:
        bpy.types.SpaceView3D.draw_handler_remove(_handle.pop(), 'WINDOW')


@bpy.app.handlers.persistent
def _on_depsgraph(_scene=None, depsgraph=None):
    if depsgraph is None or not _cache:
        return
    for u in depsgraph.updates:
        if isinstance(u.id, (bpy.types.Mesh, bpy.types.Object)):
            _dirty.add(u.id.original.name if u.id.original is not None else u.id.name)


@bpy.app.handlers.persistent
def _on_reload(*_args):
    _cache.clear()
    _dirty.clear()


_HANDLERS = (("depsgraph_update_post", _on_depsgraph), ("undo_post", _on_reload), ("redo_post", _on_reload),
             ("load_post", _on_reload))


def register():
    for name, fn in _HANDLERS:
        getattr(bpy.app.handlers, name).append(fn)
    _handle.append(bpy.types.SpaceView3D.draw_handler_add(_callback, (), 'WINDOW', 'POST_VIEW'))


def unregister():
    _remove_handler()
    for name, fn in _HANDLERS:
        lst = getattr(bpy.app.handlers, name)
        if fn in lst:
            lst.remove(fn)
    _cache.clear()
    _dirty.clear()
    _shader.clear()
    _times.clear()
