# SPDX-License-Identifier: GPL-3.0-or-later
"""Global key batch 4: Ctrl+X cut / Ctrl+V paste, Alt+\\ playback range = animation range,
Alt+1 / 2 / 4 show toggles, Ctrl+` / Shift+~ / Ctrl+Shift+~ smooth proxy. Alt+X walk is Blender's view3d.walk.

Maya behaviour (scripts of the installed Maya 2022, behaviour only):
- CutSelected = cutCopyPaste "cut": export the selection (with its hierarchy) to the clipboard file, then delete it
  (startup/Maya-1139; ).
- PlaybackRangeAnimStartEnd: playback min / max = animation start / end (Maya-20634).
- toggleNurbsCurvesOption / togglePolygonsOption / toggleImagePlaneOption flip that type in the focused model panel
  (others/Maya; hotkeys_and_menus.md:113).
- smoothingDisplayToggle 1 swaps the proxy (cage) and smooth mesh visibility (both shown -> cage only), 0 shows both;
  performSmoothProxy = Mesh > Smooth Proxy > Subdiv Proxy (others/Maya; hotkeys_and_menus.md:121).
"""

import bpy

from . import display


# --- Ctrl+X ---------------------------------------------------------------------------------------------

def cut_targets(selected):
    """The selection plus everything below it (Maya exports and deletes the selected DAG hierarchy)."""
    out, seen = [], set()
    for ob in selected:
        for o in (ob, *ob.children_recursive):
            if o.name not in seen:
                seen.add(o.name)
                out.append(o)
    return out


class ALLSET_OT_cut(bpy.types.Operator):
    """Cut the selected objects (Maya Ctrl+X): copy them to the clipboard, then delete them. Ctrl+V pastes them back"""
    bl_idname = "allset.cut"
    bl_label = "Cut"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(context.selected_objects)

    def execute(self, context):
        targets = cut_targets(context.selected_objects)
        for ob in targets:
            try:
                ob.select_set(True)
            except RuntimeError:        # not in the view layer
                pass
        names = [ob.name for ob in targets]
        with context.temp_override(selected_objects=targets):
            bpy.ops.view3d.copybuffer()
        datas = {ob.data for ob in targets if ob.data is not None}
        for ob in targets:
            bpy.data.objects.remove(ob)
        # Maya deletes the shape with its transform: drop data left without users, or the paste gets "pCubeShape1.001".
        bpy.data.batch_remove([d for d in datas if d.users == 0])
        self.report({'INFO'}, f"Cut {len(names)} object(s)")
        return {'FINISHED'}


def first_pasted(before, objects):
    """Maya pasteScene selects the new nodes and then only the first (others/Maya-41): the lead.
    Of the new objects, the first top node (no parent among the new ones), by name for a stable order."""
    new = [o for o in objects if o.name not in before]
    names = {o.name for o in new}
    roots = sorted((o for o in new if o.parent is None or o.parent.name not in names), key=lambda o: o.name)
    return roots[0] if roots else None


class ALLSET_OT_paste(bpy.types.Operator):
    """Paste the clipboard objects (Maya Ctrl+V): the pasted objects stay selected and the first one becomes the lead"""
    bl_idname = "allset.paste"
    bl_label = "Paste"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        before = set(bpy.data.objects.keys())
        if bpy.ops.view3d.pastebuffer() != {'FINISHED'}:
            return {'CANCELLED'}
        lead = first_pasted(before, context.scene.objects)
        if lead is not None:
            context.view_layer.objects.active = lead
        return {'FINISHED'}


# --- Alt+\ ----------------------------------------------------------------------------------------------

def playback_to_animation_range(scene):
    """Kit rule (step 20): playback range = preview range, animation range = frame_start / end. Turning the preview
    range off makes playback = animation; its values stay, so the Range Slider double-click can bring them back."""
    scene.use_preview_range = False


class ALLSET_OT_playback_range_anim(bpy.types.Operator):
    """Set the playback range to the animation range (Maya Alt+\\)"""
    bl_idname = "allset.playback_range_anim"
    bl_label = "Playback Range = Animation Range"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        playback_to_animation_range(context.scene)
        for win in context.window_manager.windows:
            for area in win.screen.areas:
                if area.type in {'DOPESHEET_EDITOR', 'GRAPH_EDITOR', 'NLA_EDITOR', 'SEQUENCE_EDITOR'}:
                    area.tag_redraw()
        return {'FINISHED'}


# --- Alt+1 / 2 / 4 --------------------------------------------------------------------------------------

SHOW_KINDS = (
    ('CURVES', "NURBS Curves", "Maya Alt+1: curves in this view"),
    ('POLYGONS', "Polygons", "Maya Alt+2: meshes in this view"),
    ('IMAGE_PLANES', "Image Planes", "Maya Alt+4: image planes (image empties, every view)"),
)
SPACE_FILTER = {'CURVES': "show_object_viewport_curve", 'POLYGONS': "show_object_viewport_mesh"}
IMAGE_FLAGS = ("show_empty_image_perspective", "show_empty_image_orthographic")


def image_planes(scene):
    return [o for o in scene.objects if o.type == 'EMPTY' and o.empty_display_type == 'IMAGE']


def toggle_show(space, scene, kind):
    """Flip one Maya Show type. Returns the new state (True = shown). Blender has no view filter for image empties
    only (``empty`` also hides groups and locators), so image planes flip their own display flags in every view."""
    if kind in SPACE_FILTER:
        attr = SPACE_FILTER[kind]
        new = not getattr(space, attr)
        setattr(space, attr, new)
        return new
    planes = image_planes(scene)
    new = not any(getattr(o, f) for o in planes for f in IMAGE_FLAGS)
    for o in planes:
        for f in IMAGE_FLAGS:
            setattr(o, f, new)
    return new


class ALLSET_OT_toggle_show(bpy.types.Operator):
    """Show or hide one object type in the view under the mouse (Maya Alt+1 / Alt+2 / Alt+4)"""
    bl_idname = "allset.toggle_show"
    bl_label = "Toggle Show"
    bl_options = {'REGISTER'}

    kind: bpy.props.EnumProperty(items=SHOW_KINDS, name="Type", options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return context.space_data is not None and context.space_data.type == 'VIEW_3D'

    def execute(self, context):
        toggle_show(context.space_data, context.scene, self.kind)
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}


# --- Ctrl+` / Shift+~ / Ctrl+Shift+~ ----------------------------------------------------------------------
# The kit's Subdiv Proxy is a user Subsurf (ui/menu_map.py "Mesh/Smooth Proxy/Subdiv Proxy"): the cage is the mesh,
# the smooth mesh is the modifier. "Both" draws the cage wire over the smooth surface like smooth preview 2.

PROXY_ACTIONS = (
    ('TOGGLE', "Toggle Proxy Display", "Maya Ctrl+`: cage <-> smooth"),
    ('BOTH', "Both Proxy and Subdiv Display", "Maya Shift+~: cage wire and smooth surface"),
    ('CREATE', "Subdiv Proxy", "Maya Ctrl+Shift+~: add the subdivision"),
)
_BOTH_FLAG = "allset_proxy_wire"   # object custom prop: show_wire turned on by "both"


def proxy_modifier(ob):
    """The object's proxy Subsurf: its last Subsurf that is not the kit's smooth preview."""
    mods = [m for m in ob.modifiers if m.type == 'SUBSURF' and not display.is_preview(m)]
    return mods[-1] if mods else None


def _set_both_wire(ob, on):
    if on:
        if not ob.show_wire:
            ob.show_wire = True
            ob[_BOTH_FLAG] = True
    elif ob.get(_BOTH_FLAG):
        ob.show_wire = False
        del ob[_BOTH_FLAG]


def proxy_action(ob, action):
    """Apply one smooth-proxy key to a mesh object. Returns False when it has no proxy (nothing done)."""
    mod = proxy_modifier(ob)
    if action == 'CREATE':
        if mod is None:
            mod = ob.modifiers.new("Subdivision", 'SUBSURF')
            first_preview = next((i for i, m in enumerate(ob.modifiers) if display.is_preview(m)), None)
            if first_preview is not None:   # the kit's smooth preview stays last in the stack (step 15)
                with bpy.context.temp_override(object=ob):
                    bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=first_preview)
        mod.show_viewport = True
        return True
    if mod is None:
        return False
    if action == 'BOTH':
        mod.show_viewport = True
        _set_both_wire(ob, True)
    elif ob.get(_BOTH_FLAG):            # both shown -> the cage only
        _set_both_wire(ob, False)
        mod.show_viewport = False
    else:
        mod.show_viewport = not mod.show_viewport
    return True


class ALLSET_OT_smooth_proxy(bpy.types.Operator):
    """Maya smooth proxy keys: Ctrl+` toggle cage / smooth, Shift+~ show both, Ctrl+Shift+~ create"""
    bl_idname = "allset.smooth_proxy"
    bl_label = "Smooth Proxy"
    bl_options = {'REGISTER', 'UNDO'}

    action: bpy.props.EnumProperty(items=PROXY_ACTIONS, name="Action", options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return any(ob.type == 'MESH' for ob in cls._targets(context))

    @staticmethod
    def _targets(context):
        if context.mode == 'EDIT_MESH':
            return list(context.objects_in_mode)
        return list(context.selected_objects)

    def execute(self, context):
        done = [proxy_action(ob, self.action) for ob in self._targets(context) if ob.type == 'MESH']
        if not any(done):
            self.report({'WARNING'}, "No subdiv proxy on the selection (Mesh > Smooth Proxy > Subdiv Proxy, Ctrl+Shift+~)")
            return {'CANCELLED'}
        return {'FINISHED'}


classes = (ALLSET_OT_cut, ALLSET_OT_paste, ALLSET_OT_playback_range_anim, ALLSET_OT_toggle_show, ALLSET_OT_smooth_proxy)
