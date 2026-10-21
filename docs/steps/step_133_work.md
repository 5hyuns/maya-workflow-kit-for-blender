# Step 133 — 재점검 8차, 레인 WORK (작업 흐름: Maya 2022 와 같은 시나리오를 나란히)

비판 기준 (사용자 2026-10-19): "기본 Maya 에 Blender 기능이 붙은 모습". 칭찬 없이 차이만 적는다. 등급 = look / operation / function /
missing, 점수 = 하루 빈도 (1–5) × 심각도 (1–5) (step 98 과 같음). bug = 킷이 스스로 정한 동작과도 어긋남, gap = Maya 와 다른 설계 / Blender 한계.

## 방법

- 킷: `dist/maya-workflow-kit-0.2.1.zip` (1ac4b77) 을 `tmp/audit133_work/env` 샌드박스에 설치 (`tmp/audit133_work/run_kit.py`),
  `blender -b --factory-startup` + `tests/_bootstrap.py` 로 시나리오 스크립트 `tmp/audit133_work/probes/p*.py` 실행
  (메뉴는 `allset.menu_item(item=<Maya 경로>)` = 실제 메뉴 클릭과 같은 길, 옵션 창은 `allset.opt_<key>`). 결과 `tmp/audit133_work/out/p*.json`.
- Maya: `mayapy.exe` (Maya 2022, `MAYA_APP_DIR` = `tmp/audit133_work/maya/appdir`) 로 같은 장면을 runTimeCommand (메뉴 항목이 부르는 명령,
  기본 optionVar) 로 실행: `tmp/audit133_work/maya/m*.py` → `out/m*.json`. 같은 큐브 정점 순서 (v0, v1, f0 일치 확인) 와 위치 기준 선택을 씀.
- GUI: 이벤트 시뮬레이션 세션 (`ALLSET_SANDBOX=audit133_work_guienv python tests/gui/run.py --no-build`):
  기존 작업 흐름 테스트 6개 (Hypershade 131, 편집기 104/105, UV 66, 렌더 67, Graph/Playblast 70; 46/46 PASS) 를 `--shots` 로 다시 찍고,
  헤드리스에서 애매한 항목은 `tmp/audit133_work/gui/gui_work133.py` 로 실제 창에서 다시 쟀다. 그림 `tmp/audit133_work/shots/`.
- 한계: mayapy 에는 GUI runTimeCommand 일부가 없음 (Planar / Cylindrical / Spherical Projection, Unfold3D, CreateNCloth) → 그 항목은 [K].
  `research/maya/screens/editors104/uv_editor_win1.png`, `graph_editor_win1.png` 는 다른 창이 섞여 찍혀 있어 UV / Graph Editor 의 모양
  비교는 일부만 가능 (Graph 왼쪽 띠, 값 축은 보임). 엣지 번호는 킷과 Maya 가 다르므로 (M11) 엣지 명령은 위치로 고른 엣지로 다시 쟀다.

## 메뉴 범위 (작업 흐름별, 매핑 / 회색, 이번 측정 `out/p00_menumap.json`)

| 흐름 | 매핑 | 회색 | 매핑률 | 일상에서 걸리는 회색 항목 |
|---|---|---|---|---|
| 모델링 (Mesh, Edit Mesh, Mesh Tools, Mesh Display) | 90 | 39 | 70 % | Transfer Vertex Order, Paint Reduce Weights, 스컬프트 Target 툴 |
| UV (UV, UV Editor, UV Toolkit) | 101 | 93 | 52 % | Stack / Unstack / Distribute / Snap and Stack Shells, Normalize, Match Grid, Straighten Border, Move UV Shell·Cut·Sew·Unfold 툴, Auto Seams, Create UV Shell, Delete UVs, UV Statistics HUD |
| 애니 (Key, Playback, Visualize, Graph Editor, Dope Sheet) | 295 | 192 | 61 % | Scale Keys, Character Set 전부, IK/FK Keys, Playback Looping Once / Oscillate |
| 리깅 (Skeleton, Skin, Deform, Constrain, Control) | 75 | 115 | 39 % | Joint Labelling 전부, Interactive Bind Skin, Wire / Wrinkle / Tension / Sculpt / Jiggle, Edit Membership Tool, Export / Import Weights, Normal / Tangent / UV Pin constraint |
| FX (nParticles, nCloth, nHair, nConstraint, nCache, Fields, Fluids, Effects) | 37 | 168 | 18 % | nParticle Tool, Instancer, Goal, Fill Object, Create Options, nConstraint 전부, Initial State |
| 렌더 (Lighting/Shading, Render, Texturing, Hypershade, Render Settings, Toon, Stereo) | 139 | 194 | 42 % | Batch Render, Make / Break Light Links, Select Objects Illuminated by Light, Test Resolution |
| 파일 (File) | 24 | 6 | 80 % | ATOM, Offline File (일상 아님) |

## 흐름별 차이

### 모델링

| # | 차이 | 등급 | 점수 | 근거 | 파일 / 종류 / 이슈 |
|---|---|---|---|---|---|
| M1 | Edit Mesh > Connect: 마주 보는 엣지 2개를 고르고 실행하면 아무것도 안 됨 (CANCELLED). Maya 는 두 엣지 가운데를 잇는다 (8/12/6 → 10/15/7). Mesh Tools > Connect 는 같은 결과를 냄 | function | 3×3=9 | `out/p10_connect.json` vs `m10_connect.json` | `ui/menu_map.py` "Edit Mesh/Connect" = `mesh.vert_connect_path` (정점 경로 연결) / bug / 없음 |
| M2 | Edit Mesh > Merge: 정점 2개 (거리 1) → 킷 그대로 (8 정점), Maya 는 합침 (7 정점, polyMergeVert `alwaysMergeTwoVertices` = on). 옵션 창에 「Always merge for two vertices」 칸은 있으나 실행에서 안 씀 | function | 3×3=9 | `p01_model.json` merge, `p02_model2.json` merge_opt / `m01_model.json` merge | `operators/option_windows.py` merge 람다 / bug / 없음 |
| M3 | Mesh > Smooth = Subdivision 모디파이어 (이름 "Subdivision", 기하는 6면 그대로, 편집 모드는 우리 케이지). Maya 는 polySmoothFace 로 실제 24면. 면만 고르고 Smooth 하면 Maya 는 그 면만 (13/20/9), 킷은 오브젝트 전체에 모디파이어 | function | 3×3=9 | `p01_model.json` smooth / smooth_faces vs `m01_model.json` | `ui/menu_map.py` "Mesh/Smooth" = `_mod('SUBSURF')`, `option_windows._run_smooth` / gap / 없음 |
| M4 | 엣지 / 정점 Extrude (Ctrl+E) = Blender extrude + 마우스 따라가는 드래그 (polyExtrudeEdge / Vertex 노드, 매니퓰레이터, In-View Editor 없음). Maya 는 바로 만든다 (엣지 2개 → 12/18/8, 정점 → 11/18/9) | operation | 3×3=9 | `operators/extrude.py:381` invoke, `m01_model.json` Extrude / Extrude vtx | gap / #16 과 같은 유형 (Bevel) |
| M5 | Bevel (Ctrl+B) = 마우스 따라가는 모달, Esc 면 베벨 없음 (Maya 즉시 polyBevel3, fraction 0.5, segments 1, chamfer on — 옵션 창 경로 `opt_bevel` 는 Maya 와 같은 10/15/7) | operation | 4×3=12 | `p01_model.json` bevel, `m01_model.json` bevel | open #16 |
| M6 | Insert Edge Loop / Slide Edge / Offset Edge Loop = Blender 툴 | operation | 4×3=12 | step 128 | open #31 |
| M7 | Quad Draw / Create Polygon / Append = Poly Build | operation | 3×3=9 | step 128 | open #30 |
| M8 | Edit Mesh > Extract: 떼어낸 조각 이름이 `pCube1.001` (Blender 접미사), 원본 pCube1 은 그대로. Maya (Separate extracted faces 기본 on) 는 pCube1 그룹 아래 polySurface1 / polySurface2 [K] | look | 2×2=4 | `p02_model2.json` extract | `ui/menu_map.py` "Edit Mesh/Extract" = `mesh.separate` / gap / 없음 |
| M9 | Edit Mesh > Symmetrize: 고른 정점에 Blender symmetrize 를 바로 실행해 큐브가 망가짐 (8/12/6 → 9/11/3). Maya 는 대칭 엣지를 클릭하라는 툴로 들어가고 메시는 그대로 | function | 2×3=6 | `p01_model.json` edit_mesh_items / `m01_model.json` | `ui/menu_map.py` "Edit Mesh/Symmetrize" / bug / 없음 |
| M10 | Edit Mesh > Wedge: 면 하나만 골라도 메시가 바뀜 (24/44/22). Maya 는 면 + 축 엣지가 없으면 아무것도 안 함 | function | 1×2=2 | 같은 파일 | bug / 없음 |
| M11 | 큐브 엣지 번호가 Maya 와 다름 (킷 e[0] = vtx 2–0, Maya e[0] = vtx 0–1; 정점·면 순서는 같음). Command Line / 스크립트의 `pCube1.e[0]` 가 다른 엣지 | function | 1×2=2 | `p02_model2.json` indices / `m01_model.json` e0 | `operators/prim_shapes.py` / gap / 없음 |
| M12 | Bridge: 한 메시의 열린 관 양끝 테두리 두 개를 이으면 Maya 는 안쪽 면을 만든다 (8/16/8), 킷은 FINISHED 인데 그대로 (Blender bridge 한계). 두 오브젝트 Combine 뒤 마주 보는 면을 지운 흔한 경우는 같음 (16/28/14, divisions 0) | function | 1×2=2 | `p02_model2.json` bridge_raw, `p09_bridge.json` / `m01`, `m09_bridge.json` | gap / 없음 |

같음 (참고만): 프리미티브 9종 이름·크기·면수 (메뉴 기본값 기준), 큐브 옵션 창 + INPUTS 수정, 면 Extrude + 사후 수정 (12/20/10 → 16/28/14),
Combine / Separate 이름, Mirror, Duplicate Special, Delete History, Freeze, Poke, Detach, Add Divisions.

### UV

| # | 차이 | 등급 | 점수 | 근거 | 파일 / 종류 / 이슈 |
|---|---|---|---|---|---|
| U1 | 오브젝트 모드에서 UV > Automatic (그리고 Contour Stretch) 이 아무것도 안 함 (CANCELLED, GUI 에서도 같음). Maya 는 오브젝트 전체에 polyAutoProj (구 → 6 셸) | function | 4×3=12 | `p03_uv.json` obj_UV/Automatic, `gui_work133.json` uv_automatic_object_mode / `m03_uv.json` | `ui/menu_sets.py` menu_item 이 `uv.smart_project` poll 실패로 먼저 끝나 `option_windows._run_uv_auto` 의 오브젝트 모드 처리에 닿지 않음 / bug / 없음 |
| U2 | UV Editor 메뉴 88 항목 회색: Stack / Unstack / Distribute / Snap and Stack Shells, Normalize, Match Grid, Straighten Border, Map Border, Move UV Shell·Cut·Sew·Unfold 툴, Auto Seams, Create UV Shell, Toggle Shell Borders, UV Statistics. UV Editor > Create > Best Plane / Contour Stretch 는 회색인데 같은 항목이 메인 UV 메뉴에서는 동작 | missing | 3×3=9 | `out/p00_menumap.json` | `ui/editor_menu_map.py` / gap (+ Best Plane·Contour Stretch 는 매핑 누락 bug) / 없음 |
| U3 | UV Toolkit 은 Maya 의 일부: Transform 의 U/V 숫자 이동·회전 칸, Align 최소/최대/가운데, Stack / Distribute / Orient to Edges, Straighten, Auto Seams 없음 (회색 줄) | missing | 3×2=6 | `shots/gui_step66_toolkit.png`, `ui/uv_toolkit.py` | gap / 없음 |
| U4 | UV Editor 모양 = Blender UV 편집기: U/V 축 숫자, 0–1 경계 굵은 선, 파란 셸 음영, Maya 아이콘 툴바 없음 | look | 3×2=6 | `shots/gui_step66_uv_editor.png`, `gui_step104_uv_editor.png` | gap / 없음 |

같음: Cut / Unfold / Layout (gui_step66 PASS), 기본 큐브 texel density 256 px/unit @1024 (Maya 큐브 UV 크기와 같음), UV 셋 이름 map1.

### 애니메이션

| # | 차이 | 등급 | 점수 | 근거 | 파일 / 종류 / 이슈 |
|---|---|---|---|---|---|
| A1 | Graph Editor 값 축과 키 값이 Blender 미터: Maya 레이아웃 (cm) 장면에서 translateX 0 → 5 키가 0.00–0.05 로 보임. Maya 는 0–5. Channel Box 는 cm 로 보여서 같은 값이 두 숫자로 보임 | function | 4×4=16 | `shots/gui_step104_graph_editor.png` (테스트가 `5 * k` 로 키) vs `research/maya/screens/editors104/graph_editor_win1.png` (축 0–5) | `ui/graph_editor.py` (단위 변환 없음; F-curve = BU) / gap (킷 단위 결정 8 과 어긋남) / 없음 |
| A2 | Graph Editor / Dope Sheet 그림 = Blender: 재생 범위 밖 주황 음영, Blender 채널 목록 줄, 키 점 모양 | look | 3×2=6 | 같은 그림 | `ui/editor_chrome.py` / gap / 없음 |
| A3 | Key > Scale Keys 회색 | missing | 2×2=4 | `p00_menumap.json` | open #35 |
| A4 | Playblast = Blender 재생기 (`blender -a`), 파일 이름 `Scene_0001-0012.mp4`. Maya 는 장면 이름 동영상을 자체 뷰어 / 미디어 플레이어로 | look | 2×1=2 | gui_step70 로그 | `operators/playblast.py` / gap / 없음 |

같음: S = 10 채널 (translate / rotate / scale / visibility, GUI 측정), Set Key on Translate (GUI 에서 3 곡선; 헤드리스 CANCELLED 는 뷰 없음 탓),
Breakdown, Snap / Cut / Copy / Delete Keys, Min/Max 범위, 탄젠트 메뉴, 기본 24 fps · 1–120 / 1–200 · Auto Key off · 새 키 Auto (clamped) 탄젠트.

### 리깅

| # | 차이 | 등급 | 점수 | 근거 | 파일 / 종류 / 이슈 |
|---|---|---|---|---|---|
| R1 | Deform > Lattice = 빈 Lattice 모디파이어 (격자 오브젝트 없음, 변형 없음). Maya 는 ffd1Lattice + ffd1Base 를 오브젝트 둘레에 만든다. Sine / Wave = 빈 Wave, Wrap = 대상 없는 Surface Deform | function | 3×4=12 | `p05_rig.json` deformers / `m05_rig.json` | open #34 |
| R2 | Constrain > Aim = Track To (-Z 가 대상, up Y). Maya 는 +X 가 대상, up = 월드 Y (Blender Z). 같은 장면에서 큐브 방향이 다름 (Maya ro (-10.1, -32.3, 18.4)°) | function | 3×3=9 | `p05_rig.json` constraints / `m05_rig.json` | `ui/menu_map.py` `_con('TRACK_TO')`, `operators/rig_tools.py` / gap / #35 (Aim 옵션 없음) 와 관련 |
| R3 | 조인트가 Outliner / 선택에서 armature 오브젝트 `skeleton1` 아래에 있음 (Maya 는 joint1 이 최상위 노드). 3 클릭 = 뼈 3개 (끝 조인트 뒤로 짧은 뼈 하나 더) | look | 4×2=8 | `p05_rig.json` joints / `m05_rig.json` joints | `operators/joints.py` new_skeleton / gap (step 57 설계) / 없음 |
| R4 | 스켈레톤을 지운 뒤 새 조인트 이름이 joint4.. 로 이어짐 (주인 없는 armature 데이터의 뼈 이름을 셈). Maya 는 다시 joint1 | look | 2×1=2 | `p05_rig.json` ik / bind (joint4–9) / `m05_rig.json` after_delete | `operators/joints.py` taken_joint_names / bug / 없음 |
| R5 | Joint Tool / IK / Paint Skin Weights 옵션 창 없음 | missing | 3×2=6 | step 128 | open #32 |

같음: IK Handle 이름 ikHandle1, Bind Skin (정규화 합 1.0, 메시를 부모로 두지 않음), Parent (offset 유지) / Point / Orient / Scale 결과 위치·회전,
Cluster / Bend / Soft Mod 핸들 이름, Set Driven Key 채널 tx..v.

### FX

| # | 차이 | 등급 | 점수 | 근거 | 파일 / 종류 / 이슈 |
|---|---|---|---|---|---|
| F1 | Fields 기본 크기가 전부 1.0: Maya Gravity 9.8, Newton 5, Radial 5, Air 4, Turbulence 5. Gravity field 가 Blender Wind (질량·면적에 따른 힘) 이라 가속도가 아님, Newton = Force +1 (밀어냄; Maya Newton 은 당김) | function | 2×3=6 | `p06_fx.json` fields / `m06_fx.json` fields | `operators/create.py:72-80` / bug / 없음 |
| F2 | Create Active Rigid Body 만 해도 장면 중력으로 떨어짐 (z 5 → 0.54 @24). Maya 의 rigid body 는 Gravity field 를 연결하기 전엔 그대로 (y 5) | function | 1×3=3 | `p06_fx.json` rigid / `m06_fx.json` rigid | `operators/fx.py` fx_rigid / gap / 없음 |
| F3 | Create Emitter = 파티클 시스템을 가진 메시 `emitter1` 하나. Maya 는 emitter1 + nParticle1 (따로 고르는 오브젝트, AE) + nucleus1. 파티클이 Blender 점으로 그려짐 (Maya nParticle 기본 Balls) | look | 2×2=4 | `p06_fx.json` emitter | `operators/fx.py` / gap / 없음 |
| F4 | nParticles 의 Instancer, Goal, nParticle Tool, Fill Object, Create Options, nConstraint 전부 회색 (FX 매핑률 18 %) | missing | 2×3=6 | `p00_menumap.json` | gap / 없음 |

같음: 방출 수 (24 프레임에 97, Maya rate 100/s), nCloth 낙하·충돌, 필드 이름 (gravityField1 ...).

### 렌더 / 룩뎁

| # | 차이 | 등급 | 점수 | 근거 | 파일 / 종류 / 이슈 |
|---|---|---|---|---|---|
| X1 | 새 Maya 레이아웃 장면에서 Render > Render Current Frame 이 아무것도 안 함 ("Cannot render, no camera", 메뉴는 CANCELLED, 화면엔 메시지도 안 남음). 장면에 카메라가 없음 — Maya 는 renderable persp 로 렌더. Render Sequence 도 같음 | function | 4×4=16 | `p07_render.json` template_render_no_camera, `gui_work133.json` render, `shots/work133_render_no_camera.png` / `m04_scene.json` renderable = perspShape | `tools/make_startup.py` (startup.blend 에 카메라 없음), `ui/menu_map.py` "Render/Render Current Frame" = `render.render` / bug / 없음 |
| X2 | Blinn / Phong 기본값이 Maya 와 다름: Base Color 0.8 (Maya color 0.5), Property Editor / AE 의 Incandescence 가 흰색 (Maya 검정), Specular Roll Off 0.5 (Maya 0.7). Lambert 는 step 100 에서 맞췄고 blinn / phong 은 안 맞춤 | look | 3×2=6 | `p07_render.json` materials, `shots/gui_step131_hypershade.png` / `m07_mat.json` | `operators/material.py` MATERIALS 'BLINN' / 'PHONG' / bug / 없음 |
| X3 | 새 장면 렌더 설정: 1920×1080 (Maya 960×540), 뷰 변환 AgX (Maya ACES 1.0 SDR-video), Render Settings 경로 `/tmp\` (Maya `<project>/images`) | function | 3×2=6 | `p04_anim.json` template_scene / `m04_scene.json` defaults, `shots/gui_step105_render_settings.png` | `tools/make_startup.py` / gap / 없음 |
| X4 | Hypershade Graph 가 Blender 노드 (Principled BSDF, Material Output, Checker Texture). Maya 는 blinn1 → blinn1SG, checker1 / file1 + place2dTexture1. Browser 견본에 이름 없음, Property Editor 용어가 Blender (Opacity ↔ Maya Transparency) | look | 3×3=9 | `shots/gui_step131_hypershade.png` vs `research/maya/screens/hypershade131/hypershade_graph_grab.png` | `ui/hypershade_layout.py`, `ui/hypershade.py` / gap / #25 (닫힘, 배치만) |
| X5 | 점 / 스포트 / 면 조명은 늘 제곱 감쇠 (Maya 기본 No Decay). intensity 1 조명을 10 단위 거리에 두면 Maya 의 약 1 % 밝기 (cm 장면 point 0.001 W). 알림 문구만 있음 | function | 3×3=9 | `p07_render.json` lights / `m07_mat.json` (decay 0) | `operators/create.py:86-115` / gap / 없음 |
| X6 | Render View = Blender 이미지 편집기 + Render / Keep / Remove 버튼 (Maya Render View 툴바, 메뉴, 아래 정보 줄 없음) | look | 3×2=6 | `shots/gui_step67_render_view.png` | `ui/render_view.py` / gap / 없음 |
| X7 | Batch Render 회색 (Render Sequence 는 UI 를 막는 render.render animation) | missing | 2×3=6 | `p00_menumap.json` | gap / 없음 |
| X8 | Light Linking: Make / Break Light Links, Select Objects Illuminated by Light 등 회색 (Light Linking Editor = Properties Object 탭) | missing | 2×2=4 | 같음 | gap / 없음 |

같음: lambert1 / initialShadingGroup, blinn1 / blinn1SG 이름, 할당, Keep Image, Light Editor, Hypershade 패널 배치 (step 131).

### 파일 입출력

| # | 차이 | 등급 | 점수 | 근거 | 파일 / 종류 / 이슈 |
|---|---|---|---|---|---|
| I1 | Export → FBX 를 Maya 로 가져오면 변환에 Rotate X -90, Scale 100 이 붙음 (모양 크기는 맞음), 셰이프 `pCube1Shape` (Maya pCubeShape1), SG `pCube1SG`, 애니메이션 곡선 0 [U] | function | 3×4=12 | `m08_file.json` import_kit.fbx | `operators/file_io.py` export_args FBX (축·단위를 오브젝트 변환으로 씀) / bug / 없음 |
| I2 | Maya FBX / OBJ 를 가져오면 오브젝트에 Rotate X 90 (Channel Box rx 90), FBX 메시 데이터 이름 `Mesh`, OBJ 는 오브젝트 이름이 파일 이름 `maya_cube` (Maya 의 g pCube1 무시), 재질 `initialShadingGroup` | function | 3×3=9 | `p08_file.json` import_maya | `operators/file_io.py` import_args / bug / 없음 |
| I3 | Export → Alembic: Maya 에서 Scale 100 (global_scale 이 루트 스케일로 들어감). USD: `root` (rx -90, scale 100) 와 `env_light` 노드가 더 생김 | function | 2×3=6 | `m08_file.json` abc / usd | 같음 / bug / 없음 |
| I4 | Export → OBJ: Maya 에서 메시 이름 `Mesh` (Blender 가 g 그룹 안 씀), 재질 kit_cube_lambert1 | function | 2×2=4 | `m08_file.json` obj | 같음 (`export_object_groups`) / bug / 없음 |
| I5 | Maya 장면 (.ma / .mb) 은 열기 / 가져오기 / 참조 불가 (Files of type 의 "Maya Scenes" = .blend) | missing | 2×4=8 | `operators/file_io.py` FORMATS | gap (Blender 한계) / 없음 |
| I6 | Create Reference 뒤 Outliner 에 Blender 컬렉션 줄 (`ref_src`, `ref_src:Collection`, `Collection`) 이 더 보임 | look | 2×1=2 | `p08_file.json` reference | `operators/project.py` / gap / 없음 |

같음: Increment and Save (`scene_a.0001.blend` 로 이어서 작업), Create Reference 이름공간 `ref_src:pSphere1`, 프로젝트 기본 폴더.

## 우선순위 표 (점수순)

| 순위 | # | 차이 (요약) | 등급 | 점수 | 종류 | 이슈 |
|---|---|---|---|---|---|---|
| 1 | A1 | Graph Editor 값이 미터 (5 cm 키 = 0.05) | function | 16 | gap/bug | 없음 |
| 2 | X1 | 새 장면 Render Current Frame 이 카메라 없어 무반응 | function | 16 | bug | 없음 |
| 3 | U1 | 오브젝트 모드 UV > Automatic 무반응 | function | 12 | bug | 없음 |
| 4 | I1 | FBX 내보내기 → Maya 에서 rx -90 / scale 100 | function | 12 | bug | 없음 |
| 5 | M5 | Bevel 모달 | operation | 12 | gap | #16 |
| 6 | M6 | Insert Edge Loop 등 Blender 툴 | operation | 12 | gap | #31 |
| 7 | R1 | Lattice / Sine / Wrap 빈 모디파이어 | function | 12 | gap | #34 |
| 8 | M1 | Edit Mesh > Connect (엣지) 무반응 | function | 9 | bug | 없음 |
| 9 | M2 | Merge 가 정점 2개를 안 합침 | function | 9 | bug | 없음 |
| 10 | M3 | Smooth = 모디파이어, 선택 면 무시 | function | 9 | gap | 없음 |
| 11 | M4 | 엣지 / 정점 Extrude = Blender 드래그 모달 | operation | 9 | gap | (#16 유형) |
| 12 | M7 | Quad Draw = Poly Build | operation | 9 | gap | #30 |
| 13 | R2 | Aim = -Z / up Y | function | 9 | gap | (#35) |
| 14 | U2 | UV Editor 88 항목 회색 (Stack, Distribute, Move UV Shell...) | missing | 9 | gap | 없음 |
| 15 | X4 | Hypershade Graph 가 Blender 노드 | look | 9 | gap | (#25 닫힘) |
| 16 | X5 | 조명 감쇠: No Decay 없음, 1 % 밝기 | function | 9 | gap | 없음 |
| 17 | I2 | Maya FBX / OBJ 가져오기 rx 90, OBJ 이름 = 파일 | function | 9 | bug | 없음 |
| 18 | R3 | 조인트 위 `skeleton1` 오브젝트 | look | 8 | gap | 없음 |
| 19 | I5 | .ma / .mb 불가 | missing | 8 | gap | 없음 |
| 20 | X2 | Blinn / Phong 기본값 (color 0.8, 흰 Incandescence) | look | 6 | bug | 없음 |
| 21 | X3 | 렌더 기본값 1920×1080, AgX, /tmp | function | 6 | gap | 없음 |
| 22 | I3 | Alembic scale 100, USD root / env_light | function | 6 | bug | 없음 |
| 23 | M9 | Symmetrize 가 선택을 바로 망가뜨림 | function | 6 | bug | 없음 |
| 24 | F1 | 필드 크기 1.0, Gravity = Wind, Newton 이 밀어냄 | function | 6 | bug | 없음 |
| 25 | U3 / U4 / A2 / X6 / X7 / F4 / R5 | UV Toolkit 일부, UV Editor 모양, Graph 모양, Render View, Batch Render, FX 회색, 리깅 옵션 | look/missing | 6 | gap | R5 = #32 |
| 26 | M8 / F3 / A3 / I4 / X8 | Extract 이름 .001, emitter 구조, Scale Keys, OBJ 이름, Light Linking | — | 4 | — | A3 = #35 |
| 27 | F2 / M10 / M11 / M12 / R4 / A4 / I6 | rigid 중력, Wedge, 엣지 번호, 관 Bridge, 조인트 번호, Playblast 재생기, 참조 컬렉션 줄 | — | 2–3 | — | 없음 |

흐름별 개수: 모델링 12 (bug 5), UV 4 (bug 1 + U2 일부), 애니 4, 리깅 5 (bug 1), FX 4 (bug 1), 렌더 8 (bug 2), 파일 6 (bug 4) = 43.
이미 열린 이슈가 다루는 것: M5 #16, M6 #31, M7 #30, R1 #34, R5 #32, A3 #35 (R2 는 #35 와 관련).

## bug 재현 (새 이슈 후보)

1. **X1** Maya 레이아웃 새 장면 (File > New Scene) → Create > Polygon Primitives > Cube → Render > Render Current Frame: 아무 창도 안 열림,
   콘솔 "Cannot render, no camera". 기대 (Maya): persp 로 렌더한 Render View.
2. **A1** 새 장면 → 큐브 선택 → 1 프레임 S, 24 프레임 Translate X = 5, S → Windows > Animation Editors > Graph Editor: 값 축 0.00–0.05.
   기대: 0–5 (Channel Box 와 같은 cm).
3. **U1** 큐브 / 구를 오브젝트 모드로 선택 → UV > Automatic: 아무 일 없음 (경고). 기대: 6 셸 자동 투영.
4. **I1** 큐브 (Translate 1 2 3, Rotate Y 28.6) → File > Export All → FBX → Maya 2022 에서 Import: Rotate X -90, Scale 100. 기대: Rotate 0 28.6 0, Scale 1.
5. **I2** Maya 에서 pCube1 을 FBX / OBJ 로 내보내 킷에서 File > Import: Rotate X 90; OBJ 는 오브젝트 이름 `maya_cube`. 기대: Rotate 0, 이름 pCube1.
6. **I3 / I4** 같은 큐브를 Alembic / USD / OBJ 로 내보내 Maya 에서 Import: ABC Scale 100, USD 에 root (rx -90, s 100) + env_light, OBJ 이름 Mesh.
7. **M1** 큐브 → 엣지 모드 → 윗면의 마주 보는 엣지 두 개 → Edit Mesh > Connect: 아무 일 없음. 기대: 가운데를 잇는 엣지 (10/15/7).
8. **M2** 큐브 → 정점 모드 → 이웃 정점 두 개 → Edit Mesh > Merge: 그대로 8 정점. 기대: 7 정점 (Always merge for two vertices).
9. **M9** 큐브 → 정점 두 개 → Edit Mesh > Symmetrize: 큐브가 9/11/3 으로 망가짐. 기대: 대칭 엣지를 고르라는 툴, 메시는 그대로.
10. **X2** 오브젝트 → Lighting/Shading > Assign New Material > Blinn → Attribute Editor: Incandescence 흰색, Color 0.8, Specular Roll Off 0.5.
    기대: 검정, 0.5, 0.7.
11. **F1** Fields/Solvers > Gravity / Newton: 크기 1 (Wind / Force +1). 기대: 9.8 아래쪽 가속도 / 5 끌어당김.
12. **R4** 조인트 3개 만들기 → 스켈레톤 지우기 → 다시 조인트 만들기: joint4. 기대: joint1.
13. **U2 일부** UV Editor > Create > Best Plane / Contour Stretch 회색 (메인 UV 메뉴의 같은 항목은 동작).

## 파일

스크립트와 결과는 추적하지 않는 `tmp/audit133_work/` 에 있다: `run_kit.py`, `probes/p00–p10*.py`, `maya/m01–m10*.py`, `gui/gui_work133.py`,
`out/*.json`, `shots/*.png`, `xfer/` (주고받은 FBX / OBJ / ABC / USD).
