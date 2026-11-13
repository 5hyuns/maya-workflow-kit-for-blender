# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya's wireframe on selected objects over shading (lead light green, other selected white).

Maya draws every edge of a selected object in the selection colour over its shading;
Blender only outlines it.

The kit draws the edges itself (POST_VIEW):
- Blender's own ``Object.show_wire`` mixes a selected object's colour with the theme's dormant wire colour
  by up to ~19 % depending on how the edge faces the view (#37cf95 = 0.81 lead + 0.19 #000460),
  so it can't give Maya's flat colour; it is also ID data (saved, in undo steps) and shared with the
  smooth preview 2 cage wire (operators/display.py ``_WIRE_FLAG``).
- Here: evaluated mesh edges in a cached batch per object (numpy, ~28 ms for 100k polys, rebuilt only when
  the object's geometry changes), drawn with the object matrix and a small depth bias (no z-fighting).
  Nothing is written to the file.
- The colours are kit-fixed: the user's theme ``object_active`` / ``object_selected`` is Blender's
  orange, since the kit ships no theme.
  LEAD / OTHER = Maya's lead / other selected colours.
- #76: in wireframe shading Maya draws unselected objects in a dark blue dormant
  wire colour (DORMANT); Blender draws them in the
  theme's wire colour (#181818 here). The same pass draws them in DORMANT (the "Selection Wireframe"
  preference covers both).
- #91: a frame change (playback, scrubbing, ``frame_set``) evaluates the depsgraph without a
  ``depsgraph_update_post``, so a skinned / nCloth mesh kept the wire of the first evaluated frame. ``frame_change_post``
  drops the batches of objects whose evaluated shape can depend on time (``time_dependent``: modifiers, shape keys,
  animated data); static meshes keep their batch.
- A selected lattice is drawn too (Blender's own is the theme's orange). Maya draws a selected
  lattice in the same colours as meshes (white, the lead green). Edges = the lattice grid along U / V / W through the evaluated points
  (``co_deform``).
- Maya highlights the whole hierarchy under a selected object: every descendant shape is drawn in the
  colour of its nearest selected ancestor (Maya: group1
  (selected) -> pCube1 white, pCube2 (lead) -> pCube3 green). Without it a child in front of its selected parent hid
  the parent's wire (side view, pCube2 under pCube1 in front of it) — ``highlighted``.
- #330: Rendered shading draws the wire too. Maya highlights a selection in a lit, shadowed view as well,
  and the Maya layout keeps Blender's outline off, so a selection in Rendered shading (EEVEE, Cycles) had no
  highlight at all. The depth test works there: EEVEE writes the view's depth, and for an external engine
  Blender draws a depth pass of the objects while overlays are on. The one rule (``view_draws``) is Blender's
  own for its outline: overlays on. The IPR window's picture turns its overlays off, so it stays clean.
"""

import bpy
from bpy.app.handlers import persistent

TYPES = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}
WIRE_TYPES = TYPES | {'LATTICE'}   # selected wire only (the dormant wireframe colour stays mesh / curve types)
DEPTH_BIAS = 1e-4          # Legacy limit; retained for dormant, X-ray and native Make Live wires.
DEPTH_BIAS_PIXELS = 1.0    # At most one pixel of the bounds' projected depth change.
DEPTH_BIAS_MAX_SPAN = 1 / 16
DEPTH_BIAS_THIN_RATIO = 1 / 8
DEPTH_BIAS_THIN_SPAN = 1 / 4
LEAD = "#43ffa3"           # lead (last selected = Blender's active)
OTHER = "#ffffff"          # other selected objects
DORMANT = "#000460"        # unselected polymesh wire in wireframe shading
# the 3D View's per-type visibility (the Tool Box column hides every type, ui/toolbox.is_toolbox)
TYPE_FLAGS = {'MESH': "show_object_viewport_mesh", 'CURVE': "show_object_viewport_curve",
              'SURFACE': "show_object_viewport_surf", 'FONT': "show_object_viewport_font",
              'META': "show_object_viewport_meta"}

_batches = {}              # object session_uid -> (batch, edge count)
_handle = []
_shader = []
_times = []


def _enabled():
    from .. import preferences
    try:
        return preferences.get().maya_selection_wire
    except (KeyError, AttributeError):
        return False


def _sh():
    if not _shader:
        import gpu
        info = gpu.types.GPUShaderCreateInfo()
        info.push_constant('MAT4', 'mvp')
        info.push_constant('VEC4', 'color')
        info.push_constant('FLOAT', 'bias')
        info.vertex_in(0, 'VEC3', 'pos')
        info.fragment_out(0, 'VEC4', 'fragColor')
        info.vertex_source("void main() { gl_Position = mvp * vec4(pos, 1.0);"
                           " gl_Position.z -= bias * gl_Position.w; }")
        info.fragment_source("void main() { fragColor = color; }")
        _shader.append(gpu.shader.create_from_info(info))
    return _shader[0]


# Modifiers that only move a mesh's points: an object with no others keeps its edges from frame to frame
DEFORM_ONLY = frozenset({'ARMATURE', 'CAST', 'CURVE', 'DISPLACE', 'HOOK', 'LAPLACIANDEFORM', 'LATTICE', 'MESH_DEFORM',
                         'SHRINKWRAP', 'SIMPLE_DEFORM', 'SMOOTH', 'CORRECTIVE_SMOOTH', 'LAPLACIANSMOOTH',
                         'SURFACE_DEFORM', 'WARP', 'WAVE'})
_edges = {}     # object session_uid -> ((vertex count, edge count), edge indices) of a mesh that only deforms


def keeps_edges(ob):
    """A new frame only moves the evaluated mesh's points (shape keys, armature / lattice / ... modifiers): its edges
    stay the same, so playback reads only the points again (reading the edges took several ms a frame)."""
    return (ob.type == 'MESH' and not getattr(ob, "particle_systems", None)
            and all(m.type in DEFORM_ONLY for m in ob.modifiers))


def _positions(me):
    """(N * 3,) float32 point positions of mesh ``me`` (the position attribute: one copy, not a read per vertex)."""
    import numpy as np
    co = np.empty(len(me.vertices) * 3, np.float32)
    pos = me.attributes.get("position")
    if pos is not None and pos.domain == 'POINT' and pos.data_type == 'FLOAT_VECTOR' and len(pos.data) * 3 == len(co):
        pos.data.foreach_get("vector", co)
    else:
        me.vertices.foreach_get("co", co)
    return co


def edges_of(ob, depsgraph):
    """(vertex positions (N, 3) float32, edge indices (E, 2) int32) of the evaluated object, object space."""
    import numpy as np
    ev = ob.evaluated_get(depsgraph)
    if ob.type == 'LATTICE':
        return lattice_edges(ev.data)
    if ob.type == 'MESH':
        me, temp = ev.data, False
    else:
        me, temp = ev.to_mesh(), True
    try:
        co = _positions(me)
        size = (len(me.vertices), len(me.edges))
        got = _edges.get(ob.session_uid) if not temp else None
        if got is not None and got[0] == size:
            ed = got[1]
        else:
            ed = np.empty(size[1] * 2, np.int32)
            me.edges.foreach_get("vertices", ed)
            ed = ed.reshape(-1, 2)
            if not temp and keeps_edges(ob):
                _edges[ob.session_uid] = (size, ed)
            else:
                _edges.pop(ob.session_uid, None)
    finally:
        if temp:
            ev.to_mesh_clear()
    return co.reshape(-1, 3), ed


def lattice_edges(lat):
    """(points (N, 3), edges (E, 2)) of a lattice grid: neighbours along U, V and W, index u + v·U + w·U·V."""
    import numpy as np
    nu, nv, nw = lat.points_u, lat.points_v, lat.points_w
    co = np.empty(len(lat.points) * 3, np.float32)
    lat.points.foreach_get("co_deform", co)
    idx = np.arange(nu * nv * nw, dtype=np.int32).reshape(nw, nv, nu)
    pairs = [np.stack((idx[:, :, :-1].ravel(), idx[:, :, 1:].ravel()), 1),
             np.stack((idx[:, :-1, :].ravel(), idx[:, 1:, :].ravel()), 1),
             np.stack((idx[:-1, :, :].ravel(), idx[1:, :, :].ravel()), 1)]
    return co.reshape(-1, 3), np.concatenate(pairs).astype(np.int32).reshape(-1, 2)


def _batch(ob, depsgraph):
    key = ob.session_uid
    if key not in _batches:
        from gpu_extras.batch import batch_for_shader
        co, ed = edges_of(ob, depsgraph)
        batch = batch_for_shader(_sh(), 'LINES', {"pos": co}, indices=ed) if len(ed) else None
        _batches[key] = (batch, len(ed))
    return _batches[key][0]


def _view(context):
    space = getattr(context, "space_data", None)
    return space if space is not None and space.type == 'VIEW_3D' else None


def _shown(ob, space):
    """Drawn in this view: the per-view type filter and local view count (``visible_get()`` alone
    ignores them, ``visible_get(viewport=space)`` doesn't)."""
    if isinstance(space, bpy.types.SpaceView3D):
        return ob.visible_get(viewport=space)
    return ob.visible_get()


# Maya Show > Selection Highlighting is per panel (Issue #173). The kit's highlight is this wire; Maya
# Workflow Kit views keep Blender's outline off, so ``show_outline_selected`` can't be the row's state.
# Views with highlighting off = a JSON {area index: Blender outline was on} on their screen (Blender
# spaces / areas take no ID properties; an area index survives save / open).
HILITE_OFF = "allset_hilite_off"


def _off_map(screen):
    import json
    try:
        return json.loads(screen.get(HILITE_OFF) or "{}") if screen is not None else {}
    except (TypeError, ValueError):
        return {}


def _area_index(context, space):
    screen = getattr(context, "screen", None)
    if screen is None or space is None:
        return None
    for i, area in enumerate(screen.areas):
        if area.spaces.active == space:
            return str(i)
    return None


def highlighting(context):
    """Maya Show > Selection Highlighting of this view (the panel menu row ``SELECTION_HILITE``): off = no kit
    selection wire and no Blender outline."""
    space = _view(context)
    if space is None:
        return True
    key = _area_index(context, space)
    return key is None or key not in _off_map(context.screen)


def set_highlighting(context, on):
    """Turn this view's Selection Highlighting on / off; Blender's outline goes with it and comes back as it was."""
    import json
    space = _view(context)
    key = _area_index(context, space)
    if key is None:
        return
    screen = context.screen
    off = _off_map(screen)
    if on and key in off:
        if off.pop(key):
            space.overlay.show_outline_selected = True
    elif not on and key not in off:
        off[key] = bool(space.overlay.show_outline_selected)
        space.overlay.show_outline_selected = False
    if off:
        screen[HILITE_OFF] = json.dumps(off)
    elif HILITE_OFF in screen:
        del screen[HILITE_OFF]


def wire_objects(context):
    """Selected objects that get the wire: object mode, drawable types, visible."""
    space = _view(context)
    return [ob for ob in context.selected_objects
            if ob.type in WIRE_TYPES and ob.mode == 'OBJECT' and _shown(ob, space)]


def highlighted(context):
    """[(object, is_lead)]: the selected objects that get the wire plus their descendants (Maya's hierarchy
    highlight), each in the colour of its nearest selected ancestor (itself when selected)."""
    if not highlighting(context):
        return []
    space = _view(context)
    active = context.view_layer.objects.active
    out, seen = [], set()
    from ..operators import live
    live_objects = set(live.objects(context.scene))

    def visit(ob, lead):
        if ob.session_uid in seen:
            return
        seen.add(ob.session_uid)
        if ob.type in WIRE_TYPES and ob.mode == 'OBJECT' and _shown(ob, space) and ob not in live_objects:
            out.append((ob, lead))
        for child in ob.children:
            if not child.select_get():          # a selected child keeps its own colour (visited as a root)
                visit(child, lead)
    for ob in context.selected_objects:
        # #173: an armature in Pose / Edit mode is selected for its bones (Maya: a picked control),
        # so its child meshes aren't a selected hierarchy
        if ob.mode != 'OBJECT':
            continue
        visit(ob, ob == active)
    return out


def dormant_objects(context):
    """Unselected objects that get Maya's dormant wire: wireframe shading, object mode, drawable types shown in this
    view (local view, per-type visibility)."""
    space = context.space_data
    if space is None or space.type != 'VIEW_3D' or space.shading.type != 'WIREFRAME':
        return []
    out = []
    from ..operators import live
    scene = getattr(context, "scene", None)
    live_objects = set(live.objects(scene)) if scene is not None else set()
    for ob in context.visible_objects:
        if ob.type not in TYPES or ob.mode != 'OBJECT' or ob.select_get() or (live_objects and ob in live_objects):
            continue
        if not getattr(space, TYPE_FLAGS[ob.type], True):
            continue
        if space.local_view is not None and not ob.local_view_get(space):
            continue
        out.append(ob)
    return out


def srgb(hex_str):
    """'#rrggbb' -> sRGB floats (r, g, b)."""
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _linear(c):
    from mathutils import Color
    lin = Color(tuple(c)[:3]).from_srgb_to_scene_linear()
    return (lin.r, lin.g, lin.b, 1.0)


def wire_colors():
    """(lead, other) RGBA in scene linear: kit-fixed Maya colours, whatever the user's theme is."""
    return _linear(srgb(LEAD)), _linear(srgb(OTHER))


def dormant_color():
    """Maya's dormant wire RGBA in scene linear."""
    return _linear(srgb(DORMANT))


def frame_ms():
    return sum(_times) / len(_times) * 1000.0 if _times else 0.0


def live_wire_objects(context):
    from ..operators import live
    space = context.space_data
    if space.shading.type != 'WIREFRAME' and not space.overlay.show_wireframes:
        return []
    return [o for o in live.objects(context.scene) if _shown(o, space)]


def depth_bias(ob, depsgraph, projection, viewport):
    """Conservative NDC offset from evaluated bounds and this view's pixel scale.

    No positive floor is safe for an arbitrarily thin / distant object. An
    unusable projection or bounds therefore returns zero rather than falling
    back to the old fixed offset. Bounds are a heuristic, not an occlusion
    guarantee for closely spaced surfaces or unrelated foreground objects.
    """
    import math
    from mathutils import Vector
    try:
        width, height = viewport
        if not all(math.isfinite(v) and v > 0 for v in (width, height)):
            return 0.0
        bounds = tuple(tuple(c) for c in ob.evaluated_get(depsgraph).bound_box)
        if (len(bounds) != 8 or any(len(c) != 3 for c in bounds)
                or not all(math.isfinite(v) for c in bounds for v in c)):
            return 0.0
        matrix = projection @ ob.matrix_world
        xs, ys, depths = [], [], []
        for corner in bounds:
            clip = matrix @ Vector((*corner, 1.0))
            if (not all(math.isfinite(v) for v in clip) or clip.w <= 1e-8
                    or clip.z <= -clip.w or clip.z >= clip.w):
                return 0.0  # Behind the eye, intersecting a clip plane, or unstable.
            xs.append(clip.x / clip.w)
            ys.append(clip.y / clip.w)
            depths.append(clip.z / clip.w)
        if not all(math.isfinite(v) for values in (xs, ys, depths) for v in values):
            return 0.0
        span = max(depths) - min(depths)
        pixels = max(1.0, (max(xs) - min(xs)) * width * 0.5,
                     (max(ys) - min(ys)) * height * 0.5)
        if not math.isfinite(span) or not math.isfinite(pixels) or span <= 0.0:
            return 0.0
        bias = min(DEPTH_BIAS, span * DEPTH_BIAS_MAX_SPAN, span * DEPTH_BIAS_PIXELS / pixels)

        # For a thin box viewed obliquely, its overall depth span includes the
        # long sides. Cap against the projected separation along each thin axis.
        sizes = [max(c[i] for c in bounds) - min(c[i] for c in bounds) for i in range(3)]
        world = ob.matrix_world
        lengths = [math.sqrt(sum((world[row][i] * sizes[i]) ** 2 for row in range(3))) for i in range(3)]
        if not all(math.isfinite(v) for v in lengths):
            return 0.0
        longest = max(lengths)
        for axis, length in enumerate(lengths):
            if length <= 0.0 or length >= longest * DEPTH_BIAS_THIN_RATIO:
                continue
            other_axes = tuple(i for i in range(3) if i != axis)
            separations = [abs(depths[i] - depths[j])
                           for i in range(8) for j in range(i + 1, 8)
                           if bounds[i][axis] != bounds[j][axis]
                           and all(bounds[i][k] == bounds[j][k] for k in other_axes)]
            if not separations:
                return 0.0
            bias = min(bias, min(separations) * DEPTH_BIAS_THIN_SPAN)
        return bias
    except (AttributeError, TypeError, ValueError, OverflowError, RuntimeError):
        return 0.0


_PAIRS = [(i, j) for i in range(8) for j in range(i + 1, 8)]     # every two corners of a bound box
ARRAY_FROM = 8      # from this many objects on ``depth_biases`` computes in arrays (fewer: one by one is quicker)
_NO_BOX = [0.0] * 24
_NO_MATRIX = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


def depth_biases(objects, depsgraph, projection, viewport):
    """``depth_bias`` of each of ``objects`` (a list of floats): the same rule, computed for many objects at once in
    arrays (hundreds of selected objects took tens of milliseconds a redraw one by one)."""
    import math
    import numpy as np
    n = len(objects)
    if n < ARRAY_FROM:
        return [depth_bias(ob, depsgraph, projection, viewport) for ob in objects]
    width, height = viewport
    if not all(math.isfinite(v) and v > 0 for v in (width, height)):
        return [0.0] * n
    ok = np.ones(n, bool)
    boxes, mats = [], []
    for k, ob in enumerate(objects):
        # plain lists: reading Blender's arrays into numpy one object at a time costs several times more
        try:
            box = [v for corner in ob.evaluated_get(depsgraph).bound_box for v in corner]
            mat = [v for row in ob.matrix_world for v in row]
        except (AttributeError, TypeError, ValueError, OverflowError, RuntimeError, ReferenceError):
            box = mat = None
        if box is None or len(box) != 24 or len(mat) != 16:
            ok[k] = False
            box, mat = _NO_BOX, _NO_MATRIX
        boxes.extend(box)
        mats.extend(mat)
    corners = np.array(boxes, np.float64).reshape(n, 8, 3)
    worlds = np.array(mats, np.float64).reshape(n, 4, 4)
    with np.errstate(all='ignore'):
        ok &= np.isfinite(corners).all(axis=(1, 2)) & np.isfinite(worlds).all(axis=(1, 2))
        clip = np.einsum('nij,nkj->nki', np.array(projection, np.float64) @ worlds,
                         np.concatenate((corners, np.ones((n, 8, 1))), axis=2))
        w, z = clip[..., 3], clip[..., 2]
        # behind the eye, intersecting a clip plane, or unstable
        ok &= np.isfinite(clip).all(axis=(1, 2)) & (w > 1e-8).all(1) & (z > -w).all(1) & (z < w).all(1)
        xs, ys, depths = clip[..., 0] / w, clip[..., 1] / w, z / w
        ok &= np.isfinite(xs).all(1) & np.isfinite(ys).all(1) & np.isfinite(depths).all(1)
        span = depths.max(1) - depths.min(1)
        pixels = np.maximum(np.maximum(1.0, (xs.max(1) - xs.min(1)) * width * 0.5),
                            (ys.max(1) - ys.min(1)) * height * 0.5)
        ok &= np.isfinite(span) & np.isfinite(pixels) & (span > 0.0)
        bias = np.minimum(np.minimum(DEPTH_BIAS, span * DEPTH_BIAS_MAX_SPAN), span * DEPTH_BIAS_PIXELS / pixels)
        # a thin box viewed obliquely: cap against the projected separation along each thin axis
        sizes = corners.max(1) - corners.min(1)
        lengths = np.sqrt(((worlds[:, :3, :3] * sizes[:, None, :]) ** 2).sum(axis=1))
        ok &= np.isfinite(lengths).all(1)
        longest = lengths.max(1)
        a = np.array([p[0] for p in _PAIRS])
        b = np.array([p[1] for p in _PAIRS])
        sep = np.abs(depths[:, a] - depths[:, b])
        for axis in range(3):
            thin = (lengths[:, axis] > 0.0) & (lengths[:, axis] < longest * DEPTH_BIAS_THIN_RATIO)
            others = [i for i in range(3) if i != axis]
            along = ((corners[:, a, axis] != corners[:, b, axis])
                     & (corners[:, a, others[0]] == corners[:, b, others[0]])
                     & (corners[:, a, others[1]] == corners[:, b, others[1]]))
            found = along.any(1)
            ok &= ~(thin & ~found)
            least = np.where(along, sep, np.inf).min(1)
            bias = np.where(thin & found, np.minimum(bias, least * DEPTH_BIAS_THIN_SPAN), bias)
    return np.where(ok, bias, 0.0).tolist()


def view_draws(space):
    """This 3D View gets the selection wire: overlays on, in every shading mode (Solid, Material Preview and
    Rendered alike, as Blender's own outline). A view with overlays off, like the IPR picture, draws nothing."""
    return bool(space.overlay.show_overlays)


def _draw():
    context = bpy.context
    space, rv3d = context.space_data, context.region_data
    if rv3d is None or not view_draws(space):
        return
    if (not context.selected_objects and space.shading.type != 'WIREFRAME'
            and not space.overlay.show_wireframes):
        return              # no selected wire, no dormant wire, no Make Live wire
    from ..operators import live
    live_obs = live_wire_objects(context)
    obs = highlighted(context) if _enabled() else []
    dormant = dormant_objects(context) if _enabled() else []
    if not obs and not dormant and not live_obs:
        return
    import time
    import gpu
    t0 = time.perf_counter()
    # the colours are sRGB, this shader writes the 3D View's linear framebuffer as is (#43ffa3 drew as
    # #8bffd0 without the conversion; built-in shaders convert by themselves)
    lead, other = wire_colors()
    # view_layer.depsgraph: already evaluated for this redraw; evaluated_depsgraph_get() inside a draw
    # callback re-evaluates and broke a timer-set region flag (gui_step11 Ctrl+A sidebar)
    depsgraph = context.view_layer.depsgraph
    sh = _sh()
    # X-ray wireframe (Blender's default in wireframe shading) shows the hidden edges too, like Maya's wireframe
    xray = space.shading.type == 'WIREFRAME' and space.shading.show_xray_wireframe
    gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
    try:
        gpu.state.depth_mask_set(False)
        sh.bind()
        sh.uniform_float("bias", DEPTH_BIAS)
        pm = rv3d.perspective_matrix
        if dormant:
            sh.uniform_float("color", dormant_color())
            for ob in dormant:
                batch = _batch(ob, depsgraph)
                if batch is not None:
                    sh.uniform_float("mvp", pm @ ob.matrix_world)
                    batch.draw(sh)
        region = context.region
        biases = [DEPTH_BIAS] * len(obs) if xray else depth_biases(
            [ob for ob, _lead in obs], depsgraph, pm, (region.width, region.height))
        for (ob, is_lead), bias in zip(obs, biases):
            batch = _batch(ob, depsgraph)
            if batch is None:
                continue
            sh.uniform_float("bias", bias)
            sh.uniform_float("mvp", pm @ ob.matrix_world)
            sh.uniform_float("color", lead if is_lead else other)
            batch.draw(sh)
        sh.uniform_float("bias", DEPTH_BIAS)  # preserve 0.7 Make Live pass behavior
        sh.uniform_float('color', _linear(live.COLOR))
        for ob in live_obs:
            batch = _batch(ob, depsgraph)
            if batch is not None:
                sh.uniform_float('mvp', pm @ ob.matrix_world)
                batch.draw(sh)
    finally:
        gpu.state.depth_test_set('NONE')
    _times.append(time.perf_counter() - t0)
    if len(_times) > 120:
        del _times[0]


def _callback():
    try:
        _draw()
    except Exception:  # never let a draw error repeat every frame
        import traceback
        traceback.print_exc()
        _remove_handler()


def _remove_handler():
    while _handle:
        bpy.types.SpaceView3D.draw_handler_remove(_handle.pop(), 'WINDOW')


@persistent
def _on_depsgraph(_scene, depsgraph):
    """Drop the cached batch of objects whose geometry changed (edits, modifiers, shape keys). Their edges go too,
    unless only the points can have moved: a mesh that only deforms (``keeps_edges``) re-evaluated with no update of
    its own mesh data — its skeleton or lattice moved (a moved rig re-read every child mesh's edges each step)."""
    if not _batches and not _edges:
        return
    data_updated = None
    for update in depsgraph.updates:
        if update.is_updated_geometry and isinstance(update.id, bpy.types.Object):
            ob = update.id.original
            _batches.pop(ob.session_uid, None)
            if ob.session_uid not in _edges:
                continue
            if data_updated is None:
                data_updated = {u.id.original.as_pointer() for u in depsgraph.updates
                                if not isinstance(u.id, bpy.types.Object)}
            if ob.data is None or ob.data.as_pointer() in data_updated or not keeps_edges(ob):
                _edges.pop(ob.session_uid, None)


def time_dependent(ob):
    """Can the evaluated geometry change with the frame? Modifiers (armature / cloth / lattice / nodes ...), shape
    keys, animated object data. Object transforms don't matter: the batch is drawn with the live matrix."""
    if ob.modifiers or getattr(ob, "particle_systems", None):
        return True
    data = ob.data
    if data is None:
        return False
    if getattr(data, "shape_keys", None) is not None or data.animation_data is not None:
        return True
    return False


@persistent
def _on_frame(scene, _depsgraph=None):
    """Drop the batches of time-dependent objects so the next redraw reads this frame's evaluated mesh (#91); a mesh
    that only deforms keeps its edges (``keeps_edges``)."""
    if not _batches:
        return
    for ob in scene.objects:
        if ob.session_uid in _batches and time_dependent(ob):
            del _batches[ob.session_uid]
            if not keeps_edges(ob):
                _edges.pop(ob.session_uid, None)


@persistent
def _on_reload(*_args):
    _batches.clear()
    _edges.clear()


_HANDLERS = (("depsgraph_update_post", _on_depsgraph), ("frame_change_post", _on_frame), ("undo_post", _on_reload), ("redo_post", _on_reload),
             ("load_post", _on_reload))


def register():
    for name, fn in _HANDLERS:
        getattr(bpy.app.handlers, name).append(fn)
    _handle.append(bpy.types.SpaceView3D.draw_handler_add(_callback, (), 'WINDOW', 'POST_VIEW'))


def unregister():
    _remove_handler()
    for name, fn in _HANDLERS:
        lst = getattr(bpy.app.handlers, name)
        if fn in lst:
            lst.remove(fn)
    _batches.clear()
    _edges.clear()
    _shader.clear()
    _times.clear()
