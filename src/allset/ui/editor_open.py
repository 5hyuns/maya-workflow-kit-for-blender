# SPDX-License-Identifier: GPL-3.0-or-later
"""After an editor is opened from a Maya menu: frame the playback range from frame 1, fold the Dope Sheet to object
rows, show the UV Editor's tool header and UV Toolkit tab (``prepare_later``, a timer; ``frame_playback_range``).
"""

import bpy

from .. import live_refs


# --- opening an editor the Maya way ----------------------------------------------------------------------------

def frame_playback_range(context, area):
    """Horizontal view = the playback range from frame 1 (Maya: no frame 0 / out-of-range area at the left)."""
    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
    if region is None or region.width < 2:
        return False
    with context.temp_override(window=context.window, area=area, region=region):
        if area.type == 'GRAPH_EDITOR':
            bpy.ops.graph.view_all()
        bpy.ops.anim.scene_range_frame()
        sc = context.scene
        start = sc.frame_preview_start if sc.use_preview_range else sc.frame_start
        lo, _ = region.view2d.region_to_view(0, 0)
        hi, _ = region.view2d.region_to_view(region.width, 0)
        per_px = (hi - lo) / region.width if hi > lo else 0
        if per_px > 0:
            dx = int(round(((start - 0.5) - lo) / per_px))
            if dx:
                bpy.ops.view2d.pan(deltax=dx, deltay=0)
    return True


def prepare_later(window, ui_type, tries=60):
    """After ``allset.open_editor``: frame the playback range (Graph Editor / Dope Sheet), fold the Dope Sheet to
    object rows (Maya Dopesheet Summary + objects), show the UV Editor's tool header and UV Toolkit. From a timer:
    a new window's regions have no size inside the operator."""
    state = {"n": tries}
    ptr = window.as_pointer()

    def tick():
        window = live_refs.window(ptr)     # the pointer, looked up each tick: a closed window crashes (#36)
        if window is None:
            return None
        try:
            area = window.screen.areas[0]
            if area.ui_type != ui_type:
                return None
            space = area.spaces.active
            ctx = bpy.context
            with ctx.temp_override(window=window, area=area):
                if ui_type == 'UV':
                    space.show_region_tool_header = True
                    space.show_region_toolbar = False
                    from ..operators.menu_extras import sidebar_tab_later
                    from .uv_toolkit import CATEGORY
                    sidebar_tab_later(window, CATEGORY)
                    return None
                space.show_region_ui = False    # Maya's Graph Editor / Dope Sheet have no side panel
                if not frame_playback_range(ctx, area):
                    state["n"] -= 1
                    return 0.05 if state["n"] > 0 else None
                if ui_type == 'DOPESHEET':
                    chan = next((r for r in area.regions if r.type == 'CHANNELS'), None)
                    if chan is not None:
                        with ctx.temp_override(window=window, area=area, region=chan):
                            bpy.ops.anim.channels_collapse(all=True)
                    space.dopesheet.show_expanded_summary = True     # Dopesheet Summary open, objects folded
                area.tag_redraw()
        except (ReferenceError, AttributeError, IndexError, RuntimeError):
            return None
        return None

    bpy.app.timers.register(tick, first_interval=0.05)
