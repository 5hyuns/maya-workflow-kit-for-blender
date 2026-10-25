# Step 182 부록 — 재점검 13차 수치 감사 (lane B, paper + look_compare)

Step 173 부록 (`docs/steps/step_173_quant.md`)의 수치를 오늘 master에서 같은 방법으로 다시 셌다. 칭찬은 빼고 차이만 적는다.
기준: 「기본 Maya에 Blender 기능이 붙은 모습」. 읽기 전용 감사, 2026-10-25, HEAD 326f12f (0.4.0 + steps 174–181).
확장 zip `dist/maya-workflow-kit-0.4.0.zip` (09:31 빌드, HEAD 커밋 09:30 이후) — 파일 227개를 `src/allset`과 바이트 비교해 차이 0,
src에만 있는 파일 0이라 HEAD와 같다 (재빌드 안 함: 메인 세션이 `dist/`를 쓴다). 스크립트와 원자료는 `tmp/audit182b/`.
step 173 기준선 = `git archive b07f9a7 src tools` → `tmp/audit182b/old/` + step 173 원자료 (`tmp/q173/results/option_kinds.json`,
`tmp/audit173b/probe173.json`, `research/maya/screens/compare_audit173_s100/`, `compare_audit173_s125/`).

방법 (step 173과 같음, 경로만 바꿈):

- 메뉴: `python tools/menu_count.py` (→ `tmp/audit182b/menu_count.txt`), 메뉴별 표 `tmp/audit182b/menus_per.py <root>`
  (b07f9a7 / HEAD, 경로 단위 diff), 에디터 메뉴바 `tmp/audit182b/ed_diff.py <root>`.
- 옵션 박스: `ALLSET_SANDBOX=q182 python tests/run.py --no-build -k step140_option_count` (1 passed) → `tmp/q182/results/option_kinds.json`.
  `menu_count.py --options`는 같은 테스트를 샌드박스 `option_count` + 빌드로 돌리므로 (메인 세션의 `dist/`를 다시 씀) 쓰지 않았다 — 결과 표는 같다.
- 선반 / 서로 다른 옵션 창 / 마킹 메뉴: `tmp/audit182b/run_probe.sh` + `probe_quant.py`, 샌드박스 `tmp/audit182b/sandbox`
  (폴더 먼저 생성, `--factory-startup`, `BLENDER_USER_*` 모두 tmp 안) → `tmp/audit182b/probe182.json`; 마킹 분류 `tmp/audit182b/marking.py`.
- 단축키: `tools/gen_keymap_mapping.py`를 출력만 `tmp/audit182b/keymap_mapping.md`로 바꾼 사본 (`gen_keymap_tmp.py`, exit 0) —
  결과가 체크인된 `docs/keymap_mapping.md` (77a5263, step 175)와 같다.
- look_compare: (a) `ALLSET_GUI_UI_SCALE=0.8 ALLSET_LOOK_TAG=audit182_s100 python tmp/audit182b/look_nobuild.py` →
  `research/maya/screens/compare_audit182_s100/`; (b) 배율 없이 `ALLSET_LOOK_TAG=audit182_s125` (실효 1.25) → `compare_audit182_s125/`.
  샌드박스 `tmp/look_env_audit182_s100` / `_s125`. 각각 step 173 폴더와 md diff.
- 수동 점검: `docs/manual_checks.md`의 `- [ ]` / `- [x]` 개수 (작업 사본).

## 0. Headline (step 173 → now)

| Metric | Step 173 (b07f9a7) | Now (326f12f) | Δ |
|---|---|---|---|
| Unique kit menu leaves (main menu sets) | 1318 | 1318 | 0 |
| ... working (mapped, incl. with notice) | 699 (53.0 %) | **714 (54.2 %)** = 613 + 101 with a notice | **+15** |
| ... greyed with a notice / without | 619 / 0 | 604 / 0 | −15 / 0 |
| Leaves counted per set | 1486, working 806 (54.2 %) | 1486, working **821 (55.2 %)** | +15 |
| `menu_map.MAP` / `notices.NOTICES` / `CATEGORIES` | 1259 / 178 / 171 | 1292 / 176 / 171 | +33 / −2 / 0 |
| Editor menu bars (7 editors, 914 leaves) | 560 (61 %) | **578 (63 %)** — UV Editor 118 → 136 | +18 |
| ... minus web page 52 / Blender Preferences 5 | real 503 / 914 (55 %) | real **521 / 914 (57 %)** | +18 |
| Panel menus / panel toolbar / Status Line greys (새 계수, step 177) | — | 67 / 111 (60 %), 22 / 29 (76 %), 0 / 9 | 새 기준선 |
| Option-box paths (`OPTION_BOXES`) | 507 | 507 | 0 |
| ... kit Maya option window | 104 paths (95 specs) | **114 paths (105 specs)** | +10 / +10 |
| ... distinct real windows / dialogs | 109 | **119** | +10 (Surfaces 10) |
| ... operator dialog / tool / redo / menu | 22 / 10 / 120 / 1 | 22 / 10 / **118** / 1 | redo −2 (Revolve → window, Insert Isoparms → generic) |
| ... "Blender has no settings" (`option_generic`) | 36 | **35** | −1 (Loft / Extrude / Reverse Direction → window; Insert Isoparms, Duplicate NURBS Patch → generic) |
| ... dead (box on a greyed item) | 214 (42 %) | **207 (41 %)** | −7 |
| How a box opens (#82) | click = command; window by a 0.2 s hold | 그대로 (`ui/menu_sets.py:261` `operator_menu_hold`, `:823` `from_hold`) | **여섯 번째 감사 연속 같음** |
| Shelves (8 tabs, 203 buttons) | 155 / 48 + notice / 0 | **159** / 44 / 0 | +4 (Curves / Surfaces 26 → 30) |
| Hotkeys (468 rows) 구현 / IC / 해당 없음 / 미검토 / macOS | 209 / 27 / 164 / 0 / 68 | **210 / 26** / 164 / 0 / 68 | g RepeatLast IC → 구현 (step 175) |
| Main-menu items with Maya hotkey text | 57; editor 0 | 57; editor 0 | 0 |
| Marking menus (26 menus, 474 entries) | 368 working (298 + 70 `item`), 65 greyed, 41 submenus | **같음** (greyed 경로 집합 diff 0) | 0 |
| Manual checks (unticked / ticked) | 567 / 86 | **587 / 96** | +20 / +10 |
| look_compare viewport (ΔE00 < 5), scale 1.0 | 11/12 | **12/12** (face fill ΔE 40.5 → **2.3**) | +1 |
| look_compare kit-drawn pixels / theme > 5 | 6/6 · 20 of 31 | 6/6 · 20 of 31 | 0 |
| look_compare rects / density / scene / grid / furniture / checks, 1.0 | 5/12 · 5/6 · 3/3 · ok · 2/3 · 9/9 | 동일 (pixels, rects, density, scene, furniture.md 바이트 단위로 같음) | 0 |
| look_compare at 1.25 | rects 5/12, viewport 11/12, density 5/6 (−10.4 px) | rects 5/12, **viewport 12/12**, density 5/6 (−10.4 px) | viewport +1 |

읽기: steps 174–181 중 메뉴 계수기를 움직인 것은 **Light Linking (step 179, Lighting/Shading 36 → 93 %)**, **Surfaces (step 181, 20 → 37 %)**,
**UV Editor (step 178, 69 → 79 %)** 세 가지뿐이다. step 174 (도구가 모드를 따라감), 175 (G 반복), 176 (선택 면 모양), 180 (애니 레이어 = Layer
Editor Anim 탭)은 계수기에 잡히지 않는다 (174 / 176은 이미지에서 확인, §5c). step 177은 새 계수 (panel menu)를 만들었을 뿐 메인 수치는 그대로.
Key 54 %, Control 7 %, Mesh Display 38 %, Create 57 %, 모든 FX 메뉴는 **한 leaf도 움직이지 않았다**.

## 1. Menus per menu set

| Set | Leaves | Working 173 → now | Greyed + notice 173 → now | Greyed, no notice |
|---|---|---|---|---|
| Common | 449 | 291 (65 %) | 158 | 0 |
| Modeling | 349 | 185 → **192** (53 % → 55 %) | 164 → 157 | 0 |
| Rigging | 190 | 130 (68 %) | 60 | 0 |
| Animation | 180 | 113 (63 %) | 67 | 0 |
| FX | 205 | 37 (18 %) | 168 | 0 |
| Rendering | 63 | 19 → **27** (30 % → 43 %) | 44 → 36 | 0 |
| (always visible) Cache + Help | 50 | 31 (62 %) | 19 | 0 |

### 1a. Per top menu (Deform and Constrain listed once)

바뀐 줄만 굵게; 나머지는 step 173 §1a와 같은 값.

| Set | Menu | Leaves | % working 173 → now | Working (+ notice) | Greyed + notice | Option boxes |
|---|---|---|---|---|---|---|
| Common | File | 30 | 80 % | 15 + 9 | 6 | 12 |
| Common | Edit | 68 | 68 % | 45 + 1 | 22 | 19 |
| Common | Create | 70 | 57 % | 32 + 8 | 30 | 44 |
| Common | Select | 81 | 67 % | 54 + 0 | 27 | 3 |
| Common | Modify | 90 | 63 % | 47 + 10 | 33 | 31 |
| Common | Display | 36 | 64 % | 20 + 3 | 13 | 2 |
| Common | Windows | 74 | 64 % | 38 + 9 | 27 | 1 |
| Modeling | Mesh | 26 | 81 % | 21 + 0 | 5 | 20 |
| Modeling | Edit Mesh | 28 | 89 % | 25 + 0 | 3 | 18 |
| Modeling | Mesh Tools | 36 | 81 % | 20 + 9 | 7 | 35 |
| Modeling | Mesh Display | 39 | 38 % | 15 + 0 | 24 | 10 |
| Modeling | Curves | 36 | 58 % | 19 + 2 | 15 | 24 |
| Modeling | **Surfaces** | 41 | **20 % → 37 %** | 13 + 2 | 26 | 37 |
| Modeling | Deform | 74 | 65 % | 31 + 17 | 26 | 47 |
| Modeling | UV | 19 | 84 % | 16 + 0 | 3 | 11 |
| Modeling | Generate | 50 | 4 % | 2 + 0 | 48 | 8 |
| Rigging | Skeleton | 54 | 94 % | 48 + 3 | 3 | 8 |
| Rigging | Skin | 28 | 68 % | 19 + 0 | 9 | 13 |
| Rigging | Constrain | 20 | 55 % | 8 + 3 | 9 | 17 |
| Rigging | Control | 14 | 7 % | 0 + 1 | 13 | 3 |
| Animation | Key | 41 | 54 % | 21 + 1 | 19 | 12 |
| Animation | Playback | 26 | 73 % | 18 + 1 | 7 | 1 |
| Animation | Audio | 9 | 56 % | 4 + 1 | 4 | 0 |
| Animation | Visualize | 10 | 80 % | 8 + 0 | 2 | 4 |
| FX | nParticles | 25 | 28 % | 5 + 2 | 18 | 15 |
| FX | Fluids | 25 | 16 % | 2 + 2 | 21 | 20 |
| FX | nCloth | 13 | 38 % | 2 + 3 | 8 | 3 |
| FX | nHair | 54 | 4 % | 1 + 1 | 52 | 13 |
| FX | nConstraint | 19 | 0 % | 0 + 0 | 19 | 11 |
| FX | nCache | 20 | 15 % | 3 + 0 | 17 | 12 |
| FX | Fields/Solvers | 38 | 37 % | 13 + 1 | 24 | 19 |
| FX | Effects | 11 | 18 % | 2 + 0 | 9 | 8 |
| Rendering | **Lighting/Shading** | 14 | **36 % → 93 %** | 13 + 0 | 1 | 0 |
| Rendering | Texturing | 8 | 12 % | 1 + 0 | 7 | 2 |
| Rendering | Render | 15 | 73 % | 9 + 2 | 4 | 6 |
| Rendering | Toon | 20 | 5 % | 0 + 1 | 19 | 1 |
| Rendering | Stereo | 6 | 17 % | 0 + 1 | 5 | 0 |
| (always visible) | Cache | 24 | 46 % | 5 + 6 | 13 | 15 |
| (always visible) | Help | 26 | 77 % | 18 + 2 | 6 | 1 |

경로 diff (b07f9a7 → 326f12f), **+15 working, 잃은 것 없음**:

- Lighting/Shading (+8, step 179): `Make / Break Light Links`, `Make / Break Shadow Links`, `Select Lights Illuminating / Shadowing Object`,
  `Select Objects Illuminated / Shadowed by Light`.
- Surfaces (+7, step 181): `Attach`, `Birail/Birail 1 Tool`, `Boundary`, `Detach`, `Duplicate NURBS Patch`, `Rebuild`, `Square`;
  `Loft` / `Extrude`는 notice 붙은 working → notice 없는 working.

움직이지 않은 메뉴: **step 98 이후 여섯 번째 감사 연속**: Control 7 %, nConstraint 0 %, nCache 15 %, Fields/Solvers 37 %, Effects 18 %,
Texturing 12 %. step 133 이후 다섯 번 연속: Mesh Display 38 %, Windows 64 %. step 145 이후 네 번 연속: Display, Generate, 모든 FX, Toon,
Stereo, Cache. step 154 이후 세 번 연속: Mesh, Edit Mesh, Mesh Tools, UV, Skin, Constrain, Playback, Audio, Render, File, Create, Curves.
step 163 이후 두 번 연속: Key, Select, Edit, Modify, Deform, Visualize.

### 1b. Weakest menus by Maya-user impact (daily use × greyed share), 현재

| Menu | % working | 아직 greyed인, Maya 사용자가 매일·매주 누르는 항목 |
|---|---|---|
| **Mesh Display** | 38 % (다섯 번째 연속) | `Set Vertex Normal`, `Apply Color`, 컬러 세트 `Rename Current Set...` / `Modify Current Set` / `Assign New Set` / `Assign Existing Set` / `Edit Assigned Set`, `Set Keyframe for Vertex Color`, `Color Material Channel/*` 6, `Material Blend Setting/*` 7 |
| **Key / Control** | 54 % / 7 % | Character Set 계열 Key 9 + Control 10, `Scene Time Warp/*` 4 (+ Graph / Dope Sheet Edit 4씩), `IK/FK Keys/*` 4, `Set Blend Shape Target Weight Keys`. Time Slider 행의 `No Character Set` 칸은 여전히 비활성 라벨 (`ui/time_slider.py:146`, step 180에서 Anim Layer 칸만 살아남) |
| **Create** | 57 % | `Polygon Primitives/Pipe`, `Helix`, `Gear`, `Soccer Ball`, `Super Ellipse`, `Spherical Harmonics`, `Ultra Shape`, `Interactive Creation`, `Exit On Completion`, `Construction Plane`, `Lights/Ambient` / `Volume` |
| **Skin** | 68 % | `Move Weights to Influences`, `Normalize Weights/Enable Weight Post Normalization`, `Bake Deformation to Skin Weights`, `Move Skinned Joints`, `Substitute Geometry`, `Interactive Bind Skin` (+ Tool), Weight Maps 2 |
| **Constrain** | 55 % | `Normal`, `Tangent`, `UV Pin`, `Proximity Pin`, `Remove Target`, `Set Rest Position`, `Modify Constrained Axis...`, `Motion Paths/Flow Path Object`, `Set Motion Path Key` |
| **Curves** | 58 % | `Lock / Unlock Length`, `Bend`, `Curl`, `Scale Curvature`, `Duplicate Surface Curves`, `Align`, `Edit Curve Tool`, `Intersect`, `Fit B-spline`, `CV Hardness`, `Project Tangent`, `Extend / Offset Curve On Surface` |
| **Surfaces** | 37 % | 26 greyed (Trim / Untrim / Intersect / Project Curve / Extend / Offset / Round / Stitch / Sculpt Geometry 등 — 4.5 NURBS에 trim·custom knot 없음, CLAUDE.md step 181); 박스 37 중 22 dead, 4 generic |
| **Deform** | 65 % | `Tension`, `Solidify`, `Morph`, `Wrinkle`, `Jiggle` 3, `Sculpt`, `Pose Space Deformation/Create Pose Interpolator`, `Blend Shape#2/Swap`, `Edit Membership Tool`, `Display / Hide Intermediate Objects`, `Wire#2/Add Holder` |
| **Modify** | 63 % | `Transformation Tools/Type Manipulator`, `Paint Attributes Tool`, `Paint Scripts Tool`, Asset 15, Convert 12 |
| Generate / nHair / nConstraint / Toon | 0–5 % | Blender 대응 없는 시스템 전체 — notice만 |

Lighting/Shading (36 → 93 %)는 이 표에서 내려왔다.

### 1c. Editor menu bars

| Editor | Leaves | Working 173 → now | Greyed + notice | Most-greyed menus now |
|---|---|---|---|---|
| Graph Editor | 229 | 154 (67 %) | 75 | View 20 / 40, Show 18 / 34, Curves 16 / 39, Edit 10 / 23, List 6 / 8 |
| Dope Sheet | 181 | 130 (72 %) | 51 | Show 18 / 34, Curves 12 / 34, Edit 10 / 23, List 6 / 7 |
| UV Editor | 172 | 118 → **136 (79 %)** | 36 | Image 8 / 14, UV Sets 7 / 11, View 7 / 20, Tools 4 / 19, Cut/Sew 3 / 9, Modify 3 / 31 |
| UV Toolkit | 3 | 1 | 2 | |
| Hypershade | 249 | 115 (46 %) | 134 | Create 91 / 160, Edit 20 / 30, Tabs 6 / 6, Options 6 / 6 |
| Render Settings | 21 | 10 | 11 | Presets 9 / 10 |
| Script Editor | 59 | 32 | 27 | **History 13 / 13** (여섯 번째 감사 연속 0 %) |

새로 working (+18, 모두 UV Editor, step 178): `Edit/Unpin All`; `Modify/Distribute UVs`, `Layout Along`, `Map Border`, `Match Grid`,
`Stack Similar Shells`, `Straighten Border`; `Select/Back-Facing`, `Front-Facing`, `Non-Overlapping`, `Texture Borders`, `Unmapped Faces`,
`Convert Selection/To Connected Faces`, `Filter Selection/Connected Faces`, `Contained Faces`; `View/Isolate Select/Add Selected`,
`Remove Selected`, `Remove All`.

UV Editor에 남은 Maya 사용자가 매주 누르는 것: `Cut/Sew/Auto Seams` (+ 마킹 메뉴 2개), `Split`, `Create Shell (Grid)`, `Modify/Symmetrize`,
`Tools/Symmetrize`, `Smudge`, `Smear`, `Lattice`, `UV Sets/Rename Current UV Set...`, `Copy UVs to UV Set/map1`, `View/Isolate Select/Load Set`,
`View/Heads-Up Display/UV Statistics` / `UV Position`.

Graph Editor 그대로 (세 번째 연속): `View/Show Buffer Curves` + `Curves/Buffer Curve/*`, Weighted / Non-weighted Tangents 4,
`Lock / Free Tangent Length`, `Edit/Retime Tool`, `Region Keys Tool`, `Lattice Deform Keys Tool`, `Keys/Add Key Tool`, `List/Load / Add Selected Objects`,
`Show/Attributes/*` 6.

### 1d. Panel menus / panel toolbar / Status Line (step 177에서 처음 세는 항목, 새 기준선)

Panel menus 111 leaf 중 greyed 44: View 4 (`View Sequence Time`, Camera Tools 3), Shading 9 (`Flat Shade All`, `Flat / Smooth Shade Selected
Items`, `Bounding Box`, `Points`, `X-Ray Active Components`, `Interactive Shading`, `Smooth Wireframe`, `Hardware Fog`), Lighting 3, **Show 20**
(`IK Handles`, `NURBS CVs`, `NURBS Hulls`, `Image Planes`, `Dynamics`, `nCloths`, `nParticles` …), Renderer 2, Panels 5. Panel toolbar greyed 7
(`Bookmarks`, `2D Pan/Zoom`, `Resolution Gate`, `Field Chart`, `Motion Blur`, `Multisample Anti-aliasing`, `X-Ray Active Components`).
Status Line greys 9 (`Select by hierarchy`, `… handle / dynamic object type`, `Snap to projected center`, `Snap to view planes`,
**`Construction History`**, `Render Setup`, `Pause Viewport 2.0`, `Show or hide the Character Controls`).

모순: kit에 IK handle (step 58, IK target empty), NURBS surface (step 181), image plane (`create.KINDS`)이 있는데 `Show/IK Handles`,
`NURBS CVs`, `NURBS Hulls`, `Image Planes` 표시 토글은 greyed.

## 2. Option boxes per top menu (507 paths)

window = kit Maya option window, dialog = operator / file dialog, tool = tool + Tool Settings, redo = run + Adjust Last Operation,
generic = "Blender has no settings for this" 창, dead = greyed 항목의 박스. 바뀐 칸만 [step 173 값]; 나머지 줄은 step 173 §2와 같다.

| Menu | window | dialog | tool | redo | generic | dead |
|---|---|---|---|---|---|---|
| Surfaces | **10** [0] | – | – | **1** [3] | **4** [5] | **22** [29] |
| (그 밖의 메뉴 전부) | step 173과 같음 | | | | | |

경로 diff (12개): dead → window 6 (`Surfaces/Attach`, `Birail/Birail 1 Tool`, `Boundary`, `Detach`, `Rebuild`, `Square`); generic → window 3
(`Loft`, `Extrude`, `Reverse Direction`); redo → window 1 (`Revolve`); **dead → generic 1** (`Duplicate NURBS Patch`); **redo → generic 1**
(`Surfaces/Insert Isoparms` — 이제 kit `allset.surface_insert_isoparm` (`operators/surfaces_maya.py:504`)인데 보이는 속성이 없어 "Blender has no
settings" 창이 뜬다; Maya에는 Insert location / # isoparms 옵션 창. 이번 기간의 유일한 역행).

generic 35개 중 Maya 사용자가 매일 쓰는 박스 (step 173에서 그대로): `Curves/Cut`, `Detach`, `Smooth` ×2, `Reverse Direction`, `Straighten`,
`Create/Curve Tools/Three / Two Point Circular Arc`, `Pencil Curve Tool`, `UV/Merge UVs`, `Contour Stretch`, `3D Cut and Sew UV Tool`,
`Skeleton/Set / Assume Preferred Angle`, `Skin/Edit Influences/Add Influence`. 매주: `Surfaces/Planar`, `Bevel Plus`, `Insert Isoparms`,
`Duplicate NURBS Patch`, `nCloth/Create nCloth / Create Passive Collider`, `nParticles/Create Emitter` ×2 / `Emit from Object` ×2 / `Make Collide`,
`Fluids/Make Collide`, `Modify/Bake Pivot`, `Mesh Display/Paint Vertex Color Tool`, `Texturing/3D Paint Tool`, `File/Archive Scene`,
`Control / Key/Create Character Set`. `Render/Render Current Frame` / `IPR`는 Maya와 같은 경고지만 분류기는 generic으로 센다.

dead 207개를 메뉴별로 많은 순: Surfaces 22, Fluids 16, Modify 16, Create 14, Deform 12, Curves 11, nHair 11, nConstraint 11, nCache 9,
Generate 8, nParticles 8, Cache 7, Constrain 7, Mesh Tools 7, Fields/Solvers 6, Effects 6, Skin 5.

박스를 여는 방법: 여전히 plain click = 명령, 창은 0.2 s hold (`ui/menu_sets.py:261` `operator_menu_hold`, `:823` / `:855` `from_hold`;
b07f9a7 이후 이 파일 변경은 `_dynamic_label` (Edit > Repeat 라벨)뿐). ❒ 부분 클릭으로 창이 열리지 않는다 (#82). 여섯 번째 감사 연속.

## 3. Shelves (`ui/shelf.all_buttons`)

203 buttons, **159 working (78 %)** [155], 44 greyed with a notice [48], 0 without. 바뀐 탭: Curves / Surfaces 26 → **30 / 38**
(`Attach Surfaces`, `Detach Surfaces`, `Rebuild Surfaces`, `Birail 1 Tool`). 나머지 탭 같음: Poly Modeling 41 / 43, Sculpting 19 / 26,
Rigging 17 / 18, Animation 14 / 14, Rendering 21 / 25, FX 13 / 29, FX Caching 4 / 10. 남은 greyed: Curves / Surfaces 8 (Curve Editing Tool,
Project Curve on Surface, Intersect / Trim / Untrim / Extend Surfaces, Sculpt Geometry Tool, Surface Editing Tool), FX 16, FX Caching 6,
Sculpting 7, Rendering 4, Poly Modeling 2 (Super Shape, 3D Grab UV Tool), Rigging 1 (Human IK).

## 4. Hotkeys / marking menus

Hotkeys (468 rows, `tmp/audit182b/keymap_mapping.md` = 체크인된 `docs/keymap_mapping.md`): 구현 **210**, IC 일치 **26**, 해당 없음 164,
미검토 0, macOS 전용 68. 바뀐 줄: `g` global RepeatLast (IC `screen.repeat_last` → kit `allset.repeat_last`, step 175); g가 걸린 Time Editor
2행 / Graph Editor 1행의 현재 바인딩 텍스트만 바뀜. 164 n/a의 큰 덩어리: Hypershade / Node Editor 57행, Time Editor 32행 (그대로).
메뉴 hotkey 글자: 메인 57 (`ui/menu_hotkeys.HOTKEYS`, 바뀌지 않음), 에디터 메뉴바 0.

Marking menus: 474 entries, 368 working (298 direct + 70 `item`), 65 greyed (55 + 빈 submenu 10), 41 submenus — **세 번째 감사 연속 변화 0**.
greyed 55 분포 (step 173과 같음): Shift+Q `doSelectComponentMM` 25, `translateMarkingMenuImpl` 4, `buildSelectAllMM` 4, `dagMenuProc_curve` 3,
`contextPolyToolsDefaultMM` 3, rotate 2, hotbox east / west 2 + 2, 나머지 1씩 (UV `Auto Seams` 2, radial `Vertex Face` 포함).
step 181 NURBS surface가 들어왔지만 `dagMenuProc_curve`류 외에 NURBS surface RMB 메뉴 (Isoparm / Surface Point / Surface Patch / Hull) 없음 —
마킹 메뉴 목록에 surface proc 0.

## 5. look_compare

### 5a. 실효 UI 배율 1.0 (`compare_audit182_s100/`, 15 side-by-side, 6 crops)

- checks 9/9; pixels kit-drawn **6/6** (theme 31, 20 > 5 not counted, 1 no kit element, 0 anchors missing); viewport **12/12** [11/12];
  rects **5/12**; scene 3/3; density 5/6 (menu bar 26.0/27, item pitch 20.1/20, CB row 16.1/16, **menu top − bar bottom −6.0/0**,
  shelf 64/64, icon 32/32); grid ok (ΔE00 0.7, corners 4/4, 0.200 ms); furniture 2/3.
- step 173 대비: pixels / rects / density / scene / furniture.md **바이트 단위로 같음**; viewport.md 2줄만 다름 —
  selected face fill: raw kit mean #ad8e6e → **#8d8177**, ΔE **40.5 ✗ → 2.3 ✓** (step 176); 보라 정점 샘플 위치 1줄 (값 같음).
- theme ✗ 20개: step 173 §5a 값 그대로 (메뉴바 #181818 vs #444444 14.0, 팝업 18.7, 에디터 틈 22.8, Outliner 선택 행 21.0, frame 칸 13.5,
  Help Line 14.0, Tool Box 활성 9.1, Layer 탭 9.7, 결과 칸 5.0, 나머지 5.6–6.5). step 130 결정상 kit가 고칠 수 없음.
- rects ✗ 7개 (값 그대로): Tool Box / Outliner / viewport / dock가 Maya보다 37 px 높고 10 px 위에서 시작 (Outliner −27 px), Tool Box 56 vs 40 폭,
  dock 287 vs 260 폭, Time Slider 1300 vs 1596 폭 (Δy +24), Range Slider 높이 26 vs 31.

### 5b. 실효 UI 배율 1.25 (`compare_audit182_s125/`)

- checks 9/9, kit-drawn 6/6, viewport **12/12**, rects 5/12, scene 3/3, density 5/6 (**menu top − bar bottom −10.4 px**), grid ok
  (0.191 ms), furniture 2/3. pixels / rects / density / scene / furniture.md는 step 173과 바이트 단위로 같다.
- rects ✗: Shelf 높이 80 vs 64, Tool Box 폭 70 vs 40, Outliner 폭 325 vs 260, **메인 뷰포트 폭 850 vs 1003 (−153 px)**, dock 346 vs 260 (+86),
  Time Slider 폭 1225 vs 1596 (−371 px). 이미지 01 (1.25): Poly Modeling 선반 아이콘이 약 27개만 보이고 나머지는 overflow 줄로 (Maya 1.0 샷은
  한 줄에 약 40개), panel toolbar 끝이 `»`로 접힘, Time Slider 눈금 숫자가 10 간격.

### 5c. 이미지에서 보이는 차이 (왼쪽 Maya, 오른쪽 kit; 차이만, 직접 봄)

step 173 §5c 대비 해결된 것: **#1 컴포넌트 모드 도구** — 07 / 08 / 09 모두 kit 편집 모드에 Move manipulator가 있고 08 / 09 Help Line은
"Move Tool: drag the manipulator…" (step 174). **#2 선택 면 채우기** — 07 확대 (`tmp/audit182b/crop07_kit.png`) kit 면이 주황 stipple만,
불투명 채우기 없음 (step 176). 남은 / 새로 본 차이:

1. **RMB 리스트 위치** (`14`): 변화 없음. Maya = 링 바로 아래 한 열, 창 아래로 넘쳐 잘림 (Time Editor 행까지 보임). kit = 링 왼쪽 옆,
   위로 링 위 (pCube1... 행이 Edge 박스보다 위)까지. 회색: kit `Metadata`, `Time Editor`, radial `Vertex Face` (Maya는 활성). 링 가운데 원형 커서는
   Maya에 없음.
2. **Move manipulator** (`02`, `07`, `09`): Maya는 축 사이 평면 사각형 3개가 크고 진하며 (빨강 / 파랑 / 초록) 가운데 상자가 노란색; kit는 평면
   사각형이 작고 흐리며 가운데 상자가 흰색. 축 색 배치: Maya 위 = 초록 (Y-up), kit 위 = 파랑 (Blender Z-up — 구조적, 고칠 대상 아님).
3. **선택 엣지가 거의 안 보임** (`09`, 확대 `tmp/audit182b/crop09_kit.png` / `crop09_maya.png`): Maya는 얇은 하늘색 와이어 위에 선택 엣지
   e[0] / e[5]가 주황으로 또렷. kit는 하늘색 와이어 (#64dcff)가 두껍고, 선택 엣지는 아래 앞 모서리에 가는 주황 테두리로만 겹쳐 보인다 —
   viewport.md는 엣지 색만 샘플하고 두께·가시성은 재지 않는다. 새로 찾은 차이.
4. **Channel Box 모양** (`crop_channel_box`): Maya는 `pCube1Shape` 행과 SHAPES / INPUTS 아래에 어두운 행 바탕 + 굵은 머리글, 위 오른쪽에 세 아이콘
   (CB / LE 표시 전환), 아래 가로 스크롤바; kit는 행 바탕 없음, 머리글 굵기 없음, 맨 위 `::::::` tear-off 손잡이, 라벨 열이 오른쪽으로 더 들어가 있음.
   Layer Editor `Display` / `Anim` 탭이 kit는 파란 알약 버튼 (Maya: 회색 탭), Layer 아이콘 4개 중 2개가 흐림.
5. **컴포넌트 CB의 CVs 줄** (`07`, `09`): kit는 vertex 모드 (`08`)에서만 `CVs (click to show)`를 보여 주고 face (`07`) / edge (`09`) 모드에서는
   shape 이름 + INPUTS만. Maya `09`는 edge 선택에서도 `CVs (click to show)` 줄이 있다 — 단, Maya CB는 idle 갱신으로 이전 (vertex) 상태를 보여 줄 수
   있어 (step 165 메모) 확정 아님 (§8).
6. **Four view** (`16`): kit 네 칸 위에 panel menu + toolbar 한 벌 (Maya: 칸마다); ViewCube가 kit front 칸 (작은 "FRONT") / Maya top 칸 ("TOP");
   kit 직교 칸의 큐브가 Maya의 약 4배 (표시 px 38 vs 9; Maya = 칸 폭에 약 30 unit) — 그러나 샷 스크립트가 `screen.region_quadview`를 직접 부른다
   (`tools/look_shots.py:604-605`), kit의 Maya 직교 칸 설정 (`operators/view.py:634` `maya_ortho_panes`, `:659-672`)을 거치지 않으므로 kit 경로의
   차이인지 샷 차이인지는 이 이미지로 판단 불가 (§8). 라벨 `top -Y` / `front -Z` / `side -X`는 이제 Maya와 같음 (step 176). 샷 장면 차이 (kit pCube1
   선택 + manipulator, Maya 선택 없음).
7. **Create 메뉴** (`12`): 메뉴가 메뉴바와 6 px (1.25: 10.4 px) 겹침; 첫 줄 tear-off 점선 (Maya: "Objects" 섹션 라벨); 밑줄 니모닉; Maya 2022 샷에 없는
   `Subdiv Primitives`; `Adobe(R) Illustrator(R) Object...`, `Construction Plane`, `Scene Assembly` 회색; Maya의 `Sweep Mesh` / `USD` 녹색 What's New 표시 없음.
8. **Outliner** (`crop_outliner`): 순서 pCube1–3 → persp/top/front/side (Maya: 카메라 먼저); 주황 삼각 메시 아이콘 (Maya: 회색 transform 마름모);
   선택 행 주황 글자 + 남색 (Maya 흰 글자 + 하늘색); 줄무늬 행; 스크롤바 없음; 검색 칸이 메뉴 줄 오른쪽 작은 칸 (Maya: 메뉴 아래 전체 폭 줄);
   kit 맨 위 `::::::` 손잡이.
9. **Time Slider** (`crop_time_slider`): 변화 없음 — kit 숫자가 크고 5 프레임마다, 프레임마다의 짧은 틱 없음; 현재 프레임 = 파란 말풍선
   (Maya: 회색 박스 + 세로선); 120 이후 붉은 영역; 현재 프레임 칸 + 재생 버튼이 오른쪽 별도 area (rect Δw −296).
10. **Hotbox** (`13`): 행 간격은 Maya와 같은 약 22 px (표시 기준)이지만 kit 버튼 바탕이 거의 안 보임 (Maya: 회색 상자 뚜렷); 가운데 제목
    "Maya Workflow Kit" (Maya "Maya"); Maya의 `MASH` (플러그인) 줄 없음 — 정상.
11. **Status Line** (`crop_status_line`): undo / redo 회색; 선택 마스크 그룹 첫 세 아이콘 (hierarchy / handle / dynamic)과 snap 두 아이콘 회색
    (§1d Status Line greys 9); `Construction History` 아이콘 회색; Maya 계정 칸 (Modak Games Inc) 없음 — 정상. 아래 줄: Command Line 라벨 `Python`
    (Maya `MEL`), 상단 바 오른쪽 Maya / Blender 스위치, Workspace "Maya Classic" (Maya 샷 "General*").

## 6. Domain 차이 (시나리오별, 증거)

| Domain | Maya가 아니라고 느껴지는 곳 (큰 것부터) | 증거 |
|---|---|---|
| Modeling | 옵션 박스 click (#82); 선택 엣지 안 보임 (09); manipulator 평면 핸들; Mesh Display 38 % (vertex normal / color set); Pipe / Helix / Gear 등 7 primitive; Show NURBS CVs / Hulls 회색 | §2, §5c-2/3, §1b, §1d |
| Surfaces | 37 % (Trim / Untrim / Intersect / Project 없음 — 4.5 한계); `Insert Isoparms` 박스가 generic으로 역행; NURBS surface RMB 마킹 메뉴 없음 | §1a, §2, §4 |
| UV | UV Editor 79 %: `Auto Seams` (+ 마킹 2), `Split`, `Symmetrize` ×2, `Smudge` / `Smear` / `Lattice`, UV Set Rename / Copy, Isolate `Load Set`; `3D Grab UV Tool` 선반 | §1c, §3 |
| Animation | Character Set 19 leaf + Time Slider `No Character Set` 칸 비활성; Scene Time Warp 12 leaf; Graph Editor View 20 / Show 18 greyed (buffer curves, weighted tangents); Time Slider 눈금 / playhead | §1b, §1c, §5c-9 |
| Rigging | Constrain 55 %, Skin 68 %, Control 7 %; Show `IK Handles` 토글 회색인데 kit IK handle 존재 | §1b, §1d |
| FX | 18 %, **여섯 번째 연속 불변** (nParticles Create Options / Goal / Instancer, Fields/Solvers Initial State, nConstraint 0 %, nHair 4 %) | §1a, §3 |
| Rendering | Light Linking 해결 (93 %); Texturing 12 %, Hypershade Create 91 greyed, Render Settings Presets 9 / 10, `Render Current Frame` 박스 generic | §1a, §1c |
| File I/O | 메뉴 80 % 불변: `ATOM/*` 3, `Export / Assign Offline File` 2, After Effects Live Link; Cache 46 %; `Archive Scene` 박스 generic. 왕복 정확도는 `research/maya/re/file_io.md` 기록을 믿음 — 이번 lane은 재실행 안 함 | §1a, §2 |
| 공통 UI | 테마 색 20개 (step 130 결정상 불가), Outliner 순서 / 아이콘 (C Outliner 한계), 메뉴 6 px 겹침, CB 행 바탕 / 머리글, 에디터 메뉴 hotkey 글자 0, Script Editor History 0 / 13 | §5a, §5c-4, §4 |

## 7. Ranked remaining differences and one-step backlog

점수 = 심각도 (1–5) × 빈도 (1–5). step 173 #1 (도구), #4 (면 채우기), #7 (Light Linking)은 해결되어 빠짐; #6 (UV Editor)은 대부분 해결.

| # | 차이 | S × F | 점수 | step 173 순위 |
|---|---|---|---|---|
| 1 | 옵션 박스 ❒ 클릭 = 명령 (창은 0.2 s hold, #82) | 4 × 4 | 16 | #2 |
| 2 | RMB 리스트가 링 옆 / 위로 (Maya: 아래로, 창 밖으로 잘림) | 3 × 5 | 15 | #3 |
| 3 | 선택 엣지가 두꺼운 하늘색 와이어에 묻혀 안 보임 | 3 × 4 | 12 | 새로 |
| 4 | Time Slider 눈금 / 현재 프레임 표시 | 2 × 5 | 10 | #5 |
| 5 | Character Set 계열 19 leaf + Time Slider 칸 비활성 | 3 × 3 | 9 | #8 |
| 6 | Mesh Display 38 % (vertex normal, color set) | 3 × 3 | 9 | #9 |
| 7 | Move manipulator 평면 핸들 작음 / 가운데 상자 흰색 | 2 × 4 | 8 | #11 (승격) |
| 8 | Channel Box 행 바탕·머리글·CB/LE 아이콘, Layer 탭 모양 | 2 × 4 | 8 | 새로 |
| 9 | Polygon Primitives 7종 (Pipe, Helix, Gear …) | 2 × 3 | 6 | #10 |
| 10 | Panel Show 토글 `IK Handles` / `NURBS CVs` / `NURBS Hulls` / `Image Planes` 회색 (kit에 그 노드가 있음) + Status Line `Construction History` | 2 × 3 | 6 | 새로 |
| 11 | FX 18 % 불변 | 3 × 2 | 6 | #12 |
| 12 | `Surfaces/Insert Isoparms` 박스 redo → generic 역행 | 2 × 1 | 2 | 새로 |

1. **옵션 박스 ❒ 클릭 (#82)** — 지시: ❒ 마크가 그려지는 행 오른쪽 끝 폭을 정해 두고, `allset.cb_hover`처럼 첫 자리 MOUSEMOVE PASS_THROUGH
   연산자가 메뉴 행 위의 마우스 x를 기록 → `allset.menu_item.execute`에서 그 x가 ❒ 폭 안이면 옵션 창. 메뉴 popup 안에서 keymap이 MOUSEMOVE를
   못 받는다고 측정되면 그 측정을 `docs/steps/`에 남기고 hold 유지 + 툴팁 안내. 검증: GUI — ❒ 위 클릭 = 창, 라벨 클릭 = 명령.
2. **RMB 리스트 아래로** — 지시: `marking/engine.py` `fit_ring`의 리스트 배치에서 링 아래에 행 1개 이상 들어가면 아래에 두고 넘치는 행은 Maya처럼
   잘리게; 옆 배치는 아래 공간이 0일 때만 (step 161 판단을 사용자에게 확인 후). 검증: `gui_step52_hotbox_rmb` "list is under the ring",
   look_compare 14.
3. **선택 엣지 보이게** — 지시: `ui/component_colors.py` POST_VIEW 엣지 그리기에서 비선택 엣지 폭을 Maya 1 px, 선택 엣지 (#e3ac79)를 2 px로 비선택
   위에 (depth bias 더 크게) 그리기; 09 샷에서 선택 엣지 중점 샘플을 `look_data.VIEW_SAMPLES`에 추가. 검증: look_compare viewport에 "selected edge"
   행 ✓, 09 확대에서 e[0] / e[5]가 주황으로 보임.
4. **Time Slider 모양** — 지시: Dope Sheet WINDOW POST_PIXEL (`ui/time_slider.py`)에 프레임마다 짧은 틱 + 회색 현재 프레임 박스 / 세로선, 숫자는
   Maya 간격으로 (Blender 숫자 덮기는 측정 필요). 검증: `crop_time_slider` 나란히, look_compare에 time-slider 샘플점.
5. **Character Set** — 지시: Character Set = 이름 붙은 Keying Set (`allset_character` 표시), Create (옵션 창 Name / Attributes / Hierarchy),
   Add / Remove / Merge / Select Members / Set Current, Time Slider 칸을 `anim_layers`처럼 현재 set 드롭다운으로; 키 명령이 현재 set 채널 전부 키.
   검증: Key ≥ 70 %, Control ≥ 50 %, generic 2 → 0.
6. **Mesh Display** — 지시: `Set Vertex Normal` (custom split normals, Maya 옵션 창), `Apply Color`, 컬러 세트 Rename / Modify / Assign New / Assign
   Existing / Edit Assigned, `Set Keyframe for Vertex Color`; mayapy 대조. 검증: Mesh Display ≥ 60 %, normal 값 1e-4.
7. **Manipulator 평면 핸들** — 지시: `ui/manipulator.py` (ALLSET_GGT_xform)의 평면 핸들 크기 / 위치 / 불투명도를 `research/maya/screens/` 02 샷
   측정값으로, 가운데 상자 노랑 (Maya 활성 색). 검증: look_compare 02에 평면 핸들 픽셀 샘플 3개 ΔE < 5, 위치 ±3 px.
8. **Channel Box 모양** — 지시: dock CB 부분 (`channel_box.py` `Lines`)에 shape / SHAPES / INPUTS 행 바탕 (Maya 측정 색)과 머리글 굵게 (kit 그리기가
   가능한 범위; 불가면 측정 기록), Layer Editor 탭을 Maya 회색 탭 모양으로. 검증: `crop_channel_box` 나란히, pixels.md에 CB 행 바탕 샘플 추가.
9. **Polygon Primitives 7종** — 지시: `operators/prim_history.py` 방식으로 Pipe / Helix / Gear / Soccer Ball / Super Ellipse 등, Maya 기본값·면 순서
   mayapy 측정, `create.KINDS` 경유. 검증: Create ≥ 70 %, 정점 1e-4.
10. **Panel Show 토글 / Construction History** — 지시: `ui/panel_menu_data.py`의 `Show/IK Handles` (IK target empty 표시), `NURBS CVs` / `NURBS Hulls`
    (SURFACE 편집 overlay), `Image Planes` (kit image plane 오브젝트 표시)를 오브젝트 종류별 뷰 숨김으로 연결; Status Line `Construction History`는
    측정 후 notice 유지 또는 kit record 끄기. 검증: `menu_count.py` Panel menus ≥ 64 %, headless 테스트.
11. **FX** — 지시: `nParticles/Create Options/*` 5 (표시 preset), `Fields/Solvers/Initial State/*`, `Instancer`. 검증: FX ≥ 25 %.
12. **Insert Isoparms 옵션 창** — 지시: `option_windows`에 Maya Insert Isoparms 창 (Insert location At selection / Between selections, # isoparms,
    Keep original) 추가하고 `allset.surface_insert_isoparm`에 연결. 검증: option_count에서 generic 35 → 34, window +1.

뒤로 미룸 (점수 ≤ 5): 에디터 메뉴 hotkey 글자 (2 × 2), Script Editor History 13 (1 × 2), Hypershade Create 91 (2 × 2), Outliner 검색 줄 / 스크롤바
(1 × 4), 메뉴 6 px 겹침 (1 × 4), NURBS surface RMB 마킹 메뉴 (2 × 1), 테마 색 20개 / Outliner 아이콘·순서 (결정상 / C 한계로 불가 — 고치지 말 것).
도구 쪽 후속: `tools/look_shots.py` 16 샷이 kit four-view 경로 (`operators/view.py` 토글)를 쓰도록 바꿔야 직교 배율을 잴 수 있다.

## 8. Not measured / counterevidence

- Maya와 나란히 하는 실제 시나리오 실행 (파일 입출력, 모델링, UV, 애니, 리깅, FX, 렌더): 이 lane은 수치 재계산, look_compare, 코드 / notice 읽기만.
  Maya 이미지는 기존 `research/maya/screens/*` 그대로 (새 Maya 캡처 없음).
- 옵션 박스 열기 (#82), RMB 리스트, Time Slider는 코드 경로와 기존 샷으로만 확인; GUI 키 조작으로 다시 재지 않았다.
- `07` kit Help Line이 "Select Tool: click or drag to select…"인데 같은 샷에 Move manipulator가 있고 08 / 09는 "Move Tool" — step 174의 도구 이전이
  0 s 타이머라 샷 (한 틱 뒤)과 Help Line 갱신이 엇갈린 것으로 보인다; 실제 사용에서 Help Line이 늦는지는 재지 않았다.
- `09` Maya CB의 `CVs (click to show)` 줄은 Maya idle 갱신 지연일 수 있음 (step 165) — §5c-5는 확정 아님.
- `16` 직교 배율 4배는 샷 스크립트가 kit 경로를 우회한 결과일 가능성 (§5c-6) — kit 결함으로 세지 않음.
- 선택 엣지 가시성 (§5c-3)은 이미지 확대로만 봄; look_compare에 엣지 폭 / 선택 엣지 색 샘플이 없다.
- 1.25 배율 Maya 기준 이미지 없음 (Maya 샷은 Qt 논리 px) — 1.25 rect 차이는 과대평가일 수 있다.
- 서로 다른 옵션 창 119개는 프로브 기준; 창마다 필드가 Maya와 같은지는 보지 않았다.
- step 180 애니 레이어 (Layer Editor Anim 탭)와 step 175 G 반복은 계수기 밖 — 기능 정확도는 각 step 테스트를 믿었다.
- 수동 점검 개수는 작업 사본 기준 (다른 lane이 동시에 `docs/manual_checks.md`를 고칠 수 있음).
