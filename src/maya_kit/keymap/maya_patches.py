# SPDX-License-Identifier: GPL-3.0-or-later
"""Patches that turn Industry Compatible data into the "Maya" keyconfig.

``IC:<line>`` = ``$S\\presets\\keyconfig\\keymap_data\\industry_compatible_data.py``.
Plan and rationale: 

``ADDED`` lists every binding this module adds; tests use it for the
shadowing check and  is cross-checked against it.
"""

from .patch import KeyconfigData, make_event

# (km_name, idname, event, props) for every binding added below.
ADDED = []


def _add(kd, km_name, idname, event, props=None):
    kd.add(km_name, idname, event, props)
    ADDED.append((km_name, idname, event, dict(props or {})))


# --- 1. Selection modifiers ----------------------------------------------
# Maya: Shift = toggle, Ctrl = deselect, Ctrl+Shift = add, for click and
# marquee (). Order of variants:
# (shift, ctrl) = none, Shift, Ctrl, Ctrl+Shift.

def _click(plain, toggle, deselect, add):
    return [((False, False), plain), ((True, False), toggle),
            ((False, True), deselect), ((True, True), add)]


# Operators with a real ``deselect`` option ().
_CLICK_EXACT = _click({"deselect_all": True}, {"toggle": True},
                      {"deselect": True}, {"extend": True})

# outliner.item_activate / graph.clickselect have no ``deselect`` option, so
# Ctrl and Ctrl+Shift fall back to toggle (workaround, ).
_OUTLINER_CLICK = _click({"extend": False, "deselect_all": True},
                         {"extend": True, "deselect_all": True},
                         {"extend": True, "deselect_all": True},
                         {"extend": True, "deselect_all": True})
_GRAPH_CLICK = _click({"extend": False, "deselect_all": True},
                      {"extend": True}, {"extend": True}, {"extend": True})

_BOX = _click({"mode": "SET"}, {"mode": "XOR"}, {"mode": "SUB"}, {"mode": "ADD"})
# uv/outliner/graph select_box only have SET/ADD/SUB (no XOR): Shift adds
# instead of toggling (workaround, ).
_BOX_NO_XOR = _click({"mode": "SET"}, {"mode": "ADD"}, {"mode": "SUB"}, {"mode": "ADD"})

SELECT_RULES = (
    # idname, event value, variants, props kept from IC's plain item
    ("view3d.select", "CLICK", _CLICK_EXACT, ()),          # IC "3D View" (dump), viewport
    ("view3d.select", "PRESS", _CLICK_EXACT, ()),          # "3D View Tool: Tweak"
    ("uv.select", "CLICK", _CLICK_EXACT, ()),              # "UV Editor"
    ("uv.select", "PRESS", _CLICK_EXACT, ()),              # "Image Editor Tool: Uv, Tweak"
    ("outliner.item_activate", "CLICK", _OUTLINER_CLICK, ()),
    ("graph.clickselect", "PRESS", _GRAPH_CLICK, ("column", "curves")),
    ("view3d.select_box", "CLICK_DRAG", _BOX, ("tweak",)),
    ("uv.select_box", "CLICK_DRAG", _BOX_NO_XOR, ("tweak",)),
    ("outliner.select_box", "CLICK_DRAG", _BOX_NO_XOR, ("tweak",)),
    ("graph.select_box", "CLICK_DRAG", _BOX_NO_XOR, ("tweak", "axis_range")),
)


def patch_selection(kd):
    # IC:935 Ctrl+Shift+LMB = select keys left/right of the frame; Maya has no
    # such binding and Ctrl+Shift click must add to the selection.
    kd.remove("Graph Editor", "graph.select_leftright", type="LEFTMOUSE",
              shift=True, ctrl=True)
    touched = {}
    for idname, value, variants, keep in SELECT_RULES:
        kms = kd.rewrite_modifier_set(idname, value, variants, keep_props=keep)
        if not kms:
            raise LookupError(f"selection patch: {idname} {value} not found in IC data")
        touched[(idname, value)] = kms
    return touched


# --- 2. 4/5/6/7 display modes ---------------------------------------------
# Maya: 4 wireframe, 5 shaded, 6 shaded+textured, 7 all lights
# (; hotkeys_default.json "4".."7").

DISPLAY_KEYS = (("FOUR", "WIREFRAME"), ("FIVE", "SHADED"),
                ("SIX", "TEXTURED"), ("SEVEN", "LIGHTS"))


def patch_display(kd):
    # IC:3458-3459 "Object Non-modal": 4 = object mode, 5 = mode pie.
    kd.remove("Object Non-modal", "object.mode_set", type="FOUR")
    kd.remove("Object Non-modal", "wm.call_menu_pie", type="FIVE")
    for key, mode in DISPLAY_KEYS:
        _add(kd, "3D View", "maya_kit.display_mode", make_event(key), {"mode": mode})
    # Losing 4 = object mode leaves no quick way out of edit mode; Maya's F8
    # toggles object <-> last component mode ().
    _add(kd, "Object Non-modal", "object.editmode_toggle", make_event("F8"))


# --- 3. Ctrl+G group --------------------------------------------------------
# Maya Ctrl+G = group under common parent, pivot at origin
# (). IC Ctrl+G = move to collection (IC:2547).

def patch_group(kd):
    for km in ("Object Mode", "Outliner"):
        kd.remove(km, "object.move_to_collection", type="G", ctrl=True)
        _add(kd, km, "maya_kit.group", make_event("G", ctrl=True))


# --- 4. Space reserved for the hotbox ---------------------------------------
# Maya Space = hotbox ( "Space" ShowHotbox),
# implemented in step 11; until then Space does nothing in editors.
# Playback moves to Maya's Alt+V (PlaybackToggle) and Alt+Shift+V (GoToMinFrame).

def patch_space(kd):
    kd.remove("Frames", "screen.animation_play", type="SPACE")  # IC:2258
    _add(kd, "Frames", "screen.animation_play", make_event("V", alt=True))
    _add(kd, "Frames", "screen.frame_jump", make_event("V", alt=True, shift=True), {"end": False})


PATCHES = (patch_selection, patch_display, patch_group, patch_space)


def apply(data):
    """Apply all patches to IC data in place and return it."""
    ADDED.clear()
    kd = KeyconfigData(data)
    for patch in PATCHES:
        patch(kd)
    return data
