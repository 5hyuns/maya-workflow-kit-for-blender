# SPDX-License-Identifier: GPL-3.0-or-later
"""GPU drawing of the marking menu engine and the hotbox (docs/steps/step_9.md 「계획」 1, 4).

One POST_PIXEL draw handler per editor type, added once at register. The
callback draws only into the region whose pointer is in ``ACTIVE`` (set by the
modal operators), so other regions pay a single dictionary lookup.
research/blender/api_limits.md #4 (:53): ``draw_handler_add`` + ``gpu`` + ``blf``.
"""

import time
import traceback

import blf
import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from . import engine

# The interaction being drawn: {"region": pointer, "session": Session} or
# {"region": pointer, "hotbox": HotboxLayout, "hover": key, ...}; empty = nothing.
ACTIVE = {}

SPACES = (bpy.types.SpaceView3D, bpy.types.SpaceOutliner, bpy.types.SpaceGraphEditor,
          bpy.types.SpaceDopeSheetEditor, bpy.types.SpaceNodeEditor, bpy.types.SpaceImageEditor)

# Maya-like greys (theme/maya.xml palette, step 5) and selection blue #5285A6.
BG = (0.27, 0.27, 0.27, 0.95)
BG_HOVER = (0.32, 0.52, 0.65, 1.0)
EDGE = (0.12, 0.12, 0.12, 1.0)
TEXT = (0.92, 0.92, 0.92, 1.0)
TEXT_OFF = (0.55, 0.55, 0.55, 1.0)
LINE = (0.95, 0.95, 0.95, 0.9)
DIM = (0.0, 0.0, 0.0, 0.35)

_handles = []
_shader = None


def ui_scale():
    return bpy.context.preferences.system.ui_scale


def font_size():
    return max(8, round(11 * ui_scale()))


def measure(text):
    blf.size(0, font_size())
    return blf.dimensions(0, text)[0]


def _sh():
    global _shader
    if _shader is None:
        _shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    return _shader


def _rect(r, color, ox=0.0, oy=0.0):
    x0, y0, x1, y1 = r[0] + ox, r[1] + oy, r[2] + ox, r[3] + oy
    sh = _sh()
    batch = batch_for_shader(sh, 'TRI_FAN', {"pos": ((x0, y0), (x1, y0), (x1, y1), (x0, y1))})
    sh.uniform_float("color", color)
    batch.draw(sh)


def _outline(r, color, ox=0.0, oy=0.0):
    x0, y0, x1, y1 = r[0] + ox, r[1] + oy, r[2] + ox, r[3] + oy
    sh = _sh()
    batch = batch_for_shader(sh, 'LINE_LOOP', {"pos": ((x0, y0), (x1, y0), (x1, y1), (x0, y1))})
    sh.uniform_float("color", color)
    batch.draw(sh)


def _line(points, color, width=1.0):
    if len(points) < 2:
        return
    gpu.state.line_width_set(width)
    sh = _sh()
    batch = batch_for_shader(sh, 'LINE_STRIP', {"pos": points})
    sh.uniform_float("color", color)
    batch.draw(sh)
    gpu.state.line_width_set(1.0)


def _text(x, y, s, color):
    blf.size(0, font_size())
    blf.color(0, *color)
    blf.position(0, x, y, 0)
    blf.draw(0, s)


def _circle(cx, cy, r, color, segments=24):
    import math
    pts = [(cx + r * math.cos(2 * math.pi * i / segments), cy + r * math.sin(2 * math.pi * i / segments))
           for i in range(segments + 1)]
    _line(pts, color, 1.5)


# --- marking menu -------------------------------------------------------------------

CHECK = (0.32, 0.52, 0.65, 1.0)   # selection blue #5285A6 (step 5 palette)


def checked(action):
    """On/off state of a toggle item (None for other items); step 26."""
    if not engine.is_toggle(action):
        return None
    op, props = action
    try:
        if op == "wm.context_toggle":
            return bool(bpy.context.path_resolve(props["data_path"]))
        from ..operators import manip
        return manip.option_state(props["option"])
    except (ValueError, KeyError, AttributeError):
        return None

def draw_session(s, now):
    if not s.visible(now):
        _line(s.trail, LINE, 2.0)  # a quick mark: only the stroke
        return
    cx, cy = s.center
    lay = s.layout
    hover, hover_opt = s.hover
    p = lay.params
    _circle(cx, cy, p.dead, LINE)
    _line([(cx, cy), s.pos], LINE, 1.5)
    pad = p.pad
    for it in lay.items:
        on = it is hover
        _rect(it.rect, BG_HOVER if on and not hover_opt and it.enabled else BG, cx, cy)
        _outline(it.rect, EDGE, cx, cy)
        text = engine.Layout._text(it.label, it.action)
        _text(cx + it.rect[0] + pad, cy + it.rect[1] + (it.rect[3] - it.rect[1]) * 0.3, text,
              TEXT if it.enabled else TEXT_OFF)
        state = checked(it.action)
        if state is not None:
            right = it.opt_rect[0] if it.opt_rect else it.rect[2]
            size = (it.rect[3] - it.rect[1]) * 0.42
            x1 = right - pad
            y0 = it.rect[1] + (it.rect[3] - it.rect[1] - size) / 2
            box = (x1 - size, y0, x1, y0 + size)
            _outline(box, TEXT if it.enabled else TEXT_OFF, cx, cy)
            if state:
                _rect((box[0] + 2, box[1] + 2, box[2] - 2, box[3] - 2), CHECK, cx, cy)
        if it.opt_rect:
            if on and hover_opt:
                _rect(it.opt_rect, BG_HOVER, cx, cy)
            inner = (it.opt_rect[0] + 4, it.opt_rect[1] + 4, it.opt_rect[2] - 4, it.opt_rect[3] - 4)
            _outline(inner, TEXT if it.enabled else TEXT_OFF, cx, cy)


# --- hotbox ---------------------------------------------------------------------------

ZONE_NAMES = {"N": "Panel Layouts", "S": "Panel Types", "E": "UI Elements", "W": "Selection Masks"}


def draw_hotbox(state, region):
    lay = state["hotbox"]
    _rect((0, 0, region.width, region.height), DIM)
    cx, cy = lay.center
    p = lay.params
    for rect, key, label in lay.labels:
        _rect(rect, BG_HOVER if key == state.get("hover") else BG)
        _outline(rect, EDGE)
        _text(rect[0] + p.pad, rect[1] + (rect[3] - rect[1]) * 0.3, label, TEXT)
    _rect(lay.center_rect, BG)
    _outline(lay.center_rect, LINE)
    title = state.get("title", "Maya Kit")
    w = measure(title)
    _text(cx - w / 2, cy - p.item_h * 0.25, title, TEXT)
    if lay.style == "CENTER":
        return
    # Faint zone names at the region edges (discoverability; Maya draws none).
    faint = (1, 1, 1, 0.35)
    # Inset past the 3D View's overlapping header/toolbar regions.
    x0, _y0, x1, _y1 = lay.bounds or (0, 0, region.width, region.height)
    c0, _c1, c2, _c3 = lay.center_rect
    gap = 10 * ui_scale()
    for key, (x, y) in {"N": (cx, region.height - 4 * p.item_h), "S": (cx, 2 * p.item_h),
                        "E": (max(x1 - 140 * ui_scale(), c2 + gap), cy),
                        "W": (x0 + 90 * ui_scale(), cy)}.items():
        name = ZONE_NAMES[key]
        w = measure(name)
        if key == "W":
            x = min(x, c0 - gap - w)
        if key in "EW" and (x < x0 or x + w > x1):
            continue   # no room beside the centre box (cursor near an edge)
        _text(x - (w / 2 if key in "NS" else 0), y, name, faint)


# --- handler -----------------------------------------------------------------------------

def _callback():
    if not ACTIVE:
        return
    region = bpy.context.region
    if region is None or region.as_pointer() != ACTIVE.get("region"):
        return
    try:
        gpu.state.blend_set('ALPHA')
        if "hotbox" in ACTIVE:
            draw_hotbox(ACTIVE, region)
        if "session" in ACTIVE:
            draw_session(ACTIVE["session"], time.monotonic())
    except Exception:  # never let a draw error repeat every frame
        traceback.print_exc()
        ACTIVE.clear()
    finally:
        gpu.state.blend_set('NONE')


def register():
    for space in SPACES:
        _handles.append((space, space.draw_handler_add(_callback, (), 'WINDOW', 'POST_PIXEL')))


def unregister():
    ACTIVE.clear()
    while _handles:
        space, handle = _handles.pop()
        space.draw_handler_remove(handle, 'WINDOW')
