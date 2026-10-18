# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya selection priority for object-mode clicks.

Maya picks the overlapping candidate of the highest type priority (``selectPrefPriorityMode
"animation"``; ikHandle 10, joint 9, nurbsCurve 4, everything else 2 — ,
, PREF:779-847), occluded or not. Blender's ``view3d.select`` picks by
depth, so a control curve or a joint in front of (or behind) a mesh can lose to the mesh.

``maya_kit.select_priority`` sits in front of the object-mode click select items. It only looks for
candidates above priority 2: when there is none, Blender's own pick (with its cycling) runs as usual.
"""

import math

import bpy
import numpy as np

from .preselect import project, segment_distance

# Maya factory customSelectPriority (PREF:781-847) for the kit's object kinds; anything else is 2.
IK_HANDLE, JOINT, CURVE, DEFAULT = 10, 9, 4, 2
RADIUS_PX = 5.0     # clickBoxSize 4 (defaults.json:95) = a box of half-width 4: half diagonal ~5.7 
BONE_WIDTH = 0.1    # octahedral bone: widest at 0.1 x length (Blender's bone shape)


# --- pure helpers (tests/test_step76_select_priority.py) -----------------------------------------------

def priority(kind):
    """Maya priority of a kit object kind: 'IK_HANDLE', 'ARMATURE', 'CURVE' or anything else."""
    return {'IK_HANDLE': IK_HANDLE, 'ARMATURE': JOINT, 'CURVE': CURVE}.get(kind, DEFAULT)


def rank(hits, radius):
    """The winning ``(name, priority, distance)`` of ``hits`` within ``radius`` that beats priority 2:
    highest priority, then nearest on screen, then name; None when nothing qualifies."""
    ok = [h for h in hits if h[2] <= radius and h[1] > DEFAULT]
    return min(ok, key=lambda h: (-h[1], h[2], h[0])) if ok else None


def bone_width(t, width):
    """Half thickness of an octahedral bone at parameter ``t`` (0 head .. 1 tail): ``width`` at 0.1,
    tapering to 0 at both ends."""
    return np.where(t < BONE_WIDTH, width * t / BONE_WIDTH, width * (1.0 - t) / (1.0 - BONE_WIDTH))


def segments_hit(mouse, a, b, front, width=None):
    """Smallest screen distance from ``mouse`` to the segments a[i]-b[i] with both ends in front of the
    view, less the bone thickness when ``width`` (per segment, at its widest) is given; inf when none."""
    if len(a) == 0:
        return float("inf")
    dist, t = segment_distance(mouse, a, b)
    if width is not None:
        dist = dist - bone_width(t, width)
    dist = np.where(front, dist, np.inf)
    return float(dist.min())


# --- scene -------------------------------------------------------------------------------------------------

def ik_targets(scene):
    """Objects that are an IK constraint's target (Maya ikHandle; kit ``ikHandleN``, step 58)."""
    out = set()
    for ob in scene.objects:
        if ob.type != 'ARMATURE' or ob.pose is None:
            continue
        for pb in ob.pose.bones:
            for con in pb.constraints:
                if con.type == 'IK' and con.target is not None and con.target.type != 'ARMATURE':
                    out.add(con.target.name)
    return out


def kind_of(ob, targets):
    if ob.name in targets:
        return 'IK_HANDLE'
    return ob.type if ob.type in ('ARMATURE', 'CURVE') else 'OTHER'


def _selectable(ob, space, view_layer):
    viewport = {"viewport": space} if isinstance(space, bpy.types.SpaceView3D) else {}   # tests: no view
    if ob.hide_select or not ob.visible_get(view_layer=view_layer, **viewport):
        return False
    key = ob.type.lower()
    return (getattr(space, "show_object_viewport_" + key, True)
            and getattr(space, "show_object_select_" + key, True))


def _segments(ob, kind, depsgraph):
    """World-space segments (a, b, reach) of what is drawn for ``ob``; reach = widest half thickness
    per unit of length (bones)."""
    mw = ob.matrix_world
    if kind == 'ARMATURE':
        a, b = [], []
        for pb in ob.pose.bones:
            bone = pb.bone
            if bone.hide or (len(bone.collections) and not any(c.is_visible_effectively for c in bone.collections)):
                continue
            a.append(mw @ pb.head)
            b.append(mw @ pb.tail)
        return a, b, BONE_WIDTH
    if kind == 'CURVE':
        ev = ob.evaluated_get(depsgraph)
        me = ev.to_mesh()
        try:
            co = np.empty(len(me.vertices) * 3)
            me.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            ed = np.empty(len(me.edges) * 2, dtype=np.int64)
            me.edges.foreach_get("vertices", ed)
            ed = ed.reshape(-1, 2)
        finally:
            ev.to_mesh_clear()
        if len(co):
            m = np.array(mw)
            co = co @ m[:3, :3].T + m[:3, 3]
        return co[ed[:, 0]], co[ed[:, 1]], 0.0
    # IK handle empty: the plain axes it draws (other empty shapes approximated by their axes)
    size = ob.empty_display_size if ob.type == 'EMPTY' else 0.0
    o = mw.translation
    a, b = [], []
    for axis in range(3):
        d = mw.col[axis].xyz * size
        a.append(o - d)
        b.append(o + d)
    return a, b, 0.0


def hits(context, region, rv3d, mouse):
    """``(name, priority, screen distance)`` for every selectable object above priority 2."""
    space, view_layer = context.space_data, context.view_layer
    depsgraph = context.evaluated_depsgraph_get()
    targets = ik_targets(context.scene)
    persp = np.array(rv3d.perspective_matrix)
    out = []
    for ob in context.scene.objects:   # view_layer.objects can yield None after removals (step 67)
        kind = kind_of(ob, targets)
        pri = priority(kind)
        if pri <= DEFAULT or not _selectable(ob, space, view_layer):
            continue
        a, b, reach = _segments(ob, kind, depsgraph)
        if len(a) == 0:
            continue
        xa, fa = project(np.asarray(a, dtype=np.float64), persp, region.width, region.height)
        xb, fb = project(np.asarray(b, dtype=np.float64), persp, region.width, region.height)
        width = reach * np.hypot(*(xb - xa).T) if reach else None
        d = segments_hit(mouse, xa, xb, fa & fb, width)
        out.append((ob.name, pri, max(d, 0.0)))
    return out


def apply(context, ob, shift, ctrl):
    """Maya click modifiers (): none = replace, Shift = toggle,
    Ctrl = deselect, Ctrl+Shift = add. Selecting makes ``ob`` the lead (active)."""
    view_layer = context.view_layer
    if ctrl and not shift:
        ob.select_set(False)
        return
    if shift and not ctrl and ob.select_get():
        ob.select_set(False)
        return
    if not shift and not ctrl:
        for other in context.selected_objects:
            if other != ob:
                other.select_set(False)
    ob.select_set(True)
    view_layer.objects.active = ob


def _enabled(context):
    from .. import preferences
    return preferences.get(context).select_priority


class MAYAKIT_OT_select_priority(bpy.types.Operator):
    """Click selection with Maya's priority: IK handles, joints and curves win over meshes"""
    bl_idname = "maya_kit.select_priority"
    bl_label = "Select (Maya Priority)"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def invoke(self, context, event):
        from ..ui import toolbox
        space, region = context.space_data, context.region
        if (context.mode != 'OBJECT' or space is None or space.type != 'VIEW_3D' or region is None
                or region.type != 'WINDOW' or toolbox.is_toolbox(space) or not _enabled(context)):
            return {'PASS_THROUGH'}
        rv3d = context.region_data
        if rv3d is None:
            return {'PASS_THROUGH'}
        scale = context.preferences.system.ui_scale or 1.0
        best = rank(hits(context, region, rv3d, (event.mouse_region_x, event.mouse_region_y)), RADIUS_PX * scale)
        if best is None:
            return {'PASS_THROUGH'}
        ob = context.scene.objects[best[0]]
        apply(context, ob, event.shift, event.ctrl)
        if event.value == 'PRESS' and ob.select_get():
            # Tweak tool: this press is consumed, so Blender makes no CLICK_DRAG from it — start the
            # tweak's move ourselves once the mouse leaves the drag threshold (step 97)
            self._start = (event.mouse_x, event.mouse_y)
            self._threshold = context.preferences.inputs.drag_threshold_mouse * scale
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        return {'FINISHED'}

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            if math.hypot(event.mouse_x - self._start[0], event.mouse_y - self._start[1]) >= self._threshold:
                bpy.ops.transform.translate('INVOKE_DEFAULT', release_confirm=True)
                return {'FINISHED'}
            return {'RUNNING_MODAL'}
        if event.type in {'LEFTMOUSE', 'ESC', 'RIGHTMOUSE'} and event.value in {'RELEASE', 'PRESS'}:
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


classes = (MAYAKIT_OT_select_priority,)
