# SPDX-License-Identifier: GPL-3.0-or-later
"""GPU drawing of the marking menu engine and the hotbox.

POST_PIXEL draw handlers per editor type and region type, added once at register.
Maya's menus float over the whole window (step 52): the modal operators work in the
coordinates of the region they were invoked in, and every region of that window draws
the same picture moved by its offset from that region (each region clips its own
part), so menus also cover sidebars, toolbars and neighbouring editors. Other
windows / no menu: a single dictionary lookup.
 #4 (:53): ``draw_handler_add`` + ``gpu`` + ``blf``.
"""

import time
import traceback

import blf
import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from . import engine

# The interaction being drawn: {"region": pointer, "window": pointer, "origin": (x, y) of that region
# in the window, "session": Session} or {..., "hotbox": HotboxLayout, "hover": key, ...}; empty = nothing.
ACTIVE = {}

# Editors the menus open in (marking menus, hotbox) ...
SPACES = (bpy.types.SpaceView3D, bpy.types.SpaceOutliner, bpy.types.SpaceGraphEditor,
          bpy.types.SpaceDopeSheetEditor, bpy.types.SpaceNodeEditor, bpy.types.SpaceImageEditor)
# ... and every editor they may cover (step 52).
COVER_SPACES = SPACES + tuple(getattr(bpy.types, n) for n in (
    "SpaceProperties", "SpaceNLA", "SpaceSequenceEditor", "SpaceClipEditor", "SpaceTextEditor",
    "SpaceConsole", "SpaceInfo", "SpaceFileBrowser", "SpaceSpreadsheet", "SpacePreferences")
    if hasattr(bpy.types, n))
# 'HUD' = the Adjust Last Operation panel, drawn over the view: without it the RMB list went under it (step 91).
REGION_TYPES = ('WINDOW', 'UI', 'TOOLS', 'HEADER', 'TOOL_HEADER', 'CHANNELS', 'FOOTER', 'HUD')

# Maya greys and selection blue #5285A6. Menu boxes and the list body: #525252
# ( ui_samples marking_menu_box / marking_menu_list_bg, step 52).
BG = (0x52 / 255, 0x52 / 255, 0x52 / 255, 1.0)
DIVIDER = (0x3a / 255, 0x3a / 255, 0x3a / 255, 1.0)
BG_HOVER = (0.32, 0.52, 0.65, 1.0)
EDGE = (0.12, 0.12, 0.12, 1.0)
TEXT = (0.92, 0.92, 0.92, 1.0)
TEXT_OFF = (0.55, 0.55, 0.55, 1.0)
LINE = (0.95, 0.95, 0.95, 0.9)

_handles = []
_shader = None


def ui_scale():
    return bpy.context.preferences.system.ui_scale


def font_size():
    # Maya menus: Segoe UI 11 px at Qt dpr 1.0 ( metrics.font) = Blender's 11 pt
    # widget text at an effective scale of 1.0 (the Maya density preset, ).
    # blf font 0 is the interface font, so it is Segoe UI when view.font_path_ui points there.
    return max(8, round(11 * ui_scale()))


# Submenu arrow: drawn as a triangle, not the "▸" glyph. A UI font without it (Segoe UI, the Maya Font
# preference) makes blf.dimensions return millions of pixels (checked, step 52: the RMB list spanned the view).
ARROW = " ▸"


def _arrow_w():
    return font_size() * 0.9


def measure(text):
    blf.size(0, font_size())
    if text.endswith(ARROW):
        return blf.dimensions(0, text[:-len(ARROW)])[0] + _arrow_w()
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
    arrow = s.endswith(ARROW)
    if arrow:
        s = s[:-len(ARROW)]
    blf.color(0, *color)
    blf.position(0, x, y, 0)
    blf.draw(0, s)
    if arrow:   # a small right-pointing triangle after the text
        k = font_size()
        ax = x + blf.dimensions(0, s)[0] + k * 0.35
        ay = y + k * 0.35
        sh = _sh()
        batch = batch_for_shader(sh, 'TRIS', {"pos": ((ax, ay - k * 0.25), (ax, ay + k * 0.25), (ax + k * 0.3, ay))})
        sh.uniform_float("color", color)
        batch.draw(sh)


def _circle(cx, cy, r, color, segments=24):
    import math
    pts = [(cx + r * math.cos(2 * math.pi * i / segments), cy + r * math.sin(2 * math.pi * i / segments))
           for i in range(segments + 1)]
    _line(pts, color, 1.5)


# --- marking menu -------------------------------------------------------------------

# On = filled light blue: the step-26 selection blue (0.32, 0.52, 0.65) hardly differed from the
# empty box in the step-31 screenshot.
CHECK = (0.45, 0.72, 0.95, 1.0)


def checked(action):
    """On/off state of a toggle item (None for other items); step 26."""
    if not engine.is_toggle(action):
        return None
    op, props = action
    try:
        if op == "wm.context_toggle":
            return bool(bpy.context.path_resolve(props["data_path"]))
        if op == "allset.symmetry":
            from ..operators import symmetry
            return symmetry.item_state(props["mode"])
        if op == "allset.pivot_option":          # pivot edit menu check boxes (step 94)
            from ..operators import pivot_menu
            return pivot_menu.option(props["option"])
        if op == "allset.component_mask":        # Shift+Q check boxes = the mesh select modes (step 93)
            mask = bpy.context.scene.tool_settings.mesh_select_mode
            return bool(mask[engine.MASK_CHECKS.index(props["kind"])])
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
    _draw_list_body(lay, cx, cy)
    for it in lay.items:
        on = it is hover
        if it.kind == "radial" or (on and not hover_opt and it.enabled):
            _rect(it.rect, BG_HOVER if on and not hover_opt and it.enabled else BG, cx, cy)
        if it.kind == "radial":
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
                _rect((box[0] + 1, box[1] + 1, box[2] - 1, box[3] - 1), CHECK, cx, cy)
        if it.opt_rect:
            if on and hover_opt:
                _rect(it.opt_rect, BG_HOVER, cx, cy)
            inner = (it.opt_rect[0] + 4, it.opt_rect[1] + 4, it.opt_rect[2] - 4, it.opt_rect[3] - 4)
            _outline(inner, TEXT if it.enabled else TEXT_OFF, cx, cy)


def _draw_list_body(lay, cx, cy):
    """The list under the ring as one menu body per column with divider lines (14_marking_menu_object.png)."""
    columns = {}
    for it in lay.items:
        if it.kind == "list":
            columns.setdefault(round(it.rect[0], 3), []).append(it)
    for rows in columns.values():
        body = (rows[0].rect[0], min(it.rect[1] for it in rows), rows[0].rect[2], max(it.rect[3] for it in rows))
        _rect(body, BG, cx, cy)
        _outline(body, EDGE, cx, cy)
        for a, b in zip(rows, rows[1:]):
            if a.rect[1] - b.rect[3] > 0.5:   # a divider gap
                y = (a.rect[1] + b.rect[3]) / 2 + cy
                _line([(body[0] + cx + 4, y), (body[2] + cx - 4, y)], DIVIDER, 1.0)


# --- hotbox ---------------------------------------------------------------------------

# Maya hotbox (13_hotbox.png): no dimming; each row is one translucent strip (#444444 at 70 % = #4c4c4c over
# Maya's #5c5c5c view, colors.json ui_samples hotbox_row_bg), the hovered menu name lights up, the centre box
# shows "Maya", four short white diagonal lines mark the zones (no zone names).
ROW_BG = (0x44 / 255, 0x44 / 255, 0x44 / 255, 0.7)
ROW_TEXT = (0xbb / 255, 0xbb / 255, 0xbb / 255, 1.0)
ZONE_LINE = (0.95, 0.95, 0.95, 0.9)


def draw_hotbox(state, region, own=True):
    lay = state["hotbox"]
    cx, cy = lay.center
    p = lay.params
    for band in lay.bands:
        _rect(band, ROW_BG)
    for rect, key, label in lay.labels:
        hover = key == state.get("hover")
        if hover:
            _rect(rect, BG_HOVER)
        _text(rect[0] + p.pad, rect[1] + (rect[3] - rect[1]) * 0.3, label, TEXT if hover else ROW_TEXT)
    _rect(lay.center_rect, ROW_BG)
    title = lay.title
    w = measure(title)
    r = lay.center_rect
    _text(cx - w / 2, r[1] + (r[3] - r[1]) * 0.3, title, ROW_TEXT)
    for a, b in lay.zone_lines:
        _line([a, b], ZONE_LINE, 1.0)


def _overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


# --- handler -----------------------------------------------------------------------------

_window = {"ptr": None}     # the last window drawn into (redraw after ACTIVE is cleared)


def activate(window, region, **state):
    """Start drawing ``state`` (session / hotbox ...) for ``region`` over all of ``window``."""
    ACTIVE.clear()
    ACTIVE.update(state, region=region.as_pointer(), window=window.as_pointer(), origin=(region.x, region.y))
    _window["ptr"] = window.as_pointer()


def window_bounds(window, region):
    """The window's editors (not its global top bar / status bar) in ``region`` pixels."""
    areas = window.screen.areas if window and window.screen else ()
    if not areas:
        return (0, 0, region.width, region.height)
    x0 = min(a.x for a in areas)
    y0 = min(a.y for a in areas)
    x1 = max(a.x + a.width for a in areas)
    y1 = max(a.y + a.height for a in areas)
    return (x0 - region.x, y0 - region.y, x1 - region.x, y1 - region.y)


def redraw():
    """Redraw every editor of the menu's window (the picture spans regions)."""
    ptr = ACTIVE.get("window", _window["ptr"])
    for window in bpy.context.window_manager.windows:
        if window.as_pointer() == ptr and window.screen:
            for area in window.screen.areas:
                area.tag_redraw()


def _callback():
    if not ACTIVE:
        return
    context = bpy.context
    region, window = context.region, context.window
    if region is None or window is None or window.as_pointer() != ACTIVE.get("window"):
        return
    ox, oy = ACTIVE["origin"]
    own = region.as_pointer() == ACTIVE.get("region")
    try:
        gpu.state.blend_set('ALPHA')
        gpu.matrix.push()
        gpu.matrix.translate((ox - region.x, oy - region.y))
        if "hotbox" in ACTIVE:
            draw_hotbox(ACTIVE, region, own)
        if "session" in ACTIVE:
            draw_session(ACTIVE["session"], time.monotonic())
    except Exception:  # never let a draw error repeat every frame
        traceback.print_exc()
        ACTIVE.clear()
    finally:
        gpu.matrix.pop()
        gpu.state.blend_set('NONE')


def register():
    for space in COVER_SPACES:
        for region_type in REGION_TYPES:
            try:
                _handles.append((space, region_type,
                                 space.draw_handler_add(_callback, (), region_type, 'POST_PIXEL')))
            except (TypeError, ValueError, RuntimeError):
                pass   # this editor has no such region


def unregister():
    ACTIVE.clear()
    while _handles:
        space, region_type, handle = _handles.pop()
        space.draw_handler_remove(handle, region_type)
