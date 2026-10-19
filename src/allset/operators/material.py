# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya material assignment (docs/steps/step_29.md 「계획」).

Lighting/Shading > Material Attributes / Assign New / Favorite / Existing Material
(research/maya/menus.md:1652-1657) and the same items at the end of the RMB object
menu list (research/maya/hotkeys_and_menus.md:252). Maya assigns to the selection,
or to the object the RMB menu was opened on when nothing is selected.

- Object assignment = the whole shape gets the material (Maya: the shape joins the
  shading group): one slot, every face/spline index 0.
- Face assignment (mesh edit mode, face select mode, selected faces) = only those
  faces: the material's slot is found or added and their ``material_index`` set.
  A mesh without slots first gets an empty slot (Blender's default grey, Maya's
  lambert1) so the other faces keep it (research/maya/concepts.md:113-115).
"""

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty

from .. import compat

SUPPORTED = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}

# Maya createAndAssignShader kinds on Principled BSDF (research/maya/shelves.md:60-62):
# kind -> (Maya node name, UI label, Principled inputs).
MATERIALS = {
    'STANDARD_SURFACE': ("standardSurface", "Standard Surface", {}),
    # Arnold's default material (Maya with mtoa); same Principled stand-in (render.md §4.4, step 67)
    'AI_STANDARD_SURFACE': ("aiStandardSurface", "aiStandardSurface", {}),
    # Maya lambert defaults (mayapy, docs/steps/step_100.md): color 0.5 grey; diffuse 0.8 has no Principled input
    # (its "Weight" socket is disabled), so the colour is Maya's attribute value, not color x diffuse
    # incandescence 0 = black Emission Color (Principled's default is white at strength 0: the AE showed white)
    'LAMBERT': ("lambert", "Lambert", {"Base Color": (0.5, 0.5, 0.5, 1.0), "Roughness": 1.0,
                                       "Specular IOR Level": 0.0, "Emission Color": (0.0, 0.0, 0.0, 1.0)}),
    'BLINN': ("blinn", "Blinn", {"Roughness": 0.3}),
    'PHONG': ("phong", "Phong", {"Roughness": 0.15}),
    'SURFACE': ("surfaceShader", "Surface Shader", {"Emission Strength": 1.0}),
    # Step 105: the rest of Maya's Hypershade Create > Maya > Surface list that Blender can build (Principled stand-ins
    # plus a node or two; research/maya/screens/audit7/pairs/h01_hypershade_win1.png)
    'PHONG_E': ("phongE", "Phong E", {"Roughness": 0.25}),
    'ANISOTROPIC': ("anisotropic", "Anisotropic", {"Roughness": 0.3, "Anisotropic": 0.5}),
    'RAMP': ("rampShader", "Ramp Shader", {"Roughness": 0.5}),
    'LAYERED': ("layeredShader", "Layered Shader", {}),
    'USE_BACKGROUND': ("useBackground", "Use Background", {}),
}
# Kinds whose look comes from extra nodes around the Principled BSDF (``_build``)
BUILT = {'RAMP', 'LAYERED', 'USE_BACKGROUND'}
KIND_ITEMS = [(k, v[1], f"Maya {v[0]} (Principled BSDF)") for k, v in MATERIALS.items()]
# The Assign Favorite Material submenu (Maya's surface-shader favourites).
FAVORITES = ('LAMBERT', 'BLINN', 'PHONG', 'STANDARD_SURFACE')
# ID property naming the Maya node type of a kit-made material (AE tab label/sections, step 38).
TYPE_PROP = "allset_type"
# Maya's default material (step 100, measured with mayapy): every new shape joins initialShadingGroup, whose surface
# shader is lambert1 (lambert, color 0.5, diffuse 0.8); Delete Unused Nodes keeps it, a new Lambert is lambert2.
DEFAULT_PROP = "allset_default"
DEFAULT_NAME = "lambert1"
DEFAULT_GROUP = "initialShadingGroup"
DEFAULT_TYPES = {'MESH', 'SURFACE'}   # Maya polygon and NURBS surface shapes (curves have no shading group)


# --- data ------------------------------------------------------------------------------------

def new_material(kind):
    """A Maya-named (lambert1, blinn2, ...) Principled material of this kind."""
    from . import naming
    base, _label, values = MATERIALS[kind]
    if _maya_scene():
        default_material()   # Maya's scene always has lambert1, so a new Lambert is lambert2 (mayapy, step 100)
    n = naming.next_number(base, {m.name for m in bpy.data.materials})
    mat = bpy.data.materials.new(f"{base}{n}")
    mat[TYPE_PROP] = base
    compat.ensure_material_nodes(mat)
    node = next(nd for nd in mat.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED')
    for socket, value in values.items():
        node.inputs[socket].default_value = value
    if kind == 'SURFACE':
        node.inputs["Emission Color"].default_value = node.inputs["Base Color"].default_value
    if kind in BUILT:
        _build(mat, node, kind)
    return mat


def _build(mat, bsdf, kind):
    """Node set-ups of Maya shaders that aren't one Principled BSDF:
    rampShader = colour from a ramp over the facing ratio (Layer Weight Facing -> Color Ramp -> Base Color);
    layeredShader = two layers mixed (Mix Shader; Maya's top layer transparency = the mix factor);
    useBackground = the surface shows the background (Holdout)."""
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    if kind == 'RAMP':
        facing = nodes.new('ShaderNodeLayerWeight')
        ramp = nodes.new('ShaderNodeValToRGB')
        facing.location = (bsdf.location.x - 560, bsdf.location.y)
        ramp.location = (bsdf.location.x - 300, bsdf.location.y)
        for el in ramp.color_ramp.elements:      # Maya's default ramp: one 0.5 grey entry
            el.color = (0.5, 0.5, 0.5, 1.0)
        links.new(facing.outputs["Facing"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    elif kind == 'LAYERED':
        second = nodes.new('ShaderNodeBsdfPrincipled')
        mix = nodes.new('ShaderNodeMixShader')
        second.location = (bsdf.location.x, bsdf.location.y - 700)
        mix.location = (out.location.x - 200, out.location.y)
        out.location.x += 100
        mix.inputs["Fac"].default_value = 0.0      # top layer (input 1) fully opaque
        links.new(bsdf.outputs["BSDF"], mix.inputs[1])
        links.new(second.outputs["BSDF"], mix.inputs[2])
        links.new(mix.outputs["Shader"], out.inputs["Surface"])
    elif kind == 'USE_BACKGROUND':
        hold = nodes.new('ShaderNodeHoldout')
        hold.location = (bsdf.location.x, bsdf.location.y + 200)
        links.new(hold.outputs["Holdout"], out.inputs["Surface"])


def default_material(create=True):
    """The scene's lambert1 (marked by DEFAULT_PROP, so a rename keeps it); made on first use with a fake user so
    File > Optimize Scene Size / purges keep it like Maya's Delete Unused Nodes."""
    mat = next((m for m in bpy.data.materials if m.get(DEFAULT_PROP)), None)
    if mat is not None or not create:
        return mat
    old = bpy.data.materials.get(DEFAULT_NAME)
    if old is not None and old.get(TYPE_PROP) == "lambert" and old.library is None:
        # a kit "lambert1" from before step 100 (Assign New Material > Lambert): it becomes the default
        old[DEFAULT_PROP] = True
        old.use_fake_user = True
        return old
    mat = bpy.data.materials.new(DEFAULT_NAME)   # another material owns the name: Blender's suffix, names untouched
    mat[TYPE_PROP] = "lambert"
    mat[DEFAULT_PROP] = True
    mat.use_fake_user = True
    compat.ensure_material_nodes(mat)
    node = next(nd for nd in mat.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED')
    for socket, value in MATERIALS['LAMBERT'][2].items():
        node.inputs[socket].default_value = value
    return mat


def is_default(mat):
    return mat is not None and bool(mat.get(DEFAULT_PROP))


def shading_group_name(mat):
    """Maya's shading group of a material: initialShadingGroup for lambert1, else <material>SG."""
    return DEFAULT_GROUP if is_default(mat) else f"{mat.name}SG"


def give_default(ob):
    """A new shape without a material joins lambert1 (Maya: initialShadingGroup); True when assigned."""
    if ob is None or ob.type not in DEFAULT_TYPES or ob.data is None or ob.library is not None:
        return False
    if any(m is not None for m in ob.data.materials) or any(s.material is not None for s in ob.material_slots):
        return False
    mat = default_material()
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return True


def _maya_scene(context=None):
    from .. import preferences
    try:
        return preferences.get(context or bpy.context).maya_naming
    except KeyError:
        return True


# New objects (any path: kit create, Blender's Add menu, duplicate, separate, import) are found by comparing the
# scene's objects with the last known set; file load, undo and redo only re-baseline (their objects aren't new).
_known = {}
_busy = [False]


def _baseline(*_args):
    _known.clear()
    for scene in bpy.data.scenes:
        _known[scene.as_pointer()] = {o.as_pointer() for o in scene.objects}


@bpy.app.handlers.persistent
def _on_load(*_args):
    _baseline()
    if not bpy.data.filepath and _maya_scene():   # File > New: Maya's new scene already has lambert1
        default_material()


@bpy.app.handlers.persistent
def _on_undo(*_args):
    _baseline()


@bpy.app.handlers.persistent
def _on_depsgraph(scene, depsgraph):
    if _busy[0] or not depsgraph.id_type_updated('OBJECT'):
        return
    key = scene.as_pointer()
    now = {o.as_pointer() for o in scene.objects}
    known = _known.get(key)
    _known[key] = now
    if known is None or not (now - known) or not _maya_scene():
        return
    _busy[0] = True
    try:
        for ob in scene.objects:
            if ob.as_pointer() not in known:
                give_default(ob)
    finally:
        _busy[0] = False


HANDLERS = ((bpy.app.handlers.load_post, _on_load), (bpy.app.handlers.undo_post, _on_undo),
            (bpy.app.handlers.redo_post, _on_undo), (bpy.app.handlers.depsgraph_update_post, _on_depsgraph))


def register_handlers():
    for lst, fn in HANDLERS:
        if fn not in lst:
            lst.append(fn)
    try:
        _baseline()
    except AttributeError:   # register runs with restricted bpy.data at startup: the first update baselines
        pass


def unregister_handlers():
    for lst, fn in HANDLERS:
        if fn in lst:
            lst.remove(fn)
    _known.clear()


def targets(context, rmb=False):
    """Objects to assign to: the edited objects, the selection, else (from the RMB
    menu) the object the menu was opened on (buildShaderMenus.mel:372-374)."""
    if context.mode.startswith('EDIT'):
        return [o for o in context.objects_in_mode if o.type in SUPPORTED]
    obs = [o for o in context.selected_objects if o.type in SUPPORTED]
    if not obs and rmb:
        ob = bpy.data.objects.get(getattr(context.window_manager, "allset_mm_target", ""))
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
        if not slots:   # the rest of the mesh keeps the default: Maya's lambert1 (step 100), else no material
            ob.data.materials.append(default_material() if _maya_scene() else None)
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


class ALLSET_OT_shelf_material(bpy.types.Operator):
    """Create a material and assign it to the selected objects or faces (Maya shelf
    material buttons, Assign Favorite Material)"""
    bl_idname = "allset.shelf_material"
    bl_label = "Assign New Material"
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(items=KIND_ITEMS)
    rmb: _RMB

    @classmethod
    def poll(cls, context):
        return _poll(context)

    def execute(self, context):
        return create_and_assign(self, context, self.kind)


class ALLSET_OT_assign_new_material(bpy.types.Operator):
    """Pick a material type, create it and assign it to the selected objects or faces
    (Maya Assign New Material, Shift+T)"""
    bl_idname = "allset.assign_new_material"
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


class ALLSET_OT_assign_material(bpy.types.Operator):
    """Assign this material to the selected objects or faces (Maya Assign Existing Material)"""
    bl_idname = "allset.assign_material"
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


class ALLSET_OT_material_attributes(bpy.types.Operator):
    """Show the object's material in the Attribute Editor (Maya Material Attributes)"""
    bl_idname = "allset.material_attributes"
    bl_label = "Material Attributes"

    rmb: _RMB

    @staticmethod
    def _object(context, rmb):
        if rmb:
            ob = bpy.data.objects.get(getattr(context.window_manager, "allset_mm_target", ""))
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
        attribute_editor.show_dock(context, 'ATTRIBUTE_EDITOR')
        attribute_editor.set_tab(context, f"MAT:{i}")
        for area in context.screen.areas if context.screen else ():
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}


# --- menus -----------------------------------------------------------------------------------

class ALLSET_MT_assign_favorite_material(bpy.types.Menu):
    """Create a material of a favourite type and assign it (Maya Assign Favorite Material)"""
    bl_idname = "ALLSET_MT_assign_favorite_material"
    bl_label = "Assign Favorite Material"
    rmb = False

    def draw(self, context):
        for kind in FAVORITES:
            op = self.layout.operator("allset.shelf_material", text=MATERIALS[kind][1], icon='MATERIAL')
            op.kind = kind
            op.rmb = self.rmb


class ALLSET_MT_assign_existing_material(bpy.types.Menu):
    """Assign a material of the scene (Maya Assign Existing Material)"""
    bl_idname = "ALLSET_MT_assign_existing_material"
    bl_label = "Assign Existing Material"
    rmb = False

    def draw(self, context):
        mats = sorted((m for m in bpy.data.materials if not m.is_grease_pencil), key=lambda m: m.name.lower())
        if not mats:
            self.layout.label(text="No materials in the scene")
            return
        for mat in mats:
            op = self.layout.operator("allset.assign_material", text=mat.name, icon='MATERIAL')
            op.material = mat.name
            op.rmb = self.rmb


class ALLSET_MT_assign_existing_material_rmb(ALLSET_MT_assign_existing_material):
    """Assign a material of the scene to the selection or the object under the RMB menu"""
    bl_idname = "ALLSET_MT_assign_existing_material_rmb"
    rmb = True


classes = (ALLSET_OT_shelf_material, ALLSET_OT_assign_new_material, ALLSET_OT_assign_material,
           ALLSET_OT_material_attributes, ALLSET_MT_assign_favorite_material,
           ALLSET_MT_assign_existing_material, ALLSET_MT_assign_existing_material_rmb)
