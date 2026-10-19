# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya's viewport grid: finite, 12 units each way, a line every unit, thicker every 5, axes thicker.

Maya 2022 factory grid ( metrics.grid {size 12, spacing 5, divisions 5};
, Maya-226): lines from -12 to +12 every 1 unit, every
5th line (and the axes through the origin) thicker, all the same grey (displayColor grid / gridAxis /
gridHighlight = index 2, #404040), aliased. checked in 
only the background and #404040 in the view, minor lines 1 px, major lines and axes 2 px
.

Blender's floor is infinite with unit-system steps of x10 (no 5-unit lines, ), so
the kit draws its own grid with a POST_VIEW handler in the 3D views that use it. Like Maya, only on
the ground: top views show it, front / side views (ground edge-on) show none.

Per-view state: a 3D View uses the Maya grid when Blender's floor and ortho grid are off and
``overlay.grid_lines`` (not used by Blender 4.x, not in its UI) is 0. The grid unit is one Maya length
(``units.maya_unit``, ), which ``units.grid_scale`` also makes Blender's finest perspective
grid step, so X-hold grid snapping lands on these lines.
"""

import time

import bpy

# Maya factory grid (colors.json metrics.grid).
SIZE = 12
SPACING = 5
DIVISIONS = 5
# Line widths in px (01_layout_empty.png): minor, major (every SPACING), axes.
WIDTHS = (1.0, 2.0, 2.0)
OFF_LINES = 16          # Blender's default grid_lines: "not the Maya grid"

_handle = []
_batches = {}
_times = []


# --- maths (no bpy) ----------------------------------------------------------------------

def segments(size=SIZE, spacing=SPACING, divisions=DIVISIONS):
    """Grid lines in Maya units on a plane (u, v): {"minor"|"major"|"axis": [((u0, v0), (u1, v1)), ...]}.

    One line every ``spacing / divisions`` unit from -size to +size in both directions; lines at
    multiples of ``spacing`` are major, the two through the origin are the axes.
    """
    step = spacing / divisions
    n = int(round(size / step))
    out = {"minor": [], "major": [], "axis": []}
    for i in range(-n, n + 1):
        t = i * step
        if i == 0:
            kind = "axis"
        elif abs(t / spacing - round(t / spacing)) < 1e-9:
            kind = "major"
        else:
            kind = "minor"
        out[kind].append(((t, -size), (t, size)))     # along v
        out[kind].append(((-size, t), (size, t)))     # along u
    return out


# plane -> how (u, v) map to Blender (x, y, z). Maya is Y-up: its ground XZ is Blender's XY.
PLANES = {
    "FLOOR": lambda u, v: (u, v, 0.0),     # Blender top / user views
    "XZ": lambda u, v: (u, 0.0, v),       # Blender front / back (Maya front)
    "YZ": lambda u, v: (0.0, u, v),       # Blender left / right (Maya side)
}


def plane_points(segs, plane="FLOOR", unit=1.0):
    """Line segment end points in Blender units (flat list, 2 per line)."""
    f = PLANES[plane]
    pts = []
    for (u0, v0), (u1, v1) in segs:
        pts.append(f(u0 * unit, v0 * unit))
        pts.append(f(u1 * unit, v1 * unit))
    return pts


def plane_for_view(perspective, side_view, view_dir):
    """Grid plane of a view: always Maya's ground plane, or None when a view looks at it edge-on.

    Maya's grid lies on the ground only: the top view shows it, the front and side views show no grid
    ( "front -Z" / "side -X" panels are empty). ``view_dir`` =
    the view's looking direction in world space (x, y, z).
    """
    if perspective == 'ORTHO' and side_view and abs(view_dir[2]) < 1e-6:
        return None
    return "FLOOR"


def project(matrix, point, width, height):
    """Region pixel (x, y) of a world point for a 4x4 ``perspective_matrix`` (rows), or None behind
    the view; the same as bpy_extras.view3d_utils.location_3d_to_region_2d."""
    x, y, z = point
    v = [sum(matrix[r][c] * p for c, p in enumerate((x, y, z, 1.0))) for r in range(4)]
    if v[3] <= 0.0:
        return None
    return (width / 2 + width / 2 * v[0] / v[3], height / 2 + height / 2 * v[1] / v[3])


def corners(plane="FLOOR", unit=1.0, size=SIZE):
    """The grid's four corners in Blender units (for the projection checks)."""
    f = PLANES[plane]
    s = size * unit
    return [f(-s, -s), f(s, -s), f(s, s), f(-s, s)]


# --- per-view state ------------------------------------------------------------------------

def is_on(space):
    ov = space.overlay
    return ov.grid_lines == 0 and not ov.show_floor and not ov.show_ortho_grid


def visible(space):
    """Any grid shown in this view (the Maya grid or Blender's)."""
    ov = space.overlay
    return is_on(space) or ov.show_floor or ov.show_ortho_grid


def set_grid(space, on):
    """Maya grid on (Blender's floor, ortho grid and red/green axis lines off) or no grid at all."""
    ov = space.overlay
    ov.show_floor = False
    ov.show_ortho_grid = False
    ov.show_axis_x = ov.show_axis_y = False
    ov.grid_lines = 0 if on else OFF_LINES


def toggle(space):
    """Maya Show > Grid: hide whatever grid is shown, else show the Maya grid. Returns the new state."""
    on = not visible(space)
    set_grid(space, on)
    return on


class ALLSET_OT_toggle_grid(bpy.types.Operator):
    """Show or hide the grid in this view (Maya grid: 12 units, a thicker line every 5)"""
    bl_idname = "allset.toggle_grid"
    bl_label = "Grid"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.space_data is not None and context.space_data.type == 'VIEW_3D'

    def execute(self, context):
        toggle(context.space_data)
        for area in context.screen.areas if context.screen else ():
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}


# --- drawing -------------------------------------------------------------------------------

def frame_ms():
    """Average time (ms) of the last grid draws (step 45 frame-time record)."""
    return sum(_times) / len(_times) * 1000.0 if _times else 0.0


def _batch_set(plane, unit):
    key = (plane, round(unit, 9))
    if key not in _batches:
        import gpu
        from gpu_extras.batch import batch_for_shader
        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        segs = segments()
        _batches[key] = (shader, [batch_for_shader(shader, 'LINES', {"pos": plane_points(segs[k], plane, unit)})
                                  for k in ("minor", "major", "axis")])
    return _batches[key]


def _view_plane(rv3d):
    from mathutils import Vector
    d = rv3d.view_rotation @ Vector((0.0, 0.0, -1.0))
    return plane_for_view(rv3d.view_perspective, rv3d.is_orthographic_side_view, tuple(d))


def _draw():
    context = bpy.context
    space, rv3d, region = context.space_data, context.region_data, context.region
    if space is None or rv3d is None or not space.overlay.show_overlays or not is_on(space):
        return
    t0 = time.perf_counter()
    import gpu
    from .. operators import units
    plane = _view_plane(rv3d)
    if plane is None:
        return
    shader, batches = _batch_set(plane, units.maya_unit(context.scene))
    colour = tuple(context.preferences.themes[0].view_3d.grid)[:3]
    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.depth_mask_set(False)
    gpu.state.blend_set('ALPHA')
    shader.bind()
    shader.uniform_float("viewportSize", (region.width, region.height))
    shader.uniform_float("color", (*colour, 1.0))
    shader.uniform_bool("lineSmooth", False)
    for width, batch in zip(WIDTHS, batches):
        shader.uniform_float("lineWidth", width)
        batch.draw(shader)
    gpu.state.blend_set('NONE')
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
        unregister_draw()


def unregister_draw():
    while _handle:
        bpy.types.SpaceView3D.draw_handler_remove(_handle.pop(), 'WINDOW')


classes = (ALLSET_OT_toggle_grid,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    _handle.append(bpy.types.SpaceView3D.draw_handler_add(_callback, (), 'WINDOW', 'POST_VIEW'))


def unregister():
    unregister_draw()
    _batches.clear()
    _times.clear()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
