# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya component-mode keys that need more than one Blender operator: Alt+D select none
(back to object mode), Ctrl+B bevel (vertices or edges by the select mode),
Ctrl+F9-F11 convert selection and Delete / Backspace on components.

research/maya/interaction.md:75 (SelectNone: ``changeSelectMode -object; select -cl``),
:79 (Ctrl+F9-F12 convert), hotkeySetup.mel:385 via docs/keymap_mapping.md (Ctrl+B BevelPolygon).
Plan: docs/steps/step_18.md 「계획」 2-3, 5; Delete: docs/steps/step_24.md 「계획」.
"""

import bmesh
import bpy

_MODES = {'VERT': (True, False, False), 'EDGE': (False, True, False), 'FACE': (False, False, True)}


class ALLSET_OT_select_none(bpy.types.Operator):
    """Clear the selection and go back to object mode (Maya Alt+D)"""
    bl_idname = "allset.select_none"
    bl_label = "Select None"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.view_layer is not None

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            bpy.ops.mesh.select_all(action='DESELECT')
        if context.mode != 'OBJECT' and context.active_object is not None:
            bpy.ops.object.mode_set(mode='OBJECT')
        for ob in context.view_layer.objects:
            ob.select_set(False)
        return {'FINISHED'}


def bevel_affect(select_mode):
    """Maya bevels vertices in vertex mode, edges otherwise (faces: their edges)."""
    return 'VERTICES' if tuple(select_mode) == (True, False, False) else 'EDGES'


class ALLSET_OT_bevel(bpy.types.Operator):
    """Bevel the selection right away, dragging sets the width (Maya Ctrl+B)"""
    bl_idname = "allset.bevel"
    bl_label = "Bevel"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def invoke(self, context, event):
        affect = bevel_affect(context.scene.tool_settings.mesh_select_mode)
        bpy.ops.mesh.bevel('INVOKE_DEFAULT', affect=affect)
        return {'FINISHED'}

    def execute(self, context):
        # 0.1 Maya units (decision 8): 0.1 BU was 10 Maya units in the cm template (found in step 48)
        from . import units
        bpy.ops.mesh.bevel(affect=bevel_affect(context.scene.tool_settings.mesh_select_mode),
                           offset=0.1 * units.maya_unit(context.scene))
        return {'FINISHED'}


def touching(bm, select_mode, target):
    """Maya "Convert Selection to Vertices / Edges / Faces": the target elements touching
    the selection, read from the current component type (faces -> their edges / vertices;
    vertices -> the edges / faces using them). Blender's select_mode switch keeps only
    *contained* elements, which is Maya's separate "To Contained ..." (Ctrl+RMB menu), and
    ``use_expand=True`` clears the selection instead (measured in 4.5)."""
    sv, se, sf = select_mode
    if sf and not (sv or se):
        src = [f for f in bm.faces if f.select]
    elif se and not sv:
        src = [e for e in bm.edges if e.select]
    else:
        src = [v for v in bm.verts if v.select]
    out = set()
    for el in src:
        if target == 'VERT':
            out.update([el] if isinstance(el, bmesh.types.BMVert) else el.verts)
        elif target == 'EDGE':
            if isinstance(el, bmesh.types.BMEdge):
                out.add(el)
            else:
                out.update(el.edges if isinstance(el, bmesh.types.BMFace) else el.link_edges)
        else:
            out.update([el] if isinstance(el, bmesh.types.BMFace) else el.link_faces)
    return out


def select_only(bm, target, elements):
    for seq in (bm.verts, bm.edges, bm.faces):
        for el in seq:
            el.select_set(False)
    bm.select_mode = {target}
    for el in elements:
        el.select_set(True)
    bm.select_flush_mode()


class ALLSET_OT_convert_selection(bpy.types.Operator):
    """Convert the selection to the vertices, edges or faces it touches (Maya Ctrl+F9-F11)"""
    bl_idname = "allset.convert_selection"
    bl_label = "Convert Selection"
    bl_options = {'REGISTER', 'UNDO'}

    type: bpy.props.EnumProperty(name="To", items=(('VERT', "Vertices", "Maya Ctrl+F9"),
                                                   ('EDGE', "Edges", "Maya Ctrl+F10"),
                                                   ('FACE', "Faces", "Maya Ctrl+F11")))

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        ts = context.scene.tool_settings
        mode = tuple(ts.mesh_select_mode)
        # Read first: switching the select mode re-flushes the selection.
        found = []
        for ob in context.objects_in_mode_unique_data:
            bm = bmesh.from_edit_mesh(ob.data)
            found.append((ob, bm, touching(bm, mode, self.type)))
        ts.mesh_select_mode = _MODES[self.type]
        for ob, bm, elements in found:
            select_only(bm, self.type, elements)
            bmesh.update_edit_mesh(ob.data)
        return {'FINISHED'}


def delete_components(bm, mode):
    """Maya Delete on one mesh's selection; ``mode`` = 'FACE' / 'EDGE' / 'VERT'.

    Returns (deleted, skipped): elements removed and border edges left alone.
    research/maya/runtime_commands.json DeleteEdge (polyDelEdge -cv true: non-border
    edges, vertices cleaned up) and DeleteVertex (vertices and their attached edges).
    """
    if mode == 'FACE':
        faces = [f for f in bm.faces if f.select]
        bmesh.ops.delete(bm, geom=faces, context='FACES')
        return len(faces), 0
    if mode == 'EDGE':
        sel = [e for e in bm.edges if e.select]
        inner = [e for e in sel if len(e.link_faces) == 2]
        if inner:
            bmesh.ops.dissolve_edges(bm, edges=inner, use_verts=True, use_face_split=False)
        return len(inner), len(sel) - len(inner)
    verts = [v for v in bm.verts if v.select]
    if verts:
        bmesh.ops.dissolve_verts(bm, verts=verts, use_face_split=False, use_boundary_tear=False)
    return len(verts), 0


def select_mode_kind(ts):
    vert, edge, face = ts.mesh_select_mode
    return 'FACE' if face else 'EDGE' if edge else 'VERT'


class ALLSET_OT_delete_components(bpy.types.Operator):
    """Delete the selected faces, edges (non-border, cleaning up their vertices) or vertices
    right away, by the select mode (Maya Delete on components)"""
    bl_idname = "allset.delete_components"
    bl_label = "Delete Components"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        mode = select_mode_kind(context.tool_settings)
        deleted = skipped = 0
        for ob in context.objects_in_mode_unique_data:
            if ob.type != 'MESH':
                continue
            bm = bmesh.from_edit_mesh(ob.data)
            d, s = delete_components(bm, mode)
            for seq in (bm.verts, bm.edges, bm.faces):
                for el in seq:
                    el.select = False
            bm.select_flush(False)
            bmesh.update_edit_mesh(ob.data)
            deleted, skipped = deleted + d, skipped + s
        if skipped:
            self.report({'WARNING'}, f"{skipped} border edge(s) kept (Maya Delete Edge skips borders)")
        if not deleted:
            if not skipped:
                self.report({'INFO'}, "Nothing selected")
            return {'CANCELLED'}
        return {'FINISHED'}


class ALLSET_OT_select_loops(bpy.types.Operator):
    """Select the edge loops (or rings) of the selected edges (Maya Select > Contiguous Edges, Convert
    Selection > To Edge Loop / Ring)"""
    bl_idname = "allset.select_loops"
    bl_label = "Select Edge Loops"
    bl_options = {'REGISTER', 'UNDO'}

    ring: bpy.props.BoolProperty(name="Ring", description="Edge rings instead of edge loops")

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        # Blender 4.5: mesh.loop_multi_select(ring); 5.x: mesh.select_edge_loop_multi /
        # select_edge_ring_multi (VIEW3D_MT_edit_mesh_select_loops, docs/steps/step_53.md).
        from .. import compat
        if compat.has_op(bpy.ops.mesh, "loop_multi_select"):
            return bpy.ops.mesh.loop_multi_select(ring=self.ring)
        op = bpy.ops.mesh.select_edge_ring_multi if self.ring else bpy.ops.mesh.select_edge_loop_multi
        return op()



classes = (ALLSET_OT_select_none, ALLSET_OT_bevel, ALLSET_OT_convert_selection,
           ALLSET_OT_delete_components, ALLSET_OT_select_loops)
