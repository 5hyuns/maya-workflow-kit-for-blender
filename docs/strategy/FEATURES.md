# FEATURES — Maya에서 많이 쓰는 기능 목록과 키트 상태 (4차, 2026-10-26)

목적: "사람들이 많이 쓰는 기능"을 근거를 세어 영역별로 정리하고, 그 기능이 지금 키트에서 어떤 상태인지 저장소로 확인한다.
영역 순서는 `DIRECTION.md`(0 손 → 1 모델링+UV → 2 리깅+스킨+디포머 → 3 엔진 내보내기 → 4 애니메이션 → 5 렌더 → 6 FX·스크립팅)를 따른다.
구현 순서는 `TOP40.md`, 요약은 `SUMMARY4_KO.md`에 있다.

표기: **[사실]** 출처나 저장소에서 확인한 것 · **[추정]** 해석 · **[U]** 모름

---

## 1. 근거와 등급 기준

### 1.1 근거 출처 (원문·URL 목록: `data/web/features4_sources_a.md`, `data/web/features4_sources_b.md`)

| 묶음 | id | 종류 | 수 |
|---|---|---|---|
| Autodesk 공식 | A0 (Desktop Analytics: 사용 데이터를 **수집한다는 사실만** 있고 순위 공개 없음), A1 (Maya 2022 기본 셸프, `research/maya/shelves.json`), A2·A3 (Certified User 시험 목표 2020, Certified Professional 로드맵 2015), A4 (Maya Learning Channel "Intro to Maya"), A5·A6 (Quick Start / First Time Tutorial), A7 (Autodesk Learn "Realtime rigging", 게임 태그), A8 (Customer Value: 릴리스별 개선), A18·B36 (Game Exporter 도움말), A21·B1 (공식 단축키 페이지) | 공식 | 12 |
| 교육 과정 | A9 (LinkedIn Learning Maya 2022 Essential Training), A10 (Udemy 입문 완성 과정), A11 (CGMA Intro to Maya), A12 (AnimSchool Intro to Rigging), A13 (Gnomon Character Rigging), A14 (Gnomon Workshop Intro to Maya 2026 + UV Toolkit), A15 (Animation Mentor Maya 워크숍), A16 (Pluralsight Skin-Weighting), A19 (World of Level Design 모델링 툴 11개), A20·B44 (Madwomb 리깅 강의), B5 (SDC 교재), B6 (Animation Mentor 블로그) | 교육 | 12 |
| 게임 파이프라인 | A17·B35 (Unreal FBX Skeletal Mesh / Maya에서 가져오기 공식 문서), B37·B38 (Maya→Unreal 내보내기 가이드, Epic 포럼), B39 (Send to Unreal), B40·B41 (Unity 내보내기·FBX Exporter), B43 (Unity 하드 엣지 문제), B45·B46 (스킨 웨이트 블로킹·미러 튜토리얼, Autodesk 문서), B47 (tech-artists.org 리그 FBX), B48 (게임 스키닝 블로그), B54 (UV 텍셀 밀도 워크플로) | 게임 | 13 |
| 채용·직무 | B49 (Bungie TA Rigging), B50 (Keywords Environment / TA), B51 (Wolftagon Environment), B52 (Mysteria Rigger & Animator), B53 (VFS / CG Spectrum Character Rigger 직무 설명) | 채용 | 5 |
| 커뮤니티 | B7·B11–B15·B17–B22·B33·B34 (Reddit r/Maya·r/blender·r/3Dmodeling, **검색 스니펫만**, 본문 차단), B10·B24·B25 (BlenderArtists), B26–B29 (Polycount), B16 (Hacker News), B23 (note.com 일본 실무자: Component Editor), B30–B32·B8·B9·B55·B56 (YouTube 강의·반응 영상 자막) | 커뮤니티 | 27 |
| 치트시트 | B2 (Logickeyboard PDF), B3 (Evercast, 본문 못 읽음), B4 (YourDevKit, 오류 있음 tier 4) | 비공식 | 3 |
| 키트 측정 | `docs/first_hour.md` (step 217 측정 39동작), GitHub 이슈, `tools/menu_count.py` | 저장소 | — |

**중요한 한계** [사실]
- **Autodesk는 "가장 많이 쓰는 툴" 순위를 공개하지 않았다.** 찾은 것은 사용 데이터를 수집한다는 도움말(A0)뿐이다. 그래서 빈도는 "얼마나 많은 독립 출처가 그 기능을 이름으로 다루는가"로 대신 쟀다. 실제 사용 횟수가 아니다.
- Reddit 본문은 tavily·WebFetch 모두 거부되어 스니펫만 썼다. 대학 강의계획서는 1개도 확인 못 했다(USC PDF 실패, Columbia 거부).
- 채용 공고는 "rigging, skinning, UV, LOD, Python in Maya" 같은 영역 단위로만 말하고 개별 메뉴 이름은 거의 쓰지 않는다.

### 1.2 빈도 등급 (근거 수 기준)

| 등급 | 뜻 | 기준 |
|---|---|---|
| **A** 매일 | 거의 모든 입문·직무 자료가 다룬다 | 독립 출처 6개 이상 |
| **B** 자주 | 여러 묶음(공식·교육·게임·커뮤니티 중 2개 이상)에서 나온다 | 3–5개 |
| **C** 가끔 | 일부 자료만 | 1–2개 (**1개면 '추정'**) |

같은 저자가 두 번 나오면(A20=B44, A21=B1) 1개로 셌다. 셋업 작업(핫키 편집기처럼 하루에 한 번 쓰는 것)은 수가 많아도 한 등급 내렸고, 내렸다고 적었다 [delegated].

### 1.3 키트 상태 (저장소에서 확인)

| 상태 | 뜻 | 확인 방법 |
|---|---|---|
| **동작** | Maya 메뉴·키가 키트 동작으로 이어지고 알려진 막힘 없음 | `ui/menu_map.MAP`에 있음 = `tools/menu_count.py` "working" (항목별 덤프: `data/menu_status_4.tsv`, 스크립트 `data/scripts/menu_status_dump.py`), `docs/keymap_mapping.md` "구현" |
| **부분** | 동작하지만 측정에서 AWKWARD/BLOCKED, 열린 이슈, 또는 Blender 기본 동작으로만 이어짐 | `docs/first_hour.md`, `gh issue list`, `src/` grep |
| **회색** | 메뉴에 보이지만 회색 + 안내문 (미구현) | `notices.greyed_notice` |
| **없음** | 메뉴 데이터에도 없음 | grep |

`menu_count.py` 오늘(2026-10-26) 실행 결과 [사실]: 메뉴 고유 경로 1,319개 중 806개 동작(61.1 %), 회색인데 안내문 없는 항목 0. 메뉴 세트별: Common 69 %, Modeling 65 %, Rigging 86 %, Animation 78 %, FX 21 %, Rendering 43 %. 편집기 메뉴 바: Graph Editor 82 %, Dope Sheet 87 %, UV Editor 85 %, Hypershade 47 %, Component Editor 57 %, Shape Editor 60 %, Connection Editor 42 %. 전체 출력: `data/menu_count_4.txt`.

**먼저 알아 둘 결론** [사실 + 해석]: 많이 쓰는 기능의 **메뉴는 거의 다 동작한다**(아래 표 125행 중 회색 6행·없음 1행). 남은 공백은 메뉴가 아니라 ① 측정에서 나온 **손 감각·개념 차이**(Translate Y, Paint Skin Weights에서 Q, UV Editor 여는 방식), ② **게임 엔진으로 가는 끝 단계**(스킨 리그 FBX가 BLOCKED, Game Exporter가 Blender 기본 창), ③ 몇 개의 **회색 핵심 기능**(LOD Group, IK/FK 키)에 있다.

---

## 2. 영역 0 — 손 (내비게이션·선택·핫박스·Channel Box·홀드 키)

| # | 기능 (Maya 경로·단축키) | 빈도 · 근거 | 키트 상태 [근거] | Blender 대응 | 비고 (손 감각 차이 등) |
|---|---|---|---|---|---|
| 0-1 | Tumble / Track / Dolly (Alt+LMB / MMB / RMB) | **A** · 6 (A4, A9, A15, A21, B4, B9) | 동작 [README Navigation; Alt+RMB = `allset.dolly`, CLAUDE.md step 130] | MMB 궤도, Shift+MMB 이동, 휠 | 입력 필드 위 MMB 가상 슬라이더 드래그는 C++ 필요로 불가 [README Known limits] |
| 0-2 | Q/W/E/R 툴 + 매니퓰레이터 | **A** · 8 (A4, A9, A10, B1, B4, B5, B6, B8) | 동작 (Move/Scale = Maya 매니퓰레이터, **Rotate는 Blender C 기즈모**) [README Look & layout; CLAUDE.md step 59] | 툴바 Move/Rotate/Scale, G/R/S | Rotate 링 모양·클리핑이 Maya와 다름 — Python dial이 C 기즈모처럼 클립을 못 함 [CLAUDE.md step 59] |
| 0-3 | Channel Box (값 입력 `+=`, 채널 선택, MMB 가상 슬라이더, RMB Channels 메뉴) | **A** · 7 (A4, A14, B4, B7, B8, B21, B32) | 동작 [steps 38, 129, 135, 148, 158; #87 닫힘] | N 사이드바 Item | 키트의 가장 강한 영역 중 하나. 단 아래 0-4 |
| 0-4 | **Translate Y = 위** (Y-up 세계) | **B** · 추정 (근거 = 모든 바운스·리깅 튜토리얼이 Y를 위로 씀 + 키트 측정 first_hour #30 점수 6.0) | **부분** — Z-up 유지(결정 5), Channel Box "Translate Y"가 Blender의 수평 Y라 공이 미끄러짐 [`docs/first_hour.md` #30 AWKWARD] | Z-up | 측정 점수 공동 1위. 같은 원인이 엔진 내보내기(영역 3)까지 이어짐 |
| 0-5 | Attribute Editor (Ctrl+A) | **A** · 8 (A2, A3, A4, A9, A14, B4, B8, B9) | 동작 [steps 99, 141, 211; 도크 탭] | Properties 편집기 | |
| 0-6 | Outliner | **A** · 9 (A2, A3, A4, A9, A14, B7, B11, B21, B23) | 동작 (Maya 행 순서·기본 카메라 행·세트 행·MMB 재배치) [steps 99, 202, 211] | Outliner | Blender C Outliner의 타입 아이콘은 못 바꿈 [CLAUDE.md step 131] |
| 0-7 | Hotbox (Space 누름) | **A** · 7 (A9, A11, A14, B2, B7, B10, B20) | 동작 [steps 8, 33, 52] | 없음 (F3 검색) | 사람 손 감각 확인은 `docs/manual_checks.md`에 남음 |
| 0-8 | Marking menus (RMB, Shift+RMB, Ctrl+RMB) | **A** · 7 (A9, A11, A14, B9, B20, B25, B26) | 동작 (반경 55 px Maya 측정, 항목 = 메인 메뉴 경로) [steps 136, 151, 193] | 파이 메뉴 | |
| 0-9 | Shelves (기본 셸프 + 내 셸프, Ctrl+Shift+클릭 추가) | **A** · 7 (A1, A10, A11, A13, A14, B11, B20) | 동작 [steps 109, 162, 167] | 없음 (Quick Favorites) | |
| 0-10 | Duplicate (Ctrl+D) / Duplicate Special (Ctrl+Shift+D) | **A** · 7 (A1, A2, A9, A10, B4, B20, B21) | 동작 [keymap_mapping.md `Ctrl+d` 구현] | Shift+D / Alt+D | |
| 0-11 | Group (Ctrl+G) / Parent (P) / Unparent (Shift+P) | **A** · 8 (A9, A10, A12, B1, B2, B4, B10, B21) | 동작 [menu_status: Edit/Group, Parent, Unparent; step 10 Maya 방식 부모] | Ctrl+P / 컬렉션 | 부모 역행렬 = 단위 행렬(Maya 식) |
| 0-12 | 피벗 편집 D / Insert, Center Pivot | **A** · 9 (A1, A2, A3, A10, B2, B10, B19, B21, B42) | 동작 (D/Insert 홀드, 컴포넌트 피벗) [steps 59, 77, 94] | 원점 / 3D 커서 | **회전·스케일 피벗 분리 불가** (C++) [README Known limits] |
| 0-13 | Frame Selected / All (F / A) | **B** · 3 (B1, B4, B8) | 동작 (보이는 영역 기준) [step 17] | Numpad . / Home | 매일 쓰지만 근거가 단축키 자료뿐이라 B |
| 0-14 | 컴포넌트 모드 F8 / F9–F12, RMB 컴포넌트 | **B** · 4 (A4, A9, A10, B1) | 동작 [README; keymap_mapping.md] | Tab + 1/2/3 | |
| 0-15 | Snap 홀드 X / C / V, J 스텝 | **B** · 4 (A9, A10, B1, B19) | 동작 [step 95, README Hold keys] | Ctrl 스냅 | |
| 0-16 | Repeat Last (G) | **B** · 3 (B1, B2, B4) | 동작 (메뉴·셸프·마킹 메뉴 명령까지) [step 175] | Shift+R | |
| 0-17 | Display Layers | **B** · 4 (A9, A14, B7, B8) | 동작 [menu_status: Windows/General Editors/Display Layer Editor; step 129] | 컬렉션 숨김 | |
| 0-18 | Soft Select (B 탭 / B+드래그 반경) | **B** · 4 (A4, A9, A10, B4) | 동작 [keymap_mapping.md:267] | O 비례 편집 | |
| 0-19 | Undo / Redo (z, Shift+Z) | **B** · 3 (B1, B2, B4) | 부분 — 키는 동작, **언두 깊이는 Blender 기본 32**(키트는 환경설정을 못 씀, 안내만) [CLAUDE.md step 141; step 130 스토어 규칙] | Ctrl+Z | 할 수 있는 일 거의 없음(스토어 규칙) |
| 0-20 | Set Project / File 프로젝트 | **B** · 4 (A9, A10, A11, B7) | 동작 [step 69, 102] | 없음 | |
| 0-21 | 메뉴 세트 F2–F6, 옵션 박스(❒) | **B** · 4 (B2, B5, B21, B22) | 부분 — 메뉴 세트 동작, 옵션 박스 507개 중 **Maya식 옵션 창 176개**, 나머지는 Blender 설정·안내 [#108 본문; step 140] | 없음 / Adjust Last Operation | 자주 쓰는 명령의 옵션 창이 빠졌는지는 [U] |
| 0-22 | Hotkey Editor / 내 단축키 | **B** · 7 (A11, A14, A15, B5, B7, B20, B27) — 셋업 작업이라 한 등급 내림 | 동작 [step 215] | Preferences > Keymap | |
| 0-23 | Convert Selection (Ctrl+F9–F12) | C · 1 추정 (B1) | 동작 [menu_status Select/Convert Selection 18개 동작] | Ctrl+Tab | |
| 0-24 | Grow / Shrink (> <), Pick Walk (화살표) | C · 2 (A21, B1) | 동작 [step 39] | Ctrl+NumPad+ | |
| 0-25 | Hide / Show (Ctrl+H, H), Isolate Select (Ctrl+1) | C · 1 추정 (B4) | 동작 (부모 숨김 상속까지) [step 164] | H / Numpad / | |
| 0-26 | Symmetry (Status Line) | C · 2 (A9, A10) | 동작 [step 36] | 메시별 X 미러 | |
| 0-27 | Image Plane | **B** · 3 (A9, A10, A14) | 동작 [menu_status Create/Free Image Plane] | 참조 이미지 Empty | |
| 0-28 | Quick Select Sets | **B** · 3 (A9, A10, A12) | 동작 [step 96] | 없음 | |
| 0-29 | Space 탭 = 4분할 / 1분할 | C · 1 추정 (B2) | 동작 [README] | Ctrl+Alt+Q | |

---

## 3. 영역 1 — 모델링 + UV

### 3.1 모델링

| # | 기능 | 빈도 · 근거 | 키트 상태 | Blender 대응 | 비고 |
|---|---|---|---|---|---|
| 1-1 | Extrude (Ctrl+E, 매니퓰레이터 Shift+드래그) | **A** · 7 (A1, A9, A10, A19, B1, B30, B55) | 동작 (polyExtrudeFace mayapy 일치, Maya 매니퓰레이터) [steps 65, 151; first_hour #7–8 OK] | E | |
| 1-2 | Multi-Cut (Ctrl+Shift+X) | **A** · 7 (A1, A19, B1, B30, B34, B55, B56) | 동작 [first_hour #10 OK] | K 나이프 | |
| 1-3 | Quad Draw (Ctrl+Shift+Q) + Make Live | **A** · 7 (A1, A9, A10, B1, B2, B55, B56) | **부분** — 동작, 남은 것: 오버레이 색 옵션, Tab+MMB 스트립 크기, Ctrl+Shift+RMB 옵션 메뉴 [이슈 #89 OPEN] | Poly Build / 리토폴로지 애드온 | 키트 외부 사용자 신호가 있던 곳(IDENTITY §0-5) |
| 1-4 | Freeze Transformations | **A** · 9 (A1, A3, A10, A20, B21, B37, B42, B43, B44) | 동작 [menu_status Modify/Freeze Transformations; step 10 피벗 유지] | Ctrl+A Apply | 게임 내보내기 전 필수 단계로 반복 언급 |
| 1-5 | Delete History (Alt+Shift+D), Non-Deformer History | **A** · 8 (A1, A9, A10, A14, B37, B38, B42, B43) | 동작 [first_hour #12 OK; step 162] | 모디파이어 Apply | |
| 1-6 | Center Pivot | **A** · 6 (A1, A2, A3, A10, B21, B42) | 동작 | Origin to Geometry | |
| 1-7 | Bevel (Ctrl+B) | **A** · 6 (A1, A9, A10, A19, B30, B55) | 동작 (polyBevel3 mayapy 1e-4) [step 139; first_hour #9 OK] | Ctrl+B | |
| 1-8 | Smooth Mesh Preview 1 / 2 / 3 | **A** · 7 (A1, A2, A9, A21, B1, B10, B55) | 동작 [step 15] | Subdivision 모디파이어 | |
| 1-9 | Bridge | **B** · 5 (A1, A9, A10, A19, B55) | 동작 | Bridge Edge Loops | |
| 1-10 | Target Weld | **B** · 4 (A1, A19, B27, B56) | 동작 | Merge / Snap | |
| 1-11 | Merge / Merge to Center / Collapse | **B** · 3 (A1, A10, B56) | 동작 [first_hour #11 OK] | M | |
| 1-12 | Combine / Separate / Extract | **B** · 4 (A1, A10, A19, B21) | 동작 (mayapy 이름·피벗) [step 63] | Ctrl+J / P | |
| 1-13 | Mirror | **B** · 3 (A1, A10, B21) | 동작 | Mirror 모디파이어 | |
| 1-14 | Circularize | **B** · 4 (A1, A10, A19, B30) | 동작 [step 110] | LoopTools 애드온 | |
| 1-15 | Booleans | **B** · 3 (A3, A9, A19) | 동작 | Boolean 모디파이어 | |
| 1-16 | Remesh / Retopologize | **B** · 4 (A1, A8, A11, A14) | 동작 | Remesh / QuadriFlow | |
| 1-17 | Modeling Toolkit | **B** · 4 (A5, A9, A14, B9) | 동작 [step 63, 도크 탭] | 없음 | |
| 1-18 | Sculpting Tools (Ctrl+1–0) | **B** · 3 (A1, A9, B2) | 동작 (Imprint·Target 계열 5개 회색) [menu_status] | Sculpt 모드 | |
| 1-19 | 폴리곤 프리미티브 | **B** · 3 (A1, A4, A6) | 동작 (Maya 면 순서·이름) [steps 129, 190, 196] | Shift+A | |
| 1-20 | NURBS 커브 CV / EP (리그 컨트롤용) | **B** · 4 (A1, A2, A9, A10) | 동작 [step 156] | 커브 | |
| 1-21 | Reduce / **LOD Group / Generate LOD Meshes** | **B** · 5 (A17, B37, B48, B50, B53) | **부분** — Reduce 동작, **Edit > LOD (Level of Detail) 3항목 회색** [menu_status: Edit/LOD 회색 "Blender has no LOD groups"] | Decimate 모디파이어 | 게임 채용·엔진 문서에 반복. UE/Unity는 `_LOD0` 이름 규칙 [추정: 일반 관행] |
| 1-22 | Soften / Harden Edge, Set to Face, Unlock Normals | C · 2 (A19, B43) | 동작 [step 189] | Shade Smooth / Sharp | 게임 쪽 문제(하드 엣지가 엔진에서 깨짐, B43)는 영역 3 FBX 설정과 연결 |
| 1-23 | Insert Edge Loop / Offset Edge Loop / Connect | C · 2 (A10, A19) / (A19, B56) | 동작 [step 144] | Ctrl+R | Multi-Cut 안에서 쓰는 경우가 많아 수가 적게 나온 듯 [추정] |
| 1-24 | Prefix Hierarchy Names / Search and Replace Names | **B** · 3 (A3, A20, B44) | 동작 | Batch Rename | 게임 조인트 이름 정리에 씀 |
| 1-25 | Lattice | **B** · 3 (A1, A4, A10) | 동작 [step 144, #95 닫힘] | Lattice | (영역 2 디포머에도 해당) |
| 1-26 | Reverse (노멀 뒤집기), Triangulate | C · 2 (A19, B35/B37) | 동작 | Flip / Ctrl+T | |
| 1-27 | Sweep Mesh | C · 2 (A1, A8) | 동작 | Curve 베벨 | |

### 3.2 UV

| # | 기능 | 빈도 · 근거 | 키트 상태 | Blender 대응 | 비고 |
|---|---|---|---|---|---|
| 1-30 | **UV Editor 열기** (Windows > Modeling Editors > UV Editor) | **A** · 7 (A1, A5, A9, A11, A14, B12, B28) | **부분** — 새 창으로 열리고 **편집 모드로 바뀜** (Maya: 패널, 오브젝트 모드 유지) [first_hour #13 AWKWARD, 점수 3.6] | UV Editing 워크스페이스 | 메뉴 85 % 동작. 여는 방식만 다름 |
| 1-31 | Planar / Cylindrical / Spherical / Automatic 투영 | **B** · 4 (A1, A9, A10, B54) | **부분** — 오브젝트 모드에선 동작, **편집 모드 + 면 선택 없음이면 아무 일 없음** (Maya: 오브젝트 전체) [first_hour #14 AWKWARD, 점수 4.0] | U 메뉴 | |
| 1-32 | Cut / Sew (+ 3D Cut and Sew UV Tool) | **B** · 4 (A1, A14, B22, B54) | 동작 [first_hour #16–17 OK; step 79] | Mark Seam | |
| 1-33 | Unfold | **B** · 4 (A10, A14, B22, B54) | 부분 — 메뉴 동작, 결과는 **Blender Minimum Stretch unwrap** (Maya Unfold3D와 다른 엔진, 결과 줄에 안내) [first_hour #18 비고] | Unwrap | 결과 차이 크기 [U] — 미측정 |
| 1-34 | Layout | **B** · 4 (A10, A14, B22, B54) | 동작 (Pack Islands + Maya 픽셀 간격) [first_hour #19 OK] | Pack Islands | |
| 1-35 | Texel Density (Get / Set) | **B** · 3 (B22, B50, B54) | 동작 [`ui/uv_toolkit.py:135`, `operators/uv_tools.py:539`] | 애드온(Texel Density Checker) | |
| 1-36 | UV Sets (라이트맵 UV 포함) | **B** · 3 (A14, A17, B51) | 동작 [menu_status UV Editor/UV Sets 6개 동작] | UV Maps | |
| 1-37 | Checker Map / Assign Checker Shader | **B** · 3 (A10, B2, B54) | 동작 | 없음 (이미지 생성) | |
| 1-38 | Optimize, Straighten, Stack, Orient Shells, Align | C · 2 (A10, A14) | 동작 [menu_status UV Editor/Modify 다수] | Minimize Stretch 등 | |
| 1-39 | UV Shell 선택 (Alt+F12, To UV Shell) | C · 1 추정 (B2) | 동작 | L | |
| 1-40 | Transfer Attributes (UV) | C · 1 추정 (B54) | 동작 [menu_status Mesh/Transfer Attributes] | Data Transfer | |
| 1-41 | 3D Grab UV Tool | C · 1 추정 (A1) | 회색 | UV Grab 브러시 | |

---

## 4. 영역 2 — 리깅 + 스킨 웨이트 + 디포머

| # | 기능 | 빈도 · 근거 | 키트 상태 | Blender 대응 | 비고 |
|---|---|---|---|---|---|
| 2-1 | **Paint Skin Weights** | **A** · 14 (A1, A7, A10, A14, A16, A17, A20, B23, B24, B45, B46, B52, B53 + B44) | **부분** — 도구·Influences 목록·잠금·U 메뉴·N 값 드래그·Alt+F Flood 동작 [`ui/paint_weights.py`, keymap_mapping.md:266–272]. **Q를 눌러도 페인트가 안 끝남** [first_hour #27 AWKWARD, 점수 6.0]. **B = Blender radial_control(누르고 움직이기)**로, Maya의 B+드래그와 손이 다름 [`maya_patches.py:1201`] | Weight Paint 모드 | 근거 수 전체 1위. "Weight painting: pro with Maya, incompetent with Blender"(B24) |
| 2-2 | Bind Skin (Smooth Bind, Max Influences) | **A** · 13 (A1, A2, A3, A7, A10, A11, A13, A16, A17, A20, B44, B48, B55) | 동작 (Maya closest distance 가중치 mayapy 일치, skinCluster1 이름) [step 149; first_hour #26 OK] | Ctrl+P With Automatic Weights | |
| 2-3 | Create Joints (Joint Tool) | **A** · 11 (A1, A2, A3, A7, A10, A11, A12, A13, A16, A17, B44) | 동작 [step 57; first_hour #24 OK] | Armature 추가·압출 | |
| 2-4 | Constraints: Parent / Point / Orient / Scale / Aim / Pole Vector | **A** · 11 (A1, A3, A4, A10, A11, A12, A13, A20, B13, B44, B53) | 동작 [menu_status Constrain/ 8개 동작] | 본 컨스트레인트 | |
| 2-5 | IK Handle (Rotate Plane) | **A** · 10 (A1, A2, A3, A10, A11, A13, B10, B25, B44, B53) | 동작 [step 58; first_hour #25, #28 OK] | IK 컨스트레인트 | |
| 2-6 | Blend Shape / Shape Editor | **A** · 7 (A1, A11, A12, B15, B35, B36, B53) | 부분 — Deform > Blend Shape·Shape Editor 동작 [step 213], **Key > Set Blend Shape Target Weight Keys 회색**, Bake Topology / Swap 회색 [menu_status] | Shape Keys | 게임 얼굴·교정 셰이프에서 반복 |
| 2-7 | Orient Joint (+ Local Rotation Axes 표시) | **A** · 6 (A7, A10, A12, A20, B44, B53) | 동작 [menu_status Skeleton/Orient Joint, Display/Transform Display/Local Rotation Axes] — 단 Blender 본 롤 ≠ Maya 조인트 오리엔트라 **FBX로 나가면 깨짐** (영역 3, first_hour #39) | Bone Roll | |
| 2-8 | Set Driven Key | **A** · 6 (A1, A12, A20, B14, B16, B55) | 동작 [step 62] | 드라이버 | |
| 2-9 | Mirror Skin Weights | **B** · 5 (A7, A16, B45, B46, B53) | 동작 (Closest joint, Label) [step 159] | Mirror Vertex Group | |
| 2-10 | IK/FK 전환 (Key > IK/FK Keys, Skeleton > Enable IK/FK Control) | **B** · 4 (A7, A11, A13, B10) | **회색** — 6항목 회색, 안내 "IK constraint Influence를 키로" [menu_status] | IK Influence 키 | 받은 리그(Rigify) 애니메이션 경로에서 바로 걸림 [추정, IDENTITY Blindspot #1] |
| 2-11 | Component Editor (스킨 가중치 숫자 편집) | **B** · 3 (B23, B45, B46) | 동작 (Maya 비례 정규화, Hold) [step 213] — 편집기 메뉴 57 % | 없음 (N 패널 Vertex Weights) | 일본 실무자 "Maya의 강점"(B23) |
| 2-12 | Copy Skin Weights | **B** · 3 (A16, B43, B45) | 동작 | Data Transfer | |
| 2-13 | Add Attribute (커스텀 속성) | **B** · 4 (A3, A4, A12, A13) | 동작 | Custom Properties | |
| 2-14 | Connection Editor / Node Editor | **B** · 4 (A12, A20, B15, B47) | 부분 — Connection Editor 창 동작, 메뉴 42 % [step 213; menu_count] | 드라이버 편집기 | |
| 2-15 | NURBS 컨트롤 커브 (Circle 등) | **B** · 3 (A7, A10, A12) | 동작 [step 156] | 커스텀 셰이프 본 | |
| 2-16 | Lattice / Nonlinear (Bend·Squash 등) / Cluster | **B** · 3 (A1, A4, A10 / A4, A11, A14) | 동작 [steps 110, 144, 205] | Lattice / Simple Deform / Hook | |
| 2-17 | Quick Rig / HumanIK | **B** · 3 (A1, A11, B9) | 부분 — Quick Rig = Rigify 메타리그, **HumanIK 회색** [menu_status] | Rigify | "재구현 안 함" 원칙 대상 |
| 2-18 | Prune Small Weights / Normalize / Max Influences | C · 2 (A7, B45) / (B23, B45) / (B44, B48) | 동작 [menu_status Skin/ 전부 동작] | Clean / Normalize / Limit Total | 게임은 정점당 4 영향(B48) [사실: 인용] |
| 2-19 | Add / Remove Influence | C · 2 (A20, B44) | 동작 (Maya 거리 가중치) [step 202] | 버텍스 그룹 추가 | |
| 2-20 | Mirror Joints / Insert Joint | C · 1 추정 (B44) / 2 (A20, B44) | 동작 | Symmetrize | |
| 2-21 | Spline IK | C · 1 추정 (A13) | 동작 [step 110] | Spline IK | |
| 2-22 | Expressions | C · 2 (A4, A12) | 동작 (Expression Editor) | 드라이버 식 | |
| 2-23 | Lock and Hide (Channel Box) | C · 2 (A20, B44) | 동작 [step 55] | 잠금 | |
| 2-24 | Interactive Bind Skin | 근거 0 | 회색 | — | 참고 |

---

## 5. 영역 3 — 엔진 내보내기 (FBX → Unity / Unreal)

| # | 기능 | 빈도 · 근거 | 키트 상태 | Blender 대응 | 비고 |
|---|---|---|---|---|---|
| 3-1 | **File > Export All / Export Selection (FBX)** | **A** · 7 (A3, A17, A18, B35, B37, B38, B40) | **부분** — 메시는 맞음(cm, Y-up, 크기·위치) [first_hour #35 OK]. **스킨 리그는 BLOCKED**: Maya에서 열면 리그가 `skeleton1` 아래 rotate −90 / scale 100, 조인트 위치가 조금씩 어긋남 [first_hour #39 BLOCKED] | File > Export > FBX | 실시간 파이프라인의 끝 = "에셋이 끝났다"의 정의(DIRECTION) |
| 3-2 | 단위 cm · Move to Origin · 루트 조인트 · 조인트 이름 | **B** · 4 (B35, B36, B37, B38) | 부분 — 메시 단위·축 동작, 리그 루트에 여분 변환(위 3-1) | FBX Apply Unit / Armature 옵션 | |
| 3-3 | FBX: Skins + Blend Shapes 포함 | C · 1 추정 (B35) (단 A17 UE 스켈레탈 메시 문서 전체가 이 주제) | 부분 — 3-1과 같은 이유로 리그 쪽 미검증 | Armature / Shape Keys 옵션 | |
| 3-4 | FBX: Bake Animation | **B** · 3 (B37, B38, B41) | 부분 — NLA off·타임라인 1개 액션으로 굽기 [`operators/file_io.py:94–103`, step 138], 리그 FBX가 깨져 엔진 확인 전 [first_hour] | Bake Animation 옵션 | |
| 3-5 | FBX: Smoothing Groups / Tangents & Binormals / Triangulate | C · 2 (B35, B37) | 부분 [추정] — 키트 FBX 인자에 `mesh_smooth_type`·`use_tspace`·`use_triangles` 설정 없음 = Blender 기본(노멀만, Smoothing 'OFF') [사실: `file_io.py:101–103` grep]. UE가 "smoothing group 없음" 경고를 내는 설정인지는 [추정] | FBX Geometry 옵션 | B43: "Maya→Unity FBX 후 모든 엣지가 하드" |
| 3-6 | **Game Exporter** (모델 / 애니메이션 클립, 프리셋) | **B** · 3 (A18, B36, B41) | **부분** — 메뉴는 `export_scene.fbx` = **Blender 기본 FBX 창을 그대로 엶** (Maya 프리셋·클립 탭 없음) [사실: `ui/menu_map.py:632`] | FBX + NLA 액션 | |
| 3-7 | Send to Unity / Send to Unreal | C · 2 (B39, B40) | 부분 — 3-6과 같은 Blender FBX 창 [`menu_map.py:633–634`] | 없음 (Send to Unreal 애드온) | |
| 3-8 | FBX Import (엔진·외주 에셋을 다시 가져오기, 스킨 메시) | **B** · 3 (A3, B38, B47) | **부분 (BLOCKED)** — 참조 큐브는 맞고 **스킨 프롭이 0.01 배·90° 돌아감, 스켈레톤 1.5배** [first_hour #37 BLOCKED] | File > Import > FBX | |
| 3-9 | LOD Group (영역 1-21과 같은 항목) | **B** · 5 | 회색 | Decimate + 이름 규칙 | |

---

## 6. 영역 4 — 애니메이션

| # | 기능 | 빈도 · 근거 | 키트 상태 | Blender 대응 | 비고 |
|---|---|---|---|---|---|
| 4-1 | **Graph Editor** | **A** · 11 (A2, A3, A4, A5, A9, A10, A15, B1, B31, B32, B55) | 부분 — 메뉴 82 % 동작, 툴바·Maya 채널 목록·1/2/3 보기·Alt+/ 스냅 [steps 70, 92, 150, 203]. MMB 드래그 키 이동 = IC 기본 동작 [사실: `keymap/ic_4_5.py` Graph Editor `MIDDLEMOUSE CLICK_DRAG`]. **길이 커브 값은 미터로 표시**(Blender에 F-curve 표시 배율 없음) [CLAUDE.md step 150], Region Keys Tool·Lattice Deform Keys 회색 [menu_status] | Graph Editor | 손 감각 확인은 사람 몫(수정키 시뮬레이션 불가, step 170) |
| 4-2 | Set Key (S, Shift+W/E/R) | **A** · 6 (A1, A9, A21, B1, B2, B4) | 동작 (10채널 Maya처럼) [first_hour #30; step 151] | I | 단 4-4 Translate Y |
| 4-3 | Time Editor / 애니메이션 클립 | **A** · 7 (A4, A8, A9, A11, B1, B36, B41) | 부분 — Windows > Time Editor 동작 = **NLA** [menu_status; keymap_mapping.md "kit Time Editor = NLA"] | NLA Editor | Blender 레이어드 액션과 겹쳐 재구현 안 함(IDENTITY Blindspot #5). 게임에선 클립 = 엔진 애니 클립(3-6과 연결) |
| 4-4 | 바운스처럼 **Translate Y로 키** (0-4와 같은 원인) | **B** 추정 | 부분 [first_hour #30] | Z | |
| 4-5 | Motion Path / Motion Trail | **A** · 6 (A1, A2, A3, A4, A9, A10) | 동작 (Attach to Motion Path, Editable Motion Trail) [menu_status] | Follow Path / Motion Paths | Flow Path Object 회색 |
| 4-6 | Time Slider (스크럽·범위·키 틱) | **B** · 5 (A2, A3, A5, A9, A10) | 동작 [steps 56, 73, 186] | Timeline | |
| 4-7 | Playblast | **B** · 4 (A1, A4, A10, A15) | 동작 [step 70] | Viewport Render Animation | |
| 4-8 | Tangents (Spline / Linear / Flat / Stepped) | C · 1 추정 (A4) — 근거가 적게 잡혔지만 Graph Editor 자료 전부가 다룸 [추정] | 동작 [first_hour #31–32 OK] | Interpolation / Handle | |
| 4-9 | Insert Key Tool (i) / Breakdown | C · 2 (A4, A21) | 동작 [step 92] | | |
| 4-10 | Auto Keyframe | C · 2 (A20, B44) | 동작 [step 70] | 자동 키 | |
| 4-11 | Bake Animation / Bake Simulation | C · 2 (A1, A4) | 동작 [menu_status Key/Bake Simulation] | Bake Action | |
| 4-12 | Ghosting | C · 1 추정 (A8) | 동작 [step 171] | Onion skin 애드온 | |
| 4-13 | Blue Pencil / Grease Pencil | C · 2 (A9, A10) | **없음** — 메뉴 데이터에 Blue Pencil 항목 없음 [사실: `data/menu_status_4.tsv` grep] | Grease Pencil | |
| 4-14 | 애니메이션 레이어 | 근거 0 (이번 수집) | 동작 [steps 180, 194, 204] | NLA / 레이어드 액션 | 이전 조사에선 유료 애드온 수요가 있었음(SUMMARY3) |

---

## 7. 영역 5 — 렌더·셰이더 (연결만)

| # | 기능 | 빈도 · 근거 | 키트 상태 | Blender 대응 |
|---|---|---|---|---|
| 5-1 | Hypershade + Assign New Material | **A** · 9 (A2, A3, A9, A11, A14, B1, B2, B4, B9) | 부분 — 창·레이아웃 동작, 편집기 메뉴 47 % [menu_count]; Assign Material 동작 [first_hour #21–22 OK] | Shader Editor |
| 5-2 | Arnold / Standard Surface | **A** · 6 (A1, A4, A9, A10, A11, A14) | 부분 — standardSurface 이름 = Principled 매핑 [step 67], Arnold 없음 | Principled BSDF, Cycles |
| 5-3 | 라이트 종류 | **A** · 6 (A1, A2, A3, A9, A10, A11) | 동작 (Maya 강도·감쇠, Ambient/Volume) [steps 137, 214] | Lights |
| 5-4 | Render Settings / Render View | **B** · 5 (A2, A3, A9, B2, B4) | 부분 — 메뉴 48 % [menu_count]; 배경 회색 [first_hour #34] | Properties > Render |
| 5-5 | Render Layers / Render Setup | C · 2 (B16, B17) | 동작 (Render Layer Editor) | View Layers |
| 5-6 | Batch Render | C · 2 (A1, A4) | 동작 [step 152] | 커맨드라인 렌더 |

## 8. 영역 6 — FX·스크립팅 (보류)

| # | 기능 | 빈도 · 근거 | 키트 상태 | Blender 대응 |
|---|---|---|---|---|
| 6-1 | MEL / Python, Script Editor | **A** · 7 (A10, A13, B26, B47, B49, B50, B53) | 부분 — Python만, `maya.cmds` 흉내는 216에서 멈춤(사용자 결정), MEL 없음 [README Known limits; HANDOFF] | Python 콘솔 / Text |
| 6-2 | nCloth / Nucleus, Bullet 리지드 | C · 2–3 (A10, A11 / A3, A10, A11) | 부분 — FX 메뉴 21 % [menu_count] | Cloth / Rigid Body |
| 6-3 | Bifrost, MASH | C · 2–3 (A4, A5, A10 / A10, A11) | 회색 (MASH는 메뉴 데이터에도 항목 없음, IDENTITY Blindspot #9) | Geometry Nodes |
| 6-4 | Paint Effects | C · 1 추정 (A11) | 회색 (Generate 메뉴) | Grease Pencil / GN |

---

## 9. 이 목록에서 읽히는 것

1. **근거가 가장 많은 기능은 리깅·스킨 쪽이다**: Paint Skin Weights 14, Bind Skin 13, Create Joints 11, Constraints 11, IK Handle 10, Graph Editor 11. 교육 과정(A9–A16)과 게임 문서(A17, B35–B48)가 같은 기능을 반복한다 [사실: 근거 수]. DIRECTION의 영역 2 "깊게 투자"와 맞는다 [해석].
2. **많이 쓰는 기능의 메뉴는 이미 거의 다 있다.** 이 표에서 A·B 등급 90행 = 동작 64 · 부분 24 · 회색 2(IK/FK 키, LOD Group 줄) · 없음 0 [사실: 이 표 집계; 3-9는 1-21과 같은 항목]. 메뉴 동작률을 올리는 작업은 이 목록의 우선순위와 거의 상관이 없다.
3. **공백은 "단계 사이 연결"에 몰려 있다**: 모델 → UV(여는 방식, 편집 모드 투영), 리그 → 웨이트(Q로 나가기, B 브러시), 리그 → 엔진(FBX 리그 BLOCKED, Game Exporter가 Blender 창), 애니 → 엔진(클립). "에셋 하나를 끝까지"라는 DIRECTION 기준이 바로 이 연결을 잰다 [해석].
4. **커뮤니티가 "Maya가 낫다"고 꼽은 것**은 UV 툴(B12, B28), 웨이트 페인트·Component Editor(B23, B24), 리깅 노드(B15)였다. 셋 다 키트에 동작으로 있지만 사람 손으로 확인되지 않았다(`docs/manual_checks.md` 미체크 667 / 체크 106) [사실].
