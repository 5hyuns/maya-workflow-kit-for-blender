# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Smart Duplicate / Smart Extrude: Shift+drag a Move/Rotate/Scale manipulator
duplicates the selected objects, or extrudes the selected faces/edges, and the drag
transforms the copies / new components (research/maya/interaction.md:107,
``manipSmartDuplicate 1``, ``manipSmartExtrude 1``, PREF:371-374).

Blender's transform gizmo is C (research/blender/api_limits.md:62). Its keymap
(``Generic Gizmo Maybe Drag``) runs ``gizmogroup.gizmo_tweak`` for any Shift; the
Maya keyconfig puts ``maya_kit.manip_duplicate`` in front of it
(keymap/maya_patches.py 21). This operator duplicates/extrudes and always passes the
event on, so the gizmo then transforms the selection, which is the new part. A timer
waits for the transform to end and takes the copy / extrusion back when nothing moved
(a Shift+click, a cancelled drag). Plans: docs/steps/step_22.md, docs/steps/step_26.md.
"""

import bmesh
import bpy

from . import duplicate

# Gizmo groups of the transform manipulator (tool gizmo and the viewport's object gizmos);
# light/camera/spot gizmos share the keymap but are left alone (measured, step_26.md).
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
    """Extrude in place (Maya polyExtrudeFacet / polyExtrudeEdge, keepFacesTogether on [K]):
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


def finish(state, window, area, region):
    """After the transform: keep a moved copy / extrusion, take back one that didn't move."""
    if not moved(state):
        if _last_op() != state["last_op"]:
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


def option_state(option):
    """Current value of a manip_option toggle (for the hold menus' check boxes)."""
    return bool(_pref(bpy.context, OPTIONS[option]))


classes = (MAYAKIT_OT_manip_duplicate, MAYAKIT_OT_manip_option)
