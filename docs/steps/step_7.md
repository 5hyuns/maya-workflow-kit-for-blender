# Step 7 — M2-c 상단 UI: Status Line, 메뉴셋, 커맨드 라인, Help Line

## 계획

근거: `research/maya/ui_layout.md` §4.1 메뉴바·메뉴셋 (:170-192), §4.2 Status Line (:193-217), §4.12 Command Line (:290-293), §4.13 Help Line (:295-298); `research/maya/menus.json` / `menus.md` (메뉴셋별 메뉴 트리 42 메뉴); `research/blender/api_limits.md` #10 (TOPBAR/STATUSBAR 확장 :80-81), #14 (커맨드 라인 :93-94); `$S\startup\bl_ui\space_topbar.py:14-62` (`TOPBAR_HT_upper_bar.draw_left/draw_right`), `space_statusbar.py:8-31`, `$S\modules\bpy_types.py:1058-1146` (append/prepend/`_draw_funcs`).

사용자 지시 범위: Status Line(메뉴셋 드롭다운, 선택 마스크, 스냅 토글, 렌더 버튼), 커맨드 라인(Python exec, 결과/오류, MEL 안내, `cmds_shim`), Help Line, 메뉴셋 전환 시 상단 메뉴 교체(매핑되는 항목만 활성, 없는 것은 회색). PLAN #7 의 Range Slider·타임라인 모양·`.` `,` 키는 이번 지시에 없어서 뒤로 미룬다 (「남은 것」).

### 1. 상단 바 (TOPBAR) — delegated

- Blender TOPBAR 는 한 줄(왼쪽 영역 = 메뉴 + 워크스페이스 탭, 오른쪽 영역 = 씬/뷰 레이어)이다. Maya 는 메뉴바와 Status Line 이 두 줄이다. 새 영역 종류는 만들 수 없으므로(api_limits #11) **한 줄에 넣는다**: 왼쪽 = Maya 메뉴바, 오른쪽 = Status Line.
- 방법: `TOPBAR_HT_upper_bar.draw_left` / `draw_right` 메서드를 Maya 판으로 바꾸고 unregister 에서 원래 함수로 되돌린다 (`draw` 가 `self.draw_left()` 를 부르므로 다른 애드온이 `append` 한 함수는 그대로 돈다). `_draw_funcs`(비공개) 를 건드리지 않는다. 환경설정 `maya_top_bar`(기본 켬)를 끄면 원래 함수를 그대로 부른다.
- 폭: 워크스페이스 탭(약 700 px)은 Maya 의 워크스페이스 선택기(Status Line 오른쪽 끝, ui_layout.md:216)처럼 **드롭다운**으로 바꿔 오른쪽 끝에 둔다. 씬 선택기는 유지, 뷰 레이어 선택기는 Maya 에 없어 뺀다 (Blender Window 메뉴에서 접근). 1600 px GUI 스크린샷으로 넘침 확인.

### 2. 메뉴셋과 메뉴

- 데이터: `tools/gen_menu_data.py` 가 `research/maya/menus.json` 을 읽어 `src/maya_kit/ui/menu_data.py` 를 만든다 (메뉴 이름·라벨·메뉴셋, 항목 라벨·구분선·하위 메뉴 트리만; MEL 명령 문자열은 넣지 않음 — decision 6). 정리: `<dynamic:...>` 라벨은 알려진 것만 이름을 붙이고(`$QuitLabel` → Exit, `$kIncrementAndSaveLabel` → Increment and Save) 나머지는 버림, 따옴표·괄호가 섞인 파싱 잔재 버림, 연속 중복 라벨 하나로.
- 매핑: 손으로 쓴 `src/maya_kit/ui/menu_map.py` — 키 = 라벨 경로(`"Create/Polygon Primitives/Cube"`, 메뉴 *라벨* 기준이라 Modeling/Rigging/Animation 의 같은 Deform·Constrain 메뉴에 한 번에 적용). 값 종류:
  - `"op.id"` / `("op.id", {props})` — 그 자리에서 `layout.operator` (poll 이 실패하면 Blender 가 자동으로 회색: 예 편집 모드 전용 명령은 오브젝트 모드에서 회색).
  - `("v3d", "op.id", {props})` — 3D 뷰 영역/리전이 필요한 연산자(모달 베벨, 플레이블라스트 등): `maya_kit.menu_run` 이 가장 큰 3D 뷰로 `temp_override` 해서 INVOKE.
  - `("tool", "builtin.x", edit)` — 툴 전환 (`wm.tool_set_by_id`), `edit=True` 면 메시를 먼저 컴포넌트(편집) 모드로 (Maya 에서 Multi-Cut 을 고르면 컴포넌트 편집으로 들어가는 것과 같게 [I]).
  - `("menu", "MENU_ID")` — Blender 메뉴를 하위 메뉴로 (Import/Export, Recent Files 등).
  - 매핑 없음 → `maya_kit.menu_unavailable` (poll 항상 False → 회색, 툴팁에 "No Blender equivalent in Maya Kit yet").
- 클래스: 메뉴(와 하위 메뉴) 하나당 `MAYAKIT_MT_mm_<n>` 를 데이터에서 동적으로 생성·등록. 핫박스(Step 9)가 같은 메뉴를 `wm.call_menu` 로 열 수 있게 `menu_sets.menu_idname(maya_name)` 공개.
- 메뉴바 순서 (ui_layout.md:172-175): Blender 로고 메뉴, 공통 File Edit Create Select Modify Display Windows, **메뉴셋 드롭다운**, 현재 메뉴셋 메뉴들, Cache, Help. Maya 는 드롭다운이 Status Line 맨 왼쪽(:196)이지만 한 줄 배치에서는 바뀌는 메뉴 바로 앞에 두는 것이 관계가 잘 보인다 (delegated).
- Blender 메뉴 보존: Maya File/Edit/Windows/Help/Render 끝에 "Blender File/Edit/Window/Help/Render ▸" 하위 메뉴(원래 `TOPBAR_MT_*`). 메뉴바 접기(`show_menus` 꺼짐)도 한 메뉴로 접기.
- 메뉴셋 상태: 애드온 환경설정 `menu_set` (Maya optionVar `currentMenuBarTab` 처럼 세션 간 유지, 기본 Modeling — ui_layout.md:182-183). F2–F6 단축키는 Step 13(셸프/메뉴셋)으로.
- 옵션 박스 `[]` 는 Blender 메뉴에 없음 (C) → 생략, Adjust Last Operation 이 대신 (ui_layout.md:186-187).

### 3. Status Line (오른쪽 영역) — ui_layout.md:193-217

| Maya 그룹 | Blender |
|---|---|
| File: New/Open/Save, Undo/Redo (:198) | `wm.read_homefile` / `wm.open_mainfile` / `wm.save_mainfile` / `ed.undo` / `ed.redo` |
| 선택 모드 Hierarchy/Object/Component (:200) | Object = 오브젝트 모드, Component = 편집 모드(`maya_kit.component_mode` 재사용 아님: 메시가 아니면 `object.mode_set(EDIT)`), Hierarchy = 회색 (Blender 에 루트 선택 모드 없음) |
| 오브젝트 마스크 (:201-204) | 모든 3D 뷰의 `SpaceView3D.show_object_select_*`. Maya 그룹 → 타입: handles·misc → Empty·Speaker·Light Probe, joints → Armature, curves → Curve·Font·Curves, surfaces → Mesh·Surface·Meta·Point Cloud·Volume, deformers → Lattice, dynamics → 회색(Blender 힘장은 Empty), rendering → Camera·Light. 표시 상태 = 가장 큰 3D 뷰 |
| 컴포넌트 마스크 (:205) | `tool_settings.mesh_select_mode` 정점/엣지/면 토글 (여러 개 켜기 = Maya 마스크 여러 개) |
| 스냅 토글 (:207) | grid → `GRID`, curve → `EDGE`, point → `VERTEX`, view plane → 회색, live surface → `FACE_PROJECT`. 버튼 = `maya_kit.snap_toggle`; 켜짐 = `use_snap` 이고 그 요소 포함. **X/C/V 홀드(`operators/hold.py`) 와 같은 `tool_settings` 를 읽으므로 홀드 중에는 그 버튼이 켜져 보인다 (Maya 와 같음 [I]); 홀드 중 버튼을 누르면 놓을 때 홀드 전 상태로 돌아간다** (홀드가 저장한 상태 복원, 문서화) |
| Render (:210) | Render View `render.view_show`, Render `render.render`, IPR = 가장 큰 3D 뷰 셰이딩 RENDERED 토글, Render Settings = Properties 영역을 Render 탭으로 (없으면 보고), Hypershade = "Shading" 워크스페이스 |
| 에디터 토글 (:213-216) | Attribute Editor = Properties 영역을 Object 탭으로, Tool Settings = 3D 뷰 툴 헤더 토글, Channel Box = 3D 뷰 사이드바 토글 (Step 6 Channel Box 탭) |
| 워크스페이스 선택기 (:217) | `template_ID(window, "workspace")` 드롭다운 |

입력 라인(:211, 절대/상대 이동·이름 바꾸기·이름으로 선택), Symmetry(:208), History 토글(:209), 선택 잠금/하이라이트(:206)는 이번에 안 함 (「남은 것」).

### 4. 커맨드 라인 + Help Line (STATUSBAR, `prepend`)

- 배치: 상태바 왼쪽 = `[Python]` 언어 버튼 + 입력 필드 + 결과 필드 + Script Editor 버튼 (ui_layout.md:290-293), 그 뒤 Help Line 문구, 그 뒤 Blender 원래 내용(입력 상태·보고·통계). Maya 는 커맨드 라인과 Help Line 이 두 줄이지만 상태바는 한 줄 (delegated).
- 입력: `WindowManager.maya_kit_cmd` StringProperty, `update` 에서 `command_line.submit()` 호출 → 필드 비우고 결과를 `maya_kit_cmd_result` 에. 실행은 `maya_kit.command_line_exec` 연산자(`REGISTER|UNDO`)를 통해서 → 명령 하나 = 언두 1단계 (GUI 로 확인).
- 실행 (`command_line/runner.py`, 헤드리스 테스트 가능): 네임스페이스 = `bpy`, `C`(context), `D`(data), `cmds`(shim), `mc`; 세션 동안 유지(변수 이어 쓰기). `ast` 로 파싱해 마지막 문장이 식이면 그 값의 `repr` 을 결과로 (Maya Python 커맨드 라인이 결과를 보여주듯 [K]). 예외 → `# Error: <Type>: <msg>` (Maya 결과 표기 [K]) + 결과 필드 붉게(`alert`) + `self.report({'ERROR'})`. stdout 은 캡처해 결과에 마지막 줄.
- MEL 안내: 언어 버튼 클릭 → "MEL is not supported" 보고 (decision 5). 입력이 Python 문법 오류이고 MEL 처럼 보이면 (`;` 로 끝남, `-flag` 인자, `$var`, `polyCube -w 2` 꼴) `# Error: MEL is not supported. Python: cmds.polyCube(w=2)` 처럼 cmds 변환 힌트를 보여준다 (단순 변환: `cmd -f v -g;` → `cmds.cmd(f=v, g=True)`).
- `import maya.cmds as cmds` 지원: register 때 `sys.modules` 에 `maya` 가 없을 때만 가짜 패키지 `maya` + `maya.cmds` (= `cmds_shim`) 를 넣고 unregister 에서 우리가 넣은 것만 뺀다 (delegated; 진짜 Maya Python 이 있으면 건드리지 않음).
- 기록: 최근 20개 명령 `MAYAKIT_MT_cmd_history` (클릭 = 다시 실행). Maya 처럼 ↑/↓ 는 텍스트 필드 안에서 못 받음 (C).
- Script Editor 버튼: 새 창을 열고 그 창 영역을 Python Console 로 (`wm.window_new` 후 영역 `type='CONSOLE'`).
- Help Line (ui_layout.md:295-298): Maya 는 마우스 아래 UI 의 툴팁을 보여주지만 Blender Python 은 hover 를 알 수 없음 (C). 대신 **활성 툴의 Maya 식 도움말**(Move Tool: "Drag manipulator to move; Shift+drag...", Select: "Click or drag to select; Shift toggles, Ctrl deselects") + 커맨드 라인 마지막 결과가 없을 때만. Blender 의 마우스 버튼 힌트(`template_input_status`)는 그대로 남는다 (Blender 쪽 Help Line).
- 환경설정 (Maya Windows > UI Elements, ui_layout.md:190-191): `show_status_line`, `show_command_line`, `show_help_line`; Maya Windows 메뉴의 "UI Elements" 하위 메뉴가 이 토글을 보여준다.

### 5. `cmds_shim` (maya.cmds 흉내) — `command_line/cmds_shim.py`

- 단위: Maya 명령 숫자는 현재 선형 단위(기본 cm)·각도(도) [K]. 변환: BU = 값 × (씬 `length_unit` 의 m 배수) ÷ `scale_length` (단위계 NONE 이면 1 BU). decision 1 기본(cm 표시, scale 1.0) 에서 `move(0, 5, 0)` = 0.05 BU = 5 cm 로 보임, Maya 단위 옵션(scale 0.01) 에서는 5 BU. 회전 = 도 → 라디안.
- 명령: `ls(sl, type, long)`, `select(*objs, add, deselect/d, toggle/tgl, clear/cl, replace/r)`, `move/rotate/scale(x, y, z, *objs, relative/r, absolute/a)` (scale 상대 = 곱), `setAttr(attr, *values)`, `getAttr(attr)`, `polyCube/polySphere/polyCylinder/polyPlane(w,h,d / r / sx..., name/n)` → `[transform, node]` (`pCube1`, `polyCube1` — Maya 명명 [K]), `delete`, `rename`, `objExists`, `currentTime(t, query/q)`, `xform(q, t/ws/r/s)` 질의. 속성: `translate/t/tx/ty/tz`, `rotate/r/rx..`, `scale/s/sx..`, `visibility/v` (Channel Box 와 같은 이름, `ui/channel_box.py` MAIN). 없는 명령 → `AttributeError: maya.cmds.<name> is not available in Maya Kit (cmds_shim)`.

### 6. 테스트

- 헤드리스 `test_step7_top_ui.py`: 데이터·매핑 일치(모든 매핑 키가 데이터에 있음, 모든 연산자 id 존재, 메뉴 id 존재), 메뉴셋별 메뉴 클래스 등록, 메뉴셋 전환 → 그려질 메뉴 목록 변경, 회색 항목 = `menu_unavailable`; 상단 바 패치 후 disable → 원래 `draw_left/right` 복원; 스냅 토글 + 홀드 상호작용, 선택 마스크(모든 3D 뷰), 선택 모드, 렌더 설정 버튼; 커맨드 라인 실행/식 결과/오류/MEL 감지·힌트/기록/네임스페이스 유지, `import maya.cmds`, disable 후 `sys.modules` 정리; cmds_shim 단위 변환·명령 전부.
- `tests/kit.py` 스냅샷: `ui_extensions` 에서 클래스의 원래 draw 만 남은 항목(append 후 remove 하면 생김, `bpy_types.is_extended` 와 같은 기준)은 무시하도록 수정 + `TOPBAR_HT_upper_bar.draw_left/right` 함수 식별자 기록.
- GUI `gui_step7_top_ui.py`: 템플릿 레이아웃에서 상단 바 스크린샷(메뉴셋 Modeling ↔ Rigging 전환), 메뉴 열기(클릭) 스크린샷 — 활성/회색 항목, 커맨드 라인에 클릭·타이핑·Enter → 결과 필드와 큐브 생성, Ctrl+Z 로 되돌림, 상태바 스크린샷.
- manual_checks: 메뉴 항목 실제 실행 감, 폭 넘침(작은 창), Script Editor 창.

## 한 것

- **메뉴 데이터**: `tools/gen_menu_data.py` → `src/maya_kit/ui/menu_data.py` (42 메뉴, 1454 항목, 라벨·구분선·하위 메뉴만). 파싱 정리: 알 수 없는 `<dynamic>` 라벨 제거, 빈 섹션 구분선 합치기, Edit > Delete by Type 이 형제 항목을 삼킨 파싱 잔재 펴기, 같은 이름 형제(Select > Components ×3)는 경로에 `#2`, `#3`.
- **매핑** `ui/menu_map.py`: 255 항목(잎 1331 중)을 Blender 연산자 / 3D 뷰 실행(`maya_kit.menu_run`) / 툴 전환(`maya_kit.menu_tool`, 필요하면 편집 모드 먼저) / Blender 메뉴로. 나머지는 `maya_kit.menu_unavailable` (poll False → 회색, 툴팁 "Maya: <경로> / No Blender equivalent in Maya Kit yet"). File/Edit/Windows/Render/Help 끝에 "Blender File/Edit/Window/Render/Help ▸".
- **메뉴바** `ui/menu_sets.py` + `ui/status_line.py`: `TOPBAR_HT_upper_bar.draw_left/right` 교체 → 왼쪽 = Blender 로고, File Edit Create Select Modify Display Windows, **메뉴셋 드롭다운**, 셋 메뉴, Cache, Help; 오른쪽 = 워크스페이스 드롭다운 (씬 선택기는 씬이 2개 이상일 때만). 메뉴셋은 애드온 환경설정 `menu_set` (세션 간 유지). 플러그인 메뉴(MASH, Bifrost, Boss)는 데이터가 없어 뺀다.
- **Status Line 위치 변경 (계획 1 과 다름, delegated)**: TOPBAR 오른쪽에 넣었더니 1600 px 창에서 Maya 메뉴가 "Displ…" 에서 잘렸다 (GUI 스크린샷). Maya 처럼 **메뉴 아래 별도 줄**이 되도록 가장 큰 3D 뷰의 **툴 헤더 맨 앞**(`VIEW3D_HT_tool_header.prepend`)에 그린다 — 3D 뷰가 여럿이어도 한 번만. 템플릿은 툴 헤더를 켠다 (`tools/make_startup.py`, Step 5 의 "툴 헤더 숨김" 변경). 그 결과 상단 = 메뉴바, 그 아래 = Status Line + Blender 툴 설정, 맨 아래 = 커맨드 라인/Help Line.
- **Status Line 그룹**: New/Open/Save, Undo/Redo · 선택 모드 Hierarchy(회색)/Object/Component · 오브젝트 마스크 8개(handles·dynamics 회색, 나머지 = 모든 화면 3D 뷰의 `show_object_select_*`) / 편집 모드에서는 정점·엣지·면 토글 · 스냅 grid/curve/point/view plane(회색)/live(`FACE_PROJECT`) · Render View/Render/IPR/Render Settings/Hypershade · Attribute Editor(Properties Object 탭)/Tool Settings(`VIEW3D_PT_active_tool` 팝업)/Channel Box(사이드바 토글). 스냅 버튼은 X/C/V 홀드와 같은 `tool_settings` 를 읽어서 홀드 중에는 켜져 보인다 (GUI 스크린샷 `gui_step7_hold_x.png`).
- **커맨드 라인** `command_line/`: 상태바 앞에 `[Python]` + 입력 필드 + 결과(오류는 붉게) + 최근 명령 메뉴 + Script Editor(가장 큰 영역을 새 창으로 복제 → Python Console). Enter → `runner.run` (네임스페이스 bpy/C/D/cmds/mc 유지, 마지막 식 = `# Result: … #`, 예외 = `# Error: Type: msg`, print 마지막 줄). 필드 update 콜백에서 부른 연산자는 언두 단계를 만들지 않아(GUI 실측) `ed.undo_push` 를 직접 → 명령 하나 = Ctrl+Z 하나 (GUI 확인). MEL: `[Python]` 버튼 = 안내, MEL 같은 입력 = `# Error: no MEL, use Python: cmds.polyCube(w=2)` (변환 힌트), `$`/백쿼트 = 변환 없이 안내.
- **`cmds_shim`**: ls, select, move, rotate, scale, setAttr, getAttr, xform, polyCube/Sphere/Cylinder/Plane (`pCube1`/`pCubeShape1`/`polyCube1`, Maya 기본 분할 수: 구 382, 원기둥 40, 평면 121 정점), delete, rename, objExists, listRelatives (없으면 None), currentTime. 단위 = 씬 표시 단위(기본 cm → BU 0.01, Maya 단위 옵션이면 1), 각도 = 도. 축은 바꾸지 않는다 (Channel Box 와 같은 X/Y/Z; Y-up 불가, decision 5) — 단 폴리 프리미티브의 height 는 위쪽(Blender Z). `import maya.cmds` 는 진짜 `maya` 패키지가 없을 때만 `sys.modules` 에 넣고 disable 때 뺀다.
- **Help Line**: 상태바 커맨드 라인 뒤에 활성 툴의 Maya 식 도움말 (Select/Move/Rotate/Scale/Universal/Multi-Cut/Insert Edge Loop/Quad Draw).
- **환경설정**: Maya Menu Bar, Menu Set, Status Line, Command Line, Help Line (Maya Windows > UI Elements 메뉴에도).
- `tests/kit.py`: `ui_extensions` 는 원래 draw 만 남은 항목 무시 (`bpy_types.is_extended` 기준), `ui_methods`(TOPBAR draw_left/right), `sys_modules`(maya) 스냅샷 추가.

## 검증

```
python tests/run.py        → 99 passed, 0 failed, 8 file(s)   (step 7: 20, 기준 79)
python tests/gui/run.py    → 67 passed, 0 failed, 5 file(s)   (step 7: 15, 기준 52)
python tools/build.py      → maya_kit-0.1.0.zip, maya_kit-0.1.0-legacy.zip
```

- 헤드리스 `test_step7_top_ui.py` (20): 매핑 키가 전부 데이터에 있음, 연산자·속성·메뉴·툴 id 존재 (C 메뉴 `TOPBAR_MT_file_open_recent` 제외), 메뉴 클래스 42+ 등록, 메뉴셋 전환 → 메뉴바 메뉴 목록 (가짜 layout 기록), 활성/회색 항목·Blender 하위 메뉴·Components 3개 구분·모든 메뉴 draw 오류 없음, 상단 바 메서드 교체·disable 시 원래 함수, Maya/Blender 그리기·Status Line 은 가장 큰 3D 뷰에서만, 스냅 토글·홀드 상호작용, 선택 마스크 전 화면, 선택 모드·Render Settings·Attribute Editor·Channel Box·IPR, runner 결과/오류/MEL 힌트/기록, 필드 → 실행, `import maya.cmds`·disable 후 정리, Help Line, cmds_shim 단위·생성·변환·속성·잠금·선택·계층·시간·오류.
- GUI `gui_step7_top_ui.py` (15): 템플릿 로드 후 메뉴바·툴 헤더, 상태바 필드에 마우스 클릭 + 타이핑 + Enter → `pCube1` 생성·필드 비움, Ctrl+Z 로 사라짐, MEL 입력 오류 힌트, X 홀드 중 grid 스냅 켜짐/놓으면 꺼짐, Help Line Move 문구, Multi-Cut 메뉴 → 편집 모드 + knife 툴, Display > Grid (3D 뷰 실행) 토글, Script Editor 새 창 = Python Console, Tool Settings 팝업.
- 스크린샷 직접 확인 (`tmp/shots7/`): `gui_step7_topbar_modeling.png` (1600 px 에서 File … Generate Cache Help 전부 보임, 아래 줄 Status Line), `gui_step7_topbar_rigging.png` (Skeleton Skin Deform Constrain Control), `gui_step7_mesh_menu.png` (Booleans ▸, 매핑 항목 진하게, 미매핑·poll 실패 회색, 섹션 라벨), `gui_step7_command_line.png` (`# Result: ['pCube1', 'polyCube1'] #`), `gui_step7_hold_x.png` (grid 스냅 버튼 켜짐, 붉은 MEL 오류, Move Tool 도움말), `gui_step7_tool_settings.png`, `gui_step7_script_editor.png`.
- GUI 테스트 환경 주의: `--factory-startup` 에서 템플릿을 로드하면 팩토리 환경설정이 다시 읽혀 활성 키맵이 "Blender" 가 된다 → 테스트에서 `maya_kit.keymap_activate`. 사용자 저장 환경설정에서는 유지되는지 manual_checks.
- 사용자 실제 설정(`%APPDATA%/Blender Foundation`)은 사용 안 함 (모든 실행이 `tmp/test_env` 샌드박스).

## 결정 (delegated)

- Status Line = 가장 큰 3D 뷰의 툴 헤더 첫머리 (TOPBAR 한 줄에 다 안 들어감, 위 「한 것」).
- 메뉴셋 드롭다운은 Status Line 이 아니라 메뉴바 안, 바뀌는 메뉴 바로 앞.
- 워크스페이스 탭 → 드롭다운 (Maya 워크스페이스 선택기), 씬 선택기는 씬 2개 이상일 때만.
- Maya 메뉴 라벨·구조(`menu_data.py`)는 저장소에 넣는다: MEL 코드·아이콘·리소스 파일이 아니라 배치 정보 (decision 6 범위 안으로 판단).
- 연산자 poll 이 실패하는 항목은 Blender 가 회색으로 그림 (예: 빈 씬에서 Mesh > Smooth) — Maya 도 선택이 없으면 경고만 내지만 회색이 더 명확.
- Freeze/Reset/Center Pivot/Delete History 는 개념 단계(Maya 의미 연산자)까지 회색.
- cmds 숫자 = 씬 표시 단위, 축 변환 없음; `select()` 인자 없이 = 선택 해제 [K].
- Script Editor = 가장 큰 영역을 새 창으로 복제 후 Python Console.

## 남은 것

- 이번 지시에 없던 PLAN #7 항목: **Range Slider** (4 필드 + 재생 범위 토글, 또는 GPU 듀얼 핸들), **타임라인 모양** (Maya 붉은 키 틱 덧그리기), **`.` `,` Alt+`.` Alt+`,`** 키/프레임 이동 → PLAN 「Ordering after step 7」.
- Status Line 미구현 그룹: 입력 라인(절대/상대 이동·이름 바꾸기·이름으로 선택), Symmetry, Construction History 토글, 선택 잠금/하이라이트, 마스크 아이콘 RMB 세부 마스크.
- 메뉴: 옵션 박스 `[]` 없음 (C), 메뉴 F2–F6 단축키 (셸프/메뉴셋 단계), tear-off 없음 (C), Modify 의 Pivot 섹션(동적 라벨이라 데이터에 없음) — 개념 단계에서 Center Pivot 등을 추가할 때 `menu_map` 에 "추가 항목" 방식 필요.
- 커맨드 라인: ↑/↓ 기록 탐색은 텍스트 필드에서 불가 (C) → 최근 명령 메뉴. 결과가 길면 잘림 (상태바 폭).
- Help Line: 마우스 아래 UI 툴팁은 Python 으로 알 수 없음 (C).
- 다음 단계(8 마킹메뉴, 9 핫박스)는 `menu_sets.menu_idname(maya_name)` 으로 같은 메뉴를 열 수 있다 (핫박스 메뉴 행).
