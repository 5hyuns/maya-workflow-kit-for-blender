# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya material assignment.

Lighting/Shading > Material Attributes / Assign New / Favorite / Existing Material
() and the same items at the end of the RMB object
menu list (). Maya assigns to the selection,
or to the object the RMB menu was opened on when nothing is selected.

- Object assignment = the whole shape gets the material (Maya: the shape joins the
  shading group): one slot, every face/spline index 0.
- Face assignment (mesh edit mode, face select mode, selected faces) = only those
  faces: the material's slot is found or added and their ``material_index`` set.
  A mesh without slots first gets an empty slot (Blender's default grey, Maya's
  lambert1) so the other faces keep it ().
"""

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty

SUPPORTED = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}

# Maya createAndAssignShader kinds on Principled BSDF ():
# kind -> (Maya node name, UI label, Principled inputs).
MATERIALS = {
    'STANDARD_SURFACE': ("standardSurface", "Standard Surface", {}),
    'LAMBERT': ("lambert", "Lambert", {"Roughness": 1.0, "Specular IOR Level": 0.0}),
    'BLINN': ("blinn", "Blinn", {"Roughness": 0.3}),
    'PHONG': ("phong", "Phong", {"Roughness": 0.15}),
    'SURFACE': ("surfaceShader", "Surface Shader", {"Emission Strength": 1.0}),
}
KIND_ITEMS = [(k, v[1], f"Maya {v[0]} (Principled BSDF)") for k, v in MATERIALS.items()]
# The Assign Favorite Material submenu (Maya's surface-shader favourites).
FAVORITES = ('LAMBERT', 'BLINN', 'PHONG', 'STANDARD_SURFACE')
# ID property naming the Maya node type of a kit-made material (AE tab label/sections, step 38).
TYPE_PROP = "maya_kit_type"


# --- data ------------------------------------------------------------------------------------

def new_material(kind):
    """A Maya-named (lambert1, blinn2, ...) Principled material of this kind."""
    from . import naming
    base, _label, values = MATERIALS[kind]
    n = naming.next_number(base, {m.name for m in bpy.data.materials})
    mat = bpy.data.materials.new(f"{base}{n}")
    mat[TYPE_PROP] = base
    mat.use_nodes = True
    node = next(nd for nd in mat.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED')
    for socket, value in values.items():
        node.inputs[socket].default_value = value
    if kind == 'SURFACE':
        node.inputs["Emission Color"].default_value = node.inputs["Base Color"].default_value
    return mat


def targets(context, rmb=False):
    """Objects to assign to: the edited objects, the selection, else (from the RMB
    menu) the object the menu was opened on (Maya-374)."""
    if context.mode.startswith('EDIT'):
        return [o for o in context.objects_in_mode if o.type in SUPPORTED]
    obs = [o for o in context.selected_objects if o.type in SUPPORTED]
    if not obs and rmb:
        ob = bpy.data.objects.get(getattr(context.window_manager, "maya_kit_mm_target", ""))
        if ob is not None and ob.type in SUPPORTED:
            obs = [ob]
    return obs


def _poll(context):
    # Poll can't see ``rmb``: the object under the last RMB menu counts too (Maya doesn't
    # grey these items either; without a target the operator reports and cancels).
    return bool(targets(context, rmb=True))


def _face_mode(context):
    return context.mode == 'EDIT_MESH' and context.tool_settings.mesh_select_mode[2]


def assign_object(ob, mat):
    """The whole object gets ``mat``; returns its slot index (0)."""
    data = ob.data
    if ob.type == 'MESH':
        if ob.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(data)
            for f in bm.faces:
                f.material_index = 0
            bmesh.update_edit_mesh(data)
        else:
            data.polygons.foreach_set("material_index", [0] * len(data.polygons))
    elif ob.type in {'CURVE', 'SURFACE'}:
        for spline in data.splines:
            spline.material_index = 0
    data.materials.clear()
    data.materials.append(mat)
    ob.active_material_index = 0
    ob.active_material = mat  # also right for object-linked slots
    return 0


def assign_faces(ob, mat):
    """Selected faces of an edited mesh get ``mat``; returns the slot index, or None
    when no face is selected."""
    bm = bmesh.from_edit_mesh(ob.data)
    faces = [f for f in bm.faces if f.select]
    if not faces:
        return None
    slots = ob.material_slots
    index = next((i for i, s in enumerate(slots) if s.material == mat), None)
    if index is None:
        if not slots:
            ob.data.materials.append(None)  # the rest of the mesh keeps the default
        ob.data.materials.append(mat)
        index = len(ob.material_slots) - 1
        bm = bmesh.from_edit_mesh(ob.data)
        faces = [f for f in bm.faces if f.select]
    for f in faces:
        f.material_index = index
    bmesh.update_edit_mesh(ob.data)
    return index


def assign(context, mat, obs):
    """Assign ``mat`` the Maya way; returns {object name: slot index}."""
    done = {}
    faces = _face_mode(context)
    for ob in obs:
        index = assign_faces(ob, mat) if faces and ob.type == 'MESH' and ob.mode == 'EDIT' else None
        done[ob.name] = assign_object(ob, mat) if index is None else index
    return done


def _show_in_ae(context, done):
    """Point the Attribute Editor's tab at the assigned material (Maya shows a new
    material in the AE, AEpopupWhenCreatingShaders)."""
    from ..ui import attribute_editor
    ob = context.active_object
    if ob is None or ob.name not in done:
        ob = bpy.data.objects.get(next(iter(done)))
    attribute_editor.set_tab(context, f"MAT:{done[ob.name]}")


# --- operators -------------------------------------------------------------------------------

_RMB = BoolProperty(name="From RMB Menu", options={'HIDDEN', 'SKIP_SAVE'},
                    description="Use the object under the RMB menu when nothing is selected")


def create_and_assign(op, context, kind):
    obs = targets(context, op.rmb)
    if not obs:
        op.report({'WARNING'}, "Select objects or faces to assign a material to")
        return {'CANCELLED'}
    mat = new_material(kind)
    _show_in_ae(context, assign(context, mat, obs))
    return {'FINISHED'}


class MAYAKIT_OT_shelf_material(bpy.types.Operator):
    """Create a material and assign it to the selected objects or faces (Maya shelf
    material buttons, Assign Favorite Material)"""
    bl_idname = "maya_kit.shelf_material"
    bl_label = "Assign New Material"
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(items=KIND_ITEMS)
    rmb: _RMB

    @classmethod
    def poll(cls, context):
        return _poll(context)

    def execute(self, context):
        return create_and_assign(self, context, self.kind)


class MAYAKIT_OT_assign_new_material(bpy.types.Operator):
    """Pick a material type, create it and assign it to the selected objects or faces
    (Maya Assign New Material, Shift+T)"""
    bl_idname = "maya_kit.assign_new_material"
    bl_label = "Assign New Material"
    bl_options = {'REGISTER', 'UNDO'}
    bl_property = "kind"

    kind: EnumProperty(items=KIND_ITEMS, name="Material")
    rmb: _RMB

    @classmethod
    def poll(cls, context):
        return _poll(context)

    def invoke(self, context, event):
        # Maya's "Assign New Material" type list with its search field.
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        return create_and_assign(self, context, self.kind)


class MAYAKIT_OT_assign_material(bpy.types.Operator):
    """Assign this material to the selected objects or faces (Maya Assign Existing Material)"""
    bl_idname = "maya_kit.assign_material"
    bl_label = "Assign Existing Material"
    bl_options = {'REGISTER', 'UNDO'}

    material: StringProperty(name="Material", options={'SKIP_SAVE'})
    rmb: _RMB

    @classmethod
    def poll(cls, context):
        return _poll(context)

    def execute(self, context):
        mat = bpy.data.materials.get(self.material)
        obs = targets(context, self.rmb)
        if mat is None or not obs:
            self.report({'WARNING'}, "Select objects or faces and a material")
            return {'CANCELLED'}
        assign(context, mat, obs)
        return {'FINISHED'}


class MAYAKIT_OT_material_attributes(bpy.types.Operator):
    """Show the object's material in the Attribute Editor (Maya Material Attributes)"""
    bl_idname = "maya_kit.material_attributes"
    bl_label = "Material Attributes"

    rmb: _RMB

    @staticmethod
    def _object(context, rmb):
        if rmb:
            ob = bpy.data.objects.get(getattr(context.window_manager, "maya_kit_mm_target", ""))
            if ob is not None:
                return ob
        return context.active_object

    @classmethod
    def poll(cls, context):
        ob = cls._object(context, True)
        return ob is not None and any(s.material for s in ob.material_slots)

    def execute(self, context):
        from ..ui import attribute_editor
        ob = self._object(context, self.rmb)
        if ob is None:
            return {'CANCELLED'}
        slots = ob.material_slots
        i = ob.active_material_index
        if i >= len(slots) or slots[i].material is None:
            i = next((n for n, s in enumerate(slots) if s.material), None)
        if i is None:
            self.report({'WARNING'}, f"{ob.name} has no material")
            return {'CANCELLED'}
        if context.active_object is not ob and context.view_layer.objects.get(ob.name):
            context.view_layer.objects.active = ob
        context.window_manager.maya_kit_dock = 'ATTRIBUTE_EDITOR'
        attribute_editor.set_tab(context, f"MAT:{i}")
        space = context.space_data
        if space is not None and space.type == 'VIEW_3D' and not space.show_region_ui:
            attribute_editor._show_sidebar_later(space)
        for area in context.screen.areas if context.screen else ():
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}


# --- menus -----------------------------------------------------------------------------------

class MAYAKIT_MT_assign_favorite_material(bpy.types.Menu):
    """Create a material of a favourite type and assign it (Maya Assign Favorite Material)"""
    bl_idname = "MAYAKIT_MT_assign_favorite_material"
    bl_label = "Assign Favorite Material"
    rmb = False

    def draw(self, context):
        for kind in FAVORITES:
            op = self.layout.operator("maya_kit.shelf_material", text=MATERIALS[kind][1], icon='MATERIAL')
            op.kind = kind
            op.rmb = self.rmb


class MAYAKIT_MT_assign_existing_material(bpy.types.Menu):
    """Assign a material of the scene (Maya Assign Existing Material)"""
    bl_idname = "MAYAKIT_MT_assign_existing_material"
    bl_label = "Assign Existing Material"
    rmb = False

    def draw(self, context):
        mats = sorted((m for m in bpy.data.materials if not m.is_grease_pencil), key=lambda m: m.name.lower())
        if not mats:
            self.layout.label(text="No materials in the scene")
            return
        for mat in mats:
            op = self.layout.operator("maya_kit.assign_material", text=mat.name, icon='MATERIAL')
            op.material = mat.name
            op.rmb = self.rmb


class MAYAKIT_MT_assign_existing_material_rmb(MAYAKIT_MT_assign_existing_material):
    """Assign a material of the scene to the selection or the object under the RMB menu"""
    bl_idname = "MAYAKIT_MT_assign_existing_material_rmb"
    rmb = True


classes = (MAYAKIT_OT_shelf_material, MAYAKIT_OT_assign_new_material, MAYAKIT_OT_assign_material,
           MAYAKIT_OT_material_attributes, MAYAKIT_MT_assign_favorite_material,
           MAYAKIT_MT_assign_existing_material, MAYAKIT_MT_assign_existing_material_rmb)
