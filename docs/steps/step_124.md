# Step 124 — 홍보 디자인 재작업: impeccable 감수 · Maya 포인트 컬러 · 로고 비율 · 영상 움직임 (사용자 피드백 2026-10-20)

사용자 피드백 요지: impeccable 로 디자인 감수, Maya 임을 알 수 있게 Maya 포인트 컬러 (Blender 주황 X) — 10:40 재지시: Maya 로고색 ·
Autodesk 색 조합, 근거 (설치본 픽셀 + Autodesk 공개 브랜드 가이드) 와 상표 메모·대체 팔레트; 영상 배속 + 화면 안 움직임; 「Allset」 이
「for Maya Users」 보다 너무 큼. 알려진 버그 (persp 두 번, 환영 창 잘림) 수정.

## 계획 (delegated)

- 감수 → 반영 순서. 감수는 impeccable `critique` 를 규칙대로 두 서브에이전트 (A 디자인 리뷰 = HEAD 결과물만 봄, B 검출기 + 기계 측정) 로
  돌리고 합성 → `docs/distribution/marketing/design_review.md`. 반영 = colorize (팔레트) · typeset (잠금업) · animate (영상) · layout /
  polish (콜아웃·버그). 질문 단계는 사용자 위임으로 생략 (문서에 기록).
- 색: Maya 2022 설치본 아이콘 (`icons/MayaEDUStartupImage.png`, `mayaico.png`, `hsMaya.png`, `bin/maya.exe` 아이콘) 픽셀 값만 측정 →
  hue 180° 틸. Autodesk 브랜드 페이지에서 Hello Yellow / Black. 틸 = 주 강조, Hello Yellow = 동작 순간 (클릭·키·CTA) 만, 검정 = 강조 위
  글자. 대체 팔레트 `maya-ui` (Maya UI 파랑 계열 + 리드 초록) 를 같은 토큰 구조로 (`ALLSET_MARKETING_PALETTE`).
- 잠금업: `compose.lockup()` 한 함수 = 모든 형식. for 줄 = 0.66 × 이름 크기 (요청 60–75 % 안), 두 줄 (한 왼쪽 선) / 한 줄 (한 기준선).
- 영상: 녹화 다시 안 함 (리깅만 버그 때문에 재녹화) — 합성 단계 (`clip_compose.py`) 에서 속도 1.35 ×, 가상 카메라 (전체 해상도 창 그림에서
  잘라 확대), 칩 팝·노랑 플래시·커서 옆 칩, 클릭 펄스, 캡션 슬라이드, 클립 인트로/아웃트로, 트레일러 움직이는 타이틀 카드 (첫 프레임 =
  키 비주얼 = 스토어 포스터) · 푸시/줌 전환 · 움직이는 엔드 카드. 정적 2 초 이상이면 스크립트가 FAIL. GIF ≤ 4 MB 까지 fps/폭/색 단계.
- 병렬: 감수 A · B, 영상 합성 = 서브에이전트 (파일 소유 분리: 영상 에이전트 = `clip_compose.py` + content.json clips/trailer), 메인 =
  팔레트·잠금업·정지 이미지·src 버그·문서·검증·커밋.

## 한 것

- **감수** (`design_review.md`, `.impeccable/critique/` 스냅샷은 추적 안 함): 22 / 32 (7·10 n/a), P1 세 개 = 주황 accent, 잠금업 2.7–3.0 ×,
  정적인 영상 (클립 81–98 % 프레임 거의 정지, 트레일러 처음 2.7 s · 끝 3.7 s 정지); P2 = persp 두 번 · 환영 창 잘림 · 썸네일 핫박스 가독성.
  검출기는 마크업이 없어 아무것도 검사하지 않음 (양성 대조로 확인).
- **색** (`style.json` `palettes`, `style.md` 「Colour」): accent #00bcbb / #149b9a / #008b8d (Maya 아이콘 픽셀), highlight #ffff00 ·
  ink #000000 (brand.autodesk.com/brand-system/color). 대비 재계산 (틸 on #252525 6.50, 검정 on 틸 8.91, 검정 on 노랑 19.56, 틸 on 뷰포트
  2.84 → 콜아웃 2 px 검정 테두리), ΔE00 (틸 vs Blender 주황 49.7, 옛 amber 15.5). 상표 메모 + 대체 팔레트.
- **잠금업**: 키 비주얼·정사각·키트 6 장·띠 브랜드·YouTube·Reddit·클립 띠·엔드 카드 모두 `lockup()`. Reddit before/after 는 Maya 쪽만
  틸 (틀 + 채운 알약), Blender 쪽은 회색 테두리 알약.
- **영상** (`clip_compose.py`, 서브에이전트 구현 + 메인 마무리): 위 계획 그대로; 엔드 카드 노랑 글로우가 틸과 섞여 올리브색이 되던 것 →
  작은 후광으로. 트레일러 33.5 s (30–45 안), 캡션 "Allset in half a minute" (listing / copy / content 반영).
- **버그 (킷)**: `ui/view_furniture.py` — 포즈/페인트 모드의 에셋 셸프 헤더 띠 (29 px) 가 Region Overlap 꺼짐 (Maya 모드, step 112) 에서
  그려지지 않고 이전 픽셀 (카메라 라벨) 을 남김 → 셸프가 접혀 있을 때 띠를 숨기고 (`screen.region_toggle`, 타이머) 셸프를 열거나 해제할
  때 되돌림. `welcome.py` — 고정 줄 대신 blf 로 잰 폭으로 줄바꿈, 아이콘 열은 split 비율로.
- **정지 이미지**: 전부 재촬영 + 재합성 (`make_marketing.py`), 콜아웃 `at` (화살표 위치) 추가 — 07 Time Slider 화살표가 persp 라벨을 덮던
  것, 10 스위치 라벨이 Outliner Cube 행을 덮던 것 정리. `docs/distribution/media/` 갱신.
- 문서: `style.md` (색 근거·상표·대비·잠금업·모션), `README.md` (표·모션·CTA), `listing.md` C, `posts.md`, `README_marketing.md`, `copy.md`.

## 검증

- 헤드리스 890/890 (`tests/run.py`, 새 `test_step124_chrome` 2 개 포함).
- GUI `gui_step124_persp_label` + `gui_step124_welcome` 7/7 (스크린샷 직접 확인: 라벨 한 번, 환영 창 본문 7 줄 554/555 px). GUI 전체 1142/1142 (92 파일).
- `clip_compose.py` 전부 PASS: 클립 5.6–7.6 s, 2.0–3.92 MB (≤ 8), 가장 긴 정적 구간 0.07–1.13 s; GIF 0.54–3.97 MB (≤ 4, 04_navigation
  4.68 → 3.47), 정적 ≤ 1.93 s; 트레일러 33.5 s 11.59 MB (≤ 20), 정적 0.7 s; 트레일러 첫 프레임 vs 키 비주얼 평균 차 1.2–1.6 / 255 (압축).
- 직접 본 것: 트레일러 1 fps 타일 (36 컷), 클립별 2.5 fps 타일, 핫박스 3 s · 리깅 4.2 s · 엔드 카드 프레임 원본 크기, 정지 이미지 07 / 08 /
  10, 키트 시트 (8 장). 재녹화한 리깅 클립에서 「front +Y」 라벨 한 번.

## 남은 것

- `design_review.md` 「Left」: 03 캡션 "keyed channels in red" vs AE 초록 필드 (킷 색 문제), 07 쿼터니언 행·Graph Editor 「Blender」 메뉴,
  썸네일 크기 핫박스 가독성, 05/09 같은 드릴 프레임, 키 비주얼 뒤 창 기울기, 06 Bake Pivot Orientation 잘림.
- `fetch_assets.py` 가 매번 Inter zip 을 다시 풀어, 다른 합성이 폰트를 연 채 돌면 Windows 에서 쓰기 실패 (순서대로 돌리면 문제 없음).
- 대체 팔레트 `maya-ui` 로 실제 재생성은 하지 않음 (스위치만 확인).
- manual_checks 「Step 124」: 스토어 미리보기에서 첫 프레임·자동 재생 확인, GitHub README 에서 GIF 재생 확인.
