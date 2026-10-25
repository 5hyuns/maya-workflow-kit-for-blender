# Step 192 부록 — 재점검 14차 수치 감사 (lane B, paper + look_compare)

Step 182 부록 (`docs/steps/step_182_quant.md`)의 수치를 오늘 master에서 같은 방법으로 다시 셌다. 칭찬은 빼고 차이만 적는다.
기준: 「기본 Maya에 Blender 기능이 붙은 모습」. 읽기 전용 감사, 2026-10-25, HEAD 13d2153 (0.4.1 = steps 183–190 + release fix).
확장 zip `dist/maya-workflow-kit-0.4.1.zip` (16:02 빌드, HEAD 커밋 15:58 이후) — 파일 234개를 `src/allset`과 바이트 비교해 차이 0,
src에만 있는 파일 0 (`tmp/audit192b/zipcmp.py`) → HEAD와 같다. 재빌드 안 함 (메인 세션이 `dist/`를 쓴다). 스크립트와 원자료는 `tmp/audit192b/`.
step 182 기준선 = `git archive 326f12f src tools` → `tmp/audit192b/old/` + step 182 원자료 (`tmp/q182/results/option_kinds.json`,
`tmp/audit182b/probe182.json`, `tmp/audit182b/keymap_mapping.md`, `research/maya/screens/compare_audit182_s100/`, `_s125/`).

방법 (step 182와 같음, 경로만 바꿈; 판단은 모두 `delegated`):

- 메뉴: `python tools/menu_count.py` (→ `tmp/audit192b/menu_count.txt`), 메뉴별 표 `tmp/audit192b/menus_per.py <root>` (326f12f / HEAD,
  경로 단위 diff), 에디터 메뉴바 `tmp/audit192b/ed_diff.py <root>`, panel menu / toolbar / Status Line `tmp/audit192b/panel_diff.py`.
- 옵션 박스: `ALLSET_SANDBOX=q192 python tests/run.py --no-build -k step140_option_count` (1 passed) → `tmp/q192/results/option_kinds.json`.
  `menu_count.py --options`는 빌드를 다시 하므로 쓰지 않았다.
- 선반 / 서로 다른 옵션 창 / 마킹 메뉴: `tmp/audit192b/run_probe.sh` + `probe_quant.py`, 샌드박스 `tmp/audit192b/sandbox` (폴더 먼저 생성,
  `--factory-startup`, `BLENDER_USER_*` 모두 tmp 안) → `tmp/audit192b/probe192.json`; 마킹 분류 `tmp/audit192b/marking.py`.
- 단축키: `tools/gen_keymap_mapping.py` 사본 (`tmp/audit192b/gen_keymap_tmp.py`, 출력 `tmp/audit192b/keymap_mapping.md`, exit 0) —
  체크인된 `docs/keymap_mapping.md`와 같고 step 182 출력과도 같다 (diff 0).
- look_compare: (a) `ALLSET_GUI_UI_SCALE=0.8 ALLSET_LOOK_TAG=audit192_s100 python tmp/audit192b/look_nobuild.py` (실효 1.0) →
  `research/maya/screens/compare_audit192_s100/`; (b) `ALLSET_LOOK_TAG=audit192_s125` (실효 1.25) → `compare_audit192_s125/`.
  샌드박스 `tmp/look_env_audit192_s100` / `_s125`. 각 md를 step 182 폴더와 diff, 이미지는 직접 봄.
- 수동 점검: `docs/manual_checks.md` (작업 사본)의 `- [ ]` / `- [x]` 개수.

## 0. Headline (step 182 → now)

| Metric | Step 182 (326f12f) | Now (13d2153) | Δ |
|---|---|---|---|
| Unique kit menu leaves (main menu sets) | 1318 | 1318 | 0 |
| ... working (mapped, incl. with notice) | 714 (54.2 %) | **750 (56.9 %)** = 652 + 98 with a notice | **+36** |
| ... greyed with a notice / without | 604 / 0 | 568 / 0 | −36 / 0 |
| Leaves counted per set | 1486, working 821 (55.2 %) | 1486, working **857 (57.7 %)** | +36 |
| `menu_map.MAP` / `notices.NOTICES` / `CATEGORIES` | 1292 / 176 / 171 | 1328 / 173 / 170 | +36 / −3 / −1 |
| Editor menu bars (7 editors, 914 leaves) | 578 (63 %) | 578 (63 %) — 경로 diff 0 | **0** |
| Panel menus / panel toolbar / Status Line greys | 67 / 111, 22 / 29, 9 leaves | **69** / 111, 22 / 29, **8** leaves | +2 (`Show/IK Handles`, `Show/Image Planes`), Construction History 회색 해제 |
| Option-box paths (`OPTION_BOXES`) | 507 | 507 | 0 |
| ... kit Maya option window | 114 paths (105 specs) | **120 paths (111 specs)** | +6 / +6 |
| ... distinct real windows / dialogs | 119 | **125** | +6 (Mesh Display 5, Insert Isoparms) |
| ... operator dialog / tool / redo / menu | 22 / 10 / 118 / 1 | 22 / 10 / **127** / 1 | redo +9 (primitives 7, Create Character Set 2) |
| ... "Blender has no settings" (`option_generic`) | 35 | **34** | −1 (Insert Isoparms → window; Create Character Set ×2 → redo; nHair Smooth / Straighten dead → generic) |
| ... dead (box on a greyed item) | 207 (41 %) | **193 (38 %)** | −14 |
| How a box opens (#82) | click = command; window by 0.2 s hold | **Maya 메뉴바에서 연 메뉴: ❒ 클릭 = 창** (step 183, `ui/option_click.py`); 그 밖 (hotbox / 마킹 / 선반 메뉴)은 hold 그대로 | 부분 해결 |
| Shelves (8 tabs, 203 buttons) | 159 / 44 + notice / 0 | **160** / 43 / 0 | +1 (Poly Modeling Super Shape) |
| Hotkeys (468 rows) 구현 / IC / 해당 없음 / 미검토 / macOS | 210 / 26 / 164 / 0 / 68 | 210 / 26 / 164 / 0 / 68 | 0 |
| Main-menu items with Maya hotkey text | 57; editor 0 | 57; editor 0 | 0 |
| Marking menus (26 menus, 474 entries) | 368 working (298 + 70 `item`), 55 greyed + 10 빈 submenu | **371** (301 + 70), **52** greyed | +3 (`contextPolyToolsDefaultMM` 3–5) |
| Manual checks (unticked / ticked) | 587 / 96 (326f12f: 586 / 96) | **598 / 107** | +11 / +11 |
| look_compare viewport (ΔE00 < 5), scale 1.0 | 12/12 | **20/20** (새 샘플 8: 선택 엣지, 엣지 와이어, flank, 가운데 상자 ×2, 평면 핸들 색 ×2 / 면적) | 표본 +8, 모두 ✓ |
| look_compare kit-drawn pixels / theme > 5 | 6/6 · 20 of 31 | **7/7** · 20 of 30 (`time_slider_bg` theme → kit, ΔE 1.6 → **0.0**) | +1 |
| look_compare rects / density / scene / grid / furniture / checks, 1.0 | 5/12 · 5/6 · 3/3 · ok · 2/3 · 9/9 | 동일 (rects / density / scene / furniture.md 바이트 단위로 같음) | 0 |
| look_compare at 1.25 | rects 5/12, viewport 12/12, density 5/6 (−10.4 px) | rects 5/12, viewport **20/20**, kit-drawn 7/7, density 5/6 (−10.4 px) | 표본 +8 |

읽기: steps 183–190 중 메뉴 계수기를 움직인 것은 **Character Sets (step 187: Key 54 → 73 %, Control 7 → 64 %)**, **Mesh Display (step 189:
38 → 64 %)**, **Polygon Primitives 7종 (step 190: Create 57 → 67 %)**, UV `Delete UVs` (89 %), nHair Modify Curves 2개 (twin)뿐. 183 (❒ 클릭),
184 (RMB 리스트), 185 (엣지·manipulator), 186 (Time Slider)은 계수기 밖 — look_compare viewport / pixels와 이미지로 확인 (§5). **에디터 메뉴바 7개는
두 번째 감사 연속 0 변화**, 단축키는 세 번째 연속 0 변화.

## 1. Menus per menu set

| Set | Leaves | Working 182 → now | Greyed + notice 182 → now | Greyed, no notice |
|---|---|---|---|---|
| Common | 449 | 291 → **298** (65 → 66 %) | 158 → 151 | 0 |
| Modeling | 349 | 192 → **203** (55 → 58 %) | 157 → 146 | 0 |
| Rigging | 190 | 130 → **138** (68 → 73 %) | 60 → 52 | 0 |
| Animation | 180 | 113 → **121** (63 → 67 %) | 67 → 59 | 0 |
| FX | 205 | 37 → **39** (18 → 19 %) | 168 → 166 | 0 |
| Rendering | 63 | 27 (43 %) | 36 | 0 |
| (always visible) Cache + Help | 50 | 31 (62 %) | 19 | 0 |

### 1a. Per top menu — 바뀐 줄만 (나머지는 step 182 §1a 값 그대로)

| Set | Menu | Leaves | % working 182 → now | Working (+ notice) | Greyed + notice | Option boxes |
|---|---|---|---|---|---|---|
| Common | **Create** | 70 | 57 → **67 %** | 39 + 8 | 23 | 44 |
| Common | Windows | 74 | 64 % | 39 + 8 (notice 1개 빠짐) | 27 | 1 |
| Modeling | **Mesh Display** | 39 | 38 → **64 %** | 25 + 0 | 14 | 10 |
| Modeling | UV | 19 | 84 → **89 %** | 17 + 0 | 2 | 11 |
| Rigging | **Control** | 14 | 7 → **64 %** | 9 + 0 | 5 | 3 |
| Animation | **Key** | 41 | 54 → **73 %** | 30 + 0 | 11 | 12 |
| FX | nHair | 54 | 4 → 7 % | 3 + 1 | 50 | 13 |

경로 diff (326f12f → 13d2153), **+36 working (greyed → working 33, notice 붙은 working → working 3), 잃은 것 없음**:

- Character Sets (step 187, Key / Control 각 8): `Add to / Remove from Character Set`, `Attribute Editor`, `Create Subcharacter Set`, `Merge Character
  Sets`, `Select Character Set Members` / `Node`, `Set Current Character Set`; `Create Character Set`은 notice가 빠짐.
- Polygon Primitives (step 190, 7): `Pipe`, `Helix`, `Gear`, `Soccer Ball`, `Super Ellipse`, `Spherical Harmonics`, `Ultra Shape`.
- Mesh Display (step 189, 10): `Set Vertex Normal`, `Apply Color`, `Prelight (Maya)`, `Rename Current Set...`, `Modify Current Set`, `Assign New / Existing
  Set`, `Edit Assigned Set`, `Set Keyframe for Vertex Color`, `Per Instance Sharing/Select Shared Instances`.
- 그 밖: `UV/Delete UVs`, `nHair/Modify Curves/Smooth` / `Straighten` (curve twin), `Windows/Relationship Editors/Animation Layers` notice 제거.

움직이지 않은 메뉴: **step 98 이후 일곱 번째 감사 연속**: nConstraint 0 %, nCache 15 %, Fields/Solvers 37 %, Effects 18 %, Texturing 12 %. step 133
이후 여섯 번 연속: Windows 64 %. step 145 이후 다섯 번 연속: Display, Generate 4 %, Toon, Stereo, Cache, nParticles / Fluids / nCloth. step 154 이후 네 번
연속: Mesh, Edit Mesh, Mesh Tools, Skin 68 %, Constrain 55 %, Playback, Audio, Render, File, Curves 58 %. step 163 이후 세 번: Select, Edit, Modify, Deform,
Visualize. step 182 이후 두 번: Surfaces 37 %, Lighting/Shading.

### 1b. Weakest menus by Maya-user impact (daily use × greyed share), 현재

| Menu | % working | 아직 greyed인, Maya 사용자가 매일·매주 누르는 항목 |
|---|---|---|
| **Skin** | 68 % (4번째 연속) | `Interactive Bind Skin` (+ Tool), `Move Weights to Influences`, `Normalize Weights/Enable Weight Post Normalization`, `Move Skinned Joints`, `Substitute Geometry`, `Bake Deformation to Skin Weights...`, Weight Maps 2 |
| **Constrain** | 55 % (4번째) | `Normal`, `Tangent`, `UV Pin`, `Proximity Pin`, `Remove Target`, `Set Rest Position`, `Modify Constrained Axis...`, `Motion Paths/Flow Path Object`, `Set Motion Path Key` |
| **Curves** | 58 % (4번째) | `Lock / Unlock Length`, `Bend`, `Curl`, `Scale Curvature`, `Duplicate Surface Curves`, `Align`, `Edit Curve Tool`, `Intersect`, `Fit B-spline`, `CV Hardness`, `Project Tangent`, `Extend / Offset Curve On Surface`, Bezier `Uneven Anchor Tangents` |
| **Create** | 67 % | `Polygon / NURBS Primitives/Interactive Creation` + `Exit On Completion` (4), `Lights/Ambient Light` / `Volume Light`, `Construction Plane`, `Measure Tools/Parameter / Arc Length Tool`, Subdiv / Volume Primitives 9 |
| **Key** | 73 % | `Scene Time Warp/*` 4 (+ Graph / Dope Sheet Edit), `IK/FK Keys/*` 4, `Set Blend Shape Target Weight Keys` |
| **Mesh Display** | 64 % | `Color Material Channel/*` 6, `Material Blend Setting/*` 7, `Per Instance Sharing/Share Instances` |
| **Surfaces** | 37 % | 26 greyed (Trim / Untrim / Intersect / Project / Extend / Offset / Round / Stitch — 4.5 NURBS에 trim / custom knot 없음) |
| **Deform** | 65 % | `Tension`, `Solidify`, `Morph`, `Wrinkle`, `Jiggle` 3, `Sculpt`, `Pose Interpolator`, `Blend Shape#2/Swap`, `Edit Membership Tool` |
| Generate / nHair / nConstraint / Toon / FX 전체 | 0–19 % | Blender 대응 없는 시스템 — notice만 |

Key / Control / Mesh Display는 이 표에서 크게 내려왔다 (step 182 1b의 1·2위).

**새로 생긴 모순 (step 187 뒤 notice가 낡음)** — kit에 Character Set이 생겼는데:
- `Windows/Relationship Editors/Character Sets`는 greyed, notice는 "Blender has no character sets: a Keying Set ... keys a chosen set of channels"
  (`src/allset/ui/notices.py:48-49`).
- 카테고리 notice `Key` / `Control` (`notices.py:336-340`)도 "Blender has no character sets" — 남은 greyed Key / Control 항목 (`Character Mapper`,
  `Redirect`, `Set Blend Shape Target Weight Keys` …)의 툴팁이 그 문장을 보여 준다.
- Graph Editor / Dope Sheet `Show/Objects/Characters` greyed, notice "Blender has no character sets" (`notices.py:848-850`).
- Status Line `Show or hide the Character Controls`는 HumanIK 것이라 그대로가 맞음 (delegated).

### 1c. Editor menu bars

914 leaves, working 578 (63 %) — **경로 diff 0** (`tmp/audit192b/ed_old.json` = `ed_now.json`). 두 번째 감사 연속 같음. step 182 §1c 목록 그대로:
Graph Editor View 20 / 40, Show 18 / 34, Curves 16 / 39 greyed (buffer curves, weighted tangents, Retime / Region Keys / Lattice Deform Keys Tool,
`Edit/Scene Time Warp`), Dope Sheet Show 18, UV Editor `Cut/Sew/Auto Seams`, `Split`, `Symmetrize` ×2, Image 8 / 14, UV Sets 7 / 11, Hypershade Create
91 / 160, Render Settings Presets 9 / 10, **Script Editor History 0 / 13 (일곱 번째 연속 0 %)**. Character Set이 생겼지만 Graph / Dope Sheet `Show/Objects/
Characters`는 greyed (§1b).

### 1d. Panel menus / panel toolbar / Status Line

Panel menus 69 / 111 (+2: `Show/IK Handles`, `Show/Image Planes`). 남은 greyed 42 중 모순 둘: **`Show/NURBS CVs`, `Show/NURBS Hulls`** — kit에
NURBS surface (step 181)와 curve가 있는데 회색. 나머지: View 4 (`View Sequence Time`, Camera Tools 3), Shading 9 (`Flat Shade All`, `Flat / Smooth Shade
Selected Items`, `Bounding Box`, `Points`, `X-Ray Active Components`, `Interactive Shading`, `Smooth Wireframe`, `Hardware Fog`), Lighting 3 (`Use Selected /
No Lights`, `Two Sided Lighting`), Show 18, Renderer 2, Panels 5. Panel toolbar greyed 7 (그대로). Status Line greys 8 (`Construction History`는 이제
`WindowManager.allset_construction_history`, step 189).

## 2. Option boxes per top menu (507 paths)

window = kit Maya option window, dialog = operator / file dialog, tool = tool + Tool Settings, redo = run + Adjust Last Operation, generic = "Blender has
no settings for this" 창, dead = greyed 항목의 박스. 바뀐 줄만 [step 182 값]:

| Menu | window | dialog | tool | redo | generic | dead |
|---|---|---|---|---|---|---|
| Create | 8 | 1 | – | **25** [18] | 3 | **7** [14] |
| Mesh Display | **5** [2] | 1 | – | **3** [5] | 1 | **0** [3] |
| Key | 9 | – | – | **2** [1] | **0** [1] | **1** [2] |
| Control | – | – | – | **2** [0] | **0** [1] | **1** [2] |
| Surfaces | **11** [10] | – | – | 1 | **3** [4] | 22 |
| nHair | – | – | – | 2 | **2** [0] | **9** [11] |
| (그 밖의 메뉴 전부) | step 182와 같음 | | | | | |

경로 diff (19개): dead → redo 9 (`Create/Polygon Primitives/Pipe`, `Helix`, `Gear`, `Soccer Ball`, `Super Ellipse`, `Spherical Harmonics`, `Ultra Shape`;
`Key` / `Control/Create Subcharacter Set`); generic → redo 2 (`Key` / `Control/Create Character Set`); dead → window 3 (`Mesh Display/Apply Color`,
`Prelight (Maya)`, `Set Vertex Normal`); redo → window 2 (`Mesh Display/Average`, `Set to Face`); generic → window 1 (`Surfaces/Insert Isoparms` — step 182
역행 해소); dead → generic 2 (`nHair/Modify Curves/Smooth`, `Straighten`).

차이: **새 primitive 7종과 Create Character Set의 박스가 Maya 옵션 창이 아니라 Adjust Last Operation (redo)**. Maya에는 `Polygon Pipe Options`,
`Polygon Helix Options` … 와 `Create Character Set Options` (Name / Character set attributes / Hierarchy) 창이 있다 (`research/maya/re/poly_prims_185.md`,
`research/maya/re/character_sets_183.md`). redo 127 중 Maya에 창이 있는 것은 이번에 늘었다.

generic 34 중 Maya 사용자가 매일 쓰는 박스 (step 182와 같음): `Curves/Cut`, `Detach`, `Smooth` ×2, `Reverse Direction`, `Straighten`, `Create/Curve
Tools/Three / Two Point Circular Arc`, `Pencil Curve Tool`, `UV/Merge UVs`, `Contour Stretch`, `3D Cut and Sew UV Tool`, `Skeleton/Set / Assume Preferred
Angle`, `Skin/Edit Influences/Add Influence`. 매주: `Surfaces/Planar`, `Bevel Plus`, `Duplicate NURBS Patch`, nCloth 2, nParticles 5, `Fluids/Make Collide`,
`Modify/Bake Pivot`, `Mesh Display/Paint Vertex Color Tool`, `Texturing/3D Paint Tool`, `File/Archive Scene`; `Render/Render Current Frame` / `IPR`는
Maya와 같은 경고 (분류기만 generic).

dead 193을 메뉴별로 많은 순: Surfaces 22, Fluids 16, Modify 16, Deform 12, Curves 11, nConstraint 11, nCache 9, nHair 9, Generate 8, nParticles 8,
Cache 7, Constrain 7, Create 7, Mesh Tools 7, Effects 6, Fields 6, Skin 5.

박스를 여는 방법: step 183으로 **Maya 메뉴바에서 연 pulldown과 그 submenu**는 ❒ 클릭이 창을 연다 (`ui/option_click.py`, UI 1.0 / 1.25 측정). hotbox
메뉴 행, 마킹 메뉴 `item`, 선반 우클릭 메뉴 등 메뉴바 밖에서 연 메뉴는 여전히 click = 명령, 창은 0.2 s hold (CLAUDE.md step 183 "elsewhere step 146's
hold / Shift / Ctrl+click stays"). 이번 lane은 GUI로 다시 재지 않았다 (§8).

## 3. Shelves (`ui/shelf.all_buttons`)

203 buttons, **160 working (79 %)** [159], 43 greyed with a notice [44], 0 without. 바뀐 탭: Poly Modeling 41 → **42 / 43** (Super Shape). 남은 greyed:
Curves / Surfaces 8, FX 16, FX Caching 6, Sculpting 7, Rendering 4, Poly Modeling 1 (3D Grab UV Tool), Rigging 1 (Human IK).

## 4. Hotkeys / marking menus

Hotkeys (468 rows): 구현 210, IC 일치 26, 해당 없음 164, 미검토 0, macOS 68 — `tmp/audit192b/keymap_mapping.md`가 step 182 출력과 diff 0 (세 번째 연속
변화 없음). 메뉴 hotkey 글자: 메인 57, 에디터 메뉴바 0 (그대로).

Marking menus: 474 entries, **371 working (301 direct + 70 `item`), 52 greyed** + 10 빈 submenu, 41 submenus. 해제 3: `contextPolyToolsDefaultMM` 3–5.
greyed 52 분포: Shift+Q `doSelectComponentMM` 25, `translateMarkingMenuImpl` 4, `buildSelectAllMM` 4, `dagMenuProc_curve` 3, rotate 2, hotbox east / west
2 + 2, 나머지 1씩. NURBS surface용 RMB 메뉴 (Isoparm / Surface Point / Hull) 여전히 0.

## 5. look_compare

### 5a. 실효 UI 배율 1.0 (`compare_audit192_s100/`, 15 side-by-side, 6 crops)

- checks 9/9; pixels kit-drawn **7/7** (theme 30, 20 > 5 not counted, 1 no kit element, 0 anchors missing); viewport **20/20**; rects **5/12**; scene 3/3;
  density 5/6 (menu bar 26.0/27, item pitch 20.1/20, CB row 16.1/16, **menu top − bar bottom −6.0/0**, shelf 64/64, icon 32/32); grid ok (ΔE00 0.7,
  corners 4/4, 0.213 ms); furniture 2/3.
- step 182 대비: rects / density / scene / furniture.md **바이트 단위로 같음**. pixels.md: `time_slider_bg` theme → kit (#303030 → **#2b2b2b**, ΔE 1.6 →
  0.0, step 186), marking menu 표본 위치만 이동 (리스트가 링 아래로, step 184). viewport.md 표본 8 추가, 모두 ✓: 선택 엣지 #e2aa78 ΔE 0.7, 엣지 모드
  와이어 0.4, "선택 엣지가 하늘색 띠 안" 0.04 (Maya 0.05), Move 가운데 사각 #ffff8c 0.6, Scale 가운데 큐브 0.1, 평면 핸들 빨강 3.0 / 파랑 2.9, 평면
  면적 158 vs 167 px (×0.95) — step 185.
- theme ✗ 20개: step 182 §5a 값 그대로 (메뉴바 #181818 vs #444444 14.0, 팝업 18.7, 에디터 틈 22.8, Outliner 선택 행 21.0 …). step 130 결정상 kit가
  고칠 수 없음.
- rects ✗ 7개 (값 그대로): Tool Box / Outliner / viewport / dock가 Maya보다 37 px 높고 10 px 위에서 시작, Tool Box 56 vs 40 폭, dock 287 vs 260, Time
  Slider 1300 vs 1596 폭, Range Slider 높이 26 vs 31.

### 5b. 실효 UI 배율 1.25 (`compare_audit192_s125/`)

- checks 9/9, kit-drawn 7/7, viewport **20/20**, rects 5/12, scene 3/3, density 5/6 (**menu top − bar bottom −10.4 px**), grid ok (0.215 ms), furniture 2/3.
  rects / density / scene / furniture.md는 step 182와 바이트 단위로 같다 (메인 뷰포트 폭 850 vs 1003, dock 346 vs 260, Time Slider 1225 vs 1596).
- pixels.md: `time_slider_bg`가 kit 분류로 바뀌었지만 1.25에서는 #303030 (ΔE 1.6) — 1.0의 #2b2b2b와 다르다 (표본점이 1.25 ruler의 다른 띠에 떨어짐;
  통과 범위 안).

### 5c. 이미지에서 보이는 차이 (왼쪽 Maya, 오른쪽 kit; 차이만, 직접 봄)

step 182 §5c 대비 해결된 것: **#3 선택 엣지** (09 — 아래 앞 엣지가 주황으로 또렷), **#2 Move manipulator** (02 / 09 — 평면 핸들 크기·색, 가운데
상자 연노랑), **#9 Time Slider 눈금** (확대 `tmp/audit192b/crop_ts_zoom.png`: 5 프레임마다 눈금 + 숫자가 눈금 오른쪽, Maya와 같은 배치). 남은 / 새로 본
차이:

1. **RMB 마킹 메뉴 (`14`)** — 리스트는 이제 링 아래 한 열 (step 184). 그러나 (a) 1.0 샷에서 링이 누른 점 (pCube1 가운데)에서 약 200 px 위로 올라가
   그려지고, 1.25 샷 (`compare_audit192_s125/14`)에서는 링 N 박스 `Edge`가 Status Line 위, `Vertex` / `UV`가 선반 위에 그려진다. Maya 샷은 링이 누른
   점에 있고 리스트가 창 아래로 넘친다. 원인: Maya 마킹 메뉴 창은 **화면 전체**로 잘리고 (`research/maya/re/rmb_list_184.md` "never clipped by the viewport
   panel or the Maya main window; only the screen bounds it"), kit은 Blender **창** 경계로 올린다 (`engine.fit_ring`, window bounds). 샷 창 900 px —
   최대화한 창에서는 차이가 작다 (delegated: 환경 의존). (b) 1.0에서 리스트가 한 열이 아니다 — 마지막 행 `Assign Existing Material ▸`가 첫 행 `pCube1...`
   오른쪽 둘째 열로 가고, `Material Attributes...`와 `Assign New Material...` 사이가 에디터 경계 띠만큼 벌어져 Time Slider 위로 내려간다 (확대
   `tmp/audit192b/crop14_kit.png`). Maya: 179 × 476 한 덩어리 (`rmb_list_184.md`). 회색 `Vertex Face`, `Metadata`, `Time Editor`, 가운데 원형 커서는 그대로.
2. **Time Slider 현재 프레임** (`crop_time_slider`): kit = Blender 파란 말풍선 "1"이 ruler 위쪽에 겹침 (C overlay, CLAUDE.md step 186 "only Blender's
   current-frame box survives"); Maya = 프레임 칸 회색 사각 + 아래쪽 숫자. kit 숫자가 약간 크다. 재생 버튼 + 현재 프레임 칸이 오른쪽 별도 area (rect Δw −296).
3. **Channel Box 모양** (`crop_channel_box`) — 변화 없음: 행 바탕 없음, `pCube1` / SHAPES / INPUTS 머리글 굵기·바탕 없음, 맨 위 `::::::` 손잡이, 라벨
   열이 오른쪽으로 들어감, 값 칸이 넓음, Maya 오른쪽 위 아이콘 3개 없음, 아래 가로 스크롤바 없음; Layer Editor `Display` / `Anim` 탭이 파란 알약 (Maya 회색
   탭), Layer 아이콘 4개 중 2개 흐림.
4. **Outliner** (`crop_outliner`, 01 / 02) — 변화 없음: 오브젝트가 카메라보다 먼저, 주황 삼각 아이콘, 선택 행 주황 글자, 검색 칸 위치, kit `::::::` 손잡이.
   09에서 kit 행 왼쪽에 점 3개 (Maya 없음).
5. **Create 메뉴** (`12`) — 변화 없음: 메뉴가 메뉴바와 6 px (1.25: 10.4 px) 겹침, 첫 줄 tear-off 점선 (Maya: `Objects` 섹션 라벨), 밑줄 니모닉, Maya 2022에
   없는 `Subdiv Primitives` 행, Maya의 `Sweep Mesh` / `USD` 녹색 표시 없음.
6. **컴포넌트 CB** (`09`): kit edge 모드 = `pCubeShape1` + INPUTS만; Maya = `pCube1Shape`, `CVs (click to show)`, INPUTS. CVs 줄은 Maya idle 지연일 수
   있음 (§8, step 182와 같음). Shape 이름도 다르다 (§8).
7. **Help Line**: 빈 장면 (01) kit "Select Tool: click or drag to select. Shift toggles…" / Maya 빈 줄; Move 도구 kit "Move Tool: drag the manipulator. Hold
   X/C/V…" / Maya "Move Tool: Use manipulator to move object(s). Ctrl+middle-drag…". 문장이 Maya 문장이 아니다.
8. **Four view** (`16`) — 변화 없음: panel menu + toolbar가 칸마다 아님 (네 칸 위 한 벌), ViewCube 칸, 직교 칸 배율 (샷 스크립트 경로 문제, step 182 §8).
9. **Hotbox** (`13`): 가운데 제목 "Maya Workflow Kit" (Maya "Maya"); 행 상자 바탕이 Maya보다 옅다.
10. **1.25 레이아웃** (`compare_audit192_s125/01`): 메인 뷰포트가 Maya보다 153 px 좁고 dock가 86 px 넓음, 선반 높이 80 vs 64 (rects 그대로).

## 6. Domain 차이 (시나리오별, 증거)

| Domain | Maya가 아니라고 느껴지는 곳 (큰 것부터) | 증거 |
|---|---|---|
| Modeling | Polygon primitive 7종 박스 = redo (Maya 옵션 창); Interactive Creation 4 greyed; Curves 58 % / generic 박스 6; NURBS CVs / Hulls 표시 토글 회색; Mesh Display Color Material Channel / Blend 13 | §1b, §1d, §2 |
| Surfaces | 37 % (trim 계열 — 4.5 한계); NURBS surface RMB 마킹 메뉴 없음 | §1a, §4 |
| UV | `Auto Seams` (+ 마킹 2), `Split`, `Symmetrize` ×2, `3D Grab UV Tool`, UV Sets 7 / 11; UV `Merge UVs` / `Contour Stretch` 박스 generic | §1c, §2, §3 |
| Animation | Time Slider 현재 프레임 = Blender 말풍선; Character Set 관련 notice 4곳이 "Blender has no character sets" (모순); Scene Time Warp 4 + 에디터 Edit 2; Graph Editor View 20 / Show 18 greyed; Create Character Set 박스 = redo | §5c-2, §1b, §1c, §2 |
| Rigging | Skin 68 %, Constrain 55 % (네 번째 연속 불변); Preferred Angle / Add Influence 박스 generic | §1b, §2 |
| FX | 19 % (nConstraint 0 %, nCache 15 %, Effects 18 %, 일곱 번째 연속) | §1a |
| Rendering | Texturing 12 %, Hypershade Create 91 greyed, Render Settings Presets 9 / 10 | §1a, §1c |
| File I/O | File 80 % 불변 (`ATOM` 3, Offline File 2, After Effects Live Link); Cache 46 %; `Archive Scene` 박스 generic. 왕복은 `research/maya/re/file_io.md`를 믿음 — 이번 lane 재실행 안 함 | §1a, §2 |
| 공통 UI | CB 모양, Outliner, RMB 리스트 둘째 열 / 링 이동, 메뉴 6 px 겹침, Help Line 문장, 테마 색 20개 (결정상 불가), 에디터 메뉴 hotkey 글자 0, Script Editor History 0 / 13 | §5c, §1c |

## 7. Ranked remaining differences and one-step backlog

점수 = 심각도 (1–3) × 빈도 (1–3) (이번 감사는 사용자 지정 척도; step 182는 1–5 × 1–5였다). step 182 #1 (❒ 클릭, 메뉴바 부분), #2 (RMB 리스트 위치),
#3 (선택 엣지), #4 (Time Slider 눈금), #5 (Character Set), #6 (Mesh Display), #7 (manipulator), #9 (primitives), #12 (Insert Isoparms)는 해결 / 대부분
해결되어 빠짐.

| # | 차이 | S × F | 점수 | step 182 |
|---|---|---|---|---|
| 1 | Channel Box / Layer Editor 모양 (행 바탕, 머리글, 손잡이, 라벨 열, 파란 탭) | 2 × 3 | 6 | #8 |
| 2 | Time Slider 현재 프레임 = Blender 파란 말풍선 (Maya 회색 칸) | 2 × 3 | 6 | #4 잔여 |
| 3 | 박스가 redo / generic인데 Maya는 옵션 창: primitive 7 + Create Character Set 2 (redo), Curves Cut / Detach / Smooth / Reverse / Straighten, Arc 2, Merge UVs, Contour Stretch, Preferred Angle 2, Add Influence (generic) | 2 × 3 | 6 | 새로 (generic은 #1 주변) |
| 4 | FX 19 % 불변 (Create Options, Initial State, Instancer, nConstraint 0 %) | 3 × 2 | 6 | #11 |
| 5 | Character Set notice 모순 4곳 + `Windows/Relationship Editors/Character Sets`, Graph / Dope `Show/Objects/Characters` greyed | 2 × 2 | 4 | 새로 |
| 6 | RMB 리스트가 둘째 열로 갈라짐 / 경계 띠 틈 + 링이 누른 점에서 창 경계만큼 위로 이동 | 2 × 2 | 4 | #2 잔여 |
| 7 | Skin 68 % (`Interactive Bind Skin`, `Move Weights to Influences`, `Bake Deformation to Skin Weights`, Post Normalization) | 2 × 2 | 4 | 1b |
| 8 | Constrain 55 % (`Normal`, `Tangent`, `UV Pin`, `Proximity Pin`, `Remove Target`, `Set Rest Position`) | 2 × 2 | 4 | 1b |
| 9 | Panel `Show/NURBS CVs` / `NURBS Hulls` 회색 (kit에 NURBS surface 있음) | 2 × 2 | 4 | #10 잔여 |
| 10 | ❒ 클릭이 hotbox / 마킹 / 선반 메뉴에서는 여전히 명령 (메뉴바 메뉴만 해결) | 2 × 2 | 4 | #1 잔여 |
| 11 | Curves 58 % (`Lock / Unlock Length`, `Bend`, `Curl`, `Align`, `Fit B-spline`, `Edit Curve Tool`) | 2 × 2 | 4 | 1b |
| 12 | Help Line 문장이 Maya 문장 아님 (빈 장면 / Move Tool) | 1 × 3 | 3 | 새로 |
| 13 | Create 메뉴 첫 줄 tear-off (Maya 섹션 라벨) + 메뉴 6 px 겹침 | 1 × 3 | 3 | 뒤로 미룸 |
| 14 | `Create/*/Interactive Creation` + `Exit On Completion` 4 greyed | 1 × 2 | 2 | 새로 |

1. **Channel Box 모양** — Maya: `crop_channel_box` 왼쪽 (행 바탕 #3a3a3a대, 머리글 굵게, 아이콘 3개; `research/maya/colors.json`, `research/maya/screens/`). kit:
   `ui/channel_box.py` `Lines`가 바탕 없이 그림. 지시: CB 부분 POST_PIXEL로 shape / SHAPES / INPUTS 행 바탕과 머리글 굵기 (blf bold 불가면 측정 기록),
   tear-off 손잡이를 Maya처럼 dock 경계로, Layer Editor 탭 = 회색 탭. 검증: `crop_channel_box` 나란히, `look_data` pixels에 CB 행 바탕 / 탭 표본 2개 ΔE < 5.
2. **Time Slider 현재 프레임** — Maya: 프레임 칸 회색 사각 + 세로선 (`research/maya/re/time_slider_186.md`). kit: Blender C overlay 말풍선은 끌 RNA가 없음 (step
   186). 지시: Maya 칸을 POST_PIXEL로 그리고, 말풍선은 Time Slider 영역 `region.height`를 줄여 ruler 위 띠에 가두거나 Dope Sheet `show_seconds` 등으로 못
   지우면 측정 기록 + manual check. 검증: `crop_time_slider` 확대, pixels.md에 현재 프레임 칸 표본.
3. **옵션 창 11+개** — Maya: `research/maya/re/poly_prims_185.md` (Pipe / Helix / Gear / Soccer Ball / Super Shape 옵션 기본값), `character_sets_183.md`
   (Create Character Set Options), `option_boxes.md`. kit: `menu_sets.option_kind` = redo / generic. 지시: `operators/option_windows_*`에 primitive 7 + Create
   Character Set 창 (Maya 필드 이름 / 기본값), 다음 단계로 Curves generic 6. 검증: `test_step140_option_count` redo 127 → 118, window 120 → 129.
4. **FX** — `nParticles/Create Options/*`, `Fields/Solvers/Initial State/*`, `Instancer`. 검증: FX ≥ 25 %.
5. **Character Set notice 정리** — kit: `notices.py:48-49`, `:336-340`, `:848-850`. 지시: `Windows/Relationship Editors/Character Sets`를 kit Character Set
   목록 (Keying Sets 패널 또는 kit 창)에 연결, Graph / Dope `Show/Objects/Characters`를 `character_sets` 필터로, 카테고리 문장에서 "no character sets" 제거.
   검증: `tools/menu_consistency.py` 0, `rg "no character sets" src` 0.
6. **RMB 리스트 한 열** — Maya: `rmb_list_184.md` (한 덩어리 179 × 476, 링 = 누른 점 (화면 경계 안이면)). kit: `engine.fit_ring` 경계 띠 건너뛰기 + 창
   경계 lift. 지시: 리스트 행은 경계 띠를 건너뛰지 않고 (Maya 메뉴는 패널 경계를 무시) 한 열로, 올려야 할 양 = 띠 건너뛰기 없는 높이로 다시 계산.
   검증: 14 샷 1.0에서 열 1개, 행 간격 균일; `gui_step52_hotbox_rmb`.
7. **Skin** — `Move Weights to Influences`, `Bake Deformation to Skin Weights`, `Enable Weight Post Normalization` (mayapy 대조). 검증: Skin ≥ 80 %.
8. **Constrain** — `Normal` / `Tangent` (Blender Shrinkwrap / Track 조합, mayapy 값), `Remove Target`, `Set Rest Position`. 검증: Constrain ≥ 75 %.
9. **NURBS CVs / Hulls 토글** — `ui/panel_menu_data.py`에 SURFACE / CURVE 편집 overlay (control points / hulls) 표시 연결. 검증: Panel menus 69 → 71.
10. **❒ 클릭 (메뉴바 밖)** — `ui/option_click.py` 모델을 hotbox 메뉴 행 (같은 Maya 메뉴, 위치는 kit이 그림 → 행 rect를 알 수 있음)에 확장. 검증: GUI —
    hotbox Create 메뉴의 `Polygon Primitives/Cube ❒` 클릭 = 창.

뒤로 미룸 (점수 ≤ 3): Help Line 문장 (1 × 3), Create 메뉴 tear-off / 겹침 (1 × 3), Interactive Creation (1 × 2), 에디터 메뉴 hotkey 글자 (1 × 2), Script
Editor History 13 (1 × 2), Hypershade Create 91 (2 × 1), 1.25 dock / 뷰포트 폭 (rects, Maya 1.25 기준 없음), 테마 색 20개 / Outliner 순서·아이콘 (결정상 /
C 한계 — 고치지 말 것). 도구 쪽: `tools/look_shots.py` 16 샷이 kit four-view 경로를 쓰도록 (step 182와 같음).

## 8. Not measured / counterevidence

- Maya와 나란히 하는 실제 시나리오 실행 (파일 입출력, 모델링, UV, 애니, 리깅, FX, 렌더)은 하지 않았다: 수치 재계산, look_compare, 코드 / notice 읽기만.
  Maya 이미지는 기존 `research/maya/screens/*` 그대로.
- ❒ 클릭 (step 183), RMB lift (step 184), Character Set 동작 (step 187)은 GUI로 다시 재지 않았다 — 각 step 테스트를 믿음.
- §5c-1 (a) 링 이동은 샷 창 (1600 × 900, 화면보다 작음) 때문이다: Maya는 화면 경계, kit는 창 경계. Blender를 최대화하면 차이가 줄어든다 — 결함 점수는
  (b) 둘째 열 / 틈에 주로 둠 (delegated).
- `09` / `14` Maya CB의 shape 이름 `pCube1Shape` vs kit `pCubeShape1`: Maya `polyCube` 기본은 `pCubeShape1`이므로 Maya 샷 장면이 스크립트로 이름을 붙였을
  가능성 — 차이로 세지 않음. `CVs (click to show)` 줄도 Maya idle 지연일 수 있음 (step 165).
- 1.25 `time_slider_bg` #303030 (1.0 #2b2b2b): 표본점 위치 차이로 보이며 통과 범위 안 — 결함으로 세지 않음.
- 1.25 Maya 기준 이미지 없음 (Maya 샷은 Qt 논리 px) — 1.25 rect 차이는 과대평가일 수 있다.
- 옵션 창 125개는 프로브 기준; 창마다 필드가 Maya와 같은지는 보지 않았다.
- 수동 점검 개수는 작업 사본 기준 (다른 lane이 동시에 고칠 수 있음).
