# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Smart Duplicate / Smart Extrude: Shift+drag a Move/Rotate/Scale manipulator
duplicates the selected objects, or extrudes the selected faces/edges, and the drag
transforms the copies / new components (,
``manipSmartDuplicate 1``, ``manipSmartExtrude 1``, PREF:371-374).

Blender's transform gizmo is C (). Its keymap
(``Generic Gizmo Maybe Drag``) runs ``gizmogroup.gizmo_tweak`` for any Shift; the
Maya keyconfig puts ``maya_kit.manip_duplicate`` in front of it
(keymap/maya_patches.py 21). This operator duplicates/extrudes and always passes the
event on, so the gizmo then transforms the selection, which is the new part. A timer
waits for the transform to end and takes the copy / extrusion back when nothing moved
(a Shift+click, a cancelled drag). Plans: , 
"""

import bmesh
import bpy

from . import duplicate

# Gizmo groups of the transform manipulator (tool gizmo and the viewport's object gizmos);
# light/camera/spot gizmos share the keymap but are left alone (checked, ).
XFORM_GROUPS = {"VIEW3D_GGT_xform_gizmo", "VIEW3D_GGT_xform_gizmo_context"}
POLL = 0.05
EPS = 1e-6


def _pref(context, name):
    from .. import preferences
    try:
        return getattr(preferences.get(context), name)
    except KeyError:
        return True


def from_xform_gizmo(context):
    """The press is on the transform manipulator (context set by the gizmo map handler)."""
    group = getattr(context, "gizmo_group", None)
    return group is not None and group.bl_idname in XFORM_GROUPS


def _edit_meshes(context):
    return [ob for ob in context.objects_in_mode_unique_data if ob.type == 'MESH']


def _selected_coords(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    return [v.co.copy() for v in bm.verts if v.select]


def kind(context):
    """'DUPLICATE', 'EXTRUDE' or None for a Shift+press on the manipulator."""
    if not from_xform_gizmo(context):
        return None
    if context.mode == 'OBJECT':
        if context.selected_objects and _pref(context, "smart_duplicate"):
            return 'DUPLICATE'
        return None
    if context.mode == 'EDIT_MESH' and _pref(context, "smart_extrude"):
        _vert, edge, face = context.tool_settings.mesh_select_mode
        if (edge or face) and any(_selected_coords(ob) for ob in _edit_meshes(context)):
            return 'EXTRUDE'
    return None


# --- what each kind did, and how to take it back ---------------------------------------

def start_duplicate(context):
    originals = list(context.selected_objects)
    active = context.view_layer.objects.active
    duplicate.duplicate(context)
    copies = list(context.selected_objects)
    return {"kind": 'DUPLICATE', "copies": [o.name for o in copies],
            "matrices": [o.matrix_world.copy() for o in copies],
            "originals": [o.name for o in originals], "active": active.name if active else None}


def start_extrude(context):
    """Extrude in place (Maya polyExtrudeFacet / polyExtrudeEdge, keepFacesTogether on ):
    edges extrude as a region too, so a connected edge strip stays connected (delegated)."""
    obs = _edit_meshes(context)
    saved = {}
    for ob in obs:
        ob.update_from_editmode()
        saved[ob.name] = ob.data.copy().name    # mesh before the extrusion (for a cancel)
    bpy.ops.mesh.extrude_region(use_normal_flip=False)
    return {"kind": 'EXTRUDE', "saved": saved,
            "coords": {ob.name: _selected_coords(ob) for ob in obs}}


def moved(state):
    if state["kind"] == 'DUPLICATE':
        for name, m in zip(state["copies"], state["matrices"]):
            ob = bpy.data.objects.get(name)
            if ob is not None and any(abs(a - b) > EPS for ra, rb in zip(ob.matrix_world, m)
                                      for a, b in zip(ra, rb)):
                return True
        return False
    for name, before in state["coords"].items():
        ob = bpy.data.objects.get(name)
        if ob is None or ob.mode != 'EDIT':
            return True    # left edit mode meanwhile: keep what is there
        now = _selected_coords(ob)
        if len(now) != len(before) or any((a - b).length > EPS for a, b in zip(now, before)):
            return True
    return False


def revert(state):
    """Take back a copy / extrusion whose transform was cancelled (no undo step exists)."""
    if state["kind"] == 'DUPLICATE':
        for name in state["copies"]:
            ob = bpy.data.objects.get(name)
            if ob is not None:
                bpy.data.objects.remove(ob)
        for name in state["originals"]:
            ob = bpy.data.objects.get(name)
            if ob is not None:
                ob.select_set(True)
        if state["active"] in bpy.data.objects:
            bpy.context.view_layer.objects.active = bpy.data.objects[state["active"]]
        return
    for name, mesh_name in state["saved"].items():
        ob, saved = bpy.data.objects.get(name), bpy.data.meshes.get(mesh_name)
        if ob is None or saved is None or ob.mode != 'EDIT':
            continue
        bm = bmesh.from_edit_mesh(ob.data)
        bm.clear()
        bm.from_mesh(saved)
        bmesh.update_edit_mesh(ob.data)


def cleanup(state):
    for mesh_name in state.get("saved", {}).values():
        me = bpy.data.meshes.get(mesh_name)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


def _last_op():
    ops = bpy.context.window_manager.operators
    return ops[-1].as_pointer() if len(ops) else 0


def _transform_running(window):
    return any(op.bl_idname.startswith("TRANSFORM_OT_") for op in window.modal_operators)


# --- the active handle (Maya MMB drag anywhere), step 28 -------------------------------

# Last handle per transform kind:  (manipsRememberActiveHandle,
# ...AfterToolSwitch true, defaults.json:63-65). Session only; a re-tap of the tool key resets.
HANDLES = {}
OP_KINDS = {"TRANSFORM_OT_translate": 'TRANSLATE', "TRANSFORM_OT_rotate": 'ROTATE',
            "TRANSFORM_OT_resize": 'RESIZE'}


def handle_from_op(bl_idname, props):
    """(kind, handle) for a transform the manipulator ran; handle None = free (centre)."""
    kind = OP_KINDS.get(bl_idname)
    if kind is None:
        return None, None
    axes = tuple(bool(a) for a in props.constraint_axis)
    if kind == 'ROTATE':
        if props.orient_axis == 'VIEW' and not any(axes):
            return kind, None
        return kind, {"constraint_axis": axes, "orient_type": props.orient_type,
                      "orient_axis": props.orient_axis}
    if not any(axes):
        return kind, None
    return kind, {"constraint_axis": axes, "orient_type": props.orient_type}


def remember_last_op(since):
    """Remember the handle of a transform registered after ``since`` (an op pointer)."""
    ops = bpy.context.window_manager.operators
    if not len(ops) or ops[-1].as_pointer() == since:
        return
    kind, handle = handle_from_op(ops[-1].bl_idname, ops[-1].properties)
    if kind is not None:
        HANDLES[kind] = handle


def reset_handle(kind):
    HANDLES.pop(kind, None)


def finish(state, window, area, region):
    """After the transform: remember its handle; keep a moved copy / extrusion, take back
    one that didn't move."""
    if state["kind"] == 'PRESS' or moved(state):
        remember_last_op(state["last_op"])
    elif _last_op() != state["last_op"]:
        # Confirmed without moving (Shift+click): the transform pushed the only undo
        # step (the duplicate/extrude was a nested call), so one undo is the state before.
        with bpy.context.temp_override(window=window, area=area, region=region):
            bpy.ops.ed.undo()
    else:
        revert(state)    # cancelled: no undo step, take it back by hand
    cleanup(state)


def watch(state, window, area, region):
    """Poll until the gizmo's transform ends, then ``finish``."""
    state["last_op"] = _last_op()

    def tick():
        try:
            if window not in bpy.context.window_manager.windows[:]:
                cleanup(state)
                return None
            if _transform_running(window):
                return POLL
            finish(state, window, area, region)
        except ReferenceError:
            cleanup(state)
        return None

    bpy.app.timers.register(tick, first_interval=POLL)


class MAYAKIT_OT_manip_duplicate(bpy.types.Operator):
    """Shift+drag a manipulator: duplicate the selected objects or extrude the selected
    faces/edges, then the drag moves, rotates or scales them (Maya Smart Duplicate /
    Smart Extrude)"""
    bl_idname = "maya_kit.manip_duplicate"
    bl_label = "Smart Duplicate / Extrude"
    bl_options = {'INTERNAL'}

    def invoke(self, context, _event):
        return self.execute(context)

    def execute(self, context):
        what = kind(context)
        if what is not None:
            state = start_duplicate(context) if what == 'DUPLICATE' else start_extrude(context)
            if context.window is not None:
                watch(state, context.window, context.area, context.region)
            else:
                cleanup(state)
        # Always pass the event on: the gizmo's own tweak transforms the selection.
        return {'PASS_THROUGH'}


class MAYAKIT_OT_manip_press(bpy.types.Operator):
    """LMB on the manipulator: remember which handle the drag used (Maya active handle)"""
    bl_idname = "maya_kit.manip_press"
    bl_label = "Manipulator Press"
    bl_options = {'INTERNAL'}

    def invoke(self, context, _event):
        if from_xform_gizmo(context) and context.window is not None:
            watch({"kind": 'PRESS'}, context.window, context.area, context.region)
        return {'PASS_THROUGH'}


TRANSFORM_OPS = {'TRANSLATE': "translate", 'ROTATE': "rotate", 'RESIZE': "resize"}


class MAYAKIT_OT_manip_mmb(bpy.types.Operator):
    """MMB drag anywhere: move/rotate/scale along the last picked manipulator handle
    (free when none, Maya)"""
    bl_idname = "maya_kit.manip_mmb"
    bl_label = "Drag Active Handle"
    bl_options = {'INTERNAL'}

    mode: bpy.props.EnumProperty(items=[(k, k.title(), "") for k in TRANSFORM_OPS])

    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == 'VIEW_3D'

    def invoke(self, context, _event):
        kwargs = {"release_confirm": True}
        handle = HANDLES.get(self.mode)
        if handle:
            kwargs.update(handle)
        op = getattr(bpy.ops.transform, TRANSFORM_OPS[self.mode])
        try:
            res = op('INVOKE_DEFAULT', **kwargs)
        except RuntimeError:     # nothing to transform (poll failed)
            return {'PASS_THROUGH'}
        return {'FINISHED'} if res & {'RUNNING_MODAL', 'FINISHED'} else {'CANCELLED'}


OPTIONS = {'SMART_DUPLICATE': "smart_duplicate", 'SMART_EXTRUDE': "smart_extrude"}


class MAYAKIT_OT_manip_option(bpy.types.Operator):
    """Toggle a manipulator option (W/E/R hold menu: Smart Duplicate, Smart Extrude)"""
    bl_idname = "maya_kit.manip_option"
    bl_label = "Manipulator Option"
    bl_options = {'INTERNAL'}

    option: bpy.props.EnumProperty(items=(('SMART_DUPLICATE', "Smart Duplicate", ""),
                                          ('SMART_EXTRUDE', "Smart Extrude", "")))

    def execute(self, context):
        from .. import preferences
        prefs = preferences.get(context)
        name = OPTIONS[self.option]
        setattr(prefs, name, not getattr(prefs, name))
        label = self.option.replace("_", " ").title()
        self.report({'INFO'}, f"{label} {'on' if getattr(prefs, name) else 'off'}")
        return {'FINISHED'}


class MAYAKIT_OT_manip_size(bpy.types.Operator):
    """Make the manipulator bigger or smaller (Maya = / -)"""
    bl_idname = "maya_kit.manip_size"
    bl_label = "Manipulator Size"
    bl_options = {'INTERNAL'}

    # Maya: manipOptions -r -s 2.0 / 0.5 (Maya-389 via );
    # Blender's gizmo_size is 10-200 px, so 1.25x steps.
    factor: bpy.props.FloatProperty(name="Factor", default=1.25, min=0.1, max=10.0,
                                    options={'SKIP_SAVE'})

    def execute(self, context):
        from .. import prefs_preset
        size = context.preferences.view.gizmo_size
        new = max(10, min(200, round(size * self.factor)))
        if new == size:
            new = max(10, min(200, size + (1 if self.factor > 1 else -1)))
        got = prefs_preset.set_runtime("view.gizmo_size", new)
        self.report({'INFO'}, f"Manipulator size {got} px")
        for area in context.screen.areas if context.screen else ():
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}


def option_state(option):
    """Current value of a manip_option toggle (for the hold menus' check boxes)."""
    return bool(_pref(bpy.context, OPTIONS[option]))


classes = (MAYAKIT_OT_manip_duplicate, MAYAKIT_OT_manip_option, MAYAKIT_OT_manip_size,
           MAYAKIT_OT_manip_press, MAYAKIT_OT_manip_mmb)
