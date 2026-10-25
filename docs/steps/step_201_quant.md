# Step 201 부록 — 재점검 15차 수치 감사 (lane B, paper + look_compare)

Step 192 부록 (`docs/steps/step_192_quant.md`)의 수치를 오늘 master에서 같은 방법으로 다시 셌다. 칭찬은 빼고 차이만 적는다.
기준: 「기본 Maya에 Blender 기능이 붙은 모습」. 읽기 전용 감사, 2026-10-25, HEAD 0d75f44 (steps 193–200).
확장 zip `dist/maya-workflow-kit-0.4.1.zip` (21:45 빌드) — 파일 245개를 `src/allset`과 바이트 비교해 차이 0, src에만 있는 파일 0
(`tmp/audit201b/zipcmp.py`) → HEAD와 같다. 재빌드 안 함. 스크립트와 원자료는 `tmp/audit201b/`.
step 192 기준선 = `git archive 13d2153 src tools` → `tmp/audit201b/old/` + step 192 원자료 (`tmp/q192/results/option_kinds.json`,
`tmp/audit192b/probe192.json`, `tmp/audit192b/keymap_mapping.md`, `research/maya/screens/compare_audit192_s100/`, `_s125/`).

방법 (step 192와 같음, 경로만 `audit201b`로 바꿈; 판단은 모두 `delegated`):

- 메뉴: `python tools/menu_count.py` (→ `tmp/audit201b/menu_count.txt`), 메뉴별 표 `menus_per.py <root>` (13d2153 / HEAD, 경로 단위 diff),
  에디터 메뉴바 `ed_diff.py <root>`, panel menu / toolbar / Status Line `panel_diff.py`, 마킹 `marking.py`.
- 옵션 박스: `ALLSET_SANDBOX=q201 python tests/run.py --no-build -k step140_option_count` (1 passed) → `tmp/q201/results/option_kinds.json`.
- 선반 / 서로 다른 옵션 창 / 마킹 메뉴: `tmp/audit201b/run_probe.sh` + `probe_quant.py`, 샌드박스 `tmp/audit201b/sandbox` (폴더 먼저 생성,
  `--factory-startup`, `BLENDER_USER_*` 모두 tmp 안) → `tmp/audit201b/probe201.json` (4/4 ok).
- 단축키: `tools/gen_keymap_mapping.py` 사본 (`tmp/audit201b/gen_keymap_tmp.py`, exit 0) → `tmp/audit201b/keymap_mapping.md`.
- look_compare: `ALLSET_GUI_UI_SCALE=0.8 ALLSET_LOOK_TAG=audit201_s100 python tmp/audit201b/look_nobuild.py` (실효 1.0), `ALLSET_LOOK_TAG=audit201_s125`
  (실효 1.25) → `research/maya/screens/compare_audit201_s100/`, `_s125/`. GUI Blender는 한 번에 하나씩. md는 step 192 폴더와 diff, 이미지는 직접 봄.
- 수동 점검: `docs/manual_checks.md`의 `- [ ]` / `- [x]` 줄 수 (13d2153: `git show`).

## 0. Headline (step 192 → now)

| Metric | Step 192 (13d2153) | Now (0d75f44) | Δ |
|---|---|---|---|
| Unique kit menu leaves (main menu sets) | 1318 | 1318 | 0 |
| ... working (mapped, incl. with notice) | 750 (56.9 %) | **762 (57.8 %)** = 664 + 98 with a notice | **+12** |
| ... greyed with a notice / without | 568 / 0 | 556 / 0 | −12 / 0 |
| Leaves counted per set | 1486, working 857 (57.7 %) | 1486, working **874 (58.8 %)** | +17 (Constrain는 Rigging·Animation 두 세트에 셈) |
| `menu_map.MAP` / `notices.NOTICES` / `CATEGORIES` | 1328 / 173 / 170 | 1362 / 168 / 155 | +34 / −5 / −15 |
| Editor menu bars (7 editors, 914 leaves) | 578 (63 %) | **600 (66 %)** | **+22** (Graph Editor +13, Dope Sheet +9) — 세 번째 감사 만에 처음 움직임 |
| Panel menus / panel toolbar / Status Line greys | 69 / 111, 22 / 29, 8 leaves | 69 / 111, 22 / 29, 8 leaves — 경로 diff 0 | 0 |
| Option-box paths (`OPTION_BOXES`) | 507 | 507 | 0 |
| ... kit Maya option window | 120 paths (111 specs) | **164 paths (151 specs)** | **+44 / +40** |
| ... distinct real windows / dialogs | 125 | **166** | **+41** |
| ... operator dialog / tool / redo / menu | 22 / 10 / 127 / 1 | 23 / 10 / **104** / 0 | dialog +1, redo −23, menu −1 (`Mesh/Cleanup...` → 창) |
| ... "Blender has no settings" (`option_generic`) | 34 | **19** | −15 |
| ... dead (box on a greyed item) | 193 (38 %) | **187 (37 %)** | −6 |
| How a box opens (#82) | 메뉴바 메뉴만 ❒ 클릭 = 창; 그 밖은 hold | 같음 (이번 lane GUI 재측정 안 함) | 0 |
| Shelves (8 tabs, 203 buttons) | 160 / 43 + notice / 0 | 160 / 43 / 0 | 0 |
| Hotkeys (468 rows) 구현 / IC / 해당 없음 / 미검토 / macOS | 210 / 26 / 164 / 0 / 68 | 210 / 26 / 164 / 0 / 68 (출력 diff 0, 체크인 문서와도 0) | 0 (네 번째 연속) |
| Main-menu items with Maya hotkey text | 57; editor 0 | 57; editor 0 | 0 |
| Marking menus (26 menus, 474 entries) | 371 working (301 + 70 `item`), 52 greyed | 371 / 52 | 0 |
| Manual checks (unticked / ticked) | 598 / 107 | **619 / 107** | +21 / 0 |
| look_compare viewport (ΔE00 < 5), 1.0 | 20/20 | 20/20 (viewport.md 바이트 동일) | 0 |
| look_compare kit-drawn pixels / theme > 5, 1.0 | 7/7 · 20 of 30 | **12/12** · **19 of 25** | 표본 5개 theme → kit (dock 회색, step 195), +1 `time_slider_current` |
| look_compare rects / density / scene / furniture, 1.0 | 5/12 · 5/6 · 3/3 · 2/3 | 같음 (md 바이트 동일) | 0 |
| look_compare at 1.25 | kit-drawn 7/7, viewport 20/20, rects 5/12, density 5/6 (−10.4 px) | kit-drawn **11/12** (`time_slider_current` ✗ ΔE 13.8), 나머지 같음 | **−1 회귀 (1.25 전용)** |

읽기: steps 193–200 중 계수기를 움직인 것은 **Skin (68 → 89 %)**, **Constrain (55 → 80 %)** (step 199), **Graph Editor / Dope Sheet 메뉴바 +22**
(Weighted Tangents, Buffer Curve, Retime Tool, Tangent Length, Set Curve Colors, Select Unsnapped, Add Key Tool), `Windows/Relationship Editors/Character
Sets`, 그리고 **옵션 창 +40 spec** (primitive 15, Curves 6, Character Set 4, Constrain 4, Preferred Angle 2, Add Influence, Substitute Geometry, UV 2,
Arc 2, nHair 2, Cleanup). 193 (RMB 리스트), 195 (dock 회색 / 현재 시간 칸)은 look_compare pixels로만 보임 (§5). Panel menu, 선반, 단축키, 마킹 메뉴는
0 변화.

## 1. Menus per menu set

| Set | Leaves | Working 192 → now | Greyed + notice 192 → now | Greyed, no notice |
|---|---|---|---|---|
| Common | 449 | 298 → **299** (66 → 67 %) | 151 → 150 | 0 |
| Modeling | 349 | 203 (58 %) | 146 | 0 |
| Rigging | 190 | 138 → **149** (73 → 78 %) | 52 → 41 | 0 |
| Animation | 180 | 121 → **126** (67 → 70 %) | 59 → 54 | 0 |
| FX | 205 | 39 (19 %) | 166 | 0 |
| Rendering | 63 | 27 (43 %) | 36 | 0 |
| (always visible) Cache + Help | 50 | 31 (62 %) | 19 | 0 |

### 1a. Per top menu — 바뀐 줄만 (나머지는 step 192 값 그대로)

| Set | Menu | Leaves | % working 192 → now | Working (+ notice) | Greyed + notice | Option boxes |
|---|---|---|---|---|---|---|
| Common | Windows | 74 | 64 → **65 %** | 40 + 8 | 26 | 1 |
| Rigging | **Skin** | 28 | 68 → **89 %** | 25 + 0 | 3 | 13 |
| Rigging / Animation | **Constrain** | 20 | 55 → **80 %** | 13 + 3 | 4 | 17 |

경로 diff (13d2153 → 0d75f44), **+12 working (모두 greyed → working), 잃은 것 없음**:

- Skin (6): `Bake Deformation to Skin Weights...`, `Export Weight Maps...`, `Import Weights Maps...`, `Move Weights to Influences`,
  `Normalize Weights/Enable Weight Post Normalization`, `Substitute Geometry`.
- Constrain (5): `Normal`, `Tangent`, `Remove Target`, `Set Rest Position`, `Modify Constrained Axis...`.
- `Windows/Relationship Editors/Character Sets` (step 192 §1b 모순 해소).

움직이지 않은 메뉴: **step 98 이후 여덟 번째 감사 연속**: nConstraint 0 %, nCache 15 %, Fields/Solvers 37 %, Effects 18 %, Texturing 12 %. step 133 이후
일곱 번: Windows 65 % (+1 항목만). step 145 이후 여섯 번: Display, Generate 4 %, Toon, Stereo, Cache, nParticles / Fluids / nCloth. step 154 이후 다섯
번: Mesh, Edit Mesh, Mesh Tools, Playback, Audio, Render, File, Curves 58 %. step 163 이후 네 번: Select, Edit, Modify, Deform 65 %, Visualize. step 182
이후 세 번: Surfaces 37 %, Lighting/Shading. step 192 이후 두 번: Create 67 %, Mesh Display 64 %, Key 73 %, Control 64 %, UV 89 %.
**FX 세트 전체 19 %는 세 번째 연속 39 / 205.**

### 1b. Weakest menus by Maya-user impact (daily use × greyed share), 현재

| Menu | % working | 아직 greyed인, Maya 사용자가 매일·매주 누르는 항목 |
|---|---|---|
| **Curves** | 58 % (5번째 연속) | `Lock / Unlock Length`, `Bend`, `Curl`, `Scale Curvature`, `Duplicate Surface Curves`, `Align`, `Edit Curve Tool`, `Intersect`, `Fit B-spline`, `CV Hardness`, `Project Tangent`, `Extend / Offset Curve On Surface` |
| **Create** | 67 % | `Polygon / NURBS Primitives/Interactive Creation` + `Exit On Completion` (4), `Lights/Ambient` / `Volume Light`, `Construction Plane`, `Adobe(R) Illustrator(R) Object`, `Scene Assembly`, Measure Tools 2, Subdiv / Volume Primitives 9 |
| **Key** | 73 % | `Scene Time Warp/*` 4, `IK/FK Keys/*` 4, `Set Blend Shape Target Weight Keys` |
| **Mesh Display** | 64 % | `Color Material Channel/*` 6, `Material Blend Setting/*` 7, `Share Instances` |
| **Control** | 64 % | `Tag As Controller`, `Parent Controller`, `Create Control Rig`, `Character Mapper`, `Redirect` |
| **Surfaces** | 37 % | 26 greyed (Trim / Untrim / Intersect / Project / Extend / Offset / Round / Stitch — 4.5 NURBS 한계) |
| **Deform** | 65 % | `Tension`, `Solidify`, `Morph`, `Wrinkle`, `Jiggle` 3, `Sculpt`, `Pose Interpolator`, `Blend Shape#2/Swap`, `Edit Membership Tool` |
| Constrain | 80 % | `UV Pin`, `Proximity Pin`, `Motion Paths/Flow Path Object`, `Set Motion Path Key` |
| Skin | 89 % | `Interactive Bind Skin` (+ Tool), `Move Skinned Joints` |
| Generate / nHair / nConstraint / Toon / FX 전체 | 0–19 % | Blender 대응 없는 시스템 — notice만 |

Skin / Constrain은 step 192 1b 상위에서 내려왔다. Character Set notice 모순 (step 192 §1b): `rg "no character sets" src` 0 (`.pyc` 제외),
`Windows/.../Character Sets` working, Graph Editor `Show/Objects/Characters` working, `menu_consistency` 0. **남은 것: Dope Sheet `Show/Objects/Characters`는
greyed** (notice `notices.py:828-830` "Blender's Dope Sheet channel list can't show character set nodes" → Graph Editor로 안내). Maya는 두 에디터 모두 있음.

### 1c. Editor menu bars

914 leaves, working **600 (66 %)** [578]. 경로 diff 22개, 모두 G → W:

- Graph Editor (13): `Curves/Weighted Tangents`, `Non-weighted Tangents`, `Default Tangent Weight/*` 2, `Swap Buffer Curve`, `View/Show Buffer Curves`,
  `Edit/Select Unsnapped`, `Set Curve Colors...`, `Transformation Tools/Retime Tool`, `Keys/Add Key Tool`, `Tangents/Free / Lock Tangent Length`,
  `Show/Objects/Characters`.
- Dope Sheet (9): 위와 같은 이름 중 Weighted 4, `Select Unsnapped`, `Set Curve Colors...`, `Retime Tool`, Tangent Length 2.

남은 greyed: Graph Editor View 19 / 40, Show 17 / 34, Curves 11 / 39, List 6 / 8; Dope Sheet Show 18 / 34, Curves 8, List 6 / 7; UV Editor 36 (그대로),
Hypershade 134 / 249 (그대로, Create 91), Render Settings 11 / 21, **Script Editor History 0 / 13 (여덟 번째 연속 0 %)**.

### 1d. Panel menus / panel toolbar / Status Line

경로 diff 0. Panel menus 69 / 111 (greyed 42: View 4, Shading 9, Lighting 3, Show 18 — **`Show/NURBS CVs`, `NURBS Hulls` 여전히 회색 (step 192 #9)**,
Renderer 2, Panels 5), panel toolbar greyed 7, Status Line greys 8.

## 2. Option boxes per top menu (507 paths)

window = kit Maya option window, dialog = operator / file dialog, tool = tool + Tool Settings, redo = run + Adjust Last Operation, generic = "Blender has
no settings for this" 창, dead = greyed 항목의 박스. 바뀐 줄만 [step 192 값]:

| Menu | window | dialog | tool | redo | generic | dead |
|---|---|---|---|---|---|---|
| Create | **29** [8] | 1 | – | **6** [25] | **1** [3] | 7 |
| Curves | **9** [3] | – | – | 4 | **0** [6] | 11 |
| Constrain | **10** [6] | – | – | 4 | – | **3** [7] |
| Skin | **6** [4] | **1** [0] | – | 3 | **0** [1] | **3** [5] |
| Skeleton | **5** [3] | – | – | 3 | **0** [2] | – |
| Key | **11** [9] | – | – | **0** [2] | – | 1 |
| Control | **2** [0] | – | – | **0** [2] | – | 1 |
| UV | **5** [3] | – | – | 3 | **1** [3] | 2 |
| Mesh | **3** [2] | 1 | 1 | 11 | – | 4 (menu 1 → 0) |
| nHair | **2** [0] | – | – | 2 | **0** [2] | 9 |
| (그 밖의 메뉴 전부) | step 192와 같음 | | | | | |

경로 diff (45개): redo → window 23 (Polygon Primitives 11 — `Disc`, `Platonic Solid`, `Prism`, `Pyramid`, `Pipe`, `Helix`, `Gear`, `Soccer Ball`, `Super
Ellipse`, `Spherical Harmonics`, `Ultra Shape`; NURBS Primitives 8; `Key` / `Control/Create Character Set` / `Create Subcharacter Set` 4); generic → window
15 (`Curves/Cut`, `Detach`, `Reverse Direction`, `Smooth` ×2, `Straighten`, Arc 2, `Skeleton/Set / Assume Preferred Angle`, `Skin/Edit Influences/Add
Influence`, `UV/Merge UVs`, `Contour Stretch`, `nHair/Modify Curves/Smooth`, `Straighten`); dead → window 5 (Constrain 4, `Skin/Substitute Geometry`);
dead → dialog 1 (`Skin/Export Weight Maps...`); menu → window 1 (`Mesh/Cleanup...`). **step 192 #3 (redo / generic 박스) 목록은 전부 해소.**

남은 generic 19: `Create/Curve Tools/Pencil Curve Tool`, `UV/3D Cut and Sew UV Tool`, `Surfaces/Planar`, `Bevel Plus`, `Duplicate NURBS Patch`,
`Modify/Bake Pivot`, `Mesh Display/Paint Vertex Color Tool`, `Texturing/3D Paint Tool`, `File/Archive Scene`, nParticles 5 (`Create Emitter` ×2,
`Emit from Object` ×2, `Make Collide`), nCloth 2, `Fluids/Make Collide`, `Render/Render Current Frame` / `IPR` (Maya와 같은 경고).
redo 104 중 Maya에 옵션 창이 있는 매일·매주 항목: `Create/Lights/Point / Spot / Directional / Area Light`, `Create/Free Image Plane`, `Create/Curve
Tools/Bezier Curve Tool`, `UV/Cylindrical / Spherical / Camera-based`, `Curves/Open/Close`, `Offset Curve`, `Extend Curve`, `Insert Knot`, `Skin/Smooth /
Mirror Skin Weights`, `Prune Small Weights`, `Constrain/Geometry`, `Point On Poly`, `Closest Point`, `Motion Paths/Attach to Motion Path`
(+ Edit Mesh 9, Mesh 11).

dead 187을 메뉴별로 많은 순: Surfaces 22, Fluids 16, Modify 16, Deform 12, Curves 11, nConstraint 11, nCache 9, nHair 9, Generate 8, nParticles 8,
Cache 7, Create 7, Mesh Tools 7, Effects 6, Fields 6; Constrain 7 → 3, Skin 5 → 3.

## 3. Shelves (`ui/shelf.all_buttons`)

203 buttons, **160 working (79 %)**, 43 greyed with a notice, 0 without — step 192와 같음 (두 번째 연속). 남은 greyed: Curves / Surfaces 8, FX 16,
FX Caching 6, Sculpting 7, Rendering 4 (`Ambient Light`, `Volume Light`, `Shading Map`, `Render Diagnostics`), Poly Modeling 1 (`3D Grab UV Tool`),
Rigging 1 (`Human IK`).

## 4. Hotkeys / marking menus

Hotkeys (468 rows): 구현 210, IC 일치 26, 해당 없음 164, 미검토 0, macOS 68 — `tmp/audit201b/keymap_mapping.md`가 step 192 출력과 체크인 문서
모두와 diff 0 (네 번째 연속 변화 없음). 메뉴 hotkey 글자: 메인 57, 에디터 메뉴바 0 (`ui/menu_hotkeys.py` 파일 변화 없음).

Marking menus: 474 entries, 371 working (301 direct + 70 `item`), 52 greyed + 51 submenus — 경로 diff 0 (`marking.py`: new greyed [], no longer
greyed []). NURBS surface용 RMB 메뉴 (Isoparm / Surface Point / Hull) 여전히 0.

## 5. look_compare

### 5a. 실효 UI 배율 1.0 (`compare_audit201_s100/`, 15 side-by-side, 6 crops)

- checks 9/9; pixels kit-drawn **12/12** (theme 25, 19 > 5 not counted, 2 no kit element, 0 anchors missing); viewport 20/20; rects 5/12; scene 3/3;
  density 5/6 (**menu top − bar bottom −6.0/0** 그대로); grid ok (ΔE00 0.7, corners 4/4, 0.22 ms); furniture 2/3.
- step 192 대비: rects / density / scene / furniture / viewport.md **바이트 단위로 같음**. pixels.md만 다름 (step 195 dock 회색):
  `cb_bg` theme #303030 ΔE **6.5 ✗ → kit #444444 0.0**, `cb_field` #1d1d1d 4.4 → #313131 1.9, `cb_shape_row` 2.3 → 1.9, `layer_editor_list` theme → kit
  (1.3), `cb_input_row`는 "Maya 가로 스크롤바, kit 없음"으로 표본 없음; `dock_side_tab_strip` #303030 2.3 → #444444 **4.3** (나빠짐, 통과 범위 안);
  새 `time_slider_current` #525252 = Maya 0.0. 마킹 메뉴 표본: 링이 누른 점으로 내려옴 (y 234 → 438, step 193); `marking_menu_list_bg`가 #5c5c5c
  (뷰포트 바탕)에 떨어져 ΔE 0.3 → **3.5** — 리스트가 링 아래가 아니라 옆으로 가서 표본점이 리스트 밖 (§5c-1).
- theme ✗ 19개 (step 130 결정상 kit가 못 고침): 메뉴바 / 팝업 / 에디터 틈 / Outliner 선택 행 등 step 192 값 그대로.
- rects ✗ 7개 그대로: Tool Box / Outliner / viewport / dock 37 px 높고 10 px 위, Tool Box 56 vs 40 폭, dock 287 vs 260, Time Slider 1300 vs 1596 폭,
  Range Slider 높이 26 vs 31.

### 5b. 실효 UI 배율 1.25 (`compare_audit201_s125/`)

- checks 9/9, kit-drawn **11/12**, viewport 20/20, rects 5/12, scene 3/3, density 5/6 (−10.4 px), grid ok (0.219 ms), furniture 2/3. rects / density /
  scene / furniture / viewport.md는 step 192와 바이트 동일.
- **회귀: `time_slider_current` = #282828 vs Maya #525252, ΔE 13.8 ✗** (1.0은 0.0). 1.25에서는 kit 회색 현재 시간 칸이 표본점 (40, 845)에 없다 —
  Blender 파란 프레임 상자가 칸을 거의 다 덮는다는 CLAUDE.md step 195 기록과 맞음. kit-drawn 표본 중 유일한 ✗.

### 5c. 이미지에서 보이는 차이 (왼쪽 Maya, 오른쪽 kit; 차이만, 직접 봄)

step 192 §5c 대비 해결된 것: **#1 (a) 링 이동** (14: 링이 누른 점 = pCube1 가운데에 그려짐, 1.0 / 1.25 모두), **#1 (b) 둘째 열 / 경계 틈** (리스트가 한
열, 행 간격 균일), **#3 일부 — dock 바탕 회색** (crop_channel_box: Maya #444444와 같은 톤, 값 칸 #313131), **dock 오른쪽 세로 탭 줄** (Channel Box /
Layer Editor · Attribute Editor · Modeling Toolkit, Maya와 같은 배치). 남은 / 새로 본 차이:

1. **RMB 리스트 위치 (`14`)** — Maya: 리스트가 링 **아래** (pCube1... 행이 Face 박스 바로 밑, 창 아래로 넘침). kit 1.0: 리스트가 링 **왼쪽** 한 열
   (x 1305–1410, y 155–460 / 2000 px 표시 기준), 링보다 위에서 시작. kit 1.25: 리스트가 Outliner 위를 덮고 마지막 행 `Assign Existing Material ▸`가 Time
   Slider 위에 걸침. step 193 규칙 ("under the ring, else beside it") 대로이지만 Maya 샷과는 다른 자리 — 샷 창 900 px가 화면보다 작아서 (§8).
2. **Time Slider 현재 프레임** (`crop_time_slider`): Blender 파란 말풍선 "1"이 그대로 위에 있다. 1.0에서는 그 아래 회색 칸이 표본상 맞지만 (ΔE 0.0)
   눈으로는 말풍선만 보인다; 1.25에서는 칸이 가려짐 (§5b). Maya = 회색 칸 + 아래쪽 숫자.
3. **Channel Box 모양** (`crop_channel_box`): 바탕 회색은 맞음. 남은 것: 맨 위 `::::::` 손잡이 + `v` 접기 (Maya: 오른쪽 위 아이콘 3개), `pCube1` / SHAPES /
   INPUTS 머리글 굵기 없음, SHAPES 행이 둥근 입력 칸 (Maya 평평한 띠), Layer Editor `Display` 탭이 파란 알약 (Maya 회색 탭), Layer 아이콘 4개 중 2개 흐림,
   아래 가로 스크롤바 없음, Layer 리스트 아래 `▸` / `::::` 손잡이.
4. **Outliner** (01 / 09 / 14) — 변화 없음: 오브젝트가 카메라보다 먼저, 주황 삼각 아이콘, 09에서 kit 행 왼쪽 점 3개.
5. **Create 메뉴** (`12`) — 변화 없음: 메뉴바와 6 px 겹침, 첫 줄 tear-off 점선 (Maya: `Objects` 섹션 라벨), `Subdiv Primitives` 행 (Maya 2022 없음),
   `Sweep Mesh` / `USD` 녹색 표시 없음, `Adobe(R) Illustrator(R) Object`, `Construction Plane`, `Scene Assembly` 회색.
6. **컴포넌트 CB** (`09`): kit = `pCubeShape1` + INPUTS; Maya = `pCube1Shape`, `CVs (click to show)`, INPUTS (§8, 그대로).
7. **Help Line**: Move Tool kit "Move Tool: drag the manipulator. Hold X/C/V to snap to grid/curve/point, D to move the pivot" / Maya "Move Tool: Use
   manipulator to move object(s). Ctrl+middle-drag to move components along normals. Shift+drag manipulator axis or plane handle..." — 그대로.
8. **Four view** (`16`) — 변화 없음: panel menu + toolbar가 네 칸 위 한 벌, 직교 칸 배율이 Maya보다 큼, kit은 선택 상태 (샷 스크립트 경로 문제).
9. **Hotbox** (`13`): 가운데 제목 "Maya Workflow Kit" (Maya "Maya"); Maya 행의 `MASH` 두 개 없음 (플러그인, 차이로만 기록).
10. **1.25 레이아웃** (`compare_audit201_s125/14`): panel toolbar가 `>>`로 잘림, 메인 뷰포트가 Maya보다 좁고 dock 넓음 (rects 그대로).

## 6. Domain 차이 (시나리오별, 증거)

| Domain | Maya가 아니라고 느껴지는 곳 (큰 것부터) | 증거 |
|---|---|---|
| Modeling | Curves 58 % (5번째 불변); Interactive Creation 4 greyed; NURBS CVs / Hulls 표시 토글 회색; Mesh Display Color Material Channel / Blend 13; Pencil Curve / Bezier 박스 generic / redo | §1b, §1d, §2 |
| Surfaces | 37 % (4.5 trim 한계); NURBS surface RMB 마킹 메뉴 없음; Planar / Bevel Plus / Duplicate Patch 박스 generic | §1a, §2, §4 |
| UV | 3D Cut and Sew 박스 generic, Cylindrical / Spherical / Camera-based 박스 = redo; `3D Grab UV Tool` 선반 회색; UV Editor 메뉴바 36 greyed 그대로 | §1c, §2, §3 |
| Animation | Time Slider 현재 프레임 = Blender 말풍선 (1.25에서 kit 칸 가려짐); Dope Sheet `Show/Objects/Characters` greyed; Scene Time Warp 4; Graph Editor View 19 / Show 17 greyed | §5b, §5c-2, §1b, §1c |
| Rigging | Control 64 % (controller tags, HumanIK); Skin `Interactive Bind Skin`, Constrain `UV / Proximity Pin`; Smooth / Mirror Skin Weights 박스 = redo | §1b, §2 |
| FX | 19 % (세 번째 연속 39 / 205; nConstraint 0 %, 여덟 번째) | §1 |
| Rendering | Texturing 12 %, Hypershade Create 91 greyed, 조명 4종 박스 = redo, 선반 Ambient / Volume Light 회색 | §1c, §2, §3 |
| 공통 UI | RMB 리스트 링 옆 (Maya 아래), CB 머리글 / 손잡이 / 파란 탭, Outliner, 메뉴 6 px 겹침 + tear-off, Help Line 문장, 테마 색 19개 (결정상 불가), 에디터 메뉴 hotkey 글자 0, Script Editor History 0 / 13 | §5c, §1c |

## 7. Ranked remaining differences by number

점수 = 심각도 (1–3) × 빈도 (1–3). step 192 #3 (redo / generic 박스 목록), #5 (Character Set notice — Dope Sheet 1개 남음), #6 (RMB 둘째 열 / 링 이동),
#7 (Skin), #8 (Constrain)은 해결 / 대부분 해결.

| # | 차이 | 수치 | S × F | 점수 | step 192 |
|---|---|---|---|---|---|
| 1 | Time Slider 현재 프레임 = Blender 말풍선; 1.25에서 kit 칸 가려짐 | 1.25 `time_slider_current` ΔE 13.8 ✗ (유일한 kit-drawn ✗) | 2 × 3 | 6 | #2 |
| 2 | Channel Box / Layer Editor 모양 (머리글, 손잡이, 파란 탭, 스크롤바) | 바탕은 해결 (cb_bg 6.5 → 0.0), `dock_side_tab_strip` 2.3 → 4.3 | 2 × 3 | 6 | #1 |
| 3 | FX 세트 19 % 세 번째 연속 불변 | 39 / 205, nConstraint 0 % 8번째 | 3 × 2 | 6 | #4 |
| 4 | 박스 redo인데 Maya는 창: 조명 4, UV 투영 3, Curves 4, Skin 3, Constrain 4 등 | redo 104, generic 19, dead 187 | 2 × 2 | 4 | #3 잔여 |
| 5 | RMB 리스트가 링 옆 / 위 (Maya 링 아래) | `marking_menu_list_bg` ΔE 0.3 → 3.5 (표본점 밖) | 2 × 2 | 4 | #6 잔여 |
| 6 | Curves 58 % 다섯 번째 연속 | 0 변화 | 2 × 2 | 4 | #11 |
| 7 | Panel `Show/NURBS CVs` / `NURBS Hulls` 회색 | Panel menus 69 / 111, 0 변화 | 2 × 2 | 4 | #9 |
| 8 | ❒ 클릭이 hotbox / 마킹 / 선반 메뉴에서는 명령 | 재측정 안 함 | 2 × 2 | 4 | #10 |
| 9 | 단축키 / 선반 / 마킹 / panel menu 네 계수기 0 변화 | 210 / 160 / 371 / 69 | 1 × 3 | 3 | 새로 (정체) |
| 10 | 수동 점검 미체크 증가 | 598 → 619 (+21), 체크 0 증가 | 1 × 3 | 3 | 새로 |
| 11 | Help Line 문장, Create 메뉴 tear-off / 6 px 겹침 | density −6.0 / −10.4 px 그대로 | 1 × 3 | 3 | #12 / #13 |
| 12 | Dope Sheet `Show/Objects/Characters` greyed (Graph Editor는 working) | 1 | 1 × 2 | 2 | #5 잔여 |

## 8. Not measured / counterevidence

- Maya와 나란히 하는 실제 시나리오 실행은 하지 않았다: 수치 재계산, look_compare, 코드 / notice 읽기만. Maya 이미지는 기존 `research/maya/screens/*`.
- ❒ 클릭 (step 183), RMB 리스트 배치 (step 193), Skin / Constrain 동작 (step 199)은 GUI로 다시 재지 않았다 — 각 step 테스트를 믿음.
- §5c-1 RMB 리스트: Maya 샷의 리스트는 화면 아래로 넘쳐 잘리고, kit 샷 창은 1600 × 900 (화면보다 작음) — step 193 규칙상 아래 공간이 모자라 옆으로
  간다. 최대화한 창에서는 링 아래로 갈 수 있다 (delegated: 결함 점수 2 × 2로 둠).
- 1.25 `time_slider_current` ✗: 표본점이 Blender 파란 상자 밑일 가능성 — kit 칸이 그려지지 않은 것인지 가려진 것인지는 확대 crop으로 확인하지 않았다.
- `09` Maya shape 이름 `pCube1Shape` vs kit `pCubeShape1`, `CVs (click to show)` 줄: step 192 §8과 같은 이유로 차이로 세지 않음.
- 1.25 Maya 기준 이미지 없음 (Maya 샷은 Qt 논리 px) — 1.25 rect 차이는 과대평가일 수 있다.
- 옵션 창 166개는 프로브 기준; 창마다 필드가 Maya와 같은지는 보지 않았다. redo 중 "Maya에 창이 있는 것" 목록은 메뉴 이름으로 판단 (delegated).
- 수동 점검 개수는 HEAD 0d75f44 기준 (619 / 107). 작업 사본은 다른 lane이 고치는 중이라 미체크 624 (+5).
