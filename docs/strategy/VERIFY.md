# VERIFY — 2차 권장("애니메이션 먼저, 받은 리그 1순위")을 반증해 본다 (2026-10-26, 3차)

전제: `GOALS.md`(P1+P2, 영어만, 메뉴 늘리기 멈춤), `IDENTITY.md`·`SUMMARY2_KO.md`(2차 권장), 원자료 `data/`. 저장소(`C:/Repos/blender-maya-kit`)는 읽기만 했다.
표기: **[사실]** 출처·원자료에서 직접 확인 · **[추정]** 해석 · **[U]** 모름. 근거 강도: **강** = 독립 출처 여럿 또는 원자료 숫자 · **중** = 한두 출처, 방향은 분명 · **약** = 일화 1건·간접.

조사 방법 메모: tavily는 이번 실행 내내 **429(요청 차단)** 로 한 번도 응답하지 않았다. 그래서 WebSearch / WebFetch로 대신했고, 2차 원자료(`data/yt/yt_demand.json`, `data/web/survey.html`)를 다시 집계했다. 새 스크립트: `data/scripts/demand_sensitivity.py`. Reddit 본문은 이번에도 못 읽었다(검색 스니펫만).

---

## 1. Blindspot — 2차 권장이 틀렸을 수 있는 이유 (`/unknowns:blindspot`)

**요청한 것**: 2차 분석의 약점 찾기. 지표 몇 개를 다시 보는 일처럼 들린다.

**실제로 들어가는 곳**:
- 2차의 "애니메이션 1위"는 **지표를 어떻게 고르느냐에 달려 있다.** 같은 원자료에서 Blender 원주민 신호(Blender 설문)와 일본 채용 공고를 빼면 1위가 ⑧ 파일 왕복으로 바뀐다(아래 1.1). 애니메이션은 어느 방식으로 세도 **상위 3**에는 남지만, **1위는 아니다.**
- 이주 영상 중 애니메이션으로 센 조회수의 약 1/3은 **"Maya에서 애니메이션하고 Blender에서 렌더"** 하는 영상이다. 이런 사람은 애니메이션을 Blender로 옮기지 않는다. 정반대 신호다.
- 이 키트를 만드는 사람은 **제너럴리스트/TA이고 애니메이터가 아니다**(GitHub 프로필 "3D generalist", Maya VAT baker). 애니메이터 작업대 전략은 "감각이 맞는지"를 판정할 사람이 팀 안에 없다. 모든 완료 조건이 외부 애니메이터에게 걸린다.
- "2주·100응답일 때만 순서 변경" 규칙은 **응답이 모이지 않으면 2차 순서를 그대로 확정하는 규칙**이 된다. 반응 파도는 이미 지나갔다(스타 하루 38 → 1, 스토어 168 다운로드). 100응답이 올지가 이 규칙에서 가장 큰 변수다.

**집계**: Landmine 4 · Missing concept 3 · Convention 1 · History 2 (10장)

| # | 종류 | 발견 | 왜 아픈가 | 근거 | 권장 조치 |
|---|---|---|---|---|---|
| B1 | Landmine | **"애니메이션 1위"는 지표 선택의 결과다.** 6가지 계산 방식 중 애니메이션이 1위인 것은 Blender 설문·일본 채용을 넣은 2가지뿐. 이주자 신호만 쓰면 4가지 모두 ⑧ 파일 왕복이 1위 | 1위 근거가 "Maya 이주자"가 아닌 "Blender 사용자·일본 채용 시장"의 의견 | [사실] 1.1 표 | 판단 근거를 "애니는 상위 3에 확실히 들어감"으로 낮추고, 1위는 정하지 않은 채 확인한다 |
| B2 | Landmine | **Blender 설문은 Maya 이주자 의견이 아니다.** 응답 5,102명 중 처음 쓴 3D 앱이 Maya인 사람은 329명(6.4 %), 지금 Maya를 같이 쓰는 사람은 240명(4.7 %). "Animation이 가장 부족" 1,351표는 대부분 Blender 원주민의 의견이다 | S1이 지수의 1/5을 차지하고, 애니(99)와 모델링(100)을 끌어올린다 | [사실] `data/web/survey.html` (multi__first_3d_software, multi__companion_software, "5102 people participated") | S1은 "Blender 자체의 약점"을 보여 주는 참고 자료로만 쓴다(키트가 메울 곳이 아닐 수도 있다: B5) |
| B3 | Landmine | **유튜브 "애니메이션" 조회 160만 = 반응 영상 41 % + Maya 애니→Blender 렌더 33 % + 나머지 26 %.** 진짜 "Blender로 애니메이트하는 법" 영상은 약 41만 조회 | 조회수는 엔터테인먼트(“Maya Artist Tries Blender”)와 **Maya에 남는 하이브리드 작업**을 섞어 셌다 | [사실] `yt_demand.json` 재집계: "ATTEMPTING 3D Animation in Blender! Maya Artist's First Time" 35.5만, "How to Render Maya Animations in Blender (USD vs Alembic)" 33.9만, "Bring your Maya animations to Blender's Cycles" 7.6만, "Maya to Blender Render Workflow" 6.9만 | 하이브리드 수요(Maya 애니 → Blender 렌더)를 별도 후보로 본다(2.1) |
| B4 | Missing concept | **질의 설계가 애니메이션 쪽으로 기울어 있다.** 34개 쿼리 중 애니메이션 겨냥 6개(영어 3, 일본어 2, 중국어 1), 모델링 4, 손 3, 파일 3. 분류 순서도 애니가 맨 앞이라 겹치는 제목은 애니로 갔다 | 영상 "수"는 쿼리 수에 비례한다 | [사실] `yt_demand.json` area별 쿼리 수, `yt_classify.py` AREAS 순서 | 쿼리당 영상 수로 보면 손(8.0) > 애니(6.5) > 파일(5.3) (V4) |
| B5 | Missing concept | **Blender 애니 도구의 공백은 이미 유료 애드온이 메우고 있다.** Animation Layers($30, "made me feel like I'm animating in Maya again"), AniMate Pro("animbot for blender"), Graph Editor Toolkit(무료), SGET, **Maya Config Pro Ani**(경쟁품의 애니메이션판, $65) | 키트가 줄 수 있는 차이가 "처음부터 같이 들어 있다" 정도로 작아진다. 레이어는 Blender 자체도 준비 중 | [사실] [Animation Layers 리뷰](https://superhivemarket.com/products/animation-layers/ratings?page=4), [AniMate Pro 리뷰](https://superhivemarket.com/products/animatepro/ratings?page=2), [Graph Editor Toolkit](https://anim.works/product/graph-editor-toolkit-blender-plugin/), [Maya Config Pro Ani](https://formaffinity.gumroad.com/l/wDpgH), [Blender Actions 매뉴얼: 레이어는 아직 UI에 없음](https://docs.blender.org/manual/en/4.4/animation/actions.html) | 키트의 애니 가치는 "기능"이 아니라 **"Maya 손 그대로 + 다른 애드온 없이"** 로만 성립. 경쟁 애드온과 나란히 써 보는 비교가 필요 |
| B6 | Landmine | **Maya 애니메이터가 안 옮기는 이유의 상당 부분은 파이프라인·직장이고, 키트로 풀리지 않는다.** 스튜디오는 축적된 도구·재교육 비용 때문에 Maya에 남는다. 업계 교육은 반대 방향(Blender → Maya)을 가르친다: Animation Mentor "Maya for Blender Animators" 워크숍, Sir Wade의 "Moving From Blender to Maya" 강좌 | 회사 애니메이터는 회사에서 Maya를 계속 쓴다. 키트가 닿는 것은 **개인 작업** 쪽 애니메이터뿐 | [사실] [polycount 스레드](https://polycount.com/discussion/comment/2397574), [Animation Mentor 검색 스니펫 "Maya for Blender Animators"](https://www.animationmentor.com/blog/2025/04/), [Skillshare: Moving From Blender to Maya](https://www.skillshare.com/en/classes/moving-from-blender-to-maya-learn-a-layered-animation-workflow/992930012), [Skillshare: Bring Maya Animations to Blender](https://www.skillshare.com/en/classes/3d-animation-workflow-manage-feedback-and-bring-maya-animations-to-blender/1374631607) | P1 애니메이터(개인 단편)가 실제로 몇 명인지가 핵심 unknown(U1) |
| B7 | History | **실제 사용자 신호는 애니메이터가 아니다.** 외부 이슈 5명 6건: 모델링 손 2(#80, #84), 메뉴 옵션 박스·UI 리셋 2(#81, #82), 설치 1(#79). 애니 0. GitHub 스타 중 직함이 보이는 사람: Pipeline TD/TA 4~5, 리깅 TA 1~2, 애니 교육·제작 2(중국), 프리랜스 3D 1. BlenderArtists 시험기도 D 피벗·Quad Draw(모델링) | 권장 대상과 실제 사용자가 다르다. 실제 사용자를 떠나게 할 위험 | [사실] `gh issue list`, `data/github_user_profiles_2026-10-26.tsv` | 1순위에 "현재 사용자 보고" 칸을 둔다(2차도 제안). **바닥 유지가 아니라 경쟁 순위로** 다룬다 |
| B8 | Missing concept | **"받은 리그" 가정은 반만 맞다.** 무료 연습용 리그 생태계는 Maya 쪽이 크다(Mery, Ray 등 — Maya 리그). Blender 쪽 공개 리그는 **Blender Studio 리그(Rain, Snow, Vincent — CloudRig 기반)** 와 Rigify, 게임 쪽은 Mixamo. 개인 단편이면 **자기 캐릭터를 직접 리깅**(Rigify·Auto-Rig Pro)해야 한다 | "받은 리그 = Rigify"로 측정하면 실제 사용자(Rain 리그로 연습하는 사람, ARP 사용자)를 놓친다. P1 개인 작업이면 "리그를 직접 만든다"가 먼저일 수 있다 | [사실] [The Rookies: free Blender rigs](https://www.therookies.co/blog/resources/top-free-blender-rigs-for-3d-artists), [Blender Studio Rain](https://studio.blender.org/characters/rain/v2/), [ARP는 유료 $50](https://app.cinevva.com/guides/auto-rig-pro-alternatives); 리그 출처 비율 통계는 **못 찾음** [U] | 측정 리그 = **Rigify 휴먼 + Blender Studio Rain(CloudRig)** 2개로. 비율은 설문 Q-C로 |
| B9 | Convention | **만드는 사람이 애니메이터가 아니다.** 2차도 "손 감각은 사람이 직접 써 봐야 확인"(카드 6)이라고 했지만, 그 사람이 누군지 정하지 않았다 | I2를 고르면 모든 ⑥ 작업의 완료 조건이 외부 애니메이터에게 달린다. 섭외 실패 = 진행 정지 | [사실] 5hyuns 프로필 "3D generalist", Maya VAT baker | 사용자 인터뷰 Q2로 본인의 애니 경력을 확인 |
| B10 | History | **판정 규칙의 기본값 문제.** "2주·100응답 이상일 때만 순서 변경"인데, 현재 유입은 하루 스타 1개 수준 | 100응답이 안 오면 2차 순서가 근거 없이 확정된다 | [사실] RESEARCH A1 스타 추이, 스토어 168 / [추정] 2주 100응답은 어렵다 | 응답이 안 모일 때의 대체 규칙(인터뷰 n명, 투표 결과)을 미리 정한다(인터뷰 Q5) |

### 1.1 수요 지수 민감도 — 같은 원자료, 다른 지표 선택 [사실: 계산 / 추정: 해석]

`python -I data/scripts/demand_sensitivity.py` (각 지표 최댓값 = 100, 있는 지표의 평균).

| 방식 | 1위 | 2위 | 3위 | 4위 |
|---|---|---|---|---|
| V0 2차 원래 방식 (S1~S5) | 애니 73 | 모델링 60 | 손 47 | FX 41 |
| V1 이주자 신호만 (S3 영상 수, S4 BA) | **파일 71** | 애니 69 | 손 47 | 리깅 34 |
| V2 Blender 원주민·Maya 학습자 제외 (S2, S3, S4) | 애니 79 | 파일 71 | 손 47 | 모델링 34 |
| V3 S3를 조회수로 + 반응 영상 제외 + "Maya 애니→Blender 렌더"를 파일로 이동, + S4 | **파일 100** | 애니 50 | 리깅 32 | 손 30 |
| V4 S3를 쿼리당 영상 수로, + S4 | **파일 83** | 손 66 | 애니 59 | 리깅 33 |
| V5 BA 스레드만 | **파일 100** | 리깅 46 | 애니 38 | 손 32 |

읽는 법 [추정]: 애니메이션은 6개 중 6개에서 상위 3 안에 있다 → "애니메이션이 중요하다"는 **강**. "애니메이션이 1위"는 2/6 → **약**. 이주자 신호만 보면 파일 왕복이 1위 → "두 집 살림"(I3) 쪽 근거가 2차가 본 것보다 강하다. 단, ⑧의 상당 부분은 **Maya → Blender(렌더)** 방향이고, GOALS 1순위인 **Blender → Maya(리그 FBX)** 방향과는 다르다.

---

## 2. 반증 조사 — 약점마다 반대 근거

### 2.1 Maya 애니메이터: 실제로 옮긴 사례 vs 돌아간·안 옮긴 사례

| 방향 | 사례 | 근거 강도 | 출처 |
|---|---|---|---|
| 옮김 | Mountaineer Animation(독일): Maya → Blender로 전환, 단편 "Spiritquest" (Blender Conference 2025 발표; 이유는 페이지에 없음) | 중 | [BCON 2025 #4048](https://conference.blender.org/2025/presentations/4048/) |
| 옮김 | 오스트리아 프리랜서 애니메이터: Maya 1.0부터 쓰다 4년 전 Blender로 | 약 | [BCON 프로필 814](https://conference.blender.org/profile/814/) |
| 옮김 | 토론토 애니메이터(3dAnimationHub): "professionally transitioned from Animating in Maya to Blender", 계기는 Maya 라이선스 변경 | 약 | [BlenderNation 2020](https://www.blendernation.com/2020/06/16/moving-from-maya-to-blender-heres-what-you-need-to-know/) |
| 옮김 + 도구 재작성 | 애니메이터 Wilhelm Ogterop: Maya에서 만든 개인 도구가 그리워 Blender 애드온으로 다시 만듦 | 약 | [LinkedIn](https://bg.linkedin.com/in/wilhelm-ogterop-2529433) |
| 하이브리드(애니는 Maya에 남음) | 졸업 단편: 캐릭터 애니는 Maya, 나머지는 Blender, Alembic으로 이동 | 중 | [BlenderNation 2019](https://www.blendernation.com/2019/06/21/behind-the-scenes-3d-animated-short-film/) |
| 하이브리드 | "How to Render Maya Animations in Blender" 33.9만 조회 외 4편, 합 약 53만 | 강(숫자) | `data/yt/yt_demand.json` |
| 하이브리드 | Sir Wade 강좌 "Bring Maya Animations to Blender" | 중 | [Skillshare](https://www.skillshare.com/en/classes/3d-animation-workflow-manage-feedback-and-bring-maya-animations-to-blender/1374631607) |
| 스튜디오가 Maya로 돌아감 | Tangent Animation 말기에 Maya 파이프라인으로 옮겼다는 댓글(확인 안 됨) | 약 | [BA Tangent 스레드](https://blenderartists.org/t/tangent-animation-shuts-down/1320208?page=2) |
| 안 옮기는 이유 = 파이프라인 | 축적된 사내 도구, 재교육 비용, 지원 비용 | 중 | [polycount](https://polycount.com/discussion/comment/2397574) |
| 안 옮기는 이유 = 도구 | "Maya is up to 8x faster with rigs … unusable for me"(성능, C++ 영역), "isn't really meant to be used for animation"(Graph Editor 손) | 중 | 2차 `IDENTITY_RESEARCH.md` ⑤⑥ |

**판정 [추정]**: 돌아간 이유는 세 갈래 — **파이프라인(직장)**, **성능(리그 평가 속도, 키트로 못 고침)**, **Graph Editor 손(키트로 고칠 수 있음)**. 키트로 풀리는 것은 세 번째뿐이다. 그리고 가장 큰 무리는 "옮긴 사람"이 아니라 **애니는 Maya, 렌더는 Blender인 하이브리드**다. 이 사람들에게 키트의 Maya 손은 덜 중요하고, **Maya 애니메이션을 Blender로 가져오는 길(Alembic/USD/FBX)** 이 중요하다. 이 방향은 2차 Top 10에 없다.

### 2.2 "받은 리그" 가정
- [사실] 리그 출처 비율을 잰 조사는 **찾지 못했다** [U].
- [사실] Blender에서 무료로 바로 쓸 수 있는 애니메이터용 리그: Blender Studio의 Rain/Snow/Vincent(CC-BY, CloudRig 기반), CG Cookie VonnBots, Mixamo(게임). Rigify는 리그가 아니라 **생성기**라서 사용자가 메시에 붙이고 웨이트를 해야 한다. Auto-Rig Pro는 유료($50). ([The Rookies](https://www.therookies.co/blog/resources/top-free-blender-rigs-for-3d-artists), [cinevva](https://app.cinevva.com/guides/auto-rig-pro-alternatives))
- [추정] P1 개인 단편 애니메이터 = 자기 캐릭터를 Rigify/ARP로 **직접** 리깅할 가능성이 높다 → "받은 리그"보다 "Rigify로 만들고 바로 Maya 손으로 애니"가 맞는 시나리오. P2 애니메이터의 연습·포트폴리오 = Rain 같은 공개 리그. 게임 쪽 = Mixamo.
- 판정: 가정은 **중간**. 측정 리그를 "Rigify 생성 리그 + Rain"으로 바꾸면 두 경우를 모두 덮는다.

### 2.3 Blender 애니 도구가 이미 충분한가 (키트가 메울 공백의 크기)
- [사실] Blender 5.0 애니 변경: Copy Global Transform 내장, 본 커스텀 셰이프 "Use As Pivot / Affect Gizmo", 재생 컨트롤 푸터, Jump by Delta. **레이어 UI는 아직 없음**(Actions 매뉴얼: "not currently exposed in the UI"). ([5.0 release notes](https://developer.blender.org/docs/release_notes/5.0/animation_rigging/))
- [사실] 애드온 생태계가 Maya식 레이어·animBot식 도구·Graph Editor 도구를 이미 판다(B5). 일부 Maya 사용자 평: "This really made me feel like I'm animating in Maya again"(Animation Layers), "I can't animate in Blender without AniMate Pro".
- [사실] 반대 평도 있다: Blender 쪽이 낫다("Blender tends to have better animation tools", [BlenderNation 댓글](https://www.blendernation.com/2011/10/15/digicel-pacific-commercial/); 2차의 @POPREQ "Mayaのグラフエディタが使いづらかった").
- 판정 [추정]: 공백은 **Graph Editor 손(선택 커브만 보기, Shift+MMB 축 고정)과 Channel Box 키 찍기** 정도로 좁다. 레이어·도구 깊이는 애드온·Blender 로드맵과 겹친다. 그래서 키트의 차이는 "새 기능"이 아니라 **"손이 처음부터 Maya"** 하나다 — 이건 Maya Config Pro Ani도 노리는 자리다.

### 2.4 모델러: 이주 장애는 정말 작은가
- [사실] 이주 글에서 모델러의 최대 장애는 도구가 아니라 **단축키·근육기억·인터페이스**다("muscle memory from Maya's interface made the switch frustrating", [Ulster 블로그](https://blogs.ulster.ac.uk/curtisgirvin/?p=305); [UAL 블로그](https://yihuang.myblog.arts.ac.uk/?p=411)). 이것은 키트의 **① 손**이 정확히 푸는 문제다.
- [사실] 경쟁품 Maya Config(기본판 평가 약 750개, Pro 63개)는 내비게이션·마킹 메뉴·모델링 툴킷 중심 — 모델러·제너럴리스트 시장이 **돈을 낸 시장**이다. ([formaffinity](https://formaffinity.gumroad.com/l/FKhQL))
- [사실] 키트 실제 사용자 보고는 모델링 손(B7).
- 판정 [추정]: 2차의 "모델링 이주 신호 17"은 **질문이 적다**는 뜻이지 **사람이 적다**는 뜻이 아니다. 모델러는 ①만 맞으면 조용히 옮긴다 — 그래서 수요 지수엔 안 잡히고, 키트 다운로드·이슈엔 잡힌다. "모델러는 장애가 작다"는 맞지만, **"그래서 키트가 덜 필요하다"는 틀릴 수 있다**: 작은 장애(손)가 바로 키트의 핵심 기능이기 때문.

### 2.5 "두 집 살림"(회사 Maya + 개인 Blender) 인구
- [사실] Blender 설문 2025: Maya를 Blender와 함께 쓴다 240/5,102(4.7 %); Maya가 첫 3D 앱 329(6.4 %). 일본 CG 회사 메인 툴 Maya 58 %, Blender 사용 회사 222/351(RESEARCH B1·B2). 개인 일화: "Commercial and studio work is mostly Maya, while personal projects are Blender"([BlenderNation 릴 2014](https://www.blendernation.com/2014/10/23/reel-luciano-munoz/)), 스튜디오 일만 Maya인 애니메이터 릴([BlenderNation 2019](https://www.blendernation.com/2019/08/29/character-animation-reel-raul-ibarra/)).
- [U] 정량 조사(설문)는 없다. Blender 설문은 Blender 쪽 표본이라 "Maya 주력 + Blender 가끔"인 사람을 덜 잡는다.
- 판정 [추정]: P2는 실재하고, 2차 페르소나 표와도 맞는다. 다만 **P2가 원하는 파일 방향**(Blender→Maya 리그 vs Maya→Blender 렌더 vs 게임 엔진)은 모른다 [U].

---

## 3. 결정별 판정표

### 결정 1 — 먼저 집중할 방향

| 항목 | 내용 |
|---|---|
| 2차 주장 | I2 애니메이터 작업대 (대안 I3 두 집 살림) |
| 근거 | 애니가 상위 3 안: **강**(6/6 방식). 애니가 1위: **약**(2/6). 애니 공백이 키트로 메워짐: **중**(Graph Editor 손은 키맵으로 가능, 나머지는 애드온·로드맵과 겹침) |
| 반대 근거 | B1~B3(지표), B5(애드온), B6(파이프라인은 키트 밖), B7(실제 사용자 = 모델러·TA), B9(만드는 사람이 애니메이터 아님), 2.1(하이브리드: 애니는 Maya에 남음) |
| 남은 핵심 unknown | U1 키트 설치자 중 **Blender에서 키 애니를 하는 사람**의 비율 · U2 P2의 파일 방향 · U3 사용자 본인이 애니 감각을 판정할 수 있는가 |
| 2주 안에 싸게 확인 | ① 사용자 인터뷰 Q1~Q3(30분) ② X 투표 1개(영어, 작성자 계정): "Maya users in Blender: which part of your work did you actually move? Modeling / Animation / Rendering only (I animate in Maya) / Not yet" ③ GitHub Discussions에 "What do you use the kit for?" 글 1개(스타 81명에게 보이는 곳; @멘션 없이) ④ 설문 Q-C(리그 출처, "I don't animate" 포함) 중간 집계 |
| 잠정 결론 | **"두 집 살림(I3)을 뼈대로: ① 손 + ⑧ 파일 왕복을 우선하고, 애니메이터 경로는 측정 대상으로 둔다(투자는 측정 결과로)."** I2를 버리는 것이 아니라 **확정을 미룬다.** 이유: 이주자 신호만 보면 ⑧이 1위(4/6), 실제 사용자는 ① 손에 있음, 애니 공백은 생각보다 좁고 경쟁 애드온이 있음, 애니 감각을 판정할 사람이 아직 없음 |
| 확신도 | **55 %** (I2가 맞을 확률 약 30 %, I1 모델링·렌더 약 15 %) |
| 뒤집을 신호 | 투표·설문에서 "Animation"을 옮겼다는 답이 30 % 이상 · 설문 Q-C에서 "I don't animate"가 50 % 미만 · 사용자 본인이 키 애니 경력 3년 이상(Q2) → I2로. 반대로 Modeling만 압도적이면 I1 쪽으로 |

### 결정 2 — 1순위 조정

| 항목 | 내용 |
|---|---|
| 2차 주장 | (a) "받은 리그를 Maya 손으로 + Y-up 표시" 1순위, 리그 FBX 2순위 |
| 근거 | Y-up 표시: **강** — 키트 측정에서 최고 점수(first_hour #30), 비용 S, 결정 5(Z-up 유지)와 맞음, 모델러에게도 해 없음. 받은 리그 애니: **중~약** — 근거는 "테스트가 없다"(공백)이지 "사람들이 원한다"(수요)가 아님; 리그 출처 통계 없음. 리그 FBX(Blender→Maya): **중** — BLOCKED 2개는 측정 사실, 수요 근거는 X 답글 1건 + BA 스레드(방향 섞임) |
| 반대 근거 | 받은 리그: B8(리그는 직접 만들 가능성), B5(경쟁 애드온). 리그 FBX: 2.1(실제 흐름은 Maya→Blender가 더 큼), 깊은 함정(본 롤·pre-rotation, 2차 카드 8), 비용 M–L. 모델링 손 1순위 쪽 근거: B7(실제 보고) |
| 남은 핵심 unknown | U2 파일 방향 · U4 Rigify/Rain 리그 위에서 키트가 **지금** 얼마나 막히는가(측정 안 함 — 고칠 게 거의 없을 수도 있음) |
| 2주 안에 싸게 확인 | ① **30분 자가 테스트**: Maya 모드에서 Rigify 휴먼 + Rain 리그로 컨트롤 선택 → CB 값 → S 키 → Graph Editor 축 고정 → IK/FK, 막힘 수 기록(에이전트 dogfood + 사용자 녹화 1회) ② 리그 FBX: mayapy 왕복 재현만(고치지 않음) ③ 인터뷰 Q3(본인이 실제로 옮긴 파일과 방향) |
| 잠정 결론 | **(a)의 수정판: "Y-up 표시(S) + 보고된 모델링 손 버그"를 지금 바로 하는 1순위로, "받은 리그 애니"는 30분 측정 결과가 나온 뒤 구현 순위를 정하고, 리그 FBX는 재현만 하고 2순위 유지.** 받은 리그를 "구현 1순위"로 확정하기엔 수요 근거가 약하고, 측정이 1주 안에 끝나므로 기다리는 비용이 작다 |
| 확신도 | **60 %** |
| 뒤집을 신호 | 30분 측정에서 BLOCKED ≥ 2 또는 AWKWARD ≥ 5 → 받은 리그 애니를 구현 1순위로 · 인터뷰/설문에서 "Blender → Maya로 리그를 보낸다"가 파일 응답의 과반 → 리그 FBX를 1순위로 복귀 · 외부 이슈가 2주에 모델링 3건 이상 → 모델링 손을 단독 1순위로 |

### 결정 3 — 사용 테스트 기준

| 항목 | 내용 |
|---|---|
| 2차 주장 | (a) 모델러 경로 / 애니메이터 경로로 나누고, 애니는 Rigify·공개 리그로 측정 |
| 근거 | **강** — 지금 39동작 시나리오는 한 사람이 모델→리그→애니→FBX를 다 해서 어느 직군의 숫자도 아님(2차 카드 4, 사실). 어느 방향을 고르든 경로별 숫자가 필요. 비용이 작음(기존 dogfood 시나리오 분리) |
| 반대 근거 | 경로를 나누면 측정 비용이 2배; 애니 경로의 "감각" 항목은 시뮬레이션 이벤트로 판정 불가(사람 필요, B9). "공개 리그 1개"가 어떤 리그인지 정해지지 않음(B8) |
| 남은 핵심 unknown | U3 애니 경로를 판정할 사람 · 공개 리그 라이선스(Rain = CC-BY, tmp/에 두고 배포하지 않으면 문제 없음 [추정]) |
| 2주 안에 싸게 확인 | 시나리오 분리는 문서 작업(1일). 애니 경로는 결정 2의 30분 자가 테스트를 그대로 첫 기준선으로 씀 |
| 잠정 결론 | **(a) 채택, 단 리그를 "Rigify 생성 휴먼 + Blender Studio Rain(CloudRig)"로 고정하고, 애니 경로의 감각 항목은 "사용자 본인 녹화 1회 + 외부 애니메이터 1명"을 완료 조건으로 둔다.** 모델러 경로는 기존 39동작 중 ①②③④를 그대로 씀 |
| 확신도 | **80 %** |
| 뒤집을 신호 | 외부 애니메이터를 2주 안에 1명도 못 구함 → 애니 경로는 "자동 측정 + 본인 녹화"만 두고 감각 항목은 보류(단일 시나리오로 돌아가는 것은 아님) |

---

## 4. 결정 트리 (2주 확인 결과 → 방향)

```
[Day 1] 사용자 인터뷰 (INTERVIEW_QUESTIONS.md Q1~Q5)
   ├─ Q2: 본인 키 애니 경력 "주업/3년+" ──► 애니 감각 판정 가능 → I2 후보 유지(가중 +)
   └─ Q2: "거의 안 함" ─────────────────► I2는 외부 애니메이터 섭외가 전제 (Q4 결과로)
[Day 1-3] 즉시 1순위: Y-up 표시(S) + 보고된 모델링 손 버그   ← 어느 가지로 가도 하는 일
[Day 2-5] 30분 자가 테스트 (Rigify 휴먼 + Rain) + 리그 FBX mayapy 재현
   ├─ BLOCKED ≥ 2 또는 AWKWARD ≥ 5 ─► "리그 애니 손"을 구현 1순위로 (I2 쪽 작업 시작)
   └─ 거의 OK ─────────────────────► 애니는 바닥 유지, 다음 단계로
[Day 2-14] X 투표 1개 + GitHub Discussion + 설문(Q-A~Q-D) 중간 집계
   ├─ "Animation을 Blender로 옮겼다/옮기고 싶다" ≥ 30 % 그리고 Q-C "I don't animate" < 50 %
   │      ──► I2 애니메이터 작업대 (2차 권장 복귀)
   ├─ "Rendering only (animate in Maya)" 가 애니 응답보다 많음
   │      ──► I3 두 집 살림, 파일 방향 = Maya → Blender(Alembic/USD/FBX 애니 가져오기) 먼저
   ├─ 파일 응답 중 "Blender → Maya로 리그를 보낸다" 과반
   │      ──► I3, 리그 FBX(Blender→Maya)를 1순위로 복귀 (GOALS 원안)
   └─ Modeling이 압도적 (≥ 50 %), 애니 < 20 %
          ──► I1 모델링·렌더 (① 손 + ② + ④ 렌더 연결)
[Day 14] 응답 < 100 이면: 인터뷰 Q5에서 정한 대체 규칙 적용
          (권장: 투표 응답 ≥ 50 + 인터뷰 3명이 같은 방향이면 그쪽으로; 아니면 위 잠정 결론 유지)
```

---

## 5. 남은 핵심 unknown (영향 큰 순)

| # | unknown | 왜 큰가 | 확인 방법 | 비용 |
|---|---|---|---|---|
| U1 | 키트 설치자·관심층 중 Blender에서 **키 애니를 실제로 하는 사람** 비율 | I2 전체가 여기에 걸림 | X 투표 + 설문 Q-C + GitHub Discussion | 낮음 |
| U2 | P2의 **파일 방향**: Blender→Maya 리그 / Maya→Blender 애니(렌더) / 게임 엔진 | GOALS 1순위(리그 FBX)가 맞는 방향인지 | 인터뷰 Q3 + 설문 자유 응답 + 투표 선택지 | 낮음 |
| U3 | 애니 감각을 **판정할 사람** (본인 / 동료 / 외부) | I2를 고르면 모든 완료 조건 | 인터뷰 Q2·Q4 | 낮음 |
| U4 | Rigify·Rain 위에서 키트의 **현재 막힘 수** | 받은 리그 1순위가 "할 일이 있는가" | 30분 자가 테스트 | 낮음 |
| U5 | 2주에 응답이 **100개 오는가** | 판정 규칙이 작동하는가 | 1주 차 중간 집계 | 없음 |
| U6 | 경쟁 애드온(Animation Layers, AniMate Pro, Maya Config Pro Ani) 대비 키트의 애니 차이 | I2의 차별점 | 애드온 1~2개와 같은 30분 작업 비교(무료 Graph Editor Toolkit부터) | 중간 |

---

## 6. 확인 계획 (2주) — 바뀔 가능성이 큰 결정부터 (`/unknowns:plan`)

먼저 검토할 순서 = 사용자가 고칠 가능성이 큰 순서. 실행 순서는 §4 결정 트리를 따른다.

| 순위 | 결정 (바뀔 가능성) | 지금 정한 값 | 왜 바뀌기 쉬운가 | 확인 / 완료 조건 |
|---|---|---|---|---|
| 1 | 응답이 부족할 때의 판정 규칙 (높음) | 설문 + 투표 50개 이상 + 인터뷰 3명이 같은 방향이면 순서 변경 | 사용자 취향 문제이고, 지금 유입으로는 100응답이 어려움 | 인터뷰 Q5 답 |
| 2 | 파일 방향 (높음) | 리그 FBX(Blender→Maya)는 재현만, 2순위 | Maya→Blender 하이브리드 신호가 새로 나옴; 사용자 본인 경험이 바로 바꿀 수 있음 | 인터뷰 Q3 + 투표 선택지 "Rendering only (I animate in Maya)" |
| 3 | 방향 I3 뼈대 vs I2 (중간) | I3 뼈대, I2는 측정 대상 | U1·U3이 정해지면 바로 바뀜 | 인터뷰 Q2·Q4, 투표, 설문 Q-C |
| 4 | "받은 리그 애니"의 구현 순위 (중간) | 30분 측정 뒤 | 측정 결과가 숫자로 정함 | 막힘 수: BLOCKED ≥ 2 또는 AWKWARD ≥ 5면 구현 1순위 |
| 5 | 측정 리그 2개 (낮음) | Rigify 생성 휴먼 + Blender Studio Rain | 라이선스·버전 문제가 있으면 교체(대안: Snow, VonnBots) | Rain이 4.5/5.x에서 열리는지 1회 확인, `tmp/`에만 둠 |
| 6 | 지금 바로 하는 1순위: Y-up 표시 + 보고된 모델링 손 버그 (낮음) | 확정 | 어느 방향에서도 필요, 비용 S | 기존 테스트 + GUI 확인, first_hour #30 재측정 |
| 7 | 경로를 둘로 나누기 (낮음) | 확정 | 어느 방향에서도 필요 | `docs/first_hour.md`에 모델러 / 애니메이터 경로 두 표 |

하지 않음(2주 동안): 새 Maya 메뉴·편집기, 애니 레이어·Time Editor 확장, 리그 FBX **수정**(재현만), 경쟁 애드온 기능 따라 만들기.
