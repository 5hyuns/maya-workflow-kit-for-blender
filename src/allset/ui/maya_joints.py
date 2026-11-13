# SPDX-License-Identifier: GPL-3.0-or-later
"""Joints drawn like Maya's in the Maya layout's 3D Views, in place of Blender's bone shapes.

Maya draws a joint as a wire sphere of three great circles in the joint's local XY, YZ and XZ planes, never filled,
1 px lines, at pure world size: the drawn radius is half the joint's Radius times the scene's Joint Size, with no
screen-size limit. Between a joint and each child it draws a wire four-sided pyramid: the square base stands across
the bone on the parent's sphere, turned with the parent's axes, its corners on that sphere; the apex touches the
child's sphere. A joint without children draws no bone.

Colours follow the selection: unselected joints dark violet, selected ones white, the lead (last selected) green; a
joint below a selected one takes that joint's colour, and a bone takes its parent joint's colour. A joint in a Template
display layer draws grey and in a Reference layer black (unless it is selected itself); a joint a display layer hides,
or one below a joint whose Visibility is off, is not drawn, but the bone from its shown parent joint stays (it belongs
to the parent). Joints a layer hides or makes Template / Reference, and joints Blender can't select, are never picked.
Selected joints in a perspective view also show short local axes (X red, Y green, Z blue). A shaded surface hides the
joints behind or inside it; X-Ray Joints, X-Ray and wireframe views draw them through every surface.

Here a skeleton's joints are its bones' heads (pose positions in Object / Pose Mode, edit bones in Edit Mode); in
Object Mode a selected skeleton object counts as its root joints selected. Bones with a custom shape draw that shape
instead. The skeleton's Blender display type picks the look: Octahedral (Blender's default for a new skeleton) draws
Maya joints; Stick or Wire one line per bone and no spheres; B-Bone a wire box per bone (per segment, following the
curve) and Envelope the wire head and tail spheres joined along the bone, both in the joint colours. The kit draws
only in 3D Views of the Maya layout's workspaces where Blender's Bones overlay is off — the kit turns it off once per
screen; a view whose Bones overlay is turned back on shows Blender's bones and no kit joints.
"""

import math

import bpy
from mathutils import Matrix, Quaternion, Vector

UNSELECTED = (0x26 / 255, 0.0, 0x43 / 255)
SELECTED = (1.0, 1.0, 1.0)
LEAD = (0x43 / 255, 1.0, 0xa3 / 255)
AXIS_COLORS = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
SEGMENTS = 32
LINE_PX = 1.0
SETTLED = "allset_bones_settled"      # screen ID prop: the kit turned Blender's Bones overlay off in its 3D Views
MAYA_RADIUS = 1.0                     # Maya joint Radius default
STICK_TYPES = {'STICK', 'WIRE'}       # the skeleton's Blender display type: one line per bone, no spheres
SHAPE_TYPES = {'BBONE', 'ENVELOPE'}   # display types drawn as wire versions of Blender's bone shapes

_HIDDEN = "HIDDEN"                    # ui/layer_joints.HIDDEN
_handle = []
_GEN = [0]          # bumped by every update that can change a drawn joint
_CACHE = {}         # space pointer -> (key, points, colours)
_COS = [math.cos(2.0 * math.pi * i / SEGMENTS) for i in range(SEGMENTS)]
_SIN = [math.sin(2.0 * math.pi * i / SEGMENTS) for i in range(SEGMENTS)]


# --- which views ------------------------------------------------------------------------------------------------

def maya_workspace(workspace):
    from .. import switch
    try:
        return switch.is_maya_workspace(workspace)
    except (ReferenceError, AttributeError):
        return False


def is_maya_view(space, workspace):
    """A 3D View where the kit draws the joints (and Blender's bones are off)."""
    from . import toolbox
    return (space is not None and workspace is not None and space.type == 'VIEW_3D' and not toolbox.is_toolbox(space)
            and space.overlay.show_overlays and not space.overlay.show_bones
            and space.show_object_viewport_armature and maya_workspace(workspace))


def settle(window):
    """Turn Blender's Bones overlay off in the 3D Views of ``window``'s screen once (Maya layout workspaces only)."""
    from . import toolbox
    screen = window.screen
    # temporary screens (Preferences, file browser windows) can't be a context override and hold no 3D View
    if screen is None or screen.is_temporary or screen.get(SETTLED) or not maya_workspace(window.workspace):
        return False
    changed = False
    with bpy.context.temp_override(window=window, screen=screen):
        for area in screen.areas:
            space = area.spaces.active
            if area.type == 'VIEW_3D' and not toolbox.is_toolbox(space) and space.overlay.show_bones:
                space.overlay.show_bones = False
                area.tag_redraw()
                changed = True
    screen[SETTLED] = True
    return changed


def release_all():
    """Give Blender's bones back in every screen the kit settled (disable / Maya mode off)."""
    from . import toolbox
    for screen in bpy.data.screens:
        if not screen.get(SETTLED):
            continue
        for area in screen.areas:
            space = area.spaces.active
            if area.type == 'VIEW_3D' and not toolbox.is_toolbox(space):
                space.overlay.show_bones = True
                area.tag_redraw()
        del screen[SETTLED]


def _tick():
    try:
        for window in bpy.context.window_manager.windows:
            settle(window)
    except (ReferenceError, AttributeError, RuntimeError):
        pass
    return 0.5


# --- joints ------------------------------------------------------------------------------------------------------

def drawn_radius(bone, scene, arm_scale=1.0):
    """World radius of the drawn joint sphere: 0.5 x Radius x Joint Size, in centimetres (``units.radius_unit``)."""
    from ..operators import joint_display, joints, units
    r = float(bone.get(joints.RADIUS, MAYA_RADIUS))
    size = joint_display.joint_size(scene)
    return 0.5 * r * size * units.radius_unit(scene) * arm_scale


def _maya_q(bone):
    from ..operators import joints
    q = bone.get(joints.MAYA_FRAME)
    return Quaternion(q).to_matrix() if q is not None else None


class Joint:
    __slots__ = ("name", "parent", "centre", "frame", "radius", "shape", "children", "state")

    def __init__(self, name, parent, centre, frame, radius, shape=None, state=None):
        self.name, self.parent, self.centre, self.frame, self.radius = name, parent, centre, frame, radius
        self.shape = shape          # (custom shape object, world matrix) or None
        self.children = []
        self.state = state          # ui/layer_joints: HIDDEN (not drawn) / TEMPLATE / REFERENCE, None = normal


def skeleton(ob, scene):
    """{name: Joint} of armature object ``ob`` in world space: the joints not hidden by their own flags, with their
    display layer state (a joint a layer hides is kept for its parent's bone, ``joint_segments`` draws nothing for
    it)."""
    from .. import compat
    from ..operators import joints
    from ..operators.joint_edit import local_frame
    from . import layer_joints
    layered = layer_joints.state(ob)
    mw = ob.matrix_world
    m3 = mw.to_3x3()
    s = max(mw.to_scale())
    out = {}
    if ob.mode == 'EDIT':
        for eb in ob.data.edit_bones:
            if eb.hide or _coll_hidden(eb):
                continue
            frame = (m3 @ local_frame(eb)).normalized()
            out[eb.name] = Joint(eb.name, eb.parent.name if eb.parent else None, mw @ eb.head, frame,
                                 drawn_radius(eb, scene, s), state=layered.get(eb.name))
    else:
        for pb in ob.pose.bones:
            bone = pb.bone
            if compat.bone_hidden(pb) or _coll_hidden(bone):
                continue
            f = m3 @ pb.matrix.to_3x3() @ joints.JOINT_AXES
            q = _maya_q(bone)
            frame = (f @ q if q is not None else f).normalized()
            shape = None
            if pb.custom_shape is not None:
                shape = (pb.custom_shape, mw @ _shape_matrix(pb))
            out[pb.name] = Joint(pb.name, bone.parent.name if bone.parent else None, mw @ pb.head, frame,
                                 drawn_radius(bone, scene, s), shape, layered.get(pb.name))
    for j in out.values():
        if j.parent in out:
            out[j.parent].children.append(j.name)
    return out


def _coll_hidden(bone):
    return bool(bone.collections) and not any(c.is_visible_effectively for c in bone.collections)


def _shape_matrix(pb):
    """Armature-space matrix Blender draws ``pb``'s custom shape with."""
    src = pb.custom_shape_transform or pb
    scale = Vector(pb.custom_shape_scale_xyz)
    if pb.use_custom_shape_bone_size:
        scale = scale * pb.bone.length
    return (src.matrix @ Matrix.Translation(pb.custom_shape_translation)
            @ pb.custom_shape_rotation_euler.to_matrix().to_4x4() @ Matrix.Diagonal(scale.to_4d()))


def selection(ob, joints_):
    """(selected joint names, lead name or None) of ``ob`` in Maya's terms."""
    from ..operators import joint_preview
    from ..operators.joint_selection import _edit_selected
    from .channel_box import bone_selected
    if joint_preview.running() and joint_preview.STATE.get("ob") == ob.name:
        cur = joint_preview.STATE.get("current")
        return ({cur} if cur else set()), cur          # the Joint Tool: the newest joint is the selection
    if ob.mode == 'EDIT':
        sel = {eb.name for eb in ob.data.edit_bones if eb.name in joints_ and _edit_selected(eb)}
        act = ob.data.edit_bones.active
    elif ob.mode == 'POSE':
        sel = {pb.name for pb in ob.pose.bones if pb.name in joints_ and bone_selected(pb)}
        act = ob.data.bones.active
    else:
        if not ob.select_get():
            return set(), None
        roots = [n for n, j in joints_.items() if j.parent is None]
        lead = roots[0] if roots and bpy.context.view_layer.objects.active == ob else None
        return set(roots), lead
    lead = act.name if act is not None and act.name in sel else None
    return sel, lead


def colours(joints_, sel, lead):
    """{name: colour}: own selection first, else its Template / Reference layer colour, else the nearest selected
    joint above it, else unselected."""
    from .layer_joints import COLOURS
    out = {}

    def colour(name):
        if name in out:
            return out[name]
        if name == lead:
            c = LEAD
        elif name in sel:
            c = SELECTED
        elif joints_[name].state in COLOURS:
            c = COLOURS[joints_[name].state]
        else:
            p = joints_[name].parent
            c = colour(p) if p in joints_ else UNSELECTED
        out[name] = c
        return c

    for n in joints_:
        colour(n)
    return out


def sphere_lines(c, frame, r):
    """Line segment end points of the three great circles."""
    x, y, z = frame.col[0], frame.col[1], frame.col[2]
    pts = []
    for a, b in ((x, y), (y, z), (x, z)):
        ring = [c + (a * _COS[i] + b * _SIN[i]) * r for i in range(SEGMENTS)]
        for i in range(SEGMENTS):
            pts += (ring[i], ring[(i + 1) % SEGMENTS])
    return pts


def bone_lines(parent, child):
    """The eight edges of the bone pyramid from ``parent`` to ``child`` (Joint), or [] when they overlap."""
    d = child.centre - parent.centre
    length = d.length
    if length <= parent.radius + child.radius or length < 1e-9:
        return []
    u = d / length
    base = parent.centre + u * parent.radius
    apex = child.centre - u * child.radius
    a = parent.frame.col[1] - u * parent.frame.col[1].dot(u)
    if a.length < 1e-6:
        a = parent.frame.col[2] - u * parent.frame.col[2].dot(u)
    a.normalize()
    b = u.cross(a)
    r = parent.radius
    corners = [base + a * r, base + b * r, base - a * r, base - b * r]
    pts = []
    for i in range(4):
        pts += (corners[i], corners[(i + 1) % 4], corners[i], apex)
    return pts


def _box_lines(rings):
    """Edges of a tube through ``rings`` (each four corners): the rings and the lines joining their corners."""
    pts = []
    for k, ring in enumerate(rings):
        for i in range(4):
            pts += (ring[i], ring[(i + 1) % 4])
            if k:
                pts += (rings[k - 1][i], ring[i])
    return pts


def bbone_lines(ob, bone):
    """World edges of Blender's B-Bone box of ``bone`` (pose bone, or edit bone in Edit Mode): ``bbone_x`` /
    ``bbone_z`` half sizes, one box per segment along the bent bone in Object / Pose Mode."""
    mw = ob.matrix_world
    data = bone.bone if isinstance(bone, bpy.types.PoseBone) else bone
    x, z = data.bbone_x, data.bbone_z
    corners = (Vector((x, 0.0, z)), Vector((-x, 0.0, z)), Vector((-x, 0.0, -z)), Vector((x, 0.0, -z)))
    base = mw @ bone.matrix
    frames = []
    if isinstance(bone, bpy.types.PoseBone) and data.bbone_segments > 1:
        try:
            frames = [base @ bone.bbone_segment_matrix(i, rest=False) for i in range(data.bbone_segments + 1)]
        except (RuntimeError, ValueError):
            frames = []
    if not frames:
        frames = [base, base @ Matrix.Translation((0.0, bone.length, 0.0))]
    return _box_lines([[f @ c for c in corners] for f in frames])


def envelope_lines(ob, bone):
    """World edges of Blender's Envelope shape of ``bone``: wire spheres of the head and tail radius joined by four
    lines along the bone."""
    mw = ob.matrix_world
    data = bone.bone if isinstance(bone, bpy.types.PoseBone) else bone
    s = max(mw.to_scale())
    m = mw @ bone.matrix
    frame = m.to_3x3().normalized()
    head, tail = mw @ bone.head, mw @ bone.tail
    rh, rt = data.head_radius * s, data.tail_radius * s
    pts = sphere_lines(head, frame, rh) + sphere_lines(tail, frame, rt)
    for axis in (frame.col[0], -frame.col[0], frame.col[2], -frame.col[2]):
        pts += (head + axis * rh, tail + axis * rt)
    return pts


def own_shape_lines(ob, kind):
    """{bone name: world edges} of every visible bone of ``ob`` drawn as Blender's ``kind`` shape (B-Bone /
    Envelope), custom-shaped bones left out (they draw their shape)."""
    from .. import compat
    from . import layer_joints
    layered = layer_joints.state(ob)       # hidden by a display layer or a hidden joint above: nothing drawn
    fn = bbone_lines if kind == 'BBONE' else envelope_lines
    out = {}
    if ob.mode == 'EDIT':
        for eb in ob.data.edit_bones:
            if not (eb.hide or _coll_hidden(eb) or layered.get(eb.name) == _HIDDEN):
                out[eb.name] = fn(ob, eb)
    else:
        for pb in ob.pose.bones:
            if not (compat.bone_hidden(pb) or _coll_hidden(pb.bone) or pb.custom_shape is not None
                    or layered.get(pb.name) == _HIDDEN):
                out[pb.name] = fn(ob, pb)
    return out


def shape_lines(ob, matrix, depsgraph):
    """World line segments of a custom shape's edges."""
    try:
        ev = ob.evaluated_get(depsgraph)
        me = ev.to_mesh()
    except (RuntimeError, AttributeError):
        return []
    try:
        vs = [matrix @ v.co for v in me.vertices]
        return [vs[i] for e in me.edges for i in e.vertices]
    finally:
        ev.to_mesh_clear()


def joint_segments(js, name, depsgraph=None):
    """World line segments drawn for joint ``name``: its sphere and its bones to the children (a bone belongs to
    its parent joint), or its custom shape; nothing for a joint a display layer hides. Flat list of end points."""
    j = js[name]
    if j.state == _HIDDEN:
        return []
    if j.shape is not None:
        return shape_lines(j.shape[0], j.shape[1], depsgraph) if depsgraph is not None else []
    pts = sphere_lines(j.centre, j.frame, j.radius)
    for cn in j.children:
        if js[cn].shape is None:
            pts += bone_lines(j, js[cn])
    return pts


def depth(js, name):
    n, p = 0, js[name].parent
    while p in js:
        n, p = n + 1, js[p].parent
    return n


def _screen(context, pts):
    """(a, b, ok) screen end points of segments ``pts`` (pairs) in the context region; ok = both in front."""
    from ..operators.preselect import project
    region, rv3d = context.region, context.region_data
    xy, front = project([tuple(p) for p in pts], rv3d.perspective_matrix, region.width, region.height)
    return xy[0::2], xy[1::2], front[0::2] & front[1::2]


def _unpickable(ob, js):
    """Joints of ``js`` that can't be picked: hidden / Template / Reference by a display layer, or Blender's
    unselectable bones."""
    bones = ob.data.edit_bones if ob.mode == 'EDIT' else ob.data.bones
    return {n for n, j in js.items() if j.state is not None or (n in bones and bones[n].hide_select)}


def screen_distance(context, ob, mouse):
    """{joint: screen distance from ``mouse`` to its drawn lines} of armature ``ob``, for the joints that can be
    picked."""
    from ..operators.preselect import segment_distance
    js = skeleton(ob, context.scene)
    dg = context.evaluated_depsgraph_get()
    skip = _unpickable(ob, js)
    out = {}
    for n in js:
        if n in skip:
            continue
        pts = joint_segments(js, n, dg)
        if not pts:
            continue
        a, b, ok = _screen(context, pts)
        if not ok.any():
            continue
        d, _t = segment_distance(mouse, a[ok], b[ok])
        out[n] = float(d.min())
    return out


def pick(context, ob, mouse, radius):
    """The joint of ``ob`` whose drawn line is nearest to ``mouse`` within ``radius`` px (Maya: a click hits the wire,
    not the inside of the sphere; a bone hit picks its parent joint), or None."""
    d = screen_distance(context, ob, mouse)
    near = [(v, n) for n, v in d.items() if v <= radius]
    return min(near)[1] if near else None


def _seg_cross(p1, p2, q1, q2):
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2 = orient(q1, q2, p1), orient(q1, q2, p2)
    d3, d4 = orient(p1, p2, q1), orient(p1, p2, q2)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


def _in_poly(pt, poly):
    x, y = pt
    inside = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def segments_touch(a, b, poly):
    """Does any segment a[i]-b[i] touch the closed polygon ``poly`` (screen points)?"""
    edges = [(poly[i - 1], poly[i]) for i in range(len(poly))]
    for p, q in zip(a, b):
        if _in_poly(p, poly) or _in_poly(q, poly):
            return True
        if any(_seg_cross(p, q, e0, e1) for e0, e1 in edges):
            return True
    return False


def region_pick(context, ob, poly):
    """Maya marquee / lasso on a skeleton: the bones whose drawn lines touch ``poly``. Maya joints keep the one
    closest to the root (a box around a whole chain selects its top joint); controls (bones with a custom shape)
    and bones of a skeleton not drawn as Maya joints are each picked, like Maya's curve controls. Joints that can't be
    picked (``_unpickable``) are left out. Returns names."""
    js = skeleton(ob, context.scene)
    dg = context.evaluated_depsgraph_get()
    maya_drawn = getattr(ob.data, "display_type", 'OCTAHEDRAL') not in STICK_TYPES | SHAPE_TYPES
    skip = _unpickable(ob, js)
    joints, each = [], []
    for n in js:
        if n in skip:
            continue
        pts = joint_segments(js, n, dg)
        if not pts:
            continue
        a, b, ok = _screen(context, pts)
        if ok.any() and segments_touch([tuple(v) for v in a[ok]], [tuple(v) for v in b[ok]], poly):
            if maya_drawn and js[n].shape is None:
                joints.append((depth(js, n), list(js).index(n), n))
            else:
                each.append(n)
    return each + ([min(joints)[2]] if joints else [])


def _sphere_array(js):
    """(points, joint order) of every sphere's three great circles as one float32 array of segment end points."""
    import numpy as np
    order = [n for n, j in js.items() if j.shape is None and j.state != _HIDDEN]
    if not order:
        return np.zeros((0, 3), np.float32), order
    c = np.array([tuple(js[n].centre) for n in order], np.float64)                  # (N, 3)
    f = np.array([[tuple(r) for r in js[n].frame] for n in order], np.float64)      # (N, 3, 3) rows
    r = np.array([js[n].radius for n in order], np.float64)
    return _spheres(c, f, r), order


def _spheres(c, f, r):
    """Segment end points (float32) of the three great circles of spheres at centres ``c`` (N, 3) with frames ``f``
    (N, 3, 3; columns = the joint's X, Y, Z) and radii ``r`` (N,)."""
    import numpy as np
    if _RING[0] is None:
        # every end point of the three circles in the joint's own axes: (3 circles, S segments, 2 ends, xyz)
        t = np.arange(SEGMENTS + 1) * (2.0 * math.pi / SEGMENTS)
        unit = np.zeros((3, SEGMENTS + 1, 3))
        for k, (a, b) in enumerate(((0, 1), (1, 2), (0, 2))):
            unit[k, :, a], unit[k, :, b] = np.cos(t), np.sin(t)
        _RING[0] = np.stack((unit[:, :-1], unit[:, 1:]), axis=2).reshape(-1, 3)      # (3 * S * 2, 3)
    pts = c[:, None, :] + np.matmul(_RING[0], f.transpose(0, 2, 1)) * r[:, None, None]   # (N, 3 * S * 2, 3)
    return pts.reshape(-1, 3).astype(np.float32)


_RING = [None]


def _bone_array(pc, pf, pr, cc, cr):
    """``bone_lines`` for many bones at once: parents' centres / frames / radii (M, 3) (M, 3, 3) (M,) and children's
    centres / radii. Returns (end points (K * 16, 3), the K bones that are drawn) — a bone whose spheres overlap
    draws nothing."""
    import numpy as np
    d = cc - pc
    length = np.linalg.norm(d, axis=1)
    drawn = np.nonzero((length > pr + cr) & (length >= 1e-9))[0]
    if not len(drawn):
        return np.zeros((0, 3), np.float64), drawn
    d, length, pc, pf, pr, cc, cr = d[drawn], length[drawn], pc[drawn], pf[drawn], pr[drawn], cc[drawn], cr[drawn]
    u = d / length[:, None]
    base = pc + u * pr[:, None]
    apex = cc - u * cr[:, None]

    def across(axis):
        v = pf[:, :, axis]
        return v - u * np.sum(v * u, axis=1)[:, None]

    a = across(1)
    flat = np.linalg.norm(a, axis=1) < 1e-6
    if flat.any():
        a[flat] = across(2)[flat]
    n = np.linalg.norm(a, axis=1)[:, None]
    a = np.divide(a, n, out=np.zeros_like(a), where=n > 0)
    b = np.cross(u, a)
    ar, br = a * pr[:, None], b * pr[:, None]
    corners = np.stack((base + ar, base + br, base - ar, base - br), axis=1)            # (K, 4, 3)
    nxt = np.roll(corners, -1, axis=1)
    tip = np.broadcast_to(apex[:, None, :], corners.shape)
    pts = np.stack((corners, nxt, corners, tip), axis=2)                                # (K, 4, 4, 3)
    return pts.reshape(-1, 3), drawn


class JointList:
    """What a pose doesn't change of a skeleton's drawn joints (Object / Pose Mode)."""
    __slots__ = ("js", "names", "rows", "parents", "raw", "turned", "shaped", "plain", "ctrl", "ctrl_src",
                 "ctrl_len", "ctrl_shapes", "bone_par", "bone_child", "widgets", "bone_rows", "shown", "tint")


def _joint_list(ob):
    """What a pose doesn't change of skeleton ``ob``'s drawn joints: joints {name: Joint, geometry left out}, names,
    their pose bone rows, parent index per joint (-1: no drawn parent), Radius values, {index: Maya frame turn
    (3, 3)}, {index: custom shape object}; for the controls (bones with a custom shape) the pose bone row their shape
    follows and their rest length; the drawn bones (parent, child) between joints without a custom shape."""
    import numpy as np
    from .. import compat
    from ..operators import joints
    from . import layer_joints
    layered = layer_joints.state(ob)
    pbs = ob.pose.bones
    js, names, keep, raw, turned, shaped, src, blen = {}, [], [], [], {}, {}, [], []
    for i, pb in enumerate(pbs):
        bone = pb.bone
        if compat.bone_hidden(pb) or _coll_hidden(bone):
            continue
        name, parent = pb.name, bone.parent
        if pb.custom_shape is not None:
            shaped[len(keep)] = pb.custom_shape
            t = pb.custom_shape_transform
            row = pbs.find(t.name) if t is not None else i
            src.append(row if row >= 0 else i)
            blen.append(bone.length)
        q = bone.get(joints.MAYA_FRAME)
        if q is not None:
            turned[len(keep)] = np.array(Quaternion(q).to_matrix(), np.float64)
        js[name] = Joint(name, parent.name if parent else None, None, None, None, state=layered.get(name))
        names.append(name)
        keep.append(i)
        raw.append(float(bone.get(joints.RADIUS, MAYA_RADIUS)))
    index = {nm: j for j, nm in enumerate(names)}
    jl = JointList()
    jl.js, jl.names, jl.rows, jl.raw = js, names, np.asarray(keep, np.intp), np.asarray(raw, np.float64)
    jl.parents = np.array([index.get(js[nm].parent, -1) for nm in names], np.intp)
    jl.turned, jl.shaped = turned, shaped
    jl.plain = np.ones(len(names), bool)
    jl.ctrl = np.fromiter(shaped, np.intp, len(shaped))
    jl.plain[jl.ctrl] = False
    jl.ctrl_src = np.asarray(src, np.intp)
    jl.ctrl_len = np.asarray(blen, np.float64)
    jl.ctrl_shapes = list(shaped.values())
    # a joint a display layer hides draws nothing, but the bone from its shown parent stays (the parent's)
    jl.shown = np.array([js[nm].state != layer_joints.HIDDEN for nm in names], bool)
    jl.tint = {j: (*layer_joints.COLOURS[js[nm].state], 1.0) for j, nm in enumerate(names)
               if js[nm].state in layer_joints.COLOURS}
    child = np.nonzero(jl.parents >= 0)[0]
    child = child[jl.plain[child] & jl.plain[jl.parents[child]] & jl.shown[jl.parents[child]]]
    par = jl.parents[child]
    order = np.lexsort((child, par))           # a bone belongs to its parent joint: parent by parent
    jl.bone_child, jl.bone_par = child[order], par[order]
    jl.widgets = None                          # the controls' shape lines in their own space (``_control_lines``)
    jl.bone_rows = None                        # rows of the joints in ``ob.data.bones`` (``_bone_rows``)
    return jl


_LISTS = {}     # skeleton object pointer -> (key, _joint_list) kept while playback runs
_EDITS = [0]    # bumped by every change that can change a skeleton's joint list (not by a new frame)
_WIDGETS = {}   # custom shape object session uid -> (its data pointer, its edges' end points in its own space)


def joint_list(ob, playing=False):
    """``_joint_list`` of ``ob``. While playback runs only the pose changes from frame to frame, so the list read
    on the first frame is used again until something is edited (a depsgraph update, undo, a Radius typed)."""
    key = (_EDITS[0], ob.data.as_pointer(), len(ob.pose.bones))
    got = _LISTS.get(ob.as_pointer())
    if playing and got is not None and got[0] == key:
        return got[1]
    out = _joint_list(ob)
    if playing:
        if len(_LISTS) > 32:
            _LISTS.clear()
        _LISTS[ob.as_pointer()] = (key, out)
    else:
        _LISTS.pop(ob.as_pointer(), None)
    return out


def _bone_rows(ob, jl):
    """Row of every joint of ``jl`` in ``ob.data.bones`` (its order can differ from the pose bones')."""
    import numpy as np
    if jl.bone_rows is None:
        index = {b.name: i for i, b in enumerate(ob.data.bones)}
        jl.bone_rows = np.array([index[nm] for nm in jl.names], np.intp)
    return jl.bone_rows


def _pose_read(ob, scene, jl):
    """(world matrix (4, 4), every pose bone's armature-space matrix (n, 4, 4), and the drawn joints' centres (N, 3),
    frames (N, 3, 3; columns normalised) and radii (N,)) of skeleton ``ob`` — one read of the pose for all joints."""
    import numpy as np
    from ..operators import joint_display, joints, units
    pbs = ob.pose.bones
    n = len(pbs)
    mw = ob.matrix_world
    k = 0.5 * joint_display.joint_size(scene) * units.radius_unit(scene) * max(mw.to_scale())
    mat = np.empty(n * 16, np.float32)
    pbs.foreach_get("matrix", mat)
    head = np.empty(n * 3, np.float32)
    pbs.foreach_get("head", head)
    allm = mat.reshape(n, 4, 4).transpose(0, 2, 1).astype(np.float64)       # stored by columns
    w = np.array(mw, np.float64)
    m3 = w[:3, :3]
    rows = jl.rows
    centres = head.reshape(n, 3)[rows].astype(np.float64) @ m3.T + w[:3, 3]
    frames = m3 @ allm[rows][:, :3, :3] @ np.array(joints.JOINT_AXES, np.float64)
    for j, q in jl.turned.items():
        frames[j] = frames[j] @ q
    norms = np.linalg.norm(frames, axis=1, keepdims=True)
    frames = np.divide(frames, norms, out=np.zeros_like(frames), where=norms > 0)
    return w, allm, centres, frames, jl.raw * k


def _pose_arrays(ob, scene, playing=False):
    """The visible joints of ``ob`` in Object / Pose Mode: (joints {name: Joint, geometry left out}, names, parent
    index per joint (-1: no drawn parent), centres (N, 3), frames (N, 3, 3), radii (N,), {index: (custom shape,
    world matrix)}) — the same joints, centres, frames (columns normalised) and radii as ``skeleton``."""
    import numpy as np
    jl = joint_list(ob, playing)
    if not jl.names:
        return jl.js, jl.names, jl.parents, np.zeros((0, 3)), np.zeros((0, 3, 3)), jl.raw, {}
    _w, _allm, centres, frames, radii = _pose_read(ob, scene, jl)
    pbs, mw = ob.pose.bones, ob.matrix_world
    shapes = {j: (shape, mw @ _shape_matrix(pbs[int(jl.rows[j])])) for j, shape in jl.shaped.items()}
    return jl.js, jl.names, jl.parents, centres, frames, radii, shapes


def _joint_selection(ob, jl):
    """``selection`` of ``ob``; in Pose Mode the selected bones are read in one call."""
    import numpy as np
    from ..operators import joint_preview
    if ob.mode != 'POSE' or (joint_preview.running() and joint_preview.STATE.get("ob") == ob.name):
        return selection(ob, jl.js)
    pbs = ob.pose.bones
    flags = np.zeros(len(pbs), bool)
    pbs.foreach_get("select", flags)
    sel = {jl.names[j] for j in np.nonzero(flags[jl.rows])[0]}
    act = ob.data.bones.active
    return sel, (act.name if act is not None and act.name in sel else None)


def _joint_rgba(jl, sel, lead):
    """(N, 4) colour of every joint (``colours``); nothing selected: all unselected."""
    import numpy as np
    if not sel:
        rgba = np.tile(np.array((*UNSELECTED, 1.0), np.float32), (len(jl.names), 1))
        for j, c in jl.tint.items():           # Template / Reference layer colour
            rgba[j] = c
        return rgba
    col = colours(jl.js, sel, lead)
    return np.array([(*col[nm], 1.0) for nm in jl.names], np.float32)


def _read_widget(shape, depsgraph):
    """(2E, 3) end points of the edges of custom shape object ``shape``'s evaluated geometry, in its own space."""
    import numpy as np
    try:
        ev = shape.evaluated_get(depsgraph)
        me = ev.to_mesh()
    except (RuntimeError, AttributeError, ReferenceError):
        return np.zeros((0, 3))
    try:
        if me is None:
            return np.zeros((0, 3))
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        ed = np.empty(len(me.edges) * 2, np.int32)
        me.edges.foreach_get("vertices", ed)
        return co.reshape(-1, 3).astype(np.float64)[ed]
    finally:
        ev.to_mesh_clear()


# modifiers that only reshape the object's own geometry: unkeyed, their result can't change with the frame
_STILL_MODIFIERS = frozenset({'SUBSURF', 'MULTIRES', 'TRIANGULATE', 'EDGE_SPLIT', 'WELD', 'SOLIDIFY', 'BEVEL',
                              'WIREFRAME'})


def shape_moves(shape):
    """Can custom shape ``shape``'s geometry change with the frame? Shape keys, particles, animated or driven data,
    a modifier that can read the time or other objects, or a keyed / driven modifier setting. A Subdivision Surface
    (Bevel, Solidify ...) modifier alone can't."""
    if getattr(shape, "particle_systems", None):
        return True
    if shape.modifiers and (shape.animation_data is not None
                            or any(m.type not in _STILL_MODIFIERS for m in shape.modifiers)):
        return True
    data = shape.data
    return data is not None and (getattr(data, "shape_keys", None) is not None or data.animation_data is not None)


def _widget_segments(shape, depsgraph):
    """(``_read_widget`` of ``shape``, changes with the frame). A shape whose geometry can't change with the frame is
    read once and kept until something is edited (``changed``) or undone; one that can (``shape_moves``) is read
    every time."""
    uid, data = shape.session_uid, shape.data
    dptr = data.as_pointer() if data is not None else 0
    got = _WIDGETS.get(uid)
    if got is not None and got[0] == dptr:
        return got[1], False
    segs = _read_widget(shape, depsgraph)
    if shape_moves(shape):
        return segs, True
    _WIDGETS[uid] = (dptr, segs)
    return segs, False


def _euler_xyz(e):
    """(K, 3) XYZ Euler angles -> (K, 3, 3) rotation matrices (``Euler.to_matrix``)."""
    import numpy as np
    cx, cy, cz = np.cos(e[:, 0]), np.cos(e[:, 1]), np.cos(e[:, 2])
    sx, sy, sz = np.sin(e[:, 0]), np.sin(e[:, 1]), np.sin(e[:, 2])
    m = np.empty((len(e), 3, 3))
    m[:, 0, 0], m[:, 0, 1], m[:, 0, 2] = cy * cz, sx * sy * cz - cx * sz, cx * sy * cz + sx * sz
    m[:, 1, 0], m[:, 1, 1], m[:, 1, 2] = cy * sz, sx * sy * sz + cx * cz, cx * sy * sz - sx * cz
    m[:, 2, 0], m[:, 2, 1], m[:, 2, 2] = -sy, sx * cy, cx * cy
    return m


def _control_lines(ob, jl, w, allm, rgba, depsgraph):
    """(points, colours) of every control's custom shape (``shape_lines`` with ``_shape_matrix``, all controls at
    once), or None. The shapes' own lines are joined once per joint list; the pose and the custom shape
    offset / turn / scale (they can be keyed) are read every time."""
    import numpy as np
    plan = jl.widgets
    if plan is not None and plan[3]:
        p = plan[0]
        for shape, start, count in plan[3]:          # shapes that change with the frame: read again in place
            segs = _read_widget(shape, depsgraph)
            if len(segs) != count:
                plan = None                          # a new edge count: join every shape again
                break
            p[start:start + count] = segs
    if plan is None:
        segs, moving, start = [], [], 0
        for shape in jl.ctrl_shapes:
            s, m = _widget_segments(shape, depsgraph)
            if m:
                moving.append((shape, start, len(s)))
            segs.append(s)
            start += len(s)
        counts = np.fromiter((len(s) for s in segs), np.intp, len(segs))
        p = np.concatenate(segs) if counts.sum() else np.zeros((0, 3))
        plan = jl.widgets = (p, np.repeat(np.arange(len(segs)), counts), counts, moving)
    p, owner, counts, _moving = plan
    if not len(p):
        return None
    pbs = ob.pose.bones
    n = len(pbs)
    rows = jl.rows[jl.ctrl]
    got = {}
    for prop in ("custom_shape_translation", "custom_shape_rotation_euler", "custom_shape_scale_xyz"):
        a = np.empty(n * 3, np.float32)
        pbs.foreach_get(prop, a)
        got[prop] = a.reshape(n, 3)[rows].astype(np.float64)
    use = np.zeros(n, bool)
    pbs.foreach_get("use_custom_shape_bone_size", use)
    scale = got["custom_shape_scale_xyz"] * np.where(use[rows], jl.ctrl_len, 1.0)[:, None]
    src = allm[jl.ctrl_src]
    a = w[:3, :3] @ src[:, :3, :3]
    lin = a @ (_euler_xyz(got["custom_shape_rotation_euler"]) * scale[:, None, :])
    off = (a @ got["custom_shape_translation"][:, :, None])[:, :, 0] + src[:, :3, 3] @ w[:3, :3].T + w[:3, 3]
    pts = np.einsum('kij,kj->ki', lin[owner], p) + off[owner]
    cols = np.repeat(rgba[jl.ctrl], counts, axis=0)
    if not jl.shown.all():                     # controls a display layer hides draw nothing
        keep = jl.shown[jl.ctrl][owner]
        pts, cols = pts[keep], cols[keep]
    return pts.astype(np.float32), cols


def _box_array(frames, corners):
    """``_box_lines`` of many tubes with the same number of rings: frames (K, F, 4, 4) of each ring, corners
    (K, 4, 3) of each tube in its rings' space. Returns (K, 8 + 16 * (F - 1), 3) end points per tube."""
    import numpy as np
    rings = np.einsum('kfij,kcj->kfci', frames[:, :, :3, :3], corners) + frames[:, :, None, :3, 3]
    edges = np.stack((rings, np.roll(rings, -1, axis=2)), axis=3)                 # (K, F, 4, 2, 3)
    k = len(rings)
    first = edges[:, 0].reshape(k, -1, 3)
    if rings.shape[1] < 2:
        return first
    joins = np.stack((rings[:, :-1], rings[:, 1:]), axis=3)                       # (K, F - 1, 4, 2, 3)
    rest = np.stack((edges[:, 1:], joins), axis=3).reshape(k, -1, 3)             # ring edge i, then join i
    return np.concatenate((first, rest), axis=1)


def _own_lines(ob, jl, w, allm, rgba, kind):
    """(points, colours) of Blender's B-Bone / Envelope ``kind`` shape of every drawn joint without a custom shape
    (``bbone_lines`` / ``envelope_lines`` in joint order), or None."""
    import numpy as np
    plain = np.nonzero(jl.plain & jl.shown)[0]
    if not len(plain):
        return None
    pbs, bones = ob.pose.bones, ob.data.bones
    n, nb = len(pbs), len(bones)
    rows, brows = jl.rows[plain], _bone_rows(ob, jl)[plain]
    w3, wt = w[:3, :3], w[:3, 3]
    m = allm[rows]

    def bone_values(prop, dtype=np.float32):
        a = np.empty(nb, dtype)
        bones.foreach_get(prop, a)
        return a[brows].astype(np.float64)

    if kind == 'ENVELOPE':
        hd, tl = np.empty(n * 3, np.float32), np.empty(n * 3, np.float32)
        pbs.foreach_get("head", hd)
        pbs.foreach_get("tail", tl)
        s = max(ob.matrix_world.to_scale())
        f = w3 @ m[:, :3, :3]
        norms = np.linalg.norm(f, axis=1, keepdims=True)
        f = np.divide(f, norms, out=np.zeros_like(f), where=norms > 0)
        h = hd.reshape(n, 3)[rows].astype(np.float64) @ w3.T + wt
        t = tl.reshape(n, 3)[rows].astype(np.float64) @ w3.T + wt
        rh, rt = bone_values("head_radius") * s, bone_values("tail_radius") * s
        k = len(rows)
        ax = np.stack((f[:, :, 0], -f[:, :, 0], f[:, :, 2], -f[:, :, 2]), axis=1)          # (K, 4, 3)
        joins = np.stack((h[:, None] + ax * rh[:, None, None], t[:, None] + ax * rt[:, None, None]), axis=2)
        pts = np.concatenate((_spheres(h, f, rh).reshape(k, -1, 3), _spheres(t, f, rt).reshape(k, -1, 3),
                              joins.reshape(k, -1, 3)), axis=1)
        return pts.reshape(-1, 3).astype(np.float32), np.repeat(rgba[plain], pts.shape[1], axis=0)
    # B-Bone: one box per segment along the bent bone, a straight box for one segment
    x, z, segments = bone_values("bbone_x"), bone_values("bbone_z"), bone_values("bbone_segments", np.int32)
    length = np.empty(n, np.float32)
    pbs.foreach_get("length", length)
    zero = np.zeros_like(x)
    corners = np.stack((np.stack((x, zero, z), 1), np.stack((-x, zero, z), 1), np.stack((-x, zero, -z), 1),
                        np.stack((x, zero, -z), 1)), axis=1)                           # (K, 4, 3)
    base = w @ m
    tip = base.copy()
    tip[:, :3, 3] += base[:, :3, 1] * length[rows][:, None]
    straight = np.stack((base, tip), axis=1)                                            # (K, 2, 4, 4)
    bent = {}
    for k in np.nonzero(segments > 1)[0]:
        pb = pbs[int(rows[k])]
        try:
            bent[int(k)] = np.array([np.array(pb.bbone_segment_matrix(i, rest=False), np.float64)
                                     for i in range(int(segments[k]) + 1)])
        except (RuntimeError, ValueError):
            continue
    if not bent:
        pts = _box_array(straight, corners)
        return pts.reshape(-1, 3).astype(np.float32), np.repeat(rgba[plain], pts.shape[1], axis=0)
    blocks = [None] * len(rows)
    rest = np.array([k for k in range(len(rows)) if k not in bent], np.intp)
    if len(rest):
        for k, b in zip(rest, _box_array(straight[rest], corners[rest])):
            blocks[k] = b
    by_rings = {}
    for k, fr in bent.items():
        by_rings.setdefault(len(fr), []).append(k)
    for ks in by_rings.values():
        frames = base[ks][:, None] @ np.array([bent[k] for k in ks])
        for k, b in zip(ks, _box_array(frames, corners[ks])):
            blocks[k] = b
    sizes = [len(b) for b in blocks]
    return np.concatenate(blocks).astype(np.float32), np.repeat(rgba[plain], sizes, axis=0)


def _parts(ob, scene, depsgraph, kind=None, playing=False):
    """Every line of skeleton ``ob`` as three parts (points list, colours list): the joints' spheres and the
    controls' shapes; the local axes of the selected joints (drawn in perspective views only); the bones (pyramids,
    sticks, or Blender's B-Bone / Envelope shapes). ``kind`` = the display type (default: the skeleton's). Object
    and Pose Mode build them in arrays from one read of the pose; Edit Mode joint by joint."""
    import numpy as np
    if kind is None:
        kind = getattr(ob.data, "display_type", 'OCTAHEDRAL')
    if ob.mode == 'EDIT':
        return _joint_parts(ob, scene, depsgraph, kind)
    before, axes, after = ([], []), ([], []), ([], [])
    jl = joint_list(ob, playing)
    if not jl.names:
        return before, axes, after
    stick, own = kind in STICK_TYPES, kind in SHAPE_TYPES
    w, allm, centres, frames, radii = _pose_read(ob, scene, jl)
    sel, lead = _joint_selection(ob, jl)
    rgba = _joint_rgba(jl, sel, lead)
    plain = jl.plain & jl.shown                # spheres / axes: joints with no custom shape that are shown
    if not (stick or own) and plain.any():
        before[0].append(_spheres(centres[plain], frames[plain], radii[plain]))
        before[1].append(np.repeat(rgba[plain], 3 * SEGMENTS * 2, axis=0))
    if len(jl.ctrl):
        got = _control_lines(ob, jl, w, allm, rgba, depsgraph)
        if got is not None:
            before[0].append(got[0])
            before[1].append(got[1])
    if sel:
        picked = np.array([j for j, nm in enumerate(jl.names) if plain[j] and nm in sel], np.intp)
        if len(picked):
            c = centres[picked]
            ends = c[:, None, :] + frames[picked].transpose(0, 2, 1) * radii[picked][:, None, None]   # (K, 3, 3)
            axes[0].append(np.stack((np.broadcast_to(c[:, None, :], ends.shape), ends), axis=2)
                           .reshape(-1, 3).astype(np.float32))
            axis_rgba = np.array([(*rgb, 1.0) for rgb in AXIS_COLORS], np.float32)
            axes[1].append(np.tile(np.repeat(axis_rgba, 2, axis=0), (len(picked), 1)))
    if own:
        got = _own_lines(ob, jl, w, allm, rgba, kind)
        if got is not None:
            after[0].append(got[0])
            after[1].append(got[1])
    elif len(jl.bone_child):
        child, par = jl.bone_child, jl.bone_par
        if stick:
            segs = np.stack((centres[par], centres[child]), axis=1).reshape(-1, 3)
            owner = np.repeat(par, 2)
        else:
            segs, drawn = _bone_array(centres[par], frames[par], radii[par], centres[child], radii[child])
            owner = np.repeat(par[drawn], 16)
        if len(segs):
            after[0].append(segs.astype(np.float32))
            after[1].append(rgba[owner])
    return before, axes, after


def _joint_parts(ob, scene, depsgraph, kind):
    """``_parts`` joint by joint (``skeleton``): Edit Mode."""
    import numpy as np
    before, axes, after = ([], []), ([], []), ([], [])
    js = skeleton(ob, scene)
    if not js:
        return before, axes, after
    stick, own = kind in STICK_TYPES, kind in SHAPE_TYPES
    sel, lead = selection(ob, js)
    col = colours(js, sel, lead)

    def add(part, segs, colour):
        if segs:
            part[0].append(np.array([tuple(v) for v in segs], np.float32))
            part[1].append(np.tile(np.array((*colour, 1.0), np.float32), (len(segs), 1)))

    spheres, order = _sphere_array(js) if not (stick or own) else (None, ())
    if order:
        before[0].append(spheres)
        before[1].append(np.repeat(np.array([(*col[n], 1.0) for n in order], np.float32), 3 * SEGMENTS * 2,
                                   axis=0))
    bones, bone_cols = [], []
    if own:
        for name, segs in own_shape_lines(ob, kind).items():
            if name in col and js[name].state != _HIDDEN:
                bones += segs
                bone_cols += [col[name]] * len(segs)
    for j in js.values():
        if j.state == _HIDDEN:
            continue                           # hidden by a display layer: only its parent's bone to it stays
        if j.shape is not None:
            add(before, shape_lines(j.shape[0], j.shape[1], depsgraph), col[j.name])
            continue
        for cn in () if own else j.children:
            child = js[cn]
            if child.shape is None:
                segs = [j.centre, child.centre] if stick else bone_lines(j, child)
                bones += segs
                bone_cols += [col[j.name]] * len(segs)
        if j.name in sel:
            for i in range(3):
                add(axes, [j.centre, j.centre + j.frame.col[i] * j.radius], AXIS_COLORS[i])
    if bones:
        after[0].append(np.array([tuple(v) for v in bones], np.float32))
        after[1].append(np.array([(*c, 1.0) for c in bone_cols], np.float32))
    return before, axes, after


def _join(parts, perspective):
    """(points, colours) float32 arrays of the ``_parts`` of several skeletons, the axes only in perspective."""
    import numpy as np
    pts, cols = [], []
    for before, axes, after in parts:
        for part in (before, axes, after) if perspective else (before, after):
            pts += part[0]
            cols += part[1]
    if not pts:
        return np.zeros((0, 3), np.float32), np.zeros((0, 4), np.float32)
    return np.concatenate(pts), np.concatenate(cols)


def _fast_lines(ob, scene, perspective, depsgraph, stick, playing=False, kind=None):
    """(points, colours) lists of float32 arrays of skeleton ``ob`` drawn as ``kind`` (default: Maya joints, or
    sticks with ``stick``): the same lines and colours as the per-joint geometry, built in arrays."""
    before, axes, after = _parts(ob, scene, depsgraph, kind or ('STICK' if stick else 'OCTAHEDRAL'), playing)
    pts, cols = list(before[0]), list(before[1])
    if perspective:
        pts += axes[0]
        cols += axes[1]
    return pts + after[0], cols + after[1]


def _view_skeletons(context, space):
    return [ob for ob in context.visible_objects if ob.type == 'ARMATURE' and ob.visible_in_viewport_get(space)]


def transforming():
    """A transform runs in some window (move / rotate / scale, a manipulator drag): until it ends only poses and
    object transforms change, so what is kept while playback runs can be kept too."""
    from ..operators.manip_scale import TRANSFORM_MODALS
    wm = bpy.context.window_manager
    return wm is not None and any(op.bl_idname.startswith(TRANSFORM_MODALS)
                                  for w in wm.windows for op in w.modal_operators)


def _posing():
    """A transform runs in Object or Pose Mode (not Edit Mode: there it moves points and bones)."""
    return getattr(bpy.context, "mode", None) in {'OBJECT', 'POSE'} and transforming()


def _playing(context):
    """Playback runs or a pose / object is being dragged: the joint lists and control shapes read once are used
    again."""
    screen = getattr(context, "screen", None)
    return (screen is not None and screen.is_animation_playing) or _posing()


def view_lines(context):
    """(points, colours) float32 arrays of every joint to draw in this view."""
    scene, depsgraph = context.scene, context.view_layer.depsgraph
    playing = _playing(context)
    parts = [_parts(ob, scene, depsgraph, None, playing) for ob in _view_skeletons(context, context.space_data)]
    return _join(parts, context.region_data.is_perspective)


@bpy.app.handlers.persistent
def _depsgraph_post(_scene, depsgraph):
    """Drop the cached lines unless the update only touched objects that are no skeleton (a moved mesh). While a
    pose or an object is dragged only the pose changes: the lines are built again, the joint lists and control
    shapes are kept."""
    try:
        if _posing():
            _GEN[0] += 1
            return
        for u in depsgraph.updates:
            ob = u.id
            if isinstance(ob, bpy.types.Object) and ob.type not in {'ARMATURE', 'MESH', 'CURVE', 'EMPTY'}:
                continue
            if isinstance(ob, bpy.types.Object) and ob.type != 'ARMATURE' and not u.is_updated_geometry:
                continue
            changed()
            return
    except (ReferenceError, AttributeError):
        changed()


def changed():
    """Something that can change the drawn joints other than a new frame (an edit, undo, a Radius typed)."""
    _GEN[0] += 1
    _EDITS[0] += 1
    _WIDGETS.clear()


@bpy.app.handlers.persistent
def _frame_post(*_args):
    _GEN[0] += 1


@bpy.app.handlers.persistent
def _reload(*_args):
    changed()
    _LISTS.clear()


_WORLD = [None]   # what the lines in _PARTS / _JOINED were built for: edit generation, frame, scene, view layer, ...
_PARTS = {}       # skeleton object pointer -> its ``_parts``
_JOINED = {}      # (skeletons drawn, perspective) -> [points, colours, GPU batch or None], shared by the views


def _joined(context):
    """[points, colours, batch] of this view. The lines of each skeleton are built once per frame (or edit) and
    shared by every 3D View that shows the same skeletons in the same projection; any skeleton in Edit Mode: built
    every redraw."""
    from ..operators import joint_preview
    space, scene, layer = context.space_data, context.scene, context.view_layer
    if context.mode == 'EDIT_ARMATURE':
        pts, cols = view_lines(context)
        return [pts, cols, None]
    key = (_GEN[0], scene.frame_current, scene.as_pointer(), layer.as_pointer(), joint_preview.running(),
           str(joint_preview.STATE.get("current")))
    if _WORLD[0] != key:
        _WORLD[0] = key
        _PARTS.clear()
        _JOINED.clear()
    obs = _view_skeletons(context, space)
    persp = context.region_data.is_perspective
    shown = (tuple(ob.as_pointer() for ob in obs), persp)
    hit = _JOINED.get(shown)
    if hit is None:
        playing, depsgraph, parts = _playing(context), layer.depsgraph, []
        for ob in obs:
            got = _PARTS.get(ob.as_pointer())
            if got is None:
                got = _PARTS[ob.as_pointer()] = _parts(ob, scene, depsgraph, None, playing)
            parts.append(got)
        hit = _JOINED[shown] = list(_join(parts, persp)) + [None]
    if len(_CACHE) > 32:
        _CACHE.clear()
    _CACHE[space.as_pointer()] = (key + (persp,), hit[0], hit[1])
    return hit


def cached_view_lines(context):
    """``view_lines`` kept until a joint can have changed (any skeleton in Edit Mode: every redraw), shared by the
    views."""
    hit = _joined(context)
    return hit[0], hit[1]


@bpy.app.handlers.persistent
def _save_pre(*_args):
    try:
        release_all()        # a saved file shows Blender's bones when it opens without the kit
    except (ReferenceError, AttributeError, RuntimeError):
        pass


@bpy.app.handlers.persistent
def _save_post(*_args):
    _tick()


def see_through(space):
    """Joints draw over every surface: X-Ray Joints, a wireframe view (no surface hides a joint, like Maya) or
    X-Ray shading."""
    shading = space.shading
    return bool(space.overlay.show_xray_bone or shading.type == 'WIREFRAME' or shading.show_xray)


def _draw():
    context = bpy.context
    try:
        if not is_maya_view(context.space_data, context.window.workspace):
            return
        hit = _joined(context)
    except (ReferenceError, AttributeError, KeyError, ValueError, RuntimeError):
        return
    if not len(hit[0]):
        return
    import gpu
    from gpu_extras.batch import batch_for_shader
    region = context.region
    sh = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
    gpu.state.depth_test_set('NONE' if see_through(context.space_data) else 'LESS_EQUAL')
    gpu.state.depth_mask_set(False)
    gpu.state.blend_set('ALPHA')
    try:
        sh.uniform_float("viewportSize", (region.width, region.height))
        sh.uniform_float("lineWidth", LINE_PX * context.preferences.system.pixel_size)
        if hit[2] is None:          # one batch per set of lines, drawn by every view that shows them
            hit[2] = batch_for_shader(sh, 'LINES', {"pos": hit[0], "color": hit[1]})
        hit[2].draw(sh)
    finally:
        gpu.state.blend_set('NONE')
        gpu.state.depth_test_set('NONE')


def HANDLERS():
    h = bpy.app.handlers
    return ((h.save_pre, _save_pre), (h.save_post, _save_post), (h.depsgraph_update_post, _depsgraph_post),
            (h.frame_change_post, _frame_post), (h.load_post, _reload), (h.undo_post, _reload),
            (h.redo_post, _reload), (h.animation_playback_pre, _reload))


def register():
    if not _handle:
        _handle.append(bpy.types.SpaceView3D.draw_handler_add(_draw, (), 'WINDOW', 'POST_VIEW'))
    if not bpy.app.timers.is_registered(_tick):
        bpy.app.timers.register(_tick, first_interval=0.2, persistent=True)
    for lst, fn in HANDLERS():
        if fn not in lst:
            lst.append(fn)


def unregister():
    for lst, fn in HANDLERS():
        if fn in lst:
            lst.remove(fn)
    _CACHE.clear()
    _LISTS.clear()
    _PARTS.clear()
    _JOINED.clear()
    _WIDGETS.clear()
    _WORLD[0] = None
    if bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)
    while _handle:
        bpy.types.SpaceView3D.draw_handler_remove(_handle.pop(), 'WINDOW')
    try:
        release_all()
    except (ReferenceError, AttributeError, RuntimeError):
        pass
