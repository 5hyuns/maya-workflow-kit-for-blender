# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Layer Editor (Display Layers) wrapped on collections.

; design  「계획」.
A display layer is a child collection of a "Display Layers" collection that
is excluded from every view layer, so layers are membership lists that do
not change the scene hierarchy or visibility by themselves. The layer state
is applied to its member objects:
  V (visible)  -> hide_viewport
  T (template) -> unselectable, wireframe; R (reference) -> unselectable
  P (playback) -> off: members hidden while animation plays
An object belongs to at most one display layer, as in Maya.
"""

import re

import bpy
from bpy.app.handlers import persistent
from bpy.props import BoolProperty, EnumProperty, IntProperty, PointerProperty

from . import chrome

ROOT_NAME = "Display Layers"
TYPES = (("NORMAL", "Normal", "Selectable, normal display"),
         ("TEMPLATE", "Template", "Unselectable, wireframe (Maya T)"),
         ("REFERENCE", "Reference", "Unselectable (Maya R)"))
TYPE_LETTER = {"NORMAL": " ", "TEMPLATE": "T", "REFERENCE": "R"}


def _update(self, context):
    coll = self.id_data
    if self.is_layer:
        apply_layer(coll)


class ALLSET_PG_layer(bpy.types.PropertyGroup):
    is_layer: BoolProperty(options={'HIDDEN'})
    visible: BoolProperty(name="Visible", default=True, update=_update,
                          description="Show the layer's objects (Maya V)")
    playback: BoolProperty(name="Playback", default=True, update=_update,
                           description="Show the layer's objects during playback (Maya P)")
    display_type: EnumProperty(name="Display Type", items=TYPES, default="NORMAL", update=_update)


# --- data helpers -------------------------------------------------------------------------------

def root(scene, create=False):
    coll = scene.collection.children.get(ROOT_NAME)
    if coll is None and create:
        coll = bpy.data.collections.new(ROOT_NAME)
        scene.collection.children.link(coll)
        for vl in scene.view_layers:
            lc = vl.layer_collection.children.get(coll.name)
            if lc is not None:
                lc.exclude = True
    return coll


def layers(scene):
    r = root(scene)
    return [c for c in r.children if c.allset_layer.is_layer] if r else []


def layer_of(ob, scene):
    for coll in layers(scene):
        if ob.name in coll.objects:
            return coll
    return None


def next_layer_name():
    used = {int(m.group(1)) for c in bpy.data.collections if (m := re.match(r"^layer(\d+)$", c.name))}
    n = 1
    while n in used:
        n += 1
    return f"layer{n}"


def apply_object(ob, layer):
    """Apply a layer's state to one member (None = back to normal)."""
    if layer is None:
        ob.hide_viewport = False
        ob.hide_select = False
        ob.display_type = 'TEXTURED'
        return
    st = layer.allset_layer
    ob.hide_viewport = not st.visible
    ob.hide_select = st.display_type != "NORMAL"
    ob.display_type = 'WIRE' if st.display_type == "TEMPLATE" else 'TEXTURED'


def apply_layer(coll):
    for ob in coll.objects:
        apply_object(ob, coll)


def new_layer(scene, objects=()):
    coll = bpy.data.collections.new(next_layer_name())
    root(scene, create=True).children.link(coll)
    coll.allset_layer.is_layer = True
    add_objects(scene, coll, objects)
    return coll


def add_objects(scene, coll, objects):
    for ob in objects:
        old = layer_of(ob, scene)
        if old is not None and old != coll:
            old.objects.unlink(ob)
        if ob.name not in coll.objects:
            coll.objects.link(ob)
        apply_object(ob, coll)


def remove_objects(scene, coll, objects):
    for ob in objects:
        if ob.name in coll.objects:
            coll.objects.unlink(ob)
            apply_object(ob, None)


def delete_layer(scene, coll):
    remove_objects(scene, coll, list(coll.objects))
    bpy.data.collections.remove(coll)


def active_layer(context):
    ls = layers(context.scene)
    i = context.scene.allset_layer_index
    return ls[i] if 0 <= i < len(ls) else None


# --- playback (P) -------------------------------------------------------------------------------

_hidden_for_playback = []


@persistent
def on_playback_pre(scene, *_args):
    _hidden_for_playback.clear()
    for coll in layers(scene):
        st = coll.allset_layer
        if st.visible and not st.playback:
            for ob in coll.objects:
                if not ob.hide_viewport:
                    ob.hide_viewport = True
                    _hidden_for_playback.append(ob.name)


@persistent
def on_playback_post(scene, *_args):
    for name in _hidden_for_playback:
        ob = bpy.data.objects.get(name)
        if ob is not None:
            ob.hide_viewport = False
    _hidden_for_playback.clear()


# --- operators -----------------------------------------------------------------------------------

class _LayerOp:
    bl_options = {'REGISTER', 'UNDO'}


class ALLSET_OT_layer_new(_LayerOp, bpy.types.Operator):
    """Create a display layer (optionally with the selected objects)"""
    bl_idname = "allset.layer_new"
    bl_label = "New Layer"

    selected: BoolProperty(name="Assign Selected", default=False)

    def execute(self, context):
        objs = list(context.selected_objects) if self.selected else []
        coll = new_layer(context.scene, objs)
        context.scene.allset_layer_index = layers(context.scene).index(coll)
        return {'FINISHED'}


class ALLSET_OT_layer_assign(_LayerOp, bpy.types.Operator):
    """Add (or remove) the selected objects to the active display layer"""
    bl_idname = "allset.layer_assign"
    bl_label = "Add Selected Objects"

    remove: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return active_layer(context) is not None

    def execute(self, context):
        coll = active_layer(context)
        fn = remove_objects if self.remove else add_objects
        fn(context.scene, coll, list(context.selected_objects))
        return {'FINISHED'}


class ALLSET_OT_layer_select(_LayerOp, bpy.types.Operator):
    """Select the objects of the active display layer"""
    bl_idname = "allset.layer_select"
    bl_label = "Select Objects"

    @classmethod
    def poll(cls, context):
        return active_layer(context) is not None

    def execute(self, context):
        coll = active_layer(context)
        for ob in context.view_layer.objects:
            ob.select_set(ob.name in coll.objects and not ob.hide_select)
        return {'FINISHED'}


class ALLSET_OT_layer_delete(_LayerOp, bpy.types.Operator):
    """Delete the active display layer (its objects stay, back to normal display)"""
    bl_idname = "allset.layer_delete"
    bl_label = "Delete Layer"

    @classmethod
    def poll(cls, context):
        return active_layer(context) is not None

    def execute(self, context):
        delete_layer(context.scene, active_layer(context))
        context.scene.allset_layer_index = max(0, context.scene.allset_layer_index - 1)
        return {'FINISHED'}


class ALLSET_OT_layer_cycle_type(_LayerOp, bpy.types.Operator):
    """Cycle display type: normal -> template (T) -> reference (R)"""
    bl_idname = "allset.layer_cycle_type"
    bl_label = "Cycle Layer Type"

    layer: bpy.props.StringProperty()

    def execute(self, context):
        coll = bpy.data.collections.get(self.layer)
        if coll is None:
            return {'CANCELLED'}
        order = [t[0] for t in TYPES]
        st = coll.allset_layer
        st.display_type = order[(order.index(st.display_type) + 1) % len(order)]
        return {'FINISHED'}


# --- UI ------------------------------------------------------------------------------------------

class ALLSET_UL_layers(bpy.types.UIList):
    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flags = [self.bitflag_filter_item if c.allset_layer.is_layer else 0 for c in items]
        return flags, []

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        st = item.allset_layer
        row = layout.row(align=True)
        row.prop(st, "visible", text="V", toggle=True)
        row.prop(st, "playback", text="P", toggle=True)
        row.operator("allset.layer_cycle_type", text=TYPE_LETTER[st.display_type]).layer = item.name
        row.prop(item, "color_tag", text="", icon_only=True)
        row.prop(item, "name", text="", emboss=False)
        row.label(text=str(len(item.objects)))


class ALLSET_MT_le_layers(bpy.types.Menu):
    """Maya Layer Editor Layers menu (layerEditorBuildDisplayLayerMenu, )"""
    bl_label = "Layers"

    def draw(self, context):
        lay = self.layout
        lay.operator("allset.layer_new", text="Create Empty Layer").selected = False
        lay.operator("allset.layer_new", text="Create Layer from Selected").selected = True
        lay.separator()
        lay.operator("allset.layer_assign", text="Add Selected Objects").remove = False
        lay.operator("allset.layer_assign", text="Remove Selected Objects").remove = True
        lay.operator("allset.layer_select", text="Select Objects")
        lay.separator()
        lay.operator("allset.layer_delete", text="Delete Layer")


class ALLSET_MT_le_options(bpy.types.Menu):
    """Maya Layer Editor Options menu (layerEditorBuildDisplayOptionMenu)"""
    bl_label = "Options"

    def draw(self, context):
        for label in ("Make New Layers Current", "Add New Objects to Current Layer", "Auto Overwrite",
                      "Show Namespace"):
            chrome.grey(self.layout, label)


class ALLSET_MT_le_help(bpy.types.Menu):
    bl_label = "Help"

    def draw(self, context):
        self.layout.operator("wm.url_open", text="Help on Display Layers (Blender collections)").url = HELP_URL


HELP_URL = "https://docs.blender.org/manual/en/4.5/scene_layout/collections/collections.html"
# Maya Layer Editor: tabs Display / Anim (Maya-5135), menu bar Layers / Options / Help
# (:5082-5098), toolbar on the right (:5100-5111); 
TABS = (('DISPLAY', "Display", "Display layers"), ('ANIM', "Anim", "Animation layers"))
MENU_BAR = (("Layers", "ALLSET_MT_le_layers"), ("Options", "ALLSET_MT_le_options"), ("Help", "ALLSET_MT_le_help"))
ANIM_TEXT = ("Blender has no animation layers:", "layer actions in the Nonlinear Animation editor.")


class ALLSET_PT_layer_editor(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Channel Box / Layer Editor"   # = channel_box.CATEGORY (the dock's first tab, step 99)
    bl_label = "Layer Editor"
    bl_order = 1
    bl_options = {'HIDE_HEADER'}   # Maya: tabs + menu bar, no collapsible panel title (step 50)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        wm = context.window_manager
        sdk = getattr(wm, "allset_sdk", None)
        if sdk is not None and sdk.open:
            from . import set_driven_key   # the Set Driven Key window takes the Layer Editor's place (step 62)
            set_driven_key.draw(layout, context)
            return
        layout.separator(type='LINE')   # Maya's splitter between Channel Box and Layer Editor
        layout.row(align=True).prop(wm, "allset_le_tab", expand=True)
        chrome.menu_bar(layout, MENU_BAR)
        if wm.allset_le_tab == 'ANIM':
            chrome.wrapped(layout, ANIM_TEXT, alignment='LEFT')
            layout.operator("allset.open_editor", text="Nonlinear Animation").ui_type = 'NLA_EDITOR'
            return
        row = layout.row(align=True)
        row.alignment = 'RIGHT'
        row.operator("allset.layer_new", text="", icon='ADD').selected = False
        row.operator("allset.layer_new", text="", icon='COLLECTION_NEW').selected = True
        row.separator()
        row.operator("allset.layer_assign", text="", icon='ZOOM_IN').remove = False
        row.operator("allset.layer_assign", text="", icon='ZOOM_OUT').remove = True
        row.operator("allset.layer_select", text="", icon='RESTRICT_SELECT_OFF')
        row.operator("allset.layer_delete", text="", icon='TRASH')
        # Maya shows the (empty) layer list area even with no layers (11b_channel_box_crop.png): an empty
        # list over the scene collection's children (the filter keeps display layers only).
        r = root(scene)
        owner = r if r is not None else scene.collection
        layout.template_list("ALLSET_UL_layers", "", owner, "children", scene, "allset_layer_index",
                             rows=list_rows(context))


def list_rows(context):
    """Layer list rows that fill the dock to the bottom (Maya's Layer Editor pane is the dock's lower part,
    channel_box.CB_SHARE; step 99)."""
    from .channel_box import CB_SHARE
    region = context.region
    if region is None or region.type != 'UI':
        return 8
    u = round(18.0 * context.preferences.system.ui_scale) + 2 * context.preferences.system.pixel_size
    return max(3, int((1.0 - CB_SHARE) * region.height / max(u, 1)) - 5)


classes = (ALLSET_PG_layer, ALLSET_OT_layer_new, ALLSET_OT_layer_assign, ALLSET_OT_layer_select,
           ALLSET_OT_layer_delete, ALLSET_OT_layer_cycle_type, ALLSET_UL_layers,
           ALLSET_MT_le_layers, ALLSET_MT_le_options, ALLSET_MT_le_help, ALLSET_PT_layer_editor)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Collection.allset_layer = PointerProperty(type=ALLSET_PG_layer)
    bpy.types.Scene.allset_layer_index = IntProperty(options={'HIDDEN'})
    bpy.types.WindowManager.allset_le_tab = EnumProperty(name="Layer Editor Tab", items=TABS,
                                                           options={'SKIP_SAVE'})
    bpy.app.handlers.animation_playback_pre.append(on_playback_pre)
    bpy.app.handlers.animation_playback_post.append(on_playback_post)


def unregister():
    bpy.app.handlers.animation_playback_post.remove(on_playback_post)
    bpy.app.handlers.animation_playback_pre.remove(on_playback_pre)
    del bpy.types.WindowManager.allset_le_tab
    del bpy.types.Scene.allset_layer_index
    del bpy.types.Collection.allset_layer
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
