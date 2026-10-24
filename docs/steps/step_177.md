# Step 177 — Panel menus honesty and twins

Backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_174.json` 4 번째 (재점검 12차 BS2 / BS6,
`docs/steps/step_173_remaining.md` §4).

## 계획

- 문제: 3D View 패널 메뉴 (View / Shading / Lighting / Show / Renderer / Panels) 의 회색 44 행, 패널 툴바 회색 8 개,
  Status Line 회색 위젯 9 개가 `tools/menu_count.py` · step 101 notice 규칙 · `tools/menu_consistency.py` 밖이었고
  툴팁이 모두 "No Blender equivalent in Maya Workflow Kit yet".
- 표 데이터를 bpy 없는 `ui/panel_menu_data.py` 로 옮겨 (panel_menus / panel_toolbar 는 거기서 import) 세 도구가 읽게 한다
  (bpy 스텁으로 panel_menus 를 import 하면 `type()` / numpy 때문에 깨짐 — 시험함). 경로: `Panel menu/<menu>/<sub>/<label>`,
  `Panel toolbar/<label>`, `Status Line/<tooltip>`; 이름 안의 "/" 는 U+2215 (`2D Pan/Zoom` 이 가짜 쌍둥이를 만들었음).
- notice: `notices.PANEL_MENU` (NOTICES 와 따로: step 54 테스트가 NOTICES 키를 menus.json 경로로 검사).
- 연결 (Maya 근거 먼저): Center View of Selection (mayapy 측정), Camera Attribute Editor (+ 툴바 Camera Attributes),
  Tumble / Track / Dolly Tool (WorkSpaceTool: LMB 드래그 = kit `allset.tumble` / 새 `allset.track` / `allset.dolly`),
  Grease Pencil Tool (툴바의 같은 버튼 = Annotate 와 쌍둥이).
- 레인: 같은 파일 (panel_menus / panel_toolbar / notices) 을 거의 모든 일이 건드려서 순차로 함 (Maya 측정만 독립 —
  mayapy 한 번이라 메인이 직접).

## Maya 측정 (`research/maya/re/panel_menus_177.md`)

- Center View of Selection = `viewFit -c <camera>` (createModelPanelMenu.mel:1435-1437). mayapy: persp (28, 21, 28),
  큐브 (5, 2, -3) → 회전 그대로, 카메라 (31.8764, 22.1573, 23.8764), COI 44.82 → 43.02 = |중심 − 눈| (√1851). 규칙: 회전 유지,
  거리 = 선택 bbox 중심까지의 직선 거리, 중심이 시선 축 위.
- Camera Attribute Editor = `showPanelCameraEditor` → `showEditor <panel camera>` (선택 안 바꿈).
- Resolution Gate: Maya 기본 off, 켜도 overscan 1.0; Blender 카메라 뷰는 렌더 프레임을 항상 그림 (끌 수 없음) → notice.

## 한 것

- `ui/panel_menu_data.py`: 행 표 (VIEW … LAYOUTS, TOOLBAR), `MENUS` (idname → 경로), `STATUS_LINE`, `COMMANDS`
  (runTimeCommand), `item_path` / `toolbar_path` / `leaves()`.
- `ui/notices.py` `PANEL_MENU` 60 개 (패널 메뉴 44, 툴바 7, Status Line 9), `greyed_notice` / `tooltip` 이 읽음.
- `tools/menu_count.py`: 패널 줄 3 개 (Panel menus 111 / 67 working, Panel toolbar 29 / 22, Status Line greys 9 / 0),
  회색 notice 없음 0. `tools/menu_consistency.py` `panel_leaves`: 0 쌍.
- `ui/camera_tools.py`: `allset.center_view_selection` (뷰: view_location = 중심, distance = |중심 − 눈|, ortho 는 중심만;
  카메라 뷰: 카메라 이동, Lock Camera 면 경고), `allset.camera_attribute_editor` (카메라 뷰 = 그 카메라를 활성 + AE —
  kit AE 는 활성 오브젝트를 보여 줘서 선택이 바뀜, `object_attributes` 와 같은 delegated 차이; Blender persp / ortho 뷰 =
  perspShape 팝오버: Focal Length 를 Maya mm 로 (`WindowManager.allset_persp_focal`, view lens × 36 / 72), Near / Far Clip),
  `allset.track`, 도구 `allset.tumble_tool` / `track_tool` / `dolly_tool` (OBJECT, EDIT_MESH; W / Q / E / R 로 떠남).
  `allset.dolly` 는 시작한 버튼의 RELEASE 에서 끝남 (Alt+RMB = RMB, Dolly Tool = LMB).
- 나머지 회색: 이유 + 대체가 있는 notice (예: Flat Shade All → Use Flat Lighting, Bounding Box → Object Properties >
  Viewport Display, Use Selected Lights → Use All Lights + h / light linking — Blender 는 뷰마다 조명 목록이 없음,
  Show 의 Maya 전용 노드 종류 → 오브젝트 종류로만 거름, Image Planes / IK Handles → Locators).

## 검증

- 헤드리스 전체 `ALLSET_SANDBOX=s177full python tests/run.py`: **1628 / 1628** (176 끝 1621 + `test_step177_panel_menus` 7).
  새 테스트: 회색 패널 항목마다 notice · 남는 notice 없음, 그리는 행 = 세는 행 (Status Line 그리는 회색 = `STATUS_LINE`),
  menu_count 패널 줄, 쌍둥이 0 + 심어 둔 쌍 찾기, 연결된 행, Maya viewFit -c 수치 (1e-3), 카메라 회전 유지.
- GUI `gui_step177_panel_menus` 9 / 9: Center View (중심 · 회전 유지 · 거리 = 눈-선택 거리), Tumble Tool LMB 드래그 0.67 rad +
  선택 유지, Dolly Tool LMB 드래그 0.389 → 0.250 + LMB 놓으면 끝, W = Move, persp 팝오버. 스크린샷 (`tmp/s177/shots/`) 직접 봄:
  View 메뉴 (Center View of Selection · Camera Attribute Editor 켜짐, View Sequence Time 회색), Shading 메뉴 (회색 9 행),
  perspShape 팝오버 (Focal Length 35 = Maya persp).
- 관련 GUI: `gui_step4_view`, `gui_step37_panel_menus` 통과; `gui_step129_panel_toolbar` 3 실패는 수정 전 코드 (git stash) 에서도
  같은 3 개 (머리 폭 의존, 알려진 것).
- GUI 전체 묶음은 돌리지 않음 (CLAUDE.md step 141 규칙: 바꾼 모듈의 GUI 파일만, 전체는 릴리스 준비 때).

## 남은 것

- Maya 2022 View 메뉴의 Look at Selection (`viewLookAt`) 행이 kit 패널 메뉴에 없음 (회색도 아님 — 빠진 행).
- Camera Attribute Editor 는 카메라를 선택함 (Maya 는 선택 안 바꿈): kit AE 가 활성 오브젝트만 보여 줌.
- Resolution Gate · Use Selected Lights 는 연결 못 함 (Blender 에 같은 뷰별 스위치 없음) — notice.
