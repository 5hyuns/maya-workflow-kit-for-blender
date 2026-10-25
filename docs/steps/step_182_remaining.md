# Step 182 lane A — 끝난 것, 남은 것, blindspot (재점검 13차)

User request (lane A 부분): "research/README.md 대응표·docs/PLAN.md·docs/steps/*.md 「남은 것」·docs/manual_checks.md를 모아 끝난 것
지우고 남은 것 정리 (know-your-unknowns blindspot으로 놓친 것 보완)" — 기준 (2026-10-19): "기본 Maya 에 Blender 기능이 붙은 모습",
칭찬 말고 차이만.

Paper lane, **Blender 실행 없음**. 입력: `docs/steps/step_173_remaining.md` (감사 12 목록 R1–R28, BS1–BS6), `step_173.md` (G1–G5,
우선순위 표), `step_174.md` … `step_181.md` 의 「남은 것」 (git `b07f9a7..326f12f` = 174–181 커밋 10 개), `gh issue list`
(2026-10-25, 읽기만), `docs/manual_checks.md`. 판정은 HEAD 326f12f 의 `src/allset` 을 grep / 읽기로 다시 확인한 것 ("[I]" = 코드를
읽은 것, 돌린 것 아님). 메뉴 수치 = `python tools/menu_count.py` (bpy stub) + `tmp/audit154a/greyed.py` / `edgrey.py` (출력
`tmp/audit182a/`). 점수 = 심각도 S (1–3) × 빈도 F (1–3), step 173 과 같은 척도. 판정은 delegated.

## 1. 구현률 — research/README.md 대응표 (33 행)

| 묶음 | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | **13** | 0 | 0 | 0 |
| UI (9) | 8 | 1 — 테마 (Maya 회색) | 0 | 0 |
| 개념 (11) | 9 | 0 | 0 | 2 — 분리 rotate / scale pivot, Y-up |
| **합계 (33)** | **30 (91 %)** | **1 (3 %)** | **0** | **2 (6 %)** |

감사 12 (30 / 1 / 0 / 2) 에서 **움직인 행 없음**. 174–181 은 대응표 밖 (UV, 조명, 애니 레이어, 표면) 또는 Done 행 아래 숨은 차이를 고쳤다:

- "Space 핫박스 / 마킹메뉴" 행 아래 BS1 (G 가 메뉴 명령을 반복 안 함) → step 175 로 끝 (`operators/repeat_maya.py`, Screen G =
  `allset.repeat_last`, `keymap/mapping.py` RepeatLast KIT).
- "Display Layer = Layer Editor" 행 아래 BS3 (Anim 탭 글뿐) → step 180 으로 끝 (`operators/anim_layers.py`, `ui/layer_editor.py`
  Anim 탭). 남은 연결 끊김은 §4 BS2.
- "QWERT" 행 아래 G5 (F9 에서 Select 로 바뀜) → step 174 (`operators/tool_keys.py` `_carry` / `carried_tool`).
- 테마 (Partial, 그대로): 킷은 테마를 싣지 않음 (step 130). 174–181 이 그린 색도 뷰포트 안 (선택 면 `ui/component_colors.py`
  step 176). 위젯 / 메뉴 / Outliner / Graph 키 색은 사용자 테마 그대로.
- Not possible 2 행 그대로 (분리 피벗 = `delta_location` 하나, Y-up = IO 변환만).

## 2. 감사 12 뒤 끝난 것 — 목록에서 지움

| 항목 (step_173_remaining.md / step_173.md) | 끝낸 것 (근거) |
|---|---|
| step_173.md G5 / 우선순위 9 컴포넌트 모드에서 도구가 Select 로 | step 174: `operators/tool_keys.py` `carried_tool` / `_carry` / `_seen`; `gui_step174_tool_modes` 21 / 21 (수정 전 8 실패) |
| R1 / BS1 G · Edit > Repeat · Recent Commands 가 메뉴 · 셸프 · 마킹 명령을 반복 안 함 | step 175: `operators/repeat_maya.py` (`record` / `last` / `allset.repeat_last` / `ALLSET_MT_recent_commands`), 기록 지점 `marking/modal.run_action`, `option_windows._record`; `test_step175_repeat` 8 / 8, `gui_step175_repeat` 5 / 5 |
| step_173.md 우선순위 6 선택 면 거의 불투명 주황 (ΔE 40.5, 다섯 감사째) | step 176 A: `ui/component_colors.face_overlay_action` (Maya 레이아웃 뷰 `show_faces` 끔); look_compare viewport 11 → **12 / 12** (ΔE 40.5 → 2.3) |
| G1 CB INPUTS polyCube1 사라짐 | step 176 B: 킷 버그 아님 — dogfood 스크립트가 Alt+Shift+D (Delete History) 를 누름 (`tools/dogfood_session.py:226-234`); `gui_step176_inputs_undo` 로 고정 |
| G2 Undo 뒤 결과 칸 `Result: group1` | step 176 C: `command_line/undo_text.py` (`Undo: <이름>` / `Redo: <이름>`, Maya 측정 `research/maya/re/undo_result_176.md`) |
| R15 / G3 네 뷰 이름표 Blender 축 | step 176 D: `ui/view_furniture.py` `SIDE_LABELS` = top -Y / front -Z / side -X |
| R2 / BS2 / BS6 패널 메뉴 · 패널 툴바 · Status Line 회색이 셈 · notice · 쌍둥이 검사 밖 | step 177: `ui/panel_menu_data.py`, `notices.PANEL_MENU` 60, `tools/menu_count.py` 패널 줄 3 개, `menu_consistency.panel_leaves` 0 쌍; 연결: Center View of Selection, Camera Attribute Editor, Tumble / Track / Dolly Tool (`ui/camera_tools.py`) |
| R3 UV Editor 118 / 172 (Map / Straighten Border, Layout Along, Stack Similar, Distribute, Match Grid, Select Unmapped / Back · Front-Facing / Texture Borders / Non-Overlapping, Isolate Add / Remove) | step 178: `operators/uv_modify.py`, `operators/uv_select_178.py`, `ui/uv_display.py`; UV Editor **136 / 172** (mayapy ≤ 2e-7) |
| step_173.md 우선순위 6 Light Links 8 회색 | step 179: `operators/light_links.py`, `ui/light_link_editor.py`; Lighting/Shading 5 → **13 / 14** |
| R5 / BS3 Animation Layers 없음 | step 180: `operators/anim_layers.py` (NLA COMBINE / REPLACE, `solve`), `ui/layer_editor.py` Anim 탭, `ui/time_slider.py:146` 선택 레이어 이름; mayapy 1e-5 |
| R7 일부 Surfaces 8 / 41 (다섯 감사째) | step 181: `operators/surfaces_maya.py`, `operators/surfaces_math.py` (Blender 레거시 NURBS 표면, mayapy ≤ 2.2e-7); Surfaces **15 / 41**. Curves 21 / 36 은 그대로 → R7 |

## 3. 남은 것 한 목록 (step_173 R 목록 재확인 + 174–181 「남은 것」 + 이번 blindspot)

판정: **일부** (일부 끝남) / **그대로** / **새**. 메뉴 수 = `tmp/audit182a/greyed_sum.txt` / `edgrey.py` (HEAD 326f12f).

### 레이아웃 / UI

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| U1 | Maya Preferences / Hotkey Editor = Blender Preferences (`ui/menu_map.py:296-297`), Shelf / Marking Menu / Panel Editor 회색 (`ui/notices.py:27-35`) | 그대로 | 2×2 = **4** | step_173 R11 |
| U2 | 스크립팅: `maya.cmds` 닮은꼴 17 함수 (`command_line/cmds_shim.py:135-488`) — `parent` `group` `duplicate` `setKeyframe` `playbackOptions` `spaceLocator` `file` 없음; Script Editor 32 / 59 | 그대로 | 2×2 = **4** | R9 |
| U3 | 옵션 상자 ❒ 부분 클릭 (C, #82), 5.x 메뉴가 옵션 창 아래 열린 채 (`compat.menus_close_on_leave`), `gui_step143_user` #82 묶음 안 불안정 (step 172 뒤 다시 안 봄) | 그대로 | 1×3 = **3** | R13 |
| U4 | Status Line 회색 9 / 9 (`ui/panel_menu_data.py:254-257`): **Construction History 토글**, Select by hierarchy, handle / dynamic 마스크, Snap to projected center / view planes, Render Setup, Pause Viewport 2.0, Character Controls — notice 만 (step 177) | 일부 (notice 생김) | 2×1 = **2** | R18 + 이번 |
| U5 | 패널 메뉴 67 / 111 · 툴바 22 / 29: Look at Selection 행 자체가 없음 (`ui/panel_menu_data.py` grep 0), Camera Attribute Editor 가 카메라를 선택함 (Maya 는 선택 안 바꿈), Resolution Gate · Use Selected Lights notice | 일부 | 1×2 = **2** | step_177.md |
| U6 | 네 뷰 / RMB 목록: 머리줄 하나 (C), RMB 목록 링 옆 (step 161 규칙, 판단 보류 manual_checks Step 161) | 일부 (이름표 끝) | 1×2 = **2** | R15 |
| U7 | 매니퓰레이터 / 링 세부 (목록 줄 22 vs 20 px, dead zone, 압출 매니퓰레이터 회전 고리 / world·local 토글 없음, 엣지 / 정점 압출 · 베벨 화살표 하나) | 그대로 | 1×3 = **3** | R16 |
| U8 | HUD Poly Count / Object / Selection Details = `overlay.show_stats`, Frame Rate = Preferences, HUD Animation Details / Bounding Box 회색 | 그대로 | 1×2 = **2** | R22 |
| U9 | 작업 공간 나머지 (Saved Layouts / Save / Import / Delete Workspace 회색, Modeling - Expert 머리줄, Blender 탭으로 바꾸면 메뉴 세트 안 바뀜) | 그대로 | 1×1 = 1 | R24 |
| U10 | 결과 칸 Undo 문구 빈 곳: 버튼 속성 편집 · 보고 없는 UNDO 전용 연산자 · `auto_key.py` / `graph_keys.py` / `view.py` 직접 `ed.undo_push` 는 이름 목록에 없음 (앞 단계 이름이 나옴), 더 없을 때 빨간 Maya 오류 없음, Script Editor `// Undo:` 줄 · Edit 메뉴 `Undo "Group"` 없음 | 새 (step 176) | 1×2 = **2** | step_176.md |
| U11 | Repeat 라벨 = 메뉴 이름 ("Cube"; Maya runtime 이름 `CreatePolygonCube`), Recent Commands List 가 창이 아니라 하위 메뉴, Combine / 셸프 / 마킹 기록 Maya 쪽 미측정 | 새 (step 175) | 1×1 = 1 | step_175.md |
| U12 | 셸프 탭 줄 화살표 없음 (좁은 창에서 탭 잘림), 체크 / 라디오 메뉴 항목 Ctrl+Shift 셸프 추가 불가; AE 탭 · 메뉴 잘림 (step 173 G4 — 실제 세션 확인 안 함) | 그대로 | 1×1 = 1 | R27, step_173.md G4 |

### Channel Box / AE

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| C1 | 상태 색 하나 (keyed 빨강만, 나머지는 아이콘 `ui/channel_box.py:1668-1669`; Maya driven 노랑 / expression 보라 / muted 갈색), CVs 표 자체 스크롤 아님, 곡선 / 격자 편집 모드 CV 표 없음, 고른 노드 줄 파랑 강조 없음, DG Traversal 한 단계 · "More..." 없음 | 그대로 | 1×3 = **3** | R14 |
| C2 | AE 라이트 탭에 Illuminates by Default 체크 없음 (속성 `Object.allset_illuminates_by_default` 만, `ui/ae_layout.py` grep 0); Illuminates by Default 끈 라이트의 그림자 목록 Maya `[]` 안 따름; EEVEE 렌더 프로브 없음 | 새 (step 179) | 1×1 = 1 | step_179.md |

### 마킹 메뉴 / 핫박스 / 키

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| K1 | Hypershade / Node Editor 그래프 키 ~50 행 NO (`keymap/mapping.py:536-602`: 1/2/3/4 속성 표시, 연결 선택, pick-walk, Solo Material …) — kit Hypershade 그래프 = Shader Editor, Blender 키 그대로 | 새 (mapping 에만 있었음) | 1×2 = **2** | §4 BS4 |
| K2 | Maya Universal Manipulator (Ctrl+T) 측정 안 함 (kit Ctrl+T = `builtin.transform`), 컴포넌트 전환 때 Select Box 깜박임 여부 손 확인 | 새 (step 174) | 1×1 = 1 | step_174.md |

### 모델링

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| M1 | Mesh / Edit Mesh 정확도 (Connect ≥ 4, Automatic Less distortion, Bevel Chamfer off / Mitering), Mesh Display 15 / 39, Edit Mesh 회색 3 (Reorder Vertices, Assign Invisible Faces, Project Curve on Mesh), Mesh Clipboard Copy / Paste Attributes, Transfer Vertex Order | 그대로 | 2×2 = **4** | R12 |
| M2 | Create > Polygon Primitives 회색 7 (Pipe, Helix, Gear, Soccer Ball, Super Ellipse, Spherical Harmonics, Ultra Shape) + Interactive Creation, Subdiv / Volume Primitives | 그대로 | 1×2 = **2** | R17 |
| M3 | #89 Quad Draw (overlay 색, Tab+MMB strip `operators/quad_draw.py:1053`, Ctrl+Shift+RMB), Insert Edge Loop Auto complete, Lattice local | 그대로 | 2×1 = **2** | R20 |
| M4 | Modify 회색 33 (Asset, Convert subdiv / Paint Effects / fluid / nParticle, Type Manipulator, Paint Scripts / Attributes Tool), Geometry to BBox Combine / Bake Animation | 그대로 | 1×1 = 1 | R25 |

### UV

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| V1 | UV Editor 136 / 172: Cut/Sew Auto Seams / Create Shell (Grid) / Split, Modify Cycle / Symmetrize / Warp Image, Tools Lattice / Smudge / Smear / Symmetrize, View HUD UV Statistics / Position / Isolate · Load Set · Undo View Change, Image 8 / 14 회색, UV Sets Copy / Rename / Per Instance Sharing, UV Toolkit 1 / 3; 메인 UV > Auto Seams / 3D Grab UV Tool 회색 | 일부 | 2×2 = **4** | step_178.md, `edgrey.py "UV Editor"` |
| V2 | **메인 UV > Delete UVs 가 회색인데 `allset.uv_delete` 는 있음** (UV Editor 마킹 메뉴 `marking/menus.py:939`, hotkey `keymap/mapping.py:567`), 회색 notice 는 "delete UVs by removing the UV map" (`ui/notices.py:374-375`) — 틀린 안내 | 새 | 2×1 = **2** | §4 BS1 |
| V3 | UV Sync 꺼짐 + 메시 면만 선택 시 Map Border 가 FINISHED 인데 바뀐 것 없음 (Maya 는 경고), Distribute / Match Grid 의 "면만 선택" 오류 경우 미검사, Filter Selection 이 켤 때 선택으로 고정 | 새 (step 178) | 1×1 = 1 | step_178.md |

### 애니메이션

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| A1 | **레이어 오브젝트에 Auto Key 가 키를 안 넣음** (`operators/auto_key.py` 에 `anim_layers` 0 — 활성 액션이 없음), Blender 자체 I / autokey 는 레이어를 모름 (tweak 모드 아래 쌓임만, step 180) | 새 (step 180) | 3×2 = **6** | step_180.md |
| A2 | Graph Editor 154 / 229 · Dope Sheet 130 / 181 (그대로): **Retime Tool / Region Keys / Lattice Deform Keys 회색** (Edit > Transformation Tools), Swap Buffer Curve, Weighted / Non-weighted Tangents, Pin Channel, Rotation Interp 5, Key Sync / Peak Removal, List Load / Add Selected / Bookmarks, Show 16 / 34, Add Key Tool, Lock / Free Tangent Length; 섞인 곡선 Translate 미터 (C, step 150); Blender I 키에 Default Tangent 없음 | 그대로 (+ Retime 명시) | 2×3 = **6** | R4, `edgrey.py "Graph Editor"` |
| A3 | 애니 레이어 나머지: 회전 By Layer (쿼터니언), Ghost 버튼, Zero Key / Zero Weight, 레이어 순서 위 / 아래, Merge Layers, 영향 점, Weight K, 이름 가운데 정렬, 띠 범위 [−1000, 1000] 고정 (밖 키 평가 안 됨) | 새 (step 180) | 2×2 = **4** | step_180.md |
| A4 | **애니 레이어 입구 두 곳이 step 180 전 그대로**: Windows > Relationship Editors > Animation Layers = NLA 창 + "Blender has no animation layers" (`ui/menu_map.py:107`, `ui/notices.py:44-45`), Channel Box Channels > Add to / Remove From Selected Layers 회색 + 같은 문구 (`ui/cb_channels.py:199-204`) | 새 | 2×2 = **4** | §4 BS2 |
| A5 | Key > Character Sets 11 (Key 22 / 41), IK/FK Keys 4, Scene Time Warp; Playback Looping Once / Oscillate · Cached Playback · Stepped Preview 회색 (Playback 19 / 26) | 그대로 (+ Playback 명시) | 2×2 = **4** | R6 일부, `greyed.py Key Playback` |
| A6 | Visualize 나머지 (Turntable, Animated Sweep, Ghosting Editor 타입 필터 / 목록 / Ghost Driver, 재생 중 고스트 안 채움, 셰이드 고스트 ≤ 11 / 255) | 그대로 | 1×1 = 1 | R26 |

### 리깅

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| G1 | Skin 19 / 28 (Interactive Bind / Tool, Post Normalization, Move Skinned Joints, Move Weights to Influences, Substitute Geometry, Bake Deformation, Export / Import Weight Maps), HumanIK, Skeleton IK Handle Snap / IK/FK Control, Constrain 11 / 20 (Normal, Tangent, UV Pin, Proximity Pin, Remove Target, Set Rest Position), Deform dead (Tension, Solidify, Morph, Wrinkle, Pose Interpolator, Sculpt, Jiggle …), Wire holders / Crossing / 4 개 넘는 dropoff, Bind = rest 포즈, 킷 XML 을 Maya 가 읽는지 미확인 | 그대로 | 3×2 = **6** | R6 |
| G2 | Display > Transform Display Rotate / Scale Pivots / Selection Handles 회색, 마스크 Handles / Dynamics (U4) | 그대로 | 2×1 = **2** | R18 |
| G3 | DAG 나머지: 숨은 부모의 자손 선택 불가 (Maya Outliner 는 가능), Blender 자체 H / Outliner 눈은 규칙 밖, `dag.sync` depsgraph 마다 O(n), Isolate Maya 규칙 [K] | 그대로 | 2×1 = **2** | R23 |

### FX / 렌더 / 파일

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| F1 | FX: Generate 2 / 50, nHair 2 / 54, nConstraint 0 / 19, Toon 1 / 20, Fluids 4 / 25, nCache 3 / 20, Effects 2 / 11, Fields 14 / 38 — notice 만; **MASH 메뉴 자체가 없음** (plugin 메뉴라 `menus.json` 에 데이터 없음 `ui/menu_sets.py:30` → 셈에도 안 들어감) | 그대로 (+ MASH 다시 꺼냄) | 2×1 = **2** | R21, §4 BS3 |
| F2 | 렌더: lambert1 1.25 배 밝음 (Principled 에 Diffuse 0.8 없음, `operators/material.py:82`), Blender F12 / Ctrl+Alt+Enter 에 기본 조명 없음, Status Line Render Setup 회색, Ambient / Volume Light 회색 (Lighting 13 / 14 는 Transfer Maps 만 회색 — Ambient / Volume 은 Create > Lights), Render Sequence All Layers / Cameras · Render Region 없음 | 일부 (Lighting 메뉴 끝) | 2×2 = **4** | R10 |
| F3 | Hypershade 115 / 249 (Create, Tabs, Options, Graph Clear / Add / Remove / Rearrange …), 드래그는 링크된 재질 안 됨, 면 위 놓기 규칙 미측정 | 그대로 | 1×2 = **2** | R19 |
| F4 | Reference Editor = Outliner Blender File 모드 (`ui/menu_map.py:133`), Reload / Unload / Replace / Import Objects from Reference 없음, Namespace Editor 회색 (`ui/notices.py:70`) | 그대로 | 2×2 = **4** | R8 |

### Surfaces / Curves

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| S1 | Surfaces 15 / 41: Birail 2 / 3+, Bevel, Align, Attach Without Moving, Move Seam, Intersect, Project Curve, Trim / Untrim (Blender 표면 트림 불가 [K]), Extend, Offset, Round, Stitch 3, Fillet 3, Sculpt Geometry, Surface Editing 3, Booleans 3 — notice; [U] Birail 1 꼬인 레일 (Maya 와 0.17–0.61), Extrude Rotation / Scale, Tube 차수 1 경로 (0.052), Rebuild 알고리즘; Birail 이 도구가 아니라 선택에 실행; Insert Isoparms / Duplicate Patch ❒ = generic | 일부 | 2×2 = **4** | step_181.md |
| S2 | Curves 21 / 36 (Edit Curve Tool, Intersect, Extend, Fit B-spline, CV Hardness, Align, Bend / Curl / Scale Curvature, Lock Length), Rebuild [U], 그리기 도구가 곡선 하나 뒤 끝남, V / C 스냅 · 표면 위 그리기 없음; 비균일 knot 곡선은 Bezier 분해로만 남아 Loft 매개변수가 Maya 와 다를 수 있음 (곡선에 `allset_nurbs` 기록 없음) | 그대로 (+ step 181 지적) | 2×2 = **4** | R7, step_181.md |

### 검증 / 정리 빚 (Maya 사용자에게 안 보임)

- **5.x**: 마지막 5.x 헤드리스 전체 = step 153 (`docs/compat_5x.md:62`). 154–181 은 5.x 실행 기록 없음. 새 API: NLA 띠 · `action.slots.new`
  (180), `light_linking` 컬렉션 (179), 레거시 NURBS 표면 `use_bezier_u/v` · `points` 행 (181, 5.x 에서 레거시 표면이 그대로인지 [U]),
  GN 모디파이어 입력 (169).
- `gui_step129_panel_toolbar` **3 실패** (step 177 기록: 수정 전 코드에서도 같은 3 개, 머리 폭 의존) — step 173 은 "실패 기록 없음"이라
  적었음. GUI 전체 묶음은 step 172 뒤 안 돌림.
- `docs/compat_5x.md` 테마 행 (step 130 뒤 없는 기능, 154 부터 이월).
- 코드 정리 이월 (그대로): `ui/outliner.py:9,133-137` `allset_outliner_rows`, `marking/rmb_items.py:208-209,322` 옛 VERTEX_PERIMETER /
  SHELL_BORDER.
- mayapy / GUI Maya 로 다시 확인할 것: 킷 `deformerWeights` XML 을 Maya 가 읽는지 (159), Hypershade 면 위 놓기 (162), Isolate 규칙 (164
  [K]), Geometry to Bounding Box 원본 지움 (168 [U]), Graph Editor Ctrl+클릭 실손 (170), Combine / 셸프 / 마킹 repeatLast 기록 (175),
  Symmetrize UV (178, GUI 5 번 실패).
- `tools/menu_consistency.py` 가 메인 UV > Delete UVs 쌍둥이를 못 찾음 (§4 BS1: 라벨은 같고 명령 이름이 다른 경우), Channel Box 메뉴
  (`ui/cb_channels.NOTICES`) 는 셈 · 쌍둥이 검사 밖 (§4 BS2).
- `tools/dogfood_session.py` 가 Alt+Shift+D 를 눌러 INPUTS 샷이 비어 보임 (step 176 B; 스크립트 선택).

## 4. Blindspot (어느 「남은 것」 / 이슈 / backlog / manual_checks 에도 없던 것, grep 확인)

| # | Maya 동작 | 킷 지금 (근거) | S×F |
|---|---|---|---|
| BS1 | 메인 UV > Delete UVs (모델러가 UV 를 다시 펼 때) | 회색 + "delete UVs by removing the UV map (Data properties > UV Maps)" (`ui/notices.py:374-375` 의 `UV` 범주 규칙). 같은 Maya 명령은 킷에 있음: `allset.uv_delete` (`operators/uv_shells.py:590-597`, step 155), UV Editor 마킹 메뉴 SW (`marking/menus.py:939`), UV Editor 핫키 (`keymap/mapping.py:567`). `menu_consistency` 0 쌍 — 메인은 runtime `DeleteUVsWithoutHotkey` (`polyPerformAction polyMapDel f 0`, research/maya/menus.json, ModelingUVMenu.mel:208), 마킹 메뉴는 `DeleteUVs` (research/maya/marking_menus.json:6086-6090) 라 이름 비교가 놓침 [O]. 마킹 메뉴 작동 라벨 vs 메인 회색 라벨 대조로 찾음 (`tmp/audit182a/all_greyed.txt`; 다른 쌍은 nCloth/Delete History 하나 — 다른 명령) | 2×1 = 2 |
| BS2 | 애니 레이어 입구: Windows > Relationship Editors > Animation Layers, Channel Box 우클릭 Channels > Add to / Remove From Selected Layers (Maya 에서 채널을 레이어에 넣는 기본 길) | step 180 이 Layer Editor Anim 탭 · `anim_layers` 를 만들었지만 두 입구는 그 전 그대로: 메뉴 = NLA 창 + 툴팁 "Blender has no animation layers" (`ui/menu_map.py:107`, `ui/notices.py:44-45`), CB 두 항목 회색 + 같은 문구 (`ui/cb_channels.py:199-204`). step 101 / 166 규칙 테스트는 CB 메뉴를 안 세고, NOTICES 는 작동 항목에도 툴팁으로 남음 | 2×2 = 4 |
| BS3 | MASH (Maya 2022 Animation / FX 메뉴 세트에 기본 로드되는 플러그인 메뉴 [K]) | 메뉴 없음 (`ui/menu_sets.py:30` "Plugin menus … skipped"), `menus.json` 에 데이터가 없어 menu_count 에도 안 나옴. 마지막 언급은 `docs/PLAN.md:402,529` (Left out) — 163 / 173 목록에서 빠짐. 회색 메뉴 + notice (GN Instance on Points) 도 없음 | 2×1 = 2 |
| BS4 | Hypershade 그래프 키 (1/2/3/4 속성 표시, 연결 · 위 / 아래 흐름 선택, 화살표 pick-walk, Solo) | `keymap/mapping.py:536-602` NO 약 50 행 ("Blender 키 그대로") — 「남은 것」 의 Hypershade 항목 (R19) 은 메뉴만 셈 | 1×2 = 2 |
| BS5 | Status Line Construction History 토글 (history 끄고 모델링) | 회색 + notice (`ui/panel_menu_data.py:256`); 킷은 `prim_history` / step 65 기록을 늘 만듦 — 끄는 길 없음 [I] | 1×1 = 1 |
| BS6 | Graph Editor Edit > Transformation Tools > Retime Tool (Maya 2017+, 키 간격 조정 도구) | 회색 (`edgrey.py "Graph Editor"`), R4 목록에 이름 없었음 | 2×1 = 2 |
| BS7 | 측정 도구 빈 곳 (절차): `menu_consistency` 는 라벨 + 명령이 같은 쌍만, CB Channels 메뉴 (`cb_channels.NOTICES`) 와 Status Line 은 쌍둥이 검사 밖 → BS1 · BS2 같은 "기능이 생겼는데 입구는 회색" 이 다음 단계 뒤에도 남음 | — (절차) |

확인했고 blindspot 아님 (근거): Duplicate Special / with Transform (`keymap/mapping.py:255,263`), Isolate Select
(`keymap/mapping.py:215`), K 시간 드래그 (`keymap/mapping.py:106`), Playback Looping Continuous (`ui/notices.py:57,219` — Once /
Oscillate 은 A5), Graph Editor Tangents 57 / 59.

## 5. GitHub 이슈 (2026-10-25, `gh issue list --state open` / `--state all --limit 200`)

- 전체 **101**, 닫힘 **100**, 열림 **1**: **#89** "Quad Draw leftovers: overlay colour options, Tab+MMB strip resize, Ctrl+Shift+RMB
  options menu" (label maya-parity, 0.5.0) — 코드도 열림 (`operators/quad_draw.py:1053`). 174–181 동안 새 이슈 없음.
- step 173 이 적은 "닫혔지만 코드가 다 안 보여 줌" (#66 섞인 곡선 미터 → A2, #82 ❒ 부분 클릭 → U3, #80 / #84 고친 곳 링크 없음) 그대로.

## 6. 수치 (감사 12 → 지금)

| 수치 | step 173 (b07f9a7) | 지금 (326f12f) |
|---|---|---|
| 대응표 | 30 / 1 / 0 / 2 | **30 / 1 / 0 / 2** (Done / Partial / Not started / Not possible) |
| 메뉴 leaves 작동 (unique 1318) | 699 (53.0 %) | **714 (54.2 %)** |
| 메뉴 세트별 합 (1486) | 806 (54.2 %) | **821 (55.2 %)**, 회색 + notice 없음 0 |
| Graph Editor / Dope Sheet / UV Editor | 154 / 130 / 118 | 154 / 130 / **136** (229 / 181 / 172) |
| Hypershade / Render Settings / Script Editor | 115 / 10 / 32 | 115 / 10 / 32 |
| 패널 메뉴 / 툴바 / Status Line 회색 (셈) | 회색 28 + 8, notice 0 (lane A 셈) | **67 / 111**, **22 / 29**, **0 / 9**, notice 없는 회색 0 (step 177 셈 기준) |
| 메뉴별 | Lighting 5 / 14, Surfaces 8 / 41 | Lighting **13 / 14**, Surfaces **15 / 41** |
| 헤드리스 전체 | 1600 / 1600 | 1658 / 1658 (step 180 기록; step 181 문서 숫자는 메인이 확인; 이 레인은 안 돌림) |
| 열린 이슈 | 1 (#89) | 1 (#89) |
| manual_checks (`- [ ]` / `- [x]` 줄 수) | 663 / 96 | 682 / 96 → **691 / 107** (§7) |

약한 곳 (여섯 감사째 그대로 포함): nConstraint 0 / 19, Generate 2 / 50, nHair 2 / 54, Toon 1 / 20, Control 1 / 14, Texturing 1 / 8,
nCache 3 / 20, Fluids 4 / 25, Stereo 1 / 6, Effects 2 / 11, nParticles 7 / 25, Fields 14 / 38, Mesh Display 15 / 39, Surfaces 15 / 41,
nCloth 5 / 13. 숫자는 lane B (`step_182_quant.md`) 가 기준 — 이 표는 bpy stub 셈.

## 7. manual_checks 정리 (`docs/manual_checks.md`)

- 셈 = `grep -cE '^\s*- \[( |x)\]'` (step 173 과 같은 셈법).
- 전: **682 항목, 96 체크, 586 열림** (174–181 이 19 항목 추가).
- 후: **691 항목, 107 체크, 584 열림**. 지운 항목 0.
- **체크 / 나눠서 체크 11** (GUI 테스트가 확인하는 부분을 `[x]` + 테스트 이름, 안 보는 부분을 `[ ]` 로 남김):
  Step 174 W / E / R / Q + F8–F11 (`gui_step174_tool_modes`; Select Box 깜박임 남김), E + RMB Vertex · Shift+RMB Target Weld
  (`gui_step174_tool_modes`, `gui_step64`), Step 175 메뉴 Cube → 실제 G · 라벨 · Ctrl+D 뒤 G (`gui_step175_repeat`; Combine · 셸프 ·
  Ctrl+E 남김), Step 176 선택 면 점 무늬 (`gui_step134_selection`), Ctrl+Z `Undo: Group` (`gui_step176_inputs_undo`; Redo · Adjust Last
  남김), Step 177 Tumble / Dolly Tool · Center View persp (`gui_step177_panel_menus`; Track · 카메라 통해 남김), Step 178 Map Border
  pPlane (`gui_step178_uv_map_border`; 사용자 메시 남김), Step 179 Break Light Links · 편집기 열기 (`gui_step179_light_linking`; 렌더 ·
  토글 남김), Step 180 Anim 탭 행 / Mute / Weight / COMBINE (`gui_step180_anim_layers`; S 키 결과 남김), Step 181 Loft · Revolve
  (`gui_step181_surfaces`; 고른 순서 · CV 편집 남김).
- **낡은 문구 고침 4**: Step 50 "Anim 탭 안내" (→ step 180 레이어 목록), Step 101 회색 예 "Surfaces > Loft" (Loft 는 step 181 부터 작동 →
  Trim Tool), Step 109 Loft (→ NURBS 표면), Step 70 "3D View 의 G = Repeat Last 그대로" (→ kit Repeat Last, step 175).
- 체크 안 함 (GUI 테스트는 있지만 함수를 직접 부르거나 일부만): Step 177 패널 회색 툴팁 hover (헤드리스가 notice 만 검사), Step 178
  Isolate Add / Remove, Step 181 Birail / Detach / Insert / Duplicate Patch.

## 8. 차이 우선순위 top 10 (S×F, 같은 점수는 Maya 사용자가 먼저 부딪히는 순)

| 순 | S×F | 차이 | 근거 | 단계 후보 · 검증 |
|---|---|---|---|---|
| 1 | 6 | 레이어 오브젝트에 Auto Key 가 키를 안 넣음, Blender I 키는 레이어 모름 (A1) | `operators/auto_key.py` (`anim_layers` 0), step_180.md 「남은 것」 | **"Animation layers 2"** — auto key → `anim_layers.key`, I 키 (Blender `anim.keyframe_insert`) 를 kit 키 경로로 덮기 (레이어 오브젝트만), 입구 두 곳 연결 (A4 / BS2: Windows 메뉴 = Layer Editor Anim 탭, CB Add to / Remove From Selected Layers = 채널 단위 레이어 — mayapy `animLayer -at` 측정), Merge Layers / Zero Key. 검증: 헤드리스 auto key 결과 = mayapy, CB 메뉴 항목 작동, menu_count |
| 2 | 6 | Graph Editor 나머지 + Retime Tool (A2, BS6) | `edgrey.py "Graph Editor"`, `ui/notices.py:479` | **"Graph Editor depth 2"** (세 감사째 이월) — Retime Tool (Maya GUI 측정 먼저), Swap Buffer Curve, Weighted Tangents (mayapy 핸들 길이), Pin Channel, I 키 Default Tangent. 검증: mayapy 비교, Graph Editor ≥ 165 / 229 |
| 3 | 6 | 리그 나머지 (G1) | `greyed.py Skin Constrain Skeleton` | **"Skin tools 2"** (이월) — Move Weights to Influences, Post Normalization, Interactive Bind, Constrain Remove Target / Set Rest Position, 킷 XML mayapy 왕복. 검증: mayapy 1e-6, Skin ≥ 24 / 28 |
| 4 | 4 | 스크립팅 cmds 17 함수 (U2) | `command_line/cmds_shim.py:135-488` | **"maya.cmds look-alike 2"** (이월) — parent / group / duplicate / setKeyframe / playbackOptions / spaceLocator / file. 검증: 같은 스크립트 mayapy vs 킷 헤드리스 |
| 5 | 4 | Reference Editor (F4) | `ui/menu_map.py:133` | **"Reference Editor"** (이월) — kit 창 Reload / Unload / Replace / Import Objects / Remove. 검증: 링크 .blend 왕복, override 편집 유지 |
| 6 | 4 | 렌더 기본 (F2) | `operators/material.py:82`, step_152 | **"Render parity 2"** (이월) — lambert1 밝기, Ambient Light, Render Setup notice → 최소판. 검증: 렌더 평균 밝기 Maya ±3 % |
| 7 | 4 | Preferences / Hotkey Editor (U1) | `ui/menu_map.py:296-297` | **"Maya Preferences window"** (이월) — 장면 · 애드온 설정만 (step 130). 검증: preferences 스냅숏 차 0 |
| 8 | 4 | UV 나머지 + 메인 Delete UVs 회색 (V1, V2 / BS1) | `edgrey.py "UV Editor"`, `ui/notices.py:374` | **"UV 3"** — Delete UVs 연결 (한 줄), Auto Seams (mayapy), HUD UV Statistics, UV Sets Copy / Rename. 검증: menu_count UV ≥ 17 / 19, UV Editor ≥ 142 / 172 |
| 9 | 4 | Curves 21 / 36 + Surfaces 나머지 (S1, S2) | step_181.md | **"Curves 2"** — Fit B-spline, Extend, CV Hardness, Edit Curve Tool, 곡선 `allset_nurbs` 기록 (Loft 매개변수), 그리기 도구 계속 그리기 + V / C 스냅. 검증: mayapy CV, Curves ≥ 27 / 36 |
| 10 | 4 | Mesh / Edit Mesh 정확도 · Mesh Display 15 / 39 (M1) | step_139*.md | **"Mesh depth"** (이월) — Connect ≥ 4, Bevel Chamfer off / Mitering mayapy, Copy / Paste Attributes. 검증: mayapy 1e-4 |

다음 (점수 3 이하): 옵션 상자 부분 클릭 (U3, C), CB 상태 색 (C1), 매니퓰레이터 세부 (U7), Status Line Construction History (U4 / BS5),
MASH (BS3), Hypershade 그래프 키 (BS4), Character Sets / Playback Looping (A5), 패널 Look at Selection (U5).

## 모르는 것 / 반대 증거

- BS1: 메인 `DeleteUVsWithoutHotkey` = `polyMapDel` 은 확인 [O]; `DeleteUVs` runtime 의 MEL 본문이 같은 polyMapDel 인지는 열어 보지 않음 [I] (이름 · annotation 으로 판단).
- BS3 MASH 가 Maya 2022 팩토리 실행에서 로드되는지 [K] — research `menus.json` 은 설치본 MEL 에서 뽑아 플러그인 메뉴가 없음;
  research/maya/workflows/fx.md:99 는 "MASH1 + ReproMesh" 를 Maya 에서 관찰 [O fx_04] 이라 적음.
- A1 은 step 180 문서의 주장 + `auto_key.py` grep 0 (돌려 보지 않음).
- BS5 Construction History 끄기를 Maya 사용자가 얼마나 쓰는지 [U].
- 메뉴 수치는 bpy stub 셈 (Blender poll 실패 안 셈); `--options` 는 Blender 가 필요해 안 돌림 (lane B).
- manual_checks 의 체크는 GUI 테스트 코드를 읽고 판단 — 이 레인은 GUI 를 돌리지 않음 (step 174–181 문서의 통과 기록에 기댐).
- 5.x 에서 154–181 이 도는지 모름 (§3 빚).
