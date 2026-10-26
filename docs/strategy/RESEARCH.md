# RESEARCH — Maya Workflow Kit: 반응, 시장, 이주자, 경쟁 (2026-10-26)

표기: **[사실]** 출처에서 직접 확인한 숫자·문장 · **[추정]** 사실에서 끌어낸 해석 · **[재인용]** 같은 날 오전 전략 검토(an earlier internal review)에서 모은 근거로, 이번에 다시 열어 보지 않은 것.
수집 방법: tavily search/extract, `gh api`, fxtwitter 공개 API(X 게시물의 좋아요·조회수). 원자료: `data/github_stargazers_2026-10-26.txt`, `data/github_user_profiles_2026-10-26.tsv`.
한계: 검색 엔진에 잡힌 것만 셌다. 중국 플랫폼(bilibili, 微博, 知乎, WeChat), Discord, 비공개 그룹은 검색되지 않았다. X 답글은 일부만 읽혔다. 레딧에서는 이 키트 언급을 찾지 못했다(없다는 뜻은 아님).

---

## A. 이 키트에 대한 실제 반응 (공개 6일째, 2026-10-20 v0.2.0 → 10-22 v0.2.1)

### A1. 숫자 [사실]

| 지표 | 값 | 출처 |
|---|---|---|
| extensions.blender.org 다운로드 | **168**, 리뷰 **0**, 0.4.1, 등록 10-20 | https://extensions.blender.org/add-ons/allset/ (2026-10-26 조회) |
| GitHub 릴리스 zip 다운로드 합계 | **1,277** (0.2.1: 819, 0.3.0: 256, 0.4.0: 38, 0.4.1: 154, 0.2.0: 10) | `gh api repos/.../releases` |
| GitHub 스타 / 포크 / 워처 | **81** / 8 / 3 | `gh repo view` |
| 스타가 붙은 날 | 10-22: 19, **10-23: 38**, 10-24: 16, 10-25: 7, 10-26: 1 | stargazers API |
| GitHub 조회 (14일) | 1,711회 / 685명 | traffic/views |
| 유입 경로 (14일, 순 방문자) | 5hyuns.github.io 272 · **modelinghappy.com 201** · Facebook 42 · github.com 22 · 3dnchu.com 2 | traffic/popular/referrers |
| 외부 사용자 이슈 | 5명 6건 (#79 영국 프리랜서, #80, #81·#82 같은 사람, #84 터키) — 나머지 118건은 작성자 본인 | `gh issue list` |

[추정] 스타는 10-23 하루에 거의 절반이 붙고 나흘 만에 하루 1개로 줄었다. 일본 매체 보도(10-22~23)의 파도가 한 번 지나간 모양이다. 이 파도 동안 피드백을 받는 장치(스토어 리뷰, 설문 링크, 앱 안 링크)가 없었다 — 리뷰 0, 외부 이슈 6.

[추정] 0.4.1의 다운로드(154)가 0.2.1(819)의 약 1/5이다. 업데이트를 따라오는 사람의 비율로 읽을 수 있지만, 스토어 업데이트를 쓰는 사람은 GitHub 숫자에 안 잡히므로 하한일 뿐이다.

### A2. 언어별 반응 — X (트위터) [사실]

조회수·좋아요는 fxtwitter API로 2026-10-26에 읽음.

| 언어 | 게시물 | 조회 합계 | 좋아요 합계 | 대표 게시물 |
|---|---|---|---|---|
| **일본어** | 10 | **300,836** | **3,345** | [@syu_ya23](https://x.com/syu_ya23/status/2113279896470622240) 126,453 조회 / 1,384 좋아요 "BlenderをMayaのようにできるMaya Workflow Kitを少し触ってみたけど、めっちゃMaya！ すごい！"; [@happy_modeling](https://x.com/happy_modeling/status/2113176078374338563) 94,517 / 971; [@Yokohara_h](https://x.com/Yokohara_h/status/2113297464887554447) 32,943 / 367 "BlenderがまるでMayaだ"; [@ymt3d (3D人)](https://x.com/ymt3d/status/2113650127521071347) 30,903 / 478 |
| 영어 | 7 | 45,161 | 646 | [@ArtOfPilgrim](https://x.com/ArtOfPilgrim/status/2113601919369326912) 32,443 / 427 "just use maya at this point?"; [@yiningkarlli](https://x.com/yiningkarlli/status/2113725325331087631) 4,711 / 109 "holy cow it really does look/behave exactly like Maya… 15+ years of Maya baked into muscle memory" |
| 합계 | 17 | 345,997 | 3,991 | |

- 일본어 비중: **조회의 87 %, 좋아요의 84 %** (찾은 게시물 기준).
- 영어 게시물 7개 중 **6개는 일본어 게시물을 인용하거나 그 답글**이다(ArtOfPilgrim 2개, royal_konijn, AlexGuyBooks, Bardeinn → @syu_ya23; NikSaf_art → @ymt3d). 독립적인 영어 게시물은 Yining Karl Li 하나.
- **사용자 가설 "일본인 비중이 높다" → 도달(reach)에 대해서는 맞다.** 다만 원인은 "일본에 Maya 사용자가 많아서"가 아니라, 일본 CG 뉴스 계정 두 곳(MODELING HAPPY, 3D人)과 일본 Blender 커뮤니티의 유명 작가 두 명(Syuya Mukai, Hirokazu Yokohara)이 사흘 안에 연달아 소개한 것이다 [사실: 날짜·인용 관계]. "애니메이션 때문"이라는 근거는 반응 글 안에서 찾지 못했다 — 일본어 반응은 거의 "めっちゃMaya", "MAYAじゃん", "まるでMaya" 같은 외형 감탄이다.

반응 내용 (원문):
- 긍정·기대: "Will give it a spin tomorrow!! … muscle memory is hard wired after 20 years of Maya." ([@StephenJHibberd](https://x.com/syu_ya23/status/2113279896470622240)) · "the only reason why I still haven't made the switch after 15 years of wanting to" ([@PMoppelpo](https://x.com/yiningkarlli/status/2113725325331087631)) · "I went to school for Maya so this is something I've been waiting for" ([@shanomen](https://x.com/ymt3d/status/2113650127521071347)) · "早速導入してみました🙏" ([@teikenCG](https://x.com/teikenCG/status/2113329753268826596)) · "えっ！！blender覚えなくて使える！？" ([@MangaNoriba](https://x.com/MangaNoriba/status/2113361011231359263))
- 회의·반대: "just use maya at this point?" (32k 조회, 답글 47) · "I gratefully left that dinosaur behind for a reason" ([@AlexGuyBooks](https://x.com/AlexGuyBooks/status/2113369602415788219)) · "blenderさまの尊厳破壊" ([@lnbl_](https://x.com/lnbl_/status/2113520564216418631)) · "+ Blender is more ethical + Blender is free + Blender doesn't crash every 10 seconds" (@VestigiumDev, 답글)
- 기대와 다른 것: "Tested it and while very impressive it's not addressing the key issue which is muscle memory and 1 to 1 conversion." ([@Javgamedev](https://x.com/happy_modeling/status/2113176078374338563)) · "I was hoping for a add on that allow you to import Maya rig model to blender or blender rig model into Maya without breaking the rig ctrl" (@thechriss2004ss) · "Even with the g repeat?" (@Hashgraphian)
- **3ds Max 판 요청 4건 이상**: "maxもぉぉmax版もたのむぅぅ" (@humihito1213), "3dsMaxっほしいなー Cinema4Dでもいい！" (@tw003_), "Need 3ds max one too" (@ChaggerSahil), "one like 3ds max?" (@Bardeinn). 같은 주에 3ds Max 풍 Blender 앱(Jake Denham, AI로 약 1주) 보도: https://3dnchu.com/archives/blender-3ds-max-interface-ai/ ; "バイブコーディングなんで、同じパターンのBlender UIが何十と生まれそうです" ([@oakcorp](https://x.com/oakcorp/status/2113572618297393644), 7,278 조회).
- 학습 대체재로 보는 시각: "a genius move for anyone needing to learn Maya for a studio. So you don't have to pay Autodesk pricetag just to learn it" ([@ArtOfPilgrim](https://x.com/ArtOfPilgrim/status/2113715323484680213)) — 상표·포지셔닝 위험이 있는 해석(STRATEGY ④).

### A3. 언어별 반응 — 웹 글 [사실]

| 언어 | 글 | 내용 요지 |
|---|---|---|
| 일본어 | [MODELING HAPPY](https://modelinghappy.com/archives/71166) (10-22) | 기능 소개. "ひと目ではBlenderと気づかないほど" |
| 일본어 | [3D人](https://3dnchu.com/archives/maya-workflow-kit-for-blender/) (10-23) | 기능 소개 + 관리자 한마디 "Blenderに移行したいけどUIに馴染めなかった方は…オールインワンアドオンから入るのもアリ". 3D人은 같은 작성자의 "Maya VAT Encoder"도 소개한 적 있음 |
| 일본어 | [ModelingTechNote](https://modelingtechnote.com/2026/10/23/maya-workflow-kit-for-blender) (10-23) | "上のバーのスイッチでいつでも素のBlenderに戻せるところ…Blenderのチュートリアルはどれも標準のキーで説明しているので" — 스위치를 가장 좋은 점으로 꼽음 |
| 일본어 | [note: みよちゃん (shinnichi chiba)](https://note.com/sc_conceptart/n/n570449d1be00) (10-22) | 컨셉 아트 작가. "Blenderの高速プレビューやマテリアル環境には強く惹かれるが、Mayaで身についた操作感のせいで移れない" 문제를 이 키트가 입구에서 풀 수 있다고 기대 (아직 써보지 않음) |
| 한국어 | [arca.live 3DCG 채널](https://arca.live/b/3d3d/186753806) (10-22) | 조회 259, 댓글 20. 댓글은 .ma/.mb 호환 문의가 많고, "블렌더 강의에서 강사가 마야 단축키로 진행해서 계속 스턴이 걸렸다"는 불만 — Blender 사용자 입장에서 Maya 키가 *남을 방해하는* 사례 |
| 영어 | [BlenderArtists 스레드](https://blenderartists.org/t/maya-workflow-tool-for-blender/1655759) (10-23) | 비판적 시험기: "Not everything works like Maya, like Quaddraw (Multicut does); Deformers are just Blender Modifiers"; "if you press D to change the pivot like Maya, you won't be able to do it"; Maya 워크스페이스 전환은 "a hybrid abomination"; 스컬프트는 Blender UI로 돌아가라고 권함; 숫자패드 1/3은 안 됨 |
| 영어 | [Lenovo Creator Community](https://www.lenovo.com/creator/digital-art-school/post/maya-workflow-kit-for-blender-GXbeGAlZ2OdqpMH) | "I seriously wish something like this would have been available about a decade ago. Although it's probably best to learn the default Blender UI / UX, since any app updates will be handled better" |
| 스페인어 | [Facebook 그룹 bigminimentor](https://www.facebook.com/groups/bigminimentor/posts/30158346580432102) | 링크 공유 |
| 베트남어 | [Instagram](https://www.instagram.com/p/De248vBHzR4) | "Dân Maya dùng Blender mà không phải học lại phím tắt!" |

### A4. GitHub 행동 사용자(스타·포크·이슈)의 지역 [사실 + 추정]

프로필에 위치·소속·한자 이름이 **명시된** 경우만 셈(작성자 계정 2개 제외, 스타 79명):

| 지역 | 명시된 수 | 예 |
|---|---|---|
| 중국·대만·홍콩 | **11** (+ 병음 아이디로 보이는 약 10명 [추정]) | Taipei Pipeline TD/TA, 상하이 TA(ex-Perfect World), 쓰촨 대학 3D 애니메이션 교수, AboutCG, 홍콩 리깅 TA, 포크 중 数字王国(Digital Domain) 소속 |
| 일본 | **3** (+ 약 3명 [추정]) | Tokyo 2명, 게임 회사 Melpot TA(포크도 함) |
| 미국 | 3 | Boise VR 아티스트, LA, FR/US |
| 기타 | 약 9 | 브라질, 터키, 태국, 러시아권 2, 폴란드, 영국(이슈) |
| 알 수 없음 | 약 40 | |

[추정] **도달은 일본, 행동(스타·포크)은 중화권이 더 많다.** 스타·포크한 사람 중 직함이 보이는 사람은 TA·Pipeline TD·리깅 TA가 눈에 띈다 — 일반 아티스트보다 도구를 뜯어보는 사람이 GitHub에서 반응한다. 일본 쪽은 GitHub보다 github.io 사이트와 스토어로 갔을 수 있다(유입 1·2위가 사이트와 일본 매체).

---

## B. 일본 시장

| # | 사실 | 출처 |
|---|---|---|
| B1 | CG년감 2026 게재 기업 중심 151개사 응답(2026-07-10~16): **메인 툴 Maya 58 %(87건)**, 3ds Max 17 %, Blender 12 %, Cinema 4D 7 %, Houdini 2 %. 응답사 사업 영역: 애니메 81, 게임 75, 실사 VFX 60, 유기기 53 (복수 응답) | [CGWORLD × mouse「CGプロダクション制作環境一斉調査2026」](https://cgworld.jp/special-feature/2609-mouse-daiv-cg2026.html) |
| B2 | 같은 글: CG년감 2026 게재 351개사의 사용 툴 전반 — **Maya 269사, Blender 222사, 3ds Max 206사**, Houdini 145, C4D 74 | 같음 |
| B3 | 일본 애니메 스튜디오의 Blender 도입은 대부분 **3ds Max에서** 옴: 카라(2019, Max → Blender), 산지겐(2023 라이선스 갱신 때 Max → Blender, 약 200명 중 70 %가 3DCG 툴 사용, "3年ごとに発生する巨額の更新費用"), MAPPA『LAZARUS』(Max에 Blender 추가, R&D 3개월, 실패 시 Max로 돌아갈 Plan B) | [Khara 사례](https://www.blender.org/user-stories/japanese-anime-studio-khara-moving-to-blender) [재인용], [CGWORLD 산지겐 ACTF2026](https://cgworld.jp/article/202604-actf-sanzigen.html), [Too 레포트 MAPPA](https://www.too.com/dc/report/2512_atsuc2025_mappa_lazarus) |
| B4 | 산지겐: 아티스트가 AI로 직접 툴을 만들어 사내 툴 100개 이상, "アドオンは自由に購入して良い" 방침 — 이전 툴의 기능을 Blender 애드온으로 다시 만드는 것이 스튜디오 이전의 표준 방식 | 같음 |
| B5 | Maya 가격(일본): 정가 연 약 ¥328,900(세금 포함, 영상 설명), **Maya Indie 연 ¥52,800~53,900**; 일본은 Indie 대상국 | [kimstation](https://kimstation.com/maya_indie), [YouTube short](https://www.youtube.com/shorts/Jeu03OpR_Yc), [Autodesk JP Indie](https://www.autodesk.com/jp/campaigns/me-indie/maya-indie) |
| B6 | 일본어 이주 글의 불만: 게임 TA "ネットのチュートリアルではblender操作のショートカットキーがよく使用されており、この設定(業界互換)だと操作がわからない場合があります"; 타임라인 범위 설정을 못 찾음, 음수 프레임, Graph Editor 감각 차이 | [Zenn hota「mayaユーザーが知っておきたいblenderの基礎知識」](https://zenn.dev/hota12/articles/5428eafc52dd6e) |
| B7 | 일본어로 Maya Config(유료 경쟁품)를 관리자 권한으로 설치하는 강좌 영상이 있음 — 일본에도 "Maya 풍 Blender" 수요가 이 키트 전부터 있었음 | [YouTube Basic 4-0](https://www.youtube.com/watch?v=--yAdeT9AGc), [JOINUNIVERSE EP.35](https://www.youtube.com/watch?v=JjTQNhkfhug) |
| B8 | Blender Survey 2025(전 세계): Blender 전에 쓴 3D 앱 중 3ds Max 27.43 %, **Maya 13.47 %**, C4D 13.14 % | [blender.jp 요약](https://www.blender.jp/news/2026/survey2025_result) |

[추정] 일본은 **회사 메인 툴로서 Maya 비중이 높은 시장**이고(B1), Blender 사용 회사도 많다(B2). 그래서 "Maya 손 + Blender" 조합에 관심이 클 바탕은 있다. 하지만 일본에서 실제로 스튜디오 단위로 Blender로 옮긴 사례는 3ds Max 출신 애니메 스튜디오다(B3). "일본 = 애니메이션 = Maya"라는 연결은 근거가 약하다 — 일본 애니메 CG는 역사적으로 3ds Max 비중이 크고, 일본 Maya 비중은 게임·VFX·유기기에서 올 가능성이 높다 [U: 업종×툴 교차표는 공개되지 않음]. X의 3ds Max 판 요청(A2)도 같은 방향이다.

---

## C. 영어권 Maya → Blender 이주자 [재인용 위주]

| 주제 | 근거 (원문) |
|---|---|
| 1위 장애 = 튜토리얼 불일치 | "that keymap regularly goes out of date… every tutorial… rely on default settings" ([BA](https://blenderartists.org/t/should-i-learn-industry-compatible/1284160)); Tangent Animation "don't change your hot keys… just the wrong thing to do" ([BCON](https://www.youtube.com/watch?v=CqSEtTF8hPE)); 반대 목소리 "IC keymap was basically my stepping stone" ([HAJWORKS](https://www.youtube.com/watch?v=XJywS5Mmacc)) |
| 근육기억 | 이번 X 반응 A2 (15–20년 경력자들) |
| 애니메이터 | Sir Wade Neistadt: Graph Editor 차이가 "drive me crazy", 대신 F-Curve Noise 모디파이어는 "would take so much longer in Maya" ([YouTube 215k](https://www.youtube.com/watch?v=L-vLraYGir8)); BA "I love blender but I'm getting a sense that it isn't really meant to be used for animation" — 답은 전부 환경설정 바꾸기 ([BA 1589561](https://blenderartists.org/t/i-need-help-with-blenders-graph-editor/1589561), 이번 조사) ; Graph Editor를 Maya처럼 세팅하는 튜토리얼 수요 ([YouTube](https://www.youtube.com/watch?v=vKgO3NsYORo), 이번 조사) |
| 리거 | "The worst experience in blender rigging is weight painting" ([devtalk](https://devtalk.blender.org/t/rigging-more-work-needs-to-be-done/9622)) |
| 모델러 | 모델링 부서 전환은 "very smooth", 걱정은 리깅·애니 ([tech-artists.org](https://www.tech-artists.org/t/moving-a-pipeline-from-maya-to-blender/14490)); "[Maya] UV and retopology tools are much better" (r/3Dmodeling 스니펫) |
| 개념 혼란 | Collections ≠ Groups ("confused the collection with Groups as a 10 years Maya user", [rendereverything](https://www.rendereverything.com/blender-groups-confusion-about-collections)); 스케일: "We lock AYON's blender host to 0.01 scale (otherwise light values, clipping planes are really troublesome)" ([Ynput](https://community.ynput.io/t/blender-look-workflow/2453)) |
| 빨리 적응한 사례 | Flow: "Many of the animators in Flow took less than a week to switch", 전환 이유 "mainly because of EEVEE" ([blender.org](https://www.blender.org/user-stories/making-flow-an-interview-with-director-gints-zilbalodis)); 교육 현장: 학생이 Maya보다 빨리 익힘 ([BCON26](https://www.youtube.com/watch?v=dVrELpmfcEQ)) |
| 스튜디오 실패 패턴 | "seniors treated a Blender pipeline as a Maya-but-free" 하면 실패 ([BA](https://blenderartists.org/t/studios-that-are-using-blender/1466142)) |

직군별 [추정, 위 근거 종합]: 모델러 = 손·내비게이션이 벽, 몇 주 안에 적응 · 애니메이터 = Graph Editor·레이어·키 동작이 벽이고 가장 오래 Maya에 남음 · 리거 = 웨이트·디포머가 벽, 가장 회의적 · 게임 아티스트 = FBX 왕복·단위가 벽 · 학생 = Blender 기본을 빨리 익혀 키트 필요가 적음 · 프리랜서·인디 = 비용 동기가 가장 크고 "회사에선 Maya, 집에선 Blender" 이중 생활.

---

## D. Maya의 강점 vs Blender의 강점

| Maya 쪽 | 근거 |
|---|---|
| 캐릭터 애니메이션 환경: Graph Editor, 애니메이션 레이어, Time Editor, HumanIK (모캡 정리) | ["Maya is the strongest overall choice… for demanding motion capture cleanup. Its HumanIK retargeting, Graph Editor, animation layers, Time Editor"](https://www.mimicproductions.com/post/best-3d-animation-software-for-character-production-maya-vs-blender-vs-3ds-max) (이번 조사, 판매자 글 T2) |
| 스튜디오 표준·채용 조건 | "スタジオに入社するのにMaya必須など条件が続く限りは学校としても授業は必須" ([note やす](https://note.com/yasucg/n/nba131ed760a3)); 일본 회사 메인 툴 58 % (B1) |
| 대규모 파이프라인(USD, 자체 툴, 렌더팜) | Behaviour Interactive: Maya 스크립트 100+ 조사 후 이전, 3–4개월 교육 ([BCON 2025](https://conference.blender.org/2025/presentations/3973)) [재인용] |

| Blender 쪽 | 근거 |
|---|---|
| 비용 | Maya 미국 정가 **$2,010/년, 월 $255**, Indie $330/년(수익 $100k 미만, 나라마다 다름) ([Vagon 2026-08](https://vagon.io/blog/how-much-does-maya-cost), [SuperRenders 2026-09](https://superrendersfarm.com/article/how-much-does-maya-cost)); 산지겐의 1순위 이유도 비용 (B3) |
| 렌더 속도·EEVEE | Flow, 산지겐("Eeveeは非常に軽快で、3Dビューポート上で確認しながらリアルタイムに作業") |
| 모디파이어·Geometry Nodes·Grease Pencil·스컬프트 | [재인용] W5, W38, Khara |
| 빠른 실험(컨셉 아트) | note みよちゃん (A3) |
| 오픈소스로 옛 버전 유지 | 산지겐 (B3) |

---

## E. 경쟁·대체재

| 대안 | 사실 | 사람들이 말하는 장단 |
|---|---|---|
| Blender Industry Compatible 키맵 (내장) | 매뉴얼 "not a comprehensive list"; Tab=검색 등 기본 키 이동 [재인용 W13] | 튜토리얼 불일치, 낡음; 디딤돌로 쓴다는 사람도 있음 |
| Form Affinity Maya Config (Gumroad) | 작성자 평점 "4.9 from 769 verified reviews across 6 other products" ([Gumroad](https://formaffinity.gumroad.com/l/EyCxF), 이번 조사); 원조 752 평점 [재인용] | 칭찬 = 내비게이션·마킹 메뉴·"집 같다"; 불만 = 이중 바인딩, Blender 업데이트마다 고장 ("the UI was broken, a lot of hotkeys were broken… pretty normal for a big Blender update", [DevLog 010](https://www.youtube.com/watch?v=KXdN3l--Q4I)), 관리자 권한 설치, 기존 애드온 삭제 |
| Maya Config Pro V2.5 (Superhive) | Sales 50+, 3개월 전 출시, Blender 5.0–5.2, 12개월 지원, Program Files에 설치해 권한 팝업 ([Superhive](https://superhivemarket.com/products/maya-config-pro)); CG Vortex 소개 영상 1,465 조회 (2026-10-16) | 마킹 메뉴, 셸프, 모델링 툴킷 — 키트와 같은 방향의 유료품 |
| 3ds Max 풍 Blender 앱 (Jake Denham) | AI로 약 1주 만에 구축, 미배포 (2026-10) | "同じパターンのBlender UIが何十と生まれそう" — **"Maya처럼 보이게"는 곧 흔해진다** [추정] |
| "Blender for Maya users" 강좌 | Blender Studio 공식 "From Maya and Max to Blender" (Object/Edit Mode, 3D Cursor, Bad Scaling…) [재인용 W23] | 공식이 인정한 개념 함정 목록 = 키트의 개념 층 대상 |

**키트의 차별점이 통하는가** [추정, A의 반응 기준]:
- 통한 것: "겉모습이 정말 Maya" (일본어 반응 대부분), "언제든 Blender로 돌아가는 스위치" (ModelingTechNote, 3D人, note — 세 매체가 따로 꼽음), 무료·제거 깔끔.
- 아직 증명 안 된 것: 메뉴 깊이(옵션 창, 1,318개 메뉴 중 61 %). 이 깊이를 칭찬하거나 그 부족을 지적한 외부 글은 찾지 못했다. 외부 사용자 지적은 손(D 피벗, Quad Draw, 숫자패드, 압출 후 이동, 더블클릭 루프)과 리그 왕복이다.
- 위험: "Maya처럼 보이는 Blender"는 AI로 1주면 흉내 낼 수 있다(E 3행). 남는 차이는 **정확한 손 감각, 조용히 틀어지는 개념의 처리, Blender 업데이트 내구성**이다.

---

## F. 저장소에서 확인한 관련 사실 [사실]

- 키트 내부 첫 1시간 측정(에이전트가 시뮬레이션 이벤트로 수행, 사람 아님): 39 동작 중 OK 32 · AWKWARD 5 · **BLOCKED 2** — 막힌 두 개는 모두 **리그가 있는 FBX 왕복**(Blender로 다시 가져오면 0.01 배·90° 회전, Maya에서 열면 `skeleton1` 아래 rotate −90 / scale 100). AWKWARD 중 하나는 **바운스 애니메이션: Maya의 Translate Y(위)가 키트에서는 Blender의 수평 Y라 공이 미끄러짐** (`C:/Repos/blender-maya-kit/docs/first_hour.md:75,82,84`, 커밋 전).
- 앱 안에 피드백·설문 링크 없음, 번역(`bpy.app.translations`) 없음 (`src/allset` grep). "(Blender: …)" 두 언어 표시는 마킹 메뉴 한 곳뿐 (`src/allset/marking/modal.py:77`).
- 스토어 설명이 0.2.1 이전 내용(테마 적용, 앱 템플릿 복사, `bpy.utils.execfile`, 「Revert Maya Look」)을 아직 담고 있음 — 같은 페이지의 0.2.1 변경 내역("No theme is shipped… no files are copied")과 모순. GitHub Pages 사이트도 "The extensions.blender.org listing is not live yet"라고 씀.
- 수동 확인 목록: 773개 중 106개만 체크 (`docs/manual_checks.md`).
