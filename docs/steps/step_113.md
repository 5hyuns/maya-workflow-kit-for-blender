# Step 113 — Top area like Maya: menu bar, Status Line, Shelf, panel bar

User feedback 2026-10-19 (`hermes/autodrive_bmk/user_top_1019.png`, 125 %, Blender's own theme): 「상단부분이 너무 애매해서
마야 같다는 느낌이 전혀 안 든다」.

## Maya reference

Maya 2022 GUI, factory prefs, main window 1600×900, DPR 1.0 (`research/scripts/maya_top113/`: `launch.ps1` +
`top113.py`, Maya closed by the script): `research/maya/screens/top113/t01_full.png`, `t02_top.png`, per-widget grabs
`w/`, geometry / class / font of every visible widget in `_top113.json`. Rows (y, height): menu bar 0–27, Status Line
29–56 (icons 20 px on a 23 px pitch, fields 100×22), Shelf 62–126 (tab bar 18 px, 11 px Segoe UI; icons 32 px, pitch
35, group separators 12 px), panel menu bar 133–152 (19 px), panel toolbar 153–171 (16 px icons, pitch 19). Every
background #444444 except the shelf tab strip #373737.

## 차이 (행·요소)

| Row | Maya 2022 | Kit before (`user_top_1019.png`, `tmp/s113/cmp_before.png`) | Fix |
|---|---|---|---|
| Menu bar | File … Help only, items = text + ~11 px | menu set dropdown between Windows and Mesh; Blender pulldown padding, at 125 % the bar ends at "Cach…" | dropdown moves to the Status Line; items sized from the measured text + Maya's padding |
| Menu bar right | `Workspace:` label + dropdown (+ lock) | Blender workspace ID field (screen icon, name, ✕) | label + dropdown of workspaces |
| Menu bar right | — | `Maya` / `Blender` blue toggle | kept, flat text, the inactive mode dim |
| Status Line left | grip, menu set combo (100 px) | file icons first | menu set dropdown first |
| Status Line groups | `|` bar … `▷` collapse arrow; masks, history, input line collapsed | Blender GRIP_V / triangle; masks, history, input line open | kit-drawn bar / arrow icons; Maya's collapsed groups collapsed |
| Status Line icons | flat light-grey glyphs, teal snap magnets, no button box, active = blue square | Blender's coloured icons in embossed boxes | kit-drawn Maya-style icons (`ui/status_icons.py`, code-drawn, CC0-able), flat, box only when active |
| Status Line right | sidebar toggles right-aligned | toggles follow the input line | spacer, toggles at the right end |
| Shelf tabs | 18 px tab strip, small flat tabs, active lighter, `≡` at the left | 26 px Blender header with buttons + gear | header hidden; tabs drawn in the shelf WINDOW region (blf 11 px), picked by gizmos |
| Shelf icons | distinct pictograms | several buttons fall back to the same orange sphere | new glyphs for the repeated ones |
| Panel menu bar | View Shading Lighting Show Renderer Panels | Blender header: editor type, mode, Maya menus, `Blender ▸`, orientation, pivot, snap, proportional, overlays, shading | in the Maya layout: Maya menus only |
| Panel toolbar | icon row (camera, gates, shading modes, lights, isolate, X-ray …) | none | 3D View tool header = Maya panel toolbar (kit-drawn 16 px icons) |
| Colours | #444444 everywhere, tab strip #373737 | Blender's theme (#303030 / #3d3d3d) | Maya mode switches the Maya theme on (the switch already says "Maya keymap, layout, menus and theme") |

## 계획 (delegated)

1. Menu bar (`ui/status_line.py`, `ui/menu_sets.py`): no menu set dropdown when a Status Line is on screen; item widths
   = blf text width + 11 px × scale; right side `Workspace:` + `WindowManager.allset_workspace` enum (get / set the
   window's workspace); switch drawn flat.
2. Status Line: Maya order, groups with drawn `|` / `▷` / `▶`, Maya's collapsed groups, flat icons from
   `ui/status_icons.py` (numpy canvas like `shelf_icons.py`, written into `bpy.utils.previews` pixels — no files),
   editors right-aligned.
3. Shelf: shelf row area without header; the WINDOW handler draws tab strip + icons; tabs / `≡` are gizmos.
4. Panel bar: `VIEW3D_HT_header`'s own draw replaced (like `editor_chrome`, restored on unregister, snapshotted) for
   3D Views of the Maya layout (screen has the Maya strip) — Maya menus only; tool header shown there = panel toolbar.
5. Maya mode switch turns the Maya theme on (snapshot restores the user's theme on the switch back).
6. Verify: same 1600×900 grab (effective 1.0 and 1.25), Maya / before / after stacked in `docs/steps/step_113/`, GUI
   regression test.

Distribution steps (114–116): no new class-draw replacements outside Maya mode; every replaced draw restored on
unregister and listed in `tests/kit.py`; icons are generated at run time (no binary files).

## 한 것

- Maya 측정: `research/scripts/maya_top113/` (Maya 2022 GUI, 공장 설정, 1600×900, 끝나면 스크립트가 Maya 종료) →
  `research/maya/screens/top113/` (전체·상단 그림, 위젯별 그림, `_top113.json`: 메뉴 막대 항목 폭, Status Line 위젯 위치,
  셸프 8 개의 아이콘·구분선 순서, 패널 메뉴·툴바).
- 메뉴 막대 (`ui/menu_sets.py`, `ui/status_line.py`, `switch.py`): Status Line 이 화면에 있으면 메뉴셋 드롭다운 없음
  (`status_line_shown`), 항목 폭 = blf 로 잰 글자 폭 + Maya 여백 11 px (`menu_width_units`) → 125 % 1600 px 에서도 Help
  까지 보임; 오른쪽 `Workspace:` + 작업 공간 드롭다운 (`WindowManager.allset_workspace`, Blender ID 칸·✕·화면 아이콘 없음);
  Maya | Blender 전환은 테두리 없는 글자, 현재 모드만 밝게.
- Status Line: 메뉴셋 드롭다운이 맨 앞, Maya 그룹 `| 버튼 ▷` (모으면 `| ▶`), Maya 공장값처럼 마스크·히스토리·입력 줄은 접힌
  상태로 시작 (`DEFAULT_COLLAPSED`), 스냅 6 개 (Projected Center 회색 추가), 렌더 그룹에 Render Setup (회색)·Light Editor·
  Pause (회색), 사이드바 토글은 오른쪽 끝 (Character Controls 회색 추가). 아이콘은 킷이 그린 Maya 풍 글리프
  (`ui/status_icons.py`: numpy 캔버스 → `bpy.utils.previews` 픽셀, 파일 없음), 눌린 버튼만 테두리. No Live Surface /
  Symmetry 는 ▾ + 글자 칸 (Scene 읽기 전용 문자열).
- 셸프 (`ui/shelf.py`): 셸프 줄의 머리 영역을 없애고 WINDOW 한 영역에 Maya 64 px 블록을 그림 — 18 px 탭 줄 (#373737,
  11 px 글자, 현재 탭 밝게), 왼쪽 ≡ (셸프 고르기)·톱니 (셸프 편집), x 43 부터 32 px 아이콘, Maya 셸프 구분선
  (`shelf_data.GAPS`, Maya 그림에서 잰 위치; 생성기 `tools/gen_shelf_data.py`). 탭·≡·톱니는 기즈모로 클릭.
  예전 파일은 `toolbox.fit_columns` 가 셸프 머리를 끔. 아이콘: 같은 그림을 쓰던 버튼에 새 글리프 (Reduce, Remesh,
  Retopologize, Merge To Center, Collapse, Target Weld, UV Planar / Cylindrical / Spherical / Automatic / Contour Stretch /
  3D Grab, 조명 5 종) + 남은 중복엔 구분 글자 배지 (`badge_text`: Parent / Point / Orient Constraint → PA / PO / OR).
- 패널 바 (`ui/panel_toolbar.py`): Allset 레이아웃의 3D View 에서 `VIEW3D_HT_header` 자신의 draw = Maya 패널 메뉴만
  (편집기 버튼·모드·Blender ▸·방향·피벗·스냅·비례 편집·오버레이·셰이딩 없음), `VIEW3D_HT_tool_header` 자신의 draw =
  Maya 패널 툴바 (카메라 7, 그리드·게이트 7, 셰이딩·조명 7, 효과 4, 아이솔레이트·X-ray 4, 노출·감마·뷰 변환; Blender 에
  없는 것은 회색). 다른 레이아웃은 Blender 헤더 그대로. 등록 해제 때 원래 draw 복원, `tests/kit.py` 스냅샷에 추가.
  템플릿 3D View 는 tool header 를 켬 (`tools/make_startup.py`, `switch._fit_views`).
- 색: Maya 모드로 전환하면 Maya 테마가 켜짐 (전환 설명이 이미 「keymap, layout, menus and theme」; Blender 로 돌아가면
  스냅샷의 사용자 테마로 복원) — delegated.
- 테스트: `tests/gui/gui_step113_top.py` (사용자 경로: Maya 모드 끄고 켜기 → Maya 테마·레이아웃; 메뉴셋 드롭다운 없음,
  메뉴 18 개 + 오른쪽이 1600 px 안, 셸프 머리 없음·그린 탭 클릭으로 셸프 바뀜, 패널 툴바, 화면 픽셀 메뉴 막대 #444444 ·
  탭 줄 #373737, Blender 로 돌아가면 테마 복원; 10 개). 바뀐 설계에 맞춘 기존 테스트: test_step51 (접기 화살표·글리프 그리기),
  test_step5 / gui_step7 (tool header = 패널 툴바), test_step7 (Workspace 드롭다운), gui_step12 / 49 / 51 (셸프 줄은 WINDOW,
  File 접기 화살표 위치, 접힌 그룹은 콤보 바로 뒤의 ▶), gui_step75 (입력 줄 그룹을 먼저 펼침), `tests/kit.py` (VIEW3D 헤더 두
  클래스의 자기 draw 스냅샷).
- 비교 그림 (`docs/steps/step_113/`): `compare_100.png` (Maya / 이전 / 이후, 실효 배율 1.0), `compare_125.png` (이전 / 이후,
  125 %), `status_zoom.png` (Status Line 2 배: Maya / 킷), `shelf_icons.png` (셸프 8 개 아이콘 전체).

## 검증

- GUI `gui_step113_top` 10/10 (1.25, 0.8 = 실효 1.0), 그림을 직접 봄: 125 % 에서도 메뉴 막대 Help 까지, 탭 줄·아이콘 줄이
  Maya 블록처럼, 패널 바는 Maya 메뉴 + 아이콘 줄만.
- 헤드리스 851/851, GUI 전체 1093/1093 (1083 + 10). 첫 전체 실행에서 python311.dll 접근 위반 3 건 (Workspace 드롭다운의
  enum 항목 목록을 그릴 때마다 새로 만들어 이전 문자열이 풀림) → 이름 집합별로 캐시해 고정, 아이콘 미리보기는 등록 뒤 타이머에서
  만듦; 다시 돌려 0 건.

## 남은 것

- 셸프 줄 왼쪽 `‹`·오른쪽 위 `⌄`: 숨긴 영역(툴바·머리)의 Blender 화살표는 API 로 끌 수 없음.
- 커서 맞춤이 안 되면 (사용자 세션처럼) 125 % 의 셸프 줄은 템플릿 높이(약 56–64 px) 그대로라 아이콘이 28 px 정도로 작아짐
  (탭 줄 24 px 를 빼고 맞춤).
- 상태 줄 아이콘은 Blender 버튼 아이콘 크기 16 px × 배율 (Maya 20 px; 125 % 에서는 20 px 로 같음). 비활성(회색) 버튼은
  Blender 처럼 흐리게 보임 — Maya 는 같은 밝기.
- Outliner 의 Display / Show / Help · 검색 칸은 Maya Outliner 도 같은 메뉴라 그대로 둠 (Maya 는 검색 칸이 메뉴 아래 줄).
- Blender 헤더가 필요한 사람: 다른 작업 공간(레이아웃)은 Blender 헤더 그대로, Allset 레이아웃에서는 Blender 메뉴는 위
  Blender 로고 메뉴와 F3 검색으로.
