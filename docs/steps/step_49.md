# Step 49 — 레이아웃 동등화 (도크 열·툴박스·사이드바 탭·하단 줄)

backlog 8 (`docs/PLAN.md` 「Maya 동일화 계획」). 근거: `research/maya/screens/_maya_ui_dump.json` widgets
(ToolBox [2,132,40,653], Outliner [48,149,260,636], MainPane [314,132,1003,653], ChannelBoxLayerEditor [1323,132,260,653],
AttributeEditor 460, TimeSlider [2,791,1596,36], RangeSlider [2,833,1596,31], HelpLine [2,870,675,28], CommandLine [683,870,915,28]),
`research/maya/ui_layout.md:78-137` (General 분할 트리), `:224-233` (툴박스), compare/01·02·07, step_40.md blindspot 13.

## 계획

### 실측 (계획 전)
- 팩토리 워크스페이스는 모두 오른쪽 Outliner+Properties 열이 있음 (헤드리스 목록) → 다른 워크스페이스에서 시작해도 열은 남는다.
- 헤드리스 `screen.area_join` 은 `EXCEPTION_STACK_OVERFLOW` 로 죽거나 크기 0 영역을 더 만든다; `area_close` 는 `-b` 에서 멈춤 (CLAUDE.md).
  → **생성기를 GUI Blender 에서 돌린다** (`tools/make_startup.py`: 창 1600x900, 이벤트 시뮬레이션, 샌드박스 설정, 타이머에서 편집 →
  저장 → 종료). 영역 크기는 실제 픽셀로 맞출 수 있고 사이드바 폭은 경계를 시뮬레이션 드래그로 맞춘다 (API 로 못 바꿈).
- 툴바 한 열 폭은 C 상수 `UI_TOOLBAR_WIDTH` = 0.5·32 + 1.25·32 = 56 px (배율 1). Maya 40 → Δw 16 은 남는다.
- `ToolSelectPanelHelper.draw_cls` 는 `context.space_data.type` 의 툴을 `wm.tool_set_by_id` 로 켠다 → 툴박스 버튼은 3D 뷰 TOOLS
  영역에서만 Blender 툴 아이콘·강조·툴팁 그대로 그릴 수 있다. `wm.tool_set_by_id` 는 `tools_from_context` 에서 idname 을 찾으므로
  `_tools` 를 바꾸면 툴박스에 없는 툴 (셸프 Multi-Cut, Quad Draw, 키) 을 켤 수 없게 된다.

### 결정 (delegated)
1. **화면 트리** (Maya General 순서): topbar | strip (Status Line + Shelf, 전체 폭) | [툴박스 3D 뷰 56 | Outliner 260 | 3D 뷰 + 사이드바 도크 260] |
   타임라인 전체 폭 (WINDOW = Time Slider 36, 헤더를 아래로 뒤집어 = Range Slider 줄) | 상태 바 (Help Line + Command Line 한 줄).
   오른쪽 Outliner(Layer Editor)·Properties(AE) 열은 없앤다: CB/LE·AE 는 이미 사이드바 도크 (`maya_kit_dock`) 에 있다.
2. **툴박스** = 왼쪽 끝 좁은 3D 뷰 (툴바만; 헤더·툴 헤더·사이드바·오버레이·기즈모 끔) — Blender 툴 시스템을 그대로 쓰므로 활성 툴
   강조·툴팁·더블클릭이 같다. 툴 목록은 `VIEW3D_PT_tools_active` 의 **그리기만** 거른다 (`_tools` 는 그대로 — 위 실측 이유,
   요청 "_tools 교체" 와 다름): Select (box) / Lasso / Paint Select (circle) / Move / Rotate / Scale / — / 마지막 툴
   (`tool_keys.LAST`), 모든 모드 같음 (없는 모드는 원래 목록). 아래에 빠른 레이아웃 패널 (Single Perspective, Four View,
   Front/Persp 회색, Outliner). 좁은 뷰의 빈 아래쪽 클릭이 WINDOW 로 넘어가 선택을 지우지 않게: 오브젝트 없는 로컬 뷰 (실측 후 결정).
   kit 그리기 (그리드·가구·선택 와이어) 는 이미 `show_overlays` 를 보므로 툴박스 뷰는 오버레이 끔.
3. **사이드바 탭**: 환경설정 「Maya Dock Only」 (기본 켬) — kit 이 아닌 VIEW_3D 사이드바 패널 (Item/Tool/View, 그 외 등록돼 있던 것)
   을 poll 래퍼로 숨긴다 (사이드바 UI 영역에서만; `wm.call_panel` 팝업은 그대로). poll 이 없던 패널은 C 가 등록 때만 poll 을 보므로
   등록 해제 → poll 추가 → 재등록 (자식 먼저 해제, 부모 먼저 등록), 끌 때 원래대로. kit 사이드바 Outliner 탭도 같은 옵션으로 숨김.
4. **툴 헤더 숨김** (템플릿 3D 뷰). **상태 바**: `STATUSBAR_HT_header.draw` 교체 — Help Line (33.75 units = 675 px) 왼쪽, Command
   Line (45.75 units = 915 px) 오른쪽, Blender 입력 힌트·보고·진행은 Help Line 칸에 (Maya Help Line 도 진행 표시). 둘 다 끄면 원래 draw.
5. Status Line 편집기 토글: Properties 영역이 없으면 Attribute Editor = 도크 AE 전환, Render Settings = Properties 새 창.
6. 셸프 높이 (Maya 64, kit 26) 는 step 51 (셸프 모양) — 그래서 가운데 줄의 y 는 Maya 보다 ~54 px 위. rects.md 는 축별 Δ 를 그대로
   보고한다 (x/w 맞춤, y/h 는 51 뒤).

### 검증 계획
- `tools/look_compare.py` rects.md: 툴박스·Outliner·뷰·도크·Time/Range Slider·Help/Command 의 x/w ±10 px, 하단 줄 y/h ±10 px.
- 헤드리스: 템플릿 영역 구성·설정 (`test_step5_layout`/`test_step31_layout` 갱신), 새 `test_step49_layout` (툴박스 목록 모든 모드,
  Dock Only 숨김/복원, 상태 바 draw 교체/복원, 툴박스 뷰 판별), `test_enable_disable` 누수 0.
- GUI: 툴박스 버튼 클릭 → 툴 바뀜, 툴박스 빈 곳 클릭 → 선택 유지, 사이드바 탭 없음, 하단 줄 위치. 두 배율.
- release 스크린샷 재생성, 나란히 이미지 직접 확인.

### 구현 중 바뀐 것 (delegated)
- 툴박스 열의 빈 곳 클릭: 빈 로컬 뷰는 Blender 가 파일을 읽을 때 버림 (실측) → 그 뷰에서 모든 오브젝트 종류를 숨김
  (`show_object_viewport_*`, 뒤에 아무것도 안 그림, 박스/라쏘 선택 무해). 그래도 `view3d.select` 클릭은 숨은 종류까지 해제함
  (실측) → `maya_kit.toolbox_guard` 를 "3D View" 키맵 맨 앞에 (툴박스 뷰에서만 클릭을 삼킴, 그 밖은 PASS_THROUGH).
- 사이드바: Item 탭의 Transform 은 **C 패널** 이라 Python 으로 못 숨김. 저장된 활성 탭이 없으면 Blender 가 Item 을 열어서,
  생성기가 임시 "Channel Box" 패널을 등록하고 Ctrl+휠로 그 탭을 골라 저장 (영역이 활성 카테고리를 파일에 저장함). 오브젝트를 고르면
  Item 탭은 여전히 생김 (남은 것).
- 도크 폭 = 260 + 17 (Maya 도크 탭 줄 자리, Blender 탭 줄은 사이드바 안) = 277 → 뷰 패널 x/w, 도크 x 가 맞음.
- Status Line + Shelf: 높이 고정의 한 영역 (헤더 + 툴 헤더) 은 UI 배율 1.25 에서 툴 헤더 (셸프) 가 사라짐 (실측) → 헤더만 있는
  두 영역 (`.MayaKitStrip` Status Line, `.MayaKitShelf` 셸프). Blender 는 모든 영역을 헤더 높이 이상으로 키우므로 어느 배율에서나 보임.
  Shelf 토글로 다른 레이아웃에 만드는 줄은 예전처럼 한 영역 두 줄.
- 툴박스 열 폭: 영역 크기는 UI 배율을 따라가지 않음. `screen.area_move` 의 poll 은 마우스가 어느 영역 위에 있으면 False (실측:
  영역 경계 위에서만 True) → 0.5 s 타이머가 될 때 한 열 폭 (56 × 배율) 으로 맞추고, 그 전까지 열이 좁으면 메인 뷰에 툴바를 보임
  (`toolbox.fit_columns`). Maya Density (Make Blender Maya 가 켬) 에서는 템플릿 그대로 맞음.
- 상태 바: `STATUSBAR_HT_header.draw` 교체 (다른 애드온이 append 한 항목은 Command Line 뒤에 그림), 해제 시 복원.

## 한 것
- `tools/make_startup.py`: GUI Blender 에서 실행 (창 1600x900, 실효 배율 1.0, 이벤트 시뮬레이션, 샌드박스). 팩토리 타임라인·오른쪽
  열 닫기 → Status Line 줄 / Shelf 줄 / [툴박스 56 | Outliner 260 | 뷰 + 사이드바 277] / 타임라인 (헤더를 아래로 = Range Slider) 분할,
  사이드바 폭 드래그, Channel Box 탭 선택, 툴 헤더·뷰 툴바 끔.
- `ui/toolbox.py` (새): Maya 툴 목록 그리기 필터 (Select/Lasso/Paint Select/Move/Rotate/Scale/—/마지막 툴), 빠른 레이아웃 패널
  (Single, Four, Front/Persp 회색, Outliner), `toolbox_guard`, 열 폭 맞춤 + 툴바 대체. 환경설정 「Maya Tool Box」.
- `ui/dock_tabs.py` (새): 「Channel Box Dock Only」 — kit 아닌 3D 뷰 사이드바 패널을 poll 래퍼로 재등록 (순서 유지), 해제 시 복원.
  kit 사이드바 Outliner 탭도 같은 옵션.
- `command_line`: Help Line (33.75 units = 675 px) | Command Line (45.75 units = 915 px) 한 줄.
- `ui/shelf.py`: 셸프 줄 영역 (`SHELF_MARKER`, 헤더에 셸프). `ui/status_line.py`: AE 버튼 = 도크 AE (Properties 없을 때),
  Render Settings = Properties 새 창 (`open_editor` 에 PROPERTIES + tab).
- look 도구: `toolbox`, `shelf`, `view3d.pane`, `statusbar.help/command` 앵커, rects.md 축별 열.
- 테스트: 새 `test_step49_layout` (10), `gui_step49_layout` (16); test_step5/12/31/41, gui_step5/7/11/12, `tests/kit.py` 스냅숏
  (툴바 draw·tools_from_context, 상태 바 draw, 사이드바 패널 poll), `sim.view3d` = 가장 큰 3D 뷰. release_shots 07 = 왼쪽 Outliner.

## 검증
- 헤드리스 **385/385** (step 48: 375). `test_enable_disable` 누수 0.
- GUI 전체 **307/307** (배율 1.25) · **307/307** (`--ui-scale 0.8`) (step 47: 293).
- look_compare rects **1/12 → 4/12** (모든 축 ±10 px), 축별로는 크게 개선: 메뉴바·Status Line·Help Line·Command Line ✓;
  툴박스 x, Outliner w, 뷰 패널 x w, 도크 x y, Time/Range Slider x w h, Shelf x y w. density 3/3, 테마 ΔE>5 0/38, furniture 3/3.
- release_check: validate·설치·켜기 PASS, 스크린샷 7장 재생성 (직접 봄: 01_layout, 07).
- 나란히 이미지 compare/01·07·11 직접 확인: 툴박스 열·Outliner·도크·하단 줄이 Maya 와 같은 자리.

## 남은 것
- y 축: 셸프 줄 26 px (Maya 64) 라 가운데 줄이 ~32 px 위, 하단 줄은 C 헤더 높이 (Range 26 vs 31, 상태 바 23 vs 28) 라 Time Slider 가
  24 px 아래 → step 51 (셸프 아이콘 줄 높이) 에서 다시 잼.
- 툴박스 폭 56 (Maya 40): C 상수 `UI_TOOLBAR_WIDTH`. Outliner x +11.
- AE 탭 폭 460 (Maya) — 사이드바 폭은 API 로 못 바꿈. Item 탭 (C 패널) 은 오브젝트 선택 시 보임. Modeling Toolkit 탭은 step 60.
- 배율 > 1.0 + Maya Density 끔: 툴박스 열이 좁은 동안 메인 뷰 툴바로 대체 (release 스크린샷이 이 상태).
- 수동 확인: `docs/manual_checks.md` 「Step 49」.
