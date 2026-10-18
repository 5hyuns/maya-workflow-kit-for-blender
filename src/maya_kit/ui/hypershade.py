# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Hypershade = a Shader Editor window with a "Hypershade" sidebar tab (docs/steps/step_67.md 「계획」 1,
docs/steps/step_105.md 「계획」 1).

Maya's Hypershade (research/maya/workflows/render.md:20-29; audit-7 pair h01_hypershade_win1; menus and Browser tabs
captured in research/maya/screens/editors105/_editors105.json) is a floating window: a menu bar (File / Edit / View /
Create / Tabs / Graph / Window / Options / Help), the Browser (swatch tabs Materials / Textures / Utilities /
Rendering / Lights / Cameras / Shading Groups ...), Create (node types), the node graph and the Property Editor.
Blender's Shader Editor is the graph; the kit adds:

- the Maya menu bar in every Shader Editor header (``NODE_MT_editor_menus.draw_collapsible``, step 37 pattern;
  Blender's menus in a 「Blender」 menu, the slot / New buttons stay); items in ``editor_menu_map`` "Hypershade/...";
- Browser: swatch tabs as a preview grid (View menu: swatch size and sort order); a click makes a material the
  Hypershade's current one (the active object's slot when it has it, else this Shader Editor is pinned to it),
  selects a light / camera, or shows a texture / utility node in its material's graph;
- Create: Maya's surface shaders Blender can build (Maya order), created unassigned like Maya's Create bar;
- Assign Material To Selection (Maya's swatch RMB item, ``maya_kit.assign_material``);
- Property Editor: the Attribute Editor's material sections with their map buttons.

``maya_kit.hypershade`` opens the window: Windows > Rendering Editors > Hypershade, the Status Line icon and the
hotbox's Windows menu all run it.
"""

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty

from ..operators import material as material_ops
from ..operators import menu_extras
from . import ae_layout

CATEGORY = "Hypershade"
# Maya Hypershade Create > Maya > Surface, alphabetical like Maya (h01_hypershade_win1): the ones Blender can build
CREATE = ('ANISOTROPIC', 'BLINN', 'LAMBERT', 'LAYERED', 'PHONG', 'PHONG_E', 'RAMP', 'STANDARD_SURFACE', 'SURFACE',
          'USE_BACKGROUND')
COLUMNS = 3

# Browser swatch tabs (captured tab bar; Bake Sets / Projects / Asset Nodes have no Blender counterpart)
TABS = (("MATERIALS", "Materials", "Materials of the scene"),
        ("TEXTURES", "Textures", "Image and texture nodes in the materials"),
        ("UTILITIES", "Utilities", "Other nodes in the materials (Maya utility nodes)"),
        ("RENDERING", "Rendering", "Worlds (Blender's environment / render node)"),
        ("LIGHTS", "Lights", "Light objects"),
        ("CAMERAS", "Cameras", "Camera objects"),
        ("SHADING_GROUPS", "Shading Groups", "Maya shading groups: one per material"))
# View > As Icons / As List / As Small ... Extra Large Swatches (captured View menu); icon scale per size
SWATCHES = (("ICONS", "As Icons", "", 2.0), ("LIST", "As List", "", 0.0), ("SMALL", "As Small Swatches", "", 2.0),
            ("MEDIUM", "As Medium Swatches", "", 3.0), ("LARGE", "As Large Swatches", "", 4.5),
            ("XLARGE", "As Extra Large Swatches", "", 6.0))
SORTS = (("NAME", "By Name", ""), ("TYPE", "By Type", ""), ("TIME", "By Time", ""))

TEXTURE_NODES = {'TEX_IMAGE', 'TEX_CHECKER', 'TEX_NOISE', 'TEX_WAVE', 'TEX_VORONOI', 'TEX_BRICK', 'TEX_GRADIENT',
                 'TEX_MAGIC', 'TEX_ENVIRONMENT', 'TEX_SKY', 'TEX_WHITE_NOISE', 'TEX_GABOR'}
SHADER_NODES = {'OUTPUT_MATERIAL', 'BSDF_PRINCIPLED', 'MIX_SHADER', 'ADD_SHADER', 'HOLDOUT', 'EMISSION',
                'BSDF_DIFFUSE', 'BSDF_GLOSSY', 'BSDF_TRANSPARENT', 'BSDF_TRANSLUCENT', 'BSDF_REFRACTION', 'BSDF_GLASS',
                'SUBSURFACE_SCATTERING', 'BSDF_TOON', 'BSDF_SHEEN', 'BSDF_HAIR', 'BSDF_HAIR_PRINCIPLED',
                'VOLUME_ABSORPTION', 'VOLUME_SCATTER', 'PRINCIPLED_VOLUME', 'BSDF_METALLIC', 'FRAME', 'REROUTE',
                'GROUP_INPUT', 'GROUP_OUTPUT'}

# Hypershade Create menu node types -> Blender shader nodes (data in editor_menu_map, bpy-free)
from .editor_menu_map import HS_NODES as NODES  # noqa: E402


def materials():
    return sorted((m for m in bpy.data.materials if not m.is_grease_pencil), key=lambda m: m.name.lower())


def current(context):
    """The Hypershade's current material: the picked one, else the active object's active material."""
    mat = bpy.data.materials.get(context.window_manager.maya_kit_hs_material)
    if mat is None and context.active_object is not None:
        mat = context.active_object.active_material
    return mat


def show(context, mat, space=None):
    """Make ``mat`` current and show it in the Shader Editor ``space``: the active object's slot when it has
    the material (the editor follows the object, unpinned), else pin the editor to it."""
    context.window_manager.maya_kit_hs_material = mat.name
    ob = context.active_object
    index = next((i for i, s in enumerate(ob.material_slots) if s.material == mat), None) if ob else None
    if space is None or space.type != 'NODE_EDITOR':
        if index is not None:
            ob.active_material_index = index
        return
    if index is not None:
        ob.active_material_index = index
        space.pin = False
    elif mat.node_tree is not None:
        space.pin = True
        space.node_tree = mat.node_tree


def _hypershade_area(context):
    return max(context.window.screen.areas, key=lambda a: a.width * a.height, default=None)


# --- Browser items --------------------------------------------------------------------------------------------

def _node_items(want_textures):
    out = []
    for mat in materials():
        if not mat.use_nodes or mat.node_tree is None:
            continue
        for node in mat.node_tree.nodes:
            if node.type in SHADER_NODES:
                continue
            if (node.type in TEXTURE_NODES) == want_textures:
                out.append((f"{mat.name}::{node.name}", node.label or node.name, mat, node))
    return out


def browser_items(context, tab):
    """[(key, label, icon or ID with a preview, type name)] of a Browser tab, sorted by the View menu's order."""
    scene = context.scene
    if tab == 'MATERIALS':
        items = [(m.name, m.name, m, m.get(material_ops.TYPE_PROP, "material")) for m in materials()]
    elif tab in {'TEXTURES', 'UTILITIES'}:
        items = []
        for key, label, mat, node in _node_items(tab == 'TEXTURES'):
            img = getattr(node, "image", None)
            items.append((key, label, img if img is not None else
                          ('TEXTURE' if tab == 'TEXTURES' else 'NODE'), node.bl_idname))
    elif tab == 'RENDERING':
        items = [(w.name, w.name, w, "world") for w in bpy.data.worlds]
    elif tab in {'LIGHTS', 'CAMERAS'}:
        kind = 'LIGHT' if tab == 'LIGHTS' else 'CAMERA'
        items = [(o.name, o.name, ('LIGHT_' + o.data.type if kind == 'LIGHT' else 'CAMERA_DATA'),
                  o.data.type if kind == 'LIGHT' else "camera")
                 for o in scene.objects if o.type == kind]
        items = [(k, lab, ic if ic in _ICONS else 'LIGHT', t) for k, lab, ic, t in items]
    else:   # SHADING_GROUPS
        items = [(m.name, material_ops.shading_group_name(m), 'NODETREE', "shadingEngine") for m in materials()]
    wm = context.window_manager
    order = wm.maya_kit_hs_sort
    if order == 'TYPE':
        items.sort(key=lambda it: (str(it[3]).lower(), it[1].lower()))
    elif order == 'TIME':
        items.sort(key=lambda it: _uid(context, tab, it[0]))
    else:
        items.sort(key=lambda it: it[1].lower())
    if wm.maya_kit_hs_reverse:
        items.reverse()
    return items


_ICONS = {'LIGHT_POINT', 'LIGHT_SUN', 'LIGHT_SPOT', 'LIGHT_AREA', 'CAMERA_DATA'}


def icon_value(name):
    """The icon id of a named Blender icon (template_icon takes ids only)."""
    return bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items[name].value


def _uid(context, tab, key):
    """Creation order (session uid grows with every new data-block)."""
    if tab == 'MATERIALS' or tab == 'SHADING_GROUPS':
        data = bpy.data.materials.get(key)
    elif tab == 'RENDERING':
        data = bpy.data.worlds.get(key)
    elif tab in {'LIGHTS', 'CAMERAS'}:
        data = bpy.data.objects.get(key)
    else:
        data = bpy.data.materials.get(key.split("::", 1)[0])
    return getattr(data, "session_uid", 0)


class MAYAKIT_OT_hypershade(bpy.types.Operator):
    """Hypershade: a Shader Editor window with the material browser, Create and Property Editor (sidebar tab)"""
    bl_idname = "maya_kit.hypershade"
    bl_label = "Hypershade"

    def execute(self, context):
        if context.window is None:
            return {'CANCELLED'}
        area = _hypershade_area(context)
        if area is None:
            return {'CANCELLED'}
        window = menu_extras.open_window(context, area)
        if window is None:
            self.report({'ERROR'}, "Could not open a new window")
            return {'CANCELLED'}
        target = window.screen.areas[0]
        target.ui_type = 'ShaderNodeTree'
        mat = current(context)
        if mat is not None:
            show(context, mat, target.spaces.active)
        menu_extras.sidebar_tab_later(window, CATEGORY)
        return {'FINISHED'}


class MAYAKIT_OT_hs_pick(bpy.types.Operator):
    """Show this material in the graph and the Property Editor (Maya Hypershade swatch click)"""
    bl_idname = "maya_kit.hs_pick"
    bl_label = "Pick Material"

    material: StringProperty(name="Material", options={'SKIP_SAVE'})

    def execute(self, context):
        mat = bpy.data.materials.get(self.material)
        if mat is None:
            return {'CANCELLED'}
        show(context, mat, context.space_data)
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_hs_item(bpy.types.Operator):
    """Maya Hypershade Browser swatch: a light / camera = select it; a texture / utility = show it in its graph;
    a world = the scene's environment"""
    bl_idname = "maya_kit.hs_item"
    bl_label = "Browser Item"
    bl_options = {'REGISTER', 'UNDO'}

    tab: EnumProperty(items=[t for t in TABS], name="Tab", options={'SKIP_SAVE'})
    key: StringProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        if self.tab in {'LIGHTS', 'CAMERAS'}:
            ob = context.scene.objects.get(self.key)
            if ob is None:
                return {'CANCELLED'}
            for o in context.selected_objects:
                o.select_set(False)
            ob.select_set(True)
            context.view_layer.objects.active = ob
        elif self.tab == 'RENDERING':
            world = bpy.data.worlds.get(self.key)
            if world is None:
                return {'CANCELLED'}
            context.scene.world = world
        elif self.tab in {'TEXTURES', 'UTILITIES'}:
            mname, _sep, nname = self.key.partition("::")
            mat = bpy.data.materials.get(mname)
            node = mat.node_tree.nodes.get(nname) if mat is not None and mat.node_tree else None
            if node is None:
                return {'CANCELLED'}
            show(context, mat, context.space_data)
            for n in mat.node_tree.nodes:
                n.select = n == node
            mat.node_tree.nodes.active = node
        else:
            return bpy.ops.maya_kit.hs_pick(material=self.key)
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_hs_create(bpy.types.Operator):
    """Create a material of this type without assigning it (Maya Hypershade Create)"""
    bl_idname = "maya_kit.hs_create"
    bl_label = "Create Material"
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(items=material_ops.KIND_ITEMS, name="Material")

    def execute(self, context):
        mat = material_ops.new_material(self.kind)
        mat.use_fake_user = True    # no user yet: Blender would drop it on save, Maya keeps it
        show(context, mat, context.space_data)
        context.window_manager.maya_kit_hs_tab = 'MATERIALS'
        return {'FINISHED'}


class MAYAKIT_OT_hs_node(bpy.types.Operator):
    """Add this Maya node type to the current material's graph (Maya Hypershade Create: a texture / utility node
    is made on its own; the Blender node is left unconnected)"""
    bl_idname = "maya_kit.hs_node"
    bl_label = "Create Node"
    bl_options = {'REGISTER', 'UNDO'}

    node_type: StringProperty(name="Node", options={'SKIP_SAVE'})
    label: StringProperty(name="Maya Name", options={'SKIP_SAVE'})

    def execute(self, context):
        mat = current(context)
        if mat is None:
            mat = material_ops.new_material('LAMBERT')
            mat.use_fake_user = True
        mat.use_nodes = True
        tree = mat.node_tree
        try:
            node = tree.nodes.new(self.node_type)
        except RuntimeError:
            self.report({'ERROR'}, f"Blender has no node {self.node_type}")
            return {'CANCELLED'}
        if self.label:
            node.label = self.label
        left = min((n.location.x for n in tree.nodes if n != node), default=0.0)
        node.location = (left - 300.0, 300.0)      # left of the network, like a new upstream node
        for n in tree.nodes:
            n.select = n == node
        tree.nodes.active = node
        show(context, mat, context.space_data)
        _redraw(context)
        return {'FINISHED'}


class MAYAKIT_OT_hs_edit(bpy.types.Operator):
    """Maya Hypershade Edit menu commands"""
    bl_idname = "maya_kit.hs_edit"
    bl_label = "Hypershade Edit"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(items=(
        ("DELETE", "Delete", "Delete the current material (lambert1 stays, like Maya's)"),
        ("DELETE_UNUSED", "Delete Unused Nodes", "Delete the materials no object uses (lambert1 stays)"),
        ("DELETE_MATERIALS", "Delete All Materials", "Delete every material but lambert1"),
        ("SELECT_OBJECTS", "Select Objects with Materials", "Select the objects that use the current material"),
        ("FROM_OBJECT", "Select Materials from Objects", "The active object's material becomes current"),
        ("DUPLICATE", "Duplicate", "Copy the current material (and its network)"),
    ), name="Action", options={'SKIP_SAVE'})

    def execute(self, context):
        act = self.action
        cur = current(context)
        if act in {"DELETE", "SELECT_OBJECTS", "DUPLICATE"} and cur is None:
            self.report({'WARNING'}, "No material selected in the Hypershade")
            return {'CANCELLED'}
        if act == "DELETE":
            if material_ops.is_default(cur):
                self.report({'WARNING'}, f"{cur.name} can't be deleted (Maya's default material)")
                return {'CANCELLED'}
            bpy.data.materials.remove(cur)
            context.window_manager.maya_kit_hs_material = ""
        elif act in {"DELETE_UNUSED", "DELETE_MATERIALS"}:
            n = 0
            for m in list(materials()):
                used = m.users - (1 if m.use_fake_user else 0) > 0
                if material_ops.is_default(m) or (act == "DELETE_UNUSED" and used):
                    continue
                bpy.data.materials.remove(m)
                n += 1
            self.report({'INFO'}, f"Deleted {n} material{'s' if n != 1 else ''}")
        elif act == "SELECT_OBJECTS":
            for o in context.selected_objects:
                o.select_set(False)
            hits = [o for o in context.scene.objects if any(s.material == cur for s in o.material_slots)]
            for o in hits:
                try:
                    o.select_set(True)
                except RuntimeError:
                    pass
            if hits:
                context.view_layer.objects.active = hits[0]
        elif act == "FROM_OBJECT":
            ob = context.active_object
            if ob is None or ob.active_material is None:
                self.report({'WARNING'}, "Select an object with a material")
                return {'CANCELLED'}
            show(context, ob.active_material, context.space_data)
        elif act == "DUPLICATE":
            new = cur.copy()
            new.use_fake_user = True
            show(context, new, context.space_data)
        _redraw(context)
        return {'FINISHED'}


def _redraw(context):
    for area in context.screen.areas if context.screen else ():
        area.tag_redraw()


# --- panels ---------------------------------------------------------------------------------------------------

def draw_browser(layout, context):
    wm = context.window_manager
    layout.row(align=True).prop(wm, "maya_kit_hs_tab", expand=True)
    tab = wm.maya_kit_hs_tab
    items = browser_items(context, tab)
    if not items:
        layout.label(text=f"No {dict((t[0], t[1]) for t in TABS)[tab].lower()} in the scene")
        return
    cur = current(context)
    size = next(s for s in SWATCHES if s[0] == wm.maya_kit_hs_swatch)
    region = context.region
    s = context.preferences.system.ui_scale or 1.0
    if size[3] == 0.0:       # As List
        col = layout.column(align=True)
        for key, label, icon, _t in items:
            _item_button(col, tab, key, label, icon, cur, list_row=True)
        return
    cell = size[3] * 20 * s + 12
    width = region.width if region is not None else 300
    columns = max(1, min(COLUMNS * 3, int(width // cell))) if region is not None else COLUMNS
    grid = layout.grid_flow(row_major=True, columns=columns, even_columns=True, align=False)
    for key, label, icon, _t in items:
        col = grid.column(align=True)
        value = icon_value(icon) if isinstance(icon, str) else layout.icon(icon)
        col.template_icon(icon_value=value, scale=size[3])
        _item_button(col, tab, key, label, icon, cur)


def _item_button(layout, tab, key, label, icon, cur, list_row=False):
    picked = (tab in {'MATERIALS', 'SHADING_GROUPS'} and cur is not None and key == cur.name)
    if tab == 'MATERIALS':
        kw = {"icon_value": layout.icon(icon)} if list_row else {}
        op = layout.operator("maya_kit.hs_pick", text=label, depress=picked, **kw)
        op.material = key
        return
    kw = {}
    if list_row:
        kw = {"icon": icon} if isinstance(icon, str) else {"icon_value": layout.icon(icon)}
    op = layout.operator("maya_kit.hs_item", text=label, depress=picked, **kw)
    op.tab, op.key = tab, key


def draw_create(layout, context):
    col = layout.column(align=True)
    for kind in CREATE:
        col.operator("maya_kit.hs_create", text=material_ops.MATERIALS[kind][1], icon='MATERIAL').kind = kind


def draw_property_editor(layout, context):
    from . import attribute_editor
    mat = current(context)
    if mat is None:
        layout.label(text="Pick a material")
        return
    head = layout.row(align=True)
    head.label(text=f"{attribute_editor.material_type(mat)}:")
    head.prop(mat, "name", text="")
    name = attribute_editor.material_type(mat)
    sections = ae_layout.BY_KIND[name][0]
    attribute_editor.draw_sections(layout, context, None, mat, sections, f"hs_{name}")


class _Panel:
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = CATEGORY

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and getattr(space, "tree_type", "") == 'ShaderNodeTree'


class MAYAKIT_PT_hs_browser(_Panel, bpy.types.Panel):
    bl_label = "Browser"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        draw_browser(layout, context)
        cur = current(context)
        row = layout.row()
        row.enabled = cur is not None
        op = row.operator("maya_kit.assign_material", text="Assign Material To Selection", icon='MATERIAL')
        op.material = cur.name if cur is not None else ""


class MAYAKIT_PT_hs_create(_Panel, bpy.types.Panel):
    bl_label = "Create"
    bl_order = 1

    def draw(self, context):
        draw_create(self.layout, context)


class MAYAKIT_PT_hs_property_editor(_Panel, bpy.types.Panel):
    bl_label = "Property Editor"
    bl_order = 2

    def draw(self, context):
        draw_property_editor(self.layout, context)


# --- Maya menu bar in the Shader Editor header ---------------------------------------------------------------

def draw_collapsible(cls, context, layout):
    """``NODE_MT_editor_menus.draw_collapsible`` while the kit is on: Maya's Hypershade menus in a Shader Editor."""
    from . import editor_chrome
    space = context.space_data
    if editor_chrome.enabled(context) and getattr(space, "tree_type", "") == 'ShaderNodeTree':
        return editor_chrome.draw_menus(layout, context, "Hypershade")
    return bpy.types.Menu.draw_collapsible.__func__(cls, context, layout)


def patch_header():
    bpy.types.NODE_MT_editor_menus.draw_collapsible = classmethod(draw_collapsible)


def unpatch_header():
    cls = bpy.types.NODE_MT_editor_menus
    if "draw_collapsible" in cls.__dict__:
        del cls.draw_collapsible


classes = (MAYAKIT_OT_hypershade, MAYAKIT_OT_hs_pick, MAYAKIT_OT_hs_item, MAYAKIT_OT_hs_create, MAYAKIT_OT_hs_node,
           MAYAKIT_OT_hs_edit, MAYAKIT_PT_hs_browser, MAYAKIT_PT_hs_create, MAYAKIT_PT_hs_property_editor)


def register():
    wm = bpy.types.WindowManager
    wm.maya_kit_hs_material = StringProperty(name="Hypershade Material", options={'SKIP_SAVE'})
    wm.maya_kit_hs_tab = EnumProperty(name="Browser Tab", items=TABS, options={'SKIP_SAVE'})
    wm.maya_kit_hs_swatch = EnumProperty(name="Swatch Size", items=[s[:3] for s in SWATCHES], default='MEDIUM',
                                         options={'SKIP_SAVE'})
    wm.maya_kit_hs_sort = EnumProperty(name="Sort", items=SORTS, options={'SKIP_SAVE'})
    wm.maya_kit_hs_reverse = BoolProperty(name="Reverse Order", options={'SKIP_SAVE'})
    for cls in classes:
        bpy.utils.register_class(cls)
    patch_header()


def unregister():
    unpatch_header()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    for name in ("maya_kit_hs_material", "maya_kit_hs_tab", "maya_kit_hs_swatch", "maya_kit_hs_sort",
                 "maya_kit_hs_reverse"):
        delattr(bpy.types.WindowManager, name)
