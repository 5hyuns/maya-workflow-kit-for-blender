# Step 40 — Maya 동일화 재설계 (조사·계획)

사용자 요청 (2026-10-17): 「UI 색이랑 그런 것까지 Maya랑 똑같이. 누가 봐도 켜면 '어? 마야네' 하는 느낌. know-your-unknowns 와
/sc:brainstorm 으로 빠진 것·문제 있는 것·사용성에서 Maya와 다른 것을 한 번 더 찾아라. 시중 유료 애드온보다 더 좋게.」
이번 단계는 조사·계획만 한다 (작은 버그 수정 1건 포함).

## 계획 (delegated)

1. Maya 2022 를 **깨끗한 임시 prefs** (`MAYA_APP_DIR=tmp/maya_app` = 팩토리 기본값) 로 띄워, 1600x900 창에서 같은 장면을
   스크립트로 찍는다 (Qt `grabWindow`, 핫박스·마킹 메뉴는 Windows `SendInput`). 색은 픽셀만이 아니라 실행 중인 Maya 에서
   직접 읽는다: Qt 팔레트·폰트·위젯 크기 (PySide2), 뷰포트 색 `displayRGBColor` / `displayColor` / `colorIndex`.
   → 사용자 Maya prefs (`Documents/maya/2022`) 는 건드리지 않는다. 끝나면 그 PID 만 종료 (스크립트가 `cmds.quit`).
2. Blender 쪽은 같은 크기·같은 상태로 찍는 재사용 도구 (`tools/look_shots.py` + `tools/look_compare.py`): 나란히 붙인 비교
   이미지 + 테마 색 ΔE00 표. 앞으로 외형 작업의 검증 기준이 된다.
3. 경쟁 제품 조사는 서브에이전트 (deep-researcher) 에 맡긴다 → `research/competitors.md`.
4. know-your-unknowns blindspot (unknowns-scout 서브에이전트) + /sc:brainstorm (비대화형: 질문 없이 결정은 delegated).
5. 결과: `docs/PLAN.md` 「Maya 동일화 계획」, backlog 8–12개 (`C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json`).

## 한 것

### 기준 자료 (research/ — git 미추적, 결정 6)

| 파일 | 내용 |
|---|---|
| `research/maya/screens/*.png` | Maya 2022.4 팩토리 화면 22장 (1600x900): 빈 레이아웃, 큐브 선택+Move/Rotate/Scale 매니퓰레이터, 와이어 (리드/다른 선택/비선택), 면·정점·엣지 선택, AE, Channel Box, Create 메뉴, Space 핫박스, RMB·Shift+RMB 마킹 메뉴, 4분할, Outliner/Status Line/Shelf/Time·Range Slider 잘라낸 것 |
| `research/maya/screens/_maya_ui_dump.json` | Maya 안에서 읽은 Qt 팔레트, 폰트, 위젯 위치·크기, 위젯 크기 분포, displayRGBColor 전체, displayColor 인덱스, colorIndex 1–31, 그리드·매니퓰레이터 prefs |
| `research/maya/colors.json` | 위를 정리한 색·측정치 (UI 팔레트, 픽셀 샘플 38개, 뷰포트 색과 의미, 메트릭). 생성: `mayapy research/scripts/maya_colors.py` |
| `research/maya/screens/compare/*.png` | Maya (왼쪽) / kit (오른쪽) 같은 해상도 나란히 15장 |
| `research/maya/screens/compare/delta_e.md` | 테마 31쌍 CIEDE2000 |
| `research/competitors.md` | 경쟁 제품 22개 + IC: 표, 기능 매트릭스, 모두 하는 것 / 아무도 못 하는 것 / 흔한 불만 |

Maya 실행: 2022.4, 라이선스 문제 없이 GUI 기동. 첫 시도에서 대화상자 닫기 코드가 메인 창까지 닫아 Maya 가 종료됨 → 이름
(`MayaWindow`) 비교로 고쳐 재실행. 스크립트: `research/scripts/maya_shots/shots.py` (research/ 아래, git 미추적).

### 측정된 Maya 사실 [O] (colors.json)

- **UI 팔레트** (Qt, 스타일 `adskdarkflatui`): Window #444444, Button #5d5d5d, Base(필드) #2b2b2b, AlternateBase #2e2e2e,
  Highlight #5285a6, Text #c8c8c8, WindowText(라벨) #bbbbbb, ButtonText #eeeeee, Mid #2d2d2d, Midlight #373737, Light #616161,
  비활성 텍스트 #808080/#696969. 메뉴 팝업 #525252, Outliner 목록 #373737 (테마는 #2b2b2b), 셸프 탭 줄 #373737, 선택 탭 #444444.
- **폰트**: Segoe UI **11 px** (화면 125 %, logicalDpi 120, Qt dpr 1.0), 줄 높이 13 px. 메뉴 항목 20 px, Outliner 행 20 px,
  Channel Box 행 16 px, 메뉴바 27 px, Status Line 27 px, 셸프 64 px (아이콘 32), 툴박스 버튼 36 px, Time Slider 36, Range Slider 31,
  Command/Help line 28. Channel Box 폭 260, AE 460, Outliner 260, 툴박스 40.
- **뷰포트**: 팩토리 배경은 **단색 0.36 (#5c5c5c), 그라디언트 꺼짐** (`displayPref -q -displayGradient` = False). 그라디언트 색
  (0.535,0.617,0.702)→(0.052) 은 Alt+B 용. 그리드 index 2 (#404040), 축선 같은 색 굵게, 12 칸·5 분할 (`grid` size 12, spacing 5,
  divisions 5).
- **선택 색**: 리드 (마지막 선택 = Blender active) = index 19 **연두 #43ffa3**, 다른 선택 = index 16 **흰색**, 비선택 와이어 index 5
  #000460 (어두운 파랑) (`04_wire_selected_lead.png`). 셰이딩 모드에서도 선택 오브젝트 위에 와이어가 그려진다 (`02`).
- **컴포넌트**: 컴포넌트 모드 오브젝트 와이어 hilite index 18 **#64dcff (하늘색)**, 비선택 정점 hiliteComponent index 9 #c800c8 (보라),
  선택 정점 index 17 **노랑**, 선택 엣지·면 index 21 **#e4ac79 (살구)**, 선택 면은 반투명 채움 (`07`).
- **매니퓰레이터**: X #e60000, Y #00e600, Z #4a92ff, 현재 핸들 노랑 (index 17), 핸들 크기 35, 가운데 사각형 + 평면 핸들 (`02`, `05`, `06`).
- 기타: 프리셀렉트 하이라이트 (1, 0.8, 0.9), Time Slider 배경 #2b2b2b·키 빨강·현재 프레임 회색 반투명, Graph Editor 배경 0.375.

### 작은 버그 수정

- **리드/다른 선택 색이 반대였다.** `tools/make_theme.py` 가 `object_selected` = 연두, `object_active` = 흰색으로 두었는데 Maya 는
  리드 = 연두 / 나머지 = 흰색 (displayColor lead 19, active 16; `04_wire_selected_lead.png`). 바꾸고 `maya.xml` 재생성 →
  ΔE00 28.5 → **0.0** (두 쌍).

### 도구 (저장소)

- `tools/look_shots.py` (GUI Blender 안): Maya 샷과 같은 이름·상태로 kit 화면을 찍는다 (`00_first_start` = 테마 적용 전 첫 화면).
- `tools/look_compare.py`: 샌드박스 설치 (`tmp/look_env`) → 1600x900 GUI 샷 → `blender -b` 에서 나란히 이미지 + 테마 31쌍 CIEDE2000
  (`--no-shots` = ΔE 만). Maya 쪽 자료가 없으면 비교 이미지는 건너뛴다.

### Blindspot (know-your-unknowns, unknowns-scout 서브에이전트, 읽기 전용) — 18건

종류: L 지뢰 · C 관례 · M 빠진 개념 · H 이력. API 주장 중 테마/환경설정 필드 존재는 헤드리스 프로브로 확인함
(`edge_mode_select`, `face_mode_select`, `vertex_size`, `edge_width`, `outline_width`, `facedot_size`, `face_select` 알파 0.2,
`view.ui_scale`/`mini_axis_type`/`font_path_ui`/`show_splash`, `panel_roundness`). 템플릿 `userpref.blend` 의 실제 교체 범위는 [U].

| # | 종류 | 발견 | 대응 (backlog 번호) |
|---|---|---|---|
| 1 | M | 앱 템플릿은 자체 `userpref.blend` (테마·키맵·애드온·조명, 폰트 경로) 를 가질 수 있다 → 템플릿 안에서만 Maya, 사용자 기본 Blender 는 그대로 | 2 |
| 2 | L | 그때 애드온 목록도 템플릿 것으로 바뀜 → 사용자 애드온이 MayaKit 안에서 꺼짐 (경쟁 제품 불만과 같은 모양) | 2 |
| 3 | H/L | 뷰 배경 그라디언트는 사용자 Maya prefs 값 ([O-pref]); 팩토리는 단색 #5c5c5c. 테마 그리드 #5c5c5c = Maya 배경이라 단색만 바꾸면 그리드가 사라짐. `test_step5_layout.py:74` 가 그라디언트를 단언 | 3 |
| 4 | L | `axis_x/y/z` 가 매니퓰레이터·내비 기즈모·그리드 축선을 함께 칠함 → Maya 매니퓰레이터 색을 넣으면 바닥에 빨강/초록 선 | 3, 5 |
| 5 | L | 4.5 는 `edge_mode_select`/`face_mode_select` 가 따로 있고 면 채움 알파는 `face_select` RGBA, `vertex_size` 등도 테마 | 3 |
| 6 | M | Maya 는 셰이딩 위 선택 오브젝트에 와이어 전체; Blender 는 외곽선만, `show_wire` 는 ID 데이터 + `display.py:70` `_WIRE_FLAG` 와 충돌 | 7 |
| 7 | M | ViewCube·축 삼각·'persp' 라벨 대 Blender 내비 기즈모·텍스트 오버레이 — 어떤 문서에도 없음 | 6 |
| 8 | H | "5 cm 주 그리드선 불가" (재점검 3차 10) — Maya 그리드는 유한 12칸·5 분할·같은 회색 축선; 자체 GPU 그리드로 재검토, X 스냅과 같은 단계여야 | 5 |
| 9 | L | 밀도: kit 는 Maya 의 약 1.25~1.5 배 크기 (CB 행 25 vs 16 px). `ui_scale` 변경은 GUI 테스트 픽셀 좌표·release 샷을 흔듦 | 4 |
| 10 | M | 폰트 Segoe UI 11 px; `font_path_ui` 로 시스템 폰트 지정 가능 (동봉 금지, Windows 만) | 4 |
| 11 | C | 위젯 모양 (roundness 0.4, emboss, 메뉴 그림자, panel_roundness) 이 표에 없음 — Maya 는 각진 평면 | 4 |
| 12 | L | `tests/kit.py` 스냅숏이 테마·`ui_styles` 를 안 봄 → 자동 적용하면 누수를 못 잡음 | 2 |
| 13 | M | 남은 Blender 요소: 툴바 (Cursor/Annotate/Measure/Add Cube), 툴 헤더 줄, Properties 탭, Item/Tool/View 탭 | 8 |
| 14 | M | RMB 목록 위치·제목·항목이 2022 화면과 다름 (링 아래, 'pCube1...', DG Traversal 등) | 11 |
| 15 | H | 타임라인 현재 프레임이 빨강 ([K]) — Maya 실측 #c7c7c7 반투명 | 3 |
| 16 | M | 첫 실행이 세 동작 (키맵 자동, 레이아웃 설치+열기, 테마 버튼), 스플래시는 Blender 것 | 2 |
| 17 | M | Maya 는 컴포넌트 모드에서도 W/E/R 툴 유지; kit 편집 모드는 Select Box (look_shots 탓일 수도 [U]) | PLAN 「Later candidates」 |
| 18 | C | 테마는 `tools/make_theme.py` 표로만, 비교는 `look_compare.py`, release 샷 재생성 | 모든 외형 항목의 검증 규칙 |

### /sc:brainstorm (비대화형, 결정은 delegated)

탐색 축: ① 켜자마자 보이는 것 ② 손에 익은 조작 ③ 경쟁 제품 대비. 결정 (모두 delegated, `docs/PLAN.md` 「Maya 동일화 계획」 D1–D3):
D1 Maya 기준 = 팩토리 prefs, D2 전역 환경설정 변경은 백업/복원 프리셋 + 자동 경로는 템플릿 prefs 가 사용자 애드온을 지킬 때만,
D3 Maya 아이콘·이미지·폰트 동봉 금지.

### 리뷰 (self-review 서브에이전트) → 반영

| # | 지적 | 반영 |
|---|---|---|
| 1 | backlog 가 가리키는 blindspot 절이 step_40.md 에 없음 | 위 표 추가, 18번까지 대응 항목 지정 |
| 2 | 항목 4개에 수치 기준 없음 | 모든 항목에 수치 (±px, ΔE00, 개수·순서 일치) |
| 3 | 테마 값 ΔE 만으로는 화면 색을 증명 못함 | backlog 1: 렌더 픽셀 ΔE 표 추가 |
| 4 | 비교 샷의 장면 상태가 Maya 와 다름 (카메라가 큐브에 붙음, 4분할 라벨) | backlog 1 을 선행 단계로 |
| 5 | 메뉴 팝업·CB/LE·Outliner·Time Slider·패널 헤더·사이드바 탭이 빠짐 | backlog 8·9·10 |
| 6 | 결정 3 (템플릿 버튼 설치) 과 충돌, D2 의 근거 인용이 틀림 | backlog 2 에 개정 기록 조건, D2 인용 수정 |
| 7 | 너무 큰 항목 5개 | 테마 색/위젯 감각, 그리드/뷰 가구 분리; 레이아웃은 (a)(b)(c) 나눌 수 있게 적음 |
| 8 | 테마·그리드·와이어 순서 | PLAN 에 순서 (5·7 은 3 다음) |
| 9 | 첫 시작이 먼저여야 | backlog 2 로 앞당김 |
| 10 | ①/② 섞임 | 툴 유지·매니퓰레이터 모양은 Later candidates 로, 핫박스는 ② 로 표시 |
| 11–12 | 5.x 는 결정 4 유지, Maya prefs 가져오기는 파싱만 | backlog 12 에 명시, 가져오기는 Later candidates |

## 검증

- Maya 기준 자료: 스크린샷 22장 + 덤프 → `colors.json` (픽셀 샘플 38, UI 팔레트 19 역할, 뷰포트 색 30+). 이미지를 직접 열어 확인
  (02, 04, 07, 08, 13, 14).
- `python tools/look_compare.py`: kit 샷 15장, 나란히 이미지 15장, 테마 ΔE00 > 5 = **13/31 → 11/31** (리드/선택 색 수정 후).
- 헤드리스 `python tests/run.py`: **339/339** (37 파일, 테마 수정 후).
- GUI 테스트는 돌리지 않음: `src/` 변경은 테마 XML 의 두 색뿐이고 GUI 테스트는 그 색을 보지 않는다. look_shots 가 GUI 에서
  kit 전 흐름 (설치, 템플릿, 테마, 핫박스, RMB, 4분할) 을 오류 없이 돌았다.
- Maya 는 스크립트 끝에서 `cmds.quit` 로 종료 (tasklist 확인), Blender 는 look_compare 가 띄운 것만 종료.

## 남은 것

- backlog 12개 (`docs/PLAN.md` 「Maya 동일화 계획」 순서). 첫 항목은 비교 기준 정확화 (look_shots 카메라·상태, 렌더 픽셀 ΔE).
- `colors.json` 의 그리드 색은 displayColor 인덱스 값 (#404040); 렌더 픽셀 확인은 backlog 1.
- Maya 2022 `displayColor -list` 는 이름마다 한 모드만 출력 → 비선택 폴리 와이어 (index 5) 는 스크린샷으로 확인한 값.
- Maya 쪽 스크립트 `research/scripts/maya_shots/shots.py`, `research/scripts/maya_colors.py` 는 저장소 미추적 (Maya 자료 정책). 다시 찍을 때:
  `powershell -File research/scripts/maya_shots/launch.ps1` → `mayapy research/scripts/maya_colors.py`.
