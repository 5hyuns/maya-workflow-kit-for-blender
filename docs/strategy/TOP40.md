# TOP40 — 구현 목록 (4차, 2026-10-26)

근거·표: `FEATURES.md` (괄호 안 `n-m`은 그 표의 행 번호). 영역 순서는 DIRECTION.md(0 손 → 1 모델링+UV → 2 리깅+스킨+디포머 → 3 엔진 내보내기 → 4 애니메이션)를 따르고, 영역 안에서는 빈도(근거 수) 순서로 놓았다. 5 렌더·6 FX는 넣지 않았다.

**고른 규칙**: 빈도 A·B인데 키트 상태가 부분·회색·없음인 것만 넣었다. 이 조건에 맞는 일은 **31개**다(같은 원인은 하나로 합침: Translate Y 0-4 = 4-4, LOD 1-21 = 3-9).
40개를 채우려고 **V 9개**를 더했다. V는 "상태는 동작인데 사람이 손으로 확인한 적 없는 A 등급 기능"의 확인 작업이다. 키트의 수동 확인 목록은 667개가 미체크, 106개가 체크다(`docs/manual_checks.md`) [사실]. V는 구현이 아니라 확인이므로 31개와 따로 센다.

크기: **S** 하루 안 · **M** 한 step(며칠) · **L** 여러 step이거나 해법이 확실하지 않음.
빈도: **A** 근거 6개 이상 · **B** 3–5개 · '추정' = 근거 1개 또는 간접 근거.

| 순위 | 기능 | 영역 | 빈도 | 현재 상태 | 할 일 (한 줄) | 크기 |
|---|---|---|---|---|---|---|
| 1 | Rotate 매니퓰레이터 (E) (0-2) | 0 손 | A · 8 | 부분: Move·Scale은 Maya 것, Rotate는 Blender C 기즈모 | Maya Rotate 링(축 링 + 뷰 링 + 자유 회전 구)을 Python 기즈모로 그린다. 뒤쪽 반 클리핑은 셰이더 깊이로 흉내 낼 수 있는지 먼저 시험한다 | L |
| 2 | 옵션 박스 ❒ (0-21) | 0 손 | B · 4 | 부분: 507개 중 Maya 창 176개 | 이 목록의 A·B 명령 중 옵션 박스가 `generic`·`dead`로 나오는 것을 `menu_count.py --options --greyed`로 뽑아 Maya 창으로 만든다 | M |
| 3 | **Translate Y = 위** (0-4, 4-4) | 0 손 (+4) | B 추정 (측정 점수 6.0 공동 1위) | 부분: first_hour #30 AWKWARD | Z-up은 그대로 둔다(결정 5). Channel Box·AE·Graph Editor 채널 이름에 Maya 축을 보여 준다(예: "Translate Z (Maya Y, up)"), 또는 "Maya 축 이름" 표시 옵션. Y에 키를 넣을 때 Help Line에 한 줄 안내 | M |
| 4 | Undo 깊이 (0-19) | 0 손 | B · 3 | 부분: Blender 기본 32, 키트는 환경설정을 쓸 수 없음 | 환영 창과 Preferences 페이지에 "Undo Steps 256" 버튼을 둔다. 버튼은 Blender 환경설정 해당 칸을 열기만 하고, 값은 사용자가 바꾼다(스토어 규칙) | S |
| 5 | **UV Editor 열기** (1-30) | 1 모델링+UV | A · 7 | 부분: 새 창 + 편집 모드로 바뀜 (first_hour #13) | Maya처럼 패널(현재 창의 영역)로 열고, 오브젝트 모드를 그대로 둔다. 선택한 오브젝트의 UV를 보여 준다 | M |
| 6 | Quad Draw 남은 것 (1-3) | 1 | A · 7 | 부분: 이슈 #89 OPEN | 오버레이 색 옵션, Tab+MMB 스트립 크기, Ctrl+Shift+RMB 옵션 메뉴 3가지 | M |
| 7 | **LOD Group / Generate LOD Meshes** (1-21) | 1 | B · 5 | 회색 | LOD 그룹 = Empty + `<name>_LOD0..n` 자식(Decimate 비율 = Maya 기본값). 엔진이 LOD로 읽는지는 #25에서 함께 확인 | M |
| 8 | UV 투영을 오브젝트 전체에 (1-31) | 1 | B · 4 | 부분: 편집 모드 + 면 선택 없음 → 아무 일 없음 (first_hour #14) | 면 선택이 없으면 오브젝트 전체에 투영한다(Maya 규칙). Planar / Cylindrical / Spherical / Automatic 모두 | S |
| 9 | Unfold 결과 (1-33) | 1 | B · 4 | 부분: Blender Minimum Stretch unwrap | mayapy Unfold3D와 같은 메시에서 왜곡·셸 수를 비교 측정한다. 차이가 크면 옵션 매핑(반복 횟수, Pin)을 조정하고, 아니면 안내만 남긴다 | M |
| 10 | **Paint Skin Weights: Q/W/E/R로 나가기** (2-1) | 2 리깅+스킨 | A · 14 | 부분: Q를 눌러도 페인트가 안 끝남 (first_hour #27) | 웨이트 페인트에서 Q/W/E/R = 페인트를 끝내고 오브젝트 모드 + 그 툴(step 174 `_carry` 규칙) | S |
| 11 | **Paint Skin Weights: B+드래그 브러시 크기** (2-1) | 2 | A · 14 | 부분: B = Blender radial_control (`maya_patches.py:1201`) | Maya처럼 B를 누른 채 LMB 가로 드래그로 반경을 바꾸고, 놓으면 끝나게 한다. Soft Select의 B 홀드(`taphold`)와 같은 방식 | S |
| 12 | Paint Skin Weights: 뷰에서 조인트로 영향 고르기 (2-1) | 2 | A · 14 | [U]: Influences 목록은 동작, 뷰에서 조인트를 골라 바꾸는 손은 미확인 | 먼저 확인한다. 안 되면 페인트 중 조인트 클릭 = 그 영향 활성 | S |
| 13 | Blend Shape 가중치 키 (2-6) | 2 | A · 7 | 회색: Key > Set Blend Shape Target Weight Keys | 선택 메시의 Key 타깃 Value에 현재 프레임 키 (S 키 범위와 같은 규칙) | S |
| 14 | Shape Editor 남은 메뉴 (2-6) | 2 | A · 7 | 부분: 편집기 메뉴 60 % | 회색 12개 중 게임 얼굴·교정 셰이프에 쓰는 것(In-between, Combine Targets 등)만 고른다. 나머지는 안내 유지 | M |
| 15 | **IK/FK 전환** (2-10) | 2 | B · 4 | 회색: Key > IK/FK Keys, Skeleton > Enable IK/FK Control | Set IK/FK Key = IK 컨스트레인트 Influence 키 + FK 회전 키, Move IK to FK = 핸들을 FK 끝으로 스냅. Rigify 리그의 IK/FK 속성도 같은 메뉴에서 | M |
| 16 | Connection Editor 남은 메뉴 (2-14) | 2 | B · 4 | 부분: 편집기 메뉴 42 % | 리깅에 쓰는 것(Left/Right Display, Reload, 필터)만 채운다 | S |
| 17 | Component Editor 남은 메뉴 (2-11) | 2 | B · 3 | 부분: 편집기 메뉴 57 % | 스키닝 표에 쓰는 메뉴(Options, Layout, 정렬)를 채운다 | S |
| 18 | Quick Rig → 게임 스켈레톤 (2-17) | 2 | B · 3 | 부분: Quick Rig = Rigify 메타리그, HumanIK 회색 | HumanIK는 재구현하지 않는다. Rigify 결과에서 변형 본(DEF)만 엔진으로 나가는 경로를 Export 옵션과 안내로 연결한다(#19와 함께) | M |
| 19 | **스킨 리그 FBX 내보내기** (3-1) | 3 엔진 | A · 7 | **BLOCKED**: Maya에서 리그가 `skeleton1` 아래 rotate −90 / scale 100 (first_hour #39) | 아마추어 오브젝트의 단위·축 변환을 본에 굽는다. mayapy 왕복(`research/scripts/first_hour_217/`)이 메시·조인트 위치·조인트 오리엔트 모두 맞을 때 완료 | L |
| 20 | 게임 내보내기 전 검사 (3-1 하위) | 3 | A · 7 (부모 항목) | 없음 | Export 전에 Maya 게임 체크(Freeze, Delete History, 정점당 영향 ≤ 4, 정규화, 루트 1개)를 보여 주고 고칠지 묻는다 | S |
| 21 | FBX 게임 옵션: Smoothing Groups / Tangents / Triangulate (3-5) | 3 | 3-1의 하위 (자체 근거 C · 2) | 부분 [추정]: 키트 FBX 인자에 설정 없음 = Blender 기본 | Maya FBX 기본값(Smoothing Groups 켬 등)을 Export 옵션 창에 둔다. UE·Unity에서 하드 엣지가 맞는지 #22에서 확인 | S |
| 22 | 엔진에서 확인: 단위·루트·조인트 이름 (3-2) | 3 | B · 4 | 부분: 메시 cm·Y-up 동작, 리그는 미확인 | 기준 에셋 2개를 Unity·Unreal에 실제로 가져와 크기·축·스켈레톤·이름·하드 엣지를 기록한다(이 PC에 엔진이 있는지 [U]) | M |
| 23 | 스킨 메시 FBX 가져오기 (3-8) | 3 | B · 3 | **BLOCKED**: 스킨 프롭 0.01 배·90°, 스켈레톤 1.5 배 (first_hour #37) | 키트 Import에서 아마추어에 붙은 스킨 메시에도 축·단위 보정을 굽는다 | M |
| 24 | **Game Exporter 창** (3-6, 3-7) | 3 | B · 3 | 부분: 메뉴가 Blender 기본 FBX 창을 엶 (`menu_map.py:632`) | Maya Game Exporter 창(Model / Animation Clips 탭, 프리셋, 경로)을 만들고 Send to Unity / Unreal도 같은 창으로 보낸다 | M |
| 25 | 애니 클립 FBX (Bake Animation, Time Editor 클립) (3-4) | 3 | B · 3 | 부분: 타임라인 1개 액션만 굽기 | Animation Clips 탭의 클립 1개 = 액션(또는 NLA 스트립) 1개 = FBX take 1개. 엔진에서 클립 이름·길이 확인 | M |
| 26 | LOD 내보내기 (3-9) | 3 | B · 5 | 회색 (#7과 같은 항목) | #7의 LOD 그룹을 FBX LOD 그룹으로 내보내고 UE·Unity가 LOD로 읽는지 #22에서 확인 | S |
| 27 | Graph Editor: Region Keys Tool (4-1) | 4 애니 | A · 11 | 회색 | 선택 키를 감싸는 상자의 모서리·가장자리를 끌어 스케일·이동한다(Maya regionKeysCtx) | M |
| 28 | Graph Editor: 길이 커브를 Maya 단위로 (4-1) | 4 | A · 11 | 부분: 모든 커브가 길이일 때만 숫자를 바꾼다, 섞이면 미터 (step 137, 150) | 섞인 경우의 방법을 찾는다(정규화 보기 안내, 길이 커브만 남기는 필터 버튼 등). Blender에 F-curve 표시 배율이 없어 해법이 확실하지 않다 | L |
| 29 | Graph Editor: Lattice Deform Keys (4-1) | 4 | A · 11 | 회색 | 선택 키를 격자로 휘게 한다. #27 다음에 같은 코드로 | M |
| 30 | Time Editor 클립 = 게임 클립 (4-3) | 4 | A · 7 | 부분: Time Editor = NLA (재구현 안 함) | 새 데이터 구조를 만들지 않는다. Time Editor 메뉴에서 "Game Exporter로 보내기"만 연결한다(#25) | S |
| 31 | Motion Path: Flow Path Object (4-5) | 4 | A · 6 | 회색 | 경로를 따라가는 오브젝트에 Lattice를 붙이는 Maya 동작을 Follow Path + Lattice로 만든다. 게임 경로에서는 우선순위가 낮다 [추정] | M |
| V1 | Hotbox / 마킹 메뉴 손 확인 (0-7, 0-8) | 0 | A · 7 | 동작 (사람 확인 전) | 본인 녹화 1회: Space 누름 위치, RMB 제스처 속도, 클릭 모드 | S |
| V2 | Channel Box 손 확인 (0-3) | 0 | A · 7 | 동작 (사람 확인 전) | 채널 이름 선택 + 뷰 MMB 가상 슬라이더, `+=`, RMB Channels 메뉴, 잠금 | S |
| V3 | Multi-Cut / Extrude 매니퓰레이터 손 확인 (1-1, 1-2) | 1 | A · 7 | 동작 (사람 확인 전) | Multi-Cut Ctrl+드래그(루프)·Shift 스냅, Extrude 매니퓰레이터 크기·드래그 속도 | S |
| V4 | UV Cut / Sew / Unfold / Layout 손 확인 (1-32 ~ 1-34) | 1 | B · 4 (커뮤니티 "Maya UV가 낫다" B12, B28) | 동작 (사람 확인 전) | UV Editor 안 RMB 마킹 메뉴, 셸 색, 3D Cut and Sew 드래그 | S |
| V5 | 하드서피스 프롭 끝까지 (영역 1→3) | 1 | (DIRECTION 측정) | 측정 전 | 기준 에셋 1(프롭): 모델 → UV → 머티리얼 → FBX → 엔진을 dogfood 시나리오로 추가 | S |
| V6 | Paint Skin Weights 녹화 (2-1) | 2 | A · 14 | 동작 + 부분 (#10–12) | #10–12를 고친 뒤 본인 녹화: 브러시 Add/Replace/Smooth, 값 N, Flood, 잠금, Mirror | S |
| V7 | 캐릭터 리그 끝까지 (영역 2→3) | 2 | A (2-2, 2-3, 2-5, 2-7) | 측정 전 | 기준 에셋 2(캐릭터): Joint → Orient → IK → Bind → Paint → Mirror → Copy → FBX를 dogfood 시나리오로 추가 | M |
| V8 | Graph Editor 손 확인 (4-1) | 4 | A · 11 | 동작 (사람 확인 전): MMB 키 이동은 IC 기본 (`ic_4_5.py`) | MMB 드래그 + Shift 축 고정, 박스 선택, 탄젠트 핸들 드래그, F/A, 1/2/3 | S |
| V9 | 받은 리그 위 애니 (4-2, 4-6) | 4 | A · 6 / B · 5 | 동작 (자체 3관절 리그로만 측정) | Rigify 휴먼에서 컨트롤 선택 → CB → S → Time Slider → Graph Editor → IK/FK(#15) | S |

## 순서에 대한 메모

- **#19 스킨 리그 FBX는 영역 3이지만 "에셋이 끝났다"의 정의**다(DIRECTION). 영역 순서를 지키되, #10–#12(웨이트 손)를 끝내면 바로 #19로 넘어가는 것이 경로에 맞다 [해석].
- **크기 S만 모은 첫 묶음**(한 step에 넣을 수 있음): #4, #8, #10, #11, #12, #13, #20, #21, #26, #30 + V1–V4. 측정에서 나온 AWKWARD 3개(#8, #10, 그리고 #3의 안내 부분)가 여기에 들어간다.
- **L 3개**(#1 Rotate, #19 리그 FBX, #28 길이 커브)는 시작 전에 `docs/steps/step_<n>.md` 「계획」이 필요하다(CLAUDE.md 규칙: 매니퓰레이터·행렬 계산).
- 빠진 것: 렌더(Hypershade 47 %, Render Settings 48 %)와 스크립팅(MEL 없음)은 빈도 A여도 DIRECTION에서 "연결만 / 보류"라 넣지 않았다.
