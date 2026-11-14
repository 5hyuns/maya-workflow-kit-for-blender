# SPDX-License-Identifier: GPL-3.0-or-later
"""Show > Selection Highlighting per 3D View (the panel menu row): views with highlighting off are kept on the screen
by area index (``HILITE_OFF``); Blender's outline goes off with it and comes back as it was (``highlighting``,
``set_highlighting``). Also ``_view``, the context's 3D View space. Related: ``selection_wire``, ``panel_state``.
"""

def _view(context):
    space = getattr(context, "space_data", None)
    return space if space is not None and space.type == 'VIEW_3D' else None


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
