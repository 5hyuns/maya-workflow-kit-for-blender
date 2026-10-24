# Step 173 lane A — 끝난 것, 남은 것, blindspot (재점검 12차)

User request (lane A 부분, 번역 범위): "research/README.md 대응표·docs/PLAN.md·docs/steps/*.md 「남은 것」·docs/manual_checks.md를
모아 끝난 것 지우고 남은 것 정리 (know-your-unknowns blindspot으로 놓친 것 보완)" — 기준 (2026-10-19): "기본 Maya 에 Blender 기능이 붙은
모습", 칭찬 말고 차이만, Maya 사용자가 실제로 느끼는 것 먼저.

Paper lane, **Blender 실행 없음**. 입력: `docs/steps/step_163_remaining.md` (감사 11 정리 목록), `step_163.md` 우선순위 표,
`step_164.md` … `step_172.md` 의 「남은 것」 (git `416563f..c8d006c` = 164–172 커밋 13 개), `docs/PLAN.md` 「재점검 11차」,
`gh issue list --state all --limit 120` (2026-10-25, 읽기만), `docs/manual_checks.md`. 판정은 HEAD c8d006c 의 `src/allset` 을 grep /
읽기로 다시 확인한 것 ("[I]" = 코드를 읽은 것, 돌린 것 아님). 메뉴 수치 = `python tools/menu_count.py` (bpy stub, Blender 없이) +
`tmp/audit154a/greyed.py` (메뉴별 작동 / 회색 목록, 출력 `tmp/audit173a/greyed_list.txt`, `greyed_common.txt`). 판정은 delegated.
점수 = 심각도 S (1–3) × 빈도 F (1–3) — 감사 11 의 F 1–5 × S 1–4 와 척도가 다르므로 점수끼리 직접 비교하지 말 것.

## 1. 구현률 — research/README.md 대응표 (33 행)

| 묶음 | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | **13** | 0 | 0 | 0 |
| UI (9) | 8 | 1 — 테마 (Maya 회색) | 0 | 0 |
| 개념 (11) | 9 | 0 | 0 | 2 — 분리 rotate / scale pivot, Y-up |
| **합계 (33)** | **30 (91 %)** | **1 (3 %)** | **0** | **2 (6 %)** |

감사 11 (29 / 2 / 0 / 2) 에서 **움직인 행 하나**:

- **"Shift 클릭=토글, Ctrl=해제, Ctrl+Shift=추가" Partial → Done**: step 170 (`operators/select_2d.py`, `keymap/maya_patches.py`
  `SELECT_2D_CLICKS` / `SELECT_2D_BOXES`, GUI 실측 `research/maya/re/select_mods_170.md`); README 행은 step 170 이 이미 Done 으로 고침.
  남은 것: Outliner 범위 기준점 = Blender active 행 (Maya = 마지막 일반 클릭), NLA / Node Editor 재측정 안 함, 실제 손 확인
  (manual_checks Step 170; `event_simulate` 는 드래그 / Ctrl 클릭의 수정키를 안 실음).
- **테마 (Partial, 그대로)**: 킷은 테마를 싣지 않음 (step 130). 164–171 이 그린 색도 뷰포트 안 (고스트 `ui/ghosting.py`, 와이어).
  위젯 / 메뉴 / Outliner / Graph 키 색은 사용자 테마 그대로.
- 감사 11 이 "Group = Empty 행에 숨어 있다" 고 한 DAG 상속은 step 164 로 끝 (§2) — 행은 Done 그대로가 맞음.
- 대응표 밖이지만 Done 행 아래 숨은 차이 둘 (§4 BS1, BS3): "Space 핫박스 / 마킹메뉴" 행의 **G = Repeat Last 가 메뉴 명령을 반복하지
  않음** [I], "Display Layer = Layer Editor" 행의 **Anim 탭이 글뿐** (Animation Layers 없음). 행을 Partial 로 바꿀지는 측정 뒤 —
  이번엔 수치를 그대로 둠 (delegated).

## 2. 감사 11 뒤 끝난 것 — 목록에서 지움

| 항목 (step_163_remaining.md §3 / §4, step_163.md G) | 끝낸 것 (근거) |
|---|---|
| §3 #1 / BS1 DAG 상속 없음 (9) | step 164: `operators/dag.py` (`sync`, `delete_hierarchy`, `selected_hierarchy`, `allset.delete`, `allset.isolate`); h / Ctrl+H / layer V 가 자손에, Delete · Export Selection · Ctrl+1 이 자손 포함. 남은 부분 §3 R23 |
| step_163.md G4 / §3 #13 일부 컴포넌트 모드 Channel Box | step 165: `ui/channel_box.py` `component_mode`, `ui/cb_points.py` (CVs 줄 / 표); 남은 부분 §3 R12 |
| step_163.md G1 RMB DG Traversal / Inputs / Outputs 회색 | step 165: `marking/menus.py` `NodeList`, `marking/rmb_nodes.py` (`allset.mm_node*`) |
| §3 #3 일부 · BS6 · §3 #7 일부 · BS4 메뉴 쌍둥이 (UV Editor Tools Unfold / Cut / Sew / Pin, Dope Sheet Curves 필터, IK Handles / Clusters by type) | step 166: `tools/menu_consistency.py` 0 쌍, `ui/menu_map.py` `TWINS`, `allset.dope_graph_op`, `operators/by_type.py`; Dope Sheet 124 → 130, UV Editor 110 → 118 |
| §3 #2 / BS2 셸프 더블클릭 = `redo_last`, 긴 탭 스크롤 없음 | step 167: `ui/shelf.py` `option_box` → `allset.menu_option_box`, `row_layout` / `scroll_rects`, 휠 = "Image" 첫 자리 |
| §3 #6 / BS3 Smooth Mesh Preview to Polygons = `object.convert` | step 168: `allset.smooth_to_polygons` (`operators/modify_maya.py`), skinCluster1 남음; Modify 37 → **57 / 90** |
| step_163.md 우선순위 "Deform 41 %" | step 169: kit Wire (`operators/wire_deformer.py`, mayapy 1e-5), Wire / ShrinkWrap / Lattice 편집, Paint Weights 창; Deform 30 → **48 / 74**, generic 9 → 0 |
| §3 #5 / README Partial 선택 수정키 | step 170 (§1) |
| §3 #18 Visualize 2 / 10 (네 감사째) | step 171: `operators/anim_snapshot.py`, `ui/ghosting.py`; Visualize **8 / 10** |
| 검증 빚 "GUI 전체 묶음 (마지막 step 156)" · `gui_step129_panel_toolbar` · `gui_manual_sweep` step 161 뒤 | step 172: GUI 전체 165 파일 1823 / 1827 → 실패 4 를 고침 (step52 / step91 의 RMB 목록 기대값, step143 #82 불안정 1) — `gui_step129_panel_toolbar` 실패 기록 없음 |
| 고쳐진 이슈 19 개 닫기 | step 172: #81–#101 닫힘 (§5) |

## 3. 남은 것 한 목록 (step_163_remaining.md §3 재확인 + 164–172 「남은 것」 + 이번 blindspot)

점수 S×F (각 1–3). 판정: **일부** / **그대로** / **새**. 메뉴 수는 `greyed_list.txt` (unique, HEAD c8d006c).

| # | 영역 | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|---|
| R1 | 애니 / 모델링 | **G (Repeat Last) / Edit > Repeat / Recent Commands 가 메뉴 · 셸프 · 마킹 메뉴 명령을 반복하지 않음** [I] (§4 BS1) | 새 | 2×3 = **6** | 이번 |
| R2 | UI | **3D View 패널 메뉴 / 패널 툴바의 회색 36 개가 menu_count · notice 규칙 · menu_consistency 밖** — 일반 툴팁만, 그중 킷에 상대가 있는 것도 회색 (§4 BS2) | 새 | 2×3 = **6** | 이번 |
| R3 | UV | **UV Editor 나머지** 118 / 172: Modify (Map / Straighten Border, Layout Along, Stack Similar, Distribute UVs, Match Grid, Cycle, Symmetrize, Warp Image), Select (Unmapped Faces, Back / Front-Facing, Non-Overlapping, Texture Borders, To Edge Loop / Ring), View (HUD UV Statistics / Position, Isolate Load / Add / Remove), Cut/Sew Auto Seams / Split, Tools 브러시 (Smear / Smudge / Lattice / Symmetrize), UV Toolkit 1 / 3, 3D View 셸 테두리, Move UV Shell Prevent Overlap. Tools Unfold / Cut / Sew / Pin 은 브러시가 아니라 선택에 한 번 (step 166 delegated) | 일부 | 2×3 = **6** | step_155.md, step_166.md |
| R4 | 애니 | **Graph Editor / Dope Sheet 나머지** 154 / 229 · 130 / 181: Buffer Curve Swap 없음 (`ui/graph_editor.py:18` ghost curve 표시만), Weighted / Non-weighted Tangents (`ui/notices.py:483`), Pin Channel, Rotation Interp, Key Sync / Peak Removal, List Load / Add Selected / Bookmarks, Show 16 / 34, Add Key Tool; 섞인 곡선에서 Translate 가 미터 (C, step 150); Blender 자체 I / Set Key on Animated 에 Default Tangent 없음; Dope Sheet Isolate Curve 는 Graph Editor 에서만 숨김 | 일부 | 2×3 = **6** | step_157.md, step_166.md |
| R5 | 애니 | **Animation Layers 없음**: Layer Editor Anim 탭 = 안내 글 (`ui/layer_editor.py:499-501,530-531`), Relationship Editors > Animation Layers = NLA 창, Time Slider "No Anim Layer" 고정 (`ui/time_slider.py:141`) (§4 BS3) | 새 (어느 「남은 것」 에도 없음) | 3×2 = **6** | 이번, research/maya/workflows/animation.md:43,75,106 |
| R6 | 리깅 | **리그 나머지**: Skin 19 / 28 (Interactive Bind, Post Normalization, Move Skinned Joints, Move Weights to Influences, Substitute Geometry, Bake Deformation, Export / Import Weight Maps), Key > IK/FK Keys 4, HumanIK, Character Sets 11 (Key 22 / 41), Deform dead 12 (Tension, Solidify, Morph, Wrinkle, Pose Interpolator, Sculpt, Jiggle, Blend Shape Swap, Add Holder …), Wire holders / Crossing Effect / Tension / 4 개 넘는 dropoff locator, Bind = rest 포즈, 킷 XML 을 Maya 가 읽는지 미확인 | 일부 | 3×2 = **6** | step_159.md, step_169.md |
| R7 | 모델링 | **Surfaces 8 / 41 (다섯 감사째) + Curves 21 / 36** (Edit Curve Tool, Intersect, Extend, Fit B-spline, CV Hardness, Align, Bend / Curl / Scale Curvature, Lock Length); Rebuild [U], 그리기 도구가 곡선 하나 뒤 끝남, V / C 스냅 · 표면 위 그리기 없음 | 그대로 | 3×2 = **6** | step_156.md |
| R8 | 파일 | **Reference Editor** = Outliner Blender File 모드 (`ui/menu_map.py:133`), Reload / Unload / Replace / Import Objects from Reference 없음, Namespace Editor 회색 (`ui/notices.py:70`) | 그대로 | 2×2 = **4** | step_145 BS4 |
| R9 | UI | **스크립팅**: `maya.cmds` 닮은꼴 17 함수 그대로 (`command_line/cmds_shim.py:135-488`: ls select move rotate scale getAttr setAttr xform polyCube/Sphere/Cylinder/Plane delete rename objExists listRelatives currentTime) — `parent` `group` `duplicate` `setKeyframe` `playbackOptions` `spaceLocator` `file` 없음; MEL 은 결정 5; Script Editor 32 / 59 | 그대로 (감사 11 BS5, backlog 에 안 들어감) | 2×2 = **4** | step_163_remaining.md §4 BS5 |
| R10 | 렌더 | lambert1 1.25 배 밝음 (Principled 에 Diffuse 0.8 없음), Blender F12 / Ctrl+Alt+Enter 에 기본 조명 없음, Render Setup 회색 (`ui/status_line.py:543`), Lighting 5 / 14 (Ambient / Volume Light 회색), Render Sequence All Layers / Cameras · Render Region 없음 | 그대로 | 2×2 = **4** | step_152*.md |
| R11 | UI | Maya Preferences / Hotkey Editor = Blender Preferences (`ui/menu_map.py:296-297`), Shelf / Marking Menu / Panel Editor 회색 (`ui/notices.py:30`) | 그대로 | 2×2 = **4** | step_145 BS1 / BS2 |
| R12 | 모델링 | Mesh / Edit Mesh 정확도 (Connect ≥ 4, Automatic Less distortion, Bevel Chamfer off / Mitering), Mesh Display 15 / 39, Edit Mesh 회색 3 (Reorder Vertices, Assign Invisible Faces, Project Curve on Mesh), Mesh Copy / Paste Attributes, Transfer Vertex Order | 그대로 | 2×2 = **4** | step_139*.md |
| R13 | UI | 옵션 상자 ❒ 부분 클릭 (C, #82 측정), 5.x 메뉴가 옵션 창 아래 열린 채 (`compat.menus_close_on_leave`), `gui_step143_user` #82 박스 클릭이 묶음 안에서만 한 번 실패 (step 172) | 그대로 | 1×3 = **3** | step_146, 153, 172 |
| R14 | UI | Channel Box 나머지: 상태 색 하나 (keyed 빨강만; Maya driven 노랑 / expression 보라 / muted 갈색 / constraint 파랑, research/maya/channel_box.md:138-139), CVs 표가 자체 3 줄 스크롤 아님, 곡선 / 격자 편집 모드에 CV 표 없음, 고른 노드 줄 파랑 강조 없음, DG Traversal 한 단계 · "More..." 없음 | 일부 | 1×3 = **3** | step_158.md, step_165.md |
| R15 | UI | 네 뷰 / 정사영: 칸 이름표가 Blender 축 "top -Z" / "front +Y" / "side -X" (`ui/view_furniture.py:51-52`; Maya "top -Y" / "front -Z" / "side -X"), 머리줄 하나 (C, 툴팁), RMB 목록 링 옆 (step 161 규칙, step 172 가 테스트를 맞춤 — Maya 는 아래 + 창 밖으로; 판단 보류, manual_checks Step 161) | 그대로 | 1×3 = **3** | step_163.md G2 G3 |
| R16 | UI | 매니퓰레이터 / 링 세부 (목록 줄 22 vs 20 px, dead zone, 압출 매니퓰레이터 회전 고리 / world·local 토글 없음, 엣지 / 정점 압출 · 베벨 화살표 하나) | 그대로 | 1×3 = **3** | step_151.md |
| R17 | 모델링 | Create > Polygon Primitives 회색 7: Pipe, Helix, Gear, Soccer Ball, Super Ellipse, Spherical Harmonics, Ultra Shape + Interactive Creation (Maya 기본 꺼짐), Subdiv / Volume Primitives (§4 BS4) | 새 (quant 에만 있었음) | 1×2 = **2** | 이번 |
| R18 | 리깅 | Display > Transform Display > Rotate Pivots / Scale Pivots / Selection Handles 회색, Status Line Select by hierarchy 회색 (`ui/status_line.py:487`), 마스크 Handles / Dynamics 회색 (§4 BS5) | 새 | 2×1 = **2** | 이번 |
| R19 | 렌더 | Hypershade 115 / 249 (Create, Tabs, Options, Graph Clear / Add / Remove / Rearrange, Select All by Type > Shading Groups / Cameras), 드래그는 링크된 재질 안 됨, 면 위 놓기 규칙 미측정 | 그대로 | 1×2 = **2** | step_162.md, step_166.md |
| R20 | 모델링 | #89 Quad Draw 남은 것 (overlay 색, Tab+MMB strip `operators/quad_draw.py:1053`, Ctrl+Shift+RMB), Insert Edge Loop Auto complete, Lattice local | 그대로 | 2×1 = **2** | #89, step_144 |
| R21 | FX | Generate 2 / 50, nHair 2 / 54, nConstraint 0 / 19, Toon 1 / 20, Fluids 4 / 25, nCache 3 / 20, Effects 2 / 11, Fields 14 / 38 — notice 만 | 그대로 | 2×1 = **2** | step_145 §3 #22 |
| R22 | UI | HUD Poly Count / Object / Selection Details = `overlay.show_stats`, Frame Rate = Preferences 열기, HUD Animation Details / Bounding Box 회색 | 그대로 | 1×2 = **2** | step_151.md |
| R23 | 개념 | DAG 나머지: 숨은 부모의 자손은 Blender 에서 선택 불가 (Maya Outliner 는 가능), Blender 자체 H / Outliner 눈은 규칙 밖, `dag.sync` 가 depsgraph 마다 O(n), Isolate 의 Maya 쪽 규칙 [K] | 일부 | 2×1 = **2** | step_164.md |
| R24 | UI | 작업 공간 나머지 (Saved Layouts / Save / Import / Delete Workspace 회색, Modeling - Expert 머리줄, Blender 탭으로 바꾸면 메뉴 세트 안 바뀜) | 그대로 | 1×1 = 1 | step_160.md |
| R25 | 기타 | Modify 회색 33 (Asset 15, Convert subdiv / Paint Effects / displacement / fluid / nParticle 12, Type Manipulator, Paint Scripts / Attributes Tool), Geometry to BBox Combine / Bake Animation, 자세 잡힌 skin 에서 smooth(skin) 순서 차이 | 일부 | 1×1 = 1 | step_168.md |
| R26 | 기타 | Visualize 나머지 (Turntable, Animated Sweep, Ghosting Editor 타입 필터 / Ghosted Objects 목록 / Ghost Driver, 재생 중 고스트 프레임 안 채움, 셰이드 고스트 ≤ 11 / 255) | 일부 | 1×1 = 1 | step_171.md |
| R27 | 기타 | 셸프 탭 줄 화살표 없음 (좁은 창에서 탭 잘림), 체크 / 라디오 메뉴 항목은 Ctrl+Shift 셸프 추가 불가; 선택 수정키 나머지 (§1); Toggle Dependent "첫 선택" 추정; 열기 대화 문구; 도구 설정 세션 사이 | 일부 | 1×1 = 1 | step_167, 170, 162, 138 |
| R28 | 기타 | Undo 세부 (옵션 창 Apply 따로 step 아님), 격자 / 메쉬 밑 Blender 주황 1 px (C), 관절 라벨 크기 · 위치 추정 | 그대로 | 1×1 = 1 | step_147, 149, 159 |

검증 / 정리 빚 (Maya 사용자에게 안 보임):

- **5.x**: 157–171 은 5.x 헤드리스 실행 기록 없음 (step 172 release_check 5.2.2 14 PASS 는 설치 / 켜기 / Make Maya 만). 새 API 를 쓴 곳:
  GN 모디파이어 입력 (`wire_deformer.set_`, step 169), FModifier 이름 (157), `frame_set` 루프 (171).
- `docs/compat_5x.md` 테마 행 (:30-31) / 「테마 차이」 (:108-) — step 130 뒤 없는 기능 (154 부터 이월, 그대로).
- 코드 정리 이월: `ui/outliner.py:9,133-137` `allset_outliner_rows`, `marking/rmb_items.py:208-209,322-332` 옛 VERTEX_PERIMETER /
  SHELL_BORDER 규칙 (그대로).
- mayapy / GUI Maya 로 다시 확인할 것: 킷 `deformerWeights` XML 을 Maya 가 읽는지 (159), Hypershade 면 위 놓기 (162), Isolate 규칙
  (164 [K]), Geometry to Bounding Box 가 Keep original 없이 원본을 지우는지 (168 [U]), Graph Editor Ctrl+클릭 = 일반 클릭 실손 (170).
- `gui_step143_user` 의 #82 박스 클릭 불안정 (step 172, 단독은 통과) — 다음 GUI 전체 때 다시 보기.

## 4. Blindspot (어느 「남은 것」 / 이슈 / backlog / manual_checks 에도 없던 것, grep 확인)

| # | Maya 동작 | 킷 지금 (근거) | S×F |
|---|---|---|---|
| BS1 | **G = "Repeat last menu action"** (research/maya/interaction.md:207, HK:362), Edit > Repeat "<명령>" / Recent Commands List 가 메뉴 · 셸프 명령을 담음 | G / Edit > Repeat = `screen.repeat_last`, Recent Commands = `screen.repeat_history` (`keymap/mapping.py:101`, `ui/menu_map.py:142-143`, 핫박스 `marking/modal.py:401`). 메뉴 / 셸프 / 마킹 메뉴 / MTK 명령은 `marking/modal.py:80-86` `run_action` → `undo_steps.command` 로 **undo=True 없이** 부르므로 등록되지 않음 (`undo_steps.py:4-6` 자체 docstring: "pushes no undo step and is not registered"). 그러면 G 는 그 전에 **키로** 부른 마지막 연산을 반복 [I]. step 147 은 "키로 부르는 명령" 만 G 대상으로 다룸 (`step_147.md:33`, `test_step147_undo.py:139`). 예: 메뉴 Mesh > Combine 뒤 G, 셸프 Cube 뒤 G, Edit Mesh > Bevel (메뉴) 뒤 G | 2×3 = **6** |
| BS2 | **3D View 패널 메뉴 (View / Shading / Lighting / Show / Renderer / Panels) 와 패널 툴바도 Maya 메뉴** — 회색이면 이유가 있어야 하고 (step 101 규칙), 같은 명령이 다른 곳에서 되면 여기서도 돼야 함 (step 166 규칙) | `ui/panel_menus.py:36` `_grey` 28 곳 (Center View of Selection :59, **Camera Attribute Editor... :65** (킷 AE 에 camera 탭 있음 `ui/ae_layout.py:101-110`), Tumble / Track / Dolly Tool :77, Flat Shade All :91, Bounding Box / Points :93-94, Use Selected Lights :117 …), `ui/panel_toolbar.py:323-348` "grey" 8 개 (Camera Attributes, Bookmarks, 2D Pan/Zoom, **Resolution Gate :330**, Field Chart, Motion Blur, AA, X-Ray Active Components). 그리기 = `allset.menu_unavailable(item="Panel menu/<label>")` (`ui/panel_menus.py:574`) → `notices.py` 에 "Panel menu/" 키 **0 개** → 모두 "No Blender equivalent in Maya Workflow Kit yet" (`ui/menu_sets.py:479`). `tools/menu_count.py` / `menu_consistency.py` 는 panel_menus 를 안 셈 (grep 0) | 2×3 = **6** |
| BS3 | **Animation Layers** (Layer Editor Anim 탭, 가중치 / 뮤트 / 솔로, 기본 Additive) — 애니메이터가 매일 쓰는 층 | Anim 탭 = "Blender has no animation layers: layer actions in the Nonlinear Animation editor." 글 (`ui/layer_editor.py:501,530-531`); Blender 4.5 는 slotted action 층 1 개지만 NLA 트랙 (blend Add / Replace, influence, mute / solo) 은 있음 [K]. 2026-10-17 워크플로 표에서 "impossible" 로 접고 (research/maya/workflows/animation.md:106) 그 뒤 어느 「남은 것」 에도 없음 | 3×2 = **6** |
| BS4 | Create > Polygon Primitives 의 Pipe / Helix / Gear / Soccer Ball / Super Ellipse | 회색 + notice (`greyed_common.txt` Create 30 개 중 7) — `step_154_quant.md` 숫자에만 있고 「남은 것」 목록엔 없음. 킷은 Maya 위상 primitive 를 이미 만듦 (`operators/prim_history.py`) | 1×2 = 2 |
| BS5 | Display > Transform Display > Selection Handles / Rotate Pivots / Scale Pivots, Status Line "Select by hierarchy" (루트 선택) | 회색 (`ui/menu_data.py:17`, `ui/status_line.py:487,503`; 마스크 HANDLES / DYNAMICS `ui/status_line.py:48,54` = None). 리거 컨트롤 선택 (Selection Handles) 은 Blender 에 없음 [K]; Local Rotation Axes 만 작동 (`ui/menu_map.py:283`) | 2×1 = 2 |
| BS6 | 측정 도구 자체의 빈 곳: 마킹 메뉴 (step 136) · 메인 / 편집기 메뉴 (101, 104, 166) 는 규칙 테스트가 있지만 **패널 메뉴 / 패널 툴바 / Status Line 회색 위젯 (`_grey` `ui/status_line.py:487-557`)** 은 개수에도 notice 규칙에도 안 들어감 — 메뉴 % 가 오를 때 이 면은 감사에 안 보임 (BS2 의 원인) | — (절차) |

확인했고 blindspot 아님 (근거): Outliner 이름 필터 (`ui/outliner.py:405-408`), AE 아래 Select / Load Attributes / Copy Tab
(`ui/attribute_editor.py:678`), Duplicate Special instance (`operators/duplicate.py:39`), Film Gate / Gate Mask / Safe Action /
Safe Title 패널 툴바 작동 (`ui/panel_toolbar.py:329-335`), Mesh > Cleanup (`ui/menu_map.py:680`), Motion Trail (`ui/menu_map.py:458`),
Light Linking (`ui/menu_map.py:673,799`), Buffer Curve Snapshot (`ui/editor_menu_map.py:93`, Swap 은 R4).

## 5. GitHub 이슈 (2026-10-25, `gh issue list --state all --limit 120`)

- 전체 **101**, 닫힘 **100**, 열림 **1**: **#89** "Quad Draw leftovers" (milestone 0.5.0) — 코드도 열림 (`operators/quad_draw.py:1053`
  "Tab+MMB … not in the kit", overlay 색 / Ctrl+Shift+RMB 회색). 감사 11 의 열린 19 개 (#81–#101) 는 step 172 에서 닫힘.
- 닫혔지만 코드가 이슈 글을 다 보여 주지 않는 것:
  - **#66** Graph Editor Translate 미터: step 137 의 눈금 덮어 그리기는 **보이는 곡선이 모두 길이일 때만**, 마우스가 그 영역에 있을
    때만 (`ui/graph_units.py`); 섞인 곡선 (Translate + Scale) 은 미터 그대로 (C, step 150 기록) → R4.
  - **#82** file 메뉴 옵션 상자: ❒ 부분 클릭은 C (step 146 측정), 길게 누르기 / Shift·Ctrl 로 대체해 닫음 → R13.
  - **#80** (압출 뒤 이동, F9–F12) / **#84** (더블클릭 엣지 루프 오류): 댓글 없이 닫힘, 커밋 `156c2ab`, `f637eb2` (step 143) 가 고침 —
    이슈에 고친 곳 링크가 없음 (사용자에게 안 보임).
  - **#79**: 다른 애드온의 `classes` 가 모듈일 때 — 고침 + 댓글 있음. 그대로.

## 6. 수치 (감사 11 → 지금)

| 수치 | step 163 (2cd3406) | 지금 (c8d006c) |
|---|---|---|
| 대응표 | 29 / 2 / 0 / 2 | **30 / 1 / 0 / 2** |
| 메뉴 leaves 작동 (unique 1318) | 649 (49.2 %) | **699 (53.0 %)** |
| 메뉴 세트별 합 (1486) | 720 (48.5 %) | **806 (54.2 %)**, 회색 + notice 없음 0 |
| Graph Editor / Dope Sheet / UV Editor | 154 / 124 / 110 | 154 / **130** / **118** (229 / 181 / 172) |
| Hypershade / Render Settings / Script Editor | 114 / 10 / 32 | 115 / 10 / 32 |
| 패널 메뉴 / 툴바 회색 (새로 셈) | — | 28 + 8, notice 0 |
| 헤드리스 전체 | 1518 | 1600 / 1600 (step 172 기록; 이 레인은 안 돌림) |
| GUI 전체 | 1688 / 1691 (step 156) | 1823 / 1827 → 고침 (step 172) |
| 열린 이슈 | 20 (코드로 열림 1) | **1** (#89) |
| manual_checks (`- [ ]` / `- [x]` 줄 수) | 620 / 86 (163 의 셈) | 653 / 86 → **663 / 96** (§7) |

메뉴별 많이 오른 것: Modify 37 → 57 / 90, Deform 30 → 48 / 74, Visualize 2 → 8 / 10. 약한 곳 (다섯 감사째 그대로 포함):
nConstraint 0 / 19, Generate 2 / 50, nHair 2 / 54, Toon 1 / 20, Control 1 / 14, Texturing 1 / 8, nCache 3 / 20, Fluids 4 / 25, Stereo 1 / 6,
Effects 2 / 11, **Surfaces 8 / 41**, nParticles 7 / 25, Lighting 5 / 14, Fields 14 / 38, Mesh Display 15 / 39, nCloth 5 / 13.

## 7. manual_checks 정리 (`docs/manual_checks.md`)

- 셈 = `grep -cE '^\s*- \[( |x)\]'` (들여쓴 줄 포함 — 163 의 620 과 셈법이 다를 수 있음).
- 전: **653 항목, 86 체크, 567 열림** (164–171 이 33 항목 추가).
- 후: **663 항목, 96 체크, 567 열림**. 지운 항목 0.
- **나눠서 체크 10** (GUI 테스트가 확인하는 부분을 `[x]` + 테스트 이름, 안 보는 부분을 새 `[ ]` 로):
  Step 155 UV Editor 키 (4 / 8 / 9 / Ctrl+1 = `gui_step155_uv`; 5 / 6 / 선택 복원 남김), Step 161 Edit > Group 결과 칸
  (`gui_step161_messages` G1; Ctrl+G 키 · "Created pCube1" 남김), Step 161 RMB 한 열 (G2; 끌어 실행 + "옆" 판단 남김), Step 162
  Non-Deformer All (`gui_step162_option_windows`; before-only 남김), Step 162 Hypershade 드래그 (`gui_step162_hs_drag`; 커서 따라옴 ·
  Outliner 놓기 남김), Step 164 h 와 Ctrl+1 (`gui_step164_dag`; 스스로 숨긴 자식 · 레이어 V 남김), Step 166 Dope Sheet Euler / Resample
  (`gui_step166_dope_curves`; 뷰 유지 남김), Step 167 Polygon Cube 더블클릭 · 넘침 휠 / ▲ (`gui_step167_shelf`; Extrude 더블클릭 · ▼
  남김).
- **낡은 문구 고침 3**: Step 12 셸프 더블클릭 (`screen.redo_last` 주의 → step 167 옵션 상자), Step 52 RMB 목록 ("링 아래" → 아래 / 옆,
  "회색 ▸ 항목들" → step 165 노드 목록, Select Similar □ = `option_kind`), Step 170 머리에 "실제 키만" 안내 (`event_simulate` 가 수정키를
  안 실음).
- 체크 안 함 (GUI 테스트는 있지만 일부만): Step 156 EP (X 스냅), 원호 (2 점); Step 157 Only Curve (박스), Mute (Unmute / 사이드바);
  Step 158 조명 Intensity (Key Selected); Step 160 Status Line 드롭다운; Step 162 Toggle (Dependent), Ctrl+Shift 셸프 추가 (실제 키);
  Step 165 CVs 표 입력 / 모서리 / 면; Step 166 Auto Frame (GUI 는 함수를 직접 부름); Step 168 Smooth to Polygons (skin); Step 169 Wire
  (비틀기); Step 170 전부 (수정키는 연산자로만); Step 171 고스트 (Editor 2s).

## 8. 차이 우선순위 + 다음 단계 후보 (한 단계 크기)

| 순 | S×F | 차이 | 단계 제목 · 지시 · 검증 |
|---|---|---|---|
| 1 | 6 | G / Recent Commands 가 메뉴 · 셸프 · 마킹 명령을 반복 안 함 (BS1, [I]) | **"Repeat Last for Maya commands"** — 먼저 헤드리스로 확인 (`run_action('Mesh/Combine')` 뒤 `wm.operators[-1]`, `screen.repeat_last` 결과), Maya 쪽 GUI 측정 (메뉴 / 셸프 / 마킹 / 옵션 창 확인 뒤 G 가 무엇을 반복, Edit > Repeat 라벨). 킷 "마지막 Maya 명령" 기록 (path + option 값) → G = `allset.repeat_last` (기록이 키 연산보다 새것이면 `run_action` 으로, 아니면 `screen.repeat_last`), Edit > Repeat 라벨 = Maya "Repeat <label>", Recent Commands = 킷 기록 + Blender 기록. 검증: 헤드리스 Combine → G → 두 번째 Combine 결과 이름, 셸프 Cube → G = pCube2, Ctrl+E (키) → G 그대로, 한 G = undo step 하나; GUI G 키 |
| 2 | 6 | 패널 메뉴 / 툴바 회색 36 이 감사 밖, 상대가 있는데 회색 (BS2, BS6) | **"Panel menus honesty and twins"** — `menu_count` / `menu_consistency` / step 101 notice 규칙에 panel_menus · panel_toolbar · Status Line 회색 위젯 추가 (`notices.PANEL_MENU`), 상대 있는 것 연결: Camera Attribute Editor = AE camera 탭, Resolution Gate = 카메라 뷰 frame / passepartout (측정 먼저), Center View of Selection (거리 그대로 중심만, 킷 연산자), Tumble / Track / Dolly Tool (킷 모달), Use Selected Lights; 나머지 notice. 검증: 테스트에 "Panel menu/" 회색마다 notice, menu_count 에 패널 줄, GUI Shading / View 메뉴 스크린샷 |
| 3 | 6 | UV Editor 나머지 (R3) | **"UV Editor finish"** (163 #3 이월) — mayapy 로 Map / Straighten Border, Layout Along, Stack Similar, Distribute UVs, Select Unmapped / Back-Facing / Texture Borders / To Edge Loop·Ring 측정 (step 155 방식, `research/maya/re/uv_*.md`), HUD UV Statistics, 3D View 셸 테두리 (POST_VIEW). 검증: 헤드리스 UV 1e-4 vs mayapy, menu_count UV Editor ≥ 135 / 172, GUI 3D View 셸 테두리 샷 |
| 4 | 6 | Animation Layers 없음 (BS3) | **"Animation Layers on NLA"** — mayapy 측정 (animLayer Additive / Override 결과값, weight, mute / solo, BaseAnimation, 키가 어느 층에 들어가는지) → Layer Editor Anim 탭 = NLA 트랙 목록 (Create Empty / from Selected, weight = influence, M / S / L), 선택 층에 키 (tweak), Time Slider 층 이름. 검증: 헤드리스 두 층 Additive translateX 값 = mayapy (1e-6), 층 mute 뒤 값; GUI Anim 탭 샷 vs Maya 캡처 |
| 5 | 6 | Graph Editor 나머지 (R4) | **"Graph Editor depth 2"** (이월) — Buffer Curve Swap (킷 F-curve 복사본 + 바꾸기), Weighted Tangents (Maya 가중 핸들 길이 측정 → Blender 핸들 길이 고정 / 자유), Pin Channel, I / Set Key on Animated 에 Default Tangent (`graph_key_menu.after_insert`). 검증: 헤드리스 mayapy 핸들 값 비교, menu_count Graph Editor ≥ 165 / 229 |
| 6 | 6 | 리그 나머지 (R6) | **"Skin tools 2"** — Move Weights to Influences, Weight Post Normalization, Interactive Bind (볼륨 = 거리 규칙 측정), IK/FK Keys; 킷 XML 을 mayapy `deformerWeights -im` 으로 읽어 왕복. 검증: mayapy 왕복 가중치 1e-6, Skin ≥ 24 / 28 |
| 7 | 6 | Surfaces 8 / 41 다섯 감사째 (R7) | **"Surfaces basics"** (이월) — Loft / Planar / Revolve / Extrude / Birail 1 (mayapy CV 측정, Blender 표현 = NURBS surface 또는 메시 — 측정 먼저), 그리기 도구 계속 그리기 + V / C 스냅. 검증: mayapy CV 비교, Surfaces ≥ 15 / 41 |
| 8 | 4 | 스크립팅 cmds 17 함수 (R9) | **"maya.cmds look-alike 2"** — parent / group / duplicate / setKeyframe / playbackOptions / spaceLocator / file(new / open / save) / getAttr 셰이프 를 킷 연산자 위에. 검증: 같은 스크립트를 mayapy 와 킷 헤드리스에서 돌려 반환값 · 장면 (이름, 부모, 키) 비교 |
| 9 | 4 | Reference Editor (R8) | **"Reference Editor"** — 킷 창 (step 69 Create Reference 가 만든 것 목록): Reload / Unload / Load / Replace / Import Objects / Remove, Namespace Editor 최소판. mayapy 로 unload / reload 의 편집 유지 규칙 측정. 검증: 헤드리스 링크 .blend 왕복, override 편집 유지 |
| 10 | 4 | 렌더 기본 (R10) | **"Render parity 2"** — lambert1 밝기 (base × 0.8 흉내 또는 Diffuse 노드 — 렌더 픽셀을 Maya 캡처와 비교), Ambient Light (World 색 + notice), F12 기본 조명 (Maya 키 없음 → 결정 기록). 검증: 같은 장면 렌더 평균 밝기 Maya ±3 % |
| 11 | 3 | 네 뷰 이름표 · Transform Display (R15, R18) | **"View labels and transform display"** — 칸 이름표를 Maya 축으로 (top -Y / front -Z / side -X, `view_furniture.SIDE_LABELS`), Display > Transform Display Rotate / Scale Pivots · Selection Handles 를 POST_VIEW 로 그림 (Selection Handles 는 고르기도), Status Line hierarchy 모드 (클릭 = 루트). 검증: GUI 네 뷰 샷 vs `research/maya/screens/` four view, 헤드리스 hierarchy 선택 |
| 12 | 4 | Preferences / Hotkey Editor (R11) | **"Maya Preferences window"** (이월) — 킷 창: Working Units / fps / Up Axis 안내 / Undo 안내 / 키 = Blender 키맵 편집기 버튼 (step 130: Blender 환경설정에 안 씀, 장면 · 애드온 설정만). 검증: GUI 샷, 헤드리스 장면 단위 / fps 바뀜 + `preferences` 스냅숏 차 0 (`test_enable_disable` 방식) |

모르는 것 / 반대 증거:

- BS1 은 [I] — `run_action` 안의 `bpy.ops` 가 정말 등록되지 않는지는 step 147 docstring (`undo_steps.py:4-6`) 의 주장이고 이 레인은
  헤드리스로 재지 않음. 특히 `allset.menu_item` 이 안에서 다시 `undo=True` 로 부르는 경로 (option box "redo" 종류, `mark_pushed`) 는
  등록되므로 G 가 될 수 있음 — 명령마다 다름.
- BS2 의 "상대가 있다" 는 이름만 보고 판단: Resolution Gate ↔ Blender 카메라 뷰 frame 은 항상 보이는 것 (끌 수 없음) 이라 Maya 의
  토글과 같지 않을 수 있음 [K]; Center View of Selection 의 Maya 규칙 [U].
- BS3 Blender 4.5 NLA 로 Maya Additive 층의 회전 (Euler / Quaternion 더하기) 이 같은 값을 내는지 [U] — 측정 먼저.
- 메뉴 수치 (699 / 1318 등) 는 bpy stub 셈 — 실제 Blender 의 poll 실패 (`menu_item` 경고) 는 안 셈; `--options` (옵션 상자 종류) 는
  Blender 가 필요해 안 돌림 (레인 B).
- manual_checks 셈이 163 (620) 과 이번 전 (653) 사이에 33 늘었는데 164–171 이 더한 항목 수를 하나씩 맞춰 보지 않음.
- 5.x 에서 164–171 이 도는지 모름 (§3 빚).
