# Step 131 — Icon overhaul (#23) + Hypershade layout (#25)

## 계획

사용자 지시: Maya 2022 아이콘의 실루엣 · 주색 · 구도 · 크기를 따라 킷이 직접 그린 (CC0) 아이콘으로 바꾼다. Maya 아이콘 파일은
복사 · 추적 금지 — 설치본 `C:/Program Files/Autodesk/Maya2022/icons` 와 Maya 내장 리소스는 **보기만** 하고, 비교 시트는 `tmp/` 에만
둔다 (결정 6). Hypershade 창은 Maya 2022 의 기본 배치 (Browser · Create · Material Viewer · Graph 작업 영역 · Property Editor) 로.

### 레인 (병렬, 사용자 지시 2026-10-20)

| 레인 | 하는 일 | 파일 | 순서 |
|---|---|---|---|
| REF | Maya 2022 GUI 를 한 번 띄워 `resourceManager -saveAs` 로 셸프 · Status Line · Tool Box · 패널 툴바 · Layer Editor · Outliner 노드 아이콘을 `tmp/maya_icons131/` 로 내보냄 (1x / 150 / 200), 키트 아이콘 ↔ Maya 아이콘 ↔ Maya 명령 대응 `index.json`, 비교 시트 + 알아보기 점수 | `tmp/maya_icons131/`, `research/maya/re/icons131.md` | 먼저 |
| SHELF | 셸프 203 버튼 아이콘 다시 그림 (버튼마다 고유, 픽셀 힌팅, 2x) | `ui/shelf_icons.py` (+ `ui/shelf.py` 텍스처 크기) | REF 뒤 |
| STATUS | Status Line · 메뉴 바 · 패널 툴바 글리프, Tool Box 빠른 레이아웃 버튼, Layer Editor · Outliner 타입 아이콘 | `ui/status_icons.py`, `ui/panel_toolbar.py` 글리프, `ui/toolbox.py`, `ui/layer_editor.py`, `ui/maya_outliner.py` | REF 뒤 |
| HYPER | Maya Hypershade 캡처 (같은 크기, 실행 후 종료) + 창 레이아웃 재구성 | `ui/hypershade.py` (+ 새 모듈), `research/maya/screens/hypershade131/` | 바로 |
| MAIN | 아이콘 고유성 테스트, 콘택트 시트 생성기 (`tools/icon_sheet.py` → `docs/icons/`), 인벤토리 표, 병합 · 검증 · 커밋 | `tests/test_step131_icons.py`, `tools/icon_sheet.py`, docs | 동시 |

순서가 필요한 것: SHELF / STATUS 는 비교할 Maya 그림이 있어야 해서 REF 다음 (Maya 를 여러 개 띄우는 것보다 한 번 내보내는 게 빠름).
코드 레인은 worktree 로 격리하고 메인이 병합 (같은 `dist/` · `tmp/test_env` 를 함께 쓰면 빌드 · 샌드박스가 부딪힘).

### 아이콘 규칙 (delegated)

- 그리는 방식은 그대로 numpy 벡터 → RGBA (파일 없음, CC0, `ASSETS_LICENSE.txt` 에 넣을 파일이 없다). "SVG" 는 이 벡터 정의를 뜻한다.
- 32 px 와 64 px (2x, UI 배율 ≥ 1.25) 를 같은 정의에서 그리고, 선 두께 · 끝점을 픽셀 격자에 맞춘다 (힌팅).
- Maya 아이콘의 **알아볼 수 있는 특징만** 따른다: 무엇이 그려졌는지 (실루엣), 주색, 구도 (도구 부분이 어디 있는지), 크기. 윤곽선을
  따라 그리거나 픽셀을 옮기지 않는다.
- 같은 셸프 / 같은 Status Line 그룹 안에서 같은 그림 금지 (테스트로 검사).

## 한 것

레인 6 개 (REF, HYPER, SHELF, STATUS, TOOLBOX, MENU — MENU 는 TOOLBOX 결과를 보고 추가) 를 병렬로 돌리고 메인이 병합했다.
레인별 계획 · delegated 결정 · 점수표: `step_131_hypershade.md`, `step_131_shelf.md`, `step_131_status.md`, `step_131_toolbox.md`,
`step_131_menu.md`. 아이콘 목록 (킷 아이콘 ↔ Maya 명령 ↔ 이전 점수): `step_131_icons.md`. 콘택트 시트: `docs/icons/` (`tools/icon_sheet.py`).

- **REF**: Maya 2022 를 띄워 (`research/scripts/maya_icons131/`) `resourceManager` 로 아이콘 1390 개를 `tmp/maya_icons131/` 에만
  내보내고 (저장소에는 없음), 320 항목 대응표 `index.json`, 비교 시트, 점수 (0–3). Maya 아이콘의 알아볼 수 있는 특징은
  `research/maya/re/icons131.md` 에 글로만 (클린룸). Maya 2022 UI 리소스에는 `_150` / `_200` 파일이 없다 (측정) — 2x 는 킷이 직접 그림.
- **SHELF** (`ui/shelf_icons.py` 다시 씀): 셸프 203 버튼 모두 버튼마다 그림 하나 (`"<shelf>/<label>"`, 같은 이름 버튼은 index),
  두 글자 배지 · 글자 타일 폐지 (사용자 셸프의 비 팩토리 버튼만 Maya 식 스크립트 버튼 + 이니셜). Maya 어휘: 모든 도형에 #3a3a3a 테두리,
  종류별 색 (NURBS 파랑, poly 주황, UV 초록 + 체커, 리깅 라벤더, 키 주황빨강, 렌더 노랑, FX 연어색), 도구 부분 #bcbcbc, 동작 표시는
  모서리에 작게. 32 / 64 px 를 같은 정의에서 픽셀 격자에 맞춰 그림; `shelf.py` 는 32 px 보다 크게 그릴 때 64 텍스처.
  점수 평균 0.52–1.13 → 2.45–2.86, 2 미만 0 개.
- **STATUS** (`ui/status_icons.py`, `ui/panel_toolbar.py`): `Canvas` 가 크기마다 픽셀 격자에 맞춤 + Maya 의 어두운 테두리,
  `image(name, size)`, 미리보기를 `round(16 × ui_scale)` px 로 만들고 배율이 바뀌면 타이머에서 다시 만듦 (같은 크기가 2x 보다
  10–15 % 선명, 측정). 선택 마스크 청록, 스냅 자석 + 오른쪽 아래 대상 표시, 렌더 클래퍼 + 내용 표시, 패널 툴바 카메라 · 게이트 ·
  X-ray 등. 0 점이던 mask_SURFACES / mask_RENDERING / pan_zoom / ssao / aa / xray / color_mgmt → 2–3. 2 미만: 그룹 접기 손잡이
  open / closed (Status Line 배치 문제라 남김).
- **TOOLBOX** (새 `ui/kit_icons.py`): Tool Box 열의 Select / Lasso / Paint Selection / Move / Rotate / Scale 를 킷 벡터 아이콘
  (`bpy.app.icons.new_triangles`, 킷 전용 이름으로 `_icon_cache` 에 등록, 해제 시 제거; 테마 Icon Saturation 보정) 으로,
  빠른 레이아웃 버튼 · Outliner 버튼 · Layer Editor 버튼 · 킷 Outliner 행 (세트, 카메라) 을 Maya 모양으로. 모두 1→3 또는 0→3.
- **MENU** (새 `ui/menu_icons.py`, 생성 데이터 `ui/menu_icon_data.py` ← `tools/gen_menu_icons.py`): Maya 가 아이콘을 보이는
  메뉴 항목 중 킷 그림이 있는 190 개 (그림 183 종) 에 아이콘. Blender 팝업 메뉴는 아이콘 열을 늘 비워 두므로 (측정) 글자 · 단축키 ·
  ❒ 정렬이 그대로다. 미리보기 타이머는 `persistent=True` (Maya 레이아웃을 여는 파일 로드가 타이머를 지움).
- **HYPER** (#25, `ui/hypershade.py` + 새 `ui/hypershade_layout.py`): Maya 2022 Hypershade 캡처 (`research/maya/screens/hypershade131/`,
  명세 `research/maya/re/hypershade131.md`) 와 같은 배치의 별도 창 — 메뉴 줄, Browser (탭 10 개 + 스와치), Create (분류 + 목록 +
  검색), Material Viewer (재질 미리보기), Graph (Shader Editor + Maya 그래프 툴바 + `Untitled_1` 탭), Property Editor (재질 AE).
  창 비율 차이 최대 0.6 %. 창 제목 · 패널 float 버튼 · 회전 가능한 GL 뷰어는 Blender 에 없음 (step_131_hypershade.md).
- 메인: `tests/test_step131_icons.py` (셸프 · Status Line · 패널 툴바 버튼마다 고유 그림 = 명확히 다른 픽셀 4 % 이상, 크기 16–64),
  `tools/icon_sheet.py` + `docs/icons/` 콘택트 시트 (킷 아이콘만), `step_131_icons.md` 목록.

순서가 필요했던 것: 다시 그리는 레인은 REF 의 Maya 기준 그림 뒤 (Maya 를 레인마다 띄우지 않으려고); MENU 는 셸프 그림이 병합된 뒤.

### 병합 뒤 메인이 고친 것

- **GUI 테스트가 모두 끝에서 멈춤**: TOOLBOX 레인의 Tool Box 벡터 아이콘 (`bpy.app.icons.new_triangles`) 때문에 Maya 모드를 끄거나
  Blender 를 끌 때마다 tbbmalloc 접근 위반 → 각 GUI 파일이 시간 제한까지 기다림. `-b` 에서 재현: `new_triangles` 아이콘은
  `release` 해도, 그대로 두고 종료해도 죽고, `new_triangles_from_file` 아이콘은 둘 다 멀쩡하다 ("MEM_freeN on a pointer created with
  MEM_new" — Blender 4.5 버그). 그래서 `kit_icons.geom_icon` 이 Blender 의 .dat 형식 그대로 확장 사용자 폴더
  (`extension_path_user(.../icons)`) 에 쓰고 파일에서 읽는다 (delegated). 회귀 테스트 `test_vector_icons_free_cleanly`.
- 콘택트 시트 / 고유성 테스트는 같은 이름 셸프 버튼 (FX "From Current", FX Caching "Delete Cache") 을 index 로 그림.

## 검증

- 헤드리스 전체 `python tests/run.py`: 1011 passed, 0 failed (124 파일, MENU 병합 전) → 병합 · 수정 뒤 관련 파일
  `-k step131,enable_disable,step130,step114` 49/49, `-k step131,step109,step51,step130,step114,enable_disable` 62/62.
- GUI 전체 `python tests/gui/run.py`: 첫 묶음 604 PASS 뒤 위 크래시로 멈춤 → 수정 후 남은 38 파일 + 실패 4 파일 다시 실행
  703 passed, 1 failed. 합계 1307 PASS, 1 FAIL = `gui_step106_tool_settings` toggle 2 (1.25 배율에서 Tool Settings 를 닫으면 뷰포트가
  좁아짐) = 열린 이슈 #53 (step 130 에서도 남은 1 건).
- 레인별: SHELF 헤드리스 33 + GUI 25/26 (1.25 / 1.0), STATUS GUI 16 + 10, TOOLBOX 헤드리스 34 + GUI 32 + 7, MENU 헤드리스 77 (1 실패 =
  worktree 에 research/ 없음, 본 저장소에서 통과) + GUI 49 + 13, HYPER 헤드리스 102 + GUI 7 + 30 + 수동 스윕 24.
- 화면을 직접 봄: `docs/icons/*.png` (킷 아이콘만), `tmp/status131/sheet_status.png`, `tmp/shelf131/sheet_*.png` (Maya 비교, tmp 전용),
  Tool Box / Outliner / Layer Editor 1.0 · 1.25 크롭, Polygon Primitives 메뉴 1.25, Hypershade 창 vs Maya 캡처.
- 손 확인: `docs/manual_checks.md` 「Step 131 — Hypershade」 7 항목, 「Step 131 — menu icons」, 「Step 131 — icons」.

## 남은 것

- Blender C Outliner 의 오브젝트 종류 아이콘 (18 종, Maya out_* 와 다름): Python 으로 바꿀 수 없고, 행 ↔ 오브젝트를 확실히 알 수 없어
  덧그리기도 하지 않음 (step_131_toolbox.md 에 들여쓰기 스캔 아이디어).
- Maya 가 아이콘을 보이는 메뉴 항목 중 킷 그림이 없는 489 개 (주로 Deform, Mesh Display, Effects / Fields, 셸프 버튼 없는 Edit Mesh /
  Mesh Tools) — 새 그림이 필요. 편집기 메뉴 바 (Graph Editor, Hypershade 등) 의 Maya 메뉴 아이콘 캡처도 아직 없음. 마킹 메뉴 · 핫박스는
  GPU 로 그려 아이콘 없음.
- Status Line 그룹 접기 손잡이 open / closed (점수 1): 아이콘이 아니라 손잡이 위치 (배치) 문제.
- 셸프 줄 높이 때문에 1.25 배율에서 아이콘이 28 px (64 텍스처는 줄이 더 높을 때만 쓰임).
- 위 항목은 후속 이슈 #54 로 남김 (#23 의 요구 — 목록, 비교 · 점수, 약한 것 다시 그림, 이웃 구분, 고유성 테스트, 콘택트 시트 — 는 끝남).
