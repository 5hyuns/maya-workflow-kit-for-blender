# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Outliner as a UIList in the 3D View sidebar (category "Outliner").

 (``Maya``: showShapes 0,
showDagOnly 1, autoExpand 0),  (transform / shape),
 #3 (Blender's Outliner tree is C; a UIList is the
way to a custom tree, without drag and drop). Design:  「계획」 2.

Rows (``WindowManager.maya_kit_outliner_rows``) are rebuilt outside drawing
(ID data can't be written while drawing): from the depsgraph / load handlers
and from this module's operators, skipped when nothing they show changed.
"""

import bpy
from bpy.app.handlers import persistent
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, IntProperty, StringProperty

CATEGORY = "Outliner"
_state = {"sig": None, "busy": False}


def _target(row):
    return bpy.data.objects.get(row.object)


def _get_label(self):
    ob = _target(self)
    if ob is None:
        return self.object
    if self.kind == 'SHAPE':
        return ob.data.name if ob.data is not None else ""
    return ob.name


def _set_label(self, value):
    ob = _target(self)
    if ob is None or not value:
        return
    if self.kind == 'SHAPE' and ob.data is not None:
        ob.data.name = value
    else:
        ob.name = value
        self.object = ob.name   # Blender may have added a suffix


class MAYAKIT_PG_outliner_row(bpy.types.PropertyGroup):
    kind: EnumProperty(items=(('OBJECT', "Object", ""), ('SHAPE', "Shape", "")))
    object: StringProperty()
    depth: IntProperty()
    has_children: BoolProperty()
    label: StringProperty(name="Name", get=_get_label, set=_set_label)


# --- rows ------------------------------------------------------------------------------------

def dag_rows(scene, shapes):
    """[(kind, object name, depth, has children)] in Maya DAG order: roots in scene
    order, children depth first; collapsed objects hide their children."""
    order = {ob: i for i, ob in enumerate(scene.objects)}
    rows = []

    def visit(ob, depth):
        kids = sorted((c for c in ob.children if c in order), key=order.get)
        shape = shapes and ob.data is not None
        rows.append(('OBJECT', ob.name, depth, bool(kids) or shape))
        if ob.maya_kit_expanded:
            if shape:
                rows.append(('SHAPE', ob.name, depth + 1, False))
            for c in kids:
                visit(c, depth + 1)

    for ob in sorted((o for o in order if o.parent is None or o.parent not in order), key=order.get):
        visit(ob, 0)
    return rows


def rebuild(context=None, force=False):
    context = context or bpy.context
    wm, scene = context.window_manager, context.scene
    if scene is None or not hasattr(wm, "maya_kit_outliner_rows") or _state["busy"]:
        return False
    rows = dag_rows(scene, wm.maya_kit_outliner_shapes)
    sig = (scene.name, tuple(rows))
    if not force and sig == _state["sig"] and len(wm.maya_kit_outliner_rows) == len(rows):
        return False
    _state["busy"] = True
    try:
        coll = wm.maya_kit_outliner_rows
        coll.clear()
        for kind, name, depth, has in rows:
            it = coll.add()
            it.kind, it.object, it.depth, it.has_children = kind, name, depth, has
        _state["sig"] = sig
    finally:
        _state["busy"] = False
    return True


@persistent
def _on_depsgraph(scene, _depsgraph):
    rebuild()


@persistent
def _on_load(_dummy):
    _state["sig"] = None
    rebuild(force=True)


# --- selection ---------------------------------------------------------------------------------

def _get_index(self):
    ob = bpy.context.view_layer.objects.active
    for i, row in enumerate(self.maya_kit_outliner_rows):
        if row.kind == 'OBJECT' and ob is not None and row.object == ob.name:
            return i
    return -1


def _set_index(self, value):
    rows = self.maya_kit_outliner_rows
    if 0 <= value < len(rows):
        select_rows(bpy.context, rows, value, 'REPLACE')


def _select(ob, state=True):
    """``select_set``; False if ``ob`` is not in the view layer. (Checking
    ``view_layer.objects.get`` instead misses objects linked since the last
    view layer sync.)"""
    try:
        ob.select_set(state)
        return True
    except RuntimeError:
        return False


def select_rows(context, rows, index, mode, anchor=None):
    """Maya Outliner selection: REPLACE (click), TOGGLE (Ctrl), RANGE (Shift, from
    ``anchor`` = the active row)."""
    vl = context.view_layer
    ob = bpy.data.objects.get(rows[index].object)
    if ob is None:
        return
    if mode == 'TOGGLE':
        if _select(ob, not ob.select_get()) and ob.select_get():
            vl.objects.active = ob
        return
    if mode == 'RANGE' and anchor is not None and 0 <= anchor < len(rows):
        lo, hi = sorted((anchor, index))
        for row in list(rows)[lo:hi + 1]:
            o = bpy.data.objects.get(row.object)
            if o is not None:
                _select(o)
        vl.objects.active = ob
        return
    for o in context.selected_objects:
        o.select_set(False)
    if _select(ob):
        vl.objects.active = ob


class MAYAKIT_OT_outliner_select(bpy.types.Operator):
    """Select (Ctrl: toggle, Shift: range), like Maya's Outliner"""
    bl_idname = "maya_kit.outliner_select"
    bl_label = "Outliner Select"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty()
    mode: EnumProperty(items=(('REPLACE', "Replace", ""), ('TOGGLE', "Toggle", ""),
                              ('RANGE', "Range", "")))

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def invoke(self, context, event):
        self.mode = 'TOGGLE' if event.ctrl else 'RANGE' if event.shift else 'REPLACE'
        return self.execute(context)

    def execute(self, context):
        wm = context.window_manager
        rows = wm.maya_kit_outliner_rows
        if not 0 <= self.index < len(rows):
            return {'CANCELLED'}
        select_rows(context, rows, self.index, self.mode, anchor=wm.maya_kit_outliner_index)
        return {'FINISHED'}


class MAYAKIT_OT_outliner_expand(bpy.types.Operator):
    """Expand / collapse (Shift: with all descendants)"""
    bl_idname = "maya_kit.outliner_expand"
    bl_label = "Expand"
    bl_options = {'INTERNAL'}

    name: StringProperty()
    recursive: BoolProperty()

    def invoke(self, context, event):
        self.recursive = event.shift
        return self.execute(context)

    def execute(self, context):
        ob = bpy.data.objects.get(self.name)
        if ob is None:
            return {'CANCELLED'}
        state = not ob.maya_kit_expanded
        for o in ([ob, *ob.children_recursive] if self.recursive else [ob]):
            o.maya_kit_expanded = state
        rebuild(context)
        return {'FINISHED'}


class MAYAKIT_OT_outliner_refresh(bpy.types.Operator):
    """Rebuild the Outliner rows"""
    bl_idname = "maya_kit.outliner_refresh"
    bl_label = "Refresh"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        rebuild(context, force=True)
        return {'FINISHED'}


# --- drawing -------------------------------------------------------------------------------------

_ICONS = set()


def icon_for(row, ob):
    if not _ICONS:
        _ICONS.update(bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items.keys())
    name = f"OUTLINER_DATA_{ob.type}" if row.kind == 'SHAPE' else f"OUTLINER_OB_{ob.type}"
    return name if name in _ICONS else ('OBJECT_DATA' if row.kind == 'SHAPE' else 'OBJECT_DATAMODE')


class MAYAKIT_UL_outliner(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0):
        ob = _target(item)
        row = layout.row(align=True)
        if ob is None:
            row.label(text=item.object)
            return
        for _ in range(item.depth):
            row.label(text="", icon='BLANK1')
        if item.has_children:
            op = row.operator(MAYAKIT_OT_outliner_expand.bl_idname, text="", emboss=False,
                              icon='DISCLOSURE_TRI_DOWN' if ob.maya_kit_expanded else 'DISCLOSURE_TRI_RIGHT')
            op.name = ob.name
        else:
            row.label(text="", icon='BLANK1')
        op = row.operator(MAYAKIT_OT_outliner_select.bl_idname, text="", icon=icon_for(item, ob),
                          emboss=False, depress=ob.select_get())
        op.index = index
        sub = row.row()
        sub.active = ob.visible_get()   # hidden = grey text (Maya)
        sub.prop(item, "label", text="", emboss=False)

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flags = bpy.types.UI_UL_list.filter_items_by_name(
            self.filter_name, self.bitflag_filter_item, items, "label") if self.filter_name else []
        return flags, []


class MAYAKIT_PT_outliner(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = CATEGORY
    bl_label = "Outliner"

    @classmethod
    def poll(cls, context):
        # The Maya dock has no Outliner tab: with "Channel Box Dock Only" the Outliner is the
        # layout's own Outliner editor (ui/dock_tabs.py, ).
        from .. import preferences
        try:
            return not preferences.get(context).maya_dock_only
        except KeyError:
            return True

    def draw_header_preset(self, context):
        row = self.layout.row(align=True)
        row.prop(context.window_manager, "maya_kit_outliner_shapes", text="Shapes", toggle=True)

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        row = layout.row(align=True)
        row.operator("maya_kit.parent", text="Parent", icon='LINKED')
        row.operator("maya_kit.unparent", text="Unparent", icon='UNLINKED')
        row.operator(MAYAKIT_OT_outliner_refresh.bl_idname, text="", icon='FILE_REFRESH')
        layout.template_list("MAYAKIT_UL_outliner", "", wm, "maya_kit_outliner_rows",
                             wm, "maya_kit_outliner_index", rows=12)


def _shapes_changed(self, context):
    rebuild(context)


classes = (MAYAKIT_PG_outliner_row, MAYAKIT_OT_outliner_select, MAYAKIT_OT_outliner_expand,
           MAYAKIT_OT_outliner_refresh, MAYAKIT_UL_outliner, MAYAKIT_PT_outliner)


def _first_rebuild():
    rebuild(force=True)
    return None


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.types.WindowManager
    wm.maya_kit_outliner_rows = CollectionProperty(type=MAYAKIT_PG_outliner_row, options={'SKIP_SAVE'})
    wm.maya_kit_outliner_index = IntProperty(get=_get_index, set=_set_index, options={'SKIP_SAVE'})
    wm.maya_kit_outliner_shapes = BoolProperty(
        name="Shapes", description="Show shape nodes (object data) under their transforms (Maya "
                                   "Display > Shapes)", update=_shapes_changed, options={'SKIP_SAVE'})
    bpy.types.Object.maya_kit_expanded = BoolProperty(
        name="Expanded", description="Expanded in the Maya Outliner", options={'HIDDEN'})
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph)
    bpy.app.handlers.load_post.append(_on_load)
    _state["sig"] = None
    bpy.app.timers.register(_first_rebuild, first_interval=0.0)


def unregister():
    if bpy.app.timers.is_registered(_first_rebuild):
        bpy.app.timers.unregister(_first_rebuild)
    bpy.app.handlers.load_post.remove(_on_load)
    bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph)
    del bpy.types.Object.maya_kit_expanded
    wm = bpy.types.WindowManager
    del wm.maya_kit_outliner_shapes
    del wm.maya_kit_outliner_index
    del wm.maya_kit_outliner_rows
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    _state["sig"] = None
