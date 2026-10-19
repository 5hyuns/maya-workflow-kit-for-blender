# Step 122 — 마케팅 카피 · 키 비주얼 · 설명 문구 넣은 스크린샷 (사용자 요청 2026-10-19)

사용자 요청 요지: 「Git이나 Blender 애드온에 올릴 때 쓸 시청각 자료 — 짧은 GIF 클립과 스크린샷(제품 특징이 영어로 적힌), 제품 대표 이미지,
마케팅 자료」. 이번 단계 = 카피, 디자인 기준, 기능별 캡션 스크린샷 10 장, 키 비주얼 (16:9 + 정사각) + 아이콘, extensions 미디어 교체.
클립·GIF 는 step 123. 기준: `docs/distribution/marketing/references.md` §5–§6 (step 121).

## 계획

1. 카피: copy-masters (ad-copy-agency-skill) 를 영어 / 미국 / 브랜드 / 랜딩페이지로 끝까지 — 원자료 수집 → 플래너 → CD 서저리 →
   팀 셋 차례 → CD 1차 → 재작업·변론 → CD 2차 → 광고주 (사실·규제 검수) → assemble. 특징 제목·한 줄·소개문·해시태그는 스킬 밖
   (스킬은 헤드라인만) — listing.md B 의 구현된 기능만 근거로 직접 씀.
2. 디자인: Claude Design 은 연결 실패 (FIRST_PARTY_AUTH_REJECTED) → ui-ux-pro-max design-system 스킬의 3 층 토큰 (primitive →
   semantic → component) 으로 `tools/marketing/style.json` + `style.md`. 색 = 킷 Maya 회색 + 강조 하나, 글꼴 Inter (OFL).
3. 자산: 사용자 규칙 (외부 명확한 라이선스, NC/ND 금지, 로그인 없는 직접 다운로드, 기능별 맞는 모델) → 일반 서브에이전트가
   찾고 받고 Blender 4.5 에서 import 확인·미리보기, `tools/marketing/assets.json` + `fetch_assets.py` (sha256).
4. 장면·촬영: `tools/marketing/shots.py` (GUI Blender, 깨끗한 샌드박스, 이벤트 시뮬레이션, 1920 × 1080 창, Maya 테마 + Maya
   기본 배경, Material Preview — 월드 숨김) 가 10 장면 + 히어로 + 설치 전 화면을 찍고 UI 사각형을 meta.json 에. 중단된 10-19 stash 는
   장면 레시피만 참고.
5. 합성: `tools/marketing/compose.py` (Pillow 만): 제목 띠 + 85 % 화면 + 콜아웃, 키 비주얼 (기울인 실제 화면 두 장), 정사각,
   아이콘. 모든 이미지를 직접 보고 고침.
6. extensions 미디어 교체 (`tools/make_listing_media.py` = 마케팅 파이프라인 + 복사), listing.md C, CREDITS.md.

## 한 것

- **카피** (`docs/distribution/marketing/copy.md`): copy-masters 실행 (`research/copy-runs/allset/2026-10-20-allset-listing/`, 추적 안 함):
  원자료 F47 / V48 / C34 → 재정의 (문제 종류 바꾸기: Maya 사용자는 정보가 모자란 게 아니라 Maya 설정이 Blender 를 끊을까 두려움 —
  튜토리얼 키가 안 맞음) → 단일 제안 「Work the Maya way in Blender today, and get plain Blender back in one click」 → 99 줄 → CD 1차
  15 → 재작업 40 + 변론 3 → CD 2차 5 → 광고주. **최종 「The tutorial ends. Your Channel Box comes back.」**, 대안 「"Just use the default
  keymap." One click away.」 「Your first cube is called pCube1.」. 광고주 검수가 1 줄 ("You installed it. Blender didn't notice." — 설치
  시 스위치·메뉴·단축키·환영 창이 생기므로 사실 아님) 을 뺌. 과정 점검 45 / 45. 태그라인은 결정 12 그대로. 특징 10 개 (제목 ≤ 6 단어 +
  한 줄 ≤ 12 단어, listing.md B 근거 표), 스토어 캡션 10 개 (≤ 255 자), 짧은 / 긴 소개문, 해시태그, 크레딧 줄, 상표 고지문.
- **디자인** (`style.md`, `tools/marketing/style.json`): 회색 #1e1e1e – #eeeeee (Maya 2022 Qt 팔레트·킷 테마) + 강조 amber #ffb547
  (`delegated`: 화면 속 UI 상태색 — 흰 선택, 리드 초록, 하이라이트 파랑 — 과 겹치지 않는 따뜻한 색), Inter, 1920 × 1080 격자 (여백
  144, 제목 띠 162, 화면 1632 × 918), 콜아웃 (4 px 상자 + 알약 라벨 + 화살표, 화면당 ≤ 2), 키 비주얼 / 정사각 / 아이콘 규칙. 대비 계산
  amber/#252525 8.7:1, #1e1e1e/amber 9.5:1, #c8c8c8/#252525 9.2:1.
- **자산** (`CREDITS.md`, `tools/marketing/assets.json`, `fetch_assets.py`): 모두 CC0 (+ Inter OFL) — Kenney Animated Characters
  Protagonists (스킨 58 본 캐릭터), Quaternius RobotExpressive (걷기 등 14 액션), Poly Haven Drill / Wooden Table / Metal Toolbox /
  Barrel / Cardboard Box / Potted Plant (+ Desk Lamp Arm, 123 용). 거절: 브랜드 로고 있는 텍스처 (Camera 01, Television 01), 조잡한
  모델, 라이선스가 엇갈리는 Quaternius 팩, Sketchfab / Mixamo / 3D Warehouse. 파일은 `research/marketing_assets/` (추적 안 함).
- **촬영** (`tools/marketing/shots.py`): 장면 = 작업대 + 드릴 + 소품, 캐릭터 둘. 기능별 모델 — 드릴 = 컴포넌트 선택 / Modeling
  Toolkit / 피벗 / Channel Box 키, 스킨 캐릭터 = 마킹 메뉴 / 메뉴셋 / 스킨 가중치, 걷는 로봇 = Time Slider + Graph Editor, 장면 전체 =
  핫박스·히어로. 고친 것: glTF 쿼터니언 → Rotate X/Y/Z (Channel Box 가 Maya 처럼), import 빈 객체 숨김, 뼈는 리깅 장면만 (도움 뼈
  숨김), 스킨 가중치는 그라데이션이 보이는 Spine, 로봇 걷기 범위 = 장면·재생 범위, Kenney FBX 의 스킨 텍스처 연결 (파일은 그대로),
  나눈 3D View 의 Asset Shelf 머리줄 (29 px, 이전 화면이 남아 그려짐) 숨김.
- **합성** (`tools/marketing/compose.py`): `docs/distribution/marketing/screens/01–10_*.png`, `key_visual.png`, `key_visual_square.png`,
  `icon_256.png` (새 아이콘: 둥근 타일에 방사형 마킹 메뉴, 강조 항목 하나 — 이전 큐브 와이어 3 개 대신).
- **extensions 미디어**: `docs/distribution/media/` = icon.png, featured.png (키 비주얼), 01–10 (1920 × 1080). 옛 1600 × 900 6 장 삭제.
  `tools/make_listing_media.py` 가 마케팅 파이프라인을 부르고 복사. listing.md A (미리보기 행) · C (규칙, 파일·캡션 표, 123 뒤의 갤러리 구성).
- `CLAUDE.md`: Testing 명령 + 마케팅 메모 한 줄.

## 검증

- 모든 이미지를 직접 봄 (매 실행마다): 글자 잘림 없음, 콜아웃 위치, 대비, Maya 기본 배경 #5c5c5c 의 뷰포트, Blender 로고 칠함.
  고친 것 (첫 실행 → 마지막): 뼈·빈 객체가 장면을 가림, 쿼터니언 채널, 식물과 로봇 겹침, 드릴이 너무 작음, 다리 가중치 → Spine,
  로봇 너무 가까움, 키 비주얼 문구와 화면 겹침, 정사각 하단 글자와 화면 겹침, 셸프 콜아웃 화살표 길이, 옵션 박스 콜아웃 추가,
  Modeling Toolkit 장면이 Rigging 메뉴셋, 애니메이션 장면 아래의 잔상 띠 (영역 목록을 덤프해 Asset Shelf 머리줄로 확인).
- 촬영 세션 검사 6 / 6 PASS (환영 창, 템플릿, Maya 키맵, 장면, 스킨 가중치 페인트, Graph Editor 분할).
- `fetch_assets.py`: 전 자산 sha256 일치 ("all assets verified").
- 헤드리스 (배포 문서·자산 관련) step114 / step117 / step61 / step13: 11 / 11. `src/` 변경 없음 → GUI 전체 묶음은 돌리지 않음.

## 남은 것

- 클립·트레일러·GIF·키트: step 123 (references.md §6, copy.md 캡션).
- 킷 쪽 작은 것 (이번 단계에서 고치지 않음): 환영 창 본문이 1920 × 1080 / 125 % 에서 「the Maya colou…」 로 잘림, 리깅·애니메이션 장면
  에서 카메라 이름 「persp」 가 두 번 그려짐.
- 애니메이션 장면 Channel Box 는 본의 쿼터니언 회전을 보여 줌 (액션이 쿼터니언 F-curve 라 Euler 로 바꾸지 않음).
- 서브에이전트가 남긴 것: 빈 폴더 `C:\previews` (안전 장치가 삭제를 막음 — 사용자가 지우면 됨), Git Bash `/tmp/ph_drill_01_bak`
  (재다운로드 시험용 사본).
