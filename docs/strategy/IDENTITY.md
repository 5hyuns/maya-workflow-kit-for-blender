# IDENTITY — Maya Workflow Kit는 어떤 도구가 될 것인가: 수요 기반 구현 순서 (2026-10-26)

근거 자료와 인용은 `IDENTITY_RESEARCH.md`, 원자료는 `data/`. 1차 문서(`STRATEGY.md`, `GOALS.md`, `UNKNOWNS.md`)의 결정(P1+P2, 영어만, 메뉴·편집기 늘리기 멈춤)을 전제로 하고, 바꾸자고 하는 곳은 그렇다고 적었다. 표기: **[사실]** 출처·저장소에서 확인 · **[추정]** 해석 · **[delegated]** 묻지 않고 정한 판단.

---

## 0. 요약 (결론 먼저)

1. **수요가 가장 큰 영역은 ⑥ 키프레임 애니메이션, 그 다음이 ⑧ 파일 왕복이다.** 합성 수요 지수 ⑥ 73, ② 60, ① 47, ⑦·⑧ 41 / 이주 신호만 보면 ⑧ 71, ⑥ 69, ① 47, ⑤ 34, ② 17 [추정, `IDENTITY_RESEARCH.md` §0.6].
2. 애니메이션은 세 신호가 겹치는 유일한 영역이다: 유튜브 Maya→Blender 이주 영상 주제 1위(39편, 160만 조회), Blender 사용자 스스로 꼽은 "가장 집중해야 할 영역" 1위(1,351표), Maya에 남는 대표 이유("animation & rigging") [사실].
3. **"일본 애니메이터 수요가 높다"는 반만 맞다.** 일본 채용 공고에서는 애니메이터 모집이 1위(115개사 중 65)지만, 일본 3DCG 디자이너 본인 직군은 모델러 33 % > 애니메이터 18 %이고, 일본 애니 CG의 Blender 이전은 3ds Max 출신이며, 키트에 대한 일본어 반응에 애니메이션 언급이 없다 [사실]. 애니메이션을 앞에 두는 근거는 일본이 아니라 전 세계 공통 신호다.
4. 사용자의 예시에 대한 답: **MASH(모션그래픽)는 뒤, NURBS는 "리그 컨트롤 커브" 용도만 중간, 애니메이션 계열이 먼저.** MASH는 Maya 학습자 관심은 있지만(튜토리얼 65만 조회) Blender로 옮기려는 사람의 신호가 거의 0이다("MASH Blender equivalent" 관련 영상 2편, 3,050 조회; BlenderArtists 0건) [사실].
5. 다만 지금까지 **키트를 실제로 써 본 사람의 신호는 모델링 손**이다(외부 이슈 #80·#84, BA 시험기의 D 피벗·Quad Draw) [사실]. 그래서 ① 손·② 모델링은 "새 기능 없이 바닥 유지"로 계속 고친다.
6. 추천 정체성 [delegated]: **"Maya 애니메이터의 Blender 작업대 — Maya 손으로 Blender 리그를 움직이고, 결과를 Maya로 돌려보낸다."** 대안: **"두 집 살림 키트 — 손은 Maya, 파일은 양쪽에서 그대로 열린다."**
7. "첫 1시간"은 하나의 시나리오가 아니라 **직군별 경로(모델러 경로 / 애니메이터 경로)** 로 나눈다. 지금의 측정(`docs/first_hour.md`)은 둘을 섞었고, 애니메이터 경로는 키트가 직접 만든 3관절 리그로 쟀다 — 실제 애니메이터는 남이 만든 리그(Rigify, Auto-Rig Pro, 커뮤니티 리그)를 쓴다.

---

## 1. Blindspot — "어느 영역을 먼저 책임질까" (`/unknowns:blindspot`)

**요청한 것**: Maya 워크플로우를 영역으로 나눠, 이 키트가 먼저 책임질 영역과 이유를 정한다. 메뉴 동작률이 61 %인 키트에서 "어디가 덜 됐나"를 고르는 일처럼 들린다.

**실제로 들어가는 곳**:
- 동작률 표(`tools/menu_count.py`)는 **수요와 거꾸로** 생겼다: 수요가 큰 애니메이션 쪽(Graph Editor 82 %, Dope Sheet 87 %, Skeleton 94 %)은 이미 높고, 수요가 작은 FX(21 %)·Generate(4 %)가 낮다 [사실]. 동작률을 올리는 방향으로 가면 수요 낮은 곳에 시간을 쓴다.
- 애니메이션의 남은 공백은 **메뉴가 아니라 손 감각과 개념**(키 선택·축 고정 드래그·커브만 보기, Y가 위가 아님, 레이어=NLA, 리그 출처)이고, 이 둘은 헤드리스 테스트로 증명이 안 된다(수동 확인 773개 중 106개 체크) [사실].
- 반응(누가 써 봤나)과 수요(누가 필요한가)가 다른 사람을 가리킨다: 반응 = 일본 모델러·제너럴리스트의 외형 감탄 + 모델링 버그, 수요 = 영어권 애니메이터 + 파이프라인.

**집계**: Landmine 4 · Convention 2 · Missing concept 3 · History 2 (11장)

| # | 종류 | 발견 | 왜 아픈가 | 권장 조치 (prompt fix) |
|---|---|---|---|---|
| 1 | Missing concept | **"리그는 어디서 오나"** 가 계획에 없다. Maya 애니메이터는 리그를 직접 만들지 않고 받아 쓴다. Maya 리그는 FBX로 컨트롤이 깨져 온다(X 답글, r/Maya "the main issue is always will be your control rig"). 키트의 Quick Rig는 Rigify 메타리그를 붙이는 데서 끝나고, **생성된 Rigify 리그를 Maya 손으로 애니메이트하는 테스트는 없다** (`tests/test_step62_rigging_tools.py:264`, grep) [사실] | 애니메이터 경로의 첫 단계가 비어 있다. 키트 측정은 3관절 자체 리그로 OK를 받았지만 실제 사용 조건과 다르다 | "애니메이터 경로 = Rigify(그리고 공개 커뮤니티 리그 1개) 위에서 Channel Box·컨트롤 선택·S 키·IK/FK 전환·Graph Editor"로 측정 시나리오를 다시 쓴다 |
| 2 | Landmine | **반응 신호 ≠ 수요 신호.** 외부 이슈 6건 중 애니메이션 0, 모델링 손 2 (#80, #84) [사실]. 수요 지수는 애니·파이프라인 | 수요만 보고 모델링 손을 내려놓으면 지금 쓰는 사람이 떠난다 | ①②는 "새 기능 0, 버그·감각만"을 바닥으로 계속. 우선순위 표에 "현재 사용자 보고" 칸을 둔다 |
| 3 | History | **가설 "일본 = 애니메이터"** — 채용 1위는 맞지만 인구·이주 신호는 아님(§0, `IDENTITY_RESEARCH.md` ⑥-a) | 일본 애니메이터 맞춤(일본어 + 애니 튜토리얼)에 투자하면 근거 없는 곳에 쓴다 | 애니메이션 우선은 전 세계 근거로 정하고, 일본 애니메이터 비중은 설문 Q1×언어로 따로 확인 |
| 4 | Missing concept | **"첫 1시간"이 직군을 섞었다.** 측정 39동작 = 모델 → UV → 머티리얼 → 리그 → 애니 → 렌더 → FBX를 한 사람이 다 함 (`docs/first_hour.md`) | 모델러는 리그를 안 만들고, 애니메이터는 모델을 안 만든다. 합계 BLOCKED 2는 어느 직군의 숫자도 아니다 | 지표를 "경로별 막힘"으로 바꾼다: 모델러 경로(②③④ + ①), 애니메이터 경로(받은 리그 → ⑥ → 플레이블라스트 → ⑧ 내보내기) |
| 5 | Landmine | **Blender 자체의 애니메이션 로드맵과 겹친다.** 키트 애니 레이어는 NLA 트랙으로 만들었다(step 180·194·204, tweak 모드 한계 메모). Blender는 4.4부터 layered/slotted action을 넣고 있다 [사실: `compat.id_fcurves` 메모] / 레이어 본격 도입 시점 [U] | Blender가 레이어를 내놓으면 키트 레이어가 충돌하거나 쓸모없어진다 | ⑥ 투자는 "Blender 데이터 위의 손 감각"(Graph Editor 조작, 키 선택, 채널 이름)에 두고, 데이터 구조 재구현(레이어·Time Editor)은 더 늘리지 않는다 |
| 6 | Landmine | **애니메이터의 "감각"은 시뮬레이션 이벤트로 못 잰다.** 시뮬레이션 이벤트는 수정키를 창 상태에 복사하지 않고(step 170), DOUBLE_CLICK을 못 보낸다(step 73) [사실: CLAUDE.md] | Graph Editor를 고쳐도 "고쳐졌다"를 증명할 길이 사람 확인뿐이다 | 사람 1명(Maya 애니메이터)의 녹화 세션을 ⑥ 작업의 완료 조건으로 둔다 |
| 7 | Missing concept | **수요 지표에 "Maya 경력자 이주자"를 직접 재는 것이 없다.** 유튜브 조회는 바이럴에, Maya 튜토리얼은 학생에, Blender 설문은 Blender 원주민에 치우친다 | 순위가 지표 선택에 따라 바뀐다: 인구 지표면 ② 모델링, 이주 지표면 ⑧·⑥ | 합성 지수는 출발점으로만 쓰고, 설문 Q-A·Q-B(§7)로 2주 안에 검증 |
| 8 | Landmine | **리그 FBX 문제는 스케일보다 깊다.** Blender 본의 롤·길이 축과 Maya 조인트 오리엔트가 달라 "bones radically change shape"(Autodesk 포럼), IK는 pre-rotation 처리가 필요(Better FBX 설명) [사실: 인용] | "rotate −90 / scale 100만 고치면 된다"로 잡으면 다음 단계에서 다시 막힌다 | ⑧ 작업은 mayapy 왕복 검증(이미 `research/scripts/first_hour_217/`)을 완료 조건으로, 범위는 "스켈레톤+스킨+키 애니"까지(컨트롤 리그는 안 함) |
| 9 | Convention | **원칙 "엔진은 Blender" + 동결 목록**(user_decisions 2026-10-26). MASH는 메뉴 데이터에조차 없다(`ui/menu_data.py`의 `mainMashMenu`는 메뉴셋 목록에만 있고 MENUS에 항목 없음) [사실] | MASH·nCloth·XGen·HumanIK를 재구현하면 원칙과 충돌 | ⑦은 "Blender 기능으로 가는 안내"로만. MASH 메뉴 자리를 만든다면 Geometry Nodes 안내 1장까지 |
| 10 | Convention | **태그라인 "The whole Maya workflow"** 는 유지로 결정됨(GOALS) — 그런데 'whole'의 뜻이 없다 | 외부 평가가 "전부" 기준으로 나옴(BA 시험기) | 'whole' = "한 직군의 일을 처음부터 끝까지 Maya 손으로"로 정의하고 README에 직군 경로 2개를 적는다 (§6) |
| 11 | History | **투자는 이미 고르게 갔다.** CLAUDE.md 단계 메모를 영역으로 나눠 보면 대략 모델링 18, 애니 15, 리깅 13, 씬·파일 9, 스크립팅 8, 렌더 7, UV 4, FX 2, 나머지 손·UI [추정: 수기 분류] | "애니메이션을 하자"가 새 메뉴를 만들자로 읽히면 이미 있는 것을 또 만든다 | 다음 투자는 "기능 수"가 아니라 "애니메이터 경로의 막힘 수"로 잰다 |

---

## 2. 워크플로우 영역 지도

열 설명 — **이주자가 원하는 것**: 인용 요지(원문은 `IDENTITY_RESEARCH.md`) · **Blender가 더 잘하는 것**: 사람들이 그 영역 때문에 Blender로 오는 이유 · **손 습관 비중**: 근육기억(손)이 결정적인가, 개념 차이가 결정적인가 · **키트 상태**: `tools/menu_count.py` 동작률(2026-10-26 실행), 첫 1시간 측정, 이슈 · **할 수 있는 한계**: Python 애드온으로 되는 것 / C++이 필요한 것 · **투자 대비 효과**(1–5).

| 영역 | 수요 지수 (전체 / 이주) | 이주자가 원하는 것 | Blender가 더 잘하는 것 | 손 습관 비중 | 키트 상태 [사실] | 할 수 있는 한계 | 투자 대비 효과 |
|---|---|---|---|---|---|---|---|
| ① 뷰포트 조작·선택 | 47 / 47 | Maya 내비게이션·선택 그대로, 튜토리얼과 키 충돌 해결 (유튜브 24편; "Maya users have to start over from scratch") | 모드 덕분에 다른 캐릭터를 실수로 키 찍지 않음 | **손 (최대)** | 핫키 행 전부 분류(step 107), 홀드 키·핫박스·마킹 메뉴·CB; BA 시험기 지적(D 피벗, 숫자패드); 외부 이슈 #80·#84 | 거의 다 Python 가능. 회전/스케일 피벗 분리·필드 MMB 드래그는 C (README Known limits) | **4** — 모든 직군의 바닥, 이미 대부분 있음, 버그 비용 작음 |
| ② 폴리 모델링 | 60 / 17 | Multi-Cut·Quad Draw·압출 후 바로 이동 같은 손 감각. 질문은 적음 ("very smooth") | 모디파이어·비파괴·스컬프트·GN; "Going back to Maya to model feels so outdated" | 손 | Mesh 81 %, Edit Mesh 89 %, Mesh Tools 81 %; 첫 1시간 모델 단계 10/10 OK; #89 Quad Draw 잔여 | bmesh로 거의 다 가능 (step 139 mayapy 일치) | **3** — 인구 최대지만 이주 고통 작음; 버그만 |
| ③ UV | 25 / 10 | Maya Cut/Sew·Unfold·셸 색 ("Mayaの方がやりやすい", "I was only using Maya for unfolding UVs") | 애드온 생태계(UVPackmaster 등) | 손 + 도구 | UV 95 %, UV Editor 85 %; 첫 1시간 #13·#14 AWKWARD | Python 가능 | **2** — 이미 높고 질문 적음; #13·#14만 |
| ④ 머티리얼·라이팅·렌더 | 26 / 20 | 렌더 레이어·라이트 단위·Arnold 용어를 Blender로 번역 | **EEVEE·Cycles = 오는 이유** (Flow, 산지겐) | 개념 | Rendering 메뉴 43 %, Hypershade 47 %, Render Settings 48 %; #123; 첫 1시간 #34 AWKWARD | 연결·용어 안내는 Python; Arnold 재현은 안 함(원칙) | **3** — 작은 연결로 "온 이유"를 맛보게 함 |
| ⑤ 리깅 | 39 / 34 | 조인트↔본 개념, 커브 컨트롤, 웨이트 페인트 ("worst experience … is weight painting"), 리그 성능 | 벤디 본, 비파괴 Armature 모디파이어, Rigify | **개념 + 성능** | Skeleton 94 %, Skin 89 %, Constrain 90 %, Deform 81 %; 첫 1시간 #27 AWKWARD | 웨이트 브러시 엔진·병렬 리그 평가·GPU 디포머는 C; 개념 번역·도구는 Python | **3** — 애니메이터가 *쓰는* 쪽(포즈 본 CB, 컨트롤 선택)은 효과 큼, 리거용 깊이는 작음 |
| ⑥ 키프레임 애니메이션 | **73 / 69** | Graph Editor 손(선택 커브만 보기, Shift+MMB 축 고정, 값 입력), 레이어, 키 찍기 ("isn't really meant to be used for animation", 「イチイチXかY押してから」) | F-Curve 모디파이어(Noise), 모드로 실수 방지, 키 복사 쉬움 | **손 + 개념(Y-up)** | Key 73 %, Playback 73 %, Graph Editor 82 %, Dope Sheet 87 %, 애니 레이어·플레이블라스트·고스팅 있음; 첫 1시간 #30 AWKWARD(Y가 위가 아님) | Graph Editor 조작은 키맵·모달로 가능; 커브별 표시 스케일 없음(step 150), NLA 트윅 한계(step 180), Blender 레이어 로드맵 | **5** — 수요 최대, 메뉴는 이미 있어 남은 일이 "감각"이라 상대적으로 쌈 |
| ⑦ FX·시뮬 (MASH·nCloth·XGen·Bifrost) | 41 / 14 | XGen·MASH 바람 (BA), 실제 이주 질문은 거의 없음 (MASH 3천 조회) | GN·Physics (단, 시뮬은 Blender 약점으로 평가됨) | 개념 (손 아님) | FX 메뉴셋 21 % (nConstraint 0 %, Fluids 16 %); MASH 메뉴 없음 | 솔버는 C; GN 노드 그룹 생성은 Python 가능하나 큼 | **1** — 안내만 |
| ⑧ 씬·파일·파이프라인 | 41 / **71** | 리그·애니 FBX가 Maya에서 그대로 열림, 단위·축 (BA 114건 최다) | 오픈소스로 옛 버전 유지, USD 발전 중 | **개념 (신뢰)** | File 87 %, Reference Editor 71 %; 첫 1시간 **BLOCKED 2 (#37, #39)** | FBX 익스포터가 Python 애드온 → 감싸기·후처리 가능; mayapy로 검증 가능 | **4** — P2의 핵심, 막힘이 측정됨, 비용 M |
| ⑨ 스크립팅·커스터마이즈 | 21 / 11 | 셸프 버튼 쉽게 ("easily add them to shelves") | Python API가 더 낫다는 TA 증언 | 개념 | Script Editor 76 %, 셸프 완료, maya.cmds 216에서 동결 | 가능 | **1** — 동결 유지 |

---

## 3. 페르소나 × 영역 매트릭스 [추정]

비중 = 하루 작업 시간 중 그 영역에 쓰는 비율(합 100). 근거: CGWORLD 직군 비율, 각 영역 인용, 1차 조사의 GitHub 스타 직함(TA·Pipeline TD·리깅 TA 다수), X 반응(외형·스위치), 일본 시장(제너럴리스트 44 %). ★ = 막히면 Maya로 돌아가는 영역.

| 페르소나 | ① 손 | ② 모델 | ③ UV | ④ 렌더 | ⑤ 리그 | ⑥ 애니 | ⑦ FX | ⑧ 파일 | ⑨ 스크립트 | 막히면 포기 | 근거 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 모델러형 (개인 작업) | 20 ★ | 40 | 15 | 20 | – | – | – | 5 | – | ① 손(첫 5분 카메라·피벗), ③ UV | note みよちゃん 첫 5분 [재인용], gorouya UV |
| P1 애니메이터형 (개인 단편) | 15 | – | – | 10 | 10 (받은 리그 다루기) | 55 ★ | – | 10 ★ | – | ⑥ Graph Editor, ⑤ 리그를 못 구함 | BA 1589561, BIGFOOT, 大和司 |
| P2 게임 아티스트 (회사 Maya/집 Blender) | 15 | 35 | 20 | 10 | – | – | – | 20 ★ | – | ⑧ FBX 축·단위 | Zenn hota(게임 TA), BA 파이프라인 114건 |
| P2 애니메이터 (회사 Maya/프리랜스 Blender) | 15 | – | – | 5 | 10 | 50 ★ | – | 20 ★ | – | ⑧ 리그 왕복, ⑥ Y-up | X 답글(리그 import), first_hour #30·#39 |
| P2 리거/TA | 10 | 5 | – | – | 45 ★ | 5 | – | 20 | 15 | ⑤ 웨이트·성능, ⑧ | devtalk, BA "8x faster", GitHub 스타 직함 |
| 일본 제너럴리스트 (도달 최대층) | 20 | 30 | 10 | 15 | 10 | 10 | 5 | – | – | ① (외형으로 들어와 손에서 판단) | CGWORLD 44 %, X 반응 = 외형 |

읽는 법 [추정]: 애니메이터형은 하루의 절반 이상이 ⑥에 몰려 있어 ⑥이 깨지면 키트 전체가 쓸모없다. 모델러형은 ①만 통과하면 나머지는 Blender 방식으로도 버틴다("very smooth"). 그래서 **같은 투자에 대한 이탈 방지 효과는 ⑥이 가장 크고, 도달 효과는 ①②가 크다.**

---

## 4. 앞으로 구현 순서 — Top 10 기능 묶음

점수 = 수요(1–5) × 현재 공백(1–5, 키트 상태 반영) × 구현 가능성(1–5, 비용이 작고 Python으로 될수록 높음). 비용 S/M/L. [추정: 점수는 근거를 숫자로 옮긴 판단]

| 순위 | 기능 묶음 | 대상 직군 | 수요 근거 | 키트 현재 상태 | Blender 대응 (그대로 연결?) | 비용 | 수요×공백×가능 = 점수 |
|---|---|---|---|---|---|---|---|
| **1** | **받은 리그를 Maya 손으로 애니메이트** — Rigify·커뮤니티 리그에서 컨트롤 클릭 선택, Channel Box(포즈 본), S 키, IK/FK 전환 속성 노출, 포즈 미러/복사, 선택 세트 | P1·P2 애니메이터 | ⑥ 지수 73; "리그는 어디서" 공백(카드 1); Blender 설문 Animation 1위 | 포즈 본 CB(step 55), 픽워크; Rigify는 메타리그 추가까지만, 생성 리그 위 테스트 없음 | 리그는 Blender 것 그대로, 키트는 손만 얹음 | M | 5×4×4 = **80** |
| **2** | **Translate Y(위) 문제 표시** — Maya 위 방향을 Channel Box·키 찍을 때 보여 줌 | 애니메이터 | first_hour #30 (점수 6.0, 최고) | 없음 (결정 5: Z-up 유지) | 표시만 (월드 바꾸지 않음) | S | 4×4×5 = **80** (비용 S라 1번과 같은 달에) |
| **3** | **Graph Editor 손 감각** — 선택 채널 커브만 보기, Shift+MMB 축 고정 드래그, 키 값 바로 입력, Ctrl+MMB 확대 위치 유지, 정규화 | 애니메이터 | BA 1589561, Brian Kouhi("really pisses people off"), BIGFOOT 「Shift+MMDで」, REACTING 영상 | Graph Editor 메뉴 82 %, 키 선택 규칙(step 170), 아웃라이너(step 150) — 감각은 사람 확인 없음 | Blender Graph Editor 위에 키맵·모달 | M | 5×3×4 = **60** |
| **4** | **리그+애니 FBX를 Maya로 (그리고 되돌리기)** | P2 애니메이터·게임 | BA 파이프라인 114건(1위), 이주 지수 71, X 답글, first_hour BLOCKED 2 | 메시 OK, 스킨 리그 BLOCKED (#37, #39) | Blender FBX 익스포터(Python) 감싸기 + mayapy 검증 | M–L | 4×5×3 = **60** |
| **5** | **모델링 손 버그 바닥** — 압출 후 이동, 더블클릭 루프, D 피벗, 숫자패드 | P1 모델러, 일본 제너럴리스트 | 외부 이슈 #80·#84, BA 시험기; 인구 지수 최대(②) | 대부분 동작, 보고된 것만 수정됨 | — | S (계속) | 5×2×5 = **50** |
| **6** | **Blender 렌더로 가는 Maya 자리** — Render 메뉴·Render Settings에서 EEVEE/Cycles 한 번에, 렌더 레이어 ↔ View Layer, 라이트 단위 안내 | 모든 직군 | "오는 이유"(Flow, 산지겐), BA 렌더 28건 | 43–48 %, #123 | 그대로 연결 | S–M | 3×3×5 = **45** |
| **7** | **스킨 웨이트 손** — Paint Skin Weights에서 Q/W/E/R로 나가기, 미러·복사, Component Editor 감각 | P2 리거, 애니메이터(자기 리그) | devtalk "worst experience", Maya 스킨 튜토리얼 91만 | first_hour #27 AWKWARD; step 149·159·213 | 브러시는 Blender 것 | S–M | 3×3×4 = **36** |
| **8** | **커브 컨트롤 → 본 셰이프** — Maya식으로 NURBS 커브를 그려 컨트롤로 쓰면 Blender 본 커스텀 셰이프로 연결 | 리거/TA, 개인 리그 만드는 애니메이터 | 리그 컨트롤 커브 튜토리얼 65만; Zenn「骨をコントローラーにする」 개념 차이 | 커브 도구 89 %(step 156), AE "Display as Control Shape"만 | 본 custom_shape | M | 3×4×3 = **36** |
| **9** | **Quad Draw 감각** (#89) | 모델러·게임 | Maya Quad Draw 튜토리얼 123만; BA "Quaddraw not like Maya" | 도구 있음, #89 잔여 | (PolyQuilt 등 대안 있음) | M | 3×3×3 = **27** |
| **10** | **HumanIK·모캡 정리 → Blender 길 안내** (리타깃 애드온·NLA 안내) | 게임 애니메이터 | Maya의 강점으로 자주 꼽힘(mimic), 튜토리얼 37만 | Rigify 안내 notice | 내장 리타깃 없음 → 안내만 | S | 2×5×2 = **20** |

순위 밖(이유):
| 묶음 | 점수 | 이유 |
|---|---|---|
| 애니 레이어·Time Editor 더 깊이 | 3×2×2 = 12 | 이미 구현(step 180·194·204), Blender 레이어 로드맵과 충돌 위험(카드 5) |
| UV Toolkit 더 깊이 | 3×1×4 = 12 | 95 %, 질문 적음 — #13·#14만 |
| XGen → 헤어 커브 | 3×4×1 = 12 | 학습자 관심 큼(135만)이나 재구현 비용 L, 원칙상 안내 |
| **MASH** | 1×5×1 = **5** | 이주 신호 ≈ 0, 메뉴 자체 없음, GN 재구현 L |
| nCloth/Bifrost/파티클 | 1×4×2 = 8 | 이주 신호 작음, 솔버 C — 안내만 |
| NURBS 서피스 모델링 | 2×3×1 = 6 | Blender 설문 NURBS 629표는 제품·CAD 쪽 [추정], 동결 목록 |
| maya.cmds·스크립팅 | 1×2×3 = 6 | 동결 |

### 4.1 영역별 순서 (1→9) [delegated]

| 순서 | 영역 | 이 영역에서 하는 일 | 이유 한 줄 |
|---|---|---|---|
| 1 | ⑥ 키프레임 애니메이션 | 받은 리그 + Graph Editor 손 + Y-up 표시 | 수요 지수 1위, Maya에 남는 이유, 메뉴는 이미 있어 남은 일이 감각 |
| 2 | ⑧ 파일·파이프라인 | 리그·애니 FBX 왕복 | 이주 신호 1위, 측정된 BLOCKED 2, P2의 신뢰 |
| 3 | ① 손 | 새 기능 없이 보고된 버그·감각 (계속 진행되는 바닥) | 모든 직군의 입구, 지금 사용자의 보고가 여기 |
| 4 | ⑤ 리깅 | 애니메이터가 *쓰는* 쪽 먼저(포즈 본·스킨 손), 리거 깊이는 뒤 | ⑥과 이어짐, 개념 차이 큼 |
| 5 | ② 모델링 | 버그만, Quad Draw는 설문 결과로 | 인구 최대지만 Blender가 더 낫다는 평 |
| 6 | ④ 렌더 | Blender 엔진으로 가는 Maya 자리 (#123의 Render 부분) | 오는 이유, 작은 연결로 효과 |
| 7 | ③ UV | #13·#14만 | 95 %, 질문 적음 |
| 8 | ⑦ FX | 안내만 (MASH·nCloth·XGen → Blender 기능 한 줄) | 이주 신호 작음, 원칙 |
| 9 | ⑨ 스크립팅 | 동결 | 신호 최소 |

GOALS의 "1순위 = 리그 FBX 왕복 + Y-up 안내"는 **유지하되 2순위로 옮기고, 그 앞에 "받은 리그를 Maya 손으로 애니메이트"를 둔다** [delegated]. 이유: FBX 왕복은 P2 중 *Maya로 보내는* 사람만의 문제이고, 리그를 다루는 손은 P1·P2 애니메이터 전원의 첫 단계다. 둘 다 같은 3개월 안에 들어간다.

---

## 5. 정체성 후보 (`/unknowns:brainstorm`)

| # | 한 문장 정체성 | 집중 영역 | 의도적으로 얕게 | 대상 | 6개월 뒤 사용자가 하는 말 | 위험 | 지금 코드에 있는 것 / 없는 것 |
|---|---|---|---|---|---|---|---|
| **I1** | Maya 손으로 하는 Blender 모델링·렌더 키트 | ② ③ ④ (+①) | ⑤ ⑥ ⑦ | P1 모델러, 게임 아티스트, 일본 제너럴리스트 | "모델링은 Maya 손 그대로고 렌더는 EEVEE라 빠르다" | 이주 고통이 작은 곳(②)에 집중 → "Blender 그냥 배우면 되잖아"; 경쟁품(Maya Config)과 같은 자리 | 있음: ②③ 80–95 %, 렌더 메뉴 절반 / 없음: 렌더 연결 다듬기 |
| **I2** | **Maya 애니메이터의 Blender 작업대** — 받은 리그를 Maya 손으로 움직이고 Maya로 돌려보낸다 | ⑥ ① ⑧ (+⑤ 쓰는 쪽) | ② ③ ⑦ ⑨ (유지) | P1·P2 애니메이터 | "Rigify 리그로 단편 한 편을 Maya 감각으로 끝냈고, 회사 Maya에 FBX로 넘겼다" | 지금 반응층(모델러·외형)과 다름; 감각은 사람 확인 필요; 애니메이터는 작은 인구 | 있음: Graph Editor/Dope Sheet 80 %대, 레이어, 플레이블라스트, 포즈 본 CB / 없음: 생성 리그 위 측정, Graph Editor 손 감각 확인, 리그 FBX |
| **I3** | **두 집 살림 키트** — 손은 Maya, 파일은 양쪽에서 그대로 열린다 | ① ⑧ | ⑦ ⑨, 나머지 유지 | P2 전체 (게임·애니) | "회사 Maya와 집 Blender 사이에 FBX가 한 번도 안 깨졌다" | FBX 함정이 깊음(카드 8); 손 외 가치가 '안 깨짐'뿐이라 눈에 안 띔 | 있음: 파일 I/O Maya 프리셋(step 102·138), 메시 왕복 OK / 없음: 리그·애니 왕복 |
| **I4** | 얇고 단단한 손 — 키맵·핫박스·Channel Box만, 나머지는 Blender 그대로 안내 | ① | ②–⑨ 전부 Blender 방식 | P1 전체 | "Blender를 배우는 3주 동안 손이 안 꼬였다" | 이미 만든 깊이(1,300개 메뉴)를 버리는 셈; AI로 1주면 흉내 가능한 층(RESEARCH E) | 있음: 거의 다 / 없음: 두 언어 툴팁 전면 |
| **I5** | Maya 리거·TA의 Blender 번역기 — 조인트·커브 컨트롤·스킨을 Blender 본·셰이프·웨이트로 | ⑤ ⑧ ⑨ | ② ③ ④ ⑦ | P2 리거/TA, 중화권 TA | "Maya식 리그 순서로 Blender 리그를 짰다" | 성능·브러시는 C 영역; 리거는 가장 회의적(1차 C) | 있음: Skeleton 94 %, Skin 89 %, SDK·디포머 / 없음: 커브→본 셰이프, 리그 성능 |
| **I6** | Maya→Blender 통역사 — 모든 Maya 동작이 Blender 이름·키를 같이 보여 주고, 언젠가 Blender로 졸업해도 됨 | ① + 전 영역 얕게 | 깊은 재현 전부 | P1 (학습 의지 있음) | "Maya 손으로 시작했는데 이제 Blender 키도 안다" | "Blender 배우면 되잖아"와 같은 결론으로 가서 키트 필요가 줄어듦 | 있음: 마킹 메뉴 한 곳의 "(Blender: …)", 315+ 안내 / 없음: 전면 두 언어 |
| **I7** | 개인 단편 완주 키트 — Maya 손으로 Blender에서 모델 → 리그(Rigify) → 애니 → EEVEE 렌더 한 편 | ⑥ ④ ① (② 바닥) | ⑦ ⑨ ③ | P1 (개인 작업이 목적) | "Maya 라이선스 없이 내 단편을 Maya 손으로 끝냈다" | 범위가 넓어 다시 '전부'로 흐름 | 있음: 각 단계 메뉴 / 없음: 경로 측정·튜토리얼 |
| **I8** | (현행) Maya 전체 복제 — 메뉴·편집기 패리티 | 전부 | 없음 | 모두 | "메뉴가 전부 있네" | 수요와 거꾸로 투자(카드 및 §1); 이미 GOALS에서 멈춤 결정 | 61 % |

---

## 6. 추천

### 1순위: I2 "Maya 애니메이터의 Blender 작업대" [delegated]

**근거**
- 수요: ⑥ 지수 73(1위), 이주 69(2위); Blender 설문 Animation 1위; 이주 영상 주제 1위 [사실 → 추정 집계].
- 이탈: 애니메이터형은 하루 50 % 이상이 ⑥이고, ⑥이 막히면 Maya로 돌아간다 — "Maya is up to 8x faster … unusable for me (when it comes to character animation)", "isn't really meant to be used for animation".
- 차별: 유료 경쟁품(Maya Config, Maya Config Pro)은 내비게이션·마킹 메뉴·셸프·모델링 툴킷 중심 [재인용 E]; "Maya처럼 보이게"는 AI로 1주면 흉내 낼 수 있다 [재인용 E]. 애니메이터의 손 감각 + 리그 왕복은 흉내 내기 어렵다.
- 비용: 메뉴·편집기는 이미 80 %대라, 남은 일은 측정·감각·FBX — 새 편집기를 만들지 않는다(GOALS "멈춤"과 맞음).

**앞으로 3개월 (영역 단위)**
| 기간 | 시간을 쓰는 곳 | 멈추는 곳 |
|---|---|---|
| 1개월 | ⑥ 애니메이터 경로 측정을 새로: Rigify 리그 + 공개 리그 1개, 사람(Maya 애니메이터) 1명 녹화 → 막힘 목록. ⑧ 리그 FBX를 mayapy 왕복으로 재현. ① 보고된 버그 | ⑦ ⑨ 새 작업 전부, ② ③ 새 기능 |
| 2개월 | ⑥ 막힘 상위부터(손 감각, Y-up 표시), ⑤ 애니메이터가 쓰는 쪽(포즈 본·스킨 손) | 레이어·Time Editor 재구현 확장 |
| 3개월 | ⑧ 리그+애니 FBX 왕복 완료, ④ 렌더 연결(#123의 Render 부분, 작게), 애니메이터 경로 재측정 | NURBS 서피스, MASH, XGen |

**맞는지 확인할 질문 3개 (설문·인터뷰)**
1. "When you animate in Blender, where does the rig come from?" — Rigify / Auto-Rig Pro / a rig someone shared / I build my own / a Maya rig via FBX / I don't animate → 애니메이터 비율과 "리그 출처"를 동시에 잰다.
2. "The last time you stopped a Blender task and went back to Maya, what were you doing?" — 영역 9개 + 자유 응답 → 이탈 영역 1위가 ⑥인지.
3. "Pick ONE thing that, if it worked exactly like Maya, would make you keep the kit on" — Graph Editor / Channel Box & keying / FBX to Maya / modeling tools / UV / render / FX(MASH, nCloth) / shelves & scripts → 순서표의 1·2위 확인.

### 대안: I3 "두 집 살림 키트"

- 언제 이쪽으로: 설문에서 "회사 Maya + 집 Blender"(Q3) 응답이 과반이고, 질문 2의 답이 ⑧ 파일이 ⑥보다 많을 때.
- 3개월: ⑧(리그·애니·카메라·단위 왕복, mayapy 자동 검증) + ① 바닥. ⑥은 Y-up 표시까지만. ② ③ ④ ⑤ ⑦ ⑨ 새 작업 없음.
- 확인 질문: "How often do files go between Maya and Blender in your week?" / "What broke the last time?" / "Would you pay attention to a kit that only guarantees the round trip?"(인터뷰).

### 태그라인 "The whole Maya workflow in Blender, in one install"

- **유지 가능** — 단, 'whole'을 "**한 직군의 일을 처음부터 끝까지**(애니메이터: 리그 받기 → 키 → Graph Editor → 플레이블라스트 → FBX로 Maya / 모델러: 모델 → UV → 머티리얼 → 렌더) Maya 손으로"로 정의하고, README·스토어에 이 두 경로를 그대로 적는다. 메뉴 전부라는 뜻이 아님을 Known limits 바로 위에 한 줄로.
- 이 정의면 FX·MASH가 비어 있어도 약속을 어기지 않는다(그 직군 경로에 없음). 반대로 애니메이터 경로가 리그 FBX에서 막히는 동안은 'whole'이 거짓이 된다 → 1순위와 2순위가 태그라인을 지키는 일이다.

---

## 7. 이 순서가 틀렸는지 확인할 설문 문항 (SURVEY.md에 추가 제안)

| # | 문항 (EN, 설문 그대로) | 유형 | 순서표의 어디를 확인하나 | 틀렸다고 볼 기준 |
|---|---|---|---|---|
| Q-A | "Which ONE area would decide whether you keep using a Maya-style setup in Blender?" — Viewport & selection / Modeling / UV / Materials & rendering / Rigging / Keyframe animation (Graph Editor, Dope Sheet) / FX & simulation (MASH, nCloth, XGen) / Files to and from Maya / Scripts & shelves | 단일 | 영역 순서 1→9 | ⑥이 상위 2에 없으면 순서 재작성 |
| Q-B | "Rank these by how much they matter to you" — Graph Editor feel / Animating a Blender rig with Channel Box & S key / Rig + animation FBX to Maya / Quad Draw & Multi-Cut feel / UV Toolkit / MASH-like motion graphics / NURBS curves for rig controls / nCloth & XGen equivalents | 순위 | Top 10 묶음 | MASH나 NURBS가 상위 3이면 해당 묶음 재평가 |
| Q-C | "When you animate in Blender, where does the rig come from?" | 단일 | 묶음 1의 전제 | "I don't animate"가 70 % 이상이면 I2 → I1/I3 |
| Q-D | "What do you mainly do in 3D?" × 설문 언어 (기존 Q1) | 교차 | 일본 애니메이터 가설 | 일본어 응답의 애니메이터 비율이 영어보다 10 %p 이상 높으면 일본 애니 입구(B5·B6) 재검토 |

판정 기간·표본 [delegated]: 2주, 응답 100개 이상(언어별 30개 이상)일 때만 순서를 바꾼다. 그 전에는 이 순서로 1개월 차 작업(측정)만 한다 — 측정은 어느 정체성이든 필요하다.

---

## 8. 개선된 프롬프트 초안 (다음 작업용)

```
Maya Workflow Kit — 애니메이터 경로 기준선 (IDENTITY.md 1순위 I2, 2026-10-26).
저장소 C:/Repos/blender-maya-kit. 전제: GOALS.md(P1+P2, 영어만, 메뉴·편집기 늘리기 멈춤),
user_decisions 2026-10-26(엔진은 Blender, 동결 목록), 결정 5(Z-up 유지).

순서:
1) docs/first_hour.md를 "모델러 경로"와 "애니메이터 경로"로 나눈다. 기존 39동작은 모델러 경로로 재분류.
2) 애니메이터 경로 시나리오(tools/dogfood_first_hour.py 옆 새 시나리오): Rigify로 생성한 사람 리그
   + 공개 커뮤니티 리그 1개를 열고 → 컨트롤 클릭 선택 → Channel Box 값 입력 → S 키 → Graph Editor에서
   키 선택·축 고정 이동·탄젠트 → 플레이블라스트 → FBX(스켈레톤+스킨+키)로 내보내 mayapy로 열기.
   각 동작 OK / AWKWARD / BLOCKED + 층(손·장소·개념·엔진). 리그 파일은 tmp/에, 라이선스 확인.
3) 시뮬레이션 이벤트로 판정 못 하는 감각 항목은 docs/manual_checks.md에 "animator path" 절로 모은다
   (사람 1명 녹화로 채움).
4) 리그 FBX: #37·#39를 mayapy 왕복 테스트로 재현만 한다 (고치지 않음). 원인 후보를 축·롤·스케일로 나눠 기록.
금지: 새 Maya 메뉴·편집기, 애니 레이어/Time Editor 확장, MASH·FX·NURBS 서피스, maya.cmds.
체크포인트: 2와 4의 막힘 표를 보여 주고 멈춘다. 고칠 순서는 그 표와 설문 Q-A~Q-D를 본 뒤 정한다.
```
