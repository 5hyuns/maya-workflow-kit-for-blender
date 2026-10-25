# Step 210 lane A — 끝난 것, 남은 것, blindspot (재점검 16차)

User request (lane A 부분): "2) research/README.md 대응표·docs/PLAN.md·docs/steps/*.md 「남은 것」·docs/manual_checks.md를 모아 끝난 것
지우고 남은 것 정리 (know-your-unknowns blindspot으로 놓친 것 보완)" — 기준: "이건 '기본 Maya에 Blender 기능이 붙은 모습'이어야 한다.
칭찬 말고 차이만."

Paper lane, **Blender / Maya 실행 없음**. 입력: `docs/steps/step_201_remaining.md` (감사 15 목록 U/C/K/M/V/A/G/F/S, NB7–NB11),
`step_202.md` … `step_209.md` 의 「남은 것」 / 「Left」 (git `0d75f44..4dd0b14` = 커밋 23 개), PLAN 「재점검 15차」, `gh issue list`
(2026-10-26, 읽기만), `docs/manual_checks.md`. 판정은 HEAD 4dd0b14 의 `src/allset` 을 grep / 읽기로 다시 확인한 것 ("[I]" = 코드를 읽은 것,
돌린 것 아님). 메뉴 수치 = `python tools/menu_count.py` / `--greyed` / `tools/menu_consistency.py` (bpy 없음) + `tmp/audit210a/greyed.py` /
`edgrey.py` / `panels.py` (step 201 스크립트 복사). 원 출력 `tmp/audit210a/`. 점수 = 심각도 S (1–3) × 빈도 F (1–3), step 192 / 201 과 같은 척도.
판정은 모두 delegated.

## 1. 구현률 — research/README.md 대응표 (33 행)

| 묶음 | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | **13** | 0 | 0 | 0 |
| UI (9) | 8 | 1 — 테마 (Maya 회색; 결정 13 으로 테마를 안 실음, 195 는 dock 만 덧칠) | 0 | 0 |
| 개념 (11) | 9 | 0 | 0 | 2 — 분리 rotate / scale pivot, Y-up |
| **합계 (33)** | **30 (91 %)** | **1 (3 %)** | **0** | **2 (6 %)** |

감사 15 (30 / 1 / 0 / 2) 에서 **움직인 행 없음** (다섯 감사째). 표가 굵은 단위라 202–209 는 Done 행 아래 숨은 차이만 고쳤고, 그 행들에
새로 보이는 차이:

- "Construction History / Delete History": Non-Deformer History 가 킷 GN 디포머를 남김 (202, `operators/history.py` `is_deformer`). 남음:
  Blender 자체 Outliner Delete / X 는 제약 helper 를 남김 (step_202.md 「남은 것」).
- "이름 규칙 pCube1 / pCubeShape1": 208 이 Maya 의 「가장 큰 번호 + 1」 규칙을 생성 경로에 넣음 (`operators/naming.py:27` `next_number`).
  **새 숨은 차이 §4 NB15** — set / display layer / anim layer / character set / bookmark 이름은 아직 빈 번호 채우기, Ctrl+V 붙여넣기는
  Blender `.001`.
- "Maya식 Outliner": Reference Editor 가 킷 창이 됨 (209). 남음: Windows > Hypergraph: Hierarchy = Blender Outliner, Namespace Editor 회색
  (§4 NB12 / NB14).
- "Channel Box": 202 가 메뉴 바 "Chann..." 잘림을 줄바꿈으로. 남음: 상태 색이 아이콘, 굵은 머리글, 레이어 멤버 teal 바탕 (C1 / C3,
  step_204.md 「남은 것」).
- "타임 슬라이더 모양": UI 1.25 현재 칸 회복 (202, `ui/toolbox.py` `TIME_SLIDER_PX`). 남음: Blender 파란 현재 프레임 상자 (C overlay).

## 2. 감사 15 뒤 끝난 것 — 목록에서 지움

| 항목 (step_201_remaining) | 끝낸 것 (근거) |
|---|---|
| G5 / NB7 Delete Non-Deformer History 가 킷 GN 디포머 (Wire, skin weight-sum) 를 굽고 지움 | step 202: `operators/history.py` `is_deformer` (Wire `wire_deformer.is_wire`, `skin_tools_199.is_part`), 205 부터 `deformers.base_of` 로 킷 GN 디포머 전부; `test_step202_history` 13 / 13 |
| G5 / NB8 Normal / Tangent helper 고아 | step 202: `constrain_199.helpers_owned_by` / `remove_helpers`, `dag.delete_hierarchy` · Delete by Type > Constraints. 남음: Outliner Delete · Blender X (→ G3 에 붙임) |
| NB9 All by Type Wires / nCloths / nParticles / nRigids 회색 | step 202: `operators/by_type.py`, `history.TYPES`. 남음: Fluids 회색 (Edit / Select 각 1) |
| G4 / NB10 Add Influence 무게 0 | step 202: `rig_maya.maya_add_weights` (w = d^-dropoff, mayapy 23 경우 8.1e-7, `research/maya/re/add_influence_202.md`). 남음: [U] 1 정점, 옵션 창 Dropoff 칸, Bind Skin 이 `allset_max_influences` 안 씀 |
| step_201 quant 회귀 Time Slider 현재 칸 UI 1.25 (ΔE 13.8) | step 202: `toolbox.fit_columns` 가 Time Slider 높이를 `TIME_SLIDER_PX` × scale + header 로; look_compare 1.25 ΔE 0.3 |
| step_201 G2 Channel Box 메뉴 바 "Chann...", 컴포넌트 모드 Outliner 모드 열 | step 202: `wrap_rows` 줄바꿈, `show_mode_column = False` (템플릿 + `maya_outliner.setup`) |
| A2 일부 Pin / Unpin, List Load / Add Selected, Show > Attributes 필터, Show Objects IkHandles / Sets / Characters, Change Rotation Interp, Select Curve Nodes, Key Sync / Peak Removal | step 203: `ui/editor_chrome.py` (`.AllsetList` 컬렉션 필터), `operators/graph_curves_203.py`; Graph Editor 167 → **187 / 229**, Dope Sheet 139 → **158 / 181** |
| C4 일부 Dope Sheet Show > Characters 회색 | step 203: Show > Objects > Characters 두 편집기 (`editor_menu_map`) |
| A3 (대부분) Extract / Duplicate (= Maya 2022 의 "Copy") / Empty / Delete Empty / Zero · Full Weight and Key, 여러 레이어 선택 | step 204: `operators/anim_layers_204.py`, `ui/layer_editor.py` Ctrl / Shift 선택, `ui/graph_layers.py` 흐린 커브; mayapy 23 / 25 일치 |
| G1 일부 Deform dead (Tension, Solidify, Sculpt, Morph, Jiggle), UV Pin / Proximity Pin, Display / Hide Intermediate Objects | step 205: `operators/deformers_205a.py`, `deformers_205b.py`, `pins_205.py`; Deform 48 → **60 / 74**, Constrain 16 → **18 / 20** |
| V1 일부 Cycle, Split, Create Shell (Grid), Auto Seams, UV Statistics / Position / Isolate HUD, UV Sets 3 | step 206: `operators/uv_206.py`, `ui/uv_hud.py`; UV Editor 136 → **146 / 172**, 메인 UV 17 → **18 / 19** |
| S2 일부 Bend / Curl / Scale Curvature, Lock Length, CV Hardness, Fit B-spline, Align, Duplicate Surface Curves, Intersect | step 207: `operators/curves_207.py`, `curves_math.py`; Curves 21 → **32 / 36**; nHair Modify Curves 쌍둥이로 nHair 4 → 9 |
| U2 일부 `maya.cmds` parent / group / duplicate / spaceLocator / setKeyframe / cutKey / keyframe / playbackOptions / file / addAttr | step 208: `command_line/cmds_dag.py`, `cmds_anim.py`, `cmds_file.py`; 공개 함수 17 → **28** (`__all__` 4 곳); mayapy 23 경우 |
| F4 Reference Editor = Outliner Blender File 모드 | step 209: `operators/references.py`, `ui/reference_editor.py`, `ui/menu_map.py:140`; Reference Editor 메뉴 바 **27 / 38**, File 24 → **26 / 30** |
| NB11 manual_checks 낡은 문구 | step 201 에서 고침 (이번 §7 에 새 낡은 곳) |

step_201 §3 의 **42 항목: 지움 3** (G4, G5, F4 — 남은 조각은 아래 다른 행에 붙임), **일부 7** (U2, C4, V1, A2, A3, G1, S2), **그대로 32**.
step_201 §8 top 10 중 8 개가 backlog 202–209 로 끝남; **#4 Maya Preferences 창과 #6 렌더 기본은 손대지 않음** (이월 6 · 5 회째).

## 3. 남은 것 한 목록 (step 201 목록 재확인 + 202–209 「남은 것」 + 이번 blindspot)

판정: **일부** (일부 끝남) / **그대로** / **새**. 메뉴 수 = `tmp/audit210a/greyed_sum.txt` / `greyed_detail.txt` / `edgrey.txt` /
`panels.txt` 꼴 출력 (HEAD 4dd0b14). 점수는 남은 부분에 대해 다시 매김.

### 레이아웃 / UI

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| U1 | Maya Preferences / Hotkey Editor = Blender Preferences (`ui/menu_map.py:306-309`), Marking Menu / Shelf / Panel Editor 회색 | 그대로 (이월 6 회) | 2×2 = **4** | R11 |
| U2 | `maya.cmds` 28 함수: makeIdentity, 제약 (`parentConstraint` …), joint, connectAttr, nodeType / objectType, attributeQuery, shadingNode / sets, currentUnit, polyExtrude* 없음; `keyframe -e -option`, `setKeyframe -itt / -ott` 무시, cutKey 클립보드 없음; Script Editor **32 / 59** (History 0 / 13 — Echo All Commands 등, 결과 에코 = Blender report) | 일부 (208) | 2×2 = **4** | step_208.md 「Left」, `edgrey.txt` |
| U3 | ❒ 클릭: 핫박스 · 마킹 · 편집기 메뉴 바 · » · 떼어낸 메뉴는 hold / Shift / Ctrl+클릭만; 모델은 UI 1.0 / 1.25 측정 (1.5 / 2.0 [U]) | 그대로 | 1×2 = **2** | step_183.md |
| U4 | Status Line 회색 **8** (Select by hierarchy / handle / dynamic, Snap projected center / view planes, Render Setup, Pause Viewport 2.0, Character Controls) | 그대로 | 1×1 = 1 | `tmp/audit210a/panels.py` |
| U5 | 패널 메뉴 **69 / 111** · 툴바 **22 / 29** (Look at Selection 행 없음, Flat Shade, Use Selected / No Lights, Show NURBS CVs / Hulls = C) | 그대로 | 1×2 = **2** | step_177.md |
| U6 | 창이 작으면 RMB 목록이 링 옆 (Maya: 늘 아래), UI 1.25 경계 띠 틈, 네 뷰 머리줄 하나 (C) | 그대로 | 1×2 = **2** | step_193.md |
| U7 | 매니퓰레이터 / 링 세부 (평면 투명도, Rotate = C gizmo, 목록 줄 22 vs 20 px, 압출 매니퓰레이터 회전 고리 없음) | 그대로 | 1×2 = **2** | step_185.md |
| U8 | HUD Animation Details / Bounding Box 회색, Poly Count = `overlay.show_stats` | 그대로 | 1×2 = **2** | `greyed_detail.txt` Display |
| U9 | Panels > Saved Layouts / Panel Editor 회색 | 그대로 | 1×1 = 1 | R24 |
| U11 | Repeat 라벨 = 메뉴 이름, Recent Commands List 하위 메뉴 | 그대로 | 1×1 = 1 | step_175.md |
| U12 | AE 탭 줄바꿈 (Maya 는 스크롤), 메시지 조각 | 그대로 | 1×1 = 1 | step_197.md |
| U13 | Blender 파란 현재 프레임 상자 (C overlay), step 규칙 11 / 43 어긋남, frame 1 빨간 눈금 [U]; event-simulated 세션은 Time Slider 높이 · dock 폭을 안 맞춤 (`ALLSET_FIT_WARP`, step_202.md) | 그대로 | 1×3 = **3** | step_186.md, step_202.md |
| U14 | Tool Settings dock · Hypershade 창 · **Reference Editor 창 (209)** 은 #444444 로 안 들어 올림; Layer Editor 툴바 teal 아이콘이 lift 만큼 밝음 (step_202.md) | 일부 새 | 1×1 = 1 | step_195.md, step_202.md |

### Channel Box / AE

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| C1 | 상태 색이 아이콘 (`ui/channel_box.py:1709` `_STATE_ICON`; Maya driven 노랑 / muted 갈색 / 레이어 teal 은 칸 바탕 — step_204.md 「남은 것」 "확인 필요"), CVs 표 스크롤, DG Traversal 한 단계 | 그대로 | 1×3 = **3** | R14 |
| C2 | AE 라이트 탭 Illuminates by Default 없음 (`Object.allset_illuminates_by_default` 는 `operators/light_links.py` 에만, `ui/ae_layout.py` grep 0) | 그대로 | 1×1 = 1 | step_179.md |
| C3 | 굵은 머리글 (UILayout 에 굵은 글꼴 없음), CB 오른쪽 위 아이콘 3 개, 라벨 글자색 #bbbbbb | 그대로 | 1×3 = **3** | step_195.md |
| C4 | Character set node 가 Outliner / CB 에 node 로 안 보임, Mapper / Redirect notice | 일부 (203) | 1×1 = 1 | step_197.md |

### 마킹 메뉴 / 키

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| K1 | Hypershade / Node Editor 그래프 키 NO **58** 줄 (`keymap/mapping.py`, grep), 전체 NO 162 | 그대로 | 1×2 = **2** | BS4 |
| K2 | Universal Manipulator (Ctrl+T) 미측정 | 그대로 | 1×1 = 1 | step_174.md |

### 모델링

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| M1 | Edit Mesh 회색 3 (Reorder Vertices, Assign Invisible Faces, Project Curve on Mesh), Mesh Display **25 / 39**, 노멀 16 bit · 면적 가중, Mesh Display 명령의 history 노드 없음 | 그대로 | 2×1 = **2** | step_189.md |
| M2 | Interactive Creation / Exit On Completion, Subdiv / Volume Primitives, Construction Plane; 새 primitive In-View Editor 없음; ❒ `missing` 필드 | 그대로 | 1×1 = 1 | step_190.md, step_196.md |
| M3 | #89 Quad Draw (overlay 색, Tab+MMB strip, Ctrl+Shift+RMB) | 그대로 | 2×1 = **2** | #89 |
| M4 | Modify **57 / 90**; Mesh Clipboard Actions (Copy / Paste Attributes), Transfer Vertex Order, Edit > Transfer Attribute Values 회색 | 그대로 | 1×1 = 1 | `greyed_detail.txt` |

### UV

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| V1 | UV Editor **146 / 172** (Tools Lattice / Smudge / Smear / Symmetrize, Modify Symmetrize / Warp Image, Image **6 / 14**, UV Sets **7 / 11** Per Instance Sharing, View Undo / Redo View Change), UV Toolkit 1 / 3, 메인 UV 18 / 19 (3D Grab UV Tool); UV Statistics HUD Options 창, Auto Seams ❒ 없음; Auto Seams 원환 = 원판 (Maya 와 모서리 수 다름), 4 번 Cycle 뒤 면이 다시 붙음 | 일부 (206) | 1×2 = **2** | step_206.md 「Left」 |
| V3 | Map Border FINISHED 인데 변화 없음 (Sync 꺼짐 + 면만), Filter Selection 고정 | 그대로 | 1×1 = 1 | step_178.md |

### 애니메이션

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| A1 | Blender I 키는 레이어 오브젝트에 "NLA stack setup" 경고로 키 안 넣음 (S 는 됨) | 그대로 | 1×1 = 1 | step_194.md |
| A2 | Graph Editor **187 / 229** (View 21 / 40: Undo / Redo View Change, Theme 6, Key View, Time Ruler Placement …; List Bookmarks 3; Spreadsheet; Buffer Curve Reference; Show Objects Asset / Clips / MASH, Select Attributes / Entry), Dope Sheet **158 / 181**; Pin / 필터 상태는 편집기 모두 공유 + 세션 상태, Hierarchy Below 는 자손을 행으로, Upstream 행 이름 = 속성 이름 (`userA`), Peak Removal noisy [U] | 일부 (203) | 1×2 = **2** | step_203.md 「남은 것」, `edgrey.txt` |
| A3 | 레이어: 선택한 여러 레이어 중 마지막 하나만 편집 가능 (나머지는 그려진 읽기 전용, Blender 한 action 한계), View All / Frame 이 다른 레이어 커브 무시, 레이어 부모 · Exclusive solo · Select Objects / Branch / Layer Node · Export · Membership (RMB), 띠 ±1000 고정 (`operators/anim_layers.py:34`) | 일부 (204) | 2×1 = **2** | step_204.md 「남은 것」 |
| A5 | IK/FK Keys 4, Scene Time Warp 4 (Key + 두 편집기 Edit), Set Blend Shape Target Weight Keys, Character Mapper / Redirect; Playback **19 / 26** (Looping Once / Oscillate, Cached Playback, Stepped Preview); File > ATOM 3 | 그대로 | 2×1 = **2** | `greyed_detail.txt` |
| A6 | Visualize Turntable / Animated Sweep | 그대로 | 1×1 = 1 | R26 |
| A8 | Blender (I 키 · 가져오기) 가 만든 커브는 weighted — Maya 공장값 non-weighted (`operators/graph_weights.py:16-17`) | 그대로 | 1×1 = 1 | step_198.md |

### 리깅

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| G1 | Skin **25 / 28** (Interactive Bind Skin / Tool, Move Skinned Joints), Constrain **18 / 20** (Flow Path Object, Set Motion Path Key), Deform **60 / 74** (Wrinkle, Muscle, Pose Space Deformation, Jiggle Disk Cache 2, Add Tweak, Blend Shape#2 3, Proximity Wrap#2, ShrinkWrap#2 2, Wire#2 Add Holder, Edit Membership Tool), HumanIK (Skeleton 51 / 54, Control 9 / 14); [U] Solidify 회전 · Sculpt Stretch 원점 밖 · Morph Retarget · Jiggle weight < 1; Proximity Pin 창 칸 4, Wrap 여러 influence = 가장 가까운 하나, Jiggle 이 jiggle1Cache 대신 오브젝트 선택 | 일부 (205) | 2×2 = **4** | step_205.md 「남은 것」 |
| G2 | Display > Transform Display Rotate / Scale Pivots / Selection Handles 회색 | 그대로 | 2×1 = **2** | R18 |
| G3 | DAG: 숨은 부모의 자손 선택 불가, Blender H / Outliner 눈 규칙 밖; Outliner Delete · Blender X 는 Normal / Tangent helper 를 남김 (step_202.md) | 그대로 + 202 조각 | 2×1 = **2** | R23 |
| G6 | Add Influence: [U] 동점 + 잠금 1 정점, ❒ 에 Dropoff 칸 없음, Bind Skin 이 `allset_max_influences` 를 안 씀 (기본 5) | 새 (202) | 1×1 = 1 | step_202.md |

### FX / 렌더 / 파일

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| F1 | FX **44 / 205 (21 %, 아홉 감사째)**: Generate 2 / 50, nHair 9 / 54 (+5 = 207 커브 쌍둥이), nConstraint 0 / 19, Toon 1 / 20, Fluids 4 / 25, nCache 3 / 20, Effects 2 / 11, nParticles 7 / 25, Fields 14 / 38, nCloth 5 / 13; MASH 없음 | 그대로 | 2×1 = **2** | R21 |
| F2 | lambert1 1.25 배 밝음 (`operators/material.py:29,82` — diffuse 0.8 입력 없음), Blender F12 기본 조명 없음 (킷 렌더만, step 152), Create > Lights > Ambient / Volume Light 회색, Render Setup 회색 (Status Line + Windows) | 그대로 (이월 5 회) | 2×2 = **4** | R10 |
| F3 | Hypershade **115 / 249 (46 %)**: Create 69 / 160, Tabs 0 / 6, Options 0 / 6, Graph 4 / 9, Edit 10 / 30 | 그대로 | 1×2 = **2** | `edgrey.txt` |
| F4 | Reference Editor 나머지: Proxy 0 / 6, View 0 / 2, Save Reference Edits, List Unknown Edits, 목록 위 검색 칸, 중첩 레퍼런스 안 보임; Unload 가 메모리에 데이터 유지, `.blend` 만 (FBX / `.ma` 레퍼런스 불가 — README:184) | 일부 (209) | 1×1 = 1 | step_209.md 「Left」 |

### Surfaces / Curves

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| S1 | Surfaces **15 / 41** (Birail 2 / 3+, Bevel, Align, Attach Without Moving, Move Seam, Intersect, Project Curve, Trim / Untrim [K 불가], Extend, Offset, Round, Stitch 3, Fillet 3, Surface Editing 3, Booleans 3, Sculpt Geometry) | 그대로 (여섯 감사째) | 2×2 = **4** | step_181.md |
| S2 | Curves **32 / 36** (Edit Curve Tool, Project Tangent, Extend / Offset Curve On Surface); Fit B-spline degree > 1 [U], CV Hardness 다중도 1, Align / Duplicate Surface Curves / CV Hardness / Fit B-spline / Intersect ❒ = 공장값만, Lock Length 를 Maya CV 매니퓰레이터로 끄는 것 미측정 | 일부 (207) | 1×1 = 1 | step_207.md 「Left」 |

### 새 (§4 blindspot)

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| B1 | Windows 편집기 17 줄이 「작동」으로 세지지만 맨 Blender 편집기 (Component Editor = 읽기 전용 Spreadsheet, Shape Editor = Properties Data …) | 새 (NB12) | 2×2 = **4** | §4 |
| B2 | Windows > Relationship Editors > Light Linking 이 킷 Light Linking Editor 대신 Properties Object 탭 | 새 (NB13) | 1×1 = 1 | §4 |
| B3 | Namespace Editor 회색 — 209 가 네임스페이스를 실제로 만들고 바꾸게 했는데 | 새 (NB14) | 1×2 = **2** | §4 |
| B4 | Ctrl+V = `pCube1.001`, set / layer / anim layer / character set / bookmark 이름은 빈 번호 채우기 | 새 (NB15) | 1×2 = **2** | §4 |
| B5 | 202–209 를 5.x 에서 한 번도 안 돌림 | 새 (NB16) | 2×1 = **2** | §4 |
| B6 | Maya 2022 의 Arnold 메뉴 / 셸프 / 라이트 (aiSkyDomeLight 등) 가 데이터에 없음 [U] | 새 (NB17) | 2×2 = **4** [U] | §4 |

### 검증 / 정리 빚 (Maya 사용자에게 안 보임)

- **5.x**: `docs/compat_5x.md` 의 마지막 전체 실행 = step 200 (`:66`); step_202–209 문서에 5.x 실행 기록 0 (`grep -i '5\.x\|--blender'`).
  204 (5.x layered action 위 anim layer), 205 (GN Repeat / Simulation zone 을 Python 으로 만듦), 209 (`Library.reload`, override) 가 버전
  민감 → NB16.
- `test_step138_file_io` 가 `tmp/file_io138` 을 sandbox 사이에 공유 (`tests/test_step138_file_io.py:25`) — 그대로.
- 코드 정리 이월 (그대로): `ui/outliner.py:133` `allset_outliner_rows`, `marking/rmb_items.py:208-209,322` 옛 VERTEX_PERIMETER / SHELL_BORDER;
  새: `operators/naming.py:6` 모듈 docstring 이 아직 "the lowest one free" (208 뒤 틀림, `next_number` 는 max + 1).
- **git worktree 64 개** (`git worktree list` 65 줄 − 본 작업 트리; step 201 땐 63) + `C:/Repos/bmk-hotfix` — 지우지 않음 (사용자 확인 필요).
- `master` 가 `origin/master` 보다 **44 커밋 앞** (`git status -sb`) — #103–#107, #109–#116 의 `Fixes` 가 아직 GitHub 에 안 감.
- mayapy / GUI Maya 로 다시 볼 것 (그대로): 킷 `deformerWeights` XML 을 Maya 가 읽는지, Hypershade 면 위 놓기, Isolate 규칙, repeatLast
  기록, Symmetrize UV, Prelight, Retime Snap off, 버퍼 회색, Weight Map 픽셀; 새: Solidify 회전 / Sculpt Stretch / Jiggle weight (205),
  Auto Seams 원환 (206), Lock Length 드래그 (207), Peak Removal noisy (203), set / layer 이름 규칙 (NB15), Arnold 메뉴 유무 (NB17).

## 4. Blindspot (어느 「남은 것」 / 이슈 / backlog / manual_checks 에도 없던 것, grep 확인)

| # | Maya 동작 | 킷 지금 (근거) | S×F |
|---|---|---|---|
| NB12 | Windows > General / Animation Editors 의 편집기는 Maya 자기 창: Component Editor = 선택 정점의 skinCluster / blendShape 가중치를 숫자로 고치는 표, Shape Editor = blendShape 목록 + 슬라이더 + 타깃 추가 / 편집, Connection Editor = 두 노드 속성 목록 연결, Expression Editor, Hypergraph [K] | 메뉴 수에서 「작동」이지만 맨 Blender 편집기를 엶 (`ui/menu_map.py`): Component Editor / Attribute Spread Sheet = Spreadsheet (`:685`, `:99` — Blender 4.5 Spreadsheet 는 읽기 전용 [K], 가중치 탭 없음), Shape Editor = Properties Data 탭 (`:690`), Connection Editor / Expression Editor / Hypergraph: Connections = Drivers 편집기 (`:686`, `:109`, `:116`), Hypergraph: Hierarchy = Outliner (`:115`), Node Editor = Shader Editor (`:302`), Time / Trax Editor = NLA (`:105-106`), Camera Sequencer = VSE (`:107`), Render Layer Editor / Render Layers = View Layer 탭 (`:691-692`), Command Shell = Python Console (`:689`), Content Browser = Asset Browser (`:695`). Component / Shape Editor 는 PLAN.md:401, 529-530, 598-599 (감사 6–8) 에 있었다가 이후 목록에서 빠짐 (이월 누락). `menu_count` 는 MAP 에 있으면 작동으로 셈 → Windows 48 / 74 중 17 줄 (Light Linking, Sets 포함) 이 "Blender 편집기 열기" | 2×2 = **4** |
| NB13 | Windows > Relationship Editors > Light Linking = Maya Light Linking 편집기 (Light-Centric / Object-Centric) | `ui/menu_map.py:693` `_props('OBJECT')` = Properties Object 탭 — 같은 기능의 킷 편집기 (`:871` `allset.light_linking_editor`, step 179) 를 안 씀. 라벨이 달라 `menu_consistency` 쌍둥이로 안 잡힘 (0 건). 감사 14 NB2 / 감사 15 NB9 와 같은 꼴 (기능 단계가 옛 Windows 매핑을 다시 안 봄) | 1×1 = 1 |
| NB14 | Windows > General Editors > Namespace Editor: 네임스페이스 목록, 새로 만들기 / 이름 바꾸기 / 합치기 / 지우기 [K] | 회색 + notice (`ui/notices.py:59`). step 173 / 182 목록의 F4 / R8 에는 "Namespace Editor 최소판" 이 있었지만 (`step_173_remaining.md:177`) step 201 F4 와 step 209 에서 빠짐. 209 는 Reference Editor 의 Namespace 칸으로 `ns:` 이름 바꾸기만 (`step_209.md` Done) — 레퍼런스 없는 네임스페이스 / 합치기 / 목록 없음 | 1×2 = **2** |
| NB15 | Maya 노드 이름 = 같은 base 중 가장 큰 번호 + 1, 빈 번호를 안 채움 (`research/maya/re/cmds_201.md:36-40`, transform / joint / history 측정; set / layer 는 측정 안 함 → [I] 같은 DG 규칙); Ctrl+V = `pasted__pCube1` (others/bulletCutCopyPaste.mel:33-37, `step_90.md:95-96`) | (a) 빈 번호 채우기가 남음: `operators/sets.py:43` `next_name` ("lowest free", `research/maya/re/sets.md:9` S2 는 빈 번호 경우를 안 잼), `ui/layer_editor.py:94` `next_layer_name`, `operators/anim_layers.py:72` `unique_name`, `operators/character_sets.py:45` `next_name`, `operators/bookmarks.py:27`; (b) `allset.paste` (`operators/global_keys4.py:83-89`) 는 Blender pastebuffer → 원본이 있으면 `pCube1.001` / `pCubeShape1.001` [I] — step 90 이 delegated 로 남긴 것이 이후 「남은 것」 에서 빠짐. 208 이 "모든 생성 경로" 라고 했지만 이 둘은 밖 | 1×2 = **2** |
| NB16 | — (지원 범위) manifest 는 5.x 까지 지원 (CLAUDE.md step 118) | 202–209 (커밋 23 개) 의 5.x 헤드리스 / GUI 실행 0 (§3 검증 빚). 버전 민감: 204 의 NLA strip action slot (`action.slots.new`, 5.x layered actions), 205 의 GN zone 노드 생성 API, 206 `uv_layers`, 209 `Library.reload` / override | 2×1 = **2** [U] |
| NB17 | Maya 2022 GUI 의 공장 렌더러는 Arnold (`research/maya/re/render_grid_152.md:58-59` `currentRenderer` = "arnold") → mtoa 가 실려 있으면 메인 메뉴 바에 Arnold 메뉴 (Render, Arnold RenderView, Lights: Area / Skydome / Mesh / Photometric / Physical Sky …) 와 Arnold 셸프 [K] | `research/maya/menus.json` · `src/allset/ui/menu_data.py` · Hypershade Create 캡처에 "Arnold" 0 줄 (`grep -c`); 킷은 aiStandardSurface AE 만 앎 (`ui/ae_layout.py:309`). 반대 증거: factory 스크린샷 `research/maya/screens/01_layout_empty.png` 메뉴 바 / 셸프 탭에 Arnold 없음 — 캡처 세션마다 mtoa 상태가 달랐을 수 있음 [U] | 2×2 = **4** [U] |

확인했고 blindspot 아님 (근거): `.ma` / `.mb` 를 못 여는 것은 README:184, 340 에 적힘; Script Editor History 회색은 U2 / step_208.md
「Left」 에 있음; Interactive Bind Skin / Cached Playback / Paint Effects 는 이전 목록에 있음 (grep 4 / 3 / 3 파일); Shelf 사용자 스크립트
버튼은 있음 (`ui/shelf.py:423,513`); Ctrl+C = `view3d.copybuffer` (`ui/menu_map.py:154`), Ctrl+V = `allset.paste` (`keymap/maya_patches.py:1017`).

## 5. GitHub 이슈 (2026-10-26, `gh issue list --state open` / `--state all --limit 300`)

- 전체 **116**, 닫힘 **101**, 열림 **15**: #89 Quad Draw leftovers (0.5.0); **#103–#107** (steps 196–200) 과 **#109–#116** (steps 202–209)
  은 로컬 커밋 `Fixes #…` 로 고쳤지만 **push 전이라 열림** (`master` ahead 44) — 손대지 않음; #108 "Maya menu coverage and roadmap" (문서).
- #108 본문은 감사 15 수치 그대로 ("Last update: audit 15"): 762 / 1318 (58 %), 세트별 Common 299 · Modeling 203 · Rigging 149 · Animation 126
  · FX 39, 편집기 600 / 914, Graph Editor 167 / 229, "Weakest: Curves 58 %, Deform 65 %, UV Editor 136 / 172", Planned next #109–#116 —
  지금 **803 / 1318 (61 %)**, Common 309 · Modeling 227 · Rigging 163 · Animation 140 · FX 44 · Rendering 27 · Cache + Help 31, 편집기
  **676 / 952** (Reference Editor 38 추가), Graph Editor 187, Curves 89 %, Deform 81 %, UV Editor 146. 메인이 고칠 것.
- 202–209 동안 사용자 이슈 없음 (`tmp/audit210a/issues_open.txt`, `issues_all.json`).

## 6. 수치 (감사 15 → 지금, bpy stub 셈 — 기준 수치는 lane B)

| 수치 | step 201 (0d75f44) | 지금 (4dd0b14) |
|---|---|---|
| 대응표 | 30 / 1 / 0 / 2 | **30 / 1 / 0 / 2** |
| 메뉴 leaves 작동 (unique 1318) | 762 (57.8 %) | **803 (60.9 %)** |
| 메뉴 세트별 합 (1486) | 874 (58.8 %) | **941 (63.3 %)**, 회색 + notice 없음 0 |
| 메뉴별 (바뀐 것) | Constrain 16, Curves 21, Deform 48, Edit 46, File 24, Select 54, UV 17, nHair 4 | **Constrain 18 / 20, Curves 32 / 36, Deform 60 / 74, Edit 50 / 68, File 26 / 30, Select 58 / 81, UV 18 / 19, nHair 9 / 54** |
| 편집기 메뉴 바 | 600 / 914 | **676 / 952** — Graph Editor **187**, Dope Sheet **158**, UV Editor **146**, Reference Editor **27 / 38** (새); Hypershade 115, Render Settings 10, Script Editor 32 그대로 |
| 패널 메뉴 / 툴바 / Status Line 회색 | 69 / 111, 22 / 29, 8 | 그대로 |
| menu_consistency 쌍둥이 | 0 | 0 (NB13 은 라벨이 달라 못 잡음) |
| `maya.cmds` 공개 함수 | 17 | **28** |
| 헤드리스 전체 | 1844 / 1844 (4.5, 5.x 셋) | **2018 / 2018** (4.5, step 209 기록; 5.x 안 돌림 — NB16; 이 레인은 안 돌림) |
| 열린 이슈 | 7 | 15 (#89, #103–#107 · #109–#116 push 대기, #108 문서) |
| manual_checks (`- [ ]` / `- [x]` 줄) | 731 / 107 | 753 / 107 → **757 / 106** |

그대로인 약한 곳 (아홉 감사째 포함): nConstraint 0 / 19, Generate 2 / 50, Toon 1 / 20, Texturing 1 / 8, nCache 3 / 20, Fluids 4 / 25,
Stereo 1 / 6, Effects 2 / 11, nParticles 7 / 25, nHair 9 / 54, Fields 14 / 38, Surfaces 15 / 41, nCloth 5 / 13, Hypershade 115 / 249,
Render Settings 10 / 21, Script Editor 32 / 59.

## 7. manual_checks 정리 (`docs/manual_checks.md`)

- 셈 = `grep -cE '^\s*- \[( |x)\]'` (step 192 / 201 과 같은 셈법).
- 전: **1342 줄, 753 항목, 107 체크, 646 열림** (202–209 가 22 항목 추가).
- 후: **1354 줄, 757 항목, 106 체크, 651 열림**. 지운 항목 1, 새 항목 5, 새로 체크 0.
- **지움 1**: step 69 `[x]` "File > Reference Editor: Outliner 새 창 Blender File 보기 …" — 209 부터 킷 Reference Editor 창 (Step 209 항목이 대신;
  `gui_manual_sweep.py` 에도 이 확인이 더는 없음, grep 0).
- **낡은 문구 고침 5 곳**: step 144 Deform 회색 목록 (Tension / Solidify / Morph / Sculpt / Jiggle 은 205 부터, Wire 는 169 부터 작동 →
  Wrinkle / Muscle / Pose Space Deformation 만), Step 201 머리말 ("expected to show a difference today" → 202 가 고침, 이제 통과해야 함) 과 세
  항목 끝 문장 (Today … → step 202 이후; Outliner Delete / X 는 helper 남김, Fluids 회색 그대로), Step 209 항목이 Step 207 묶음 안에 머리글
  없이 있던 것 → `### Step 209 — Reference Editor`.
- 208 의 이름 규칙 변경 (빈 번호 안 채움) 과 어긋나는 항목은 찾지 못함 (`pCube2` / `joint` 항목 grep: 모두 새 오브젝트가 하나씩 늘어나는 경우).
- **새 「Step 210 — Audit 16 blindspots」 5 항목**: NB12 Component / Shape / Connection Editor, NB13 Light Linking 메뉴, NB14 Namespace Editor,
  NB15 붙여넣기 이름 + set / layer 번호, NB16 5.2 / 5.0 에서 202–209 기능.

## 8. 차이 우선순위 top 10 (S×F, 같은 점수는 Maya 사용자가 먼저 부딪히는 순) — 다음 backlog 입력

202–209 가 끝낸 것은 뺌. NB17 은 [U] 라 측정을 먼저 둠.

| 순 | S×F | 차이 | 킷 지금 | 파일 | backlog 제목 · 검증 |
|---|---|---|---|---|---|
| 1 | 4 | Maya 렌더 기본 (F2): lambert1 = color 0.5 × diffuse 0.8 (`research/maya/re/render_defaults_137.md:34-46`), Ambient / Volume Light, F12 기본 조명 | lambert1 1.25 배 밝음, Ambient / Volume Light 회색, Blender F12 는 조명 없음 (킷 렌더만 defaultLight) | `operators/material.py:29,82`, `operators/default_light.py`, `operators/lights.py` | **"Render parity 2"** (이월 5 회). 검증: 같은 씬 Maya Software / Arnold vs 킷 Cycles 렌더 평균 밝기 ±3 %, Ambient Light 가 만들어지고 AE · CB 행, 헤드리스 렌더 픽셀 |
| 2 | 4 | Rigging 편집기 (NB12): Component Editor 가중치 표, Shape Editor, Connection Editor | Spreadsheet (읽기 전용) / Properties Data / Drivers 편집기 | `ui/menu_map.py:685-690`, `:109`, `:116` | **"Maya editors: Component / Shape / Connection Editor"** — 킷 창 (Properties Tool 탭 표시, 209 의 Reference Editor 방식). 검증: mayapy `skinPercent` 와 같은 값 편집 · blendShape weight 슬라이더 · `connectAttr` 결과 = 드라이버, GUI 샷 |
| 3 | 4 | Maya Preferences / Hotkey Editor (U1) | Blender Preferences | `ui/menu_map.py:306-309`, `preferences.py` | **"Maya Preferences window"** (이월 6 회): 킷 add-on prefs 를 Maya 범주 (Interface / Display / Settings: Animation / Modeling / Selection …) 로 보이는 창 + Hotkey Editor = Maya 키 목록 (읽기 + 검색). 검증: Windows 메뉴 +3 작동, GUI 샷, 바꾼 값이 기능에 반영 (헤드리스) |
| 4 | 4 | `maya.cmds` 나머지 + Script Editor History (U2) | 28 함수, History 0 / 13, 결과 에코 = Blender report | `command_line/cmds_*.py`, `ui/script_editor.py` | **"maya.cmds look-alike 3"**: makeIdentity, parent/point/orient/aim/scaleConstraint, joint, connectAttr, nodeType / objectType, attributeQuery, shadingNode / sets, currentUnit + Echo All Commands. 검증: `tests/test_step208_cmds.py` 꼴 mayapy 대조 (cases 추가), Script Editor 32 → ≥ 40 / 59 |
| 5 | 4 | Surfaces (S1, 여섯 감사째) | 15 / 41 | `operators/surfaces_maya.py`, `surfaces_math.py` | **"Surfaces 2"**: Birail 2 / 3+, Extend, Offset, Move Seam, Attach Without Moving, Intersect (곡선), Stitch Edges, Circular Fillet. 검증: mayapy `surfaces_181.json` 꼴 CV 대조 1e-4, Surfaces ≥ 25 / 41 |
| 6 | 4 [U] | Arnold 메뉴 / 셸프 / 라이트 (NB17) | 데이터에 없음 | `research/maya/menus.json`, `ui/menu_data.py` | **"Arnold menu (measure first)"**: GUI Maya 에서 mtoa 실린 공장 상태의 메뉴 바 · 셸프 캡처 → 있으면 Arnold Lights (Area / Skydome / Physical Sky) = Blender 라이트 / World, RenderView = Render View. 검증: 캡처 JSON, menu_count 에 Arnold 줄 |
| 7 | 3 | Channel Box 모양 (C1 / C3) | 상태 색 = 아이콘, 굵은 머리글 없음, 라벨 색 | `ui/channel_box.py:1709`, `ui/maya_dock.py` | **"Channel Box look 2"**: 칸 바탕 색 (keyed 빨강 / driven 노랑 / muted 갈색 / 레이어 teal) 을 POST_PIXEL 로 (195 의 dock 덧칠 방식), 머리글 두 번 그리기로 굵게. 검증: look_compare kit-drawn 표본 + CB 상태 4 종 ΔE00 < 5 (`research/maya/screens/cb135`) |
| 8 | 2 | FX 21 % (F1, 아홉 감사째) | 44 / 205 | `operators/fx.py` | **"FX menus 1"**: nConstraint (Component to Component / Point to Surface / Transform = Blender cloth pin · hook), Fields 나머지, nCache Create / Delete = Blender bake. 검증: FX ≥ 70 / 205, `fx.sim_scale` 헤드리스 시뮬 값 |
| 9 | 2 | 작은 차이 묶음 (NB13–NB16) | Light Linking 메뉴 = Properties, Namespace Editor 회색, 붙여넣기 `.001` / 빈 번호 채우기, 202–209 5.x 미실행 | `ui/menu_map.py:693`, `ui/notices.py:59`, `operators/global_keys4.py:83`, `operators/sets.py:43`, `ui/layer_editor.py:94`, `operators/anim_layers.py:72`, `operators/character_sets.py:45`, `operators/bookmarks.py:27` | **"Audit 16 fix batch"** (싸서 먼저 할 만함): Light Linking → `allset.light_linking_editor`, Namespace Editor 최소판 (목록 / 이름 바꾸기 / 지우기), `pasted__` 이름 + max + 1 namer 통일 (mayapy 로 set / displayLayer / animLayer 빈 번호 측정 먼저), 5.0 / 5.2 헤드리스 전체 + 202–209 GUI 파일. 검증: 헤드리스 이름 테스트, 5.x 결과를 `docs/compat_5x.md` 에 |
| 10 | 2 | Hypershade 46 % (F3) | 115 / 249 (Create 69 / 160, Tabs 0 / 6, Options 0 / 6) | `ui/hypershade.py`, `operators/material.py` `MATERIALS` | **"Hypershade depth 2"**: Tabs (만들기 / 이름 / 지우기), Graph Clear / Add / Remove Selected / Rearrange, Create 2D / 3D Textures 나머지 = Blender 텍스처 노드. 검증: Hypershade ≥ 150 / 249, GUI 샷 |

다음 (점수 2 이하): 리그 나머지 (G1 Interactive Bind Skin · HumanIK · Flow Path Object, 4 → 205 뒤 주로 측정 [U] 이라 2 로 봄), Graph Editor
나머지 (A2, 2), Time Slider 파란 상자 (U13, 3 — C, Time Slider 를 Image Editor 띠로 옮기지 않으면 못 끔), 애니 레이어 여러 개 편집 (A3, 2 —
Blender 한 action 한계), UV 나머지 (V1, 2), ❒ 클릭 나머지 입구 (U3, 2), RMB 목록 링 옆 (U6, 2), #89 Quad Draw (M3, 2), ATOM (A5).

## 모르는 것 / 반대 증거

- NB12 의 "Spreadsheet 는 읽기 전용" 은 Blender 4.5 지식 [K] — 이 레인은 Blender 를 안 띄움. Maya Component Editor / Shape Editor 의 일상
  빈도 (F2) 는 리깅 사용자 기준 추정 [I].
- NB15 (a) 의 Maya 쪽은 [I]: cmds_201 은 transform / joint / history 노드만 쟀고, sets.md S2 는 빈 번호 경우를 안 잼 — set / displayLayer /
  animLayer / character / timeSliderBookmark 이 같은 규칙인지는 mayapy 로 재야 함. (b) `pCube1.001` 은 코드 읽기 [I] (Blender pastebuffer 의
  이름 규칙); Maya `pasted__` 접두사는 step_90.md 가 MEL 주석으로 적은 것 [K].
- NB16 은 실행 안 함 [U]: 실제로 5.x 에서 깨지는지 모름 — 204 / 205 / 209 가 `compat.py` 를 거쳤는지 이 레인은 확인 안 함.
- NB17 은 모순된 증거 [U]: render_grid_152 (Arnold 가 current renderer) vs 01_layout_empty.png (Arnold 메뉴 · 셸프 없음). mtoa 를 공장 상태로
  보느냐가 결정 사항 — 사용자 결정 4 ("Maya 기준은 2022 팩토리 기본값", `docs/user_decisions.md:9`) 에 mtoa 가 들어가는지부터 정해야 함.
- 대응표가 다섯 감사째 그대로인 것은 표가 굵은 단위라서 — 숨은 차이는 §3 에서만 보임. 반대로 NB12 처럼 메뉴 「작동」 수가 실제 Maya 다움보다
  부풀어 있는 곳도 있음 (Windows 48 / 74 중 17 줄이 Blender 편집기 열기).
- 메뉴 수치는 bpy stub 셈 (Blender poll 실패 안 셈); `--options` 는 Blender 가 필요해 안 돌림 (lane B). 헤드리스 2018 / 2018 은 step 209 기록.
- manual_checks 체크 판단은 GUI 테스트 코드 / 단계 문서 통과 기록에 기댐 — 이 레인은 GUI 를 돌리지 않음. step 69 항목을 지운 것은 「낡음」
  판단 (그 동작 자체가 없어짐) 이지 실패가 아님.
