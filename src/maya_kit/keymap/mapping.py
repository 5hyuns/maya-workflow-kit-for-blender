# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya runTimeCommand -> Blender handling, for .

Pure Python. Used by tools/gen_keymap_mapping.py (writes the doc) and by
tests/test_keymap_maya.py (checks every IC/KIT row is really bound).

Maya side:  (keys, contexts and
runTimeCommand names only; no MEL is copied, ).

Status:
  IC    Industry Compatible already does the Maya thing; kept.
  KIT   Bound by this kit's "Maya" keyconfig.
  STEP  Planned in  step ``step``.
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
    "ShowHotbox": _e("STEP", step=10, note="탭=4분할↔단일 뷰 구현 (maya_kit.tap_hold space), "
                     "홀드 핫박스는 Step 10. 재생은 Alt+V"),

    # --- IC already matches () ---
    "Duplicate": _e("IC", (OBJ, "object.duplicate_move", {})),
    "FrameSelectedWithoutChildren": _e("IC", (V3D, "view3d.view_selected", {}),
                                       note="선택만 프레이밍 (자식은 선택 안 되면 제외)"),
    "SelectAllMarkingMenu": _e("KIT", (V3D, "maya_kit.tap_hold", {"binding": "select_all"}),
                               note="탭=Frame All, 홀드+클릭=선택 메뉴 (마킹메뉴 엔진은 Step 9)"),
    "RepeatLast": _e("IC", ("Screen", "screen.repeat_last", {})),
    "HideSelectedObjects": _e("IC", (OBJ, "object.hide_view_set", {})),
    "SetKey": _e("IC", (OBJ, "anim.keyframe_insert_by_name", {"type": "LocRotScale"}),
                  note="Maya 는 키 가능한 모든 채널, IC 는 LocRotScale"),
    "SetKeyTranslate": _e("IC", (OBJ, "anim.keyframe_insert_by_name", {"type": "Location"})),
    "SetKeyRotate": _e("IC", (OBJ, "anim.keyframe_insert_by_name", {"type": "Rotation"})),
    "SetKeyScale": _e("IC", (OBJ, "anim.keyframe_insert_by_name", {"type": "Scaling"})),
    "TranslateToolWithSnapMarkingMenu": _e("KIT", (OBJ, "maya_kit.tap_hold", {"binding": "tool_move"}),
        note="누름=툴 전환, 누른 채 LMB=Move 옵션 마킹메뉴(파이, Step 8)"),
    "RotateToolWithSnapMarkingMenu": _e("KIT", (OBJ, "maya_kit.tap_hold", {"binding": "tool_rotate"}),
        note="누름=툴 전환, 누른 채 LMB=Rotate 옵션 마킹메뉴(파이, Step 8)"),
    "ScaleToolWithSnapMarkingMenu": _e("KIT", (OBJ, "maya_kit.tap_hold", {"binding": "tool_scale"}),
        note="누름=툴 전환, 누른 채 LMB=Scale 옵션 마킹메뉴(파이, Step 8)"),
    "SelectToolOptionsMarkingMenu": _e("KIT", (OBJ, "maya_kit.tap_hold", {"binding": "tool_select"}),
        note="누름=툴 전환, 누른 채 LMB=Select 옵션 마킹메뉴(파이, Step 8)"),

    # --- Planned ---
    "SnapToGridPress": _e("KIT", (V3D, "maya_kit.hold", {"name": "grid"}),
                          note="누르는 동안 GRID 스냅, 놓으면 복원"),
    "SnapToCurvePress": _e("KIT", (V3D, "maya_kit.hold", {"name": "curve"}),
                           note="누르는 동안 EDGE 스냅 (커브 전용 없음, 근사)"),
    "SnapToPointPress": _e("KIT", (V3D, "maya_kit.hold", {"name": "point"}),
                           note="누르는 동안 VERTEX 스냅"),
    "MoveRotateScaleToolToggleSnapMode": _e("KIT", (V3D, "maya_kit.hold", {"name": "step"}),
                                            note="누르는 동안 INCREMENT 스냅"),
    "MoveRotateScaleToolToggleSnapRelativeMode": _e("KIT", (V3D, "maya_kit.hold", {"name": "step"}),
                                                    note="J 와 동일 (INCREMENT 는 상대 증분)"),
    "ModifyUpperRadiusPress": _e("KIT", (V3D, "maya_kit.tap_hold", {"binding": "soft_select"}),
                                 note="탭=소프트 셀렉트 토글, 홀드+LMB 드래그=반경"),
    "UndoViewChange": _e("KIT", (V3D, "maya_kit.view_history", {"direction": "UNDO"}),
                         note="뷰 전용 스택 (씬 언두와 별개)"),
    "RedoViewChange": _e("KIT", (V3D, "maya_kit.view_history", {"direction": "REDO"})),
    "FrameAllInAllViews": _e("KIT", (V3D, "maya_kit.frame_all_views", {"selected": False}),
                             note="창의 모든 3D 뷰(쿼드 포함)"),
    "FrameSelectedWithoutChildrenInAllViews": _e("KIT", (V3D, "maya_kit.frame_all_views",
                                                         {"selected": True}),
                                                 note="창의 모든 3D 뷰(쿼드 포함)"),
    "FrameSelectedInAllViews": _e("STEP", step=8, note="자식 포함 프레이밍"),
    "GoToDefaultView": _e("STEP", step=8),
    "LowQualityDisplay": _e("KIT", (OBJ, "maya_kit.smooth_preview", {"level": 1}),
                            note="Subsurf 뷰포트 끔"),
    "MediumQualityDisplay": _e("KIT", (OBJ, "maya_kit.smooth_preview", {"level": 2}),
                               note="Subsurf + 와이어 (케이지 근사)"),
    "HighQualityDisplay": _e("KIT", (OBJ, "maya_kit.smooth_preview", {"level": 3}),
                             note="Subsurf 뷰포트 켬 (없으면 추가, 렌더 영향 없음)"),
    "DefaultQualityDisplay": _e("STEP", step=8),
    "SelectVertexMask": _e("KIT", (OBJ_NM, "maya_kit.component_mode", {"type": "VERT"})),
    "SelectEdgeMask": _e("KIT", (OBJ_NM, "maya_kit.component_mode", {"type": "EDGE"})),
    "SelectFacetMask": _e("KIT", (OBJ_NM, "maya_kit.component_mode", {"type": "FACE"})),
    "SelectMultiComponentMask": _e("KIT", (OBJ_NM, "maya_kit.component_mode", {"type": "MULTI"}),
                                   note="정점·엣지·면 동시 선택 모드"),
    "SelectUVMask": _e("NO", note="3D 뷰 UV 컴포넌트 선택 없음 (UV Editor 사용)"),
    "SelectVertexFaceMask": _e("NO", note="Blender 에 vertex-face 컴포넌트 없음"),
    "ToggleFullScreenMode": _e("KIT", ("Screen", "screen.screen_full_area", {"use_hide_panels": True}),
                               note="UI 숨긴 전체 화면"),
    "ConvertSelectionToVertices": _e("STEP", step=8), "ConvertSelectionToEdges": _e("STEP", step=8),
    "ConvertSelectionToFaces": _e("STEP", step=8), "ConvertSelectionToUVs": _e("STEP", step=8),
    "ToggleIsolateSelect": _e("STEP", step=8),
    "HideUnselectedObjects": _e("STEP", step=8), "ShowSelectedObjects": _e("STEP", step=8),
    "ToggleVisibilityAndKeepSelection": _e("STEP", step=8),
    "ToggleWireframeOnShadedCmd": _e("STEP", step=8),
    "SmoothingLevelIncrease": _e("STEP", step=8), "SmoothingLevelDecrease": _e("STEP", step=8),
    "IncreaseManipulatorSize": _e("STEP", step=8), "DecreaseManipulatorSize": _e("STEP", step=8),
    "Parent": _e("STEP", step=8, note="IC P=parent_set 이지만 Maya식(로컬 재계산)으로 교체 예정"),
    "Unparent": _e("STEP", step=8),
    "PickWalkUp": _e("KIT", (OBJ, "maya_kit.pick_walk", {"direction": "UP"}),
                     note="오브젝트 모드만 (컴포넌트는 미구현)"),
    "PickWalkDown": _e("KIT", (OBJ, "maya_kit.pick_walk", {"direction": "DOWN"}),
                       note="오브젝트 모드만"),
    "PickWalkLeft": _e("KIT", (OBJ, "maya_kit.pick_walk", {"direction": "LEFT"}),
                       note="오브젝트 모드만, 이름순 형제 순환"),
    "PickWalkRight": _e("KIT", (OBJ, "maya_kit.pick_walk", {"direction": "RIGHT"}),
                        note="오브젝트 모드만, 이름순 형제 순환"),
    "EnterEditModePress": _e("KIT", (OBJ, "maya_kit.hold", {"name": "pivot"}),
                             note="누르는 동안 Affect Only Origins (오브젝트 모드)"),
    "EnterEditMode": _e("KIT", (OBJ, "maya_kit.pivot_toggle", {}),
                        note="Affect Only Origins 토글 (오브젝트 모드)"),
    "NextKey": _e("STEP", step=7), "PreviousKey": _e("STEP", step=7),
    "NextFrame": _e("STEP", step=7), "PreviousFrame": _e("STEP", step=7),
    "DeleteHistory": _e("STEP", step=11),
    "ShowModelingUI": _e("STEP", step=13), "ShowRiggingUI": _e("STEP", step=13),
    "ShowAnimationUI": _e("STEP", step=13), "ShowDynamicsUI": _e("STEP", step=13),
    "ShowRenderingUI": _e("STEP", step=13),

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
