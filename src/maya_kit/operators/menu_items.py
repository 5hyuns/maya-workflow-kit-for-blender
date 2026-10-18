# SPDX-License-Identifier: GPL-3.0-or-later
"""Small Maya menu commands Blender has no single operator for (docs/steps/step_101.md 「계획」 3).

Each reproduces the Maya result with a few data / bmesh edits: Modify > Naming, Mesh Display > Soften/Harden
Edges, Edit Mesh > Detach / Edit Edge Flow / Wedge, Deform > Nonlinear, Display > Object Display, Mesh Tools >
Sculpting Tools, UV > Assign Checker Shader, the Audio menu, Stereo > Create, and ``menu_note`` for items whose
Maya behaviour already is Blender's (only the notice is shown). Maya behaviour: research/maya/re/menu_honesty.md.
"""

import math

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector


def _hierarchy(objects):
    """``objects`` and all their descendants, parents first, each once."""
    out, seen = [], set()

    def walk(ob):
        if ob.name in seen:
            return
        seen.add(ob.name)
        out.append(ob)
        for child in ob.children:
            walk(child)
    for ob in objects:
        walk(ob)
    return out


def _rename(ob, fn):
    """Rename the object and (like Maya renames the shape with its transform) its single-user data."""
    ob.name = fn(ob.name)
    data = ob.data
    if data is not None and data.users == 1 and data.library is None:
        data.name = fn(data.name)


# --- Modify > Naming --------------------------------------------------------------------------

class MAYAKIT_OT_prefix_hierarchy(bpy.types.Operator):
    """Put a prefix in front of the names of the selected objects and everything under them
    (Maya Modify > Prefix Hierarchy Names)"""
    bl_idname = "maya_kit.prefix_hierarchy"
    bl_label = "Prefix Hierarchy Names"
    bl_options = {'REGISTER', 'UNDO'}

    prefix: StringProperty(name="Prefix", default="prefix_")

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if not self.prefix:
            return {'CANCELLED'}
        obs = _hierarchy(context.selected_objects)
        for ob in obs:
            _rename(ob, lambda name: self.prefix + name)
        self.report({'INFO'}, f"Prefixed {len(obs)} name(s)")
        return {'FINISHED'}


class MAYAKIT_OT_search_replace_names(bpy.types.Operator):
    """Replace text in object names: in the selected hierarchies, the selection only, or every object
    (Maya Modify > Search and Replace Names)"""
    bl_idname = "maya_kit.search_replace_names"
    bl_label = "Search and Replace Names"
    bl_options = {'REGISTER', 'UNDO'}

    search: StringProperty(name="Search For")
    replace: StringProperty(name="Replace With")
    scope: EnumProperty(name="Operation", default='HIERARCHY', items=(
        ('HIERARCHY', "Hierarchy", "The selected objects and everything under them"),
        ('SELECTED', "Selected", "Only the selected objects"),
        ('ALL', "All", "Every object in the scene")))

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if not self.search:
            self.report({'WARNING'}, "Nothing to search for")
            return {'CANCELLED'}
        if self.scope == 'ALL':
            obs = list(context.scene.objects)
        elif self.scope == 'SELECTED':
            obs = list(context.selected_objects)
        else:
            obs = _hierarchy(context.selected_objects)
        n = 0
        for ob in obs:
            if self.search in ob.name:
                _rename(ob, lambda name: name.replace(self.search, self.replace))
                n += 1
        self.report({'INFO'}, f"Renamed {n} object(s)")
        return {'FINISHED'}


# --- Mesh Display > Soften/Harden Edges -------------------------------------------------------

def soften_harden(bm, angle, edges=None):
    """Maya polySoftEdge: an edge whose faces meet at less than ``angle`` degrees is soft, the rest hard;
    the faces shade smooth (mayapy: Soften/Harden on an object = every edge, angle 30)."""
    limit = math.radians(angle) + 1e-6
    for e in (bm.edges if edges is None else edges):
        e.smooth = len(e.link_faces) != 2 or e.calc_face_angle(0.0) <= limit
    for e in (bm.edges if edges is None else edges):
        for f in e.link_faces:
            f.smooth = True


class MAYAKIT_OT_soften_harden(bpy.types.Operator):
    """Soften edges whose faces meet at less than the angle, harden the rest: the selected edges in
    component mode, every edge of the selected meshes in object mode (Maya Mesh Display > Soften/Harden)"""
    bl_idname = "maya_kit.soften_harden"
    bl_label = "Soften/Harden Edges"
    bl_options = {'REGISTER', 'UNDO'}

    angle: FloatProperty(name="Angle", default=30.0, min=0.0, max=180.0,
                         description="Maya default 30: faces at a smaller angle shade smooth across the edge")
    option_box: BoolProperty(options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return any(ob.type == 'MESH' for ob in _meshes(context))

    def invoke(self, context, event):
        if self.option_box:
            return context.window_manager.invoke_props_dialog(self)
        return self.execute(context)

    def execute(self, context):
        for ob in _meshes(context):
            if ob.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(ob.data)
                soften_harden(bm, self.angle, [e for e in bm.edges if e.select] or None)
                bmesh.update_edit_mesh(ob.data)
            else:
                bm = bmesh.new()
                bm.from_mesh(ob.data)
                soften_harden(bm, self.angle)
                bm.to_mesh(ob.data)
                bm.free()
                ob.data.update()
        return {'FINISHED'}


def _meshes(context):
    if context.mode == 'EDIT_MESH':
        return [ob for ob in context.objects_in_mode if ob.type == 'MESH']
    return [ob for ob in context.selected_objects if ob.type == 'MESH']


# --- Edit Mesh > Detach / Edit Edge Flow / Wedge ----------------------------------------------

def _edit_bm(context):
    ob = context.edit_object
    return ob, bmesh.from_edit_mesh(ob.data)


def detach(bm, mode):
    """Maya Detach of vertices (each face around a selected vertex gets its own vertex) or edges (split
    open). Returns how many elements were detached."""
    if mode == 'VERT':
        verts = [v for v in bm.verts if v.select and len(v.link_faces) > 1]
        for v in verts:
            bmesh.utils.vert_separate(v, list(v.link_edges))
        return len(verts)
    if mode == 'EDGE':
        edges = [e for e in bm.edges if e.select and not e.is_boundary]
        if edges:
            bmesh.ops.split_edges(bm, edges=edges)
        return len(edges)
    return 0


class MAYAKIT_OT_detach(bpy.types.Operator):
    """Detach the selected components: vertices split per face, edges split open, faces become their own
    shell (Maya Edit Mesh > Detach)"""
    bl_idname = "maya_kit.detach"
    bl_label = "Detach"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        ob, bm = _edit_bm(context)
        mode = context.tool_settings.mesh_select_mode
        if mode[2]:
            if not any(f.select for f in bm.faces):
                self.report({'WARNING'}, "No vertices or edges selected to detach.")
                return {'CANCELLED'}
            bpy.ops.mesh.split()
            return {'FINISHED'}
        n = detach(bm, 'VERT' if mode[0] else 'EDGE')
        if not n:
            self.report({'WARNING'}, "No vertices or edges selected to detach.")   # Maya's warning (mayapy)
            return {'CANCELLED'}
        bmesh.update_edit_mesh(ob.data)
        return {'FINISHED'}


def _across(v, e):
    """The edge of ``v`` opposite ``e`` in a 4-edge vertex (the next edge of the ring), or None."""
    if len(v.link_edges) != 4:
        return None
    faces = set(e.link_faces)
    others = [x for x in v.link_edges if x is not e and not (set(x.link_faces) & faces)]
    return others[0] if len(others) == 1 else None


def edge_flow(bm, edges, flow=1.0):
    """Maya Edit Edge Flow (polyEditEdgeFlow -adjustEdgeFlow): move each vertex of the selected edges onto the
    curve through its two ring neighbours and their next ring neighbours (Catmull-Rom at the vertex's own
    parameter), so the loop follows the surrounding curvature; flow 0 = the straight line between them.
    Returns the number of moved vertices."""
    selected = set(edges)
    moves = {}
    for v in {v for e in edges for v in e.verts}:
        ring = [x for x in v.link_edges if x not in selected]
        if len(ring) != 2:
            continue
        pts = []
        for x in ring:
            a = x.other_vert(v)
            nxt = _across(a, x)
            pts.append((a.co.copy(), nxt.other_vert(a).co.copy() if nxt else a.co.copy()))
        (a, a2), (b, b2) = pts
        da, db = (v.co - a).length, (v.co - b).length
        if da + db < 1e-9:
            continue
        t = da / (da + db)
        t2, t3 = t * t, t * t * t
        # Catmull-Rom between a and b with outer points a2, b2
        curve = 0.5 * ((2 * a) + (-a2 + b) * t + (2 * a2 - 5 * a + 4 * b - b2) * t2 + (-a2 + 3 * a - 3 * b + b2) * t3)
        line = a.lerp(b, t)
        moves[v] = line.lerp(curve, flow)
    for v, co in moves.items():
        v.co = co
    return len(moves)


class MAYAKIT_OT_edge_flow(bpy.types.Operator):
    """Move the selected edges so they follow the curvature of the surrounding surface
    (Maya Edit Mesh > Edit Edge Flow)"""
    bl_idname = "maya_kit.edge_flow"
    bl_label = "Edit Edge Flow"
    bl_options = {'REGISTER', 'UNDO'}

    flow: FloatProperty(name="Edge Flow", default=1.0, soft_min=-1.0, soft_max=2.0,
                        description="Maya adjustEdgeFlow: 1 follows the curvature, 0 is straight")

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        for ob in context.objects_in_mode:
            bm = bmesh.from_edit_mesh(ob.data)
            edge_flow(bm, [e for e in bm.edges if e.select], self.flow)
            bmesh.update_edit_mesh(ob.data)
        return {'FINISHED'}


class MAYAKIT_OT_wedge(bpy.types.Operator):
    """Sweep the selected faces around one of their edges (the active edge) (Maya Edit Mesh > Wedge)"""
    bl_idname = "maya_kit.wedge"
    bl_label = "Wedge"
    bl_options = {'REGISTER', 'UNDO'}

    angle: FloatProperty(name="Wedge Angle", default=90.0, min=-360.0, max=360.0)
    divisions: IntProperty(name="Divisions", default=4, min=1, max=256)

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        ob, bm = _edit_bm(context)
        faces = [f for f in bm.faces if f.select]
        edge = bm.select_history.active
        if not isinstance(edge, bmesh.types.BMEdge):
            edge = next((e for e in bm.edges if e.select and e.is_boundary is False
                         and sum(f.select for f in e.link_faces) == 1), None)
        if not faces or edge is None:
            self.report({'WARNING'}, "No faces selected to wedge. Select faces and one or more edges from the "
                                     "selected faces to wedge about.")   # Maya's warning (mayapy)
            return {'CANCELLED'}
        mw = ob.matrix_world
        p0, p1 = mw @ edge.verts[0].co, mw @ edge.verts[1].co
        axis = (p1 - p0).normalized()
        centre = (p0 + p1) / 2
        # spin so the faces turn away from the rest of the mesh (towards their normal)
        normal = (mw.to_3x3() @ faces[0].normal).normalized()
        side = (mw @ faces[0].calc_center_median()) - centre
        if axis.cross(side).dot(normal) < 0:
            axis = -axis
        bpy.ops.mesh.spin(steps=self.divisions, angle=math.radians(self.angle), center=centre, axis=axis,
                          dupli=False, use_auto_merge=True)
        return {'FINISHED'}


# --- Deform > Nonlinear -----------------------------------------------------------------------

NONLINEAR = (('BEND', "Bend", "Maya bend1: Simple Deform Bend"),
             ('TAPER', "Flare", "Maya flare1: Simple Deform Taper"),
             ('STRETCH', "Squash", "Maya squash1: Simple Deform Stretch"))
_NONLINEAR_NAME = {'BEND': "bend", 'TAPER': "flare", 'STRETCH': "squash"}


class MAYAKIT_OT_nonlinear(bpy.types.Operator):
    """Add a nonlinear deformer to the selected objects: Simple Deform with Maya's neutral start value
    (Maya Deform > Nonlinear: curvature 0 / flare 1 / factor 0 until you edit it)"""
    bl_idname = "maya_kit.nonlinear"
    bl_label = "Nonlinear Deformer"
    bl_options = {'REGISTER', 'UNDO'}

    method: EnumProperty(items=NONLINEAR, name="Type")

    @classmethod
    def poll(cls, context):
        return any(ob.type in {'MESH', 'CURVE', 'SURFACE', 'LATTICE'} for ob in context.selected_objects)

    def execute(self, context):
        base = _NONLINEAR_NAME[self.method]
        names = {md.name for ob in bpy.data.objects for md in ob.modifiers}
        n = 1
        while f"{base}{n}" in names:
            n += 1
        for ob in context.selected_objects:
            if ob.type not in {'MESH', 'CURVE', 'SURFACE', 'LATTICE'}:
                continue
            md = ob.modifiers.new(f"{base}{n}", 'SIMPLE_DEFORM')
            md.deform_method = self.method
            md.deform_axis = 'Z'          # Maya's handle points along Y (up) = Blender Z
            md.angle = 0.0
            md.factor = 0.0
        return {'FINISHED'}


# --- Display > Object Display -----------------------------------------------------------------

TEMPLATE_PROP = "maya_kit_template"
DISPLAY = (('TEMPLATE', "Template", "Grey wireframe that can't be selected in the view"),
           ('UNTEMPLATE', "Untemplate", "Undo Template (on the selection, else on every templated object)"),
           ('BBOX', "Bounding Box", "Draw as a bounding box"),
           ('NO_BBOX', "No Bounding Box", "Draw the geometry again"))


class MAYAKIT_OT_object_display(bpy.types.Operator):
    """Maya Display > Object Display: template / bounding box display of the selected objects"""
    bl_idname = "maya_kit.object_display"
    bl_label = "Object Display"
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(items=DISPLAY, name="Display")

    def execute(self, context):
        obs = list(context.selected_objects)
        if self.kind == 'UNTEMPLATE':
            obs = [ob for ob in obs if ob.get(TEMPLATE_PROP)] or \
                [ob for ob in context.scene.objects if ob.get(TEMPLATE_PROP)]
        if not obs:
            self.report({'WARNING'}, "Nothing selected.")
            return {'CANCELLED'}
        for ob in obs:
            if self.kind == 'TEMPLATE':
                ob[TEMPLATE_PROP] = ob.display_type
                ob.display_type = 'WIRE'
                ob.select_set(False)
                ob.hide_select = True
            elif self.kind == 'UNTEMPLATE':
                ob.hide_select = False
                ob.display_type = ob.get(TEMPLATE_PROP) or 'TEXTURED'
                del ob[TEMPLATE_PROP]
            elif self.kind == 'BBOX':
                ob.display_type = 'BOUNDS'
            elif ob.display_type == 'BOUNDS':
                ob.display_type = 'TEXTURED'
        return {'FINISHED'}


# --- Mesh Tools > Sculpting Tools -------------------------------------------------------------

SCULPT_LIBRARY = "brushes/essentials_brushes-mesh_sculpt.blend/Brush/"


class MAYAKIT_OT_sculpt_tool(bpy.types.Operator):
    """Sculpt the active mesh with this brush (Maya Mesh Tools > Sculpting Tools)"""
    bl_idname = "maya_kit.sculpt_tool"
    bl_label = "Sculpting Tool"
    bl_options = {'REGISTER', 'UNDO'}

    brush: StringProperty(name="Brush", options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and ob.type == 'MESH'

    def execute(self, context):
        if context.mode != 'SCULPT':
            bpy.ops.object.mode_set(mode='SCULPT')
        try:
            bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',
                                         relative_asset_identifier=SCULPT_LIBRARY + self.brush)
        except RuntimeError as ex:
            self.report({'WARNING'}, str(ex).strip().splitlines()[-1])
            return {'CANCELLED'}
        return {'FINISHED'}


# --- UV > Assign Checker Shader ---------------------------------------------------------------

CHECKER_IMAGE = "uvChecker"


class MAYAKIT_OT_checker_shader(bpy.types.Operator):
    """Give the selected objects (or faces) a UV checker material (Maya UV > Assign Checker Shader)"""
    bl_idname = "maya_kit.checker_shader"
    bl_label = "Assign Checker Shader"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from . import material
        obs = [ob for ob in (context.objects_in_mode or context.selected_objects) if ob.type == 'MESH']
        if not obs:
            self.report({'WARNING'}, "Select objects or faces to assign the checker to")
            return {'CANCELLED'}
        img = bpy.data.images.get(CHECKER_IMAGE) or bpy.data.images.new(CHECKER_IMAGE, 1024, 1024)
        img.generated_type = 'UV_GRID'
        mat = material.new_material('LAMBERT')
        tree = mat.node_tree
        node = tree.nodes.new("ShaderNodeTexImage")
        node.image = img
        node.location = (-350, 300)
        bsdf = next(nd for nd in tree.nodes if nd.type == 'BSDF_PRINCIPLED')
        tree.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
        material.assign(context, mat, obs)
        return {'FINISHED'}


# --- Audio ------------------------------------------------------------------------------------

def _strips(scene, create=False):
    if scene.sequence_editor is None:
        if not create:
            return None
        scene.sequence_editor_create()
    se = scene.sequence_editor
    return getattr(se, "strips", None) or se.sequences


class MAYAKIT_OT_import_audio(bpy.types.Operator, ImportHelper):
    """Import a sound at the start of the time slider; it plays with the scene (Maya Audio > Import Audio)"""
    bl_idname = "maya_kit.import_audio"
    bl_label = "Import Audio"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(default="*.wav;*.mp3;*.ogg;*.flac;*.aif;*.aiff;*.m4a", options={'HIDDEN'})

    def execute(self, context):
        import os
        scene = context.scene
        strips = _strips(scene, create=True)
        try:
            strip = strips.new_sound(os.path.basename(self.filepath), self.filepath, 1, scene.frame_start)
        except RuntimeError as ex:
            self.report({'ERROR'}, str(ex).strip())
            return {'CANCELLED'}
        self.report({'INFO'}, f"Imported {strip.name}")
        return {'FINISHED'}


class MAYAKIT_OT_delete_sounds(bpy.types.Operator):
    """Delete the scene's sounds (Maya Audio > Delete Sounds)"""
    bl_idname = "maya_kit.delete_sounds"
    bl_label = "Delete Sounds"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        strips = _strips(context.scene)
        sounds = [s for s in strips if s.type == 'SOUND'] if strips is not None else []
        for s in sounds:
            strips.remove(s)
        self.report({'INFO'}, f"Deleted {len(sounds)} sound(s)")
        return {'FINISHED'}


# --- Stereo > Create --------------------------------------------------------------------------

class MAYAKIT_OT_stereo_camera(bpy.types.Operator):
    """Create a stereo camera: a Maya camera with Blender's stereoscopy (Views) turned on
    (Maya Stereo > Create > Stereo Camera)"""
    bl_idname = "maya_kit.stereo_camera"
    bl_label = "Stereo Camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from . import create
        ob = create.create(context, 'CAMERA', maya_naming=False)
        from . import naming
        naming.apply_maya_name(ob, "stereoCamera")
        render = context.scene.render
        render.use_multiview = True
        render.views_format = 'STEREO_3D'
        return {'FINISHED'}


# --- notice-only items ------------------------------------------------------------------------

class MAYAKIT_OT_menu_note(bpy.types.Operator):
    """Maya item whose behaviour already is Blender's: shows the notice"""
    bl_idname = "maya_kit.menu_note"
    bl_label = "Note"
    bl_options = {'INTERNAL'}

    item: StringProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        from ..ui import notices
        n = notices.notice(self.item)
        if n:
            notices.show(f"{self.item.rsplit('/', 1)[-1]}: {n[1]}")
            self.report({'INFO'}, n[1])
        return {'FINISHED'}


classes = (MAYAKIT_OT_prefix_hierarchy, MAYAKIT_OT_search_replace_names, MAYAKIT_OT_soften_harden,
           MAYAKIT_OT_detach, MAYAKIT_OT_edge_flow, MAYAKIT_OT_wedge, MAYAKIT_OT_nonlinear,
           MAYAKIT_OT_object_display, MAYAKIT_OT_sculpt_tool, MAYAKIT_OT_checker_shader, MAYAKIT_OT_import_audio,
           MAYAKIT_OT_delete_sounds, MAYAKIT_OT_stereo_camera, MAYAKIT_OT_menu_note)
