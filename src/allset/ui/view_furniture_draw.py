# SPDX-License-Identifier: GPL-3.0-or-later
"""GPU drawing of the view furniture: the ViewCube's faces, outlines, face names and controls (``draw_cube``) and the
camera label and axis triad (``_draw_hud``, run by the draw handler ``_hud_callback``), with cached batches and
draw plans (``_plan``) so an unchanged view is not rebuilt on every redraw. Geometry from view_furniture_geometry.py,
view state from view_furniture_state.py; view_furniture.py adds the draw handler and re-exports these names.
"""

import math

import bpy
from mathutils import Vector

from .view_furniture_geometry import (FACES, LABEL_PX, LABEL_RGB, TRIAD_LEN, _arc_arrow, _bounds, _cube_rotation,
                                      _face_aligned, _roll_arrows, _scale, control_layout, cube_size, faces_2d,
                                      label_camera, label_for, layout, triad)
from .view_furniture_state import (_apply_later, _check_strip, _hideable, _prefs, _remove_handler,
                                   blender_gizmo_wanted, maya_view)

# --- drawing --------------------------------------------------------------------------------

_shader = []
def _face_label(name, poly, facing, u2, size, alpha):
    """``_text`` arguments of the face's name in Blender's UI font, centred on the projected face, along its text axis
    and never upside down."""
    cx = sum(p[0] for p in poly) / 4
    cy = sum(p[1] for p in poly) / 4
    ang = math.atan2(u2[1], u2[0])
    if math.cos(ang) < 0:
        ang += math.pi
    return name, cx, cy, max(6, round(size * 0.14 * facing ** 0.5)), (.16, .16, .16, min(1.0, alpha * 1.5)), ang


def _draw_controls(context, centre, size, hover):
    arrows = _roll_arrows(context, centre, size)
    for name, (x, y, radius) in control_layout(context, centre, size).items():
        if name.startswith(('ROLL', 'ORBIT')) and not _face_aligned(context.region_data):
            continue
        colour = (.55, .78, .98, 1.0) if hover == name else (.82, .85, .88, .88)
        r = radius * .55
        if name == 'HOME':
            points, head = _arc_arrow((x,y), r, 550, 225, r*.65, r*.29)
            _lines(points, colour, 1.4 * _scale(), context.region)
            _fill(head, colour)
            continue
        elif name == 'MENU':
            points = [(x-r, y+r*.35), (x, y-r*.45), (x+r, y+r*.35)]
        elif name.startswith('ORBIT'):
            dx, dy = {'ORBIT_UP': (0, 1), 'ORBIT_DOWN': (0, -1),
                      'ORBIT_LEFT': (-1, 0), 'ORBIT_RIGHT': (1, 0)}[name]
            dx, dy = -dx, -dy  # The small triangles point toward the cube.
            _fill([(x+dx*r, y+dy*r),
                   (x-dx*r*.6-dy*r, y-dy*r*.6+dx*r),
                   (x-dx*r*.6+dy*r, y-dy*r*.6-dx*r)], colour)
            continue
        else:
            points, head = arrows[name]
            _lines(points, colour, 1.8 * _scale(), context.region)
            _fill(head, colour)
            continue
        _lines(points, colour, 1.5 * _scale(), context.region)


_batches = {}        # (kind, geometry) -> GPU batch: the ViewCube controls redraw the same shapes
_plans = {}          # (what, view rotation, place, size, ...) -> the ViewCube's / axis triad's draw steps


def _cached_batch(key, build):
    batch = _batches.get(key)
    if batch is None:
        if len(_batches) > 128:
            _batches.clear()
        batch = _batches[key] = build()
    return batch


def _plan(key, build):
    """Draw steps of ``key``, built once: a view keeps its rotation and size from redraw to redraw (every frame
    while playback runs), so the ViewCube's faces and the triad are worked out and uploaded once."""
    got = _plans.get(key)
    if got is None:
        if len(_plans) > 32:
            _plans.clear()
        got = _plans[key] = build()
    return got


def _sh():
    if not _shader:
        import gpu
        _shader.append(gpu.shader.from_builtin('UNIFORM_COLOR'))
        _shader.append(gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR'))
        _shader.append(gpu.shader.from_builtin('SMOOTH_COLOR'))
    return _shader


def _fill(poly, colour):
    from gpu_extras.batch import batch_for_shader
    sh = _sh()[0]
    batch = _cached_batch(("fan", tuple(map(tuple, poly))), lambda: batch_for_shader(sh, 'TRI_FAN', {"pos": poly}))
    sh.uniform_float("color", colour)
    batch.draw(sh)


def _cube_face_batch(poly, name, facing, alpha):
    """World-up lighting: bright upper face, darker underside, smooth sides."""
    from gpu_extras.batch import batch_for_shader
    normal, u, v = FACES[name]
    colours = []
    for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        height = .5 + .5 * (normal[2] + u[2] * su + v[2] * sv)
        shade = (.77 + .22 * height) * (.92 + .08 * facing)
        colours.append((shade, shade, shade, alpha))
    return batch_for_shader(_sh()[2], 'TRI_FAN', {'pos': poly, 'color': colours})


def _strip_batch(points):
    from gpu_extras.batch import batch_for_shader
    return batch_for_shader(_sh()[1], 'LINE_STRIP', {"pos": [(x, y, 0.0) for x, y in points]})


def _draw_strip(batch, colour, width, region):
    sh = _sh()[1]
    sh.bind()
    sh.uniform_float("viewportSize", (region.width, region.height))
    sh.uniform_float("lineWidth", width)
    sh.uniform_float("color", colour)
    batch.draw(sh)


def _lines(points, colour, width, region, loop=False):
    pts = list(points) + ([points[0]] if loop else [])
    _draw_strip(_cached_batch(("strip", tuple(map(tuple, pts))), lambda: _strip_batch(pts)), colour, width, region)


def _text(s, x, y, px, colour, angle=0.0, centre=True):
    import blf
    fid = 0
    blf.size(fid, px)
    w, h = blf.dimensions(fid, s)
    if angle:
        blf.enable(fid, blf.ROTATION)
        blf.rotation(fid, angle)
    if centre:
        c, sn = math.cos(angle), math.sin(angle)
        x, y = x - (c * w / 2 - sn * h / 2), y - (sn * w / 2 + c * h / 2)
    blf.color(fid, *colour)
    blf.position(fid, x, y, 0)
    blf.draw(fid, s)
    if angle:
        blf.disable(fid, blf.ROTATION)


def _cube_plan(q, centre, size, hover, alpha):
    """(faces, [(face fill, face outline, label or None)]) of the ViewCube seen with rotation ``q``."""
    from gpu_extras.batch import batch_for_shader
    faces = faces_2d(q, centre, size)
    steps = []
    for name, poly, facing, u2, _v2 in faces:
        if name == hover:
            fill = (batch_for_shader(_sh()[0], 'TRI_FAN', {"pos": poly}), (0.55, 0.75, 0.95, alpha))
        else:
            fill = (_cube_face_batch(poly, name, facing, alpha), None)
        label = _face_label(name, poly, facing, u2, size, alpha) if facing > 0.28 else None
        steps.append((fill, _strip_batch(list(poly) + [poly[0]]), label))
    return faces, steps


def draw_cube(context, hover=None, alpha=0.5):
    import gpu
    region, rv3d = context.region, context.region_data
    s = _scale()
    size = cube_size(region.width, region.height, s)
    centre, _label, _triad = layout(_bounds(context), s, size)
    q = _cube_rotation(rv3d)
    faces, steps = _plan(("cube", tuple(q), centre, size, hover, alpha),
                         lambda: _cube_plan(q, centre, size, hover, alpha))
    shaders = _sh()
    for (batch, colour), outline, label in steps:
        gpu.state.blend_set('ALPHA')
        if colour is not None:                 # the face under the mouse
            shaders[0].uniform_float("color", colour)
            batch.draw(shaders[0])
        else:
            shaders[2].bind()
            batch.draw(shaders[2])
        _draw_strip(outline, (0.418, 0.418, 0.418, alpha), 1.95, region)
        if label is not None:
            _text(*label)
    if hover is not None:
        _draw_controls(context, centre, size, hover)
    return faces


def _triad_plan(q, origin, s, colours):
    """[(line, colour, letter ``_text`` arguments)] of the axis triad seen with rotation ``q``."""
    steps = []
    for i, end, _depth in triad(q, origin, TRIAD_LEN * s):
        rgb = colours[i]
        dx, dy = end[0] - origin[0], end[1] - origin[1]
        n = math.hypot(dx, dy) or 1.0
        steps.append((_strip_batch((origin, end)), (*rgb, 1.0),
                      ("xyz"[i], end[0] + dx / n * 5 * s, end[1] + dy / n * 5 * s, round(10 * s), (*rgb, 1.0))))
    return steps


def _draw_hud():
    context = bpy.context
    space, region, rv3d = context.space_data, context.region, context.region_data
    if rv3d is None or not maya_view(space):
        return
    prefs = _prefs()
    if prefs is None:
        return
    _check_strip(context)
    if not space.show_gizmo_navigate and blender_gizmo_wanted(prefs) and _hideable(space):
        _apply_later()
    import gpu
    s = _scale()
    _cube, label, origin = layout(_bounds(context), s, 0.0)
    gpu.state.blend_set('ALPHA')
    if prefs.maya_camera_names:
        cam = label_camera(space, context.scene)
        d = rv3d.view_rotation @ Vector((0.0, 0.0, -1.0))
        text = label_for(rv3d.view_perspective, rv3d.is_orthographic_side_view, tuple(d),
                         cam.name if cam else None)
        import blf
        blf.size(0, round(LABEL_PX * s))
        w = blf.dimensions(0, text)[0]
        _text(text, label[0] - w / 2, label[1], round(LABEL_PX * s), (*LABEL_RGB, 1.0), centre=False)
    if prefs.maya_view_axis:
        ui = context.preferences.themes[0].user_interface
        colours = tuple(tuple(c)[:3] for c in (ui.axis_x, ui.axis_y, ui.axis_z))
        q = rv3d.view_rotation
        for line, colour, letter in _plan(("triad", tuple(q), origin, s, colours),
                                          lambda: _triad_plan(q, origin, s, colours)):
            gpu.state.blend_set('ALPHA')
            _draw_strip(line, colour, 1.0, region)
            _text(*letter)
    gpu.state.blend_set('NONE')


def _hud_callback():
    try:
        _draw_hud()
    except Exception:  # never let a draw error repeat every frame
        import traceback
        traceback.print_exc()
        _remove_handler()
