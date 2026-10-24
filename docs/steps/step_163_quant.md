# Step 163 부록 — 재점검 11차 수치 감사 (lane B, paper + look_compare)

Step 154 부록 (`docs/steps/step_154_quant.md`)의 수치를 오늘 master에서 같은 방법으로 다시 셌다. 칭찬은 빼고 차이만 적는다.
읽기 전용 감사, 2026-10-24, HEAD 2cd3406 (0.3.0 + steps 145–162). 확장 zip은 `dist/maya-workflow-kit-0.3.0.zip`
(23:04 빌드, HEAD 커밋 23:03 이후 — HEAD와 같다, `--no-build`). 스크립트와 원자료는 저장소 밖 `tmp/audit163b/`에 있다.
step 154 기준선은 `git archive e26b969 src tools` → `tmp/audit163b/old/`, 그리고 step 154의 원자료
(`tmp/option_count154/results/option_kinds.json`, `tmp/audit154b/probe154.json`, `compare_audit154_s100/`)이다.

방법 (step 154와 같음):

- 메뉴: `python tools/menu_count.py` (+ `--greyed`), 메뉴별 표는 `tmp/audit163b/menus_per.py` (step 154 스크립트에 root 인자만 추가),
  e26b969과 HEAD에서 각각 돌려 경로 단위로 비교했다. 에디터 메뉴바는 `tmp/audit154b/ed_diff.py`를 두 root에서 돌렸다.
- 옵션 박스: `ALLSET_SANDBOX=option_count163 python tests/run.py --no-build -k step140_option_count` (1 passed).
  `menu_count.py --options`는 샌드박스 `option_count`를 고정으로 쓰므로 step 154처럼 테스트를 직접 돌렸다 →
  `tmp/option_count163/results/option_kinds.json`.
- 선반 / 서로 다른 옵션 창 / 마킹 메뉴: `tmp/audit163b/run_probe.sh` + `probe_quant.py` (step 133 프로브), 샌드박스
  `tmp/audit163b/sandbox` (폴더를 먼저 만들고 `--factory-startup`, `BLENDER_USER_*`는 모두 tmp 안).
- 마킹 메뉴 분류 (direct / item / greyed / sub): `tmp/audit163b/marking.py` (HEAD와 e26b969의 `marking/menus.py`를 일반 모듈로 import).
- 단축키: `python tools/gen_keymap_mapping.py` (exit 0; `docs/keymap_mapping.md`는 git에 이미 같은 내용이라 바뀐 파일 없음).
  행 비교는 `git show e26b969:docs/keymap_mapping.md`와 비교.
- look_compare: (a) `ALLSET_GUI_UI_SCALE=0.8 ALLSET_LOOK_TAG=audit163_s100 python tmp/audit163b/look_nobuild.py`
  (= `look_compare.main`, `build.main`만 기존 zip을 돌려주게 막음 — 다른 lane이 `dist/`를 쓰는 중) →
  `research/maya/screens/compare_audit163_s100/`, step 154의 `compare_audit154_s100/`과 md 파일 diff.
  (b) 태그·배율 없이 같은 스크립트 (실효 배율 1.25) → `research/maya/screens/compare/`. step 154는 1.25를 돌리지 않았으므로
  1.25 쪽 기준선은 step 134의 `compare_step134_s125/`뿐이다.
- 수동 점검 개수: `docs/manual_checks.md`의 `- [ ]` / `- [x]` 개수 (e26b969은 `git show`로 같은 방식으로 셈).

## 0. Headline (step 154 → now)

| Metric | Step 154 (e26b969, 0.3.0 + 153) | Now (2cd3406, 0.3.0 + 162) | Δ |
|---|---|---|---|
| Unique kit menu leaves (main menu sets) | 1318 | 1318 | 0 (leaf 추가·삭제 없음) |
| ... working (mapped, incl. with notice) | 600 (45.5 %) | **649 (49.2 %)** = 556 + 93 with a notice | **+49** |
| ... greyed with a notice / without | 718 / 0 | 669 / 0 | −49 / 0 |
| Leaves counted per set | 1486, working 667 (44.9 %) | 1486, working **720 (48.5 %)** | +53 |
| `menu_map.MAP` / `notices.NOTICES` / `CATEGORIES` | 1117 / 162 / 179 | 1194 / 166 / 172 | +77 / +4 / −7 |
| Editor menu bars (7 editors, 914 leaves) | 517 (57 %) | **545 (60 %)** — Graph 145 → 154, Dope Sheet 120 → 124, UV Editor 95 → 110 | +28 |
| ... of which web page / Blender Preferences | 52 / 39 → real 426 (47 %) | 52 / **5** → real **488 / 914 (53 %)** | Prefs −34 (Default In/Out Tangent 라디오가 kit 설정으로, step 157) |
| Option-box paths (`OPTION_BOXES`) | 507 | 507 | 0 |
| ... kit Maya option window | 78 paths (68 specs) | **85 paths (75 specs)** | +7 / +7 |
| ... operator dialog | 22 | 22 | 0 |
| ... distinct real windows / dialogs | 83 | **90** | +7 |
| ... tool + Tool Settings | 10 | 10 | 0 |
| ... run + Adjust Last Operation | 121 | 120 | −1 (CV Curve Tool → window) |
| ... "Blender has no settings" (`option_generic`) | 43 | **44** | +1 (−4 → window, +5 dead → generic) |
| ... opens a Blender menu | 1 | 1 | 0 |
| ... dead (box on a greyed item) | 232 (46 %) | **225 (44 %)** | −7 |
| How a box opens (#82) | click = command; window by a 0.2 s press and release | 그대로 (`menu_sets.py:666` hold menu, `from_hold`) | 변화 없음 |
| Shelves (8 tabs, 203 buttons) | 153 working / 50 greyed + notice / 0 | **155 / 48 / 0** | +2 (Curves/Surfaces: Rebuild Curve, Three Point Circular Arc) |
| Hotkeys (468 rows) 구현 / IC / 해당 없음 / 미검토 / macOS | 202 / 27 / 171 / 0 / 68 | **209** / 27 / **164** / 0 / 68 | +7 UV Editor 행 (step 155) |
| Main-menu items with Maya hotkey text | 57; editor menu bars 0 | 57; editor menu bars **0** | 0 |
| Marking menus (26 menus, 474 entries) | 364 working (294 + 70 `item`), 69 greyed (59 + 10 empty sub), 41 submenus | **368 working (298 + 70)**, **65 greyed (55 + 10)**, 41 submenus | +4 (UV marking menus) |
| Manual checks (unticked / ticked) | 504 / 79 (같은 grep으로 e26b969 재계산; step 154 본문은 503) | **540 / 81** | +36 / +2 |
| look_compare viewport (ΔE00 < 5), scale 1.0 | 11/12 | 11/12 | 0 (같은 요소: face stipple) |
| look_compare kit-drawn pixels, scale 1.0 | 5/6 | **6/6** | +1 (`marking_menu_box` 샘플점 재지정, 색 변화 아님) |
| look_compare theme pixels > 5 (not counted) | 19 of 30 | 20 of 31 | +1 (`command_result_field` 새 샘플, ΔE 5.0) |
| look_compare rects / density / scene / grid / furniture / checks, scale 1.0 | 5/12 · 5/6 · 3/3 · ok · 2/3 · 9/9 | 동일 (rects.md, density.md, scene.md, viewport.md, furniture.md diff 없음) | 0 |
| look_compare at scale 1.25 | 측정 안 함 (step 134: rects 3/12, viewport 7/12) | rects 5/12, viewport 11/12, density 5/6 (menu gap −10.4), kit-drawn 6/6 | 기준선 없음 |

읽기: steps 155–162의 폭(breadth)은 거의 전부 **Rigging > Skeleton 한 메뉴** (Joint Labelling 35 + IK enable 2 + 기타 1 = +38)와
**Curves / Create > Curve Tools** (+8), UV Editor 메뉴바 (+15), Graph / Dope Sheet Keys·Select (+13)에서 왔다.
Common 7개 메뉴 중 Create 외 6개, Mesh Display, Surfaces, Generate, Key, Visualize, FX 전 메뉴, Rendering 전 메뉴, Hypershade,
Render Settings, Script Editor 메뉴바는 **한 leaf도 움직이지 않았다**. step 160 (workspaces), 161 (메시지 / four view / RMB list),
162 (Ctrl+Shift shelf add, Hypershade MMB drag)는 이 계수기에 잡히는 항목이 없다 (옵션 창 2개 제외).

## 1. Menus per menu set

| Set | Leaves | Working 154 → now | Greyed + notice 154 → now | Greyed, no notice |
|---|---|---|---|---|
| Common | 449 | 263 → **266** (59 %) | 186 → 183 | 0 |
| Modeling | 349 | 160 → **167** (46 % → 48 %) | 189 → 182 | 0 |
| Rigging | 190 | 71 → **112** (37 % → **59 %**) | 119 → 78 | 0 |
| Animation | 180 | 86 → **88** (48 % → 49 %) | 94 → 92 | 0 |
| FX | 205 | 37 (18 %) | 168 | 0 |
| Rendering | 63 | 19 (30 %) | 44 | 0 |
| (always visible) Cache + Help | 50 | 31 (62 %) | 19 | 0 |

(Deform / Constrain은 Modeling·Rigging·Animation 세트에 중복 집계 — Deform +2가 세 세트에 다 들어간다.)

### 1a. Per top menu (Deform and Constrain shared, listed once)

| Set | Menu | Leaves | % working 154 → now | Working (+ notice) | Greyed + notice | Option boxes |
|---|---|---|---|---|---|---|
| Common | File | 30 | 80 % | 15 + 9 | 6 | 12 |
| Common | Edit | 68 | 66 % | 44 + 1 | 23 | 19 |
| Common | Create | 70 | 53 % → **57 %** | 32 + 8 | 30 | 44 |
| Common | Select | 81 | 62 % | 50 + 0 | 31 | 3 |
| Common | Modify | 90 | 41 % | 33 + 4 | 53 | 31 |
| Common | Display | 36 | 64 % | 20 + 3 | 13 | 2 |
| Common | Windows | 74 | 64 % | 38 + 9 | 27 | 1 |
| Modeling | Mesh | 26 | 81 % | 21 + 0 | 5 | 20 |
| Modeling | Edit Mesh | 28 | 89 % | 25 + 0 | 3 | 18 |
| Modeling | Mesh Tools | 36 | 81 % | 20 + 9 | 7 | 35 |
| Modeling | Mesh Display | 39 | 38 % | 15 + 0 | 24 | 10 |
| Modeling | Curves | 36 | 44 % → **58 %** | 19 + 2 | 15 | 24 |
| Modeling | Surfaces | 41 | 20 % | 4 + 4 | 33 | 37 |
| Modeling | Deform | 74 | 38 % → **41 %** | 16 + 14 | 44 | 47 |
| Modeling | UV | 19 | 84 % | 16 + 0 | 3 | 11 |
| Modeling | Generate | 50 | 4 % | 2 + 0 | 48 | 8 |
| Rigging | Skeleton | 54 | 24 % → **94 %** | 48 + 3 | 3 | 8 |
| Rigging | Skin | 28 | 64 % → **68 %** | 19 + 0 | 9 | 13 |
| Rigging | Constrain | 20 | 55 % | 8 + 3 | 9 | 17 |
| Rigging | Control | 14 | 7 % | 0 + 1 | 13 | 3 |
| Animation | Key | 41 | 51 % | 21 + 0 | 20 | 12 |
| Animation | Playback | 26 | 73 % | 18 + 1 | 7 | 1 |
| Animation | Audio | 9 | 56 % | 4 + 1 | 4 | 0 |
| Animation | Visualize | 10 | 20 % | 2 + 0 | 8 | 4 |
| FX | nParticles | 25 | 28 % | 5 + 2 | 18 | 15 |
| FX | Fluids | 25 | 16 % | 2 + 2 | 21 | 20 |
| FX | nCloth | 13 | 38 % | 2 + 3 | 8 | 3 |
| FX | nHair | 54 | 4 % | 1 + 1 | 52 | 13 |
| FX | nConstraint | 19 | 0 % | 0 + 0 | 19 | 11 |
| FX | nCache | 20 | 15 % | 3 + 0 | 17 | 12 |
| FX | Fields/Solvers | 38 | 37 % | 13 + 1 | 24 | 19 |
| FX | Effects | 11 | 18 % | 2 + 0 | 9 | 8 |
| Rendering | Lighting/Shading | 14 | 36 % | 5 + 0 | 9 | 0 |
| Rendering | Texturing | 8 | 12 % | 1 + 0 | 7 | 2 |
| Rendering | Render | 15 | 73 % | 9 + 2 | 4 | 6 |
| Rendering | Toon | 20 | 5 % | 0 + 1 | 19 | 1 |
| Rendering | Stereo | 6 | 17 % | 0 + 1 | 5 | 0 |
| (always visible) | Cache | 24 | 46 % | 5 + 6 | 13 | 15 |
| (always visible) | Help | 26 | 77 % | 18 + 2 | 6 | 1 |

경로 diff (e26b969 → 2cd3406), **+49 working, 잃은 것 없음**:

- Create (+3, step 156): `Curve Tools/EP Curve Tool`, `Three Point Circular Arc`, `Two Point Circular Arc`.
- Curves (+5, step 156): `Cut`, `Fillet`, `Move Seam`, `Rebuild`, `Straighten`.
- Deform (+2, step 159): `Export Weights...`, `Import Weights...`.
- Skeleton (+38, step 159): `Enable / Disable Selected IK Handles`, `Joint Labelling` 전체 (Add Joint Labels 30, Show / Hide All Labels,
  Toggle Selected Labels, Label Based on Joint Names, Rename Joints From Labels).
- Skin (+1, step 159): `Reset Default Weights`.

움직이지 않은 메뉴: **step 98 이후 네 번째 감사 연속**: Control 7 %, Visualize 20 %, nConstraint 0 %, nCache 15 %, Fields/Solvers 37 %,
Effects 18 %, Texturing 12 %. step 133 이후 세 번 연속: Surfaces, Mesh Display, Modify, Windows. step 145 이후 두 번 연속: Key, Select,
Display, Edit, Generate, 모든 FX 메뉴, Lighting/Shading, Toon, Stereo, Cache.

### 1b. Weakest menus by Maya-user impact (daily use × greyed share), 현재

| Menu | % working | 아직 greyed인, Maya 사용자가 매일·매주 누르는 항목 |
|---|---|---|
| **Modify** | 41 % (greyed 53 — 최다) | `Transformation Tools/Default Object Manipulator/*` 5, `Align Tool`, `Snap Align Objects/Position Along Curve`, `Evaluate Nodes/*` 14, `Convert/Geometry to Bounding Box`, `Convert/Displacement to Polygons`, Asset 14 |
| **Mesh Display** | 38 % | `Set Vertex Normal`, `Apply Color`, 컬러 세트 편집 (Rename / Modify / Assign New / Assign Existing / Edit Assigned Set, Set Keyframe for Vertex Color), `Color Material Channel/*` 6, `Material Blend Setting/*` 7 |
| **Deform** | 41 % (greyed 44) | `Wire` + `Wire#2/*` 7 + `Paint Weights/Wire`, `ShrinkWrap#2/*` 6, `Solidify`, `Tension`, `Morph`, `Jiggle` 3, `Edit Membership Tool`, `Prune Membership/*` 4, `Display / Hide Intermediate Objects`, `Lattice#2/Reset Lattice`, `Remove Lattice Tweaks` |
| **Curves** | 58 % | `Lock / Unlock Length`, `Bend`, `Curl`, `Scale Curvature`, `Duplicate Surface Curves`, `Align`, `Edit Curve Tool`, `Intersect`, `Extend / Offset Curve On Surface`, `CV Hardness`, `Fit B-spline`, `Project Tangent` |
| **Key** | 51 % | `Character Set` 10, `IK/FK Keys/*` 4, `Scene Time Warp/*` 4 (Graph / Dope Sheet Edit에도 4개씩 — 같은 기능 12 leaf), `Set Blend Shape Target Weight Keys`, `Key/Attribute Editor` |
| **Visualize** | 20 % | `Ghost Selected` / `Unghost Selected` / `Unghost All` / `Open Ghosting Editor`, `Create Animation Snapshot`, `Update Snapshot`, `Create Animated Sweep`, `Create Turntable...` |
| **Skin** | 68 % | `Export / Import Weight Maps`, `Interactive Bind Skin` (+ Tool), `Move Weights to Influences`, `Normalize Weights/Enable Weight Post Normalization`, `Bake Deformation to Skin Weights`, `Move Skinned Joints`, `Substitute Geometry` |
| **Select** | 62 % | `All by Type/*` 16 (IK Handles, Clusters, Wires, Particles ...), `Components/Vertex Face`, `Convert Selection/To Vertex Faces`, NURBS 컴포넌트 9, `Use Constraints...` |
| **Surfaces** | 20 % | 33 greyed (Rebuild, Trim / Untrim, Intersect, Attach / Detach, Extend, Birail ...); 옵션 박스 37 중 29 dead |
| Generate / nHair / nConstraint / Toon | 0–5 % | Blender 대응 없는 시스템 전체 (Paint Effects, XGen, Nucleus hair / constraints, Toon) — notice만 |

Curves는 이 표의 1위에서 내려왔고 (44 → 58 %), Skeleton은 표에서 빠졌다 (94 %; 남은 3개는 IK Handle Snap, IK/FK Control, HumanIK).

### 1c. Editor menu bars (step 104 / 105)

| Editor | Leaves | Working 154 → now | Greyed + notice | Most-greyed menus now |
|---|---|---|---|---|
| Graph Editor | 229 | 145 → **154 (67 %)** | 75 | View 20 / 40, Show 18 / 34, Curves 16 / 39, Edit 10 / 23, List 6 / 8 |
| Dope Sheet | 181 | 120 → **124 (69 %)** | 57 | Show 18 / 34, Curves 17 / 34, Edit 10 / 23, List 6 / 7 |
| UV Editor | 172 | 95 → **110 (64 %)** | 62 | Select 13 / 39, View 10 / 20, Modify 9 / 31, Tools 8 / 19, Image 8 / 14, UV Sets 7 / 11 |
| UV Toolkit | 3 | 1 → 1 | 2 | Maya UV Toolkit 패널 전체가 여전히 menu leaf 3개 |
| Hypershade | 249 | 114 → 114 (46 %) | 135 | Create 91 / 160, Edit 21 / 30, Tabs 6 / 6, Options 6 / 6 |
| Render Settings | 21 | 10 → 10 | 11 | Presets 9 / 10 |
| Script Editor | 59 | 32 → 32 | 27 | **History 13 / 13** (네 번째 감사 연속 0 %) |

새로 working (경로 diff, +28):

- Graph Editor / Dope Sheet `Keys/Mute Key`, `Unmute Key` (×2 에디터), `Tangents/Default In / Out Tangent/Flat` (×2), Graph Editor
  `Select/Curve`, `Key`, `In Tangent`, `Out Tangent`, `Only Curve` (step 157).
- UV Editor (step 155): `Edit/Delete`, `Cut/Sew/Create UV Shell`, `Modify/Distribute Shells`, `Normalize`, `Orient Shells to Edges`,
  `Snap Together`, `Snap and Stack`, `Stack Shells`, `Stack and Orient Shells`, `Unstack Shells`, `Tools/Move UV Shell`,
  `View/Isolate Select/View Selected`, `View/Texture Borders`, `View/Toggle Shell Borders`, `Image/Display`.

정직성 메모: web page 52개는 그대로. Blender Preferences를 여는 항목은 39 → 5 (`Graph Editor/Edit/Preferences`,
`Dope Sheet/Edit/Preferences`, `Graph Editor/View/Keys/Always`, `Active Only`, `View/Theme/Color Preferences`) — `Keys/Always`·`Active Only`가
Preferences > Animation을 여는 것은 Maya의 표시 옵션이 아니다.

UV Editor에 아직 greyed인 매일 쓰는 도구: `Tools/Unfold`, `Cut`, `Sew`, `Pin`, `Smudge`, `Lattice`, `Symmetrize` (UV 메인 메뉴의 Unfold /
3D Cut and Sew는 working인데 UV Editor의 Tools 메뉴에서는 greyed), `Modify/Map Border`, `Straighten Border`, `Match Grid`, `Symmetrize`,
`Layout Along`, `Stack Similar Shells`, `Cut/Sew/Auto Seams`, `Split`, `Select/Convert Selection/To Edge Loop / To Edge Ring /
To Contained Edges / To Connected Faces / To Contained Faces`, `Select/Back-Facing / Front-Facing / Unmapped Faces / Texture Borders`,
`Edit/Unpin All`, `View/Isolate Select/Add Selected / Remove Selected / Remove All / Load Set`.

Graph Editor에서는 working인데 **Dope Sheet `Curves`에서만 greyed**: `Euler Filter`, `Smooth Filter (Butterworth / Gaussian)`,
`Resample Curve`, `Isolate Curve`, Dope Sheet `View/Auto Frame` — 같은 동작을 Dope Sheet 경로에 연결하지 않은 것.

## 2. Option boxes per top menu (507 paths)

window = kit Maya option window, dialog = operator / file dialog, tool = tool + Tool Settings, redo = run + Adjust Last Operation,
generic = "Blender has no settings for this" 창, dead = greyed 항목의 박스. 바뀐 칸만 [step 154 값].

| Menu | window | dialog | tool | redo | generic | dead |
|---|---|---|---|---|---|---|
| File | 2 | 6 | – | 1 | 1 | 2 |
| Edit | **13** [12] | – | – | 2 | **0** [1] | 4 |
| Create | **8** [6] | 1 | – | **18** [19] | **3** [1] | **14** [17] |
| Select | – | – | – | 2 | – | 1 |
| Modify | 2 | – | 4 | 7 | 1 | 17 |
| Display | **2** [1] | – | – | 0 | **0** [1] | 1 |
| Mesh | 2 | 1 | 1 | 11 | – | 4 (+1 menu) |
| Edit Mesh | 6 | – | 1 | 9 | – | 2 |
| Mesh Tools | 4 | 3 | 4 | 17 | – | 7 |
| Mesh Display | – | 1 | – | 5 | 1 | 3 |
| Curves | **3** [0] | – | – | 4 | **6** [5] | **11** [15] |
| Surfaces | – | – | – | 3 | 5 | 29 |
| Deform | 16 | – | – | 2 | 9 | 20 |
| UV | 3 | – | – | 3 | 3 | 2 |
| Generate | – | – | – | – | – | 8 |
| Skeleton | 3 | – | – | 3 | 2 | – |
| Skin | 4 | – | – | 3 | 1 | 5 |
| Constrain | 6 | – | – | 4 | – | 7 |
| Control | – | – | – | – | 1 | 2 |
| Key | 9 | – | – | – | – | 3 |
| Playback / Windows | – | 1 / 1 | – | – | – | – |
| Visualize | – | – | – | 1 | – | 3 |
| nParticles / Fluids / nCloth / nHair / nConstraint / nCache | – | – | – | 2 / 3 / – / 2 / – / 3 | 5 / 1 / 2 / – / – / – | 8 / 16 / 1 / 11 / 11 / 9 |
| Fields/Solvers / Effects | – | – | – | 13 / 2 | – | 6 / 6 |
| Render / Texturing / Toon | 2 / – / – | – | – | – | 2 / 1 / – | 2 / 1 / 1 |
| Cache | – | 8 | – | – | – | 7 |
| Help | – | – | – | – | – | 1 |

경로 diff (11개):

- → window: `Create/Curve Tools/CV Curve Tool` (redo → window), `EP Curve Tool` (dead → window), `Curves/Attach` (generic → window),
  `Curves/Fillet`, `Curves/Rebuild` (dead → window), `Display/Toggle Show/Hide`, `Edit/Delete by Type/Non-Deformer History`
  (generic → window, step 162 — step 154가 지적한 두 회귀가 Maya 창으로 해결).
- **dead → generic (5)**: `Create/Curve Tools/Three Point Circular Arc`, `Two Point Circular Arc`, `Curves/Cut`, `Curves/Straighten`
  (step 156) — 메뉴 항목은 살아났지만 박스는 "Blender has no settings" 창이다. Maya에서는 넷 다 실제 옵션 창이 있다
  (Arc: Degree / Sections, Cut: Find intersections / Keep, Straighten: Smoothness / Preserve length).

generic 44개 중 Maya 사용자가 매일 쓰는 박스: `Curves/Cut`, `Detach`, `Smooth` (×2), `Reverse Direction`, `Straighten`,
`Create/Curve Tools/Three / Two Point Circular Arc`, `Pencil Curve Tool`, `UV/Merge UVs`, `UV/Contour Stretch`, `UV/3D Cut and Sew UV Tool`,
`Skeleton/Set` / `Assume Preferred Angle`, `Skin/Edit Influences/Add Influence`. 매주: `Deform/Paint Weights/*` 9, `Surfaces/Loft / Extrude /
Planar / Bevel Plus / Reverse Direction`, `nCloth/Create nCloth / Create Passive Collider`, `nParticles/Create Emitter` (×2) / `Emit from Object` (×2)
/ `Make Collide`, `Fluids/Make Collide`, `Modify/Bake Pivot`, `Mesh Display/Paint Vertex Color Tool`, `Texturing/3D Paint Tool`,
`File/Archive Scene`, `Control/Create Character Set`. `Render/Render Current Frame` / `IPR`는 Maya와 같은 경고 문구 (step 152)지만
분류기는 generic으로 센다.

dead 225개를 메뉴별로 많은 순: Surfaces 29, Deform 20, Modify 17, Fluids 16, Create 14, Curves 11, nHair 11, nConstraint 11,
nCache 9, Generate 8, nParticles 8, Cache 7, Constrain 7, Mesh Tools 7, Fields/Solvers 6, Effects 6, Skin 5.

박스를 여는 방법: 여전히 plain click = 명령 실행, 창은 0.2 s 누르고 떼기 (`ui/menu_sets.py:666` hold menu). ❒ 부분을 클릭하는
Maya 습관으로는 창이 열리지 않는다 (#82, 네 번째 감사 연속 같은 상태). 이번 lane은 GUI에서 다시 재지는 않았고 코드 경로만 확인했다.

## 3. Shelves (`ui/shelf.all_buttons`)

203 buttons, **155 working (76 %)**, 48 greyed with a notice, 0 without. 변화: Curves / Surfaces 24 → 26 (`Rebuild Curve`,
`Three Point Circular Arc`, step 156).

| Shelf | Buttons | Working | Greyed (+ notice) |
|---|---|---|---|
| Curves / Surfaces | 38 | **26** | 12: Curve Editing Tool, Birail 1 Tool, Project Curve on Surface, Intersect / Trim / Untrim / Attach / Detach / Extend / Rebuild Surfaces, Sculpt Geometry Tool, Surface Editing Tool |
| Poly Modeling | 43 | 41 | 2: Super Shape, 3D Grab UV Tool |
| Sculpting | 26 | 19 | 7: Imprint, Convert To Frozen, Pose Editor, Smooth / Clone / Mask / Erase Target |
| Rigging | 18 | 17 | 1: Human IK |
| Animation | 14 | 14 | 0 |
| Rendering | 25 | 21 | 4: Ambient Light, Volume Light, Shading Map, Render Diagnostics |
| FX | 29 | 13 | 16: 2D Fluid Container with Emitter, Make Selected Curves Dynamic, 14 nHair buttons |
| FX Caching | 10 | 4 | 6: Set / Clear Initial State, Enable / Disable All Caches, Merge Caches, Replace Cache Frame |

step 162의 Ctrl+Shift+click 선반 추가는 사용자 선반을 늘리는 기능이라 factory 버튼 수에는 잡히지 않는다.

## 4. Hotkeys / marking menus

Hotkeys (`docs/keymap_mapping.md`, 468 rows): 구현 **209** (+7), IC 일치 27, 해당 없음 **164** (−7), 미검토 0, macOS 전용 68.
옮겨진 7행은 모두 UV Editor (`polyTexturePlacementPanel`, step 155): 4 `DisplayUVWireframe`, 6 `ToggleUVTextureImage`,
8 `ToggleUVShellBorder`, 9 `UVEditorToggleTextureBorderDisplay`, Ctrl+1 `ToggleUVIsolateViewSelected`, Ctrl+Shift+X
`CreateUVShellAlongBorder`, Delete `DeleteUVs`. 남은 164 n/a의 큰 덩어리는 그대로: Hypershade / Node Editor 57행, Time Editor 32행,
Graph Editor `l` 등.

메뉴 hotkey 글자: 메인 메뉴 57개, 에디터 메뉴바 0개 (불변). step 155가 UV Editor 키를 묶었지만 UV Editor 메뉴에 키 글자가 없다
(예: `View/Toggle Shell Borders` 옆에 Maya는 8을 표시).

Marking menus: 474 entries, **368 working** (298 direct + 70 `item`), **65 greyed** (55 + 빈 submenu 10), 41 submenus.
변화 (step 155): `contextPolyToolsUVMM` SE `Create UV Shell`, SW `Delete UVs`, 리스트 `Texture Borders`, `contextPolyToolsUVShellMM`
`Texture Borders` 가 working. greyed로 남은 55개 분포: Shift+Q `doSelectComponentMM` 25 (비메시 마스크), translate 4, select-all 4,
curve RMB 3, Shift+RMB default 3, rotate 2, hotbox east / west 2+2, 나머지 1씩 (UV 두 메뉴의 `Auto Seams` 포함).

## 5. look_compare

### 5a. 실효 UI 배율 1.0 (`compare_audit163_s100/`, 15 side-by-side, 6 crops)

- checks 9/9; pixels kit-drawn **6/6** (theme 31, 20 > 5 not counted, 1 no kit element); viewport **11/12**; rects **5/12**; scene 3/3;
  density 5/6 (menu top − bar bottom −6 px); grid ok (ΔE00 0.7, corners 4/4, 0.194 ms); furniture 2/3 (axis triad outline only).
- step 154 대비 pixels.md만 바뀜: `marking_menu_box` 샘플점이 (797,414) → (783,438)로 재지정되어 ΔE 13.0 → 0.3 (step 154의 지적 해결).
  `marking_menu_list_bg`의 kit 샘플이 (791,657) → (616,352)로 옮겨졌고 설명이 "kit: the column left of the ring" — 아래 5c-1 참조.
  `command_result_field`가 새로 측정됨 (step 161의 결과 칸): Maya #2b2b2b vs kit #1b1b1b, ΔE 5.0 ✗.
- 나머지 md (rects, density, scene, viewport, furniture)는 step 154와 바이트 단위로 같다. grid draw 시간만 0.178 → 0.194 ms.

### 5b. 실효 UI 배율 1.25 (`compare/`, 이 PC 기본)

- checks 9/9, kit-drawn 6/6, viewport 11/12, rects 5/12, scene 3/3, density 5/6 (**menu top − bar bottom −10.4 px**), grid ok
  (0.224 ms), furniture 2/3.
- rects ✗ (Maya Qt 논리 px 대비이므로 1.25에서는 위젯이 커지는 것이 일부 당연하지만, 결과적으로): Shelf 높이 80 vs 64,
  Tool Box 폭 70 vs 40, Outliner 폭 325 vs 260, **메인 뷰포트 폭 850 vs 1003 (−153 px)**, dock 폭 346 vs 260 (+86),
  Time Slider 폭 1225 vs 1596 (−371 px). 125 % Windows의 Maya 사용자는 Maya도 125 %로 보므로 이 차이의 크기는 과대평가일 수 있다 — Maya를
  125 %로 찍은 기준 이미지가 없어 확인 못 함 (§7).

### 5c. 이미지에서 보이는 차이 (왼쪽 Maya, 오른쪽 kit; 차이만)

1. **RMB 마킹 메뉴 리스트 위치** (`14_marking_menu_object`, 가운데 아래 / 왼쪽): Maya는 링 바로 아래에 한 열로 내려가 창 아래로
   잘린다. kit는 step 161 이후 한 열이지만 **링의 왼쪽 옆** (x≈1305–1410, 링 중심 x≈1510)에 위에서부터 놓인다. Maya 사용자의 "RMB 후
   아래로 끌기" 동선이 맞지 않는다. 또 kit는 `DG Traversal`, `Inputs`, `Outputs`, `Metadata`, `Time Editor`, radial `Vertex Face`를 회색으로
   그리고 Maya는 활성이다. kit 링 가운데의 원형 커서는 Maya에 없다.
2. **Four view** (`16_four_view`): kit 네 칸 위에 panel menu + toolbar가 한 벌뿐 (Maya: 칸마다 한 벌). kit 직교 칸의 큐브가 Maya보다 약
   3–4배 크다 (step 161에서 30 units across로 맞췄다고 했지만 이 샷에서는 kit 큐브 ≈ 37 px 폭, Maya ≈ 10 px). 라벨 `top -Z` / `front +Y`
   vs Maya `top -Y` / `front -Z` (Y-up, 결정 C). ViewCube가 kit에서는 front 칸에만 ("FRONT"), Maya는 top 칸에 "TOP". 장면 상태도
   다르다: Maya 샷은 선택 없음 (Channel Box에 "Select objects in the scene..." 안내 문구), kit 샷은 pCube1이 선택되어 네 칸 모두
   manipulator — 샷 스크립트의 시나리오 차이 (`tools/look_shots.py`).
3. **선택된 면** (`07_faces_selected`): kit는 면을 불투명에 가까운 주황으로 채운다; Maya는 #e3ac79 stipple 25 %. step 134 이후 유일한
   viewport ✗ (ΔE 40.5). 또 Maya는 면 모드에서 Move manipulator가 선택 면에 남는데 kit 샷은 Select Tool (manipulator 없음, Help Line
   "Select Tool: ...").
4. **정점 모드 Channel Box** (`08_verts_selected`, 오른쪽 위 dock): Maya는 컴포넌트 모드에서 `pCube1Shape` / `INPUTS polyCube1`만 보이고
   Translate/Rotate/Scale 행이 없다. kit는 오브젝트 모드와 같이 pCube1의 Translate X…Visibility 10행을 그대로 보여 준다
   (`ui/channel_box.py`에 컴포넌트 모드 분기 없음). 08 / 09에서도 kit는 Select Tool, Maya는 Move manipulator가 정점에 있다.
5. **Outliner** (`crop_outliner`): 행 아이콘이 Blender 주황 삼각 메시 아이콘 (Maya: 회색 transform 마름모), 선택 행 글자가 주황
   (Maya 흰 글자 + #5285a6 배경, kit #334d80), 줄무늬 배경, 순서 pCube1–3 → persp/top/front/side (Maya: 카메라가 먼저), 검색 칸이
   메뉴줄 오른쪽 작은 칸 (Maya: 메뉴 아래 한 줄 전체), "Outliner" 제목 줄 없음, 스크롤바 없음, 편집 모드에서 메시 행 앞 점 표시 (07/08).
6. **Create 메뉴** (`12_create_menu`): 메뉴가 메뉴바와 6 px (1.25에서 10 px) 겹친다; 첫 줄이 Maya "Objects" 섹션 라벨 대신 tear-off 점선;
   Blender 밑줄 니모닉; Maya 2022 샷에 없는 `Subdiv Primitives` 행; kit에서 `Adobe(R) Illustrator(R) Object...`, `Construction Plane`,
   `Scene Assembly`가 회색 (Maya 활성).
7. **Move manipulator** (`02_cube_selected_move`): Maya의 빨강 / 파랑 평면 사각형이 축 사이에 뚜렷한데 kit에는 작은 사각형 흔적만 있다.
8. **Hotbox** (`13_hotbox`): kit 행 블록이 Maya보다 약 20 px 아래에서 시작하고 행 폭이 좁다; 가운데 "Maya Workflow Kit" (Maya "Maya");
   MASH 행 없음 (플러그인, 예상됨).
9. **Time Slider** (`crop_time_slider`): kit 눈금 숫자가 크고 5 프레임마다 큰 라벨, 프레임마다 짧은 틱이 없다; 현재 프레임 표시가 파란 말풍선
   (Maya: 회색 박스 + 세로선); 끝 (120 이후) 붉은 영역; 현재 프레임 칸 + 재생 버튼이 같은 줄이 아니라 오른쪽 별도 area (rect Δw −296,
   Δy +24).
10. **Status Line** (`crop_status_line`): kit는 여러 그룹이 ▷로 접혀 있다 (snap 그룹 아이콘 일부, 오른쪽 아이콘 4개뿐); Maya의 로그인 /
    계정 버튼 (예상됨) 없음; undo/redo 아이콘이 비활성 회색.
11. **아래 줄**: Command Line 언어 라벨 `Python` (Maya `MEL`); 결과 칸 #1b1b1b vs #2b2b2b; 상단 바 오른쪽 끝 Maya / Blender 스위치
    (Maya에 없음); Workspace 드롭다운 값 "Maya Classic" (Maya 2022 샷 "General*").
12. **테마 색** (결정 #45, 변화 없음): 메뉴바 / 팝업 #181818 vs Maya #444444 / #525252, 에디터 사이 틈 #161616 vs #5c5c5c, frame 칸 #545454 vs
    #2b2b2b, Tool Box 활성 도구 #4772b3 vs #5285a6, Layer 탭 #262626 vs #444444.
13. **레이아웃 rect (1.0)**: Tool Box / Outliner / viewport / dock이 Maya보다 37 px 크고 10 px 위에서 시작 (Outliner는 제목 줄 때문에 Maya가 27 px
    아래), dock 27 px 넓음 (287 vs 260) — step 154와 같은 값.

## 6. Ranked remaining gaps and one-step backlog

수치로 본 우선순위 (Maya 사용자 체감 × 크기). 각 항목은 한 step 분량.

1. **옵션 박스 클릭 = 창 (#82)** — 507 박스 전부에 걸리는 조작 차이, 네 번째 감사 연속 미해결.
   지시: ❒가 붙은 메뉴 줄에서 마우스 x가 행 오른쪽 끝 ❒ 폭 안이면 명령 대신 옵션 창을 여는 경로를 찾는다 (예: `allset.menu_item` invoke에서
   `event.mouse_region_x`가 아니라 클릭 직전 hover 위치를 timer로 기록, 또는 ❒ 전용 hover gizmo). 불가능이 측정되면 그 측정을 문서화하고
   hold를 기본 경로로 남긴다. 검증: GUI 테스트 — ❒ 위 클릭이 창을 열고 라벨 클릭은 명령 실행.
2. **Modify 메뉴 41 % (greyed 53)** — 지시: `Default Object Manipulator/*` 5 (tool 전환 pref), `Align Tool`, `Snap Align Objects/Position Along Curve`,
   `Convert/Geometry to Bounding Box`, `Evaluate Nodes/*` (IK Solvers / Constraints = 제약·IK mute 토글, Ignore All)를 `menu_map`에 연결.
   검증: `menu_count.py`에서 Modify ≥ 60 %, 각 항목 headless 테스트.
3. **Mesh Display 38 %** — 지시: `Set Vertex Normal` (custom split normals), `Apply Color`, 컬러 세트 Rename / Assign / Edit, `Set Keyframe for Vertex Color`,
   `Color Material Channel` / `Material Blend Setting` (뷰포트 attribute 표시 모드). 검증: Mesh Display ≥ 65 %, mayapy 대조 (vertex normal 값).
4. **Deform 41 % + dead 20 / generic 9** — 지시: `Wire` + `Wire#2/*` (Blender Curve 기반 hook/Surface Deform 근사, mayapy 측정), `ShrinkWrap#2/*` 6
   (Shrinkwrap modifier target/inner 설정), `Solidify`, `Tension`; `Paint Weights/*` 9개 generic 박스를 Maya Paint Weights 창으로.
   검증: Deform ≥ 60 %, generic 9 → 0, mayapy 결과 1e-4.
5. **RMB 리스트 위치 / 회색 항목** (§5c-1) — 지시: 리스트를 링 아래에 두고 창 아래로 넘치면 Maya처럼 잘리게 (또는 스크롤) 하며, 옆 배치는
   아래 공간이 한 행도 없을 때만. `Inputs` / `Outputs`를 INPUTS 노드 / 연결 목록 submenu로 채운다. 검증: look_compare `marking_menu_list_bg`
   kit 샘플점이 링 아래 (Maya 860,600 근처), GUI 테스트.
6. **컴포넌트 모드 Channel Box** (§5c-4) — 지시: 편집 모드에서는 Maya처럼 shape 노드 + INPUTS만 보이고 transform 행을 숨긴다 (선택 정점이 있으면
   Maya의 `CVs (click to show)` 행). 검증: headless channel_box 행 목록 테스트 + look_compare 08 crop.
7. **Curves 남은 15 + generic 6 + dead 11** — 지시: `Cut` / `Straighten` / Arc 두 개의 generic 박스를 Maya 옵션 창으로 (Degree / Sections, Find
   intersections, Smoothness / Preserve length), `Duplicate Surface Curves`, `Align`, `Lock / Unlock Length`, `Bend` / `Curl` / `Scale Curvature`,
   `Fit B-spline` (curves_math, mayapy 대조). 검증: Curves ≥ 75 %, Curves generic 6 → ≤ 2.
8. **Key 51 % / Visualize 20 %** — 지시: `Create / Update Animation Snapshot` (프레임별 evaluated mesh 복제 그룹), `Ghost Selected` /
   `Unghost` (프레임 오프셋 draw 핸들러), `Scene Time Warp` 4 (+ Graph / Dope Sheet Edit 같은 4개 = 12 leaf, 시간 리맵 F-curve 또는 NLA strip
   time). 검증: Key ≥ 65 %, Visualize ≥ 60 %, 에디터 leaf +8.
9. **UV Editor 64 %** — 지시: UV Editor `Tools/Unfold`, `Cut`, `Sew`, `Pin`을 메인 UV 메뉴 / step 79 tool과 같은 동작에 연결, `Modify/Map Border`,
   `Straighten Border`, `Match Grid`, `Stack Similar Shells`, `Cut/Sew/Auto Seams` (+ 마킹 메뉴 2개), Convert Selection 5개 (`select_convert` 재사용).
   검증: UV Editor ≥ 80 %, marking greyed 55 → 53.
10. **Dope Sheet ↔ Graph Editor 동치 항목** — 지시: Dope Sheet `Curves/Euler Filter`, `Smooth Filter` ×2, `Resample Curve`, `Isolate Curve`,
    `View/Auto Frame`을 Graph Editor와 같은 동작에 연결 (6 leaf, 작은 step 또는 9번에 합침). 검증: ed_diff에서 Dope Sheet +6.
11. **선택 면 stipple** (viewport 11/12, step 134 이후 고정 실패) — 지시: `ui/component_colors.py`에서 선택 면을 25 % stipple (또는 알파 0.25
    단색)로. 검증: look_compare viewport 12/12.
12. **Four view** (§5c-2) — 지시: 직교 칸 배율을 Maya 샷과 맞추고 (큐브 화면 폭 ±10 %), ViewCube를 top 칸에. 칸별 header는 Blender Quad View
    한계 — 측정해 불가면 notice. 검증: look_compare에 four-view scene 행 추가.
13. **Skin 68 %** — 지시: `Export / Import Weight Maps` (이미지 기반 weight, UV 샘플링), `Move Weights to Influences`, `Enable Weight Post Normalization`
    (pref + 페인트 후 normalize). 검증: Skin ≥ 85 %, mayapy 대조.
14. **Script Editor History 0 / 13, Hypershade Create 91 greyed** — History 메뉴 13개는 kit Info 기록 표시 토글로 매핑 가능 (Echo All Commands,
    Line Numbers 등). 검증: Script Editor ≥ 70 %.
15. **에디터 메뉴 hotkey 글자 0** — 지시: `tools/gen_menu_hotkeys.py`를 editor 메뉴바 (`<Editor>/<Menu>/...`)까지 확장 (UV Editor 4/6/8/9, Ctrl+1,
    Graph Editor f/a/i 등). 검증: editor 메뉴 hotkey > 0, GUI 메뉴 샷.

## 7. Not measured

- Maya와 나란히 하는 실제 시나리오 실행 (파일 입출력, 모델링, UV, 애니, 리깅, FX, 렌더): 이 lane은 수치 재계산과 look_compare만 했다.
  Maya 이미지는 기존 `research/maya/screens/*` 그대로이고 새 Maya 캡처는 없다.
- 1.25 배율의 Maya 기준: Maya 샷은 Qt 논리 px (= 1.0)뿐이라 §5b rect 차이는 과대평가일 수 있다.
- 옵션 박스 클릭 동작은 GUI로 다시 재지 않고 코드 경로만 확인 (§2).
- 서로 다른 옵션 창 수 (90)는 step 133 프로브 기준; 창마다 필드가 Maya와 같은지는 보지 않았다.
- step 160 (workspaces) / 161 (메시지, four view, 한 열 RMB) / 162 (Ctrl+Shift 선반 추가, Hypershade MMB drag)의 효과는 이 계수기에 잡히지 않아
  §5c 이미지 관찰 외에는 수치가 없다.
