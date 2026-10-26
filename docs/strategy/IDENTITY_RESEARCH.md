# IDENTITY_RESEARCH — 영역별 수요 근거, 인용, 출처 (2026-10-26)

`IDENTITY.md`의 근거 자료. 표기: **[사실]** 출처에서 직접 확인 · **[추정]** 해석 · **[재인용]** 1차 `RESEARCH.md`에서 가져옴(다시 열어 보지 않음). 날짜를 확인하지 못한 글은 "날짜 미확인"으로 적었다.
수집: tavily search/extract, yt-dlp(유튜브 검색 결과의 조회수), Discourse 검색 API(BlenderArtists), Blender 공식 설문 원자료 JSON, CGWORLD JOBS 페이지. 원자료와 스크립트는 `data/`에 있다.

| 원자료 | 파일 | 스크립트 |
|---|---|---|
| 유튜브 이주 주제 34개 쿼리 × 상위 30 | `data/yt/yt_demand.json` | `data/scripts/yt_demand.py`, `yt_classify.py` |
| 유튜브 Maya 기능별 튜토리얼 19개 쿼리 × 상위 30 | `data/yt/yt_features.json` | `data/scripts/yt_features.py` |
| BlenderArtists 제목 "maya"+영역어 스레드 | `data/web/ba_threads.json` | `data/scripts/ba_threads.py` |
| Blender Survey 2025 원자료 | `data/web/multi__*.json` | (https://survey.blender.org/static/survey/feedback-2025/…) |
| CGWORLD JOBS 목록(2026-10-26 스냅숏) | `data/web/cgw_jobs.html` | `data/scripts/cgw_jobs_count.py` |
| 합성 수요 지수 | — | `data/scripts/demand_index.py` |

한계: Reddit은 API 403으로 개수를 못 셌다(검색 스니펫 인용만). Indeed 공고 수는 차단. 중국 플랫폼(bilibili·知乎 본문)은 거의 잡히지 않았다. 유튜브 조회수는 바이럴 영상 몇 개에 크게 흔들린다.

---

## 0. 숫자 대리 지표 [사실, 집계 방법은 위 스크립트]

### 0.1 Blender Survey 2025 — Blender 사용자가 하는 일 (복수 응답, 응답자 수)
출처: https://survey.blender.org (원자료 `multi__what_do_you_do.json`)

| 작업 | 수 | | 작업 | 수 |
|---|---|---|---|---|
| Modeling | 3,865 | | Environment Art | 1,903 |
| 3D Animation | **3,837** | | Motion Graphics | 1,273 |
| Generalist | 2,597 | | Simulation (FX) | 1,254 |
| Lighting | 2,297 | | Technical Art | 900 |
| Texturing | 2,209 | | Look Development | 861 |
| Sculpting | 2,032 | | Add-ons Development | 648 |
| Rigging | 1,972 | | Pipeline | 426 |

- "Blender가 집중해야 할 영역"(최대 3개): **Animation 1,351 (1위)**, Cycles 1,265, Modeling 1,151, Texture Painting 1,118, Physics 1,102, Geometry Nodes 1,096 … Rigging 508, UV Editing 451, Pipeline and I/O 298, Python API 185.
- "집중할 프로젝트": Texturing Tools 1,924, **Animation & Rigging 1,520 (2위)** … USD 720, **NURBS modeling tools 629**.
- 설문 요약문 원문: "Rigging & Animation: Users coming from other DCCs feel the rigging system is outdated, specifically the NLA editor and the lack of a robust pose library or animation layers (though they acknowledge improvements are coming)."
- Blender 전에 처음 쓴 3D 앱(상위 10): 3ds Max 670, **Maya 329**, Cinema 4D 321.

[추정] Blender 안에서도 애니메이션은 모델링과 같은 크기의 작업이고, 사용자들이 "가장 부족하다"고 꼽는 영역이다. 다른 DCC에서 온 사람이 레이어·NLA를 낡았다고 느낀다는 문장은 Maya 출신을 직접 가리킨다.

### 0.2 일본 — 직군 비율과 채용
- CGWORLD 독자 조사(3DCG 디자이너 본인 직군): **제너럴리스트 44 %, 모델러 33 %, 애니메이터·모션 디자이너 18 %, 이펙트 5 %** — CGWORLD 편집장 누마쿠라 인터뷰, https://mynavi-creator.jp/blog/article/interview-with-arihito-numakura (날짜 미확인) [사실]
- CGWORLD JOBS 목록(2026-10-26 스냅숏, 115개 회사 블록, 회사가 모집하는 직종에 그 직군이 있는 회사 수): **애니메이터/모션 65**, 모델러 44, 이펙트/FX 41, TA/TD/파이프라인 37, 컴포지트 28, 제너럴리스트 24, 리그 20, 라이팅/룩 6 [사실; "모션"이 모션그래픽을 일부 포함할 수 있음 — 추정 오차]
- 일본 애니 CG 툴: 도에이 애니메이션 = Pencil+4 for Maya(https://cgworld.jp/feature/202002-atsuc2019-03.html), 폴리곤 픽처스 = Maya 리그·애니 프레임워크 eST3 연재(2026-10-01, https://cgworld.jp/special/animationdays2026 검색 스니펫), 오렌지·산지겐 = 3ds Max 계열(산지겐은 2023년 Max → Blender [재인용 B3]). 셀룩 CG가 Max에 몰린 이유: "pencil＋…5年前まで3dsmax向けにしか販売されていませんでした"(https://detail.chiebukuro.yahoo.co.jp/qa/question_detail/q13286969178, 날짜 미확인) [사실: 인용, 해석은 추정]
- 일본 회사 메인 툴 Maya 58 %, 사용 툴 Maya 269 / Blender 222 / Max 206사 [재인용 B1·B2]

### 0.3 유튜브 — Maya→Blender 이주 영상 (제목에 Maya와 Blender가 모두 있는 영상, 중복 제거, 제목 키워드로 분류)
34개 쿼리 × 상위 30. `yt_classify.py`의 분류 순서(애니→리그→UV→렌더→FX→파이프→스크립트→모델→손)라서, "How to Render Maya Animations in Blender"(33.9만)처럼 두 주제에 걸친 영상은 애니메이션으로 셌다.

| 주제 | 영상 수 | 조회 합 | 대표 영상 (조회) |
|---|---|---|---|
| (일반 비교·첫인상) | 82 | 3,977,426 | "Should I learn Blender 3D or Maya?" 1,015,635 · "Maya Artist Tries Blender for the First Time!" 974,723 |
| **애니메이션** | **39** | **1,595,784** | "ATTEMPTING 3D Animation in Blender! Maya Artist's First Time" 355,038 · Sir Wade "First Impressions Blender vs Maya - Animation Workflows!" 215,197 |
| 손(내비게이션·키맵) | 24 | 178,966 | "Switching From Maya to Blender 2.8 - Maya Navigation Config Simple" 38,872 |
| 파일·파이프라인 | 16 | 144,514 | "Export Models Correctly from Blender to Maya" 24,651 |
| 리깅 | 8 | 118,266 | "BlenderからMayaへのリギング：Quick Rigの使い方" 35,498 · "Maya rig in Blender? See for yourself" 32,444 |
| 모델링 | 6 | 235,397 | "Maya Pro Tries 3D Modeling in Blender" 216,368 |
| 렌더 | 6 | 81,341 | "Blender 2.83 CYCLES vs Maya 2020.2 ARNOLD – Speed 400%" 60,663 |
| UV | 5 | 34,422 | BlenderBub "I am now more efficient doing UVs in Blender than in Maya!" 17,010 |
| 스크립팅 | 4 | 12,087 | "Blender 2.8 Python Addons vs Maya Mel-Script" 10,272 |
| FX | 3 | 71,559 | (Houdini 천 시뮬을 둘 다로 내보내기 51,653) |

- **MASH**: "MASH Blender equivalent" 상위 30 중 관련 영상 2편, 합 3,050 조회; "Maya MASH vs Blender geometry nodes" 2편, 3,374 조회 (첫 실행에서는 "mashed potatoes" 영상이 섞여 들어와 키워드에서 뺐다).
- 지역어: "Maya Blender アニメーション 移行" 11편 166,858 · "Maya Blender モデリング 移行" 11편 210,694 · "Maya Blender リギング" 5편 194,182 · "Maya用户 Blender 动画" 6편 384,089 · "Maya 转 Blender" 9편 2,325.

### 0.4 BlenderArtists — 제목에 "maya"와 영역어가 함께 있는 스레드 (전 기간, 영역별 중복 제거)
파이프라인(fbx/export/import/alembic/usd) **114** · 리깅 53 · 애니메이션 43 · 손(navigation/hotkeys/keymap) 37 · 렌더 28 · FX 23 · 모델링 22 · 스크립팅 14 · UV 8. (전체 283개 중 "fbx" 16, "uv" 8, "weight" 8, "mash" 0, "humanik" 0, "quad draw" 0)
[추정] 이주자가 "도와 달라"고 글을 쓰는 곳은 파일 왕복이 압도적이다. 모델링·UV는 질문이 적다 — 잘 되거나, Blender 방식으로 쉽게 넘어간다.

### 0.5 Maya 사용자 쪽 관심 — "Maya <기능> tutorial" 상위 30 조회 합 (Maya 학습 인구의 대리 지표)
폴리 모델링 5,830,020 · UV 1,756,779 · 리깅 1,667,996 · Arnold 라이팅 1,443,429 · XGen 1,354,615 · Quad Draw/리토폴 1,233,611 · nCloth 935,523 · 스킨 웨이트 905,233 · FBX 게임 내보내기 857,144 · **MASH 651,047** · 리그 컨트롤 커브 649,377 · Bifrost 563,930 · Python 561,948 · Graph Editor 398,138 · 애니 레이어 395,567 · HumanIK/모캡 368,330 · Playblast 354,731 · Time Editor 332,881 · **NURBS 모델링 305,644**.
[추정] 이 숫자는 "Maya를 배우는 사람"(학생 다수)의 관심이다. 모델링 튜토리얼이 압도적인 것은 입문자가 많아서이고, 애니메이터는 숫자가 작지만 유료 강좌로 배운다. **이주 수요와는 다르다** — MASH는 Maya 학습자 관심(65만)은 있지만 Blender로 옮기려는 사람의 영상은 거의 없다(3천).

### 0.6 합성 수요 지수 (`data/scripts/demand_index.py`, 각 지표 최댓값 = 100, 있는 지표의 평균) [추정: 방법이 거칠다]

| 영역 | S1 Blender 설문 | S2 일본 채용 | S3 유튜브 이주 영상 수 | S4 BA 스레드 | S5 Maya 학습 조회 | **지수** | 이주 신호만(S3·S4) |
|---|---|---|---|---|---|---|---|
| ① 손 | – | – | 62 | 32 | – | 47 | 47 |
| ② 모델링 | 100 | 68 | 15 | 19 | 100 | 60 | 17 |
| ③ UV | 57* | – | 13 | 7 | 25 | 25 | 10 |
| ④ 렌더 | 59 | 9 | 15 | 25 | 20 | 26 | 20 |
| ⑤ 리깅 | 51 | 31 | 21 | 46 | 46 | 39 | 34 |
| ⑥ 애니메이션 | 99 | 100 | 100 | 38 | 26 | **73** | **69** |
| ⑦ FX | 65 | 63 | 8 | 20 | 50 | 41 | 14 |
| ⑧ 파일·파이프라인 | 11 | – | 41 | 100 | 12 | 41 | **71** |
| ⑨ 스크립팅 | 17 | 57** | 10 | 12 | 8 | 21 | 11 |

\* Texturing으로 대신함 · \*\* TA/TD 모집을 스크립팅으로 셈(과대). ① 손은 모든 직군이 쓰므로 인구 지표를 넣지 않았다.

---

## ① 뷰포트 조작·선택 (손)

| 언어·날짜 | 출처 | 원문 |
|---|---|---|
| EN, 2026-10-23 | [BlenderArtists 키트 시험기](https://blenderartists.org/t/maya-workflow-tool-for-blender/1655759) [재인용] | "if you press D to change the pivot like Maya, you won't be able to do it"; 숫자패드 1/3 안 됨 |
| EN, 날짜 미확인(2024 추정) | [BA "REACTING to 'Maya Animator Tries Blender'"](https://blenderartists.org/t/reacting-to-maya-animator-tries-blender/1515997) | "Most Blender tutorials are done exclusively with hotkeys … And the same hotkeys do different things in different modes. Maya users have to start over from scratch to a very large extent when going to Blender." |
| JA, 날짜 미확인 | [note gorouya「MayaユーザーがBlenderを使う⑤」](https://note.com/famous_oxalis656/n/nfda3334b57bd) | 「カメラ操作はMaya風にする」「マニピュレーターが初期設定だと非表示」「グループ化したときの挙動がMayaとBlenderで異なり、私は最初かなり混乱しました」 |
| JA | [Zenn hota](https://zenn.dev/hota12/articles/5428eafc52dd6e) | 「Mayaよりも今のモードが何になっているか意識しながら使う印象です」 |
| EN, 영상 | "How To Change Blender Navigation To Be Like Maya" 32,757 조회 · "Switching From Maya to Blender 2.8 - Maya Navigation Config Simple" 38,872 | (유튜브 이주 영상 24편이 이 주제) |

Blender가 더 낫다고 말하는 것: 모드가 있어서 다른 캐릭터를 실수로 키 찍지 않는다 — "because it has no modes … you won't accidentally animate other objects or controllers on other characters when you drag select something which is an issue I've had on Productions in Maya" ([유튜브 REACTING](https://www.youtube.com/watch?v=Fu1dJEG-Gak)).

## ② 폴리 모델링

| 언어·날짜 | 출처 | 원문 |
|---|---|---|
| EN, 2021 추정 | [tech-artists.org "Moving a pipeline from Maya to Blender"](https://www.tech-artists.org/t/moving-a-pipeline-from-maya-to-blender/14490) | "modelling departments transitioning to Blender and that part so far seems to be very smooth." |
| EN, 2020 추정 | [BA "Is there anything … you wish was the same as Maya?"](https://blenderartists.org/t/is-there-anything-that-you-use-blender-that-you-wish-was-the-same-as-maya/1252150) | "Polyquilt addon is actually better than Maya Quad Draw, imo. QD is good, but Maya's modeling UX is so painful that it's just not worth it. … Going back to Maya to model … feels so outdated now" |
| JA | [Zenn hota](https://zenn.dev/hota12/articles/5428eafc52dd6e) | 「基本的な機能に関してはMayaとそこまで大差はないように感じました。ただblenderの方が機能にアクセスしやすく分かりやすい印象です」 |
| EN, 2026-10-23 | BA 키트 시험기 [재인용] | "Not everything works like Maya, like Quaddraw (Multicut does)" |
| EN, 2026-10 | 키트 외부 이슈 #80 "After extruding the faces, I can't move them as usual.", #84 "Double click select edge loop error" | (외부 사용자 이슈 6건 중 2건이 모델링 손) |
| JA, 날짜 미확인 | [filament「Blender→MAYA移行で戸惑ったこと」](https://flmt.jp/press/3629) | 역방향(Blender→Maya) 글이지만 회사 현장 증언: 「MAYAの操作感を基準にされている事が多い…Maya Config Addon…を利用して覚えた方が良いかもしれません」 |

Blender가 더 낫다고 말하는 것: 모디파이어·비파괴(gorouya: Armature 모디파이어 「ボーンとメッシュを関連付けた後でも、いつでもメッシュの形状を変えたり」), 스컬프트, Geometry Nodes. Poliigon 2024 설문 요약: "Users also marked modeling as Blender's strongest feature, and simulations as the weakest" ([Springer 논문 인용](https://link.springer.com/article/10.1007/s00371-025-04281-1)).

## ③ UV

| 언어·날짜 | 출처 | 원문 |
|---|---|---|
| JA | [note gorouya](https://note.com/famous_oxalis656/n/nfda3334b57bd) | 「UV展開に関しては、Mayaの方がやりやすいと思いました…BlenderのUV展開は少し弱くアドオンがないとちょっと使いずらい」(애드온 3개 사용) |
| EN, 영상 | [BlenderBub](https://www.youtube.com/watch?v=4t7OGePY-i8) 17,010 조회 | "how much I hated doing UVs in Blender … the cut and sew UV tool. It's absolutely amazing" / "I was only using Maya for unfolding UVs" |
| EN, 2021-07 | [Blender StackExchange 230192](https://blender.stackexchange.com/questions/230192/how-can-i-improve-uv-unwrapping-in-blender) | "the recently added unwrapping algorithm in Maya also takes the topology and even the face positions into account which the Blender one does not" |
| EN | r/3Dmodeling 스니펫 [재인용] | "[Maya] UV and retopology tools are much better" |

[추정] Maya 쪽 UV가 낫다는 데 비교적 합의가 있다. 다만 이주 질문 수는 가장 적다(BA 8, 유튜브 5편) — 애드온으로 해결하고 넘어가는 영역.

## ④ 머티리얼·라이팅·렌더

| 언어·날짜 | 출처 | 원문 |
|---|---|---|
| EN | [Flow 인터뷰](https://www.blender.org/user-stories/making-flow-an-interview-with-director-gints-zilbalodis) [재인용] | 전환 이유 "mainly because of EEVEE" |
| JA, 2026-04 | [CGWORLD 산지겐 ACTF2026](https://cgworld.jp/article/202604-actf-sanzigen.html) [재인용] | 「Eeveeは非常に軽快で、3Dビューポート上で確認しながらリアルタイムに作業」 |
| EN | [Ynput](https://community.ynput.io/t/blender-look-workflow/2453) [재인용] | "We lock AYON's blender host to 0.01 scale (otherwise light values, clipping planes are really troublesome)" |
| EN, 2023-03 / 2023-11 | BA 스레드 제목 | "Does Blender have a C4D like Take System / Maya like Render Setup?" · "Viewlayers Renderlayers - Maya to Blender" |
| EN, 영상 | "Blender 2.83 CYCLES vs Maya 2020.2 ARNOLD (4K) – Speed 400%" 60,663 조회 | |

[추정] 렌더는 Blender로 오는 이유이고, 손 습관보다 개념(렌더 레이어, 라이트 단위, Arnold 노드 이름)이 걸린다.

## ⑤ 리깅 (조인트·스킨·컨스트레인트·컨트롤)

| 언어·날짜 | 출처 | 원문 |
|---|---|---|
| EN, 2019 추정 | [devtalk "RIGGING - more work needs to be done"](https://devtalk.blender.org/t/rigging-more-work-needs-to-be-done/9622) | "The worst experience in blender rigging is weight painting." / 반대로 "The bendy bone is super nice … it is just one bone, single weight painting!" |
| EN, 날짜 미확인 | [r/Maya "Blender rigging vs Maya rigging"](https://www.reddit.com/r/Maya/comments/171hq8b/blender_rigging_vs_maya_rigging) (스니펫) | "Blender's attempt to simplify things with constraints can actually become a hindrance for more complex rigs." |
| EN, 2020 추정 | [BA 1252150](https://blenderartists.org/t/is-there-anything-that-you-use-blender-that-you-wish-was-the-same-as-maya/1252150) | "Parallel Rig evaluation. GPU accelerated deformers. … Maya is up to 8x faster with rigs and animations on my machine than Blender is, which makes the latter unusable for me (when it comes to character animation)." |
| JA | [Zenn hota](https://zenn.dev/hota12/articles/5428eafc52dd6e) | 「リギング：個人的にかなりmayaとの違いを感じる部分でした…blenderでは骨をコントローラーにするのが一般的なのか」 |
| JA, 날짜 미확인 | [note 大和司](https://note.com/tsukasa_yamato/n/nefaab8b89468) | 「Blenderのボーン、何となく扱いにくいと感じなかったか？」「ボーンのロール軸問題。外部に持っていった時にBlenderのY軸ロールはトラブルの元の可能性が非常に高い」 |

[추정] 리깅의 벽은 손보다 **개념**(조인트 ↔ 본의 길이·롤, 커브 컨트롤 ↔ 본 커스텀 셰이프)과 **성능**(병렬 평가·GPU 디포머, C++ 영역)이다.

## ⑥ 키프레임 애니메이션

| 언어·날짜 | 출처 | 원문 |
|---|---|---|
| EN, 날짜 미확인 | [BA "I need help with Blenders graph editor"](https://blenderartists.org/t/i-need-help-with-blenders-graph-editor/1589561) | "I've been a long time animator in maya and max … I can select one, then shift select the other but moving them seems to deselect them. Also, I have just the x euler rotation channel selected on the left but all the other channels keys are ghosted and selectable … I love blender but I'm getting a sense that it isn't really meant to be used for animation" |
| EN, 2025-06 | [Brian Kouhi, BlenderNation 소개](https://www.blendernation.com/2025/06/10/youre-using-blenders-graph-editor-wrong) / [영상](https://www.youtube.com/watch?v=vKgO3NsYORo) | "one big thing with Blender's graph editor that … really pisses people off is that right away you see … all the curves and every single channel, even if they're not selected" |
| EN, 영상 | [REACTING to 'Maya Animator Tries Blender'](https://www.youtube.com/watch?v=Fu1dJEG-Gak) (원 영상 인용) | "in Maya when I select these not only does it highlight them in the graph editor it hides everything else" / Ctrl+MMB 세로 확대에서 커브가 움직임 |
| JA, 날짜 미확인 | [BIGFOOT「ゴリゴリのMayaアニメーターのおれがblenderを使用する際やったことメモ」](https://www.bigfootinc.jp/blog/mayatoblender) (검색 스니펫; 본문 페이지는 2026-10-26 현재 오류) | 「グラフエディタでキーを選んで動かすときにイチイチXかY押してからじゃないと一軸で動かない。Maya みたく shift +MMDで出来ないか？」 |
| JA, 날짜 미확인 | [note 大和司](https://note.com/tsukasa_yamato/n/nefaab8b89468) | 「Blenderでのキーフレーム操作、ちょっと触っただけでも「使いにくくね？」と思ってしまった」「タイムシート？ドープシート？何だかよく分からん」 |
| EN, 2025 | Blender Survey 2025 요약 (0.1) | "the NLA editor and the lack of a robust pose library or animation layers" |
| EN, 영상 215k | Sir Wade [재인용] | Graph Editor 차이가 "drive me crazy", 대신 F-Curve Noise는 "would take so much longer in Maya" |

반대 방향 증언(Blender가 더 낫다): 「僕はMayaのグラフエディタが使いづらかった」([X @POPREQ](https://x.com/POPREQ/status/1309208669645545477), 2020); Brian Kouhi: Blender는 Ctrl+C/V로 키 복사가 쉽다.

[추정] 애니메이션은 **이주 이야기의 양(유튜브 1위)**, **Blender 사용자 자신의 불만(설문 1위)**, **Maya에 남는 이유("Maya is better for animation")** 세 가지가 겹치는 유일한 영역이다. 불만의 내용은 대부분 Graph Editor·키 선택의 손 감각과 레이어/NLA 개념이다 — 메뉴 개수 문제가 아니다.

### ⑥-a 일본 애니메이터 수요는 실제로 높은가 (사용자 가설 검증)

| 신호 | 값 | 판정 |
|---|---|---|
| 일본 채용: 애니메이터 모집 회사 | 65/115 (1위) | 업계 **채용 수요**는 높다 [사실] |
| 일본 3DCG 디자이너 본인 직군 | 애니메이터·모션 18 % vs 모델러 33 % | **인구**는 모델러가 더 많다 [사실] |
| 일본 애니 CG의 Blender 이전 | 카라·산지겐·MAPPA = 3ds Max 출신 | Maya 애니메이터의 이전 사례 아님 [재인용 B3] |
| 일본 Maya 애니 스튜디오 | 도에이(Maya), 폴리곤 픽처스(Maya, 자체 리그 프레임워크) | 회사 단위로는 Maya에 머묾 [사실] |
| 일본어 이주 영상 | 애니 11편 16.7만 · 모델링 11편 21.1만 · 리깅 5편 19.4만 | 애니가 특별히 크지 않다 [사실] |
| 키트에 대한 일본어 반응(X 10건, 매체 4곳) | 애니메이션 언급 0 (외형·스위치 감탄) | [재인용 A2·A3] |

**결론 [추정]**: "일본 애니메이터 수요가 높다"는 **업계 채용 수요로는 맞지만, Maya→Blender 이주 수요로는 확인되지 않는다.** 일본 애니메이터는 회사에서 Maya(또는 Max)를 계속 쓰고, Blender는 개인 쪽(P2)일 가능성이 크다. 애니메이션을 앞에 두는 근거는 일본이 아니라 **전 세계 공통 신호**(0.1, 0.3)다. 일본에서 애니메이터를 따로 겨냥할지는 설문 Q1×언어로 확인한다(GOALS 영어만 원칙과도 맞음).

## ⑦ FX·시뮬레이션 (MASH 포함)

| 언어·날짜 | 출처 | 원문 |
|---|---|---|
| EN, 2020 추정 | [BA 1252150](https://blenderartists.org/t/is-there-anything-that-you-use-blender-that-you-wish-was-the-same-as-maya/1252150) | "For me, the no. 1 wish is Xgen. Blender's hair tools are really terrible." / "it reminded me of Mash, and I want Mash too." |
| EN | [r/Maya 10douy3](https://www.reddit.com/r/Maya/comments/10douy3/does_maya_have_similar_features_to_blender_for) (스니펫) | "yes, Bifrost would be the equivalent of geometry nodes" |
| EN, 2024 | Poliigon 설문(Springer 논문 인용) | "simulations as the weakest" (Blender 사용자 평가) |
| 숫자 | 유튜브 "MASH Blender equivalent" | 관련 2편, 3,050 조회 · BA "maya"+"mash" 제목 0건 |

[추정] FX 이주자는 Maya FX를 Blender로 옮기기보다 Houdini로 간다(BA FX 스레드 상위는 Houdini 경유). MASH는 Maya 학습자 관심(65만 조회)에 비해 **Blender로 옮기려는 사람의 신호가 거의 0**이다.

## ⑧ 씬 관리·파일 입출력·파이프라인

| 언어·날짜 | 출처 | 원문 |
|---|---|---|
| EN, 2026-10 | X @thechriss2004ss (키트 반응 답글) [재인용] | "I was hoping for a add on that allow you to import Maya rig model to blender or blender rig model into Maya without breaking the rig ctrl" |
| EN, 날짜 미확인 | [r/Maya raya77 "Blender to Maya bone rotations problem"](https://www.reddit.com/r/Maya/comments/raya77/blender_to_maya_bone_rotations_problem) (스니펫) | "In blender up axis is Z while in maya it is Y … but the main issue is always will be your control rig" |
| EN, 2021-12 | [BA 1343332](https://blenderartists.org/t/something-is-wrong-with-rigs-exported-to-maya-from-blender/1343332) | "When I export fbx ( rig and outfit) to maya , rigs are not at their right place." |
| EN, 2023-01 | [Autodesk 포럼](https://forums.autodesk.com/t5/maya-animation-and-rigging-forum/bones-change-shape-when-i-transfer-armature-from-blender-to-maya/td-p/11687081) | "When I export it as an FBX from Blender and import it into Maya, most of the bones radically change shape" |
| EN | [Better FBX 설명](https://superhivemarket.com/products/better-fbx-importer--exporter) | Maya IK는 "copy the rotation value to the 'Pre-rotation' value for every bone between the IK chains" 해야 함 — 축 문제가 스케일보다 깊다 |
| EN, 2021 추정 | [tech-artists.org 14490](https://www.tech-artists.org/t/moving-a-pipeline-from-maya-to-blender/14490) | "You need to get your hands dirty with all the pipeline including animation caching, control rig retargetting ond even FBX exporting" |
| JA | [note 大和司](https://note.com/tsukasa_yamato/n/nefaab8b89468) | 「外にアニメーションを出すときにはFBX一択」 |
| 키트 측정 | `docs/first_hour.md:82,84` | BLOCKED 2개 모두 리그 FBX 왕복 |

Collections ≠ Groups 혼란 [재인용 C], 단위 100배 [재인용 C].

## ⑨ 스크립팅·커스터마이즈

| 언어·날짜 | 출처 | 원문 |
|---|---|---|
| EN, 2021 추정 | [tech-artists.org 14490](https://www.tech-artists.org/t/moving-a-pipeline-from-maya-to-blender/14490) | "I'm amazed about it's Python API and documentation. It's much more pythonic and intuitive than anything Maya can offer. What I miss is Qt" |
| EN, 날짜 미확인 | [r/Maya 1gcwjvb](https://www.reddit.com/r/Maya/comments/1gcwjvb/what_features_that_only_exist_in_maya_and_not_in) (스니펫) | "It is easier to script custom tools/actions in Maya and you can easily add them to shelves" |
| EN, 2020 추정 | BA 1252150 | "the ability to quickly and easily create editable custom buttons of actions." |
| 숫자 | 유튜브 이주 스크립팅 영상 4편 1.2만 · BA 14건 | 가장 작은 영역 |

[추정] TA는 Blender Python을 오히려 좋아한다. 아쉬운 것은 "버튼 하나로 만드는 셸프"다 — 키트 셸프(step 109·162·167)가 이미 그 자리.

---

## 지역별 차이 요약 [추정]

| 지역 | 도달·반응 | 수요 신호 | 의미 |
|---|---|---|---|
| 일본 | 키트 도달의 87 % (외형 감탄) | 직군 인구 모델러 > 애니메이터, 채용은 애니메이터 1위, 애니 CG 이전은 Max 출신 | 일본 = "모델러·제너럴리스트가 많은 도달 시장". 애니메이터 집중의 근거로는 약함 |
| 영어권 | X 반응 13 %, BA 시험기, 외부 이슈 대부분 | 유튜브 이주 애니 영상 최다, BA는 파이프라인·리깅 | 애니메이터·파이프라인 수요는 영어권에서 가장 뚜렷 |
| 중화권 | GitHub 스타·포크 다수(TA·Pipeline TD) [재인용 A4] | 검색 불가 영역 많음; "Maya用户 Blender 动画" 38만(1편이 대부분) | 도구를 뜯어보는 TA층 — ⑤⑧⑨에 민감 |
