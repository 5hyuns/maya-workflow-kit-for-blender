# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya's wireframe on selected objects over shading (lead light green, other selected white).

Maya draws every edge of a selected object in the selection colour over its shading
(, 04_wire_selected_lead.png); Blender only outlines it.

The kit draws the edges itself (POST_VIEW), :
- Blender's own ``Object.show_wire`` mixes a selected object's colour with the theme's dormant wire colour
  by up to ~19 % depending on how the edge faces the view (checked #37cf95 = 0.81 lead + 0.19 #000460),
  so it can't give Maya's flat colour; it is also ID data (saved, in undo steps) and shared with the
  smooth preview 2 cage wire (operators/display.py ``_WIRE_FLAG``).
- Here: evaluated mesh edges in a cached batch per object (numpy, ~28 ms for 100k polys, rebuilt only when
  the object's geometry changes), drawn with the object matrix and a small depth bias (no z-fighting),
  colours = theme ``object_active`` / ``object_selected`` (Maya lead green / white with the Maya theme).
  Nothing is written to the file.
"""

import bpy
from bpy.app.handlers import persistent

TYPES = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}
DEPTH_BIAS = 1e-4          # NDC depth; 0 breaks the lines up on a 1 cm cube in the cm template (probe)

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


def edges_of(ob, depsgraph):
    """(vertex positions (N, 3) float32, edge indices (E, 2) int32) of the evaluated object, object space."""
    import numpy as np
    ev = ob.evaluated_get(depsgraph)
    if ob.type == 'MESH':
        me, temp = ev.data, False
    else:
        me, temp = ev.to_mesh(), True
    try:
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        ed = np.empty(len(me.edges) * 2, np.int32)
        me.edges.foreach_get("vertices", ed)
    finally:
        if temp:
            ev.to_mesh_clear()
    return co.reshape(-1, 3), ed.reshape(-1, 2)


def _batch(ob, depsgraph):
    key = ob.session_uid
    if key not in _batches:
        from gpu_extras.batch import batch_for_shader
        co, ed = edges_of(ob, depsgraph)
        batch = batch_for_shader(_sh(), 'LINES', {"pos": co}, indices=ed) if len(ed) else None
        _batches[key] = (batch, len(ed))
    return _batches[key][0]


def wire_objects(context):
    """Selected objects that get the wire: object mode, drawable types, visible."""
    return [ob for ob in context.selected_objects
            if ob.type in TYPES and ob.mode == 'OBJECT' and ob.visible_get()]


def _linear(c):
    from mathutils import Color
    lin = Color(tuple(c)[:3]).from_srgb_to_scene_linear()
    return (lin.r, lin.g, lin.b, 1.0)


def frame_ms():
    return sum(_times) / len(_times) * 1000.0 if _times else 0.0


def _draw():
    context = bpy.context
    space, rv3d = context.space_data, context.region_data
    if rv3d is None or not space.overlay.show_overlays or space.shading.type == 'RENDERED' or not _enabled():
        return
    obs = wire_objects(context)
    if not obs:
        return
    import time
    import gpu
    t0 = time.perf_counter()
    theme = context.preferences.themes[0].view_3d
    active = context.view_layer.objects.active
    # theme colours are sRGB, this shader writes the 3D View's linear framebuffer as is (#43ffa3 drew as
    # #8bffd0 without the conversion; built-in shaders convert by themselves)
    lead, other = (_linear(theme.object_active), _linear(theme.object_selected))
    # view_layer.depsgraph: already evaluated for this redraw; evaluated_depsgraph_get() inside a draw
    # callback re-evaluates and broke a timer-set region flag (gui_step11 Ctrl+A sidebar)
    depsgraph = context.view_layer.depsgraph
    sh = _sh()
    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.depth_mask_set(False)
    sh.bind()
    sh.uniform_float("bias", DEPTH_BIAS)
    pm = rv3d.perspective_matrix
    for ob in obs:
        batch = _batch(ob, depsgraph)
        if batch is None:
            continue
        sh.uniform_float("mvp", pm @ ob.matrix_world)
        sh.uniform_float("color", lead if ob == active else other)
        batch.draw(sh)
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
    """Drop the cached batch of objects whose geometry changed (edits, modifiers, shape keys)."""
    if not _batches:
        return
    for update in depsgraph.updates:
        if update.is_updated_geometry and isinstance(update.id, bpy.types.Object):
            _batches.pop(update.id.original.session_uid, None)


@persistent
def _on_reload(*_args):
    _batches.clear()


_HANDLERS = (("depsgraph_update_post", _on_depsgraph), ("undo_post", _on_reload), ("redo_post", _on_reload),
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
    _shader.clear()
    _times.clear()
