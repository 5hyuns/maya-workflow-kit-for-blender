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
    "ShowHotbox": _e("KIT", (V3D, "maya_kit.hotbox", {}),
                     note="홀드=핫박스(메뉴 행·존 마킹메뉴), 탭=4분할↔단일 / 패널 최대화. 재생은 Alt+V"),

    # --- IC already matches () ---
    "Duplicate": _e("KIT", (OBJ, "maya_kit.duplicate", {}),
                    note="제자리, 자식 포함, pCube2/pCubeShape2 (편집 모드는 IC duplicate_move)"),
    "FrameSelectedWithoutChildren": _e("KIT", (V3D, "maya_kit.frame", {"selected": True}),
                                       note="Maya 여백 0.95, 사이드바 밑 제외, 선택 없으면 전체 (step 17)"),
    "SelectAllMarkingMenu": _e("KIT", (V3D, "maya_kit.tap_hold", {"binding": "select_all"}),
                               note="탭=Frame All, 홀드+클릭=선택 메뉴 (마킹메뉴 엔진은 Step 9)"),
    "RepeatLast": _e("IC", ("Screen", "screen.repeat_last", {})),
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
    "FrameSelectedInAllViews": _e("KIT", (V3D, "maya_kit.frame_all_views",
                                          {"selected": True, "children": True}),
                                  note="자식 포함, 창의 모든 3D 뷰"),
    "GoToDefaultView": _e("KIT", (V3D, "maya_kit.view_home", {}),
                          note="Maya 새 씬 persp 자리 (정사영: 방향 유지, 원점) — step 27"),
    "LowQualityDisplay": _e("KIT", (OBJ, "maya_kit.smooth_preview", {"level": 1}),
                            note="Subsurf 뷰포트 끔"),
    "MediumQualityDisplay": _e("KIT", (OBJ, "maya_kit.smooth_preview", {"level": 2}),
                               note="Subsurf + 와이어 (케이지 근사)"),
    "HighQualityDisplay": _e("KIT", (OBJ, "maya_kit.smooth_preview", {"level": 3}),
                             note="Subsurf 뷰포트 켬 (없으면 추가, 렌더 영향 없음)"),
    "DefaultQualityDisplay": _e("KIT", (OBJ, "maya_kit.smooth_preview", {"level": 1}),
                                note="1 과 같음 (거친 표시) — step 27"),
    "SelectVertexMask": _e("KIT", (OBJ_NM, "maya_kit.component_mode", {"type": "VERT"})),
    "SelectEdgeMask": _e("KIT", (OBJ_NM, "maya_kit.component_mode", {"type": "EDGE"})),
    "SelectFacetMask": _e("KIT", (OBJ_NM, "maya_kit.component_mode", {"type": "FACE"})),
    "SelectMultiComponentMask": _e("KIT", (OBJ_NM, "maya_kit.component_mode", {"type": "MULTI"}),
                                   note="정점·엣지·면 동시 선택 모드"),
    "SelectUVMask": _e("NO", note="3D 뷰 UV 컴포넌트 선택 없음 (UV Editor 사용)"),
    "SelectVertexFaceMask": _e("NO", note="Blender 에 vertex-face 컴포넌트 없음"),
    "ToggleFullScreenMode": _e("KIT", ("Screen", "screen.screen_full_area", {"use_hide_panels": True}),
                               note="UI 숨긴 전체 화면"),
    # --- step 18: mesh component keys ---
    "ConvertSelectionToVertices": _e("KIT", ("Mesh", "maya_kit.convert_selection", {"type": "VERT"})),
    "ConvertSelectionToEdges": _e("KIT", ("Mesh", "maya_kit.convert_selection", {"type": "EDGE"}),
                                  note="닿는 엣지 (면 -> 테두리 엣지)"),
    "ConvertSelectionToFaces": _e("KIT", ("Mesh", "maya_kit.convert_selection", {"type": "FACE"}),
                                  note="닿는 면 (Blender 모드 전환은 포함된 면만)"),
    "ConvertSelectionToUVs": _e("NO", note="3D 뷰 UV 컴포넌트 없음 (UV Editor 사용)"),
    "GrowPolygonSelectionRegion": _e("KIT", ("Mesh", "mesh.select_more", {})),
    "ShrinkPolygonSelectionRegion": _e("KIT", ("Mesh", "mesh.select_less", {})),
    "GrowLoopPolygonSelectionRegion": _e("KIT", ("Mesh", "mesh.select_next_item", {}),
                                         note="선택 순서 따라 한 칸 (루프 확장 근사)"),
    "ShrinkLoopPolygonSelectionRegion": _e("KIT", ("Mesh", "mesh.select_prev_item", {}),
                                           note="선택 순서 따라 한 칸 되돌림 (근사)"),
    "PolyExtrude": _e("KIT", ("Mesh", "view3d.edit_mesh_extrude_move_normal", {}),
                      note="압출 후 바로 법선 방향 이동 모달"),
    "BevelPolygon": _e("KIT", ("Mesh", "maya_kit.bevel", {}),
                       note="정점 모드 = 정점 베벨, 그 외 엣지; 드래그로 폭"),
    # --- step 24: component Delete; plain Delete/Backspace is
    # Maya's doDelete (not a hotkeySetup row): Mesh "maya_kit.delete_components" ---
    "DeletePolyElements": _e("IC", ("Mesh", "mesh.dissolve_mode", {}),
                             note="엣지·정점 dissolve (Delete Edge/Vertex); Delete/Backspace = 바로 삭제 (step 24)"),
    # --- step 16: undo / visibility / isolate ---
    "Undo": _e("KIT", ("Screen", "ed.undo", {}),
               note="Screen 키맵: 모든 에디터. z 를 가리던 zoom/viewer border 제거 (Shift+B 로 남음)"),
    "Redo": _e("KIT", ("Screen", "ed.redo", {})),
    "ToggleVisibilityAndKeepSelection": _e("KIT", (OBJ, "maya_kit.visibility", {"action": "TOGGLE"}),
        note="숨긴 객체를 '선택 유지' 표시로 기억, 다시 h = 보이고 선택 (오브젝트 모드)"),
    "HideSelectedObjects": _e("KIT", (OBJ, "maya_kit.visibility", {"action": "HIDE"}),
                              note="컴포넌트: Mesh mesh.hide (IC)"),
    "HideUnselectedObjects": _e("KIT", (OBJ, "maya_kit.visibility", {"action": "HIDE_UNSELECTED"}),
                                note="컴포넌트: mesh.hide(unselected)"),
    "ShowSelectedObjects": _e("KIT", (OBJ, "maya_kit.visibility", {"action": "SHOW_SELECTED"}),
                              note="h 로 숨긴 선택 + 숨겨진 활성 객체; 컴포넌트: mesh.reveal"),
    "ShowLastHidden": _e("KIT", (OBJ, "maya_kit.visibility", {"action": "SHOW_LAST"}),
                         note="킷 숨김 동작(h/Ctrl+H/Alt+H)의 마지막 대상; 컴포넌트: mesh.reveal"),
    "ShowAllPolyComponents": _e("KIT", ("Mesh", "mesh.reveal", {})),
    "ToggleIsolateSelect": _e("KIT", (V3D, "view3d.localview", {"frame_selected": False}),
                              note="로컬 뷰 (카메라 그대로), 다시 누르면 해제"),
    "SelectIsolate": _e("IC", (V3D, "view3d.localview", {}), note="로컬 뷰 토글 (프레이밍 포함)"),
    "InvertSelection": _e("KIT", (OBJ, "object.select_all", {"action": "INVERT"}),
                          note="편집 모드: mesh.select_all(INVERT)"),
    "ToggleWireframeOnShadedCmd": _e("KIT", (V3D, "wm.context_toggle",
                                             {"data_path": "space_data.overlay.show_wireframes"}),
                                     note="뷰포트 오버레이 Wireframe (모든 오브젝트) — step 27"),
    "SmoothingLevelIncrease": _e("KIT", (OBJ, "maya_kit.smooth_level", {"delta": 1}),
                                 note="스무스 프리뷰 단계 0–4 — step 27"),
    "SmoothingLevelDecrease": _e("KIT", (OBJ, "maya_kit.smooth_level", {"delta": -1})),
    "IncreaseManipulatorSize": _e("KIT", (V3D, "maya_kit.manip_size", {"factor": 1.25}),
                                  note="gizmo_size ×1.25 (Maya ×2), 끄면 원래 값 — step 27"),
    "DecreaseManipulatorSize": _e("KIT", (V3D, "maya_kit.manip_size", {"factor": 0.8})),
    "Parent": _e("KIT", (OBJ, "maya_kit.parent", {}),
                 note="월드 유지, parent inverse 단위행렬 (환경설정 Parent Mode=Blender 로 IC 방식)"),
    "Unparent": _e("KIT", (OBJ, "maya_kit.unparent", {}), note="월드로, 월드 유지"),
    "PickWalkUp": _e("KIT", (OBJ, "maya_kit.pick_walk", {"direction": "UP"}),
                     note="오브젝트 모드만 (컴포넌트는 미구현)"),
    "PickWalkDown": _e("KIT", (OBJ, "maya_kit.pick_walk", {"direction": "DOWN"}),
                       note="오브젝트 모드만"),
    "PickWalkLeft": _e("KIT", (OBJ, "maya_kit.pick_walk", {"direction": "LEFT"}),
                       note="오브젝트 모드만, 이름순 형제 순환"),
    "PickWalkRight": _e("KIT", (OBJ, "maya_kit.pick_walk", {"direction": "RIGHT"}),
                        note="오브젝트 모드만, 이름순 형제 순환"),
    "EnterEditModePress": _e("KIT", (OBJ, "maya_kit.hold", {"name": "pivot"}),
                             note="오브젝트 모드: 누르는 동안 Affect Only Origins; 편집 모드: 3D 커서 피벗 배치 (step 18)"),
    "EnterEditMode": _e("KIT", (OBJ, "maya_kit.pivot_toggle", {}),
                        note="Affect Only Origins 토글 (오브젝트 모드)"),
    # --- step 20: key / frame stepping ---
    "NextKey": _e("KIT", ("Frames", "screen.keyframe_jump", {"next": True}),
                  note="Frames 키맵 (대부분 에디터); 3D View 피벗 파이는 헤더로"),
    "PreviousKey": _e("KIT", ("Frames", "screen.keyframe_jump", {"next": False}),
                      note="3D View 방향 파이는 헤더로"),
    "NextFrame": _e("KIT", ("Frames", "screen.frame_offset", {"delta": 1}), note="누르고 있으면 반복"),
    "PreviousFrame": _e("KIT", ("Frames", "screen.frame_offset", {"delta": -1})),
    "DeleteHistory": _e("KIT", (OBJ, "maya_kit.delete_history", {}),
                        note="모디파이어 + 셰이프 키를 메시에 굽기"),
    "DuplicateSpecial": _e("KIT", (OBJ, "maya_kit.duplicate_special", {}),
                           note="복사/인스턴스, 사본 수, 누적 오프셋 (Adjust Last Operation)"),
    "ShowAttributeEditorOrChannelBox": _e("KIT", (OBJ, "maya_kit.ae_toggle", {}),
                                          note="사이드바 Channel Box 탭 안에서 CB/LE ↔ AE 전환"),
    "SelectAll": _e("KIT", (OBJ, "object.select_all", {"action": 'SELECT'}),
                    note="편집 모드: mesh.select_all(SELECT)"),
    "SelectNone": _e("KIT", (OBJ, "object.select_all", {"action": 'DESELECT'}),
                     note="편집 모드: maya_kit.select_none (해제 + 오브젝트 모드)"),
    "DuplicateWithTransform": _e("KIT", (OBJ, "maya_kit.duplicate_with_transform", {}),
                                 note="직전 복제의 변환을 반복"),
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
