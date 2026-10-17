# Step 67 — Hypershade 창 · Light Editor · Render 메뉴 · Render View Keep Image · AE 맵 버튼

근거: `research/maya/workflows/render.md` (§3 Gap 표, §4 개념 결정 1–6, §5 후보 1–3), shots `render_01_win1` (Hypershade),
`render_03_win1` (Light Editor), `render_04_win1` (Render Settings), `render_05_win1` (Render View).

## 계획

측정 (이 단계 시작 때, `tmp/exp67/`):
- **`Region.active_panel_category` 는 4.5 에서 쓸 수 있다** — 영역이 한 번 그려져 탭 목록이 생긴 뒤 (GUI, `gui_tab.py`: 새 창 Shader Editor
  사이드바 → "Hypershade", 3D View → "Light Editor" 로 바뀜, 스크린샷 확인). 그 전 (탭이 없을 때) 은 효과 없음 → 타이머로 그려진 뒤 설정.
  새 창의 사이드바는 처음엔 첫 탭 (Node / Item) 이고 `bl_order` 로는 안 바뀐다. (CLAUDE.md step 11 "read-only" 기록을 고친다.)
- `SpaceNodeEditor.pin = True` 후 `node_tree = mat.node_tree` 설정 가능 (헤드리스).
- Render Result: 슬롯 8 개, `render_slots.active_index` 로 다음 렌더 슬롯 선택, `render_slots.new()` 로 9 번째. 슬롯에 그림이 있는지 알 수 있는 API 는 없음 → kit 이 기록.
- `UILayout.operator_menu_enum` 은 속성을 돌려준다 (안 씀: 팝업 연산자가 Break Connection 도 그림).

설계 (모두 delegated):
1. **Hypershade = `maya_kit.hypershade`** (`ui/hypershade.py`): 가장 큰 영역을 새 창으로 복제 (`area_dupli`, open_editor 와 같은 방식) →
   Shader Editor + 사이드바 표시 + "Hypershade" 탭 활성 (타이머). 탭 (모든 Shader Editor 사이드바): 안내 줄, **Browser** (씬 재질 미리보기 격자,
   클릭 = 그 재질을 Hypershade 의 현재 재질로: 활성 오브젝트 슬롯에 있으면 그 슬롯을 활성, 없으면 이 Shader Editor 를 핀),
   **Create** (Maya 재질 종류 버튼: 만들기만, 할당 안 함 = Maya Hypershade Create; 사용자 0 명이라 저장 때 사라지지 않게 fake user),
   **Assign Material To Selection**, **Property Editor** (kit AE 재질 섹션 재사용, 맵 버튼 포함). Windows 메뉴·Status Line 아이콘·핫박스 Windows
   메뉴가 모두 이 연산자. 핫박스 N 존 레이아웃 (Hypershade/Persp 등) 과 Panels > Hypershade 는 그대로 (render.md §4.1).
2. **Light Editor = `maya_kit.light_editor`** (`ui/light_editor.py`): 주 3D View 를 새 창으로 복제 → 그 공간을 Light Editor 공간으로 기록
   (창 포인터 + 공간 포인터, 창에 영역 하나일 때만 유효 — 해제된 포인터 재사용 대비) → 사이드바 "Light Editor" 탭 (그 공간에서만 poll).
   내용: 안내 ("Blender 에 Light Editor 없음 — kit 목록"), 라이트 만들기 버튼 (`maya_kit.create` 라이트 4 종), 표 (이름 = 선택, 색, Intensity =
   `energy`, Enable, Isolate), 아래 Property Editor = 선두 라이트의 AE 라이트 섹션. Enable = `hide_render` + `hide_viewport` 함께.
   Isolate = 다른 라이트를 끄고 이전 값을 씬 ID 속성 `maya_kit_light_isolate` 에 저장, 다시 누르면 복구 (지워진 라이트는 건너뜀).
3. **Render 메뉴**: 원인 = menus.json 의 `("renMenuRenderUsingItemMenuItem")` 자리 표시 항목 (Render Using 하위 메뉴) 이 형제 15 개를 자식으로
   삼킴 (menus.json 전체에서 이 한 곳, 측정). `tools/gen_menu_data.py` 가 이 자리 표시를 "Render Using" 으로 바꾸고 삼킨 형제를 꺼낸다.
   MAP: Render Using = 렌더 엔진 메뉴, Render Current Frame / Redo Previous Render = `render.render` (INVOKE → Render View),
   IPR Render Current Frame / Redo Previous IPR Render = `maya_kit.ipr_toggle`, Render Sequence = `render.render(animation=True)`.
   Batch Render 류 = 회색 + 안내 (명령줄 `blender -b file -a`).
4. **Render View Keep Image / Remove Image** (`ui/render_view.py`): Image Editor 가 Render Result 를 보일 때 헤더 끝에 Render · Keep Image ·
   Remove Image (shelf.py 가 이미 바꿔 둔 `IMAGE_HT_header.draw` 래퍼에서 호출). Keep = 지금 슬롯을 "보관" 으로 기록 (이미지 ID 속성
   `maya_kit_kept`) → 보관 안 된 첫 슬롯을 활성 (없으면 `render_slots.new()`) → 다음 렌더가 새 슬롯에. Remove = 지금 슬롯 비우기 + 기록 삭제.
   툴팁 "Maya Keep Image = Blender Render Slot (J / Alt+J)".
5. **AE 맵 버튼**: AE 소켓 행 (`attribute_editor.draw_row`) 오른쪽에 체커 버튼 → 팝업 "Create Render Node": File (Image Texture) / Ramp
   (UV V 방향 Color Ramp, 빨·초·파 = Maya ramp 기본 [K]) / Noise / Checker (UV, 4×4 [K/U]), 연결돼 있으면 Break Connection.
   Normal 소켓은 Bump 노드를 거친다 (Maya bump2d). 연결된 행 = "connected (노드)" + 맵 버튼, Image Texture 면 이미지 선택/열기 (Maya file 노드의 Image Name).
6. **standardSurface / aiStandardSurface ↔ Principled 이름 표** (`ae_layout.STANDARD_SURFACE_ATTRS`, render.md §4.4): 맵 버튼 툴팁에 Maya 속성
   이름, AE Geometry 에 Thin Walled 회색 행, 재질 종류 `AI_STANDARD_SURFACE` (`aiStandardSurface1`, STANDARD_SURFACE 섹션) 추가.

검증: 헤드리스 `tests/test_step67_render.py`, GUI `tests/gui/gui_step67_render.py` (구 → Hypershade → Create → 목록에서 할당 → AE Base Color 맵 →
File → Render > Render Current Frame → Keep Image → 다시 렌더 → 슬롯 2 개, Light Editor 창), 스크린샷, dogfood, manual_checks.

## 한 것

- **Hypershade** (`ui/hypershade.py`): `maya_kit.hypershade` = 가장 큰 영역을 새 창으로 복제 → Shader Editor, 사이드바 「Hypershade」 탭 활성
  (`menu_extras.sidebar_tab_later`). 탭 (모든 Shader Editor): 안내, Browser (미리보기 격자 + 이름 버튼 = `maya_kit.hs_pick`), Assign Material To
  Selection, Create (Blinn / Lambert / Phong / Standard Surface / aiStandardSurface / Surface Shader = `maya_kit.hs_create`, 할당 없이 + fake user),
  Property Editor (AE 재질 섹션 + 맵 버튼). Windows 메뉴 · Status Line 아이콘 (예전 Shading 워크스페이스 전환 연산자 삭제) · 핫박스 Windows 메뉴가 같은 연산자.
- **Light Editor** (`ui/light_editor.py`): `maya_kit.light_editor` = 주 3D View 를 새 창으로 복제, (창, 공간) 포인터로 표시, 사이드바 「Light Editor」 탭:
  안내, 라이트 만들기 4 개, 표 (이름 = `light_select`, 색, Intensity = energy, 켜기 = `light_enable`, Solo = `light_isolate`), Property Editor - Light Editor
  (Enable / Isolate, AE 라이트 섹션, Translate/Rotate/Scale). Isolate 상태는 씬 ID 속성 `maya_kit_light_isolate` (지운 라이트는 복구 때 건너뜀).
- **Render 메뉴**: `tools/gen_menu_data.py` `PLACEHOLDERS` — `("renMenuRenderUsingItemMenuItem")` → 「Render Using」, 삼켜진 형제 15 개를 꺼냄 → Render 메뉴
  17 항목 (Maya 순서). MAP: Render Using = `MAYAKIT_MT_render_using` (엔진), Render Current Frame / Redo Previous = `render.render`,
  IPR / Redo IPR = `maya_kit.ipr_toggle`, Render Sequence = `render.render(animation=True)`; Batch Render / Cancel / Show = 회색 + 안내 (`blender -b … -a`).
- **Render View** (`ui/render_view.py`): Render Result 를 보이는 Image Editor 헤더 맨 앞에 Render · Keep Image · Remove Image · 「Slot N · k kept」
  (끝에 두면 작은 렌더 창에서 잘림 — GUI 스크린샷에서 확인 후 앞으로 옮김). Keep = 지금 슬롯 기록 + 기록 안 된 첫 슬롯 활성 (모두면 `render_slots.new()`).
- **AE 맵 버튼** (`operators/shading_maps.py`): 소켓 행마다 체커 버튼 → 팝업 Create Render Node (File / Ramp / Noise / Checker, 연결돼 있으면 Break
  Connection). Ramp = UV V 방향 Color Ramp 빨·초·파, Checker = UV 4×4 [U], Normal 은 Bump 노드 경유. 연결된 File 은 이미지 New / Open 행.
- **이름 표**: `ae_layout.STANDARD_SURFACE_ATTRS` (33 속성 → Principled 입력 / None), 맵 버튼 툴팁 = Maya 속성 이름, AE Geometry 의 Thin Walled 회색 행
  (새 행 종류 `missing`), 재질 종류 `AI_STANDARD_SURFACE` (`aiStandardSurface1`, AE = standardSurface 섹션).
- `chrome.paragraph` (영역 너비로 줄 바꿈한 안내 글).
- 측정 정정: `Region.active_panel_category` 는 영역이 탭을 그리기 전엔 "read-only" AttributeError, 그린 뒤엔 설정됨 (CLAUDE.md 항목 고침).

## 검증

- 헤드리스 `tests/test_step67_render.py` 10/10 (Render 메뉴 순서·매핑·안내, 공유 연산자, 이름 표 vs Principled 4.5 입력, aiStandardSurface,
  맵 버튼 그리기·네 종류 연결·Bump·Break, Hypershade create/pick/pin/assign/패널, Light Editor isolate/enable/선택/패널, Keep Image 슬롯).
  step 34 (Hypershade = `maya_kit.hypershade`), step 54 (회색 안내 예 = Render/Batch Render) 기대 갱신. 전체 헤드리스 549/549 (step 66 의 539 + 10).
- GUI `tests/gui/gui_step67_render.py` 9/9 (ui 1.0): 구 → Hypershade 창 (탭 Hypershade) → Create Standard Surface (할당 없음, 핀) → Assign → 목록에서 pick
  (핀 해제) → Base Color 맵 File (Image Texture 연결) → Render > Render Current Frame (Render Result 창) → Keep Image → 다시 렌더 → kept {0}, 활성 슬롯 2 →
  Light Editor 창 (탭 Light Editor, 표시됨) → pointLight1 Isolate → directionalLight1 꺼짐 → 다시 → 켜짐. 스크린샷 3 장 직접 확인
  (`gui_step67_hypershade.png`, `_keep_image.png`, `_light_editor.png`). GUI 전체 ui 0.8: 461/461. dogfood 47/47 (콘솔 오류 0).
- `docs/manual_checks.md` 「Step 67」 6 항목.

## 남은 것

- Maya Hypershade 의 Textures / Utilities / Lights 탭, 스와치 MMB 드래그 할당, Material Viewer: 없음 (Browser 는 재질만).
- Light Editor 창은 파일을 다시 열면 일반 3D View 로 돌아감 (포인터 표시, 저장 안 됨). Maya Exposure 열 없음. Light Editor 창의 사이드바에도
  Channel Box / Item 탭이 같이 있음 (C 패널 Item 은 숨길 수 없음).
- 960×540 템플릿 해상도, Light Linking, Shader Editor Tab 노드 생성,
  AE 재질 스와치: render.md §3 의 8점 이하 후보 — 이번 범위 밖.
- Maya checker 의 반복 수, ramp 기본 색은 [K/U] (Maya 에서 측정 안 함).

## 이어서 한 것 (같은 단계, 두 번째 세션)

- **Render Settings = 자기 창** (render.md §4.5, delegated): `maya_kit.render_settings` 가 언제나 새 Properties 창 (Render 탭) 을 연다 —
  화면의 Properties 가 AE 역할일 때 그 탭을 빼앗지 않게. 창을 못 열면 (백그라운드) 예전처럼 화면의 Properties 탭 전환.
  측정: 연산자 안에서 막 만든 Properties 공간은 탭 목록이 없어 `context = 'RENDER'` 가 조용히 OBJECT 로 남음 →
  `menu_extras.properties_tab_later` 가 타이머로 다시 설정 (`open_editor(tab=...)` 전부에 적용).
- **AE 라이트 Decay Rate 행** (render.md §3 C4, attribute_editor.md:132-135): Point / Spot / Area 라이트 섹션에 회색 「Decay Rate: Quadratic …」
  (`missing` 행). Directional 은 없음.
- 검증: 헤드리스 `test_step67_render` 11/11 (+ Decay Rate), GUI `gui_step67_render` 10/10 (+ Render > Render Settings… = 새 창, 탭 RENDER;
  스크린샷 `gui_step67_render_settings.png` 확인). 전체 숫자는 아래 「검증 (최종)」.

## 검증 (최종)

- 헤드리스 550/550 (step 66 의 539 + step 67 11).
- GUI ui 0.8 전체 460/462: 실패 2 = `gui_step26_smart_extrude` RMB 취소 두 항목 — 이 단계와 무관한 코드, 혼자 다시 돌리면 3 번 모두 8/8
  (첫 세션 전체 실행에서도 통과) → 전체 실행 때만 가끔 나는 타이밍 실패로 기록. `gui_step67_render` 10/10 (ui 1.0).
- dogfood 47/47, 콘솔 오류 0.

