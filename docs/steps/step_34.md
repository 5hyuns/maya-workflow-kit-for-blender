# Step 34 — 메뉴 막다른 길 채우기

## 계획 (delegated)

근거: 재점검 3차 blindspot 1 (`docs/PLAN.md` 「재점검 3차」). Maya 메뉴 구조 research/maya/menus.md:440-462 (Windows),
:79 (Edit > Ungroup), :397 (Display > Heads Up Display), :23 (File > Export Selection), :837-850 (UV).
Maya 2022 설치본 스크립트는 동작·목록만 읽었다. 저장소에는 복사하지 않음:
- `startup/WindowMenu.mel` (build*EdMenu: Windows 하위 메뉴 내용)
- `others/performUngroup.mel` (Ungroup 기본 옵션)
- `startup/incrementAndSaveScene.mel` (번호 규칙)

1. **Windows > ... Editors**: Maya 가 실행 중에 채우는 하위 메뉴라서 menu_data 에 자식이 없다.
   - `menu_map.CHILDREN` (새): 경로 → 항목 목록. 순서와 라벨은 WindowMenu.mel 의 runTimeCommand 와
     research/maya/runtime_commands.json 라벨을 따른다.
   - `menu_sets` 가 이것을 하위 메뉴로 그린다 (`sub_items`).
   - Blender 대응이 있는 항목만 MAP 에 연결하고 나머지는 회색:
     - Attribute Editor / Channel Box / Layer Editor → 사이드바 독 (`maya_kit.dock_show`)
     - Tool Settings
     - Attribute Spread Sheet → Spreadsheet
     - Script Editor
     - UV Editor
     - Graph Editor
     - Time / Trax Editor → NLA
     - Camera Sequencer → Sequencer
     - Dope Sheet
     - Expression Editor → Drivers
     - Hypershade → Shader Editor
     - Render View
     - Render Settings
     - Shading Group Attributes
     - Display Layers
   - 편집기는 새 창으로 연다 (`maya_kit.open_editor`: area_dupli + ui_type). Maya 편집기도 떠 있는 창이다.
     Windows > Outliner / Node Editor 도 같은 방식이다.
2. **UV**: UV Editor = 새 창. Planar / Normal-Based = `maya_kit.uv_planar` (선택 면 평균 법선 평면에 투영, 0–1 에 맞춤,
   가로세로 비율 유지). Best Plane 은 점 세 개를 고르는 툴이라 회색으로 둔다.
3. **Edit > Ungroup** (`maya_kit.ungroup`): Maya 기본 옵션 (`ungroupPreserve true`, `-world` 아님) 을 따른다.
   - 자식은 그룹의 부모 밑으로 (부모가 없으면 월드로) 옮기고, 월드 변환을 유지한다 (`group.set_parent_keep_world` = Maya 방식).
   - 빈 그룹 (Empty) 은 지운다. 메시처럼 자기 데이터가 있는 오브젝트는 자식만 내보내고 남긴다 (delegated).
   - 안쪽 그룹부터 처리하고, 옮긴 자식을 선택한다.
4. **Display > Heads Up Display**: Maya HUD 항목 목록 [K] 을 CHILDREN 으로 두고 대응하는 것만 연결한다:
   - Poly Count = `overlay.show_stats`
   - Camera Names = `overlay.show_text`
   - View Axis = 내비게이션 기즈모
5. **File > Increment and Save** (`maya_kit.increment_save`): Maya 규칙 그대로 `increment_path`.
   - 루트 이름 끝의 `.숫자` 를 같은 자릿수로 +1, 없으면 `.0001` (MyFile.99 → MyFile.100).
   - 저장한 적 없는 씬이면 Save As 를 연다.
   - 같은 이름의 파일이 있으면 Maya 는 덮어쓸지 묻는다. 여기서는 덮어쓰지 않고 다음 빈 번호로 저장한다 (delegated).
6. **File > Export Selection...**: `MAYAKIT_MT_export_selection` = 내보내기마다 "선택한 것만" 을 켜고 파일 브라우저를 연다
   (FBX `use_selection`, OBJ `export_selected_objects`, glTF, USD, Alembic).

## 한 것

- `ui/menu_map.py`: `_editor`, `_dock`, `_hud`, `_WINDOW_EDITORS`, `CHILDREN`, MAP 항목 (Windows 편집기들, Outliner, Node Editor,
  UV Editor/Planar/Normal-Based, Edit > Ungroup, HUD Poly Count/Camera Names/View Axis, Increment and Save, Export Selection).
- `ui/menu_sets.py`: `sub_items()` — CHILDREN 이 있으면 그 항목으로 하위 메뉴를 만든다.
- `operators/menu_extras.py` (새): `maya_kit.open_editor`, `increment_path` + `maya_kit.increment_save`,
  `MAYAKIT_MT_export_selection`, `planar_uvs` + `maya_kit.uv_planar`.
- `operators/group.py`: `ungroup()`, `maya_kit.ungroup`.
- `ui/attribute_editor.py`: `maya_kit.dock_show(dock)`.
- 테스트: `tests/test_step34_menus.py` (7), `tests/gui/gui_step34_menus.py` (5 체크, 스크린샷 5장).

## 검증

- 헤드리스 `python tests/run.py`: **294/294** (32 파일). 확인한 것:
  - 새 경로 13개 매핑, MAP 경로가 모두 실제 메뉴 경로임
  - Windows 하위 메뉴 5개
  - Increment 규칙 6가지와 빈 번호 건너뛰기
  - Ungroup 의 월드 변환 유지 (부모 아래 / 월드)
  - Planar UV (윗면 = 0–1 정사각, 비율 유지)
  - Export Selection 이 "선택한 것만"을 켬
- GUI `python tests/gui/run.py`: **251/251** (26 파일). dogfood **47/47**, 콘솔 오류 0.
- 스크린샷 (`tmp/shots34/`) 직접 확인:
  - Windows 메뉴: Editors 5개가 ▸ 하위 메뉴, Outliner / Node Editor 활성
  - General Editors: 연결된 항목 활성, 나머지 회색
  - Animation Editors: Graph Editor / Time / Trax / Camera Sequencer / Dope Sheet / Expression Editor 활성
  - Graph Editor 새 창 열림
  - Poly Count = 뷰포트 통계 표시
  - Export Selection 메뉴: FBX / OBJ / glTF / USD / Alembic

## 남은 것

- 회색으로 남은 Windows 편집기: Hypergraph, Component Editor, Connection Editor, Namespace Editor, Shape Editor, Pose Editor,
  Light Editor, Relationship 편집기 대부분. Blender 대응이 없거나 약해서, 만들려면 별도 단계가 필요하다.
- UV > Best Plane (점 세 개를 고르는 툴) 은 회색. Planar 는 Maya 처럼 투영 축을 고르는 옵션 없이 평균 법선만 쓴다.
- HUD 는 Poly Count / Camera Names / View Axis 만 연결. Frame Rate, Object Details 등은 회색.
- Windows > Home, Content Browser, Minimize/Raise Window 는 그대로 회색.
