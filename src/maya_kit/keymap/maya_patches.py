# SPDX-License-Identifier: GPL-3.0-or-later
"""Patches that turn Industry Compatible data into the "Maya" keyconfig.

``IC:<line>`` = ``$S\\presets\\keyconfig\\keymap_data\\industry_compatible_data.py``.
Plan and rationale: docs/steps/step_2.md (1-4), docs/steps/step_3.md (5-8),
docs/steps/step_4.md (9-13), docs/steps/step_10.md (16), docs/steps/step_11.md (17),
docs/steps/step_16.md (18), docs/steps/step_18.md (19), docs/steps/step_20.md (20),
docs/steps/step_22.md (21), docs/steps/step_24.md (22), docs/steps/step_27.md (23), docs/steps/step_28.md (24).

``ADDED`` lists every binding this module adds; tests use it for the
shadowing check and docs/keymap_mapping.md is cross-checked against it.
"""

from .patch import KeyconfigData, make_event

# (km_name, idname, event, props, shadows) for every binding added below.
# ``shadows``: keymaps allowed to bind the same event in the same editor
# (intentional: e.g. paint modes keep their own X/B).
ADDED = []


# Operators that return PASS_THROUGH when they don't apply, so they may sit in
# front of another item with the same event in the same keymap.
PASS_THROUGH_FIRST = ("maya_kit.cb_virtual_slider", "maya_kit.manip_duplicate", "maya_kit.manip_press")


def _add(kd, km_name, idname, event, props=None, shadows=(), first=False):
    kd.add(km_name, idname, event, props, first=first)
    ADDED.append((km_name, idname, event, dict(props or {}), tuple(shadows)))


# --- 1. Selection modifiers ----------------------------------------------
# Maya: Shift = toggle, Ctrl = deselect, Ctrl+Shift = add, for click and
# marquee (research/maya/interaction.md:68-70). Order of variants:
# (shift, ctrl) = none, Shift, Ctrl, Ctrl+Shift.

def _click(plain, toggle, deselect, add):
    return [((False, False), plain), ((True, False), toggle),
            ((False, True), deselect), ((True, True), add)]


# Operators with a real ``deselect`` option (research/blender/operators.json).
_CLICK_EXACT = _click({"deselect_all": True}, {"toggle": True},
                      {"deselect": True}, {"extend": True})

# outliner.item_activate / graph.clickselect have no ``deselect`` option, so
# Ctrl and Ctrl+Shift fall back to toggle (workaround, docs/steps/step_2.md).
_OUTLINER_CLICK = _click({"extend": False, "deselect_all": True},
                         {"extend": True, "deselect_all": True},
                         {"extend": True, "deselect_all": True},
                         {"extend": True, "deselect_all": True})
_GRAPH_CLICK = _click({"extend": False, "deselect_all": True},
                      {"extend": True}, {"extend": True}, {"extend": True})

_BOX = _click({"mode": "SET"}, {"mode": "XOR"}, {"mode": "SUB"}, {"mode": "ADD"})
# uv/outliner/graph select_box only have SET/ADD/SUB (no XOR): Shift adds
# instead of toggling (workaround, docs/steps/step_2.md).
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
# (research/maya/interaction.md:174-177; hotkeys_default.json "4".."7").

DISPLAY_KEYS = (("FOUR", "WIREFRAME"), ("FIVE", "SHADED"),
                ("SIX", "TEXTURED"), ("SEVEN", "LIGHTS"))


def patch_display(kd):
    # IC:3458-3459 "Object Non-modal": 4 = object mode, 5 = mode pie.
    kd.remove("Object Non-modal", "object.mode_set", type="FOUR")
    kd.remove("Object Non-modal", "wm.call_menu_pie", type="FIVE")
    for key, mode in DISPLAY_KEYS:
        _add(kd, "3D View", "maya_kit.display_mode", make_event(key), {"mode": mode})
    # Losing 4 = object mode leaves no quick way out of edit mode; Maya's F8
    # toggles object <-> last component mode (research/maya/interaction.md:73).
    _add(kd, "Object Non-modal", "object.editmode_toggle", make_event("F8"))


# --- 3. Ctrl+G group --------------------------------------------------------
# Maya Ctrl+G = group under common parent, pivot at origin
# (research/maya/concepts.md:89-91). IC Ctrl+G = move to collection (IC:2547).

def patch_group(kd):
    for km in ("Object Mode", "Outliner"):
        kd.remove(km, "object.move_to_collection", type="G", ctrl=True)
        _add(kd, km, "maya_kit.group", make_event("G", ctrl=True))


# --- 4. Space reserved for the hotbox ---------------------------------------
# Maya Space = hotbox (research/maya/hotkeys_default.json "Space" ShowHotbox),
# implemented in step 10; until then Space does nothing in other editors.
# Playback moves to Maya's Alt+V (PlaybackToggle) and Alt+Shift+V (GoToMinFrame).

def patch_space(kd):
    kd.remove("Frames", "screen.animation_play", type="SPACE")  # IC:2258
    _add(kd, "Frames", "screen.animation_play", make_event("V", alt=True))
    _add(kd, "Frames", "screen.frame_jump", make_event("V", alt=True, shift=True), {"end": False})


# --- 5. Hold keys: X/C/V/J snapping ------------------------------------------
# Maya: snapping only while the key is held, Shift variants identical
# (research/maya/interaction.md:141-143; hotkeys_default.json x/X, c/C, v/V, j).
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
# research/maya/interaction.md:155-156.

def patch_soft_select(kd):
    for km in ("Object Mode", "Mesh", "Curve", "Curves", "Metaball", "Lattice", "Particle"):
        kd.remove(km, "wm.context_toggle", type="B")                     # IC:2517, IC:3066
    _add(kd, "3D View", "maya_kit.tap_hold", make_event("B"), {"binding": "soft_select"},
         shadows=_PAINT_MODES)


# --- 7. A tap / hold, D hold pivot, Insert pivot toggle ---------------------
# A: research/maya/interaction.md:27 (tap = FrameAll, hold = marking menu).
# D / Insert: interaction.md:124-125 (pivot edit while held / toggle).

def patch_tap_hold_and_pivot(kd):
    kd.remove("3D View", "view3d.view_all", type="A")
    _add(kd, "3D View", "maya_kit.tap_hold", make_event("A"), {"binding": "select_all"},
         shadows=("Sculpt",))
    kd.remove("Object Mode", "wm.tool_set_by_id", type="D")              # IC:121 annotate
    _add(kd, "Object Mode", "maya_kit.hold", make_event("D"), {"name": "pivot"})
    _add(kd, "Object Mode", "maya_kit.pivot_toggle", make_event("INSERT"))


# --- 8. Arrow-key pick-walk (object mode) -----------------------------------
# research/maya/interaction.md:76 (HK:364-369). IC puts Left/Right frame
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
# research/maya/interaction.md:40 (Alt+LMB tumble), :192-195 (Shift+F / Shift+A).

def patch_camera(kd):
    kd.remove("3D View", "view3d.rotate", type="LEFTMOUSE", alt=True)       # IC:674
    _add(kd, "3D View", "maya_kit.tumble", make_event("LEFTMOUSE", alt=True))
    kd.remove("3D View", "view3d.view_center_pick", type="F", shift=True)
    _add(kd, "3D View", "maya_kit.frame_all_views", make_event("F", shift=True), {"selected": True})
    # Step 17: Maya fit (factor 0.95, sidebar excluded) for F and Ctrl+Shift+F (with children);
    # A tap goes through taphold.SelectAllBinding (research/maya/interaction.md:191-196).
    kd.remove("3D View", "view3d.view_selected", type="F")                  # IC:681
    _add(kd, "3D View", "maya_kit.frame", make_event("F"), {"selected": True})
    _add(kd, "3D View", "maya_kit.frame_all_views", make_event("F", shift=True, ctrl=True),
         {"selected": True, "children": True})
    kd.remove("3D View", "view3d.view_all", type="A", shift=True)
    _add(kd, "3D View", "maya_kit.frame_all_views", make_event("A", shift=True), {"selected": False},
         shadows=("Sculpt",))


# --- 10. View-change undo: [ ] and Alt+Z / Alt+Y ----------------------------
# research/maya/interaction.md:48 (HK:234-237). IC [ ] = select_hierarchy
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
# research/maya/interaction.md:248-249. Space hold = hotbox (step 10).

# Space = hotbox (step 9; tap = pane toggle, HotboxMenus.mel:244). Also in the editors
# the hotbox South zone switches a pane to, so the hotbox can switch it back; Space is
# free there since patch_space (IC used it only in "Frames"). Not in text editors.
HOTBOX_KEYMAPS = ("3D View", "Outliner", "Graph Editor", "Dopesheet", "Node Editor", "Image")


def patch_space_tap(kd):
    for km in HOTBOX_KEYMAPS:
        _add(kd, km, "maya_kit.hotbox", make_event("SPACE"))
    _add(kd, "Screen", "screen.screen_full_area", make_event("SPACE", ctrl=True),
         {"use_hide_panels": True})


# --- 12. 1/2/3 smooth mesh preview -------------------------------------------
# research/maya/interaction.md:166-172. IC 1/2/3 = component modes
# (IC:2558-2563 Object Mode, IC:164-177 Mesh), now on F9-F11.

SMOOTH_KEYS = (("ONE", 1), ("TWO", 2), ("THREE", 3))


def patch_smooth_preview(kd):
    for key, level in SMOOTH_KEYS:
        kd.remove("Object Mode", "object.mode_set_with_submode", type=key)
        kd.remove("Mesh", "mesh.select_mode", type=key)
        for km in ("Object Mode", "Mesh"):
            _add(kd, km, "maya_kit.smooth_preview", make_event(key), {"level": level})


# --- 13. F7/F9/F10/F11 component modes ---------------------------------------
# research/maya/interaction.md:73-74. F8 = editmode_toggle (patch 2).

COMPONENT_KEYS = (("F9", "VERT"), ("F10", "EDGE"), ("F11", "FACE"), ("F7", "MULTI"))


def patch_component_keys(kd):
    for key, comp in COMPONENT_KEYS:
        _add(kd, "Object Non-modal", "maya_kit.component_mode", make_event(key), {"type": comp})


# --- 14. Channel Box MMB virtual slider ---------------------------------------
# research/maya/channel_box.md:73-78. Tool keymaps run before "3D View" and IC
# gives Move/Rotate/Scale/Transform an MMB drag (IC:3823-3858), so the slider
# goes first in those; it passes through when no channel is selected.

SLIDER_TOOL_KEYMAPS = ("3D View Tool: Move", "3D View Tool: Rotate", "3D View Tool: Scale",
                       "3D View Tool: Transform")


def patch_cb_slider(kd):
    for km in SLIDER_TOOL_KEYMAPS:
        _add(kd, km, "maya_kit.cb_virtual_slider", make_event("MIDDLEMOUSE"), first=True,
             shadows=(km,))
    _add(kd, "Object Mode", "maya_kit.cb_virtual_slider", make_event("MIDDLEMOUSE"))


# --- 15. Marking menus (pies) and Q/W/E/R hold + LMB (docs/steps/step_8.md 「계획」 2-4) ----
# research/maya/hotkeys_and_menus.md §5.1 (:227-243). IC's RMB context menus in these
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


# --- 16. Scene concepts: P / Shift+P, Shift+D, Ctrl+Shift+D, Alt+Shift+D (docs/steps/step_10.md) ----
# research/maya/hotkeys_default.json: p Parent, P Unparent, D DuplicateWithTransform,
# Ctrl+D (capital) DuplicateSpecial, Alt+D (capital) DeleteHistory (concepts.md:68, :98).
# IC Object Mode P / Shift+P = object.parent_set / parent_clear.

def patch_concepts(kd):
    kd.remove("Object Mode", "object.parent_set", type="P")
    kd.remove("Object Mode", "object.parent_clear", type="P", shift=True)
    for km in ("Object Mode", "Outliner"):
        _add(kd, km, "maya_kit.parent", make_event("P"))
        _add(kd, km, "maya_kit.unparent", make_event("P", shift=True))
    # Ctrl+D: Maya Duplicate = in place, subtree, Maya names (docs/steps/step_19.md); IC
    # duplicate_move would name the copy pCube1.001 and start a move.
    kd.remove("Object Mode", "object.duplicate_move", type="D", ctrl=True)
    _add(kd, "Object Mode", "maya_kit.duplicate", make_event("D", ctrl=True))
    _add(kd, "Object Mode", "maya_kit.duplicate_with_transform", make_event("D", shift=True))
    _add(kd, "Object Mode", "maya_kit.duplicate_special", make_event("D", shift=True, ctrl=True))
    _add(kd, "Object Mode", "maya_kit.delete_history", make_event("D", shift=True, alt=True))


# --- 17. Ctrl+A Attribute Editor / Channel Box, Ctrl+Shift+A / Alt+D (docs/steps/step_11.md) ----
# research/maya/hotkeys_default.json: Ctrl+a ShowAttributeEditorOrChannelBox, Ctrl+A (capital)
# SelectAll, Alt+d SelectNone. IC Object Mode Ctrl+A / Ctrl+Shift+A = select all / none.

def patch_attribute_editor(kd):
    kd.remove("Object Mode", "object.select_all", type="A", ctrl=True)
    kd.remove("Object Mode", "object.select_all", type="A", ctrl=True, shift=True)
    _add(kd, "Object Mode", "maya_kit.ae_toggle", make_event("A", ctrl=True))
    _add(kd, "Object Mode", "object.select_all", make_event("A", ctrl=True, shift=True),
         {"action": 'SELECT'})
    _add(kd, "Object Mode", "object.select_all", make_event("D", alt=True), {"action": 'DESELECT'})


# --- 18. Undo / redo, visibility, isolate, invert (docs/steps/step_16.md 「계획」) ------------
# research/maya/interaction.md:220-221 (z / Shift+Z / Ctrl+Y), :233-240 (h, Ctrl+H, Alt+H,
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


# --- 19. Mesh component keys (docs/steps/step_18.md 「계획」) -------------------------------
# research/maya/interaction.md:75 (Ctrl+Shift+A / Alt+D), :79 (Ctrl+F9-F11 convert), :82 (> <,
# Ctrl: along loop), :124-129 (D component pivot); HK:384-385 (Ctrl+E extrude, Ctrl+B bevel).

CONVERT_KEYS = (("F9", "VERT"), ("F10", "EDGE"), ("F11", "FACE"))


def patch_mesh_components(kd):
    kd.remove("Mesh", "wm.tool_set_by_id", type="D")                       # annotate tool
    _add(kd, "Mesh", "maya_kit.hold", make_event("D"), {"name": "component_pivot"})
    kd.remove("Mesh", "mesh.select_all", type="A", ctrl=True, shift=True)   # IC: deselect
    _add(kd, "Mesh", "mesh.select_all", make_event("A", ctrl=True, shift=True), {"action": 'SELECT'})
    _add(kd, "Mesh", "maya_kit.select_none", make_event("D", alt=True))
    kd.remove("Mesh", "wm.tool_set_by_id", type="E", ctrl=True)            # extrude tool
    _add(kd, "Mesh", "view3d.edit_mesh_extrude_move_normal", make_event("E", ctrl=True))
    kd.remove("Mesh", "wm.tool_set_by_id", type="B", ctrl=True)            # bevel tool
    _add(kd, "Mesh", "maya_kit.bevel", make_event("B", ctrl=True))
    _add(kd, "Mesh", "mesh.select_more", make_event("PERIOD", shift=True, repeat=True))
    _add(kd, "Mesh", "mesh.select_less", make_event("COMMA", shift=True, repeat=True))
    _add(kd, "Mesh", "mesh.select_next_item", make_event("PERIOD", shift=True, ctrl=True, repeat=True))
    _add(kd, "Mesh", "mesh.select_prev_item", make_event("COMMA", shift=True, ctrl=True, repeat=True))
    for key, comp in CONVERT_KEYS:
        _add(kd, "Mesh", "maya_kit.convert_selection", make_event(key, ctrl=True), {"type": comp})


# --- 20. Key / frame stepping: . , Alt+. Alt+, (docs/steps/step_20.md 「계획」 1) -----------------
# hotkeySetup.mel:358-361 (NextKey, PreviousKey, NextFrame, PreviousFrame) via docs/keymap_mapping.md.
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


# --- 21. Shift+drag a manipulator = Smart Duplicate (docs/steps/step_22.md 「계획」) ----------------
# research/maya/interaction.md:107 (PREF:371-374). The C transform gizmo runs gizmogroup.gizmo_tweak
# from these keymaps for any Shift/Ctrl (IC:3703-3721); our item goes first, duplicates the selection
# and passes the same event on, so the gizmo moves the copies. Shift held during a transform was
# Blender's precision (IC:3611-3612): Maya has none, so precision moves to Alt (delegated).

GIZMO_KEYMAPS = ("Generic Gizmo Maybe Drag", "Generic Gizmo Drag")


def patch_manip_duplicate(kd):
    for km in GIZMO_KEYMAPS:
        _add(kd, km, "maya_kit.manip_duplicate", make_event("LEFTMOUSE", "PRESS", shift=True),
             first=True)


# --- 22. Delete / Backspace on components (docs/steps/step_24.md 「계획」) ------------------------
# Maya deletes the selected faces / edges / vertices right away (runtime_commands.json Delete,
# DeleteEdge, DeleteVertex); IC opens the Delete menu (IC:3061-3062). Ctrl+Delete / Ctrl+Backspace
# keep IC's mesh.dissolve_mode = Maya DeletePolyElements (hotkeySetup.mel:375-376).

def patch_component_delete(kd):
    for key in ("DEL", "BACK_SPACE"):
        kd.remove("Mesh", "wm.call_menu", type=key)
        _add(kd, "Mesh", "maya_kit.delete_components", make_event(key))


# --- 23. Manipulator size, smoothing level, default view, wireframe on shaded -------------------
# hotkeySetup.mel:387-389 (= Shift++ -), :678-679 (PgUp/PgDn), :336 (0), :238 (Home), :738 (Alt+5)
# via docs/keymap_mapping.md; docs/steps/step_27.md 「계획」.

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


# --- 24. MMB drag = the last picked manipulator handle (docs/steps/step_28.md 「계획」) ------------
# research/maya/interaction.md:103 (manipsRememberActiveHandle). A plain LMB press on the gizmo
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
            raise LookupError(f"{km}: no MMB {idname}")
        at = next(i for i, it in enumerate(items) if it is old[0])
        kd.remove(km, idname, type="MIDDLEMOUSE")
        item = kd.add(km, "maya_kit.manip_mmb", make_event("MIDDLEMOUSE"), {"mode": mode})
        items.remove(item)
        items.insert(at, item)      # same place: after the Channel Box slider
        ADDED.append((km, "maya_kit.manip_mmb", make_event("MIDDLEMOUSE"), {"mode": mode}, (km,)))


# --- 25. Shift+T Assign New Material (docs/steps/step_29.md) -------------------------------------
# hotkeySetup.mel:705 via research/maya/hotkeys_and_menus.md:135. IC binds Shift+T only in the
# Dope Sheet.

def patch_materials(kd):
    for km in ("Object Mode", "Mesh"):
        _add(kd, km, "maya_kit.assign_new_material", make_event("T", shift=True))


PATCHES = (patch_selection, patch_display, patch_group, patch_space,
           patch_hold_snap, patch_soft_select, patch_tap_hold_and_pivot, patch_pick_walk,
           patch_camera, patch_view_history, patch_space_tap, patch_smooth_preview,
           patch_component_keys, patch_cb_slider, patch_marking_menus, patch_concepts,
           patch_attribute_editor, patch_undo_visibility,
           patch_mesh_components, patch_key_stepping, patch_manip_duplicate,
           patch_component_delete, patch_view_keys, patch_active_handle, patch_materials)


def apply(data):
    """Apply all patches to IC data in place and return it."""
    ADDED.clear()
    kd = KeyconfigData(data)
    for patch in PATCHES:
        patch(kd)
    return data
