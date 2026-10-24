# Step 163 lane A — 끝난 것, 남은 것, blindspot (재점검 11차)

User request (2026-10-24, lane A 부분): "research/README.md 대응표·docs/PLAN.md·docs/steps/*.md 「남은 것」·docs/manual_checks.md를
모아 끝난 것 지우고 남은 것 정리 (know-your-unknowns blindspot으로 놓친 것 보완)" — 비판 기준: "이건 '기본 Maya에 Blender 기능이 붙은
모습'이어야 한다. 칭찬 말고 차이만. Maya 2022와 같은 시나리오를 나란히 따라 하며 ... 기능(메뉴 전수 대비, 파일 입출력, 모델링·UV·
애니·리깅·FX·렌더) 모두에서 Maya가 아니라고 느껴지는 곳을 찾아 우선순위로."

Paper lane, **Blender 실행 없음**. 입력: `docs/steps/step_154_remaining.md` (감사 10 의 정리 목록), `docs/steps/step_154.md` 우선순위 표,
`docs/steps/step_155.md` … `step_162.md` 의 「남은 것」 (git `a2b22b4..HEAD` = 155–162 커밋 16 개), `docs/PLAN.md` 「재점검 10차」,
`gh issue list --state open` (2026-10-24, 읽기만), `docs/manual_checks.md`. 판정은 HEAD 2cd3406 의 `src/allset` 을 grep / 읽기로 다시
확인한 것 ("[I]" = 코드를 읽은 것, 돌린 것 아님). 메뉴 수치 = `python tools/menu_count.py` (bpy 를 stub 으로 바꿔 Blender 없이 돎 —
`--options` 만 Blender 를 띄우므로 안 돌림) + `tmp/audit154a/greyed.py` / `edgrey.py` (같은 함수, 메뉴별 회색 목록) +
`tmp/audit163a_map.py` (작동 항목 중 Blender 연산자를 그대로 부르는 것). 판정은 delegated.

## 1. 구현률 — research/README.md 대응표 (33 행)

| 묶음 | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | 12 | 1 — 3D View 밖 선택 수정키 | 0 | 0 |
| UI (9) | 8 | 1 — 테마 (Maya 회색) | 0 | 0 |
| 개념 (11) | 9 | 0 | 0 | 2 — 분리 rotate / scale pivot, Y-up |
| **합계 (33)** | **29 (88 %)** | **2 (6 %)** | **0** | **2 (6 %)** |

감사 10 (step 154) 과 같음 — **움직인 행 없음**. 155–162 는 Done 행의 깊이 (UV 셸, 곡선, Graph Editor 키, Channel Box 메뉴, 가중치 /
라벨, 작업 공간, 뷰 메시지, 옵션 상자) 였다.

- **선택 수정키 (Partial, 그대로)**: `keymap/maya_patches.py:52-62` (`_OUTLINER_CLICK`, `_GRAPH_CLICK`, `_BOX_NO_XOR`, `_NODE_BOX`)
  는 `git diff a2b22b4..HEAD` 에서 안 바뀜 (이 파일의 변경은 `hs_swatch_drag` 와 UV Editor 키뿐).
- **테마 (Partial, 그대로)**: 킷은 테마를 싣지 않음 (step 130). 155–162 가 그린 색은 뷰포트 안 (UV 셸 테두리 `ui/uv_display.py`, 계층
  강조 `ui/selection_wire.py:129` `highlighted`, 관절 라벨 색 `operators/joint_labels.py`). 위젯 / 메뉴 / Outliner / Graph 키 색은 사용자
  테마 그대로.
- **대응표에 없는 개념 차이 하나 (§4 BS1)**: Maya DAG 의 "부모를 숨기면 / 지우면 / 내보내면 자식도" 가 대응표 "Group = Empty" 행
  (Done) 에 숨어 있다. 행을 Partial 로 바꿀지는 측정 뒤 (§7 #1) — 이번엔 수치를 그대로 둠.

## 2. 감사 10 뒤 끝난 것 — 목록에서 지움

| 항목 (step_154_remaining.md §3 / §4, step_154.md G) | 끝낸 것 (근거) |
|---|---|
| §3 #1 UV Editor 도구 (대부분) | step 155: Stack / Orient / Orient to Edges / Snap Together / Snap and Stack / Distribute / Normalize / Unstack / Move and Sew / Create UV Shell / Delete UVs (`operators/uv_shells.py:115,169,191`), 키 4 5 6 8 9 Ctrl+1 Delete Ctrl+Shift+X (`keymap/maya_patches.py:1169-1184`), Move UV Shell; UV Editor 메뉴 95 → **110 / 172**. 남은 부분 §3 #3 |
| §3 #2 Curves (일부) | step 156: CV / EP Curve Tool, 3 / 2 점 원호 (`operators/curve_draw.py:338`), Rebuild / Attach / Detach / Cut / Fillet / Straighten / Move Seam (mayapy 1e-6); Curves 16 → **21 / 36**. Surfaces 는 8 / 41 그대로 — §3 #8 |
| §3 #3 Graph Editor Key 메뉴가 CB 노드 기준, Mute Key, Default Tangent, Select 메뉴 | step 157: 편집기 Edit 의 키 창이 선택 키에 (`operators/option_windows_edit.py` `_paths`), Mute = Stepped F-modifier "Maya mute" (`operators/graph_key_menu.py:482`), Select 마스크, Default In / Out (`:349` `after_insert`); Graph Editor 145 → **154 / 229**, Select 7 / 8. 남은 부분 §3 #4 |
| §3 #4 / #81 Maya UI 되돌리기, 작업 공간 하나 | step 160: 템플릿 작업 공간 8 개 (`tools/make_startup.py` `MAYA_WORKSPACES`), `switch.reset_workspace` (`switch.py:151`), Windows > Workspaces = `ALLSET_MT_maya_workspaces` (`ui/menu_map.py:283`). 남은 부분 §3 #16 |
| §3 #5 가중치 / Joint Labelling / IK 켜기 | step 159: Deform > Export / Import Weights (`operators/deformer_weights.py:378`, Maya XML), Joint Labelling 38 항목 (`operators/joint_labels.py:301`), Enable / Disable Selected IK Handles, Reset Default Weights; Skeleton 13 → **51 / 54**, Skin 18 → 19 / 28, Deform 28 → 30 / 74. 남은 부분 §3 #7 |
| §3 #6 Channel Box (대부분), §4 BS2 CB 메뉴 전체 | step 158: 빈 곳 RMB / Ctrl+RMB 도 킷 메뉴, Channels 메뉴 Maya 순서 전체 (`ui/cb_channels.py`), SHAPES 채널 (조명 Intensity = `energy` 키 가능), spot Cone / Penumbra 행, MUTED 상태 아이콘. 남은 부분 §3 #10 |
| §3 #7 / #97 INPUTS "Armature" | step 158: `operators/skin.py:405` `name_skin_cluster` → skinCluster1 / 2, INPUTS 이름 = `attribute_editor.modifier_node` |
| §3 #9 일부 / §4 BS3 Hypershade 스와치 MMB 드래그 | step 162: `ui/hs_drag.py:153` `ALLSET_OT_hs_swatch_drag` (창 모달 → `scene.ray_cast` → `material.assign`) |
| §3 #13 일부 / §4 BS1 Ctrl+Shift+클릭 = 셸프에 추가 | step 162: `ui/menu_sets.py:704` `add_to_shelf_if_asked` → `shelf.add_menu_item` (`shelves.json` `"extra"`) |
| step_154.md G1 킷 결과가 Blender 보고 | step 161: `results.py:14` `result` → Command Line 결과 칸; INFO 99 곳 이동 (남은 INFO = 힌트 목록, `test_step161_messages`) |
| G2 RMB 목록이 3 열 | step 161: `marking/engine.py:388` `fit_ring` 한 열, 링 옆 |
| G3 네 뷰 정사영 ~10 배 확대 | step 161: `operators/view.py:617` `maya_ortho_distance` (30 단위), 칸마다 평면 격자 (`ui/maya_grid.py` `span_segments`). 머리줄 하나는 C → 툴팁 알림 (§3 #17) |
| G4 side 뷰 lead 와이어 | step 161: `ui/selection_wire.py:129` `highlighted` (자손 = 가까운 선택 조상의 색) |
| G6 Toggle Show/Hide ❒, Non-Deformer History ❒ 가 "no settings" 창 | step 162: `operators/option_windows_display.py:73`, `option_windows_edit.py:376`; Non-Deformer 기본을 Maya All 로 (전에는 before-only 였음) |
| step_154.md look_compare 마킹 메뉴 표본점 | step 161: `tools/look_data.py` marking_menu_box / list_bg 다시 고름, kit-drawn 6 / 6 |

**GitHub 정리** (§5): 열린 이슈 20 개 중 **19 개가 코드로 끝남** (감사 10 의 17 개 + #97 step 158 + #81 step 160). 코드로도 열린 것은
**#89 하나**. 이 프로젝트는 릴리스 때 닫음 (step_143.md:11) — 지금 닫지 않음.

## 3. 남은 것 한 목록 (step_154_remaining.md §3 항목별 재확인 + 155–162 「남은 것」)

점수 = 하루 빈도 F (1–5) × 심각도 S (1–4), 등급 외형 / 조작 / 기능 / 없음 (step 98 기준). 판정: **끝** / **일부** / **그대로**.

| # | 영역 | 항목 (지금 남은 것) | 154 판정 → 지금 | F×S | 출처 |
|---|---|---|---|---|---|
| 1 | 개념 | **DAG 상속 없음** (새 blindspot, §4 BS1) | — | 3×3 = **9** | 이번 |
| 2 | UI | **셸프 더블클릭 = `screen.redo_last`** (`ui/shelf.py:278,286`) — step 147 뒤 셸프 명령은 등록이 안 돼 (`undo_steps.command`) 더블클릭이 셸프 명령의 옵션이 아니라 아무것도 / 다른 연산의 패널 [I]; 긴 팩토리 탭 (Poly Modeling 43 개) 은 1600 px · UI 1.25 에서 추가 버튼이 화면 밖, 스크롤 없음 (step_162.md); 체크 / 라디오 메뉴 항목은 Ctrl+Shift 셸프 추가 불가 | 새 (§4 BS2) | 3×2 = **6** | step_162.md 「남은 것」, 이번 |
| 3 | UV | **UV Editor 나머지**: Tools 11 / 19 (Unfold / Cut / Sew / Pin / Smear / Smudge / Lattice / Symmetrize 브러시), Modify 22 / 31 (Map / Straighten Border, Layout Along, Stack Similar, Distribute UVs, Match Grid, Cycle, Symmetrize, Warp Image), Select 26 / 39 (Unmapped Faces, Back / Front-Facing, Non-Overlapping, Texture Borders, To Edge Loop / Ring), View 10 / 20 (HUD UV Statistics / Position, Isolate Load Set / Add / Remove), Cut/Sew Auto Seams / Split, UV Toolkit 1 / 3; 셸 테두리는 UV Editor 에서만 (Maya 는 3D View 도), 색 미측정; Move UV Shell 의 Prevent Overlap 없음 | 9 → **일부** | 3×2 = **6** | step_155.md 「남은 것」, `edgrey.py` |
| 4 | 애니 | **Graph Editor / Dope Sheet 나머지**: 섞인 곡선에서 Translate 가 미터 (C, step 150); View 20 / 40 (Buffer Curves, Undo / Redo View Change, Play Range Shades, Clip Time), Curves 23 / 39 (Weighted / Non-weighted Tangents, Pin Channel, Rotation Interp, Key Sync / Peak Removal), Tangents Lock / Free Length, List 2 / 8 (Load / Add Selected Objects, Bookmarks), Show 16 / 34, Pre-Select Highlight, Add Key Tool; Dope Sheet Curves 17 / 34 (Euler Filter · Smooth Filter 가 Graph Editor 에선 되고 Dope Sheet 에선 회색), Dope Sheet View > Auto Frame; 마스크는 최대 50 ms 늦음, 곡선 선 클릭은 안 걸러짐; Blender 자체 키 (I, Set Key on Animated = `anim.keyframe_insert_by_name`, `ui/menu_map.py:421`) 에는 Default Tangent 안 붙음 | 9 → **일부** | 3×2 = **6** | step_157.md 「남은 것」, `edgrey.py` |
| 5 | 조작 | **다른 편집기의 선택 수정키**: box XOR 없음, Outliner / Graph Ctrl-click = toggle, Outliner Shift+click 범위 아님, Graph / Node Alt+RMB 는 킷 dolly 아님 | 6 → **그대로** (`maya_patches.py:52-62`) | 3×2 = **6** | README Partial 행 |
| 6 | 모델링 | **Modify > Convert > Smooth Mesh Preview to Polygons = `object.convert`** (`ui/menu_map.py:268`, 같은 줄 NURBS to Polygons :267) — 모든 modifier 를 구움: skinCluster (Armature), 킷 디포머 (lattice / bend / wrap / cluster), 다른 history 까지 = 사실상 Delete History; smooth preview 가 없는 메시에도 같은 일 [I]. Maya 는 smooth preview 만 polySmoothFace 로 바꿈 (디포머 순서 [U]) | 새 (§4 BS3) | 2×3 = **6** | 이번 |
| 7 | 리깅 | **리그 나머지**: Skin 19 / 28 (Move Skinned Joints, Move Weights to Influences, Substitute Geometry, Bake Deformation, Post Normalization, Interactive Bind), Key > IK/FK Keys 4, Skeleton IK Handle Snap / HumanIK, Deform 30 / 74 (Wire, Wrinkle, Sculpt, Jiggle, Tension, Morph …); Bind 는 rest 포즈 기준; Import Over / barycentric / bilinear 없음, Nearest 공간 [U], 킷 XML 을 Maya 가 다시 읽는지 미확인; **Select > All by Type > IK Handles / Clusters 와 Edit > Delete All by Type > IK Handles 가 회색 + "Blender has no node of this type"** (`ui/notices.py:395,418`) — 킷은 `ikHandleN` (`operators/skin.py:108`) 과 `clusterN` 을 만듦 (§4 BS4) | 8 → **일부** | 2×3 = **6** | step_159.md 「남은 것」 |
| 8 | 모델링 | **Curves / Surfaces 나머지**: Curves 21 / 36 (Edit Curve Tool, Intersect, Extend, Fit B-spline, CV Hardness, Align, Bend / Curl / Scale Curvature, Lock Length), Surfaces **8 / 41** (세 감사째); Rebuild 알고리즘 [U] (모양 0.6 %), Detach 는 CV 근처 edit point 에서만; 그리기 도구는 곡선 하나 뒤 끝남 (Maya 는 계속), V / C 스냅 없음, 표면 위 그리기 없음, 원호 반지름 매니퓰레이터 없음 | 9 → **일부** | 2×3 = **6** | step_156.md 「남은 것」 |
| 9 | 렌더 | lambert1 1.25 배 밝음 + world 주변광, Blender F12 / Ctrl+Alt+Enter 에 기본 조명 없음, Render Sequence All Layers / Cameras · Render Region · Add to Render View 없음, Render Setup 회색 (`ui/status_line.py:543`), Lighting 5 / 14 | 6 → **그대로** (155–162 렌더 변경 없음) | 3×2 = **6** | step_152*.md |
| 10 | UI | **Maya Preferences / Hotkey Editor** = Blender Preferences (`ui/menu_map.py:290-291`), Shelf Editor / Marking Menu Editor 회색; Working Units · fps · undo 를 한 곳에서 못 바꿈 | 6 → **그대로** | 2×3 = **6** | step_145 BS1 / BS2 |
| 11 | 파일 | **Reference Editor** = Outliner Blender File 모드 (`ui/menu_map.py:133`), Reload / Unload / Replace / Import Objects from Reference 없음, Namespace Editor 회색 | 6 → **그대로** | 2×3 = **6** | step_145 BS4 |
| 12 | UI | **옵션 상자 몸짓**: ❒ 부분만 클릭은 C (버튼 안 위치 없음), 5.x 는 Maya 메뉴가 옵션 창 아래 열린 채 (`compat.menus_close_on_leave`), 실제 하드웨어 느낌 미확인 (manual_checks Step 146) | 5 → **일부** (Ctrl+Shift 셸프 추가 끝) | 5×1 = **5** | step_146 / 153 |
| 13 | UI | **Channel Box 나머지**: 상태 색 하나 (`ui/channel_box.py:1697,1839` `right.alert` = 빨강 — Maya keyed 빨강 / driven 노랑 / expression 보라 / muted 갈색 / constraint 파랑, research/maya/channel_box.md:138-139; 킷은 아이콘으로 구별, `:1664`), INPUTS 줄 (polyCube1 width …) 은 고를 수 있는 채널 아님, spot dropoff / shadow 줄 없음, Select Connection 의 곡선이 AE 노드로 안 뜸, SHAPES / INPUTS 값 칸 7 px [U] | 8 → **일부** | 4×1 = **4** | step_158.md 「남은 것」 |
| 14 | 렌더 | **Hypershade**: Create 69 / 160, Tabs 0 / 6, Options 0 / 6, Graph Clear / Add / Remove / Rearrange 회색, Edit 9 / 30; 드래그는 링크된 재질 안 됨, 스와치 클릭이 undo step 하나, 면 위 놓기 규칙 미측정 | 6 → **일부** (드래그 끝) | 2×2 = **4** | step_162.md 「남은 것」 |
| 15 | UI | **스크립팅**: Command Line 언어 Python 만 (MEL = 결정, `command_line/__init__.py:77`; 단순 MEL 은 `runner.mel_to_python`), `maya.cmds` 닮은꼴이 17 함수 (`command_line/cmds_shim.py`: ls select move rotate scale getAttr setAttr xform polyCube/Sphere/Cylinder/Plane delete rename objExists listRelatives currentTime) — `parent` `group` `duplicate` `setKeyframe` `playbackOptions` `file` `spaceLocator` 없음 (§4 BS5); Script Editor History 0 / 13, Source Script / Save Script to Shelf 회색 | 4 → **그대로** | 2×2 = **4** | step_105, `edgrey.py` |
| 16 | UI | **작업 공간 나머지**: Panels > Saved Layouts 회색 (`ui/panel_menus.py:187`), Save / Import / Delete Current Workspace · Disable Docking 회색, Modeling - Expert 머리줄에 Blender 위젯, 한 칸에 Maya 탭 묶음 하나만, Blender 작업 공간 탭으로 바꾸면 메뉴 세트 안 바뀜 | 9 → **일부** | 2×1 = **2** | step_160.md 「남은 것」 |
| 17 | UI | **네 뷰 / 정사영**: 머리줄 하나 (C, 툴팁 알림), 칸 이름표 "top -Z" / "front +Y" (Maya "top -Y" / "front -Z"), 아주 먼 줌아웃에서 격자 안 그림, 링 옆 목록은 Maya 에 없는 배치 | 6 → **일부** | 3×1 = **3** | step_161.md 「남은 것」 |
| 18 | 애니 | Visualize 2 / 10 (Ghost Selected / Ghosting Editor, Animation Snapshot) | **그대로** | 2×2 = **4** | step_145 §3 #15 |
| 19 | 모델링 | #89 Quad Draw 남은 것 (overlay 색, Tab+MMB strip — `operators/quad_draw.py:1053`, Ctrl+Shift+RMB 메뉴), Insert Edge Loop Auto complete, Lattice local, nonlinear 근사 | **그대로** | 2×2 = **4** | #89, step_144 |
| 20 | 모델링 | Mesh / Edit Mesh 정확도 (Connect ≥ 4, Automatic Less distortion, Bevel Chamfer off / Mitering), Mesh Display 15 / 39 (Set Vertex Normal, Apply Color, Color Set Rename / Modify, Material Blend) | **그대로** | 2×2 = **4** | step_139*.md, `greyed.py` |
| 21 | UI | 매니퓰레이터 / 링 세부 (목록 줄 22 vs 20 px, dead zone, ❒ 글리프, 압출 매니퓰레이터 회전 고리 / world·local 토글 없음, 엣지 / 정점 압출 · 베벨은 화살표 하나) | **그대로** | 3×1 = **3** | step_151.md |
| 22 | UI | HUD Poly Count / Object / Selection Details = Blender `overlay.show_stats` (`ui/menu_map.py:561`), Frame Rate = Preferences 열기 (`:626`) | **그대로** | 3×1 = **3** | step_151.md |
| 23 | FX | Generate 2 / 50, nHair 2 / 54, nConstraint 0 / 19, Toon 1 / 20, Fluids 4 / 25, nCache 3 / 20 — notice 만 | **그대로** | 1×4 = **4** | step_145 §3 #22 |
| 24 | 기타 | 열기 대화 문구 (Blender), 두 번째 창 레이아웃, 도구 설정이 세션 사이에 안 남음; Toggle Dependent 의 "첫 선택" 은 추정 (Blender 에 선택 순서 없음) | **그대로** | 2×1 = **2** | step_138, step_162 |
| 25 | 기타 | Undo 세부 (옵션 창 Apply 따로 step 아님, Undo History 이름 = Maya 메뉴 라벨), 격자 / 메쉬 밑 Blender 주황 1 px (C), 관절 라벨 크기 · 위치 추정 | **그대로** | 1×1 = **1** | step_147, 149, 159 |

검증 / 정리 빚 (Maya 사용자에게 안 보임):

- **GUI 전체 묶음**: 마지막 = step 156 (1688 / 1691). 157–162 는 바뀐 모듈의 GUI 파일만 (사용자 규칙 10-23 / 24). step 161 이 RMB 목록 /
  보고 위치를 바꿨으므로 `gui_manual_sweep` (M78 Stacked 안내 = "INFO report" 검사) 가 지금도 통과하는지 미확인 [U].
- **5.x**: 155 / 156 만 5.2.3 부분 실행 (`-k step155,…` 56 / 56, `-k step156,…` 40 / 40). 157 은 "5.x 에서 FModifier `name` 검증 안 함",
  158–162 는 5.x 실행 기록 없음.
- `gui_step129_panel_toolbar` 머리 폭 의존 실패 (step_156.md, step_161.md 「남은 것」) 그대로.
- `docs/compat_5x.md` 테마 행 (:30-31) / 「테마 차이」 (:108-) — step 130 뒤 없는 기능, 지울 글 (154 에서 넘어옴, 그대로).
- 코드 정리 이월: `ui/outliner.py:9,133-137` `allset_outliner_rows`, `marking/rmb_items.py:208-209,322-332` 옛 VERTEX_PERIMETER /
  SHELL_BORDER 규칙 (그대로).
- 고쳐진 이슈 19 개 닫기 (릴리스 때).
- mayapy 로 다시 확인할 것: 킷이 쓴 `deformerWeights` XML 을 Maya 가 읽는지 (step 159), Hypershade 면 위 놓기 (step 162), §4 BS1 의
  DAG 규칙 (Maya 쪽은 [K] — research 에 근거 줄이 없음, `research/maya/concepts.md` 에 visibility 상속 항목 없음).

## 4. Blindspot (어느 「남은 것」 / 이슈 / backlog / manual_checks 에도 없던 것, grep 확인)

| # | Maya 동작 | 킷 지금 (근거) | F×S |
|---|---|---|---|
| BS1 | **DAG 상속**: transform 의 visibility off = 자손 전부 안 보임; Delete = 자손까지 지움; Export Selection = 선택 + 자손; display layer 에 넣은 그룹의 V off = 자손도; Isolate Select (Ctrl+1) 한 그룹 = 자손도 보임 [K] — Maya 사용자는 Ctrl+G 다음 h 로 그룹을 숨긴다 | `operators/visibility.py:49-55` `_hide` 는 고른 오브젝트의 `hide_viewport` 만 (Blender 는 이 깃발을 자식에 안 물려줌 [K]); Delete (object mode) = IC `object.delete` (`keymap/ic_4_5.py:2298`, 메뉴 `ui/menu_map.py:157`) — 자식은 남음; Export Selection = `use_selection` / `selected_objects` 만 (`operators/file_io.py:99,106,118,125,577`); Layer Editor 는 선택만 멤버로 (`ui/layer_editor.py:230,250`) 하고 숨김은 멤버만; Ctrl+1 = `view3d.localview` (`keymap/maya_patches.py:474`) — 고른 것만. **킷 안에서도 어긋남**: Ctrl+X 는 자손까지 (`operators/global_keys4.py:24-32` `cut_targets`), Duplicate / Freeze 도 자손, 와이어 강조도 자손 (step 161). grep "children" `operators/visibility.py` 0 건 | 3×3 = **9** |
| BS2 | **셸프 버튼 더블클릭 = 그 명령의 옵션** (doubleClickCommand, research/maya/shelves.md:14-16) | `ui/shelf.py:273-286`: 두 번째 클릭 / DOUBLE_CLICK = `screen.redo_last` — step 147 뒤 셸프 명령은 `undo_steps.command` 로 돌아 등록되지 않으므로 redo 패널이 셸프 명령 것이 아님 [I]. Ctrl+클릭 (`self.option = True`, :289) 은 옵션 상자로 맞음. step 154 가 manual_checks Step 12 를 "의심" 으로만 적음 — 이번에 코드 근거 | 3×2 = **6** |
| BS3 | **Smooth Mesh Preview to Polygons** = smooth preview 만 실제 면으로 | `ui/menu_map.py:268` `object.convert(target='MESH')` = 모든 modifier 굽기 (Armature skinCluster, 킷 디포머, Bevel …) [I]. 디포머가 있는 메시에서 Maya 사용자는 리그를 잃음 | 2×3 = **6** |
| BS4 | **Select / Delete All by Type > IK Handles / Clusters** | 킷은 IK 손잡이 (`operators/skin.py:108` `ikHandleN` 엠프티, IK constraint target) 와 cluster 를 만들지만 메뉴는 회색 + "Blender has no selection by this type" / "no node of this type" (`ui/notices.py:395,418`) — notice 가 사실과 다름 (step 101 menu honesty 규칙) | 2×2 = **4** |
| BS5 | **Python 사용자의 `maya.cmds`**: `cmds.parent`, `cmds.group`, `cmds.duplicate`, `cmds.setKeyframe`, `cmds.playbackOptions`, `cmds.file` 이 가장 흔한 첫 줄들 | `command_line/cmds_shim.py` 17 함수 (§3 #15) — 없는 함수는 AttributeError [I]. 「남은 것」 어디에도 cmds 범위가 적혀 있지 않음 | 2×2 = **4** |
| BS6 | **Dope Sheet Curves > Euler Filter / Smooth Filter** (Graph Editor 와 같은 명령) | Graph Editor 에선 작동, Dope Sheet 같은 메뉴에선 회색 (`edgrey.py` "Dope Sheet/Curves 17 / 34") — 같은 Maya 명령이 편집기마다 다름 | 1×2 = 2 |

확인했고 blindspot 아님 (근거): F = 자식 없이 / Ctrl+Shift+F = 자식 포함 (`docs/keymap_mapping.md:122-124`, Maya
FrameSelectedWithoutChildren 과 같음), 템플릿 범위 1–120 / 24 fps (`tools/make_startup.py:511-514`), Time Slider fps 메뉴 · Playback
Speed (`ui/time_slider.py:149,433`), Look Through Selected (`ui/panel_menus.py:181`), Snap to Projected Center (`ui/status_line.py:171`),
.ma / .mb 를 못 읽는다는 것 (README.md:184, `operators/file_io.py:664`), Increment and Save (`keymap_mapping.md` Ctrl+Alt+S), 핫키 468
개 전부 분류 (구현 202 → **209**, IC 27, 해당 없음 171 → **164**, macOS 68).

## 5. 열린 GitHub 이슈 (2026-10-24, 20 개) — 코드 판정

| # | 제목 (줄임) | 코드 | 근거 |
|---|---|---|---|
| 101 | 렌더 기본 | 끝 | step 152 (`operators/default_light.py`, `render_batch.py`) |
| 100 | 상태 줄 Blender 문구 | 끝 | step 151 (`template_status_info` 없음) + step 161 (`results.result`) |
| 99 | RMB 링 크기 | 끝 | step 151 `marking/engine.Layout.ring_rect` |
| 98 | Move 매니퓰레이터 툴팁 | 끝 | step 151 `ui/manipulator.py` `use_tooltip = False` |
| 97 | INPUTS "Armature" | **끝 (이번에 새로)** | step 158 `operators/skin.py:405` |
| 96 | Graph Editor 이름 / 강조 / 미터 | 끝 (미터는 C, step 150 기록) | step 150 |
| 95 | ffd1Lattice Scale 0.02 | 끝 | step 148 |
| 94 | 비균일 스케일 Bind | 끝 | step 149 `skin.closest_distance_weights` |
| 93 | Delete 뒤 pCube2 | 끝 | step 149 `operators/naming.py` `drop_orphans` |
| 92 / 86 | Adjust Last Operation 패널 | 끝 | step 147 `@undo_steps.no_redo_panel` |
| 91 | 재생 중 선택 와이어 | 끝 | step 149 |
| 90 | 5.x Paint Skin Weights ❒ | 끝 | step 153 `compat.unified_paint_settings` |
| 89 | Quad Draw 남은 것 | **열림** | `operators/quad_draw.py:1053` ("Tab+MMB … not in the kit"), overlay 색 / Ctrl+Shift+RMB 회색 |
| 88 | Mesh Tools undo step | 끝 | step 147 `undo_steps.py` |
| 87 | CB RMB = Blender 메뉴 | 끝 | step 148 / 158 `allset.cb_channel_drag` `_on_rmb` |
| 85 | 좁은 도크 잘림 | 끝 (AE 노드 탭 · 헤더 버튼 재측정 안 됨, 154 §6 그대로) | step 148 |
| 83 | UI 1.5 빈 두 줄 | 끝 | step 148 `PANE_TOP = 1.6` |
| 82 | file 메뉴 옵션 상자 | 끝 | step 146 / 162 |
| 81 | Maya UI reset | **끝 (이번에 새로)** | step 160 `switch.reset_workspace`, Windows > Workspaces > Reset "…" to Factory Default |

정리: **열림 20, 코드로 끝 19, 코드로도 열림 1 (#89)**. #84 는 이미 닫힘.

## 6. 수치 (감사 10 → 지금)

| 수치 | step 154 (e26b969) | 지금 (2cd3406) |
|---|---|---|
| 대응표 | 29 / 2 / 0 / 2 | **29 / 2 / 0 / 2** |
| 메뉴 leaves 작동 (unique 1318) | 600 (45.5 %) | **649 (49.2 %)** |
| 메뉴 세트별 합 (1486) | 675 (step 159 이전 기록) | **720 (48.5 %)**, 회색 + notice 없음 0 |
| Graph Editor / Dope Sheet / UV Editor 메뉴 막대 | 145 / 120 / 95 | **154 / 124 / 110** (229 / 181 / 172) |
| Hypershade / Render Settings / Script Editor | — | 114 / 249, 10 / 21, 32 / 59 |
| 핫키 구현 | 202 | **209** (해당 없음 164) |
| 헤드리스 전체 | 1398 | 1518 (step 162 기록, 이번 레인은 안 돌림) |
| 열린 이슈 | 20 (코드로 열림 3) | 20 (코드로 열림 **1**) |

메뉴별 약한 곳 (작동 / 전체, unique): nConstraint 0 / 19, Generate 2 / 50, nHair 2 / 54, Toon 1 / 20, Control 1 / 14, Texturing 1 / 8,
nCache 3 / 20, Fluids 4 / 25, Stereo 1 / 6, Effects 2 / 11, Surfaces 8 / 41, Visualize 2 / 10, nParticles 7 / 25, Lighting 5 / 14,
Fields 14 / 38, Mesh Display 15 / 39, nCloth 5 / 13, Deform 30 / 74, Modify 37 / 90. 많이 오른 것: Skeleton 13 → 51 / 54, Curves 16 → 21,
Edit Mesh 25 / 28, UV 16 / 19.

작동으로 세는 항목 649 중 **252 가 Blender 연산자를 그대로 부름** (`tmp/audit163a_map.py`; 397 은 `allset.*`). 그대로 부르는 것 중
Maya 의미와 다른 것이 BS1 (`object.delete`), BS3 (`object.convert`), §3 #22 (`overlay.show_stats`, `userpref_show`) — 나머지 252 개는
하나씩 대조하지 않음 [U] (§7 #9).

## 7. manual_checks 정리 (`docs/manual_checks.md`)

- 전: **620 항목, 81 체크, 539 열림** (step 154 뒤 579 / 81 / 498 에 155–162 가 41 항목 추가).
- 후: **620 항목, 86 체크, 534 열림**. 지운 항목 0 (기능이 없어진 항목을 못 찾음 — 낡은 것은 문구를 고침).
- **체크 5** (모든 조건을 GUI 테스트가 확인):
  - Step 156 CV Curve Tool 3 클릭 대기 → 4 번째 → Enter (`gui_step156_curves` `s_cv_waits` / `s_cv_done`, 점 4 개 · 끝점 = 클릭).
  - Step 158 빈 곳 RMB = Channels 메뉴, Ctrl+RMB = Edit 메뉴 (`gui_step158_cb_menus`).
  - Step 160 Reset "…" to Factory Default 가 망친 레이아웃을 되돌리고 이름 유지 (`gui_step160_workspaces`).
  - Step 161 Space tap 정사영 30 단위 · 칸마다 격자 · side 줌 기억 (`gui_step161_views` G3), 계층 강조 (`gui_step161_views` G4).
- **낡은 문구 고침 8 항목** (항목은 남김): Step 9 마킹 메뉴 `[]` (결과 = `option_kind` 에 따름, step 103 / 147), Step 12 셸프 더블클릭
  (BS2 주의 추가), Step 45 네 뷰 격자 ("front / side 격자 없음" 은 step 161 이 틀린 읽기로 정정 — 비스듬한 사용자 정사영 부분만 남김),
  Step 51 옵션 상자 (창 아이콘 → 라벨 끝 ❒, 길게 누르기 = 옵션 창), Step 52 RMB 목록 (오른쪽 열 → 한 열), Step 54 조명 (역제곱 보정 →
  Maya No Decay, step 137; 안내는 Command Line 결과 칸), Step 78 체크 항목의 근거 ("INFO report (상태 표시줄)" → 결과 칸, step 161),
  Step 102 기본 프로젝트 경로 (`Documents/allset/…` → `Documents/Maya Workflow Kit/…`, step 111 / 125).
- **이름만 고침 16 곳**: "Allset 레이아웃 / 템플릿" → "Maya Workflow Kit 레이아웃" (step 111 / 125 이름; Step 125 의 「Allset」 글자 검사
  항목은 그대로).
- 체크 안 함 (GUI 테스트는 있지만 일부만): Step 155 키 (5 / 6 안 봄), Move UV Shell (클릭 / 드래그 안 봄); Step 156 EP (X 스냅 안 봄),
  원호 (2 점 안 봄); Step 157 Only Curve (박스 드래그 안 봄); Step 159 라벨 (Rename 안 봄); Step 161 Ctrl+G ("Created pCube1" 안 봄), RMB
  한 열 (끌어 실행 안 봄); Step 162 Toggle (Dependent 안 봄), Non-Deformer (before-only 안 봄).
- 그대로 둔 의심 항목: Step 12 셸프 더블클릭 (BS2 — 손으로 보고 결과를 적을 것), Step 9 / Step 52 의 Adjust Last Operation 기대값
  (항목마다 `option_kind` 가 다름, 코드만으로 종류를 다 못 셈 — `menu_count.py --options` 는 Blender 필요).

## 8. 차이 우선순위 (점수 = 심각도 × 빈도; Maya 사용자 영향 먼저) + 한 단계 backlog 문구

| 순 | 점수 | 차이 (근거) | backlog 제목 · 지시 · 검증 |
|---|---|---|---|
| 1 | **9** | DAG 상속 없음: h / Ctrl+H / CB Visibility / layer V 가 자손을 안 숨김, Delete 가 자손을 남김, Export Selection · Ctrl+1 이 자손 없이 (§4 BS1; `visibility.py:49`, `menu_map.py:157`, `file_io.py:99-125,577`, `layer_editor.py:230`, `maya_patches.py:474`) | **"Maya DAG semantics for parents"** — 먼저 mayapy 로 Maya 규칙 측정 (부모 visibility off → 자식 `isVisible`, `delete` 그룹, `file -exportSelected` 그룹, 레이어 그룹, isolate 그룹) → `research/maya/re/dag_163.md`; Blender 쪽도 헤드리스로 측정 (부모 `hide_viewport` → 자식 `visible_get()`, `object.delete` 뒤 자식). 그 뒤: 숨김은 자손을 view-layer `hide_set` + 표시 (`allset_hidden_by_parent`, 자손 자신의 Visibility 채널은 그대로 = Maya), Delete / Edit > Delete / Outliner Delete 는 `global_keys4.cut_targets` 로 자손까지 + `naming.drop_orphans`, Export Selection / Export Selection to Alembic 은 자손 추가, Ctrl+1 은 자손 포함 localview. 검증: 헤드리스 group1 > pCube1 에서 h → pCube1 안 보임 · Visibility 채널 1, Shift+H / h 로 되돌림; Delete → pCube1 · pCubeShape1 없음; FBX Export Selection 다시 가져오기 = 2 오브젝트; GUI Ctrl+1 스크린샷 |
| 2 | **6** | 셸프 더블클릭 = `redo_last` (step 147 뒤 셸프 명령 패널 아님), 긴 탭 스크롤 없음 (§4 BS2; `shelf.py:273-286`) | **"Shelf double-click and overflow"** — 더블클릭 = Ctrl+클릭과 같은 옵션 상자 (`option = True` 경로, Maya doubleClickCommand), 첫 클릭의 실행은 그대로 한 번; 셸프 줄이 넘치면 Maya 처럼 휠 / 끝 화살표로 스크롤. 검증: 헤드리스 같은 버튼 두 번 invoke → 큐브 1 개 + 옵션 창 연산자 실행; GUI 1600 px UI 1.25 Poly Modeling 끝 버튼 보임 |
| 3 | **6** | UV Editor 나머지 (Unfold / Cut / Sew 브러시, Map / Straighten Border, Layout Along, Unmapped Faces, UV Statistics HUD, 3D View 셸 테두리) (§3 #3) | **"UV Editor finish"** — mayapy 측정 (step 155 방식) 으로 Map Border / Straighten Border / Layout Along / Stack Similar / Distribute UVs, Select Unmapped / Back-Facing / Texture Borders / To Edge Loop·Ring, View HUD UV Statistics, 3D View 셸 테두리 (POST_VIEW). 검증: `tests/test_step*_uv` 에서 mayapy 정답과 UV 비교 1e-4, menu_count UV Editor ≥ 130 / 172 |
| 4 | **6** | Graph Editor / Dope Sheet 나머지: Buffer Curves, Weighted Tangents, Pin Channel, Dope Sheet Curves 필터 회색, Blender 키에 Default Tangent 없음 (§3 #4, BS6) | **"Graph Editor depth 2"** — Buffer Curve (스냅샷 + Swap = 킷 F-curve 복사본 그리기), Weighted / Non-weighted Tangents (`FCurve` 핸들 길이 고정 여부 — 측정 먼저), Pin Channel, Dope Sheet Curves 를 Graph Editor 와 같은 MAP 으로, `anim.keyframe_insert_by_name` 메뉴 항목을 킷 set_key 로 바꿔 Default Tangent 적용. 검증: 헤드리스 mayapy 값 비교 (가중 핸들), menu_count Graph Editor ≥ 165 / 229, Dope Sheet Curves ≥ 25 / 34 |
| 5 | **6** | 다른 편집기 선택 수정키 (Outliner Shift 범위, Ctrl = toggle, box XOR) (§3 #5) | **"Selection modifiers outside the 3D View"** — Outliner / Graph / Dope Sheet / UV 에 첫 자리 PASS_THROUGH 연산자 (`allset.select_maya_2d`): Ctrl = 해제, Shift 박스 = XOR (선택 깃발 직접), Outliner Shift+클릭 = 범위 (Maya). 검증: 헤드리스 각 편집기 4 변형 결과 표, GUI Outliner 범위 클릭 |
| 6 | **6** | Smooth Mesh Preview to Polygons 가 모든 modifier 를 구움 (§4 BS3; `menu_map.py:268`) | **"Convert Smooth Mesh Preview Maya's way"** — mayapy 측정 (skin 된 메시 / 디포머 없는 메시 / preview 없는 메시: 결과 history, 경고) → `allset.smooth_to_polygons`: "Maya Smooth Preview" Subsurf 만 적용 (스택의 그 자리, `modifier_apply`), preview 없으면 Maya 경고. 검증: 헤드리스 Bind 한 메시 → 변환 뒤 skinCluster1 남음, 면 수 × 4^level |
| 7 | **6** | 리그 나머지 + IK Handles / Clusters 회색 · 틀린 notice (§3 #7, §4 BS4) | **"Rig selection by type and skin tools 2"** — Select / Delete All by Type > IK Handles (IK constraint target 엠프티) · Clusters (킷 cluster 표시), notice 정리; Move Weights to Influences, Weight Post Normalization (mayapy 측정); 킷 XML 을 mayapy `deformerWeights -im` 으로 읽어 왕복. 검증: test_step101 (notice 규칙) 통과, 헤드리스 선택 결과, mayapy 왕복 가중치 1e-6 |
| 8 | **6** | Curves / Surfaces 나머지 — Surfaces 8 / 41 세 감사째 (§3 #8) | **"Surfaces basics"** — Loft / Planar / Revolve / Extrude / Birail 1 (mayapy 측정, 결과 = Blender NURBS surface 또는 메시 — 표현 측정 먼저), 그리기 도구가 다음 곡선 계속 (Maya), V / C 스냅. 검증: mayapy CV 비교, menu_count Surfaces ≥ 15 / 41 |
| 9 | 6 | 렌더 (lambert1 1.25 배, F12 기본 조명, Render Setup) (§3 #9) | "Render parity 2" — Principled base color × 0.8 로 Diffuse 0.8 흉내 (렌더 픽셀을 Maya 와 비교), F12 를 킷 Render Current Frame 로 (Maya 키 없음 → 메뉴만) — 측정 뒤 결정 |
| 10 | 6 | Preferences / Hotkey Editor, Reference Editor (§3 #10, #11) | "Maya Preferences window" — 킷 창 하나 (Working Units, fps, Up Axis 안내, Undo 안내, 키 바꾸기 = Blender 키맵 편집기로 가는 버튼) |
| 11 | 5 | 옵션 상자 몸짓 (C, 5.x) (§3 #12) | 손 확인만 (manual_checks Step 146) |
| 12 | 4 | CB 상태 색, Hypershade 탭 / 옵션, 스크립팅 cmds 17 함수, Visualize, #89, 메쉬 정확도, FX (§3 #13–#15, #18–#20, #23) | cmds: "maya.cmds look-alike 2" — parent / group / duplicate / setKeyframe / playbackOptions / spaceLocator 를 킷 연산자 위에 (반환값 Maya 형식), 헤드리스로 Maya 문서의 반환값 비교 |

모르는 것 (Blender 없이 못 본 것): BS1 의 Blender 쪽 (부모 `hide_viewport` 가 자식에 안 퍼진다, `object.delete` 가 자식을 남긴다) 은
[K] — 헤드리스 한 번으로 확인할 것; BS2 더블클릭이 실제로 무엇을 여는지; BS3 가 skinCluster 를 정말 굽는지 (`object.convert` 는
evaluated mesh 를 씀 [K]); Maya 쪽 DAG 규칙도 research 에 줄이 없음 [K]; 작동 항목 252 개의 Blender 연산자 의미 대조는 안 함;
`gui_manual_sweep` 이 step 161 뒤 통과하는지; 158–162 의 5.x.
