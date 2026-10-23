# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya polyExtrudeFace and the "last kit modeling operation" history.

Maya 2022 checked  (step 65, unit cube, top face): Edit Mesh > Extrude = a zero-length extrusion
(Thickness 0, Local Translate Z 0, Offset 0, Divisions 1, Keep Faces Together on); Local Translate Z moves each face along
its normal (a vertex shared by several extruded faces moves by the average), Thickness offsets every face plane by the
same distance (shell), Offset shrinks the extruded faces in their plane (no new faces), Divisions = rings along the sides
(, shots/modeling_03.png / modeling_04.png).

Blender keeps no history in edit mode (). The kit remembers the last extrusion per object:
its node name (``polyExtrudeFaceN``), the mesh before it and the values; changing a value rebuilds the extrusion from that
mesh (``allset.extrude_edit``), so it is one undo step and the Adjust Last Operation panel shows the same Maya names.
The record is valid only while the mesh equals one of the states the kit made (Ctrl+Z / Ctrl+Shift+Z included).

Step 139 (#70 M4, #16): the record is one ``Spec`` per Maya node - polyExtrudeEdge / polyExtrudeVertex here (edges /
vertices extrude at once, no drag) and polyBevel3 in operators/bevel_maya.py - each with its Maya fields, edit
operator and arrow field ().
"""

import bmesh
import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty
from mathutils import Vector

from . import units

NODE = "polyExtrudeFace"
COUNTER = "allset_polyExtrudeFace"     # scene ID property: Maya numbers nodes per scene
FIELDS = ("thickness", "local_translate_z", "offset", "divisions", "keep_faces_together")
LABELS = {"thickness": "Thickness", "local_translate_z": "Local Translate Z", "offset": "Offset",
          "divisions": "Divisions", "keep_faces_together": "Keep Faces Together"}
DEFAULTS = {"thickness": 0.0, "local_translate_z": 0.0, "offset": 0.0, "divisions": 1, "keep_faces_together": True}
NOTICE = "Edit-mode operations have no history in Blender: only the last one can be changed here."


class Spec:
    """One kind of Maya modeling node the kit records (step 139: edge / vertex extrusion, bevel).

    ``kinds`` = Channel Box text kind per field (cb_entry: "NONE" float, "INT", "BOOL"); ``arrow`` = the field the
    In-View manipulator arrow drags (None: no arrow); ``edit_op`` = the operator that rebuilds the node with new
    values (one undo step); ``build(bm, params, unit)`` (not FACE) -> the vertices to track."""

    def __init__(self, kind, node, fields, labels, defaults, kinds, arrow, edit_op, build=None, node_type=None):
        self.node_type = node_type or node     # Maya node type (the AE history tab title)
        self.kind, self.node, self.fields, self.labels = kind, node, tuple(fields), dict(labels)
        self.defaults, self.kinds, self.arrow, self.edit_op, self.build = dict(defaults), dict(kinds), arrow, \
            edit_op, build

    @property
    def counter(self):
        return "allset_" + self.node


SPECS = {}


def add_spec(spec):
    SPECS[spec.kind] = spec
    return spec


FACE = add_spec(Spec('FACE', NODE, FIELDS, LABELS, DEFAULTS,
                     {"thickness": "NONE", "local_translate_z": "NONE", "offset": "NONE", "divisions": "INT",
                      "keep_faces_together": "BOOL"}, "local_translate_z", "extrude_edit"))


# --- geometry (bmesh only) -------------------------------------------------------------------------

def _thickness_dir(normals):
    """Displacement that moves every face plane in ``normals`` by 1 (Maya Thickness, a shell)."""
    if len(normals) == 1:
        return normals[0].copy()
    if len(normals) == 2:
        n1, n2 = normals
        return (n1 + n2) / max(1.0 + n1.dot(n2), 1e-3)
    m = sum(normals, Vector()).normalized()
    return m / max(sum(m.dot(n) for n in normals) / len(normals), 0.1)


def _inward(face, edge):
    """Unit vector in ``face``'s plane, perpendicular to ``edge``, pointing into the face."""
    for loop in face.loops:
        if loop.edge is edge:
            t = (loop.link_loop_next.vert.co - loop.vert.co).normalized()
            return face.normal.cross(t).normalized()
    return Vector()


def _offset_dir(perps):
    """Offset of a boundary vertex: each of its two boundary edges moves 1 into the face."""
    if len(perps) == 2:
        a, b = perps
        return (a + b) / max(1.0 + a.dot(b), 1e-3)
    if perps:
        return sum(perps, Vector()) / len(perps)
    return Vector()


def _vectors(faces, together):
    """{key: (base co, T, L, O)} per extruded vertex (key = vertex index, or (face index, vertex index) for
    faces extruded one by one), from the faces before the extrusion."""
    sel = set(faces)
    out = {}
    if together:
        for f in faces:
            for v in f.verts:
                if v.index in out:
                    continue
                vf = [g for g in v.link_faces if g in sel]
                normals = [g.normal.copy() for g in vf]
                perps = []
                for e in v.link_edges:
                    ef = [g for g in e.link_faces if g in sel]
                    if len(ef) == 1:              # a border edge of the extruded region
                        perps.append(_inward(ef[0], e))
                out[v.index] = (v.co.copy(), _thickness_dir(normals),
                                sum(normals, Vector()) / len(normals), _offset_dir(perps))
    else:
        for f in faces:
            n = f.normal.copy()
            for v in f.verts:
                perps = [_inward(f, e) for e in v.link_edges if f in e.link_faces]
                out[(f.index, v.index)] = (v.co.copy(), n.copy(), n.copy(), _offset_dir(perps))
    return out


def _key(co):
    return tuple(round(c, 6) for c in co)


def _caps(ret_geom):
    verts = {g for g in ret_geom if isinstance(g, bmesh.types.BMVert)}
    return [g for g in ret_geom if isinstance(g, bmesh.types.BMFace) and all(v in verts for v in g.verts)]


def _region(bm, faces):
    edges = {e for f in faces for e in f.edges}
    ret = bmesh.ops.extrude_face_region(bm, geom=list(faces) + list(edges))
    caps = _caps(ret["geom"])
    gone = [f for f in faces if f.is_valid]
    if gone:   # an isolated region keeps its faces in bmesh; Maya's extrusion has no bottom
        bmesh.ops.delete(bm, geom=gone, context='FACES_ONLY')
    return caps


def extrude_topology(bm, faces, divisions=1, together=True):
    """Zero-length extrusion of ``faces``, ``divisions`` times. Returns (caps, levels, vectors) where
    levels[k-1] maps a vertex key to the level-k vertex (level ``divisions`` = the caps)."""
    bm.verts.index_update()
    bm.faces.index_update()
    faces = [f for f in faces if f.is_valid]
    vectors = _vectors(faces, together)
    if together:
        by_co = {_key(co): k for k, (co, *_r) in vectors.items()}
    else:
        by_co = {}
        for (fi, vi), (co, *_r) in vectors.items():
            by_co.setdefault(fi, {})[_key(co)] = (fi, vi)
    order = [f.index for f in faces]
    levels = []
    caps = faces
    for level in range(max(1, divisions)):
        if level == 0 and not together:
            caps = bmesh.ops.extrude_discrete_faces(bm, faces=caps)["faces"]
            gone = [f for f in faces if f.is_valid]
            if gone:
                bmesh.ops.delete(bm, geom=gone, context='FACES_ONLY')
        else:
            caps = _region(bm, caps)
        found = {}
        if together:
            for f in caps:
                for v in f.verts:
                    k = by_co.get(_key(v.co))
                    if k is not None:
                        found[k] = v
        else:
            # extrude_discrete_faces / later regions keep the face order; match vertices by position per face
            if level == 0:
                caps_by_face = dict(zip(order, caps))
            else:      # the next caps sit where the previous ones were
                caps_by_face = {fi: _match_face(caps, by_co[fi]) for fi in order}
            for fi, cap in caps_by_face.items():
                if cap is None:
                    continue
                for v in cap.verts:
                    k = by_co[fi].get(_key(v.co))
                    if k is not None:
                        found[k] = v
        levels.append(found)
    return caps, levels, vectors


def _match_face(caps, keys):
    want = set(keys)
    return next((c for c in caps if {_key(v.co) for v in c.verts} == want), None)


def moved_vertices(levels, vectors, unit=1.0):
    """[(vertex, P0, T, L, O)] with the level fraction and the Maya unit folded into T, L, O."""
    n = len(levels)
    out = []
    for k, found in enumerate(levels, 1):
        f = k / n * unit
        for key, v in found.items():
            co, t, l, o = vectors[key]
            out.append((v, co.copy(), t * f, l * f, o * f))
    return out


def place(moved, thickness, ltz, offset):
    for v, p0, t, l, o in moved:
        v.co = p0 + t * thickness + l * ltz + o * offset


def extrude(bm, faces, thickness=0.0, local_translate_z=0.0, offset=0.0, divisions=1, keep_faces_together=True,
            unit=1.0):
    """Maya polyExtrudeFace on ``faces`` (bmesh). Returns (caps, moved); the caps end up selected."""
    caps, levels, vectors = extrude_topology(bm, faces, divisions, keep_faces_together)
    moved = moved_vertices(levels, vectors, unit)
    place(moved, thickness, local_translate_z, offset)
    for f in bm.faces:
        f.select = False
    for e in bm.edges:
        e.select = False
    for v in bm.verts:
        v.select = False
    for f in caps:
        f.select_set(True)
    bm.select_flush_mode()
    bm.normal_update()
    return caps, moved


# --- polyExtrudeEdge / polyExtrudeVertex (step 139, -2) ------------

def deselect_all(bm):
    for seq in (bm.faces, bm.edges, bm.verts):
        for el in seq:
            el.select = False


def _unit_or(vec, fallback):
    return vec.normalized() if vec.length > 1e-9 else Vector(fallback)


def edge_frame(e):
    """Maya's local frame of an extruded edge (a -> b = the edge's vertex order): X along the edge, Z = mean of the
    adjacent face normals (Local Translate Z / Thickness), Y = Z x X (Offset). checked:"""
    a, b = e.verts
    x = _unit_or(b.co - a.co, (1.0, 0.0, 0.0))
    z = _unit_or(sum((f.normal for f in e.link_faces), Vector()), (0.0, 0.0, 1.0))
    y = _unit_or(z.cross(x), (0.0, 1.0, 0.0))
    return x, y, z


def extrude_edges(bm, edges, thickness=0.0, local_translate_z=0.0, offset=0.0, divisions=1, unit=1.0, **_unused):
    """Maya polyExtrudeEdge (Keep Faces Together off, Maya's default for edges): every edge alone gets ``divisions``
    quads ``(a, b, b', a')``; the new edge moves by Z * (Thickness + Local Translate Z) + Y * Offset (Maya units).
    The outer edges end up selected. Returns the new vertices."""
    bm.normal_update()
    edges = [e for e in edges if e.is_valid]
    k = max(1, int(divisions))
    plan = []
    for e in edges:
        _x, y, z = edge_frame(e)
        plan.append((e.verts[0], e.verts[1], (z * (thickness + local_translate_z) + y * offset) * unit,
                     e.link_faces[0] if e.link_faces else None))
    new, outer = [], []
    for a, b, d, example in plan:
        pa, pb = a, b
        for j in range(1, k + 1):
            na = bm.verts.new(a.co + d * (j / k))
            nb = bm.verts.new(b.co + d * (j / k))
            bm.faces.new((pa, pb, nb, na), example)
            new += [na, nb]
            pa, pb = na, nb
        outer.append(bm.edges.get((pa, pb)))
    deselect_all(bm)
    for e in outer:
        if e is not None:
            e.select_set(True)
    bm.select_flush_mode()
    bm.normal_update()
    return new


def _split_edges_at(bm, verts, width):
    """Split every edge of ``verts`` at ``width`` x its length from the vertex (Maya width = a fraction of each
    edge, checked on a 4 x 1 x 2 box,). Returns {vertex: [base vertices]}."""
    vset = set(verts)
    base = {v: [] for v in verts}
    edges = sorted({e for v in verts for e in v.link_edges}, key=lambda e: e.index)
    plan = []
    for e in edges:
        a, b = e.verts
        plan.append((e, a, b, {x: x.co + (e.other_vert(x).co - x.co) * width for x in (a, b) if x in vset}))
    for e, a, b, targets in plan:
        cur = e
        if a in targets:
            _ne, nv = bmesh.utils.edge_split(cur, a, 0.5)
            nv.co = targets[a]
            base[a].append(nv)
            cur = bm.edges.get((nv, b))
        if b in targets and cur is not None:
            _ne, nv = bmesh.utils.edge_split(cur, b, 0.5)
            nv.co = targets[b]
            base[b].append(nv)
    return base


def _cut_corner(bm, v):
    """Cut every face around ``v`` between its two neighbours: ``v`` keeps only triangles (Maya's cone)."""
    for f in list(v.link_faces):
        if len(f.verts) <= 3:
            continue
        loop = next(lp for lp in f.loops if lp.vert is v)
        p, q = loop.link_loop_prev.vert, loop.link_loop_next.vert
        if bm.edges.get((p, q)) is None:
            bmesh.utils.face_split(f, p, q)


def _rings(bm, v, k):
    """``k`` - 1 rings on the cone of ``v`` (Maya divisions: rings at j/k from the base ring to the tip,)."""
    tris = [f for f in v.link_faces if len(f.verts) == 3]
    ring = {}

    def at(b, j):
        if j == 0:
            return b
        if j == k:
            return v
        key = (b, j)
        if key not in ring:
            ring[key] = bm.verts.new(b.co + (v.co - b.co) * (j / k))
        return ring[key]

    rebuild = []
    for f in tris:
        loop = next(lp for lp in f.loops if lp.vert is v)
        rebuild.append((loop.link_loop_next.vert, loop.link_loop_next.link_loop_next.vert, f))
    spokes = list(v.link_edges)
    for p, q, f in rebuild:
        for j in range(k - 1):
            bm.faces.new((at(p, j), at(q, j), at(q, j + 1), at(p, j + 1)), f)
        bm.faces.new((v, at(p, k - 1), at(q, k - 1)), f)
    bmesh.ops.delete(bm, geom=[f for _p, _q, f in rebuild], context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[e for e in spokes if e.is_valid and not e.link_faces], context='EDGES')
    return list(ring.values())


def extrude_vertices(bm, verts, width=0.5, length=1.0, divisions=1, unit=1.0, **_unused):
    """Maya polyExtrudeVertex: the vertex becomes the tip of a cone, ``length`` (Maya units) along the mean normal
    of its faces; the base ring sits at ``width`` x each edge from it; ``divisions`` rings in between. The tip
    vertices end up selected. Returns the new / moved vertices."""
    bm.normal_update()
    verts = [v for v in verts if v.is_valid and v.link_faces]
    tips = {v: v.co + _unit_or(sum((f.normal for f in v.link_faces), Vector()), (0.0, 0.0, 1.0)) * (length * unit)
            for v in verts}
    base = _split_edges_at(bm, verts, width)
    k = max(1, int(divisions))
    out = []
    for v in verts:
        _cut_corner(bm, v)
    for v in verts:
        v.co = tips[v]
        out.append(v)
        out += base[v]
        if k > 1:
            out += _rings(bm, v, k)
    deselect_all(bm)
    for v in verts:
        v.select_set(True)
    bm.select_flush_mode()
    bm.normal_update()
    return out


def _build_edges(bm, params, unit):
    return extrude_edges(bm, [e for e in bm.edges if e.select], unit=unit, **params)


def _build_vertices(bm, params, unit):
    return extrude_vertices(bm, [v for v in bm.verts if v.select], unit=unit, **params)


EDGE = add_spec(Spec('EDGE', "polyExtrudeEdge", ("thickness", "local_translate_z", "offset", "divisions"),
                     {k: LABELS[k] for k in ("thickness", "local_translate_z", "offset", "divisions")},
                     {"thickness": 0.0, "local_translate_z": 0.0, "offset": 0.0, "divisions": 1},
                     {"thickness": "NONE", "local_translate_z": "NONE", "offset": "NONE", "divisions": "INT"},
                     "local_translate_z", "extrude_edge_edit", _build_edges))
VERTEX = add_spec(Spec('VERTEX', "polyExtrudeVertex", ("width", "length", "divisions"),
                       {"width": "Width", "length": "Length", "divisions": "Divisions"},
                       {"width": 0.5, "length": 1.0, "divisions": 1},
                       {"width": "NONE", "length": "NONE", "divisions": "INT"},
                       "length", "extrude_vertex_edit", _build_vertices))


def selection_signature(bm):
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    return (tuple(v.index for v in bm.verts if v.select), tuple(e.index for e in bm.edges if e.select),
            tuple(f.index for f in bm.faces if f.select))


# --- the record ------------------------------------------------------------------------------------

class Record:
    """The last kit extrusion on one object."""

    def __init__(self, name, pre, params, spec=None):
        self.name = name            # polyExtrudeFaceN (polyExtrudeEdgeN, polyExtrudeVertexN, polyBevelN)
        self.spec = spec or FACE    # which Maya node (step 139)
        self.pre = pre              # BMesh copy before the extrusion
        self.params = dict(params)
        self.cap_verts = []         # vertex indices whose positions identify the kit's state
        self.sel = None             # selection signature the operation left (not FACE)
        self.topology = None        # (divisions, together) of ``moved``
        self.moved = []             # [(vertex index, P0, T, L, O)]
        self.cap_faces = []         # face indices
        self.states = []            # [(params, signature, selection signature)]
        self.live = False           # a drag is previewing values
        self.mesh_uid = None        # session_uid of the mesh it was made on
        self.dismissed = False      # Q/W/E/R picked a tool since: Maya shows that tool's manipulator (#80)

    def free(self):
        if self.pre is not None:
            self.pre.free()
            self.pre = None


RECORDS = {}   # object name -> Record


def clear():
    for rec in RECORDS.values():
        rec.free()
    RECORDS.clear()


def signature(bm, cap_verts):
    bm.verts.ensure_lookup_table()
    if any(i >= len(bm.verts) for i in cap_verts):
        return None
    return (len(bm.verts), len(bm.faces), tuple(cap_verts), tuple(_key(bm.verts[i].co) for i in cap_verts))


def _store(rec, bm, caps, moved, params):
    bm.verts.index_update()
    bm.faces.index_update()
    rec.params = dict(params)
    rec.topology = (params["divisions"], params["keep_faces_together"])
    rec.moved = [(v.index, p0, t, l, o) for v, p0, t, l, o in moved]
    rec.cap_faces = [f.index for f in caps]
    cap_verts = sorted({v.index for f in caps for v in f.verts})
    rec.cap_verts = cap_verts
    rec.states.append((dict(params), signature(bm, cap_verts), None))
    del rec.states[:-64]
    rec.live = False


def _store_generic(rec, bm, tracked, params):
    bm.verts.index_update()
    rec.params = dict(params)
    rec.cap_verts = sorted({v.index for v in tracked if v.is_valid})
    rec.cap_faces = []
    rec.sel = selection_signature(bm)
    rec.states.append((dict(params), signature(bm, rec.cap_verts), rec.sel))
    del rec.states[:-64]
    rec.live = False


def restore_pre(bm, rec):
    """Put the mesh from before the extrusion back into ``bm`` (an edit-mode bmesh)."""
    me = bpy.data.meshes.new(".allset_pre")
    try:
        rec.pre.to_mesh(me)
        bm.clear()
        bm.from_mesh(me)
    finally:
        bpy.data.meshes.remove(me)


def run(ob, rec, params, unit):
    """Rebuild the extrusion of ``rec`` on ``ob`` (edit mode) with ``params``."""
    bm = bmesh.from_edit_mesh(ob.data)
    restore_pre(bm, rec)
    if rec.spec is not FACE:
        tracked = rec.spec.build(bm, {k: params[k] for k in rec.spec.fields}, unit)
        _store_generic(rec, bm, tracked, params)
        bmesh.update_edit_mesh(ob.data)
        return bool(tracked)
    faces = [f for f in bm.faces if f.select]
    caps, moved = extrude(bm, faces, unit=unit, **params)
    _store(rec, bm, caps, moved, params)
    bmesh.update_edit_mesh(ob.data)
    return bool(caps)


def preview(ob, rec, params, unit):
    """Show ``params`` during a drag: move the vertices when only lengths change, else rebuild."""
    if rec.spec is not FACE:
        run(ob, rec, params, unit)
        rec.live = True
        return
    topo = (params["divisions"], params["keep_faces_together"])
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    if topo != rec.topology or any(i >= len(bm.verts) for i, *_r in rec.moved):
        run(ob, rec, params, unit)
    else:
        for i, p0, t, l, o in rec.moved:
            bm.verts[i].co = p0 + t * params["thickness"] + l * params["local_translate_z"] + o * params["offset"]
        bm.normal_update()
        bmesh.update_edit_mesh(ob.data, loop_triangles=True, destructive=False)
        rec.params = dict(params)
    rec.live = True


def current(ob):
    """The valid record of ``ob`` (its mesh equals a state the kit made), with that state's values; else None."""
    if ob is None or ob.type != 'MESH' or ob.mode != 'EDIT':
        return None
    rec = RECORDS.get(ob.name)
    if rec is None or rec.pre is None or rec.mesh_uid != ob.data.session_uid:
        return None
    if rec.live:
        return rec
    bm = bmesh.from_edit_mesh(ob.data)
    for params, sig, sel in reversed(rec.states):
        cap_verts = list(sig[2]) if sig else []
        if sig is not None and signature(bm, cap_verts) == sig:
            if rec.spec is not FACE:
                rec.params, rec.cap_verts, rec.sel = dict(params), cap_verts, sel
                return rec
            if params != rec.params or cap_verts != getattr(rec, "cap_verts", None):
                rec.params = dict(params)
                rec.topology = None          # ``moved`` belongs to another state: the next drag rebuilds
                rec.cap_verts = cap_verts
                rec.cap_faces = _cap_faces(bm, cap_verts)
            return rec
    return None


def _cap_faces(bm, cap_verts):
    s = set(cap_verts)
    bm.faces.ensure_lookup_table()
    return [f.index for f in bm.faces if f.verts and all(v.index in s for v in f.verts)]


def caps_selected(ob, rec):
    """Maya's extrude manipulator / In-View Editor stay while the extruded faces are the selection (edge / vertex
    extrusion, bevel: while the selection is the one the operation left)."""
    bm = bmesh.from_edit_mesh(ob.data)
    if rec.spec is not FACE:
        return selection_signature(bm) == rec.sel
    bm.faces.ensure_lookup_table()
    sel = {f.index for f in bm.faces if f.select}
    return bool(sel) and sel == set(rec.cap_faces)


def active(context):
    """(object, record) of the active edit object when its last extrusion can be edited."""
    ob = context.edit_object if context is not None else None
    rec = current(ob)
    return (ob, rec) if rec is not None else (None, None)


def dismiss(context):
    """Maya: picking a tool (Q / W / E / R) after an extrusion swaps the extrude manipulator and In-View Editor for
    that tool's manipulator; the node stays in Channel Box INPUTS (issue #80). True when one was showing."""
    _ob, rec = active(context)
    if rec is None or rec.dismissed:
        return False
    rec.dismissed = True
    return True


def next_name(scene, spec=None):
    spec = spec or FACE
    n = int(scene.get(spec.counter, 0)) + 1
    scene[spec.counter] = n
    return f"{spec.node}{n}"


def _pre_signature(bm):
    return (len(bm.verts), len(bm.edges), len(bm.faces)) + selection_signature(bm)


def kind_of(bm, select_mode):
    """Which Maya extrusion the selection asks for: the select mode first (Maya extrudes the selected
    component type), then whatever is selected."""
    sv, se, sf = select_mode
    has = {'FACE': any(f.select for f in bm.faces), 'EDGE': any(e.select for e in bm.edges),
           'VERTEX': any(v.select for v in bm.verts)}
    for kind, on in (('FACE', sf), ('EDGE', se), ('VERTEX', sv)):
        if on and has[kind]:
            return kind
    return next((k for k in ('FACE', 'EDGE', 'VERTEX') if has[k]), None)


def record_new(context, ob, bm, spec, params, unit):
    """Run ``spec`` on the selection of ``ob`` (edit mode) as a new history node; the same node again when
    Adjust Last Operation re-runs it on the same mesh. Returns the record or None."""
    old = RECORDS.get(ob.name)
    name = None
    if (old is not None and old.spec is spec and old.pre is not None and old.mesh_uid == ob.data.session_uid
            and _pre_signature(old.pre) == _pre_signature(bm)):
        name = old.name
    pre = bm.copy()
    tracked = spec.build(bm, params, unit)
    if not tracked:
        pre.free()
        return None
    if old is not None:
        old.free()
    rec = Record(name or next_name(context.scene, spec), pre, params, spec)
    rec.mesh_uid = ob.data.session_uid
    _store_generic(rec, bm, tracked, params)
    RECORDS[ob.name] = rec
    bmesh.update_edit_mesh(ob.data)
    return rec


# --- operators -------------------------------------------------------------------------------------

def _props():
    return {
        "thickness": FloatProperty(name="Thickness", default=0.0, options={'SKIP_SAVE'},
                                   description="Every extruded face plane moves out by this much (Maya units)"),
        "local_translate_z": FloatProperty(name="Local Translate Z", default=0.0, options={'SKIP_SAVE'},
                                           description="Move the extruded faces along their normals (Maya units)"),
        "offset": FloatProperty(name="Offset", default=0.0, options={'SKIP_SAVE'},
                                description="Shrink the extruded faces in their plane (Maya units)"),
        "divisions": IntProperty(name="Divisions", default=1, min=1, soft_max=20, options={'SKIP_SAVE'},
                                 description="Segments along the extruded sides"),
        "keep_faces_together": BoolProperty(name="Keep Faces Together", default=True,
                                            description="Extrude adjacent faces as one piece (off: each face alone)"),
        # polyExtrudeVertex (step 139)
        "width": FloatProperty(name="Width", default=0.5, soft_min=0.0, soft_max=1.0, options={'SKIP_SAVE'},
                               description="Base of the extruded vertex as a fraction of each of its edges"),
        "length": FloatProperty(name="Length", default=1.0, options={'SKIP_SAVE'},
                                description="Tip of the extruded vertex along its normal (Maya units)"),
    }


def _params(op, spec=None):
    return {k: getattr(op, k) for k in (spec or FACE).fields}


class _ExtrudeProps:
    __annotations__ = _props()


def _draw_fields(op, context, default=None):
    """Adjust Last Operation shows only the fields of the node the operation made (Maya names)."""
    _ob, rec = active(context)
    spec = rec.spec if rec is not None and rec.spec.kind in ('FACE', 'EDGE', 'VERTEX') else (default or FACE)
    for k in spec.fields:
        op.layout.prop(op, k, text=spec.labels[k])


class ALLSET_OT_extrude(_ExtrudeProps, bpy.types.Operator):
    """Extrude the selection now (Maya polyExtrudeFace / polyExtrudeEdge / polyExtrudeVertex by the component
    type): change its values with the manipulator, the In-View Editor or Channel Box INPUTS"""
    bl_idname = "allset.extrude"
    bl_label = "Extrude"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def invoke(self, context, event):
        # Maya extrudes edges / vertices at once too (no drag: -2, #70)
        return self.execute(context)

    def draw(self, context):
        _draw_fields(self, context)

    def execute(self, context):
        unit = units.maya_unit(context.scene)
        mode = tuple(context.scene.tool_settings.mesh_select_mode)
        done = 0
        for ob in context.objects_in_mode_unique_data:
            if ob.type != 'MESH':
                continue
            bm = bmesh.from_edit_mesh(ob.data)
            kind = kind_of(bm, mode)
            if kind is None:
                continue
            if kind != 'FACE':
                spec = SPECS[kind]
                if record_new(context, ob, bm, spec, _params(self, spec), unit) is not None:
                    done += 1
                continue
            params = _params(self)
            faces = [f for f in bm.faces if f.select]
            old = RECORDS.get(ob.name)
            name = None
            if (old is not None and old.spec is FACE and old.pre is not None and old.mesh_uid == ob.data.session_uid
                    and _pre_signature(old.pre) == _pre_signature(bm)):
                name = old.name          # Adjust Last Operation re-runs the same extrusion
            if old is not None:
                old.free()
            rec = Record(name or next_name(context.scene), bm.copy(), params)
            rec.mesh_uid = ob.data.session_uid
            caps, moved = extrude(bm, faces, unit=unit, **params)
            _store(rec, bm, caps, moved, params)
            RECORDS[ob.name] = rec
            bmesh.update_edit_mesh(ob.data)
            done += 1
        return {'FINISHED'} if done else {'CANCELLED'}


class _ExtrudeEdit(_ExtrudeProps):
    """Shared body of the edit operators (a registered operator class can't be subclassed: its poll broke)."""
    bl_options = {'REGISTER', 'UNDO'}
    _op = "extrude_edit"                  # the specs this operator edits (Spec.edit_op)

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def invoke(self, context, event):
        _ob, rec = active(context)
        if rec is None or rec.spec.edit_op != self._op:
            return {'CANCELLED'}
        for k, v in rec.params.items():
            if not self.properties.is_property_set(k):
                setattr(self, k, v)
        return self.execute(context)

    def draw(self, context):
        spec = next(s for s in SPECS.values() if s.edit_op == self._op)
        for k in spec.fields:
            self.layout.prop(self, k, text=spec.labels[k])

    def execute(self, context):
        unit = units.maya_unit(context.scene)
        done = 0
        for ob in context.objects_in_mode_unique_data:
            rec = RECORDS.get(ob.name)
            if rec is None or rec.pre is None or rec.spec.edit_op != self._op or (
                    not rec.live and current(ob) is None):
                continue
            if run(ob, rec, _params(self, rec.spec), unit):
                done += 1
        if not done:
            self.report({'WARNING'}, "No extrusion to change: " + NOTICE)
            return {'CANCELLED'}
        return {'FINISHED'}


class ALLSET_OT_extrude_edit(_ExtrudeEdit, bpy.types.Operator):
    """Change the last extrusion (Maya: edit the polyExtrudeFace node). Blender keeps no edit-mode history,
    so only the last one can be changed"""
    bl_idname = "allset.extrude_edit"
    bl_label = "polyExtrudeFace"          # the Adjust Last Operation title = the Maya node
    _op = "extrude_edit"


class ALLSET_OT_extrude_edge_edit(_ExtrudeEdit, bpy.types.Operator):
    """Change the last edge extrusion (Maya: edit the polyExtrudeEdge node). Blender keeps no edit-mode history,
    so only the last one can be changed"""
    bl_idname = "allset.extrude_edge_edit"
    bl_label = "polyExtrudeEdge"
    _op = "extrude_edge_edit"


class ALLSET_OT_extrude_vertex_edit(_ExtrudeEdit, bpy.types.Operator):
    """Change the last vertex extrusion (Maya: edit the polyExtrudeVertex node). Blender keeps no edit-mode
    history, so only the last one can be changed"""
    bl_idname = "allset.extrude_vertex_edit"
    bl_label = "polyExtrudeVertex"
    _op = "extrude_vertex_edit"


INT_FIELDS = ("divisions", "segments")


def set_params(context, **changes):
    """Change values of the active object's last kit node (one undo step). Returns the operator result."""
    _ob, rec = active(context)
    if rec is None:
        return {'CANCELLED'}
    params = dict(rec.params)
    params.update(changes)
    for k in INT_FIELDS:
        if k in params:
            params[k] = max(1, int(params[k]))
    # undo=True: a Python operator call pushes no undo step by default (bpy.ops positional ``undo``)
    return getattr(bpy.ops.allset, rec.spec.edit_op)('EXEC_DEFAULT', True, **params)


classes = (ALLSET_OT_extrude, ALLSET_OT_extrude_edit, ALLSET_OT_extrude_edge_edit, ALLSET_OT_extrude_vertex_edit)


@bpy.app.handlers.persistent
def _on_load(_dummy):
    clear()


def register_handlers():
    if _on_load not in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.append(_on_load)


def unregister_handlers():
    if _on_load in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.remove(_on_load)
    clear()
