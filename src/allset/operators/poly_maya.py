# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Edit Mesh / Mesh Tools commands with Maya-checked results (step 110,  「계획」 1-4).

 (Circularize), (Connect), (Make Hole). Pure bmesh.
"""

import math

import bmesh
import bpy

CONNECT_WARNING = "Can't perform polyConnectComponents1 on selection"   # Maya's warning (menu_honesty.md)


# --- Circularize -------------------------------------------------------------------------------

def _ordered_loops(edges):
    """Closed loops among ``edges`` as ordered vertex lists (open chains are skipped)."""
    adj = {}
    for e in edges:
        a, b = e.verts
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    loops, seen = [], set()
    for start in adj:
        if start in seen or len(adj[start]) != 2:
            continue
        loop, prev, cur = [start], None, start
        ok = True
        while True:
            seen.add(cur)
            nxt = [v for v in adj[cur] if v is not prev]
            if len(adj[cur]) != 2 or not nxt:
                ok = False
                break
            prev, cur = cur, nxt[0]
            if cur is start:
                break
            loop.append(cur)
        if ok and len(loop) >= 3:
            loops.append(loop)
    return loops


def circularize_loop(verts):
    """Put an ordered vertex loop on a circle: centre = centroid, radius = mean distance, evenly spaced, keeping the
    loop's mean angular position (Maya polyCircularize defaults, modeling_rigging_110.md)."""
    from mathutils import Vector
    n = len(verts)
    pts = [v.co.copy() for v in verts]
    c = sum(pts, Vector()) / n
    normal = Vector()
    for i in range(n):          # Newell normal
        a, b = pts[i], pts[(i + 1) % n]
        normal += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
    if normal.length < 1e-12:
        return
    normal.normalize()
    flat = [p - normal * (p - c).dot(normal) for p in pts]
    radius = sum((p - c).length for p in flat) / n
    u = flat[0] - c
    if u.length < 1e-12:
        u = next(((p - c) for p in flat if (p - c).length > 1e-12), None)
        if u is None:
            return
    u.normalize()
    w = normal.cross(u)
    ang = [math.atan2((p - c).dot(w), (p - c).dot(u)) for p in flat]
    turn = sum(math.remainder(ang[(i + 1) % n] - ang[i], math.tau) for i in range(n))
    s = 1.0 if turn >= 0 else -1.0
    step = s * math.tau / n
    off_x = sum(math.cos(ang[i] - step * i) for i in range(n))
    off_y = sum(math.sin(ang[i] - step * i) for i in range(n))
    off = math.atan2(off_y, off_x)
    for i, v in enumerate(verts):
        t = off + step * i
        v.co = c + (u * math.cos(t) + w * math.sin(t)) * radius


def circularize_loops(bm, mode):
    """The loops Maya circularizes for the current selection: faces -> their border loops, edges / vertices ->
    closed loops of selected edges; ``mode`` 'ALL' = every border loop of the mesh. Returns the loop count."""
    if mode == 'ALL':
        edges = [e for e in bm.edges if e.is_boundary]
    elif mode == 'FACE':
        edges = [e for e in bm.edges if sum(f.select for f in e.link_faces) == 1]
    else:
        edges = [e for e in bm.edges if e.select]
    loops = _ordered_loops(edges)
    for loop in loops:
        circularize_loop(loop)
    return len(loops)


class ALLSET_OT_circularize(bpy.types.Operator):
    """Arrange the selected loop of components evenly on a circle (Maya Edit Mesh > Circularize)"""
    bl_idname = "allset.circularize"
    bl_label = "Circularize"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        sel = context.tool_settings.mesh_select_mode
        mode = 'FACE' if sel[2] else 'EDGE'
        total = 0
        for ob in context.objects_in_mode:
            bm = bmesh.from_edit_mesh(ob.data)
            # the whole mesh selected (object-mode menu run, menu_map.OBJECT_MODE): every border loop
            total += circularize_loops(bm, 'ALL' if all(e.select for e in bm.edges) else mode)
            bmesh.update_edit_mesh(ob.data)
        if not total:
            self.report({'WARNING'}, "Select a closed loop of edges or vertices, or faces")
            return {'CANCELLED'}
        return {'FINISHED'}


# --- Connect -----------------------------------------------------------------------------------

def connect(bm, mode):
    """Maya Connect: edges are cut at their midpoints and joined across each face; vertices are joined inside the
    faces they share (modeling_rigging_110.md). Returns the number of new edges (0 = nothing to connect)."""
    before = len(bm.edges)
    if mode == 'VERT':
        verts = [v for v in bm.verts if v.select]
        if len(verts) < 2:
            return 0
        res = bmesh.ops.connect_verts(bm, verts=verts)
        for e in res["edges"]:
            e.select = True
    else:
        edges = [e for e in bm.edges if e.select]
        if not edges:
            return 0
        res = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=False)
        for v in bm.verts:
            v.select = False
        for e in bm.edges:
            e.select = False
        for e in res["geom_inner"]:
            if isinstance(e, bmesh.types.BMEdge):
                e.select = True
        bm.select_flush_mode()
    return len(bm.edges) - before


class ALLSET_OT_connect(bpy.types.Operator):
    """Connect the selected edges through their midpoints, or the selected vertices across their faces
    (Maya Mesh Tools > Connect)"""
    bl_idname = "allset.connect"
    bl_label = "Connect"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        mode = 'VERT' if context.tool_settings.mesh_select_mode[0] else 'EDGE'
        made = 0
        for ob in context.objects_in_mode:
            bm = bmesh.from_edit_mesh(ob.data)
            made += connect(bm, mode)
            bmesh.update_edit_mesh(ob.data)
        if not made:
            self.report({'WARNING'}, CONNECT_WARNING)
            return {'CANCELLED'}
        return {'FINISHED'}


# --- Make Hole ---------------------------------------------------------------------------------

def make_hole(bm, target, stamp):
    """Cut ``stamp``'s outline into ``target`` (Maya Make Hole, merge mode 6: the stamp keeps its position): both
    faces go, the two loops are bridged with quads. Returns the new faces."""
    outer = list(target.edges)
    inner = list(stamp.edges)
    bmesh.ops.delete(bm, geom=[target, stamp], context='FACES_ONLY')
    res = bmesh.ops.bridge_loops(bm, edges=outer + inner)
    return res["faces"]


class ALLSET_OT_make_hole(bpy.types.Operator):
    """Cut the shape of the active (second) face as a hole into the other selected face of the same mesh
    (Maya Mesh Tools > Make Hole)"""
    bl_idname = "allset.make_hole"
    bl_label = "Make Hole"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        ob = context.edit_object
        bm = bmesh.from_edit_mesh(ob.data)
        faces = [f for f in bm.faces if f.select]
        stamp = bm.faces.active if bm.faces.active in faces else None
        if len(faces) != 2 or stamp is None:
            self.report({'WARNING'}, "Select the face to cut, then the face whose shape makes the hole")
            return {'CANCELLED'}
        target = faces[0] if faces[1] is stamp else faces[1]
        if set(target.verts) & set(stamp.verts):
            self.report({'WARNING'}, "The two faces must not share vertices")
            return {'CANCELLED'}
        new = make_hole(bm, target, stamp)
        for f in new:
            f.select = True
        bmesh.update_edit_mesh(ob.data)
        return {'FINISHED'}


classes = (ALLSET_OT_circularize, ALLSET_OT_connect, ALLSET_OT_make_hole)
