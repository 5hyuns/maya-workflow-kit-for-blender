# Step 201 lane A — 끝난 것, 남은 것, blindspot (재점검 15차)

User request (lane A 부분): "research/README.md 대응표·docs/PLAN.md·docs/steps/*.md 「남은 것」·docs/manual_checks.md를 모아 끝난 것
지우고 남은 것 정리 (know-your-unknowns blindspot으로 놓친 것 보완)" — 기준 (2026-10-19): "기본 Maya 에 Blender 기능이 붙은 모습",
칭찬 말고 차이만.

Paper lane, **Blender 실행 없음**. 입력: `docs/steps/step_192_remaining.md` (감사 14 목록 U/C/K/M/V/A/G/F/S, NB1–NB6),
`step_192.md` (메인 G1–G7), `step_193.md` … `step_200.md` 의 「남은 것」 (git `13d2153..0d75f44` = 커밋 21 개), PLAN 「재점검 14차」,
`gh issue list` (2026-10-25, 읽기만), `docs/manual_checks.md`. 판정은 HEAD 0d75f44 의 `src/allset` 을 grep / 읽기로 다시 확인한 것
("[I]" = 코드를 읽은 것, 돌린 것 아님). 메뉴 수치 = `python tools/menu_count.py` / `--greyed` / `tools/menu_consistency.py` (bpy 없음)
+ `tmp/audit201a/greyed.py` / `edgrey.py` (step 192 스크립트 복사). 원 출력 `tmp/audit201a/`. 점수 = 심각도 S (1–3) × 빈도 F (1–3),
step 192 와 같은 척도. 판정은 모두 delegated.

## 1. 구현률 — research/README.md 대응표 (33 행)

| 묶음 | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | **13** | 0 | 0 | 0 |
| UI (9) | 8 | 1 — 테마 (Maya 회색; 결정 13 으로 테마를 안 실음, 195 는 dock 만 덧칠) | 0 | 0 |
| 개념 (11) | 9 | 0 | 0 | 2 — 분리 rotate / scale pivot, Y-up |
| **합계 (33)** | **30 (91 %)** | **1 (3 %)** | **0** | **2 (6 %)** |

감사 14 (30 / 1 / 0 / 2) 에서 **움직인 행 없음** (네 감사째). 193–200 은 Done 행 아래 숨은 차이를 고쳤다:

- "RMB / Shift·Ctrl+RMB 마킹메뉴": 링이 늘 누른 점 (193) — flick 회귀 끝. 남음: 창이 작으면 목록이 링 옆 한 열 (Maya 는 늘 링 아래,
  화면 끝에서만 전체를 올림), UI 1.25 에서 옆 목록이 타임라인 경계 띠를 건너뛰며 생기는 틈 (step_193.md 「남은 것」).
- "Channel Box": dock #444444 (195), 레이어 멤버 `LAYERED` 상태 (194). 남음: 굵은 머리글 · 오른쪽 위 아이콘 3 개 · 라벨 #bbbbbb · 상태 색이
  아이콘 (C1 / C3).
- "타임 슬라이더 모양": 현재 칸 #525252 (195). 남음: Blender 파란 현재 프레임 말풍선 (C overlay; UI 1.25 에서 칸을 거의 다 덮음).
- "Display Layer = Layer Editor" (Anim 탭): 레이어 오브젝트 키 표시 끝 (194, 감사 14 NB1).
- "Construction History / Delete History": **새 숨은 차이 §4 NB7** — Delete Non-Deformer History 가 킷 Geometry Nodes 디포머 (Wire,
  skin weight-sum) 를 굽고 지움 [I].

## 2. 감사 14 뒤 끝난 것 — 목록에서 지움

| 항목 (step_192_remaining / step_192) | 끝낸 것 (근거) |
|---|---|
| step_192 G1 (점수 9) RMB flick 이 올린 메뉴에서 죽음 | step 193: `marking/engine.py:388` `fit_ring` = 중심 고정 (`lift_up` / `Layout.lifted` 지움); dogfood 48 / 48 |
| A0 / NB1 레이어 오브젝트 키가 CB · Time Slider · Graph Editor 에서 사라짐 | step 194: `operators/anim_layers.py:212,219,249` (`display_layer` / `show` / `hidden_base_curves`), `ui/channel_box.py:444` `LAYERED`, `ui/time_slider.py:745` |
| A3 일부 Merge Layers, Zero Key Layer | step 194: `operators/anim_layers.py:637,680`, Anim 탭 Layers 메뉴 (`ui/layer_editor.py:527`) |
| C3 일부 dock 회색 · shape 줄 | step 195: `ui/maya_dock.py:852,870` `dock_lift` / `draw_tint`, pref `maya_dock_colors`; look_compare kit-drawn 12 / 12 (1.0) |
| U13 일부 현재 칸 색 | step 195: `ui/time_slider.py:584` `RULER_CURRENT` (#525252, ΔE 0.0 at 1.0) |
| M5 / NB3 primitive ❒ 19 개 = redo | step 196: `operators/option_windows_prims.py` (Polygon 11 + NURBS 8), window 경로 120 → 158, redo 127 → 104, generic 34 → 19 |
| C4 일부 Create Character Set ❒ = redo | step 196: `operators/option_windows_misc196.py` (Control · Key 두 경로 + Subcharacter) |
| S2 / V1 일부 Curves 편집 ❒, Merge UVs 가 모두 한 점으로 | step 196: Cut / Detach / Reverse / Smooth / Straighten / arc 창, `allset.curve_smooth_curves`, `allset.uv_merge` (polyMergeUV) |
| U10 결과 칸 `Undo: …` 고착 | step 197: `command_line/undo_text.py:60` `_new_command` (새 명령마다 지움) |
| U12 일부 핫박스 위 in-view 메시지 / In-View Editor, AE 탭 · 메뉴 잘림 | step 197: `marking/draw.py:378` `menu_up`, `ui/attribute_editor.py:588` `wrap_rows` (Maya 는 탭 줄 스크롤 — kit 은 줄바꿈, delegated) |
| step_192 G5 Mesh > Cleanup… 의 ▸ | step 197: `operators/poly_cleanup.py:150` `allset.poly_cleanup` + Cleanup Options 창 |
| A7 / NB2 "Blender has no character sets" 문구 · 회색 입구 | step 197: `rg 'no character sets' src` = 0, Relationship Editors > Character Sets = `allset.character_editor` (`ui/menu_map.py:112`; Windows 47 → 48), Graph Editor Show > Characters 작동. Dope Sheet 쪽은 남음 (A2) |
| A2 일부 Retime Tool, Buffer Curve, Weighted Tangents, Select Unsnapped, Set Curve Colors, Add Key Tool; step_192 G6 Graph Editor 의 Blender 사이드바 | step 198: `operators/graph_retime.py`, `graph_buffers.py`, `graph_weights.py`, `graph_menu_198.py`, `ui/graph_view.py:230` `hide_sidebars`; Graph Editor 154 → **167**, Dope Sheet 130 → **139** |
| G1 일부 Skin / Constrain | step 199: `operators/skin_tools_199.py`, `constrain_199.py`; Skin 19 → **25 / 28**, Constrain 11 → **16 / 20** |
| NB4 5.x 헤드리스 154–190 안 돌림 | step 200: 4.5.4 / 5.0.1 / 5.1.2 / 5.2.3 모두 1844 / 1844; `compat.py:328` `GN_INPUT_STRUCT`, `MENU_BAR_LEAD_UNITS`; `docs/compat_5x.md` 「step 200」 |
| NB5 manual_checks 낡은 문구 | step 192 / 193 에서 고침 (이번 §7 에 남은 것) |

## 3. 남은 것 한 목록 (step 192 목록 재확인 + 193–200 「남은 것」 + 이번 blindspot)

판정: **일부** (일부 끝남) / **그대로** / **새**. 메뉴 수 = `tmp/audit201a/greyed_sum.txt` / `greyed_detail.txt` / `edgrey.txt`
(HEAD 0d75f44). 점수는 남은 부분에 대해 다시 매김.

### 레이아웃 / UI

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| U1 | Maya Preferences / Hotkey Editor = Blender Preferences (`ui/menu_map.py:301-302`), Marking Menu / Shelf / Panel Editor 회색 | 그대로 | 2×2 = **4** | R11 |
| U2 | `maya.cmds` 닮은꼴 **17** 함수 (`command_line/cmds_shim.py:135-488`); parent / group / duplicate / setKeyframe / playbackOptions / spaceLocator / file 없음; Script Editor 32 / 59 | 그대로 | 2×2 = **4** | R9 |
| U3 | ❒ 클릭: 핫박스 · 마킹 · 편집기 메뉴 바 · » · 떼어낸 메뉴는 hold / Shift / Ctrl+클릭만; 모델은 UI 1.0 / 1.25 측정 (5.x lead 는 200 에서 고침, 1.5 / 2.0 [U]) | 일부 | 1×2 = **2** | step_183.md |
| U4 | Status Line 회색 **8** | 그대로 | 1×1 = 1 | R18 |
| U5 | 패널 메뉴 69 / 111 · 툴바 22 / 29 (Look at Selection 행 없음 — `ui/panel_menu_data.py` grep 0, Camera Attribute Editor 가 카메라 선택, NURBS CVs / Hulls = Blender 가 못 숨김 197 측정) | 그대로 | 1×2 = **2** | step_177.md, step_197.md |
| U6 | 창이 작으면 RMB 목록이 링 옆 (Maya: 늘 아래), UI 1.25 경계 띠 틈, 네 뷰 머리줄 하나 (C) | 일부 (193) | 1×2 = **2** | step_193.md |
| U7 | 매니퓰레이터 / 링 세부 (평면 투명도 각도, Rotate = C gizmo, 목록 줄 22 vs 20 px, 압출 매니퓰레이터 회전 고리 없음) | 그대로 | 1×2 = **2** | step_185.md |
| U8 | HUD Animation Details / Bounding Box 회색, Poly Count = `overlay.show_stats` | 그대로 | 1×2 = **2** | R22 |
| U9 | Saved Layouts / Save / Import / Delete Workspace 회색 | 그대로 | 1×1 = 1 | R24 |
| U11 | Repeat 라벨 = 메뉴 이름, Recent Commands List 하위 메뉴 | 그대로 | 1×1 = 1 | step_175.md |
| U12 | AE 탭 줄바꿈 (Maya 는 스크롤; pCube1 / pCubeShape1 따로 줄, 197), 메시지 조각 (step 182 G5) | 일부 (197) | 1×1 = 1 | step_197.md |
| U13 | Blender 파란 현재 프레임 말풍선 (C overlay — Time Slider 를 Image Editor 띠로 옮기지 않으면 못 끔), step 규칙 11 / 43 어긋남, frame 1 빨간 눈금 안 보임 (step_192 G7 [U]) | 일부 (195) | 1×3 = **3** | step_186.md, step_195.md |
| U14 | Tool Settings dock · Hypershade 창은 #444444 로 안 들어 올림 | 새 (195) | 1×1 = 1 | step_195.md |

### Channel Box / AE

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| C1 | 상태 색이 아이콘 (`ui/channel_box.py:1696-1699` `_STATE_ICON`; Maya driven 노랑 / muted 갈색 / 레이어 teal 바탕), CVs 표 스크롤, DG Traversal 한 단계 | 일부 (194 LAYERED 아이콘) | 1×3 = **3** | R14, step_194.md |
| C2 | AE 라이트 탭 Illuminates by Default 없음 (`ui/ae_layout.py` grep 0) | 그대로 | 1×1 = 1 | step_179.md |
| C3 | 굵은 머리글 (UILayout 에 굵은 글꼴 없음), CB 오른쪽 위 아이콘 3 개 (kit 은 세로 탭 띠), 라벨 글자색 #bbbbbb | 일부 (195) | 1×3 = **3** | step_195.md |
| C4 | Character set node 가 Outliner / CB 에 node 로 안 보임, Mapper / Redirect notice, Dope Sheet Show > Characters 회색 | 일부 (196 / 197) | 1×1 = 1 | step_197.md |

### 마킹 메뉴 / 키

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| K1 | Hypershade / Node Editor 그래프 키 NO 56 행 (`keymap/mapping.py`, 줄 셈) | 그대로 | 1×2 = **2** | BS4 |
| K2 | Universal Manipulator (Ctrl+T) 미측정 | 그대로 | 1×1 = 1 | step_174.md |

### 모델링

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| M1 | Edit Mesh 회색 3 (Reorder Vertices, Assign Invisible Faces, Project Curve on Mesh), Mesh Display 14 회색, 노멀 16 bit · 면적 가중, Mesh Display 명령의 history 노드 없음 (NB6) | 그대로 | 2×1 = **2** | step_189.md |
| M2 | Interactive Creation / Exit On Completion, Subdiv / Volume Primitives; 새 primitive In-View Editor 없음; ❒ `missing` 필드 (Normalize / Preserve aspect ratio, NURBS tolerance · caps · degree 2/5/7, Pinched at pole) | 일부 (196) | 1×1 = 1 | step_190.md, step_196.md |
| M3 | #89 Quad Draw (overlay 색, Tab+MMB strip, Ctrl+Shift+RMB) | 그대로 | 2×1 = **2** | #89 |
| M4 | Modify 57 / 90; Cleanup 의 non-planar 허용치 · nonmanifold 수리 [U] | 그대로 | 1×1 = 1 | R25, step_197.md |

### UV

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| V1 | UV Editor 136 / 172 (Cut/Sew Auto Seams / Create Shell / Split, Modify Cycle / Symmetrize / Warp Image, Tools Lattice / Smudge / Smear, HUD UV Statistics, Image 6 / 14, UV Sets 4 / 11), UV Toolkit 1 / 3, 메인 UV 17 / 19; Contour Stretch ❒ 필드 전부 `missing` | 일부 (196 Merge UVs) | 2×2 = **4** | `tmp/audit201a/edgrey.txt` |
| V3 | Map Border FINISHED 인데 변화 없음 (Sync 꺼짐 + 면만), Filter Selection 고정 | 그대로 | 1×1 = 1 | step_178.md |

### 애니메이션

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| A1 | Blender I 키는 레이어 오브젝트에 "NLA stack setup" 경고로 키 안 넣음 (S 는 됨) | 일부 | 1×1 = 1 | step_194.md |
| A2 | Graph Editor **167 / 229** · Dope Sheet **139 / 181**: Pin / Unpin Channel, List Load / Add Selected Objects · Bookmarks, Show 17 / 34 (Attributes 필터 6, IkHandles / Sets …), Scene Time Warp, Change Rotation Interp 5, Select Curve Nodes (198 계획에 있었지만 회색), View Theme / Time Ruler / Key View; Retime Snap off 소수 드래그 [U], 버퍼 회색 미측정 | 일부 (197 / 198) | 2×2 = **4** | step_198.md, `edgrey.txt` |
| A3 | 애니 레이어 나머지: Extract / Copy / Delete Empty, Zero Weight / Full Weight, 여러 레이어 선택 (Graph Editor 에 둘 다), Rotation By Layer, 띠 ±1000 고정 | 일부 (194) | 2×2 = **4** | step_194.md |
| A5 | IK/FK Keys 4, Scene Time Warp 4, Set Blend Shape Target Weight Keys, Character Mapper / Redirect; Playback Looping Once / Oscillate · Cached Playback · Stepped Preview (Playback 19 / 26) | 그대로 | 2×1 = **2** | `greyed_detail.txt` |
| A6 | Visualize Turntable / Animated Sweep | 그대로 | 1×1 = 1 | R26 |
| A8 | Blender (I 키 · 가져오기) 가 만든 커브는 표시 없으면 weighted — Maya 공장값 non-weighted (`operators/graph_weights.py:16-17`, kit 키만 `default_tangent_weight`) | 새 (198, delegated 기록만) | 1×1 = 1 | step_198.md |

### 리깅

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| G1 | Skin 25 / 28 (Interactive Bind Skin / Tool, Move Skinned Joints), Constrain 16 / 20 (UV Pin, Proximity Pin, Flow Path Object, Set Motion Path Key), Deform 48 / 74 (dead: Tension, Solidify, Morph, Wrinkle, Sculpt, Jiggle …), HumanIK (Control 9 / 14), Weight Map 픽셀 · Substitute 거리 · Bake 반 가중 [U], Normal / Tangent helper 가 F12 애니 렌더에서 한 프레임 늦음 | 일부 (199) | 2×2 = **4** | step_199.md |
| G2 | Display > Transform Display Rotate / Scale Pivots / Selection Handles 회색 | 그대로 | 2×1 = **2** | R18 |
| G3 | DAG: 숨은 부모의 자손 선택 불가, Blender H / Outliner 눈 규칙 밖 | 그대로 | 2×1 = **2** | R23 |
| G4 | Add Influence = 무게 0 (`operators/rig_maya.py:320` `weight=0.0`) — Maya 공장값은 새 joint 근처에 거리 가중치 (step_196.md:56 "→ step 199" 였는데 199 가 안 함) | 새 (§4 NB10) | 2×1 = **2** | §4 |
| G5 | **Delete Non-Deformer History 가 킷 GN 디포머를 굽고 지움** (§4 NB7), Normal / Tangent helper 고아 (§4 NB8) | 새 | 3×1 = **3** / 1 | §4 |

### FX / 렌더 / 파일

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| F1 | FX 39 / 205 (19 %, 여덟 감사째): Generate 2 / 50, nHair 4 / 54, nConstraint 0 / 19, Toon 1 / 20, Fluids 4 / 25, nCache 3 / 20; MASH 없음 | 그대로 | 2×1 = **2** | R21 |
| F2 | lambert1 1.25 배 밝음, Blender F12 기본 조명 없음, Ambient / Volume Light 회색, Render Setup 회색 | 그대로 | 2×2 = **4** | R10 |
| F3 | Hypershade 115 / 249 | 그대로 | 1×2 = **2** | R19 |
| F4 | Reference Editor = Outliner Blender File 모드 (`ui/menu_map.py:136`), Reload / Unload / Replace / Import Objects 없음 | 그대로 | 2×2 = **4** | R8 |

### Surfaces / Curves

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| S1 | Surfaces 15 / 41 (Birail 2 / 3+, Bevel, Align, Intersect, Project Curve, Trim / Untrim [K 불가], Extend, Offset, Round, Stitch, Fillet …) | 그대로 | 2×2 = **4** | step_181.md |
| S2 | Curves 21 / 36 (Edit Curve Tool, Intersect, Extend, Fit B-spline, CV Hardness …), Cut / Detach Keep original · Smooth#2 Smoothness `missing` | 일부 (196 창) | 2×2 = **4** | R7, step_196.md |

### 검증 / 정리 빚 (Maya 사용자에게 안 보임)

- 5.x GUI: 200 은 `step183 / 187` 만 5.2 에서 돌림 — 193–199 의 GUI 전용 그림 (dock 덧칠 · `_list_hole` 픽셀 읽기, Retime / 버퍼 그리기,
  레이어 커브, Time Slider 눈금 — step186 GUI 파일 없음) 은 5.x 미확인 [U]. manual_checks 「Step 201」 에 넣음.
- `test_step138_file_io` 가 `tmp/file_io138` 을 sandbox 사이에 공유 (step_200.md 「남은 것」).
- 코드 정리 이월 (그대로): `ui/outliner.py:133` `allset_outliner_rows`, `marking/rmb_items.py:208-209,322` 옛 VERTEX_PERIMETER / SHELL_BORDER.
- **git worktree 63 개** (`.claude/worktrees/agent-*`, `git worktree list`; step 192 땐 2 개) + `C:/Repos/bmk-hotfix` — 지우지 않음 (사용자 확인 필요).
- mayapy / GUI Maya 로 다시 볼 것 (그대로): 킷 `deformerWeights` XML 을 Maya 가 읽는지, Hypershade 면 위 놓기, Isolate 규칙,
  repeatLast 기록, Symmetrize UV, Prelight; 새: Retime Snap off, 버퍼 회색, Weight Map 픽셀.

## 4. Blindspot (어느 「남은 것」 / 이슈 / backlog / manual_checks 에도 없던 것, grep 확인)

| # | Maya 동작 | 킷 지금 (근거) | S×F |
|---|---|---|---|
| NB7 | Delete Non-Deformer History 는 디포머 (wire, skinCluster 의 정규화 설정 포함) 를 남기고 모델링 history 만 굽는다 (`research/maya/re/options_162.md`) | `history.DEFORMERS` (`operators/history.py:21-23`) 에 `'NODES'` 없음 → 킷 Wire (`operators/wire_deformer.py:250`, step 169) 와 skin weight-sum (`operators/skin_tools_199.py:298`, Disable / Interactive 정규화) 은 「non-deformer」 로 `_bake` (`history.py:28-50`) 에서 메시에 구워지고 지워짐: wire 는 지금 모양이 고정되고 커브를 움직여도 안 따라감, weight-sum 은 Σw ≠ 1 이면 rest 메시가 Σw 배로 굽혀진 뒤 Armature 가 다시 변형 + 정규화 모드가 말없이 Post 로 바뀜 [I, 돌리지 않음]. 테스트 없음 (`tests/test_step162_option_windows.py` / `test_step169*` / `test_step199*` 에 wire · weight-sum + Non-Deformer 0) | 3×1 = **3** |
| NB8 | Normal / Tangent constraint 는 제약된 오브젝트의 자식 node — 오브젝트를 지우면 같이 지워짐 [K] | helper empty `<owner>_normalConstraint1Aim` 는 부모 없음 (`operators/constrain_199.py:460-468`, `update` 가 `h.parent = None`), `dag.delete_hierarchy` (`operators/dag.py:113-126`) 와 Delete by Type > Constraints (`history.py:185-188` `constraints.clear()`) 는 helper 를 모름 → 숨은 empty 가 씬에 남음 (Blender Outliner · FBX Export All [U]). Remove Target (`constrain_199.py:649`) 만 helper 를 지움 | 1×1 = 1 |
| NB9 | Select > All by Type / Edit > Delete All by Type 의 Wires / nCloths / nParticles / nRigids / Fluids | 회색 + "Blender has no node of this type" (`ui/notices.py:423-424`, Select `:402`) — 킷은 wire (169), nCloth / nParticles / passive collider / fluid (68) 를 만들고 Modify > Evaluate Nodes 는 그 종류를 앎 (`ui/menu_map.py:655-658`). 감사 14 NB2 와 같은 꼴 (기능 단계가 범주 notice 를 다시 안 읽음); `menu_consistency` 는 쌍둥이가 없어 못 잡음 | 1×1 = 1 |
| NB10 | Skin > Add Influence 공장값 = 새 joint 근처에 거리 가중치 (mayapy, step_196.md:56) | `add_influence(..., weight=0.0)` (`operators/rig_maya.py:320,386`) — step 196 이 "step 199 에서" 라고 미뤘는데 step_199.md 에 없음 (이월이 빠짐) | 2×1 = **2** |
| NB11 | — (절차) | manual_checks 의 193–200 이 낡게 만든 문구 6 곳 (Step 192 묶음 4 항목 "expected to show a difference today", Step 182 세 항목 = 197 이 고침, redo 예 NURBS Circle ❒ = 196 부터 Maya 창, Graph Editor 회색 View 목록의 Show Buffer Curves = 198 부터 작동, step 70 툴바 "고스트 커브") → 이번에 고침 (§7) | — |

확인했고 blindspot 아님 (근거): Unbind Skin 뒤 weight-sum 은 `_sync_sum_modifiers` 가 지움 (`skin_tools_199.py:368-380`),
레이어 오브젝트의 FBX / Alembic 내보내기는 평가 결과를 샘플 (194 는 평가를 안 바꿈, `test_step194` "평가 그대로"), 5.x dock 픽셀 읽기는
`ValueError` 를 받음 (`ui/maya_dock.py:934-946`), Graph Editor 사이드바 닫기는 새 창 Graph Editor 도 봄 (`ui/graph_view.py:238-253`).

## 5. GitHub 이슈 (2026-10-25, `gh issue list --state open` / `--state all --limit 300`)

- 전체 **108**, 닫힘 **101**, 열림 **7**: #89 Quad Draw leftovers (0.5.0); **#103–#107** (steps 196–200) 은 로컬 커밋 `Fixes #103…#107`
  (`38a88d1`, `beb75af`, `845230b`, `51bc287`, `0d75f44`) 로 고쳤지만 **push 전이라 열림** — 손대지 않음; #108 "Maya menu coverage
  and roadmap" (문서). #102 (195) 는 닫힘.
- #108 본문은 감사 14 수치 (750 / 1318, Skin 68 %, Constrain 55 %, Graph Editor 154 / 229, option window 120) 와 Planned next #102–#107
  그대로 — 지금 762 / 1318, Skin 89 %, Constrain 80 %, Graph Editor 167 / 229, window 경로 158. 메인이 고칠 것.
- 193–200 동안 사용자 이슈 없음 (`tmp/audit201a/issues_open.txt`, `issues_all.txt`).

## 6. 수치 (감사 14 → 지금, bpy stub 셈 — 기준 수치는 lane B)

| 수치 | step 192 (13d2153) | 지금 (0d75f44) |
|---|---|---|
| 대응표 | 30 / 1 / 0 / 2 | **30 / 1 / 0 / 2** |
| 메뉴 leaves 작동 (unique 1318) | 750 (56.9 %) | **762 (57.8 %)** |
| 메뉴 세트별 합 (1486) | 857 (57.7 %) | **874 (58.8 %)**, 회색 + notice 없음 0 |
| 메뉴별 (바뀐 것) | Skin 19 / 28, Constrain 11 / 20, Windows 47 / 74 | **Skin 25**, **Constrain 16**, **Windows 48** |
| Graph Editor / Dope Sheet / UV Editor / Hypershade / Render Settings / Script Editor | 154 / 130 / 136 / 115 / 10 / 32 | **167 / 139** / 136 / 115 / 10 / 32 |
| 패널 메뉴 / 툴바 / Status Line 회색 | 69 / 111, 22 / 29, 8 | 그대로 |
| 옵션 상자 → Maya 창 경로 (step 196 기록) | 120 | **158** (lane B 가 다시 셈) |
| menu_consistency 쌍둥이 | 0 | 0 |
| 헤드리스 전체 | 1731 / 1731 (4.5) | **1844 / 1844** × 4.5.4 / 5.0.1 / 5.1.2 / 5.2.3 (step 200 기록; 이 레인은 안 돌림) |
| 열린 이슈 | 1 (#89) | 7 (#89, #103–#107 push 대기, #108 문서) |
| manual_checks (`- [ ]` / `- [x]` 줄) | 709 / 107 | 726 / 107 → **731 / 107** |

그대로인 약한 곳 (여덟 감사째 포함): nConstraint 0 / 19, Generate 2 / 50, nHair 4 / 54, Toon 1 / 20, Texturing 1 / 8, nCache 3 / 20,
Fluids 4 / 25, Stereo 1 / 6, Effects 2 / 11, nParticles 7 / 25, Fields 14 / 38, Surfaces 15 / 41, nCloth 5 / 13, Hypershade 115 / 249.

## 7. manual_checks 정리 (`docs/manual_checks.md`)

- 셈 = `grep -cE '^\s*- \[( |x)\]'` (step 192 와 같은 셈법).
- 전: **726 항목, 107 체크, 619 열림** (193–198 이 17 항목 추가; 199 / 200 은 묶음 없음).
- 후: **731 항목, 107 체크, 624 열림**. 지운 항목 0, 새로 체크 0 (193–200 GUI 테스트는 단계 문서에 통과 기록이 있지만 각 항목이
  실제 마우스 / 느낌을 묻는 것이라 증명 못 함).
- **낡은 문구 고침 9 줄** (NB11): step 70 툴바 (고스트 커브 → Buffer Snapshot / Swap), redo 예 (NURBS Circle ❒ → Point Light ❒), Step 150
  회색 View 목록에서 Show Buffer Curves 뺌, Step 182 세 항목에 「step 197 이 고침 — Step 197 과 같은 확인」, Step 192 머리말 (「지금 차이가
  보일 것」 → 194 / 196 / 197 / 200 이 다룸, 이제 통과해야 함), Step 192 NB1 항목 끝 문장, Step 192 5.2 항목에 「step186 GUI 파일 없음」.
- **새 「Step 201」 5 항목**: NB7 Non-Deformer History 와 Wire / weight-sum, NB8 constraint helper 고아, NB9 All by Type 회색, step 199
  Normal 제약 · 정규화 끄기 실제 느낌, step 200 5.2 GUI 그림 (dock · Retime · 버퍼 · 레이어 커브).

## 8. 차이 우선순위 top 10 (S×F, 같은 점수는 Maya 사용자가 먼저 부딪히는 순) — 다음 backlog 입력

| 순 | S×F | 차이 | Maya (근거) | 킷 지금 | 한 단계 할 일 · 검증 |
|---|---|---|---|---|---|
| 1 | 4 | Graph Editor / Dope Sheet 나머지 (A2) | Pin Channel, List Load / Add Selected, Show > Attributes 필터 (`research/maya/screens/editors104/_editors104.json`) | 167 / 229, 139 / 181 | **"Graph Editor depth 3"**: Pin / Unpin + Load / Add Selected (kit outliner + only-selected 필터), Show Attributes 필터 6, Select Curve Nodes, Change Rotation Interp. 검증: GUI Maya 측정 → 헤드리스, Graph Editor ≥ 180 / 229 |
| 2 | 4 | 리그 나머지 (G1) | Deform dead 26 (Tension, Solidify, Morph, Jiggle …), Interactive Bind Skin, UV / Proximity Pin | Skin 25 / 28, Constrain 16 / 20, Deform 48 / 74 | **"Deform 2"**: Tension / Jiggle / Morph 를 Blender 모디파이어 · GN 으로 (mayapy 대조), UV Pin / Proximity Pin. 검증: mayapy 1e-4, Deform ≥ 55 / 74 |
| 3 | 4 | 애니 레이어 나머지 (A3) | Extract / Copy / Delete Empty, Zero / Full Weight, 여러 레이어 선택 (`research/maya/re/anim_layers_193.md`) | Merge / Zero Key 까지 (194) | **"Animation layers 4"**: mayapy `animLayer` 결과 대조. 검증: mayapy 1e-5, GUI 두 레이어 선택 = Graph Editor 커브 둘 |
| 4 | 4 | Preferences / Hotkey Editor (U1) | Maya Preferences 창 · Hotkey Editor | Blender Preferences | **"Maya Preferences window"**: 킷 add-on prefs 를 Maya 범주 (Interface / Display / Animation / Modeling …) 로 보이는 창. 검증: menu_count Windows +3, GUI 샷 |
| 5 | 4 | `maya.cmds` 17 함수 (U2) | parent / group / duplicate / setKeyframe / playbackOptions / spaceLocator / file | `command_line/cmds_shim.py` | **"maya.cmds look-alike 2"** (이월 3 회). 검증: 같은 스크립트 mayapy vs 킷 헤드리스 결과 |
| 6 | 4 | 렌더 기본 (F2) | lambert1 = color 0.5 × diffuse 0.8 (`research/maya/re/render_defaults_137.md:34-46`) | 1.25 배 밝음, Ambient Light 회색 | **"Render parity 2"** (이월). 검증: 렌더 평균 밝기 Maya ±3 % |
| 7 | 4 | Reference Editor (F4) | 목록 + Reload / Unload / Replace / Import Objects (`research/maya/workflows/scene.md:30`) | Outliner Blender File 모드 | **"Reference Editor"** (이월). 검증: 링크 .blend 왕복, override 편집 유지 |
| 8 | 4 | UV Editor 나머지 (V1) | Auto Seams, Create Shell (Grid), Split, Cycle, Warp Image, UV Statistics HUD | 136 / 172 | **"UV Editor depth 2"**. 검증: mayapy 대조, UV Editor ≥ 145 / 172 |
| 9 | 4 | Curves / Surfaces (S1 / S2) | Edit Curve Tool, Intersect, Extend, Offset, Birail 2 / 3+, Round / Stitch / Fillet | 21 / 36, 15 / 41 | **"Curves and surfaces 3"**. 검증: mayapy `curves_156.json` 꼴 대조 |
| 10 | 3 | Delete Non-Deformer History 가 킷 GN 디포머를 굽고 지움 (NB7) + helper 고아 (NB8) | Maya 는 디포머를 남김 | `history.DEFORMERS` 에 NODES 없음 | **작은 단계** (다른 일과 묶기): `history` 가 킷 GN 디포머 (`wire_deformer.GROUP`, `skin_tools_199.is_part`) 를 디포머로 봄, `dag.delete_hierarchy` / Delete Constraints 가 `constrain_199.helper_of` helper 도 지움; All by Type Wires / nCloths / nParticles 연결 (NB9). 검증: 헤드리스 — wire + bevel 큐브 Non-Deformer 뒤 wire 남음 · 커브 이동이 변형, 제약 큐브 지운 뒤 helper 0 |

다음 (점수 3 이하): Channel Box 머리글 · 아이콘 · 상태 색 (C1 / C3, 3), Time Slider 파란 말풍선 (U13, 3 — C), FX (F1, 2), Add Influence
거리 가중치 (NB10, 2), ❒ 클릭 나머지 입구 (U3, 2), RMB 목록 링 옆 (U6, 2), #89 Quad Draw (M3, 2).

## 모르는 것 / 반대 증거

- NB7 은 코드 읽기만 [I]: `_bake` 가 keep 밖 모디파이어를 평가해 굽는 것은 확인, 실제 결과 (wire 모양 고정, Σw 배) 는 돌리지 않음.
  Maya 쪽 "wire 를 남김" 은 options_162 의 「deformer 만 남김」 규칙에서 미룬 것 [K] — wire 로 직접 재지 않음.
- NB8 의 Maya 쪽 (normalConstraint 가 오브젝트 자식이라 같이 지워짐) 은 Maya DAG 지식 [K]; FBX Export All 이 숨은 empty 를 쓰는지 [U].
- NB9 는 notice 문구가 틀린 것까지만 확인 — Maya All by Type Wires 가 무엇을 고르는지 (wire node vs 커브) [K].
- 대응표가 네 감사째 그대로인 것은 표가 굵은 단위라서 — 숨은 차이는 §3 에서만 보임 (반대 증거: 행 하나가 "Done" 이어도 A2 / G1 같은
  큰 묶음이 남음).
- 메뉴 수치는 bpy stub 셈 (Blender poll 실패 안 셈); `--options` 는 Blender 가 필요해 안 돌림 (lane B). 옵션 창 158 은 step 196 기록.
- manual_checks 체크 판단은 GUI 테스트 코드 / 단계 문서 통과 기록에 기댐 — 이 레인은 GUI 를 돌리지 않음.
