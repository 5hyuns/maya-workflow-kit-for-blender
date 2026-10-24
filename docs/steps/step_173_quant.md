# Step 173 부록 — 재점검 12차 수치 감사 (lane B, paper + look_compare)

Step 163 부록 (`docs/steps/step_163_quant.md`)의 수치를 오늘 master에서 같은 방법으로 다시 셌다. 칭찬은 빼고 차이만 적는다.
기준: 「기본 Maya에 Blender 기능이 붙은 모습」. 읽기 전용 감사, 2026-10-25, HEAD c8d006c (0.4.0 = 0.3.0 + steps 164–172).
확장 zip은 `dist/maya-workflow-kit-0.4.0.zip` (03:25 빌드) — 파일 215개를 `src/allset`과 바이트 비교해 차이 0이라 HEAD와 같다
(재빌드 안 함: 다른 lane이 `dist/`를 쓸 수 있음). 스크립트와 원자료는 저장소 밖 `tmp/audit173b/`.
step 163 기준선은 `git archive 2cd3406 src tools` → `tmp/audit173b/old/`, 그리고 step 163의 원자료
(`tmp/option_count163/results/option_kinds.json`, `tmp/audit163b/probe163.json`, `compare_audit163_s100/`, `compare/`)이다.

방법 (step 163과 같음, 경로만 바꿈):

- 메뉴: `python tools/menu_count.py`, 메뉴별 표 `tmp/audit173b/menus_per.py <root>` (2cd3406과 HEAD 각각, 경로 단위 diff),
  에디터 메뉴바 `tmp/audit173b/ed_diff.py <root>`.
- 옵션 박스: `ALLSET_SANDBOX=q173 python tests/run.py --no-build -k step140_option_count` (1 passed) →
  `tmp/q173/results/option_kinds.json`. `menu_count.py --options`는 샌드박스 `option_count` 고정 + 빌드를 하므로 쓰지 않았다.
- 선반 / 서로 다른 옵션 창 / 마킹 메뉴: `tmp/audit173b/run_probe.sh` + `probe_quant.py`, 샌드박스 `tmp/audit173b/sandbox`
  (폴더 먼저 생성, `--factory-startup`, `BLENDER_USER_*` 모두 tmp 안) → `tmp/audit173b/probe173.json`.
- 마킹 메뉴 분류: `tmp/audit173b/marking.py` (HEAD와 2cd3406의 `marking/menus.py`).
- 단축키: `python tools/gen_keymap_mapping.py` (exit 0; `docs/keymap_mapping.md` 내용 변화 없음 — git diff 없음).
- look_compare: (a) `ALLSET_GUI_UI_SCALE=0.8 ALLSET_LOOK_TAG=audit173_s100 python tmp/audit173b/look_nobuild.py`
  (= `look_compare.main`, `build.main`이 기존 0.4.0 zip을 돌려줌) → `research/maya/screens/compare_audit173_s100/`;
  (b) 배율 없이 `ALLSET_LOOK_TAG=audit173_s125` (실효 1.25) → `compare_audit173_s125/`. 각각 step 163의 `compare_audit163_s100/`,
  `compare/` (10-24 23:09, step 163 1.25 실행)과 md diff.
- 수동 점검: `docs/manual_checks.md`의 `- [ ]` / `- [x]` 개수 (작업 사본; lane A가 동시에 고칠 수 있음).

## 0. Headline (step 163 → now)

| Metric | Step 163 (2cd3406, 0.3.0 + 162) | Now (c8d006c, 0.4.0) | Δ |
|---|---|---|---|
| Unique kit menu leaves (main menu sets) | 1318 | 1318 | 0 |
| ... working (mapped, incl. with notice) | 649 (49.2 %) | **699 (53.0 %)** = 596 + 103 with a notice | **+50** |
| ... greyed with a notice / without | 669 / 0 | 619 / 0 | −50 / 0 |
| Leaves counted per set | 1486, working 720 (48.5 %) | 1486, working **806 (54.2 %)** | +86 (Deform가 세 세트에 중복) |
| `menu_map.MAP` / `notices.NOTICES` / `CATEGORIES` | 1194 / 166 / 172 | 1259 / 178 / 171 | +65 / +12 / −1 |
| Editor menu bars (7 editors, 914 leaves) | 545 (60 %) | **560 (61 %)** — Dope Sheet 124 → 130, UV Editor 110 → 118, Hypershade 114 → 115 | +15 |
| ... minus web page 52 / Blender Preferences 5 | real 488 / 914 (53 %) | real **503 / 914 (55 %)** | +15 |
| Option-box paths (`OPTION_BOXES`) | 507 | 507 | 0 |
| ... kit Maya option window | 85 paths (75 specs) | **104 paths (95 specs)** | +19 / +20 |
| ... distinct real windows / dialogs | 90 | **109** | +19 |
| ... operator dialog / tool / redo / menu | 22 / 10 / 120 / 1 | 22 / 10 / 120 / 1 | 0 |
| ... "Blender has no settings" (`option_generic`) | 44 | **36** | −8 (Paint Weights 9 → window, Key/Create Character Set dead → generic) |
| ... dead (box on a greyed item) | 225 (44 %) | **214 (42 %)** | −11 |
| How a box opens (#82) | click = command; window by a 0.2 s hold | 그대로 (`ui/menu_sets.py:664-680`, `from_hold`) | **다섯 번째 감사 연속 같음** |
| Shelves (8 tabs, 203 buttons) | 155 working / 48 greyed + notice / 0 | 155 / 48 / 0 | 0 |
| Hotkeys (468 rows) 구현 / IC / 해당 없음 / 미검토 / macOS | 209 / 27 / 164 / 0 / 68 | 209 / 27 / 164 / 0 / 68 | 0 |
| Main-menu items with Maya hotkey text | 57; editor menu bars 0 | 57 (`ui/menu_hotkeys.HOTKEYS`); editor 0 | 0 |
| Marking menus (26 menus, 474 entries) | 368 working (298 + 70 `item`), 65 greyed (55 + 10 empty sub), 41 submenus | **같음** (greyed 경로 집합 diff 0) | 0 |
| Manual checks (unticked / ticked) | 539 / 81 (같은 grep으로 재계산; step 163 본문 540) | **567 / 86** | +28 / +5 |
| look_compare viewport (ΔE00 < 5), scale 1.0 | 11/12 | 11/12 | 0 (face fill ΔE 40.5, 다섯 번째 연속) |
| look_compare kit-drawn pixels / theme > 5 | 6/6 · 20 of 31 | 6/6 · 20 of 31 | 0 |
| look_compare rects / density / scene / grid / furniture / checks, 1.0 | 5/12 · 5/6 · 3/3 · ok · 2/3 · 9/9 | 동일 (pixels, rects, density, scene, viewport, furniture.md 바이트 단위로 같음) | 0 |
| look_compare at 1.25 | rects 5/12, viewport 11/12, density 5/6 (−10.4 px) | 동일 (md 6개 바이트 단위로 같음) | 0 |

읽기: steps 164–171의 폭은 **Modify (+20), Deform (+18), Visualize (+6), Select All by Type (+4)**에서 왔다. 나머지 메뉴는
한 leaf도 움직이지 않았다. step 164 (DAG), 165 (컴포넌트 CB, RMB node submenu), 167 (선반 overflow), 170 (2D 선택 modifier)는
계수기에 잡히지 않는다. look_compare 수치는 **아홉 가지 표 전부가 step 163과 바이트 단위로 같다** — steps 164–171 중 시각
기준선을 움직인 것이 없다 (step 165 컴포넌트 CB는 이미지 08에서만 보인다, §5c-3).

## 1. Menus per menu set

| Set | Leaves | Working 163 → now | Greyed + notice 163 → now | Greyed, no notice |
|---|---|---|---|---|
| Common | 449 | 266 → **291** (59 % → 65 %) | 183 → 158 | 0 |
| Modeling | 349 | 167 → **185** (48 % → 53 %) | 182 → 164 | 0 |
| Rigging | 190 | 112 → **130** (59 % → 68 %) | 78 → 60 | 0 |
| Animation | 180 | 88 → **113** (49 % → 63 %) | 92 → 67 | 0 |
| FX | 205 | 37 (18 %) | 168 | 0 |
| Rendering | 63 | 19 (30 %) | 44 | 0 |
| (always visible) Cache + Help | 50 | 31 (62 %) | 19 | 0 |

(Deform / Constrain은 Modeling·Rigging·Animation 세트에 중복 집계 — Deform +18이 세 세트에 다 들어간다.)

### 1a. Per top menu (Deform and Constrain listed once)

| Set | Menu | Leaves | % working 163 → now | Working (+ notice) | Greyed + notice | Option boxes |
|---|---|---|---|---|---|---|
| Common | File | 30 | 80 % | 15 + 9 | 6 | 12 |
| Common | Edit | 68 | 66 % → **68 %** | 45 + 1 | 22 | 19 |
| Common | Create | 70 | 57 % | 32 + 8 | 30 | 44 |
| Common | Select | 81 | 62 % → **67 %** | 54 + 0 | 27 | 3 |
| Common | Modify | 90 | 41 % → **63 %** | 47 + 10 | 33 | 31 |
| Common | Display | 36 | 64 % | 20 + 3 | 13 | 2 |
| Common | Windows | 74 | 64 % | 38 + 9 | 27 | 1 |
| Modeling | Mesh | 26 | 81 % | 21 + 0 | 5 | 20 |
| Modeling | Edit Mesh | 28 | 89 % | 25 + 0 | 3 | 18 |
| Modeling | Mesh Tools | 36 | 81 % | 20 + 9 | 7 | 35 |
| Modeling | Mesh Display | 39 | 38 % | 15 + 0 | 24 | 10 |
| Modeling | Curves | 36 | 58 % | 19 + 2 | 15 | 24 |
| Modeling | Surfaces | 41 | 20 % | 4 + 4 | 33 | 37 |
| Modeling | Deform | 74 | 41 % → **65 %** | 31 + 17 | 26 | 47 |
| Modeling | UV | 19 | 84 % | 16 + 0 | 3 | 11 |
| Modeling | Generate | 50 | 4 % | 2 + 0 | 48 | 8 |
| Rigging | Skeleton | 54 | 94 % | 48 + 3 | 3 | 8 |
| Rigging | Skin | 28 | 68 % | 19 + 0 | 9 | 13 |
| Rigging | Constrain | 20 | 55 % | 8 + 3 | 9 | 17 |
| Rigging | Control | 14 | 7 % | 0 + 1 | 13 | 3 |
| Animation | Key | 41 | 51 % → **54 %** | 21 + 1 | 19 | 12 |
| Animation | Playback | 26 | 73 % | 18 + 1 | 7 | 1 |
| Animation | Audio | 9 | 56 % | 4 + 1 | 4 | 0 |
| Animation | Visualize | 10 | 20 % → **80 %** | 8 + 0 | 2 | 4 |
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

경로 diff (2cd3406 → c8d006c), **+50 working, 잃은 것 없음**:

- Modify (+20, step 168): `Align Tool`, `Convert/Geometry to Bounding Box`, `Evaluate Nodes/*` 11 (Constraints, Expressions, Fluids,
  IK Solvers, Ignore All, Particles, Rigid Bodies, Snapshots, nCloths, nParticles, nRigids), `Snap Align Objects/Position Along Curve`,
  `Transformation Tools/Default Object Manipulator/*` 5, `Show Manipulator Tool`.
- Deform (+18, step 169): `Wire` + `Wire#2/*` 6, `Paint Weights/Wire`, `Point On Curve`, `Prune Membership/Cluster`, `Lattice`, `Wire`,
  `ShrinkWrap#2/*` 4, `Lattice#2/Reset Lattice`, `Remove Lattice Tweaks`.
- Visualize (+6, step 171): `Create Animation Snapshot`, `Update Snapshot`, `Ghost Selected`, `Unghost Selected`, `Unghost All`,
  `Open Ghosting Editor`.
- Select (+4) / Edit (+1, step 166): `All by Type/Clusters`, `IK Handles`, `Particles`, `Rigid Bodies`; `Delete All by Type/IK Handles`.
- Key (+1): `Create Character Set` (Keying Set으로 가는 notice 항목 — 박스는 generic, §2).

움직이지 않은 메뉴: **step 98 이후 다섯 번째 감사 연속**: Control 7 %, nConstraint 0 %, nCache 15 %, Fields/Solvers 37 %, Effects 18 %,
Texturing 12 %. step 133 이후 네 번 연속: Surfaces 20 %, Mesh Display 38 %, Windows 64 %. step 145 이후 세 번 연속: Display, Generate,
모든 FX 메뉴, Lighting/Shading, Toon, Stereo, Cache. step 154 이후 두 번 연속: Mesh, Edit Mesh, Mesh Tools, UV, Skin, Constrain, Playback,
Audio, Render, File, Create (step 156 이후), Curves (step 156 이후).

### 1b. Weakest menus by Maya-user impact (daily use × greyed share), 현재

| Menu | % working | 아직 greyed인, Maya 사용자가 매일·매주 누르는 항목 |
|---|---|---|
| **Mesh Display** | 38 % (네 번째 연속) | `Set Vertex Normal`, `Apply Color`, 컬러 세트 `Rename Current Set...` / `Modify Current Set` / `Assign New Set` / `Assign Existing Set` / `Edit Assigned Set`, `Set Keyframe for Vertex Color`, `Color Material Channel/*` 6, `Material Blend Setting/*` 7 |
| **Lighting/Shading** | 36 % | `Make / Break Light Links`, `Make / Break Shadow Links`, `Select Lights Illuminating Object`, `Select Objects Illuminated by Light` (+ shadow 2) — **Blender 4.5에 light linking이 있다** (`Object.light_linking`, 확인: `-b --factory-startup` python-expr), notice만 있고 kit 코드에 `light_linking` 사용 0 |
| **Key / Control** | 54 % / 7 % | Character Set 계열 Key 9 + Control 10 (`Add to / Remove from / Merge / Select Members / Set Current`), `Scene Time Warp/*` 4 (+ Graph / Dope Sheet Edit 4씩 = 12 leaf), `IK/FK Keys/*` 4, `Set Blend Shape Target Weight Keys` |
| **Create** | 57 % | `Polygon Primitives/Pipe`, `Helix`, `Gear`, `Soccer Ball`, `Super Ellipse`, `Spherical Harmonics`, `Ultra Shape`, `Interactive Creation`, `Exit On Completion` (notice: "Extra Objects extension", `ui/notices.py:402`), `Construction Plane`, `Lights/Ambient` / `Volume` |
| **Skin** | 68 % | `Move Weights to Influences`, `Normalize Weights/Enable Weight Post Normalization`, `Bake Deformation to Skin Weights`, `Move Skinned Joints`, `Substitute Geometry`, `Interactive Bind Skin` (+ Tool), Weight Maps 2 |
| **Constrain** | 55 % | `Normal`, `Tangent`, `UV Pin`, `Proximity Pin`, `Remove Target`, `Set Rest Position`, `Modify Constrained Axis...`, `Motion Paths/Flow Path Object`, `Set Motion Path Key` |
| **Curves** | 58 % | `Lock / Unlock Length`, `Bend`, `Curl`, `Scale Curvature`, `Duplicate Surface Curves`, `Align`, `Edit Curve Tool`, `Intersect`, `Fit B-spline`, `CV Hardness`, `Project Tangent`, `Extend / Offset Curve On Surface` |
| **Surfaces** | 20 % | 33 greyed; 옵션 박스 37 중 29 dead, 5 generic (`Loft`, `Extrude`, `Planar`, `Bevel Plus`, `Reverse Direction`) |
| **Deform** | 65 % | `Tension`, `Solidify`, `Morph`, `Wrinkle`, `Jiggle` 3, `Sculpt`, `Pose Space Deformation/Create Pose Interpolator`, `Blend Shape#2/Swap`, `Edit Membership Tool`, `Display / Hide Intermediate Objects`, `Wire#2/Add Holder` |
| **Modify** | 63 % | `Transformation Tools/Type Manipulator`, `Paint Attributes Tool`, `Paint Scripts Tool`, `Evaluate Nodes/nucleuses / Dynamic Constraints / Global Stitch`, Asset 15, Convert 12 (subdiv / Paint Effects / displacement / fluid / nParticle) |
| Generate / nHair / nConstraint / Toon | 0–5 % | Blender 대응 없는 시스템 전체 (Paint Effects, XGen, Nucleus hair / constraints, Toon) — notice만 |

Modify (41 → 63 %)와 Visualize (20 → 80 %)는 이 표 상단에서 내려왔다.

### 1c. Editor menu bars

| Editor | Leaves | Working 163 → now | Greyed + notice | Most-greyed menus now |
|---|---|---|---|---|
| Graph Editor | 229 | 154 (67 %) | 75 | View 20 / 40, Show 18 / 34, Curves 16 / 39, Edit 10 / 23, List 6 / 8 |
| Dope Sheet | 181 | 124 → **130 (72 %)** | 51 | Show 18 / 34, Curves 12 / 34, Edit 10 / 23, List 6 / 7 |
| UV Editor | 172 | 110 → **118 (69 %)** | 54 | View 10 / 20, Select 9 / 39, Modify 9 / 31, Image 8 / 14, UV Sets 7 / 11, Tools 4 / 19 |
| UV Toolkit | 3 | 1 | 2 | Maya UV Toolkit 패널 = menu leaf 3개 |
| Hypershade | 249 | 114 → 115 (46 %) | 134 | Create 91 / 160, Edit 20 / 30, Tabs 6 / 6, Options 6 / 6 |
| Render Settings | 21 | 10 | 11 | Presets 9 / 10 |
| Script Editor | 59 | 32 | 27 | **History 13 / 13** (다섯 번째 감사 연속 0 %) |

새로 working (+15): Dope Sheet `Curves/Euler Filter`, `Isolate Curve`, `Resample Curve`, `Smooth Filter (Butterworth / Gaussian)`,
`View/Auto Frame` (step 166 twins — step 163 #10 해결); UV Editor `Tools/Cut`, `Sew`, `Pin`, `Unfold`, `Select/Convert Selection/To Contained
Edges / To Contained Faces / To Edge Loop / To Edge Ring`; Hypershade `Edit/Select All by Type/Lights`.

UV Editor에 남은 매일 쓰는 것: `Modify/Map Border`, `Straighten Border`, `Match Grid`, `Symmetrize`, `Layout Along`, `Stack Similar Shells`,
`Distribute UVs`, `Cut/Sew/Auto Seams` (+ 마킹 메뉴 2개), `Split`, `Select/Back-Facing`, `Front-Facing`, `Unmapped Faces`, `Texture Borders`,
`Convert Selection/To Connected Faces`, `Edit/Unpin All`, `Tools/Symmetrize`, `Smudge`, `Lattice`, `View/Isolate Select/Add / Remove /
Remove All / Load Set`, `UV Sets/Rename Current UV Set...`, `Copy UVs to UV Set`.

Graph Editor 그대로: `View/Show Buffer Curves` + `Curves/Buffer Curve/Reference` / `Swap Buffer Curve`, `Weighted / Non-weighted Tangents` 4,
`Lock / Free Tangent Length`, `Edit/Retime Tool`, `Region Keys Tool`, `Lattice Deform Keys Tool`, `Keys/Add Key Tool`, `List/Load / Add Selected
Objects`, `Show/Attributes/*` 6.

정직성 메모: web page 52, Blender Preferences 5 (`Graph Editor/Edit/Preferences`, `Dope Sheet/Edit/Preferences`, `Graph Editor/View/Keys/
Always`, `Active Only`, `View/Theme/Color Preferences`) — step 163과 같다.

## 2. Option boxes per top menu (507 paths)

window = kit Maya option window, dialog = operator / file dialog, tool = tool + Tool Settings, redo = run + Adjust Last Operation,
generic = "Blender has no settings for this" 창, dead = greyed 항목의 박스. 바뀐 칸만 [step 163 값].

| Menu | window | dialog | tool | redo | generic | dead |
|---|---|---|---|---|---|---|
| File | 2 | 6 | – | 1 | 1 | 2 |
| Edit | 13 | – | – | 2 | 0 | 4 |
| Create | 8 | 1 | – | 18 | 3 | 14 |
| Select | – | – | – | 2 | – | 1 |
| Modify | **3** [2] | – | 4 | 7 | 1 | **16** [17] |
| Display | 2 | – | – | 0 | 0 | 1 |
| Mesh | 2 | 1 | 1 | 11 | – | 4 (+1 menu) |
| Edit Mesh | 6 | – | 1 | 9 | – | 2 |
| Mesh Tools | 4 | 3 | 4 | 17 | – | 7 |
| Mesh Display | – | 1 | – | 5 | 1 | 3 |
| Curves | 3 | – | – | 4 | 6 | 11 |
| Surfaces | – | – | – | 3 | 5 | 29 |
| Deform | **33** [16] | – | – | 2 | **0** [9] | **12** [20] |
| UV | 3 | – | – | 3 | 3 | 2 |
| Generate | – | – | – | – | – | 8 |
| Skeleton | 3 | – | – | 3 | 2 | – |
| Skin | 4 | – | – | 3 | 1 | 5 |
| Constrain | 6 | – | – | 4 | – | 7 |
| Control | – | – | – | – | 1 | 2 |
| Key | 9 | – | – | – | **1** [0] | **2** [3] |
| Playback / Windows | – | 1 / 1 | – | – | – | – |
| Visualize | **1** [0] | – | – | 1 | – | **2** [3] |
| nParticles / Fluids / nCloth / nHair / nConstraint / nCache | – | – | – | 2 / 3 / – / 2 / – / 3 | 5 / 1 / 2 / – / – / – | 8 / 16 / 1 / 11 / 11 / 9 |
| Fields/Solvers / Effects | – | – | – | 13 / 2 | – | 6 / 6 |
| Render / Texturing / Toon | 2 / – / – | – | – | – | 2 / 1 / – | 2 / 1 / 1 |
| Cache | – | 8 | – | – | – | 7 |
| Help | – | – | – | – | – | 1 |

경로 diff (20개): generic → window 9 (`Deform/Paint Weights/Blend Shape`, `Cluster`, `Delta Mush`, `Lattice`, `Nonlinear`,
`Proximity Wrap`, `Set Membership`, `ShrinkWrap`, `Texture Deformer`); dead → window 10 (`Deform/Paint Weights/Wire`, `Point On Curve`,
`Wire`, `Wire#2/Add`, `Parent Base Wire`, `Remove`, `Reset`, `Wire Dropoff Locator`, `Modify/Convert/Geometry to Bounding Box`,
`Visualize/Create Animation Snapshot`); **dead → generic 1** (`Key/Create Character Set` — Maya에는 Name / Attributes / Hierarchy 옵션 창).

generic 36개 중 Maya 사용자가 매일 쓰는 박스 (step 163에서 그대로): `Curves/Cut`, `Detach`, `Smooth` ×2, `Reverse Direction`, `Straighten`,
`Create/Curve Tools/Three / Two Point Circular Arc`, `Pencil Curve Tool`, `UV/Merge UVs`, `Contour Stretch`, `3D Cut and Sew UV Tool`,
`Skeleton/Set / Assume Preferred Angle`, `Skin/Edit Influences/Add Influence`. 매주: `Surfaces/Loft / Extrude / Planar / Bevel Plus /
Reverse Direction`, `nCloth/Create nCloth / Create Passive Collider`, `nParticles/Create Emitter` ×2 / `Emit from Object` ×2 / `Make Collide`,
`Fluids/Make Collide`, `Modify/Bake Pivot`, `Mesh Display/Paint Vertex Color Tool`, `Texturing/3D Paint Tool`, `File/Archive Scene`,
`Control / Key/Create Character Set`. `Render/Render Current Frame` / `IPR`는 Maya와 같은 경고 문구지만 분류기는 generic으로 센다.

dead 214개를 메뉴별로 많은 순: Surfaces 29, Fluids 16, Modify 16, Create 14, Deform 12, Curves 11, nHair 11, nConstraint 11, nCache 9,
Generate 8, nParticles 8, Cache 7, Constrain 7, Mesh Tools 7, Fields/Solvers 6, Effects 6, Skin 5.

박스를 여는 방법: 여전히 plain click = 명령 실행, 창은 0.2 s 누르고 있기 (`ui/menu_sets.py:664-680` hold menu, 행 261
`operator_menu_hold`). ❒ 부분을 클릭하는 Maya 습관으로는 창이 열리지 않는다 (#82). 선반은 step 167에서 더블클릭 = 옵션 박스가 되어 Maya와
같아졌지만, 메뉴는 다섯 번째 감사 연속 같은 상태. GUI로 다시 재지는 않고 코드 경로만 확인.

## 3. Shelves (`ui/shelf.all_buttons`)

203 buttons, **155 working (76 %)**, 48 greyed with a notice, 0 without — step 163과 같음 (탭별 표 동일: Curves / Surfaces 26 / 38,
Poly Modeling 41 / 43, Sculpting 19 / 26, Rigging 17 / 18, Animation 14 / 14, Rendering 21 / 25, FX 13 / 29, FX Caching 4 / 10).
남은 greyed: Curves / Surfaces 12 (Curve Editing Tool, Birail 1, Project Curve on Surface, Intersect / Trim / Untrim / Attach / Detach /
Extend / Rebuild Surfaces, Sculpt Geometry Tool, Surface Editing Tool), FX 16 (2D Fluid Container with Emitter, Make Selected Curves
Dynamic, nHair 14), FX Caching 6, Sculpting 7, Rendering 4, Poly Modeling 2 (Super Shape, 3D Grab UV Tool), Rigging 1 (Human IK).
step 167 (overflow / 더블클릭)은 이 수를 바꾸지 않는다.

## 4. Hotkeys / marking menus

Hotkeys (`docs/keymap_mapping.md`, 468 rows): 구현 209, IC 일치 27, 해당 없음 164, 미검토 0, macOS 전용 68 — step 163과 같음
(`gen_keymap_mapping.py` 재생성 결과 파일 변화 없음). 164 n/a의 큰 덩어리: Hypershade / Node Editor 57행, Time Editor 32행.
메뉴 hotkey 글자: 메인 57, 에디터 메뉴바 0 (UV Editor `View/Toggle Shell Borders` 옆 8 등, step 155 키가 메뉴에 안 보임).

Marking menus: 474 entries, 368 working (298 direct + 70 `item`), 65 greyed (55 + 빈 submenu 10), 41 submenus — 변화 0.
greyed 55 분포: Shift+Q `doSelectComponentMM` 25 (비메시 마스크), `translateMarkingMenuImpl` 4, `buildSelectAllMM` 4,
`dagMenuProc_curve` 3, `contextPolyToolsDefaultMM` 3, rotate 2, hotbox east / west 2 + 2, 나머지 1씩 (UV 두 메뉴의 `Auto Seams` 포함,
`dagMenuProc` 1 = radial `Vertex Face`).

## 5. look_compare

### 5a. 실효 UI 배율 1.0 (`compare_audit173_s100/`, 15 side-by-side, 6 crops)

- checks 9/9; pixels kit-drawn **6/6** (theme 31, 20 > 5 not counted, 1 no kit element, 0 anchors missing); viewport **11/12**;
  rects **5/12**; scene 3/3; density 5/6 (menu bar 26.0/27, item pitch 20.1/20, CB row 16.1/16, **menu top − bar bottom −6.0/0**,
  shelf 64/64, icon 32/32); grid ok (ΔE00 0.7, corners 4/4, 0.196 ms); furniture 2/3.
- step 163 대비: pixels / rects / density / scene / viewport / furniture.md **바이트 단위로 같음**; grid draw 0.194 → 0.196 ms만 다름.
- viewport ✗ 1개: selected face fill — kit raw mean #ad8e6e (거의 불투명 주황) vs Maya stipple #e3ac79 25 % (mean #918477), ΔE 40.5.
- theme ✗ 20개 (값 그대로): 메뉴바 #181818 vs #444444 (14.0), 팝업 #181818 vs #525252 (18.7), 에디터 틈 #161616 vs #5c5c5c (22.8),
  Outliner 선택 행 #334d80 vs #5285a6 (21.0), frame 칸 #545454 vs #2b2b2b (13.5), Help Line #181818 vs #444444 (14.0), Tool Box 활성 도구
  #4772b3 vs #5285a6 (9.1), Layer 탭 #262626 vs #444444 (9.7), 결과 칸 #1b1b1b vs #2b2b2b (5.0), 나머지 #303030 / #333333 vs #444444 (5.6–6.5).
  step 130 (테마 미배포, 결정)이라 kit가 고칠 수 없는 차이.
- rects ✗ 7개 (1.0): Tool Box / Outliner / viewport / dock가 Maya보다 37 px 높고 10 px 위에서 시작 (Outliner −27 px, Maya 제목 줄),
  dock 287 vs 260 폭, Time Slider 1300 vs 1596 폭 (Δy +24, 오른쪽에 현재 프레임 + 재생 버튼이 별도 area), Range Slider 높이 26 vs 31.

### 5b. 실효 UI 배율 1.25 (`compare_audit173_s125/`)

- checks 9/9, kit-drawn 6/6, viewport 11/12, rects 5/12, scene 3/3, density 5/6 (**menu top − bar bottom −10.4 px**), grid ok
  (0.194 ms), furniture 2/3 — step 163의 `compare/` md 6개와 바이트 단위로 같다.
- rects ✗: Shelf 높이 80 vs 64, Tool Box 폭 70 vs 40, Outliner 폭 325 vs 260, **메인 뷰포트 폭 850 vs 1003 (−153 px)**, dock 346 vs 260 (+86),
  Time Slider 폭 1225 vs 1596 (−371 px). Maya 125 % 기준 이미지가 없어 과대평가 여부는 모름 (§7).

### 5c. 이미지에서 보이는 차이 (왼쪽 Maya, 오른쪽 kit; 차이만, 직접 봄)

1. **컴포넌트 모드에서 도구가 Select로 바뀜** (`07_faces_selected`, `08_verts_selected`, `09`): 샷 스크립트는 오브젝트 모드에서 Move 도구를
   켠 뒤 (`tools/look_shots.py:491`) 편집 모드로 들어간다. Maya는 Move manipulator가 선택 컴포넌트에 남는다 (Help Line "Move Tool: ...").
   kit는 **Select Tool** (Help Line "Select Tool: click or drag to select...", manipulator 없음). 원인: Blender 도구는 모드별이고
   `allset.component_mode` (`src/allset/operators/display.py:254-262`, F9 / F10 / F11 / F7)는 `mode_set` + select mode만 바꾼다 —
   오브젝트 모드의 Q/W/E/R 도구를 편집 모드로 옮기는 코드가 없다 (`tool_keys.py`는 Y용 LAST만 기억). 이번 감사에서 새로 찾은 조작 차이.
2. **선택 면 채우기** (`07`): kit 면이 거의 불투명 주황 (ΔE 40.5). kit stipple은 그려진다 (`ui/component_colors.py:197-240`) — 그 아래에
   Blender의 편집 모드 면 강조가 함께 그려지는 것으로 보인다: 3D View overlay `show_faces` (4.5에 있음, 확인)를 kit / 템플릿 어디서도 끄지 않는다
   (`grep show_faces src tools/make_startup.py` = UV 에디터만).
3. **컴포넌트 CB** (`08`): step 165 이후 kit = `pCubeShape1` / `CVs (click to show)` / INPUTS polyCube1 — Maya 측정 (`research/maya/re/
   cb_component_164.md` §1)과 맞다. `07`의 Maya 샷이 Translate… 행을 보여 주는 것은 Maya CB가 idle 콜백으로 늦게 갱신되는 grab (같은 문서
   서두) 때문 — **반증: 이미지 07의 CB 차이는 kit 문제가 아니다**.
4. **RMB 리스트 위치** (`14`): Maya는 링 바로 아래 한 열로 창 아래까지 내려가 잘린다. kit는 링 왼쪽 옆 (위로 링 위까지 올라감) —
   `marking/engine.py:424-432` (step 161: 아래에 안 들어가면 옆). 회색: kit `Metadata`, `Time Editor`, radial `Vertex Face`; Maya는 활성.
   `DG Traversal` / `Inputs` / `Outputs`는 step 165 이후 kit도 활성 (step 163 지적 중 일부 해결). kit 링 가운데 원형 커서는 Maya에 없음.
5. **Four view** (`16`): kit 네 칸 위에 panel menu + toolbar 한 벌 (Maya: 칸마다); kit 직교 칸 큐브 ≈ Maya의 약 2배 (화면 37 vs 20 px 정도);
   ViewCube가 kit front 칸 / Maya top 칸 ("TOP"); 라벨 `top -Z` / `front +Y` vs `top -Y` / `front -Z` (Y-up 결정); 샷 장면 차이 (Maya 선택 없음).
6. **Create 메뉴** (`12`): 메뉴가 메뉴바와 6 px (1.25: 10.4 px) 겹침; 첫 줄 tear-off 점선 (Maya "Objects" 섹션 라벨); 밑줄 니모닉;
   Maya 2022 샷에 없는 `Subdiv Primitives`; `Adobe(R) Illustrator(R) Object...`, `Construction Plane`, `Scene Assembly` 회색.
7. **Outliner** (`crop_outliner`): 순서 pCube1–3 → persp/top/front/side (Maya: 카메라가 먼저), 주황 삼각 메시 아이콘 (Maya: 회색 transform
   마름모, step 131: C Outliner 아이콘은 못 바꿈), 선택 행 주황 글자 + #334d80 (Maya 흰 글자 + #5285a6), 줄무늬, 스크롤바 없음, 검색 칸 작음.
8. **Time Slider** (`crop_time_slider`): kit 눈금 숫자가 크고 5 프레임마다, 프레임마다의 짧은 틱 없음; 현재 프레임 = 파란 말풍선
   (Maya: 회색 박스 + 세로선); 120 이후 붉은 영역; 현재 프레임 칸 + 재생 버튼이 오른쪽 별도 area.
9. **Hotbox** (`13`): kit 행이 Maya보다 약 20 px 아래 시작, 버튼 바탕이 거의 안 보임 (Maya: 회색 상자 뚜렷), 가운데 "Maya Workflow Kit".
10. **Status Line / 아래 줄**: undo / redo 회색; Command Line 언어 라벨 `Python` (Maya `MEL`); 상단 바 오른쪽 Maya / Blender 스위치;
    Workspace 값 "Maya Classic" (Maya 샷 "General*").
11. **Move manipulator** (`02`): Maya의 평면 사각형이 축 사이에 뚜렷, kit는 작은 사각형만 (step 163과 같음).

## 6. Domain 차이 (시나리오별, 증거)

| Domain | Maya가 아니라고 느껴지는 곳 (큰 것부터) | 증거 |
|---|---|---|
| Modeling | W → F9에서 Select 도구 (§5c-1); 선택 면 채우기; 옵션 박스 click; Mesh Display 38 % (vertex normal / color set); Pipe / Helix / Gear 등 7 primitive; Surfaces 20 % | `operators/display.py:254`, viewport.md, `ui/notices.py:402`, §1a |
| UV | UV Editor 69 %: Map Border / Straighten Border / Match Grid / Symmetrize / Layout Along / Stack Similar, Back / Front-facing / Unmapped 선택, Isolate Add / Remove; `UV/Auto Seams` + 마킹 2; `3D Grab UV Tool` | §1c, marking_grey.txt |
| Animation | Character Set 19 leaf (Keying Set notice), Scene Time Warp 12 leaf, Graph Editor View 20 / Show 18 greyed (buffer curves, weighted tangents), Time Slider 눈금 / playhead 모양, Playback Looping Once / Oscillate | §1a, §1c, crop_time_slider |
| Rigging | Constrain 55 % (Normal / Tangent / UV Pin / Proximity Pin / Remove Target), Skin 68 % (Move Weights to Influences, Post Normalization), Control 7 % | §1b |
| FX | 18 %, **다섯 번째 연속 불변**: nParticles Create Options 5 / Goal / Instancer, Fields/Solvers Initial State 8, nConstraint 0 %, nHair 4 % (shelf FX 13 / 29) | §1a, §3; 마지막 FX research = `research/maya/re/fields_141.md` |
| Rendering | Light Linking 6 + 2 select (Blender에 기능 있음), Texturing 12 %, Hypershade Create 91 greyed, Render Settings Presets 9 / 10, `Render Current Frame` 박스 generic | §1b, §1c |
| File I/O | 메뉴 80 %: `ATOM/*` 3, `Export / Assign Offline File` 2, After Effects Live Link; Cache 46 % (Geometry Cache 10); `Archive Scene` 박스 generic. FBX / OBJ / ABC / USD 왕복은 Maya-exact로 기록 (`research/maya/re/file_io.md`) — 이번 lane은 재실행 안 함 | §1a, §2 |
| 공통 UI | 테마 색 20개 (step 130 결정상 불가), Outliner 순서 / 아이콘 (C Outliner 한계), 메뉴 6 px 겹침, 에디터 메뉴 hotkey 글자 0, Script Editor History 0 / 13 | §5a, §4 |

## 7. Ranked remaining differences and one-step backlog

점수 = 심각도 (1–5, Maya 손에 거슬리는 정도) × 빈도 (1–5, 하루에 만나는 횟수). 각 항목은 한 step 분량.

| # | 차이 | S × F | 점수 |
|---|---|---|---|
| 1 | 컴포넌트 모드 진입 시 Move/Rotate/Scale 도구가 Select로 바뀜 | 4 × 5 | 20 |
| 2 | 옵션 박스 ❒ 클릭 = 명령 (창은 0.2 s hold, #82) | 4 × 4 | 16 |
| 3 | RMB 리스트가 링 옆 / 위로 (Maya: 아래로, 창 밖으로 잘림) | 3 × 5 | 15 |
| 4 | 선택 면이 불투명 주황 (stipple 아래 Blender 면 강조) | 3 × 4 | 12 |
| 5 | Time Slider 눈금 / 현재 프레임 표시 | 2 × 5 | 10 |
| 6 | UV Editor 남은 Modify / Select / Isolate 항목 | 3 × 3 | 9 |
| 7 | Light Linking 메뉴 greyed (Blender에 기능 있음) | 3 × 3 | 9 |
| 8 | Character Set 계열 19 leaf | 3 × 3 | 9 |
| 9 | Mesh Display 38 % (vertex normal, color set) | 3 × 3 | 9 |
| 10 | Polygon Primitives 7종 (Pipe, Helix, Gear ...) | 2 × 3 | 6 |
| 11 | Four view (칸별 header, 직교 배율, ViewCube) | 2 × 3 | 6 |
| 12 | FX 18 % 불변 (nParticles Create Options / Initial State) | 3 × 2 | 6 |

1. **도구가 컴포넌트 모드로 따라오게** — 지시: `allset.component_mode` / F8 `editmode_toggle` 경로 / 마킹 메뉴 Vertex·Edge·Face 항목이
   편집 모드에 들어가기 전에 `workspace.tools.from_space_view3d_mode('OBJECT')`의 idname을 읽어, Q/W/E/R/T (builtin.select*, move, rotate,
   scale, transform)이면 0 s 타이머 (`live_refs`로 window 재조회)에서 같은 도구를 `EDIT_MESH`에 `wm.tool_set_by_id` (도구는 자기 모드에서만
   설정 가능 — step 77 메모); 나갈 때도 반대로. 비-sacred 도구는 건드리지 않음. 검증: GUI 테스트 — W, F9 → `from_space_view3d_mode(
   'EDIT_MESH').idname == 'builtin.move'`, 뷰포트에 manipulator; `tests/gui/run.py -k <new>`; look_compare 07/08 Help Line "Move Tool".
2. **옵션 박스 ❒ 클릭 (#82)** — 지시: ❒ 마크가 그려지는 행 오른쪽 끝 폭을 정해 두고, 클릭 직전 hover 위치를 `allset.cb_hover`처럼 첫 자리
   MOUSEMOVE PASS_THROUGH 연산자로 기록 (`context.button_operator`가 그 메뉴 행이면 마우스 x 저장) → `allset.menu_item.execute`에서 그 x가 ❒ 폭
   안이면 옵션 창. 불가가 측정되면 그 측정을 `docs/steps/`에 남기고 hold 유지 + notice. 검증: GUI — ❒ 위 클릭 = 창, 라벨 클릭 = 명령.
3. **RMB 리스트 아래로** — 지시: `marking/engine.py:424-432`에서 링 아래에 행 1개 이상 들어가면 아래에 두고 창 아래로 넘치는 행은 Maya처럼
   잘리게 (또는 가장 아래 행부터 스크롤); 옆 배치는 아래 공간이 0일 때만. step 161 판단 보류 (manual_checks Step 161)를 사용자에게 확인 후.
   검증: `gui_step52_hotbox_rmb` "the list is under the ring" 2줄 통과, look_compare 14에서 리스트가 링 아래.
4. **선택 면 stipple만** — 지시: Maya 레이아웃 3D View (`tools/make_startup.py` + `ui/scene_carry.py` / `switch.enter_layout`)에서 overlay
   `show_faces = False` (space data, 사용자 prefs 아님), kit stipple (`ui/component_colors.py`)만 남김; 면 모드 외 영향 확인. 검증:
   look_compare viewport 12/12 (face fill ΔE < 5).
5. **Time Slider 모양** — 지시: Dope Sheet WINDOW POST_PIXEL (`ui/time_slider.py:590` `_draw_keys` 옆)에 프레임마다 짧은 틱 + 회색 현재
   프레임 박스 / 세로선을 그리고, 숫자는 Maya 간격으로 (Blender 숫자는 timeline header/scrubbing 영역 높이로 줄이거나 덮기 — 측정 필요).
   검증: `crop_time_slider` 나란히 비교, look_compare에 time-slider 샘플점 추가.
6. **UV Editor 나머지** — 지시: `Modify/Map Border`, `Straighten Border`, `Match Grid`, `Stack Similar Shells`, `Layout Along`, `Symmetrize`,
   `Select/Back-Facing` / `Front-Facing` / `Unmapped Faces` / `Texture Borders`, `View/Isolate Select/Add / Remove / Remove All`을
   `operators/uv_shells.py` 규칙 + mayapy 대조로. 검증: UV Editor ≥ 80 %, `menu_count.py`, headless 테스트.
7. **Light Linking** — 지시: `Make / Break Light Links`, `Make / Break Shadow Links` = 선택 light의 `Object.light_linking.receiver_collection`
   / `blocker_collection` (kit 컬렉션 `<light>_lightLinks`)에 선택 오브젝트 추가 / 제거, `Select Lights Illuminating Object` 등 4개는 그
   컬렉션 조회. Maya 기본 = 모두 조명 (컬렉션 없음)이라 Break는 처음에 장면 전체로 컬렉션을 만든 뒤 제외. 검증: Lighting/Shading ≥ 85 %,
   Cycles 렌더 픽셀 테스트 (링크 끊긴 큐브가 검게).
8. **Character Set** — 지시: Character Set = 이름 붙은 Keying Set (`scene.keying_sets`, `allset_character` 표시), Create (옵션 창: Name /
   Attributes All keyable / From Channel Box), Add / Remove / Merge / Select Members / Select Node / Set Current (Time Slider 행의
   "No Character Set" 칸과 연결), 키 명령이 현재 Character Set이면 그 채널 전부 키. 검증: Key ≥ 70 %, Control ≥ 50 %, generic 2 → 0.
9. **Mesh Display** — 지시: `Set Vertex Normal` (custom split normals, Maya 옵션 창 값), `Apply Color`, 컬러 세트 Rename / Modify / Assign New /
   Assign Existing / Edit Assigned, `Set Keyframe for Vertex Color`. 검증: Mesh Display ≥ 60 %, mayapy 대조 (normal 값 1e-4).
10. **Polygon Primitives 7종** — 지시: `operators/prim_history.py` 방식으로 Pipe / Helix / Gear / Soccer Ball / Super Ellipse 등을 bmesh로,
    Maya 기본값·면 순서 mayapy 측정 (`research/maya/re/primitives_129.md`에 추가), `create.KINDS` 경유. 검증: Create ≥ 70 %, 정점 위치 1e-4.
11. **Four view** — 지시: 직교 칸 배율을 Maya 샷과 맞추고 (큐브 화면 폭 ±10 %, `view.remember_ortho`), ViewCube를 top 칸에; 칸별 panel
    menu는 Blender Quad View 한계 — 측정 후 불가면 notice. 검증: look_compare에 four-view scene 행 추가.
12. **FX** — 지시: `nParticles/Create Options/*` 5 (kit 파티클 표시 preset: Point / Balls / Cloud / Thick Cloud / Water = display / render
    type + 크기), `Fields/Solvers/Initial State/Set Initial State / Clear` (cloth / particle point cache를 현재 프레임 상태에서 시작 —
    measure), `Instancer` (particle render as collection). 검증: FX ≥ 25 %, `fx.sim_scale` 테스트 확장.

뒤로 미룸 (점수 ≤ 5): 에디터 메뉴 hotkey 글자 (2 × 2), Script Editor History 13 (1 × 2), Hypershade Create 91 (2 × 2), Surfaces 20 % (3 × 1,
NURBS 표면 사용자 한정), 메뉴 6 px 겹침 (1 × 4), 테마 색 20개 / Outliner 아이콘·순서 (결정상 / C 한계로 불가 — 고치지 말 것).

## 8. Not measured / counterevidence

- Maya와 나란히 하는 실제 시나리오 실행 (파일 입출력, 모델링, UV, 애니, 리깅, FX, 렌더): 이 lane은 수치 재계산, look_compare, 코드 / notice
  읽기만. Maya 이미지는 기존 `research/maya/screens/*` 그대로 (새 Maya 캡처 없음); 파일 왕복 정확도는 `file_io.md` 기록을 믿었다.
- #1 (도구가 Select로)은 look_shots의 `mode_set` 경로와 코드 읽기로 판단; 실제 F9 키 GUI 실행으로 재지 않았다. 편집 모드가 이전 편집 세션의
  도구를 기억하므로 사용자가 편집 모드에서 W를 한 번 누른 뒤에는 차이가 줄어든다 (모드별 기억은 Maya에 없는 동작이지만 빈도는 낮아짐).
- #4 (면 채우기)의 원인이 overlay `show_faces`라는 것은 추정 — `show_faces`를 끈 GUI 샷으로 확인하지 않았다.
- 이미지 07의 Maya CB (Translate 행)는 Maya idle 갱신으로 늦은 grab — kit 차이 아님 (`cb_component_164.md`).
- 1.25 배율의 Maya 기준 없음 (Maya 샷은 Qt 논리 px). rect 차이는 과대평가일 수 있다.
- Create 메뉴의 `Sweep Mesh` / `USD` 줄: Maya 샷에 녹색 표시 (What's New 강조로 보임)가 있고 kit에는 ❒ 없음 (`OPTION_BOXES`에 없음) —
  Maya 2022에 그 옵션 박스가 있는지 확인 안 함.
- 서로 다른 옵션 창 109개는 프로브 기준; 창마다 필드가 Maya와 같은지는 보지 않았다.
- 수동 점검 개수는 작업 사본 기준 (lane A가 동시에 `docs/manual_checks.md`를 고칠 수 있음).
