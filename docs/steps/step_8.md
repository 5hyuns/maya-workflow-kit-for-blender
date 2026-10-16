# Step 8 — M3-a 마킹메뉴 1차 (파이메뉴)

(사용자 번호 8 = `docs/PLAN.md` 표 #9.)

## 계획

근거: `research/maya/hotkeys_and_menus.md` §5.1 트리거 (:227-243), §5.2 RMB 오브젝트 메뉴 (:246-252), §5.3 Shift+RMB (:254-265), §5.4 Ctrl+RMB (:267-269), §5.5 툴 옵션 (:271-276); `research/maya/marking_menus.json` → `menus[<proc>]` (방사 위치·라벨·줄 번호), `triggers_curated`; `research/blender/api_limits.md` #5 (:56-60, 파이 = 8칸, 누른 채 놓기 = `pie_tap_timeout`); `research/blender/keymap_industry_compatible.json` (IC 의 RMB = 컨텍스트 메뉴, Shift+RMB = 3D 커서).

### 1. 파이 = 마킹메뉴 1차

- Maya 방사 위치 N/NE/E/SE/S/SW/W/NW 를 그대로 Blender 파이 슬롯에 둔다. Blender `menu_pie()` 는 항목을 **W, E, S, N, NW, NE, SW, SE** 순서로 채우므로 빈 칸은 `separator()` 로 자리만 차지.
- Maya 의 "링 아래 선형 목록"(overflow)은 파이에 자리가 없다(api_limits #5) → **S 슬롯을 column 으로**: S 항목, 구분선, 목록 항목. 링 아래에 목록이 붙는 Maya 모양과 가장 비슷 (delegated).
- 방사 하위 메뉴(▸) = 그 자리 항목이 하위 파이를 연다 (`wm.call_menu_pie`); 목록 안 하위 메뉴 = 일반 드롭다운 메뉴. Maya 처럼 그 자리에서 펼쳐지는 중첩 방사는 Step 9 엔진.
- 누른 채 끌어서 놓기 = 선택 (Blender 파이: `pie_tap_timeout` 보다 오래 누르면 놓을 때 확정) — Maya 와 같은 press-drag-release. 짧게 클릭하면 파이가 열린 채 남아 클릭으로 고름 (Maya 도 클릭하면 메뉴가 떠 있음 [K]).
- 항목 동작 형식은 Step 7 메뉴 매핑(`ui/menu_map.py`)과 같다: `"op.id"` / `("op.id", {props})` / `("v3d", …)` / `("tool", id, edit)` / `("menu", id)` + 새 `("pie", 메뉴 id)`; `None` = 회색(`maya_kit.menu_unavailable`). 그리기 함수는 `menu_sets.draw_spec` 로 공유.
- 정의는 손으로 쓴 `src/maya_kit/marking/menus.py` (라벨·방사 위치·동작; MEL 없음, 줄 번호 인용). 테스트가 research JSON 의 방사 위치와 대조한다.

### 2. 트리거와 디스패치 (`maya_kit.marking_menu`, trigger 별)

| 트리거 (3D 뷰) | Maya 빌더 | 우리 파이 |
|---|---|---|
| RMB 누름 | `dagMenuProc` (메시: N Edge · W Vertex · S Face · E UV · SW Vertex Face · SE Multi · NE Object Mode, hotkeys_and_menus.md:248-250) | 오브젝트 모드: 커서 아래 객체(레이 캐스트) 또는 활성 객체가 메시면 컴포넌트 파이 — 고른 항목이 그 객체를 선택·활성화 후 컴포넌트 모드 (Maya: 커서 아래 객체가 대상 [O :252]); 커브/서피스면 CV 파이; 그 밖(아마추어·카메라 등)은 Blender 컨텍스트 메뉴 (delegated). 편집 모드: 같은 컴포넌트 파이 (NE Object Mode 로 나가기 = "컴포넌트에서 반대"). 빈 곳: Select All / Complete Tool 목록 (:252) |
| Shift+RMB | `contextToolsMM` → 선택 종류별 (:254-265) | 편집 모드 면/엣지/정점 선택 모드 → Face/Edge/Vertex 파이; 오브젝트 모드에서 메시 선택 → Object 파이; 선택 없음 → Default(프리미티브 생성) 파이 |
| Ctrl+RMB | `buildConvertMM` → `polyConvertMM` (:267-269) | 편집 메시 → 변환 파이; 그 밖은 RMB 파이 (Maya 도 메시 아니면 오브젝트 메뉴, buildConvertMM.mel:85-106) |
| Ctrl+Shift+RMB, Q/W/E/R 누른 채 LMB | `buildToolOptionsMM` → Select/Move/Rotate/Scale 옵션 (:271-276) | 활성 툴(또는 키의 툴)의 옵션 파이 |

### 3. Q/W/E/R 누른 채 LMB — Step 3 탭/홀드 프레임워크

- `operators/taphold.TapHoldBinding` 4개 (`tool_select`, `tool_move`, `tool_rotate`, `tool_scale`): **누름 = 툴 전환**이 Maya 동작 (hotkeys_and_menus.md triggers: "Press activates tool"), 그래서 탭(`tap`)과 클릭(`click`) 모두 툴을 켜고, 클릭은 그 툴의 옵션 파이를 연다. LMB 가 누른 채로 파이에 들어가 끌어서 놓기로 고른다.
- 키맵: IC 의 모드별 `wm.tool_set_by_id` Q/W/E/R (Object Mode, Mesh, Curve, Armature, Pose, Metaball, Lattice, Curves, IC:—) 를 `maya_kit.tap_hold` 로 바꾼다. 페인트/스컬프트 모드(Q = 박스 마스크 등)는 그대로.

### 4. 키맵 충돌 (delegated)

- RMB: IC 모드별 `wm.call_menu` 컨텍스트 메뉴 (Object Mode, Mesh, Curve) 를 제거하고 `maya_kit.marking_menu` 로. Armature/Pose/Metaball/Lattice/Font/Particle 은 Blender 컨텍스트 메뉴 유지 (Maya 전용 메뉴 없음).
- Shift+RMB: IC "3D View" 의 `view3d.cursor3d` (PRESS) 와 커서 끌기 `transform.translate` (CLICK_DRAG) 제거 — Maya 에 3D 커서 없음. 3D 커서는 Blender 툴바 Cursor 툴로 남는다. Ctrl+RMB / Ctrl+Shift+RMB: IC 3D 뷰 키맵에 없음 (덤프 확인) → 추가만.
- 페인트/스컬프트 모드는 RMB 를 자기 키맵에서 쓰므로 3D View 공통이 아니라 모드 키맵에 넣는다.

### 5. 다음 단계와의 경계

- Step 9 마킹메뉴 엔진은 같은 `marking/menus.py` 정의를 읽어 GPU 로 그린다 (방사 + 목록 + 중첩 + 옵션 박스). 그래서 정의는 Blender 파이에 묶이지 않은 순수 데이터로 둔다.

### 6. 테스트

- 헤드리스: 정의 형식(방사 키, 같은 메뉴 안 위치 중복 없음), research JSON 과 방사 위치·라벨 일치, 모든 동작 대상(연산자·속성·툴·메뉴·하위 파이) 존재, 파이 Menu 클래스 등록·가짜 layout 로 슬롯 순서, 디스패치(모드·선택·선택 모드별 메뉴), 컴포넌트 항목 = 대상 객체 선택 + 편집 모드, 키맵(RMB 4종, QWER tap_hold, 제거된 IC 항목), 탭/홀드 바인딩 등록, enable/disable 깨끗.
- GUI: 큐브 위 RMB 누름 → 위로 끌기 → 놓기 = 엣지 모드; Shift+RMB 스크린샷; W 누른 채 LMB → 옵션 파이 스크린샷, 아래로 끌어 World 선택; Ctrl+RMB 변환 파이 스크린샷.
- manual_checks: 누름-끌기-놓기 감각, 짧은 클릭 시 남는 파이, 마우스 아래 객체 대상.

## 한 것

- `src/maya_kit/marking/menus.py`: Maya 마킹메뉴 13개를 데이터로 — RMB `dagMenuProc`(메시)·커브·빈 곳, Shift+RMB Object/Vertex/Edge/Face/Default(생성), Ctrl+RMB `polyConvertMM`, 툴 옵션 Move/Rotate/Scale/Select. 방사 위치·라벨은 research 그대로, 줄 번호 주석. 방사 하위 메뉴 15개, 선형 목록(링 아래) 포함.
- `src/maya_kit/marking/__init__.py`:
  - 메뉴·방사 하위 메뉴마다 파이 `Menu` 클래스 `MAYAKIT_MT_mm_<proc>[_<위치>]` (목록 안 하위 메뉴는 일반 메뉴). Maya 위치 → Blender 파이 순서(W E S N NW NE SW SE), 빈 칸은 separator, 선형 목록은 S 칸 column 아래 상자.
  - `maya_kit.marking_menu(trigger)`: 모드·선택·선택 모드·활성 툴로 메뉴 고르기(Maya 빌더 디스패치), RMB 는 커서 아래 객체를 레이 캐스트로 골라 `WindowManager.maya_kit_mm_target` 에 기억. 아마추어·카메라 등은 Blender 컨텍스트 메뉴.
  - `maya_kit.mm_component` (대상 객체만 선택·활성 → 컴포넌트 모드 / 커브는 편집 모드 / Select), `maya_kit.mm_clear_selection`.
  - Q/W/E/R: Step 3 `TapHoldBinding` 4개 — 누름(탭) = 툴 전환, 누른 채 LMB = 툴 전환 + 옵션 파이 (LMB 놓기로 고름).
- 항목 그리기는 Step 7 `menu_sets.draw_spec` 공유 (`menu_map.normalize` 에 `("pie", id)` 추가). 툴 옵션의 방향(World/Object/Component/Parent/Gimbal)은 `wm.context_set_enum` 으로 `transform_orientation_slots[0].type` 설정 — `transform.select_orientation` 은 메뉴에서 부르면 자기 열거 팝업을 또 띄운다 (GUI 스크린샷으로 발견).
- 키맵 (`maya_patches.patch_marking_menus`): Object Mode/Mesh/Curve 의 RMB 컨텍스트 메뉴 → RMB/Shift/Ctrl/Ctrl+Shift+RMB 마킹메뉴; 3D View Shift+RMB 3D 커서(누름·끌기) 제거; Object Mode/Mesh/Curve/Armature/Pose/Metaball/Lattice/Curves 의 Q/W/E/R `wm.tool_set_by_id` → `maya_kit.tap_hold`. 대응표 4행(q/w/e/r) IC → KIT, 매핑 문서 재생성.
- `tests/test_keymap_maya.py` 섀도잉 검사에 편집·포즈 모드 키맵 스택 추가.

## 검증

```
python tests/run.py        → 110 passed, 0 failed, 9 file(s)   (step 8: 11, 기준 99)
python tests/gui/run.py    → 74 passed, 0 failed, 6 file(s)    (step 8: 7, 기준 67)
python tools/gen_keymap_mapping.py → 468 rows, 구현 42
```

- 헤드리스 `test_step8_marking_menus.py` (11): 정의 형식, **research JSON 과 방사 위치·라벨 134개 일치**(손으로 푼 dagMenuProc 3개 제외), 모든 동작 대상(연산자·속성·툴·메뉴) 존재, 파이 클래스 등록·슬롯 순서·하위 파이·빈 칸·회색 항목, 디스패치(빈 씬/메시/편집 정점·엣지·면/카메라/커브, 툴 옵션 4종), 컴포넌트 항목이 커서 아래 객체를 대상으로, 레이 캐스트 선택, 키맵(RMB 4종 × 3 모드, IC 컨텍스트 메뉴·Shift+RMB 커서 제거, QWER × 8 모드), disable 후 바인딩·클래스·WM 속성 정리.
- GUI `gui_step8_marking_menus.py` (7): 선택 없이 큐브 위 RMB 누름 → 위로 120 px → 놓기 = 엣지 모드 + 큐브 활성; 컴포넌트 모드에서 RMB → NE 놓기 = 오브젝트 모드; W 누름 = Move 툴, W 누른 채 LMB → 왼쪽으로 끌어 놓기 = World 방향.
- 스크린샷 직접 확인 (`tmp/shots8/`): `gui_step8_rmb_object.png` (N Edge, W Vertex, S Face + 목록, E UV 회색, SW Vertex Face 회색, SE Multi, NE Object Mode 회색), `gui_step8_shift_rmb_edge.png` (Merge/Collapse ▸, Flip/Spin ▸, Bevel, Soften/Harden ▸, Extrude, Delete, Multi-Cut, Paint Select 회색 + 목록), `gui_step8_ctrl_rmb_convert.png` (To Edges ▸ … Grow ▸), `gui_step8_w_move_options.png` (NW Object, W World, NE Component, E Snap ▸, SW Axis ▸, SE Keep Spacing 회색), `gui_step8_shift_rmb_create.png` (Plane/Disc/Cylinder/Sphere/Cone/Torus/Cube + 목록).

## 결정 (delegated)

- 선형 목록 = S 칸 아래 상자 (파이에 9번째 칸이 없음). 긴 목록(Edge 툴)은 화면 아래로 길어진다.
- RMB 대상 = 커서 아래 객체(레이 캐스트, 메시만 맞음), 없으면 활성 객체. 선택은 항목을 고를 때만 바뀐다 (취소하면 그대로).
- Maya 메시 오브젝트 모드의 Extrude/Fill Holes/Target Weld 등은 Blender 에서 편집 모드 전용이라 오브젝트 Shift+RMB 에서 회색. Soften/Harden 은 오브젝트 단위 셰이딩(flat/smooth/auto smooth) 으로.
- Maya manip 모드 → Blender 방향: Object = Local, World = Global, Component/Normal = Normal, Parent = Parent, Along Rotation Axis/Gimbal = Gimbal.
- 아마추어·카메라·라이트 등의 RMB 는 Blender 오브젝트 컨텍스트 메뉴 (Maya 의 조인트/로케이터 전용 메뉴는 범위 밖).
- 페인트·스컬프트 모드의 RMB/Q 는 Blender 그대로.

## 남은 것

- Step 9 엔진 몫: 그 자리 중첩 방사(지금은 새 파이), 옵션 박스 `[]`, 보지 않고 긋기(제스처·플릭), 9개 이상 항목의 Maya 식 목록.
- 회색 항목: UV/Vertex Face 컴포넌트, Paint Select, Target Weld, Wedge, Booleans, Circularize, Edit Edge Flow, 툴 옵션의 Keep Spacing·Discrete Rotate·Snap Scale·Relative 등.
- Maya 의 다른 홀드 메뉴(Shift+Q, Alt+Q, Shift+S 탄젠트, A 홀드 MM — 지금은 Blender 선택 메뉴)는 아직.
- NURBS 서피스·조인트·HIK 전용 RMB 메뉴, n 홀드 Traversal.
