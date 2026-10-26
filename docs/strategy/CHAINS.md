# CHAINS — 애니메이션용 캐릭터·소품을 만드는 기능 사슬 지도 (5차, 2026-10-26)

목적: 리깅·디폼·NURBS·애니메이션 기능을 하나씩 보지 않고, **앞 단계의 결과가 다음 단계의 입력이 되는 사슬**로 따라가며 키트에서 어디가 끊기는지 찾는다.
판정과 구현 순서: `ANIM_FOCUS_VERDICT.md`, 1페이지 요약: `SUMMARY5_KO.md`.

표기: **[사실]** 출처나 저장소에서 확인함 · **[추정]** 해석 · **[U]** 모름 · **[delegated]** 묻지 않고 정함
키트 상태: **동작** / **부분** / **회색**(메뉴에 있으나 미구현 + 안내) / **없음** / **막힘**(BLOCKED, 측정에서 막힘)
"끊김" 칸: 앞 단계의 결과를 다음 단계가 받지 못하는 곳. `L<n>`은 §7 끊긴 고리 목록의 번호.

## 0. 확인 방법과 한계

- **메뉴 상태**: `data/menu_status_4.tsv`(오늘 `tools/menu_count.py` 덤프: 2,354행, 동작 1,541 / 회색 814) [사실].
- **고리가 이어지는지**: 저장소 코드·테스트·문서 읽기(Explore 에이전트 + 직접 확인). 직접 다시 읽어 확인한 것은 ✔ 표시: Cluster(`src/allset/operators/rig_maya.py:618-625, 676-680`), Spline IK(`rig_maya.py:226-261`), Bake 옵션(`operators/option_windows.py:255`), SDK 채널(`operators/driven_key.py:43-46` + `ui/channel_box.py:1346-1349`), 회전 채널(`ui/channel_box.py:285-291`), Constrain(`operators/rig_tools.py:47-67`), custom_shape(`ui/ae_layout.py:298`).
- **Blender를 실행하지 않았다.** "Blender 대응" 칸의 Blender 자체 동작은 공식 매뉴얼 근거거나 [추정]이다.
- **빈도 근거 id**: `F 2-1(14)` = FEATURES.md 행 2-1, 독립 출처 14개. `C1–C9` = 이번에 찾은 리깅 교육과정(§8), `G1–G4` = 게임 파이프라인 문서, `T` = 튜토리얼만 있고 교육과정 강의계획서엔 없음. 강의계획서 9개 중 몇 개가 그 단계를 이름으로 다루는지가 "n/9"이다.

---

## 1. 사슬 ① NURBS 커브 → 컨트롤 → 애니메이터 (컨트롤 리그)

Maya 리거의 매일 손: 커브를 그려 컨트롤을 만들고, 오프셋 그룹으로 0을 만들고, 컨스트레인트로 조인트를 움직이고, 채널을 잠근 뒤 애니메이터에게 넘긴다.

| 단계 | Maya 기능 (메뉴 경로) | 이 단계로 오는 이유 → 다음에 넘기는 것 | 빈도 근거 | Blender 대응 | 키트 상태 | 사슬이 끊기는 곳 |
|---|---|---|---|---|---|---|
| 1 | Create > NURBS Primitives > Circle / Square, Create > Curve Tools > CV / EP Curve | 컨트롤 모양이 필요 → **커브 오브젝트** | F 1-20(4), F 2-15(3), C1·C2·C6·C9 컨트롤 = 4/9 | Curve 오브젝트 (NURBS / Bezier) | **동작** — 레거시 Curve + NURBS 스플라인, Maya 크기 (`operators/prim_history.py:233-240, 334`; CV/EP `operators/curves_maya.py:92,123`) [사실]. Square = 빈 오브젝트 아래 커브 4개 (`prim_history.py:348-360`) | — |
| 2 | 셰이프 교체 / 합치기 (`parent -r -s`, 커브 셰이프를 조인트·그룹 아래로) | 모양을 바꾸거나 여러 커브를 컨트롤 하나로 → **컨트롤 = 하나의 트랜스폼** | T (create3dcharacters, YouTube 숏츠) — 강의계획서 0/9, 튜토리얼 다수 [사실] | 본 Custom Shape (아무 오브젝트), Bone Widget 애드온 | **없음** — `parent -s`는 잘못된 플래그로 거부 (`command_line/cmds_dag.py:166-194`). 커브 → 본 모양은 조인트 AE의 "Display as Control Shape" 칸뿐(`ui/ae_layout.py:298` ✔), 커브 숨김·크기 보정 없음 | **L1** 커브를 컨트롤 모양으로 바꾸는 명령이 없음 |
| 3 | Display > Wireframe Color, Attribute Editor > Drawing Overrides (색 번호 0–31) | 좌 파랑 / 우 빨강 / 가운데 노랑 관례 → **색으로 구분되는 컨트롤** | T (YouTube overrideColor) [사실] | Object Color + 뷰포트 Wire Color = Object, 본 색(Bone Color) | **부분** — 메뉴는 Properties Object 탭을 열기만 함 (`ui/menu_map.py:686` ✔), Maya 색 번호 팔레트 없음, 뷰포트 와이어 색 모드를 바꾸지 않아 색이 안 보일 수 있음 [추정], 본 색은 Bind Skin "Colorize skeleton"만 (`operators/skin.py:325-328`) | **L2** 색을 줘도 뷰에서 Maya처럼 보이지 않음 |
| 4 | Edit > Group (Ctrl+G) = 오프셋 그룹, Modify > Match Transformations (조인트 위치로), Modify > Freeze Transformations, Reset | 컨트롤 채널을 0/0/1로 → **애니메이터가 0으로 되돌릴 수 있는 컨트롤** | F 1-4(9, Freeze), F 0-11(8, Group); 오프셋 그룹 = Reddit 스니펫 [사실] | Parent + Apply Transform, Snap | Group **동작** (`operators/group.py:39-64`), Freeze **동작** (커브도 굽고 피벗 유지, `operators/freeze.py:26, 115-152`; 테스트는 메시뿐). **Match Transformations는 오브젝트 모드 전용, 조인트를 대상으로 하면 아마추어 원점으로 감** (`operators/snap_align.py:153-162, 229-231`) | **L3** 오프셋 그룹을 조인트 위치·방향에 맞출 수 없음 |
| 5 | Constrain > Parent / Point / Orient / Aim (컨트롤 → 조인트), Maintain Offset | 컨트롤이 조인트를 움직임 → **구동되는 스켈레톤** | F 2-4(11), C2·C3·C5 = 3/9 | 본 컨스트레인트 (Child Of, Copy Location/Rotation, Track To) | **부분** — 포즈 모드에서 활성 본 + 선택 오브젝트 = 대상 (`operators/rig_tools.py:47-67` ✔, 테스트 `tests/test_step62_rigging_tools.py:175-212`는 Empty로만). **포즈 모드 중 커브를 클릭해 함께 고르는 길이 없음** (`lock_object_modes` 처리 없음, select priority는 오브젝트 모드 전용). 반대 방향(오브젝트가 조인트를 따름)은 본 지정 없이 아마추어가 대상 | **L4** "컨트롤 고르고 → 조인트 고르고 → Parent Constraint"가 손으로 한 번에 안 됨 |
| 6 | Constrain > Pole Vector | 무릎·팔꿈치 방향 컨트롤 → **IK 체인 방향** | F 2-4, 2-5(10) | IK Pole Target | **동작** (`operators/skin.py:259-309`, `tests/test_step140_rig.py:252`) | — |
| 7 | Modify > Add Attribute (컨트롤에 커스텀 속성) | 손가락 말기·IK/FK 같은 스위치 → **드라이버의 입력** | F 2-13(4), C2·C3 = 2/9 | Custom Property | **동작** | — |
| 8 | Key > Set Driven Key, Windows > General Editors > Connection Editor, Node Editor | 속성 하나로 여러 채널 구동 → **조인트 회전·블렌드셰이프·IK 가중치** | F 2-8(6), F 2-14(4), C2·C6 SDK 2/9, C2·C5 노드 2/9, 유료 애드온 "Set Driven Key"가 팔림 [사실] | 드라이버 (+ Action Constraint) | **부분** — 커스텀 속성 → 조인트 회전 **동작·테스트 있음** (`tests/test_step62_rigging_tools.py:135-172`). **SDK 창의 채널 = 트랜스폼 + 커스텀만** (`operators/driven_key.py:43-46` ✔) → 셰이프 키 가중치·컨스트레인트 Influence는 구동 못 함. Connection Editor·`connectAttr`은 오브젝트만 (`ui/connection_editor.py:47-68`) | **L5** 컨트롤 속성 → 블렌드셰이프 / IK 가중치 / 포즈 본이 안 이어짐 |
| 9 | Channel Box > Lock and Hide Selected, Make Nonkeyable; Windows > General Editors > Channel Control | 애니메이터가 건드리면 안 되는 채널 정리 → **깨끗한 컨트롤** | F 2-23(2), C 등급 | lock_location / rotation / scale | Lock·Hide **동작** (오브젝트·포즈 본, `ui/channel_box.py:195-206, 1449-1470`, 매니퓰레이터가 잠금을 지킴). Nonkeyable은 키트 플래그라 Blender I 키는 무시. Channel Control 창은 **회색** | (작음) Channel Control 목록 창 없음 — Channels 메뉴로 대체 |
| 10 | Control > Tag As Controller | 피킹·평가 최적화 | 근거 0 (이번 수집) | 없음 | **회색** | 끊김 아님 (영향 작음) [추정] |
| 11 | 애니메이터: 뷰에서 컨트롤 클릭, S / Shift+W/E/R, 홀드 키 | 컨트롤 선택 → **키** | F 4-2(6), F 0-3(7) | Pose 모드 선택, I | **동작** — 커브가 메시보다 먼저 선택됨 (`operators/select_priority.py:22-31`), S는 오브젝트·포즈 본 (`operators/time_keys.py:111-142`). 단 쿼터니언 본은 회전 키 없음(사슬 ⑤ L19) | — |
| 12 | Graph Editor (그 컨트롤의 커브) | 타이밍 다듬기 | F 4-1(11) | Graph Editor | **동작** (키트 채널 목록, step 150) | 사슬 ⑤로 이어짐 |

**사슬 ①의 그림**: 커브 ✔ → 컨트롤 모양 ✖(L1) → 색 △(L2) → 오프셋 그룹 △(L3) → 컨스트레인트 △(L4) → Pole ✔ → 속성 ✔ → SDK △(L5) → 잠금 ✔ → 키 ✔ → Graph Editor ✔
**발견(경계 넓히기)** [추정]: Maya 방식(커브 오브젝트가 컨스트레인트로 본을 움직임)과 Blender 방식(같은 아마추어 안의 컨트롤 본 + Custom Shape)은 갈린다. Maya 손에 맞는 것은 앞쪽, FBX·Rigify·성능에 맞는 것은 뒤쪽이다. 키트는 지금 앞쪽만 반쯤 된다. → 판정 문서 §3의 설계 선택.

---

## 2. 사슬 ② NURBS 커브 → IK Spline / Motion Path / Wire / Loft(리본)

| 단계 | Maya 기능 (메뉴 경로) | 이유 → 넘기는 것 | 빈도 근거 | Blender 대응 | 키트 상태 | 끊김 |
|---|---|---|---|---|---|---|
| 2a-1 | Skeleton > Create IK Spline Handle (자동 커브 / **기존 커브 사용**, Auto Create Curve 끔) | 꼬리·척추·촉수 → **커브가 체인을 끌고 감** | F 2-21(1 추정), C3·C5·C9 = 3/9, C1 촉수 과제 [사실] | Spline IK 컨스트레인트 (어떤 커브든 대상) | **부분** — 항상 새 커브를 만듦, 옵션은 Root on curve뿐 (`operators/rig_maya.py:226-261` ✔) | **L6** 미리 그린 커브로 Spline IK를 못 만듦 |
| 2a-2 | Deform > Cluster (커브 CV 선택 → 클러스터) | CV마다 손잡이 → **클러스터를 컨트롤에 부모** | C9·T (스파인 리그) [사실] | Hook 모디파이어 (커브 점 인덱스) | **부분** — 메시만 선택 정점 사용. **커브는 bound box 중심 + 점 인덱스 없음 → Hook이 아무것도 안 움직임** (`rig_maya.py:618-625, 676-680` ✔; CLAUDE.md step 110 "neither a vertex group nor vertex_indices_set moves nothing") | **L7** 커브 CV 클러스터가 커브를 못 움직임 → 2a-1과 함께 스파인 리그 전체가 막힘 |
| 2a-3 | 클러스터 → 컨트롤에 Parent, Advanced Twist | 컨트롤로 척추 구동 | C5 W5 [사실] | Hook 대상 = 컨트롤 오브젝트, Spline IK Twist는 별도 | [U] — L7이 막혀 확인 불가 | (L7 뒤) |
| 2b-1 | Constrain > Motion Paths > Attach to Motion Path (U 값, Follow, Front/Up Axis, 시작·끝 시간 키) | 경로 애니 (카메라, 차, 비행) → **U에 키가 있는 오브젝트** | F 4-5(6, A) | Follow Path (Offset / Animate Path) | **부분** — 그냥 Follow Path, 옵션 창 없음, U·Follow·축 없음 (`ui/menu_map.py:439`, `operators/rig_tools.py:29`, 안내 `ui/notices.py:337`). Maya 선택 순서(오브젝트 → 경로 마지막)인데 키트는 마지막 선택에 컨스트레인트 → **커브에 붙을 가능성** [추정, 코드 읽기] | **L8** 선택 순서·U 키·축 옵션 |
| 2b-2 | Constrain > Motion Paths > Flow Path Object | 경로 따라 휘기 (Lattice) | F 4-5 하위 | Curve 모디파이어 | **회색** | **L9** (낮음) |
| 2b-3 | Constrain > Motion Paths > Set Motion Path Key | 경로 위 위치 키 | F 4-5 하위 | Follow Path offset 키 | **회색** | L8에 포함 |
| 2c | Deform > Wire (커브 → 메시) | 입술·눈썹·케이블 | F 2-16 계열, C 등급 | (GN으로 키트가 구현) | **동작** — mayapy 일치 (`operators/wire_deformer.py`, step 169) | — |
| 2d-1 | Surfaces > Loft / Revolve / Extrude (Output: NURBS / **Polygons**) | 커브 두 줄 → 리본 서피스, 또는 메시 만들기 | C1 리본 1/9 + 튜토리얼; 게임 리그는 "리본 안 씀"(G3 Mutant Tools) [사실] | Curve 베벨·Curve to Mesh, B-Bones | **부분** — NURBS 서피스만, "Polygons / Bezier not made" (`operators/option_windows_surfaces.py:12`) | **L10** 폴리곤 출력 없음 |
| 2d-2 | Modify > Convert > NURBS to Polygons | 서피스 → 메시 | — | Convert to Mesh | **동작** (Blender 변환, Maya 옵션 없음, `ui/menu_map.py:283`), UV 생성 여부 [U] | L10에 포함 |
| 2d-3 | Constrain > UV Pin / Proximity Pin (리본 위 Follicle 대체) → 조인트 | 서피스 위 점 → **리본 조인트** | C1 + 튜토리얼 | Copy Transforms / Shrinkwrap, B-Bones | **부분** — 메시만, UV 필요 (`operators/pins_205.py:463, 591, 635, 653`), 핀이 움직이는 건 오브젝트(본 아님) | L10에 포함 (메시 → 빈 오브젝트 → 본 컨스트레인트 = 3단계 우회) |

**사슬 ②의 그림**: 커브 ✔ → Spline IK(기존 커브) ✖(L6) → CV 클러스터 ✖(L7) → 컨트롤 [U] / 커브 → Motion Path △(L8) → Flow Path ✖(L9) / 커브 → Wire ✔ / 커브 → Loft △(L10) → 메시 ✔ → 핀 △ → 조인트 △

---

## 3. 사슬 ③ 조인트 → 스킨 → 엔진 (캐릭터 · 스킨 프롭)

| 단계 | Maya 기능 | 이유 → 넘기는 것 | 빈도 근거 | Blender 대응 | 키트 상태 | 끊김 |
|---|---|---|---|---|---|---|
| 3-1 | Skeleton > Create Joints | **스켈레톤** | F 2-3(11), C 7/9 | Armature 압출 | **동작** (first_hour #24 OK) | — |
| 3-2 | Skeleton > Orient Joint, Display > Transform Display > Local Rotation Axes | 축 정리 → 회전이 예측 가능 | F 2-7(6), C1·C2·C5 = 3/9 | Bone Roll (본 축은 Y 고정, B-dev 문서) | **동작** (`ui/menu_map.py:412`) — 단 jointOrient는 rest 포즈에서 읽기 전용 표시 (`ui/attribute_editor.py:349-361`) | 3-14에서 깨짐 (L11) |
| 3-3 | Skeleton > Mirror Joints, Joint Labelling | 좌우 → **라벨로 웨이트 미러** | F 2-20(1–2) | Symmetrize, 이름 .L/.R | **동작** (`operators/joint_labels.py`) | — |
| 3-4 | Skeleton > Create IK Handle (RP / SC) + Pole Vector | 다리·팔 IK | F 2-5(10), C 3/9 | IK 컨스트레인트 | **동작** (`operators/skin.py:96-130`; first_hour #25, #28 OK) | — |
| 3-5 | Key > IK/FK Keys, Skeleton > Enable IK/FK Control (또는 리그 방식 IK/FK 블렌드 체인) | 팔 IK ↔ FK 전환 → **애니메이터의 스위치** | F 2-10(4), C3·C5·C9 = 3/9 | IK Influence 키, Rigify 스냅 버튼 | **회색** (6항목) — IK Influence 행은 Channel Box에 있음 (`ui/channel_box.py:1799, 2198`), 매칭·FK 포즈 없음, S가 컨스트레인트 행을 키하지 않음 (`operators/time_keys.py:111-115`) | **L14** IK/FK 전환·매칭 |
| 3-6 | Skin > Bind Skin (Max Influences 4) | **스킨 메시** | F 2-2(13), C 9/9 (모든 강의) | Automatic Weights | **동작** (Maya closest distance, mayapy 일치, step 149) | — |
| 3-7 | Skin > Paint Skin Weights (B+드래그 크기, Q로 나가기, 뷰에서 조인트 고르기) | 웨이트 다듬기 | F 2-1(14, 1위), C1 W5 NGSkinTools, Superhive Voxel Heat Diffuse Skinning 13,000+ 판매 [사실] | Weight Paint 모드 | **부분** — 도구 동작, **Q가 페인트를 안 끝냄** (first_hour #27 AWKWARD), B = Blender radial (`keymap/maya_patches.py:1201`) | **L13** 페인트 → 다음 도구로 손이 안 넘어감 |
| 3-8 | Windows > General Editors > Component Editor | 숫자로 웨이트 | F 2-11(3) | N 패널 Vertex Weights | **동작** (step 213), 메뉴 57 % | — |
| 3-9 | Skin > Mirror / Copy Skin Weights | 좌 → 우, 옷·LOD로 복사 | F 2-9(5), F 2-12(3) | Mirror Vertex Group, Data Transfer | **동작** (`tests/test_step159_labels.py:248-304`) | — |
| 3-10 | Skin > Prune Small Weights, Normalize, Set Max Influences | 엔진 제한(정점당 4) | F 2-18(2), G1 Unreal 4/8, G2 Unity 1/2/4 [사실] | Clean / Normalize / Limit Total | **동작** | — |
| 3-11 | Skin > Export / Import Weights (deformerWeights XML) | 웨이트 백업·다른 메시로 | C 등급 | 없음 (애드온) | **동작** (`operators/deformer_weights.py`) | — |
| 3-12 | (게임) 루트 조인트 추가, 컨트롤 리그는 남기고 바인드 조인트만 | 엔진은 디포머·컨트롤을 안 읽음 → **DEF 본만** | G3 Mutant Tools "only Bind_Joints_Grp is exported" [사실] | FBX "Only Deform Bones" | 부분 — Quick Rig = Rigify 메타리그, DEF만 내보내는 길은 안내 없음 (TOP40 #18) | (L11의 일부) |
| 3-13 | Key > Bake Simulation (컨스트레인트·IK를 조인트 키로) | 엔진용 굽기 | F 4-11(2), G4 mGear 포럼 [사실] | Bake Action (Visual Keying) | **부분** — 동작하지만 **"Keep unbaked keys"를 끄면 컨스트레인트를 지움** (`operators/option_windows.py:255` `clear_constraints=not keep_unbaked` ✔). Maya의 그 옵션은 "굽지 않은 키 유지"이지 컨스트레인트 삭제가 아님 [추정: Maya는 별도 옵션] | **L18** 옵션 의미가 다름 → 리그가 조용히 망가짐 |
| 3-14 | File > Export Selection (FBX: Skins, Blend Shapes, Bake Animation) → Unity / Unreal | **에셋 끝** | F 3-1(7), F 3-2(4), G1·G2 | FBX Export | **막힘** — Maya에서 열면 `skeleton1` 아래 rotate −90 / scale 100, jointOrient 없이 rotate에 방향 (first_hour #39; `research/maya/re/first_hour_217_kit_fbx_in_maya.json`) | **L11** 리그 FBX |
| 3-15 | File > Import (FBX 스킨 메시, 외주·엔진 에셋) | 받은 리그로 다시 작업 | F 3-8(3) | FBX Import | **막힘** — 0.01 배·90°, 스켈레톤 1.5 배 (first_hour #37) | **L12** 스킨 FBX 가져오기 |

**사슬 ③의 그림**: 조인트 ✔ → 오리엔트 ✔ → 미러·라벨 ✔ → IK ✔ → IK/FK ✖(L14) → 바인드 ✔ → 페인트 △(L13) → Component Editor ✔ → 미러·복사 ✔ → Prune·Max 4 ✔ → 웨이트 내보내기 ✔ → (루트·DEF만 △) → Bake △(L18) → **FBX ✖(L11)** → 엔진 / 다시 가져오기 ✖(L12)
**발견** [사실: B-dev 문서, devtalk]: Blender 본은 Y축 고정, 메시별 바인드 행렬이 없다. L11은 키트가 축·단위 변환을 본에 구워 우회해야 하고, 애드온으로 완전히 없앨 수 없는 한계가 남을 수 있다 [추정].

---

## 4. 사슬 ④ 디포머 → 교정 셰이프

| 단계 | Maya 기능 | 이유 → 넘기는 것 | 빈도 근거 | Blender 대응 | 키트 상태 | 끊김 |
|---|---|---|---|---|---|---|
| 4-1 | Deform > Blend Shape, Windows > Animation Editors > Shape Editor | 얼굴·교정 → **타깃 가중치** | F 2-6(7), C2·C6·C9·G1 = 4 [사실] | Shape Keys | **동작** (step 213) | — |
| 4-2 | Shape Editor > Add In-Between Target, Combination Target | 중간 모양·조합 교정 | C9 "Mirror & Combo Shapes", C4·C6 교정 [사실] | (없음 — 드라이버로) | **회색** (`ui/notices.py:908-918`) | **L15** 인비트윈·조합 타깃 |
| 4-3 | Key > Set Blend Shape Target Weight Keys | 셰이프 가중치 키 | F 2-6 하위 | Shape Key Value 키 | **회색** | **L15b** (S) |
| 4-4 | Set Driven Key로 블렌드셰이프 구동 (조인트 회전 → 교정 셰이프) | 팔꿈치 접힘 교정 → **자동 교정** | C 교정 5/9 (C1·C4·C6·C7·C9), CGMA 블로그 "driven by controllers and SDK" [사실] | 드라이버 → Shape Key Value | **없음** — SDK 창이 셰이프 키를 못 고름 (사슬 ① L5와 같은 원인) | **L5** |
| 4-5 | Deform > Pose Space Deformation > Create Pose Interpolator, Windows > Pose Editor | 포즈 기반 교정 | C 교정 계열 | (없음 — 드라이버 + 셰이프 키, Pose Shape Keys 애드온) | **회색** | **L16** (L5 뒤에 대체 경로 가능) |
| 4-6 | Deform > Cluster (메시 정점) | 부분 변형 손잡이 | F 2-16(3) | Hook | **동작** (`tests/test_step110_model_rig.py:335-360`) | — |
| 4-7 | Deform > Lattice, Nonlinear (Bend / Squash / Twist / Sine / Flare / Wave) | 큰 덩어리 변형, 스쿼시 | F 2-16(3), F 1-25(3), C6 W8 Lattice | Lattice, Simple Deform | **동작** | — |
| 4-8 | Deform > Wrap / Delta Mush / Tension / Jiggle | 고해상도 따라가기, 부드럽게, 흔들림 | C5·C6 디포머 2/9 (영화 쪽) [사실] | Surface Deform, Corrective Smooth, GN | **동작** (Tension·Jiggle = 키트 GN, step 205) — **성능 [U]** (문서에 측정 없음) | 성능 [U] |
| 4-9 | Inputs 목록 순서 바꾸기 (RMB > Inputs > All Inputs…, 가운데 드래그), Deformation Order 옵션 | 스킨 앞·뒤 순서가 결과를 바꿈 | T (리깅 강의 공통 함정) [추정] | 모디파이어 순서 | **없음** — 목록·켜기/끄기만 (`marking/rmb_nodes.py:250-293`), Deformation order 옵션 없음 (`operators/option_windows_deform.py:7-8, 29`) | **L17** 디포머 순서 |
| 4-10 | Deform > Paint Weights > (각 디포머) | 디포머 영향 범위 | F 2-1 계열 | Vertex Group 페인트 | **동작** (`ui/menu_map.py:799-813`) | — |
| 4-11 | Deform > Edit Membership Tool | 영향 정점 추가·빼기 | C 등급 | Vertex Group 편집 | **회색** | (작음) Paint Weights로 대체 |
| 4-12 | FBX: 블렌드셰이프만 엔진으로 (다른 디포머는 굽거나 버림) | 엔진은 조인트 + 모프 타깃만 | G1 Unreal Morph Target 문서, G3 [사실] | FBX Shape Keys | 부분 — 메시는 동작, 리그 쪽 L11 | L11 |

**사슬 ④의 그림**: 블렌드셰이프 ✔ → 인비트윈·조합 ✖(L15) → 가중치 키 ✖(L15b) → SDK 구동 ✖(L5) → 포즈 교정 ✖(L16) / 클러스터·격자·논리니어·Wrap·Delta Mush ✔ → 순서 ✖(L17) → 페인트 ✔ → 엔진 (모프만) △(L11)

---

## 5. 사슬 ⑤ 애니메이션 → 엔진 (받은 리그 포함)

| 단계 | Maya 기능 | 이유 → 넘기는 것 | 빈도 근거 | Blender 대응 | 키트 상태 | 끊김 |
|---|---|---|---|---|---|---|
| 5-0 | (받은 리그) Rigify·Auto-Rig Pro·외주 리그를 열고 컨트롤 선택 | 애니메이터 대부분은 리그를 받아 씀 (Animation Mentor가 리그를 줌) [사실] | Superhive Auto-Rig Pro 70,400+ 판매 [사실] | Pose 모드 | **부분** — 커스텀 속성(IK_FK)은 CB 커스텀 채널로 보임 (`ui/channel_box.py:211-219`). **쿼터니언 본은 Rotate X/Y/Z 행이 없음** (`ui/channel_box.py:285-291` ✔: ROT은 오일러일 때만) → **S·Shift+E가 회전을 안 키함**. Pick walk가 숨은 본으로 들어감 (`operators/joints.py:498-510`). Rigify 테스트는 메타리그 추가뿐 | **L19** 쿼터니언 본, **L20** 숨은 본 pick walk |
| 5-1 | Key > Set Key (S), Shift+W/E/R, Auto Key | **키** | F 4-2(6), F 4-10(2) | I, 자동 키 | **동작** (오일러) — 단 **Translate Y가 위가 아님** (first_hour #30 AWKWARD) | **L23** Translate Y (TOP40 #3) |
| 5-2 | Time Slider (범위·스크럽·키 틱), Range Slider | 타이밍 | F 4-6(5) | Timeline | **동작** (steps 56, 73, 186) | — |
| 5-3 | Graph Editor: 탄젠트, Buffer Curve, Pre/Post Infinity (Cycle) | 커브 다듬기, 걷기 사이클 | F 4-1(11), F 4-8 | Graph Editor, Cycles 모디파이어 | **동작** (탄젠트 first_hour #31–32 OK, Infinity `operators/graph_keys.py:450-483`, Buffer `operators/graph_buffers.py`). Region Keys / Lattice Deform Keys **회색**, 길이 커브 미터 표시 | TOP40 #27–29 (손 감각) |
| 5-4 | Dope Sheet | 키 리타이밍 | F 4-1 계열 | Dope Sheet | **동작** (메뉴 87 %) | — |
| 5-5 | Windows > Relationship Editors > Animation Layers | 원본 위에 수정 | F 4-14(0 이번 수집), Superhive Animation Layers 9,700+ 판매 [사실] | NLA / **Layered Actions (Blender 개발 중)** | **동작** (NLA 트랙, steps 180/194/204) | **위험**: Blender 2026 계획 "animation layers… work expected to start during Q2" [사실] → 키트 구현이 겹치거나 깨질 수 있음 [추정] |
| 5-6 | Visualize > Ghost Selected, Create Editable Motion Trail | 아크 확인 | F 4-12(1), F 4-5(6) | Onion skin 애드온, Motion Paths | **부분** — 고스트는 지오메트리만(스킨 메시는 됨, 본은 안 됨) (`ui/ghosting.py:31, 417`), 모션 트레일은 오브젝트 모션 패스 = 편집 불가, 포즈 본 버전 없음 (`ui/menu_map.py:480`) | **L21** 본(컨트롤)의 편집 가능한 모션 트레일 |
| 5-7 | Windows > Playblast | 리뷰 | F 4-7(4) | Viewport Render Animation | **동작** (step 70) | — |
| 5-8 | Key > Bake Simulation | 엔진용 굽기 | F 4-11(2) | Bake Action | **부분** (사슬 ③ L18) | L18 |
| 5-9 | File > Game Exporter (Animation Clips 탭), Time Editor 클립 | 클립 = 엔진 애니 | F 3-6(3), F 4-3(7) | NLA 액션 + FBX | **부분** — Blender FBX 창을 그대로 엶 (`ui/menu_map.py:632`), 레이어 → FBX는 테스트 없음 [U] | **L24** 레이어·클립 → FBX, TOP40 #24–25 |
| 5-10 | FBX (리그 애니) / Cache > Alembic > Export | 엔진 / 렌더 | F 3-4(3) | FBX / Alembic | 메시 애니 **동작** (step 138), 리그 FBX **막힘** (L11) | L11 |

**사슬 ⑤의 그림**: 받은 리그 △(L19 쿼터니언, L20) → S ✔(Y-up △ L23) → Time Slider ✔ → Graph Editor ✔(손 감각 미확인) → Dope Sheet ✔ → 레이어 ✔(Blender와 겹칠 위험) → 고스트 △ / 트레일 ✖(L21) → Playblast ✔ → Bake △(L18) → 클립·Game Exporter △(L24) → **FBX ✖(L11)**

---

## 6. 다섯 사슬이 만나는 곳 (교차점)

| 교차 고리 | 걸리는 사슬 | 왜 중요한가 |
|---|---|---|
| **L11 리그 FBX** | ③ ④ ⑤ | 세 사슬의 끝이 모두 여기서 막힌다. "에셋이 끝났다"(DIRECTION)의 정의 |
| **L5 SDK 대상 (셰이프 키·컨스트레인트 가중치·포즈 본)** | ① ④ (③ IK/FK) | 컨트롤 → 얼굴, 조인트 → 교정 셰이프, 스위치 → IK 가중치 모두 같은 원인 |
| **L18 Bake 옵션** | ③ ⑤ | 조용히 컨스트레인트를 지우는 정확성 문제 — 작고 위험 |
| **L19 쿼터니언 본** | ⑤ (받은 리그), ③ (FBX 가져온 리그 [추정]) | 받은 리그에서 S가 회전을 안 키함 = 애니메이터 경로의 첫 단계 |
| **L1 + L4 컨트롤 설계** | ① ② ③ | 커브 오브젝트 컨트롤이냐 본 Custom Shape냐가 컨스트레인트·FBX·성능을 함께 정함 |

---

## 7. 끊긴 고리 목록 (크기: S 하루 · M 한 step · L 여러 step / 해법 불확실)

| id | 고리 | 사슬 | 크기 | 할 일 (한 줄) |
|---|---|---|---|---|
| L1 | 커브 → 컨트롤 모양 (`parent -s`, 셰이프 교체) | ① | M | "커브를 이 조인트/컨트롤의 모양으로": 선택 커브(들)를 본 Custom Shape(또는 오브젝트 컨트롤의 데이터 교체)로, 커브는 숨김 컬렉션, 크기·오프셋 보정, `cmds.parent(s=True, r=True)`도 같은 함수 |
| L2 | 컨트롤 색 (Maya 색 번호) | ① | S–M | Drawing Overrides 32색 팔레트 → Object Color + 키트 뷰의 Wire Color = Object(뷰 설정, 환경설정 아님), 본은 Bone Color custom |
| L3 | Match Transformations → 조인트 | ① | S | 대상이 포즈 본이면 본의 world 행렬 사용 |
| L4 | 컨트롤 + 조인트 함께 선택 → 컨스트레인트 | ① | M | 포즈 모드 중 커브 클릭 = 그 오브젝트를 추가 선택(`tool_settings.lock_object_modes` 다루기), "오브젝트가 조인트를 따름"은 subtarget = 본 |
| L5 | SDK / Connection Editor 대상 확장 | ① ④ ③ | M | Driven 목록에 셰이프 키 가중치(INPUTS blendShape), 컨스트레인트 가중치, 포즈 본 채널 추가 |
| L6 | Spline IK에 기존 커브 | ② | S | Auto Create Curve 끔 = 선택한 커브를 대상으로 |
| L7 | 커브 CV 클러스터 | ② | S | 편집 모드 선택 CV 인덱스 → `vertex_indices_set`, 오브젝트 모드는 모든 점; Spline IK가 따라 움직이는 테스트 |
| L8 | Attach to Motion Path 옵션·선택 순서 | ② | M | Maya 선택 순서, U 값 0→1 키(Time Slider 범위), Follow / Front / Up 축 옵션 창 |
| L9 | Flow Path Object | ② | M | Lattice + 경로 (낮음) |
| L10 | Loft 폴리곤 출력 + 리본 | ② | M | Output Polygons(+UV), 핀이 본을 직접 구동 (낮음: 게임 리그는 리본을 피함 G3) |
| L11 | **리그 FBX 내보내기** (+ jointOrient) | ③ ④ ⑤ | **L** | 단위·축 변환을 본에 굽기, 루트 여분 노드 제거, DEF 본만, mayapy 왕복 검증 (TOP40 #19) |
| L12 | 스킨 FBX 가져오기 | ③ ⑤ | M | 아마추어에 붙은 메시도 축·단위 보정 (TOP40 #23) |
| L13 | Paint Skin Weights 손 (Q 나가기, B+드래그) | ③ | S | TOP40 #10, #11 |
| L14 | IK/FK 전환·매칭 | ③ ⑤ | M | Set IK/FK Key, Move IK to FK, Rigify 스위치도 같은 메뉴 (TOP40 #15) |
| L15 | 인비트윈·조합 타깃 | ④ | M | 인비트윈 = 가중치 구간별 드라이버로 켜지는 셰이프 키, 조합 = 두 가중치 곱 드라이버 |
| L15b | Set Blend Shape Target Weight Keys | ④ | S | TOP40 #13 |
| L16 | 포즈 교정 (Pose Interpolator 대체) | ④ | M | L5 뒤: "조인트 회전 → 교정 셰이프" 한 번에 만드는 창 |
| L17 | 디포머 순서 | ④ | S–M | INPUTS / All Inputs 목록에서 순서 바꾸기 = `modifier_move_to_index`, Deformation order 옵션 |
| L18 | **Bake Simulation "Keep unbaked keys" = 컨스트레인트 삭제** | ③ ⑤ | S | 옵션 의미를 Maya에 맞추고 컨스트레인트 삭제는 별도 옵션 |
| L19 | **쿼터니언 본 회전 채널** | ⑤ | M | 쿼터니언 본에 Rotate X/Y/Z 표시·키(오일러 표시 변환 또는 "오일러로 바꾸기" 버튼), S가 회전 키 |
| L20 | pick walk 숨은 본 | ⑤ | S | 숨은 본·숨은 본 컬렉션 건너뛰기 |
| L21 | 본의 편집 가능 모션 트레일 | ⑤ | M–L | 포즈 본 모션 패스 + 점 드래그 = 키 이동 |
| L23 | Translate Y = 위 | ⑤ ① | M | TOP40 #3 |
| L24 | 레이어·클립 → FBX | ⑤ | S(확인) + M(Game Exporter) | 먼저 테스트로 확인, 이어서 TOP40 #24–25 |

(L22 = 고스트 본 버전은 스킨 메시로 대신 볼 수 있어 뺐다 [delegated].)

---

## 8. 출처 (이번에 새로 찾은 것; FEATURES 출처는 `data/web/features4_sources_a.md`, `_b.md`)

교육과정 [사실, 강의계획서·예고편 자막]
- C1 Rigging Dojo Character Rigging 101 — https://www.riggingdojo.com/rigging-101-course (W2 조인트·오리엔트, W3 스키닝·컨트롤, W4 촉수·스페이스 스위치, W5 트위스트·교정 셰이프)
- C2 AnimSchool Intro to Rigging — https://animschool.edu/ClassDetails?courseid=11 ("constraints, skinning, blendshapes… curve controls, custom attributes, sets, Set Driven Keys")
- C3 Gnomon Character Rigging Fundamentals — https://www.gnomon.edu/academics/individual-courses/course-list/character-rigging-fundamentals ("IK, FK, and spline IK controls")
- C4 Gnomon Character Rigging for Production — https://www.gnomon.edu/academics/individual-courses/course-list/character-rigging-for-production ("Corrective blendshapes")
- C5 CGMA Intro to Rigging (10주, 예고편) — https://www.youtube.com/watch?v=WY-R1aUw8WA (W3 노드·커넥션 에디터, W4 IK·스플라인·디포머, W9 스키닝)
- C6 CGMA Character Facial Rigging — https://www.cgmasteracademy.com/courses/13-character-facial-rigging-for-production.html ; 블로그 https://www.cgmasteracademy.com/blog/8-steps-to-rig-an-expressive-character-and-their-clothes.html
- C7 CAVE Academy Introduction to Rigging — https://caveacademy.com/wiki/post-production-assets/rigging/rigging-training/introduction-to-rigging-course/11-corrective-blendshapes (10 스키닝 → 11 교정 셰이프)
- C8 Udemy Maya & Unreal — https://www.udemy.com/course/maya-unreal-complete-guide-to-fast-3d-animation-rigging
- C9 Gnomon Workshop Character Rigging path — https://www.thegnomonworkshop.com/learning-path-character-rigging (스플라인 IK 척추, FK/IK 스위치, Mirror & Combo Shapes)

게임 [사실]
- G1 Unreal 영향 수 — https://dev.epicgames.com/documentation/unreal-engine/skeletal-mesh-rendering-paths-in-unreal-engine ; 모프 타깃 — https://dev.epicgames.com/documentation/unreal-engine/fbx-morph-target-pipeline-in-unreal-engine
- G2 Unity skinWeights — https://docs.unity3d.com/6000.6/Documentation/ScriptReference/QualitySettings-skinWeights.html
- G3 Mutant Tools 게임 리깅 — https://mutanttools.com/game-character-rigging-maya ("only Bind_Joints_Grp is exported", "no ribbons")
- G4 mGear 포럼 Bake — http://forum.mgear-framework.com/t/bake-animation-on-joints-skeleton/477

컨트롤·Blender [사실]
- 셰이프 부모 — https://create3dcharacters.com/maya-shape-parent-curve-controls , https://www.youtube.com/shorts/OnPtXI0X9xU ; overrideColor — https://www.youtube.com/watch?v=A9vJ51YRGRk
- Bone Widget — https://extensions.blender.org/add-ons/bone-widget
- Blender 애니·리깅 모듈 프로젝트 목록(본 Y축 고정, Rig Nodes는 계획만) — https://developer.blender.org/docs/features/animation/module/projects ; 바인드 행렬 없음 — https://devtalk.blender.org/t/rigging-orientation-mismatch-between-blender-and-other-dccs/39901
- Spline IK — https://docs.blender.org/manual/en/latest/animation/armatures/posing/bone_constraints/inverse_kinematics/spline_ik.html ; Follow Path — https://docs.blender.org/manual/en/latest/animation/constraints/relationship/follow_path.html ; Hook — https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/hooks.html ; B-Bones — https://docs.blender.org/manual/en/latest/animation/armatures/bones/properties/bendy_bones.html
- Blender 2026 계획(애니 레이어 Q2 시작) — https://www.blender.org/development/projects-to-look-forward-to-in-2026 ; 로드맵 — https://www.blender.org/roadmap
- 판매 수(2026-10-26 페이지 "Sales") — https://superhivemarket.com/products/auto-rig-pro , …/voxel-heat-diffuse-skinning , …/animation-layers , …/faceit , …/boxcutter , …/hardopsofficial ; SDK 유료 도구 — https://superhivemarket.com/products/set-driven-key
- Animation Mentor 리그 제공 — https://www.animationmentor.com/animation-program/animation-characters
