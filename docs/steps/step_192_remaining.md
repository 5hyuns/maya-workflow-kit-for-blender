# Step 192 lane A — 끝난 것, 남은 것, blindspot (재점검 14차)

User request (lane A 부분): "research/README.md 대응표·docs/PLAN.md·docs/steps/*.md 「남은 것」·docs/manual_checks.md를 모아 끝난 것
지우고 남은 것 정리 (know-your-unknowns blindspot으로 놓친 것 보완)" — 기준 (2026-10-19): "기본 Maya 에 Blender 기능이 붙은 모습",
칭찬 말고 차이만.

Paper lane, **Blender 실행 없음**. 입력: `docs/steps/step_182_remaining.md` (감사 13 목록 U/C/K/M/V/A/G/F/S, BS1–BS7),
`step_182.md` (메인 G1–G6), `step_182_quant.md` §7, `step_183.md` … `step_191.md` 의 「남은 것」 (git `326f12f..13d2153` = 커밋 10 개),
PLAN 「재점검 13차」, `gh issue list` (2026-10-25, 읽기만), `docs/manual_checks.md`. 판정은 HEAD 13d2153 의 `src/allset` 을 grep /
읽기로 다시 확인한 것 ("[I]" = 코드를 읽은 것, 돌린 것 아님). 메뉴 수치 = `python tools/menu_count.py` / `--greyed` /
`tools/menu_consistency.py` (bpy 없음) + `tmp/audit192a/greyed.py` / `edgrey.py` (step 182 스크립트 복사). 원 출력 `tmp/audit192a/`.
점수 = 심각도 S (1–3) × 빈도 F (1–3), step 182 와 같은 척도. 판정은 모두 delegated.

## 1. 구현률 — research/README.md 대응표 (33 행)

| 묶음 | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | **13** | 0 | 0 | 0 |
| UI (9) | 8 | 1 — 테마 (Maya 회색) | 0 | 0 |
| 개념 (11) | 9 | 0 | 0 | 2 — 분리 rotate / scale pivot, Y-up |
| **합계 (33)** | **30 (91 %)** | **1 (3 %)** | **0** | **2 (6 %)** |

감사 13 (30 / 1 / 0 / 2) 에서 **움직인 행 없음** (세 감사째). 183–190 은 Done 행 아래 숨은 차이를 고쳤고, 새로 숨은 차이도 생겼다:

- "RMB / Shift·Ctrl+RMB 마킹메뉴" 행: 목록 링 아래 + 메뉴 전체 올림 (step 184), 그려지기 전 flick (191) — 끝. 남음: ❒ 클릭은 메뉴
  바에서 연 메뉴만 (183; 핫박스 · 마킹 · 편집기 메뉴 바 · » 는 hold / Shift / Ctrl+클릭).
- "타임 슬라이더 모양" 행: Maya 눈금 · 칸 · 북마크 띠 (186) — 끝. 남음: Blender 파란 현재 프레임 상자 (C overlay) 가 위에 그려짐.
- "Status Line / Shelf" 행: Construction History 토글 실제 작동 (189) → Status Line 회색 9 → **8**.
- "Construction History / Delete History" 행: 토글 끄면 primitive / extrude / bevel 기록 안 남음 (189). 남음: Mesh Display 새 명령
  (노멀 · 색) 은 Maya 처럼 `polyNormalPerVertex` / `polyColorPerVertex` INPUTS 노드를 안 남김 (`research/maya/re/mesh_display_184.md:14-15`).
- "Display Layer = Layer Editor" 행 (Anim 탭): **새 숨은 차이 §4 NB1** — 레이어에 넣은 오브젝트의 키가 CB / Time Slider / Graph Editor
  에서 사라짐 [I].
- 테마 (Partial) · Not possible 2 행 그대로.

## 2. 감사 13 뒤 끝난 것 — 목록에서 지움

| 항목 (step_182_remaining / step_182 / step_182_quant) | 끝낸 것 (근거) |
|---|---|
| quant #1 / U3 일부 옵션 상자 ❒ 클릭 = 명령 (#82) — **메뉴 바 메뉴** | step 183: `ui/option_click.py`, `ui/menu_sets.py` `on_box`; GUI 24 / 24 (UI 1.0 / 1.25). 나머지 입구 → U3 |
| quant #2 / step_182 G1 / U6 일부 RMB 목록 링 옆 · Time Slider 덮음 | step 184: `marking/engine.py` `lift_up` / `fit_ring` / `Layout.lifted`; 191 flick 수정 |
| quant #3 #7 / G6 / U7 일부 선택 엣지 묻힘, 평면 핸들 작음 · 가운데 흰색 | step 185: `ui/component_colors.py` `OVERLAY_OFF` / `EDGE_SEL_*`, `ui/manipulator.py` `PLANE_*` / `CENTER_IDLE`; look_compare viewport 20 / 20 |
| quant #4 Time Slider 눈금 / 칸 | step 186: `ui/time_slider.py` `_draw_ruler` / `tick_step` (Maya 43 경우 중 32). 파란 상자만 남음 → U13 |
| quant #5 / A5 일부 Character Sets (Key 54 %, Control 7 %) | step 187: `operators/character_sets.py`; Key **73 %**, Control **64 %**. 나머지 → A5 |
| A1 (kit Auto Key) / A4 / BS2 Auto Key 가 레이어 모름, 옛 "no animation layers" 입구 두 곳 | step 188: `operators/auto_key.py` `changed_layer_channels`, `ui/cb_channels.py:199`, Relationship Editors > Animation Layers = Anim 탭. Blender 자체 I 키 → A1 |
| quant #6 / M1 일부 Mesh Display 38 % | step 189: `operators/normals_maya.py`, `operators/color_sets_maya.py`; Mesh Display **25 / 39 (64 %)** |
| V2 / BS1 메인 UV > Delete UVs 회색 + 틀린 안내 | step 189: 연결 + `tools/menu_consistency.py` runtime 별칭 (nHair Smooth / Straighten 도 연결, nHair 2 → 4) |
| quant #10 패널 Show IK Handles / Image Planes | step 189: 패널 메뉴 67 → **69 / 111** (NURBS CVs / Hulls 는 구체 notice 로 회색) |
| quant #12 Insert Isoparms ❒ generic 후퇴 | step 189: `operators/option_windows_surfaces.py` Maya 창 |
| U4 일부 / BS5 Status Line Construction History 회색 | step 189: `ui/input_line.py:319-345` `allset.construction_history`, `prim_history.history_on` (`operators/prim_history.py:50,371`), `extrude.py:508` |
| quant #9 / M2 일부 Polygon Primitives 7 회색 | step 190: `operators/prim_shapes_more.py`, `prim_supershape.py`; Create **47 / 70 (67 %)**. 나머지 → M2 |
| step 191 킷 버그 `allset.dolly_2d`, 올린 메뉴 flick | step 191 (출시 0.4.1) |

## 3. 남은 것 한 목록 (step 182 목록 재확인 + 183–191 「남은 것」 + 이번 blindspot)

판정: **일부** (일부 끝남) / **그대로** / **새**. 메뉴 수 = `tmp/audit192a/greyed_sum.txt` / `edgrey.txt` (HEAD 13d2153). 점수는
현재 남은 부분에 대해 다시 매김 (끝난 부분만큼 내림).

### 레이아웃 / UI

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| U1 | Maya Preferences / Hotkey Editor = Blender Preferences (`ui/menu_map.py:299-302`), Marking Menu / Shelf / Panel Editor 회색 | 그대로 | 2×2 = **4** | R11 |
| U2 | `maya.cmds` 닮은꼴 **17** 함수 (`command_line/cmds_shim.py` — ls select move rotate scale getAttr setAttr xform polyCube/Sphere/Cylinder/Plane delete rename objExists listRelatives currentTime); parent / group / duplicate / setKeyframe / playbackOptions / spaceLocator / file 없음; Script Editor 32 / 59 | 그대로 | 2×2 = **4** | R9 |
| U3 | ❒ 클릭: 핫박스 · 마킹 메뉴 · 편집기 메뉴 바 (Graph Editor …) · » 메뉴 · 떼어낸 메뉴는 hold / Shift / Ctrl+클릭만; 모델은 UI 1.0 / 1.25 만 측정 (1.5 / 2.0 · 5.x [U]); `gui_step143_user` #82 묶음 안 불안정 (191) | 일부 (183) | 1×2 = **2** | step_183.md |
| U4 | Status Line 회색 **8** (`ui/notices.py:671-690`): Select by hierarchy, handle / dynamic 마스크, Snap to projected center / view planes, Render Setup, Pause Viewport 2.0, Character Controls | 일부 | 1×1 = 1 | R18 |
| U5 | 패널 메뉴 69 / 111 · 툴바 22 / 29: Look at Selection 행 없음 (`ui/panel_menu_data.py` grep 0), Camera Attribute Editor 가 카메라를 선택함, Resolution Gate · Use Selected Lights notice | 그대로 | 1×2 = **2** | step_177.md |
| U6 | 네 뷰 머리줄 하나 (C); 올린 메뉴의 빠른 마크 방향 기준 [U], 화면 좌우 끝 Maya 측정 없음, Blender 창이 화면보다 작으면 더 일찍 올림 | 일부 (184) | 1×1 = 1 | step_184.md |
| U7 | 매니퓰레이터 / 링 세부: 평면 투명도가 보는 각도로 바뀌지 않음 (185), Rotate = Blender C gizmo, 목록 줄 22 vs 20 px, dead zone, 압출 매니퓰레이터 회전 고리 / world·local 토글 없음 | 일부 (185) | 1×2 = **2** | step_185.md, R16 |
| U8 | HUD Poly Count / Object Details = `overlay.show_stats`, HUD Animation Details / Bounding Box 회색 | 그대로 | 1×2 = **2** | R22 |
| U9 | 작업 공간 나머지 (Saved Layouts / Save / Import / Delete Workspace 회색) | 그대로 | 1×1 = 1 | R24 |
| U10 | 결과 칸이 Undo 뒤 다른 명령에도 `Undo: …` 그대로 (step_182 G4, manual_checks Step 182), 보고 없는 명령은 결과 칸 안 바꿈 | 그대로 | 1×2 = **2** | step_182.md G4, step_176.md |
| U11 | Repeat 라벨 = 메뉴 이름 (Maya runtime 이름), Recent Commands List 가 하위 메뉴 | 그대로 | 1×1 = 1 | step_175.md |
| U12 | AE 탭 · 메뉴 잘림 (G3, 실제 세션 미확인), 핫박스 위 in-view 메시지 (G2), 메시지 조각 (G5) — manual_checks Step 182 | 그대로 | 1×2 = **2** | step_182.md |
| U13 | Time Slider 위 Blender 파란 현재 프레임 상자 (C overlay — 없애려면 Time Slider 를 Image Editor 띠로 옮겨 전부 그려야 함), step 규칙 폭 의존 11 / 43 어긋남 | 새 (186) | 1×3 = **3** | step_186.md |

### Channel Box / AE

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| C1 | 상태 색 하나 (keyed 빨강만 `right.alert`, driven / muted 는 아이콘 `ui/channel_box.py:1669-1702`; Maya driven 노랑 / expression 보라 / muted 갈색 / **애니 레이어 색** `research/maya/channel_box.md:138-139`), CVs 표 스크롤, DG Traversal 한 단계 | 그대로 | 1×3 = **3** | R14 |
| C2 | AE 라이트 탭에 Illuminates by Default 없음 (`ui/ae_layout.py` grep 0) | 그대로 | 1×1 = 1 | step_179.md |
| C3 | Channel Box 모양: shape / SHAPES / INPUTS 행 바탕 · 굵은 머리글 · 위 오른쪽 CB/LE 아이콘 3 개 · Layer 탭 모양 (183–190 에서 손 안 댐) | 그대로 (A 목록엔 처음) | 2×2 = **4** | step_182_quant.md:268,319 |
| C4 | Character set node 가 Outliner / Channel Box 에 node 로 안 보임 (메뉴로만), Create Character Set ❒ = 일반 redo (Maya 이름 · 속성 창 없음), Mapper / Redirect notice | 새 (187) | 1×2 = **2** | step_187.md |

### 마킹 메뉴 / 키

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| K1 | Hypershade / Node Editor 그래프 키 NO **58** 행 (`keymap/mapping.py` grep) | 그대로 | 1×2 = **2** | BS4 |
| K2 | Universal Manipulator (Ctrl+T) 미측정 | 그대로 | 1×1 = 1 | step_174.md |

### 모델링

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| M1 | Edit Mesh 회색 3 (Reorder Vertices, Assign Invisible Faces, Project Curve on Mesh), Connect ≥ 4 · Bevel Chamfer off / Mitering 정확도, Mesh Display 14 회색 (Color Material Channel 6, Material Blend Setting 7, Share Instances — Blender 대응 없음), 노멀 16 bit 저장 · 면적 가중 차이, Set to Face 굽은 strip [U] | 일부 (189) | 2×1 = **2** | step_189.md |
| M2 | Interactive Creation / Exit On Completion, Subdiv / Volume Primitives notice; 새 7 primitive 에 In-View Editor 없음 (INPUTS 만); Gear Offset 0 노멀 [U] | 일부 (190) | 1×1 = 1 | step_190.md |
| M3 | #89 Quad Draw (overlay 색, Tab+MMB strip `operators/quad_draw.py`, Ctrl+Shift+RMB) | 그대로 | 2×1 = **2** | #89 |
| M4 | Modify 57 / 90 (Asset, Convert subdiv / Paint Effects / fluid, Type Manipulator, Paint Scripts) | 그대로 | 1×1 = 1 | R25 |
| M5 | **primitive ❒ 19 개가 Maya 창이 아님** (§4 NB3) | 새 | 2×1 = **2** | §4 |

### UV

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| V1 | UV Editor 136 / 172 (Cut/Sew Auto Seams / Create Shell / Split, Modify Cycle / Symmetrize / Warp Image, Tools Lattice / Smudge / Smear, HUD UV Statistics, Image 8 / 14, UV Sets Copy / Rename), UV Toolkit 1 / 3; 메인 UV 17 / 19 (Auto Seams, 3D Grab UV Tool) | 일부 (Delete UVs 끝) | 2×2 = **4** | `tmp/audit192a/edgrey.txt` |
| V3 | Map Border FINISHED 인데 변화 없음 (Sync 꺼짐 + 면만), Filter Selection 고정 | 그대로 | 1×1 = 1 | step_178.md |

### 애니메이션

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| A0 | **레이어에 넣은 오브젝트의 키가 CB 빨강 · Time Slider 눈금 · Graph Editor 에서 사라짐** (§4 NB1) | 새 | 3×2 = **6** | §4 |
| A1 | Blender 자체 I 키 / Blender autokey 는 레이어 모름 (tweak 모드 한계) | 일부 (188) | 1×1 = 1 | step_188.md |
| A2 | Graph Editor 154 / 229 · Dope Sheet 130 / 181 (그대로, 네 감사째): Retime Tool (`research/maya/screens/editors104/_editors104.json:316-325`), Swap Buffer Curve, Weighted Tangents, Pin Channel, Show 16 / 34, Add Key Tool, 섞인 곡선 미터 (C) | 그대로 | 2×3 = **6** | R4, BS6 |
| A3 | 애니 레이어 나머지: Merge / Extract / Copy / Delete Empty, Zero Key / Zero Weight / Full Weight 버튼, Lock / Solo, Rotation By Layer (쿼터니언 `research/maya/re/anim_layers_180.md:20`), 「Selected Layers」 하나만 (Maya 여러 개), 띠 범위 ±1000 고정 | 일부 (188 속성 멤버) | 2×2 = **4** | step_180.md, step_188.md |
| A5 | IK/FK Keys 4, Scene Time Warp, Character Mapper / Redirect; Playback Looping Once / Oscillate · Cached Playback · Stepped Preview (Playback 19 / 26) | 일부 (187) | 2×1 = **2** | `greyed_sum.txt` |
| A6 | Visualize 나머지 (Turntable, Animated Sweep, Ghosting Editor 필터) | 그대로 | 1×1 = 1 | R26 |
| A7 | **Character set 끝났는데 안내 문구 · 회색 입구 남음** (§4 NB2) | 새 | 2×2 = **4** | §4 |

### 리깅

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| G1 | Skin 19 / 28, Constrain 11 / 20, Deform 48 / 74 (dead: Tension, Solidify, Morph, Wrinkle, Sculpt, Jiggle …), HumanIK, IK Handle Snap, Wire holders; 킷 XML 을 Maya 가 읽는지 미확인 | 그대로 | 3×2 = **6** | R6 |
| G2 | Display > Transform Display Rotate / Scale Pivots / Selection Handles 회색 | 그대로 | 2×1 = **2** | R18 |
| G3 | DAG: 숨은 부모의 자손 선택 불가, Blender H / Outliner 눈 규칙 밖 | 그대로 | 2×1 = **2** | R23 |

### FX / 렌더 / 파일

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| F1 | FX 39 / 205 (19 %, 일곱 감사째): Generate 2 / 50, nHair 4 / 54, nConstraint 0 / 19, Toon 1 / 20, Fluids 4 / 25, nCache 3 / 20; MASH 메뉴 없음 (`ui/menu_sets.py:30`) | 그대로 | 2×1 = **2** | R21, BS3 |
| F2 | lambert1 1.25 배 밝음 (`operators/material.py:82` 주석의 diffuse 0.8 없음, Maya `research/maya/re/render_defaults_137.md:34-46`), Blender F12 기본 조명 없음, Ambient / Volume Light 회색, Render Setup 회색 | 그대로 | 2×2 = **4** | R10 |
| F3 | Hypershade 115 / 249 | 그대로 | 1×2 = **2** | R19 |
| F4 | Reference Editor = Outliner Blender File 모드 (`ui/menu_map.py:136`), Reload / Unload / Replace / Import Objects 없음 (Maya `research/maya/workflows/scene.md:30`) | 그대로 | 2×2 = **4** | R8 |

### Surfaces / Curves

| # | 지금 남은 것 | 판정 | S×F | 출처 |
|---|---|---|---|---|
| S1 | Surfaces 15 / 41 (Birail 2 / 3+, Bevel, Align, Intersect, Project Curve, Trim / Untrim [K 불가], Extend, Offset, Round, Stitch, Fillet …) | 일부 (Insert Isoparms 창) | 2×2 = **4** | step_181.md |
| S2 | Curves 21 / 36 (Edit Curve Tool, Intersect, Extend, Fit B-spline, CV Hardness …), 그리기 도구 곡선 하나 뒤 끝남 | 그대로 | 2×2 = **4** | R7 |

### 검증 / 정리 빚 (Maya 사용자에게 안 보임)

- **5.x 헤드리스**: 마지막 전체 = step 153 (`docs/compat_5x.md:62`). 154–190 은 release_check (191: 5.2.2 14 PASS) 밖에 없음 → §4 NB4.
- 코드 정리 이월 (그대로): `ui/outliner.py:9,133-137` `allset_outliner_rows`, `marking/rmb_items.py:208-209,322` 옛 VERTEX_PERIMETER / SHELL_BORDER.
- mayapy / GUI Maya 로 다시 확인할 것 (그대로): 킷 `deformerWeights` XML 을 Maya 가 읽는지, Hypershade 면 위 놓기, Isolate 규칙 [K],
  Geometry to Bounding Box, repeatLast 기록 (Combine / 셸프 / 마킹), Symmetrize UV. 새: Prelight 결과 (렌더러 없는 mayapy [U], 189),
  올린 마킹 메뉴의 빠른 마크 기준 (184).
- `step_189.md` 의 worktree 두 개 (`.claude/worktrees/agent-a1d69614…`, `agent-aed8f880…`) 가 훅에 막혀 남음.

## 4. Blindspot (어느 「남은 것」 / 이슈 / backlog / manual_checks 에도 없던 것, grep 확인)

| # | Maya 동작 | 킷 지금 (근거) | S×F |
|---|---|---|---|
| NB1 | 애니 레이어에 넣은 오브젝트도 Time Slider 에 키 눈금, Channel Box 필드 색 (keyed / 레이어 색 `research/maya/channel_box.md:138-139` [O]), Graph Editor 에 레이어 · base 커브 [K] | `anim_layers.ensure_base` 가 활성 액션을 BaseAnimation NLA 띠로 옮기고 `ad.action = None` (`operators/anim_layers.py:117-128`). 키 읽는 곳은 모두 활성 액션만 봄: `compat.id_fcurve_collection` (`compat.py:79-88`, action None → None) → `channel_box._fcurves` / `fcurve` / `channel_state` (`ui/channel_box.py:369-371,389-398,430-445`: None = 상태 없음 → 빨강 없음), `time_keys.node_fcurves` (`operators/time_keys.py:74-82` → []) → `time_slider.key_frames` (`ui/time_slider.py:729-741`: 눈금 없음) · Time Slider 키 편집 (Cut / Copy / Delete) 대상 없음; Blender Graph Editor / Dope Sheet 는 활성 액션 (또는 tweak 모드) 만 그림 → 커브 사라짐 [I, 돌리지 않음]. 테스트 없음 (`tests/test_step180*` / `188*` / `gui_step180*` 에 `key_frames` / `channel_state` / Graph Editor 0). manual_checks Step 188 의 "a key on AnimLayer1 (Graph Editor)" 는 이 때문에 실패할 가능성 큼 | 3×2 = **6** |
| NB2 | Character set 이 있는 Maya | step 187 이 character set 을 만들었지만 문구 셋이 그 전 그대로: Windows > Relationship Editors > Character Sets 회색 + "Blender has no character sets" (`ui/notices.py:48-49`), Key / Control 범주 notice "Blender has no character sets" (`ui/notices.py:336-340`, Character Mapper / Redirect 등이 이 문구로 뜸), Graph Editor / Dope Sheet Show > Objects > Characters 회색 + 같은 문구 (`ui/notices.py:848-850`). step 182 BS2 (Animation Layers) 와 같은 꼴 — 기능 단계가 범주 notice 를 다시 읽지 않음 | 2×2 = **4** |
| NB3 | Create > Polygon / NURBS Primitives 의 ❒ = 각자 Maya 옵션 창 (`research/maya/menus.json:879-883` Pipe `optionBox: true`, ModCreateMenu.mel:323; 다른 primitive 도 같음) | Maya 창은 Cube / Sphere / Cylinder / Cone / Torus / Plane 6 개뿐 (`operators/option_windows.py:340-370`); Disc · Platonic · Pyramid · Prism + step 190 의 7 개 + NURBS Primitives 8 개는 "redo" (Blender Adjust Last Operation 패널) — step 183 의 ❒ 클릭이 이제 이것을 바로 연다. step 190 문서는 "기존 Disc / Prism 처럼 redo" 라고만 적음 | 2×1 = **2** |
| NB4 | — (5.x 사용자도 Maya 사용자) | 5.x 헤드리스 전체가 step 153 뒤 없음 (`docs/compat_5x.md:62`); 183–190 의 버전 민감 코드 [U]: Time Slider 눈금 `_draw_ruler` 는 `has_slider_panel(space)` 만 봄 (`ui/time_slider.py:532-534`, 5.x 는 사이드바 1 px 라 header 분기 `:86-91` — 눈금이 그려지는지 모름), ❒ 클릭 모델 (`ui/option_click.py`, 4.5 만 측정; 5.x 는 메뉴가 클릭까지 열림 `compat.menus_close_on_leave`), Keying Set API (187), custom split normals / colour attributes (189), NLA slots (180/188). release_check 14 PASS 는 설치 · 켜기만 | 2×2 = **4** |
| NB5 | — (절차) | manual_checks 에 183–190 이 옛 규칙으로 만든 문구 4 개: RMB 목록 "링 옆" (`[x]` 항목, 테스트는 step 184 에서 새 규칙으로 바뀜), "beside the ring 판단" 질문 (184 가 닫음), Relationship Editors > Animation Layers 안내 (188 부터 실제), "회색 Super Ellipse" (190 부터 작동) → 이번에 문구 고침 (§6) | — |
| NB6 | Maya Mesh Display 명령은 history 노드를 남김 (`polyNormalPerVertex` / `polyColorPerVertex`, `research/maya/re/mesh_display_184.md:14-15`) — INPUTS 에 보이고 Construction History 끄면 안 남음 | step 189 노멀 · 색 연산자는 메시를 바로 고침, INPUTS 행 없음 (CB 에 "Blender keeps no edit-mode history" 안내만). Construction History 토글은 primitive / extrude / bevel 만 봄 (`prim_history.history_on` 호출 2 곳: `operators/prim_history.py:371`, `operators/extrude.py:508`) | 1×1 = 1 |

확인했고 blindspot 아님 (근거): 새 primitive 의 AE / CB INPUTS (`ui/attribute_editor.py:151-152` `prim_history.node_of` 일반),
셸프 Super Shape (`ui/shelf_map.py:194` 메뉴 경유), character set S 키의 Undo (`operators/character_sets.py` 모든 편집 `UNDO`),
5.x 의 character set 칸 (`ui/time_slider.py:86-91` → `draw_range_slider` 안에 있음), `menu_consistency` 0 쌍 (별칭 규칙 189).

## 5. GitHub 이슈 (2026-10-25, `gh issue list --state open` / `--state all --limit 300`)

- 전체 **101**, 닫힘 **100**, 열림 **1**: **#89** "Quad Draw leftovers: overlay colour options, Tab+MMB strip resize, Ctrl+Shift+RMB
  options menu" (maya-parity, 0.5.0). 183–191 동안 새 이슈 없음 (`tmp/audit192a/issues_open.txt`, `issues_all.txt`).
- #82 (❒ 클릭) 은 닫혔고 메뉴 바 경로는 183 이 고침 — 다른 입구는 U3.

## 6. 수치 (감사 13 → 지금, bpy stub 셈 — 기준 수치는 lane B)

| 수치 | step 182 (326f12f) | 지금 (13d2153) |
|---|---|---|
| 대응표 | 30 / 1 / 0 / 2 | **30 / 1 / 0 / 2** |
| 메뉴 leaves 작동 (unique 1318) | 714 (54.2 %) | **750 (56.9 %)** |
| 메뉴 세트별 합 (1486) | 821 (55.2 %) | **857 (57.7 %)**, 회색 + notice 없음 0 |
| 메뉴별 (바뀐 것) | Key 22, Control 1, Create 40, Mesh Display 15, UV 16, nHair 2 | Key **30 / 41**, Control **9 / 14**, Create **47 / 70**, Mesh Display **25 / 39**, UV **17 / 19**, nHair **4 / 54** |
| Graph Editor / Dope Sheet / UV Editor / Hypershade / Render Settings / Script Editor | 154 / 130 / 136 / 115 / 10 / 32 | 그대로 |
| 패널 메뉴 / 툴바 / Status Line 회색 | 67 / 111, 22 / 29, 9 | **69 / 111**, 22 / 29, **8** |
| menu_consistency 쌍둥이 | 0 (별칭 못 봄) | 0 (별칭 포함) |
| 헤드리스 전체 | 1683 / 1683 | 1731 / 1731 (step 191 기록; 이 레인은 안 돌림) |
| 열린 이슈 | 1 (#89) | 1 (#89) |
| manual_checks (`- [ ]` / `- [x]` 줄) | 691 / 107 (step 182 뒤) | 705 / 107 → **709 / 107** |

그대로인 약한 곳 (일곱 감사째 포함): nConstraint 0 / 19, Generate 2 / 50, nHair 4 / 54, Toon 1 / 20, Texturing 1 / 8, nCache 3 / 20,
Fluids 4 / 25, Stereo 1 / 6, Effects 2 / 11, nParticles 7 / 25, Fields 14 / 38, Surfaces 15 / 41, nCloth 5 / 13.

## 7. manual_checks 정리 (`docs/manual_checks.md`)

- 셈 = `grep -cE '^\s*- \[( |x)\]'` (step 182 와 같은 셈법).
- 전: **705 항목, 107 체크, 598 열림** (183–190 이 14 항목 추가).
- 후: **709 항목, 107 체크, 602 열림**. 지운 항목 0, 새로 체크 0 (183–190 의 GUI 테스트는 단계 문서에 통과 기록이 있지만 각 항목이
  "실제 마우스 / 느낌" 을 묻는 것이라 증명 못 함).
- **낡은 문구 고침 5** (NB5): step 52 RMB 목록 (링 옆 → step 184 규칙), step 54 Relationship Editors (Animation Layers 는 188 부터
  실제), step 131 회색 아이콘 예 (Super Ellipse → Trim Tool), Step 161 `[x]` 항목 문구 (테스트가 184 에서 새 규칙 — 체크 유지),
  Step 161 절의 "beside the ring" 질문 (step 172 판단 보류) → superseded 표시 (열림 유지).
- **새 「Step 192」 4 항목**: NB1 레이어 오브젝트 키 표시, NB3 primitive ❒ 창, NB2 character set 툴팁, NB4 5.2 Time Slider 눈금 /
  ❒ 클릭.

## 8. 차이 우선순위 top 10 (S×F, 같은 점수는 Maya 사용자가 먼저 부딪히는 순) — 다음 backlog 입력

| 순 | S×F | 차이 | Maya (근거) | 킷 지금 | 한 단계 할 일 · 검증 |
|---|---|---|---|---|---|
| 1 | 6 | 레이어 오브젝트의 키가 CB 빨강 · Time Slider 눈금 · Graph Editor 에서 사라짐 (NB1) | 레이어가 있어도 키 표시 그대로, CB 레이어 색 (`research/maya/channel_box.md:138-139`), Graph Editor 에 레이어 커브 [K] — GUI Maya 로 먼저 잴 것 (`research/maya/screens/anim180/` 이어서) | `anim_layers.py:128` `ad.action = None` → `compat.id_fcurve_collection` None | **"Animation layers 3"**: 키 읽기 한 곳 (`channel_box._fcurves` / `time_keys.node_fcurves`) 이 레이어 오브젝트면 선택 레이어 (없으면 Base) 의 띠 액션 커브를 줌; Graph Editor 는 선택 레이어 띠를 tweak 모드로 (평가는 `anim_layers.solve` 유지) 또는 kit 채널 목록 (`ui/editor_chrome.py`) 에 레이어 커브. 검증: 헤드리스 — 레이어 만든 뒤 `key_frames` / `channel_state` 가 전과 같음, GUI Graph Editor 커브 픽셀 |
| 2 | 6 | Graph Editor 나머지 + Retime Tool (A2, 네 감사째) | Edit > Transformation Tools > Retime Tool (`research/maya/screens/editors104/_editors104.json:316-325`), Swap Buffer Curve (`research/maya/workflows/animation.md:33`) | 154 / 229 회색 75 | **"Graph Editor depth 2"**: Retime Tool (GUI Maya 측정 먼저), Buffer Curve Snapshot / Swap, Weighted Tangents (mayapy 핸들 길이), Pin Channel. 검증: mayapy 비교, Graph Editor ≥ 165 / 229 |
| 3 | 6 | 리그 나머지 (G1) | Skin / Constrain 메뉴 (`research/maya/re/skin_bind_149.md`, `skin_weights_159.md`) | Skin 19 / 28, Constrain 11 / 20 | **"Skin tools 2"**: Move Weights to Influences, Post Normalization, Constrain Remove Target / Set Rest Position, 킷 XML mayapy 왕복. 검증: mayapy 1e-6, Skin ≥ 24 / 28 |
| 4 | 4 | Character set 끝났는데 "Blender has no character sets" 문구 · 회색 입구 3 곳 (NB2) | Relationship Editor (Character Sets) 가 멤버 편집기, Graph Editor Show > Characters 필터 [K] | `ui/notices.py:48-49,336-340,848-850` | **작은 단계** (다른 일과 묶어도 됨): Relationship Editors > Character Sets = `allset.character_attributes` 팝업, Key / Control 범주 notice 를 Mapper / Redirect 에 맞게 다시 씀, Show > Characters = 현재 character 멤버로 채널 거르기 (`filter_text` 또는 kit 채널 목록). 검증: `menu_count` Windows +1, notice 문자열 테스트 ("no character sets" 0), `test_step101` |
| 5 | 4 | 애니 레이어 나머지 (A3) | Merge / Extract / Copy / Delete Empty, Zero Key / Zero Weight / Full Weight, Lock / Solo (`research/maya/channel_box.md:166-169`), 여러 레이어 선택 | 속성 멤버까지 (188) | NB1 과 같은 단계로 묶기 좋음: Merge Layers (mayapy `animLayer` 병합 결과 대조), Zero Key, 여러 레이어 선택. 검증: mayapy 1e-5 |
| 6 | 4 | Channel Box 모양 (C3) | 행 바탕 · 굵은 머리글 · CB/LE 아이콘 3 개 (`step_182_quant.md:268`, `research/maya/screens/compare*/crop_channel_box.png`) | 평평한 행, 아이콘 없음 | **"Channel Box look"**: dock CB `Lines` 그리기에 Maya 측정 색 행 바탕 + 머리글, 위 오른쪽 아이콘 3 개 (`ui/kit_icons.py`). 검증: look_compare `crop_channel_box` ΔE / 새 kit-drawn 샘플 |
| 7 | 4 | 5.x 헤드리스 154–190 (NB4) | — | 마지막 5.x 전체 step 153 | **"5.x pass 2"**: `ALLSET_SANDBOX=… python tests/run.py --blender <5.0/5.1/5.2>` 전체 + GUI `-k step183,step186,step187` 를 5.2 에서; 깨진 것만 `compat.py`. 검증: 네 버전 헤드리스 전체 녹색, `docs/compat_5x.md` 새 절 |
| 8 | 4 | `maya.cmds` 17 함수 (U2) | parent / group / duplicate / setKeyframe / playbackOptions / spaceLocator / file (Maya 스크립트 기본) | `command_line/cmds_shim.py` | **"maya.cmds look-alike 2"** (이월). 검증: 같은 스크립트 mayapy vs 킷 헤드리스 결과 |
| 9 | 4 | 렌더 기본 (F2) | lambert1 = color 0.5 × diffuse 0.8 (`research/maya/re/render_defaults_137.md:34-46`) | 1.25 배 밝음, F12 기본 조명 없음 | **"Render parity 2"** (이월): lambert1 밝기 (Base Color 0.4 또는 노드), Ambient Light. 검증: 렌더 평균 밝기 Maya ±3 % |
| 10 | 4 | Reference Editor (F4) | 목록 + Reload / Unload / Replace / Import Objects (`research/maya/workflows/scene.md:30`) | Outliner Blender File 모드 (`ui/menu_map.py:136`) | **"Reference Editor"** (이월): kit 창. 검증: 링크 .blend 왕복, override 편집 유지 |

다음 (점수 4 이하 이어서): Preferences 창 (U1, 4), UV 나머지 (V1, 4), Curves / Surfaces (S1 / S2, 4), Time Slider 파란 상자 (U13, 3),
CB 상태 색 (C1, 3), primitive ❒ 창 (NB3 / M5, 2), ❒ 클릭 나머지 입구 (U3, 2), Character set node (C4, 2).

## 모르는 것 / 반대 증거

- NB1 은 코드 읽기만 [I]: Blender Graph Editor 가 NLA 띠 액션 커브를 안 그린다는 것은 Blender 동작 지식 [K]; 킷 다른 곳 (예:
  `cb_channels.timeline_curves`) 이 레이어 커브를 따로 주는지 `anim_layers` grep 으로 찾았지만 없음. 돌려 보면 바로 확인됨.
- NB1 의 Maya 쪽 (Graph Editor 레이어 표시, Time Slider 가 어느 레이어 키를 보이는지) 은 측정 없음 [K].
- NB2 Graph Editor Show > Characters 의 Maya 동작 (현재 character 만 보이기 vs character node 목록) [K].
- NB3 primitive 옵션 창 필드는 Maya 창을 잡아 봐야 함 (Cube 창처럼 `research/maya/re/option_boxes.md`).
- NB4 는 위험 목록일 뿐 — 5.x 에서 실제로 깨졌다는 증거는 없음.
- 메뉴 수치는 bpy stub 셈 (Blender poll 실패 안 셈); `--options` 는 Blender 가 필요해 안 돌림 (lane B).
- manual_checks 체크 판단은 GUI 테스트 코드 / 단계 문서 통과 기록에 기댐 — 이 레인은 GUI 를 돌리지 않음.
