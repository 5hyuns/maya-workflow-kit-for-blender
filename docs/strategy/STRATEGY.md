# STRATEGY — Maya Workflow Kit: 누구를 위해, 무엇을, 어떻게 잴 것인가 (2026-10-26 초안)

근거는 `RESEARCH.md`(출처 링크), 모르는 것은 `UNKNOWNS.md`. 같은 날 정한 제품 원칙(`docs/user_decisions.md` 「2026-10-26 제품 원칙: 겉모습은 Maya, 엔진은 Blender」)을 뒤집지 않고, 그 위에 **대상 사용자**를 얹는다. 이 문서의 판단은 모두 delegated(사용자 위임)이고, ⑦의 질문에 답하면 바뀐다.

---

## ① 한 줄 정의 (미션)

**Maya에서 일을 배운 사람이 Blender를 쓰기로 한 첫날부터, 손에 익은 Maya 방식 그대로 일하면서 Blender의 렌더·모델링 도구를 쓰게 하는 다리. 언제든 한 번에 순수 Blender로 돌아갈 수 있다.**

- 아닌 것: Maya 복제품, Maya 학습용 대체재, Maya 파일(.ma/.mb)·MEL 호환 도구.
- 태그라인 제안 (현재 "The whole Maya workflow in Blender, in one install"은 "전부"를 약속해서 BlenderArtists 시험기처럼 "D 피벗이 안 된다, Quad Draw가 다르다"로 평가받는다):
  - "Your Maya hands, Blender's engines" (35자)
  - "Work the Maya way in Blender, switch back anytime" (49자)

## ② 대상 사용자 페르소나

| | 페르소나 | 근거 (RESEARCH) | 비중 [추정] |
|---|---|---|---|
| **P1** | **근육기억 베테랑 — Maya 10–20년, 개인 작업·부업은 Blender로 하고 싶다.** 회사는 Maya 그대로일 수 있음. 영어권·일본 모두 | X: "15+ years of Maya baked into muscle memory"(Yining Karl Li), "after 20 years of Maya"(StephenJHibberd), "the only reason why I still haven't made the switch after 15 years"(PMoppelpo), "since first beta back in 1997"(Keyframe) | 반응 중 가장 큼 |
| **P2** | **두 집 살림 — 회사는 Maya, 프리랜스·개인 게임·컨셉 아트는 Blender.** 하루에도 두 프로그램을 오간다 | 일본 게임 TA (Zenn hota: 업무 Maya, 개인 게임은 Blender), 컨셉 아티스트 (note みよちゃん: Blender 프리뷰·머티리얼이 끌리는데 손 때문에 못 옮김), QvElI 영상(스튜디오 Maya, 저녁 프리랜스 Blender), 일본 회사 메인 툴 Maya 58 % + Blender 사용 회사 222/351 | 일본에서 특히 클 가능성 |
| **P3** | **Blender로 옮기는 팀의 Maya 출신 스태프·TD** — 회사가 비용 때문에 Blender로 가는데 손은 Maya | 산지겐(라이선스 갱신 비용), MAPPA(3개월 R&D), Behaviour Interactive(3–4개월 교육); GitHub 스타·포크 중 Pipeline TD·TA (대만, 상하이, 홍콩, Melpot, Digital Domain 소속) | 수는 적고 영향은 큼 |
| (P4) | Maya로 학교를 나왔지만 라이선스가 없는 졸업생·독학자 | "I went to school for Maya"(shanomen), "learn Maya for a studio without paying"(ArtOfPilgrim) | **1차 대상 아님**: "Maya 학습 대체"는 상표·제휴 오해 소지(UNKNOWNS 카드 11), Autodesk 교육 라이선스는 학생에게 무료, 결국 Maya로 가는 사람 |

대상 아님 (명시): Blender를 처음부터 Blender로 배우는 사람(arca.live의 반감), Maya 파일·리그를 그대로 옮기길 원하는 사람(키트 범위 밖 — 안내만), 3ds Max 사용자(⑦ 질문 4).

**권장 1차 대상 = P1 + P2** (같은 사람이 많다: 경력자이고 Blender를 "개인 쪽"에서 쓴다). P3은 P1·P2가 만족한 뒤 따라온다. 일본은 별도 페르소나가 아니라 **P1·P2가 가장 많이 모인 곳**으로 다룬다.

## ③ 할 일(JTBD)과 Pain

| 페르소나 | 하려는 일 (When … I want to … so I can …) | Pain (근거) |
|---|---|---|
| P1 | 개인 작업을 시작할 때, 손을 다시 배우지 않고 첫날부터 모델·애니를 만들고 싶다, 그래야 Blender 렌더·무료의 이점을 바로 얻는다 | 첫 5분에 카메라·피벗에서 막혀 창을 닫음 (note みよちゃん); 튜토리얼이 Blender 키 (BA, Tangent); D 피벗·Quad Draw·숫자패드가 Maya와 다름 (BlenderArtists 시험기) |
| P2 | 회사(Maya)와 집(Blender)을 오갈 때, 손이 헷갈리지 않고 결과 파일이 상대 프로그램에서 그대로 열리길 원한다 | **리그 FBX를 Maya로 보내면 rotate −90 / scale 100** (키트 측정, BLOCKED); "import Maya rig… without breaking the rig ctrl"(X 답글); 단위 100배 (Ynput) |
| P2 (애니) | 바운스·걷기 같은 기본 애니를 Maya 감각으로 찍고 Graph Editor로 다듬고 싶다 | **Maya Translate Y(위)가 Blender Y(수평)** → 바운스가 미끄러짐 (키트 측정, AWKWARD); Graph Editor 감각 "drive me crazy" (Sir Wade); "isn't really meant to be used for animation?" (BA) |
| P3 | 팀이 Blender로 갈 때, 스태프가 몇 주 안에 이전 속도를 되찾게 하고 싶다 | 업데이트마다 깨지는 애드온 (Maya Config DevLog), 관리자 권한 설치, 사내 배포·버전 고정 필요 (산지겐: 툴을 직접 유지보수) |

## ④ 가치 제안 — "Maya처럼"과 "Blender 장점" 사이의 원칙

오전의 네 층(손·장소·개념·엔진)을 그대로 쓰고, 사람들이 실제로 칭찬한 것과 막힌 것으로 경계를 정한다.

| 판정 | 무엇 | 왜 (근거) |
|---|---|---|
| **Maya 그대로** | 손: 내비게이션, 선택·수정키, QWERTY, 핫박스·마킹 메뉴, 홀드 키(D/X/C/V), Channel Box 입력과 S 키 찍기 | 칭찬은 모두 여기서 나옴 ("めっちゃMaya", "holy cow"); 외부 버그 보고도 여기 (#80, #84, BA 시험기) |
| **Maya 그대로** | 조용히 틀어지는 개념: 부모 지정, Freeze, 단위(cm), 이름, **내보내기 축·스케일(리그 포함)** | 틀어진 결과는 다른 프로그램에서 발견됨 → 신뢰를 잃음 (키트 측정 BLOCKED 2개) |
| **Maya 자리, Blender 이름 같이** | 메뉴 위치·이름, 편집기 틀, 회색 항목 안내 | "장소"는 찾기 위한 것. 작동 항목에도 "(Blender: 이름 키)"를 붙여 두 언어로 (지금은 마킹 메뉴 한 곳뿐) |
| **Blender 방식으로 안내** | 렌더(EEVEE/Cycles), 셰이더, 시뮬레이션, Geometry Nodes, 스컬프트, 모디파이어 | 사람들이 Blender로 오는 이유 (Flow "because of EEVEE", 산지겐 EEVEE, note みよちゃん). Maya 메뉴 자리에서 Blender 기능을 열고 Maya 말로 설명 |
| **Blender로 돌아가는 문은 언제나 열려 있게** | Maya / Blender 스위치, 키트는 사용자 설정을 안 바꿈 | 일본 매체 세 곳이 따로 꼽은 1위 장점 |
| **안 함** | .ma/.mb 읽기, MEL, Y-up 월드, nCloth/nCache 재구현, maya.cmds 확장(216에서 멈춤), Maya 렌더 밝기 맞추기, "Maya 학습 대체" 마케팅 | 비용 대비 대상 사용자 가치 낮음, 상표 위험 |

Y-up은 "안 함"이지만 바운스 문제는 남는다 → 해결은 월드 축이 아니라 **안내와 표시**(예: Channel Box에서 Maya 위 방향 채널을 알려 주기, 키 찍을 때 한 줄 경고, 또는 Maya 축 이름 표시 옵션)로 찾는다. 어느 쪽이 덜 헷갈리는지는 애니메이터 인터뷰로 정한다.

## ⑤ 성공 지표

텔레메트리는 쓸 수 없다(스토어 심사, 네트워크 코드 없음). 그래서 밖에서 보이는 숫자로 잰다.

**North Star: 새 버전을 받는 사람 수** — 각 릴리스 후 14일 동안의 다운로드(스토어 + GitHub zip). 업데이트를 따라오는 사람 = 아직 쓰는 사람이라는 대리 지표.
- 기준선: 0.2.1 GitHub 819, 0.4.1 GitHub 154 (공개 6일 차), 스토어 누적 168. 스토어는 버전별 숫자가 안 보이므로 누적 증가분을 릴리스 날마다 기록.
- 목표(6개월) [delegated]: 릴리스당 14일 다운로드가 줄지 않고 늘어남.

보조 지표:
| 지표 | 재는 법 | 목표 [delegated] |
|---|---|---|
| PMF 문항: "이 키트를 못 쓰게 되면 얼마나 실망하나" 중 "매우 실망" 비율 | 설문 Q9 | 첫 측정을 기준선으로, 40 %가 흔히 쓰는 기준 |
| 2주 유지: 설치 2주 뒤 Maya 모드를 켜 두는가 | 설문 Q4 | 기준선 측정 |
| 페르소나 흐름의 첫 1시간 BLOCKED | `tools/dogfood.py --scenario first_hour` + 사람 1명 녹화 | 0 (지금 2) |
| 외부 사용자 보고 수와 첫 답변 시간 | GitHub 이슈 | 주 3건 이상 받기, 48시간 안에 답 |
| 스토어 리뷰 수·평점 | extensions.blender.org | 리뷰 10개 (지금 0) |
| 업데이트 내구성 | 새 Blender 출시일에 켜서 실패 0 | 유지 |
| 메뉴 동작률 % | `tools/menu_count.py` | **목표 아님**, 회귀 확인용 부록 |

## ⑥ 열린 이슈·백로그 재정렬

| 항목 | 판정 | 이유 |
|---|---|---|
| 스토어 설명·사이트 문구 갱신 (낡은 테마/템플릿/execfile 설명, "listing not live yet") | **올림 — 오늘** | 처음 보는 사람에게 키트의 가장 큰 장점을 가림 |
| 설문 링크 (README, 스토어, 사이트) + 앱 Help > Send Feedback | **올림 — 이번 주** | 피드백 장치 없음 (리뷰 0) |
| #124 First hour as a Maya user (측정 진행 중, 커밋 전) | **유지·올림** | 이미 BLOCKED 2개를 찾음. 사람 1명 녹화를 추가 |
| 리그 FBX 왕복 (Maya에서 rotate −90/scale 100, 재수입 0.01 배) | **올림 — 1순위 수정** | P2의 핵심 일, 신뢰 문제 |
| Y-up 바운스 안내 | **올림** | P2 애니메이터의 첫 애니 |
| #123 FX and Render: Maya menu places, Blender engines | **나눔**: Render 연결 = 유지, FX = 내림 | 렌더는 사람들이 Blender로 오는 이유; FX는 cm 단위 계약이 먼저고 대상 사용자 빈도 낮음 |
| #108 Maya menu coverage and roadmap | **바꿈**: "Maya → Blender 개념 지도 + 사용자 보고 우선" 이슈로, % 표는 부록 | % 는 목표가 아님 |
| #89 Quad Draw leftovers | **내림** (설문에서 Quad Draw가 Top 3에 오르면 올림) | BA 시험기는 Quad Draw가 Maya와 다르다고 지적 → 남은 일보다 "다르다는 느낌"의 원인을 먼저 들어야 함 |
| 동결 목록 (maya.cmds, NURBS Surfaces, GN 디포머, Reference/Component/Shape/Connection Editor 고급, 렌더 밝기) | **중단(고장만)** | 대상 사용자 신호 없음 |
| 두 언어 툴팁 "(Blender: 이름 키)" | **유지 — 다음 분기** | 설문 H3 결과로 앞당길지 결정 |
| 일본어 현지화 | **보류 → 작게 시험** (README_ja, 스토어 설명 일본어 단락, 환영 창) | 도달 87 % 일본어. 전체 번역은 H6 확인 후 |
| 3ds Max 판 | **보류** | ⑦ 질문 4 |

### 브레인스토밍: 포지셔닝과 다음 6개월 후보 (`/unknowns:brainstorm`)

영향 × 노력 배치:

```
영향 ↑
 큼  │ B1 B2 B3        B4  B7      B10
     │                 B8  B9      B6
 중간│     B5                      B11
 작음│
     └──────────────────────────────── 노력 →
        S(오늘)   M(1–2주~분기)   L/XL(분기 이상)
```

| # | 이름 | 한 줄 | 기대 효과 | 노력 | 위험 | 성공 측정 | 코드 |
|---|---|---|---|---|---|---|---|
| **B1** | 진열장 고치기 | 스토어 설명·사이트를 0.4.1 실제 동작으로, 태그라인 교체, 설문 링크 | 처음 보는 사람이 "아무것도 안 바꾸는 키트"로 이해; 리뷰·응답 유입 | S (오늘) | 스토어 설명 변경은 사용자가 직접 업로드 | 스토어 리뷰 수, 설문 응답 수 | `docs/distribution/listing.md` |
| **B2** | 지금 묻기 | 설문(3개 언어) 게시 + 일본어 반응 글(@syu_ya23 등)에 답글로 감사·설문 링크 | 2주 안에 응답 50–150개 [추정] | S | 홍보로 읽히면 반발 → 문구를 짧고 정직하게 | 응답 수, 언어·직군 분포 | — |
| **B3** | 앱 안 피드백 문 | Help 메뉴·환영 창·환경설정에 "Send Feedback / Survey / Report a Problem" (`wm.url_open`) | 설치한 사람이 직접 말할 길; 다음 파도에서 놓치지 않음 | S | 심사 스캔(네트워크 코드 금지)과 충돌 없음 확인 필요 | 외부 이슈/주 | `src/allset/welcome.py`, Help 메뉴 (`ui/menu_map.py`) |
| **B4** | 두 집 살림의 신뢰 | 리그 FBX 왕복을 Maya-정확하게, Y-up 바운스 안내 | P2가 "Maya로 보내도 된다"고 믿게 됨; first hour BLOCKED 2 → 0 | M | FBX 리그 축 변환은 깊은 함정 (Blender FBX 임포터·익스포터 한계) | first hour BLOCKED 수, mayapy 왕복 테스트 | `docs/first_hour.md:75,82,84`, `operators/file_io.py` |
| **B5** | 일본어 입구 | README_ja, 스토어 설명 일본어 단락, 환영 창·Recommended setup 일본어 | 도달 87 %에 맞는 첫 화면 | M | 유지 비용(문서 둘), 번역 품질 | 일본어 응답의 "설치까지 갔다" 비율 | 번역 장치 없음 (`bpy.app.translations` 미사용) |
| **B6** | 일본 × 애니메이터 집중 | 일본 애니메이터용 시나리오·튜토리얼·Graph Editor 손 감각 | H2가 맞으면 가장 큰 단일 집단 | L | H2가 틀리면 헛수고 (일본 애니메 CG는 Max 출신이 많음) | 일본 애니메이터 응답 비율 | — |
| **B7** | 두 언어 다리 | 모든 동작 항목 툴팁·Help Line에 "Blender: 이름 (키)", 스위치 옆 "이 동작 Blender로는?" | 튜토리얼 불일치(1위 장애)를 직접 줄임; Blender 커뮤니티 반감 완화 | M | 315+개 안내와 문체 통일 작업 | 설문 H3, 인터뷰 | `marking/modal.py:77` (이미 마킹 메뉴에서 함), `ui/notices.py` |
| **B8** | Maya 손으로 Blender 렌더 | Render 메뉴 자리에서 EEVEE/Cycles 한 번에, Maya 사용자가 보는 기본 조명·카메라 그대로 | 사람들이 Blender로 오는 이유를 첫 시간에 맛보게 함 | M | Maya 렌더 흉내로 다시 흐를 위험 → "Blender 결과"를 목표로 | first hour render 행 OK, 설문 | `operators/default_light.py`, `ui/render_settings.py`, #123 |
| **B9** | 범위 줄이기·내구성 | 동결 목록 확정, 5.x 출시일 테스트, 다른 애드온과 함께 켜기 테스트(#79 유형) | 업데이트마다 고장(경쟁품 1위 불만)을 피함 | M | 기능을 줄이면 일부 사용자 실망 | 새 Blender 출시일 실패 0, #79 유형 0 | `compat.py`, `ui/render_settings.py:356-453` |
| **B10** | 스튜디오 도입 키트 | 사내 배포 문서, 버전 고정, 설정 프리셋 공유, 일본 스튜디오 발표(CGWORLD/ACTF 류) | P3 확보 → 한 번에 수십 명 | XL | 혼자 유지하는 무료 GPL로 지원 약속 불가 | 도입 문의 수 | `docs/DISTRIBUTION.md` |
| **B11** | 3ds Max 사용자판 | 같은 엔진으로 "Workflow Kit for 3ds Max users" | 일본에서 실제 이동하는 집단(애니메 스튜디오)과 맞음 | XL | 초점 분산, 두 제품 유지, 상표 문제 그대로 | 설문 H7 | 키맵·마킹 엔진 재사용 가능 [추정] |

권장 순서 [delegated]: **B1 → B2 → B3 (이번 주) → 2주 설문 → B4 (+B7 일부) → 설문 결과로 B5/B6/B8 중 선택 → B9는 계속.** B10·B11은 6개월 안에는 하지 않음, 신호만 기록.

## ⑦ 사용자 결정이 필요한 질문

1. **1차 대상** — (a) P1+P2: 경력자, 개인·프리랜스에서 Blender 【권장】 (b) P2 중 애니메이터만 (c) P3 스튜디오 도입 (d) P4 학생·졸업생
2. **일본** — (a) 일본어 입구만 (README_ja·스토어·환영 창) 【권장】 (b) 전체 UI 번역 (c) 영어만 유지, 일본어는 게시 글만
3. **애니메이터 신뢰 작업(B4: 리그 FBX 왕복, Y-up 안내)을 다음 단계 1순위로?** — (a) 예 【권장】 (b) 설문 결과 뒤 (c) 아니오, 모델링 흐름 먼저
4. **3ds Max 판 요청** — (a) 안 함, 기록만 【권장】 (b) 6개월 뒤 검토 (c) 지금 별도 제품 계획
5. **태그라인** — (a) "Your Maya hands, Blender's engines" (b) "Work the Maya way in Blender, switch back anytime" 【권장: 스위치가 1위 장점】 (c) 현행 유지
6. **피드백 경로** — (a) Google Forms 설문 + GitHub 이슈, 앱 Help 메뉴 링크 【권장】 (b) GitHub Discussions만 (c) Discord 서버 개설 (운영 부담 큼)
7. **설문 결과가 올 때까지 새 Maya 편집기·메뉴 깊이 작업을 멈출까?** — (a) 멈춤, 고장·first hour만 【권장】 (b) 동결 목록 밖은 계속 (c) 계속
