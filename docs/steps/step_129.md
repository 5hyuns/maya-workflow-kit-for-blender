# Step 129 — Fix batch for 0.2.1 (#36 crash + user-report issues + P1 audit issues)

## 계획

- 순서상 먼저: `origin/hotfix/crash-36` merge (menu_extras 타이머가 Window 를 포인터로 재조회). 그다음 같은 패턴을 모든
  `bpy.app.timers.register` 46곳에 적용 (레인 T).
- 범위 (delegated): user-report 이슈 전부 (#1–#14, #22, #27, #28, #36, #37, #38) + P1 audit (#19, #20, #26, #39); 같은 원인으로 묶이는
  #15 (#1), #29 (#28), #24 (#10 계열), #17/#18 (#39 의 컴포넌트 모드 표). #23 아이콘·#25 Hypershade 는 step 130.
  나머지 P2/P3 audit 이슈 → 마일스톤 0.3.0, 이번에 고친 것 → 0.2.1.
- 병렬 레인 (worktree 격리, 파일 소유 단위로 나눔; 같은 파일을 만지는 레인끼리는 hunk 단위 병합):
  | 레인 | 이슈 | 주 파일 |
  |---|---|---|
  | T timers | #36 패턴 전수 | 46 타이머 사이트, `src/allset/live_refs.py` |
  | S softsel | #1 #2 #15 | operators/taphold.py, 새 soft select 표시 모듈 |
  | TS tool settings | #3 #28 #29 | ui/tool_settings.py, ui/toolbox.py(더블클릭), ui/tool_dock.py |
  | MC multi-cut | #27 (+ #28 Multi-Cut 옵션) | 새 operators/multi_cut.py, ui/mesh_tools.py |
  | P prims | #11 #12 | operators/create.py, INPUTS (channel_box / history) |
  | V viewport | #10 #13 #24 #8 #9 | ui/panel_toolbar.py, ui/panel_menus.py, ui/uv_toolkit.py, status_line IPR, quick layout, operators/framing.py |
  | M marking | #5 | marking/ |
  | CB channel box | #6 #7 #26 | ui/channel_box.py, ui/cb_entry.py, ui/layer_editor.py, operators/visibility.py |
  | X misc | #4 #14 #22 #37 #38 | ui/maya_dock.py tear-off, material display, loop select, auto key, time slider ticks |
  | A audit P1 | #19 #20 #39 (#17 #18) | switch.py, operators/skin.py, ui/menu_sets.py edit-mode table |
- 순차인 것: hotfix merge → 레인 시작 (모든 레인이 merge 된 HEAD 에서 출발해야 함); 레인 병합 → 헤드리스 전체 → GUI 전체 1회.
