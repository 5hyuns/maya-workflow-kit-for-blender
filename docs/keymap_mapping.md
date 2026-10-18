# Maya 기본 단축키 → Blender 대응표

자동 생성: `python tools/gen_keymap_mapping.py` (손으로 고치지 말 것).
입력: `research/maya/hotkeys_default.json` (Maya 2022 팩토리 핫키 468개; 근거 열 = Maya `scripts/startup/hotkeySetup.mel` 줄). Blender 쪽: 이 킷의 "Maya" 키컨피그 (`src/maya_kit/keymap/`), 상태 = `keymap/mapping.py`.

현재 바인딩 = Maya 컨텍스트에 대응하는 Blender 키맵들(`mapping.CONTEXT_KEYMAPS`)에서 같은 키에 걸린 항목. 근사 조회라 모드에 따라 실제로 먼저 잡히는 항목은 다를 수 있다.

| 상태 | 개수 |
|---|---|
| 구현 | 113 |
| IC 일치 | 10 |
| 해당 없음 | 10 |
| 미검토 | 267 |
| macOS 전용 | 68 |

| Maya 키 | Blender 이벤트 | 컨텍스트 | runTimeCommand | Maya 키컨피그 현재 바인딩 | 상태 | 비고 | 근거 |
|---|---|---|---|---|---|---|---|
| Ctrl+Shift+A | Ctrl+Shift+A | global | SelectAll | Object Mode: `object.select_all` (action='SELECT'); Mesh: `mesh.select_all` (action='SELECT') | 구현 | 편집 모드: mesh.select_all(SELECT) | hotkeySetup.mel:59 |
| Ctrl+Shift+C | Ctrl+Shift+C | global | CreateCameraFromView | — | 미검토 |  | hotkeySetup.mel:60 |
| Alt+d | Alt+D | global | SelectNone | Object Mode: `object.select_all` (action='DESELECT'); Mesh: `maya_kit.select_none` | 구현 | 편집 모드: maya_kit.select_none (해제 + 오브젝트 모드) | hotkeySetup.mel:62 |
| Ctrl+d | Ctrl+D | global | Duplicate | Object Mode: `maya_kit.duplicate`; Mesh: `mesh.duplicate_move` | 구현 | 제자리, 자식 포함, pCube2/pCubeShape2 (편집 모드는 IC duplicate_move) | hotkeySetup.mel:64 |
| Ctrl+Shift+D | Ctrl+Shift+D | global | DuplicateSpecial | Object Mode: `maya_kit.duplicate_special` | 구현 | 복사/인스턴스, 사본 수, 누적 오프셋 (Adjust Last Operation) | hotkeySetup.mel:65 |
| z | Z | global | Undo | Screen: `ed.undo` | 구현 | Screen 키맵: 모든 에디터. z 를 가리던 zoom/viewer border 제거 (Shift+B 로 남음) | hotkeySetup.mel:67 |
| Ctrl+z | Ctrl+Z | global | Undo | Screen: `asset.catalog_undo`; Screen: `ed.undo` | 구현 | Screen 키맵: 모든 에디터. z 를 가리던 zoom/viewer border 제거 (Shift+B 로 남음) | hotkeySetup.mel:68 |
| Shift+Z | Shift+Z | global | Redo | Screen: `ed.redo` | 구현 |  | hotkeySetup.mel:69 |
| Ctrl+q | Ctrl+Q | global | Quit | Window: `wm.quit_blender` | 미검토 |  | hotkeySetup.mel:71 |
| Ctrl+o | Ctrl+O | global | OpenScene | Window: `maya_kit.open_scene` | 구현 | 파일 창이 프로젝트 scenes 폴더에서 시작 (없으면 Blender 그대로) | hotkeySetup.mel:73 |
| Ctrl+n | Ctrl+N | global | NewScene | Window: `wm.read_homefile` | 미검토 |  | hotkeySetup.mel:74 |
| Ctrl+s | Ctrl+S | global | SaveScene | Window: `maya_kit.save_scene` | 구현 | 처음 저장은 프로젝트 scenes 폴더에서 Save As | hotkeySetup.mel:75 |
| Ctrl+Shift+S | Ctrl+Shift+S | global | SaveSceneAs | Window: `maya_kit.save_scene_as` | 구현 | 프로젝트 scenes 폴더에서 시작 | hotkeySetup.mel:76 |
| Ctrl+Alt+s | Ctrl+Alt+S | global | IncrementAndSave | Window: `maya_kit.increment_save` | 구현 | Maya 규칙 shot_v001 → shot_v001.0001 (메뉴와 같음; IC 의 Blender 규칙 shot_v002 대신) | hotkeySetup.mel:77 |
| Ctrl+r | Ctrl+R | global | CreateReference | Window: `maya_kit.create_reference` | 구현 | .blend 링크 + library override, 이름 ns:이름 (편집 모드 등 Ctrl+R 이 있는 에디터는 그쪽 우선) | hotkeySetup.mel:78 |
| Ctrl+g | Ctrl+G | global | Group | Object Mode: `maya_kit.group` | 구현 | Empty 그룹, 피벗 원점, group1 명명 (Outliner 도) | hotkeySetup.mel:79 |
| Ctrl+Shift+I | Ctrl+Shift+I | global | InvertSelection | Object Mode: `object.select_all` (action='INVERT'); Mesh: `mesh.select_all` (action='INVERT') | 구현 | 편집 모드: mesh.select_all(INVERT) | hotkeySetup.mel:81 |
| Ctrl+x | Ctrl+X | global | CutSelected | — | 미검토 |  | hotkeySetup.mel:84 |
| Ctrl+c | Ctrl+C | global | CopySelected | 3D View: `view3d.copybuffer` | 미검토 |  | hotkeySetup.mel:85 |
| Ctrl+v | Ctrl+V | global | PasteSelected | 3D View: `view3d.pastebuffer` | 미검토 |  | hotkeySetup.mel:86 |
| Ctrl+Up | Ctrl+UP_ARROW | global | IncreaseCheckerDensity | — | 미검토 |  | hotkeySetup.mel:88 |
| Ctrl+Down | Ctrl+DOWN_ARROW | global | DecreaseCheckerDensity | — | 미검토 |  | hotkeySetup.mel:89 |
| q | Q | timeEditorPanel | TimeEditorSceneAuthoringToggle | NLA Editor: `nla.select_box` (axis_range=False) | 미검토 |  | hotkeySetup.mel:92 |
| w | W | timeEditorPanel | TimeEditorClipRazor | NLA Editor: `transform.transform` (mode='TRANSLATION') | 미검토 |  | hotkeySetup.mel:93 |
| e | E | timeEditorPanel | TimeEditorClipTrimToggle | NLA Editor: `transform.transform` (mode='TIME_EXTEND') | 미검토 |  | hotkeySetup.mel:94 |
| r | R | timeEditorPanel | TimeEditorClipScaleToggle | NLA Editor: `transform.transform` (mode='TIME_SCALE') | 미검토 |  | hotkeySetup.mel:95 |
| t | T | timeEditorPanel | TimeEditorClipLoopToggle | — | 미검토 |  | hotkeySetup.mel:96 |
| y | Y | timeEditorPanel | TimeEditorClipHoldToggle | — | 미검토 |  | hotkeySetup.mel:97 |
| s | S | timeEditorPanel | TimeEditorSetKey | — | 미검토 |  | hotkeySetup.mel:98 |
| d | D | timeEditorPanel | TimeEditorSetZeroKey | — | 미검토 |  | hotkeySetup.mel:99 |
| m | M | timeEditorPanel | TimeEditorToggleMuteSelectedTracks | NLA Editor: `nla.mute_toggle`; NLA Editor: `marker.add` | 미검토 |  | hotkeySetup.mel:101 |
| n | N | timeEditorPanel | TimeEditorToggleSoloSelectedTracks | — | 미검토 |  | hotkeySetup.mel:102 |
| Alt+n | Alt+N | timeEditorPanel | TimeEditorAddToSoloSelectedTracks | — | 미검토 |  | hotkeySetup.mel:103 |
| b | B | timeEditorPanel | TimeEditorGhostTrackToggle | — | 미검토 |  | hotkeySetup.mel:104 |
| k | K | timeEditorPanel | TimeEditorToggleTimeCursorPress / TimeEditorToggleTimeCursorRelease (release) | Screen: `maya_kit.tap_hold` (binding='time_drag') | 미검토 |  | hotkeySetup.mel:106 |
| Ctrl+g | Ctrl+G | timeEditorPanel | TimeEditorCreateGroupFromSelection | NLA Editor: `nla.meta_add` | 미검토 |  | hotkeySetup.mel:108 |
| Ctrl+Shift+G | Ctrl+Shift+G | timeEditorPanel | TimeEditorExplodeGroup | — | 미검토 |  | hotkeySetup.mel:109 |
| Ctrl+e | Ctrl+E | timeEditorPanel | TimeEditorExportSelection | — | 미검토 |  | hotkeySetup.mel:111 |
| Shift+I | Shift+I | timeEditorPanel | TimeEditorCreateAudioClip | — | 미검토 |  | hotkeySetup.mel:112 |
| i | I | timeEditorPanel | TimeEditorImportAnimation | — | 미검토 |  | hotkeySetup.mel:114 |
| o | O | timeEditorPanel | TimeEditorCreateClip | — | 미검토 |  | hotkeySetup.mel:115 |
| p | P | timeEditorPanel | TimeEditorCreatePoseClip | — | 미검토 |  | hotkeySetup.mel:116 |
| u | U | timeEditorPanel | TimeEditorRippleEditTogglePress / TimeEditorRippleEditToggleRelease (release) | NLA Editor: `nla.make_single_user` | 미검토 |  | hotkeySetup.mel:117 |
| g | G | timeEditorPanel | TimeEditorClipTrimStart | Screen: `screen.repeat_last` | 미검토 |  | hotkeySetup.mel:118 |
| h | H | timeEditorPanel | TimeEditorClipTrimEnd | — | 미검토 |  | hotkeySetup.mel:119 |
| Shift+G | Shift+G | timeEditorPanel | TimeEditorClipScaleStart | — | 미검토 |  | hotkeySetup.mel:120 |
| Shift+H | Shift+H | timeEditorPanel | TimeEditorClipScaleEnd | — | 미검토 |  | hotkeySetup.mel:121 |
| l | L | timeEditorPanel | TimeEditorCreateAdditiveLayer | — | 미검토 |  | hotkeySetup.mel:122 |
| Shift+L | Shift+L | timeEditorPanel | TimeEditorCreateOverrideLayer | — | 미검토 |  | hotkeySetup.mel:123 |
| Ctrl+c | Ctrl+C | timeEditorPanel | TimeEditorCopyClips | — | 미검토 |  | hotkeySetup.mel:126 |
| Ctrl+x | Ctrl+X | timeEditorPanel | TimeEditorCutClips | — | 미검토 |  | hotkeySetup.mel:127 |
| Delete | DEL | timeEditorPanel | TimeEditorDeleteClips | NLA Editor: `nla.delete` | 미검토 |  | hotkeySetup.mel:128 |
| Ctrl+v | Ctrl+V | timeEditorPanel | TimeEditorPasteClips | — | 미검토 |  | hotkeySetup.mel:129 |
| a | A | timeEditorPanel | TimeEditorFrameAll | NLA Editor: `nla.view_all` | 미검토 |  | hotkeySetup.mel:134 |
| f | F | timeEditorPanel | TimeEditorFrameSelected | NLA Editor: `nla.view_selected` | 미검토 |  | hotkeySetup.mel:135 |
| g | G | timeEditorPanel | TimeEditorFramePlaybackRange | Screen: `screen.repeat_last` | 미검토 |  | hotkeySetup.mel:136 |
| y | Y | timeEditorPanel | TimeEditorFrameCenterView | — | 미검토 |  | hotkeySetup.mel:137 |
| x | X | timeEditorPanel | TimeEditorToggleSnapToClipPress / TimeEditorToggleSnapToClipRelease (release) | — | 미검토 |  | hotkeySetup.mel:138 |
| a | A | graphEditor | GraphEditorFrameAll | Graph Editor: `graph.view_all` | IC 일치 |  | hotkeySetup.mel:144 |
| f | F | graphEditor | GraphEditorFrameSelected | Graph Editor: `graph.view_selected` | IC 일치 |  | hotkeySetup.mel:145 |
| g | G | graphEditor | GraphEditorFramePlaybackRange | Graph Editor: `anim.scene_range_frame`; Screen: `screen.repeat_last` | 구현 | 재생 범위 (preview 켜져 있으면 그 범위) 로 가로 맞춤 | hotkeySetup.mel:146 |
| t | T | graphEditor | GraphEditorFrameCenterView | — | 미검토 |  | hotkeySetup.mel:147 |
| 1 | ONE | graphEditor | GraphEditorAbsoluteView | — | 미검토 |  | hotkeySetup.mel:148 |
| 2 | TWO | graphEditor | GraphEditorStackedView | — | 미검토 |  | hotkeySetup.mel:149 |
| 3 | THREE | graphEditor | GraphEditorNormalizedView | — | 미검토 |  | hotkeySetup.mel:150 |
| d | D | graphEditor | TangentAuto | Graph Editor: `maya_kit.set_tangent` (kind='AUTO') | 구현 | 선택 키 = Bezier + Auto Clamped | hotkeySetup.mel:151 |
| h | H | graphEditor | GraphEditorLockChannel | — | 미검토 |  | hotkeySetup.mel:152 |
| j | J | graphEditor | GraphEditorUnlockChannel | — | 미검토 |  | hotkeySetup.mel:153 |
| l | L | graphEditor | GraphEditorValueLinesToggle | — | 미검토 |  | hotkeySetup.mel:154 |
| Cmd+Shift+A | Shift+Oskey+A | global | SelectAll | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:166 |
| Cmd+Shift+C | Shift+Oskey+C | global | CreateCameraFromView | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:167 |
| Cmd+d | Oskey+D | global | Duplicate | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:169 |
| Cmd+Shift+D | Shift+Oskey+D | global | DuplicateSpecial | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:170 |
| Cmd+z | Oskey+Z | global | Undo | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:172 |
| Cmd+Shift+Z | Shift+Oskey+Z | global | Redo | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:173 |
| Cmd+q | Oskey+Q | global | Quit | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:175 |
| Cmd+w | Oskey+W | global | CloseFrontWindow | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:177 |
| Cmd+i | Oskey+I | global | Import | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:179 |
| Home | HOME | global | EnterEditMode | 3D View: `maya_kit.view_home` | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:181 |
| Cmd+o | Oskey+O | global | OpenScene | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:183 |
| Cmd+n | Oskey+N | global | NewScene | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:184 |
| Cmd+s | Oskey+S | global | SaveScene | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:185 |
| Cmd+Shift+S | Shift+Oskey+S | global | SaveSceneAs | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:186 |
| Alt+Cmd+s | Alt+Oskey+S | global | IncrementAndSave | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:187 |
| Cmd+r | Oskey+R | global | CreateReference | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:188 |
| Cmd+g | Oskey+G | global | Group | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:189 |
| Cmd+y | Oskey+Y | global | RepeatLast | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:191 |
| Cmd+Shift+I | Shift+Oskey+I | global | InvertSelection | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:193 |
| Cmd+Shift+? | Shift+Oskey+SLASH | global | Help | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:195 |
| Cmd+x | Oskey+X | global | CutSelected | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:198 |
| Cmd+c | Oskey+C | global | CopySelected | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:199 |
| Cmd+v | Oskey+V | global | PasteSelected | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:200 |
| Cmd+Up | Oskey+UP_ARROW | global | IncreaseCheckerDensity | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:202 |
| Cmd+Down | Oskey+DOWN_ARROW | global | DecreaseCheckerDensity | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:203 |
| Cmd+g | Oskey+G | timeEditorPanel | TimeEditorCreateGroupFromSelection | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:206 |
| Cmd+Shift+G | Shift+Oskey+G | timeEditorPanel | TimeEditorExplodeGroup | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:207 |
| Cmd+e | Oskey+E | timeEditorPanel | TimeEditorExportSelection | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:209 |
| Cmd+c | Oskey+C | timeEditorPanel | TimeEditorCopyClips | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:211 |
| Cmd+x | Oskey+X | timeEditorPanel | TimeEditorCutClips | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:212 |
| Cmd+v | Oskey+V | timeEditorPanel | TimeEditorPasteClips | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:213 |
| Ctrl+y | Ctrl+Y | global | Redo | Screen: `ed.redo` | 구현 |  | hotkeySetup.mel:223 |
| Insert | INSERT | global | EnterEditMode | Object Mode: `maya_kit.pivot_toggle`; Mesh: `maya_kit.pivot_toggle` | 구현 | 피벗 편집 토글: 오브젝트 모드 = Translate 불변 (step 59); 편집 모드 = 3D 커서 피벗 + 커서 툴, 면 클릭 방향 = Maya Pivot (step 77) | hotkeySetup.mel:225 |
| a | A | global | SelectAllMarkingMenu / SelectAllMarkingMenuPopDown (release) | 3D View: `maya_kit.tap_hold` (binding='select_all') | 구현 | 탭=Frame All, 홀드+클릭=선택 메뉴 (마킹메뉴 엔진은 Step 9) | hotkeySetup.mel:228 |
| Shift+A | Shift+A | global | FrameAllInAllViews | 3D View: `maya_kit.frame_all_views` (selected=False) | 구현 | 창의 모든 3D 뷰(쿼드 포함) | hotkeySetup.mel:229 |
| Ctrl+a | Ctrl+A | global | ShowAttributeEditorOrChannelBox | Object Mode: `maya_kit.ae_toggle`; Mesh: `mesh.select_all` (action='SELECT') | 구현 | 사이드바 Channel Box 탭 안에서 CB/LE ↔ AE 전환 | hotkeySetup.mel:230 |
| f | F | global | FrameSelectedWithoutChildren | 3D View: `maya_kit.frame` (selected=True) | 구현 | Maya 여백 0.95, 사이드바 밑 제외, 선택 없으면 전체 (step 17) | hotkeySetup.mel:231 |
| Shift+F | Shift+F | global | FrameSelectedWithoutChildrenInAllViews | 3D View: `maya_kit.frame_all_views` (selected=True) | 구현 | 창의 모든 3D 뷰(쿼드 포함) | hotkeySetup.mel:232 |
| Ctrl+Shift+F | Ctrl+Shift+F | global | FrameSelectedInAllViews | 3D View: `maya_kit.frame_all_views` (selected=True, children=True) | 구현 | 자식 포함, 창의 모든 3D 뷰 | hotkeySetup.mel:233 |
| [ | LEFT_BRACKET | global | UndoViewChange | 3D View: `maya_kit.view_history` (direction='UNDO') | 구현 | 뷰 전용 스택 (씬 언두와 별개) | hotkeySetup.mel:234 |
| ] | RIGHT_BRACKET | global | RedoViewChange | 3D View: `maya_kit.view_history` (direction='REDO') | 구현 |  | hotkeySetup.mel:235 |
| Alt+z | Alt+Z | global | UndoViewChange | 3D View: `maya_kit.view_history` (direction='UNDO') | 구현 | 뷰 전용 스택 (씬 언두와 별개) | hotkeySetup.mel:236 |
| Alt+y | Alt+Y | global | RedoViewChange | 3D View: `maya_kit.view_history` (direction='REDO') | 구현 |  | hotkeySetup.mel:237 |
| Home | HOME | global | GoToDefaultView | 3D View: `maya_kit.view_home` | 구현 | Maya 새 씬 persp 자리 (정사영: 방향 유지, 원점) — step 27 | hotkeySetup.mel:238 |
| Shift+{ | Shift+LEFT_BRACKET | global | PreviousViewArrangement | Object Mode: `object.select_hierarchy` (direction='PARENT', extend=True) | 미검토 |  | hotkeySetup.mel:239 |
| Shift+} | Shift+RIGHT_BRACKET | global | NextViewArrangement | Object Mode: `object.select_hierarchy` (direction='CHILD', extend=True) | 미검토 |  | hotkeySetup.mel:240 |
| Alt+p | Alt+P | global | CameraModeToggle | — | 미검토 |  | hotkeySetup.mel:241 |
| Alt+Home | Alt+HOME | global | AppHome | — | 미검토 |  | hotkeySetup.mel:243 |
| Shift+D | Shift+D | global | DuplicateWithTransform | Object Mode: `maya_kit.duplicate_with_transform` | 구현 | 직전 복제의 변환을 반복 | hotkeySetup.mel:245 |
| Alt+Shift+D | Alt+Shift+D | global | DeleteHistory | Object Mode: `maya_kit.delete_history` | 구현 | 모디파이어 + 셰이프 키를 메시에 굽기 | hotkeySetup.mel:247 |
| p | P | global | Parent | Object Mode: `maya_kit.parent` | 구현 | 월드 유지, parent inverse 단위행렬 (환경설정 Parent Mode=Blender 로 IC 방식); 포즈·아마추어 편집 모드 = `maya_kit.parent_joint` (조인트, 제자리) — step 57 | hotkeySetup.mel:249 |
| Shift+P | Shift+P | global | Unparent | Object Mode: `maya_kit.unparent` | 구현 | 월드로, 월드 유지; 포즈·아마추어 편집 모드 = `maya_kit.unparent_joint` (step 57) | hotkeySetup.mel:250 |
| F8 | F8 | global | SelectToggleMode | Object Non-modal: `maya_kit.toggle_sel_mode` | 구현 | 오브젝트 ↔ 마지막 컴포넌트 모드 | hotkeySetup.mel:251 |
| F9 | F9 | global | SelectVertexMask | Object Non-modal: `maya_kit.component_mode` (type='VERT') | 구현 |  | hotkeySetup.mel:253 |
| F10 | F10 | global | SelectEdgeMask | Object Non-modal: `maya_kit.component_mode` (type='EDGE') | 구현 |  | hotkeySetup.mel:254 |
| F11 | F11 | global | SelectFacetMask | Object Non-modal: `maya_kit.component_mode` (type='FACE') | 구현 |  | hotkeySetup.mel:255 |
| F12 | F12 | global | SelectUVMask | Object Mode: `maya_kit.uv_component` (mode='UV'); Mesh: `maya_kit.uv_component` (mode='UV') | 구현 | UV Editor 를 열고 (편집 모드) UV 선택 = UV Sync 끔 + UV 정점 (step 66) | hotkeySetup.mel:256 |
| Alt+F9 | Alt+F9 | global | SelectVertexFaceMask | — | 해당 없음 | Blender 에 vertex-face 컴포넌트 없음 | hotkeySetup.mel:257 |
| Alt+F12 | Alt+F12 | global | SelectMeshUVShell | Object Mode: `maya_kit.uv_component` (mode='SHELL'); Mesh: `maya_kit.uv_component` (mode='SHELL') | 구현 | UV Editor 를 열고 UV Shell = Blender UV 섬 모드 (step 66) | hotkeySetup.mel:258 |
| F7 | F7 | global | SelectMultiComponentMask | Object Non-modal: `maya_kit.component_mode` (type='MULTI') | 구현 | 정점·엣지·면 동시 선택 모드 | hotkeySetup.mel:259 |
| Ctrl+F9 | Ctrl+F9 | global | ConvertSelectionToVertices | Mesh: `maya_kit.convert_selection` (type='VERT') | 구현 |  | hotkeySetup.mel:262 |
| Ctrl+F10 | Ctrl+F10 | global | ConvertSelectionToEdges | Mesh: `maya_kit.convert_selection` (type='EDGE') | 구현 | 닿는 엣지 (면 -> 테두리 엣지) | hotkeySetup.mel:263 |
| Ctrl+F11 | Ctrl+F11 | global | ConvertSelectionToFaces | Mesh: `maya_kit.convert_selection` (type='FACE') | 구현 | 닿는 면 (Blender 모드 전환은 포함된 면만) | hotkeySetup.mel:264 |
| Ctrl+F12 | Ctrl+F12 | global | ConvertSelectionToUVs | — | 해당 없음 | 3D 뷰 UV 컴포넌트 없음 (UV Editor 사용) | hotkeySetup.mel:265 |
| Shift+> | Shift+PERIOD | global | GrowPolygonSelectionRegion | Mesh: `mesh.select_more` | 구현 |  | hotkeySetup.mel:266 |
| Ctrl+Shift+> | Ctrl+Shift+PERIOD | global | GrowLoopPolygonSelectionRegion | Mesh: `mesh.select_next_item` | 구현 | 선택 순서 따라 한 칸 (루프 확장 근사) | hotkeySetup.mel:267 |
| Shift+< | Shift+COMMA | global | ShrinkPolygonSelectionRegion | Mesh: `mesh.select_less` | 구현 |  | hotkeySetup.mel:268 |
| Ctrl+Shift+< | Ctrl+Shift+COMMA | global | ShrinkLoopPolygonSelectionRegion | Mesh: `mesh.select_prev_item` | 구현 | 선택 순서 따라 한 칸 되돌림 (근사) | hotkeySetup.mel:269 |
| h | H | global | ToggleVisibilityAndKeepSelection | Object Mode: `maya_kit.visibility` (action='TOGGLE') | 구현 | 숨긴 객체를 '선택 유지' 표시로 기억, 다시 h = 보이고 선택 (오브젝트 모드) | hotkeySetup.mel:271 |
| x | X | global | SnapToGridPress / SnapToGridRelease (release) | 3D View: `maya_kit.hold` (name='grid') | 구현 | 누르는 동안 GRID 스냅 (절대 그리드 선, 매니퓰레이터 중심), 놓으면 복원 — step 59 | hotkeySetup.mel:272 |
| Shift+X | Shift+X | global | SnapToGridPress / SnapToGridRelease (release) | 3D View: `maya_kit.hold` (name='grid') | 구현 | 누르는 동안 GRID 스냅 (절대 그리드 선, 매니퓰레이터 중심), 놓으면 복원 — step 59 | hotkeySetup.mel:273 |
| Ctrl+h | Ctrl+H | global | HideSelectedObjects | Object Mode: `maya_kit.visibility` (action='HIDE'); Mesh: `mesh.hide` (unselected=False) | 구현 | 컴포넌트: Mesh mesh.hide (IC) | hotkeySetup.mel:274 |
| Shift+H | Shift+H | global | ShowSelectedObjects | Object Mode: `maya_kit.visibility` (action='SHOW_SELECTED'); Mesh: `mesh.reveal` | 구현 | h 로 숨긴 선택 + 숨겨진 활성 객체; 컴포넌트: mesh.reveal | hotkeySetup.mel:275 |
| Ctrl+Shift+H | Ctrl+Shift+H | global | ShowLastHidden | Object Mode: `maya_kit.visibility` (action='SHOW_LAST'); Mesh: `mesh.reveal` | 구현 | 킷 숨김 동작(h/Ctrl+H/Alt+H)의 마지막 대상; 컴포넌트: mesh.reveal | hotkeySetup.mel:276 |
| Alt+h | Alt+H | global | HideUnselectedObjects | Object Mode: `maya_kit.visibility` (action='HIDE_UNSELECTED'); Mesh: `mesh.hide` (unselected=True) | 구현 | 컴포넌트: mesh.hide(unselected) | hotkeySetup.mel:277 |
| Ctrl+Alt+h | Ctrl+Alt+H | global | ShowAllPolyComponents | Mesh: `mesh.reveal` | 구현 |  | hotkeySetup.mel:278 |
| c | C | global | SnapToCurvePress / SnapToCurveRelease (release) | 3D View: `maya_kit.hold` (name='curve') | 구현 | 누르는 동안 EDGE 스냅 (커브 전용 없음, 근사) | hotkeySetup.mel:279 |
| Shift+C | Shift+C | global | SnapToCurvePress / SnapToCurveRelease (release) | 3D View: `maya_kit.hold` (name='curve') | 구현 | 누르는 동안 EDGE 스냅 (커브 전용 없음, 근사) | hotkeySetup.mel:280 |
| v | V | global | SnapToPointPress / SnapToPointRelease (release) | 3D View: `maya_kit.hold` (name='point') | 구현 | 누르는 동안 VERTEX 스냅 (매니퓰레이터 중심이 정점에) — step 59 | hotkeySetup.mel:281 |
| Shift+V | Shift+V | global | SnapToPointPress / SnapToPointRelease (release) | 3D View: `maya_kit.hold` (name='point') | 구현 | 누르는 동안 VERTEX 스냅 (매니퓰레이터 중심이 정점에) — step 59 | hotkeySetup.mel:282 |
| q | Q | global | SelectToolOptionsMarkingMenu / SelectToolOptionsMarkingMenuPopDown (release) | Object Mode: `maya_kit.tap_hold` (binding='tool_select'); Mesh: `maya_kit.tap_hold` (binding='tool_select') | 구현 | 누름=툴 전환, 누른 채 LMB=Select 옵션 마킹메뉴(파이, Step 8) | hotkeySetup.mel:285 |
| Shift+Q | Shift+Q | global | SelectComponentToolMarkingMenu / SelectComponentToolMarkingMenuPopDown (release) | — | 미검토 |  | hotkeySetup.mel:286 |
| Alt+q | Alt+Q | global | SelectPolygonToolMarkingMenu / SelectPolygonToolMarkingMenuPopDown (release) | — | 미검토 |  | hotkeySetup.mel:287 |
| Alt+m | Alt+M | global | FullHotboxDisplay | — | 미검토 |  | hotkeySetup.mel:288 |
| Ctrl+m | Ctrl+M | global | ToggleMainMenubar | — | 미검토 |  | hotkeySetup.mel:289 |
| Shift+M | Shift+M | global | TogglePanelMenubar | — | 미검토 |  | hotkeySetup.mel:290 |
| Ctrl+Shift+M | Ctrl+Shift+M | global | ToggleModelEditorBars | — | 미검토 |  | hotkeySetup.mel:291 |
| Shift+J | Shift+J | global | MoveRotateScaleToolToggleSnapRelativeMode / MoveRotateScaleToolToggleSnapRelativeMode (release) | 3D View: `maya_kit.hold` (name='step') | 구현 | J 와 동일 (INCREMENT 는 상대 증분) | hotkeySetup.mel:294 |
| j | J | global | MoveRotateScaleToolToggleSnapMode / MoveRotateScaleToolToggleSnapMode (release) | 3D View: `maya_kit.hold` (name='step') | 구현 | 누르는 동안 INCREMENT 스냅 | hotkeySetup.mel:295 |
| Cmd+F9 | Oskey+F9 | global | ConvertSelectionToVertices | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:298 |
| Cmd+F10 | Oskey+F10 | global | ConvertSelectionToEdges | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:299 |
| Cmd+F11 | Oskey+F11 | global | ConvertSelectionToFaces | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:300 |
| Cmd+F12 | Oskey+F12 | global | ConvertSelectionToUVs | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:301 |
| Cmd+Shift+H | Shift+Oskey+H | global | ShowLastHidden | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:303 |
| w | W | global | TranslateToolWithSnapMarkingMenu / TranslateToolWithSnapMarkingMenuPopDown (release) | Object Mode: `maya_kit.tap_hold` (binding='tool_move'); Mesh: `maya_kit.tap_hold` (binding='tool_move') | 구현 | 누름=툴 전환, 누른 채 LMB=Move 옵션 마킹메뉴(파이, Step 8) | hotkeySetup.mel:307 |
| e | E | global | RotateToolWithSnapMarkingMenu / RotateToolWithSnapMarkingMenuPopDown (release) | Object Mode: `maya_kit.tap_hold` (binding='tool_rotate'); Mesh: `maya_kit.tap_hold` (binding='tool_rotate') | 구현 | 누름=툴 전환, 누른 채 LMB=Rotate 옵션 마킹메뉴(파이, Step 8) | hotkeySetup.mel:309 |
| r | R | global | ScaleToolWithSnapMarkingMenu / ScaleToolWithSnapMarkingMenuPopDown (release) | Object Mode: `maya_kit.tap_hold` (binding='tool_scale'); Mesh: `maya_kit.tap_hold` (binding='tool_scale') | 구현 | 누름=툴 전환, 누른 채 LMB=Scale 옵션 마킹메뉴(파이, Step 8) | hotkeySetup.mel:311 |
| Ctrl+t | Ctrl+T | global | UniversalManip | Object Mode: `wm.tool_set_by_id` (name='builtin.transform'); Mesh: `wm.tool_set_by_id` (name='builtin.transform') | 구현 |  | hotkeySetup.mel:313 |
| t | T | global | ShowManipulators | Object Mode: `wm.tool_set_by_id` (name='builtin.transform', cycle=True); Mesh: `wm.tool_set_by_id` (name='builtin.transform', cycle=True) | IC 일치 | Blender 에 Show Manipulator 툴 없음: Transform 툴 | hotkeySetup.mel:315 |
| y | Y | global | NonSacredTool | Object Mode: `maya_kit.last_tool`; Mesh: `maya_kit.last_tool` | 구현 | Q/W/E/R/T 가 아닌 마지막 툴 (모드별 기억) | hotkeySetup.mel:316 |
| Ctrl+Shift+Q | Ctrl+Shift+Q | global | QuadDrawToolNameCommand | Object Mode: `maya_kit.menu_tool` (tool='builtin.poly_build', edit=True); Mesh: `maya_kit.menu_tool` (tool='builtin.poly_build', edit=True) | 구현 | Poly Build, 오브젝트 모드면 편집 모드로 | hotkeySetup.mel:319 |
| Ctrl+Shift+X | Ctrl+Shift+X | global | MultiCutToolNameCommand | Object Mode: `maya_kit.menu_tool` (tool='builtin.knife', edit=True); Mesh: `maya_kit.menu_tool` (tool='builtin.knife', edit=True) | 구현 | Knife, 오브젝트 모드면 편집 모드로; 툴 안 Ctrl+클릭 = 엣지 루프 (Ctrl+MMB 가운데), Shift = Snap Step % (step 64) | hotkeySetup.mel:320 |
| F2 | F2 | global | ShowModelingUI | Screen: `maya_kit.menu_set` (set='modelingMenuSet') | 구현 | 메뉴 세트 전환 (IC 3D 뷰 F2–F5 뷰 키 대신; 직교 뷰는 핫박스·Space·Ctrl+F1–F3) | hotkeySetup.mel:322 |
| F3 | F3 | global | ShowRiggingUI | Screen: `maya_kit.menu_set` (set='riggingMenuSet') | 구현 | 메뉴 세트 전환 (IC 3D 뷰 F2–F5 뷰 키 대신; 직교 뷰는 핫박스·Space·Ctrl+F1–F3) | hotkeySetup.mel:323 |
| F4 | F4 | global | ShowAnimationUI | Screen: `maya_kit.menu_set` (set='animationMenuSet') | 구현 | 메뉴 세트 전환 (IC 3D 뷰 F2–F5 뷰 키 대신; 직교 뷰는 핫박스·Space·Ctrl+F1–F3) | hotkeySetup.mel:324 |
| F5 | F5 | global | ShowDynamicsUI | Screen: `maya_kit.menu_set` (set='dynamicsMenuSet') | 구현 | 메뉴 세트 전환 (IC 3D 뷰 F2–F5 뷰 키 대신; 직교 뷰는 핫박스·Space·Ctrl+F1–F3) | hotkeySetup.mel:326 |
| F6 | F6 | global | ShowRenderingUI | Screen: `maya_kit.menu_set` (set='renderingMenuSet') | 구현 | 메뉴 세트 전환 (IC 3D 뷰 F2–F5 뷰 키 대신; 직교 뷰는 핫박스·Space·Ctrl+F1–F3) | hotkeySetup.mel:327 |
| s | S | global | SetKey | Object Mode: `maya_kit.set_key` | 구현 | 키 가능한 모든 채널 (가시성·커스텀 포함, Hide/Nonkeyable 제외), 포즈 모드 = 선택 본; 활성 Keying Set 이 있으면 그것 (step 56) | hotkeySetup.mel:328 |
| Alt+e | Alt+E | global | HIKPinRotate | Object Mode: `object.rotation_clear` (clear_delta=False) | 해당 없음 | HumanIK 없음 | hotkeySetup.mel:329 |
| Alt+w | Alt+W | global | HIKPinTranslate | Object Mode: `object.location_clear` (clear_delta=False) | 해당 없음 | HumanIK 없음 | hotkeySetup.mel:330 |
| Alt+s | Alt+S | global | HIKSetFullBodyKey | Object Mode: `anim.keyframe_delete_v3d` | 해당 없음 | HumanIK 없음 | hotkeySetup.mel:331 |
| Alt+v | Alt+V | global | PlaybackToggle | Frames: `screen.animation_play` | 구현 |  | hotkeySetup.mel:332 |
| Alt+Shift+V | Alt+Shift+V | global | GoToMinFrame | Frames: `screen.frame_jump` (end=False) | 구현 |  | hotkeySetup.mel:333 |
| k | K | global | TimeDraggerToolActivate / TimeDraggerToolDeactivate (release) | Screen: `maya_kit.tap_hold` (binding='time_drag') | 구현 | K 누른 채 LMB 드래그 = 시간 (어느 에디터든), 선택 그대로; Mesh knife K → Multi-Cut 은 Ctrl+Shift+X (step 56) | hotkeySetup.mel:334 |
| i | I | global | InsertKeyToolActivate / InsertKeyToolDeactivate (release) | Mesh: `wm.tool_set_by_id` (name='builtin.inset_faces', cycle=True) | 미검토 |  | hotkeySetup.mel:335 |
| 0 | ZERO | global | DefaultQualityDisplay | Object Mode: `maya_kit.smooth_preview` (level=1); Mesh: `maya_kit.smooth_preview` (level=1) | 구현 | 1 과 같음 (거친 표시) — step 27 | hotkeySetup.mel:336 |
| 1 | ONE | global | LowQualityDisplay | Object Mode: `maya_kit.smooth_preview` (level=1); Mesh: `maya_kit.smooth_preview` (level=1) | 구현 | Subsurf 뷰포트 끔 | hotkeySetup.mel:337 |
| 2 | TWO | global | MediumQualityDisplay | Object Mode: `maya_kit.smooth_preview` (level=2); Mesh: `maya_kit.smooth_preview` (level=2) | 구현 | Subsurf + 와이어 (케이지 근사) | hotkeySetup.mel:338 |
| 3 | THREE | global | HighQualityDisplay | Object Mode: `maya_kit.smooth_preview` (level=3); Mesh: `maya_kit.smooth_preview` (level=3) | 구현 | Subsurf 뷰포트 켬 (없으면 추가, 렌더 영향 없음) | hotkeySetup.mel:339 |
| Alt+3 | Alt+THREE | global | ToggleDisplacement | — | 미검토 |  | hotkeySetup.mel:340 |
| 4 | FOUR | global | DisplayWireframe | 3D View: `maya_kit.display_mode` (mode='WIREFRAME') | 구현 |  | hotkeySetup.mel:341 |
| 5 | FIVE | global | DisplayShaded | 3D View: `maya_kit.display_mode` (mode='SHADED') | 구현 |  | hotkeySetup.mel:342 |
| 6 | SIX | global | DisplayShadedAndTextured | 3D View: `maya_kit.display_mode` (mode='TEXTURED') | 구현 |  | hotkeySetup.mel:343 |
| 7 | SEVEN | global | DisplayLight | 3D View: `maya_kit.display_mode` (mode='LIGHTS') | 구현 | Material Preview + 씬 라이트 (근사) | hotkeySetup.mel:344 |
| Ctrl+Shift+% | Ctrl+Shift+FIVE | global | ToggleUseDefaultMaterial | — | 미검토 |  | hotkeySetup.mel:345 |
| Ctrl+1 | Ctrl+ONE | global | ToggleIsolateSelect | 3D View: `view3d.localview` (frame_selected=False) | 구현 | 로컬 뷰 (카메라 그대로), 다시 누르면 해제 | hotkeySetup.mel:346 |
| Alt+a | Alt+A | global | CycleDisplayMode | — | 미검토 |  | hotkeySetup.mel:347 |
| Shift+I | Shift+I | global | SelectIsolate | 3D View: `view3d.localview` | IC 일치 | 로컬 뷰 토글 (프레이밍 포함) | hotkeySetup.mel:351 |
| Space | SPACE | global | ShowHotbox / HideHotbox (release) | 3D View: `maya_kit.hotbox` | 구현 | 홀드=핫박스(메뉴 행·존 마킹메뉴), 탭=4분할↔단일 / 패널 최대화. 재생은 Alt+V | hotkeySetup.mel:352 |
| Return | RET | global | CompleteCurrentTool | Screen: `file.execute` | 해당 없음 | Blender 모달 툴은 자기 키맵의 Return 으로 확정; 3D 뷰의 IC 이름 바꾸기 팝오버는 제거 | hotkeySetup.mel:353 |
| Esc | ESC | global | AbortCurrentTool | Frames: `screen.animation_cancel`; Screen: `file.cancel`; Screen: `render.view_cancel` | 미검토 |  | hotkeySetup.mel:354 |
| d | D | global | EnterEditModePress / EnterEditModeRelease (release) | Object Mode: `maya_kit.hold` (name='pivot'); Mesh: `maya_kit.hold` (name='component_pivot') | 구현 | 오브젝트 모드: 누르는 동안 피벗 편집 (Translate 불변, 자식 제자리, step 59); 편집 모드: 3D 커서 피벗 배치 (step 18), 피벗 방향 = Maya Pivot (step 77) | hotkeySetup.mel:355 |
| Ctrl+Alt+, | Ctrl+Alt+COMMA | global | SelectPreviousKey | — | 미검토 |  | hotkeySetup.mel:356 |
| Ctrl+Alt+. | Ctrl+Alt+PERIOD | global | SelectNextKey | — | 미검토 |  | hotkeySetup.mel:357 |
| , | COMMA | global | PreviousKey | Frames: `screen.keyframe_jump` (next=False) | 구현 | 3D View 방향 파이는 헤더로 | hotkeySetup.mel:358 |
| Alt+, | Alt+COMMA | global | PreviousFrame | Frames: `screen.frame_offset` (delta=-1) | 구현 |  | hotkeySetup.mel:359 |
| . | PERIOD | global | NextKey | Frames: `screen.keyframe_jump` (next=True) | 구현 | Frames 키맵 (대부분 에디터); 3D View 피벗 파이는 헤더로 | hotkeySetup.mel:360 |
| Alt+. | Alt+PERIOD | global | NextFrame | Frames: `screen.frame_offset` (delta=1) | 구현 | 누르고 있으면 반복 | hotkeySetup.mel:361 |
| g | G | global | RepeatLast | Screen: `screen.repeat_last` | IC 일치 |  | hotkeySetup.mel:362 |
| Shift+G | Shift+G | global | RepeatLastActionAtMousePosition | — | 미검토 |  | hotkeySetup.mel:363 |
| Up | UP_ARROW | global | PickWalkUp | Object Mode: `maya_kit.pick_walk` (direction='UP'); Mesh: `maya_kit.pick_walk_component` (direction='UP') | 구현 | 편집 모드: 엣지 = 링, 정점·면 = 화면 위쪽 이웃 (step 39); 포즈 모드: 부모 조인트 (step 57) | hotkeySetup.mel:364 |
| Down | DOWN_ARROW | global | PickWalkDown | Object Mode: `maya_kit.pick_walk` (direction='DOWN'); Mesh: `maya_kit.pick_walk_component` (direction='DOWN') | 구현 | 편집 모드: 엣지 = 링, 정점·면 = 화면 아래쪽 이웃 (step 39); 포즈 모드: 첫 자식 조인트 (step 57) | hotkeySetup.mel:365 |
| Left | LEFT_ARROW | global | PickWalkLeft | Object Mode: `maya_kit.pick_walk` (direction='LEFT'); Mesh: `maya_kit.pick_walk_component` (direction='LEFT') | 구현 | 이름순 형제 순환; 편집 모드: 엣지 = 루프, 정점·면 = 화면 왼쪽 이웃 (step 39); 포즈 모드: 형제 조인트 | hotkeySetup.mel:366 |
| Right | RIGHT_ARROW | global | PickWalkRight | Object Mode: `maya_kit.pick_walk` (direction='RIGHT'); Mesh: `maya_kit.pick_walk_component` (direction='RIGHT') | 구현 | 이름순 형제 순환; 편집 모드: 엣지 = 루프, 정점·면 = 화면 오른쪽 이웃 (step 39); 포즈 모드: 형제 조인트 | hotkeySetup.mel:367 |
| Ctrl+Page_Up | Ctrl+PAGE_UP | global | PickWalkIn | Screen: `screen.workspace_cycle` (direction='PREV') | 미검토 |  | hotkeySetup.mel:368 |
| Ctrl+Page_Down | Ctrl+PAGE_DOWN | global | PickWalkOut | Screen: `screen.workspace_cycle` (direction='NEXT') | 미검토 |  | hotkeySetup.mel:369 |
| Alt+Up | Alt+UP_ARROW | global | MoveUp | — | 미검토 |  | hotkeySetup.mel:370 |
| Alt+Down | Alt+DOWN_ARROW | global | MoveDown | — | 미검토 |  | hotkeySetup.mel:371 |
| Alt+Left | Alt+LEFT_ARROW | global | MoveLeft | — | 미검토 |  | hotkeySetup.mel:372 |
| Alt+Right | Alt+RIGHT_ARROW | global | MoveRight | — | 미검토 |  | hotkeySetup.mel:373 |
| Ctrl+Backspace | Ctrl+BACK_SPACE | global | DeletePolyElements | Mesh: `mesh.dissolve_mode` | IC 일치 | 엣지·정점 dissolve (Delete Edge/Vertex); Delete/Backspace = 바로 삭제 (step 24) | hotkeySetup.mel:375 |
| Ctrl+Delete | Ctrl+DEL | global | DeletePolyElements | Mesh: `mesh.dissolve_mode` | IC 일치 | 엣지·정점 dissolve (Delete Edge/Vertex); Delete/Backspace = 바로 삭제 (step 24) | hotkeySetup.mel:376 |
| Ctrl+Alt+Left | Ctrl+Alt+LEFT_ARROW | global | PolySpinEdgeBackward | — | 미검토 |  | hotkeySetup.mel:378 |
| Ctrl+Alt+Right | Ctrl+Alt+RIGHT_ARROW | global | PolySpinEdgeForward | — | 미검토 |  | hotkeySetup.mel:379 |
| Ctrl+Left | Ctrl+LEFT_ARROW | global | RenderViewNextImage | Object Mode: `screen.frame_jump` (end=False) | 미검토 |  | hotkeySetup.mel:381 |
| Ctrl+Right | Ctrl+RIGHT_ARROW | global | RenderViewPrevImage | Object Mode: `screen.frame_jump` (end=True) | 미검토 |  | hotkeySetup.mel:382 |
| Ctrl+e | Ctrl+E | global | PolyExtrude | Mesh: `maya_kit.extrude` | 구현 | polyExtrudeFace: 길이 0 압출 + 매니퓰레이터·In-View Editor·INPUTS (step 65); 엣지/정점은 압출 + 법선 드래그 | hotkeySetup.mel:384 |
| Ctrl+b | Ctrl+B | global | BevelPolygon | Mesh: `maya_kit.bevel` | 구현 | 정점 모드 = 정점 베벨, 그 외 엣지; 드래그로 폭 | hotkeySetup.mel:385 |
| - | MINUS | global | DecreaseManipulatorSize | 3D View: `maya_kit.manip_size` (factor=0.8) | 구현 |  | hotkeySetup.mel:387 |
| = | EQUAL | global | IncreaseManipulatorSize | 3D View: `maya_kit.manip_size` (factor=1.25) | 구현 | gizmo_size ×1.25 (Maya ×2), 끄면 원래 값 — step 27 | hotkeySetup.mel:388 |
| Shift++ | Shift+EQUAL | global | IncreaseManipulatorSize | 3D View: `maya_kit.manip_size` (factor=1.25) | 구현 | gizmo_size ×1.25 (Maya ×2), 끄면 원래 값 — step 27 | hotkeySetup.mel:389 |
| Alt+Shift+Y | Alt+Shift+Y | global | — | — | 미검토 |  | hotkeySetup.mel:391 |
| Ctrl+Shift+Y | Ctrl+Shift+Y | global | — | — | 미검토 |  | hotkeySetup.mel:392 |
| Ctrl+Alt+Shift+Y | Ctrl+Alt+Shift+Y | global | — | — | 미검토 |  | hotkeySetup.mel:393 |
| Shift+W | Shift+W | global | SetKeyTranslate | Object Mode: `anim.keyframe_insert_by_name` (type='Location') | IC 일치 |  | hotkeySetup.mel:394 |
| Shift+E | Shift+E | global | SetKeyRotate | Object Mode: `anim.keyframe_insert_by_name` (type='Rotation') | IC 일치 |  | hotkeySetup.mel:395 |
| Shift+R | Shift+R | global | SetKeyScale | Object Mode: `anim.keyframe_insert_by_name` (type='Scaling') | IC 일치 |  | hotkeySetup.mel:396 |
| Ctrl+i | Ctrl+I | global | SelectNextIntermediatObject | Object Mode: `object.select_all` (action='INVERT'); Mesh: `mesh.select_all` (action='INVERT') | 미검토 |  | hotkeySetup.mel:398 |
| F1 | F1 | global | Help | 3D View: `view3d.view_axis` (type='FRONT') | 미검토 |  | hotkeySetup.mel:400 |
| Cmd+Shift+X | Shift+Oskey+X | global | MultiCutToolNameCommand | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:403 |
| Cmd+1 | Oskey+ONE | global | ToggleIsolateSelect | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:405 |
| Cmd+Backspace | Oskey+BACK_SPACE | global | DeletePolyElements | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:407 |
| Cmd+Delete | Oskey+DEL | global | DeletePolyElements | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:408 |
| Alt+Cmd+Left | Alt+Oskey+LEFT_ARROW | global | PolySpinEdgeBackward | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:410 |
| Alt+Cmd+Right | Alt+Oskey+RIGHT_ARROW | global | PolySpinEdgeForward | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:411 |
| Cmd+e | Oskey+E | global | PolyExtrude | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:413 |
| Shift+S | Shift+S | global | KeyframeTangentMarkingMenu / KeyframeTangentMarkingMenuPopDown (release) | Object Mode: `maya_kit.tap_hold` (binding='key_tangent') | 구현 | 홀드 + LMB = Keys / Tangents 마킹 메뉴 (Graph Editor·Dope Sheet·포즈도), 탭 = 없음 | hotkeySetup.mel:418 |
| n | N | global | TraversalMarkingMenu / TraversalMarkingMenuPopDown (release) | — | 미검토 |  | hotkeySetup.mel:424 |
| Alt+Shift+< | Alt+Shift+COMMA | global | PreviousGreasePencilFrame | — | 미검토 |  | hotkeySetup.mel:429 |
| Alt+Shift+> | Alt+Shift+PERIOD | global | NextGreasePencilFrame | — | 미검토 |  | hotkeySetup.mel:430 |
| u | U | global | PaintOperationMarkingMenuPress / PaintOperationMarkingMenuRelease (release) | — | 미검토 |  | hotkeySetup.mel:433 |
| b | B | global | ModifyUpperRadiusPress / ModifyUpperRadiusRelease (release) | 3D View: `maya_kit.tap_hold` (binding='soft_select') | 구현 | 탭=소프트 셀렉트 토글, 홀드+LMB 드래그=반경 | hotkeySetup.mel:436 |
| Shift+B | Shift+B | global | ModifyLowerRadiusPress / ModifyLowerRadiusRelease (release) | — | 미검토 |  | hotkeySetup.mel:439 |
| / | SLASH | global | PickColorActivate / PickColorDeactivate (release) | — | 미검토 |  | hotkeySetup.mel:442 |
| n | N | global | ModifyPaintValuePress / ModifyPaintValueRelease (release) | — | 미검토 |  | hotkeySetup.mel:445 |
| Shift+U | Shift+U | global | ModifyUVVectorPress / ModifyUVVectorRelease (release) | — | 미검토 |  | hotkeySetup.mel:448 |
| Alt+f | Alt+F | global | FloodSurfaces | — | 미검토 |  | hotkeySetup.mel:451 |
| Alt+c | Alt+C | global | ToggleColorFeedback | Mesh: `wm.tool_set_by_id` (name='builtin.loop_cut', cycle=True) | 미검토 |  | hotkeySetup.mel:452 |
| Alt+j | Alt+J | global | ToggleMultiColorFeedback | — | 미검토 |  | hotkeySetup.mel:453 |
| Ctrl+Alt+c | Ctrl+Alt+C | global | CopyVertexSkinWeights | — | 미검토 |  | hotkeySetup.mel:454 |
| Ctrl+Alt+v | Ctrl+Alt+V | global | PasteVertexSkinWeights | — | 미검토 |  | hotkeySetup.mel:455 |
| Ctrl+. | Ctrl+PERIOD | global | NextSkinPaintMode | — | 미검토 |  | hotkeySetup.mel:456 |
| Ctrl+, | Ctrl+COMMA | global | PrevSkinPaintMode | Screen: `screen.userpref_show` | 미검토 |  | hotkeySetup.mel:457 |
| o | O | global | PolyBrushMarkingMenu / PolyBrushMarkingMenuPopDown (release) | — | 미검토 |  | hotkeySetup.mel:458 |
| m | M | global | ModifyDisplacementPress / ModifyDisplacementRelease (release) | Object Mode: `wm.tool_set_by_id` (name='builtin.measure', cycle=True); Mesh: `wm.tool_set_by_id` (name='builtin.measure', cycle=True) | 미검토 |  | hotkeySetup.mel:463 |
| Return | RET | outlinerPanel | OutlinerRenameSelectedItem | Outliner: `outliner.item_rename` (use_active=True); Screen: `file.execute` | 미검토 |  | hotkeySetup.mel:467 |
| f | F | outlinerPanel | OutlinerRevealSelected | Outliner: `outliner.show_active` | 미검토 |  | hotkeySetup.mel:468 |
| 1 | ONE | nodeEditorPanel | NodeEditorHideAttributes | — | 미검토 |  | hotkeySetup.mel:471 |
| 2 | TWO | nodeEditorPanel | NodeEditorShowConnectedAttrs | — | 미검토 |  | hotkeySetup.mel:472 |
| 3 | THREE | nodeEditorPanel | NodeEditorShowAllAttrs | — | 미검토 |  | hotkeySetup.mel:473 |
| 4 | FOUR | nodeEditorPanel | NodeEditorShowCustomAttrs | — | 미검토 |  | hotkeySetup.mel:474 |
| 5 | FIVE | nodeEditorPanel | NodeEditorToggleNodeTitleMode | — | 미검토 |  | hotkeySetup.mel:475 |
| p | P | nodeEditorPanel | NodeEditorToggleNodeSelectedPins | Node Editor: `node.parent_set` | 미검토 |  | hotkeySetup.mel:476 |
| v | V | nodeEditorPanel | NodeEditorToggleNodeSwatchSize | — | 미검토 |  | hotkeySetup.mel:477 |
| = | EQUAL | nodeEditorPanel | NodeEditorToggleZoomIn | — | 미검토 |  | hotkeySetup.mel:478 |
| - | MINUS | nodeEditorPanel | NodeEditorToggleZoomOut | — | 미검토 |  | hotkeySetup.mel:479 |
| Shift+C | Shift+C | nodeEditorPanel | NodeEditorToggleSyncedSelection | — | 미검토 |  | hotkeySetup.mel:480 |
| s | S | nodeEditorPanel | NodeEditorToggleAttrFilter | — | 미검토 |  | hotkeySetup.mel:481 |
| x | X | nodeEditorPanel | NodeEditorGridToggleSnap / NodeEditorGridToggleSnap (release) | Node Editor: `wm.context_toggle` (data_path='tool_settings.use_snap_node') | 미검토 |  | hotkeySetup.mel:482 |
| l | L | nodeEditorPanel | NodeEditorLayout | Node Editor: `node.link_make` (replace=False) | 미검토 |  | hotkeySetup.mel:483 |
| / | SLASH | nodeEditorPanel | NodeEditorSelectConnected | — | 미검토 |  | hotkeySetup.mel:484 |
| , | COMMA | nodeEditorPanel | NodeEditorSelectUpStream | — | 미검토 |  | hotkeySetup.mel:485 |
| w | W | nodeEditorPanel | NodeEditorConnectNodeOnCreation | Node Editor: `node.translate_attach`; Node Editor: `transform.translate` | 미검토 |  | hotkeySetup.mel:486 |
| c | C | nodeEditorPanel | NodeEditorConnectSelectedNodes | — | 미검토 |  | hotkeySetup.mel:487 |
| Ctrl+g | Ctrl+G | nodeEditorPanel | NodeEditorCreateCompound | Node Editor: `node.group_make` | 미검토 |  | hotkeySetup.mel:488 |
| . | PERIOD | nodeEditorPanel | NodeEditorSelectDownStream | — | 미검토 |  | hotkeySetup.mel:489 |
| Shift+? | Shift+SLASH | nodeEditorPanel | NodeEditorGraphUpDownstream | — | 미검토 |  | hotkeySetup.mel:490 |
| Shift+< | Shift+COMMA | nodeEditorPanel | NodeEditorGraphUpstream | — | 미검토 |  | hotkeySetup.mel:491 |
| Shift+> | Shift+PERIOD | nodeEditorPanel | NodeEditorGraphDownstream | — | 미검토 |  | hotkeySetup.mel:492 |
| Ctrl+l | Ctrl+L | nodeEditorPanel | NodeEditorGraphRemoveSelected | — | 미검토 |  | hotkeySetup.mel:493 |
| Ctrl+/ | Ctrl+SLASH | nodeEditorPanel | NodeEditorGraphRemoveUnselected | — | 미검토 |  | hotkeySetup.mel:494 |
| Ctrl+, | Ctrl+COMMA | nodeEditorPanel | NodeEditorGraphRemoveUpstream | Screen: `screen.userpref_show` | 미검토 |  | hotkeySetup.mel:495 |
| Ctrl+. | Ctrl+PERIOD | nodeEditorPanel | NodeEditorGraphRemoveDownstream | — | 미검토 |  | hotkeySetup.mel:496 |
| Up | UP_ARROW | nodeEditorPanel | NodeEditorPickWalkUp | — | 미검토 |  | hotkeySetup.mel:497 |
| Down | DOWN_ARROW | nodeEditorPanel | NodeEditorPickWalkDown | — | 미검토 |  | hotkeySetup.mel:498 |
| Right | RIGHT_ARROW | nodeEditorPanel | NodeEditorPickWalkRight | — | 미검토 |  | hotkeySetup.mel:499 |
| Left | LEFT_ARROW | nodeEditorPanel | NodeEditorPickWalkLeft | — | 미검토 |  | hotkeySetup.mel:500 |
| Ctrl+c | Ctrl+C | nodeEditorPanel | NodeEditorCopy | Node Editor: `node.clipboard_copy` | 미검토 |  | hotkeySetup.mel:501 |
| Ctrl+x | Ctrl+X | nodeEditorPanel | NodeEditorCut | — | 미검토 |  | hotkeySetup.mel:502 |
| Ctrl+v | Ctrl+V | nodeEditorPanel | NodeEditorPaste | Node Editor: `node.clipboard_paste` | 미검토 |  | hotkeySetup.mel:503 |
| Cmd+c | Oskey+C | nodeEditorPanel | NodeEditorCopy | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:506 |
| Cmd+x | Oskey+X | nodeEditorPanel | NodeEditorCut | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:507 |
| Cmd+v | Oskey+V | nodeEditorPanel | NodeEditorPaste | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:508 |
| Cmd+g | Oskey+G | nodeEditorPanel | NodeEditorCreateCompound | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:509 |
| i | I | nodeEditorPanel | NodeEditorDiveIntoCompound | — | 미검토 |  | hotkeySetup.mel:511 |
| u | U | nodeEditorPanel | NodeEditorBackToParent | — | 미검토 |  | hotkeySetup.mel:512 |
| Return | RET | nodeEditorPanel | NodeEditorDiveIntoCompound | Node Generic: `wm.call_panel` (name='TOPBAR_PT_name', keep_open=False); Screen: `file.execute` | 미검토 |  | hotkeySetup.mel:513 |
| Delete | DEL | polyTexturePlacementPanel | DeleteUVs | — | 미검토 |  | hotkeySetup.mel:516 |
| Ctrl+c | Ctrl+C | polyTexturePlacementPanel | CopyUVs | UV Editor: `uv.copy` | 미검토 |  | hotkeySetup.mel:517 |
| Ctrl+v | Ctrl+V | polyTexturePlacementPanel | PasteUVs | UV Editor: `uv.paste` | 미검토 |  | hotkeySetup.mel:518 |
| Ctrl+l | Ctrl+L | polyTexturePlacementPanel | LayoutUV | UV Editor: `maya_kit.uv_layout` | 구현 | Pack Islands, 셸 패딩 px / 맵 크기 (IC select_linked 제거) | hotkeySetup.mel:519 |
| Ctrl+u | Ctrl+U | polyTexturePlacementPanel | UnfoldUV | UV Editor: `maya_kit.uv_unfold` | 구현 | Blender Unwrap (Minimum Stretch), 셸 경계·자리 유지 (Unfold3D 아님) | hotkeySetup.mel:520 |
| Shift+x | Shift+X | polyTexturePlacementPanel | CutUVs | UV Editor: `maya_kit.uv_cut` | 구현 | 솔기 + 작은 쪽 셸을 0.2 px 떼어 그 자리에서 분리 (IC 스냅 파이 제거) | hotkeySetup.mel:521 |
| Shift+s | Shift+S | polyTexturePlacementPanel | SewUVs | UV Editor: `maya_kit.uv_sew` | 구현 | 솔기 지움 + 작은 셸을 엣지에 맞춰 옮김 | hotkeySetup.mel:522 |
| Ctrl+Shift+x | Ctrl+Shift+X | polyTexturePlacementPanel | CreateUVShellAlongBorder | — | 미검토 |  | hotkeySetup.mel:523 |
| 4 | FOUR | polyTexturePlacementPanel | DisplayUVWireframe | UV Editor: `uv.select_mode` (type='ISLAND') | 미검토 |  | hotkeySetup.mel:524 |
| 5 | FIVE | polyTexturePlacementPanel | DisplayUVShaded | — | 미검토 |  | hotkeySetup.mel:525 |
| 7 | SEVEN | polyTexturePlacementPanel | ToggleUVDistortion | — | 미검토 |  | hotkeySetup.mel:526 |
| 8 | EIGHT | polyTexturePlacementPanel | ToggleUVShellBorder | — | 미검토 |  | hotkeySetup.mel:527 |
| 9 | NINE | polyTexturePlacementPanel | UVEditorToggleTextureBorderDisplay | — | 미검토 |  | hotkeySetup.mel:528 |
| 6 | SIX | polyTexturePlacementPanel | ToggleUVTextureImage | — | 미검토 |  | hotkeySetup.mel:529 |
| Ctrl+1 | Ctrl+ONE | polyTexturePlacementPanel | ToggleUVIsolateViewSelected | UV Editor: `mesh.select_mode` (use_expand=True, type='VERT') | 미검토 |  | hotkeySetup.mel:530 |
| f | F | polyTexturePlacementPanel | UVEditorFrameSelected | Image: `image.view_selected` | 미검토 |  | hotkeySetup.mel:531 |
| a | A | polyTexturePlacementPanel | UVEditorFrameAll | Image: `image.view_all` | 미검토 |  | hotkeySetup.mel:532 |
| q | Q | polyTexturePlacementPanel | SelectUVTool | UV Editor: `wm.tool_set_by_id` (name='builtin.select_box', cycle=True); Image: `wm.tool_set_by_id` (name='builtin.select_box', cycle=True) | 미검토 |  | hotkeySetup.mel:533 |
| w | W | polyTexturePlacementPanel | MoveUVTool | UV Editor: `wm.tool_set_by_id` (name='builtin.move', cycle=True); Image: `wm.tool_set_by_id` (name='builtin.transform', cycle=True) | 미검토 |  | hotkeySetup.mel:534 |
| e | E | polyTexturePlacementPanel | RotateUVTool | UV Editor: `wm.tool_set_by_id` (name='builtin.rotate', cycle=True); Image: `wm.tool_set_by_id` (name='builtin.transform', cycle=True) | 미검토 |  | hotkeySetup.mel:535 |
| r | R | polyTexturePlacementPanel | ScaleUVTool | UV Editor: `wm.tool_set_by_id` (name='builtin.scale', cycle=True); Image: `wm.tool_set_by_id` (name='builtin.transform', cycle=True) | 미검토 |  | hotkeySetup.mel:536 |
| x | X | polyCutUV | CutUVs3D | — | 미검토 |  | hotkeySetup.mel:539 |
| s | S | polyCutUV | SewUVs3D | — | 미검토 |  | hotkeySetup.mel:540 |
| d | D | polyCutUV | UnfoldPackUVs3DInCurrentTile | — | 미검토 |  | hotkeySetup.mel:541 |
| Shift+d | Shift+D | polyCutUV | UnfoldPackUVs3DInEmptyTile | — | 미검토 |  | hotkeySetup.mel:542 |
| Cmd+c | Oskey+C | polyTexturePlacementPanel | CopyUVs | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:545 |
| Cmd+v | Oskey+V | polyTexturePlacementPanel | PasteUVs | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:546 |
| Cmd+l | Oskey+L | polyTexturePlacementPanel | LayoutUV | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:547 |
| Cmd+u | Oskey+U | polyTexturePlacementPanel | UnfoldUV | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:548 |
| Cmd+Shift+x | Shift+Oskey+X | polyTexturePlacementPanel | CreateUVShellAlongBorder | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:550 |
| Cmd+1 | Oskey+ONE | polyTexturePlacementPanel | ToggleUVIsolateViewSelected | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:551 |
| Ctrl+g | Ctrl+G | shapePanel | ShapeEditorNewGroup | — | 미검토 |  | hotkeySetup.mel:555 |
| Ctrl+d | Ctrl+D | shapePanel | ShapeEditorDuplicateTarget | — | 미검토 |  | hotkeySetup.mel:556 |
| Alt+d | Alt+D | shapePanel | ShapeEditorSelectNone | — | 미검토 |  | hotkeySetup.mel:557 |
| Ctrl+g | Ctrl+G | posePanel | PoseInterpolatorNewGroup | — | 미검토 |  | hotkeySetup.mel:560 |
| 1 | ONE | hyperShadePanel | HypershadeHideAttributes | — | 미검토 |  | hotkeySetup.mel:563 |
| 2 | TWO | hyperShadePanel | HypershadeShowConnectedAttrs | — | 미검토 |  | hotkeySetup.mel:564 |
| 3 | THREE | hyperShadePanel | HypershadeShowAllAttrs | — | 미검토 |  | hotkeySetup.mel:565 |
| 4 | FOUR | hyperShadePanel | HypershadeShowCustomAttrs | — | 미검토 |  | hotkeySetup.mel:566 |
| 5 | FIVE | hyperShadePanel | HypershadeToggleNodeTitleMode | — | 미검토 |  | hotkeySetup.mel:567 |
| p | P | hyperShadePanel | HypershadePinSelected | Node Editor: `node.parent_set` | 미검토 |  | hotkeySetup.mel:568 |
| = | EQUAL | hyperShadePanel | HypershadeToggleZoomIn | — | 미검토 |  | hotkeySetup.mel:569 |
| - | MINUS | hyperShadePanel | HypershadeToggleZoomOut | — | 미검토 |  | hotkeySetup.mel:570 |
| / | SLASH | hyperShadePanel | HypershadeSelectConnected | — | 미검토 |  | hotkeySetup.mel:571 |
| , | COMMA | hyperShadePanel | HypershadeSelectUpStream | — | 미검토 |  | hotkeySetup.mel:572 |
| . | PERIOD | hyperShadePanel | HypershadeSelectDownStream | — | 미검토 |  | hotkeySetup.mel:573 |
| Shift+? | Shift+SLASH | hyperShadePanel | HypershadeGraphUpDownstream | — | 미검토 |  | hotkeySetup.mel:574 |
| Shift+< | Shift+COMMA | hyperShadePanel | HypershadeGraphUpstream | — | 미검토 |  | hotkeySetup.mel:575 |
| Shift+> | Shift+PERIOD | hyperShadePanel | HypershadeGraphDownstream | — | 미검토 |  | hotkeySetup.mel:576 |
| Ctrl+l | Ctrl+L | hyperShadePanel | HypershadeGraphRemoveSelected | — | 미검토 |  | hotkeySetup.mel:577 |
| Ctrl+/ | Ctrl+SLASH | hyperShadePanel | HypershadeGraphRemoveUnselected | — | 미검토 |  | hotkeySetup.mel:578 |
| Ctrl+, | Ctrl+COMMA | hyperShadePanel | HypershadeGraphRemoveUpstream | Screen: `screen.userpref_show` | 미검토 |  | hotkeySetup.mel:579 |
| Ctrl+. | Ctrl+PERIOD | hyperShadePanel | HypershadeGraphRemoveDownstream | — | 미검토 |  | hotkeySetup.mel:580 |
| Up | UP_ARROW | hyperShadePanel | HypershadePickWalkUp | — | 미검토 |  | hotkeySetup.mel:581 |
| Down | DOWN_ARROW | hyperShadePanel | HypershadePickWalkDown | — | 미검토 |  | hotkeySetup.mel:582 |
| Right | RIGHT_ARROW | hyperShadePanel | HypershadePickWalkRight | — | 미검토 |  | hotkeySetup.mel:583 |
| Left | LEFT_ARROW | hyperShadePanel | HypershadePickWalkLeft | — | 미검토 |  | hotkeySetup.mel:584 |
| Shift+! | Shift+ONE | hyperShadePanel | SoloLastOutput | — | 미검토 |  | hotkeySetup.mel:585 |
| Shift+@ | Shift+TWO | hyperShadePanel | SoloMaterial | — | 미검토 |  | hotkeySetup.mel:586 |
| Shift+# | Shift+THREE | hyperShadePanel | RemoveMaterialSoloing | — | 미검토 |  | hotkeySetup.mel:587 |
| Ctrl+0 | Ctrl+ZERO | xgmIGBrush | XgmSetFreezeBrushTool | — | 미검토 |  | hotkeySetup.mel:590 |
| Ctrl+1 | Ctrl+ONE | xgmIGBrush | XgmSetDensityBrushTool | — | 미검토 |  | hotkeySetup.mel:591 |
| Ctrl+2 | Ctrl+TWO | xgmIGBrush | XgmSetCombBrushTool | — | 미검토 |  | hotkeySetup.mel:592 |
| Ctrl+3 | Ctrl+THREE | xgmIGBrush | XgmSetGrabBrushTool | — | 미검토 |  | hotkeySetup.mel:593 |
| Ctrl+5 | Ctrl+FIVE | xgmIGBrush | XgmSetDirectionBrushTool | — | 미검토 |  | hotkeySetup.mel:595 |
| Ctrl+6 | Ctrl+SIX | xgmIGBrush | XgmSetSmoothBrushTool | — | 미검토 |  | hotkeySetup.mel:596 |
| Ctrl+7 | Ctrl+SEVEN | xgmIGBrush | XgmSetNoiseBrushTool | — | 미검토 |  | hotkeySetup.mel:597 |
| Ctrl+8 | Ctrl+EIGHT | xgmIGBrush | XgmSetClumpBrushTool | — | 미검토 |  | hotkeySetup.mel:598 |
| Ctrl+9 | Ctrl+NINE | xgmIGBrush | XgmSetPartBrushTool | — | 미검토 |  | hotkeySetup.mel:599 |
| Alt+r | Alt+R | global | ToggleReflection | Object Mode: `object.scale_clear` (clear_delta=False) | 미검토 |  | hotkeySetup.mel:602 |
| Shift+U | Shift+U | sculptMeshCache | SculptMeshUnfreezeAll | — | 미검토 |  | hotkeySetup.mel:604 |
| Ctrl+Shift+I | Ctrl+Shift+I | sculptMeshCache | SculptMeshInvertFreeze | — | 미검토 |  | hotkeySetup.mel:605 |
| Ctrl+0 | Ctrl+ZERO | sculptMeshCache | SetMeshFreezeTool | — | 미검토 |  | hotkeySetup.mel:607 |
| Ctrl+1 | Ctrl+ONE | sculptMeshCache | SetMeshSculptTool | — | 미검토 |  | hotkeySetup.mel:608 |
| Ctrl+2 | Ctrl+TWO | sculptMeshCache | SetMeshSmoothTool | — | 미검토 |  | hotkeySetup.mel:609 |
| Ctrl+3 | Ctrl+THREE | sculptMeshCache | SetMeshRelaxTool | — | 미검토 |  | hotkeySetup.mel:610 |
| Ctrl+4 | Ctrl+FOUR | sculptMeshCache | SetMeshGrabTool | — | 미검토 |  | hotkeySetup.mel:611 |
| Ctrl+5 | Ctrl+FIVE | sculptMeshCache | SetMeshPinchTool | — | 미검토 |  | hotkeySetup.mel:612 |
| Ctrl+6 | Ctrl+SIX | sculptMeshCache | SetMeshFlattenTool | — | 미검토 |  | hotkeySetup.mel:613 |
| Ctrl+7 | Ctrl+SEVEN | sculptMeshCache | SetMeshFoamyTool | — | 미검토 |  | hotkeySetup.mel:614 |
| Ctrl+8 | Ctrl+EIGHT | sculptMeshCache | SetMeshSprayTool | — | 미검토 |  | hotkeySetup.mel:615 |
| Ctrl+9 | Ctrl+NINE | sculptMeshCache | SetMeshRepeatTool | — | 미검토 |  | hotkeySetup.mel:616 |
| f | F | sculptMeshCache | SculptMeshFrame | — | 미검토 |  | hotkeySetup.mel:618 |
| b | B | sculptMeshCache | SculptMeshActivateBrushSize / SculptMeshDeactivateBrushSize (release) | — | 미검토 |  | hotkeySetup.mel:620 |
| m | M | sculptMeshCache | SculptMeshActivateBrushStrength / SculptMeshDeactivateBrushStrength (release) | — | 미검토 |  | hotkeySetup.mel:621 |
| b | B | texSculptCacheContext | TexSculptActivateBrushSize / TexSculptDeactivateBrushSize (release) | — | 미검토 |  | hotkeySetup.mel:623 |
| m | M | texSculptCacheContext | TexSculptActivateBrushStrength / TexSculptDeactivateBrushStrength (release) | — | 미검토 |  | hotkeySetup.mel:624 |
| b | B | Unfold3DBrush | U3DBrushSizeOn / U3DBrushSizeOff (release) | — | 미검토 |  | hotkeySetup.mel:626 |
| m | M | Unfold3DBrush | U3DBrushPressureOn / U3DBrushPressureOff (release) | — | 미검토 |  | hotkeySetup.mel:627 |
| b | B | SymmetrizeUVBrush | SymmetrizeUVBrushSizeOn / SymmetrizeUVBrushSizeOff (release) | — | 미검토 |  | hotkeySetup.mel:629 |
| b | B | texCutContext | TexSewActivateBrushSize / TexSewDeactivateBrushSize (release) | — | 미검토 |  | hotkeySetup.mel:631 |
| Cmd+g | Oskey+G | shapePanel | ShapeEditorNewGroup | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:635 |
| Cmd+d | Oskey+D | shapePanel | ShapeEditorDuplicateTarget | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:636 |
| Cmd+g | Oskey+G | posePanel | PoseInterpolatorNewGroup | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:639 |
| Cmd+Shift+I | Shift+Oskey+I | sculptMeshCache | SculptMeshInvertFreeze | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:641 |
| Cmd+0 | Oskey+ZERO | sculptMeshCache | SetMeshFreezeTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:642 |
| Cmd+1 | Oskey+ONE | sculptMeshCache | SetMeshSculptTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:643 |
| Cmd+2 | Oskey+TWO | sculptMeshCache | SetMeshSmoothTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:644 |
| Cmd+3 | Oskey+THREE | sculptMeshCache | SetMeshRelaxTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:645 |
| Cmd+4 | Oskey+FOUR | sculptMeshCache | SetMeshGrabTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:646 |
| Cmd+5 | Oskey+FIVE | sculptMeshCache | SetMeshPinchTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:647 |
| Cmd+6 | Oskey+SIX | sculptMeshCache | SetMeshFlattenTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:648 |
| Cmd+7 | Oskey+SEVEN | sculptMeshCache | SetMeshFoamyTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:649 |
| Cmd+8 | Oskey+EIGHT | sculptMeshCache | SetMeshSprayTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:650 |
| Cmd+9 | Oskey+NINE | sculptMeshCache | SetMeshRepeatTool | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:651 |
| Ctrl+Up | Ctrl+UP_ARROW | global | CoarserSubdivLevel | — | 해당 없음 | Maya subdiv surface 노드 없음 | hotkeySetup.mel:655 |
| Ctrl+Down | Ctrl+DOWN_ARROW | global | CreateSubdivRegion | — | 해당 없음 | Maya subdiv surface 노드 없음 | hotkeySetup.mel:656 |
| Alt+Shift+A | Alt+Shift+A | global | DecrementFluidCenter | — | 해당 없음 | Maya Fluids 없음 | hotkeySetup.mel:660 |
| Alt+Shift+S | Alt+Shift+S | global | IncrementFluidCenter | — | 해당 없음 | Maya Fluids 없음 | hotkeySetup.mel:661 |
| Ctrl+Space | Ctrl+SPACE | global | ToggleFullScreenMode | Screen: `screen.screen_full_area` (use_hide_panels=True) | 구현 | UI 숨긴 전체 화면 | hotkeySetup.mel:664 |
| Shift+Space | Shift+SPACE | global | ToggleZoomInMode | 3D View Generic: `wm.context_toggle` (data_path='space_data.show_region_asset_shelf') | 미검토 |  | hotkeySetup.mel:666 |
| Alt+b | Alt+B | global | CycleBackgroundColor | — | 미검토 |  | hotkeySetup.mel:669 |
| Ctrl+` | Ctrl+ACCENT_GRAVE | global | SmoothingDisplayToggle | — | 미검토 |  | hotkeySetup.mel:673 |
| Shift+~ | Shift+ACCENT_GRAVE | global | SmoothingDisplayShowBoth | — | 미검토 |  | hotkeySetup.mel:674 |
| Ctrl+Shift+~ | Ctrl+Shift+ACCENT_GRAVE | global | SmoothProxy | — | 미검토 |  | hotkeySetup.mel:675 |
| Alt+` | Alt+ACCENT_GRAVE | global | CreateSubdivSurface | — | 미검토 |  | hotkeySetup.mel:676 |
| Alt+Shift+~ | Alt+Shift+ACCENT_GRAVE | global | CreateSubdivSurfaceOptions | — | 미검토 |  | hotkeySetup.mel:677 |
| Page_Up | PAGE_UP | global | SmoothingLevelIncrease | Object Mode: `maya_kit.smooth_level` (delta=1); Mesh: `maya_kit.smooth_level` (delta=1) | 구현 | 스무스 프리뷰 단계 0–4 — step 27 | hotkeySetup.mel:678 |
| Page_Down | PAGE_DOWN | global | SmoothingLevelDecrease | Object Mode: `maya_kit.smooth_level` (delta=-1); Mesh: `maya_kit.smooth_level` (delta=-1) | 구현 |  | hotkeySetup.mel:679 |
| ` | ACCENT_GRAVE | global | STRSTweakModeOn / STRSTweakModeOff (release) | Object Non-modal: `object.transfer_mode` | 미검토 |  | hotkeySetup.mel:682 |
| l | L | global | LockCurveLength / UnlockCurveLength (release) | — | 미검토 |  | hotkeySetup.mel:686 |
| Alt+g | Alt+G | hyperGraphPanel | HypergraphIncreaseDepth | — | 미검토 |  | hotkeySetup.mel:689 |
| Alt+t | Alt+T | hyperGraphPanel | HypergraphDecreaseDepth | — | 미검토 |  | hotkeySetup.mel:690 |
| Ctrl+Shift+W | Ctrl+Shift+W | global | ToggleSteeringWheel | — | 미검토 |  | hotkeySetup.mel:694 |
| \ | BACK_SLASH | global | TogglePanZoomPress | — | 미검토 |  | hotkeySetup.mel:697 |
| \ | BACK_SLASH | global | — / TogglePanZoomRelease (release) | — | 미검토 |  | hotkeySetup.mel:698 |
| Alt+x | Alt+X | global | WalkContext_Command | 3D View: `view3d.toggle_xray` | 미검토 |  | hotkeySetup.mel:701 |
| Shift+T | Shift+T | global | AssignNewMaterial | Object Mode: `maya_kit.assign_new_material`; Mesh: `maya_kit.assign_new_material` | 구현 | 재질 종류 검색 팝업 → 만들어 지정 (편집 모드 면 선택 = 면에만, step 29) | hotkeySetup.mel:705 |
| Ctrl+= | Ctrl+EQUAL | global | IncreaseExposureFine | — | 미검토 |  | hotkeySetup.mel:708 |
| Ctrl+- | Ctrl+MINUS | global | DecreaseExposureFine | — | 미검토 |  | hotkeySetup.mel:709 |
| Ctrl+' | Ctrl+QUOTE | global | IncreaseGammaFine | — | 미검토 |  | hotkeySetup.mel:710 |
| Ctrl+; | Ctrl+SEMI_COLON | global | DecreaseGammaFine | — | 미검토 |  | hotkeySetup.mel:711 |
| Ctrl+Alt+= | Ctrl+Alt+EQUAL | global | IncreaseExposureCoarse | — | 미검토 |  | hotkeySetup.mel:712 |
| Ctrl+Alt+- | Ctrl+Alt+MINUS | global | DecreaseExposureCoarse | — | 미검토 |  | hotkeySetup.mel:713 |
| Ctrl+Alt+' | Ctrl+Alt+QUOTE | global | IncreaseGammaCoarse | — | 미검토 |  | hotkeySetup.mel:714 |
| Ctrl+Alt+; | Ctrl+Alt+SEMI_COLON | global | DecreaseGammaCoarse | — | 미검토 |  | hotkeySetup.mel:715 |
| Ctrl+p | Ctrl+P | global | ColorPickerNameCommand | — | 미검토 |  | hotkeySetup.mel:716 |
| Ctrl+r | Ctrl+R | profilerPanel | ProfilerToolToggleRecording | — | 미검토 |  | hotkeySetup.mel:719 |
| 1 | ONE | profilerPanel | ProfilerToolCategoryView | — | 미검토 |  | hotkeySetup.mel:720 |
| 2 | TWO | profilerPanel | ProfilerToolCpuView | — | 미검토 |  | hotkeySetup.mel:721 |
| 3 | THREE | profilerPanel | ProfilerToolThreadView | — | 미검토 |  | hotkeySetup.mel:722 |
| Ctrl+f | Ctrl+F | global | SearchEngine | — | 미검토 |  | hotkeySetup.mel:724 |
| Cmd+f | Oskey+F | global | SearchEngine | — | macOS 전용 | Cmd 키 바인딩 (Windows 해당 없음) | hotkeySetup.mel:727 |
| Ctrl+Shift+E | Ctrl+Shift+E | global | InsertKeyRotate | — | 미검토 |  | hotkeySetup.mel:729 |
| Ctrl+Shift+W | Ctrl+Shift+W | global | InsertKeyTranslate | — | 미검토 |  | hotkeySetup.mel:730 |
| Ctrl+Shift+R | Ctrl+Shift+R | global | InsertKeyScale | — | 미검토 |  | hotkeySetup.mel:731 |
| Alt+i | Alt+I | global | InsertKey | — | 미검토 |  | hotkeySetup.mel:732 |
| Alt+/ | Alt+SLASH | graphEditor | SnapTimeToSelection | — | 미검토 |  | hotkeySetup.mel:734 |
| Alt+1 | Alt+ONE | global | ToggleNurbsCurvesOptionCmd | — | 미검토 |  | hotkeySetup.mel:735 |
| Alt+2 | Alt+TWO | global | TogglePolygonsOptionCmd | — | 미검토 |  | hotkeySetup.mel:736 |
| Alt+4 | Alt+FOUR | global | ToggleImagePlaneOptionCmd | — | 미검토 |  | hotkeySetup.mel:737 |
| Alt+5 | Alt+FIVE | global | ToggleWireframeOnShadedCmd | 3D View: `wm.context_toggle` (data_path='space_data.overlay.show_wireframes') | 구현 | 뷰포트 오버레이 Wireframe (모든 오브젝트) — step 27 | hotkeySetup.mel:738 |
| Shift+) | Shift+ZERO | global | NudgeSelectedKeysForward | — | 미검토 |  | hotkeySetup.mel:739 |
| Shift+( | Shift+NINE | global | NudgeSelectedKeysBackward | — | 미검토 |  | hotkeySetup.mel:740 |
| Alt+t | Alt+T | global | CreateTimeSliderBookmark | — | 미검토 |  | hotkeySetup.mel:742 |
| Alt+Shift+T | Alt+Shift+T | global | QuickCreateTimeSliderBookmark | — | 미검토 |  | hotkeySetup.mel:743 |
| Shift+\| | Shift+BACK_SLASH | global | FrameTimeSliderBookmark | — | 미검토 |  | hotkeySetup.mel:744 |
| Shift+" | Shift+QUOTE | global | FrameNextTimeSliderBookmark | — | 미검토 |  | hotkeySetup.mel:745 |
| Shift+: | Shift+SEMI_COLON | global | FramePreviousTimeSliderBookmark | — | 미검토 |  | hotkeySetup.mel:746 |
| Alt+\ | Alt+BACK_SLASH | global | PlaybackRangeAnimStartEnd | — | 미검토 |  | hotkeySetup.mel:747 |
| ' | QUOTE | global | NextTimeSliderBookmark | — | 미검토 |  | hotkeySetup.mel:748 |
| ; | SEMI_COLON | global | PreviousTimeSliderBookmark | — | 미검토 |  | hotkeySetup.mel:749 |
