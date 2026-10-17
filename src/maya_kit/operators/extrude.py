# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya polyExtrudeFace and the "last kit modeling operation" history (docs/steps/step_65.md 「계획」 1-2).

Maya 2022 measured with mayapy (step 65, unit cube, top face): Edit Mesh > Extrude = a zero-length extrusion
(Thickness 0, Local Translate Z 0, Offset 0, Divisions 1, Keep Faces Together on); Local Translate Z moves each face along
its normal (a vertex shared by several extruded faces moves by the average), Thickness offsets every face plane by the
same distance (shell), Offset shrinks the extruded faces in their plane (no new faces), Divisions = rings along the sides
(research/maya/workflows/modeling.md:19-24, shots/modeling_03.png / modeling_04.png).

Blender keeps no history in edit mode (research/maya/concepts.md:72). The kit remembers the last extrusion per object:
its node name (``polyExtrudeFaceN``), the mesh before it and the values; changing a value rebuilds the extrusion from that
mesh (``maya_kit.extrude_edit``), so it is one undo step and the Adjust Last Operation panel shows the same Maya names.
The record is valid only while the mesh equals one of the states the kit made (Ctrl+Z / Ctrl+Shift+Z included).
"""

import bmesh
import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty
from mathutils import Vector

from . import units

NODE = "polyExtrudeFace"
COUNTER = "maya_kit_polyExtrudeFace"     # scene ID property: Maya numbers nodes per scene
FIELDS = ("thickness", "local_translate_z", "offset", "divisions", "keep_faces_together")
LABELS = {"thickness": "Thickness", "local_translate_z": "Local Translate Z", "offset": "Offset",
          "divisions": "Divisions", "keep_faces_together": "Keep Faces Together"}
DEFAULTS = {"thickness": 0.0, "local_translate_z": 0.0, "offset": 0.0, "divisions": 1, "keep_faces_together": True}
NOTICE = "Edit-mode operations have no history in Blender: only the last one can be changed here."


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


# --- the record ------------------------------------------------------------------------------------

class Record:
    """The last kit extrusion on one object."""

    def __init__(self, name, pre, params):
        self.name = name            # polyExtrudeFaceN
        self.pre = pre              # BMesh copy before the extrusion
        self.params = dict(params)
        self.topology = None        # (divisions, together) of ``moved``
        self.moved = []             # [(vertex index, P0, T, L, O)]
        self.cap_faces = []         # face indices
        self.states = []            # [(params, signature)]
        self.live = False           # a drag is previewing values
        self.mesh_uid = None        # session_uid of the mesh it was made on

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
    rec.states.append((dict(params), signature(bm, cap_verts)))
    del rec.states[:-64]
    rec.live = False


def restore_pre(bm, rec):
    """Put the mesh from before the extrusion back into ``bm`` (an edit-mode bmesh)."""
    me = bpy.data.meshes.new(".maya_kit_pre")
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
    faces = [f for f in bm.faces if f.select]
    caps, moved = extrude(bm, faces, unit=unit, **params)
    _store(rec, bm, caps, moved, params)
    bmesh.update_edit_mesh(ob.data)
    return bool(caps)


def preview(ob, rec, params, unit):
    """Show ``params`` during a drag: move the vertices when only lengths change, else rebuild."""
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
    for params, sig in reversed(rec.states):
        cap_verts = list(sig[2]) if sig else []
        if sig is not None and signature(bm, cap_verts) == sig:
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
    """Maya's extrude manipulator / In-View Editor stay while the extruded faces are the selection."""
    bm = bmesh.from_edit_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    sel = {f.index for f in bm.faces if f.select}
    return bool(sel) and sel == set(rec.cap_faces)


def active(context):
    """(object, record) of the active edit object when its last extrusion can be edited."""
    ob = context.edit_object if context is not None else None
    rec = current(ob)
    return (ob, rec) if rec is not None else (None, None)


def next_name(scene):
    n = int(scene.get(COUNTER, 0)) + 1
    scene[COUNTER] = n
    return f"{NODE}{n}"


def _pre_signature(bm):
    bm.faces.index_update()
    return (len(bm.verts), len(bm.edges), len(bm.faces), tuple(f.index for f in bm.faces if f.select))


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
    }


def _params(op):
    return {k: getattr(op, k) for k in FIELDS}


class _ExtrudeProps:
    __annotations__ = _props()


class MAYAKIT_OT_extrude(_ExtrudeProps, bpy.types.Operator):
    """Extrude the selected faces now (Maya polyExtrudeFace): change Thickness, Local Translate Z, Offset,
    Divisions with the manipulator, the In-View Editor or Channel Box INPUTS"""
    bl_idname = "maya_kit.extrude"
    bl_label = "Extrude"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def invoke(self, context, event):
        if not any(o.type == 'MESH' and o.data.total_face_sel for o in context.objects_in_mode_unique_data):
            # edges / vertices: Blender's extrude + drag (Maya extrudes them with polyExtrudeEdge/Vertex)
            if context.area is not None and context.area.type == 'VIEW_3D':
                return bpy.ops.view3d.edit_mesh_extrude_move_normal('INVOKE_DEFAULT')
            return {'CANCELLED'}
        return self.execute(context)

    def execute(self, context):
        unit = units.maya_unit(context.scene)
        params = _params(self)
        done = 0
        for ob in context.objects_in_mode_unique_data:
            if ob.type != 'MESH':
                continue
            bm = bmesh.from_edit_mesh(ob.data)
            faces = [f for f in bm.faces if f.select]
            if not faces:
                continue
            old = RECORDS.get(ob.name)
            name = None
            if (old is not None and old.pre is not None and old.mesh_uid == ob.data.session_uid
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


class MAYAKIT_OT_extrude_edit(_ExtrudeProps, bpy.types.Operator):
    """Change the last extrusion (Maya: edit the polyExtrudeFace node). Blender keeps no edit-mode history,
    so only the last one can be changed"""
    bl_idname = "maya_kit.extrude_edit"
    bl_label = "polyExtrudeFace"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def invoke(self, context, event):
        _ob, rec = active(context)
        if rec is None:
            return {'CANCELLED'}
        for k, v in rec.params.items():
            if not self.properties.is_property_set(k):
                setattr(self, k, v)
        return self.execute(context)

    def execute(self, context):
        unit = units.maya_unit(context.scene)
        params = _params(self)
        done = 0
        for ob in context.objects_in_mode_unique_data:
            rec = RECORDS.get(ob.name)
            if rec is None or rec.pre is None or (not rec.live and current(ob) is None):
                continue
            if run(ob, rec, params, unit):
                done += 1
        if not done:
            self.report({'WARNING'}, "No extrusion to change: " + NOTICE)
            return {'CANCELLED'}
        return {'FINISHED'}


def set_params(context, **changes):
    """Change values of the active object's last extrusion (one undo step). Returns the operator result."""
    _ob, rec = active(context)
    if rec is None:
        return {'CANCELLED'}
    params = dict(rec.params)
    params.update(changes)
    params["divisions"] = max(1, int(params["divisions"]))
    # undo=True: a Python operator call pushes no undo step by default (bpy.ops positional ``undo``)
    return bpy.ops.maya_kit.extrude_edit('EXEC_DEFAULT', True, **params)


classes = (MAYAKIT_OT_extrude, MAYAKIT_OT_extrude_edit)


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
