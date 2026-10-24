# Step 176 — Selected-face look and dogfood fixes

Backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_174.json` 3 번째 (재점검 12차 = step 173).

## 계획 (레인)

| 레인 | 내용 | 파일 | 누가 |
|---|---|---|---|
| A | 선택 면 모양 (look_compare viewport 11/12 → 12/12) | `ui/component_colors.py` | 메인 |
| B | dogfood G1: Ctrl+D → Ctrl+G → Ctrl+Z → P 뒤 INPUTS polyCube1 사라짐 | `operators/prim_history.py`, `ui/channel_box.py`, GUI 테스트 | 서브에이전트 |
| C | G2: Undo 뒤 결과 칸 = Maya 문구 (Maya 측정) | `command_line/`, `results.py`, `undo_steps.py` | 서브에이전트 |
| D | 네 뷰 이름표 Maya 축 | `ui/view_furniture.py` | 메인 |

B, C 는 서로 다른 파일이라 동시에 (Blender 2 개 한도: B · C 가 하나씩, 메인은 그동안 코드만). look_compare 는 B · C 가 끝난 뒤
(zip 빌드와 Blender 수 때문에 순서가 필요).

## A. 선택 면 — 원인 (화면으로 확인)

`tmp/look_env_audit173_s100/shots/07_faces_selected.png` 를 윗면 점 (816, 419) 에서 픽셀로 읽음:

| | stipple 점 (2 × 2 의 한 칸) | 나머지 3 칸 |
|---|---|---|
| Maya 07 | (227, 172, 121) | (118, 118, 118) = 바탕 회색 그대로 |
| kit 07 | (226, 170, 120) | **(157, 133, 107)** |
| kit 03 (선택 없음) | — | (116, 117, 119) |

kit stipple 자체는 Maya 와 같다. 사이 픽셀이 주황으로 물든 것은 Blender 의 편집 모드 선택 면 강조 (theme `face_select`,
3D View overlay `show_faces`) 가 kit stipple 아래에 그려지기 때문 — 확인됨 (kit 은 `show_faces` 를 어디서도 끄지 않았다).

고침 (delegated): Maya 레이아웃 (Maya strip 이 있는 화면) 의 3D View 에서, kit 이 편집 중인 메시를 모두 그리는 동안
`space.overlay.show_faces` 를 끈다 (뷰 데이터, preferences 아님; draw 안에서 쓰지 않고 0 s 타이머). kit 이 그리지 않게 되면
(preference `maya_component_colors` 끔, `BMESH_LIMIT` 넘는 메시) 그리고 unregister 때 kit 이 끈 뷰만 다시 켠다
(`component_colors.face_overlay_action`). 템플릿은 그대로 (kit 이 못 그리는 경우 Blender 강조가 남아야 하므로).
사용자 워크스페이스 뷰는 건드리지 않는다 (step 91 규칙).

결과 (`ALLSET_GUI_UI_SCALE=0.8 ALLSET_LOOK_TAG=s176_s100 python tools/look_compare.py` → `research/maya/screens/compare_s176_s100/`):
윗면 사이 픽셀 (116, 117, 119) = 선택 없는 면과 같음 (Maya 118). viewport **12 / 12** (선택 면 ΔE00 40.5 → **2.3**: kit 평균
#8d8177 vs Maya #918477). 측정 고침: step 174 이후 컴포넌트 모드에서도 Move 도구가 남아 (Maya 07 도 그렇다) Z 화살표 축이 윗면
중심의 표본 상자를 지나간다 — `tools/look_data.py` tint 표본에 kit 상자 오프셋 (-8, 0) px × UI 배율 (Maya 영역도 Maya
매니퓰레이터 옆). 오프셋 때문에 통과한 것이 아님: 같은 상자로 재점검 12차 샷은 평균 (178, 144, 111) (주황), 이번 샷 (150, 133, 119),
Maya (145, 132, 119). 나머지 수치는 step 173 과 같음 (pixels kit 6/6, rects 5/12, density 5/6, scene 3/3, furniture 2/3).

## B. dogfood G1 — kit 버그 아님

서브에이전트 조사: `tools/dogfood_session.py:226-234` 는 샷 04 뒤 Ctrl+D 전에 **Alt+Shift+D (Delete History)** 를 누른다.
`allset.delete_history` → `prim_history.drop` (`operators/history.py:62-69`) 이 polyCube1 을 지운다 — Maya 도 같다
(Alt+Shift+D = DeleteHistory = `delete -ch`, research/maya/hotkeys_default.json:3105-3124, 창조 노드도 history). 그래서 05 / 08
에 INPUTS 가 없는 것이 맞다. 재점검 12차의 헤드리스 탐침이 Delete History 를 빼서 GUI 와 달라 보였다. 반증 확인: memfile
undo, Channel Box 행 캐시, undo 뒤 포인터 — GUI 테스트에서 키마다 노드 · 서명이 그대로 ("sig ok").
테스트로 남김: `tests/gui/gui_step176_inputs_undo.py` (dogfood 순서 그대로 = Alt+Shift+D 에서 사라짐; Alt+Shift+D 없이 pCylinder1
= 모든 키 뒤 남음, 23 / 23), `tests/test_step176_inputs_undo.py` (헤드리스, 깊이 0 명령 + 실제 `ed.undo`, 2 / 2). src 변경 없음.

## C. G2 — Undo / Redo 뒤 결과 칸 = Maya 문구

Maya 측정 (서브에이전트, GUI Maya 2022, `MAYA_APP_DIR` = tmp, QTest 키 + 메뉴 QAction, Command Line 결과 QLineEdit 읽기 + grab;
`research/maya/re/undo_result_176.md`, 스크립트 `research/scripts/maya_undo176/`, 데이터 `research/maya/screens/undo176*/`):
Ctrl+Z / z / Edit > Undo 뒤 결과 칸 = `Undo: <undo chunk 이름>` (`//` 없음, 보통 색), Redo = `Redo: <이름>`. 이름 = 메뉴 · 핫키의
runtime command (`Group`, `CreatePolygonCube`), 입력한 MEL 은 그 글자 그대로, 이름 없는 chunk (선택) = `Undo: `. 더 없으면
`// Error: line 1: There are no more commands to undo.` (빨강). Script Editor `// Undo: Group`, Edit 메뉴 `Undo "Group"` (28 자 + ...).

구현 `src/allset/command_line/undo_text.py`: Blender 는 Python 에 undo 단계 이름을 주지 않아 (`print_undo_steps` 는 C 콘솔만)
kit 이 Blender 순서대로 이름 목록을 들고 있다 — `undo_steps.push` (Maya 항목 이름), Command Line 입력 (입력 글자),
`results.result` 를 내는 깊이 0 UNDO 연산자 (`bl_label`), Blender 가 등록한 REGISTER+UNDO 연산자 (`wm.operators`, 매 depsgraph
갱신; Blender 가 undo 전에 이 목록을 비우므로 — 측정 — undo 핸들러에서는 못 읽음). `undo_pre` / `redo_pre` 가 위치를 옮기고
`undo_post` / `redo_post` 가 글을 쓴다. Adjust Last Operation 의 되돌리고-다시-실행은 0 s 타이머가 앞 글로 되돌림. 메인 수정:
`wm.operators` 포인터는 Blender 가 오래된 것을 풀고 주소를 다시 쓰므로 살아 있는 포인터만 기억 (`_claimed` = 등록 전에 센 것).

## D. 네 뷰 이름표

`SIDE_LABELS` = Maya 카메라 이름 + Maya Y-up 시선 방향: top -Y, front -Z, side -X (bottom +Y, back +Z, left +X).
축 삼각대는 그대로 Blender 축 (Channel Box 글자와 같아야 함). delegated: 이름표는 Maya 카메라 이름이라 Maya 글자.
GUI 샷 `compare_s176_s100/16_four_view.png`: kit 칸 이름 top -Y / persp / front -Z / side -X = Maya 그대로.

## 검증

- 헤드리스 전체 `ALLSET_SANDBOX=s176full python tests/run.py`: **1621 / 1621** (175 끝 1611 + 새 10).
  새 파일: `test_step176_face_look` 2, `test_step176_inputs_undo` 2, `test_step176_undo_result` 6.
- GUI: `gui_step134_selection` 13 / 13 (새 검사 2: 면 모드에서 `show_faces` 꺼짐 + stipple 사이 회색 퍼짐 0.008, preference 끄면
  다시 켜짐), `gui_step46_view_furniture` + `gui_step161_views` 통과 (세 파일 28 / 28), `gui_step176_inputs_undo` + `gui_step161_messages`
  33 / 33 (G2: Ctrl+Z 뒤 결과 칸 `'Undo: Group'`).
- look_compare (실효 1.0): viewport **12 / 12** (처음), 나머지 수치 step 173 과 같음. 네 뷰 샷 이름표 = Maya.
- GUI 전체 묶음은 돌리지 않음: CLAUDE.md step 141 테스트 규칙 (사용자 10-23: 단계마다 바꾼 모듈의 GUI 파일, 전체는 릴리스 준비 때).

## 남은 것

- G2: kit 이 보지 못한 단계 (보고 없는 UNDO 전용 연산자, 버튼 속성 편집, `auto_key.py` / `graph_keys.py` / `view.py` 의 직접
  `ed.undo_push`) 는 목록에 없어 그 앞 단계 이름이 나온다; 더 되돌릴 것이 없을 때의 빨간 Maya 오류 (Blender `ed.undo` 가 조용히
  실패 — kit undo 연산자가 키에 있어야 함), Script Editor `// Undo: ...` 줄, Edit 메뉴 `Undo "Group"` 이름은 안 함.
- A: kit 이 끈 `show_faces` 는 파일 다시 열기 뒤에는 추적하지 않음 (그 파일을 kit 없이 열면 면 강조 없음 — 드묾).
- B: dogfood 샷 05 에 INPUTS 를 보이려면 `tools/dogfood_session.py` 가 Alt+Shift+D 를 빼야 함 (스크립트 선택, kit 문제 아님).

