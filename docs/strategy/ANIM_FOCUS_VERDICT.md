# ANIM_FOCUS_VERDICT — "애니메이션 특화(리깅·디폼·NURBS·애니)부터 하는 것이 맞는가" (5차, 2026-10-26)

사슬 표: `CHAINS.md` (끊긴 고리 L1–L24는 그 문서 §7). 1페이지 요약: `SUMMARY5_KO.md`.
표기: **[사실]** 출처·저장소 확인 · **[추정]** 해석 · **[U]** 모름 · **[delegated]** 묻지 않고 정함.

---

## 1. 판정 A

**조건부로 맞다 (확신도 70 %).**
조건: "애니메이션 특화"를 **새 Maya 기능을 더 넣는 것**이 아니라 **이미 있는 리깅·디폼·애니 기능 사이의 끊긴 고리를 이어, 사슬 하나가 처음부터 끝(엔진)까지 Maya 손으로 통하게 하는 것**으로 정의할 때.
그리고 모델링 손 버그(외부 보고)는 지금처럼 늘 먼저 고친다(DIRECTION 영역 0·1).

### 1.1 찬성 근거

| # | 근거 | 종류 |
|---|---|---|
| 1 | **수요**: 근거가 가장 많은 기능이 리깅·스킨이다 — Paint Skin Weights 14, Bind Skin 13, Create Joints 11, Constraints 11, IK Handle 10, Graph Editor 11 (FEATURES §9). 이번에 찾은 리깅 강의계획서 9개 **모두** 스키닝을 다루고, 조인트 배치 7/9, 교정 셰이프 5/9 (CHAINS §8) | [사실] |
| 2 | **Blender 쪽 빈자리가 돈으로 보인다**: Superhive 판매 수 Auto-Rig Pro 70,400+, Voxel Heat Diffuse Skinning 13,000+, Faceit 9,800+, Animation Layers 9,700+ — 모델링 상위 BoxCutter 11,500+, HardOps 9,300+ (2026-10-26 페이지 값). 리그 생성·자동 웨이트·애니 레이어가 Blender 사용자도 돈을 내는 빈칸이다 | [사실] 숫자 / [추정] 해석 |
| 3 | **Maya의 상대 강점**: Blender 설문 2025 "다른 DCC에서 온 사용자는 리깅 시스템이 낡았다고 느낌" (https://survey.blender.org), 커뮤니티 "Maya has far more tools and constraints for rigging and animation" (Reddit 스니펫), "Weight painting: pro with Maya, incompetent with Blender"(FEATURES B24) | [사실] (Reddit는 스니펫) |
| 4 | **사용자 본인 경로**: 회사 밖 Blender 작업 = 모델링 → UV → **리깅 → 웨이트 → 디폼**, Maya 경력 모델링 ≈ 애니 (DIRECTION 인터뷰 1·2) | [사실] |
| 5 | **GitHub 반응층에 TA·파이프라인 TD가 많다** (SUMMARY2 / DIRECTION) | [사실, 이전 조사] |
| 6 | **사슬이 길어서 하나만 빠져도 끝까지 못 간다** — 이번에 사슬 5개에서 끊긴 고리 24개를 찾았고(CHAINS §7), 대부분 메뉴는 이미 "동작"이다(리깅 메뉴 86 %, 애니 78 %). 즉 **남은 일은 고리 잇기이고, 고리 하나를 이으면 사슬 전체가 산다** — 같은 비용 대비 가치가 크다 | [사실] 고리 목록 / [추정] 가치 |
| 7 | **세 사슬(조인트·디포머·애니)이 같은 끝(리그 FBX, L11)에서 막힌다** — 한 곳을 풀면 세 사슬이 동시에 끝까지 간다 | [사실: first_hour #39] |

### 1.2 반대 근거

| # | 근거 | 무게 | 대응 |
|---|---|---|---|
| 1 | **Blender 리깅·애니 도구가 이미 충분하다는 시각**: Rigify, Auto-Rig Pro, Blender Studio의 CloudRig·Pose Shape Keys·EasyWeight로 영화를 만든다(https://conference.blender.org/2026/presentations/4204), "Rigify and Auto-Rig Pro are more than capable for indie films, games"(strayspark 블로그) | 중 | 키트는 리그 생성기를 다시 만들지 않는다. 받은 리그 위의 **Maya 손**(L19 쿼터니언, L14 IK/FK)과 Maya식 손작업(컨트롤·SDK·웨이트)만 다룬다 |
| 2 | **개인 작업자는 리깅을 직접 덜 한다**: 인디 가이드는 Mixamo·AccuRIG·Rigify·Auto-Rig Pro를 권함, 애니메이터는 리그를 받아 씀(Animation Mentor) — **본인이 직접 리그하는 비율 숫자는 못 찾음** | 중 | 애니메이터용 고리(L19, L20, L23)를 사슬 ⑤로 같이 넣는다. 비율은 [U] |
| 3 | **리거가 가장 회의적이다**: "terrified at the thought of the amount of things I will need to re-learn"(tech-artists.org), 리거는 스크립트·노드 그래프에 의존 — 키트는 maya.cmds를 216에서 멈춤(사용자 원칙) | 중–상 | 노드 그래프·자동 리그 스크립트는 대상에서 뺀다. 메뉴·창으로 되는 손작업까지만 |
| 4 | **키트(Python)의 한계**: Blender 본은 Y축 고정, 메시별 바인드 행렬 없음(B-dev 문서·devtalk) → L11 FBX는 완전히 못 풀 수도 있음. 키트 GN 디포머(Tension·Jiggle·Wire) **성능 측정이 없음**, "maya can run rigs at 24 fps that would run at 2 fps in blender"(오래된 Reddit 스니펫) | 상 (L11) / [U] (성능) | L11은 「계획」 문서에서 mayapy 왕복으로 먼저 가능 범위를 잰다. GN 디포머 성능은 측정 항목을 만든다 |
| 5 | **Blender가 같은 걸 만들고 있다**: 애니메이션 레이어 "work is expected to start during Q2" 2026, Layered Actions 개발 중 (https://www.blender.org/development/projects-to-look-forward-to-in-2026) | 중 (레이어만) | 레이어는 더 깊게 하지 않는다. SDK·컨트롤·교정 셰이프·Maya식 웨이트는 Blender 일정에 없음(Rig Nodes 등은 "계획만") [사실] |
| 6 | **지금 사용자(모델러) 이탈 위험**: 외부 이슈 6건 중 애니 0, 반응은 모델링 손(#80·#84·#89) | 중 | 영역 0·1 버그는 계속 최우선(DIRECTION). 사슬 작업은 그 다음 순번으로 |
| 7 | 3차 검증(SUMMARY3)에서 "애니가 1위"는 약했다(6가지 계산 중 1위 2번) | 약–중 | 이번 질문은 "애니 단독 1위"가 아니라 "리깅+디폼+애니 묶음"이다. 이 묶음은 FEATURES 근거 수 상위를 차지한다 |

### 1.3 결론

- **맞다, 단 '리깅 사슬 잇기'로.** 수요(근거 수·강의·판매)와 사용자 본인 경로가 같은 쪽을 가리키고, 키트는 메뉴를 이미 갖춰서 남은 비용이 "고리"에 몰려 있다.
- **"애니메이션 특화"의 중심은 키 애니보다 리깅·스킨·엔진 쪽이다** [추정]. 애니메이터 손(Graph Editor 감각)은 사람이 확인해야 하고(수정키 시뮬레이션 불가, step 170), 레이어는 Blender와 겹칠 위험이 있다. 리깅 사슬은 mayapy로 정답을 재고 headless로 검증할 수 있다.
- **확신도 70 %** — 찬성 근거는 여러 독립 묶음(공식·교육·판매·본인 경로)에서 오고, 반대 근거 중 가장 무거운 것(L11 기술 한계)은 순서가 아니라 범위의 문제다.

### 1.4 이 결론이 틀렸다고 알려 줄 신호

| 신호 | 뜻 | 바꿀 것 |
|---|---|---|
| 본인 dogfood에서 S 크기 고리(§4 1단계)를 고친 뒤 사슬 ③을 끝까지 갔는데 막힘 0, 어색함 ≤ 2 | 고리가 생각보다 적다 → 리깅 투자 가치가 작다 | 모델링·UV(영역 1)로 돌아감 |
| L11 「계획」에서 mayapy 왕복이 축·jointOrient를 2 step 안에 못 맞춤 | 사슬의 끝이 안 열린다 | 엔진 끝을 "Blender → 엔진 직접"(Maya 왕복 제외)으로 낮추고, 리깅은 Blender 안에서 끝나는 사슬(①④)만 |
| 리깅 사슬 릴리스 후 4주, 리깅·애니 관련 외부 이슈·토론 0, 모델링 이슈는 계속 | 리깅 사용자층이 키트에 없음 | 리깅은 유지보수만, 영역 1 우선 |
| Blender 5.x가 레이어·리그 노드·본 축 선택을 실제로 출시 | 겹침 | 겹치는 고리는 Blender 기능에 연결만 |
| 키트 GN 디포머가 중간 캐릭터(2만 정점)에서 24 fps 미만 | Python/GN 한계 | 디포머 사슬(④)은 Blender 모디파이어 연결로 낮춤 |
| 설문·투표에서 "Blender에서 직접 리그한다" < 20 % | 직접 리깅 수요 작음 | 사슬 ⑤(받은 리그)를 앞으로 |

---

## 2. NURBS 범위 판정

**필요한 것 = 커브(리그 재료). 필요 없는 것 = 서피스 모델링.** (확신도 80 %)

| NURBS 쓰임 | 애니 특화에 필요? | 근거 | Blender로 되는 정도 | 키트 상태 → 할 일 |
|---|---|---|---|---|
| 커브 그리기 (CV / EP, Circle, Square) | **필요** | 컨트롤 4/9 강의, F 1-20(4) | NURBS·Bezier 커브 오브젝트 [사실] | 동작 → 그대로 |
| 커브 → 컨트롤 모양 (셰이프 교체, 색) | **필요 (1순위)** | 튜토리얼 다수, 강의계획서엔 이름 없음(매일 손작업) | 아무 오브젝트나 본 Custom Shape 가능, Bone Widget 애드온 [사실] | 없음·부분 → L1, L2 |
| Spline IK (꼬리·척추·촉수) | **필요** | 3/9 강의 + C1 촉수 과제 | Spline IK 컨스트레인트, NURBS·Bezier 모두 [사실] | 부분 → L6, L7 |
| CV에 클러스터 / Hook | **필요** | 스파인 리그 튜토리얼 | Hook 모디파이어 (커브 점에도) [사실: Blender 매뉴얼 Hook] | 막힘 → L7 |
| Motion Path | **필요 (중)** | F 4-5(6, A) | Follow Path / Clamp To [사실] | 부분 → L8 |
| Wire | 필요 (중, 얼굴) | 디포머 계열 | Blender엔 없음 → 키트 GN | 동작 |
| Loft → 리본 리그 | **선택 (낮음)** | 1/9 강의, 게임 리그는 리본을 피함(G3) | B-Bones가 Blender식 리본 [사실] | 부분 → L10 (뒤로), 대신 B-Bones 안내 |
| Loft / Revolve → 메시 만들기 | 선택 (낮음) | 모델링 보조 | Curve to Mesh, Convert | 부분 → L10 |
| NURBS 서피스 모델링 일반 (Trim, Stitch, Fillet, Booleans, Birail 2/3) | **필요 없음** | "Subdivision modeling is more often used for movies and video games"(3ds.com), Plasticity 매뉴얼 [사실]; SUMMARY2 점수 6 | Blender 4.5 NURBS에 사용자 knot·트림 없음(step 181) | 회색 유지(안내만) |

**한 줄**: NURBS는 "리그 재료"로만 깊게(커브 → 컨트롤 · Spline IK · CV 클러스터 · Motion Path), 서피스는 멈춘다.

---

## 3. 설계 선택 하나 (사슬 ①을 시작하기 전에 정할 것) [delegated 권장]

Maya 컨트롤 = **커브 오브젝트**가 컨스트레인트로 조인트를 움직인다. Blender의 관례 = **같은 아마추어 안의 컨트롤 본 + Custom Shape**(Rigify, Auto-Rig Pro).

| 안 | Maya 손 | FBX·엔진 | 성능 | 받은 리그와 |
|---|---|---|---|---|
| A. 커브 오브젝트 컨트롤 (Maya 그대로) | 가장 같음 (Outliner의 오프셋 그룹, 컨트롤 = 트랜스폼) | Bake 필요 (L18 먼저) | 오브젝트 ↔ 본 의존 = 느릴 수 있음 [추정] | 다름 |
| B. 본 + Custom Shape (Blender 관례) | 다름 (포즈 모드 안의 선택) | 깔끔 (컨트롤 본 = deform off) | 좋음 | 같음 |
| **C. 만들 때는 A의 손, 결과는 B (권장)** | Maya 메뉴·순서로 만들고("커브를 이 조인트의 컨트롤로"), 결과는 컨트롤 본 + 커브 모양 | B와 같음 | B와 같음 | 같음 → 사슬 ⑤와 하나로 |

**권장 C** [delegated, 확신도 55 %]: Maya 사용자는 "커브를 컨트롤로 만든다"는 **행동**을 원하지, 커브 오브젝트라는 **자료 구조**를 원하는 게 아니다 [추정]. 단, Outliner에 컨트롤이 트랜스폼으로 보이지 않는 차이는 키트 Outliner 행으로 보완할지 따로 정한다. 틀렸다는 신호: 본인 dogfood에서 "오프셋 그룹을 Outliner에서 못 찾는다"가 막힘으로 나옴 → A로.

---

## 4. 구현 순서 (사슬 단위)

### 4.1 사슬 우선순위 [delegated 계산]

점수 = 빈도(1–5) × 끊긴 고리 수 ÷ 비용(S=1, M=3, L=8 합) × 10. 빈도 = 그 사슬 단계들의 FEATURES 등급·강의 수를 묶은 값.

| 사슬 | 빈도 | 끊긴 고리 | 비용 | 점수 | 순서 |
|---|---|---|---|---|---|
| ③ 조인트 → 스킨 → 엔진 | 5 (스키닝 9/9, Paint 14, Bind 13) | 6: L13 S, L18 S, L3 S, L14 M, L12 M, L11 L | 3+6+8 = 17 | 17.6 | **1** |
| ⑤ 애니 → 엔진 (받은 리그) | 4 (Graph 11, Set Key 6, Auto-Rig Pro 판매) | 6: L20 S, L24 S(+M), L19 M, L23 M, L21 M, (L11 공유) | 2+9+… ≈ 14 | 17.1 | **2** |
| ① 커브 → 컨트롤 | 4 (Constraints 11, SDK 6, 컨트롤 4/9) | 5: L3 S(공유), L2 S, L1 M, L4 M, L5 M | 2+9 = 11 | 18.2 | **3** (점수는 1위지만 설계 선택 §3을 먼저 정해야 해서) |
| ④ 디포머 → 교정 | 3 (Blend Shape 7, 교정 5/9) | 5: L15b S, L17 S, L15 M, L16 M, (L5 공유) | 2+6 = 8 | 18.8 | **4** (L5가 사슬 ①에서 풀린 뒤라야 의미) |
| ② 커브 기반 (Spline IK·Path·Loft) | 2 (Spline IK 3/9, Motion Path 6) | 5: L6 S, L7 S, L8 M, L9 M, L10 M | 2+9 = 11 | 9.1 | **5** (S 두 개는 1단계로 당김) |

의존 관계가 점수보다 앞선다: L5(SDK 대상)는 ①·④·③(IK/FK)에 공통, L11(FBX)은 ③·④·⑤의 끝.

### 4.2 단계별 순서

| 단계 | 묶음 | 고리 | 크기 | 끝났다의 정의 |
|---|---|---|---|---|
| **0** | 늘 먼저 | 외부 보고된 모델링 손 버그 (#80·#84·#89 계열) | — | DIRECTION 그대로 |
| **1** | S 묶음 (한 step) | L18 Bake 옵션(정확성), L13 Paint Skin Weights Q·B, L3 Match → 조인트, L6 Spline IK 기존 커브, L7 커브 CV 클러스터, L20 pick walk 숨은 본, L15b 셰이프 가중치 키, L24 레이어 → FBX 확인 테스트 | S×8 | 각 고리에 "앞 단계 결과 → 다음 단계" headless 테스트 1개 |
| **2** | 사슬 ③ 끝 열기 | L11 리그 FBX (「계획」 먼저, mayapy 왕복), L12 스킨 FBX 가져오기, L14 IK/FK | L + M + M | 기준 캐릭터: 조인트 → … → FBX → Maya에서 jointOrient·위치 일치, 엔진 가져오기 기록 |
| **3** | 사슬 ⑤ 받은 리그 | L19 쿼터니언 본 채널·키, L23 Translate Y, L24 Game Exporter 클립(TOP40 #24–25) | M×3 | Rigify 휴먼: 컨트롤 선택 → S(회전 포함) → Graph Editor → 레이어 → FBX 클립 |
| **4** | 사슬 ① 컨트롤 | §3 결정 → L1 컨트롤 모양, L2 색, L4 컨트롤+조인트 선택, L5 SDK 대상 확장 | M×3 + S | 커브 → 컨트롤 → 오프셋 → 컨스트레인트 → SDK → 잠금 → 키, 한 번도 Blender 키로 빠지지 않음 |
| **5** | 사슬 ④ 교정 | L17 디포머 순서, L15 인비트윈·조합, L16 조인트 회전 → 교정 셰이프 창, GN 디포머 성능 측정 | S + M×2 | 팔꿈치 교정 셰이프가 SDK로 구동, FBX 모프로 나감 |
| **6** | 사슬 ② 나머지 | L8 Motion Path 옵션, L21 본 모션 트레일, L10 Loft 폴리곤 / 리본(또는 B-Bones 안내), L9 Flow Path | M×3–4 | 낮은 순위 — 수요 신호가 나오면 |

TOP40과의 관계: TOP40 #10·#11(L13), #13(L15b), #15(L14), #19(L11), #23(L12), #3(L23), #24–25(L24)는 그대로 쓰고, 이번에 **새로 찾은 고리**는 L1–L8, L15–L21이다(특히 L18 Bake 버그, L19 쿼터니언, L7 커브 클러스터, L5 SDK 대상).

### 4.3 측정 (DIRECTION "에셋 하나 끝까지"에 사슬을 끼움)
- dogfood 시나리오 3개를 추가한다: **사슬 ③**(캐릭터, V7), **사슬 ①**(커브 컨트롤로 팔 리그), **사슬 ⑤**(Rigify 휴먼 받은 리그, V9). 지표 = 고리마다 BLOCKED / AWKWARD / Blender 키로 빠져나간 횟수.
- 고리 하나를 고칠 때마다 "앞 단계 출력을 다음 단계 입력으로 넣는" headless 테스트를 붙인다 — 지금 테스트는 대부분 고리 하나만 따로 본다(예: Constrain 테스트가 커브 대신 Empty, Cluster 테스트가 큐브만) [사실: CHAINS §1·§2].

---

## 5. 모르는 것 [U]
1. 키트 관심층 중 Blender에서 **직접 리그**하는 비율 (숫자 못 찾음).
2. 리깅·애니 채용 공고에서 Maya 대 Blender 비율 (정성 근거만: "job posting very often says Maya").
3. 키트 GN 디포머·오브젝트 컨트롤 리그의 재생 성능.
4. L11을 Python에서 어디까지 맞출 수 있는지 (Blender 본 축·바인드 행렬 한계).
5. Blender Layered Actions 출시 시점과 키트 레이어 구현과의 충돌 정도.
