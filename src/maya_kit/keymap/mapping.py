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
    "SelectToggleMode": _e("KIT", (OBJ_NM, "maya_kit.toggle_sel_mode", {}),
                           note="오브젝트 ↔ 마지막 컴포넌트 모드"),
    "ShowHotbox": _e("KIT", (V3D, "maya_kit.hotbox", {}),
                     note="홀드=핫박스(메뉴 행·존 마킹메뉴), 탭=4분할↔단일 / 패널 최대화. 재생은 Alt+V"),

    # --- IC already matches (research/blender/industry_compatible_vs_maya.md §1) ---
    "Duplicate": _e("KIT", (OBJ, "maya_kit.duplicate", {}),
                    note="제자리, 자식 포함, pCube2/pCubeShape2 (편집 모드는 IC duplicate_move)"),
    "FrameSelectedWithoutChildren": _e("KIT", (V3D, "maya_kit.frame", {"selected": True}),
                                       note="Maya 여백 0.95, 사이드바 밑 제외, 선택 없으면 전체 (step 17)"),
    "SelectAllMarkingMenu": _e("KIT", (V3D, "maya_kit.tap_hold", {"binding": "select_all"}),
                               note="탭=Frame All, 홀드+클릭=선택 메뉴 (마킹메뉴 엔진은 Step 9)"),
    "RepeatLast": _e("IC", ("Screen", "screen.repeat_last", {})),
    "SetKey": _e("KIT", (OBJ, "maya_kit.set_key", {}),
                  note="키 가능한 모든 채널 (가시성·커스텀 포함, Hide/Nonkeyable 제외), 포즈 모드 = 선택 본; "
                       "활성 Keying Set 이 있으면 그것 (step 56)"),
    "TimeDraggerToolActivate": _e("KIT", ("Screen", "maya_kit.tap_hold", {"binding": "time_drag"}),
                                  note="K 누른 채 LMB 드래그 = 시간 (어느 에디터든), 선택 그대로; Mesh knife K → "
                                       "Multi-Cut 은 Ctrl+Shift+X (step 56)"),
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
                          note="누르는 동안 GRID 스냅 (절대 그리드 선, 매니퓰레이터 중심), 놓으면 복원 — step 59"),
    "SnapToCurvePress": _e("KIT", (V3D, "maya_kit.hold", {"name": "curve"}),
                           note="누르는 동안 EDGE 스냅 (커브 전용 없음, 근사)"),
    "SnapToPointPress": _e("KIT", (V3D, "maya_kit.hold", {"name": "point"}),
                           note="누르는 동안 VERTEX 스냅 (매니퓰레이터 중심이 정점에) — step 59"),
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
    "SelectUVMask": _e("KIT", (OBJ, "maya_kit.uv_component", {"mode": 'UV'}),
                       note="UV Editor 를 열고 (편집 모드) UV 선택 = UV Sync 끔 + UV 정점 (step 66)"),
    "SelectMeshUVShell": _e("KIT", (OBJ, "maya_kit.uv_component", {"mode": 'SHELL'}),
                            note="UV Editor 를 열고 UV Shell = Blender UV 섬 모드 (step 66)"),
    # --- step 66: UV Editor (polyTexturePlacementPanel) ---
    "polyTexturePlacementPanel:CutUVs": _e("KIT", ("UV Editor", "maya_kit.uv_cut", {}),
                                           note="솔기 + 작은 쪽 셸을 0.2 px 떼어 그 자리에서 분리 (IC 스냅 파이 제거)"),
    "polyTexturePlacementPanel:SewUVs": _e("KIT", ("UV Editor", "maya_kit.uv_sew", {}),
                                           note="솔기 지움 + 작은 셸을 엣지에 맞춰 옮김"),
    "polyTexturePlacementPanel:UnfoldUV": _e("KIT", ("UV Editor", "maya_kit.uv_unfold", {}),
                                             note="Blender Unwrap (Minimum Stretch), 셸 경계·자리 유지 (Unfold3D 아님)"),
    "polyTexturePlacementPanel:LayoutUV": _e("KIT", ("UV Editor", "maya_kit.uv_layout", {}),
                                             note="Pack Islands, 셸 패딩 px / 맵 크기 (IC select_linked 제거)"),
    "SelectVertexFaceMask": _e("NO", note="Blender 에 vertex-face 컴포넌트 없음"),
    "ToggleFullScreenMode": _e("KIT", ("Screen", "screen.screen_full_area", {"use_hide_panels": True}),
                               note="UI 숨긴 전체 화면"),
    # --- step 18: mesh component keys (docs/steps/step_18.md) ---
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
    "PolyExtrude": _e("KIT", ("Mesh", "maya_kit.extrude", {}),
                      note="polyExtrudeFace: 길이 0 압출 + 매니퓰레이터·In-View Editor·INPUTS (step 65); 엣지/정점은 압출 + 법선 드래그"),
    "BevelPolygon": _e("KIT", ("Mesh", "maya_kit.bevel", {}),
                       note="정점 모드 = 정점 베벨, 그 외 엣지; 드래그로 폭"),
    # --- step 24: component Delete (docs/steps/step_24.md); plain Delete/Backspace is
    # Maya's doDelete (not a hotkeySetup row): Mesh "maya_kit.delete_components" ---
    "DeletePolyElements": _e("IC", ("Mesh", "mesh.dissolve_mode", {}),
                             note="엣지·정점 dissolve (Delete Edge/Vertex); Delete/Backspace = 바로 삭제 (step 24)"),
    # --- step 16: undo / visibility / isolate (docs/steps/step_16.md) ---
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
                 note="월드 유지, parent inverse 단위행렬 (환경설정 Parent Mode=Blender 로 IC 방식); "
                      "포즈·아마추어 편집 모드 = `maya_kit.parent_joint` (조인트, 제자리) — step 57"),
    "Unparent": _e("KIT", (OBJ, "maya_kit.unparent", {}),
                   note="월드로, 월드 유지; 포즈·아마추어 편집 모드 = `maya_kit.unparent_joint` (step 57)"),
    "PickWalkUp": _e("KIT", (OBJ, "maya_kit.pick_walk", {"direction": "UP"}),
                     note="편집 모드: 엣지 = 링, 정점·면 = 화면 위쪽 이웃 (step 39); 포즈 모드: 부모 조인트 (step 57)"),
    "PickWalkDown": _e("KIT", (OBJ, "maya_kit.pick_walk", {"direction": "DOWN"}),
                       note="편집 모드: 엣지 = 링, 정점·면 = 화면 아래쪽 이웃 (step 39); 포즈 모드: 첫 자식 조인트 (step 57)"),
    "PickWalkLeft": _e("KIT", (OBJ, "maya_kit.pick_walk", {"direction": "LEFT"}),
                       note="이름순 형제 순환; 편집 모드: 엣지 = 루프, 정점·면 = 화면 왼쪽 이웃 (step 39); 포즈 모드: 형제 조인트"),
    "PickWalkRight": _e("KIT", (OBJ, "maya_kit.pick_walk", {"direction": "RIGHT"}),
                        note="이름순 형제 순환; 편집 모드: 엣지 = 루프, 정점·면 = 화면 오른쪽 이웃 (step 39); 포즈 모드: 형제 조인트"),
    "EnterEditModePress": _e("KIT", (OBJ, "maya_kit.hold", {"name": "pivot"}),
                             note="오브젝트 모드: 누르는 동안 피벗 편집 (Translate 불변, 자식 제자리, step 59); 편집 모드: 3D 커서 피벗 배치 (step 18)"),
    "EnterEditMode": _e("KIT", (OBJ, "maya_kit.pivot_toggle", {}),
                        note="피벗 편집 토글 (오브젝트 모드, Translate 불변 — step 59)"),
    # --- step 20: key / frame stepping (docs/steps/step_20.md) ---
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
    "AssignNewMaterial": _e("KIT", (OBJ, "maya_kit.assign_new_material", {}),
                            note="재질 종류 검색 팝업 → 만들어 지정 (편집 모드 면 선택 = 면에만, step 29)"),
    # --- step 35 ---
    **{rtc: _e("KIT", ("Screen", "maya_kit.menu_set", {"set": sid}),
               note="메뉴 세트 전환 (IC 3D 뷰 F2–F5 뷰 키 대신; 직교 뷰는 핫박스·Space·Ctrl+F1–F3)")
       for rtc, sid in (("ShowModelingUI", "modelingMenuSet"), ("ShowRiggingUI", "riggingMenuSet"),
                        ("ShowAnimationUI", "animationMenuSet"), ("ShowDynamicsUI", "dynamicsMenuSet"),
                        ("ShowRenderingUI", "renderingMenuSet"))},
    "UniversalManip": _e("KIT", (OBJ, "wm.tool_set_by_id", {"name": "builtin.transform"})),
    "ShowManipulators": _e("IC", (OBJ, "wm.tool_set_by_id", {"name": "builtin.transform"}),
                           note="Blender 에 Show Manipulator 툴 없음: Transform 툴"),
    "NonSacredTool": _e("KIT", (OBJ, "maya_kit.last_tool", {}),
                        note="Q/W/E/R/T 가 아닌 마지막 툴 (모드별 기억)"),
    "MultiCutToolNameCommand": _e("KIT", (OBJ, "maya_kit.menu_tool", {"tool": "builtin.knife"}),
                                  note="Knife, 오브젝트 모드면 편집 모드로; 툴 안 Ctrl+클릭 = 엣지 루프 (Ctrl+MMB 가운데), "
                                       "Shift = Snap Step % (step 64)"),
    "QuadDrawToolNameCommand": _e("KIT", (OBJ, "maya_kit.menu_tool", {"tool": "builtin.poly_build"}),
                                  note="Poly Build, 오브젝트 모드면 편집 모드로"),
    "CompleteCurrentTool": _e("NO", note="Blender 모달 툴은 자기 키맵의 Return 으로 확정; 3D 뷰의 IC 이름 바꾸기 팝오버는 제거"),

    # --- Not applicable ---
    "HIKPinRotate": _e("NO", note="HumanIK 없음"), "HIKPinTranslate": _e("NO", note="HumanIK 없음"),
    "HIKSetFullBodyKey": _e("NO", note="HumanIK 없음"),
    "IncrementFluidCenter": _e("NO", note="Maya Fluids 없음"),
    "DecrementFluidCenter": _e("NO", note="Maya Fluids 없음"),
    "CoarserSubdivLevel": _e("NO", note="Maya subdiv surface 노드 없음"),
    "CreateSubdivRegion": _e("NO", note="Maya subdiv surface 노드 없음"),
    # --- step 70: Graph Editor, Shift+S keyframe / tangent marking menu (operators/graph_keys.py) ---
    "graphEditor:GraphEditorFrameAll": _e("IC", ("Graph Editor", "graph.view_all", {})),
    "graphEditor:GraphEditorFrameSelected": _e("IC", ("Graph Editor", "graph.view_selected", {})),
    "graphEditor:GraphEditorFramePlaybackRange": _e("KIT", ("Graph Editor", "anim.scene_range_frame", {}),
                                                    note="재생 범위 (preview 켜져 있으면 그 범위) 로 가로 맞춤"),
    "graphEditor:TangentAuto": _e("KIT", ("Graph Editor", "maya_kit.set_tangent", {"kind": "AUTO"}),
                                  note="선택 키 = Bezier + Auto Clamped"),
    "KeyframeTangentMarkingMenu": _e("KIT", (OBJ, "maya_kit.tap_hold", {"binding": "key_tangent"}),
                                     note="홀드 + LMB = Keys / Tangents 마킹 메뉴 (Graph Editor·Dope Sheet·포즈도), 탭 = 없음"),
    # --- step 69: scene files (Window keymap, operators/project.py) ---
    "OpenScene": _e("KIT", ("Window", "maya_kit.open_scene", {}), note="파일 창이 프로젝트 scenes 폴더에서 시작 (없으면 Blender 그대로)"),
    "SaveScene": _e("KIT", ("Window", "maya_kit.save_scene", {}), note="처음 저장은 프로젝트 scenes 폴더에서 Save As"),
    "SaveSceneAs": _e("KIT", ("Window", "maya_kit.save_scene_as", {}), note="프로젝트 scenes 폴더에서 시작"),
    "IncrementAndSave": _e("KIT", ("Window", "maya_kit.increment_save", {}),
                           note="Maya 규칙 shot_v001 → shot_v001.0001 (메뉴와 같음; IC 의 Blender 규칙 shot_v002 대신)"),
    "CreateReference": _e("KIT", ("Window", "maya_kit.create_reference", {}),
                          note=".blend 링크 + library override, 이름 ns:이름 (편집 모드 등 Ctrl+R 이 있는 에디터는 그쪽 우선)"),
}


def entry_for(hotkey):
    """Mapping entry for a hotkeys_default.json item (None = unreviewed)."""
    press = hotkey.get("press") or {}
    # MTK keys (Ctrl+Shift+X / Q) only have a nameCommand (research/maya/hotkeys_and_menus.md:281)
    rtc = press.get("runTimeCommand") or press.get("nameCommand")
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
