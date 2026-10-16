# Step 36 — 대칭 (Symmetry) 모델링

## 계획 (delegated)

Maya 근거:
- 기본값: 꺼짐, 축 x, 기준 object, 허용 오차 0.1, preserve seam 켬 (0.01), allow partial 켬. 시작할 때 optionVar 에서
  `symmetricModelling -e` 로 적용 (research/maya/interaction.md:159, research/maya/defaults.json:117-124). 저장된 값이 topo 이면
  시작할 때 꺼짐 + object 로 되돌린다 (Maya 2022 `initialStartup.mel:245-248`).
- Status Line 8번 그룹 (research/maya/ui_layout.md:207, `statusLine.mel:2941-2986`): ▾ 버튼 + 읽기 전용 글상자
  "Symmetry: Off" / 모드 이름, 켜지면 글상자 배경이 Maya 강조색 #5285A6 (`statusLine.mel:1909-1925`).
  ▾ LMB = 목록 Off · Object X/Y/Z · World X/Y/Z · Topology, MMB = 마지막 모드 ↔ 끔 (`reflectionProperties.mel:10-59`).
- 모드를 고르면 (Off·Topology 빼고) `SymmetrizeSelection` = 선택을 반대쪽까지 넓힌다 (`reflectionProperties.mel:39-41`).
- W/E/R 홀드 마킹 메뉴: 셋 다 `commonReflectionOptionsPopup` 을 부른다 (research/maya/marking_menus.json translate/rotate/scale
  `calls`). 그 메뉴 = N 「Symmetry ▸」 방사 하위 메뉴: N Symmetry (체크), W World, E Object, NE Topology, SW X Axis, S Y Axis,
  SE Z Axis (marking_menus.json `commonReflectionOptionsPopup` :35-77, 모두 체크 상자).
- Alt+R (`ToggleReflection`, hotkeySetup.mel:602) 은 Artisan 붓 / 옛 Move 컨텍스트의 reflection 플래그를 바꾸는 키다
  (`artisanNamedCommandSetup.mel` `artisanToggleReflection`). Status Line 대칭과 다른 상태라 묶지 않는다 (대응표 행은 그대로).

Blender 4.5 (실측 tmp/probe):
- 대칭은 메시 데이터마다: `Mesh.use_mirror_x/y/z` (로컬 축, 오브젝트 원점 기준), `use_mirror_topology`. 편집 모드 변환
  (G/R/S, 툴 기즈모 invoke) 과 스컬프트가 읽는다. `transform.translate` 를 exec 로 부를 때는 `mirror=True` 를 줘야 플래그를 쓴다
  (`mirror` 없이 x>0 정점 4개 +Z 이동 → 4개만, `mirror=True` → 8개).
- 허용 오차·seam 옵션은 RNA 에 없다. World 기준 대칭도 없다 (항상 메시 로컬).
- `depsgraph_update_post` 는 `object.mode_set(EDIT)` 때 불린다 (mode = EDIT_MESH).

설계:
1. 상태 = Maya 처럼 전역 하나. `Scene.maya_kit_symmetry` (PropertyGroup): `on` (기본 꺼짐), `about` OBJECT/WORLD/TOPOLOGY
   (기본 OBJECT), `axis` X/Y/Z (기본 X), `last` (MMB 토글이 돌아갈 모드, 기본 OBJECT_X). Maya 는 optionVar (환경설정) 이지만
   Blender 사용자 환경설정은 건드리지 않고 파일에 저장되는 씬 값으로 둔다. 템플릿 기본값 = Maya 기본값이라 startup.blend 는 그대로.
2. 적용 = `operators/symmetry.py` `apply(scene, objects)`: 편집 모드 메시마다 `use_mirror_x/y/z` 와 `use_mirror_topology` 를 쓴다
   (다를 때만). 축 대응 (delegated): **Maya 축 이름 = Blender 축 이름** (Channel Box·매니퓰레이터 색과 같은 이름; Maya Y-up ↔
   Blender Z-up 를 바꾸어 부르지 않는다, 결정 5). Object = 로컬 축 그대로. World = 그 월드 축과 가장 나란한 로컬 축 (회전한
   오브젝트도 월드 축 기준으로 대칭); 대칭면은 Blender 가 늘 오브젝트 원점을 지나므로, 원점이 월드 면 위에 없거나 축이
   어긋나면 경고 (부분 대응). Topology = `use_mirror_topology` + 현재 축 (Maya 는 seam 엣지를 고르지만 Blender 는 축 + 토폴로지로
   짝을 찾는다).
3. 메시마다 다른 Blender 상태를 전역처럼: `depsgraph_update_post` 핸들러가 편집 모드에 **들어갈 때** 들어간 메시에 전역 상태를
   적용하고, 편집 모드 **안에서** 사용자가 Blender 헤더의 X/Y/Z 미러 버튼을 바꾸면 그 값을 전역 상태로 읽어 온다 (두 쪽이 어긋나지
   않게; 쓸 때는 다를 때만이라 핸들러가 되돌아 돌지 않는다). Status Line 표시는 전역 상태.
4. `maya_kit.symmetry(mode)`: OFF / OBJECT_X… / WORLD_X… / TOPOLOGY (Status Line 목록, reflectionSetMode), TOGGLE (MMB 동작),
   ON (마킹 메뉴 체크), ABOUT_WORLD / ABOUT_OBJECT, AXIS_X/Y/Z (마킹 메뉴 체크). 켜는 모드는 `mesh.select_mirror(extend=True)`
   (SymmetrizeSelection) 를 부른다.
5. Status Line: ▾ 메뉴 버튼 (`MAYAKIT_MT_symmetry`, 글자 = "Symmetry: Off" / "Object X") + 켜짐이면 눌린 (파란) 대칭 토글
   버튼 (MMB 대신 클릭 = TOGGLE; Blender 메뉴 버튼에 MMB 동작을 달 수 없음). 스냅 그룹 오른쪽, ui_layout.md 순서대로.
6. 툴 설정: Maya Move/Rotate/Scale Tool Settings 의 「Symmetry Settings」 → `VIEW3D_PT_active_tool` 에 append (편집 메시에서만,
   변환 툴일 때): 같은 ▾ 메뉴 + Topology 상태. unregister 에서 remove.
7. 마킹 메뉴: OPT_MOVE/ROTATE/SCALE 의 N = 「Symmetry ▸」 방사 Sub (위 Maya 배치). 체크 표시는 `engine.TOGGLE_OPS` 에
   `maya_kit.symmetry` 를 넣고 `draw.checked` 가 `symmetry.item_state(mode)` 를 읽는다. 위치 테스트는 Maya 메뉴의 `calls`
   (commonReflectionOptionsPopup) 항목까지 비교하도록 넓힌다.

검증:
- 헤드리스 `tests/test_step36_symmetry.py`: 모드 → `use_mirror_*` / topology, Off 가 다 끔, World 축 고르기 (Z 축 90° 회전 →
  World X = 로컬 Y), 편집 모드 들어갈 때 다른 메시에 적용, Blender 헤더 플래그 → 전역 상태, TOGGLE 이 마지막 모드로,
  SymmetrizeSelection, `transform.translate(mirror=True)` 가 반대쪽 정점도 옮김, 마킹 메뉴 체크 상태, enable/disable 깨끗.
- GUI: Status Line ▾ 에서 Object X → 한쪽 정점을 기즈모/G 로 옮기면 반대쪽도 옮겨짐, W 홀드 → Symmetry ▸ 스크린샷.
- 전체 헤드리스·GUI·dogfood, `docs/manual_checks.md` 에 손 감각 항목.

## 한 것

- `operators/symmetry.py` (새):
  - `Scene.maya_kit_symmetry` (on / about / axis / last). 기본값 = Maya 기본값.
  - `apply` / `pull` / `flags` / `world_fit`.
  - `maya_kit.symmetry(mode)`: OFF · OBJECT_X… · WORLD_X… · TOPOLOGY · TOGGLE · ON · ABOUT_* · AXIS_*. 켜면 `mesh.select_mirror(extend)` 로 SymmetrizeSelection.
  - `depsgraph_update_post` 핸들러: 편집 모드로 들어가는 메시에 전역 상태를 적용하고, 편집 중 Blender 헤더 미러 버튼을 바꾸면 그 값을 읽어 온다.
- `ui/status_line.py`: 스냅 다음에 대칭 그룹 (파란 토글 + `MAYAKIT_MT_symmetry` ▾ "Symmetry: Off" / "Object X").
  `VIEW3D_PT_active_tool` 에 「Symmetry Settings」 append (편집 메시 + 변환/선택 툴; unregister 에서 remove).
  Maya strip 도 같은 함수로 그린다.
- `marking/menus.py`: Move / Rotate / Scale 옵션 메뉴 N = Symmetry ▸ (Maya 배치 7 항목, 모두 체크 상자).
  `engine.TOGGLE_OPS` 와 `draw.checked` 에 `maya_kit.symmetry` 를 넣었다 (파이 폴백 체크 아이콘 포함).
- `tests/test_step8_marking_menus.py`: 위치 비교가 Maya 메뉴가 부르는 proc(`calls`)의 항목까지 본다.
- delegated 결정:
  - 축 이름 = Maya 이름 그대로 (X=X, Y=Y, Z=Z).
  - World = 가장 나란한 로컬 축 + 원점이 월드 면 밖이면 경고.
  - 상태는 씬에 둔다 (사용자 환경설정은 건드리지 않음).
  - Alt+R (Artisan reflection) 은 묶지 않는다.
  - Status Line 의 MMB 토글은 별도 버튼으로 둔다.

## 검증

- 헤드리스 `tests/test_step36_symmetry.py` 12/12. 다음을 확인한다:
  - 모드 → 플래그, World 회전 축, 편집 모드 들어갈 때 전역 적용 (Blender 사용자의 메시 플래그도 덮어씀), 헤더 버튼 → 전역 상태.
  - TOGGLE, 마킹 메뉴 부분 항목·체크 상태, SymmetrizeSelection, `transform.translate(mirror=True)`, Status Line 그리기, disable 정리.
- 전체: 헤드리스 **312/312** (34 파일), GUI **267/267** (28 파일), dogfood **47/47**, 콘솔 오류 0.
- GUI `tests/gui/gui_step36_symmetry.py` 6/6:
  - Object X 를 켜고 +X 위 꼭짓점 하나를 Move 기즈모 Z 화살표로 끌면 1.0 → 2.03 이고, 선택 안 한 −X 짝도 2.03, 나머지는 그대로.
  - 스크린샷 (`--shots`): `gui_step36_status_line.png` (파란 토글 + "▾ Object X"), `gui_step36_w_symmetry.png` (W 홀드 → Symmetry ▸,
    Symmetry / Object / X Axis 체크), `gui_step36_tool_settings.png` (Tool Settings 팝업 「Symmetry Settings」). 직접 확인했다.
  - dogfood 03 스크린샷: Maya strip 1600 px 에서 "Symmetry: Off" 가 들어가고 렌더·편집기 그룹도 잘리지 않는다.
- `docs/manual_checks.md` Step 36 항목 5개.

## 남은 것

- Maya 는 대칭이 켜져 있으면 한쪽을 클릭할 때 반대쪽도 하이라이트·선택한다. 여기서는 켤 때만 반대쪽 선택을 더한다.
  옮기면 짝이 같이 움직이지만, 반대쪽 하이라이트는 없다.
- 지원하지 않는 것:
  - 허용 오차 0.1, Preserve Seam / Seam Tolerance / Falloff, Allow Partial Symmetry: Blender RNA 에 없다.
  - Topology 의 seam 엣지 고르기: Blender 는 축 + 토폴로지로 짝을 찾는다.
- World 는 Blender 가 오브젝트 원점을 지나는 면으로만 미러한다. 원점이 월드 면 위에 없으면 Maya 와 다르다 (경고만 낸다).
- Maya 피벗을 옮긴 오브젝트 (delta_location) 는 Maya Object 대칭 원점과 Blender 메시 원점이 다를 수 있다. 확인하지 않았다.
- HUD 「Symmetry」 표시 (defaults.json:150 `hud_symmetryVisibility`), 뷰 안 메시지: 없다.
- 오브젝트 모드에서 바꾼 상태는 다음 편집 모드 진입 때 적용된다 (오브젝트 모드 변환에는 대칭이 없다. Maya 도 컴포넌트 전용).
