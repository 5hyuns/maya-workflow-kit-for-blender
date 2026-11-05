# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Graph Editor List > Bookmarks: keep the objects (or the curves) the Graph Editor shows and bring them back.

- Bookmark Current Objects asks for a name ("Bookmark1", ...) and keeps the objects (and joints) listed now.
- Bookmark Selected Curves keeps the selected curves under the next free name, without asking.
- Choosing a bookmark in the List > Bookmarks menu loads its objects into the Graph Editor like List > Load Selected
  Objects (Auto Load goes off); a curve bookmark loads the curves' objects and shows only those curves.
- Remove All Bookmarks deletes them.

Bookmarks belong to the scene (saved with the file): the scene ID property ``STORE`` holds a list of
{"name", "objects", "bones", "curves": ["object<TAB>data path<TAB>index", ...]}.
"""

import bpy
from bpy.props import EnumProperty, IntProperty, StringProperty

STORE = "allset_graph_bookmarks"


def bookmarks(scene):
    out = []
    for b in scene.get(STORE, ()):
        d = {k: (list(v) if k != "name" else v) for k, v in b.items()}
        d["curves"] = [_curve(c) for c in d.get("curves", ())]
        out.append(d)
    return out


def _curve(text):
    ob, path, index = text.split("	")
    return ob, path, int(index)


def _stored(items):
    return [{**b, "curves": [f"{o}	{p}	{i}" for o, p, i in b.get("curves", ())]} for b in items]


def _save(scene, items):
    if items:
        scene[STORE] = _stored(items)
    elif STORE in scene:
        del scene[STORE]


def next_name(scene):
    used = {b["name"] for b in bookmarks(scene)}
    n = 1
    while f"Bookmark{n}" in used:
        n += 1
    return f"Bookmark{n}"


def _space(context):
    from ..ui import editor_chrome
    space = getattr(context, "space_data", None)
    return space if editor_chrome.is_graph(space) else None


def current_objects(context, space):
    """(object names, joints) the Graph Editor lists now."""
    from ..ui import editor_chrome
    names = [ob.name for ob in editor_chrome.listed_objects(context, space)]
    coll = editor_chrome.kit_list(space)
    bones = list(coll.get(editor_chrome.BONES, ())) if coll is not None else []
    return names, bones


def selected_curves(context):
    """[[object, data path, index]] of the selected curves the Graph Editor shows."""
    out = []
    for fc in getattr(context, "visible_fcurves", None) or ():
        if fc.select:
            owner = fc.id_data
            obs = [ob for ob in context.scene.objects if ob.animation_data and ob.animation_data.action == owner] \
                if isinstance(owner, bpy.types.Action) else []
            for ob in obs or ([owner] if isinstance(owner, bpy.types.Object) else []):
                out.append((ob.name, fc.data_path, fc.array_index))
    return out


def load(context, space, mark):
    """Show a bookmark in the Graph Editor: its objects as the loaded list; a curve bookmark shows only its curves."""
    from ..ui import editor_chrome as ec
    curves = [tuple(c) for c in mark.get("curves", ())]
    names = list(dict.fromkeys(c[0] for c in curves)) if curves else list(mark.get("objects", ()))
    names = [n for n in names if n in context.scene.objects]
    ds = ec._ds(space)
    coll = ec.kit_list(space) or ec._new_list()
    coll[ec.LOADED] = names
    coll[ec.BONES] = [] if curves else list(mark.get("bones", ()))
    coll[ec.AUTO] = False
    ds.filter_collection = coll
    ds.show_only_selected = False
    ec.sync_space(context, space)
    if curves:
        from .. import compat
        keep = set(curves)
        for n in names:
            for fc in compat.id_fcurves(context.scene.objects[n]):
                shown = (n, fc.data_path, fc.array_index) in keep
                fc.hide = not shown
                fc.select = shown
    return names


class ALLSET_OT_graph_bookmark(bpy.types.Operator):
    """Maya Graph Editor List > Bookmarks"""
    bl_idname = "allset.graph_bookmark"
    bl_label = "Create Bookmark"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(items=(
        ('OBJECTS', "Bookmark Current Objects", "Keep the objects the Graph Editor lists now as a bookmark"),
        ('CURVES', "Bookmark Selected Curves", "Keep the selected curves as a bookmark"),
        ('LOAD', "Load Bookmark", "Show the bookmark's objects (or curves) in the Graph Editor"),
        ('REMOVE_ALL', "Remove All Bookmarks", "Delete every Graph Editor bookmark")),
        default='OBJECTS', options={'SKIP_SAVE', 'HIDDEN'})
    name: StringProperty(name="Bookmark name", options={'SKIP_SAVE'})
    index: IntProperty(default=-1, options={'SKIP_SAVE', 'HIDDEN'})

    @classmethod
    def description(cls, context, props):
        return cls.bl_rna.properties["action"].enum_items[props.action].description

    @classmethod
    def poll(cls, context):
        return _space(context) is not None

    def invoke(self, context, event):
        if self.action == 'OBJECTS':
            self.name = next_name(context.scene)
            return context.window_manager.invoke_props_dialog(self, title="Create Bookmark", confirm_text="OK")
        return self.execute(context)

    def draw(self, context):
        self.layout.prop(self, "name")

    def execute(self, context):
        scene = context.scene
        space = _space(context)
        items = bookmarks(scene)
        if self.action == 'REMOVE_ALL':
            _save(scene, [])
        elif self.action == 'LOAD':
            if not 0 <= self.index < len(items):
                return {'CANCELLED'}
            load(context, space, items[self.index])
        elif self.action == 'OBJECTS':
            names, bones = current_objects(context, space)
            if not names:
                self.report({'WARNING'}, "Select objects to bookmark")
                return {'CANCELLED'}
            name = self.name.strip() or next_name(scene)
            items = [b for b in items if b["name"] != name]
            items.append({"name": name, "objects": names, "bones": bones, "curves": []})
            _save(scene, items)
        else:
            curves = selected_curves(context)
            if not curves:
                self.report({'WARNING'}, "Select curves to bookmark")
                return {'CANCELLED'}
            items.append({"name": next_name(scene), "objects": [], "bones": [], "curves": curves})
            _save(scene, items)
        from ..ui import editor_chrome
        editor_chrome._redraw_editors(context)
        return {'FINISHED'}


class ALLSET_MT_graph_bookmarks(bpy.types.Menu):
    """Maya Graph Editor List > Bookmarks: the bookmark commands, then the bookmarks to load"""
    bl_label = "Bookmarks"

    def draw(self, context):
        lay = self.layout
        lay.operator_context = 'INVOKE_DEFAULT'
        for action, label in (('OBJECTS', "Bookmark Current Objects"), ('CURVES', "Bookmark Selected Curves"),
                              ('REMOVE_ALL', "Remove All Bookmarks")):
            lay.operator("allset.graph_bookmark", text=label).action = action
        items = bookmarks(context.scene)
        if items:
            lay.separator()
            for i, b in enumerate(items):
                op = lay.operator("allset.graph_bookmark", text=b["name"], translate=False,
                                  icon='FCURVE' if b.get("curves") else 'OBJECT_DATA')
                op.action, op.index = 'LOAD', i


classes = (ALLSET_OT_graph_bookmark, ALLSET_MT_graph_bookmarks)
