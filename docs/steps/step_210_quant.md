# Step 210 부록 — 재점검 16차 수치 감사 (lane B, paper + look_compare)

Step 201 부록 (`docs/steps/step_201_quant.md`)의 수치를 오늘 master에서 같은 방법으로 다시 셌다. 칭찬은 빼고 차이만 적는다.
기준 (사용자): 「Maya 2022와 같은 시나리오를 나란히 따라 하며 시각(tools/look_compare.py 수치·비교 이미지)·조작·기능(메뉴 전수 대비, 파일 입출력,
모델링·UV·애니·리깅·FX·렌더) 모두에서 Maya가 아니라고 느껴지는 곳을 찾아 우선순위로.」
읽기 전용 감사, 2026-10-26, HEAD 4dd0b14 (steps 202–209). 확장 zip `dist/maya-workflow-kit-0.4.1.zip` (04:53 빌드) — 파일 260개를 `src/allset`과
바이트 비교해 차이 0, src에만 있는 파일 0 (`tmp/audit210b/zipcmp.py`) → HEAD와 같다. 재빌드 안 함. 스크립트와 원자료는 `tmp/audit210b/`.
step 201 기준선 = `git archive 0d75f44 src tools` → `tmp/audit210b/old/` + step 201 원자료 (`tmp/q201/results/option_kinds.json`,
`tmp/audit201b/probe201.json`, `tmp/audit201b/keymap_mapping.md`, `research/maya/screens/compare_audit201_s100/`, `_s125/`).

방법 (step 201과 같음, 경로만 `audit210b`로 바꿈; 판단은 모두 `delegated`):

- 메뉴: `python tools/menu_count.py` (→ `tmp/audit210b/menu_count.txt`), 메뉴별 표 `menus_per.py <root>` (0d75f44 / HEAD, 경로 단위 diff),
  에디터 메뉴바 `ed_diff.py <root>`, panel menu / toolbar / Status Line `panel_diff.py`, 마킹 `marking.py`, twins `python tools/menu_consistency.py`.
- 옵션 박스: `ALLSET_SANDBOX=option_count python tests/run.py --no-build -k step140_option_count` (1 passed) → `tmp/option_count/results/option_kinds.json`
  (사본 `tmp/audit210b/option_kinds_now.json`). `python tools/menu_count.py --options`는 `tests/run.py`를 `--no-build` 없이 불러 dist zip을 다시
  빌드하므로 (다른 lane이 같은 zip으로 headless suite를 도는 중) 같은 테스트를 `--no-build`로 직접 돌렸다 — 표는 같은 json에서 나온다.
- 선반 / 서로 다른 옵션 창 / 마킹 메뉴: `sh tmp/audit210b/run_probe.sh` + `probe_quant.py`, 샌드박스 `tmp/audit210b/sandbox` (폴더 먼저 생성,
  `--factory-startup`, `BLENDER_USER_*` 모두 tmp 안) → `tmp/audit210b/probe210.json` (4/4 ok).
- 단축키: `tools/gen_keymap_mapping.py` 사본 (`tmp/audit210b/gen_keymap_tmp.py`, exit 0) → `tmp/audit210b/keymap_mapping.md`.
- look_compare: `ALLSET_GUI_UI_SCALE=0.8 ALLSET_LOOK_TAG=audit210_s100 python tmp/audit210b/look_nobuild.py` (실효 1.0), `ALLSET_LOOK_TAG=audit210_s125`
  (실효 1.25) → `research/maya/screens/compare_audit210_s100/`, `_s125/`. GUI Blender는 한 번에 하나씩 (두 번 모두 exit 0). md는 step 201 폴더와 diff,
  이미지는 직접 봄.
- 수동 점검: `docs/manual_checks.md`의 `- [ ]` / `- [x]` 줄 수 (0d75f44: `git show`).

## 0. Headline (step 201 → now)

| Metric | Step 201 (0d75f44) | Now (4dd0b14) | Δ |
|---|---|---|---|
| Unique kit menu leaves (main menu sets) | 1318 | 1318 | 0 |
| ... working (mapped, incl. with notice) | 762 (57.8 %) | **803 (60.9 %)** = 706 + 97 with a notice | **+41** |
| ... greyed with a notice / without | 556 / 0 | 515 / 0 | −41 / 0 |
| Leaves counted per set | 1486, working 874 (58.8 %) | 1486, working **941 (63.3 %)** | +67 (Deform은 Modeling·Rigging·Animation 세 세트에 셈) |
| `menu_map.MAP` / `notices.NOTICES` / `CATEGORIES` | 1362 / 168 / 155 | 1479 / 151 / 152 | +117 / −17 / −3 |
| Editor menu bars (step 201의 7 editors, 914 leaves) | 600 (66 %) | **649 (71 %)** | **+49** (Graph Editor +20, Dope Sheet +19, UV Editor +10) |
| ... + Reference Editor (새 메뉴바, 38 leaves) | – | 27 / 38 (71 %) | 전체 952 leaves 중 676 (71 %) |
| Panel menus / panel toolbar / Status Line greys | 69 / 111, 22 / 29, 8 leaves | 같음 — 경로 diff 0 | 0 (세 번째 연속) |
| Option-box paths (`OPTION_BOXES`) | 507 | 507 | 0 |
| ... kit Maya option window | 164 paths (151 specs) | **176 paths (163 specs)** | **+12 / +12** |
| ... distinct real windows / dialogs | 166 | **179** | +13 |
| ... operator dialog / tool / redo | 23 / 10 / 104 | **25** / 10 / 104 | dialog +2 (File Offline 2), redo 0 |
| ... "Blender has no settings" (`option_generic`) | 19 | **28** | **+9 (나빠짐: dead → generic)** |
| ... dead (box on a greyed item) | 187 (37 %) | **164 (32 %)** | −23 |
| Shelves (8 tabs, 203 buttons) | 160 / 43 + notice / 0 | 160 / 43 / 0 | 0 (세 번째 연속) |
| Hotkeys (468 rows) 구현 / IC / 해당 없음 / 미검토 / macOS | 210 / 26 / 164 / 0 / 68 | 같음 (출력 diff 0, 체크인 문서와도 0) | 0 (다섯 번째 연속) |
| Marking menus (26 menus, 474 entries) | 371 working (301 + 70 `item`), 52 greyed | **373** (301 + **72**), **50** greyed | +2 (UV 마킹 2) |
| `menu_consistency` twins | 0 | 0 | 0 |
| Manual checks (unticked / ticked) | 619 / 107 | **646 / 107** | +27 / 0 |
| look_compare kit-drawn pixels, 1.0 | 12/12 | 12/12 | 0 |
| look_compare kit-drawn pixels, 1.25 | 11/12 (`time_slider_current` ΔE 13.8 ✗) | **12/12** (`time_slider_current` ΔE **0.3**) | **+1 (step 202 수정 확인)** |
| look_compare viewport / rects / scene / density / furniture, 1.0 | 20/20 · 5/12 · 3/3 · 5/6 · 2/3 | 같음 (rects / scene / furniture / viewport.md 바이트 동일) | 0 |
| look_compare at 1.25 rects / density | 5/12 · 5/6 (−10.4 px) | 5/12 · 5/6 (−10.4 px) — 칸 높이만 바뀜 (§5b) | 0 |

읽기: steps 202–209에서 계수기를 움직인 것은 **Curves 58 → 89 %** (step 207), **Deform 65 → 81 %**, **Constrain 80 → 90 %** (step 205 Tension / Solidify /
Sculpt / Morph / Jiggle / UV Pin / Proximity Pin), **Graph Editor / Dope Sheet 메뉴바 +39** (step 203), **UV +1 / UV Editor 메뉴바 +10** (step 206),
**nHair Modify Curves 5** (step 207의 Curves 명령 재사용), **Select / Edit All by Type 8** (step 202), **File Offline 2 + Reference Editor 메뉴바** (step 209).
step 204 (애니메이션 레이어)와 208 (maya.cmds)은 메뉴 계수기에 안 보인다 (Animation Layer Editor 메뉴는 메뉴바 캡처에 없음). 단축키, 선반, panel menu는
0 변화. 단계별 귀속은 커밋 제목과 경로 이름으로 추정 (delegated).

## 1. Menus per area (main menus, 메뉴 하나씩; coverage 오름차순)

working = mapped (notice 있는 것 포함). Deform / Constrain은 여러 세트에 나오지만 한 번만 적음. Bifrost / MASH / XGen은 Maya 2022 기본 메뉴 캡처에
메뉴로 없음 (플러그인) — 셈 밖.

| Area (menu) | Working / leaves | Now | Step 201 | Δ working |
|---|---|---|---|---|
| nConstraint | 0 / 19 | **0 %** | 0 % | 0 (step 98 이후 아홉 번째 연속) |
| Generate | 2 / 50 | **4 %** | 4 % | 0 |
| Toon | 1 / 20 | **5 %** | 5 % | 0 |
| Texturing | 1 / 8 | **12 %** | 12 % | 0 |
| nCache | 3 / 20 | **15 %** | 15 % | 0 |
| Fluids | 4 / 25 | 16 % | 16 % | 0 |
| nHair | 9 / 54 | 17 % | 7 % | +5 (Modify Curves 5) |
| Stereo | 1 / 6 | 17 % | 17 % | 0 |
| Effects | 2 / 11 | 18 % | 18 % | 0 |
| nParticles | 7 / 25 | 28 % | 28 % | 0 |
| Surfaces | 15 / 41 | 37 % | 37 % | 0 (step 182 이후 네 번째) |
| Fields/Solvers | 14 / 38 | 37 % | 37 % | 0 |
| nCloth | 5 / 13 | 38 % | 38 % | 0 |
| Cache | 11 / 24 | 46 % | 46 % | 0 |
| Audio | 5 / 9 | 56 % | 56 % | 0 |
| Modify | 57 / 90 | 63 % | 63 % | 0 |
| Display | 23 / 36 | 64 % | 64 % | 0 |
| Mesh Display | 25 / 39 | 64 % | 64 % | 0 |
| Control | 9 / 14 | 64 % | 64 % | 0 |
| Windows | 48 / 74 | 65 % | 65 % | 0 |
| Create | 47 / 70 | 67 % | 67 % | 0 |
| Select | 58 / 81 | 72 % | 67 % | +4 |
| Playback | 19 / 26 | 73 % | 73 % | 0 |
| Key | 30 / 41 | 73 % | 73 % | 0 |
| Render | 11 / 15 | 73 % | 73 % | 0 |
| Edit | 50 / 68 | 74 % | 68 % | +4 |
| Help | 20 / 26 | 77 % | 77 % | 0 |
| Visualize | 8 / 10 | 80 % | 80 % | 0 |
| Mesh Tools | 29 / 36 | 81 % | 81 % | 0 |
| Mesh | 21 / 26 | 81 % | 81 % | 0 |
| Deform | 60 / 74 | 81 % | 65 % | +12 |
| File | 26 / 30 | 87 % | 80 % | +2 |
| Curves | 32 / 36 | 89 % | 58 % | +11 |
| Edit Mesh | 25 / 28 | 89 % | 89 % | 0 |
| Skin | 25 / 28 | 89 % | 89 % | 0 |
| Constrain | 18 / 20 | 90 % | 80 % | +2 |
| Lighting/Shading | 13 / 14 | 93 % | 93 % | 0 |
| Skeleton | 51 / 54 | 94 % | 94 % | 0 |
| UV | 18 / 19 | 95 % | 89 % | +1 |

세트별: Common 299 → **309** (69 %), Modeling 203 → **227** (65 %), Rigging 149 → **163** (86 %), Animation 126 → **140** (78 %), **FX 39 → 44 (21 %)**,
Rendering 27 (43 %, 0), Cache + Help 31 (62 %, 0).

경로 diff (0d75f44 → 4dd0b14): **greyed → working 41, working+notice → working 1 (`File/Reference Editor`), 잃은 것 없음**:
Curves 11 (`Align`, `Bend`, `Curl`, `Scale Curvature`, `CV Hardness`, `Duplicate Surface Curves`, `Fit B-spline`, `Intersect`, `Lock / Unlock Length`,
`Bezier Curves/Tangent Options/Uneven Anchor Tangents`), Deform 12 (`Tension`, `Solidify`, `Sculpt`, `Morph`, `Jiggle/Jiggle Deformer`, Paint Weights Jiggle /
Tension, `Prune Membership/Sculpt`, `Display / Hide Intermediate Objects`, `Wrap#2/Add / Remove Influence`), Constrain 2 (`UV Pin`, `Proximity Pin`),
nHair 5, Select / Edit All by Type 8 (Wires, nCloths, nParticles, nRigids), File 2 (`Assign Offline File...`, `Export to Offline File...`), UV 1 (`Auto Seams`).

움직이지 않은 메뉴: **step 98 이후 아홉 번째**: nConstraint 0 %, nCache 15 %, Fields/Solvers 37 %, Effects 18 %, Texturing 12 %. step 133 이후 여덟 번: Windows 65 %.
step 145 이후 일곱 번: Display, Generate 4 %, Toon, Stereo, Cache, nParticles / Fluids / nCloth. step 154 이후 여섯 번: Mesh, Edit Mesh, Mesh Tools, Playback,
Audio, Render. step 163 이후 다섯 번: Modify 63 %, Visualize. step 182 이후 네 번: Surfaces 37 %, Lighting/Shading. step 192 이후 세 번: Create 67 %,
Mesh Display 64 %, Key 73 %, Control 64 %.

### 1a. Weakest menus by Maya-user impact (daily use × greyed share), 현재

| Menu | % working | 아직 greyed인, Maya 사용자가 매일·매주 누르는 항목 |
|---|---|---|
| **Select** | 72 % | NURBS 컴포넌트 선택 8 (`Components#2/Control Vertex`, `Edit Point`, `Curve Point`, `Hull`; `Components#3/Control Vertex`, `Hull`, `Isoparm`, `Surface Point`), `Components/Vertex Face`, `Convert Selection/To Vertex Faces`, `CV Selection Boundary`, `Surface Border`, `Use Constraints...` — Curves가 89 %가 됐는데 CV / EP를 메뉴로 고를 수 없음 |
| **Create** | 67 % (세 번째 불변) | `Polygon / NURBS Primitives/Interactive Creation` + `Exit On Completion` (4), `Lights/Ambient` / `Volume Light`, `Construction Plane`, Measure Tools 2, Subdiv 6 / Volume 3 |
| **Playback** | 73 % | `Playback Looping/Once` / `Oscillate`, `Cached Playback`, `Enable Stepped Preview` |
| **Display** | 64 % | `NURBS` (CV / Hull 표시 하위 메뉴), `Transform Display/Rotate / Scale Pivots`, `Selection Handles`, HUD `Animation Details` / `Bounding Box`, `Object Display/*` 5 |
| **Windows** | 65 % | `Settings/Preferences/Shelf Editor`, `Marking Menu Editor`, `General Editors/Namespace Editor` (step 209 reference는 `ns:` 이름을 쓰는데 Namespace Editor 없음), `Profiler`, `Animation Editors/Pose Editor` |
| **Key** | 73 % | `Scene Time Warp/*` 4, `IK/FK Keys/*` 4, `Set Blend Shape Target Weight Keys` |
| **Mesh Display** | 64 % | `Color Material Channel/*` 6, `Material Blend Setting/*` 7, `Share Instances` |
| **Control** | 64 % | `Tag As Controller`, `Parent Controller`, `Create Control Rig`, `Character Mapper`, `Redirect` |
| **Surfaces** | 37 % | 26 greyed (Trim / Untrim / Intersect / Project / Extend / Offset / Round / Stitch — 4.5 NURBS 한계) |
| **Deform** | 81 % | `Wrinkle`, `Muscle`, `Pose Space Deformation/Create Pose Interpolator`, `Proximity Wrap#2`, `Blend Shape#2/Swap` 외 2, `Edit Membership Tool`, `Wire#2/Add Holder`, `Add Tweak` |
| Curves | 89 % | `Edit Curve Tool`, `Project Tangent`, `Extend / Offset Curve On Surface` |
| Skin / Constrain | 89 / 90 % | `Interactive Bind Skin` (+ Tool), `Move Skinned Joints`; `Motion Paths/Flow Path Object`, `Set Motion Path Key` |
| Generate / nHair / nConstraint / Toon / FX 전체 | 0–21 % | Blender 대응 없는 시스템 — notice만 |

### 1b. Editor menu bars

952 leaves (Reference Editor 38 포함), working **676 (71 %)**; step 201 범위 914 leaves만 보면 600 → **649**. 경로 diff 49개, 모두 G → W:

- Graph Editor (20): `Curves/Change Rotation Interp/*` 5, `Key Sync Filter`, `Peak Removal Filter`, `Pin / Unpin Channel`, `Edit/Select Curve Nodes`,
  `List/Add / Load Selected Objects`, `Show Upstream Curves`, `Show/Attributes/*` 5 (Driven by Anim Curve / Driven Key / Expression, Hidden, User Defined),
  `Show/Objects/IkHandles`, `Sets`.
- Dope Sheet (19): 같은 이름들 + `List/Hierarchy Below`, **`Show/Objects/Characters` (step 201 §1b 남은 모순 해소)**.
- UV Editor (10): `Cut/Sew/Auto Seams`, `Create Shell (Grid)`, `Split`, `Modify/Cycle`, `UV Sets` 3, `View/Heads-Up Display/*` 3.

남은 greyed: Graph Editor View **19 / 40 (그대로)**, Show 10, List 3, Edit 6; Dope Sheet Show 10, Edit 6, List 3; UV Editor 26 (Image 8 / 14, Tools 4, View 4,
UV Sets 4); Hypershade **134 / 249 (그대로, Create 91, Tabs 6 / 6, Options 6 / 6)**; Render Settings 11 / 21 (그대로); **Script Editor History 0 / 13 (아홉 번째
연속 0 %)**; Reference Editor 11 (`Proxy/*` 6 / 6, `View/View Selected / All References`, `File/Save Reference Edits`, `List Unknown Edits...`).

### 1c. Panel menus / panel toolbar / Status Line

경로 diff 0 (세 번째 연속). Panel menus 69 / 111 (greyed 42, **`Show/NURBS CVs`, `NURBS Hulls` 여전히 회색** — Curves 89 %인데 viewport에서 CV를 끄고 켤 수
없음), panel toolbar greyed 7, Status Line greys 8.

## 2. Option boxes (507 paths)

window = kit Maya option window, dialog = operator / file dialog, tool = tool + Tool Settings, redo = run + Adjust Last Operation, generic = "Blender has
no settings for this" 창, dead = greyed 항목의 박스.

| Kind | Step 201 | Now | Δ |
|---|---|---|---|
| window | 164 | **176** | +12 |
| dialog | 23 | 25 | +2 |
| tool | 10 | 10 | 0 |
| redo | 104 | 104 | 0 |
| generic | 19 | **28** | **+9** |
| dead | 187 | **164** | −23 |

바뀐 줄만 [step 201 값]:

| Menu | window | dialog | redo | generic | dead |
|---|---|---|---|---|---|
| Deform | **40** [33] | – | 2 | – | **5** [12] |
| Curves | **12** [9] | – | 4 | **5** [0] | **3** [11] |
| Constrain | **12** [10] | – | 4 | – | **1** [3] |
| File | 2 | **8** [6] | 1 | 1 | **0** [2] |
| UV | 5 | – | 3 | **2** [1] | **1** [2] |
| nHair | 2 | – | 2 | **3** [0] | **6** [9] |

경로 diff 23개: dead → window 12 (Deform 7, Curves `Bend` / `Curl` / `Scale Curvature`, Constrain `UV Pin` / `Proximity Pin`), dead → dialog 2 (File Offline 2),
**dead → generic 9**: `Curves/Align`, `CV Hardness`, `Duplicate Surface Curves`, `Fit B-spline`, `Intersect`, `UV/Auto Seams`, `nHair/Modify Curves/Bend`, `Curl`,
`Scale Curvature`. 이 아홉은 Maya에 옵션 창이 있다 (메뉴 이름 기준, delegated). **모순: `Curves/Bend` / `Curl` / `Scale Curvature` 박스 = window인데 같은 명령인
`nHair/Modify Curves/Bend` / `Curl` / `Scale Curvature` 박스 = generic** ("Blender has no settings") — menu_consistency는 greyed 항목만 보므로 못 잡는다.

남은 generic 28: 위 9 + step 201의 19 (`Create/Curve Tools/Pencil Curve Tool`, `UV/3D Cut and Sew UV Tool`, `Surfaces/Planar`, `Bevel Plus`, `Duplicate NURBS
Patch`, `Modify/Bake Pivot`, `Mesh Display/Paint Vertex Color Tool`, `Texturing/3D Paint Tool`, `File/Archive Scene`, nParticles 5, nCloth 2, `Fluids/Make
Collide`, `Render/Render Current Frame` / `IPR` (Maya와 같은 경고)). redo 104는 step 201 목록 그대로 (`Create/Lights/Point / Spot / Directional / Area Light`,
`Create/Free Image Plane`, `UV/Cylindrical / Spherical / Camera-based`, `Curves/Open/Close`, `Offset Curve`, `Extend Curve`, `Insert Knot`, `Skin/Smooth / Mirror
Skin Weights`, `Prune Small Weights`, `Constrain/Geometry`, `Point On Poly`, `Closest Point`, `Motion Paths/Attach to Motion Path`, Edit Mesh 9, Mesh 11).

dead 164를 메뉴별로 많은 순: Surfaces 22, Fluids 16, Modify 16, nConstraint 11, nCache 9, Generate 8, nParticles 8, Cache 7, Create 7, Mesh Tools 7, nHair 6,
Effects 6, Fields 6, Deform 5.

## 3. Consistency / twins

`python tools/menu_consistency.py` → "0 greyed item(s) with a working twin (main / editor / marking / panel menus)" (exit 0, step 201과 같음). twins 규칙
밖의 모순은 §2의 Bend / Curl / Scale Curvature 박스 3쌍 (working 항목끼리 박스 종류가 다름).

## 4. Shelves / hotkeys / marking menus

- Shelves: 203 buttons, **160 working (79 %)**, 43 greyed with a notice, 0 without — 세 번째 연속 같음. Curves / Surfaces 선반 greyed 8 (`Curve Editing Tool`,
  `Project Curve on Surface`, `Intersect Surfaces`, `Trim Tool`, `Untrim Surfaces`, `Extend Surfaces`, `Sculpt Geometry Tool`, `Surface Editing Tool`), FX 16,
  FX Caching 6, Sculpting 7, Rendering 4, Poly Modeling 1 (`3D Grab UV Tool`), Rigging 1 (`Human IK`). steps 205–207의 새 명령은 선반 계수기를 안 움직였다.
- Hotkeys (468 rows): 구현 210, IC 일치 26, 해당 없음 164, 미검토 0, macOS 68 — `tmp/audit210b/keymap_mapping.md`가 step 201 출력과 체크인 문서 모두와
  diff 0 (**다섯 번째 연속 변화 없음**). 메뉴 hotkey 글자: 메인 57, 에디터 메뉴바 0 (확인은 step 201 방법 그대로, `ui/menu_hotkeys.py` 생성 대상 변화 없음 — delegated).
- Marking menus: 474 entries, **373 working (301 direct + 72 `item`)**, 50 greyed + 51 submenus. greyed에서 빠진 것 2: `contextPolyToolsUVMM` /
  `contextPolyToolsUVShellMM`의 항목 하나씩 (step 206). 새로 greyed 0. NURBS surface용 RMB 메뉴 (Isoparm / Surface Point / Hull) 여전히 0.

## 5. look_compare

### 5a. 실효 UI 배율 1.0 (`research/maya/screens/compare_audit210_s100/`, 15 side-by-side, 6 crops)

- checks 9/9; pixels kit-drawn **12/12** (theme 25, 19 > 5 not counted, 2 no kit element, 0 anchors missing); viewport 20/20; rects 5/12; scene 3/3;
  density 5/6 (**menu top − bar bottom −6.0/0** 그대로); grid ok (ΔE00 0.7, corners 4/4, 0.201 ms); furniture 2/3.
- step 201 대비: rects / scene / furniture / viewport.md **바이트 동일**; density는 menu pitch 20.1 → 20.0만; pixels.md는 `time_slider_current` 표본 좌표만.
- theme ✗ (step 130 결정상 kit가 못 고침), ΔE 큰 순: `viewport_border` 22.8 (에디터 틈 #161616 vs Maya #5c5c5c), `outliner_row_selected` **21.0** (#334d80 vs
  #5285a6), `menu_popup_bg` 18.7 (#181818 vs #525252), `menu_bar_bg` / `help_line_bg` 14.0 (#181818 vs #444444), `time_field` / `range_slider_field` 13.5
  (#545454 vs #2b2b2b), `outliner_row_selected_component_mode` 11.1, `layer_tab_active` 9.7, `toolbox_active_tool` 9.1, `outliner_menu_bg` 9.1.
- kit-drawn 중 가장 먼 것: `dock_side_tab_strip` ΔE 4.3 (#444444 vs #373737), `marking_menu_list_bg` 3.5 (표본점이 리스트 밖 — §5c-1).
- rects ✗ 7개 그대로: Tool Box / Outliner / viewport / dock가 Maya보다 10 px 위에서 시작하고 37 px 높음, Tool Box 56 vs 40 폭, dock 287 vs 260, Time Slider
  1300 vs 1596 폭, Range Slider 높이 26 vs 31.

### 5b. 실효 UI 배율 1.25 (`compare_audit210_s125/`)

- checks 9/9, kit-drawn **12/12** (step 201 11/12), viewport 20/20, rects 5/12, scene 3/3, density 5/6 (−10.4 px), grid ok (0.203 ms), furniture 2/3.
- **`time_slider_current` #282828 ΔE 13.8 ✗ → #535353 ΔE 0.3** (step 202 `TIME_SLIDER_PX` 맞춤). 대가: Time Slider 영역 높이 29 → **45 px** (Maya 36), 그만큼
  Tool Box / Outliner / viewport / dock 높이 655 → 639 (−16 px); `time_slider_bg`도 #303030 1.6 → #2b2b2b 0.0. rects ✗ 개수는 같음 (Time Slider는 여전히 x / h ✗,
  이제 y도 ✗).

### 5c. 이미지에서 보이는 차이 (왼쪽 Maya, 오른쪽 kit; 차이만, 직접 봄)

step 201 §5c 대비 해결: **#2 일부** (1.25에서도 kit 회색 칸이 표본상 맞음). 남은 / 새로 본 차이:

1. **RMB 리스트 위치** (`compare_audit210_s100/14_marking_menu_object.png`) — Maya: 리스트가 링 **아래** (pCube1... 행이 Face 박스 바로 밑). kit: 리스트가 링
   **왼쪽** 한 열, 링보다 위 (pCube1... 행이 Edge 박스보다 위)에서 시작 — step 201과 같음. kit에서 `Vertex Face`, `Metadata`, `Time Editor`가 회색 (Maya는
   검은 글씨); kit 하위 메뉴 `▸`가 글자 바로 뒤 (Maya: 오른쪽 끝 정렬).
2. **Time Slider 현재 프레임** (`compare_audit210_s125/crop_time_slider.png`): Blender 파란 말풍선 "1"이 여전히 위에 있다 (회색 칸은 그 뒤). Maya = 회색 칸 +
   아래쪽 작은 숫자. kit 눈금 숫자가 Maya보다 큼; kit 룰러가 창 폭의 77 % (1225 / 1596)에서 끝나고 오른쪽은 재생 버튼 영역.
3. **Outliner** (`11_channel_box.png`, `14`): kit은 pCube1–3이 카메라 (persp / top / front / side)보다 먼저, 주황 삼각 메시 아이콘 (Maya: 흰 transform 아이콘),
   선택 행 #334d80 진한 파랑 (Maya #5285a6 밝은 파랑), 헤더에 "Outliner" 제목 대신 `::::` 손잡이 + Display / Show / Help.
4. **메뉴 / 바 회색**: 메인 메뉴바, Help Line, 팝업 메뉴 바탕이 거의 검정 #181818 (Maya #444444 / #525252) — `12_create_menu.png`에서 메뉴 전체가 Maya보다
   확연히 어둡다. Create 메뉴: 메뉴바와 6 px 겹침, 첫 줄 tear-off 점선 (Maya `Objects` 섹션 라벨), `Subdiv Primitives` 행 (Maya 2022 없음), `Sweep Mesh` / `USD`
   녹색 표시 없음.
5. **Channel Box** (`11_channel_box.png`): Layer Editor `Display` 탭이 파란 알약 (Maya 회색 탭, `layer_tab_active` ΔE 9.7), 맨 위 `::::` 손잡이, SHAPES 행
   둥근 입력 칸, 아래 가로 스크롤바 없음 — step 201 §5c-3 그대로.
6. **Status Line / Command Line**: Workspace 이름 "Maya Classic" (Maya 2022 샷 "General*"), Command Line 언어 버튼 "Python" (Maya 기본 "MEL"), Help Line 문장이
   Maya와 다름 ("Move Tool: drag the manipulator. Hold X/C/V ..." vs "Move Tool: Use manipulator to move object(s). Ctrl+middle-drag ...").
7. **Four view / Hotbox / 1.25 레이아웃**: step 201 §5c-8 / 9 / 10 그대로 (네 칸 위 panel 한 벌, hotbox 제목 "Maya Workflow Kit", 1.25에서 panel toolbar `>>`
   잘림, 뷰포트 좁고 dock 넓음).

## 6. Domain 차이 (시나리오별, 증거)

| Domain | Maya가 아니라고 느껴지는 곳 (큰 것부터) | 증거 |
|---|---|---|
| Modeling | NURBS CV / EP / Hull을 Select 메뉴·panel Show로 못 고르고 못 끔 (Curves 89 %와 어긋남); Interactive Creation 4; Mesh Display Color Material / Blend 13; Pencil Curve 박스 generic | §1a, §1c, §2 |
| Surfaces | 37 % 네 번째 불변; NURBS surface RMB 마킹 없음; Planar / Bevel Plus / Duplicate Patch 박스 generic; 선반 Trim / Untrim / Extend 회색 | §1, §2, §4 |
| Curves | Align / CV Hardness / Duplicate Surface Curves / Fit B-spline / Intersect 박스 = generic (새로), nHair 쪽 Bend / Curl / Scale Curvature 박스 generic (Curves 쪽은 창) | §2 |
| UV | Auto Seams / 3D Cut and Sew 박스 generic, Cylindrical / Spherical / Camera-based = redo; UV Editor Image 메뉴 8 / 14 회색; `3D Grab UV Tool` | §1b, §2, §4 |
| Animation | Time Slider 파란 말풍선 (1.25 칸 수치는 해결); Playback Looping Once / Oscillate 회색; Scene Time Warp 4; Graph Editor View 19 / 40 그대로 | §5c-2, §1a, §1b |
| Rigging | Control 64 % (controller tags, HumanIK, 세 번째 불변); `Interactive Bind Skin`; Smooth / Mirror Skin Weights 박스 = redo | §1a, §2 |
| FX | 21 % (39 → 44는 nHair Modify Curves 재사용뿐; nConstraint 0 % 아홉 번째) | §1 |
| Rendering | Texturing 12 %, Hypershade 메뉴바 134 greyed 그대로, 조명 4종 박스 = redo, 선반 Ambient / Volume Light 회색 | §1b, §2, §4 |
| 파일 / 레퍼런스 | Reference Editor `Proxy` 메뉴 6 / 6 회색, `Save Reference Edits`; Windows `Namespace Editor` 회색; File ATOM 3 | §1a, §1b |
| 공통 UI | 메뉴 / 팝업 / Help Line 거의 검정 (ΔE 14–19, 결정상 불가), Outliner 선택 파랑 ΔE 21 / 순서 / 아이콘, RMB 리스트 링 옆, Script Editor History 0 / 13, 에디터 메뉴 hotkey 글자 0 | §5, §1b |

## 7. 차이 우선순위 (수치 기준)

점수 = 심각도 (1–3) × 빈도 (1–3). step 201 #1 (1.25 Time Slider 칸)은 수치상 해결 (말풍선은 남음), #6 (Curves 58 %)과 #12 (Dope Sheet Characters)는 해결.

| # | 차이 | 수치 | S × F | 점수 | step 201 |
|---|---|---|---|---|---|
| 1 | 메뉴바 / 팝업 메뉴 / Help Line / Outliner 선택 색이 Maya와 크게 다름 (테마 미적용 결정의 결과) | theme ✗ 19 / 25, ΔE 14.0–22.8 | 2 × 3 | 6 | (테마 표) |
| 2 | Channel Box / Layer Editor / Outliner 모양 (파란 Display 탭, 손잡이, Outliner 순서·아이콘·선택 파랑) | `layer_tab_active` 9.7, `outliner_row_selected` 21.0, `dock_side_tab_strip` 4.3 | 2 × 3 | 6 | #2 |
| 3 | FX 세트 21 % — nConstraint 0 % 아홉 번째, nCache / Effects / Fluids 불변 | 44 / 205 | 3 × 2 | 6 | #3 |
| 4 | NURBS 컴포넌트를 Select 메뉴 / panel Show로 못 다룸 (Curves 89 %가 됐는데) | Select 회색 12 (NURBS 8), panel `NURBS CVs / Hulls`, Display `NURBS` | 2 × 2 | 4 | #7 확장 |
| 5 | 옵션 박스가 창이 아닌 것: redo 104 그대로 + generic 19 → **28** (새 Curves 5, UV 1, nHair 3), Curves / nHair 같은 명령 박스 종류 불일치 3 | redo 104, generic 28 | 2 × 2 | 4 | #4 |
| 6 | Time Slider 현재 프레임 = Blender 파란 말풍선; 1.25에서 영역 높이 45 px (Maya 36) | 칸 ΔE 0.3 (1.0 / 1.25), rects Time Slider x / y / h ✗ | 2 × 2 | 4 | #1 |
| 7 | RMB 리스트가 링 옆 / 위 (Maya 링 아래) | `marking_menu_list_bg` 3.5 (표본점 밖) | 2 × 2 | 4 | #5 |
| 8 | Create 67 % / Control 64 % / Mesh Display 64 % / Display 64 % 세 번 이상 불변 | 0 변화 | 2 × 2 | 4 | 새로 묶음 |
| 9 | Surfaces 37 % 네 번째 불변 (4.5 trim 한계) + 선반 Surfaces 회색 8 | 15 / 41 | 2 × 2 | 4 | (§1b) |
| 10 | 단축키 / 선반 / panel menu 계수기 0 변화 (다섯 / 세 / 세 번째) | 210 / 160 / 69 | 1 × 3 | 3 | #9 |
| 11 | 수동 점검 미체크 증가 | 619 → 646 (+27), 체크 0 증가 | 1 × 3 | 3 | #10 |
| 12 | Script Editor History 0 / 13, Hypershade 메뉴바 134 greyed, Graph Editor View 19 / 40 불변 | 0 변화 | 1 × 2 | 2 | (§1c) |
| 13 | Help Line 문장, Create 메뉴 tear-off / 6 px 겹침 | density −6.0 / −10.4 px 그대로 | 1 × 2 | 2 | #11 |

## 8. 모르는 것 / 반증

- Maya와 나란히 하는 실제 시나리오 실행은 하지 않았다: 수치 재계산, look_compare, 메뉴 / notice 읽기만. Maya 이미지는 기존 `research/maya/screens/*`.
- 새 working 항목 41 + 49가 Maya와 같은 결과를 내는지는 각 step 테스트 (mayapy 비교)를 믿었다; 이번 lane은 GUI로 다시 누르지 않았다.
- generic 9개가 "Maya에 옵션 창이 있다"는 판단은 메뉴 박스 존재 (`OPTION_BOXES`) 기준 — 창 내용은 보지 않음 (delegated).
- 단계별 귀속 (§0 읽기)은 커밋 제목 / 경로 이름으로 추정; 단계별 중간 커밋에서 계수기를 따로 재지 않았다.
- `python tools/menu_count.py --options` 자체는 돌리지 않았다 (dist 재빌드 위험, §방법) — 같은 테스트를 `--no-build`로 돌린 결과다.
- 메뉴 hotkey 글자 수 (57 / 0)는 다시 세지 않고 step 201 값을 옮김 (생성 파일 변화 없음 가정).
- 1.25 Maya 기준 이미지 없음 (Maya 샷은 Qt 논리 px) — 1.25 rect 차이는 과대평가일 수 있다.
- 1.25 Time Slider 45 px가 Maya 36 px 대비 실제로 거슬리는지는 수치로만 봄; 1.25 `time_slider_current` 통과가 파란 상자 옆 표본점 이동 (40, 845) → (42, 834) 덕분인지
  칸이 실제로 보이는지는 crop (`compare_audit210_s125/crop_time_slider.png`)에서 말풍선이 여전히 칸을 덮는 것으로 보임.
- Animation Layer Editor / Reference Editor 외 Maya 창 (Namespace, Shelf Editor 등) 메뉴바는 캡처가 없어 셈 밖.
