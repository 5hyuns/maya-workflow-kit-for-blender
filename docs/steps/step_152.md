# Step 152 — Render and display basics (#101, audit 9)

## 계획

이슈 #101 을 먼저 만듦 (감사 9 점수 9). 새 Maya 장면 (조명 없음) 이 어둡게 렌더됨, Render Current Frame / Render Sequence 옵션 상자가
"no settings", Test Resolution / Batch Render 회색, Display > Grid ❒ 없음 (킷 격자 ±12 고정).

레인 (파일이 겹치지 않게, delegated; 에이전트 2 개 동시 = PC 부하 규칙):
- **A — Maya 캡처 + Grid Options** (worktree 에이전트): GUI Maya 한 세션에서 Grid / Render Sequence / Batch Render / Render
  Settings 창과 Test Resolution 항목, 기본 조명 렌더를 잡고 (`research/maya/re/render_grid_152.md`, `research/maya/screens/render152/`,
  `research/scripts/maya_render152/`), `ui/maya_grid.py` 를 Grid Options 에 연결.
- **B — 기본 조명 · Test Resolution · Batch Render** (worktree 에이전트): mayapy 로 기본 조명 측정
  (`research/maya/re/default_light_152.md`, `research/scripts/default_light_152/`), 킷 구현.
- **C — 메인**: A 의 캡처로 Render Sequence ❒ / Batch Render ❒ 창과 Render Current Frame ❒ 경고 (A 의 캡처가 먼저 있어야 해서 그 뒤),
  병합 · 검증 · 커밋.

## 한 일

레인 A (`a7c0973`):
- Maya Grid Options: Length and width 12, Grid lines every 5, Subdivisions 5 (1–20), 색 3 개 (색 인덱스 2 = #404040), Display 체크 4 개
  (모두 켬), 격자 숫자 Hide. `operators/option_windows_display.py` (Apply and Close / Apply, 값은 애드온 설정 `option_settings` 의
  `grid_options` — Maya optionVar 처럼 사용자별), `ui/maya_grid.py` 가 크기 · 간격 · 분할 · 색 · 표시 체크를 따름 (Maya 단위 ×
  `maya_unit()`, 선 수 상한 `MAX_LINES`). 일반 클릭 Display > Grid 는 그대로 켜기 / 끄기 (`Window(click_saved=False)`).
- delegated: 색은 Blender 색 선택기 (Maya 31 색 인덱스 슬라이더 대신), 격자 숫자는 안 그림 (Maya 공장값 Hide).

레인 B (`c9de4cc`, 자세한 기록 `docs/steps/step_152_render_b.md`):
- Maya 기본 조명 (mayapy 측정): 장면에 조명 노드가 하나도 없고 Enable Default Light 가 켜져 있을 때만, 흰 방향광 세기 1, 그림자 없음,
  카메라를 따라감 (카메라 공간에서 시선 축을 위로 25°, 왼쪽으로 25°). Maya Software 큐브 top / front / side = 76.84 / 65.12 / 10.0.
- `operators/default_light.py`: 킷 렌더 (Render Current Frame / Sequence, Batch Render) 동안만 렌더 카메라 자식 Sun `defaultLight`
  (세기 π = Maya 1), 렌더가 끝나면 지움 (undo / load 도 정리), Outliner / defaultLightSet / Light Editor 에 안 보임.
  Render Settings > Common > Render Options > Enable Default Light (`Scene.allset_default_light`, 기본 켬).
- Test Resolution 하위 메뉴 (Camera Panel / Render Settings / 10–150 %; 애드온 설정 `test_resolution`, 킷 렌더 동안만 적용).
  Batch Render = 파일 복사본을 별도 `blender -b` 로, Cancel / Show Batch Render.
- delegated: Blender 자체 F12 (`render.render`) 에는 기본 조명을 넣지 않음 (render_pre 는 렌더 스레드 — 물체 추가 위험).

메인:
- `operators/option_windows_render.py`: Render > Render Sequence ❒ = Maya "Render Sequence (Current Frame)" 창 (Current Camera =
  persp + 장면 카메라, Alternate Output File Location = 이번 렌더만의 폴더 — `render_persp._alternate_output` 가 render_complete /
  cancel 때 되돌림; 나머지 Maya 칸은 "Not in Blender"), Batch Render ❒ = Maya Software 의 "Batch Render Frame" (Use all available
  processors / Number of processors → background Blender `-t N`; delegated: Maya 공장 렌더러 Arnold 는 창 없이 경고). Render Current
  Frame ❒ / IPR ❒ = Maya 처럼 창 없이 경고 `Renderer "<엔진>" does not provide render options.` (`option_generic.invoke`).
- `render_persp._Render` 에 `camera` / `output` (숨김), `render_batch` 에 `threads`.
- `test_step103` 제목 규칙에 두 Maya 제목 예외.

## 검증

- 레인 A: 헤드리스 94/94 + 54/54, GUI `gui_step152` / `step134` 50/50 (Apply 뒤 빨간 축 692 px, Reset 으로 공장 격자).
- 레인 B: 헤드리스 162/162, GUI `gui_step137_render` 8/8 (렌더 중 `defaultLight` 있음, 큐브 밝음, 끝나면 없음). 밝기 (같은 뷰, cm 템플릿,
  선형 EXR ×255): Maya 76.84 / 65.12 / 10.0, 킷 × 0.8 (Maya Diffuse 0.8) 77.2 / 65.6 / 10.4 (EEVEE), 77.3 / 65.7 / 10.4 (Cycles).
- 병합 뒤 헤드리스 전체 1394/1394 (`test_step152_render_windows` 4 포함).
- GUI 관련 파일 한 번 (`-k step152,step137_render,step45,step105`) 21/21 / 3 파일. Grid Options 창을 Maya `grid_options.png` 와
  나란히 봄 (같은 칸 · 기본값 · 버튼, Blender 는 평평한 목록 + 색 막대), 렌더 결과에 큐브가 밝게 보임. GUI 전체 묶음은 안 돌림.

## 남은 것

- 밝기: 킷 lambert1 은 Color 0.5 를 그대로 렌더 → Maya (Color × Diffuse 0.8) 보다 1.25 배 밝음 (step 100: Principled 에 Diffuse 입력
  없음). 템플릿 world 회색 (0.051) 이 약 6.5/255 의 주변광을 더함. 둘 다 재질 / 템플릿 변경이라 따로.
- Blender 자체 F12 렌더에는 기본 조명 없음. Render Sequence 의 All Render-Enabled Layers / Cameras, Render Region, Add to Render View 없음.
- Grid: Axes / Thicker line 끈 상태의 Maya 그림은 측정 안 함, 격자 숫자 없음.
