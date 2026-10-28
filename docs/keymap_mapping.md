# Maya 기본 단축키 → Blender 대응표

자동 생성: `python tools/gen_keymap_mapping.py` (손으로 고치지 말 것).
입력: `research/maya/hotkeys_default.json` (Maya 2026 팩토리 핫키 495개; 근거 열 = Maya 2026 기본 핫키 목록의 순번). Blender 쪽: 이 킷의 "Maya" 키컨피그 (`src/allset/keymap/`), 상태 = `keymap/mapping.py`.

현재 바인딩 = Maya 컨텍스트에 대응하는 Blender 키맵들(`mapping.CONTEXT_KEYMAPS`)에서 같은 키에 걸린 항목. 근사 조회라 모드에 따라 실제로 먼저 잡히는 항목은 다를 수 있다.

| 상태 | 개수 |
|---|---|
| 구현 | 216 |
| IC 일치 | 27 |
| 해당 없음 | 181 |
| macOS 전용 | 71 |

| Maya 키 | Blender 이벤트 | 컨텍스트 | runTimeCommand | Maya 키컨피그 현재 바인딩 | 상태 | 비고 | 근거 |
|---|---|---|---|---|---|---|---|
| Ctrl+Shift+A | Ctrl+Shift+A | global | SelectAll | Object Mode: `object.select_all` (action='SELECT'); Mesh: `mesh.select_all` (action='SELECT') | 구현 | 편집 / 포즈 / UV 모드: <모드>.select_all(SELECT) (step 141) | #63 |
| Ctrl+Shift+C | Ctrl+Shift+C | global | CreateCameraFromView | Object Mode: `allset.camera_from_view` | 구현 | 뷰와 같은 camera1 (렌즈·직교 크기), 뷰는 그대로 | #64 |
| Alt+d | Alt+D | global | SelectNone | Object Mode: `allset.select_none`; Mesh: `allset.select_none` | 구현 | allset.select_none clears object/bone selection and the active object, leaving component/Pose mode | #66 |
| Ctrl+d | Ctrl+D | global | Duplicate | Object Mode: `allset.duplicate`; Mesh: `allset.component_command` (item='Edit/Duplicate') | 구현 | 제자리, 자식 포함, pCube2/pCubeShape2 (컴포넌트 모드: Maya처럼 복제 없음 + 경고, step 129) | #68 |
| Ctrl+Shift+D | Ctrl+Shift+D | global | DuplicateSpecial | Object Mode: `allset.duplicate_special` | 구현 | 복사/인스턴스, 사본 수, 누적 오프셋 (Adjust Last Operation) | #69 |
| z | Z | global | Undo | Screen: `ed.undo` | 구현 | Screen 키맵: 모든 에디터. z 를 가리던 zoom/viewer border 제거 (Shift+B 로 남음) | #71 |
| Ctrl+z | Ctrl+Z | global | Undo | Screen: `asset.catalog_undo`; Screen: `ed.undo` | 구현 | Screen 키맵: 모든 에디터. z 를 가리던 zoom/viewer border 제거 (Shift+B 로 남음) | #72 |
| Shift+Z | Shift+Z | global | Redo | Screen: `ed.redo` | 구현 |  | #73 |
| Ctrl+q | Ctrl+Q | global | Quit | Window: `wm.quit_blender` | IC 일치 |  | #75 |
| Ctrl+o | Ctrl+O | global | OpenScene | Window: `allset.open_scene` | 구현 | 파일 창이 프로젝트 scenes 폴더에서 시작 (없으면 Blender 그대로) | #77 |
| Ctrl+n | Ctrl+N | global | NewScene | Window: `allset.new_maya_scene` | 구현 | 새 장면 = Maya 레이아웃 파일 (File > New Scene 와 같음, #44) | #78 |
| Ctrl+s | Ctrl+S | global | SaveScene | Window: `allset.save_scene` | 구현 | 처음 저장은 프로젝트 scenes 폴더에서 Save As | #79 |
| Ctrl+Shift+S | Ctrl+Shift+S | global | SaveSceneAs | Window: `allset.save_scene_as` | 구현 | 프로젝트 scenes 폴더에서 시작 | #80 |
| Ctrl+Alt+s | Ctrl+Alt+S | global | IncrementAndSave | Window: `allset.increment_save` | 구현 | Maya 규칙 shot_v001 → shot_v001.0001 (메뉴와 같음; IC 의 Blender 규칙 shot_v002 대신) | #81 |
| Ctrl+r | Ctrl+R | global | CreateReference | Window: `allset.create_reference` | 구현 | .blend 링크 + library override, 이름 ns:이름 (편집 모드 등 Ctrl+R 이 있는 에디터는 그쪽 우선) | #82 |
| Ctrl+g | Ctrl+G | global | Group | Object Mode: `allset.group` | 구현 | Empty 그룹, 피벗 원점, group1 명명 (Outliner 도) | #83 |
| Ctrl+Shift+I | Ctrl+Shift+I | global | InvertSelection | Object Mode: `object.select_all` (action='INVERT'); Mesh: `mesh.select_all` (action='INVERT') | 구현 | 편집 모드: mesh.select_all(INVERT) | #85 |
| Ctrl+x | Ctrl+X | global | CutSelected | Object Mode: `allset.cut` | 구현 | 선택 (+ 그 아래 계층) 을 클립보드로 복사 후 삭제, Ctrl+V 로 되돌림 (Outliner 도) | #88 |
| Ctrl+c | Ctrl+C | global | CopySelected | 3D View: `view3d.copybuffer` | IC 일치 | 선택 오브젝트를 Blender 클립보드로 | #89 |
| Ctrl+v | Ctrl+V | global | PasteSelected | Object Mode: `allset.paste`; 3D View: `view3d.pastebuffer` | 구현 | Blender 붙여넣기 + 첫 오브젝트가 lead (Channel Box); Maya 의 pasted_ 접두사는 없음 (이름이 비면 원래 이름) | #90 |
| Ctrl+Up | Ctrl+UP_ARROW | global | CutSliderExpandShots | — | 해당 없음 | Camera Sequencer 샷 없음 (Blender 는 마커 / VSE); IC Ctrl+화살표 그대로 | #93 |
| Ctrl+Down | Ctrl+DOWN_ARROW | global | CutSliderShrinkShots | — | 해당 없음 | Camera Sequencer 샷 없음 | #94 |
| Ctrl+Left | Ctrl+LEFT_ARROW | global | CutSliderPrevShot | Object Mode: `screen.frame_jump` (end=False) | 해당 없음 | Camera Sequencer 샷 없음 | #95 |
| Ctrl+Right | Ctrl+RIGHT_ARROW | global | CutSliderNextShot | Object Mode: `screen.frame_jump` (end=True) | 해당 없음 | Camera Sequencer 샷 없음 | #96 |
| Cmd+Up | Oskey+UP_ARROW | global | CutSliderExpandShots | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #100 |
| Cmd+Down | Oskey+DOWN_ARROW | global | CutSliderShrinkShots | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #101 |
| Cmd+Left | Oskey+LEFT_ARROW | global | CutSliderPrevShot | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #102 |
| Cmd+Right | Oskey+RIGHT_ARROW | global | CutSliderNextShot | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #103 |
| a | A | motionMakerEditor | MotionMakerEditorFrameAll | — | 해당 없음 | Maya 2026 MotionMaker 편집기 없음 | #108 |
| f | F | motionMakerEditor | MotionMakerEditorFrameSelection | — | 해당 없음 | Maya 2026 MotionMaker 편집기 없음 | #109 |
| g | G | motionMakerEditor | MotionMakerEditorFramePlaybackRange | — | 해당 없음 | Maya 2026 MotionMaker 편집기 없음 | #110 |
| t | T | motionMakerEditor | MotionMakerEditorCenterCurrentTime | — | 해당 없음 | Maya 2026 MotionMaker 편집기 없음 | #111 |
| p | P | motionMakerEditor | MotionMakerEditorPinSelectedCharacter | — | 해당 없음 | Maya 2026 MotionMaker 편집기 없음 | #112 |
| l | L | motionMakerEditor | MotionMakerEditorListAllCharacters | — | 해당 없음 | Maya 2026 MotionMaker 편집기 없음 | #113 |
| Alt+g | Alt+G | motionMakerEditor | MotionMakerEditorGenerateMotion | — | 해당 없음 | Maya 2026 MotionMaker 편집기 없음 | #114 |
| Alt+, | Alt+COMMA | motionMakerEditor | MotionMakerEditorGoToPreviousFrame | — | 해당 없음 | Maya 2026 MotionMaker 편집기 없음 | #115 |
| Alt+. | Alt+PERIOD | motionMakerEditor | MotionMakerEditorGoToNextFrame | — | 해당 없음 | Maya 2026 MotionMaker 편집기 없음 | #116 |
| , | COMMA | motionMakerEditor | MotionMakerEditorGoToPreviousTag | — | 해당 없음 | Maya 2026 MotionMaker 편집기 없음 | #117 |
| . | PERIOD | motionMakerEditor | MotionMakerEditorGoToNextTag | — | 해당 없음 | Maya 2026 MotionMaker 편집기 없음 | #118 |
| q | Q | timeEditorPanel | TimeEditorSceneAuthoringToggle | NLA Editor: `nla.select_box` (axis_range=False) | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #122 |
| w | W | timeEditorPanel | TimeEditorClipRazor | NLA Editor: `transform.transform` (mode='TRANSLATION') | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #123 |
| e | E | timeEditorPanel | TimeEditorClipTrimToggle | NLA Editor: `transform.transform` (mode='TIME_EXTEND') | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #124 |
| r | R | timeEditorPanel | TimeEditorClipScaleToggle | NLA Editor: `transform.transform` (mode='TIME_SCALE') | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #125 |
| t | T | timeEditorPanel | TimeEditorClipLoopToggle | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #126 |
| y | Y | timeEditorPanel | TimeEditorClipHoldToggle | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #127 |
| s | S | timeEditorPanel | TimeEditorSetKey | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #128 |
| d | D | timeEditorPanel | TimeEditorSetZeroKey | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #129 |
| m | M | timeEditorPanel | TimeEditorToggleMuteSelectedTracks | NLA Editor: `nla.mute_toggle`; NLA Editor: `marker.add` | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #131 |
| n | N | timeEditorPanel | TimeEditorToggleSoloSelectedTracks | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #132 |
| Alt+n | Alt+N | timeEditorPanel | TimeEditorAddToSoloSelectedTracks | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #133 |
| b | B | timeEditorPanel | TimeEditorGhostTrackToggle | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #134 |
| k | K | timeEditorPanel | TimeEditorToggleTimeCursorPress / TimeEditorToggleTimeCursorRelease (release) | Screen: `allset.tap_hold` (binding='time_drag') | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #136 |
| Ctrl+g | Ctrl+G | timeEditorPanel | TimeEditorCreateGroupFromSelection | NLA Editor: `nla.meta_add` | IC 일치 | NLA 메타 스트립 | #138 |
| Ctrl+Shift+G | Ctrl+Shift+G | timeEditorPanel | TimeEditorExplodeGroup | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #139 |
| Ctrl+e | Ctrl+E | timeEditorPanel | TimeEditorExportSelection | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #141 |
| Shift+I | Shift+I | timeEditorPanel | TimeEditorCreateAudioClip | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #142 |
| i | I | timeEditorPanel | TimeEditorImportAnimation | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #144 |
| o | O | timeEditorPanel | TimeEditorCreateClip | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #145 |
| p | P | timeEditorPanel | TimeEditorCreatePoseClip | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #146 |
| u | U | timeEditorPanel | TimeEditorRippleEditTogglePress / TimeEditorRippleEditToggleRelease (release) | NLA Editor: `nla.make_single_user` | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #147 |
| g | G | timeEditorPanel | TimeEditorClipTrimStart | Screen: `allset.repeat_last` | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #148 |
| h | H | timeEditorPanel | TimeEditorClipTrimEnd | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #149 |
| Shift+G | Shift+G | timeEditorPanel | TimeEditorClipScaleStart | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #150 |
| Shift+H | Shift+H | timeEditorPanel | TimeEditorClipScaleEnd | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #151 |
| l | L | timeEditorPanel | TimeEditorCreateAdditiveLayer | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #152 |
| Shift+L | Shift+L | timeEditorPanel | TimeEditorCreateOverrideLayer | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #153 |
| Ctrl+c | Ctrl+C | timeEditorPanel | TimeEditorCopyClips | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #156 |
| Ctrl+x | Ctrl+X | timeEditorPanel | TimeEditorCutClips | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #157 |
| Delete | DEL | timeEditorPanel | TimeEditorDeleteClips | NLA Editor: `nla.delete` | IC 일치 |  | #158 |
| Ctrl+v | Ctrl+V | timeEditorPanel | TimeEditorPasteClips | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #159 |
| a | A | timeEditorPanel | TimeEditorFrameAll | NLA Editor: `nla.view_all` | IC 일치 | Maya Time Editor = kit 의 NLA (step 34) | #164 |
| f | F | timeEditorPanel | TimeEditorFrameSelected | NLA Editor: `nla.view_selected` | IC 일치 |  | #165 |
| y | Y | timeEditorPanel | TimeEditorFrameCenterView | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #166 |
| x | X | timeEditorPanel | TimeEditorToggleSnapToClipPress / TimeEditorToggleSnapToClipRelease (release) | — | 해당 없음 | Maya Time Editor 클립 편집 (kit Time Editor = NLA, 그 키는 Blender 그대로) | #167 |
| a | A | dopeSheetPanel | DopeSheetFrameAll | Dopesheet: `action.view_all` | IC 일치 |  | #173 |
| f | F | dopeSheetPanel | DopeSheetFrameSelected | Dopesheet: `action.view_selected` | IC 일치 |  | #174 |
| g | G | dopeSheetPanel | DopeSheetFramePlaybackRange | Dopesheet: `allset.dope_sheet_key` (action='RANGE'); Screen: `allset.repeat_last` | 구현 | Timeline 에서는 통과 (g = Repeat Last) | #175 |
| t | T | dopeSheetPanel | DopeSheetCenterCurrentTime | Dopesheet: `allset.dope_sheet_key` (action='CENTER') | 구현 |  | #176 |
| h | H | dopeSheetPanel | DopeSheetLockChannel | Dopesheet: `allset.dope_sheet_key` (action='LOCK') | 구현 |  | #177 |
| j | J | dopeSheetPanel | DopeSheetUnlockChannel | Dopesheet: `allset.dope_sheet_key` (action='UNLOCK') | 구현 |  | #178 |
| a | A | graphEditor | GraphEditorFrameAll | Graph Editor: `graph.view_all` | IC 일치 |  | #182 |
| f | F | graphEditor | GraphEditorFrameSelected | Graph Editor: `graph.view_selected` | IC 일치 |  | #183 |
| g | G | graphEditor | GraphEditorFramePlaybackRange | Graph Editor: `anim.scene_range_frame`; Screen: `allset.repeat_last` | 구현 | 재생 범위 (preview 켜져 있으면 그 범위) 로 가로 맞춤 | #184 |
| t | T | graphEditor | GraphEditorFrameCenterView | Graph Editor: `allset.graph_center_time` | 구현 | 현재 시간을 가운데로 (가로만, 확대 그대로) | #185 |
| 1 | ONE | graphEditor | GraphEditorAbsoluteView | Graph Editor: `allset.graph_view_mode` (mode='ABSOLUTE') | 구현 | Normalize 끔 | #186 |
| 2 | TWO | graphEditor | GraphEditorStackedView | Graph Editor: `allset.graph_view_mode` (mode='STACKED') | 구현 | Blender 에 Stacked 없음: Normalized 로 + 안내 | #187 |
| 3 | THREE | graphEditor | GraphEditorNormalizedView | Graph Editor: `allset.graph_view_mode` (mode='NORMALIZED') | 구현 | Normalize 켬 (-1..1) | #188 |
| d | D | graphEditor | TangentAuto | Graph Editor: `allset.set_tangent` (kind='AUTO') | 구현 | 선택 키 = Bezier + Auto Clamped | #189 |
| h | H | graphEditor | GraphEditorLockChannel | Graph Editor: `anim.channels_setting_enable` (type='PROTECT') | 구현 | 선택 채널 잠금 | #190 |
| j | J | graphEditor | GraphEditorUnlockChannel | Graph Editor: `anim.channels_setting_disable` (type='PROTECT') | 구현 |  | #191 |
| l | L | graphEditor | GraphEditorValueLinesToggle | — | 해당 없음 | 0 / 최소 / 최대 값 기준선 표시 없음 | #192 |
| b | B | graphEditor | SculptKeysActivateEditRadius | Graph Editor: `wm.context_toggle` (data_path='tool_settings.use_proportional_fcurve') | 해당 없음 | 키 스컬프팅 브러시 없음 (Graph Editor Sculpting Tools) | #193 |
| b | B | graphEditor | — / SculptKeysDeactivateEditRadius (release) | Graph Editor: `wm.context_toggle` (data_path='tool_settings.use_proportional_fcurve') | 해당 없음 | 키 스컬프팅 브러시 없음 | #194 |
| m | M | graphEditor | SculptKeysActivateEditStrength | Graph Editor: `marker.add` | 해당 없음 | 키 스컬프팅 브러시 없음 | #195 |
| m | M | graphEditor | — / SculptKeysDeactivateEditStrength (release) | Graph Editor: `marker.add` | 해당 없음 | 키 스컬프팅 브러시 없음 | #196 |
| Ctrl+Left | Ctrl+LEFT_ARROW | graphEditor | RetimeMoveFrameBackward | Graph Editor: `screen.frame_jump` (end=False) | 해당 없음 | Retime Tool 없음 (Blender 는 G 로 키 이동) | #197 |
| Ctrl+Right | Ctrl+RIGHT_ARROW | graphEditor | RetimeMoveFrameForward | Graph Editor: `screen.frame_jump` (end=True) | 해당 없음 | Retime Tool 없음 | #198 |
| Cmd+Shift+A | Shift+Oskey+A | global | SelectAll | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #210 |
| Cmd+Shift+C | Shift+Oskey+C | global | CreateCameraFromView | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #211 |
| Cmd+d | Oskey+D | global | Duplicate | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #213 |
| Cmd+Shift+D | Shift+Oskey+D | global | DuplicateSpecial | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #214 |
| Cmd+z | Oskey+Z | global | Undo | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #216 |
| Cmd+Shift+Z | Shift+Oskey+Z | global | Redo | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #217 |
| Cmd+q | Oskey+Q | global | Quit | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #219 |
| Cmd+w | Oskey+W | global | CloseFrontWindow | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #221 |
| Cmd+i | Oskey+I | global | Import | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #223 |
| Home | HOME | global | EnterEditMode | 3D View: `allset.view_home` | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #225 |
| Cmd+o | Oskey+O | global | OpenScene | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #227 |
| Cmd+n | Oskey+N | global | NewScene | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #228 |
| Cmd+s | Oskey+S | global | SaveScene | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #229 |
| Cmd+Shift+S | Shift+Oskey+S | global | SaveSceneAs | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #230 |
| Alt+Cmd+s | Alt+Oskey+S | global | IncrementAndSave | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #231 |
| Cmd+r | Oskey+R | global | CreateReference | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #232 |
| Cmd+g | Oskey+G | global | Group | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #233 |
| Cmd+y | Oskey+Y | global | RepeatLast | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #235 |
| Cmd+Shift+I | Shift+Oskey+I | global | InvertSelection | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #237 |
| Cmd+Shift+? | Shift+Oskey+SLASH | global | Help | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #239 |
| Cmd+x | Oskey+X | global | CutSelected | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #242 |
| Cmd+c | Oskey+C | global | CopySelected | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #243 |
| Cmd+v | Oskey+V | global | PasteSelected | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #244 |
| Cmd+g | Oskey+G | timeEditorPanel | TimeEditorCreateGroupFromSelection | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #247 |
| Cmd+Shift+G | Shift+Oskey+G | timeEditorPanel | TimeEditorExplodeGroup | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #248 |
| Cmd+e | Oskey+E | timeEditorPanel | TimeEditorExportSelection | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #250 |
| Cmd+c | Oskey+C | timeEditorPanel | TimeEditorCopyClips | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #252 |
| Cmd+x | Oskey+X | timeEditorPanel | TimeEditorCutClips | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #253 |
| Cmd+v | Oskey+V | timeEditorPanel | TimeEditorPasteClips | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #254 |
| Ctrl+y | Ctrl+Y | global | Redo | Screen: `ed.redo` | 구현 |  | #264 |
| Insert | INSERT | global | EnterEditMode | Object Mode: `allset.pivot_toggle`; Mesh: `allset.pivot_toggle` | 구현 | 피벗 편집 토글: 오브젝트 모드 = Translate 불변 (step 59); 편집 모드 = 3D 커서 피벗 + 커서 툴, 면 클릭 방향 = Maya Pivot (step 77) | #266 |
| a | A | global | SelectAllMarkingMenu / SelectAllMarkingMenuPopDown (release) | 3D View: `allset.tap_hold` (binding='select_all') | 구현 | 탭=Frame All, 홀드+클릭=선택 메뉴 (마킹메뉴 엔진은 Step 9) | #269 |
| Shift+A | Shift+A | global | FrameAllInAllViews | 3D View: `allset.frame_all_views` (selected=False) | 구현 | 창의 모든 3D 뷰(쿼드 포함) | #270 |
| Ctrl+a | Ctrl+A | global | ShowAttributeEditorOrChannelBox | Object Mode: `allset.ae_toggle`; Mesh: `allset.ae_toggle` | 구현 | CB/LE ↔ AE 전환. 편집 / 포즈 / 페인트 마스크 / UV Editor 모드도 (IC Ctrl+A 전체 선택 제거, step 141 #65), Graph Editor / Dope Sheet / NLA / 채널 목록도 (step 150 #96) | #271 |
| f | F | global | FrameSelectedWithoutChildren | 3D View: `allset.frame` (selected=True) | 구현 | Maya 여백 0.95, 사이드바 밑 제외, 선택 없으면 전체 (step 17) | #272 |
| Shift+F | Shift+F | global | FrameSelectedWithoutChildrenInAllViews | 3D View: `allset.frame_all_views` (selected=True) | 구현 | 창의 모든 3D 뷰(쿼드 포함) | #273 |
| Ctrl+Shift+F | Ctrl+Shift+F | global | FrameSelectedInAllViews | 3D View: `allset.frame_all_views` (selected=True, children=True) | 구현 | 자식 포함, 창의 모든 3D 뷰 | #274 |
| [ | LEFT_BRACKET | global | UndoViewChange | 3D View: `allset.view_history` (direction='UNDO') | 구현 | 뷰 전용 스택 (씬 언두와 별개) | #275 |
| ] | RIGHT_BRACKET | global | RedoViewChange | 3D View: `allset.view_history` (direction='REDO') | 구현 |  | #276 |
| Alt+z | Alt+Z | global | UndoViewChange | 3D View: `allset.view_history` (direction='UNDO') | 구현 | 뷰 전용 스택 (씬 언두와 별개) | #277 |
| Alt+y | Alt+Y | global | RedoViewChange | 3D View: `allset.view_history` (direction='REDO') | 구현 |  | #278 |
| Home | HOME | global | GoToDefaultView | 3D View: `allset.view_home` | 구현 | Maya 새 씬 persp 자리 (정사영: 방향 유지, 원점) — step 27 | #279 |
| Shift+{ | Shift+LEFT_BRACKET | global | PreviousViewArrangement | Object Mode: `object.select_hierarchy` (direction='PARENT', extend=True) | 해당 없음 | 패널 배치 이력 없음; IC 계층 확장 선택 그대로 | #280 |
| Shift+} | Shift+RIGHT_BRACKET | global | NextViewArrangement | Object Mode: `object.select_hierarchy` (direction='CHILD', extend=True) | 해당 없음 | 패널 배치 이력 없음; IC 계층 확장 선택 그대로 | #281 |
| Alt+p | Alt+P | global | CameraModeToggle | 3D View: `allset.camera_mode_toggle` | 구현 | 사용자 뷰 = persp ↔ ortho, 카메라 뷰 = 그 카메라 타입 (화면 크기 유지) | #282 |
| Alt+Home | Alt+HOME | global | AppHome | — | 해당 없음 | Maya Home 화면 없음 | #284 |
| Shift+D | Shift+D | global | DuplicateWithTransform | Object Mode: `allset.duplicate_with_transform` | 구현 | 직전 복제의 변환을 반복 | #286 |
| Alt+Shift+D | Alt+Shift+D | global | DeleteHistory | Object Mode: `allset.delete_history` | 구현 | 모디파이어 + 셰이프 키를 메시에 굽기 | #288 |
| p | P | global | Parent | Object Mode: `allset.parent` | 구현 | 월드 유지, parent inverse 단위행렬 (환경설정 Parent Mode=Blender 로 IC 방식); 포즈·아마추어 편집 모드 = `allset.parent_joint` (조인트, 제자리) — step 57 | #290 |
| Shift+P | Shift+P | global | Unparent | Object Mode: `allset.unparent` | 구현 | 월드로, 월드 유지; 포즈·아마추어 편집 모드 = `allset.unparent_joint` (step 57) | #291 |
| F8 | F8 | global | SelectToggleMode | Object Non-modal: `allset.toggle_sel_mode` | 구현 | 오브젝트 ↔ 마지막 컴포넌트 모드 | #292 |
| F9 | F9 | global | SelectVertexMask | Object Non-modal: `allset.component_mode` (type='VERT') | 구현 |  | #294 |
| F10 | F10 | global | SelectEdgeMask | Object Non-modal: `allset.component_mode` (type='EDGE') | 구현 |  | #295 |
| F11 | F11 | global | SelectFacetMask | Object Non-modal: `allset.component_mode` (type='FACE') | 구현 |  | #296 |
| F12 | F12 | global | SelectUVMask | Object Mode: `allset.uv_component` (mode='UV'); Mesh: `allset.uv_component` (mode='UV'); Screen: `allset.render_blender` (use_viewport=True) | 구현 | UV Editor 를 열고 (편집 모드) UV 선택 = UV Sync 끔 + UV 정점 (step 66). 3D 뷰 오브젝트·메시 편집 밖의 F12 = Blender Render Image + Maya 기본 라이트 (allset.render_blender, step 214) | #297 |
| Alt+F9 | Alt+F9 | global | SelectVertexFaceMask | — | 해당 없음 | Blender 에 vertex-face 컴포넌트 없음 | #298 |
| Alt+F12 | Alt+F12 | global | SelectMeshUVShell | Object Mode: `allset.uv_component` (mode='SHELL'); Mesh: `allset.uv_component` (mode='SHELL') | 구현 | Maya UV Shell 마스크: 3D View / UV Editor 클릭·박스가 UV 셸 전체 (면) 를 고름 (step 256, operators/uv_shell_select.py) | #299 |
| F7 | F7 | global | SelectMultiComponentMask | Object Non-modal: `allset.component_mode` (type='MULTI') | 구현 | 정점·엣지·면 동시 선택 모드 | #300 |
| Ctrl+F9 | Ctrl+F9 | global | ConvertSelectionToVertices | Mesh: `allset.convert_selection` (type='VERT') | 구현 |  | #303 |
| Ctrl+F10 | Ctrl+F10 | global | ConvertSelectionToEdges | Mesh: `allset.convert_selection` (type='EDGE') | 구현 | 닿는 엣지 (면 -> 테두리 엣지) | #304 |
| Ctrl+F11 | Ctrl+F11 | global | ConvertSelectionToFaces | Mesh: `allset.convert_selection` (type='FACE') | 구현 | 닿는 면 (Blender 모드 전환은 포함된 면만) | #305 |
| Ctrl+F12 | Ctrl+F12 | global | ConvertSelectionToUVs | Screen: `allset.render_blender` (animation=True, use_viewport=True) | 해당 없음 | 3D 뷰 UV 컴포넌트 없음 (UV Editor 사용). Ctrl+F12 = Blender Render Animation + Maya 기본 라이트 (allset.render_blender, step 214) | #306 |
| Shift+> | Shift+PERIOD | global | GrowPolygonSelectionRegion | Mesh: `mesh.select_more` | 구현 |  | #307 |
| Ctrl+Shift+> | Ctrl+Shift+PERIOD | global | GrowLoopPolygonSelectionRegion | Mesh: `mesh.select_next_item` | 구현 | 선택 순서 따라 한 칸 (루프 확장 근사) | #308 |
| Shift+< | Shift+COMMA | global | ShrinkPolygonSelectionRegion | Mesh: `mesh.select_less` | 구현 |  | #309 |
| Ctrl+Shift+< | Ctrl+Shift+COMMA | global | ShrinkLoopPolygonSelectionRegion | Mesh: `mesh.select_prev_item` | 구현 | 선택 순서 따라 한 칸 되돌림 (근사) | #310 |
| h | H | global | ToggleVisibilityAndKeepSelection | Object Mode: `allset.visibility` (action='TOGGLE') | 구현 | 숨긴 객체를 '선택 유지' 표시로 기억, 다시 h = 보이고 선택 (오브젝트 모드) | #312 |
| x | X | global | SnapToGridPress / SnapToGridRelease (release) | 3D View: `allset.hold` (name='grid') | 구현 | 누르는 동안 GRID 스냅 (절대 그리드 선, 매니퓰레이터 중심), 놓으면 복원 — step 59 | #313 |
| Shift+X | Shift+X | global | SnapToGridPress / SnapToGridRelease (release) | 3D View: `allset.hold` (name='grid') | 구현 | 누르는 동안 GRID 스냅 (절대 그리드 선, 매니퓰레이터 중심), 놓으면 복원 — step 59 | #314 |
| Ctrl+h | Ctrl+H | global | HideSelectedObjects | Object Mode: `allset.visibility` (action='HIDE'); Mesh: `mesh.hide` (unselected=False) | 구현 | 컴포넌트: Mesh mesh.hide (IC) | #315 |
| Shift+H | Shift+H | global | ShowSelectedObjects | Object Mode: `allset.visibility` (action='SHOW_SELECTED'); Mesh: `mesh.reveal` | 구현 | h 로 숨긴 선택 + 숨겨진 활성 객체; 컴포넌트: mesh.reveal | #316 |
| Ctrl+Shift+H | Ctrl+Shift+H | global | ShowLastHidden | Object Mode: `allset.visibility` (action='SHOW_LAST'); Mesh: `mesh.reveal` | 구현 | 킷 숨김 동작(h/Ctrl+H/Alt+H)의 마지막 대상; 컴포넌트: mesh.reveal | #317 |
| Alt+h | Alt+H | global | HideUnselectedObjects | Object Mode: `allset.visibility` (action='HIDE_UNSELECTED'); Mesh: `mesh.hide` (unselected=True) | 구현 | 컴포넌트: mesh.hide(unselected) | #318 |
| Ctrl+Alt+h | Ctrl+Alt+H | global | ShowAllPolyComponents | Mesh: `mesh.reveal` | 구현 |  | #319 |
| c | C | global | SnapToCurvePress / SnapToCurveRelease (release) | 3D View: `allset.hold` (name='curve') | 구현 | 누르는 동안 EDGE 스냅 (커브 전용 없음, 근사) | #320 |
| Shift+C | Shift+C | global | SnapToCurvePress / SnapToCurveRelease (release) | 3D View: `allset.hold` (name='curve') | 구현 | 누르는 동안 EDGE 스냅 (커브 전용 없음, 근사) | #321 |
| v | V | global | SnapToPointPress / SnapToPointRelease (release) | 3D View: `allset.hold` (name='point') | 구현 | 누르는 동안 VERTEX 스냅 (매니퓰레이터 중심이 정점에) — step 59 | #322 |
| Shift+V | Shift+V | global | SnapToPointPress / SnapToPointRelease (release) | 3D View: `allset.hold` (name='point') | 구현 | 누르는 동안 VERTEX 스냅 (매니퓰레이터 중심이 정점에) — step 59 | #323 |
| q | Q | global | SelectToolOptionsMarkingMenu / SelectToolOptionsMarkingMenuPopDown (release) | Object Mode: `allset.tap_hold` (binding='tool_select'); Mesh: `allset.tap_hold` (binding='tool_select') | 구현 | 누름=툴 전환, 누른 채 LMB=Select 옵션 마킹메뉴(파이, Step 8) | #326 |
| Shift+Q | Shift+Q | global | SelectComponentToolMarkingMenu / SelectComponentToolMarkingMenuPopDown (release) | Object Mode: `allset.tap_hold` (binding='select_component'); Mesh: `allset.tap_hold` (binding='select_component') | 구현 | 탭 = 선택 툴 + 컴포넌트 모드, 홀드 + LMB = 픽 마스크 마킹 메뉴 (메시 정점/엣지/면만) | #327 |
| Alt+q | Alt+Q | global | SelectPolygonToolMarkingMenu / SelectPolygonToolMarkingMenuPopDown (release) | Object Mode: `allset.tap_hold` (binding='select_polygon'); Mesh: `allset.tap_hold` (binding='select_polygon') | 구현 | 탭 = 선택 툴, 홀드 + LMB = Vertices / Edges / Faces / UVs | #328 |
| Alt+m | Alt+M | global | FullHotboxDisplay | — | 해당 없음 | kit 핫박스는 늘 모든 행을 보여 줌 | #329 |
| Ctrl+m | Ctrl+M | global | ToggleMainMenubar | Screen: `allset.main_menubar_toggle` | 구현 | 메인 메뉴 막대를 위 막대의 메뉴 버튼으로 접기/펴기 | #330 |
| Shift+M | Shift+M | global | TogglePanelMenubar | Screen: `wm.context_toggle` (data_path='area.show_menus') | 구현 | 마우스 아래 편집기의 메뉴 접기/펴기 | #331 |
| Ctrl+Shift+M | Ctrl+Shift+M | global | ToggleModelEditorBars | 3D View: `wm.context_toggle` (data_path='space_data.show_region_header') | 구현 | 3D 뷰 머리 (메뉴 + 아이콘 줄) 숨김/보임 | #332 |
| Shift+J | Shift+J | global | MoveRotateScaleToolToggleSnapRelativeMode / MoveRotateScaleToolToggleSnapRelativeMode (release) | 3D View: `allset.hold` (name='step') | 구현 | J 와 동일 (INCREMENT 는 상대 증분) | #335 |
| j | J | global | MoveRotateScaleToolToggleSnapMode / MoveRotateScaleToolToggleSnapMode (release) | 3D View: `allset.hold` (name='step') | 구현 | 누르는 동안 INCREMENT 스냅 | #336 |
| Cmd+F9 | Oskey+F9 | global | ConvertSelectionToVertices | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #339 |
| Cmd+F10 | Oskey+F10 | global | ConvertSelectionToEdges | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #340 |
| Cmd+F11 | Oskey+F11 | global | ConvertSelectionToFaces | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #341 |
| Cmd+F12 | Oskey+F12 | global | ConvertSelectionToUVs | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #342 |
| Cmd+Shift+H | Shift+Oskey+H | global | ShowLastHidden | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #344 |
| w | W | global | TranslateToolWithSnapMarkingMenu / TranslateToolWithSnapMarkingMenuPopDown (release) | Object Mode: `allset.tap_hold` (binding='tool_move'); Mesh: `allset.tap_hold` (binding='tool_move') | 구현 | 누름=툴 전환, 누른 채 LMB=Move 옵션 마킹메뉴(파이, Step 8) | #348 |
| e | E | global | RotateToolWithSnapMarkingMenu / RotateToolWithSnapMarkingMenuPopDown (release) | Object Mode: `allset.tap_hold` (binding='tool_rotate'); Mesh: `allset.tap_hold` (binding='tool_rotate') | 구현 | 누름=툴 전환, 누른 채 LMB=Rotate 옵션 마킹메뉴(파이, Step 8) | #350 |
| r | R | global | ScaleToolWithSnapMarkingMenu / ScaleToolWithSnapMarkingMenuPopDown (release) | Object Mode: `allset.tap_hold` (binding='tool_scale'); Mesh: `allset.tap_hold` (binding='tool_scale') | 구현 | 누름=툴 전환, 누른 채 LMB=Scale 옵션 마킹메뉴(파이, Step 8) | #352 |
| Ctrl+t | Ctrl+T | global | UniversalManip | Object Mode: `wm.tool_set_by_id` (name='builtin.transform'); Mesh: `wm.tool_set_by_id` (name='builtin.transform') | 구현 |  | #354 |
| t | T | global | ShowManipulators | Object Mode: `wm.tool_set_by_id` (name='builtin.transform', cycle=True); Mesh: `wm.tool_set_by_id` (name='builtin.transform', cycle=True) | IC 일치 | Blender 에 Show Manipulator 툴 없음: Transform 툴 | #356 |
| y | Y | global | NonSacredTool | Object Mode: `allset.last_tool`; Mesh: `allset.last_tool` | 구현 | Q/W/E/R/T 가 아닌 마지막 툴 (모드별 기억) | #357 |
| Ctrl+Shift+Q | Ctrl+Shift+Q | global | QuadDrawToolNameCommand | Object Mode: `allset.quad_draw_start`; Mesh: `allset.quad_draw_start` | 구현 | kit Quad Draw 툴 (step 144): 선택한 메시 / 새 polySurfaceN 편집, 라이브 표면 위 점, Shift+클릭 채우기, Ctrl+클릭 루프, Ctrl+Shift+클릭 지우기, Tab+드래그 연장 | #360 |
| Ctrl+Shift+X | Ctrl+Shift+X | global | MultiCutToolNameCommand | Object Mode: `allset.menu_tool` (tool='allset.multi_cut_tool', edit=True); Mesh: `allset.menu_tool` (tool='allset.multi_cut_tool', edit=True) | 구현 | kit Multi-Cut 툴 (step 129), 오브젝트 모드면 편집 모드로; 툴 안 Ctrl+클릭 = 엣지 루프 (Ctrl+MMB 가운데), Shift = Snap Step %, Backspace, Enter/RMB 완료 | #361 |
| F2 | F2 | global | ShowModelingUI | Screen: `allset.menu_set` (set='modelingMenuSet') | 구현 | 메뉴 세트 전환 (IC 3D 뷰 F2–F5 뷰 키 대신; 직교 뷰는 핫박스·Space·Ctrl+F1–F3) | #363 |
| F3 | F3 | global | ShowRiggingUI | Screen: `allset.menu_set` (set='riggingMenuSet') | 구현 | 메뉴 세트 전환 (IC 3D 뷰 F2–F5 뷰 키 대신; 직교 뷰는 핫박스·Space·Ctrl+F1–F3) | #364 |
| F4 | F4 | global | ShowAnimationUI | Screen: `allset.menu_set` (set='animationMenuSet') | 구현 | 메뉴 세트 전환 (IC 3D 뷰 F2–F5 뷰 키 대신; 직교 뷰는 핫박스·Space·Ctrl+F1–F3) | #365 |
| F5 | F5 | global | ShowDynamicsUI | Screen: `allset.menu_set` (set='dynamicsMenuSet') | 구현 | 메뉴 세트 전환 (IC 3D 뷰 F2–F5 뷰 키 대신; 직교 뷰는 핫박스·Space·Ctrl+F1–F3) | #367 |
| F6 | F6 | global | ShowRenderingUI | Screen: `allset.menu_set` (set='renderingMenuSet') | 구현 | 메뉴 세트 전환 (IC 3D 뷰 F2–F5 뷰 키 대신; 직교 뷰는 핫박스·Space·Ctrl+F1–F3) | #368 |
| s | S | global | SetKey | Object Mode: `allset.set_key` | 구현 | 키 가능한 모든 채널 (가시성·커스텀 포함, Hide/Nonkeyable 제외), 포즈 모드 = 선택 본; 활성 Keying Set 이 있으면 그것 (step 56) | #369 |
| Alt+e | Alt+E | global | HIKPinRotate | Object Mode: `object.rotation_clear` (clear_delta=False) | 해당 없음 | HumanIK 없음 | #370 |
| Alt+w | Alt+W | global | HIKPinTranslate | Object Mode: `object.location_clear` (clear_delta=False) | 해당 없음 | HumanIK 없음 | #371 |
| Alt+s | Alt+S | global | HIKSetFullBodyKey | Object Mode: `anim.keyframe_delete_v3d` | 해당 없음 | HumanIK 없음 | #372 |
| Alt+v | Alt+V | global | PlaybackToggle | Frames: `screen.animation_play` | 구현 |  | #373 |
| Alt+Shift+V | Alt+Shift+V | global | GoToMinFrame | Frames: `screen.frame_jump` (end=False) | 구현 |  | #374 |
| k | K | global | TimeDraggerToolActivate / TimeDraggerToolDeactivate (release) | Screen: `allset.tap_hold` (binding='time_drag') | 구현 | K 누른 채 LMB 드래그 = 시간 (어느 에디터든), 선택 그대로; Mesh knife K → Multi-Cut 은 Ctrl+Shift+X (step 56) | #375 |
| i | I | global | InsertKeyToolActivate / InsertKeyToolDeactivate (release) | Mesh: `wm.tool_set_by_id` (name='builtin.inset_faces', cycle=True) | 구현 | Graph Editor 에서 누르는 동안 MMB 클릭 / 드래그 = 선택 곡선에 모양 그대로 키 (정수 프레임); 전역 I = Mesh inset 그대로 | #376 |
| 0 | ZERO | global | DefaultQualityDisplay | Object Mode: `allset.smooth_preview` (level=1); Mesh: `allset.smooth_preview` (level=1) | 구현 | 1 과 같음 (거친 표시) — step 27 | #377 |
| 1 | ONE | global | LowQualityDisplay | Object Mode: `allset.smooth_preview` (level=1); Mesh: `allset.smooth_preview` (level=1) | 구현 | Subsurf 뷰포트 끔 | #378 |
| 2 | TWO | global | MediumQualityDisplay | Object Mode: `allset.smooth_preview` (level=2); Mesh: `allset.smooth_preview` (level=2) | 구현 | Subsurf + 와이어 (케이지 근사) | #379 |
| 3 | THREE | global | HighQualityDisplay | Object Mode: `allset.smooth_preview` (level=3); Mesh: `allset.smooth_preview` (level=3) | 구현 | Subsurf 뷰포트 켬 (없으면 추가, 렌더 영향 없음) | #380 |
| Alt+3 | Alt+THREE | global | ToggleDisplacement | — | 해당 없음 | 디스플레이스먼트 미리보기 토글 없음 (모디파이어) | #381 |
| 4 | FOUR | global | DisplayWireframe | 3D View: `allset.display_mode` (mode='WIREFRAME') | 구현 |  | #382 |
| 5 | FIVE | global | DisplayShaded | 3D View: `allset.display_mode` (mode='SHADED') | 구현 |  | #383 |
| 6 | SIX | global | DisplayShadedAndTextured | 3D View: `allset.display_mode` (mode='TEXTURED') | 구현 |  | #384 |
| 7 | SEVEN | global | DisplayLight | 3D View: `allset.display_mode` (mode='LIGHTS') | 구현 | Material Preview + 씬 라이트 (근사) | #385 |
| Ctrl+Shift+% | Ctrl+Shift+FIVE | global | ToggleUseDefaultMaterial | 3D View: `allset.panel_set` (key='DEFAULT_MATERIAL') | 구현 | Shading > Use Default Material 과 같음 | #386 |
| Ctrl+1 | Ctrl+ONE | global | ToggleIsolateSelect | 3D View: `allset.isolate` | 구현 | 로컬 뷰 (카메라 그대로, 선택의 자손 포함 — step 164), 다시 누르면 해제 | #387 |
| Alt+a | Alt+A | global | CycleDisplayMode | 3D View: `allset.cycle_display` | 구현 | X-ray 조인트 (아마추어 In Front) → 전부 → 메시만 (조인트·커브 숨김) 순환 | #388 |
| Shift+I | Shift+I | global | SelectIsolate | 3D View: `view3d.localview` | IC 일치 | 로컬 뷰 토글 (프레이밍 포함) | #392 |
| Space | SPACE | global | ShowHotbox / HideHotbox (release) | 3D View: `allset.hotbox` | 구현 | 홀드=핫박스(메뉴 행·존 마킹메뉴), 탭=4분할↔단일 / 패널 최대화. 재생은 Alt+V | #393 |
| Return | RET | global | CompleteCurrentTool | Screen: `file.execute` | 해당 없음 | Blender 모달 툴은 자기 키맵의 Return 으로 확정; 3D 뷰의 IC 이름 바꾸기 팝오버는 제거 | #394 |
| Esc | ESC | global | AbortCurrentTool | Frames: `screen.animation_cancel`; Screen: `file.cancel`; Screen: `render.view_cancel` | 해당 없음 | Blender 모달 도구는 Esc 로 스스로 취소 | #395 |
| d | D | global | EnterEditModePress / EnterEditModeRelease (release) | Object Mode: `allset.hold` (name='pivot'); Mesh: `allset.hold` (name='component_pivot') | 구현 | 오브젝트 모드: 누르는 동안 피벗 편집 (Translate 불변, 자식 제자리, step 59); 편집 모드: 3D 커서 피벗 배치 (step 18), 피벗 방향 = Maya Pivot (step 77) | #396 |
| Ctrl+Alt+, | Ctrl+Alt+COMMA | global | SelectPreviousKey | Screen: `allset.select_key` (direction='PREVIOUS') | 구현 |  | #397 |
| Ctrl+Alt+. | Ctrl+Alt+PERIOD | global | SelectNextKey | Screen: `allset.select_key` (direction='NEXT') | 구현 | 선택 키 (없으면 현재 시간) 다음 키로 가서 그 키만 선택 | #398 |
| , | COMMA | global | PreviousKey | Frames: `screen.keyframe_jump` (next=False) | 구현 | 3D View 방향 파이는 헤더로 | #399 |
| Alt+, | Alt+COMMA | global | PreviousFrame | Frames: `screen.frame_offset` (delta=-1) | 구현 |  | #400 |
| . | PERIOD | global | NextKey | Frames: `screen.keyframe_jump` (next=True) | 구현 | Frames 키맵 (대부분 에디터); 3D View 피벗 파이는 헤더로 | #401 |
| Alt+. | Alt+PERIOD | global | NextFrame | Frames: `screen.frame_offset` (delta=1) | 구현 | 누르고 있으면 반복 | #402 |
| g | G | global | RepeatLast | Screen: `allset.repeat_last` | 구현 | 메뉴 · 셸프 · 마킹 명령도 반복 (Blender repeat_last 는 등록된 연산자만) | #403 |
| Shift+G | Shift+G | global | RepeatLastActionAtMousePosition | 3D View: `allset.repeat_at_mouse` | 구현 | 마지막 동작 반복 → 선택을 마우스 아래 바닥 (Z=0) 으로 | #404 |
| Up | UP_ARROW | global | PickWalkUp | Object Mode: `allset.pick_walk` (direction='UP'); Mesh: `allset.pick_walk_component` (direction='UP') | 구현 | 편집 모드: 엣지 = 링, 정점·면 = 화면 위쪽 이웃 (step 39); 포즈 모드: 부모 조인트 (step 57) | #405 |
| Down | DOWN_ARROW | global | PickWalkDown | Object Mode: `allset.pick_walk` (direction='DOWN'); Mesh: `allset.pick_walk_component` (direction='DOWN') | 구현 | 편집 모드: 엣지 = 링, 정점·면 = 화면 아래쪽 이웃 (step 39); 포즈 모드: 첫 자식 조인트 (step 57) | #406 |
| Left | LEFT_ARROW | global | PickWalkLeft | Object Mode: `allset.pick_walk` (direction='LEFT'); Mesh: `allset.pick_walk_component` (direction='LEFT') | 구현 | 이름순 형제 순환; 편집 모드: 엣지 = 루프, 정점·면 = 화면 왼쪽 이웃 (step 39); 포즈 모드: 형제 조인트 | #407 |
| Right | RIGHT_ARROW | global | PickWalkRight | Object Mode: `allset.pick_walk` (direction='RIGHT'); Mesh: `allset.pick_walk_component` (direction='RIGHT') | 구현 | 이름순 형제 순환; 편집 모드: 엣지 = 루프, 정점·면 = 화면 오른쪽 이웃 (step 39); 포즈 모드: 형제 조인트 | #408 |
| Ctrl+Page_Up | Ctrl+PAGE_UP | global | PickWalkIn | Object Mode: `object.select_hierarchy` (direction='CHILD', extend=False) | 구현 | 자식으로 (포즈: 자식 본); IC 작업공간 순환 제거 | #409 |
| Ctrl+Page_Down | Ctrl+PAGE_DOWN | global | PickWalkOut | Object Mode: `object.select_hierarchy` (direction='PARENT', extend=False) | 구현 | 부모로 | #410 |
| Alt+Up | Alt+UP_ARROW | global | MoveUp | 3D View: `allset.pixel_move` (dx=0, dy=1) | 구현 | 선택을 화면 1 px (뷰 평면), UV 에디터 넛지 없음 | #411 |
| Alt+Down | Alt+DOWN_ARROW | global | MoveDown | 3D View: `allset.pixel_move` (dx=0, dy=-1) | 구현 |  | #412 |
| Alt+Left | Alt+LEFT_ARROW | global | MoveLeft | 3D View: `allset.pixel_move` (dx=-1, dy=0) | 구현 |  | #413 |
| Alt+Right | Alt+RIGHT_ARROW | global | MoveRight | 3D View: `allset.pixel_move` (dx=1, dy=0) | 구현 |  | #414 |
| Ctrl+Backspace | Ctrl+BACK_SPACE | global | DeletePolyElements | Mesh: `mesh.dissolve_mode` | IC 일치 | 엣지·정점 dissolve (Delete Edge/Vertex); Delete/Backspace = 바로 삭제 (step 24) | #416 |
| Ctrl+Delete | Ctrl+DEL | global | DeletePolyElements | Mesh: `mesh.dissolve_mode` | IC 일치 | 엣지·정점 dissolve (Delete Edge/Vertex); Delete/Backspace = 바로 삭제 (step 24) | #417 |
| Ctrl+Alt+Left | Ctrl+Alt+LEFT_ARROW | global | PolySpinEdgeBackward | Mesh: `mesh.edge_rotate` (use_ccw=True) | 구현 | Edit Mesh > Spin Edge Backward 와 같음 | #419 |
| Ctrl+Alt+Right | Ctrl+Alt+RIGHT_ARROW | global | PolySpinEdgeForward | Mesh: `mesh.edge_rotate` (use_ccw=False) | 구현 | Edit Mesh > Spin Edge Forward 와 같음 | #420 |
| Ctrl+e | Ctrl+E | global | PolyExtrude | Mesh: `allset.extrude` | 구현 | polyExtrudeFace: 길이 0 압출 + 매니퓰레이터·In-View Editor·INPUTS (step 65); 엣지/정점은 압출 + 법선 드래그 | #422 |
| Ctrl+b | Ctrl+B | global | BevelPolygon | Mesh: `allset.bevel` | 구현 | 정점 모드 = 정점 베벨, 그 외 엣지; 드래그로 폭 | #423 |
| - | MINUS | global | DecreaseManipulatorSize | 3D View: `allset.manip_size` (factor=0.8) | 구현 |  | #425 |
| = | EQUAL | global | IncreaseManipulatorSize | 3D View: `allset.manip_size` (factor=1.25) | 구현 | gizmo_size ×1.25 (Maya ×2), 끄면 원래 값 — step 27 | #426 |
| Shift++ | Shift+EQUAL | global | IncreaseManipulatorSize | 3D View: `allset.manip_size` (factor=1.25) | 구현 | gizmo_size ×1.25 (Maya ×2), 끄면 원래 값 — step 27 | #427 |
| Alt+Shift+Y | Alt+Shift+Y | global | — | — | 해당 없음 | Maya 가 일부러 비워 둔 바인딩 (Alt+Y) | #429 |
| Ctrl+Shift+Y | Ctrl+Shift+Y | global | — | — | 해당 없음 | Maya 가 일부러 비워 둔 바인딩 (Ctrl+Y) | #430 |
| Ctrl+Alt+Shift+Y | Ctrl+Alt+Shift+Y | global | — | — | 해당 없음 | Maya 가 일부러 비워 둔 바인딩 (Ctrl+Alt+Y) | #431 |
| Shift+W | Shift+W | global | SetKeyTranslate | Object Mode: `allset.set_key` (channels='TRANSLATE') | 구현 | Translate X / Y / Z 만 키, 보고 문구 없음 (IC keying set 보고 대신, step 151 #100) | #432 |
| Shift+E | Shift+E | global | SetKeyRotate | Object Mode: `allset.set_key` (channels='ROTATE') | 구현 | Rotate X / Y / Z 만 키 (step 151 #100) | #433 |
| Shift+R | Shift+R | global | SetKeyScale | Object Mode: `allset.set_key` (channels='SCALE') | 구현 | Scale X / Y / Z 만 키 (step 151 #100) | #434 |
| Ctrl+i | Ctrl+I | global | SelectNextIntermediatObject | — | 해당 없음 | Blender 에 intermediate object 없음; 3D 모드의 IC Ctrl+I 반전은 제거 (반전은 Maya 처럼 Ctrl+Shift+I) | #436 |
| F1 | F1 | global | Help | Window: `wm.doc_view_manual_ui_context` | 구현 | 마우스 아래 버튼의 Blender 설명서; IC 3D View 앞 뷰 / Image 1:1 제거 | #438 |
| Cmd+Shift+X | Shift+Oskey+X | global | MultiCutToolNameCommand | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #441 |
| Cmd+1 | Oskey+ONE | global | ToggleIsolateSelect | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #443 |
| Cmd+Backspace | Oskey+BACK_SPACE | global | DeletePolyElements | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #445 |
| Cmd+Delete | Oskey+DEL | global | DeletePolyElements | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #446 |
| Alt+Cmd+Left | Alt+Oskey+LEFT_ARROW | global | PolySpinEdgeBackward | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #448 |
| Alt+Cmd+Right | Alt+Oskey+RIGHT_ARROW | global | PolySpinEdgeForward | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #449 |
| Cmd+e | Oskey+E | global | PolyExtrude | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #451 |
| Shift+S | Shift+S | global | KeyframeTangentMarkingMenu / KeyframeTangentMarkingMenuPopDown (release) | Object Mode: `allset.tap_hold` (binding='key_tangent') | 구현 | 홀드 + LMB = Keys / Tangents 마킹 메뉴 (Graph Editor·Dope Sheet·포즈도), 탭 = 없음 | #456 |
| n | N | global | TraversalMarkingMenu / TraversalMarkingMenuPopDown (release) | — | 해당 없음 | 순회 마킹 메뉴 없음 (화살표 픽워크 사용) | #462 |
| b | B | bpDraw | BluePencilActivateBrushSize / BluePencilDeactivateBrushSize (release) | — | 해당 없음 | Maya Blue Pencil 브러시 (Blender Grease Pencil 은 F) | #466 |
| m | M | bpDraw | BluePencilActivateOpacity / BluePencilDeactivateOpacity (release) | — | 해당 없음 | Maya Blue Pencil 브러시 | #467 |
| Alt+Shift+< | Alt+Shift+COMMA | global | PreviousBluePencilFrame | — | 해당 없음 | Maya Blue Pencil 프레임 (Blender Grease Pencil 키는 그 모드에서) | #468 |
| Alt+Shift+> | Alt+Shift+PERIOD | global | NextBluePencilFrame | — | 해당 없음 | Maya Blue Pencil 프레임 | #469 |
| u | U | global | PaintOperationMarkingMenuPress / PaintOperationMarkingMenuRelease (release) | — | 구현 | Replace / Add / Scale / Smooth 메뉴 (누르면 열림, 드래그 아님) | #472 |
| b | B | global | ModifyUpperRadiusPress / ModifyUpperRadiusRelease (release) | 3D View: `allset.tap_hold` (binding='soft_select') | 구현 | 탭=소프트 셀렉트 토글, 홀드+LMB 드래그=반경 | #475 |
| Shift+B | Shift+B | global | ModifyLowerRadiusPress / ModifyLowerRadiusRelease (release) | — | 해당 없음 | Blender 브러시는 반지름이 하나 (압력 최소 크기는 브러시 설정); Shift+B 는 안내만 | #478 |
| / | SLASH | global | PickColorActivate / PickColorDeactivate (release) | — | 해당 없음 | Artisan 색 스포이트 없음 (가중치 샘플 I) | #481 |
| n | N | global | ModifyPaintValuePress / ModifyPaintValueRelease (release) | — | 구현 | 가중치 값 드래그 | #484 |
| Shift+U | Shift+U | global | ModifyUVVectorPress / ModifyUVVectorRelease (release) | — | 해당 없음 | Artisan UV 벡터 없음 | #487 |
| Alt+f | Alt+F | global | FloodSurfaces | — | 구현 | Maya Flood: 연산 × Opacity, 나머지 영향에 기존 비율로 재분배, 잠금 존중, 선택 정점만 (step 218) | #490 |
| Alt+c | Alt+C | global | ToggleColorFeedback | — | 구현 | 스킨 페인트 가중치 색 켬/끔; IC Mesh 의 루프 컷 도구 제거 | #491 |
| Alt+j | Alt+J | global | ToggleMultiColorFeedback | — | 해당 없음 | 다중 색 피드백 없음 | #492 |
| Ctrl+Alt+c | Ctrl+Alt+C | global | CopyVertexSkinWeights | Mesh: `allset.copy_vertex_weights` | 구현 | 편집 모드 활성 버텍스 (step 58); 가중치 페인트에서도 같은 키 (활성 / 첫 선택 정점, step 218) | #493 |
| Ctrl+Alt+v | Ctrl+Alt+V | global | PasteVertexSkinWeights | Mesh: `allset.paste_vertex_weights` | 구현 | 선택 정점에; 가중치 페인트에서도 같은 키 (step 218) | #494 |
| Ctrl+. | Ctrl+PERIOD | global | NextSkinPaintMode | — | 구현 | Paint → Select → Paint Select 순환 (Paint Select = 원 선택 도구, step 218) | #495 |
| Ctrl+, | Ctrl+COMMA | global | PrevSkinPaintMode | — | 구현 | Paint → Paint Select → Select 순환 (Select = 박스 선택 도구 + 정점 마스크, step 218); IC Ctrl+, 환경설정 제거 | #496 |
| o | O | global | PolyBrushMarkingMenu / PolyBrushMarkingMenuPopDown (release) | — | 해당 없음 | Poly Brush 없음 | #497 |
| m | M | global | ModifyDisplacementPress / ModifyDisplacementRelease (release) | — | 구현 | 조각: 세기 드래그; 3D 모드의 IC Measure 도구 제거 | #502 |
| Return | RET | outlinerPanel | OutlinerRenameSelectedItem | Outliner: `outliner.item_rename` (use_active=True); Screen: `file.execute` | IC 일치 | 활성 행 이름 바꾸기 | #506 |
| f | F | outlinerPanel | OutlinerRevealSelected | Outliner: `outliner.show_active` | IC 일치 | 선택 항목까지 펼치고 보이기 | #507 |
| Ctrl+Left | Ctrl+LEFT_ARROW | renderWindowPanel | RenderViewPrevImage | — | 해당 없음 | 렌더 슬롯 J / Alt+J (step 97); Maya 2026 은 Render View 키 | #510 |
| Ctrl+Right | Ctrl+RIGHT_ARROW | renderWindowPanel | RenderViewNextImage | — | 해당 없음 | Render View 이미지 = Image 편집기 렌더 슬롯 J / Alt+J (step 97); Maya 2026 은 Render View 키 | #511 |
| 1 | ONE | nodeEditorPanel | NodeEditorHideAttributes | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #514 |
| 2 | TWO | nodeEditorPanel | NodeEditorShowConnectedAttrs | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #515 |
| 3 | THREE | nodeEditorPanel | NodeEditorShowAllAttrs | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #516 |
| 4 | FOUR | nodeEditorPanel | NodeEditorShowCustomAttrs | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #517 |
| 5 | FIVE | nodeEditorPanel | NodeEditorToggleNodeTitleMode | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #518 |
| p | P | nodeEditorPanel | NodeEditorToggleNodeSelectedPins | Node Editor: `node.parent_set` | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #519 |
| v | V | nodeEditorPanel | NodeEditorToggleNodeSwatchSize | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #520 |
| = | EQUAL | nodeEditorPanel | NodeEditorToggleZoomIn | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #521 |
| - | MINUS | nodeEditorPanel | NodeEditorToggleZoomOut | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #522 |
| Shift+C | Shift+C | nodeEditorPanel | NodeEditorToggleSyncedSelection | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #523 |
| s | S | nodeEditorPanel | NodeEditorToggleAttrFilter | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #524 |
| x | X | nodeEditorPanel | NodeEditorGridToggleSnap / NodeEditorGridToggleSnap (release) | Node Editor: `wm.context_toggle` (data_path='tool_settings.use_snap_node') | IC 일치 |  | #525 |
| l | L | nodeEditorPanel | NodeEditorLayout | Node Editor: `node.link_make` (replace=False) | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #526 |
| / | SLASH | nodeEditorPanel | NodeEditorSelectConnected | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #527 |
| , | COMMA | nodeEditorPanel | NodeEditorSelectUpStream | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #528 |
| w | W | nodeEditorPanel | NodeEditorConnectNodeOnCreation | Node Editor: `node.translate_attach`; Node Editor: `transform.translate` | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #529 |
| c | C | nodeEditorPanel | NodeEditorConnectSelectedNodes | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #530 |
| . | PERIOD | nodeEditorPanel | NodeEditorSelectDownStream | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #531 |
| Shift+? | Shift+SLASH | nodeEditorPanel | NodeEditorGraphUpDownstream | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #532 |
| Shift+< | Shift+COMMA | nodeEditorPanel | NodeEditorGraphUpstream | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #533 |
| Shift+> | Shift+PERIOD | nodeEditorPanel | NodeEditorGraphDownstream | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #534 |
| Ctrl+l | Ctrl+L | nodeEditorPanel | NodeEditorGraphRemoveSelected | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #535 |
| Ctrl+/ | Ctrl+SLASH | nodeEditorPanel | NodeEditorGraphRemoveUnselected | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #536 |
| Ctrl+, | Ctrl+COMMA | nodeEditorPanel | NodeEditorGraphRemoveUpstream | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #537 |
| Ctrl+. | Ctrl+PERIOD | nodeEditorPanel | NodeEditorGraphRemoveDownstream | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #538 |
| Up | UP_ARROW | nodeEditorPanel | NodeEditorPickWalkUp | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #539 |
| Down | DOWN_ARROW | nodeEditorPanel | NodeEditorPickWalkDown | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #540 |
| Right | RIGHT_ARROW | nodeEditorPanel | NodeEditorPickWalkRight | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #541 |
| Left | LEFT_ARROW | nodeEditorPanel | NodeEditorPickWalkLeft | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #542 |
| Ctrl+c | Ctrl+C | nodeEditorPanel | NodeEditorCopy | Node Editor: `node.clipboard_copy` | IC 일치 |  | #543 |
| Ctrl+x | Ctrl+X | nodeEditorPanel | NodeEditorCut | — | 해당 없음 | Maya Node Editor 표시·탐색 (Blender 노드 편집기에 같은 기능 없음 / Blender 키 그대로) | #544 |
| Ctrl+v | Ctrl+V | nodeEditorPanel | NodeEditorPaste | Node Editor: `node.clipboard_paste` | IC 일치 |  | #545 |
| Cmd+c | Oskey+C | nodeEditorPanel | NodeEditorCopy | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #548 |
| Cmd+x | Oskey+X | nodeEditorPanel | NodeEditorCut | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #549 |
| Cmd+v | Oskey+V | nodeEditorPanel | NodeEditorPaste | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #550 |
| Delete | DEL | polyTexturePlacementPanel | DeleteUVs | UV Editor: `allset.uv_delete` | 구현 | step 155 | #554 |
| Ctrl+c | Ctrl+C | polyTexturePlacementPanel | CopyUVs | UV Editor: `uv.copy` | IC 일치 |  | #555 |
| Ctrl+v | Ctrl+V | polyTexturePlacementPanel | PasteUVs | UV Editor: `uv.paste` | IC 일치 |  | #556 |
| Ctrl+l | Ctrl+L | polyTexturePlacementPanel | LayoutUV | UV Editor: `allset.uv_layout` | 구현 | Pack Islands, 셸 패딩 px / 맵 크기 (IC select_linked 제거) | #557 |
| Ctrl+u | Ctrl+U | polyTexturePlacementPanel | UnfoldUV | UV Editor: `allset.uv_unfold` | 구현 | Blender Unwrap (Minimum Stretch), 셸 경계·자리 유지 (Unfold3D 아님) | #558 |
| Shift+x | Shift+X | polyTexturePlacementPanel | CutUVs | UV Editor: `allset.uv_cut` | 구현 | 솔기 + 작은 쪽 셸을 0.2 px 떼어 그 자리에서 분리 (IC 스냅 파이 제거) | #559 |
| Shift+s | Shift+S | polyTexturePlacementPanel | SewUVs | UV Editor: `allset.uv_sew` | 구현 | 솔기 지움 + 작은 셸을 엣지에 맞춰 옮김 | #560 |
| Ctrl+Shift+x | Ctrl+Shift+X | polyTexturePlacementPanel | CreateUVShellAlongBorder | UV Editor: `allset.uv_create_shell` | 구현 | step 155 | #561 |
| 4 | FOUR | polyTexturePlacementPanel | DisplayUVWireframe | UV Editor: `allset.uv_display` (mode='WIREFRAME') | 구현 | step 155 | #562 |
| 5 | FIVE | polyTexturePlacementPanel | DisplayUVShaded | UV Editor: `allset.uv_display` (mode='SHADED') | 구현 | UV 면 표시 켬 (step 155) | #563 |
| 7 | SEVEN | polyTexturePlacementPanel | ToggleUVDistortion | UV Editor: `wm.context_toggle` (data_path='space_data.uv_editor.show_stretch') | 구현 |  | #564 |
| 8 | EIGHT | polyTexturePlacementPanel | ToggleUVShellBorder | UV Editor: `allset.uv_display` (mode='SHELL_BORDERS') | 구현 | step 155 | #565 |
| 9 | NINE | polyTexturePlacementPanel | UVEditorToggleTextureBorderDisplay | UV Editor: `allset.uv_display` (mode='TEXTURE_BORDERS') | 구현 | step 155 | #566 |
| 6 | SIX | polyTexturePlacementPanel | ToggleUVTextureImage | UV Editor: `allset.uv_display` (mode='IMAGE') | 구현 | step 155 | #567 |
| Ctrl+1 | Ctrl+ONE | polyTexturePlacementPanel | ToggleUVIsolateViewSelected | UV Editor: `allset.uv_isolate` | 구현 | step 155 | #568 |
| f | F | polyTexturePlacementPanel | UVEditorFrameSelected | Image: `image.view_selected` | IC 일치 |  | #569 |
| a | A | polyTexturePlacementPanel | UVEditorFrameAll | Image: `image.view_all` | IC 일치 |  | #570 |
| q | Q | polyTexturePlacementPanel | SelectUVTool | UV Editor: `wm.tool_set_by_id` (name='builtin.select_box', cycle=True); Image: `wm.tool_set_by_id` (name='builtin.select_box', cycle=True) | IC 일치 |  | #571 |
| w | W | polyTexturePlacementPanel | MoveUVTool | UV Editor: `wm.tool_set_by_id` (name='builtin.move', cycle=True); Image: `wm.tool_set_by_id` (name='builtin.transform', cycle=True) | IC 일치 |  | #572 |
| e | E | polyTexturePlacementPanel | RotateUVTool | UV Editor: `wm.tool_set_by_id` (name='builtin.rotate', cycle=True); Image: `wm.tool_set_by_id` (name='builtin.transform', cycle=True) | IC 일치 |  | #573 |
| r | R | polyTexturePlacementPanel | ScaleUVTool | UV Editor: `wm.tool_set_by_id` (name='builtin.scale', cycle=True); Image: `wm.tool_set_by_id` (name='builtin.transform', cycle=True) | IC 일치 |  | #574 |
| Ctrl+Up | Ctrl+UP_ARROW | polyTexturePlacementPanel | IncreaseCheckerDensity | — | 해당 없음 | UV 체커 밀도 없음 (Blender 체커는 이미지); Maya 2026 은 UV Editor 키 | #575 |
| Ctrl+Down | Ctrl+DOWN_ARROW | polyTexturePlacementPanel | DecreaseCheckerDensity | — | 해당 없음 | UV 체커 밀도 없음; Maya 2026 은 UV Editor 키 | #576 |
| x | X | polyCutUV | CutUVs3D | — | 구현 | 툴 안에서 x = 선택 엣지 Cut (드래그 = 바로 자르기) | #579 |
| s | S | polyCutUV | SewUVs3D | — | 구현 | 툴 안에서 s = 선택 엣지 Sew (Ctrl+드래그 = 바로 꿰매기) | #580 |
| d | D | polyCutUV | UnfoldPackUVs3DInCurrentTile | — | 구현 | 툴 안에서 d = Unfold + Layout (0-1) | #581 |
| Shift+d | Shift+D | polyCutUV | UnfoldPackUVs3DInEmptyTile | — | 해당 없음 | Blender 에 UDIM 빈 타일 배치 없음 (d = 0-1 에 Layout) | #582 |
| Cmd+c | Oskey+C | polyTexturePlacementPanel | CopyUVs | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #585 |
| Cmd+v | Oskey+V | polyTexturePlacementPanel | PasteUVs | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #586 |
| Cmd+l | Oskey+L | polyTexturePlacementPanel | LayoutUV | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #587 |
| Cmd+u | Oskey+U | polyTexturePlacementPanel | UnfoldUV | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #588 |
| Cmd+Shift+x | Shift+Oskey+X | polyTexturePlacementPanel | CreateUVShellAlongBorder | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #589 |
| Cmd+1 | Oskey+ONE | polyTexturePlacementPanel | ToggleUVIsolateViewSelected | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #590 |
| Cmd+Up | Oskey+UP_ARROW | polyTexturePlacementPanel | IncreaseCheckerDensity | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #591 |
| Cmd+Down | Oskey+DOWN_ARROW | polyTexturePlacementPanel | DecreaseCheckerDensity | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #592 |
| Ctrl+g | Ctrl+G | shapePanel | ShapeEditorNewGroup | — | 해당 없음 | Shape Editor 없음 (Blender Shape Keys 패널) | #596 |
| Ctrl+d | Ctrl+D | shapePanel | ShapeEditorDuplicateTarget | — | 해당 없음 | Shape Editor 없음 (Blender Shape Keys 패널) | #597 |
| Alt+d | Alt+D | shapePanel | ShapeEditorSelectNone | — | 해당 없음 | Shape Editor 없음 (Blender Shape Keys 패널) | #598 |
| Ctrl+g | Ctrl+G | posePanel | PoseInterpolatorNewGroup | — | 해당 없음 | Pose Editor 없음 | #601 |
| 1 | ONE | hyperShadePanel | HypershadeHideAttributes | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #604 |
| 2 | TWO | hyperShadePanel | HypershadeShowConnectedAttrs | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #605 |
| 3 | THREE | hyperShadePanel | HypershadeShowAllAttrs | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #606 |
| 4 | FOUR | hyperShadePanel | HypershadeShowCustomAttrs | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #607 |
| 5 | FIVE | hyperShadePanel | HypershadeToggleNodeTitleMode | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #608 |
| p | P | hyperShadePanel | HypershadePinSelected | Node Editor: `node.parent_set` | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #609 |
| = | EQUAL | hyperShadePanel | HypershadeToggleZoomIn | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #610 |
| - | MINUS | hyperShadePanel | HypershadeToggleZoomOut | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #611 |
| / | SLASH | hyperShadePanel | HypershadeSelectConnected | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #612 |
| , | COMMA | hyperShadePanel | HypershadeSelectUpStream | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #613 |
| . | PERIOD | hyperShadePanel | HypershadeSelectDownStream | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #614 |
| Shift+? | Shift+SLASH | hyperShadePanel | HypershadeGraphUpDownstream | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #615 |
| Shift+< | Shift+COMMA | hyperShadePanel | HypershadeGraphUpstream | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #616 |
| Shift+> | Shift+PERIOD | hyperShadePanel | HypershadeGraphDownstream | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #617 |
| Ctrl+l | Ctrl+L | hyperShadePanel | HypershadeGraphRemoveSelected | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #618 |
| Ctrl+/ | Ctrl+SLASH | hyperShadePanel | HypershadeGraphRemoveUnselected | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #619 |
| Ctrl+, | Ctrl+COMMA | hyperShadePanel | HypershadeGraphRemoveUpstream | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #620 |
| Ctrl+. | Ctrl+PERIOD | hyperShadePanel | HypershadeGraphRemoveDownstream | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #621 |
| Up | UP_ARROW | hyperShadePanel | HypershadePickWalkUp | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #622 |
| Down | DOWN_ARROW | hyperShadePanel | HypershadePickWalkDown | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #623 |
| Right | RIGHT_ARROW | hyperShadePanel | HypershadePickWalkRight | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #624 |
| Left | LEFT_ARROW | hyperShadePanel | HypershadePickWalkLeft | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #625 |
| Shift+! | Shift+ONE | hyperShadePanel | SoloLastOutput | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #626 |
| Shift+@ | Shift+TWO | hyperShadePanel | SoloMaterial | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #627 |
| Shift+# | Shift+THREE | hyperShadePanel | RemoveMaterialSoloing | — | 해당 없음 | Hypershade 그래프 표시·탐색 (kit Hypershade = Shader Editor, Blender 키 그대로) | #628 |
| Ctrl+0 | Ctrl+ZERO | xgmIGBrush | XgmSetFreezeBrushTool | — | 해당 없음 | XGen 없음 | #631 |
| Ctrl+1 | Ctrl+ONE | xgmIGBrush | XgmSetDensityBrushTool | — | 해당 없음 | XGen 없음 | #632 |
| Ctrl+2 | Ctrl+TWO | xgmIGBrush | XgmSetCombBrushTool | — | 해당 없음 | XGen 없음 | #633 |
| Ctrl+3 | Ctrl+THREE | xgmIGBrush | XgmSetGrabBrushTool | — | 해당 없음 | XGen 없음 | #634 |
| Ctrl+5 | Ctrl+FIVE | xgmIGBrush | XgmSetDirectionBrushTool | — | 해당 없음 | XGen 없음 | #636 |
| Ctrl+6 | Ctrl+SIX | xgmIGBrush | XgmSetSmoothBrushTool | — | 해당 없음 | XGen 없음 | #637 |
| Ctrl+7 | Ctrl+SEVEN | xgmIGBrush | XgmSetNoiseBrushTool | — | 해당 없음 | XGen 없음 | #638 |
| Ctrl+8 | Ctrl+EIGHT | xgmIGBrush | XgmSetClumpBrushTool | — | 해당 없음 | XGen 없음 | #639 |
| Ctrl+9 | Ctrl+NINE | xgmIGBrush | XgmSetPartBrushTool | — | 해당 없음 | XGen 없음 | #640 |
| Alt+r | Alt+R | global | ToggleReflection | 3D View: `allset.symmetry` (mode='TOGGLE') | 구현 | 대칭 켬/끔 (kit 대칭 = 메시 mirror → 모델링·조각·페인트); IC 의 스케일 초기화 제거; 가중치 페인트에서는 X 미러 토글 (allset.paint_reflection, step 218) | #643 |
| Shift+U | Shift+U | sculptMeshCache | SculptMeshUnfreezeAll | Sculpt: `paint.mask_flood_fill` (mode='VALUE', value=0.0) | 구현 | 마스크 지움 | #645 |
| Ctrl+Shift+I | Ctrl+Shift+I | sculptMeshCache | SculptMeshInvertFreeze | Sculpt: `paint.mask_flood_fill` (mode='INVERT') | 구현 | 마스크 반전 | #646 |
| Ctrl+0 | Ctrl+ZERO | sculptMeshCache | SetMeshFreezeTool | Sculpt: `brush.asset_activate` (asset_library_type='ESSENTIALS', relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Mask') | 구현 | Mask 브러시 | #648 |
| Ctrl+1 | Ctrl+ONE | sculptMeshCache | SetMeshSculptTool | Sculpt: `brush.asset_activate` (asset_library_type='ESSENTIALS', relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Draw'); 3D View: `allset.isolate` | 구현 | Draw (IC 의 Ctrl+0–5 multires 단계 대체) | #649 |
| Ctrl+2 | Ctrl+TWO | sculptMeshCache | SetMeshSmoothTool | Sculpt: `brush.asset_activate` (asset_library_type='ESSENTIALS', relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Smooth') | 구현 | Smooth | #650 |
| Ctrl+3 | Ctrl+THREE | sculptMeshCache | SetMeshRelaxTool | Sculpt: `brush.asset_activate` (asset_library_type='ESSENTIALS', relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Relax Slide') | 구현 | Relax Slide | #651 |
| Ctrl+4 | Ctrl+FOUR | sculptMeshCache | SetMeshGrabTool | Sculpt: `brush.asset_activate` (asset_library_type='ESSENTIALS', relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Grab') | 구현 | Grab | #652 |
| Ctrl+5 | Ctrl+FIVE | sculptMeshCache | SetMeshPinchTool | Sculpt: `brush.asset_activate` (asset_library_type='ESSENTIALS', relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Pinch/Magnify') | 구현 | Pinch/Magnify | #653 |
| Ctrl+6 | Ctrl+SIX | sculptMeshCache | SetMeshFlattenTool | Sculpt: `brush.asset_activate` (asset_library_type='ESSENTIALS', relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Flatten/Contrast') | 구현 | Flatten/Contrast | #654 |
| Ctrl+7 | Ctrl+SEVEN | sculptMeshCache | SetMeshFoamyTool | Sculpt: `brush.asset_activate` (asset_library_type='ESSENTIALS', relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Blob') | 구현 | Blob (가장 가까운 것) | #655 |
| Ctrl+8 | Ctrl+EIGHT | sculptMeshCache | SetMeshSprayTool | Sculpt: `brush.asset_activate` (asset_library_type='ESSENTIALS', relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Draw Sharp') | 구현 | Draw Sharp (Blender 에 스탬프 스프레이 없음, 가장 가까운 것) | #656 |
| Ctrl+9 | Ctrl+NINE | sculptMeshCache | SetMeshRepeatTool | Sculpt: `brush.asset_activate` (asset_library_type='ESSENTIALS', relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Layer') | 구현 | Layer (Blender 에 반복 스탬프 없음, 가장 가까운 것) | #657 |
| f | F | sculptMeshCache | SculptMeshFrame | 3D View: `allset.frame` (selected=True) | 구현 |  | #659 |
| b | B | sculptMeshCache | SculptMeshActivateBrushSize / SculptMeshDeactivateBrushSize (release) | Sculpt: `wm.radial_control` (data_path_primary='tool_settings.sculpt.brush.size', data_path_secondary='tool_settings.unified_paint_settings.size', use_secondary='tool_settings.unified_paint_settings.use_unified_size', rotation_path='tool_settings.sculpt.brush.texture_slot.angle', color_path='tool_settings.sculpt.brush.cursor_color_add', fill_color_path='', fill_color_override_path='', fill_color_override_test_path='', zoom_path='', image_id='tool_settings.sculpt.brush', secondary_tex=False); 3D View: `allset.tap_hold` (binding='soft_select') | 구현 | 크기 드래그; IC 의 B 브러시 선반 제거 | #661 |
| m | M | sculptMeshCache | SculptMeshActivateBrushStrength / SculptMeshDeactivateBrushStrength (release) | Sculpt: `wm.radial_control` (data_path_primary='tool_settings.sculpt.brush.strength', data_path_secondary='tool_settings.unified_paint_settings.strength', use_secondary='tool_settings.unified_paint_settings.use_unified_strength', rotation_path='tool_settings.sculpt.brush.texture_slot.angle', color_path='tool_settings.sculpt.brush.cursor_color_add', fill_color_path='', fill_color_override_path='', fill_color_override_test_path='', zoom_path='', image_id='tool_settings.sculpt.brush', secondary_tex=False) | 구현 | 세기 드래그 | #662 |
| b | B | texSculptCacheContext | TexSculptActivateBrushSize / TexSculptDeactivateBrushSize (release) | — | 해당 없음 | UV 조각 도구 없음 (Blender UV Sculpt 는 브러시 크기 F) | #664 |
| m | M | texSculptCacheContext | TexSculptActivateBrushStrength / TexSculptDeactivateBrushStrength (release) | — | 해당 없음 | UV 조각 도구 없음 (Blender UV Sculpt 는 브러시 크기 F) | #665 |
| b | B | Unfold3DBrush | U3DBrushSizeOn / U3DBrushSizeOff (release) | — | 해당 없음 | Unfold3D 브러시 없음 | #667 |
| m | M | Unfold3DBrush | U3DBrushPressureOn / U3DBrushPressureOff (release) | — | 해당 없음 | Unfold3D 브러시 없음 | #668 |
| b | B | SymmetrizeUVBrush | SymmetrizeUVBrushSizeOn / SymmetrizeUVBrushSizeOff (release) | — | 해당 없음 | UV 대칭 브러시 없음 | #670 |
| b | B | texCutContext | TexSewActivateBrushSize / TexSewDeactivateBrushSize (release) | — | 해당 없음 | 3D Cut and Sew 브러시 크기 조정 없음 (step 79 도구는 클릭/드래그) | #672 |
| Cmd+g | Oskey+G | shapePanel | ShapeEditorNewGroup | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #676 |
| Cmd+d | Oskey+D | shapePanel | ShapeEditorDuplicateTarget | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #677 |
| Cmd+g | Oskey+G | posePanel | PoseInterpolatorNewGroup | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #680 |
| Cmd+Shift+I | Shift+Oskey+I | sculptMeshCache | SculptMeshInvertFreeze | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #682 |
| Cmd+0 | Oskey+ZERO | sculptMeshCache | SetMeshFreezeTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #683 |
| Cmd+1 | Oskey+ONE | sculptMeshCache | SetMeshSculptTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #684 |
| Cmd+2 | Oskey+TWO | sculptMeshCache | SetMeshSmoothTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #685 |
| Cmd+3 | Oskey+THREE | sculptMeshCache | SetMeshRelaxTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #686 |
| Cmd+4 | Oskey+FOUR | sculptMeshCache | SetMeshGrabTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #687 |
| Cmd+5 | Oskey+FIVE | sculptMeshCache | SetMeshPinchTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #688 |
| Cmd+6 | Oskey+SIX | sculptMeshCache | SetMeshFlattenTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #689 |
| Cmd+7 | Oskey+SEVEN | sculptMeshCache | SetMeshFoamyTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #690 |
| Cmd+8 | Oskey+EIGHT | sculptMeshCache | SetMeshSprayTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #691 |
| Cmd+9 | Oskey+NINE | sculptMeshCache | SetMeshRepeatTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #692 |
| Ctrl+Up | Ctrl+UP_ARROW | global | CoarserSubdivLevel | — | 해당 없음 | Maya subdiv surface 노드 없음 | #696 |
| Ctrl+Down | Ctrl+DOWN_ARROW | global | CreateSubdivRegion | — | 해당 없음 | Maya subdiv surface 노드 없음 | #697 |
| Alt+Shift+A | Alt+Shift+A | global | DecrementFluidCenter | — | 해당 없음 | Maya Fluids 없음 | #701 |
| Alt+Shift+S | Alt+Shift+S | global | IncrementFluidCenter | — | 해당 없음 | Maya Fluids 없음 | #702 |
| Ctrl+Space | Ctrl+SPACE | global | ToggleFullScreenMode | Screen: `screen.screen_full_area` (use_hide_panels=True) | 구현 | UI 숨긴 전체 화면 | #705 |
| Shift+Space | Shift+SPACE | global | ToggleZoomInMode | 3D View Generic: `wm.context_toggle` (data_path='space_data.show_region_asset_shelf') | 해당 없음 | 2D Pan/Zoom 확대 모드 없음; IC 에셋 선반 토글 그대로 | #707 |
| Alt+b | Alt+B | global | CycleBackgroundColor | 3D View: `allset.cycle_background` | 구현 | 모든 뷰: 회색 0.36 → 밝은 회색 0.631 → 그라데이션 → 검정 (Maya 실측, 그라데이션은 Maya 테마일 때만; step 120) | #710 |
| Ctrl+` | Ctrl+ACCENT_GRAVE | global | SmoothingDisplayToggle | Object Mode: `allset.smooth_proxy` (action='TOGGLE'); Mesh: `allset.smooth_proxy` (action='TOGGLE') | 구현 | 프록시 Subsurf 켬 ↔ 끔 (케이지 ↔ 스무드), 둘 다 보기 → 케이지 | #714 |
| Shift+~ | Shift+ACCENT_GRAVE | global | SmoothingDisplayShowBoth | Object Mode: `allset.smooth_proxy` (action='BOTH'); Mesh: `allset.smooth_proxy` (action='BOTH') | 구현 | Subsurf 켬 + 케이지 와이어 | #715 |
| Ctrl+Shift+~ | Ctrl+Shift+ACCENT_GRAVE | global | SmoothProxy | Object Mode: `allset.smooth_proxy` (action='CREATE') | 구현 | Mesh > Smooth Proxy > Subdiv Proxy (Subsurf 추가) | #716 |
| Alt+` | Alt+ACCENT_GRAVE | global | CreateSubdivSurface | — | 해당 없음 | Subdiv Surface 오브젝트 없음 (3 / Smooth Proxy) | #717 |
| Alt+Shift+~ | Alt+Shift+ACCENT_GRAVE | global | CreateSubdivSurfaceOptions | — | 해당 없음 | Subdiv Surface 오브젝트 없음 | #718 |
| Page_Up | PAGE_UP | global | SmoothingLevelIncrease | Object Mode: `allset.smooth_level` (delta=1); Mesh: `allset.smooth_level` (delta=1) | 구현 | 스무스 프리뷰 단계 0–4 — step 27 | #719 |
| Page_Down | PAGE_DOWN | global | SmoothingLevelDecrease | Object Mode: `allset.smooth_level` (delta=-1); Mesh: `allset.smooth_level` (delta=-1) | 구현 |  | #720 |
| ` | ACCENT_GRAVE | global | STRSTweakModeOn / STRSTweakModeOff (release) | 3D View: `allset.tweak_hold` | 구현 | 누르는 동안 Blender Tweak 툴 (클릭-드래그 = 그 자리 이동), 놓으면 원래 툴 | #723 |
| l | L | global | LockCurveLength / UnlockCurveLength (release) | — | 해당 없음 | 커브 길이 잠금 없음 | #727 |
| Alt+g | Alt+G | hyperGraphPanel | HypergraphIncreaseDepth | — | 해당 없음 | Hypergraph 없음 (Outliner / Drivers) | #730 |
| Alt+t | Alt+T | hyperGraphPanel | HypergraphDecreaseDepth | — | 해당 없음 | Hypergraph 없음 (Outliner / Drivers) | #731 |
| Ctrl+Shift+W | Ctrl+Shift+W | global | ToggleSteeringWheel | Screen: `allset.insert_key` (channels='TRANSLATE') | 해당 없음 | Steering Wheel 없음; Ctrl+Shift+W 는 kit 키 삽입 (step 83) | #735 |
| \ | BACK_SLASH | global | TogglePanZoomPress | 3D View: `allset.pan_zoom_hold` | 구현 | 카메라 뷰에서 누르는 동안 LMB 팬 / MMB 줌 (camera view offset / zoom, 렌더 그대로) | #738 |
| \ | BACK_SLASH | global | — / TogglePanZoomRelease (release) | 3D View: `allset.pan_zoom_hold` | 구현 | 놓기 = pan_zoom_hold 모달이 끝냄 (누름 행의 항목) | #739 |
| Alt+x | Alt+X | global | WalkContext_Command | 3D View: `view3d.walk` | 구현 | Blender Walk 모달 (클릭 / Enter = 끝, ESC = 취소); IC Alt+X X-ray 제거 | #742 |
| Shift+T | Shift+T | global | AssignNewMaterial | Object Mode: `allset.assign_new_material`; Mesh: `allset.assign_new_material` | 구현 | 재질 종류 검색 팝업 → 만들어 지정 (편집 모드 면 선택 = 면에만, step 29) | #746 |
| Ctrl+= | Ctrl+EQUAL | global | IncreaseExposureFine | — | 해당 없음 | Render View 노출 = Color Management (Render 속성) | #749 |
| Ctrl+- | Ctrl+MINUS | global | DecreaseExposureFine | — | 해당 없음 | Render View 노출 = Color Management | #750 |
| Ctrl+' | Ctrl+QUOTE | global | IncreaseGammaFine | — | 해당 없음 | Render View 감마 = Color Management | #751 |
| Ctrl+; | Ctrl+SEMI_COLON | global | DecreaseGammaFine | — | 해당 없음 | Render View 감마 = Color Management | #752 |
| Ctrl+Alt+= | Ctrl+Alt+EQUAL | global | IncreaseExposureCoarse | — | 해당 없음 | Render View 노출 = Color Management | #753 |
| Ctrl+Alt+- | Ctrl+Alt+MINUS | global | DecreaseExposureCoarse | — | 해당 없음 | Render View 노출 = Color Management | #754 |
| Ctrl+Alt+' | Ctrl+Alt+QUOTE | global | IncreaseGammaCoarse | — | 해당 없음 | Render View 감마 = Color Management | #755 |
| Ctrl+Alt+; | Ctrl+Alt+SEMI_COLON | global | DecreaseGammaCoarse | — | 해당 없음 | Render View 감마 = Color Management | #756 |
| Ctrl+p | Ctrl+P | global | ColorPickerNameCommand | — | 해당 없음 | 색 선택기 명령 없음 (Blender 색 칸 클릭) | #757 |
| Ctrl+r | Ctrl+R | profilerPanel | ProfilerToolToggleRecording | — | 해당 없음 | Maya Profiler 없음 | #760 |
| 1 | ONE | profilerPanel | ProfilerToolCategoryView | — | 해당 없음 | Maya Profiler 없음 | #761 |
| 2 | TWO | profilerPanel | ProfilerToolCpuView | — | 해당 없음 | Maya Profiler 없음 | #762 |
| 3 | THREE | profilerPanel | ProfilerToolThreadView | — | 해당 없음 | Maya Profiler 없음 | #763 |
| Ctrl+f | Ctrl+F | global | SearchEngine | Screen: `wm.search_menu` | 구현 | Blender 메뉴 검색 (F3 과 같음) | #765 |
| Cmd+f | Oskey+F | global | SearchEngine | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | #768 |
| Ctrl+Shift+E | Ctrl+Shift+E | global | InsertKeyRotate | Screen: `allset.insert_key` (channels='ROTATE') | 구현 | 있는 Rotate 곡선에만, 모양 그대로 | #770 |
| Ctrl+Shift+W | Ctrl+Shift+W | global | InsertKeyTranslate | Screen: `allset.insert_key` (channels='TRANSLATE') | 구현 | 있는 Translate 곡선에만, 모양 그대로 (새 곡선 안 만듦) | #771 |
| Ctrl+Shift+R | Ctrl+Shift+R | global | InsertKeyScale | Screen: `allset.insert_key` (channels='SCALE') | 구현 | 있는 Scale 곡선에만, 모양 그대로 | #772 |
| Alt+i | Alt+I | global | InsertKey | Screen: `allset.insert_key` (channels='ALL') | 구현 | 곡선 모양 그대로 현재 시간 키: Graph Editor 선택 곡선 → 보이는 곡선, 그 밖 = 선택 노드 곡선 | #773 |
| Alt+/ | Alt+SLASH | graphEditor | SnapTimeToSelection | Graph Editor: `allset.snap_time_toggle` | 구현 | Snap Time To Selection 켬/끔 (View 메뉴 체크): 키 선택 = 가장 이른 키로 시간 | #775 |
| Alt+1 | Alt+ONE | global | ToggleNurbsCurvesOptionCmd | 3D View: `allset.toggle_show` (kind='CURVES') | 구현 | 커서 아래 뷰의 커브 보이기 | #776 |
| Alt+2 | Alt+TWO | global | TogglePolygonsOptionCmd | 3D View: `allset.toggle_show` (kind='POLYGONS') | 구현 | 커서 아래 뷰의 메시 보이기 | #777 |
| Alt+4 | Alt+FOUR | global | ToggleImagePlaneOptionCmd | 3D View: `allset.toggle_show` (kind='IMAGE_PLANES') | 구현 | 이미지 엠프티 (Free Image Plane) 표시 — Blender 에 뷰별 필터가 없어 모든 뷰 | #778 |
| Alt+5 | Alt+FIVE | global | ToggleWireframeOnShadedCmd | 3D View: `wm.context_toggle` (data_path='space_data.overlay.show_wireframes') | 구현 | 뷰포트 오버레이 Wireframe (모든 오브젝트) — step 27 | #779 |
| Shift+) | Shift+ZERO | global | NudgeSelectedKeysForward | Screen: `allset.nudge_keys` (delta=1) | 구현 | Graph Editor / Dope Sheet 선택 키, 그 밖 = 선택 노드의 현재 시간 (또는 Shift 범위) 키 + 시간도 같이 | #780 |
| Shift+( | Shift+NINE | global | NudgeSelectedKeysBackward | Screen: `allset.nudge_keys` (delta=-1) | 구현 | 겹치는 키는 덮어씀 (Maya -o over) | #781 |
| Alt+t | Alt+T | global | CreateTimeSliderBookmark | Screen: `allset.bookmark_create` | 구현 | 북마크 = 타임라인 마커 (선택 범위 시작, 끝은 장면 속성), 이름 대화상자 | #783 |
| Alt+Shift+T | Alt+Shift+T | global | QuickCreateTimeSliderBookmark | Screen: `allset.bookmark_create` (quick=True) | 구현 |  | #784 |
| Shift+&#124; | Shift+BACK_SLASH | global | FrameTimeSliderBookmark | Screen: `allset.bookmark_frame` (which='CURRENT') | 구현 | 재생 범위 = 이 북마크 범위 | #785 |
| Shift+" | Shift+QUOTE | global | FrameNextTimeSliderBookmark | Screen: `allset.bookmark_frame` (which='NEXT') | 구현 |  | #786 |
| Shift+: | Shift+SEMI_COLON | global | FramePreviousTimeSliderBookmark | Screen: `allset.bookmark_frame` (which='PREVIOUS') | 구현 |  | #787 |
| Alt+\ | Alt+BACK_SLASH | global | PlaybackRangeAnimStartEnd | Screen: `allset.playback_range_anim` | 구현 | 재생 범위 = 애니메이션 범위 (프리뷰 범위 끔, 값은 남아 Range Slider 더블클릭으로 되돌림) | #788 |
| ' | QUOTE | global | NextTimeSliderBookmark | Screen: `screen.marker_jump` (next=True) | 구현 |  | #789 |
| ; | SEMI_COLON | global | PreviousTimeSliderBookmark | Screen: `screen.marker_jump` (next=False) | 구현 |  | #790 |
