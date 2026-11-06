# SPDX-License-Identifier: GPL-3.0-or-later
"""Mesh Tools > Connect as a kit tool, like Maya's Connect Tool (#322).

Entering the tool connects the selected components (Edit Mesh > Connect with the tool's Slide / Segments) and then
waits for clicks: click a vertex or an edge, then another one on the same face, and they are joined by a new edge
(an edge is cut at its Slide point); every further click continues the path from the last point. Ctrl+click an
edge connects its whole edge ring (a new edge loop at Slide). Enter / Esc ends the path; a click on a component that
shares no face with the last point starts a new one. A click away from the mesh keeps Blender's selection.
"""

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty

TOOL = "allset.connect_tool"
HINT = ("Connect Tool: click vertices or edges one after another to connect them, Ctrl+click an edge to connect its "
        "ring, Enter / Esc to end the path")

_path = {}     # the open path: object name, last point (kind, index) and the mesh's counts when it was made


def _counts(bm):
    return len(bm.verts), len(bm.edges), len(bm.faces)


def end_path():
    open_path = bool(_path)
    _path.clear()
    return open_path


def _faces(el):
    return set(el.link_faces)


def _point(el, slide):
    """The vertex a click point stands for; an edge is cut at ``slide`` (from its first vertex)."""
    if isinstance(el, bmesh.types.BMVert):
        return el
    _e, v = bmesh.utils.edge_split(el, el.verts[0], min(max(slide, 0.001), 0.999))
    return v


def click(bm, ob_name, kind, index, slide=0.5):
    """One click of the tool on element ``index`` (``kind`` 'VERT' / 'EDGE'). Returns the new edges (empty when the
    click only starts a path)."""
    seq = bm.verts if kind == 'VERT' else bm.edges
    seq.ensure_lookup_table()
    if not 0 <= index < len(seq):
        return []
    cur = seq[index]
    prev = None
    if _path.get("object") == ob_name and _path.get("counts") == _counts(bm):
        pk, pi = _path["point"]
        pseq = bm.verts if pk == 'VERT' else bm.edges
        pseq.ensure_lookup_table()
        if 0 <= pi < len(pseq):
            prev = (pk, pseq[pi])
    if prev is None or prev[1] is cur or not (_faces(prev[1]) & _faces(cur)):
        for el in (*bm.verts, *bm.edges, *bm.faces):          # a new path: the clicked component alone
            el.select = False
        cur.select = True
        bm.select_flush_mode()
        _path.update(object=ob_name, point=(kind, index), counts=_counts(bm))
        return []
    pv = _point(prev[1], slide)
    cv = _point(cur, slide)
    shared = _faces(pv) & _faces(cv)
    made = []
    if shared and not any(cv in e.verts for e in pv.link_edges):
        res = bmesh.ops.connect_verts(bm, verts=[pv, cv])
        made = list(res["edges"])
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for e in made:
        e.select = True
    cv.select = True
    bm.select_flush_mode()
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    _path.update(object=ob_name, point=('VERT', cv.index), counts=_counts(bm))
    return made


def ring(bm, index, slide=0.5):
    """Ctrl+click: connect the edge ring through edge ``index`` (a new loop at ``slide``)."""
    from .mesh_tools import insert_loop
    bm.edges.ensure_lookup_table()
    if not 0 <= index < len(bm.edges):
        return []
    made = insert_loop(bm, bm.edges[index], min(max(slide, 0.001), 0.999))
    for el in (*bm.verts, *bm.edges, *bm.faces):
        el.select = False
    for e in made:
        e.select = True
    bm.select_flush_mode()
    end_path()
    return made


class ALLSET_OT_connect_click(bpy.types.Operator):
    """Connect Tool click: join this vertex / edge to the last one clicked on the same face (Ctrl: the edge ring)"""
    bl_idname = "allset.connect_click"
    bl_label = "Connect"
    bl_options = {'UNDO'}

    object: StringProperty(options={'SKIP_SAVE', 'HIDDEN'})
    kind: EnumProperty(items=(('VERT', "Vertex", ""), ('EDGE', "Edge", "")), options={'SKIP_SAVE', 'HIDDEN'})
    index: IntProperty(default=-1, options={'SKIP_SAVE', 'HIDDEN'})
    ring: BoolProperty(name="Ring", description="Connect the whole edge ring", options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        from .edge_loops import settings
        ob = bpy.data.objects.get(self.object) if self.object else context.edit_object
        if ob is None or ob.type != 'MESH' or ob.mode != 'EDIT':
            return {'CANCELLED'}
        slide = settings(context).ct_slide
        bm = bmesh.from_edit_mesh(ob.data)
        if self.ring:
            if self.kind != 'EDGE' or not ring(bm, self.index, slide):
                return {'CANCELLED'}
        else:
            click(bm, ob.name, self.kind, self.index, slide)
        bmesh.update_edit_mesh(ob.data)
        return {'FINISHED'}

    def invoke(self, context, event):
        from . import mesh_tools as mt
        view = mt._view(context)
        if view is None:
            return {'PASS_THROUGH'}
        mouse = (event.mouse_region_x, event.mouse_region_y)
        radius = mt.PICK_RADIUS * mt._ui_scale()
        objects = mt._mesh_objects(context)
        ob, index, kind = None, -1, 'EDGE'
        if not self.ring:                     # a vertex wins when the click is close to it
            ob, index = mt.pick(view, objects, mouse, 'VERT', radius * 0.6)
            kind = 'VERT'
        if ob is None:
            ob, index = mt.pick(view, objects, mouse, 'EDGE', radius)
            kind = 'EDGE'
        if ob is None:
            return {'PASS_THROUGH'}
        self.object, self.kind, self.index = ob.name, kind, index
        return self.execute(context)


class ALLSET_OT_connect_end(bpy.types.Operator):
    """End the Connect Tool's path"""
    bl_idname = "allset.connect_end"
    bl_label = "End Connect Path"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        return {'FINISHED'} if end_path() else {'PASS_THROUGH'}


class ALLSET_OT_connect_tool_enter(bpy.types.Operator):
    """Maya Mesh Tools > Connect: connect the selected vertices / edges, then click components to connect them"""
    bl_idname = "allset.connect_tool_enter"
    bl_label = "Connect Tool"
    bl_options = {'REGISTER', 'UNDO'}

    slide: FloatProperty(name="Slide", default=-1.0, min=-1.0, max=1.0, options={'SKIP_SAVE'})
    segments: IntProperty(name="Segments", default=0, min=0, max=100, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return context.mode == 'EDIT_MESH' or (context.mode == 'OBJECT' and ob is not None and ob.type == 'MESH')

    def execute(self, context):
        from .edge_loops import settings
        s = settings(context)
        if self.slide >= 0.0:               # the option window's values become the tool's
            s.ct_slide = self.slide
        if self.segments > 0:
            s.ct_segments = self.segments
        if context.mode == 'OBJECT':
            if not context.active_object.visible_get():
                self.report({'WARNING'}, f"{context.active_object.name} is hidden: show it first")
                return {'CANCELLED'}
            bpy.ops.object.mode_set(mode='EDIT')
        else:                                # Maya: the components selected before the tool are connected
            from .poly_maya import connect
            v, e, _f = context.tool_settings.mesh_select_mode
            if v or e:
                for ob in context.objects_in_mode:
                    bm = bmesh.from_edit_mesh(ob.data)
                    if connect(bm, 'VERT' if v else 'EDGE', 0.0, s.ct_segments, s.ct_slide):
                        bmesh.update_edit_mesh(ob.data)
        end_path()
        try:
            bpy.ops.wm.tool_set_by_id(name=TOOL, space_type='VIEW_3D')
        except (RuntimeError, TypeError):
            pass                             # no 3D View (headless / another editor): the operation still ran
        self.report({'INFO'}, HINT)
        return {'FINISHED'}


classes = (ALLSET_OT_connect_click, ALLSET_OT_connect_end, ALLSET_OT_connect_tool_enter)
