# SPDX-License-Identifier: GPL-3.0-or-later
"""The mouse on the Time Slider's bookmark strip (Maya Workflow Kit layout, ``ui/time_slider_ruler.py`` draws it), like
Maya:

- hovering a bookmark shows its name and range next to the mouse;
- a right-click anywhere on the strip opens the bookmark menu (Create, Edit, Next / Previous Bookmark, Frame /
  Frame Previous / Frame Next Bookmark, Unframe, Update Bookmark with selection, Delete, Bookmark Manager); its items
  act at the frame under the mouse, not at the current time;
- a left click on a bookmark does not move the time (below the coloured bar the strip scrubs like the rest of the
  Time Slider); a double-click highlights the whole range as anywhere else, Ctrl + double-click highlights the
  bookmark's own range.

The hover is ``allset.time_slider_bookmark_hover`` (a "Time Scrub" mouse-move item that always passes through);
``allset.hover_leave`` (operators/graph_hover.py, a "Window" one) drops the label once the mouse leaves the Time
Slider. Pure
rules: ``strip_zone``, ``tip_text``.
"""

import bpy

from ..operators import bookmarks
from .time_slider_view import _is_timeline

_hover = {}             # area pointer -> (bookmark name, region x of the mouse)
_menu_at = {}           # "frame": the frame under the mouse when the strip menu opened


# --- geometry -----------------------------------------------------------------------------------------------------

def _maya_ruler(context):
    from .time_slider_header import has_slider_panel
    return _is_timeline(context) and has_slider_panel(context.space_data)


def strip_rows(region, scale):
    """((strip y0, y1), (bar y0, y1)) region rows of the bookmark strip and its coloured bar."""
    from .time_slider_ruler import ROWS_BOOKMARKS, _rows
    return _rows("strip", region.height, ROWS_BOOKMARKS, scale), _rows("bookmark", region.height, ROWS_BOOKMARKS,
                                                                       scale)


def strip_zone(y, strip, bar, on_bookmark):
    """'BAR' on a bookmark's coloured bar, 'STRIP' elsewhere on the strip, None below it (pure rule)."""
    if not strip[0] <= y <= strip[1] + 1:
        return None
    if on_bookmark and bar[0] <= y <= bar[1] + 1:
        return 'BAR'
    return 'STRIP'


def hit(context, region, mouse_x, mouse_y):
    """(zone, frame, bookmark) under window (mouse_x, mouse_y) in a Maya-layout Time Slider: zone 'BAR' / 'STRIP' /
    None (see ``strip_zone``), the whole frame under the mouse, the bookmark there (the latest-starting one)."""
    if region is None or region.type != 'WINDOW' or not _maya_ruler(context):
        return None, None, None
    if not bookmarks.shown(context):
        return None, None, None
    from .time_slider_mouse import frame_at
    s = context.preferences.system.ui_scale or 1.0
    strip, bar = strip_rows(region, s)
    f = frame_at(region, mouse_x)
    marker = bookmarks.bookmark_at(context.scene, f)
    zone = strip_zone(mouse_y - region.y, strip, bar, marker is not None)
    if zone is None:
        return None, f, None
    return zone, f, marker


def tip_text(scene, marker):
    """What hovering a bookmark shows: its name and range."""
    a, b = bookmarks.bookmark_range(scene, marker)
    return f"{marker.name}  {a} - {b}"


# --- hover --------------------------------------------------------------------------------------------------------

def hovered(area):
    return _hover.get(area.as_pointer()) if area is not None else None


class ALLSET_OT_time_slider_bookmark_hover(bpy.types.Operator):
    """Time Slider: remember the bookmark under the mouse to show its name and range"""
    bl_idname = "allset.time_slider_bookmark_hover"
    bl_label = "Time Slider Bookmark Hover"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        area = context.area
        if area is None or area.type != 'DOPESHEET_EDITOR':
            return {'PASS_THROUGH'}
        key = area.as_pointer()
        before = _hover.get(key)
        now = None
        try:
            zone, _f, marker = hit(context, context.region, event.mouse_x, event.mouse_y)
            if zone == 'BAR':
                now = (marker.name, event.mouse_region_x)
        except (AttributeError, ReferenceError):
            now = None
        if now is None:
            _hover.pop(key, None)
        else:
            _hover[key] = now
        if now != before:
            area.tag_redraw()
        return {'PASS_THROUGH'}


def forget_outside(wm, window, x, y):
    """Drop the shown bookmark of every Time Slider whose WINDOW region does not hold window (x, y) of ``window``;
    the areas to redraw."""
    from ..operators.graph_hover import inside
    gone = []
    for win in wm.windows:
        for area in win.screen.areas if win.screen is not None else ():
            key = area.as_pointer()
            if key not in _hover:
                continue
            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            if (win != window or region is None
                    or not inside(x, y, (region.x, region.y, region.width, region.height))):
                _hover.pop(key, None)
                gone.append(area)
    return gone


TIP_BG = (0.11, 0.11, 0.11, 0.95)
TIP_TEXT = (0.86, 0.86, 0.86, 1.0)
TIP_PAD_PX = 4


def draw_tip(context, region):
    """The hovered bookmark's name and range in a box next to the mouse, under the strip (the ruler's
    ``POST_PIXEL`` handler calls this last)."""
    shown = hovered(context.area)
    if shown is None:
        return
    marker = bookmarks.find(context.scene, shown[0])
    if marker is None:
        return
    import blf
    import gpu
    from gpu_extras.batch import batch_for_shader
    from .time_slider_ruler import label_font_size
    s = context.preferences.system.ui_scale or 1.0
    text = tip_text(context.scene, marker)
    blf.size(0, label_font_size(region.height, s))
    tw, th = blf.dimensions(0, text)
    pad = TIP_PAD_PX * s
    strip, _bar = strip_rows(region, s)
    w, h = tw + 2 * pad, th + 2 * pad
    x = min(max(0.0, shown[1] + 12 * s), max(0.0, region.width - w))
    y1 = strip[0] - 1
    y0 = max(0.0, y1 - h)
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    shader.uniform_float("color", TIP_BG)
    batch_for_shader(shader, 'TRIS', {"pos": ((x, y0), (x + w, y0), (x + w, y1), (x, y0), (x + w, y1),
                                               (x, y1))}).draw(shader)
    blf.color(0, *TIP_TEXT)
    blf.position(0, x + pad, y0 + pad, 0)
    blf.draw(0, text)
    gpu.state.blend_set('NONE')


# --- clicks -------------------------------------------------------------------------------------------------------

class ALLSET_OT_time_slider_bookmark_click(bpy.types.Operator):
    """Time Slider bookmark: a click does not move the time; Ctrl + double-click highlights the bookmark's range"""
    bl_idname = "allset.time_slider_bookmark_click"
    bl_label = "Time Slider Bookmark Click"
    bl_options = {'INTERNAL'}

    double: bpy.props.BoolProperty(options={'SKIP_SAVE', 'HIDDEN'}, description="A double-click")

    def invoke(self, context, event):
        from .time_slider_mouse import _second_press, set_range, _tag
        from .time_slider_view import playback_range
        region = context.region
        zone, _f, marker = hit(context, region, event.mouse_x, event.mouse_y)
        if zone != 'BAR':
            return {'PASS_THROUGH'}
        second = self.double or _second_press(context, event, region)
        if second:
            wm = context.window_manager
            if event.ctrl:
                set_range(wm, *bookmarks.bookmark_range(context.scene, marker))
            else:
                set_range(wm, *playback_range(context.scene))
            _tag(context)
        return {'FINISHED'}


# --- the strip's right-click menu ---------------------------------------------------------------------------------

def menu_frame():
    return _menu_at.get("frame")


class ALLSET_MT_time_slider_bookmarks(bpy.types.Menu):
    """Maya's Time Slider bookmark menu (right-click on the bookmark strip): the actions work at the frame under the
    mouse"""
    bl_label = "Time Slider Bookmarks"

    def draw(self, context):
        lay = self.layout
        f = menu_frame()
        if f is None:
            f = context.scene.frame_current

        def at(idname, text="", **props):
            op = lay.operator(idname, text=text)
            op.use_at_frame, op.at_frame = True, f
            for k, v in props.items():
                setattr(op, k, v)
        lay.operator("allset.bookmark_create", text="Create")
        at("allset.bookmark_edit", text="Edit")
        at("allset.bookmark_go", text="Next Bookmark")
        at("allset.bookmark_go", text="Previous Bookmark", previous=True)
        at("allset.bookmark_frame", text="Frame Bookmark", which='CURRENT')
        at("allset.bookmark_frame", text="Frame Previous Bookmark", which='PREVIOUS')
        at("allset.bookmark_frame", text="Frame Next Bookmark", which='NEXT')
        lay.operator("allset.playback_range_anim", text="Unframe")
        at("allset.bookmark_update", text="Update Bookmark with selection")
        at("allset.bookmark_delete", text="Delete")
        lay.separator()
        lay.operator("allset.bookmark_manager", text="Bookmark Manager")


def open_menu(context, event):
    """Open the bookmark menu when the right-click is on the strip; False elsewhere."""
    zone, f, _marker = hit(context, context.region, event.mouse_x, event.mouse_y)
    if zone is None:
        return False
    _menu_at["frame"] = f
    bpy.ops.wm.call_menu(name=ALLSET_MT_time_slider_bookmarks.__name__)
    return True


classes = (ALLSET_OT_time_slider_bookmark_hover, ALLSET_OT_time_slider_bookmark_click, ALLSET_MT_time_slider_bookmarks)


def clear():
    _hover.clear()
    _menu_at.clear()
