# Step 160 — Maya UI reset and workspaces (#81)

Backlog `autodrive_bmk/backlog_155.json` #6.

## 계획

- Maya 근거: factory 작업 공간 목록 · 순서 · 구분선 `scripts/startup/buildViewMenu.mel:29-43, 176-180`, 동작
  (Reset / Save / Import / Delete Current Workspace, Disable Docking/Undocking) `:136-160`, Reset 글자
  `MayaStrings m_buildViewMenu.kFactoryReset` = `Reset "^1s" to Factory Default`; 레이아웃 = `resources/workspaces/*.json`
  (research/maya/workspaces.json, ui_layout.md:140-152; General = "Maya Classic", linkedMenu = 메뉴 세트).
- 템플릿 (tools/make_startup.py, GUI Blender): 완성된 General 을 `workspace.duplicate` 로 복사해 Maya 레시피 적용 —
  Modeling - Standard (Outliner · Time Slider 닫음, MTK 탭), Modeling - Expert (뷰포트만), Sculpting (Tool Settings dock),
  UV Editing (뷰포트 옆 UV Editor, AE 탭), Rigging (아래 Shape Editor = Shape Key Editor — Blender 리그 데이터에 노드 그래프
  없음, delegated), Animation (아래 Graph Editor), Rendering - Standard (Render 속성 열 + 아래 Script Editor, AE 탭).
  각 작업 공간 ID 속성 `allset_template` / `allset_menu_set` / `allset_dock_tab`. Blender factory 작업 공간은 템플릿에서
  뺌 (Maya 장면 = Maya 작업 공간만, 이름 충돌 Animation / Sculpting / UV Editing / Rendering 도 없앰 — delegated).
- 킷: `switch.append_workspace` (enter_layout 의 덧붙이기 일반화), `switch.reset_workspace` (템플릿에서 새로 덧붙여 같은
  이름 · 같은 PREV_KEY 로 바꾸고 옛것 삭제), `ui/workspaces.py` (Windows > Workspaces 메뉴, Status Line 드롭다운 = Maya
  작업 공간 → 파일의 다른 작업 공간, 선택 시 없으면 덧붙임, 메뉴 세트 · 탭 적용).
- 레인: 템플릿 생성기 결과 (작업 공간 이름 · 속성) 에 킷 코드 · 테스트가 의존해 순차 (생성기 → 킷 → 테스트 → GUI).

## 한 것

- `tools/make_startup.py`: `MAYA_WORKSPACES` 8 개 + `maya_workspaces()` / `apply_recipe()`, 다시 생성
  (`startup.blend` 103 KB). Animation Graph Editor 사이드바 끔.
- `switch.py`: `append_workspace`, `template_of`, `reset_workspace(window, ws=None)`, `TEMPLATE_KEY`; `is_maya_workspace` 가
  템플릿 표시도 봄 (Modeling - Expert 처럼 Status Line 이 없는 Maya 작업 공간); enter_layout / scene_carry 는 Maya
  Classic 을 먼저 고름; `_fit_views` 는 바뀔 때만 tool header 를 쓰고, 덧붙인 뒤 창 override 안에서 실행 (-b 에서 파일
  읽은 뒤 컨텍스트 창이 없어 ED_area_init 충돌 — 측정).
- `ui/workspaces.py`: `allset.maya_workspace(name)`, `allset.reset_workspace`, `ALLSET_MT_maya_workspaces` (Maya 순서 14 개,
  템플릿에 없는 6 개 (Pose Sculpting, XGen ×2, Rendering - Expert, MASH, Motion Graphics) 와 Save / Import / Delete / Lock 은
  회색 + 알림, Reset 글자 = Maya 문구), 드롭다운 (`status_line` 이 위임). `Windows/Workspaces` → 이 메뉴.

## 검증

- `tests/test_step160_workspaces.py` 5/5: 템플릿 8 개 = 생성기 표, 속성 · 영역 구성 (Expert = 3D View 하나, UV / FCURVES /
  SHAPEKEY / TEXT_EDITOR + Render 속성, Sculpting = Tool Settings dock), Blender 파일에 덧붙이기 + 메뉴 세트 / 탭 적용 + 재사용,
  Reset 이 바뀐 Animation 레이아웃을 되돌림 (같은 이름, 옛것 삭제), 전환 레이아웃 Reset 이 PREV_KEY 유지, 메뉴 · 드롭다운 · 알림.
- 헤드리스 전체 **1492 / 1492**.
- GUI `-k gui_step160,gui_step113` 21/21, 이후 `-k gui_step160,gui_step138,gui_step129_switch` 47/47. 작업 공간 8 개 스크린샷
  (`tmp/shots160/`, 모음 sheet.png) 눈으로 확인: Maya Classic / MTK 가 올라간 Modeling - Standard / 뷰포트만 Expert / Tool
  Settings Sculpting / UV Editor 옆 UV Editing (Maya UV 메뉴) / Shape Key Editor 아래 Rigging / Graph Editor 아래 Animation /
  Render 속성 + Script Editor Rendering. Reset 이 INFO 로 바꾼 Outliner 를 되돌림.
- GUI 전체 묶음은 돌리지 않음 (사용자 규칙: release prep 에서만).

## 남은 것

- Modeling - Expert 의 뷰포트 머리줄은 Status Line 이 없는 화면이라 Maya 패널 메뉴 뒤에 Blender 머리줄 위젯이 남음.
- Maya 의 탭 묶음 (Animation 의 Time Editor, Rigging 의 Node Editor, Rendering 의 Render Setup / Light Editor 등) 은 하나만
  (Blender 영역은 탭이 없음).
- Blender 자체 작업 공간 탭으로 바꾸면 메뉴 세트 · 탭은 안 바뀜 (킷 메뉴 / 드롭다운으로 바꿀 때만).
- Save / Import / Delete Current Workspace, Disable Docking — 회색 + 알림.
