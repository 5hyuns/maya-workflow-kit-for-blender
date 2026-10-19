# Step 123 — 짧은 영상 클립 · GIF · 소개 영상 · 마케팅 키트 (사용자 요청 2026-10-19)

사용자 요청 요지: 한 기능씩 짧은 클립 (MP4 + GIF, 아래 영어 캡션 띠, 키 입력 표시, 마우스 커서), 30–45 초 소개 영상 (제목 / 끝 카드,
음악 없음), 마케팅 키트 (GitHub 히어로 + 1280 × 640 소셜 프리뷰, README GIF 배치 초안, X 카드 1600 × 900, Reddit 이미지, YouTube 썸네일
1280 × 720, 게시글 초안 + 플랫폼 규칙 메모, 결과물 표). 정정: extensions.blender.org 갤러리는 MP4 를 받으므로 스토어용 MP4 클립도 만들고,
GIF 는 GitHub README · SNS · 외부 링크용. 기준 = `docs/distribution/marketing/references.md` §5–§6, `copy.md`, `style.md`.

## 계획

### 녹화 방식 (delegated)

- **화면 녹화 (OS 캡처, ffmpeg gdigrab) 는 쓰지 않음**: 이벤트 시뮬레이션은 OS 커서를 움직이지 않고, 사용자 화면의 다른 창이 겹치면
  찍히며, 사용자가 PC 를 쓰는 동안 돌릴 수 없다. → **틱마다 `screen.screenshot`** (Blender 자기 프레임버퍼) + 커서·키·캡션을 Pillow
  로 그려 넣는다. 결정적이고, 다시 만들 때 같은 결과.
- 시간은 **가상 시간**: 틱 k 에서 먼저 찍고 (= 틱 k−1 의 이벤트 결과, `screen.screenshot` 은 앞 프레임) 그다음 행동 A_k 를 보낸다.
  찍은 그림 I_k 는 「A_k 가 일어나는 동안 보이는 화면」이므로 A_k 의 길이 (dur) 와 커서 경로 (A_k 전 위치 → 후 위치) 를 I_k 에 붙인다.
  메뉴가 열리는 데 틱이 더 필요하면 dur 0 의 대기 틱 (그림 버림). 드래그는 틱마다 MOUSEMOVE 하나 (step 95: 한 틱에 몰아 보내면
  스냅이 첫 위치에 머문다).
- 커서: OS 커서가 없으므로 킷이 그린 화살표 (흰 채움 + 검은 테두리) 를 이벤트 위치에 그림. 클릭 = amber 원 퍼짐, 누른 채 = 작은 링.
- 로고: 촬영 그림의 Blender 메뉴 아이콘을 합성 단계에서 바 색으로 칠함 (step 122 `hide_logo` 와 같은 사각형, 프레임마다 Blender 에서
  다시 저장하지 않음).
- 한 클립 = 한 Blender 프로세스 (`ALLSET_CLIP=<name>`): 장면 상태가 섞이지 않고, 실패한 클립만 다시 찍는다. 순서대로 (병렬 X — 같은
  샌드박스, 창 겹침).

### 클립 (7 개, 각 6–10 초 — 사용자 4–10 초와 references 6–15 초를 둘 다 만족, delegated)

| # | 이름 | 모델 (기능에 맞는 모델) | 흐름 |
|---|---|---|---|
| 1 | hotbox | 작업대 장면 전체 | Space 탭 = 패널 최대화 / 복원, Space 누른 채 = 핫박스 → Select 메뉴 → All |
| 2 | marking_menu | Kenney 캐릭터 (스킨) | 캐릭터 위 RMB 누른 채 → 마킹 메뉴 → Vertex 로 끌기 (컴포넌트 모드) → RMB → Object Mode |
| 3 | channel_box_keys | Poly Haven Drill | S = 모든 채널 키 (빨강), Time Slider 클릭 → Rotate Z 칸에 +=90, RMB › Key Selected, Time Slider 끌기 |
| 4 | navigation | 작업대 장면 | Alt+LMB 회전, Alt+MMB 이동, Alt+RMB 줌, 드릴 클릭 + F 프레임, A 전체 |
| 5 | pivot_snap | Poly Haven Drill | Insert = 피벗 편집, V 누른 채 피벗을 드릴 끝 꼭짓점에 스냅, Insert, E 회전 = 새 피벗 기준 |
| 6 | rigging | Kenney 캐릭터 (리그 떼고 메시만) | Rigging 셸프 Create Joints → 가슴·어깨·팔꿈치·손목 클릭, Enter → IK Handle (어깨 → 손목) → Bind Skin → IK 핸들 끌기 → Paint Skin Weights |
| 7 | switch | 작업대 장면 | Maya 레이아웃에서 상단 스위치 「Blender」 클릭 → Blender 기본 UI (장면 그대로) → 「Maya」 클릭 → 돌아옴 |

### 화면 구성 (style.md 를 따름)

- 1920 × 1080 캔버스 (#252525 → #1e1e1e), 촬영 화면 85 % (1632 × 918, 모서리 10, 그림자) 를 위에 붙이고 **아래 캡션 띠** (138 px):
  왼쪽 amber 틱 + 클립 제목 (Inter SemiBold) + 지금 하는 일 한 줄 (Regular), 오른쪽 키 칩 (amber 알약, 예 「Space (hold)」
  「Alt + LMB drag」), 오른쪽 아래 「Allset for Maya Users」 (muted). 첫 1 초부터 제목이 보임 (references §5.2 lower-third).
- MP4: H.264, yuv420p, 30 fps, 1920 × 1080, `+faststart`, 소리 없음, 클립 ≤ 8 MB, 트레일러 ≤ 20 MB.
- GIF: 960 px 폭, 15 fps, 팔레트 최적화 (palettegen stats_mode=diff + paletteuse), ≤ 5 MB (넘으면 fps / 색 수 낮춤).
- 트레일러 (30–45 초): 제목 카드 (첫 프레임 = 스토어 포스터: 이름 · 태그라인 · 다운로드 자리표시) → 클립마다 4–5 초 구간 → 끝 카드.
  음악 없음.

### 키트

- `tools/marketing/kit.py` (Pillow): GitHub 히어로 (README 상단 배너) + 소셜 프리뷰 1280 × 640, X 카드 1600 × 900, Reddit 1920 × 1080 +
  1080 × 1080, YouTube 썸네일 1280 × 720 — step 122 촬영 그림 (tmp/marketing/raw) 과 클립 프레임 재사용.
- `README_marketing.md` (README GIF 배치 초안), `posts.md` (r/blender · r/Maya · X · BlenderArtists · 80.lv, 플랫폼 규칙 메모 —
  `research/marketing_refs/platform_rules_123.md` 조사), `README.md` (결과물 · 용도 · 크기 · 용량 표, GIF 는 extensions 에 안 올림).

### 코드

- `tools/marketing/scene.py` (새, Blender 안): step 122 `shots.py` 의 장면 도우미 (import / place / shading / frame …) 를 옮김 — shots.py 와
  clips.py 가 같이 씀.
- `tools/marketing/clips.py` (Blender 안): 녹화기 + 클립 7 개. `tmp/marketing/clips/<name>/f####.png` + `timeline.json`.
- `tools/marketing/make_clips.py` (호스트): 빌드 · 샌드박스 설치 · 클립마다 GUI Blender · 합성 (`clip_compose.py`) · ffmpeg (MP4 / GIF /
  트레일러) · 크기 검사.

## 한 것

- **녹화기** (`tools/marketing/clips.py`, Blender 안): 계획대로 틱마다 찍고 행동 — `beat / move / click / press / release / key /
  drag / type_text / hold / settle`, `timeline.json` (그림마다 길이, 커서 경로, 캡션, 키 칩, 클릭, 누른 버튼). 클립마다 따로 Blender
  (`tools/marketing/make_clips.py`: 빌드 → 깨끗한 샌드박스 `tmp/marketing_env` 설치 → 클립 7 번 실행, 시간 초과 때 그 PID 만 종료).
  클립마다 끝에 실제 결과를 검사 (예: Key Selected 가 Rotate Z 만 36 프레임에 키, V 스냅 피벗이 드릴 꼭짓점 위, Bind Skin 모디파이어,
  Maya 모드 복귀).
- **클립 7 개** (모두 6.1 – 8.9 초): 01 hotbox (Space 탭 → 4 뷰 → persp 위 탭, 누른 채 핫박스 → Select › All), 02 marking menu
  (캐릭터 위 RMB → Vertex → RMB → Object Mode), 03 Channel Box keys (S → Time Slider 36 → Rotate Z `+=90` → RMB › Key Selected →
  Time Slider 끌기), 04 navigation (Alt+LMB/MMB/RMB, 드릴 클릭 + F, A), 05 pivot snap (Insert → V 누른 채 피벗을 드릴 앞 꼭짓점에 →
  Insert → E 회전), 06 rigging (Rigging 셸프: Create Joints 4 클릭 → IK Handle 어깨→손목 → Bind Skin → IK 핸들 끌어 팔 굽힘 → Paint
  Skin Weights), 07 switch (상단 스위치 Blender → 같은 장면의 Blender 기본 UI → Maya). 모델: 작업대·드릴 (Poly Haven), Kenney
  캐릭터 (리깅 클립은 스켈레톤·가중치를 장면에서 떼고 메시만), RobotExpressive.
- **합성 · 인코딩** (`tools/marketing/clip_compose.py`): 85 % 화면 + 아래 캡션 띠 (amber 틱, 제목 Inter SemiBold 40, 지금 하는 일
  Regular 28, 오른쪽 키 칩 amber 알약, 「Allset for Maya Users」), 킷이 그린 커서·클릭 원·누름 링, Blender 로고 칠함. raw 프레임을
  ffmpeg 로 파이프: MP4 = libx264 High, crf 20, yuv420p, 30 fps, `+faststart`, 소리 없음; GIF = 960 px 15 fps, 클립별 팔레트
  (`palettegen stats_mode=diff` + `paletteuse sierra2_4a`, 5 MB 넘으면 12 / 10 fps 로 다시). 트레일러 = 키 비주얼 제목 카드 3 초
  (첫 프레임 = 스토어 포스터) → 클립마다 4.6 – 5.6 초 구간 → 끝 카드 4 초 (아이콘, 이름, 최종 헤드라인, 「Free and open source ·
  Blender 4.5 – 5.2」, 다운로드 자리표시), 8 프레임 크로스페이드, 음악 없음 (`delegated`).
- **키트** (`tools/marketing/kit.py` → `docs/distribution/marketing/kit/`): README 히어로 1920 × 720, GitHub 소셜 프리뷰 1280 × 640,
  X 카드 1600 × 900, Reddit 이미지 (Maya 모드 | Blender 모드 나란히, 스위치 클립 프레임) 1920 × 1080 + 정사각 1080 × 1080, YouTube
  썸네일 1280 × 720 (「Blender, the Maya way.」 + 핫박스 크게).
- **글**: `docs/distribution/marketing/README.md` (결과물 · 용도 · 크기 · 용량 표, GIF 는 extensions.blender.org 에 안 올림, 다시 만드는
  명령, 자리표시), `README_marketing.md` (README 상단 초안: 히어로, 헤드라인, GIF 2 열 표, 스위치 GIF 전체 폭), `posts.md` (r/blender,
  r/Maya, X, BlenderArtists, 80.lv 메일 — 영어, 플랫폼 규칙 메모: 서브에이전트 조사 `research/marketing_refs/platform_rules_123.md`,
  Reddit 은 페이지가 막혀 검색 결과 문구), `copy.md` 「Clips」 절, `CREDITS.md` (클립에서 바꾼 것, Desk Lamp 안 씀), `listing.md`
  A·C (갤러리 10 = 트레일러 + 클립 7 + 정지 2 (`03`, `04`), 캡션 전부 ≤ 255 자 — `delegated`: 요청이 주제 7 개라 클립 7, 대신 정지 `10`
  을 뺌).
- 장면 도우미를 `tools/marketing/scene.py` 로 옮김 (shots.py 와 clips.py 가 같이 씀).
- `CLAUDE.md`: 명령 한 줄 + step 123 메모 (가상 시간 녹화, 같은 틱 press/release 로 핫박스 메뉴가 바로 닫힘, 팝업 메뉴는 기억한 행을
  마우스 아래에).

### 결정 (`delegated`)

- OS 화면 녹화 대신 틱마다 `screen.screenshot` + 그린 커서 (계획 참고). 1920 × 1080 (요청의 두 크기 중 스토어 기준과 같은 쪽).
- 클립 길이 6 – 10 초 (요청 4 – 10 초 ∩ references 6 – 15 초).
- 리깅 클립 모델 = Kenney 캐릭터 메시 (요청: 리깅·스킨 = 리깅 가능한 캐릭터), 가슴 → 어깨 → 팔꿈치 → 손목 체인 (몸통이 가슴 뼈에 붙어
  IK 를 당겨도 몸이 따라 돌지 않음).
- 트레일러 다운로드 줄 = `extensions.blender.org/add-ons/allset` 자리표시 (확장 id 그대로의 주소; 게시 전 확인, `content.json`).
- 게시 순서: BlenderArtists → r/blender + X → r/Maya (모더레이터 답 뒤) → 80.lv (스토어 공개 뒤).

## 검증

- 클립 녹화 검사 (클립마다 Blender 세션 안): 7 / 7 클립 모두 PASS — hotbox 보이는 객체 전부 선택, marking menu EDIT_MESH + 꼭짓점
  모드 → OBJECT, CB 곡선 10 개 / Rotate Z 키 [1, 36] / 나머지 1 개씩, navigation 드릴 선택 + F 거리 2.20 → 0.38 → A 6.64,
  pivot 꼭짓점과 0.00000 m / 0.201 m 이동 / 회전 중 피벗 고정, rigging 4 관절 + ikHandle1 + Armature 모디파이어 + PAINT_WEIGHT,
  switch 「Maya-style」 키맵 복귀.
- 크기 (`clip_compose.py` 검사, 전부 PASS): 클립 MP4 0.41 – 1.30 MB (≤ 8), 트레일러 38.8 초 3.97 MB (30 – 45 초, ≤ 20), GIF 1.02 –
  4.91 MB (≤ 5, 모두 15 fps), 소셜 프리뷰 0.23 MB (< 1), YouTube 0.34 MB (≤ 2), X 0.36 MB (≤ 5). ffprobe: 1920 × 1080 30/1, GIF
  960 × 540.
- 직접 봄: 클립마다 프레임 시트 (`tmp/marketing/sheets/`) — 고친 것: 핫박스 메뉴가 열리지 않음 (같은 틱 press/release), 메뉴 행
  어긋남 (All 대신 Deselect All, Key Selected 자리), 두 번째 Space 탭이 side 뷰로 (persp 칸 위로 이동), 캐릭터 · 드릴이 너무 작게 /
  크게, 내비게이션 줌이 탁자 다리 속으로 → 드릴 클릭 실패, 관절이 몸 뒤에 가려짐 (show_in_front), 스위치 뒤 레이아웃이 덜 그려진 그림
  (settle 늘림). 트레일러 1 fps 시트, 리깅 2.2 초 원본 크기 프레임, GIF 프레임 (960 px 에서 캡션 띠 읽힘). 키트 6 장 전부 — 고친 것:
  소셜 프리뷰 · X 카드 글자가 화면과 겹침, YouTube 「the Maya」 가 화면에 닿음.
- step 122 정지 이미지를 리팩터 뒤 다시 만듦 (`make_marketing.py --no-build`): 촬영 검사 전부 PASS, 결과 PNG 바이트 동일 (git 변경 없음).
- 헤드리스 배포 관련 step13 / step61 / step114: 11 / 11. `src/` 변경 없음 → GUI 전체 묶음은 돌리지 않음.

## 남은 것

- 게시 전: 다운로드 자리표시를 실제 주소로 (`content.json` `trailer.download`, `posts.md`), Reddit 사이드바 직접 확인, YouTube 업로드
  뒤 README 의 트레일러 링크 교체 — `docs/manual_checks.md` 「Step 123」.
- 크로스페이드 중 두 클립의 캡션 띠가 0.27 초 겹쳐 보임 (띠는 그대로 두고 화면만 섞는 방법이 있음 — 거슬리면).
- 4 분할 / 줌 장면에서 UI 글자는 GIF (960 px) 에서 읽기 어려움 — 캡션 띠가 설명을 맡음. 필요하면 GIF 용 확대 자르기.
- 앞 단계에서 남은 킷 쪽 작은 것 (환영 창 본문 잘림, 「persp」 두 번) 은 이번에도 손대지 않음.
