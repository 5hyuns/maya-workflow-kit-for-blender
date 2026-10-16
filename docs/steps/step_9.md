# Step 9 — M3-b 핫박스 + 커스텀 마킹메뉴 엔진

(사용자 번호 9 = `docs/PLAN.md` 표 #10.)

## 계획

근거: `research/maya/hotkeys_and_menus.md` §4 핫박스 (:202-221), §5 마킹메뉴 (:223-276); `research/maya/marking_menus.json` → `hotbox.zones`, `user_prefs_markingMenus` (존 메뉴 방사 위치); `research/maya/interaction.md:26-29, :80, :248` (누름/놓기, 탭 vs 홀드, Space); `research/blender/api_limits.md` #4 (:52-54 핫박스: 모달 + `draw_handler_add` POST_PIXEL + gpu/blf, 모달 끝난 뒤 `wm.call_menu`), #5 (:56-60 마킹메뉴 엔진).

### 1. 구조 (모듈)

- `marking/engine.py` — **순수 로직** (bpy 없음, 헤드리스 테스트): 방향 계산, 항목 배치(상대 좌표 사각형), 히트 테스트, 세션 상태 기계(누름-끌기-놓기 / 클릭 모드 / 제스처 / 하위 메뉴 / 옵션 박스). 입력 = (이벤트 종류, x, y, 시간), 출력 = 강조 항목·선택 결과.
- `marking/draw.py` — GPU/blf 그리기 (UNIFORM_COLOR 셰이더 + `batch_for_shader`, 한 프레임에 사각형 ≤ 100). 그리기 핸들러는 에디터 종류별 `Space*.draw_handler_add(..., 'WINDOW', 'POST_PIXEL')` 를 한 번 등록하고, 콜백은 **대상 리전 포인터와 같을 때만** 그린다 (다른 뷰에는 비용 없음).
- `marking/modal.py` — 모달 연산자 `maya_kit.mm_engine` (마킹메뉴), `maya_kit.hotbox` (핫박스), 핫박스 존 동작 연산자들.
- 정의는 Step 8 `marking/menus.py` 그대로 + 핫박스 존 메뉴 5개 추가 + 옵션 박스 표시(`OPT`).

### 2. 마킹메뉴 엔진 동작 (Maya 재현, [K] = Maya 사용 경험 기반)

- **배치**: 중심(누른 점)에서 반지름 R(= 80 px × UI 배율)에 방사 항목. N/S 는 가운데 정렬, E·NE·SE 는 왼쪽 정렬(오른쪽으로 뻗음), W·NW·SW 는 오른쪽 정렬. 선형 목록은 S 항목 아래 세로 목록 (Maya "링 아래 목록", hotkeys_and_menus.md:225).
- **방향 선택**: 중심에서 데드존(12 px, Blender `pie_menu_threshold` 와 같음) 밖이면 각도로 8방향 중 하나(45° 부채꼴) → 그 방사 항목 강조. 목록·옵션 박스는 사각형 안에 있으면 그것이 우선.
- **누름-끌기-놓기**: 버튼(RMB/LMB)을 누른 채 끌다가 놓으면 강조 항목 실행. 데드존 안에서 놓으면: 누른 시간이 짧으면(< 0.25 s) **클릭 모드**(메뉴가 떠 있고 다음 클릭으로 고름, ESC/데드존 클릭 = 취소), 길면 취소 (Maya 와 같음 [K]).
- **제스처/플릭**: 메뉴는 누른 뒤 0.15 s 지나야 그린다(보지 않고 긋기, Maya "mark" [K]). 그 전에 움직이면 궤적 선만 그린다. 선택 규칙은 같다 — 빠르게 긋고 놓아도 방향으로 선택.
- **하위 메뉴 (그 자리 중첩)**: 강조된 방사 항목이 하위 메뉴이고 포인터가 중심에서 R 이상 나가면 그 지점을 새 중심으로 하위 메뉴가 열린다 → 계속 끌어서 고름. 지그재그 제스처(첫 획 = 하위 메뉴 방향, 꺾어서 둘째 획 = 항목)도 같은 규칙으로 된다. 목록 안 하위 메뉴는 포인터가 그 줄에 오면 오른쪽에 펼쳐짐.
- **옵션 박스 `[]`**: Maya 옵션 박스가 있는 항목은 오른쪽에 작은 사각형. 거기서 놓으면(또는 클릭) 옵션 실행 = 연산자를 실행한 뒤 Blender "Adjust Last Operation" 팝업(`screen.redo_last`)으로 설정을 보여준다 (Maya 옵션 창의 대응, ui_layout.md:186-187 [I]). 툴 항목의 옵션 = 툴 전환 + Tool Settings 팝업.
- **회색 항목**: 정의가 None 이거나 연산자 poll 실패 — 열 때(하위 메뉴는 열릴 때) 한 번 계산해 캐시 (그리기마다 poll 안 함 = 성능).
- **실행**: 모달을 끝내고 같은 리전 컨텍스트에서 `INVOKE_DEFAULT` 로 (모달 연산자 — 베벨 등 — 도 정상 시작). 메뉴 동작은 `wm.call_menu`.
- **입력 누락 대비**: 놓기 이벤트를 다른 핸들러가 먹은 경우 TIMER(0.05 s) 에서 `keystate.is_down(button)` 이 False 면 놓은 것으로 처리 (Step 3 와 같은 방식). 창 밖으로 나가거나 ESC → 취소. 모달이 끝날 때 항상 그리기 핸들러 상태·타이머 정리 (예외에도 `finally`).
- **파이 대체**: 환경설정 `marking_menu_style` = **Engine**(기본) / Pie. `maya_kit.marking_menu` 와 Q/W/E/R 바인딩이 이 값으로 엔진 또는 Step 8 파이를 연다 (delegated: Maya 동작에 가까운 엔진이 기본, 문제 시 파이로).

### 3. 핫박스 (`maya_kit.hotbox`, Space)

- Space 누름 → 즉시 핫박스 (Maya 도 누르는 즉시 [O hotkeySetup.mel:352 press = hotBox]). 리전 전체에 반투명 어두운 막 + 위쪽 **메뉴 행**:
  - 행 0: Recent Commands, Hotbox Controls (HotboxMenus.mel:187-217).
  - 행 1: 공통 메뉴 File … Windows. 행 2: 현재 메뉴셋 메뉴 (Step 7 `menu_sets.menus_for_set`). Hotbox Controls 의 "Show All Menu Sets" 를 켜면 메뉴셋 행 전부 (Maya `-st/-rgt/...` 행 토글, L223-237; 기본값 [U] → 현재 메뉴셋만, delegated).
  - 가운데 사각형 = Center 존, 바깥은 대각선으로 N/S/E/W 존 (L57).
- 메뉴 이름 클릭 → 핫박스 닫고 그 Blender 메뉴를 마우스 위치에 연다 (api_limits #4). Recent Commands = `screen.repeat_history`, Hotbox Controls = 우리 메뉴(메뉴셋 고르기, 모든 행 표시).
- 존에서 LMB/MMB/RMB 누름 → 그 존의 마킹메뉴를 엔진으로 (세 버튼 모두 같은 메뉴, L142-158 기본). 핫박스는 닫히고 엔진 세션이 이어받는다 (Maya 는 핫박스가 뒤에 남음 — 단순화, delegated).
- Space 놓기: 클릭 없이 0.4 s 안이면 **탭** (L244 `-noClickDelay 0.4`): 3D 뷰 = 4분할 ↔ 단일 (Step 4 `taphold.SpaceBinding.tap`), 다른 에디터 = 그 영역 최대화(`screen.screen_full_area`, Maya `panePopAt` = 커서 아래 패널 최대화). 0.4 s 넘게 누르고 그냥 놓으면 아무것도 안 함.
- Space 반복 PRESS 무시, 놓기 누락은 keystate 로.
- 존 메뉴 (research JSON `hotbox.zones`, 위치 그대로):
  - **N** (패널 레이아웃): Single Perspective = 4분할 해제; Hypershade/Persp·Hypershade/Render/Persp·Hypershade/Outliner/Persp = "Shading" 워크스페이스; Persp/Graph·Persp/Graph/Outliner = "Animation" 워크스페이스; 나머지 회색.
  - **S** (패널 종류): 커서 아래 영역을 Outliner / Graph Editor / Dope Sheet / Node Editor(셰이더) / Hypershade(셰이더 노드) / Render View(이미지 에디터) 로 바꿈; Hypergraph·Set Editor 회색.
  - **E** (UI 요소): Help Line / Status Line / Command Line (Step 7 환경설정), Attributes ▸ (Channel Box / Layer Editor = 사이드바, Attribute Editor, Tool Settings), Tool Box (툴바), Time Slider·Range Slider·Shelf 회색.
  - **W** (선택 마스크 프리셋): Polygons / NURBS / Rendering / Deformations / Animation 만 선택 가능하게 (Step 7 마스크), Object/Components 전환, Hierarchy·Dynamics 회색.
  - **C** (뷰): Perspective (영역을 3D 뷰로 + 원근, 마지막 원근 시점 복원) / Top / Front / Side(Right) / Left / Back / Bottom.
- 핫박스 키: Space 를 3D View, Outliner, Graph Editor, Dopesheet, Node Editor, Image 키맵에 (IC 는 Space 를 Frames 재생에만 썼고 Step 2 에서 Alt+V 로 옮김 — 다른 에디터에 Space 없음, 덤프 확인). 텍스트 입력 에디터(Text, Console)는 제외. 3D View 의 Step 4 `tap_hold space` 바인딩 → `maya_kit.hotbox` 로 교체 (탭 동작은 그대로).

### 4. 성능·안정성 체크리스트

- 마우스 이동마다 리전 하나만 `tag_redraw`. 텍스트 폭(blf.dimensions)·poll 결과는 열 때 계산해 캐시.
- 그리기 콜백은 예외를 삼키고 로그 (그리기 예외가 매 프레임 터지면 UI 가 먹통) — 세션이 없으면 즉시 return.
- 모달 종료 경로(실행/취소/ESC/창 이탈/누락 감지) 모두 한 함수 `_finish` 로. unregister 때 활성 세션 강제 종료 + 핸들러 제거.

### 5. 테스트

- 헤드리스 (`test_step9_engine.py`): 방향 함수(경계 각도·데드존), 배치(정렬·겹침 없음), 세션 — 끌어 놓기, 짧은 클릭 → 클릭 모드 → 클릭 선택, 데드존 놓기 취소, 플릭(그리기 전), 하위 메뉴 그 자리 열림 + 지그재그, 옵션 박스 히트, 목록 히트, 회색 항목 선택 불가, 핫박스 레이아웃(행·존 판정·탭 시간 판정); 존 정의가 research 와 위치 일치; 존 동작 연산자(뷰·패널 종류·마스크·UI 토글); 키맵 (Space × 6 에디터); 환경설정으로 파이/엔진 전환; enable/disable 깨끗 (그리기 핸들러 포함).
- GUI (`gui_step9_hotbox.py`): RMB 누른 채 끌기 → 엔진으로 엣지 모드; 짧은 RMB → 클릭 모드 스크린샷 → 클릭 선택; 빠른 플릭; 하위 메뉴 그 자리; Space 홀드 핫박스 스크린샷 → 메뉴 행 클릭 → 메뉴 열림; 존 클릭 → 존 마킹메뉴 (C → Top 뷰); Space 탭 = 4분할.
- manual_checks: 플릭 감도, 지연 0.15 s, 실제 키보드/마우스로 입력 누락 없는지, 큰 화면/HiDPI 배율.

## 한 것

- `marking/engine.py` (bpy 없음): `direction` (8방향, 데드존 12 px), `Layout` (Maya 배치: N/S 가운데, E 계열 오른쪽으로, W 계열 왼쪽으로, 목록은 링 아래, 옵션 박스 사각형), `Session` (누름-끌기-놓기, 짧은 클릭 → 클릭 모드, 0.15 s 전 플릭 = 그리지 않고 선택, 하위 메뉴 그 자리 열기 + 지그재그, 목록 하위 메뉴는 올려두면 열림, 회색 항목은 실행 안 함), `HotboxLayout` (행·중앙 상자·N/S/E/W 존, 스타일 3종), `is_tap` (0.4 s).
- `marking/draw.py`: 에디터 6종(3D View, Outliner, Graph, Dope Sheet, Node, Image)에 POST_PIXEL 핸들러 하나씩, 대상 리전만 그림. Maya 회색·선택 파랑, 반투명 막, 궤적 선, 옵션 박스. 그리기 예외는 삼키고 세션 해제.
- `marking/modal.py`: `maya_kit.mm_engine` (모달, TIMER 로 놓기 누락 감지 `keystate`, 지연 표시 다시 그리기, ESC/창 이탈 취소, 실행은 끝난 뒤 같은 리전에서 INVOKE; 옵션 박스 = 실행 + `screen.redo_last`, 툴은 + Tool Settings), `maya_kit.hotbox` (행 클릭 → 그 메뉴, 존 클릭 → 존 마킹메뉴, 탭 → 4분할/최대화), `MAYAKIT_MT_hotbox_controls`, 존 동작 `hb_view` (원근 시점 기억·복원, 다른 에디터면 3D 뷰로), `hb_pane`, `hb_single`, `hb_workspace`, `hb_ui`, `hb_mask`, `hb_style`.
- `marking/menus.py`: 핫박스 존 메뉴 5개 (research 위치 39개 일치), 옵션 박스 표시(`options`).
- `maya_kit.marking_menu` 와 Q/W/E/R 바인딩은 `modal.open_menu` → 환경설정 **Marking Menus = Maya Engine(기본) / Blender Pies**. 누른 위치를 `origin` 으로 넘김.
- 키맵: Space = `maya_kit.hotbox` (3D View, Outliner, Graph Editor, Dopesheet, Node Editor, Image). 대응표 ShowHotbox → KIT. 환경설정: Marking Menus, Hotbox Style, Show All Menu Sets.

### 계획과 다르게 된 것 / 실측으로 바뀐 것

- **중첩 invoke 의 event 위치**: 키맵이 부른 연산자 안에서 `mm_engine` 을 INVOKE 하면 그 event 는 창의 최신 상태다. 시뮬레이션 이벤트를 한 틱에 몰아 보내면 이미 놓은 위치가 되어 플릭이 취소됐다 → 누른 위치를 `origin` 속성으로 명시해서 넘김.
- **툴바 토글**: 연산자 안에서 `show_region_toolbar` 를 바꾸거나 `screen.region_toggle`/`wm.context_toggle` 을 써도 GUI 에서 툴바가 그대로였다 (연산자 밖에서 직접 설정하면 됨) → `bpy.app.timers` 로 연산자가 끝난 직후 설정.
- **스크린샷 한 프레임 늦음**: `screen.screenshot` 은 이전 프레임을 찍는다 → GUI 테스트는 한 틱 뒤에 찍는다 (지연 표시도 이렇게 확인).

## 검증

```
python tests/run.py        → 130 passed, 0 failed, 10 file(s)   (step 9: 18, 기준 110 + step 8 개수 갱신)
python tests/gui/run.py    → 90 passed, 0 failed, 7 file(s)     (step 9: 16, 기준 74)
```

- 헤드리스 `test_step9_engine.py` (18): 방향 경계(22.5°), 배치(정렬·겹침 없음·옵션 박스), 끌어 놓기, 클릭 모드·데드존 취소, 플릭, 그 자리 하위 메뉴 + 지그재그, 옵션 박스·목록 히트, 회색 항목, 목록 하위 메뉴, 핫박스 행·존·스타일, 탭 시간, 메뉴셋 행, **존 메뉴 research 위치 39개**, **옵션 박스 research 대조**, 존 연산자(뷰·원근 복원·마스크·UI·스타일·패널 종류 → 3D 뷰 복귀), 동작 대상 존재, poll 캐시, Space 키맵 6개, 엔진/파이 전환·origin 전달, disable 시 그리기 핸들러 제거.
- GUI `gui_step9_hotbox.py` (16): RMB → 엔진(파이 아님) 위로 끌어 놓기 = Edge, 끝나면 그리기 상태 없음; 짧은 RMB 클릭 → 클릭 모드 → 클릭 W = Vertex; 한 틱 안 플릭 남쪽 = Face; Ctrl+RMB W 로 끌면 To Vertices 하위 메뉴가 그 자리에 열리고 다시 W = 정점 모드; Space 홀드 = 핫박스, "Mesh" 클릭 = Mesh 메뉴; 가운데 존 클릭 → W 끌어 놓기 = Top 뷰, Perspective 복원; 툴바 토글; Space 탭 = 4분할; 면 모드 Shift+RMB 에 옵션 박스.
- 스크린샷 직접 확인 (`tmp/shots9/`): `gui_step9_rmb_engine.png` (가만히 있어도 0.15 s 뒤 메뉴: N Edge, NE Object Mode, W Vertex, E UV 회색, SW Vertex Face 회색, SE Multi, S Face + 목록), `gui_step9_click_mode.png`, `gui_step9_submenu.png` (To Vertices / To Vertex Perimeter 가 끌어간 자리에), `gui_step9_hotbox.png` (Recent Commands·Hotbox Controls / File…Windows / Mesh…Generate 행, 가운데 "Maya Kit · Modeling", 존 이름), `gui_step9_hotbox_mesh_menu.png`, `gui_step9_hotbox_center.png` (Perspective/Left/Top/Back/Front/Bottom/Side + Hotbox Style ▸), `gui_step9_option_boxes.png` (Poke/Bevel/Extrude Face·Multi-Cut·목록 옆 `[]`).

## 결정 (delegated)

- 엔진이 기본, 파이는 환경설정으로 되돌릴 수 있음.
- 존 클릭 후 핫박스는 닫히고 존 마킹메뉴만 남음 (Maya 는 핫박스가 뒤에 남음).
- 핫박스 메뉴 행 기본 = 현재 메뉴셋만 (Maya 기본값 [U]), Hotbox Controls 에서 전부.
- 존 이름을 화면 가장자리에 흐리게 표시 (Maya 에는 없음, 처음 쓰는 사람용).
- N 존의 Hypershade/Graph 레이아웃 = Blender "Shading"/"Animation" 워크스페이스. S 존 Hypershade/Node Editor = 셰이더 노드 에디터, Render View = 이미지 에디터.
- W 존 마스크 프리셋은 "그 종류만 선택 가능" (Maya setSelectMode 프리셋 근사), "All Objects" 목록 항목 추가.
- Space 핫박스는 텍스트 입력 에디터(Text, Console)에는 넣지 않음.

## 남은 것

- 옵션 박스 실행(`screen.redo_last` 팝업)과 모달 연산자(베벨 등) 옵션은 manual_checks — 자동 테스트는 히트 판정까지.
- 마킹메뉴 편집기(Maya Marking Menu Editor), 사용자 존 메뉴, 핫박스 투명도·RMB 팝업 옵션, Recent Commands 를 Maya 식 목록으로.
- 핫박스 위 존 메뉴가 열려 있는 동안 핫박스 행 유지.
- 하위 메뉴에서 부모로 되돌아가기 (지금은 ESC 로 전체 취소).
- 큰 화면/HiDPI 배율, 실제 입력 장치에서 플릭 감도 — manual_checks.
