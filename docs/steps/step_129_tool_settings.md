# Step 129 (Tool Settings lane) — Tool Box double-click (#3), Tool Settings for every Tool Box / Mesh Tools tool (#28, #29)

## 계획 (delegated)

근거: Maya 2022 GUI 캡처 `research/scripts/maya_ts129/ts129.py` (`launch.ps1`, `MAYA_APP_DIR` = `tmp/maya_app_ts129`,
공장 설정; 두 번째 실행은 `MK_ONLY=...` 로 edge 모드가 필요한 툴만) → `research/maya/screens/ts129/_ts129.json`,
`_ts129_insert_edge_loop.json` + 그림 `<tool>_ts_full0.png`. 각 툴 = 메뉴의 runTimeCommand (`research/maya/menus.json`
rtc) 실행 → `toolPropertyWindow` → 접힌 절을 모두 펼쳐 위젯 (글자, 체크, 값) 기록. research/ 는 추적하지 않는다.

### 1. Tool Box 더블클릭 → Tool Settings (#3)

- Maya: Tool Box 버튼 더블클릭 = 그 툴의 `toolPropertyWindow` (research/maya/ui_layout.md:224-227, toolbox.mel:306-307).
- Blender 의 툴 버튼은 UI 버튼이라 더블클릭이 키맵에 오지 않는다 (#3 근본 원인). 그러나 버튼은 매 클릭마다
  `wm.tool_set_by_id` 를 실행하고 (두 번째 클릭의 DOUBLE_CLICK 은 버튼이 안 받으면 PRESS 로 다시 보내진다) 그 실행은
  `bl_ui.space_toolsystem_common.activate_by_id` 를 **호출 시점에 import** 한다 (`$S\startup\bl_operators\wm.py:2338-2347`).
- 설계: `ui/toolbox.py` 가 그 모듈 함수를 감싼다 (등록 해제 때 원래 함수로; `tests/kit.py` snapshot). 3D View 의
  TOOLS 영역 (툴바 버튼) 에서 같은 툴이 `preferences.inputs.mouse_double_click_time` 안에 두 번 켜지면 (= 더블클릭)
  타이머로 `tool_dock.show` — 어느 창에든 도크가 있으면 다시 그리기 (Blender 는 OS 창을 앞으로 올릴 수 없다), 없으면
  메인 창 왼쪽에 연다 (step 106 의 도크; Maya 공장 상태의 떠 있는 창 대신 도크로 여는 것은 step 106 결정). 키 (Q/W/E,
  WINDOW 영역) 두 번은 열지 않는다 (Maya 도 단축키 두 번은 열지 않음).

### 2. 툴별 Maya 절 (#28, #29)

`ui/tool_settings.py`: `KINDS` (Move/Rotate/Scale) 에 `TOOLS` (idname → 종류) 를 더해 `tool_kind` 가 모두 돌려준다;
`SECTIONS` 의 열림 = 종류별 (Common Selection Options 는 Select 에서 펼침, Move 에서 접힘). 종류가 있는 툴은 도크에서
Blender 툴 패널을 숨긴다 (`dock_tabs`, 기존 규칙). 회색 줄 = `allset.menu_unavailable` + `TS_NOTICES` (툴팁 한 줄).
값 설정 = 새 `allset.ts_option` (라디오 → Blender 툴 연산자 속성 조합).

| Maya 툴 (rtc) | Blender 툴 | Maya 절 (순서, 처음 펼침) | 연결 / 기본값 (Maya 2022 공장) |
|---|---|---|---|
| Select Tool (SelectTool, selectSuperContext) | `builtin.select_box`, `builtin.select` (Tweak) | Common Selection Options (펼침), Soft Selection, Symmetry Settings | step 106 의 `draw_selection` / `draw_soft` / 대칭 재사용: Marquee ●, Camera-based (WM 속성), Drag = Paint Selection Tool 로 회색, Highlight nearest ☑ (kit pref) |
| Lasso Tool (LassoTool) | `builtin.select_lasso` | Lasso Settings (펼침), Soft Selection, Symmetry Settings | Draw style Closed ● (Blender 올가미는 항상 닫힘, Open 회색), Component selection Fast ● → 회색 (Blender 는 화면 위치로 고름) |
| Paint Selection Tool (ArtPaintSelectTool, artSelectContext) | `builtin.select_circle` | Brush (펼침), Paint Operations (펼침), Stroke, Stylus Pressure, Attribute Maps, Display | Radius(U) = `view3d.select_circle.radius` (Blender 는 px, 툴팁), Radius(L) / Profile / Rotate to stroke 회색; Paint operation Select ● + Add to current selection ☑ = mode ADD, Select ☐ = SET, Unselect = SUB, Toggle 회색; Select All / Unselect All / Toggle All = `select_all` (모드별); Stroke / Stylus / Attribute Maps / Display 회색 |
| Insert Edge Loop Tool (SplitEdgeRingTool) | `builtin.loop_cut` | Description, Settings (펼침) | Maintain position: Relative ● = cuts 1 + even off, Equal distance = `edge_slide.use_even`, Multiple edge loops = `loopcut.number_cuts` (Number of edge loops 2); Use Equal Multiplier ☑ / Auto complete ☑ / Fix Quads ☑ / Insert with edge flow ☐ / Adjust Edge Flow 1 / Smoothing angle 30 회색 |
| Slide Edge Tool (SlideEdgeTool) | `builtin.edge_slide` | Description, Settings (펼침), Snapping Settings (펼침) | Mode Relative ● = `use_even` off, Absolute = on; Use Snapping ☑ / Snapping Points 1 / Tolerance 0.1 회색 |
| Target Weld Tool (MergeVertexTool) | `allset.target_weld_tool` | Description, Settings (펼침), Keyboard/Mouse Shortcuts (접힘) | Merge To Target ● / Center, Preserve UVs ☑ (`Scene.allset_mesh_tools`, step 64); LMB 끌기 = 병합, MMB (가운데로) 회색 |
| Crease Tool (PolyCreaseTool) | `allset.crease_tool` | Description, Settings (펼침) | Mode Absolute ● / Relative; Extend to creased components 회색 (기존 notice) |
| Quad Draw (QuadDrawTool) / Create Polygon / Append to Polygon | `builtin.poly_build` (셋 다) | Settings, Live Constraint Options, Keyboard/Mouse Shortcuts | 자리표시: Maya 칸 (Auto-weld 10, Relax Auto-Lock, Extend Edge, Quad Strip Width 20, Clear Dots, 색 설정) 회색 + Blender Poly Build 키를 키맵에서 읽어 단축키 절에 표시 |

Multi-Cut 은 다른 lane (WorkSpaceTool `draw_settings`): 종류가 없으므로 도크는 머리 줄 + Blender 툴 패널 (그 draw_settings
포함). 참고 측정: Maya 2022 Multi-Cut 공장값 Snap Step % **10**, Smoothing Angle 180, Edge Flow ☐, Subdivisions 1.

Reset Tool: 툴 연산자 속성 되돌림 (기존) + 종류별 Maya 값: Paint Selection mode ADD (Maya Add to current selection ☑ —
Blender 기본 SET), Target Weld Target + Preserve UVs, Crease Absolute. (delegated: Maya 값과 다른 Blender 툴 기본값은
Reset Tool 에서만 바꾼다 — 파일의 작업 공간 데이터를 몰래 쓰지 않는다.)

### 검증

- 헤드리스 `tests/test_step129_tool_settings.py`: 툴마다 절 순서·펼침이 Maya 와 같다, 줄이 kit / Blender 속성에 묶인다,
  회색 줄마다 툴팁, `ts_option` 이 라디오를 연산자 속성으로 바꾼다, Reset 이 Maya 값, 도크가 이 툴들에서 Blender 패널을
  숨긴다, 더블클릭 판정 (TOOLS 영역 + 시간 안 + 같은 툴), `activate_by_id` 감싸기 등록 / 해제.
- GUI `tests/gui/gui_step129_tool_settings.py`: Tool Box 의 Lasso 아이콘을 두 번 클릭 (시뮬레이션 이벤트) → 도크가 열리고
  Lasso 절; 한 번 클릭 = 안 열림; Select 툴 = Soft Selection / Common Selection Options; 도크 스크린샷.

## 한 것

- `ui/toolbox.py`: `space_toolsystem_common.activate_by_id` 감싸기 (`_saved`, 해제 때 복원, `tests/kit.py` snapshot).
  측정: 툴바 버튼의 연산자도 키처럼 뷰의 **WINDOW** 영역에서 실행된다 (TOOLS 가 아님) — 그래서 `_draw_begin` 이 툴바
  layout 에 `context_pointer_set("allset_toolbar", space)` 를 걸고, 그 멤버가 있는 실행만 클릭으로 센다
  (`note_tool_click`). 더블클릭 → 타이머 → `tool_dock.show` (어느 창이든 도크가 있으면 다시 그리기, 없으면 연다).
- `ui/tool_settings.py`: `TOOLS` / `KIND_OF`, 절 표 확장 (열림 = bool 또는 종류 목록), 툴별 그리기, `allset.ts_option`
  (paint_op / paint_add / select_all / iel_position / slide_mode), `reset_kind_defaults`, `TS_NOTICES` 31 줄 추가,
  "Drag" 안내를 일반 문장으로. 패널 id 는 `allset_ts_<kind>_<key>` (툴마다 처음 펼침이 다르다).
- `ui/tool_dock.py`: `show`.

## 검증

- `ALLSET_SANDBOX=lane_ts python tests/run.py`: 903 passed, 5 failed — 5 개는 worktree 에 research/ 가 없어서
  (hotkeys_default.json 등). research 를 연결해 다시: `-k keymap_maya,step107,step108,step120,step129,enable_disable,
  step106,step93` 77 passed, 0 failed.
- GUI `-k gui_step129_tool_settings` 10/10 (한 번 클릭 = 안 열림, 더블클릭 = 도크 + Lasso 절, 다시 더블클릭 = 도크 하나,
  Select / Paint Selection / Insert Edge Loop 절, Multi-Cut = Blender 패널). 기존 GUI `-k step106,step93,step49` 33/33.
- 스크린샷 확인: Select (Common Selection Options 펼침), Paint Selection (Brush, Paint Operations 펼침).

## 남은 것

- Paint Selection 의 Blender 기본 mode 는 SET (Maya 는 Add ☑): Reset Tool 에서만 Maya 값 (위 delegated).
- Quad Draw / Create Polygon / Append to Polygon 은 한 Blender 툴 (Poly Build) 이라 모두 "Quad Draw Tool" 제목.
- Multi-Cut 은 다른 lane; Maya 2022 공장 Snap Step % 는 10 으로 측정됨 (kit 상수 확인 필요).
- 다른 lane 이 Insert Edge Loop 를 kit 툴로 바꾸면 `TOOLS` 의 idname 도 바꿔야 한다.
