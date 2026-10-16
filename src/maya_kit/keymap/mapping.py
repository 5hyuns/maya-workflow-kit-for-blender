# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya runTimeCommand -> Blender handling, for docs/keymap_mapping.md.

Pure Python. Used by tools/gen_keymap_mapping.py (writes the doc) and by
tests/test_keymap_maya.py (checks every IC/KIT row is really bound).

Maya side: research/maya/hotkeys_default.json (keys, contexts and
runTimeCommand names only; no MEL is copied, docs/user_decisions.md #6).

Status:
  IC    Industry Compatible already does the Maya thing; kept.
  KIT   Bound by this kit's "Maya" keyconfig.
  STEP  Planned in docs/PLAN.md step ``step``.
  NO    Not applicable / not possible in Blender (see ``note``).
Rows without an entry are "unreviewed".

For IC/KIT rows ``check = (keymap, idname, {prop: value})`` is verified
against the generated keyconfig using the Maya key converted by
``maya_event``.
"""

# Maya key -> (Blender event type, shift implied by the character).
_SYMBOLS = {
    " ": ("SPACE", False), "Space": ("SPACE", False),
    "!": ("ONE", True), "@": ("TWO", True), "#": ("THREE", True), "%": ("FIVE", True),
    "(": ("NINE", True), ")": ("ZERO", True),
    "+": ("EQUAL", True), "=": ("EQUAL", False), "-": ("MINUS", False),
    ",": ("COMMA", False), "<": ("COMMA", True), ".": ("PERIOD", False), ">": ("PERIOD", True),
    "/": ("SLASH", False), "?": ("SLASH", True),
    ";": ("SEMI_COLON", False), ":": ("SEMI_COLON", True),
    "'": ("QUOTE", False), '"': ("QUOTE", True),
    "[": ("LEFT_BRACKET", False), "{": ("LEFT_BRACKET", True),
    "]": ("RIGHT_BRACKET", False), "}": ("RIGHT_BRACKET", True),
    "\\": ("BACK_SLASH", False), "|": ("BACK_SLASH", True),
    "`": ("ACCENT_GRAVE", False), "~": ("ACCENT_GRAVE", True),
    "Up": ("UP_ARROW", False), "Down": ("DOWN_ARROW", False),
    "Left": ("LEFT_ARROW", False), "Right": ("RIGHT_ARROW", False),
    "Page_Up": ("PAGE_UP", False), "Page_Down": ("PAGE_DOWN", False),
    "Home": ("HOME", False), "Insert": ("INSERT", False), "Return": ("RET", False),
    "Esc": ("ESC", False), "Backspace": ("BACK_SPACE", False), "Delete": ("DEL", False),
}
_DIGITS = ("ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE")


def maya_event(hotkey):
    """Blender event dict for a hotkeys_default.json entry (PRESS)."""
    key, mods = hotkey["key"], hotkey["modifiers"]
    shift = "sht" in mods
    if len(key) == 1 and key.isalpha():
        etype, shift = key.upper(), shift or key.isupper()
    elif len(key) == 1 and key.isdigit():
        etype = _DIGITS[int(key)]
    elif key in _SYMBOLS:
        etype, implied = _SYMBOLS[key]
        shift = shift or implied
    elif key.startswith("F") and key[1:].isdigit():
        etype = key
    else:
        raise KeyError(f"unknown Maya key {key!r}")
    ev = {"type": etype, "value": "PRESS"}
    if shift:
        ev["shift"] = True
    if "ctl" in mods:
        ev["ctrl"] = True
    if "alt" in mods:
        ev["alt"] = True
    if "cmd" in mods:
        ev["oskey"] = True
    return ev


def _e(status, check=None, step=None, note=""):
    return {"status": status, "check": check, "step": step, "note": note}


V3D, OBJ, OBJ_NM = "3D View", "Object Mode", "Object Non-modal"

# Keyed by runTimeCommand (global context unless the key says otherwise).
ENTRIES = {
    # --- KIT: step 2 ---
    "Group": _e("KIT", (OBJ, "maya_kit.group", {}), note="Empty 그룹, 피벗 원점, group1 명명 (Outliner 도)"),
    "DisplayWireframe": _e("KIT", (V3D, "maya_kit.display_mode", {"mode": "WIREFRAME"})),
    "DisplayShaded": _e("KIT", (V3D, "maya_kit.display_mode", {"mode": "SHADED"})),
    "DisplayShadedAndTextured": _e("KIT", (V3D, "maya_kit.display_mode", {"mode": "TEXTURED"})),
    "DisplayLight": _e("KIT", (V3D, "maya_kit.display_mode", {"mode": "LIGHTS"}),
                       note="Material Preview + 씬 라이트 (근사)"),
    "PlaybackToggle": _e("KIT", ("Frames", "screen.animation_play", {})),
    "GoToMinFrame": _e("KIT", ("Frames", "screen.frame_jump", {"end": False})),
    "SelectToggleMode": _e("KIT", (OBJ_NM, "object.editmode_toggle", {}),
                           note="오브젝트 ↔ 마지막 컴포넌트 모드"),
    "ShowHotbox": _e("STEP", step=11, note="Space 는 핫박스 자리로 비워 둠 (재생은 Alt+V)"),

    # --- IC already matches (research/blender/industry_compatible_vs_maya.md §1) ---
    "Duplicate": _e("IC", (OBJ, "object.duplicate_move", {})),
    "FrameSelectedWithoutChildren": _e("IC", (V3D, "view3d.view_selected", {}),
                                       note="자식 제외 여부는 Step 4"),
    "SelectAllMarkingMenu": _e("IC", (V3D, "view3d.view_all", {}),
                               note="탭=Frame All. 홀드 마킹메뉴는 Step 3/10"),
    "RepeatLast": _e("IC", ("Screen", "screen.repeat_last", {})),
    "HideSelectedObjects": _e("IC", (OBJ, "object.hide_view_set", {})),
    "SetKey": _e("IC", (OBJ, "anim.keyframe_insert_by_name", {"type": "LocRotScale"}),
                  note="Maya 는 키 가능한 모든 채널, IC 는 LocRotScale"),
    "SetKeyTranslate": _e("IC", (OBJ, "anim.keyframe_insert_by_name", {"type": "Location"})),
    "SetKeyRotate": _e("IC", (OBJ, "anim.keyframe_insert_by_name", {"type": "Rotation"})),
    "SetKeyScale": _e("IC", (OBJ, "anim.keyframe_insert_by_name", {"type": "Scaling"})),
    "TranslateToolWithSnapMarkingMenu": _e("IC", (OBJ, "wm.tool_set_by_id", {"name": "builtin.move"}),
                                           note="툴 전환만. 홀드 마킹메뉴는 Step 10"),
    "RotateToolWithSnapMarkingMenu": _e("IC", (OBJ, "wm.tool_set_by_id", {"name": "builtin.rotate"}),
                                        note="툴 전환만. 홀드 마킹메뉴는 Step 10"),
    "ScaleToolWithSnapMarkingMenu": _e("IC", (OBJ, "wm.tool_set_by_id", {"name": "builtin.scale"}),
                                       note="툴 전환만. 홀드 마킹메뉴는 Step 10"),
    "SelectToolOptionsMarkingMenu": _e("IC", (OBJ, "wm.tool_set_by_id", {"name": "builtin.select_box"}),
                                       note="툴 전환만. 홀드 마킹메뉴는 Step 10"),

    # --- Planned ---
    "SnapToGridPress": _e("STEP", step=3, note="홀드 스냅"),
    "SnapToCurvePress": _e("STEP", step=3, note="홀드 스냅"),
    "SnapToPointPress": _e("STEP", step=3, note="홀드 스냅"),
    "MoveRotateScaleToolToggleSnapMode": _e("STEP", step=3, note="홀드 스텝 스냅"),
    "ModifyUpperRadiusPress": _e("STEP", step=3, note="B 홀드 소프트 셀렉트 반경"),
    "UndoViewChange": _e("STEP", step=4), "RedoViewChange": _e("STEP", step=4),
    "FrameAllInAllViews": _e("STEP", step=4),
    "FrameSelectedWithoutChildrenInAllViews": _e("STEP", step=4),
    "FrameSelectedInAllViews": _e("STEP", step=4),
    "GoToDefaultView": _e("STEP", step=4),
    "LowQualityDisplay": _e("STEP", step=5), "MediumQualityDisplay": _e("STEP", step=5),
    "HighQualityDisplay": _e("STEP", step=5), "DefaultQualityDisplay": _e("STEP", step=5),
    "SelectVertexMask": _e("STEP", step=5), "SelectEdgeMask": _e("STEP", step=5),
    "SelectFacetMask": _e("STEP", step=5), "SelectUVMask": _e("STEP", step=5),
    "SelectMultiComponentMask": _e("STEP", step=5), "SelectVertexFaceMask": _e("STEP", step=5),
    "ConvertSelectionToVertices": _e("STEP", step=5), "ConvertSelectionToEdges": _e("STEP", step=5),
    "ConvertSelectionToFaces": _e("STEP", step=5), "ConvertSelectionToUVs": _e("STEP", step=5),
    "ToggleIsolateSelect": _e("STEP", step=5),
    "HideUnselectedObjects": _e("STEP", step=5), "ShowSelectedObjects": _e("STEP", step=5),
    "ToggleVisibilityAndKeepSelection": _e("STEP", step=5),
    "ToggleWireframeOnShadedCmd": _e("STEP", step=5),
    "SmoothingLevelIncrease": _e("STEP", step=5), "SmoothingLevelDecrease": _e("STEP", step=5),
    "IncreaseManipulatorSize": _e("STEP", step=5), "DecreaseManipulatorSize": _e("STEP", step=5),
    "Parent": _e("STEP", step=6, note="IC P=parent_set 이지만 Maya식(로컬 재계산)으로 교체 예정"),
    "Unparent": _e("STEP", step=6),
    "PickWalkUp": _e("STEP", step=6), "PickWalkDown": _e("STEP", step=6),
    "PickWalkLeft": _e("STEP", step=6), "PickWalkRight": _e("STEP", step=6),
    "EnterEditModePress": _e("STEP", step=6, note="D 홀드 피벗 편집"),
    "EnterEditMode": _e("STEP", step=6, note="Insert 피벗 편집 토글"),
    "NextKey": _e("STEP", step=9), "PreviousKey": _e("STEP", step=9),
    "NextFrame": _e("STEP", step=9), "PreviousFrame": _e("STEP", step=9),
    "DeleteHistory": _e("STEP", step=12),
    "ShowModelingUI": _e("STEP", step=14), "ShowRiggingUI": _e("STEP", step=14),
    "ShowAnimationUI": _e("STEP", step=14), "ShowDynamicsUI": _e("STEP", step=14),
    "ShowRenderingUI": _e("STEP", step=14),

    # --- Not applicable ---
    "HIKPinRotate": _e("NO", note="HumanIK 없음"), "HIKPinTranslate": _e("NO", note="HumanIK 없음"),
    "HIKSetFullBodyKey": _e("NO", note="HumanIK 없음"),
    "IncrementFluidCenter": _e("NO", note="Maya Fluids 없음"),
    "DecrementFluidCenter": _e("NO", note="Maya Fluids 없음"),
    "CoarserSubdivLevel": _e("NO", note="Maya subdiv surface 노드 없음"),
    "CreateSubdivRegion": _e("NO", note="Maya subdiv surface 노드 없음"),
}


def entry_for(hotkey):
    """Mapping entry for a hotkeys_default.json item (None = unreviewed)."""
    rtc = (hotkey.get("press") or {}).get("runTimeCommand")
    if hotkey.get("context", "global") != "global":
        return ENTRIES.get(f"{hotkey['context']}:{rtc}")
    return ENTRIES.get(rtc)


# Blender keymaps searched (in this order) for the current binding of a Maya
# key, per Maya hotkey context. Approximates Blender's handler order in that
# editor: mode keymaps, editor keymap, generic, frames, screen, window.
CONTEXT_KEYMAPS = {
    "global": ("Object Non-modal", "Object Mode", "Mesh", "3D View", "3D View Generic",
               "Frames", "Screen", "Window"),
    "graphEditor": ("Graph Editor", "Graph Editor Generic", "Animation", "Frames",
                    "Screen", "Window"),
    "outlinerPanel": ("Outliner", "Screen", "Window"),
    "nodeEditorPanel": ("Node Editor", "Node Generic", "Screen", "Window"),
    "hyperShadePanel": ("Node Editor", "Node Generic", "Screen", "Window"),
    "timeEditorPanel": ("NLA Editor", "NLA Generic", "Frames", "Screen", "Window"),
    "polyTexturePlacementPanel": ("UV Editor", "Image", "Image Generic", "Screen", "Window"),
}


def current_bindings(kd, hotkey):
    """[(keymap, item)] bound to the Maya key in the matching Blender keymaps."""
    ev = maya_event(hotkey)
    out = []
    for km in CONTEXT_KEYMAPS.get(hotkey.get("context", "global"), ()):
        if km in kd.keymap_names():
            out.extend((km, it) for it in kd.find(km, **ev))
    return out


def check_entry(kd, hotkey, entry):
    """True if an IC/KIT entry's expected binding exists for this Maya key."""
    from .patch import props_dict
    km, idname, want = entry["check"]
    for item in kd.find(km, idname, **maya_event(hotkey)):
        props = props_dict(item[2])
        if all(props.get(k) == v for k, v in want.items()):
            return True
    return False
