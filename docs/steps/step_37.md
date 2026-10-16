# Step 37 — 뷰 패널 메뉴 바 (View / Shading / Lighting / Show / Renderer / Panels)

## 계획 (delegated)

Maya 근거:
- 모든 modelPanel 위에 자기 메뉴 바가 있다. 순서 View · Shading · Lighting · Show · Renderer · Panels, 그 아래 아이콘 바
  (research/maya/ui_layout.md:242-244). research 에는 메뉴 내용이 추적되지 않았다 (ui_layout.md:311). 그래서 Maya 2022
  설치본을 읽어 항목을 정리했다 (복사하지 않음; 추출 스크립트와 결과는 `tmp/probe37/`, 읽기 전용).
  - 메뉴 바: `createModelPanelMenu.mel:1931-2086` (`createModelPanelMenuDoIt`). Panels 는 `buildPanelPopupMenu.mel:273-427`.
  - View `:1381-1640`, Shading `:2159-2290`, Lighting `:2488-2522`, Show `:2578-2741`, Renderer `:509-664`.
  - 영어 라벨: `resources/MayaStrings`.

Blender 4.5:
- `VIEW3D_HT_header.draw` (`$S\startup\bl_ui\space_view3d.py:816`) 는 모드 선택 · 모드 버튼 다음에
  `VIEW3D_MT_editor_menus.draw_collapsible(context, layout)` (:915) 로 View/Select/Add/Object… 를 그리고, 그 뒤에 변환 방향·
  피벗·스냅·오버레이·셰이딩 버튼을 그린다.

설계:
1. 바꾸는 곳 (delegated): `VIEW3D_HT_header.draw` 전체 (Blender 코드 300 줄) 를 복사하지 않는다. 메뉴를 그리는 한 곳만
   바꾼다: `VIEW3D_MT_editor_menus.draw_collapsible` (bpy.types.Menu 에서 물려받은 classmethod) 를 클래스에 덮어쓰고,
   unregister 에서 그 속성을 지운다 (물려받은 원래 것으로 돌아감). `tests/kit.py` 스냅샷에 넣는다.
   모드 선택·선택 모드·오른쪽 버튼 줄 (Maya 의 패널 아이콘 바에 해당) 은 Blender 그대로 둔다.
2. 그리는 것: Maya 메뉴 6개 + 끝에 「Blender ▸」 (원래 View/Select/Add/Object… 를 하위 메뉴로; Maya Kit 상단 바와 같은 방식).
   헤더 메뉴를 접었으면 (`area.show_menus` 꺼짐) 아이콘 하나에 모두. 환경설정 `maya_panel_menus` (기본 켬) 가 꺼져 있으면 원래 것.
3. 항목 (`ui/panel_menus.py`, 데이터 표 + 그리기). 체크 = 속성 그대로 `layout.prop` (Blender 가 체크 상자로 그림),
   라디오 = `maya_kit.panel_set` (상태를 읽어 RADIOBUT 아이콘), 없는 것 = `maya_kit.menu_unavailable` (회색 + 툴팁).
   - **View**: Select Camera (카메라 뷰면 그 카메라 선택), Lock Camera 회색, Undo/Redo View Change = `maya_kit.view_history`,
     Tumble Behaviour 라디오 = `preferences.inputs.use_rotate_around_active` (사용자 환경설정을 바꾸는 사용자 동작; Maya 도 전역),
     Align Camera To Polygon = `view3d.view_axis(align_active)` (편집 모드), Center View of Selection = `view3d.view_center_pick`
     아님 → 회색, Default View = `maya_kit.view_home`, Frame All / Frame Selection = `maya_kit.frame`,
     View Along Axis ▸ (delegated: 축 이름 그대로) X = Right, −X = Left, Y = Back, −Y = Front, Z = Top, −Z = Bottom
     (`viewSet -vx` = +X 쪽에서 봄, `createModelPanelMenu.mel:1169-1203`), Camera Attribute Editor 회색,
     Camera Tools ▸ Zoom = `view3d.zoom_border`, Roll = `view3d.view_roll`, Fly = `view3d.fly`, Walk = `view3d.walk`, 나머지 회색.
   - **Shading**: Wireframe / Smooth Shade All = `shading.type` WIREFRAME / SOLID (라디오), Smooth Shade Selected·Flat Shade·
     Bounding Box·Points 회색, Use Default Material = `shading.color_type` SINGLE ↔ MATERIAL, Wireframe on Shaded =
     `overlay.show_wireframes`, X-Ray = `shading.show_xray`, X-Ray Joints = `overlay.show_xray_bone`, Backface Culling,
     Hardware Texturing = color_type TEXTURE ↔ MATERIAL, Depth of Field = `shading.use_dof`, Apply Current to All = 이 뷰의
     셰이딩·오버레이 값을 모든 3D 뷰에 복사; 나머지 회색.
   - **Lighting**: Use Default Lighting = SOLID + STUDIO, Use All Lights = Material Preview + 씬 라이트, Use Flat Lighting =
     SOLID + FLAT (라디오, 현재 상태 표시), Selected/No Lights·Two Sided 회색, Shadows = `shading.show_shadows`.
   - **Show**: Isolate Select ▸ View Selected = `view3d.localview(frame_selected=False)` (Ctrl+1 과 같음), All / None = 모든
     `show_object_viewport_*`, 종류 체크: NURBS Curves = curve, NURBS Surfaces = surf, Polygons = mesh, Lights = light,
     Cameras = camera, Joints = armature, Deformers = lattice, Fluids = volume, Hair Systems = curves, Locators = empty,
     Grease Pencil = grease_pencil, Pivots = `overlay.show_object_origins`, Motion Trails = `overlay.show_motion_paths`;
     나머지 Maya 종류는 회색. Manipulators = `show_gizmo`, Grid = `overlay.show_floor`, HUD = `overlay.show_text`,
     Selection Highlighting = `overlay.show_outline_selected`, Hold-Outs 회색.
   - **Renderer**: Viewport 2.0 = Solid (라디오), Legacy 두 개 회색, 렌더 엔진 이름 (Maya 의 Arnold 자리) = Rendered.
   - **Panels**: Perspective ▸ persp (`maya_kit.hb_view(PERSP)`) + 원근 카메라 오브젝트, Orthographic ▸ top / front / side
     + 직교 카메라 (카메라 = 그 카메라로 보기), Look Through Selected = `view3d.object_as_camera`, Panel ▸ 편집기 바꾸기
     (`maya_kit.hb_pane`, 핫박스와 같은 목록), Layouts ▸ Single Perspective View (`maya_kit.hb_single`) / Four View
     (`screen.region_quadview`), Tear Off… / Tear Off Copy… = `maya_kit.open_editor('VIEW_3D')`, Stereo · Camera Set ·
     Hypergraph Panel · Saved Layouts · Panel Editor · Previous/Next Arrangement 회색.
4. 다음 단계와의 관계: 38 (Channel Box), 39 (픽워크) 와 겹치는 것 없음.

검증:
- 헤드리스 `tests/test_step37_panel_menus.py`: 활성 시 `draw_collapsible` 가 Maya 메뉴 6 + Blender 를 그림 (가짜 layout),
  환경설정 끄면 원래 것, disable 하면 속성이 없어짐 (스냅샷), 각 메뉴의 draw 가 오류 없이 돎 (모드별), 매핑된 연산자·속성 존재,
  라디오/체크 동작 (Lighting, Shading, Show All/None, View Along Axis, Apply to All).
- GUI: 3D 뷰 헤더에서 Shading 메뉴 열기 + Show 메뉴 열기 스크린샷, 메뉴 항목 클릭으로 Wireframe 바꾸기.
- 전체 헤드리스·GUI·dogfood.

## 한 것

- `ui/panel_menus.py` (새):
  - 메뉴는 데이터 표 (VIEW · VIEW_AXIS · CAMERA_TOOLS · SHADING · LIGHTING · SHOW · ISOLATE · RENDERER · PANELS · LAYOUTS) 로 정의하고, `draw_rows` 가 그린다.
  - `maya_kit.panel_set`: 라디오·토글 상태와 Apply Current to All, Show All/None, Select Camera, Layouts.
  - `maya_kit.panel_run`: 이 뷰의 주 WINDOW 영역에서 연산자를 실행한다 (헤더 메뉴 컨텍스트에는 `region_data` 가 없음).
  - `maya_kit.panel_look_through`: Perspective/Orthographic 카메라 목록.
  - `MAYAKIT_MT_panel_blender`: Blender 의 원래 메뉴. `MAYAKIT_MT_panel_bar`: 헤더 메뉴를 접었을 때.
  - `VIEW3D_MT_editor_menus.draw_collapsible` 을 덮어쓴다. unregister 에서 `del` 하면 물려받은 원래 것으로 돌아간다.
- 환경설정 `maya_panel_menus` 「Panel Menus」 (기본 켬): 애드온 환경설정과 Windows > UI Elements 에 있다.
- `tests/kit.py` 스냅샷에 `draw_collapsible` 덮어쓰기 여부를 넣었다.
- 매핑 67 행, 회색 51 행 (`test_actions_exist` 로그).
- delegated 결정:
  - 헤더 전체가 아니라 메뉴 부분만 바꾼다.
  - Blender 메뉴는 「Blender ▸」 하위 메뉴로 둔다.
  - View Along Axis 축 이름은 그대로 둔다 (X = Right, Y = Back, Z = Top).
  - Tumble Behaviour 는 사용자 환경설정 (`use_rotate_around_active`) 을 바꾼다 (사용자가 직접 고른 동작).
  - Renderer 의 Maya 렌더러 자리에는 현재 렌더 엔진 이름 = Rendered 셰이딩을 둔다.
  - 아이콘 바는 Blender 헤더 오른쪽 버튼을 그대로 쓴다.

## 검증

- 헤드리스 `tests/test_step37_panel_menus.py` 10/10. 다음을 확인한다:
  - 헤더가 View · Shading · Lighting · Show · Renderer · Panels · Blender 순으로 그려진다. 접힌 헤더는 메뉴 하나.
  - 환경설정을 끄면 원래 메뉴가 나온다.
  - 모든 메뉴가 오류 없이 그려진다 (Blender 하위 메뉴 포함).
  - 연산자·속성이 있다.
  - Shading/Lighting/Renderer 라디오, Show All/None, Apply to All, 축 이름이 맞다.
  - disable 하면 원래 것으로 돌아간다.
- `test_enable_disable` 포함 전체 헤드리스 **322/322** (35 파일), GUI **272/272** (29 파일), dogfood **47/47**, 콘솔 오류 0.
- GUI `tests/gui/gui_step37_panel_menus.py` 5/5:
  - 헤더 Shading 클릭 → Wireframe 클릭 → `shading.type == WIREFRAME`.
  - 스크린샷 (`--shots`) `gui_step37_header.png`, `_shading_menu.png`, `_blender_menu.png`, `_show_menu.png`, `_panels_menu.png` 를 직접 확인했다. Maya 순서이고 회색 항목은 흐리게, 체크·라디오가 보인다.
- dogfood 01 (MayaKit 템플릿) 에서 헤더에 Maya 메뉴가 들어간다.
- `docs/manual_checks.md` Step 37 항목 5개.

## 남은 것

- MayaKit 템플릿의 좁은 3D 뷰에서는 헤더 오른쪽 셰이딩·오버레이 버튼이 잘린다 (Ctrl+휠로 스크롤). 이 단계 전에도 잘렸다 (step 36 dogfood 03).
  Maya 의 패널 아이콘 바 (따로 한 줄) 는 만들지 않았다. Blender 헤더는 한 줄이다. 툴 헤더 줄에 아이콘 바를 두는 방법이 후보.
- 회색 51 행. Blender 에 없는 것:
  - Smooth/Flat Shade Selected, Flat Shade All, Bounding Box / Points 셰이딩 (뷰 전체 설정이 아님), Lock Camera, Center View of Selection.
  - Tumble/Track/Dolly 툴 (지속 툴), Hardware Fog, Selected/No Lights, Two Sided Lighting.
  - Maya 전용 종류 (nCloth, Follicles, IK Handles …), Stereo, Camera Set, Hypergraph Panel, Saved Layouts, Panel Editor.
- Shift+M / Ctrl+Shift+M (패널 메뉴 바 / 툴바 숨기기, hotkeys_and_menus.md:101) 키는 묶지 않았다. 대응표 미검토 행 그대로다.
- Blender 4분할은 헤더가 하나라서 메뉴는 사용자 뷰 (`region_3d`) 에 적용된다. Maya 는 패널마다 메뉴 바가 있다.
