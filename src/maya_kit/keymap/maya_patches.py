# SPDX-License-Identifier: GPL-3.0-or-later
"""Patches that turn Industry Compatible data into the "Maya" keyconfig.

``IC:<line>`` = ``$S\\presets\\keyconfig\\keymap_data\\industry_compatible_data.py``.
Plan and rationale:  (1-4),  (5-8),
 (9-13),  (16),  (17),
 (18),  (19),  (20),
 (21),  (22),  (23),  (24).

``ADDED`` lists every binding this module adds; tests use it for the
shadowing check and  is cross-checked against it.
"""

from . import patch
from .patch import KeyconfigData, make_event

# (km_name, idname, event, props, shadows) for every binding added below.
# ``shadows``: keymaps allowed to bind the same event in the same editor
# (intentional: e.g. paint modes keep their own X/B).
ADDED = []


# Operators that return PASS_THROUGH when they don't apply, so they may sit in
# front of another item with the same event in the same keymap.
PASS_THROUGH_FIRST = ("maya_kit.cb_virtual_slider", "maya_kit.time_range_drag", "maya_kit.manip_ctrl", "maya_kit.manip_duplicate", "maya_kit.manip_press",
                      "maya_kit.select_priority", "maya_kit.select_through", "maya_kit.toolbox_guard", "maya_kit.time_scrub",
                      "maya_kit.time_slider_menu")


def _add(kd, km_name, idname, event, props=None, shadows=(), first=False):
    kd.add(km_name, idname, event, props, first=first)
    ADDED.append((km_name, idname, event, dict(props or {}), tuple(shadows)))


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
            if not patch.STRICT:   # another Blender's IC data (step 53)
                patch.DRIFT.append(f"selection patch: {idname} {value} not found")
                continue
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
    # maya_kit.toggle_sel_mode = editmode_toggle + Maya's in-view message (step 72).
    _add(kd, "Object Non-modal", "maya_kit.toggle_sel_mode", make_event("F8"))


# --- 3. Ctrl+G group --------------------------------------------------------
# Maya Ctrl+G = group under common parent, pivot at origin
# (). IC Ctrl+G = move to collection (IC:2547; Blender 5.x: the same as a
# wm.call_menu of OBJECT_MT_move_to_collection, step 53), so the item is removed whatever its operator.

def patch_group(kd):
    for km in ("Object Mode", "Outliner"):
        kd.remove(km, None, type="G", ctrl=True)
        _add(kd, km, "maya_kit.group", make_event("G", ctrl=True))


# --- 4. Space reserved for the hotbox ---------------------------------------
# Maya Space = hotbox ( "Space" ShowHotbox),
# implemented in step 10; until then Space does nothing in other editors.
# Playback moves to Maya's Alt+V (PlaybackToggle) and Alt+Shift+V (GoToMinFrame).

def patch_space(kd):
    kd.remove("Frames", "screen.animation_play", type="SPACE")  # IC:2258
    _add(kd, "Frames", "screen.animation_play", make_event("V", alt=True))
    _add(kd, "Frames", "screen.frame_jump", make_event("V", alt=True, shift=True), {"end": False})


# --- 5. Hold keys: X/C/V/J snapping ------------------------------------------
# Maya: snapping only while the key is held, Shift variants identical
# (; hotkeys_default.json x/X, c/C, v/V, j).
# Paint/sculpt modes keep their own X (brush color flip): they are checked
# before "3D View", so the hold never runs there.
_PAINT_MODES = ("Sculpt", "Vertex Paint", "Image Paint", "Weight Paint")

HOLD_KEYS = (("X", "grid"), ("C", "curve"), ("V", "point"), ("J", "step"))


def patch_hold_snap(kd):
    kd.remove("3D View", "wm.context_toggle", type="X")                 # IC:780 snap toggle
    kd.remove("3D View", "wm.call_menu_pie", type="X", shift=True)      # snap pie
    kd.remove("3D View", "wm.call_menu_pie", type="V")                  # view pie
    for km in ("Object Mode", "Mesh", "Curve", "Curves", "Armature", "Metaball"):
        kd.remove(km, "wm.tool_set_by_id", type="C")                     # cursor tool
    for key, name in HOLD_KEYS:
        for shift in (False, True):
            _add(kd, "3D View", "maya_kit.hold", make_event(key, shift=shift), {"name": name},
                 shadows=_PAINT_MODES)


# --- 6. B soft select (tap toggle, hold + LMB drag radius) ------------------
# 

def patch_soft_select(kd):
    for km in ("Object Mode", "Mesh", "Curve", "Curves", "Metaball", "Lattice", "Particle"):
        kd.remove(km, "wm.context_toggle", type="B")                     # IC:2517, IC:3066
    _add(kd, "3D View", "maya_kit.tap_hold", make_event("B"), {"binding": "soft_select"},
         shadows=_PAINT_MODES)


# --- 7. A tap / hold, D hold pivot, Insert pivot toggle ---------------------
# A:  (tap = FrameAll, hold = marking menu).
# D / Insert: interaction.md:124-125 (pivot edit while held / toggle).

def patch_tap_hold_and_pivot(kd):
    kd.remove("3D View", "view3d.view_all", type="A")
    _add(kd, "3D View", "maya_kit.tap_hold", make_event("A"), {"binding": "select_all"},
         shadows=("Sculpt",))
    kd.remove("Object Mode", "wm.tool_set_by_id", type="D")              # IC:121 annotate
    _add(kd, "Object Mode", "maya_kit.hold", make_event("D"), {"name": "pivot"})
    _add(kd, "Object Mode", "maya_kit.pivot_toggle", make_event("INSERT"))


# --- 8. Arrow-key pick-walk (object mode) -----------------------------------
#  (HK:364-369). IC puts Left/Right frame
# stepping into each mode keymap (IC:93-97 _template_items_animation); only
# Object Mode's copy is replaced. Maya steps frames with Alt+,/. (step 7).

PICK_WALK_KEYS = (("UP_ARROW", "UP"), ("DOWN_ARROW", "DOWN"),
                  ("LEFT_ARROW", "LEFT"), ("RIGHT_ARROW", "RIGHT"))


def patch_pick_walk(kd):
    kd.remove("Object Mode", "object.select_more", type="UP_ARROW")
    kd.remove("Object Mode", "object.select_less", type="DOWN_ARROW")
    kd.remove("Object Mode", "screen.frame_offset", type="LEFT_ARROW")
    kd.remove("Object Mode", "screen.frame_offset", type="RIGHT_ARROW")
    for key, direction in PICK_WALK_KEYS:
        _add(kd, "Object Mode", "maya_kit.pick_walk", make_event(key, repeat=True),
             {"direction": direction})


# --- 9. Camera: ortho tumble lock, framing in all views ----------------------
#  (Alt+LMB tumble), :192-195 (Shift+F / Shift+A).

def patch_camera(kd):
    kd.remove("3D View", "view3d.rotate", type="LEFTMOUSE", alt=True)       # IC:674
    _add(kd, "3D View", "maya_kit.tumble", make_event("LEFTMOUSE", alt=True))
    kd.remove("3D View", "view3d.view_center_pick", type="F", shift=True)
    _add(kd, "3D View", "maya_kit.frame_all_views", make_event("F", shift=True), {"selected": True})
    # Step 17: Maya fit (factor 0.95, sidebar excluded) for F and Ctrl+Shift+F (with children);
    # A tap goes through taphold.SelectAllBinding ().
    kd.remove("3D View", "view3d.view_selected", type="F")                  # IC:681
    _add(kd, "3D View", "maya_kit.frame", make_event("F"), {"selected": True})
    _add(kd, "3D View", "maya_kit.frame_all_views", make_event("F", shift=True, ctrl=True),
         {"selected": True, "children": True})
    kd.remove("3D View", "view3d.view_all", type="A", shift=True)
    _add(kd, "3D View", "maya_kit.frame_all_views", make_event("A", shift=True), {"selected": False},
         shadows=("Sculpt",))


# --- 10. View-change undo: [ ] and Alt+Z / Alt+Y ----------------------------
#  (HK:234-237). IC [ ] = select_hierarchy
# (IC:2506-2512), replaced by the arrow pick-walk in step 3. Paint modes keep
# [ ] for brush size.

def patch_view_history(kd):
    kd.remove("Object Mode", "object.select_hierarchy", type="LEFT_BRACKET")
    kd.remove("Object Mode", "object.select_hierarchy", type="RIGHT_BRACKET")
    for ev, direction in ((make_event("LEFT_BRACKET"), "UNDO"), (make_event("RIGHT_BRACKET"), "REDO"),
                          (make_event("Z", alt=True), "UNDO"), (make_event("Y", alt=True), "REDO")):
        _add(kd, "3D View", "maya_kit.view_history", ev, {"direction": direction},
             shadows=_PAINT_MODES + ("Armature",))


# --- 11. Space tap = four views, Ctrl+Space = full screen -------------------
#  Space hold = hotbox (step 10).

# Space = hotbox (step 9; tap = pane toggle, Maya). Also in the editors
# the hotbox South zone switches a pane to, so the hotbox can switch it back; Space is
# free there since patch_space (IC used it only in "Frames"). Not in text editors.
HOTBOX_KEYMAPS = ("3D View", "Outliner", "Graph Editor", "Dopesheet", "Node Editor", "Image")


def patch_space_tap(kd):
    for km in HOTBOX_KEYMAPS:
        _add(kd, km, "maya_kit.hotbox", make_event("SPACE"))
    _add(kd, "Screen", "screen.screen_full_area", make_event("SPACE", ctrl=True),
         {"use_hide_panels": True})


# --- 12. 1/2/3 smooth mesh preview -------------------------------------------
#  IC 1/2/3 = component modes
# (IC:2558-2563 Object Mode, IC:164-177 Mesh), now on F9-F11.

SMOOTH_KEYS = (("ONE", 1), ("TWO", 2), ("THREE", 3))


def patch_smooth_preview(kd):
    for key, level in SMOOTH_KEYS:
        kd.remove("Object Mode", "object.mode_set_with_submode", type=key)
        kd.remove("Mesh", "mesh.select_mode", type=key)
        for km in ("Object Mode", "Mesh"):
            _add(kd, km, "maya_kit.smooth_preview", make_event(key), {"level": level})


# --- 13. F7/F9/F10/F11 component modes ---------------------------------------
#  F8 = editmode_toggle (patch 2).

COMPONENT_KEYS = (("F9", "VERT"), ("F10", "EDGE"), ("F11", "FACE"), ("F7", "MULTI"))


def patch_component_keys(kd):
    for key, comp in COMPONENT_KEYS:
        _add(kd, "Object Non-modal", "maya_kit.component_mode", make_event(key), {"type": comp})


# --- 14. Channel Box MMB virtual slider ---------------------------------------
#  Tool keymaps run before "3D View" and IC
# gives Move/Rotate/Scale/Transform an MMB drag (IC:3823-3858), so the slider
# goes first in those; it passes through when no channel is selected.

SLIDER_TOOL_KEYMAPS = ("3D View Tool: Move", "3D View Tool: Rotate", "3D View Tool: Scale",
                       "3D View Tool: Transform")


def patch_cb_slider(kd):
    for km in SLIDER_TOOL_KEYMAPS:
        _add(kd, km, "maya_kit.cb_virtual_slider", make_event("MIDDLEMOUSE"), first=True,
             shadows=(km,))
    _add(kd, "Object Mode", "maya_kit.cb_virtual_slider", make_event("MIDDLEMOUSE"))


# --- 15. Marking menus (pies) and Q/W/E/R hold + LMB ----
#  (:227-243). IC's RMB context menus in these
# modes give way to the Maya marking menus; Shift+RMB 3D cursor goes (no 3D cursor in Maya).

MM_KEYMAPS = (("Object Mode", "VIEW3D_MT_object_context_menu"),
              ("Mesh", "VIEW3D_MT_edit_mesh_context_menu"),
              ("Curve", "VIEW3D_MT_edit_curve_context_menu"))
MM_EVENTS = (("RMB", {}), ("SHIFT_RMB", {"shift": True}), ("CTRL_RMB", {"ctrl": True}),
             ("TOOL_OPTIONS", {"shift": True, "ctrl": True}))
# Modes whose IC keymap sets the Q/W/E/R tools (IC _template_items_tool_select etc.).
TOOL_KEY_KEYMAPS = ("Object Mode", "Mesh", "Curve", "Armature", "Pose", "Metaball", "Lattice", "Curves")
TOOL_KEYS = (("Q", "tool_select"), ("W", "tool_move"), ("E", "tool_rotate"), ("R", "tool_scale"))


def patch_marking_menus(kd):
    for km, menu in MM_KEYMAPS:
        kd.remove(km, "wm.call_menu", type="RIGHTMOUSE")
        for trigger, mods in MM_EVENTS:
            _add(kd, km, "maya_kit.marking_menu", make_event("RIGHTMOUSE", **mods), {"trigger": trigger})
    kd.remove("3D View", "view3d.cursor3d", type="RIGHTMOUSE", shift=True)
    kd.remove("3D View", "transform.translate", type="RIGHTMOUSE", value="CLICK_DRAG", shift=True)
    for km in TOOL_KEY_KEYMAPS:
        for key, binding in TOOL_KEYS:
            kd.remove(km, "wm.tool_set_by_id", type=key)
            _add(kd, km, "maya_kit.tap_hold", make_event(key), {"binding": binding})


# --- 16. Scene concepts: P / Shift+P, Shift+D, Ctrl+Shift+D, Alt+Shift+D ----
#  p Parent, P Unparent, D DuplicateWithTransform,
# Ctrl+D (capital) DuplicateSpecial, Alt+D (capital) DeleteHistory (concepts.md:68, :98).
# IC Object Mode P / Shift+P = object.parent_set / parent_clear.

def patch_concepts(kd):
    kd.remove("Object Mode", "object.parent_set", type="P")
    kd.remove("Object Mode", "object.parent_clear", type="P", shift=True)
    for km in ("Object Mode", "Outliner"):
        _add(kd, km, "maya_kit.parent", make_event("P"))
        _add(kd, km, "maya_kit.unparent", make_event("P", shift=True))
    # Ctrl+D: Maya Duplicate = in place, subtree, Maya names; IC
    # duplicate_move would name the copy pCube1.001 and start a move.
    kd.remove("Object Mode", "object.duplicate_move", type="D", ctrl=True)
    _add(kd, "Object Mode", "maya_kit.duplicate", make_event("D", ctrl=True))
    _add(kd, "Object Mode", "maya_kit.duplicate_with_transform", make_event("D", shift=True))
    _add(kd, "Object Mode", "maya_kit.duplicate_special", make_event("D", shift=True, ctrl=True))
    _add(kd, "Object Mode", "maya_kit.delete_history", make_event("D", shift=True, alt=True))


# --- 17. Ctrl+A Attribute Editor / Channel Box, Ctrl+Shift+A / Alt+D ----
#  Ctrl+a ShowAttributeEditorOrChannelBox, Ctrl+A (capital)
# SelectAll, Alt+d SelectNone. IC Object Mode Ctrl+A / Ctrl+Shift+A = select all / none.

def patch_attribute_editor(kd):
    kd.remove("Object Mode", "object.select_all", type="A", ctrl=True)
    kd.remove("Object Mode", "object.select_all", type="A", ctrl=True, shift=True)
    _add(kd, "Object Mode", "maya_kit.ae_toggle", make_event("A", ctrl=True))
    _add(kd, "Object Mode", "object.select_all", make_event("A", ctrl=True, shift=True),
         {"action": 'SELECT'})
    _add(kd, "Object Mode", "object.select_all", make_event("D", alt=True), {"action": 'DESELECT'})


# --- 18. Undo / redo, visibility, isolate, invert ------------
#  (z / Shift+Z / Ctrl+Y), :233-240 (h, Ctrl+H, Alt+H,
# Shift+H, Ctrl+Shift+H, Ctrl+Alt+H, Ctrl+1), :76 (Ctrl+Shift+I).

# Editor keymaps run before "Screen": their z = zoom/viewer border would hide the undo.
_Z_BORDERS = (("3D View", "view3d.zoom_border"), ("View2D", "view2d.zoom_border"),
              ("Image", "image.view_zoom_border"), ("Node Editor", "node.viewer_border"))

VISIBILITY_KEYS = (("H", {}, "TOGGLE"), ("H", {"ctrl": True}, "HIDE"),
                   ("H", {"alt": True}, "HIDE_UNSELECTED"), ("H", {"shift": True}, "SHOW_SELECTED"),
                   ("H", {"ctrl": True, "shift": True}, "SHOW_LAST"))


def patch_undo_visibility(kd):
    for km, idname in _Z_BORDERS:
        kd.remove(km, idname, type="Z")
    _add(kd, "Screen", "ed.undo", make_event("Z"))
    _add(kd, "Screen", "ed.redo", make_event("Z", shift=True))
    _add(kd, "Screen", "ed.redo", make_event("Y", ctrl=True))

    # Object Mode: IC Ctrl+H hide, Shift+H hide unselected, Alt+H reveal (IC Object Mode).
    kd.remove("Object Mode", "object.hide_view_set", type="H", ctrl=True)
    kd.remove("Object Mode", "object.hide_view_set", type="H", shift=True)
    kd.remove("Object Mode", "object.hide_view_clear", type="H", alt=True)
    for key, mods, action in VISIBILITY_KEYS:
        _add(kd, "Object Mode", "maya_kit.visibility", make_event(key, **mods), {"action": action})
    # Mesh components: hidden components can't be selected in Blender, so the "show"
    # keys reveal everything (and select it). IC Shift+H / Alt+H = hide unselected / reveal.
    kd.remove("Mesh", "mesh.hide", type="H", shift=True)
    kd.remove("Mesh", "mesh.reveal", type="H", alt=True)
    _add(kd, "Mesh", "mesh.hide", make_event("H", alt=True), {"unselected": True})
    for mods in ({"shift": True}, {"ctrl": True, "shift": True}, {"ctrl": True, "alt": True}):
        _add(kd, "Mesh", "mesh.reveal", make_event("H", **mods))

    # Ctrl+1 isolate select: local view without moving the camera; again = back.
    kd.remove("Mesh", "mesh.select_mode", type="ONE", ctrl=True)
    _add(kd, "3D View", "view3d.localview", make_event("ONE", ctrl=True), {"frame_selected": False},
         shadows=("Sculpt",))

    _add(kd, "Object Mode", "object.select_all", make_event("I", ctrl=True, shift=True),
         {"action": 'INVERT'})
    _add(kd, "Mesh", "mesh.select_all", make_event("I", ctrl=True, shift=True), {"action": 'INVERT'})


# --- 19. Mesh component keys -------------------------------
#  (Ctrl+Shift+A / Alt+D), :79 (Ctrl+F9-F11 convert), :82 (> <,
# Ctrl: along loop), :124-129 (D component pivot); HK:384-385 (Ctrl+E extrude, Ctrl+B bevel).

CONVERT_KEYS = (("F9", "VERT"), ("F10", "EDGE"), ("F11", "FACE"))


def patch_mesh_components(kd):
    kd.remove("Mesh", "wm.tool_set_by_id", type="D")                       # annotate tool
    _add(kd, "Mesh", "maya_kit.hold", make_event("D"), {"name": "component_pivot"})
    # Insert = the same pivot edit as a toggle (, )
    _add(kd, "Mesh", "maya_kit.pivot_toggle", make_event("INSERT"))
    kd.remove("Mesh", "mesh.select_all", type="A", ctrl=True, shift=True)   # IC: deselect
    _add(kd, "Mesh", "mesh.select_all", make_event("A", ctrl=True, shift=True), {"action": 'SELECT'})
    _add(kd, "Mesh", "maya_kit.select_none", make_event("D", alt=True))
    kd.remove("Mesh", "wm.tool_set_by_id", type="E", ctrl=True)            # extrude tool
    # Maya polyExtrudeFace: zero-length extrusion + manipulator / In-View Editor (step 65); edges and
    # vertices fall back to Blender's extrude + normal drag inside maya_kit.extrude.
    _add(kd, "Mesh", "maya_kit.extrude", make_event("E", ctrl=True))
    kd.remove("Mesh", "wm.tool_set_by_id", type="B", ctrl=True)            # bevel tool
    _add(kd, "Mesh", "maya_kit.bevel", make_event("B", ctrl=True))
    _add(kd, "Mesh", "mesh.select_more", make_event("PERIOD", shift=True, repeat=True))
    _add(kd, "Mesh", "mesh.select_less", make_event("COMMA", shift=True, repeat=True))
    _add(kd, "Mesh", "mesh.select_next_item", make_event("PERIOD", shift=True, ctrl=True, repeat=True))
    _add(kd, "Mesh", "mesh.select_prev_item", make_event("COMMA", shift=True, ctrl=True, repeat=True))
    for key, comp in CONVERT_KEYS:
        _add(kd, "Mesh", "maya_kit.convert_selection", make_event(key, ctrl=True), {"type": comp})


# --- 20. Key / frame stepping: . , Alt+. Alt+, -----------------
# Maya-361 (NextKey, PreviousKey, NextFrame, PreviousFrame) via .
# "Frames" is in nearly every editor; the 3D View / Image pies on . , go (pivot and orientation stay
# in the headers). The Outliner (show active) and Clip Editor (pivot pie) keep their own . first.

def patch_key_stepping(kd):
    kd.remove("3D View", "wm.call_menu_pie", type="PERIOD")      # pivot pie
    kd.remove("3D View", "wm.call_menu_pie", type="COMMA")       # orientation pie
    kd.remove("Image", "wm.call_menu_pie", type="PERIOD")        # UV pivot pie
    keep = ("Outliner", "Clip Editor")
    _add(kd, "Frames", "screen.keyframe_jump", make_event("PERIOD"), {"next": True}, shadows=keep)
    _add(kd, "Frames", "screen.keyframe_jump", make_event("COMMA"), {"next": False}, shadows=keep)
    _add(kd, "Frames", "screen.frame_offset", make_event("PERIOD", alt=True, repeat=True), {"delta": 1})
    _add(kd, "Frames", "screen.frame_offset", make_event("COMMA", alt=True, repeat=True), {"delta": -1})


# --- 21. Shift+drag a manipulator = Smart Duplicate ----------------
#  (PREF:371-374). The C transform gizmo runs gizmogroup.gizmo_tweak
# from these keymaps for any Shift/Ctrl (IC:3703-3721); our item goes first, duplicates the selection
# and passes the same event on, so the gizmo moves the copies. Shift held during a transform was
# Blender's precision (IC:3611-3612): Maya has none, so precision moves to Alt (delegated).

GIZMO_KEYMAPS = ("Generic Gizmo Maybe Drag", "Generic Gizmo Drag")


def patch_manip_duplicate(kd):
    for km in GIZMO_KEYMAPS:
        _add(kd, km, "maya_kit.manip_duplicate", make_event("LEFTMOUSE", "PRESS", shift=True),
             first=True)


# --- 22. Delete / Backspace on components ------------------------
# Maya deletes the selected faces / edges / vertices right away (runtime_commands.json Delete,
# DeleteEdge, DeleteVertex); IC opens the Delete menu (IC:3061-3062). Ctrl+Delete / Ctrl+Backspace
# keep IC's mesh.dissolve_mode = Maya DeletePolyElements (Maya-376).

def patch_component_delete(kd):
    for key in ("DEL", "BACK_SPACE"):
        kd.remove("Mesh", "wm.call_menu", type=key)
        _add(kd, "Mesh", "maya_kit.delete_components", make_event(key))


# --- 23. Manipulator size, smoothing level, default view, wireframe on shaded -------------------
# Maya-389 (= Shift++ -), :678-679 (PgUp/PgDn), :336 (0), :238 (Home), :738 (Alt+5)
# via ;  「계획」.

def patch_view_keys(kd):
    for ev, factor in ((make_event("EQUAL"), 1.25), (make_event("EQUAL", shift=True), 1.25),
                       (make_event("MINUS"), 0.8)):
        _add(kd, "3D View", "maya_kit.manip_size", ev, {"factor": factor})
    # Text edit mode keeps Home = line start (Font keymap runs first).
    _add(kd, "3D View", "maya_kit.view_home", make_event("HOME"), shadows=("Font",))
    _add(kd, "3D View", "wm.context_toggle", make_event("FIVE", alt=True),
         {"data_path": "space_data.overlay.show_wireframes"})
    for km in ("Object Mode", "Mesh"):
        _add(kd, km, "maya_kit.smooth_level", make_event("PAGE_UP", repeat=True), {"delta": 1})
        _add(kd, km, "maya_kit.smooth_level", make_event("PAGE_DOWN", repeat=True), {"delta": -1})
        _add(kd, km, "maya_kit.smooth_preview", make_event("ZERO"), {"level": 1})


# --- 24. MMB drag = the last picked manipulator handle ------------
#  (manipsRememberActiveHandle). A plain LMB press on the gizmo
# remembers the handle (after the drag); the tool keymaps' MMB press (IC: free transform) uses it.
# The Channel Box MMB slider (patch 14) stays in front.

MMB_TOOLS = (("3D View Tool: Move", "transform.translate", 'TRANSLATE'),
             ("3D View Tool: Rotate", "transform.rotate", 'ROTATE'),
             ("3D View Tool: Scale", "transform.resize", 'RESIZE'))


def patch_active_handle(kd):
    for km in GIZMO_KEYMAPS:
        _add(kd, km, "maya_kit.manip_press", make_event("LEFTMOUSE", "PRESS"), first=True)
    for km, idname, mode in MMB_TOOLS:
        items = kd.items(km)
        old = kd.find(km, idname, type="MIDDLEMOUSE")
        if not old:
            if not patch.STRICT:
                patch.DRIFT.append(f"{km}: no MMB {idname}")
                continue
            raise LookupError(f"{km}: no MMB {idname}")
        at = next(i for i, it in enumerate(items) if it is old[0])
        kd.remove(km, idname, type="MIDDLEMOUSE")
        item = kd.add(km, "maya_kit.manip_mmb", make_event("MIDDLEMOUSE"), {"mode": mode})
        items.remove(item)
        items.insert(at, item)      # same place: after the Channel Box slider
        ADDED.append((km, "maya_kit.manip_mmb", make_event("MIDDLEMOUSE"), {"mode": mode}, (km,)))


# --- 25. Shift+T Assign New Material -------------------------------------
# Maya via  IC binds Shift+T only in the
# Dope Sheet.

def patch_materials(kd):
    for km in ("Object Mode", "Mesh"):
        _add(kd, km, "maya_kit.assign_new_material", make_event("T", shift=True))


# --- 26. Marquee selects occluded components -----------------
# Maya selectPrefUseDepth false (). In front of every LMB drag
# box / lasso item of the select tools (and their fallbacks under Move/Rotate/Scale): sets the
# view's X-ray flag for the drag, then PASS_THROUGH to view3d.select_box / select_lasso.
SELECT_DRAG_KEYMAPS = ("3D View Tool: Select Box", "3D View Tool: Select Box (fallback)",
                       "3D View Tool: Select Lasso", "3D View Tool: Select Lasso (fallback)")


def patch_select_through(kd):
    for km in SELECT_DRAG_KEYMAPS:
        for shift, ctrl in ((False, False), (True, False), (False, True), (True, True)):
            _add(kd, km, "maya_kit.select_through",
                 make_event("LEFTMOUSE", "CLICK_DRAG", shift=shift, ctrl=ctrl), first=True,
                 shadows=(km,))   # in front of the select item on purpose (PASS_THROUGH)


# Step 49: a click under the Tool Box column's tools reaches that narrow 3D View's WINDOW region,
# where view3d.select would deselect everything (it deselects hidden object types too). The guard
# swallows the click there and passes it through everywhere else (ui/toolbox.py).
def patch_toolbox_guard(kd):
    for shift, ctrl in ((False, False), (True, False), (False, True), (True, True)):
        _add(kd, "3D View", "maya_kit.toolbox_guard", make_event("LEFTMOUSE", "CLICK", shift=shift, ctrl=ctrl),
             first=True, shadows=("3D View",))   # in front of view3d.select on purpose (PASS_THROUGH)


# Step 76: Maya selection priority () — in front of the object-mode click
# select items ("3D View" CLICK, Tweak tool PRESS); passes through outside object mode and when no IK
# handle / joint / curve is under the mouse (operators/select_priority.py).
SELECT_PRIORITY_ITEMS = (("3D View", "CLICK"), ("3D View Tool: Tweak", "PRESS"))


def patch_select_priority(kd):
    for km, value in SELECT_PRIORITY_ITEMS:
        for shift, ctrl in ((False, False), (True, False), (False, True), (True, True)):
            _add(kd, km, "maya_kit.select_priority", make_event("LEFTMOUSE", value, shift=shift, ctrl=ctrl),
                 first=True, shadows=(km,))   # in front of view3d.select on purpose (PASS_THROUGH)


# --- 27. Maya key batch -------------------------------------------
# Ctrl+Alt+LMB box zoom (interaction.md:43), Ctrl+T Universal Manipulator (HK:313), Y last non-sacred
# tool (HK:316), Ctrl+Shift+X Multi-Cut / Ctrl+Shift+Q Quad Draw (HK:319-320), F2-F6 menu sets
# (HK:322-327; IC's 3D View F2 right / F3 top / F4 camera / F5 orbit go, F1 and Ctrl+F1-F3 stay),
# Return (HK:353): IC's 3D View rename popover goes (Blender modal tools confirm with their own Return).

# Editors whose own F2-F6 keys stay (they run before Screen): Image / UV zoom ratios, File Browser rename.
MENU_SET_SHADOWS = ("Image", "File Browser")


def patch_key_batch(kd):
    # Blender 5.x IC binds Ctrl+Alt+LMB in Sculpt mode too: there the sculpt stroke wins (Maya has no such
    # mode; step 53).
    _add(kd, "3D View", "maya_kit.box_zoom", make_event("LEFTMOUSE", ctrl=True, alt=True), shadows=("Sculpt",))
    for km in ("Object Mode", "Mesh"):
        _add(kd, km, "wm.tool_set_by_id", make_event("T", ctrl=True), {"name": "builtin.transform"})
        _add(kd, km, "maya_kit.last_tool", make_event("Y"))
        _add(kd, km, "maya_kit.menu_tool", make_event("X", shift=True, ctrl=True),
             {"tool": "builtin.knife", "edit": True})
        _add(kd, km, "maya_kit.menu_tool", make_event("Q", shift=True, ctrl=True),
             {"tool": "builtin.poly_build", "edit": True})
    kd.remove("3D View", "view3d.view_axis", type="F2")
    kd.remove("3D View", "view3d.view_axis", type="F3")
    kd.remove("3D View", "view3d.view_camera", type="F4")
    kd.remove("3D View", "view3d.view_orbit", type="F5")
    kd.remove("3D View", "wm.call_panel", type="RET")
    for key, set_id in (('F2', 'modelingMenuSet'), ('F3', 'riggingMenuSet'), ('F4', 'animationMenuSet'),
                        ('F5', 'dynamicsMenuSet'), ('F6', 'renderingMenuSet')):
        _add(kd, "Screen", "maya_kit.menu_set", make_event(key), {"set": set_id},
             shadows=MENU_SET_SHADOWS)


# --- 28. Component pick-walk, Alt+Shift axis-locked navigation ------
# Arrows in edit mode walk vertices / edges / faces (HK:364-367, Maya pickWalk*.mel); IC's Up/Down
# grow/shrink go (Maya: Shift+> / <, step 18). Alt+Shift+LMB / MMB = tumble / track on one axis
# (interaction.md:46); IC's Alt+Shift+LMB click-select toggle goes (a PRESS item would hide it anyway).

AXIS_LOCK_SHADOWS = ("Weight Paint", "Paint Face Mask (Weight, Vertex, Texture)",
                     "Paint Vertex Selection (Weight, Vertex)")


def patch_component_pick_walk(kd):
    kd.remove("Mesh", "mesh.select_more", type="UP_ARROW")
    kd.remove("Mesh", "mesh.select_less", type="DOWN_ARROW")
    for key, direction in PICK_WALK_KEYS:
        _add(kd, "Mesh", "maya_kit.pick_walk_component", make_event(key, repeat=True),
             {"direction": direction})
    kd.remove("3D View", "view3d.select", type="LEFTMOUSE", value="CLICK", shift=True, alt=True)
    # Paint modes keep their own Alt+Shift+LMB select (they run before 3D View).
    _add(kd, "3D View", "maya_kit.view_axis_lock", make_event("LEFTMOUSE", shift=True, alt=True),
         {"mode": "TUMBLE"}, shadows=AXIS_LOCK_SHADOWS)
    _add(kd, "3D View", "maya_kit.view_axis_lock", make_event("MIDDLEMOUSE", shift=True, alt=True),
         {"mode": "TRACK"})


# --- 30. Joints = pose bones ---------------------------------
# Maya has no pose mode: picking a joint selects it (). Ctrl+Tab =
# pose mode toggle (Blender's default key for it; posemode_toggle returns PASS_THROUGH unless an
# armature is active, tmp/probe55, so Screen's Ctrl+Tab still gets the event); the Channel Box MMB
# slider works on joints.

def patch_pose_joints(kd):
    _add(kd, "Object Non-modal", "object.posemode_toggle", make_event("TAB", ctrl=True), shadows=("Screen",))
    _add(kd, "Pose", "maya_kit.cb_virtual_slider", make_event("MIDDLEMOUSE"))


# --- 31. Time Slider and keys ---------------------------------
#  The timeline is a Dope Sheet mode: the Maya Time Slider
# mouse (LMB time, Shift+LMB range, MMB time + notice, RMB menu) goes first in "Dopesheet" and passes
# through in the Dope Sheet. K (Time Dragger, Maya) is global ("Screen"); editor keymaps
# run first, so their plain K goes: Mesh knife tool cycle (IC:3074; Multi-Cut = Ctrl+Shift+X) and
# Dope Sheet select_column (IC:1435). "User Interface" / Outliner K only act over a button / row.
# S (Maya) = every keyable channel, not IC's LocRotScale (IC:2463, :2536).

TIME_SLIDER_SHADOWS = ("Dopesheet", "View2D", "Screen")   # Screen: the step 73 Range Slider click


def patch_time_slider(kd):
    for shift in (False, True):
        _add(kd, "Dopesheet", "maya_kit.time_scrub", make_event("LEFTMOUSE", shift=shift), {"range": shift},
             first=True, shadows=TIME_SLIDER_SHADOWS)
    _add(kd, "Dopesheet", "maya_kit.time_scrub", make_event("MIDDLEMOUSE"), {"notice": True}, first=True,
         shadows=TIME_SLIDER_SHADOWS)
    _add(kd, "Dopesheet", "maya_kit.time_slider_menu", make_event("RIGHTMOUSE"), first=True,
         shadows=TIME_SLIDER_SHADOWS)
    # Range Slider bar (step 73): a click on the empty label in the timeline header reaches the window
    # keymaps; the operator passes through anywhere but over the bar ui/range_bar.py drew.
    # Every editor keymap that uses the click runs first (intended: only unhandled clicks get here).
    for value in ("PRESS", "DOUBLE_CLICK"):
        under = tuple(n for n in kd.keymap_names() if n != "Screen" and kd.find(n, type="LEFTMOUSE", value=value))
        _add(kd, "Screen", "maya_kit.range_bar_drag", make_event("LEFTMOUSE", value=value), shadows=under)
    kd.remove("Mesh", "wm.tool_set_by_id", type="K")
    kd.remove("Dopesheet", "action.select_column", type="K")
    _add(kd, "Screen", "maya_kit.tap_hold", make_event("K"), {"binding": "time_drag"},
         shadows=("User Interface", "Outliner"))
    for km in ("Object Mode", "Pose"):
        kd.remove(km, "anim.keyframe_insert_by_name", type="S")
        _add(kd, km, "maya_kit.set_key", make_event("S"))


# --- 32. Joints: pose-mode pick-walk, P / Shift+P ----------------------
# Maya arrows walk joints like objects (pickWalk, ); IC Pose
# arrows = select_hierarchy (IC:2453-2459) and frame_offset Left/Right (frames are Alt+, / Alt+., step 20).
# Maya P parents joints keeping their place: IC Pose P = object.parent_set (IC:2434), Armature
# P / Shift+P = armature.parent_set / parent_clear menus (IC:3099-3100).

def patch_joints(kd):
    kd.remove("Pose", "pose.select_hierarchy", type="UP_ARROW")
    kd.remove("Pose", "pose.select_hierarchy", type="DOWN_ARROW")
    kd.remove("Pose", "screen.frame_offset", type="LEFT_ARROW")     # frames: Alt+, / Alt+. (step 20)
    kd.remove("Pose", "screen.frame_offset", type="RIGHT_ARROW")
    for key, direction in PICK_WALK_KEYS:
        _add(kd, "Pose", "maya_kit.pick_walk_joint", make_event(key, repeat=True), {"direction": direction})
    kd.remove("Pose", "object.parent_set", type="P")
    kd.remove("Armature", "armature.parent_set", type="P")
    kd.remove("Armature", "armature.parent_clear", type="P", shift=True)
    for km in ("Pose", "Armature"):
        _add(kd, km, "maya_kit.parent_joint", make_event("P"))
        _add(kd, km, "maya_kit.unparent_joint", make_event("P", shift=True))


# --- 33. Multi-Cut feel ------------------------------------------
# , 98-100: in Maya's Multi-Cut Ctrl+click on an edge inserts an edge loop
# there (Ctrl+MMB: in the middle) and Shift snaps the cut along the edge to the Snap Step %. Multi-Cut is Blender's
# knife: its tool keymap only has a plain LMB press (blender_default.py:7424-7433), so these don't share its event;
# each passes through when no edge is under the mouse. Inside the knife modal Shift = IGNORE_SNAP (IC:3490-3493)
# becomes midpoint snap (Snap Step 50 %, the only step the knife has); Ctrl keeps Blender's midpoint snap.
KNIFE_TOOL = "3D View Tool: Edit Mesh, Knife"


def patch_multi_cut(kd):
    _add(kd, KNIFE_TOOL, "maya_kit.multicut_loop", make_event("LEFTMOUSE", ctrl=True))
    _add(kd, KNIFE_TOOL, "maya_kit.multicut_loop", make_event("LEFTMOUSE", ctrl=True, shift=True), {"snap": True})
    _add(kd, KNIFE_TOOL, "maya_kit.multicut_loop", make_event("MIDDLEMOUSE", ctrl=True), {"center": True})
    _add(kd, KNIFE_TOOL, "maya_kit.multicut_snap", make_event("LEFTMOUSE", shift=True))
    for key in ("LEFT_SHIFT", "RIGHT_SHIFT"):
        for value, mode in (("PRESS", "SNAP_MIDPOINTS_ON"), ("RELEASE", "SNAP_MIDPOINTS_OFF")):
            old = "IGNORE_SNAP_ON" if value == "PRESS" else "IGNORE_SNAP_OFF"
            kd.remove("Knife Tool Modal Map", old, type=key, value=value, any=True)
            _add(kd, "Knife Tool Modal Map", mode, make_event(key, value, any=True))


# --- 34. UV workflow -------------------------------------------
# -2; Maya UV Editor keys Maya-522 (
# polyTexturePlacementPanel rows), F12 / Alt+F12 Maya-258. IC's UV Editor: Shift+X = snap pie (IC:613),
# Ctrl+L = select_linked (IC:599), RMB = context menu (IC:614); Maya has no shell-select key there.
UV_KM = "UV Editor"


def patch_uv(kd):
    kd.remove(UV_KM, "wm.call_menu", type="RIGHTMOUSE")
    for trigger, mods in (("RMB", {}), ("SHIFT_RMB", {"shift": True})):
        _add(kd, UV_KM, "maya_kit.marking_menu", make_event("RIGHTMOUSE", **mods), {"trigger": trigger})
    kd.remove(UV_KM, "wm.call_menu_pie", type="X", shift=True)
    kd.remove(UV_KM, "uv.select_linked", type="L", ctrl=True)
    _add(kd, UV_KM, "maya_kit.uv_cut", make_event("X", shift=True))
    _add(kd, UV_KM, "maya_kit.uv_sew", make_event("S", shift=True))
    _add(kd, UV_KM, "maya_kit.uv_unfold", make_event("U", ctrl=True))
    _add(kd, UV_KM, "maya_kit.uv_layout", make_event("L", ctrl=True))
    for km in ("Object Mode", "Mesh"):
        _add(kd, km, "maya_kit.uv_component", make_event("F12"), {"mode": 'UV'})
        _add(kd, km, "maya_kit.uv_component", make_event("F12", alt=True), {"mode": 'SHELL'})


# --- 36. Scene files --------------------------------------------------
# HK:73-78 (Ctrl+O / Ctrl+S / Ctrl+Shift+S / Ctrl+Alt+S / Ctrl+R). IC binds the first four in "Window"
# (IC:194-199): replaced in place by the kit's (file dialogs start in the project's scenes folder; Ctrl+Alt+S =
# Maya's Increment and Save rule shot_v001 -> shot_v001.0001, not Blender's shot_v002). Ctrl+R = Create Reference;
# editor keymaps that bind Ctrl+R themselves keep it there (they run first).

SCENE_KEYS = (
    ("wm.open_mainfile", "maya_kit.open_scene", {"ctrl": True}, "O"),
    ("wm.save_mainfile", "maya_kit.save_scene", {"ctrl": True}, "S"),
    ("wm.save_as_mainfile", "maya_kit.save_scene_as", {"ctrl": True, "shift": True}, "S"),
    ("wm.save_mainfile", "maya_kit.increment_save", {"ctrl": True, "alt": True}, "S"),
)


def patch_scene_files(kd):
    for ic, kit, mods, key in SCENE_KEYS:
        kd.remove("Window", ic, type=key, **mods)
        _add(kd, "Window", kit, make_event(key, **mods))
    # Ctrl+R stays refresh / reload where an editor binds it (they run before Window items).
    _add(kd, "Window", "maya_kit.create_reference", make_event("R", ctrl=True),
         shadows=("Image Generic", "File Browser", "File Browser Main", "Sequencer"))


# --- 37. Graph Editor keys, Shift+S tangent marking menu ----------------
# HK:146 (Graph Editor G = FramePlaybackRange), HK:151 (D = TangentAuto), HK:418 (Shift+S hold =
# KeyframeTangentMarkingMenu). G / D go in "Graph Editor" (it runs before Screen's G = repeat_last);
# Shift+S replaces IC's keyframe_insert menu in Object Mode / Pose (IC:2462, 2535) and is added to the Graph Editor
# and Dope Sheet. Mesh / UV Shift+S (UV Sew, step 66) stay.

def patch_graph_keys(kd):
    _add(kd, "Graph Editor", "anim.scene_range_frame", make_event("G"), shadows=("Screen",))   # over repeat_last
    _add(kd, "Graph Editor", "maya_kit.set_tangent", make_event("D"), {"kind": "AUTO"})
    for km in ("Object Mode", "Pose"):
        kd.remove(km, "anim.keyframe_insert", type="S", shift=True)
    for km in ("Object Mode", "Pose", "Graph Editor", "Dopesheet"):
        _add(kd, km, "maya_kit.tap_hold", make_event("S", shift=True), {"binding": "key_tangent"})


# --- 38. Key batch 2 ------------------------------------------------------------
# Graph Editor 1/2/3 (HK:148-150), Shift+Q / Alt+Q select tool marking menus (HK:286-287), Ctrl+Alt+Left/Right
# Spin Edge (HK:378-379), Shift+G repeat at the mouse (HK:363), Ctrl+Shift+C camera from view (HK:60).
# IC has none of these events in these keymaps; same-event IC items elsewhere stay (editor keymaps run first):
# Shift+Q in Grease Pencil modes, Shift+G select similar / grouped in Armature, Metaball, Grease Pencil.
SELECT_MM_KEYMAPS = ("Object Mode", "Mesh")
REPEAT_SHADOWS = ("Armature", "Metaball", "Grease Pencil Selection")
SELECT_MM_KEYS = (({"shift": True}, "select_component"), ({"alt": True}, "select_polygon"))   # marking.SELECT_BINDINGS
GRAPH_VIEW_KEYS = (("ONE", "ABSOLUTE"), ("TWO", "STACKED"), ("THREE", "NORMALIZED"))


def patch_key_batch_2(kd):
    for key, mode in GRAPH_VIEW_KEYS:
        _add(kd, "Graph Editor", "maya_kit.graph_view_mode", make_event(key), {"mode": mode})
    for km in SELECT_MM_KEYMAPS:
        for mods, binding in SELECT_MM_KEYS:
            _add(kd, km, "maya_kit.tap_hold", make_event("Q", **mods), {"binding": binding})
    _add(kd, "Mesh", "mesh.edge_rotate", make_event("LEFT_ARROW", ctrl=True, alt=True), {"use_ccw": True})
    _add(kd, "Mesh", "mesh.edge_rotate", make_event("RIGHT_ARROW", ctrl=True, alt=True), {"use_ccw": False})
    _add(kd, "3D View", "maya_kit.repeat_at_mouse", make_event("G", shift=True), shadows=REPEAT_SHADOWS)
    _add(kd, "Object Mode", "maya_kit.camera_from_view", make_event("C", shift=True, ctrl=True))


# --- 38. Outliner MMB drag ------------------------------------------
# Maya parents / reorders / unparents with an MMB drag in the Outliner (); Blender's Outliner has
# no MMB item (IC "Outliner"), only View2D's MMB scroller_activate (IC:323), which passes through off the scroll
# bars and runs first. Alt+MMB pans (IC View2D, = Maya). "View2D Buttons List" (MMB pan) belongs to button-list
# regions (header / sidebar), not the Outliner tree. LMB drag stays Blender's (operators/outliner_drag.py redoes its
# drop the Maya way).

def patch_outliner_drag(kd):
    _add(kd, "Outliner", "maya_kit.outliner_drag", make_event("MIDDLEMOUSE"), shadows=("View2D", "View2D Buttons List"))


# --- 39. Insert / nudge / select keys ------------------------------------
# Maya global keys (Maya-357, 729-732, 739-740). "Screen" so they work over the 3D View, Graph Editor,
# Dope Sheet and Time Slider; the operators read the editor under the mouse. Editor / mode keymaps with the same
# event run first and keep it (Weight Paint / Grease Pencil / Mask Alt+I, Animation Channels Ctrl+Shift+W, Text
# Ctrl+Shift+E, the UI colour-ramp eyedropper Alt+I).
INSERT_KEY_KEYS = (("I", {"alt": True}, {"channels": "ALL"}),
                   ("W", {"ctrl": True, "shift": True}, {"channels": "TRANSLATE"}),
                   ("E", {"ctrl": True, "shift": True}, {"channels": "ROTATE"}),
                   ("R", {"ctrl": True, "shift": True}, {"channels": "SCALE"}))
KEY_STEP_SHADOWS = ("User Interface", "Mask Editing", "Weight Paint", "Grease Pencil Paint Mode",
                    "Grease Pencil Edit Mode", "Grease Pencil Sculpt Mode", "Grease Pencil Weight Paint",
                    "Grease Pencil Vertex Paint", "Animation Channels", "Text")


def patch_key_insert(kd):
    for key, mods, props in INSERT_KEY_KEYS:
        _add(kd, "Screen", "maya_kit.insert_key", make_event(key, **mods), props, shadows=KEY_STEP_SHADOWS)
    for key, delta in (("NINE", -1), ("ZERO", 1)):
        _add(kd, "Screen", "maya_kit.nudge_keys", make_event(key, shift=True, repeat=True), {"delta": delta},
             shadows=KEY_STEP_SHADOWS)
    for key, direction in (("COMMA", "PREVIOUS"), ("PERIOD", "NEXT")):
        _add(kd, "Screen", "maya_kit.select_key", make_event(key, ctrl=True, alt=True), {"direction": direction},
             shadows=KEY_STEP_SHADOWS)


# --- 40. Time Slider range drag ---------------------------------------------
# A press on the highlighted range moves / scales its keys; anywhere else it passes through to time_scrub (step 56),
# so it goes in front of it (added after patch_time_slider: ``first`` puts the latest item first).
# The MayaKit Time Slider row (29 px at 1.25) is all Blender's scrub strip, whose "Time Scrub" keymap (LMB =
# anim.change_frame, blender_default.py:1171-1183) runs before "Dopesheet"; IC has no "Time Scrub", so Blender used
# its default one (checked with --debug-handlers). The Maya keyconfig gets its own: change_frame kept, the range
# drag and step 56's time_scrub (a click drops the range) in front; both pass through outside the Time Slider.
TIME_SCRUB_KM = ("Time Scrub", {"space_type": 'EMPTY', "region_type": 'WINDOW'})


def patch_time_range(kd):
    _add(kd, "Dopesheet", "maya_kit.time_range_drag", make_event("LEFTMOUSE"), first=True, shadows=TIME_SLIDER_SHADOWS)
    kd.ensure(*TIME_SCRUB_KM, [("anim.change_frame", make_event("LEFTMOUSE"), None)])
    shadows = (*TIME_SLIDER_SHADOWS, "Time Scrub")
    _add(kd, "Time Scrub", "maya_kit.time_scrub", make_event("LEFTMOUSE"), first=True, shadows=shadows)
    _add(kd, "Time Scrub", "maya_kit.time_range_drag", make_event("LEFTMOUSE"), first=True, shadows=shadows)


# --- 41. Manipulator Ctrl+LMB axis = plane, Shift+MMB = closest axis ----------
# Ctrl+LMB sits first in the gizmo keymaps (only over a highlighted gizmo; passes through off the kit manipulator's
# axis / Move centre handles). Shift+MMB goes in the Move / Scale tool keymaps (3D View has no Shift+MMB item; IC
# pans with Alt+MMB): a short modal reads the first movement, picks the axis and starts the transform (a CLICK_DRAG
# item never got the simulated MMB drag, ).

def patch_manip_ctrl(kd):
    for km in GIZMO_KEYMAPS:
        _add(kd, km, "maya_kit.manip_ctrl", make_event("LEFTMOUSE", "PRESS", ctrl=True), first=True)
    for km, _idname, mode in MMB_TOOLS:
        if mode == 'ROTATE':
            continue
        _add(kd, km, "maya_kit.manip_mmb_auto", make_event("MIDDLEMOUSE", "PRESS", shift=True), {"mode": mode},
             shadows=(km,))


PATCHES = (patch_selection, patch_display, patch_group, patch_space,
           patch_hold_snap, patch_soft_select, patch_tap_hold_and_pivot, patch_pick_walk,
           patch_camera, patch_view_history, patch_space_tap, patch_smooth_preview,
           patch_component_keys, patch_cb_slider, patch_marking_menus, patch_concepts,
           patch_attribute_editor, patch_undo_visibility,
           patch_mesh_components, patch_key_stepping, patch_manip_duplicate,
           patch_component_delete, patch_view_keys, patch_active_handle, patch_materials,
           patch_select_through, patch_key_batch, patch_component_pick_walk,
           patch_toolbox_guard, patch_select_priority, patch_pose_joints, patch_time_slider, patch_joints, patch_multi_cut, patch_uv,
           patch_scene_files, patch_graph_keys, patch_key_batch_2, patch_outliner_drag,
           patch_key_insert, patch_time_range, patch_manip_ctrl)


def apply(data):
    """Apply all patches to IC data in place and return it."""
    ADDED.clear()
    kd = KeyconfigData(data)
    for patch in PATCHES:
        patch(kd)
    return data
