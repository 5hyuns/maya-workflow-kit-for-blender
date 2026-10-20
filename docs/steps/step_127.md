# Step 127 — 제품 사이트 (GitHub Pages), impeccable 스킬로 (사용자 지시 2026-10-20)

사용자 지시: 「github.io 같은 사이트도 만들어줘, impeccable 스킬 사용해서」. 저장소 https://github.com/5hyuns/maya-workflow-kit-for-blender
(비공개, origin 설정됨). push 하지 않음 (Hermes 가 확인 후).

## 계획 (impeccable 흐름, delegated)

- `impeccable context --target site/index.html` → PRODUCT.md 없음 → 사용자가 모든 결정을 위임했으므로 init 인터뷰 대신 저장소 문서
  (listing.md · naming.md · user_decisions 12 · style.md · copy.md) 에서 추론해 `site/PRODUCT.md` 작성, 추론한 것은 [assumed] 표시.
- 시각 세계는 이미 있음 (step 124/125 style.md: Maya 회색 · Maya 로고 틸 · Hello Yellow · Inter · 잠금업) → new-work.md 「확립된 세계 안의
  새 화면」: 구조 후보 7 개 (Maya 창 자체 / 핫박스 내비게이션 / 단축키 페이지 / Maya | Blender 전후 / **셸프 탭 색인** / 문서형 / AE 접이식)
  → `concept-seed --scope surface --mode persuade` (seed 4d21a296, 5·3·2 배정, 5 가 선두) → 무인 실행이라 배정된 5 = 셸프 탭 색인.
  이미지 생성 도구 없음 → code-led. 방향 계약 = `site/.impeccable/surfaces/index-html.md`.
- 병렬: 웹용 미디어 재인코딩 = 서브에이전트 (site/media 만), 페이지 = 메인, 마무리 리뷰 = impeccable-finish-reviewer (새 컨텍스트).

## 한 것

- `site/index.html` · `styles.css` · `app.js` (빌드 도구 없음): 첫 화면 = 잠금업 + 태그라인 + 노랑 「Download the zip」 + 오른쪽 Maya 창
  조각 (셸프 탭 6 개 = 워크플로우 6 묶음, 킷 셸프 아이콘 줄, 뷰포트 = 클립, 오른쪽 Channel Box 열 = 그 워크플로우의 사실 + 크레딧).
  탭 = 클릭 / 화살표 / 1–6, 클립은 화면에 보일 때만 재생 (preload none, muted loop playsinline, reduced-motion 이면 포스터).
  그다음 Maya | Blender 전환 (같은 장면 스크린샷 두 장), 트레일러, 설치 (Maya 옵션 창 틀), 한계 (C++ 벽), FAQ (AE 프레임), 마무리, 푸터
  (GPL, GitHub, 미디어 크레딧, Autodesk 상표 · 비제휴 고지).
- `site/media/` (31 파일): 클립 1280 px MP4 ≤ 1.2 MB + VP9 WebM, 동작 중간 포스터, 1600/800 스틸, og 이미지, 파비콘 — `tools/site/make_media.py`.
  클립은 1920×1080 캔버스에 창이 (144, 22, 1632×918) 로 들어간 홍보 클립이라 CSS 로 창 부분만 보이게 자름 (페이지가 자막을 따로 둠).
- 폰트: Inter 가변 woff2 를 라틴 범위로 줄임 (57 KB, OFL, `site/fonts/Inter-LICENSE.txt`).
- `.github/workflows/pages.yml` (configure-pages + upload-pages-artifact + deploy-pages, `site/` 의 공개 파일만 — `.impeccable`, md 제외).
  비공개 저장소면 실패할 수 있음 (단계 실패 아님). README 에 사이트 링크 자리.
- `tools/site/check_site.py`: 로컬 링크 · 미디어 경로 존재 + 페이지 무게.

## 검증

- 캡처 두 번 (impeccable: 고치고 한 번 더): Playwright 1440 데스크톱 · 390 모바일 전체 페이지, 콘솔 오류 0, 실패 요청 0. 첫 판 지적
  (숨긴 img 가 빈 상자로 보임, 클립 안 이중 프레임, 긴 탭) 고침.
- impeccable detect 1 회: 20 → 11 (남은 것 = 브랜드가 정한 Inter, 구조상 오탐 cramped-padding / h1 크기, 프레임 그림자).
- finish reviewer (새 에이전트): disposition fix, 8 건 → 한 번에 고침 (포스터를 동작 중간 프레임으로, 잠금업 0.66 ×, 트레일러 포스터 고지 띠 제거 +
  크레딧을 미디어 옆에, 아래쪽에도 Maya 크롬 (옵션 창 · AE 프레임 · 점선), 셸프 아이콘 줄, 왼쪽 정렬 한 줄, 히어로 아래 빈 띠, 문구 2) → 판정: 아래.
- `check_site.py`: 로컬 경로 34 개 전부 존재, 첫 화면 210 KiB (HTML·CSS·JS·폰트·포스터), 전부 17.3 MiB (영상은 보일 때 / 재생할 때만).
- 판정 (finish reviewer, 2 라운드 = 무인 실행 예산): 1 차 fix 8 건 → 2 차 verdict: 해결 4 (잠금업 0.66, 트레일러 포스터·크레딧, 아래쪽 Maya 크롬,
  왼쪽 정렬·빈 띠·모바일 메뉴), 부분 3 → 메인이 마무리: 다른 탭 포스터 4 장은 탭별 캡처 6 장으로 직접 확인 (전부 동작 중간 프레임, 새 문구
  「MMB drag in the view」 보임), 셸프 아이콘 줄은 클립 속 진짜 셸프와 겹쳐 제거 + 탭 글자 12.5 px, 회귀 b (제목 위계) → h2 26–38 px · 마무리
  26–40 px 로 이름 (36–56 px) 이 앞서게. 회귀 a (히어로 이중 잘림) 는 오판으로 봄: 클립 자체의 가상 카메라 줌 (step 124) 이고 CSS 는 창
  영역 (고정) 만 자름 — 남은 것에 기록.
- `impeccable embed-prompt --scan site/media`: 래스터 25 개 출처 기록 0 누락. DESIGN.md + `.impeccable/design.json` = impeccable-documenter
  (코드에서 도출, style.md 와의 차이 기록: 회색 글자 #9a9a9a, 노랑 = 누름 + 포커스, 모서리 3–6 px).

## 남은 것

- push 안 함 (Hermes 확인 후). 저장소가 비공개면 Pages 가 안 될 수 있음 — 공개 후 Settings › Pages › Source = GitHub Actions.
- 히어로 클립은 홍보 클립 그대로 (카메라 줌 포함) — 사이트 전용으로 줌 없는 녹화를 따로 만들면 셸프 · 뷰포트 은유가 더 또렷함.
- 한국어 페이지 (선택) 안 함. 스토어 링크 자리표시 (listing 공개 후 채우기).
- manual_checks: 실제 브라우저에서 탭 전환 · 클립 재생 · 모바일 스크롤 메뉴 확인.
