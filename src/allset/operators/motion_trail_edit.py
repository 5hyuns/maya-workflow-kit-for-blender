# SPDX-License-Identifier: GPL-3.0-or-later
"""Move keys on a motion trail, like Maya's editable motion trail (Motion Trail Editor trails).

In Maya a click on a key marker of a motion trail picks that key (Shift adds more keys) and the Move tool drags it:
the object's translate keys at that frame change so the object passes through the new world point; only the
channels the move changes are written, a parent's space is taken into account, the other keys stay, one undo step
undoes the drag. Frame (non-key) markers can't be picked.

Here, in the Maya layout's 3D Views with Blender's Motion Paths overlay on, a left press on a key marker of a
motion path (an object's path in Object Mode, a bone's head path in Pose Mode) picks the key and a drag moves the
picked keys in the view plane at once (Blender has no gizmo for a trail key, so pick and move are one gesture).
Shift toggles a key in the picked set, Ctrl removes it, Ctrl+Shift adds it, as for the kit's other selections. The
location keys at the key's frame take the move, converted into the channels' space (parent, parent inverse); a
channel without a key at that frame gets one, a locked channel stays. Owners whose location is set by a constraint or
a driver, connected bones and bones with constraints can't be moved (a warning says why). Esc / right click puts
everything back. A press anywhere else passes through to the normal selection (a plain one also drops the picked
keys). The picked keys are drawn in the trail's Selected Key Color.
"""

import time

import bpy
from bpy.props import EnumProperty
from mathutils import Vector

from .. import compat

PICK_PX = 10.0          # how close to a key marker a press must be (UI scale 1)
MARK_PX = 4.0           # half size of the picked key square (UI scale 1)
UPDATE_S = 1.0 / 30.0   # trail recalculation interval while dragging
EPS = 1e-9

_MODES = [('SET', "Set", ""), ('TOGGLE', "Toggle", ""), ('SUB', "Deselect", ""), ('ADD', "Add", "")]

# picked keys: (object name, bone name or "", frame)
_picked = []
_draw = []


# --- trail owners and key markers ---------------------------------------------------------------------------------

class Owner:
    """An object or pose bone with a motion path."""

    def __init__(self, ob, pb=None):
        self.ob, self.pb = ob, pb

    @property
    def key(self):
        return self.ob.name, (self.pb.name if self.pb is not None else "")

    @property
    def holder(self):
        return self.pb if self.pb is not None else self.ob

    @property
    def path(self):
        return self.holder.motion_path

    @property
    def viz(self):
        if self.pb is not None:
            return self.ob.pose.animation_visualization.motion_path
        return self.ob.animation_visualization.motion_path

    def prefix(self):
        return f'pose.bones["{bpy.utils.escape_identifier(self.pb.name)}"].' if self.pb is not None else ""

    def location_path(self):
        return self.prefix() + "location"


def owner_of(key):
    ob = bpy.data.objects.get(key[0])
    if ob is None:
        return None
    if key[1]:
        pb = ob.pose.bones.get(key[1]) if ob.pose is not None else None
        return Owner(ob, pb) if pb is not None else None
    return Owner(ob)


def owners(context):
    """Owners whose motion path shows in this mode: bones of the posed armature in Pose Mode, objects otherwise."""
    ob = context.active_object
    out = []
    if ob is not None and ob.mode == 'POSE':
        if ob.pose is not None and ob.visible_get():
            out = [Owner(ob, pb) for pb in ob.pose.bones if pb.motion_path is not None and compat_visible(pb)]
        return out
    if context.mode != 'OBJECT':
        return out
    space = context.space_data if getattr(context.space_data, "type", "") == 'VIEW_3D' else None
    for o in context.view_layer.objects:
        if o.motion_path is not None and o.visible_get(viewport=space):
            out.append(Owner(o))
    return out


def compat_visible(pb):
    try:
        return not compat.bone_hidden(pb)
    except (AttributeError, TypeError):
        return True


def key_frames(owner):
    """Frames of the owner's keys (the frames Blender highlights on its path)."""
    ob = owner.ob
    fcs = compat.id_fcurves(ob)
    if owner.pb is not None and not owner.viz.show_keyframe_action_all:
        pre = owner.prefix()
        fcs = [fc for fc in fcs if fc.data_path.startswith(pre)]
    elif owner.pb is None:
        fcs = [fc for fc in fcs if not fc.data_path.startswith("pose.bones[")]
    frames = set()
    for fc in fcs:
        for kp in fc.keyframe_points:
            frames.add(int(round(kp.co.x)))
    return sorted(frames)


def drawn_range(owner, scene):
    """(first, last) frame of the path that is drawn."""
    mp, viz = owner.path, owner.viz
    first, last = mp.frame_start, mp.frame_start + len(mp.points) - 1
    if viz.type == 'CURRENT_FRAME':
        cur = scene.frame_current
        first, last = max(first, cur - viz.frame_before), min(last, cur + viz.frame_after)
    return first, last


def markers(owner, scene):
    """[(frame, world point)] of the owner's key markers that are drawn."""
    mp, viz = owner.path, owner.viz
    if mp is None or viz.use_camera_space_bake or not viz.show_keyframe_highlight:
        return []
    first, last = drawn_range(owner, scene)
    out = []
    for f in key_frames(owner):
        if first <= f <= last:
            i = f - mp.frame_start
            if 0 <= i < len(mp.points):
                out.append((f, Vector(mp.points[i].co)))
    return out


def ui_scale(context):
    return context.preferences.system.ui_scale


def pick(context, x, y):
    """(owner key, frame) of the key marker nearest to region point (x, y), or None."""
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    region, rv3d = context.region, context.region_data
    best, best_d = None, PICK_PX * ui_scale(context)
    for owner in owners(context):
        for f, co in markers(owner, context.scene):
            p = location_3d_to_region_2d(region, rv3d, co)
            if p is None:
                continue
            d = ((p.x - x) ** 2 + (p.y - y) ** 2) ** 0.5
            if d <= best_d:
                best, best_d = (owner.key, f), d
    return best


def is_maya_view(context):
    from ..ui import maya_joints, toolbox
    space = context.space_data
    try:
        return (space is not None and space.type == 'VIEW_3D' and not toolbox.is_toolbox(space)
                and space.overlay.show_overlays and space.overlay.show_motion_paths
                and maya_joints.maya_workspace(context.window.workspace))
    except (AttributeError, ReferenceError):
        return False


def select(hit, mode):
    """Update the picked keys for a press on ``hit`` (or on nothing when None)."""
    entry = (hit[0][0], hit[0][1], hit[1]) if hit is not None else None
    if entry is None:
        if mode == 'SET':
            _picked.clear()
        return
    if mode == 'SET':
        if entry not in _picked:
            _picked[:] = [entry]
    elif mode == 'TOGGLE':
        if entry in _picked:
            _picked.remove(entry)
        else:
            _picked.append(entry)
    elif mode == 'SUB':
        if entry in _picked:
            _picked.remove(entry)
    elif entry not in _picked:
        _picked.append(entry)


def picked():
    return list(_picked)


def clear():
    _picked.clear()


# --- world move -> location channels ------------------------------------------------------------------------------

class Unsupported(Exception):
    pass


def _driven(ob, path):
    ad = ob.animation_data
    return ad is not None and any(d.data_path == path for d in ad.drivers)


def channel_map(owner):
    """3x3 matrix taking a world move to the owner's location channels at the current frame (raises Unsupported)."""
    ob, pb = owner.ob, owner.pb
    if _driven(ob, owner.location_path()):
        raise Unsupported(f"{owner.holder.name}: a driver sets its location")
    if pb is None:
        parent_space = ob.matrix_world @ ob.matrix_local.inverted_safe() @ ob.matrix_parent_inverse
        local = ob.location + ob.delta_location
        if (parent_space @ local - ob.matrix_world.translation).length > 1e-4 * max(1.0, local.length):
            raise Unsupported(f"{ob.name}: a constraint moves it")
        lin = parent_space.to_3x3()
    else:
        if pb.bone.use_connect:
            raise Unsupported(f"{pb.name}: a connected bone can't move")
        if any(c.enabled and c.influence > 0.0 for c in pb.constraints):
            raise Unsupported(f"{pb.name}: a constraint moves it")
        if owner.path is not None and not owner.path.use_bone_head:
            raise Unsupported(f"{pb.name}: its trail follows the bone's tail")
        lin = (ob.matrix_world @ pb.matrix @ pb.matrix_basis.inverted_safe()).to_3x3()
    if abs(lin.determinant()) < 1e-12:
        raise Unsupported(f"{owner.holder.name}: its parent space is flat (scale 0)")
    return lin.inverted()


def channel_maps(scene, owner_frames):
    """{(owner key, frame): 3x3} evaluated at each frame (the current frame is put back)."""
    cur, sub = scene.frame_current, scene.frame_subframe
    out, errors = {}, []
    frames = sorted({f for _k, f in owner_frames})
    moved = False
    try:
        for f in frames:
            if f != cur or sub:
                scene.frame_set(f)
                moved = True
            for key, ff in owner_frames:
                if ff != f:
                    continue
                owner = owner_of(key)
                if owner is None:
                    continue
                try:
                    out[(key, f)] = channel_map(owner)
                except Unsupported as ex:
                    if str(ex) not in errors:
                        errors.append(str(ex))
    finally:
        if moved:
            scene.frame_set(cur, subframe=sub)
    return out, errors


class Channel:
    """One location channel at one frame: its F-curve and key, put back by ``restore``."""

    def __init__(self, owner, index, frame):
        self.owner, self.index, self.frame = owner, index, frame
        self.fc = self._find()
        self.created = False
        self.inserted = False
        self.snapshot = self._snap() if self.fc is not None else None
        self.base = None

    def _coll(self):
        return compat.id_fcurve_collection(self.owner.ob)

    def _find(self):
        coll = self._coll()
        if coll is None:
            return None
        return coll.find(self.owner.location_path(), index=self.index)

    def _snap(self):
        return [(tuple(k.co), tuple(k.handle_left), tuple(k.handle_right)) for k in self.fc.keyframe_points]

    def _key(self):
        for kp in self.fc.keyframe_points:
            if abs(kp.co.x - self.frame) < 1e-4:
                return kp
        return None

    def ensure(self):
        """The key at the frame (made on the first real move)."""
        if self.fc is None:
            holder = self.owner.holder
            holder.keyframe_insert("location", index=self.index, frame=self.frame)
            self.fc = self._find()
            self.created = True
            self.snapshot = []
        kp = self._key()
        if kp is None:
            value = self.fc.evaluate(self.frame)
            kp = self.fc.keyframe_points.insert(self.frame, value)
            self.inserted = not self.created
            self.fc.update()
            kp = self._key()
        if self.base is None:
            self.base = (kp.co.y, kp.handle_left.y, kp.handle_right.y)
        return kp

    def apply(self, dv):
        if self.base is None and abs(dv) < EPS:
            return
        kp = self.ensure()
        y, hl, hr = self.base
        kp.co.y = y + dv
        kp.handle_left.y = hl + dv
        kp.handle_right.y = hr + dv
        self.fc.update()

    def restore(self):
        if self.fc is None:
            return
        if self.created:
            coll = self._coll()
            if coll is not None:
                coll.remove(self.fc)
            self.fc = None
            return
        if self.inserted:
            kp = self._key()
            if kp is not None:
                self.fc.keyframe_points.remove(kp)
        for kp, (co, hl, hr) in zip(self.fc.keyframe_points, self.snapshot):
            kp.co, kp.handle_left, kp.handle_right = co, hl, hr
        self.fc.update()


class KeyMove:
    """Moving picked trail keys by one world vector."""

    def __init__(self, context, keys):
        self.scene = context.scene
        maps, self.errors = channel_maps(self.scene, keys)
        self.items = []
        for key, f in keys:
            lin = maps.get((key, f))
            owner = owner_of(key)
            if lin is None or owner is None:
                continue
            locks = tuple(owner.holder.lock_location)
            chans = [None if locks[i] else Channel(owner, i, f) for i in range(3)]
            self.items.append((owner, lin, chans))

    def __bool__(self):
        return bool(self.items)

    def apply(self, d_world):
        for _owner, lin, chans in self.items:
            dl = lin @ d_world
            for i, ch in enumerate(chans):
                if ch is not None:
                    ch.apply(dl[i])

    def restore(self):
        for _owner, _lin, chans in self.items:
            for ch in chans:
                if ch is not None:
                    ch.restore()

    def owners(self):
        seen, out = set(), []
        for owner, _lin, _c in self.items:
            if owner.key not in seen:
                seen.add(owner.key)
                out.append(owner)
        return out


def update_paths(context, owners_):
    """Recalculate the motion paths of these owners."""
    obs = [o.ob for o in owners_ if o.pb is None]
    bones = [o for o in owners_ if o.pb is not None]
    try:
        if obs:
            with context.temp_override(selected_objects=obs, selected_editable_objects=obs, active_object=obs[0],
                                       object=obs[0]):
                bpy.ops.object.paths_update()
        if bones:
            arm = bones[0].ob
            with context.temp_override(active_object=arm, object=arm):
                bpy.ops.pose.paths_update()
    except RuntimeError:
        pass


# --- operator -----------------------------------------------------------------------------------------------------

class ALLSET_OT_motion_trail_key(bpy.types.Operator):
    """Pick a key on a motion trail and drag it to move the object's location keys at that frame"""
    bl_idname = "allset.motion_trail_key"
    bl_label = "Move Motion Trail Key"
    bl_options = {'UNDO', 'INTERNAL'}

    mode: EnumProperty(items=_MODES, options={'SKIP_SAVE'})

    def invoke(self, context, event):
        if context.region is None or context.region_data is None or not is_maya_view(context):
            return {'PASS_THROUGH'}
        x, y = event.mouse_region_x, event.mouse_region_y
        try:
            hit = pick(context, x, y)
        except (AttributeError, ReferenceError, RuntimeError, ValueError):
            hit = None
        if hit is None:
            if self.mode == 'SET' and _picked:
                _picked.clear()
                _redraw(context)
            return {'PASS_THROUGH'}
        select(hit, self.mode)
        _redraw(context)
        entry = (hit[0][0], hit[0][1], hit[1])
        if entry not in _picked:
            return {'CANCELLED'}            # toggled / removed: nothing to drag
        self._keys = [((o, b), f) for o, b, f in _picked]
        self._entry, self._mode = entry, self.mode
        self._region = context.region
        self._press = (x, y)
        self._anchor = None
        for f, co in markers(owner_of(hit[0]), context.scene):
            if f == hit[1]:
                self._anchor = co
        self._move = None
        self._moved = False
        self._last_update = 0.0
        self._drag_px = max(1, context.preferences.inputs.drag_threshold_mouse) * ui_scale(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _world(self, context, x, y):
        from bpy_extras.view3d_utils import region_2d_to_location_3d
        return region_2d_to_location_3d(self._region, context.region_data, (x, y), self._anchor)

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
            if self._move is not None and self._moved:
                self._move.restore()
                update_paths(context, self._move.owners())
            _redraw(context)
            return {'CANCELLED'}
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            x, y = event.mouse_x - self._region.x, event.mouse_y - self._region.y
            if not self._moved and max(abs(x - self._press[0]), abs(y - self._press[1])) < self._drag_px:
                return {'RUNNING_MODAL'}        # not a drag yet: a click only picks
            if self._move is None:
                self._move = KeyMove(context, self._keys)
                for msg in self._move.errors:
                    self.report({'WARNING'}, msg)
            if not self._move or self._anchor is None:
                return {'RUNNING_MODAL'}
            self._moved = True
            d = self._world(context, x, y) - self._world(context, *self._press)
            self._move.apply(d)
            now = time.perf_counter()
            if now - self._last_update >= UPDATE_S:
                self._last_update = now
                update_paths(context, self._move.owners())
            _redraw(context)
            return {'RUNNING_MODAL'}
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self._moved:
                update_paths(context, self._move.owners())
            elif self._mode == 'SET':
                _picked[:] = [self._entry]          # a plain click on one of several picked keys keeps only it
            _redraw(context)
            return {'FINISHED'} if self._moved else {'CANCELLED'}
        return {'RUNNING_MODAL'}


def _redraw(context):
    screen = getattr(context, "screen", None)
    if screen is None:
        return
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


# --- drawing: the picked keys -------------------------------------------------------------------------------------

def _draw_picked():
    if not _picked:
        return
    context = bpy.context
    try:
        if not is_maya_view(context):
            return
        from bpy_extras.view3d_utils import location_3d_to_region_2d
        region, rv3d = context.region, context.region_data
        scene = context.scene
        live = {o.key: o for o in owners(context)}
        pts = []
        for ob_name, bone, f in _picked:
            owner = live.get((ob_name, bone))
            if owner is None:
                continue
            for ff, co in markers(owner, scene):
                if ff == f:
                    p = location_3d_to_region_2d(region, rv3d, co)
                    if p is not None:
                        pts.append(p)
        if not pts:
            return
        colour = tuple(scene.allset_motion_trail.selected_key_color) + (1.0,)
        half = MARK_PX * ui_scale(context)
    except (AttributeError, ReferenceError, KeyError, ValueError, RuntimeError, TypeError):
        return
    import gpu
    from gpu_extras.batch import batch_for_shader
    tris = []
    for p in pts:
        a, b = (p.x - half, p.y - half), (p.x + half, p.y - half)
        c, d = (p.x + half, p.y + half), (p.x - half, p.y + half)
        tris += [a, b, c, a, c, d]
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader.uniform_float("color", colour)
    batch_for_shader(shader, 'TRIS', {"pos": tris}).draw(shader)


@bpy.app.handlers.persistent
def _on_load_pre(*_args):
    _picked.clear()


classes = (ALLSET_OT_motion_trail_key,)


def register_handlers():
    if not _draw:
        _draw.append(bpy.types.SpaceView3D.draw_handler_add(_draw_picked, (), 'WINDOW', 'POST_PIXEL'))
    if _on_load_pre not in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.append(_on_load_pre)


def unregister_handlers():
    while _draw:
        bpy.types.SpaceView3D.draw_handler_remove(_draw.pop(), 'WINDOW')
    if _on_load_pre in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.remove(_on_load_pre)
    _picked.clear()
